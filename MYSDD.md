# mysdd — Spec Driven Development Kit para OpenCode

## Instalação

Copie a pasta `.opencode/` para a raiz do seu projeto:

```
seu-projeto/
├── .opencode/
│   ├── commands/
│   │   ├── mysdd.createcontext.md
│   │   ├── mysdd.addbacklog.md
│   │   ├── mysdd.createspec.md
│   │   ├── mysdd.createplan.md
│   │   └── mysdd.implement.md
│   └── skills/
│       ├── mysdd-context/SKILL.md
│       ├── mysdd-backlog/SKILL.md
│       ├── mysdd-spec/SKILL.md
│       ├── mysdd-plan/SKILL.md
│       └── mysdd-implement/SKILL.md
└── ... seu projeto
```

## Como usar

Digite `/` no TUI do OpenCode para ver os comandos disponíveis:

| Comando | O que faz |
|---|---|
| `/mysdd.createcontext` | Cria `specs/context.md` com premissas e checks |
| `/mysdd.addbacklog` | Cria/atualiza `specs/backlog.md` |
| `/mysdd.createspec` | Cria `specs/spec-###-nome/spec.md` |
| `/mysdd.createplan` | Cria `specs/spec-###-nome/plan.md` |
| `/mysdd.implement` | Executa o plano etapa a etapa |

Você pode passar contexto diretamente no comando:
```
/mysdd.createspec BACK-001 - sistema de autenticação via OAuth
/mysdd.implement spec-003-oauth
```

## Fluxo recomendado

```
1. /mysdd.createcontext   → define as regras do jogo (faça uma vez)
2. /mysdd.addbacklog      → lista o que precisa ser feito
3. /mysdd.createspec      → detalha uma feature com critérios de aceite
4. /mysdd.createplan      → planeja as etapas de implementação
5. /mysdd.implement       → executa e rastreia o progresso
```

## Estrutura gerada automaticamente

```
specs/
├── context.md              ← premissas e checks do projeto
├── backlog.md              ← todas as features/tarefas
├── spec-001-nome-feature/
│   ├── spec.md             ← o quê e por quê
│   └── plan.md             ← como, em quais etapas
└── spec-002-outra-feature/
    ├── spec.md
    └── plan.md
```

## Como funciona

- **Commands** (`.opencode/commands/`) são os `/comandos` que você digita no TUI
- **Skills** (`.opencode/skills/`) contêm as instruções detalhadas, carregadas sob demanda pelo agente
- Cada command carrega sua skill correspondente, mantendo o contexto leve até ser necessário
