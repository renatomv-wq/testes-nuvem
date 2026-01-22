"""
First Seller Analysis Module
Hypothesis 1: Webinar participation increases conversion to first sale
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, Tuple


def calculate_conversion_rate(df: pd.DataFrame, converted_col: str = 'had_first_sale_after') -> float:
    """Calculate conversion rate for a group"""
    if len(df) == 0:
        return 0.0
    return df[converted_col].sum() / len(df) * 100


def analyze_first_seller_conversion(
    participants_df: pd.DataFrame,
    control_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Analyze conversion to first seller between participants and control group
    
    Returns:
        Dictionary with analysis results including:
        - conversion rates
        - chi-square test results
        - breakdown by segments
    """
    results = {}
    
    # Filter to only stores that were no-seller at start
    # For participants: use status_at_webinar
    participants_no_seller = participants_df[
        participants_df['status_at_webinar'].isin(['', 'no-seller'])
    ].copy()
    
    # For control: we'll assume stores with current_status = no-seller never converted
    # and those with other status converted at some point
    # This is a simplification - ideally we'd have the same baseline
    control_no_seller = control_df[
        control_df['current_status'].isin(['', 'no-seller'])
    ].copy()
    
    # For a fair comparison, we need to estimate which control stores 
    # would have been no-seller at the same time period
    # Since we don't have historical data, we'll use all control stores
    # and mark those who are sellers as "converted"
    control_df_analysis = control_df.copy()
    control_df_analysis['had_first_sale_after'] = ~control_df_analysis['current_status'].isin(['', 'no-seller'])
    
    # Basic metrics
    results['participants'] = {
        'total': len(participants_df),
        'no_seller_at_start': len(participants_no_seller),
        'converted': participants_df['had_first_sale_after'].sum(),
        'conversion_rate': calculate_conversion_rate(participants_df, 'had_first_sale_after')
    }
    
    results['control'] = {
        'total': len(control_df),
        'sellers': control_df_analysis['had_first_sale_after'].sum(),
        'seller_rate': calculate_conversion_rate(control_df_analysis, 'had_first_sale_after')
    }
    
    # Chi-square test
    # Contingency table:
    #                   | Converted | Not Converted
    # Participants      |     a     |      b
    # Control           |     c     |      d
    
    a = results['participants']['converted']
    b = results['participants']['total'] - a
    c = results['control']['sellers']
    d = results['control']['total'] - c
    
    contingency_table = np.array([[a, b], [c, d]])
    
    if a + b > 0 and c + d > 0 and a + c > 0 and b + d > 0:
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
        results['chi_square'] = {
            'statistic': chi2,
            'p_value': p_value,
            'degrees_of_freedom': dof,
            'significant': p_value < 0.05,
            'contingency_table': contingency_table.tolist()
        }
    else:
        results['chi_square'] = {
            'statistic': None,
            'p_value': None,
            'significant': None,
            'error': 'Dados insuficientes para teste estatístico'
        }
    
    # Breakdown by webinar month
    if 'first_webinar_month' in participants_df.columns:
        monthly_conversion = participants_df.groupby('first_webinar_month').agg({
            'store_id': 'count',
            'had_first_sale_after': 'sum'
        }).reset_index()
        monthly_conversion.columns = ['month', 'total', 'converted']
        monthly_conversion['conversion_rate'] = (
            monthly_conversion['converted'] / monthly_conversion['total'] * 100
        ).round(2)
        results['by_month'] = monthly_conversion.to_dict('records')
    
    # Breakdown by store age
    if 'age_category' in participants_df.columns:
        age_conversion = participants_df.groupby('age_category').agg({
            'store_id': 'count',
            'had_first_sale_after': 'sum'
        }).reset_index()
        age_conversion.columns = ['age_category', 'total', 'converted']
        age_conversion['conversion_rate'] = (
            age_conversion['converted'] / age_conversion['total'] * 100
        ).round(2)
        results['by_age'] = age_conversion.to_dict('records')
    
    # Lift calculation
    if results['control']['seller_rate'] > 0:
        results['lift'] = (
            (results['participants']['conversion_rate'] - results['control']['seller_rate']) /
            results['control']['seller_rate'] * 100
        )
    else:
        results['lift'] = None
    
    return results


def get_first_seller_summary_text(results: Dict[str, Any]) -> str:
    """Generate human-readable summary of first seller analysis"""
    summary = []
    
    summary.append(f"**Participantes de Webinar:**")
    summary.append(f"- Total: {results['participants']['total']:,} lojas")
    summary.append(f"- Converteram para first seller: {results['participants']['converted']:,}")
    summary.append(f"- Taxa de conversão: {results['participants']['conversion_rate']:.1f}%")
    
    summary.append(f"\n**Grupo de Controle:**")
    summary.append(f"- Total: {results['control']['total']:,} lojas")
    summary.append(f"- São sellers: {results['control']['sellers']:,}")
    summary.append(f"- Taxa de sellers: {results['control']['seller_rate']:.1f}%")
    
    if results.get('lift') is not None:
        if results['lift'] > 0:
            summary.append(f"\n**Lift:** +{results['lift']:.1f}% (participantes convertem mais)")
        else:
            summary.append(f"\n**Lift:** {results['lift']:.1f}%")
    
    if results.get('chi_square') and results['chi_square'].get('p_value') is not None:
        p = results['chi_square']['p_value']
        sig = "estatisticamente significativa" if p < 0.05 else "não é estatisticamente significativa"
        summary.append(f"\n**Teste Chi-quadrado:**")
        summary.append(f"- p-valor: {p:.4f}")
        summary.append(f"- A diferença {sig} (α = 0.05)")
    
    return "\n".join(summary)
