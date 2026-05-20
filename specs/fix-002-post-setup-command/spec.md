# Fix-002 — Comando YAML Inválido no post-setup.j2

> **Status:** done
> **Spec original:** [spec-004-jellyfin-arr-stack](../spec-004-jellyfin-arr-stack/spec.md)
> **Sintoma:** `decoding failed: 'services[post-setup].command' invalid command line string` ao executar `docker compose up -d`
> **Criado em:** 2026-05-06

---

## 1. Sintoma Relatado

Ao executar `docker compose up -d` após gerar os arquivos com `./setup.py`, o Docker Compose falha com:

```
decoding failed due to the following error(s):

'services[post-setup].command' invalid command line string
```

**Passos para reproduzir:**
1. Executar `./setup.py` com Jellyfin habilitado
2. Executar `docker compose up -d` no diretório `output/`
3. Erro ocorre imediatamente no parsing do YAML

**Evidência — output gerado (linha 534-535):**
```yaml
    command: >
      sh -c "pip install --quiet requests python-dotenv rich && python3 /app/post_setup.py"  # ── Static Page (Test) ──────
  static-page:
```

O comentário `# ── Static Page...` do template `static-page.j2` é concatenado na mesma linha do comando `sh -c`, invalidando a string de comando.

---

## 2. Comportamento Esperado

O `docker-compose.yml` gerado deve ter o `command` do serviço `post-setup` como uma string YAML válida, sem conteúdo de outros templates na mesma linha. O `docker compose up -d` deve parsear o arquivo sem erros.

---

## 3. Análise de Impacto

- **Escopo do bug:** Serviço `post-setup` no `docker-compose.yml` gerado — impede toda a stack de subir
- **Risco de regressão:** baixo — a correção é isolada ao template `post-setup.j2` e não altera lógica de negócio
- **Serviços impactados:** todos os serviços (o YAML não parseia, nada sobe)

**Causa raiz:** O template `templates/services/post-setup.j2` usa YAML folded style (`>`) para o `command`. Com `trim_blocks=True` no Jinja2, não há newline após o último conteúdo do template. O próximo template incluído (`static-page.j2`) começa com um comentário na primeira linha, que é concatenado diretamente na linha do `sh -c`, invalidando o comando.

---

## 4. Critérios de Aceite da Correção

- [ ] **CA-01:** `./setup.py --dry-run` com Jellyfin habilitado gera `docker-compose.yml` onde o `command` do `post-setup` é uma string YAML válida
- [ ] **CA-02:** `docker compose up -d` parseia o `docker-compose.yml` sem erros de decoding
- [ ] **CA-03:** Nenhuma outra seção do `docker-compose.yml` foi afetada pela correção

---

## 5. Notas Técnicas

**Abordagem de correção:** Substituir o YAML folded style (`>`) por uma lista YAML explícita ou string simples no `command` do `post-setup.j2`. Duas opções:

1. **Lista YAML:** `command: ["sh", "-c", "pip install ... && python3 /app/post_setup.py"]`
2. **String simples:** `command: sh -c "pip install ... && python3 /app/post_setup.py"`

A opção 1 (lista YAML) é mais segura e evita ambiguidades de parsing.

**Templates afetados:**
- `templates/services/post-setup.j2` — corrigir o `command`
- Opcionalmente, adicionar uma linha em branco no final do template para garantir separação

---

## 6. Checklist de Aprovação do Fix

- [ ] Especifica o QUE, não o COMO — descreve comportamento desejado, não detalhes de implementação
- [ ] Critérios de aceite verificáveis — cada CA pode ser testado manualmente ou automaticamente
- [ ] Fora de escopo explícito — delimita claramente o que NÃO será feito
- [ ] Dependências declaradas — lista specs, sistemas ou decisões pendentes
- [ ] Alinhada com context.md — não viola nenhuma premissa inviolável
- [ ] Escopo atômico — uma feature por spec, sem misturar funcionalidades independentes
- [ ] Notas técnicas justificam decisões — explica o "porquê" de escolhas técnicas relevantes
