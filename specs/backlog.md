# Backlog

> Última atualização: 26/03/2026

---

## 🔲 Pendente

- [ ] **BACK-001** Mecanismo base de build em shell (build.sh)
  - Descrição: Script principal que verifica a existência de .env. Se existir, usa-o; se não, solicita interativamente todos os dados necessários (domínio, credenciais Cloudflare, etc.) para construir o .env. Este arquivo é então usado para processar todos os templates e gerar os artefatos finais em build/.
  - Spec: —
  - Prioridade: alta

- [ ] **BACK-002** Adaptar primeira versão ao novo mecanismo de build
  - Descrição: Converter os templates existentes (docker-compose.yml, traefik.yml, AdGuardHome.yaml) em templates com variáveis de ambiente (substituições via envsubst ou similar). Garantir que o build.sh processe esses templates usando o .env gerado e gere os artefatos em build/.
  - Depende de: BACK-001
  - Spec: —
  - Prioridade: alta

- [ ] **BACK-003** Headscale como VPN (substituir WireGuard)
  - Descrição: Substituir WireGuard por Headscale (servidor open-source de controle para WireGuard). Gerar configuração do Headscale via template, incluindo definição de namespace, usuários (devices) e regras de ACL. Usar o cliente oficial Tailcale para conexão dos dispositivos.
  - Spec: —
  - Prioridade: média

- [ ] **BACK-004** Authentik como Identity Provider (IdP)
  - Descrição: Adicionar Authentik como provedor de identidade centralizado (SSO/SAML/OIDC). Configurar aplicações e provedores para integração com Traefik (autenticação forward auth) e outros serviços do home server.
  - Spec: —
  - Prioridade: média

---

## 🔄 Em Progresso

---

## ✅ Concluído

