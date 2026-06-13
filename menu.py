#!/usr/bin/env python3
import getpass
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from auditoria.auditor import generate_report  # noqa: E402
from auditoria.monitor import check, initialize  # noqa: E402
from blockchain.blockchain import carregar_cadeia, registrar_evento, validar_cadeia  # noqa: E402
from usuarios.auth import (  # noqa: E402
    cadastrar_usuario,
    has_users,
    login,
    logout,
    remover_usuario,
    require_permission,
    session,
)


def pause():
    input("\nPressione Enter para continuar...")


def title(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def create_user():
    title("Cadastrar usuario")
    if has_users():
        require_permission("manage_users")
    username = input("Usuario: ").strip()
    profile = input("Perfil (admin/analista/visitante): ").strip().lower()
    password = getpass.getpass("Senha: ")
    confirm = getpass.getpass("Confirmar senha: ")

    if password != confirm:
        print("Erro: as senhas nao conferem.")
        return

    try:
        cadastrar_usuario(username, profile, password)
    except ValueError as error:
        print(f"Erro: {error}")


def remove_user():
    title("Remover usuario")
    require_permission("manage_users")
    username = input("Usuario a remover: ").strip()
    remover_usuario(username)


def login_user():
    title("Login")
    username = input("Usuario: ").strip()
    password = getpass.getpass("Senha: ")
    login(username, password)


def initialize_hashes():
    title("Inicializar hashes")
    require_permission("monitor_initialize")
    initialize()


def check_integrity():
    title("Verificar integridade")
    require_permission("monitor_check")
    update = input("Atualizar referencia apos alerta? (s/N): ").strip().lower() == "s"
    check(update_reference=update)


def execute_backup():
    title("Executar backup seguro")
    require_permission("backup")
    script = ROOT_DIR / "backup" / "backup.sh"

    if not script.exists():
        print("Erro: backup/backup.sh nao encontrado.")
        return

    env = os.environ.copy()
    password = getpass.getpass("Senha para criptografar o backup: ")
    env["SECURECHAIN_BACKUP_PASSWORD"] = password

    result = subprocess.run(
        ["bash", str(script)],
        cwd=str(ROOT_DIR),
        env=env,
        text=True,
    )

    if result.returncode != 0:
        print("Erro ao executar backup.")


def validate_blockchain():
    title("Validar blockchain")
    require_permission("blockchain_read")
    problems = validar_cadeia()
    if problems:
        print("ALERTA: blockchain inconsistente.")
        for problem in problems:
            print(f"- {problem}")
        return
    print("Blockchain integra.")


def show_blockchain():
    title("Eventos registrados na blockchain")
    require_permission("blockchain_read")
    chain = carregar_cadeia()
    if not chain:
        print("Nenhum bloco registrado.")
        return

    for block in chain:
        print(f"[{block['id']}] {block['timestamp']} - {block['evento']}")


def manual_event():
    title("Registrar evento manual")
    require_permission("blockchain_write")
    event = input("Descricao do evento: ").strip()
    if not event:
        print("Evento vazio nao registrado.")
        return
    block = registrar_evento(event)
    print(f"Evento registrado no bloco {block['id']}.")


def show_session():
    title("Sessao ativa")
    session()


def logout_user():
    title("Encerrar sessao")
    logout()


def execute_audit():
    title("Gerar relatorio de auditoria")
    require_permission("audit")
    report_path, failures = generate_report()
    print(f"Relatorio salvo em: {report_path}")
    if failures:
        print("Comandos com falha: " + ", ".join(failures))


def list_reports():
    title("Relatorios de auditoria")
    require_permission("reports_read")
    reports = sorted((ROOT_DIR / "auditoria" / "relatorios").glob("*.txt"))
    if not reports:
        print("Nenhum relatorio encontrado.")
        return
    for report in reports:
        print(report.name)


def menu():
    options = {
        "1": ("Cadastrar usuario", create_user),
        "2": ("Login", login_user),
        "3": ("Mostrar sessao ativa", show_session),
        "4": ("Remover usuario", remove_user),
        "5": ("Inicializar hashes dos documentos", initialize_hashes),
        "6": ("Verificar integridade dos documentos", check_integrity),
        "7": ("Executar backup criptografado", execute_backup),
        "8": ("Gerar relatorio de auditoria", execute_audit),
        "9": ("Listar relatorios", list_reports),
        "10": ("Validar blockchain", validate_blockchain),
        "11": ("Listar eventos da blockchain", show_blockchain),
        "12": ("Registrar evento manual", manual_event),
        "13": ("Logout", logout_user),
        "0": ("Sair", None),
    }

    while True:
        title("SecureChain Audit - Menu")
        for key, (label, _) in options.items():
            print(f"{key} - {label}")

        choice = input("\nEscolha uma opcao: ").strip()
        if choice == "0":
            print("Saindo.")
            break

        action = options.get(choice)
        if action is None:
            print("Opcao invalida.")
            pause()
            continue

        try:
            action[1]()
        except KeyboardInterrupt:
            print("\nOperacao cancelada.")
        except PermissionError as error:
            print(f"Acesso negado: {error}")
        except Exception as error:
            print(f"Erro inesperado: {error}")

        pause()


if __name__ == "__main__":
    menu()
