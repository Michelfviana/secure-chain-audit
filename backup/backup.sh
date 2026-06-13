#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DOCUMENTS_DIR="${ROOT_DIR}/documentos"
OUTPUT_DIR="${ROOT_DIR}/backup/arquivos"
LOG_FILE="${ROOT_DIR}/logs/backup.log"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ARCHIVE_FILE="${OUTPUT_DIR}/documentos-${TIMESTAMP}.tar.gz"
ENCRYPTED_FILE="${ARCHIVE_FILE}.enc"
trap 'rm -f "${ARCHIVE_FILE}"' EXIT

mkdir -p "${DOCUMENTS_DIR}" "${OUTPUT_DIR}" "$(dirname "${LOG_FILE}")"

if ! command -v openssl >/dev/null 2>&1; then
  echo "$(date -Iseconds) status=ERRO motivo=openssl_nao_encontrado" >> "${LOG_FILE}"
  python3 "${ROOT_DIR}/blockchain/blockchain.py" --event "Backup falhou: openssl nao encontrado"
  echo "Erro: openssl nao encontrado."
  exit 1
fi

if [[ -z "${SECURECHAIN_BACKUP_PASSWORD:-}" ]]; then
  read -r -s -p "Senha para criptografar o backup: " SECURECHAIN_BACKUP_PASSWORD
  echo
fi

if [[ -z "${SECURECHAIN_BACKUP_PASSWORD}" ]]; then
  echo "$(date -Iseconds) status=ERRO motivo=senha_vazia" >> "${LOG_FILE}"
  python3 "${ROOT_DIR}/blockchain/blockchain.py" --event "Backup falhou: senha vazia"
  echo "Erro: a senha do backup nao pode ser vazia."
  exit 1
fi

status="OK"
message="Backup executado"

if tar -czf "${ARCHIVE_FILE}" -C "${ROOT_DIR}" "documentos"; then
  openssl enc -aes-256-cbc -salt -pbkdf2 \
    -in "${ARCHIVE_FILE}" \
    -out "${ENCRYPTED_FILE}" \
    -pass fd:3 3<<<"${SECURECHAIN_BACKUP_PASSWORD}"
else
  status="ERRO"
  message="Backup falhou: erro na compactacao"
fi

if [[ "${status}" == "OK" && -f "${ENCRYPTED_FILE}" ]]; then
  size="$(stat -c%s "${ENCRYPTED_FILE}")"
  echo "$(date -Iseconds) arquivo=${ENCRYPTED_FILE} tamanho=${size} status=${status}" >> "${LOG_FILE}"
  python3 "${ROOT_DIR}/blockchain/blockchain.py" --event "${message}: arquivo=$(basename "${ENCRYPTED_FILE}"); tamanho=${size} bytes"
  echo "Backup criptografado criado em: ${ENCRYPTED_FILE}"
else
  echo "$(date -Iseconds) status=${status}" >> "${LOG_FILE}"
  python3 "${ROOT_DIR}/blockchain/blockchain.py" --event "${message}"
  echo "Erro ao executar backup."
  exit 1
fi
