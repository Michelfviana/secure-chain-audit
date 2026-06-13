#!/usr/bin/env python3
import argparse
import socket
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT_DIR / "auditoria" / "relatorios"

sys.path.insert(0, str(ROOT_DIR))
from blockchain.blockchain import registrar_evento  # noqa: E402


COMMANDS = {
    "USUARIOS CONECTADOS (who)": ["who"],
    "HISTORICO DE LOGINS (last)": ["last", "-n", "30"],
    "PORTAS E SERVICOS (ss -tulpn)": ["ss", "-tulpn"],
    "INTERFACES DE REDE (ip a)": ["ip", "a"],
}


def run_command(command):
    if shutil.which(command[0]) is None:
        return 127, f"Comando nao encontrado: {command[0]}\n"
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    output = result.stdout
    if result.stderr:
        output += "\nSTDERR:\n" + result.stderr
    return result.returncode, output or "(sem dados)\n"


def generate_report():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc)
    filename = f"auditoria-{timestamp.strftime('%Y%m%dT%H%M%SZ')}.txt"
    report_path = REPORTS_DIR / filename
    failures = []

    sections = [
        "SECURECHAIN AUDIT - RELATORIO DO SISTEMA OPERACIONAL",
        f"Gerado em: {timestamp.isoformat()}",
        f"Host: {socket.gethostname()}",
        "",
    ]

    for title, command in COMMANDS.items():
        return_code, output = run_command(command)
        sections.extend(
            [
                "=" * 72,
                title,
                f"Comando: {' '.join(command)}",
                f"Codigo de saida: {return_code}",
                "-" * 72,
                output.rstrip(),
                "",
            ]
        )
        if return_code != 0:
            failures.append(command[0])

    report_path.write_text("\n".join(sections) + "\n", encoding="utf-8")
    status = "parcial" if failures else "completo"
    registrar_evento(
        f"Auditoria do sistema executada: relatorio={filename}; status={status}"
    )
    return report_path, failures


def main():
    parser = argparse.ArgumentParser(description="RF06 - Auditoria do sistema operacional")
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Uso administrativo/cron: nao exige sessao da aplicacao",
    )
    args = parser.parse_args()

    if not args.no_auth:
        from usuarios.auth import require_permission

        require_permission("audit")

    report_path, failures = generate_report()
    print(f"Relatorio salvo em: {report_path}")
    if failures:
        print("Aviso: comandos indisponiveis ou com erro: " + ", ".join(failures))


if __name__ == "__main__":
    main()
