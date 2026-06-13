# SecureChain Audit

Plataforma de auditoria para Debian 13, implementada em Python 3 e Bash. O projeto combina autenticação, controle por perfil, monitoramento SHA-256, blockchain persistente, backup AES-256 e relatórios do sistema operacional.

## Requisitos

- Debian 13 e Python 3;
- `openssl`, `tar`, `iproute2`, `util-linux` e `acl`;
- `nmap` para a análise de hacking ético;
- privilégios de `root` apenas para criar usuários e aplicar permissões Linux.

```bash
sudo apt update
sudo apt install openssl tar iproute2 util-linux acl nmap
chmod +x backup/backup.sh configurar_debian.sh auditoria/analise_seguranca.sh
```

## Configuração Linux (RF01)

O script idempotente cria os usuários `administrador`, `analista` e `visitante`, grupos separados e ACLs de menor privilégio:

```bash
sudo ./configurar_debian.sh
sudo passwd administrador
sudo passwd analista
sudo passwd visitante
```

- `administrador`: proprietário e acesso total ao projeto;
- `analista`: leitura e execução dos módulos;
- `visitante`: leitura somente de `auditoria/relatorios`;
- senhas das contas Linux não são definidas pelo script nem armazenadas no projeto.

## Uso

O primeiro usuário da aplicação pode ser criado sem sessão para permitir a inicialização. Os cadastros seguintes exigem login de administrador.

```bash
python3 usuarios/auth.py create-user administrador admin
python3 usuarios/auth.py login administrador
python3 menu.py
```

Permissões da aplicação:

| Recurso | admin | analista | visitante |
|---|---:|---:|---:|
| Gerenciar usuários | sim | não | não |
| Inicializar/verificar hashes | sim | sim | não |
| Backup e auditoria | sim | sim | não |
| Ler blockchain | sim | sim | sim |
| Ler relatórios | sim | sim | sim |
| Registrar evento manual | sim | não | não |

As senhas usam PBKDF2-HMAC-SHA256, salt aleatório e 200.000 iterações. A sessão expira após oito horas.

## Monitoramento (RF03)

```bash
python3 auditoria/monitor.py --init
python3 auditoria/monitor.py --check
python3 auditoria/monitor.py --watch --interval 10
python3 auditoria/monitor.py --check --update-reference
```

Inclusões, alterações e exclusões em `documentos/` geram alertas e blocos.

## Blockchain (RF04 e RF07)

```bash
python3 blockchain/blockchain.py --event "Evento administrativo"
python3 blockchain/blockchain.py --validate
```

Cada bloco contém `id`, timestamp ISO 8601, evento, hash anterior e hash atual. A gravação é atômica e protegida por bloqueio de arquivo contra processos concorrentes. Eventos novos são recusados caso a cadeia esteja corrompida ou malformada.

## Backup (RF05)

```bash
./backup/backup.sh
```

O script compacta `documentos/`, criptografa com AES-256-CBC, salt e PBKDF2, remove o `.tar.gz` temporário, restringe as permissões com `umask 077` e registra tamanho/status no log e na blockchain. Para automação, prefira um arquivo de credenciais protegido ou um gerenciador de segredos; não grave a senha diretamente no `crontab`.

Restauração:

```bash
openssl enc -d -aes-256-cbc -pbkdf2 -in backup/arquivos/ARQUIVO.enc -out /tmp/documentos.tar.gz
tar -xzf /tmp/documentos.tar.gz -C /tmp
```

## Auditoria (RF06 e hacking ético)

Com uma sessão `admin` ou `analista` ativa:

```bash
python3 auditoria/auditor.py
./auditoria/analise_seguranca.sh
```

O primeiro comando coleta `who`, `last -n 30`, `ss -tulpn` e `ip a`. O segundo executa `nmap` local, coleta portas e revisa permissões. Os resultados ficam em `auditoria/relatorios/`.

## Testes

```bash
python3 -m unittest discover -s tests -v
bash teste_securechain.sh
```

Os testes Python são isolados em diretórios temporários. O teste Bash é demonstrativo e altera os dados locais do projeto.

## Arquivos gerados

- `blockchain/chain.json`: trilha encadeada;
- `usuarios/users.json`: usuários e hashes de senha;
- `usuarios/session.json`: sessão ativa, ignorada pelo Git;
- `auditoria/hashes_documentos.json`: referência de integridade;
- `auditoria/relatorios/`: relatórios datados;
- `backup/arquivos/`: backups criptografados;
- `logs/acessos.log` e `logs/backup.log`: logs locais.

Consulte `RELATORIO_TECNICO.md` para arquitetura, Zero Trust, riscos e evidências.
