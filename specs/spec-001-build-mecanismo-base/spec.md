# Spec-001 — Mecanismo Base de Build em Shell

> **Status:** draft
> **Backlog:** BACK-001
> **Criado em:** 26/03/2026

---

## 1. Visão Geral

Script `build.sh` que funciona como mecanismo central de build. Verifica a existência de um arquivo `.env`; se existir, usa-o diretamente; caso contrário, solicita interativamente todos os dados necessários ao usuário para construir o `.env`. Após isso, processa templates usando o `.env` e gera os artefatos finais no diretório `build/`.

---

## 2. Critérios de Aceite

- [ ] **CA-01:** `build.sh` detecta se `build/.env` existe
- [ ] **CA-02:** Se `.env` existir, o script prossegue para o passo de processar templates sem solicitar input
- [ ] **CA-03:** Se `.env` não existir, o script solicita interativamente: domínio, email Cloudflare, API token Cloudflare
- [ ] **CA-04:** O `.env` gerado contém todas as variáveis necessárias para os templates (ex: `$DOMAIN`, `$CLOUDFLARE_EMAIL`, `$CLOUDFLARE_API_TOKEN`)
- [ ] **CA-05:** O script cria o diretório `build/` se não existir
- [ ] **CA-06:** O script processa templates (ex: `templates/*.tmpl`) substituindo variáveis de ambiente via `envsubst`
- [ ] **CA-07:** Os artefatos processados são salvos em `build/` com a mesma estrutura de diretórios dos templates
- [ ] **CA-08:** O script é idempotente: executar múltiplas vezes não causa erros
- [ ] **CA-09:** O script funciona em bash puro, sem dependências externas além de `envsubst` (presente no pacote `gettext-base`)

---

## 3. Fora de Escopo

- Execução de containers Docker
- Validação de credenciais Cloudflare
- Deploy dos artefatos para o servidor
- Geração de certificados SSL
- Criação de templates específicos (isso será coberto pelo BACK-002)

---

## 4. Dependências

- **Depende de:** Nenhuma
- **Premissas assumidas:** 
  - `envsubst` está disponível no sistema (ou será alertado para instalar)
  - Estrutura de templates existirá em `templates/` (BACK-002 criará)

---

## 5. Notas Técnicas

### Fluxo do Script

```
1. Verificar se build/.env existe
   ├── SIM → Carregar variáveis do .env → Ir para passo 3
   └── NÃO → Ir para passo 2

2. Solicitar dados interativamente:
   - DOMAIN (ex: example.com)
   - CLOUDFLARE_EMAIL
   - CLOUDFLARE_API_TOKEN
   - Confirmar criação do .env

3. Criar diretório build/ se necessário

4. Processar templates em templates/:
   - Para cada *.tmpl, executar envsubst < arquivo.tmpl > build/arquivo

5. Exibir mensagem de sucesso com lista de artefatos gerados
```

### Variáveis de Ambiente Obrigatórias no .env

```bash
DOMAIN=example.com
CLOUDFLARE_EMAIL=admin@example.com
CLOUDFLARE_API_TOKEN=xxxxxxxxxxxxxxxxxxxxx
```

### Estrutura de Diretórios Esperada

```
templates/                      # Entrada (criado pelo BACK-002)
├── docker-compose.yml.tmpl
├── traefik/traefik.yml.tmpl
└── adguard/AdGuardHome.yaml.tmpl

build/                         # Saída
├── .env
├── docker-compose.yml
├── traefik/traefik.yml
└── adguard/AdGuardHome.yaml
```

---

## 6. Checklist de Aprovação da Spec

- [ ] Todos os critérios de aceite são verificáveis e binários
- [ ] Casos de erro e edge cases foram considerados
- [ ] A spec não viola nenhuma premissa do context.md
- [ ] Escopo claro e sem ambiguidades
- [ ] Artefatos gerados estão limitados à pasta build/
- [ ] Critérios de sucesso da spec estão alinhados com PROJECT.md
