# Fix-001 — Tag inválida da imagem cloudflare-ddns

> **Status:** done
> **Spec original:** [spec-002-cloudflare-ddns](../spec-002-cloudflare-ddns/spec.md)
> **Sintoma:** `manifest for oznu/cloudflare-ddns:3.1.0 not found` ao executar `docker compose up`
> **Criado em:** 2026-05-01

---

## 1. Sintoma Relatado

Ao executar `./post-setup.sh` (ou `docker compose -f output/docker-compose.yml up -d --build`), o Docker falha na pull da imagem `cloudflare-ddns`:

```
Error response from daemon: manifest for oznu/cloudflare-ddns:3.1.0 not found: manifest unknown
```

O container nunca é criado e o script para antes de subir os demais serviços.

**Passos para reproduzir:**
1. Executar `./setup.py` (gera docker-compose.yml com tag `3.1.0`)
2. Executar `./post-setup.sh` ou `docker compose up -d`

**Evidência:** Log do Docker mostrando `manifest unknown` para a tag `3.1.0`.

---

## 2. Comportamento Esperado

O container `cloudflare-ddns` deve ser criado e iniciado com sucesso, mantendo o registro DNS `A` do domínio atualizado.

---

## 3. Análise de Impacto

- **Escopo do bug:** Apenas o serviço `cloudflare-ddns` no docker-compose gerado
- **Risco de regressão:** **Baixo** — a correção é apenas trocar a tag da imagem; a nota técnica da spec original já indicava `latest`
- **Serviços impactados:** Nenhum outro serviço depende do cloudflare-ddns para iniciar

---

## 4. Critérios de Aceite da Correção

- [x] **CA-01:** O `docker compose up -d` consegue pull e iniciar o container `cloudflare-ddns` sem erro de manifest
- [x] **CA-02:** O container `cloudflare-ddns` inicia e permanece rodando (`docker ps` mostra status healthy/running)
- [x] **CA-03:** Nenhuma outra funcionalidade do stack quebrou após a correção

---

## 5. Notas Técnicas

**Causa raiz:** O template `templates/docker-compose.yml.j2` usa a tag `3.1.0` para `oznu/cloudflare-ddns`, que não existe no Docker Hub. A nota técnica da spec-002 (seção "Container cloudflare-ddns") indicava `oznu/cloudflare-ddns:latest` como imagem, mas a implementação usou uma tag versionada inexistente.

**Abordagem de correção:** Trocar a tag `3.1.0` por `latest` no template Jinja2, alinhando com a nota técnica original da spec-002.

**Arquivo a modificar:** `templates/docker-compose.yml.j2`

---

## 6. Checklist de Aprovação do Fix

- [x] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [x] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [x] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [x] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [x] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [x] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [x] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes
