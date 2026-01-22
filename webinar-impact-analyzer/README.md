# Webinar Impact Analyzer

Dashboard interativo para análise de impacto dos webinars da Nuvemshop nas métricas de negócio.

## 📊 Análises Disponíveis

### Hipótese 1: Conversão para First Seller
- Taxa de conversão para primeira venda
- Comparação Participantes vs Grupo de Controle
- Teste estatístico: Chi-quadrado

### Hipótese 2: Impacto no GMV
- Comparação de GMV atual (D-30 e D-90)
- Análise por segmento de seller
- Teste estatístico: t-test / Mann-Whitney

### Hipótese 3: Evolução de Status
- Transição de status (upgrade/downgrade)
- Diagrama Sankey de fluxo
- Distribuição de status atual

## 🚀 Como Usar

### 1. Instalar dependências

```bash
cd webinar-impact-analyzer
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Executar a aplicação

```bash
streamlit run app.py
```

### 3. Fazer upload dos dados

Acesse http://localhost:8501 e faça upload dos dois arquivos:

#### Arquivo 1: Base de Participantes do Webinar
Colunas necessárias:
- `store_id` - ID da loja
- `Data do Webinar (mês)` - Mês do webinar (ex: "Month 09 - September 2025")
- `webinar_name` - Nome do webinar
- `webinar_status` - Status (live, on-demand, registered)
- `first_seller_at` - Data da primeira venda (DD/MM/YYYY)
- `Máx. Seller Segment Mes Webinar` - Status no mês do webinar

#### Arquivo 2: Base Total de Lojas
Colunas (em ordem):
- `store_id` - ID da loja
- `<Coluna 1>` - GMV D-30
- `<Coluna 2>` - GMV D-90
- `<Coluna 3>` - Status atual
- `<Coluna 4>` - Idade da loja (em dias)

## 📁 Estrutura do Projeto

```
webinar-impact-analyzer/
├── app.py                      # Aplicação principal Streamlit
├── requirements.txt            # Dependências Python
├── README.md                   # Este arquivo
└── src/
    ├── __init__.py
    ├── data_loader.py         # Carregamento e validação de dados
    ├── data_processor.py      # Processamento e matching
    ├── visualizations.py      # Gráficos Plotly
    └── analysis/
        ├── __init__.py
        ├── first_seller.py    # Análise Hipótese 1
        ├── gmv_analysis.py    # Análise Hipótese 2
        └── status_evolution.py # Análise Hipótese 3
```

## 🔄 Atualização Mensal

Para atualizar os dados mensalmente:

1. Exporte a nova base de participantes do webinar
2. Exporte a base total de lojas com GMV e status atualizados
3. Abra a aplicação e faça upload dos novos arquivos
4. As análises serão geradas automaticamente

## 📈 Interpretação dos Resultados

### Significância Estatística
- **p-valor < 0.05**: Resultado estatisticamente significativo (podemos confiar na diferença)
- **p-valor >= 0.05**: Resultado não é estatisticamente significativo (diferença pode ser ao acaso)

### Métricas Principais
- **Lift**: Percentual de melhoria dos participantes vs controle
- **Taxa de Upgrade**: % de lojas que subiram de status
- **Taxa de Conversão**: % de lojas que fizeram primeira venda

## 🛠️ Tecnologias

- Python 3.11+
- Streamlit (interface web)
- Pandas (manipulação de dados)
- Plotly (visualizações)
- SciPy (testes estatísticos)

---

Desenvolvido para o time de Lifecycle da Nuvemshop 🚀
