# Dashboard Impacto - Lifecycle BR

Dashboard de acompanhamento das ações de Lifecycle e seu impacto na base de clientes.

## Estrutura do Projeto

```
DashLCY/
├── index.html           # Página de login (senha para acesso)
├── dashboard.html       # Dashboard (gerado automaticamente pelo script)
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

### Continuar o projeto (primeira vez ou sem bases reais)

1. **Modo demo** – O projeto já inclui uma base de exemplo (`data/base_lifecycle_10k.csv`). Se as pastas `data/base_geral/`, `data/new_sellers/` e `data/projetos/` estiverem vazias e não houver arquivos nos caminhos alternativos (Downloads), o script usa essa base automaticamente.
2. Execute o gerador:
   ```bash
   cd scripts
   python3 generate_dashboard.py
   ```
3. Abra `index.html` no navegador, informe a senha e acesse o dashboard.

### Atualizar o Dashboard com bases reais

1. Coloque as bases nas pastas em `data/` (veja formato em `data/README.md`):
   - **Base geral:** arquivos em `data/base_geral/` (ex.: `base_br_2025_01.csv`)
   - **New sellers:** arquivos em `data/new_sellers/`
   - **Projetos:** em `data/projetos/webinars/`, `projetos/onboarding/`, etc.
2. Execute:
   ```bash
   cd scripts
   python3 generate_dashboard.py
   ```
3. Abra `index.html` no navegador (login) e depois acesse o dashboard

### Caminhos alternativos (opcional)

Se você mantiver bases em outra pasta (ex.: Downloads), pode apontar o script com variáveis de ambiente:

- `DASHLCY_BASE_JAN` – base Janeiro
- `DASHLCY_BASE_FEV` – base Fevereiro  
- `DASHLCY_BASE_DEZ` – base Dezembro
- `DASHLCY_BASE_MS` – base Merchant Services
- `DASHLCY_WEBINAR` – base Webinars
- `DASHLCY_NEWSELLERS` / `DASHLCY_NEWSELLERS_FEV` – bases New Sellers

Exemplo: `DASHLCY_BASE_JAN=/caminho/para/jan.csv python3 generate_dashboard.py`

### Acesso protegido por senha

O dashboard é acessado após login na página inicial (`index.html`). A senha é verificada no navegador (hash SHA-256). **Senha padrão:** `DashLCY2025`. Para alterar a senha, edite `index.html`, localize a variável `EXPECTED_HASH` e substitua pelo hash SHA-256 da nova senha (no terminal: `echo -n "SuaNovaSenha" | shasum -a 256`). A sessão expira ao fechar o navegador (sessionStorage).

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
