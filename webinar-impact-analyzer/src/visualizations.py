"""
Visualizations module for Webinar Impact Analyzer
Creates interactive Plotly charts for all analyses
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, Any, List


# Color palette
COLORS = {
    'participants': '#6366f1',  # Indigo
    'control': '#94a3b8',       # Slate
    'upgrade': '#10b981',       # Green
    'downgrade': '#ef4444',     # Red
    'maintained': '#f59e0b',    # Amber
    'primary': '#6366f1',
    'secondary': '#8b5cf6',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6'
}

STATUS_COLORS = {
    'no-seller': '#ef4444',
    'struggling-seller': '#f97316',
    'tiny-seller': '#f59e0b',
    'small-seller': '#84cc16',
    'medium-seller': '#22c55e',
    'large-seller': '#14b8a6',
    'top-seller': '#6366f1'
}


def create_conversion_comparison_chart(results: Dict[str, Any]) -> go.Figure:
    """Create bar chart comparing conversion rates"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Participantes',
        x=['Taxa de Conversão'],
        y=[results['participants']['conversion_rate']],
        marker_color=COLORS['participants'],
        text=[f"{results['participants']['conversion_rate']:.1f}%"],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Controle',
        x=['Taxa de Conversão'],
        y=[results['control']['seller_rate']],
        marker_color=COLORS['control'],
        text=[f"{results['control']['seller_rate']:.1f}%"],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Comparação de Taxa de Conversão para First Seller',
        yaxis_title='Taxa (%)',
        barmode='group',
        showlegend=True,
        height=400
    )
    
    return fig


def create_conversion_funnel(results: Dict[str, Any]) -> go.Figure:
    """Create funnel chart for conversion"""
    p = results['participants']
    
    fig = go.Figure(go.Funnel(
        y=['Total Participantes', 'Converteram para Seller'],
        x=[p['total'], p['converted']],
        textposition='inside',
        textinfo='value+percent initial',
        marker_color=[COLORS['primary'], COLORS['success']]
    ))
    
    fig.update_layout(
        title='Funil de Conversão - Participantes de Webinar',
        height=350
    )
    
    return fig


def create_conversion_by_month_chart(results: Dict[str, Any]) -> go.Figure:
    """Create line chart showing conversion by webinar month"""
    if 'by_month' not in results or not results['by_month']:
        return None
    
    df = pd.DataFrame(results['by_month'])
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            name='Total Participantes',
            x=df['month'],
            y=df['total'],
            marker_color=COLORS['secondary'],
            opacity=0.6
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            name='Taxa de Conversão',
            x=df['month'],
            y=df['conversion_rate'],
            mode='lines+markers+text',
            text=[f"{v:.1f}%" for v in df['conversion_rate']],
            textposition='top center',
            line=dict(color=COLORS['success'], width=3),
            marker=dict(size=10)
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title='Conversão por Mês do Webinar',
        height=400,
        showlegend=True
    )
    fig.update_yaxes(title_text="Quantidade", secondary_y=False)
    fig.update_yaxes(title_text="Taxa de Conversão (%)", secondary_y=True)
    
    return fig


def create_gmv_comparison_chart(results: Dict[str, Any], metric: str = 'mean') -> go.Figure:
    """Create bar chart comparing GMV between groups"""
    fig = go.Figure()
    
    p_value = results['participants'][metric]
    c_value = results['control'][metric]
    
    fig.add_trace(go.Bar(
        name='Participantes',
        x=['GMV Médio'],
        y=[p_value],
        marker_color=COLORS['participants'],
        text=[f"R$ {p_value:,.2f}"],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Controle',
        x=['GMV Médio'],
        y=[c_value],
        marker_color=COLORS['control'],
        text=[f"R$ {c_value:,.2f}"],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Comparação de GMV Médio',
        yaxis_title='GMV (R$)',
        barmode='group',
        showlegend=True,
        height=400
    )
    
    return fig


def create_gmv_distribution_chart(
    participants_df: pd.DataFrame,
    control_df: pd.DataFrame,
    gmv_col: str = 'gmv_d30'
) -> go.Figure:
    """Create box plot comparing GMV distributions"""
    fig = go.Figure()
    
    # Filter out zeros and extreme outliers for better visualization
    p_values = participants_df[gmv_col].dropna()
    c_values = control_df[gmv_col].dropna()
    
    # Cap at 99th percentile for visualization
    p_cap = p_values.quantile(0.99)
    c_cap = c_values.quantile(0.99)
    cap = max(p_cap, c_cap)
    
    p_values_capped = p_values[p_values <= cap]
    c_values_capped = c_values[c_values <= cap]
    
    fig.add_trace(go.Box(
        y=p_values_capped,
        name='Participantes',
        marker_color=COLORS['participants'],
        boxmean=True
    ))
    
    fig.add_trace(go.Box(
        y=c_values_capped,
        name='Controle',
        marker_color=COLORS['control'],
        boxmean=True
    ))
    
    fig.update_layout(
        title='Distribuição de GMV (até percentil 99)',
        yaxis_title='GMV (R$)',
        showlegend=True,
        height=450
    )
    
    return fig


def create_gmv_by_status_chart(results: Dict[str, Any]) -> go.Figure:
    """Create grouped bar chart showing GMV by seller status"""
    if 'participants_by_status' not in results:
        return None
    
    p_df = pd.DataFrame(results['participants_by_status'])
    
    status_order = ['no-seller', 'struggling-seller', 'tiny-seller', 
                    'small-seller', 'medium-seller', 'large-seller', 'top-seller']
    p_df['status'] = pd.Categorical(p_df['status'], categories=status_order, ordered=True)
    p_df = p_df.sort_values('status')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='GMV Médio',
        x=p_df['status'],
        y=p_df['mean_gmv'],
        marker_color=[STATUS_COLORS.get(s, COLORS['primary']) for s in p_df['status']],
        text=[f"R$ {v:,.0f}" for v in p_df['mean_gmv']],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='GMV Médio por Status (Participantes)',
        xaxis_title='Status do Seller',
        yaxis_title='GMV Médio (R$)',
        height=400
    )
    
    return fig


def create_status_transition_chart(results: Dict[str, Any]) -> go.Figure:
    """Create pie chart showing status transition breakdown"""
    if 'participants_transitions' not in results:
        return None
    
    trans = results['participants_transitions']
    
    labels = ['Upgrade', 'Manteve', 'Downgrade']
    values = [
        trans.get('upgrade_count', 0),
        trans.get('maintained_count', 0),
        trans.get('downgrade_count', 0)
    ]
    colors = [COLORS['upgrade'], COLORS['maintained'], COLORS['downgrade']]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig.update_layout(
        title='Evolução de Status dos Participantes',
        height=400,
        showlegend=True
    )
    
    return fig


def create_sankey_diagram(sankey_data: Dict[str, List]) -> go.Figure:
    """Create Sankey diagram showing status transitions"""
    if not sankey_data['source']:
        return None
    
    # Color nodes
    status_order = ['no-seller', 'struggling-seller', 'tiny-seller', 
                    'small-seller', 'medium-seller', 'large-seller', 'top-seller']
    
    node_colors = []
    for s in status_order:
        node_colors.append(STATUS_COLORS.get(s, COLORS['primary']))
    for s in status_order:
        node_colors.append(STATUS_COLORS.get(s, COLORS['primary']))
    
    # Color links based on transition type (upgrade = green, downgrade = red, same = gray)
    link_colors = []
    for i, (src, tgt) in enumerate(zip(sankey_data['source'], sankey_data['target'])):
        # Adjust target index to get actual status position
        tgt_adjusted = tgt - len(status_order)
        if tgt_adjusted > src:
            link_colors.append('rgba(16, 185, 129, 0.4)')  # Green for upgrade
        elif tgt_adjusted < src:
            link_colors.append('rgba(239, 68, 68, 0.4)')  # Red for downgrade
        else:
            link_colors.append('rgba(148, 163, 184, 0.4)')  # Gray for maintained
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=sankey_data['labels'],
            color=node_colors
        ),
        link=dict(
            source=sankey_data['source'],
            target=sankey_data['target'],
            value=sankey_data['value'],
            color=link_colors
        )
    )])
    
    fig.update_layout(
        title='Fluxo de Transição de Status (Antes → Depois do Webinar)',
        height=500
    )
    
    return fig


def create_status_distribution_comparison(results: Dict[str, Any]) -> go.Figure:
    """Create grouped bar chart comparing status distributions"""
    p_dist = results.get('participants_current_distribution', {})
    c_dist = results.get('control_distribution', {})
    
    status_order = ['no-seller', 'struggling-seller', 'tiny-seller', 
                    'small-seller', 'medium-seller', 'large-seller', 'top-seller']
    
    # Calculate percentages
    p_total = sum(p_dist.values())
    c_total = sum(c_dist.values())
    
    p_pct = [p_dist.get(s, 0) / p_total * 100 if p_total > 0 else 0 for s in status_order]
    c_pct = [c_dist.get(s, 0) / c_total * 100 if c_total > 0 else 0 for s in status_order]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Participantes',
        x=status_order,
        y=p_pct,
        marker_color=COLORS['participants'],
        text=[f"{v:.1f}%" for v in p_pct],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Controle',
        x=status_order,
        y=c_pct,
        marker_color=COLORS['control'],
        text=[f"{v:.1f}%" for v in c_pct],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Distribuição de Status Atual: Participantes vs Controle',
        xaxis_title='Status do Seller',
        yaxis_title='Percentual (%)',
        barmode='group',
        height=450
    )
    
    return fig


def create_upgrade_by_status_chart(results: Dict[str, Any]) -> go.Figure:
    """Create chart showing upgrade rate by initial status"""
    if 'by_initial_status' not in results:
        return None
    
    df = pd.DataFrame(results['by_initial_status'])
    
    status_order = ['no-seller', 'struggling-seller', 'tiny-seller', 
                    'small-seller', 'medium-seller', 'large-seller']
    df['initial_status'] = pd.Categorical(df['initial_status'], categories=status_order, ordered=True)
    df = df.sort_values('initial_status')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Upgrade',
        x=df['initial_status'],
        y=df['upgrade_rate'],
        marker_color=COLORS['upgrade'],
    ))
    
    fig.add_trace(go.Bar(
        name='Manteve',
        x=df['initial_status'],
        y=df['maintained_rate'],
        marker_color=COLORS['maintained'],
    ))
    
    fig.add_trace(go.Bar(
        name='Downgrade',
        x=df['initial_status'],
        y=df['downgrade_rate'],
        marker_color=COLORS['downgrade'],
    ))
    
    fig.update_layout(
        title='Taxa de Transição por Status Inicial',
        xaxis_title='Status no Mês do Webinar',
        yaxis_title='Percentual (%)',
        barmode='stack',
        height=450
    )
    
    return fig


def format_number(n: float, prefix: str = '') -> str:
    """Format number for display"""
    if n >= 1_000_000:
        return f"{prefix}{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{prefix}{n/1_000:.1f}K"
    else:
        return f"{prefix}{n:.0f}"
