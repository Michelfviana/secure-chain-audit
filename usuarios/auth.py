#!/usr/bin/env python3
import argparse
import base64
import getpass
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
USERS_FILE = ROOT_DIR / "usuarios" / "users.json"
SESSION_FILE = ROOT_DIR / "usuarios" / "session.json"
LOG_FILE = ROOT_DIR / "logs" / "acessos.log"
VALID_PROFILES = {"admin", "analista", "visitante"}
PBKDF2_ITERATIONS = 200_000
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60
PROFILE_PERMISSIONS = {
    "admin": {
        "manage_users",
        "monitor_initialize",
        "monitor_check",
        "backup",
        "audit",
        "blockchain_read",
        "blockchain_write",
        "reports_read",
    },
    "analista": {
        "monitor_initialize",
        "monitor_check",
        "backup",
        "audit",
        "blockchain_read",
        "reports_read",
    },
    "visitante": {"reports_read", "blockchain_read"},
}

sys.path.insert(0, str(ROOT_DIR))
from blockchain.blockchain import registrar_evento  # noqa: E402


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _load_users():
    if not USERS_FILE.exists():
        return {}
    with USERS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
        return data if isinstance(data, dict) else {}


def has_users():
    return bool(_load_users())


def _save_users(users):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with USERS_FILE.open("w", encoding="utf-8") as file:
        json.dump(users, file, indent=2, ensure_ascii=False)
        file.write("\n")


def _password_hash(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return {
        "algorithm": "PBKDF2-HMAC-SHA256",
        "iterations": PBKDF2_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "hash": base64.b64encode(digest).decode("ascii"),
    }


def _verify_password(password, stored):
    try:
        salt = base64.b64decode(stored["salt"], validate=True)
        expected = base64.b64decode(stored["hash"], validate=True)
        calculated = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(stored["iterations"]),
        )
        return hmac.compare_digest(expected, calculated)
    except (KeyError, TypeError, ValueError):
        return False


def _log_access(message):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(f"{_now_iso()} {message}\n")


def cadastrar_usuario(username, profile, password):
    username = username.strip()
    profile = profile.strip().lower()

    if not username:
        raise ValueError("Nome de usuario obrigatorio.")
    if profile not in VALID_PROFILES:
        raise ValueError("Perfil invalido. Use admin, analista ou visitante.")
    if len(password) < 6:
        raise ValueError("A senha deve possuir pelo menos 6 caracteres.")

    users = _load_users()
    if username in users:
        raise ValueError("Usuario ja cadastrado.")

    users[username] = {
        "profile": profile,
        "password": _password_hash(password),
        "created_at": _now_iso(),
    }
    _save_users(users)
    registrar_evento(f"Usuario criado: usuario={username}; perfil={profile}")
    print("Usuario cadastrado com sucesso.")


def remover_usuario(username):
    username = username.strip()
    users = _load_users()
    if username not in users:
        raise ValueError("Usuario nao encontrado.")

    profile = users[username]["profile"]
    if profile == "admin":
        admin_count = sum(user.get("profile") == "admin" for user in users.values())
        if admin_count <= 1:
            raise ValueError("Nao e permitido remover o ultimo administrador.")

    del users[username]
    _save_users(users)
    registrar_evento(f"Usuario removido: usuario={username}; perfil={profile}")
    print("Usuario removido com sucesso.")


def login(username, password):
    users = _load_users()
    user = users.get(username)

    if not user or not _verify_password(password, user["password"]):
        _log_access(f"LOGIN_NEGADO usuario={username}")
        registrar_evento(f"Tentativa de acesso negada: usuario={username}")
        print("Acesso negado.")
        return False

    session = {
        "username": username,
        "profile": user["profile"],
        "login_at": _now_iso(),
    }
    with SESSION_FILE.open("w", encoding="utf-8") as file:
        json.dump(session, file, indent=2, ensure_ascii=False)
        file.write("\n")

    _log_access(f"LOGIN_OK usuario={username} perfil={user['profile']}")
    registrar_evento(f"Login realizado: usuario={username}; perfil={user['profile']}")
    print(f"Login realizado. Perfil ativo: {user['profile']}")
    return True


def get_session():
    if not SESSION_FILE.exists():
        return None
    try:
        with SESSION_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        login_at = datetime.fromisoformat(data["login_at"].replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - login_at).total_seconds()
        if age > SESSION_MAX_AGE_SECONDS:
            SESSION_FILE.unlink(missing_ok=True)
            return None
        if data.get("profile") not in VALID_PROFILES:
            return None
        return data
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def require_permission(permission):
    active = get_session()
    if active is None:
        raise PermissionError("Autenticacao obrigatoria. Realize o login.")
    allowed = PROFILE_PERMISSIONS.get(active["profile"], set())
    if permission not in allowed:
        registrar_evento(
            "Acesso negado por perfil: "
            f"usuario={active['username']}; perfil={active['profile']}; recurso={permission}"
        )
        raise PermissionError("O perfil ativo nao possui permissao para esta operacao.")
    return active


def session():
    data = get_session()
    if data is None:
        print("Nenhuma sessao ativa ou a sessao expirou.")
        return
    print(f"Usuario ativo: {data['username']}")
    print(f"Perfil: {data['profile']}")
    print(f"Login em: {data['login_at']}")


def logout():
    if SESSION_FILE.exists():
        with SESSION_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        SESSION_FILE.unlink()
        registrar_evento(f"Logout realizado: usuario={data.get('username')}")
    print("Sessao encerrada.")


def main():
    parser = argparse.ArgumentParser(description="RF02 - Autenticacao SecureChain")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-user", help="Cadastra usuario")
    create.add_argument("username")
    create.add_argument("profile", choices=sorted(VALID_PROFILES))

    sign_in = sub.add_parser("login", help="Realiza login")
    sign_in.add_argument("username")

    remove = sub.add_parser("remove-user", help="Remove usuario")
    remove.add_argument("username")

    sub.add_parser("session", help="Mostra sessao ativa")
    sub.add_parser("logout", help="Encerra sessao")

    args = parser.parse_args()

    if args.command == "create-user":
        if _load_users():
            require_permission("manage_users")
        password = getpass.getpass("Senha: ")
        confirm = getpass.getpass("Confirmar senha: ")
        if password != confirm:
            raise SystemExit("As senhas nao conferem.")
        cadastrar_usuario(args.username, args.profile, password)
    elif args.command == "remove-user":
        require_permission("manage_users")
        remover_usuario(args.username)
    elif args.command == "login":
        password = getpass.getpass("Senha: ")
        ok = login(args.username, password)
        raise SystemExit(0 if ok else 1)
    elif args.command == "session":
        session()
    elif args.command == "logout":
        logout()


if __name__ == "__main__":
    main()
