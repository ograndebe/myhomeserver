# Fix-003 — AdGuard Home crash: YAML bind_hosts e permissões do arquivo

> **Status:** done
> **Spec original:** Feature base (AdGuard Home — serviço obrigatório do projeto)
> **Sintoma:** AdGuard Home não inicia por erro de parse YAML (`bind_hosts` é seq mas deveria ser string `bind_host`) e arquivo gerado com permissão `root:root 600` impede leitura pelo container.
> **Backlog:** [BACK-006](../backlog.md)
> **Criado em:** 2026-05-07

---

## 1. Sintoma Relatado

O container AdGuard Home falha ao iniciar com dois erros combinados:

1. **Erro de parse YAML** — O template `templates/adguard/AdGuardHome.yaml.j2` gera na linha 20-21:
   ```yaml
   dns:
     bind_hosts:
       - 0.0.0.0
   ```
   O AdGuard Home espera `bind_host` (string), não `bind_hosts` (sequência). Isso causa erro de parse na linha 21.

2. **Permissão de arquivo** — O arquivo `output/adguard/AdGuardHome.yaml` é gerado via `write_text()` no `setup.py` (linha 539), herdando o umask do processo. Quando executado como root (ou com umask restritivo), o arquivo fica com permissão `root:root 600`, impedindo que o container AdGuard (que roda como usuário não-root) leia sua própria configuração.

**Como reproduzir:**
1. Executar `./setup.py` (especialmente com sudo ou umask restritivo)
2. Executar `docker compose -f output/docker-compose.yml up -d adguard`
3. Observar logs: `docker compose logs adguard`

**Evidência:** Erro de parse YAML no log do container + `Permission denied` ao ler `AdGuardHome.yaml`.

---

## 2. Comportamento Esperado

- O arquivo `AdGuardHome.yaml` deve usar a chave correta `bind_host: "0.0.0.0"` (string, não sequência)
- O arquivo gerado deve ter permissões legíveis pelo container (mínimo `644` ou `640` com grupo adequado)
- O container AdGuard Home deve iniciar sem erros de parse ou permissão

---

## 3. Fora de Escopo

- Alterar outras configurações do AdGuard Home além de `bind_host`
- Modificar permissões de outros arquivos gerados (apenas `AdGuardHome.yaml` nesta correção)
- Reescrever a lógica de geração de templates como um todo

---

## 4. Análise de Impacto

- **Escopo do bug:** Apenas o template `AdGuardHome.yaml.j2` e a função `render_templates()` no `setup.py`
- **Risco de regressão:** baixo — a correção é pontual: trocar `bind_hosts` por `bind_host` e garantir permissões adequadas no arquivo gerado
- **Serviços impactados:** AdGuard Home (DNS local). Sem AdGuard, resolução `*.domain` falha, afetando todos os serviços que dependem de DNS interno

---

## 5. Critérios de Aceite da Correção

- [ ] **CA-01:** `AdGuardHome.yaml` gerado usa `bind_host: "0.0.0.0"` (string) ao invés de `bind_hosts:` (sequência)
- [ ] **CA-02:** Arquivo `AdGuardHome.yaml` gerado tem permissões `644` (ou mais abertas), legível por qualquer usuário
- [ ] **CA-03:** `./setup.py --dry-run` exibe o YAML correto com `bind_host` como string
- [ ] **CA-04:** Re-executar `setup.py` é idempotente — não quebra permissões de arquivo existente

---

## 6. Notas Técnicas

### Causa raiz

1. **`bind_hosts` vs `bind_host`:** O template foi escrito com base em documentação desatualizada ou confusão com outra versão do AdGuard Home. A configuração oficial usa `bind_host` como string única.

2. **Permissões:** `pathlib.Path.write_text()` cria o arquivo com permissões `0o666 & ~umask`. Se o umask for `0o077` (comum em ambientes root), o arquivo fica `600`. A solução é aplicar `chmod(0o644)` explicitamente após a escrita.

### Abordagem de correção

1. Corrigir o template `AdGuardHome.yaml.j2`: trocar `bind_hosts:\n  - 0.0.0.0` por `bind_host: "0.0.0.0"`
2. No `setup.py`, após `write_text()`, aplicar `output_path.chmod(0o644)` para garantir permissões legíveis

### Referência

- AdGuard Home YAML config: `bind_host` é string, não lista (documentação oficial)

---

## 7. Checklist de Aprovação do Fix

- [ ] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [ ] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [ ] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [ ] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [ ] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [ ] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [ ] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes
