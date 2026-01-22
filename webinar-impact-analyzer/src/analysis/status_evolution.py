"""
Status Evolution Analysis Module
Hypothesis 3: Webinar participants show better status evolution than control
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List, Tuple
from src.data_loader import get_status_order, status_to_numeric


def calculate_status_transition(
    status_before: str, 
    status_after: str
) -> Tuple[str, int]:
    """
    Calculate status transition type and magnitude
    
    Returns:
        (transition_type, magnitude)
        transition_type: 'upgrade', 'downgrade', 'maintained', 'unknown'
        magnitude: number of levels changed (positive for upgrade)
    """
    before_num = status_to_numeric(status_before)
    after_num = status_to_numeric(status_after)
    
    if before_num < 0 or after_num < 0:
        return 'unknown', 0
    
    magnitude = after_num - before_num
    
    if magnitude > 0:
        return 'upgrade', magnitude
    elif magnitude < 0:
        return 'downgrade', magnitude
    else:
        return 'maintained', 0


def create_transition_matrix(
    df: pd.DataFrame,
    status_before_col: str,
    status_after_col: str
) -> pd.DataFrame:
    """Create a transition matrix showing status changes"""
    status_order = ['no-seller', 'struggling-seller', 'tiny-seller', 
                    'small-seller', 'medium-seller', 'large-seller', 'top-seller']
    
    # Filter valid statuses
    valid_df = df[
        df[status_before_col].isin(status_order) & 
        df[status_after_col].isin(status_order)
    ].copy()
    
    if len(valid_df) == 0:
        return pd.DataFrame()
    
    # Create cross-tabulation
    matrix = pd.crosstab(
        valid_df[status_before_col],
        valid_df[status_after_col],
        normalize='index'
    ) * 100
    
    # Reindex to ensure all statuses are present
    matrix = matrix.reindex(index=status_order, columns=status_order, fill_value=0)
    
    return matrix


def analyze_status_evolution(
    participants_df: pd.DataFrame,
    control_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Analyze status evolution for participants vs control
    
    For participants: compare status_at_webinar vs current_status
    For control: we only have current_status, so we'll compare distributions
    """
    results = {}
    
    # Calculate transitions for participants
    participants_with_status = participants_df[
        participants_df['status_at_webinar'].notna() & 
        (participants_df['status_at_webinar'] != '') &
        participants_df['current_status'].notna() &
        (participants_df['current_status'] != '')
    ].copy()
    
    if len(participants_with_status) > 0:
        participants_with_status['transition_type'], participants_with_status['transition_magnitude'] = zip(*
            participants_with_status.apply(
                lambda row: calculate_status_transition(
                    row['status_at_webinar'],
                    row['current_status']
                ),
                axis=1
            )
        )
        
        # Count transitions
        transition_counts = participants_with_status['transition_type'].value_counts()
        total_valid = len(participants_with_status[participants_with_status['transition_type'] != 'unknown'])
        
        results['participants_transitions'] = {
            'total_analyzed': len(participants_with_status),
            'valid_transitions': total_valid,
            'upgrade_count': transition_counts.get('upgrade', 0),
            'downgrade_count': transition_counts.get('downgrade', 0),
            'maintained_count': transition_counts.get('maintained', 0),
            'unknown_count': transition_counts.get('unknown', 0),
        }
        
        if total_valid > 0:
            results['participants_transitions']['upgrade_rate'] = (
                transition_counts.get('upgrade', 0) / total_valid * 100
            )
            results['participants_transitions']['downgrade_rate'] = (
                transition_counts.get('downgrade', 0) / total_valid * 100
            )
            results['participants_transitions']['maintained_rate'] = (
                transition_counts.get('maintained', 0) / total_valid * 100
            )
        
        # Average magnitude of change
        valid_transitions = participants_with_status[
            participants_with_status['transition_type'] != 'unknown'
        ]
        if len(valid_transitions) > 0:
            results['participants_transitions']['avg_magnitude'] = (
                valid_transitions['transition_magnitude'].mean()
            )
        
        # Transition matrix for participants
        results['participants_matrix'] = create_transition_matrix(
            participants_with_status, 
            'status_at_webinar', 
            'current_status'
        ).to_dict()
        
        # Breakdown by initial status
        status_breakdown = []
        for status in participants_with_status['status_at_webinar'].unique():
            if not status:
                continue
            status_df = participants_with_status[participants_with_status['status_at_webinar'] == status]
            counts = status_df['transition_type'].value_counts()
            total = len(status_df[status_df['transition_type'] != 'unknown'])
            
            if total > 0:
                status_breakdown.append({
                    'initial_status': status,
                    'total': len(status_df),
                    'upgrade_rate': counts.get('upgrade', 0) / total * 100,
                    'downgrade_rate': counts.get('downgrade', 0) / total * 100,
                    'maintained_rate': counts.get('maintained', 0) / total * 100
                })
        
        results['by_initial_status'] = status_breakdown
    
    # Control group status distribution
    control_status = control_df['current_status'].value_counts()
    results['control_distribution'] = control_status.to_dict()
    
    # Participants current status distribution
    participants_current = participants_df['current_status'].value_counts()
    results['participants_current_distribution'] = participants_current.to_dict()
    
    # Chi-square test comparing distributions
    # Compare current status distribution between participants and control
    status_order = ['no-seller', 'struggling-seller', 'tiny-seller', 
                    'small-seller', 'medium-seller', 'large-seller', 'top-seller']
    
    p_counts = [participants_current.get(s, 0) for s in status_order]
    c_counts = [control_status.get(s, 0) for s in status_order]
    
    # Only include statuses with data in both groups
    valid_indices = [i for i in range(len(status_order)) 
                     if p_counts[i] > 0 or c_counts[i] > 0]
    
    if len(valid_indices) >= 2:
        contingency = np.array([
            [p_counts[i] for i in valid_indices],
            [c_counts[i] for i in valid_indices]
        ])
        
        try:
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
            results['distribution_chi_square'] = {
                'statistic': chi2,
                'p_value': p_value,
                'degrees_of_freedom': dof,
                'significant': p_value < 0.05
            }
        except Exception as e:
            results['distribution_chi_square'] = {
                'error': str(e)
            }
    
    return results


def get_sankey_data(
    participants_df: pd.DataFrame
) -> Dict[str, List]:
    """
    Prepare data for Sankey diagram showing status transitions
    """
    status_order = ['no-seller', 'struggling-seller', 'tiny-seller', 
                    'small-seller', 'medium-seller', 'large-seller', 'top-seller']
    
    # Filter valid data
    valid_df = participants_df[
        participants_df['status_at_webinar'].isin(status_order) & 
        participants_df['current_status'].isin(status_order)
    ].copy()
    
    if len(valid_df) == 0:
        return {'source': [], 'target': [], 'value': [], 'labels': []}
    
    # Create labels for both sides
    before_labels = [f"{s} (antes)" for s in status_order]
    after_labels = [f"{s} (depois)" for s in status_order]
    all_labels = before_labels + after_labels
    
    # Count transitions
    transitions = valid_df.groupby(['status_at_webinar', 'current_status']).size().reset_index(name='count')
    
    source = []
    target = []
    value = []
    
    for _, row in transitions.iterrows():
        before_idx = status_order.index(row['status_at_webinar'])
        after_idx = status_order.index(row['current_status']) + len(status_order)
        
        source.append(before_idx)
        target.append(after_idx)
        value.append(row['count'])
    
    return {
        'source': source,
        'target': target,
        'value': value,
        'labels': all_labels
    }


def get_status_summary_text(results: Dict[str, Any]) -> str:
    """Generate human-readable summary of status evolution analysis"""
    summary = []
    
    if 'participants_transitions' in results:
        trans = results['participants_transitions']
        
        summary.append("**Evolução de Status dos Participantes:**")
        summary.append(f"- Total analisado: {trans['total_analyzed']:,} lojas")
        summary.append(f"- Transições válidas: {trans['valid_transitions']:,}")
        
        if trans['valid_transitions'] > 0:
            summary.append(f"\n**Taxa de Transição:**")
            summary.append(f"- Upgrade (subiram de status): {trans.get('upgrade_rate', 0):.1f}%")
            summary.append(f"- Mantiveram: {trans.get('maintained_rate', 0):.1f}%")
            summary.append(f"- Downgrade (desceram): {trans.get('downgrade_rate', 0):.1f}%")
            
            if 'avg_magnitude' in trans:
                avg = trans['avg_magnitude']
                if avg > 0:
                    summary.append(f"\n**Magnitude média:** +{avg:.2f} níveis")
                else:
                    summary.append(f"\n**Magnitude média:** {avg:.2f} níveis")
    
    if 'distribution_chi_square' in results and 'p_value' in results['distribution_chi_square']:
        chi = results['distribution_chi_square']
        sig = "significativamente diferente" if chi['significant'] else "não significativamente diferente"
        summary.append(f"\n**Distribuição de status atual:**")
        summary.append(f"- Participantes vs Controle: {sig}")
        summary.append(f"- p-valor: {chi['p_value']:.4f}")
    
    return "\n".join(summary)
