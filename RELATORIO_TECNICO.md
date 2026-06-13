# Relatório Técnico - SecureChain Audit

## 1. Arquitetura

A solução é dividida em autenticação (`usuarios/auth.py`), blockchain (`blockchain/blockchain.py`), integridade (`auditoria/monitor.py`), auditoria do sistema (`auditoria/auditor.py`) e backup (`backup/backup.sh`). Todos os eventos relevantes convergem para `chain.json`. Os relatórios e logs locais facilitam consulta, enquanto os hashes encadeados tornam adulterações detectáveis.

## 2. Controle de acesso e segregação

O script `configurar_debian.sh` cria três contas e grupos Linux. O administrador é proprietário; o analista recebe leitura/execução; o visitante recebe somente leitura dos relatórios. ACLs evitam ampliar permissões para outros usuários. Na aplicação, uma matriz de permissões valida a sessão antes de cada ação do menu.

O script deve ser executado e fotografado na VM Debian 13. Evidências recomendadas:

```bash
id administrador
id analista
id visitante
getfacl auditoria/relatorios
find . -maxdepth 2 -printf '%M %u:%g %p\n'
```

## 3. Criptografia

Senhas usam PBKDF2-HMAC-SHA256 com salt aleatório e 200.000 iterações. O salt impede tabelas pré-calculadas e as iterações aumentam o custo de força bruta. Comparações usam `hmac.compare_digest`.

Arquivos e blocos usam SHA-256 por ser uma função amplamente suportada, resistente a colisões para este contexto e adequada à detecção de alterações.

Backups usam AES-256-CBC via OpenSSL, com salt e PBKDF2. AES é eficiente em arquivos grandes e disponível no Debian. O modo CBC não fornece autenticação integrada; uma evolução recomendada é AES-256-GCM ou adicionar HMAC ao backup.

## 4. Blockchain e integridade

Cada bloco possui identificador sequencial, timestamp ISO 8601, evento, hash anterior e hash atual. A validação recalcula cada hash, verifica o encadeamento, IDs, campos obrigatórios e timestamps. JSON inválido gera alerta e bloqueia novos registros, evitando substituir evidências corrompidas.

O monitor percorre `documentos/`, calcula SHA-256 e compara com a referência. Inclusões, exclusões e alterações são exibidas e registradas individualmente.

## 5. Zero Trust

1. A identidade é verificada por usuário, senha derivada com salt e sessão temporária.
2. A autorização é recalculada em cada ação protegida por `require_permission`; tentativas negadas também geram bloco.
3. O menor privilégio existe em duas camadas: ACLs Linux e matriz de perfis da aplicação.
4. Login, negação, usuário, arquivo, backup e auditoria são registrados na cadeia.

Uma limitação é que `chain.json` continua sendo um arquivo local. Para maior imutabilidade, recomenda-se cópia somente anexável em host remoto, assinatura digital periódica ou armazenamento WORM.

## 6. Auditoria e análise da VM

`auditoria/auditor.py` coleta usuários conectados, histórico de login, portas/serviços e interfaces de rede. `auditoria/analise_seguranca.sh` executa `nmap`, `ss` e revisão de permissões.

Esta seção deve ser preenchida após executar os scripts na VM:

| Achado | Evidência | Risco | Correção aplicada/proposta |
|---|---|---|---|
| Porta/serviço exposto | preencher | preencher | desativar serviço, firewall ou restringir interface |
| Permissão excessiva | preencher | preencher | corrigir proprietário, modo ou ACL |
| Pacote desatualizado | preencher | preencher | aplicar atualização de segurança |

Não se deve declarar que uma vulnerabilidade foi corrigida sem repetir o teste e guardar a evidência.

## 7. Engenharia de software segura

| Falha | Mitigação |
|---|---|
| Senhas em texto puro | PBKDF2-HMAC-SHA256, salt aleatório e arquivo restrito |
| Permissões excessivas | grupos, `chmod`, proprietário e ACLs |
| Ausência de logs | logs locais mais blockchain |
| Entrada inválida | perfis enumerados, senha mínima, evento não vazio e validação JSON |
| Corrupção silenciosa | cadeia inválida bloqueia novos registros |
| Vazamento da senha do backup | senha não aparece nos argumentos do processo |
| Arquivo parcial após falha | gravação atômica da blockchain e limpeza do arquivo temporário |

## 8. Backup e recuperação

O backup registra data, nome, tamanho e status. O `.tar.gz` sem criptografia é removido por `trap`, inclusive em falhas. A senha deve vir de entrada interativa ou de mecanismo de segredos protegido. A equipe deve demonstrar também uma restauração em diretório temporário.

## 9. Testes e evidências

Os testes automatizados cobrem adulteração da blockchain, JSON inválido, autenticação/autorização, inclusão/alteração/exclusão de documentos e proteção do último administrador.

Comandos de evidência:

```bash
python3 -m unittest discover -s tests -v
python3 blockchain/blockchain.py --validate
python3 auditoria/auditor.py
./backup/backup.sh
```

Inserir no PDF final capturas dos comandos, do alerta de integridade, de uma validação bem-sucedida e de um teste controlado de corrupção em uma cópia da cadeia.

## 10. Limitações e melhorias

- substituir o bloqueio local por coordenação distribuída caso a solução use vários hosts;
- usar AES-GCM ou HMAC para autenticar o backup;
- armazenar a trilha em sistema remoto/WORM;
- adicionar MFA e bloqueio progressivo após falhas de login;
- integrar `systemd` timers para monitoramento e backup;
- assinar relatórios e exportar métricas para monitoramento central.
