"""
Data loader module for Webinar Impact Analyzer
Handles file upload and validation
"""
import pandas as pd
import streamlit as st
from typing import Tuple, Optional
from datetime import datetime


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in DD/MM/YYYY format"""
    if pd.isna(date_str) or date_str == '' or date_str is None:
        return None
    try:
        return datetime.strptime(str(date_str).strip(), '%d/%m/%Y')
    except ValueError:
        return None


def parse_webinar_month(month_str: str) -> Optional[str]:
    """Parse webinar month string to YYYY-MM format"""
    if pd.isna(month_str) or month_str == '':
        return None
    
    month_mapping = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }
    
    try:
        # Format: "Month 09 - September 2025"
        parts = str(month_str).lower().split()
        for word in parts:
            if word in month_mapping:
                year = parts[-1]
                return f"{year}-{month_mapping[word]}"
    except Exception:
        pass
    return None


def load_webinar_data(file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load and validate webinar participation data
    
    Expected columns:
    - store_id
    - Data do Webinar (mês)
    - webinar_name
    - webinar_status
    - first_seller_at
    - Máx. Seller Segment Mes Webinar
    - Máx. Seller Segment Mes-1 Webinar
    """
    try:
        # Try different separators
        try:
            df = pd.read_csv(file, sep='\t', encoding='utf-8')
        except Exception:
            file.seek(0)
            df = pd.read_csv(file, sep=',', encoding='utf-8')
        
        # Check required columns
        required_cols = ['store_id']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return None, f"Colunas obrigatórias faltando: {missing}"
        
        # Parse dates
        if 'first_seller_at' in df.columns:
            df['first_seller_at_parsed'] = df['first_seller_at'].apply(parse_date)
        
        if 'created_at' in df.columns:
            df['created_at_parsed'] = df['created_at'].apply(parse_date)
        
        # Parse webinar month
        if 'Data do Webinar (mês)' in df.columns:
            df['webinar_month'] = df['Data do Webinar (mês)'].apply(parse_webinar_month)
        
        # Normalize status columns
        status_cols = ['Máx. Seller Segment Mes Webinar', 'Máx. Seller Segment Mes-1 Webinar']
        for col in status_cols:
            if col in df.columns:
                df[col] = df[col].fillna('').str.strip().str.lower()
        
        return df, None
        
    except Exception as e:
        return None, f"Erro ao carregar arquivo: {str(e)}"


def load_store_data(file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load and validate store data (total base)
    
    Expected columns:
    - store_id
    - <Coluna 1> (GMV D-30)
    - <Coluna 2> (GMV D-90)
    - <Coluna 3> (current_status)
    - <Coluna 4> (store_age)
    """
    try:
        # Try different separators
        try:
            df = pd.read_csv(file, sep='\t', encoding='utf-8')
        except Exception:
            file.seek(0)
            df = pd.read_csv(file, sep=',', encoding='utf-8')
        
        # Rename columns for clarity
        cols = df.columns.tolist()
        rename_map = {}
        
        if len(cols) >= 5:
            # Assuming standard format from Nuvemshop export
            if '<Coluna 1>' in cols:
                rename_map['<Coluna 1>'] = 'gmv_d30'
            if '<Coluna 2>' in cols:
                rename_map['<Coluna 2>'] = 'gmv_d90'
            if '<Coluna 3>' in cols:
                rename_map['<Coluna 3>'] = 'current_status'
            if '<Coluna 4>' in cols:
                rename_map['<Coluna 4>'] = 'store_age_days'
        
        if rename_map:
            df = df.rename(columns=rename_map)
        
        # Check required columns
        if 'store_id' not in df.columns:
            return None, "Coluna 'store_id' não encontrada"
        
        # Convert GMV columns to numeric
        for col in ['gmv_d30', 'gmv_d90']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Convert store age to numeric
        if 'store_age_days' in df.columns:
            df['store_age_days'] = pd.to_numeric(df['store_age_days'], errors='coerce').fillna(0)
        
        # Normalize status
        if 'current_status' in df.columns:
            df['current_status'] = df['current_status'].fillna('').str.strip().str.lower()
        
        return df, None
        
    except Exception as e:
        return None, f"Erro ao carregar arquivo: {str(e)}"


def get_status_order():
    """Return seller status in order (for comparison)"""
    return {
        '': -1,
        'no-seller': 0,
        'struggling-seller': 1,
        'tiny-seller': 2,
        'small-seller': 3,
        'medium-seller': 4,
        'large-seller': 5,
        'top-seller': 6
    }


def status_to_numeric(status: str) -> int:
    """Convert status string to numeric value"""
    order = get_status_order()
    return order.get(str(status).lower().strip(), -1)
