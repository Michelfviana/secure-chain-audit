# Relatorio Tecnico - SecureChain Audit

## 1. Contexto da prova pratica

O projeto SecureChain Audit atende ao enunciado da prova pratica **SecureChain Audit - Plataforma de Auditoria Baseada em Blockchain**, que exige uma solucao em Debian 13 com Python 3, Bash Script e Git para controle de usuarios, monitoramento de integridade, blockchain de auditoria, criptografia, backup seguro, auditoria da VM e evidencias em relatorio e video.

Os artefatos de demonstracao foram adicionados ao projeto:

- Video demonstrativo: [WhatsApp Video 2026-06-13 at 10.50.43.mp4](evidencias/WhatsApp%20Video%202026-06-13%20at%2010.50.43.mp4)
- Screenshots extraidos: [pasta evidencias/screenshots](evidencias/screenshots/)
- Folha de contato dos screenshots: [screenshots_contato.png](evidencias/screenshots_contato.png)

## 2. Arquitetura da solucao

A solucao foi organizada em modulos independentes, seguindo a estrutura solicitada no PDF da prova:

| Diretorio/arquivo | Responsabilidade |
|---|---|
| `usuarios/auth.py` | Cadastro, login, sessao, perfis e autorizacao por permissao |
| `blockchain/blockchain.py` | Registro de eventos, encadeamento de blocos e validacao da cadeia |
| `auditoria/monitor.py` | Calculo SHA-256 dos documentos e deteccao de inclusao, alteracao e exclusao |
| `auditoria/auditor.py` | Coleta de `who`, `last -n 30`, `ss -tulpn` e `ip a` |
| `auditoria/analise_seguranca.sh` | Analise etica local com `ss`, `nmap` e revisao de permissoes |
| `backup/backup.sh` | Compactacao de `documentos/`, criptografia AES e log de backup |
| `configurar_debian.sh` | Criacao de usuarios Linux, grupos, permissoes e ACLs |
| `tests/test_securechain.py` | Testes automatizados dos fluxos criticos |

Todos os eventos relevantes convergem para `blockchain/chain.json`, que funciona como trilha de auditoria persistente. Os relatorios e logs locais facilitam consulta operacional, enquanto os hashes encadeados tornam adulteracoes detectaveis.

## 3. RF01 - Controle de usuarios no sistema operacional

O script `configurar_debian.sh` cria os grupos `securechain_admin`, `securechain_analista` e `securechain_visitante`, alem das contas Linux:

- `administrador`: proprietario do projeto e acesso total;
- `analista`: leitura e execucao dos modulos;
- `visitante`: acesso restrito, com leitura somente em `auditoria/relatorios`.

O menor privilegio foi aplicado com `chown`, `chmod` e `setfacl`. O diretorio raiz fica com modo `0750`, arquivos com `0640`, scripts executaveis com `0750` e ACLs especificas liberam somente o necessario para cada grupo. A segregacao de funcoes impede que o visitante acesse codigo, backups ou documentos monitorados.

Evidencias relacionadas:

| Evidencia | Descricao |
|---|---|
| <img src="evidencias/screenshots/Screenshot_20260613_091342.png" width="420"> | Instalacao de dependencias no Debian com `apt`, incluindo OpenSSL, ACL, nmap e Git. |
| <img src="evidencias/screenshots/Screenshot_20260613_091723.png" width="420"> | Execucao de `configurar_debian.sh` e validacao dos usuarios com `id`. |
| <img src="evidencias/screenshots/Screenshot_20260613_092118.png" width="420"> | Conferencia de usuarios, grupos e permissoes do projeto. |
| <img src="evidencias/screenshots/Screenshot_20260613_093658.png" width="420"> | Teste de restricao de acesso entre usuarios Linux. |
| <img src="evidencias/screenshots/Screenshot_20260613_093712.png" width="420"> | Validacao final de permissoes, usuarios e arquivos de relatorio. |

## 4. RF02 - Sistema de autenticacao em Python

O modulo `usuarios/auth.py` implementa cadastro, login, logout, sessao ativa e autorizacao por perfil. O primeiro usuario pode ser criado sem sessao para inicializacao do ambiente; os proximos cadastros exigem permissao `manage_users`.

As permissoes da aplicacao sao separadas por perfil:

| Recurso | admin | analista | visitante |
|---|---:|---:|---:|
| Gerenciar usuarios | sim | nao | nao |
| Inicializar/verificar hashes | sim | sim | nao |
| Backup e auditoria | sim | sim | nao |
| Ler blockchain | sim | sim | sim |
| Ler relatorios | sim | sim | sim |
| Registrar evento manual | sim | nao | nao |

Senhas nao sao armazenadas em texto puro. O projeto usa PBKDF2-HMAC-SHA256 com salt aleatorio de 16 bytes, 200.000 iteracoes e comparacao com `hmac.compare_digest`. Cada login bem-sucedido, tentativa negada, criacao ou remocao de usuario gera evento na blockchain.

Evidencias relacionadas:

| Evidencia | Descricao |
|---|---|
| <img src="evidencias/screenshots/Screenshot_20260613_091919.png" width="420"> | Definicao de senha do usuario administrador no sistema operacional. |
| <img src="evidencias/screenshots/Screenshot_20260613_092320.png" width="420"> | Criacao de usuario e login no sistema SecureChain. |
| <img src="evidencias/screenshots/Screenshot_20260613_092458.png" width="420"> | Menu da aplicacao e validacao de senha no cadastro. |
| <img src="evidencias/screenshots/Screenshot_20260613_092653.png" width="420"> | Cadastro de usuario visitante e retorno ao menu. |
| <img src="evidencias/screenshots/Screenshot_20260613_092707.png" width="420"> | Login de usuario e exibicao de opcoes conforme perfil. |
| <img src="evidencias/screenshots/Screenshot_20260613_092716.png" width="420"> | Encerramento de sessao e novo fluxo de autenticacao. |
| <img src="evidencias/screenshots/Screenshot_20260613_092759.png" width="420"> | Sessao ativa, criacao de usuario e controle de perfil. |
| <img src="evidencias/screenshots/Screenshot_20260613_092917.png" width="420"> | Remocao de usuario e atualizacao do estado da aplicacao. |

## 5. RF03 - Monitoramento de integridade de arquivos

O diretorio `documentos/` e monitorado por `auditoria/monitor.py`. Ao executar `--init`, o sistema calcula SHA-256 de todos os arquivos e salva a referencia em `auditoria/hashes_documentos.json`. Ao executar `--check`, o estado atual e comparado com a referencia.

O monitor detecta e registra:

- inclusao de arquivo;
- alteracao de conteudo;
- exclusao de arquivo.

Quando ha divergencia, o terminal exibe alerta e cada inconsistencia vira um bloco individual na blockchain. A opcao `--update-reference` permite atualizar a linha de base apos uma verificacao controlada.

Evidencias relacionadas:

| Evidencia | Descricao |
|---|---|
| <img src="evidencias/screenshots/Screenshot_20260613_092145.png" width="420"> | Testes automatizados cobrindo inclusao, alteracao e exclusao de documentos. |
| <img src="evidencias/screenshots/Screenshot_20260613_092949.png" width="420"> | Inicializacao/verificacao da referencia de hashes dos documentos. |
| <img src="evidencias/screenshots/Screenshot_20260613_093215.png" width="420"> | Eventos de monitoramento registrados junto dos demais eventos da blockchain. |

## 6. RF04 e RF07 - Blockchain de auditoria e validacao

Cada evento relevante gera um bloco em `blockchain/chain.json`. Cada bloco contem:

| Campo | Finalidade |
|---|---|
| `id` | identificador sequencial unico |
| `timestamp` | data e hora em ISO 8601 |
| `evento` | descricao textual do evento |
| `hash_anterior` | hash SHA-256 do bloco anterior |
| `hash_atual` | hash SHA-256 calculado sobre os campos do bloco |

Antes de registrar um novo evento, `registrar_evento` valida a cadeia atual. Se houver JSON invalido, hash recalculado diferente, quebra de encadeamento, ID fora de sequencia, campo obrigatorio ausente ou timestamp invalido, o sistema bloqueia novos registros e mostra alerta.

A gravacao da cadeia e atomica, usando arquivo temporario e `os.replace`, e ha bloqueio de arquivo com `fcntl.flock` para reduzir risco de escrita concorrente. Os testes tambem validam preservacao de eventos concorrentes.

Evidencias relacionadas:

| Evidencia | Descricao |
|---|---|
| <img src="evidencias/screenshots/Screenshot_20260613_092145.png" width="420"> | Testes de adulteracao, JSON invalido, autorizacao e concorrencia da blockchain. |
| <img src="evidencias/screenshots/Screenshot_20260613_093108.png" width="420"> | Validacao da blockchain integra pelo menu da aplicacao. |
| <img src="evidencias/screenshots/Screenshot_20260613_093126.png" width="420"> | Listagem de eventos registrados na blockchain. |

## 7. RF05 - Backup seguro automatizado

O script `backup/backup.sh` compacta o diretorio `documentos/` em `.tar.gz`, criptografa o arquivo com OpenSSL e remove o temporario nao criptografado por `trap`.

O algoritmo escolhido foi **AES-256-CBC com salt e PBKDF2**, por estar disponivel nativamente no Debian via OpenSSL, ser eficiente para arquivos e adequado para criptografia simetrica de backups. O projeto evita expor a senha na linha de comando ao usar `-pass fd:3`.

Limitacao tecnica: CBC nao fornece autenticacao integrada. Como melhoria, recomenda-se migrar para AES-256-GCM ou adicionar HMAC para detectar adulteracao do backup criptografado.

Evidencias relacionadas:

| Evidencia | Descricao |
|---|---|
| <img src="evidencias/screenshots/Screenshot_20260613_092842.png" width="420"> | Execucao de backup com senha para criptografia. |
| <img src="evidencias/screenshots/Screenshot_20260613_093013.png" width="420"> | Backup criptografado gerado em `backup/arquivos`. |
| <img src="evidencias/screenshots/Screenshot_20260613_093037.png" width="420"> | Registro local do backup e status da operacao. |
| <img src="evidencias/screenshots/Screenshot_20260613_093215.png" width="420"> | Evento de backup registrado na blockchain. |

## 8. RF06 - Auditoria do sistema operacional

O modulo `auditoria/auditor.py` gera relatorios datados em `auditoria/relatorios/`, coletando:

- `who`: usuarios conectados;
- `last -n 30`: historico recente de logins;
- `ss -tulpn`: portas e servicos em escuta;
- `ip a`: interfaces de rede e enderecos IP.

O script `auditoria/analise_seguranca.sh` complementa a auditoria com `nmap -sV --top-ports 100 localhost`, listagem de portas com `ss` e revisao de permissoes do projeto com `find`.

Evidencias relacionadas:

| Evidencia | Descricao |
|---|---|
| <img src="evidencias/screenshots/Screenshot_20260613_093054.png" width="420"> | Relatorio de auditoria do sistema operacional gerado. |
| <img src="evidencias/screenshots/Screenshot_20260613_093108.png" width="420"> | Listagem de relatorios gerados em `auditoria/relatorios`. |
| <img src="evidencias/screenshots/Screenshot_20260613_093243.png" width="420"> | Menu de auditoria e execucao de funcionalidades administrativas. |
| <img src="evidencias/screenshots/Screenshot_20260613_093712.png" width="420"> | Saida de analise de permissoes e arquivos de relatorio. |

## 9. Criptografia aplicada

| Contexto | Mecanismo | Justificativa |
|---|---|---|
| Senhas | PBKDF2-HMAC-SHA256, salt aleatorio e 200.000 iteracoes | Evita texto puro, dificulta tabelas pre-calculadas e aumenta custo de forca bruta |
| Integridade de arquivos | SHA-256 | Permite detectar alteracoes nos documentos monitorados |
| Integridade da blockchain | SHA-256 encadeado | Torna adulteracoes detectaveis ao recalcular os blocos |
| Backups | AES-256-CBC com salt e PBKDF2 via OpenSSL | Criptografia simetrica eficiente e disponivel no Debian |

## 10. Zero Trust Security

1. **Verificacao de identidade:** cada acesso exige login com senha derivada por PBKDF2 e sessao valida. A sessao expira apos oito horas.
2. **Controle e auditoria de permissoes:** cada acao protegida chama `require_permission`, que recalcula a autorizacao a partir do perfil ativo. Negativas de acesso tambem sao registradas na blockchain.
3. **Menor privilegio na pratica:** ha duas camadas de restricao: ACLs/grupos no Linux e matriz de permissoes na aplicacao.
4. **Registro imutavel de acoes:** logins, negacoes, criacao/remocao de usuarios, alteracoes de arquivos, backups e auditorias sao registrados em blocos encadeados.

Limitacao: `chain.json` ainda e um arquivo local. Para maior imutabilidade operacional, recomenda-se copia append-only em host remoto, assinatura digital periodica ou armazenamento WORM.

Evidencias relacionadas:

| Evidencia | Descricao |
|---|---|
| <img src="evidencias/screenshots/Screenshot_20260613_092707.png" width="420"> | Login e exibicao de opcoes conforme o perfil ativo. |
| <img src="evidencias/screenshots/Screenshot_20260613_093658.png" width="420"> | Restricao real de acesso no sistema operacional para usuario sem privilegio. |
| <img src="evidencias/screenshots/Screenshot_20260613_093126.png" width="420"> | Acoes registradas em trilha encadeada e verificavel. |

## 11. Hacking etico - analise da VM

A analise da propria VM deve ser registrada com os relatorios gerados por `auditoria/analise_seguranca.sh` e `auditoria/auditor.py`. Com base no que o projeto coleta, a matriz de achados deve ser preenchida apos a execucao final no Debian:

| Achado | Evidencia | Risco | Correcao aplicada/proposta |
|---|---|---|---|
| Portas/servicos em escuta | Relatorio de `ss -tulpn` e `nmap` | Exposicao indevida de servicos | Desativar servico desnecessario, restringir interface ou aplicar firewall |
| Permissao excessiva | Saida de `find` e ACLs | Leitura ou alteracao por usuario indevido | Ajustar `chmod`, `chown`, grupos e `setfacl` |
| Pacote ausente/desatualizado | Saida de instalacao e auditoria | Falha de execucao ou risco conhecido | Instalar/atualizar pacotes com `apt` |
| Logs locais alteraveis | Arquivos em `logs/` | Evidencia local pode ser apagada | Registrar tambem na blockchain e replicar para host remoto |

Nao se deve declarar uma vulnerabilidade como corrigida sem repetir o teste e guardar a evidencia correspondente.

Evidencias relacionadas:

| Evidencia | Descricao |
|---|---|
| <img src="evidencias/screenshots/Screenshot_20260613_091342.png" width="420"> | Instalacao das ferramentas de apoio para auditoria, incluindo `nmap`. |
| <img src="evidencias/screenshots/Screenshot_20260613_093054.png" width="420"> | Geracao de relatorio com dados da VM. |
| <img src="evidencias/screenshots/Screenshot_20260613_093712.png" width="420"> | Revisao de permissoes usada como parte da analise de seguranca. |

## 12. Engenharia de software segura

| Falha ou vulnerabilidade | Mitigacao no projeto |
|---|---|
| Senhas em texto puro | PBKDF2-HMAC-SHA256, salt aleatorio e arquivo `users.json` restrito |
| Permissoes excessivas | Grupos Linux, `chmod`, `chown`, ACLs e matriz de perfis |
| Ausencia de logs de eventos | Logs locais e blockchain persistente |
| Ausencia de validacao de entrada | Perfis enumerados, senha minima, evento nao vazio e validacao JSON |
| Corrupcao silenciosa da blockchain | Validacao recalcula hashes e bloqueia novos registros inconsistentes |
| Vazamento de senha do backup | Senha lida de forma interativa ou por variavel protegida e enviada ao OpenSSL por descritor |
| Arquivo parcial apos falha | Gravacao atomica da blockchain e remocao do `.tar.gz` temporario |
| Remocao indevida do ultimo admin | Regra impede excluir o ultimo usuario com perfil `admin` |

## 13. Testes e comandos de evidencia

Os testes automatizados cobrem adulteracao da blockchain, JSON invalido, concorrencia, autenticacao, autorizacao, monitoramento de documentos e protecao do ultimo administrador.

Comandos usados ou recomendados para evidenciar a entrega:

```bash
sudo ./configurar_debian.sh
id administrador
id analista
id visitante
getfacl auditoria/relatorios
find . -maxdepth 2 -printf '%M %u:%g %p\n'

python3 usuarios/auth.py create-user administrador admin
python3 usuarios/auth.py login administrador
python3 menu.py

python3 auditoria/monitor.py --init
python3 auditoria/monitor.py --check
python3 blockchain/blockchain.py --validate
python3 auditoria/auditor.py
./auditoria/analise_seguranca.sh
./backup/backup.sh

python3 -m unittest discover -s tests -v
bash teste_securechain.sh
```

## 14. Video demonstrativo

O video em MP4 demonstra a VM Debian em execucao e os fluxos principais pedidos no enunciado: login, geracao de bloco, monitoramento de arquivo, validacao da blockchain e backup criptografado.

[Abrir video demonstrativo](evidencias/WhatsApp%20Video%202026-06-13%20at%2010.50.43.mp4)

## 15. Limitacoes e melhorias futuras

- Migrar o backup para AES-256-GCM ou adicionar HMAC aos arquivos criptografados.
- Replicar a blockchain para armazenamento remoto append-only ou WORM.
- Adicionar MFA e bloqueio progressivo apos falhas de login.
- Integrar `systemd` timers para monitoramento e backup periodico.
- Assinar digitalmente relatorios de auditoria.
- Exportar metricas e alertas para monitoramento centralizado.
- Formalizar no README a divisao de tarefas da equipe e relacionar commits aos requisitos da prova.
