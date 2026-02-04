# Dashboard Impacto - Lifecycle BR

Dashboard de acompanhamento das ações de Lifecycle e seu impacto na base de clientes.

## Estrutura do Projeto

```
DashLCY/
├── index.html           # Dashboard (gerado automaticamente)
├── scripts/
│   └── generate_dashboard.py  # Script gerador
├── data/
│   ├── base_geral/      # Bases mensais de lojas
│   ├── new_sellers/     # Bases de new sellers
│   └── projetos/        # Bases dos projetos
│       ├── webinars/
│       ├── onboarding/
│       ├── human_in_the_loop/
│       └── atrai_e_cresce/
└── vercel.json          # Config para deploy
```

## Como Usar

### Atualizar o Dashboard

1. Coloque as bases nas pastas em `data/`
2. Execute:
   ```bash
   cd scripts
   python3 generate_dashboard.py
   ```
3. Abra `index.html` no navegador

### Deploy no Vercel

1. Suba o projeto para o GitHub
2. Conecte o repositório no Vercel
3. Deploy automático a cada push

## Funcionalidades

- **Resumo Executivo**: Big numbers, new sellers, matriz de transição, risco
- **Visão da Base**: Status de sellers, matriz de evolução
- **Merchant Services**: Distribuição, cross-sell, combinações
- **Risco de Churn**: Quartis de risco, evolução por mês
- **Cobertura Lifecycle**: % da base coberta por ações
- **Projetos**: Análise detalhada por projeto (Webinars, etc.)
