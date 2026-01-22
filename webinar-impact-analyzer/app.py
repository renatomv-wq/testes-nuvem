"""
Webinar Impact Analyzer - Nuvemshop
Dashboard para análise de impacto de webinars nas métricas de negócio
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Import modules
from src.data_loader import load_webinar_data, load_store_data, get_status_order
from src.data_processor import (
    merge_datasets, prepare_analysis_data, 
    get_webinar_list, get_month_list,
    filter_by_webinar, filter_by_month, filter_by_status
)
from src.analysis.first_seller import (
    analyze_first_seller_conversion, 
    get_first_seller_summary_text
)
from src.analysis.gmv_analysis import (
    analyze_gmv_comparison, 
    analyze_gmv_by_segment,
    get_gmv_summary_text
)
from src.analysis.status_evolution import (
    analyze_status_evolution,
    get_sankey_data,
    get_status_summary_text
)
from src.visualizations import (
    create_conversion_comparison_chart,
    create_conversion_funnel,
    create_conversion_by_month_chart,
    create_gmv_comparison_chart,
    create_gmv_distribution_chart,
    create_gmv_by_status_chart,
    create_status_transition_chart,
    create_sankey_diagram,
    create_status_distribution_comparison,
    create_upgrade_by_status_chart,
    format_number
)

# Page config
st.set_page_config(
    page_title="Webinar Impact Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #6366f1;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #64748b;
        margin-top: 0.25rem;
    }
    .stat-significant {
        background-color: #dcfce7;
        color: #166534;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .stat-not-significant {
        background-color: #fef3c7;
        color: #92400e;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .info-box {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background-color: #f1f5f9;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6366f1;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.markdown('<p class="main-header">📊 Webinar Impact Analyzer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Análise de impacto dos webinars nas métricas de negócio | Nuvemshop</p>', unsafe_allow_html=True)
    
    # Sidebar - File uploads
    with st.sidebar:
        st.header("📁 Upload de Dados")
        
        st.markdown("**1. Base de Participantes do Webinar**")
        webinar_file = st.file_uploader(
            "CSV/Excel com participantes",
            type=['csv', 'xlsx', 'xls'],
            key='webinar_file',
            help="Arquivo com store_id, data do webinar, status de participação"
        )
        
        st.markdown("**2. Base Total de Lojas**")
        store_file = st.file_uploader(
            "CSV/Excel com todas as lojas",
            type=['csv', 'xlsx', 'xls'],
            key='store_file',
            help="Arquivo com store_id, GMV, status atual"
        )
        
        st.divider()
        
        # Show upload status
        if webinar_file and store_file:
            st.success("✅ Arquivos carregados!")
        else:
            st.info("Faça upload dos dois arquivos para começar")
    
    # Main content
    if not webinar_file or not store_file:
        # Show instructions
        st.markdown("""
        ### 👋 Bem-vindo ao Webinar Impact Analyzer!
        
        Esta ferramenta analisa o impacto dos webinars da Nuvemshop em três hipóteses:
        
        | Hipótese | Métrica | Método |
        |----------|---------|--------|
        | **H1: First Seller** | Taxa de conversão para primeira venda | Teste Chi-quadrado |
        | **H2: GMV** | Comparação de GMV atual | Teste t / Mann-Whitney |
        | **H3: Status** | Evolução de status de seller | Análise de transição |
        
        ---
        
        ### 📋 Instruções
        
        **1. Faça upload da base de participantes do webinar** com as colunas:
        - `store_id` - ID da loja
        - `Data do Webinar (mês)` - Mês do webinar
        - `webinar_name` - Nome do webinar
        - `webinar_status` - Status (live, on-demand, registered)
        - `first_seller_at` - Data da primeira venda
        - `Máx. Seller Segment Mes Webinar` - Status no mês do webinar
        
        **2. Faça upload da base total de lojas** com as colunas:
        - `store_id` - ID da loja
        - GMV D-30 (coluna 1)
        - GMV D-90 (coluna 2)
        - Status atual (coluna 3)
        - Idade da loja (coluna 4)
        
        ---
        
        Após o upload, você verá as análises automaticamente! 🚀
        """)
        return
    
    # Load data
    with st.spinner("Carregando dados..."):
        webinar_df, webinar_error = load_webinar_data(webinar_file)
        store_df, store_error = load_store_data(store_file)
    
    if webinar_error:
        st.error(f"Erro ao carregar base de webinar: {webinar_error}")
        return
    
    if store_error:
        st.error(f"Erro ao carregar base de lojas: {store_error}")
        return
    
    # Merge datasets
    with st.spinner("Processando dados..."):
        participants_df, control_df = merge_datasets(webinar_df, store_df)
        analysis_data = prepare_analysis_data(participants_df, control_df)
        participants = analysis_data['participants']
        control = analysis_data['control']
    
    # Sidebar filters
    with st.sidebar:
        st.divider()
        st.header("🔍 Filtros")
        
        # Month filter
        months = ['Todos'] + get_month_list(webinar_df)
        selected_month = st.selectbox("Mês do Webinar", months)
        
        # Webinar filter
        webinars = ['Todos'] + get_webinar_list(webinar_df)
        selected_webinar = st.selectbox("Webinar", webinars)
        
        # Status filter
        statuses = ['Todos', 'no-seller', 'struggling-seller', 'tiny-seller', 
                    'small-seller', 'medium-seller', 'large-seller', 'top-seller']
        selected_status = st.selectbox("Status Inicial", statuses)
    
    # Apply filters
    filtered_webinar = webinar_df.copy()
    if selected_month != 'Todos':
        filtered_webinar = filter_by_month(filtered_webinar, selected_month)
    if selected_webinar != 'Todos':
        filtered_webinar = filter_by_webinar(filtered_webinar, selected_webinar)
    
    # Re-process with filtered data
    if len(filtered_webinar) > 0:
        participants_filtered, _ = merge_datasets(filtered_webinar, store_df)
        analysis_data_filtered = prepare_analysis_data(participants_filtered, control_df)
        participants = analysis_data_filtered['participants']
    
    if selected_status != 'Todos':
        participants = filter_by_status(participants, selected_status, 'status_at_webinar')
    
    # Overview metrics
    st.markdown("### 📈 Visão Geral")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Participantes de Webinar",
            value=format_number(len(participants)),
            help="Lojas únicas que participaram de webinars"
        )
    
    with col2:
        st.metric(
            label="Grupo de Controle",
            value=format_number(len(control)),
            help="Lojas que não participaram de webinars"
        )
    
    with col3:
        webinar_count = webinar_df['webinar_name'].nunique() if 'webinar_name' in webinar_df.columns else 0
        st.metric(
            label="Webinars Analisados",
            value=webinar_count,
            help="Número de webinars diferentes"
        )
    
    with col4:
        months_count = webinar_df['Data do Webinar (mês)'].nunique() if 'Data do Webinar (mês)' in webinar_df.columns else 0
        st.metric(
            label="Meses de Dados",
            value=months_count,
            help="Período analisado"
        )
    
    st.divider()
    
    # Tabs for each hypothesis
    tab1, tab2, tab3 = st.tabs([
        "🎯 H1: First Seller",
        "💰 H2: GMV",
        "📊 H3: Evolução de Status"
    ])
    
    # Tab 1: First Seller Analysis
    with tab1:
        st.markdown("## Hipótese 1: Conversão para First Seller")
        st.markdown("""
        > **Pergunta:** Participantes de webinar têm maior taxa de conversão para primeira venda?
        """)
        
        with st.spinner("Analisando conversão..."):
            h1_results = analyze_first_seller_conversion(participants, control)
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Taxa de Conversão (Participantes)",
                value=f"{h1_results['participants']['conversion_rate']:.1f}%",
                delta=f"{h1_results['participants']['converted']:,} lojas"
            )
        
        with col2:
            st.metric(
                label="Taxa de Sellers (Controle)",
                value=f"{h1_results['control']['seller_rate']:.1f}%",
                delta=f"{h1_results['control']['sellers']:,} lojas"
            )
        
        with col3:
            if h1_results.get('lift') is not None:
                lift = h1_results['lift']
                st.metric(
                    label="Lift",
                    value=f"{lift:+.1f}%",
                    delta="vs Controle"
                )
        
        # Statistical significance
        if h1_results.get('chi_square') and h1_results['chi_square'].get('p_value') is not None:
            chi = h1_results['chi_square']
            if chi['significant']:
                st.success(f"✅ **Resultado estatisticamente significativo** (p-valor: {chi['p_value']:.4f})")
            else:
                st.warning(f"⚠️ **Resultado não é estatisticamente significativo** (p-valor: {chi['p_value']:.4f})")
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_conversion_comparison_chart(h1_results)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_conversion_funnel(h1_results)
            st.plotly_chart(fig, use_container_width=True)
        
        # Monthly breakdown
        if 'by_month' in h1_results and h1_results['by_month']:
            st.markdown("### Conversão por Mês")
            fig = create_conversion_by_month_chart(h1_results)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Summary
        with st.expander("📋 Resumo Detalhado"):
            st.markdown(get_first_seller_summary_text(h1_results))
    
    # Tab 2: GMV Analysis
    with tab2:
        st.markdown("## Hipótese 2: Impacto no GMV")
        st.markdown("""
        > **Pergunta:** Participantes de webinar têm GMV maior que o grupo de controle?
        """)
        
        # GMV period selector
        gmv_period = st.radio(
            "Período de GMV",
            ['gmv_d30', 'gmv_d90'],
            format_func=lambda x: 'Últimos 30 dias' if x == 'gmv_d30' else 'Últimos 90 dias',
            horizontal=True
        )
        
        with st.spinner("Analisando GMV..."):
            h2_results = analyze_gmv_comparison(participants, control, gmv_period)
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="GMV Médio (Participantes)",
                value=f"R$ {h2_results['participants']['mean']:,.2f}",
                delta=f"Mediana: R$ {h2_results['participants']['median']:,.2f}"
            )
        
        with col2:
            st.metric(
                label="GMV Médio (Controle)",
                value=f"R$ {h2_results['control']['mean']:,.2f}",
                delta=f"Mediana: R$ {h2_results['control']['median']:,.2f}"
            )
        
        with col3:
            if h2_results.get('mean_diff_pct') is not None:
                diff = h2_results['mean_diff_pct']
                st.metric(
                    label="Diferença",
                    value=f"{diff:+.1f}%",
                    delta="Participantes vs Controle"
                )
        
        # Statistical significance
        if h2_results.get('ttest') and h2_results['ttest'].get('p_value') is not None:
            ttest = h2_results['ttest']
            if ttest['significant']:
                st.success(f"✅ **Resultado estatisticamente significativo** (p-valor: {ttest['p_value']:.4f})")
            else:
                st.warning(f"⚠️ **Resultado não é estatisticamente significativo** (p-valor: {ttest['p_value']:.4f})")
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_gmv_comparison_chart(h2_results)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_gmv_distribution_chart(participants, control, gmv_period)
            st.plotly_chart(fig, use_container_width=True)
        
        # GMV by status
        if h2_results.get('participants_by_status'):
            st.markdown("### GMV por Status do Seller")
            fig = create_gmv_by_status_chart(h2_results)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Segmented analysis
        st.markdown("### Análise por Segmento (Controlando por Status)")
        
        segment_results = analyze_gmv_by_segment(
            participants, control, 'current_status', gmv_period
        )
        
        if segment_results:
            segment_df = pd.DataFrame([
                {
                    'Status': r['segment'],
                    'GMV Participantes': f"R$ {r['participants']['mean']:,.2f}",
                    'GMV Controle': f"R$ {r['control']['mean']:,.2f}",
                    'Diferença (%)': f"{r.get('mean_diff_pct', 0):+.1f}%",
                    'p-valor': f"{r['ttest'].get('p_value', 'N/A'):.4f}" if r['ttest'].get('p_value') else 'N/A',
                    'Significativo': '✅' if r['ttest'].get('significant') else '❌'
                }
                for r in segment_results
            ])
            st.dataframe(segment_df, use_container_width=True, hide_index=True)
        
        # Summary
        with st.expander("📋 Resumo Detalhado"):
            st.markdown(get_gmv_summary_text(h2_results, gmv_period))
    
    # Tab 3: Status Evolution
    with tab3:
        st.markdown("## Hipótese 3: Evolução de Status")
        st.markdown("""
        > **Pergunta:** Participantes de webinar têm melhor evolução de status de seller?
        """)
        
        with st.spinner("Analisando evolução de status..."):
            h3_results = analyze_status_evolution(participants, control)
            sankey_data = get_sankey_data(participants)
        
        # Key metrics
        if 'participants_transitions' in h3_results:
            trans = h3_results['participants_transitions']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Lojas Analisadas",
                    value=format_number(trans['valid_transitions']),
                    help="Lojas com status válido antes e depois"
                )
            
            with col2:
                upgrade_rate = trans.get('upgrade_rate', 0)
                st.metric(
                    label="Taxa de Upgrade",
                    value=f"{upgrade_rate:.1f}%",
                    delta=f"{trans.get('upgrade_count', 0):,} lojas"
                )
            
            with col3:
                maintained_rate = trans.get('maintained_rate', 0)
                st.metric(
                    label="Mantiveram Status",
                    value=f"{maintained_rate:.1f}%",
                    delta=f"{trans.get('maintained_count', 0):,} lojas"
                )
            
            with col4:
                downgrade_rate = trans.get('downgrade_rate', 0)
                st.metric(
                    label="Taxa de Downgrade",
                    value=f"{downgrade_rate:.1f}%",
                    delta=f"{trans.get('downgrade_count', 0):,} lojas"
                )
        
        # Distribution comparison significance
        if h3_results.get('distribution_chi_square') and h3_results['distribution_chi_square'].get('p_value') is not None:
            chi = h3_results['distribution_chi_square']
            if chi['significant']:
                st.success(f"✅ **Distribuição de status é significativamente diferente entre grupos** (p-valor: {chi['p_value']:.4f})")
            else:
                st.info(f"ℹ️ **Distribuição de status não é significativamente diferente** (p-valor: {chi['p_value']:.4f})")
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_status_transition_chart(h3_results)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_status_distribution_comparison(h3_results)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Sankey diagram
        st.markdown("### Fluxo de Transição de Status")
        fig = create_sankey_diagram(sankey_data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para gerar o diagrama de Sankey")
        
        # Breakdown by initial status
        if h3_results.get('by_initial_status'):
            st.markdown("### Taxa de Transição por Status Inicial")
            fig = create_upgrade_by_status_chart(h3_results)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Summary
        with st.expander("📋 Resumo Detalhado"):
            st.markdown(get_status_summary_text(h3_results))
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #94a3b8; padding: 1rem;'>
        <p>Webinar Impact Analyzer | Nuvemshop Lifecycle Team</p>
        <p style='font-size: 0.8rem;'>Dados atualizados em: """ + datetime.now().strftime('%d/%m/%Y %H:%M') + """</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
