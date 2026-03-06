# 📁 Estrutura de Dados - Dashboard Lifecycle BR

Coloque suas bases nas pastas correspondentes e execute o script para atualizar o dashboard.

## Estrutura de Pastas

```
data/
├── base_geral/              # Base principal de lojas (obrigatório)
│   └── base_br_YYYY_MM.csv  # Ex: base_br_2024_12.csv, base_br_2025_01.csv
│
├── new_sellers/             # Bases de new sellers por mês
│   └── new_sellers_YYYY_MM.csv
│
└── projetos/                # Bases dos projetos de Lifecycle
    ├── webinars/
    │   └── webinars_cobertura.csv
    ├── onboarding/
    │   └── onboarding_cobertura.csv
    ├── human_in_the_loop/
    │   └── hil_cobertura.csv
    └── atrai_e_cresce/
        └── atrai_cresce_cobertura.csv
```

## Como Atualizar o Dashboard

1. Coloque as bases nas pastas correspondentes
2. Execute no terminal:
   ```bash
   cd scripts   # a partir da raiz do projeto DashLCY
   python3 generate_dashboard.py
   ```
3. Abra o `index.html` no navegador

## Formato das Bases

### Base Geral (obrigatório)
- `id_store` ou `store_id` - ID único da loja
- `merchant_finance_status` - Status (filtrar por 'paying')
- `status_seller` - Status do seller
- `gmv_mes` - GMV do mês
- `orders_mes` - Pedidos do mês
- `predictive_churn_probability` - Probabilidade de churn
- `nuvemmarketing`, `nuvempago`, `nuvemchat`, `nuvemenvio`, `pdv` - Produtos

### New Sellers
- `store_id` - ID da loja
- Nome do arquivo indica o mês de referência

### Projetos
- `store_id` - ID da loja
- Coluna de status (ex: 'Com cobertura')

## Matriz de Transição

Para ver a matriz de transição de status, carregue **pelo menos 2 bases** do mês geral (ex: dezembro e janeiro). O script comparará automaticamente os status entre os meses.
