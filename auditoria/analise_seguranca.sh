#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/relatorios"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
REPORT="${OUTPUT_DIR}/analise-seguranca-${TIMESTAMP}.txt"

mkdir -p "${OUTPUT_DIR}"

{
  echo "SECURECHAIN AUDIT - ANALISE DE SEGURANCA DA VM"
  echo "Data: $(date -Iseconds)"
  echo
  echo "== PORTAS LOCAIS (ss -tulpn) =="
  ss -tulpn 2>&1 || true
  echo
  echo "== ESCANEAMENTO LOCAL (nmap) =="
  if command -v nmap >/dev/null 2>&1; then
    nmap -sV --top-ports 100 localhost 2>&1 || true
  else
    echo "nmap nao instalado. Instale com: sudo apt install nmap"
  fi
  echo
  echo "== PERMISSOES DO PROJETO =="
  find "${ROOT_DIR}" -maxdepth 3 -printf "%M %u:%g %p\n" | sort
  echo
  echo "Analise de risco e melhorias devem ser preenchidas no RELATORIO_TECNICO.md."
} > "${REPORT}"

python3 "${ROOT_DIR}/blockchain/blockchain.py" \
  --event "Analise de seguranca executada: relatorio=$(basename "${REPORT}")"

echo "Relatorio salvo em: ${REPORT}"
