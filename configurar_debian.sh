#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Execute como root: sudo ./configurar_debian.sh"
  exit 1
fi

create_group() {
  local group="$1"
  getent group "${group}" >/dev/null || groupadd "${group}"
}

create_user() {
  local user="$1"
  local group="$2"
  if ! id "${user}" >/dev/null 2>&1; then
    useradd --create-home --shell /bin/bash "${user}"
    passwd -l "${user}" >/dev/null
  fi
  usermod -a -G "${group}" "${user}"
}

create_group securechain_admin
create_group securechain_analista
create_group securechain_visitante

create_user administrador securechain_admin
create_user analista securechain_analista
create_user visitante securechain_visitante

chown -R administrador:securechain_admin "${ROOT_DIR}"
chmod 0750 "${ROOT_DIR}"

find "${ROOT_DIR}" -type d -exec chmod 0750 {} +
find "${ROOT_DIR}" -type f -exec chmod 0640 {} +
chmod 0750 "${ROOT_DIR}/backup/backup.sh" "${ROOT_DIR}/configurar_debian.sh"

setfacl -R -m g:securechain_analista:r-X "${ROOT_DIR}"
setfacl -R -m g:securechain_visitante:--- "${ROOT_DIR}"
setfacl -R -m g:securechain_visitante:r-X "${ROOT_DIR}/auditoria/relatorios"
setfacl -R -d -m g:securechain_visitante:r-X "${ROOT_DIR}/auditoria/relatorios"

echo "Usuarios, grupos e permissoes configurados."
echo "Defina senhas do sistema com: passwd administrador|analista|visitante"
