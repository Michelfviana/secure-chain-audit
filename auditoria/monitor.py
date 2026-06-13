#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DOCUMENTS_DIR = ROOT_DIR / "documentos"
STATE_FILE = ROOT_DIR / "auditoria" / "hashes_documentos.json"

sys.path.insert(0, str(ROOT_DIR))
from blockchain.blockchain import registrar_evento  # noqa: E402


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_documents():
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for path in sorted(DOCUMENTS_DIR.rglob("*")):
        if path.is_file():
            relative = path.relative_to(DOCUMENTS_DIR).as_posix()
            hashes[relative] = file_hash(path)
    return hashes


def load_state():
    if not STATE_FILE.exists():
        return {}
    with STATE_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
        return data if isinstance(data, dict) else {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2, ensure_ascii=False)
        file.write("\n")


def initialize():
    state = scan_documents()
    save_state(state)
    registrar_evento(f"Hashes de referencia inicializados: total_arquivos={len(state)}")
    print(f"Referencia criada com {len(state)} arquivo(s).")


def check(update_reference=False):
    previous = load_state()
    current = scan_documents()
    alerts = []

    for name in sorted(current.keys() - previous.keys()):
        alerts.append(("INCLUSAO", name))

    for name in sorted(previous.keys() - current.keys()):
        alerts.append(("EXCLUSAO", name))

    for name in sorted(current.keys() & previous.keys()):
        if current[name] != previous[name]:
            alerts.append(("ALTERACAO", name))

    if not alerts:
        print("Nenhuma inconsistencia detectada.")
        return False

    print("ALERTA: inconsistencias detectadas no diretorio documentos/")
    event_labels = {
        "ALTERACAO": "Arquivo alterado",
        "INCLUSAO": "Arquivo incluido",
        "EXCLUSAO": "Arquivo excluido",
    }

    for kind, name in alerts:
        message = f"{event_labels[kind]}: {name}"
        print(f"- {kind}: {name}")
        registrar_evento(message)

    if update_reference:
        save_state(current)
        registrar_evento("Referencia de hashes atualizada apos verificacao")
        print("Referencia atualizada.")

    return True


def watch(interval, update_reference):
    print(f"Monitorando documentos/ a cada {interval} segundo(s). Use Ctrl+C para parar.")
    while True:
        check(update_reference=update_reference)
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="RF03 - Monitoramento de integridade")
    parser.add_argument("--init", action="store_true", help="Cria hashes de referencia")
    parser.add_argument("--check", action="store_true", help="Compara estado atual com referencia")
    parser.add_argument("--watch", action="store_true", help="Executa verificacoes periodicas")
    parser.add_argument("--interval", type=int, default=10, help="Intervalo do modo watch em segundos")
    parser.add_argument(
        "--update-reference",
        action="store_true",
        help="Atualiza a referencia apos detectar inconsistencias",
    )
    args = parser.parse_args()

    if args.init:
        initialize()
    elif args.check:
        has_alerts = check(update_reference=args.update_reference)
        raise SystemExit(1 if has_alerts else 0)
    elif args.watch:
        watch(args.interval, args.update_reference)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
