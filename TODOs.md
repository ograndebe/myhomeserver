# TODOs

## Setup.py
- [x] Fazer setup.py ler de .env existente quando disponível, evitando perguntas repetitivas

## Traefik
- [x] Adicionar `maxResponseBodySize` no middleware ForwardAuth do Authentik (warning nos logs)

## Authentik
- [x] Bootstrap de admin dá erro se volume persistir (precisa matar volume ou DB já existe)
- [ ] Configurar integração SSO com os serviços
- [ ] Configurar Outpost para Traefik

## Geral
- [ ] Testar acesso externo (com DNS wildcard no Cloudflare apontando para IP público)
- [ ] Documentar fluxo de configuração pós-instalação
