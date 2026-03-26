# Project Context

> Arquivo central de premissas. consultado em todos os comandos mysdd.
> Última atualização: 25/03/2026

---

## 1. Premissas e Regras Invioláveis

- **Reprodutibilidade total**: executar a ferramenta deve resultar no mesmo estado configurado, independentemente de quantas vezes seja repetida ou em qual servidor seja aplicada
- **Artefatos apenas no build/**: a ferramenta gera configurações, NÃO executa nada direcionado ao servidor (incompatibilidade ARM64 vs x86_64)
- **Idempotência**: executar múltiplas vezes não quebra o sistema
- **Credenciais nunca em git**: credentials.txt, .env com senhas, chaves WireGuard (build/ é descartável)
- **Shell script (bash)**: toda automação de build é feita em bash puro, sem dependência de linguagens interpretadas
- **Docker Compose**: único método de orquestração de serviços no servidor
- **Cloudflare como DNS**: Let's Encrypt wildcard requer DNS Challenge via Cloudflare API

---

## 2. Stack e Convenções

### Tecnologias Confirmadas
- **Automação**: Shell Script (bash)
- **Orquestração**: Docker Compose
- **Reverse Proxy**: Traefik (Let's Encrypt wildcard automático)
- **VPN**: WireGuard (porta 51820/UDP)
- **DNS Local**: AdGuard Home (porta 53/UDP)
- **Certificados**: Let's Encrypt via DNS Challenge (Cloudflare)
- **Armazenamento**: Git para código, build/ descartável para artefatos

### Ambiente
- **Plataforma**: Linux (x86_64/amd64)
- **Função**: Build e execução dos artefatos (home server)
- **Pré-requisitos**: Docker + Docker Compose instalados (não incluso no projeto)
- **Portas**: 443 (HTTPS), 51820/UDP (WireGuard), 53/UDP (AdGuard)

### Estrutura de Diretórios
```
build/                          # Artefatos gerados (descartável)
├── .env                        # Variáveis de ambiente
├── docker-compose.yml          # Orquestração
├── traefik/traefik.yml         # Reverse proxy
├── wireguard/                  # VPN
└── adguard/                    # DNS local

src/                            # Código fonte (opcional)
scripts/                       # Scripts auxiliares
templates/                     # Templates de configuração
```

### Artefatos Sensíveis (nunca commitar)
- `build/credentials.txt`
- `build/wireguard/*.conf`
- `build/.env` (contém senhas)

### Não Escopo
- Provisionamento de hardware/servidor
- Instalação do sistema operacional Ubuntu
- Instalação do Docker e Docker Compose
- Gerenciamento de containers após deploy
- Monitoramento contínuo
- Backup dos dados

---

## 3. Checks Obrigatórios — Spec

- [ ] Todos os critérios de aceite são verificáveis e binários
- [ ] Casos de erro e edge cases foram considerados
- [ ] A spec não viola nenhuma premissa do context.md
- [ ] Escopo claro e sem ambiguidades
- [ ] Artefatos gerados estão limitados à pasta build/
- [ ] Critérios de sucesso da spec estão alinhados com PROJECT.md

---

## 4. Checks Obrigatórios — Plan

- [ ] Cada etapa tem escopo claro e resultado esperado
- [ ] Dependências entre etapas estão mapeadas
- [ ] Nenhuma breaking change não planejada
- [ ] O plano cobre todos os critérios de aceite da spec
- [ ] Não inclui tarefas do "não escopo" do PROJECT.md
- [ ] Validação de sintaxe (shellcheck, yamllint) está prevista

---

## 5. Checks Obrigatórios — Implement

- [ ] Todos os checkboxes do plano foram concluídos
- [ ] Nenhuma premissa do context.md foi violada
- [ ] Sem TODOs críticos pendentes no código
- [ ] Implementação satisfaz os critérios de aceite da spec
- [ ] Credenciais não estão sendo logadas ou commitées
- [ ] Scripts funcionam em bash (sem dependências externas)
