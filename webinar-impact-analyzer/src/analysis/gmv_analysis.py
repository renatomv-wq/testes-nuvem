"""
GMV Analysis Module
Hypothesis 2: Webinar participants have higher GMV than control group
(controlling for initial status and store age)
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List, Tuple


def calculate_gmv_stats(df: pd.DataFrame, gmv_col: str = 'gmv_d30') -> Dict[str, float]:
    """Calculate GMV statistics for a group"""
    values = df[gmv_col].dropna()
    if len(values) == 0:
        return {'mean': 0, 'median': 0, 'std': 0, 'count': 0}
    
    return {
        'mean': values.mean(),
        'median': values.median(),
        'std': values.std(),
        'count': len(values),
        'sum': values.sum(),
        'min': values.min(),
        'max': values.max(),
        'q25': values.quantile(0.25),
        'q75': values.quantile(0.75)
    }


def perform_ttest(
    participants_values: pd.Series,
    control_values: pd.Series
) -> Dict[str, Any]:
    """Perform independent t-test between two groups"""
    # Remove NaN and zeros for meaningful comparison
    p_clean = participants_values.dropna()
    c_clean = control_values.dropna()
    
    if len(p_clean) < 2 or len(c_clean) < 2:
        return {
            'statistic': None,
            'p_value': None,
            'significant': None,
            'error': 'Dados insuficientes para teste t'
        }
    
    # Perform t-test
    t_stat, p_value = stats.ttest_ind(p_clean, c_clean, equal_var=False)
    
    return {
        'statistic': t_stat,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'participants_n': len(p_clean),
        'control_n': len(c_clean)
    }


def perform_mannwhitney(
    participants_values: pd.Series,
    control_values: pd.Series
) -> Dict[str, Any]:
    """Perform Mann-Whitney U test (non-parametric alternative)"""
    p_clean = participants_values.dropna()
    c_clean = control_values.dropna()
    
    if len(p_clean) < 2 or len(c_clean) < 2:
        return {
            'statistic': None,
            'p_value': None,
            'significant': None,
            'error': 'Dados insuficientes para teste'
        }
    
    try:
        u_stat, p_value = stats.mannwhitneyu(p_clean, c_clean, alternative='two-sided')
        return {
            'statistic': u_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
    except Exception as e:
        return {
            'statistic': None,
            'p_value': None,
            'error': str(e)
        }


def analyze_gmv_comparison(
    participants_df: pd.DataFrame,
    control_df: pd.DataFrame,
    gmv_col: str = 'gmv_d30'
) -> Dict[str, Any]:
    """
    Compare GMV between participants and control group
    
    Returns:
        Dictionary with analysis results including:
        - GMV statistics for both groups
        - t-test results
        - breakdown by segments
    """
    results = {}
    
    # Overall GMV stats
    results['participants'] = calculate_gmv_stats(participants_df, gmv_col)
    results['control'] = calculate_gmv_stats(control_df, gmv_col)
    
    # T-test
    results['ttest'] = perform_ttest(
        participants_df[gmv_col],
        control_df[gmv_col]
    )
    
    # Mann-Whitney (more robust for non-normal distributions)
    results['mannwhitney'] = perform_mannwhitney(
        participants_df[gmv_col],
        control_df[gmv_col]
    )
    
    # Calculate lift/difference
    if results['control']['mean'] > 0:
        results['mean_diff_pct'] = (
            (results['participants']['mean'] - results['control']['mean']) /
            results['control']['mean'] * 100
        )
    else:
        results['mean_diff_pct'] = None
    
    # Breakdown by status at webinar (for participants)
    if 'status_at_webinar' in participants_df.columns:
        status_gmv = participants_df.groupby('status_at_webinar').agg({
            gmv_col: ['mean', 'median', 'count']
        }).reset_index()
        status_gmv.columns = ['status', 'mean_gmv', 'median_gmv', 'count']
        results['participants_by_status'] = status_gmv.to_dict('records')
    
    # Breakdown by current status (for control)
    if 'current_status' in control_df.columns:
        control_status_gmv = control_df.groupby('current_status').agg({
            gmv_col: ['mean', 'median', 'count']
        }).reset_index()
        control_status_gmv.columns = ['status', 'mean_gmv', 'median_gmv', 'count']
        results['control_by_status'] = control_status_gmv.to_dict('records')
    
    # Breakdown by age category
    if 'age_category' in participants_df.columns:
        age_gmv_participants = participants_df.groupby('age_category')[gmv_col].agg(['mean', 'median', 'count']).reset_index()
        age_gmv_participants.columns = ['age_category', 'mean_gmv', 'median_gmv', 'count']
        results['participants_by_age'] = age_gmv_participants.to_dict('records')
        
    if 'age_category' in control_df.columns:
        age_gmv_control = control_df.groupby('age_category')[gmv_col].agg(['mean', 'median', 'count']).reset_index()
        age_gmv_control.columns = ['age_category', 'mean_gmv', 'median_gmv', 'count']
        results['control_by_age'] = age_gmv_control.to_dict('records')
    
    return results


def analyze_gmv_by_segment(
    participants_df: pd.DataFrame,
    control_df: pd.DataFrame,
    segment_col: str,
    gmv_col: str = 'gmv_d30'
) -> List[Dict[str, Any]]:
    """
    Compare GMV between groups within each segment
    Useful for controlling by initial status or age
    """
    results = []
    
    # Get all segments
    all_segments = set(participants_df[segment_col].dropna().unique()) | set(control_df[segment_col].dropna().unique())
    
    for segment in all_segments:
        if not segment:
            continue
            
        p_segment = participants_df[participants_df[segment_col] == segment]
        c_segment = control_df[control_df[segment_col] == segment]
        
        if len(p_segment) < 5 or len(c_segment) < 5:
            continue
        
        segment_result = {
            'segment': segment,
            'participants': calculate_gmv_stats(p_segment, gmv_col),
            'control': calculate_gmv_stats(c_segment, gmv_col),
            'ttest': perform_ttest(p_segment[gmv_col], c_segment[gmv_col])
        }
        
        if segment_result['control']['mean'] > 0:
            segment_result['mean_diff_pct'] = (
                (segment_result['participants']['mean'] - segment_result['control']['mean']) /
                segment_result['control']['mean'] * 100
            )
        
        results.append(segment_result)
    
    return results


def get_gmv_summary_text(results: Dict[str, Any], gmv_col: str = 'gmv_d30') -> str:
    """Generate human-readable summary of GMV analysis"""
    period = "últimos 30 dias" if gmv_col == 'gmv_d30' else "últimos 90 dias"
    
    summary = []
    
    summary.append(f"**GMV {period}:**\n")
    
    summary.append(f"**Participantes de Webinar:**")
    summary.append(f"- Média: R$ {results['participants']['mean']:,.2f}")
    summary.append(f"- Mediana: R$ {results['participants']['median']:,.2f}")
    summary.append(f"- Total de lojas: {results['participants']['count']:,}")
    
    summary.append(f"\n**Grupo de Controle:**")
    summary.append(f"- Média: R$ {results['control']['mean']:,.2f}")
    summary.append(f"- Mediana: R$ {results['control']['median']:,.2f}")
    summary.append(f"- Total de lojas: {results['control']['count']:,}")
    
    if results.get('mean_diff_pct') is not None:
        diff = results['mean_diff_pct']
        direction = "maior" if diff > 0 else "menor"
        summary.append(f"\n**Diferença:** Participantes têm GMV médio {abs(diff):.1f}% {direction}")
    
    if results.get('ttest') and results['ttest'].get('p_value') is not None:
        p = results['ttest']['p_value']
        sig = "estatisticamente significativa" if p < 0.05 else "não é estatisticamente significativa"
        summary.append(f"\n**Teste t:**")
        summary.append(f"- p-valor: {p:.4f}")
        summary.append(f"- A diferença {sig} (α = 0.05)")
    
    return "\n".join(summary)
