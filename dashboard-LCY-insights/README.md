# Dashboard de Impacto - Webinars

Dashboard interativo para análise do impacto de ações de educação (webinars) na base de clientes.

## 📊 Funcionalidades

- **Resumo Executivo**: Visão geral das métricas principais
- **Análise Pareada**: Comparação justa controlando por perfil (status + idade da loja)
- **Merchant Services**: Análise de adoção de produtos e oportunidades de cross-sell
- **Status & Evolução**: Distribuição e performance por tier de seller
- **Performance**: GMV e volume de pedidos detalhados
- **Churn**: Análise de risco de churn preditivo
- **Perfil dos Participantes**: Características de quem participa dos webinars
- **Webinars**: Ranking dos webinars mais populares

## 🚀 Deploy

### Vercel (Recomendado)

1. Faça push deste repositório para o GitHub
2. Acesse [vercel.com](https://vercel.com)
3. Clique em "New Project"
4. Importe o repositório do GitHub
5. Clique em "Deploy"

O Vercel detectará automaticamente que é um site estático e fará o deploy.

### GitHub Pages

1. Vá em Settings > Pages no seu repositório
2. Em "Source", selecione a branch `main`
3. Clique em Save
4. Acesse `https://seu-usuario.github.io/dashboard-webinar-insights`

## 📁 Estrutura

```
dashboard-webinar-insights/
├── index.html          # Dashboard principal
├── README.md           # Este arquivo
└── vercel.json         # Configuração do Vercel
```

## 🔄 Atualização dos Dados

Para atualizar os dados do dashboard:

1. Execute o script Python `dashboard_webinar_insights_v2.py` com as novas bases
2. Copie o arquivo gerado para `index.html`
3. Faça commit e push para o GitHub
4. O Vercel fará o redeploy automaticamente

## 📈 Métricas Analisadas

| Métrica | Descrição |
|---------|-----------|
| GMV | Gross Merchandise Value (valor total de vendas) |
| Orders | Volume de pedidos |
| Churn Preditivo | Probabilidade de cancelamento baseada em IA |
| Merchant Services | Produtos adicionais (NuvemPago, NuvemEnvio, etc.) |
| Status Seller | Tier do lojista (No Seller → Top Seller) |

## 🛠️ Tecnologias

- HTML5 / CSS3
- JavaScript
- [Chart.js](https://www.chartjs.org/) - Gráficos interativos
- Python / Pandas - Processamento de dados

## 📝 Licença

Uso interno - Dados confidenciais.

---

Desenvolvido para análise de Marketing Ops 📊
