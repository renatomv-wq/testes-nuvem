# Dashboard de Impacto - Webinars

Dashboard interativo para análise do impacto de ações de educação (webinars) na base de clientes.

## 📊 Funcionalidades

- **Resumo Executivo**: Visão geral das métricas principais
- **Análise Pareada**: Comparação justa controlando por perfil
- **Merchant Services**: Análise de adoção de produtos e cross-sell
- **Status & Evolução**: Distribuição e performance por tier de seller
- **Performance**: GMV e volume de pedidos
- **Churn**: Análise de risco de churn preditivo
- **Perfil dos Participantes**: Quem está participando dos webinars
- **Webinars**: Ranking dos webinars mais populares

## 🚀 Deploy no Vercel

1. Faça push deste repositório para o GitHub
2. Acesse [vercel.com](https://vercel.com)
3. Importe o repositório e clique em Deploy

## 🔄 Atualização dos Dados

1. Execute o script `scripts/generate_dashboard.py` com as novas bases
2. Copie o HTML gerado para `index.html`
3. Commit e push - o Vercel fará redeploy automático
