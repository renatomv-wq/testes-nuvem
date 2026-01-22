"""
Data processor module for Webinar Impact Analyzer
Handles data matching and control group creation
"""
import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
from datetime import datetime


def create_participant_summary(webinar_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary of participants with their first participation date
    and status at participation time
    """
    # Get unique participants with their first webinar participation
    participants = webinar_df.groupby('store_id').agg({
        'webinar_month': 'min',  # First participation month
        'Data do Webinar (mês)': 'count',  # Number of webinars attended
        'first_seller_at_parsed': 'first',
        'created_at_parsed': 'first',
        'Máx. Seller Segment Mes Webinar': 'first'  # Status at first webinar
    }).reset_index()
    
    participants.columns = [
        'store_id', 
        'first_webinar_month', 
        'webinar_count',
        'first_seller_at',
        'created_at',
        'status_at_webinar'
    ]
    
    return participants


def merge_datasets(
    webinar_df: pd.DataFrame, 
    store_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Merge webinar participation data with store data
    Returns: (participants_df, control_df)
    """
    # Create participant summary
    participants = create_participant_summary(webinar_df)
    
    # Get list of participant store_ids
    participant_ids = set(participants['store_id'].unique())
    
    # Merge participants with store data
    participants_merged = participants.merge(
        store_df[['store_id', 'gmv_d30', 'gmv_d90', 'current_status', 'store_age_days']],
        on='store_id',
        how='left'
    )
    
    # Create control group (stores that didn't participate)
    control_df = store_df[~store_df['store_id'].isin(participant_ids)].copy()
    
    return participants_merged, control_df


def calculate_status_change(status_before: str, status_after: str) -> str:
    """Calculate if status improved, declined, or stayed the same"""
    from src.data_loader import status_to_numeric
    
    before_num = status_to_numeric(status_before)
    after_num = status_to_numeric(status_after)
    
    if before_num < 0 or after_num < 0:
        return 'unknown'
    elif after_num > before_num:
        return 'upgrade'
    elif after_num < before_num:
        return 'downgrade'
    else:
        return 'maintained'


def categorize_store_age(age_days: float) -> str:
    """Categorize store by age in days"""
    if pd.isna(age_days) or age_days < 0:
        return 'unknown'
    elif age_days <= 90:
        return '0-3 meses'
    elif age_days <= 180:
        return '3-6 meses'
    elif age_days <= 365:
        return '6-12 meses'
    elif age_days <= 730:
        return '1-2 anos'
    else:
        return '2+ anos'


def prepare_analysis_data(
    participants_df: pd.DataFrame,
    control_df: pd.DataFrame
) -> Dict[str, pd.DataFrame]:
    """
    Prepare data for all three hypothesis analyses
    """
    # Add status change for participants
    participants_df = participants_df.copy()
    participants_df['status_change'] = participants_df.apply(
        lambda row: calculate_status_change(
            row.get('status_at_webinar', ''),
            row.get('current_status', '')
        ),
        axis=1
    )
    
    # Add age category
    participants_df['age_category'] = participants_df['store_age_days'].apply(categorize_store_age)
    control_df = control_df.copy()
    control_df['age_category'] = control_df['store_age_days'].apply(categorize_store_age)
    
    # Identify first sellers (converted after webinar)
    # We'll mark stores that had no seller status at webinar but now have sales
    participants_df['had_first_sale_after'] = participants_df.apply(
        lambda row: (
            row.get('status_at_webinar', '') in ['', 'no-seller'] and 
            row.get('current_status', '') not in ['', 'no-seller']
        ),
        axis=1
    )
    
    return {
        'participants': participants_df,
        'control': control_df
    }


def get_webinar_list(webinar_df: pd.DataFrame) -> List[str]:
    """Get unique list of webinars"""
    if 'webinar_name' in webinar_df.columns:
        return sorted(webinar_df['webinar_name'].dropna().unique().tolist())
    return []


def get_month_list(webinar_df: pd.DataFrame) -> List[str]:
    """Get unique list of months"""
    if 'Data do Webinar (mês)' in webinar_df.columns:
        return sorted(webinar_df['Data do Webinar (mês)'].dropna().unique().tolist())
    return []


def filter_by_webinar(webinar_df: pd.DataFrame, webinar_name: str) -> pd.DataFrame:
    """Filter webinar data by webinar name"""
    if webinar_name and webinar_name != 'Todos':
        return webinar_df[webinar_df['webinar_name'] == webinar_name]
    return webinar_df


def filter_by_month(webinar_df: pd.DataFrame, month: str) -> pd.DataFrame:
    """Filter webinar data by month"""
    if month and month != 'Todos':
        return webinar_df[webinar_df['Data do Webinar (mês)'] == month]
    return webinar_df


def filter_by_status(df: pd.DataFrame, status: str, column: str = 'status_at_webinar') -> pd.DataFrame:
    """Filter by seller status"""
    if status and status != 'Todos':
        return df[df[column] == status.lower()]
    return df
