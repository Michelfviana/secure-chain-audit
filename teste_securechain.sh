#!/usr/bin/env bash
set -e

echo "== Preparando ambiente =="
chmod +x backup/backup.sh

echo "== Criando documento inicial =="
echo "documento inicial" > documentos/teste.txt

echo "== Inicializando hashes =="
python3 auditoria/monitor.py --init

echo "== Criando usuario de teste =="
python3 - <<'PY'
from usuarios.auth import cadastrar_usuario, login

try:
    cadastrar_usuario("administrador", "admin", "senha123")
except ValueError as erro:
    print(f"Aviso: {erro}")

login("administrador", "senha123")
PY

echo "== Alterando documento =="
echo "documento alterado" > documentos/teste.txt

echo "== Verificando integridade =="
python3 auditoria/monitor.py --check || true

echo "== Executando backup criptografado =="
SECURECHAIN_BACKUP_PASSWORD="senha-forte" ./backup/backup.sh

echo "== Validando blockchain =="
python3 blockchain/blockchain.py --validate

echo "== Resultado: blockchain =="
cat blockchain/chain.json

echo "== Resultado: logs =="
cat logs/acessos.log
cat logs/backup.log

echo "== Backups gerados =="
ls -lh backup/arquivos/