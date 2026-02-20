#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Impacto - Lifecycle BR
Gerador de dashboard para análise de impacto das ações de Lifecycle
"""

import pandas as pd
import numpy as np
import json
import warnings
import os
import glob
import re
from datetime import datetime
from collections import Counter
from scipy import stats
warnings.filterwarnings('ignore')

print("=" * 70)
print("📊 DASHBOARD DE IMPACTO - LIFECYCLE BR")
print("=" * 70)

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Caminhos alternativos (para compatibilidade com bases existentes)
ALT_BASE_PATH_JAN = '/Users/renatovieira/Downloads/BR - Base Stores para Lifecycle - Jan ok.csv'
ALT_BASE_PATH_DEZ = '/Users/renatovieira/Downloads/base_br_diciembre_2024.csv'
ALT_BASE_PATH = ALT_BASE_PATH_JAN  # Base principal agora é janeiro
ALT_WEBINAR_PATH = '/Users/renatovieira/Downloads/Webinars - geral até Dezembro_25 - Raw Data_data (4).csv'
ALT_NEWSELLERS_PATH = '/Users/renatovieira/Downloads/Raw Data Total Stores (2).csv'

STATUS_ORDER = ['not informed', 'no-seller', 'struggling-seller', 'tiny-seller', 'small-seller', 
                'medium-seller', 'large-seller', 'top-seller']
STATUS_LABELS = {
    'not informed': 'Não Classificado',
    'no-seller': 'No Seller',
    'struggling-seller': 'Struggling',
    'tiny-seller': 'Tiny',
    'small-seller': 'Small',
    'medium-seller': 'Medium',
    'large-seller': 'Large',
    'top-seller': 'Top',
    'not informed': 'Não informado'
}
SELLER_STATUS = ['tiny-seller', 'small-seller', 'medium-seller', 'large-seller', 'top-seller']

# Categorias de risco (binário: 0 = sem risco, 1 = com risco)
RISK_QUARTILES = [
    {'name': 'Não Classificado', 'min': -1, 'max': -0.5, 'color': '#6b7280', 'special': 'not_classified'},
    {'name': 'Sem Risco', 'min': -0.5, 'max': 0.5, 'color': '#22c55e'},  # churn = 0
    {'name': 'Com Risco de Churn', 'min': 0.5, 'max': 1.5, 'color': '#ef4444'},  # churn = 1
]

# Produtos Merchant Services
MERCHANT_COLS = ['nuvemmarketing', 'nuvempago', 'nuvemchat', 'nuvemenvio', 'pdv']
PRODUTO_NAMES = {
    'nuvemmarketing': 'Nuvem Marketing',
    'nuvempago': 'Nuvem Pago', 
    'nuvemchat': 'Nuvem Chat',
    'nuvemenvio': 'Nuvem Envio',
    'pdv': 'PDV'
}

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def extract_date_from_filename(filename):
    """Extrai data do nome do arquivo"""
    patterns = [
        r'(\d{4})[-_](\d{2})',
        r'(\d{4})(\d{2})',
        r'([a-zA-Z]+)[-_]?(\d{4})',
    ]
    
    month_map = {
        'janeiro': '01', 'fevereiro': '02', 'marco': '03', 'abril': '04',
        'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
        'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12',
        'diciembre': '12', 'january': '01', 'february': '02', 'march': '03',
        'april': '04', 'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }
    
    basename = os.path.basename(filename).lower()
    
    for pattern in patterns:
        match = re.search(pattern, basename)
        if match:
            g1, g2 = match.groups()
            if g1.isdigit():
                return f"{g1}-{g2}"
            elif g1.lower() in month_map:
                return f"{g2}-{month_map[g1.lower()]}"
    
    mtime = os.path.getmtime(filename)
    dt = datetime.fromtimestamp(mtime)
    return dt.strftime('%Y-%m')

def find_all_files_sorted(folder, pattern='*.csv'):
    """Encontra todos os arquivos em uma pasta, ordenados por data"""
    files = glob.glob(os.path.join(folder, pattern))
    if not files:
        return []
    files_with_dates = [(f, extract_date_from_filename(f)) for f in files]
    files_with_dates.sort(key=lambda x: x[1], reverse=True)
    return files_with_dates

def find_latest_file(folder, pattern='*.csv'):
    """Encontra o arquivo mais recente em uma pasta"""
    files = find_all_files_sorted(folder, pattern)
    if not files:
        return None
    return files[0][0]

def load_base_geral():
    """Carrega todas as bases gerais de lojas - Janeiro como principal, Dezembro para campos legados"""
    data_folder = os.path.join(DATA_DIR, 'base_geral')
    files = find_all_files_sorted(data_folder)
    
    bases = {}
    campos_nao_disponiveis = []
    
    if files:
        for filepath, date_str in files:
            print(f"  📂 Base encontrada: {os.path.basename(filepath)} ({date_str})")
            df = pd.read_csv(filepath, low_memory=False)
            if 'merchant_finance_status' in df.columns:
                df = df[df['merchant_finance_status'] == 'paying'].copy()
            bases[date_str] = df
    
    # Usar base de janeiro como principal
    if not bases and os.path.exists(ALT_BASE_PATH_JAN):
        print(f"  📂 Usando base de JANEIRO: {os.path.basename(ALT_BASE_PATH_JAN)}")
        df_jan = pd.read_csv(ALT_BASE_PATH_JAN, low_memory=False)
        
        # Mapear campos de janeiro para formato esperado
        df_jan = df_jan.rename(columns={
            'store_id': 'id_store',
            'current_segment': 'status_seller',
            'main_user_email': 'main_user',
            'domain': 'store_name',
            'gmv30': 'gmv_mes_local',
            'gmv90': 'gmv_90d_local',
            'orders30': 'orders_mes',
            'orders90': 'orders_90d',
            'current_plan_name': 'plan',
            'current_plan_type': 'plan_type',
        })
        
        # Calcular aging (dias desde criação)
        df_jan['created_at'] = pd.to_datetime(df_jan['created_at'], errors='coerce')
        df_jan['aging'] = (pd.Timestamp.now() - df_jan['created_at']).dt.days
        df_jan['aging_clean'] = df_jan['aging'].fillna(0)
        
        # Campos que não existem em janeiro - marcar como não disponíveis
        df_jan['merchant_finance_status'] = 'paying'  # Base já vem filtrada
        
        # Verificar se a base de janeiro já tem dados de churn (is_potential_churn)
        if 'is_potential_churn' in df_jan.columns:
            print(f"  ✅ Usando dados de churn da BASE DE JANEIRO (is_potential_churn)")
            # Criar predictive_churn_probability a partir de is_potential_churn
            # is_potential_churn é binário (0/1), vamos manter assim
            df_jan['predictive_churn_probability'] = df_jan['is_potential_churn']
            df_jan['predictive_churn'] = df_jan['is_potential_churn'].apply(
                lambda x: 'high' if x == 1 else ('low' if x == 0 else None)
            )
            
            # Usar potential_churn_profile se existir
            if 'potential_churn_profile' in df_jan.columns:
                df_jan['predictive_churn_profile'] = df_jan['potential_churn_profile']
            
            lojas_com_churn = df_jan['predictive_churn_probability'].notna().sum()
            print(f"  ✅ Churn disponível para {lojas_com_churn:,} de {len(df_jan):,} lojas ({lojas_com_churn/len(df_jan)*100:.1f}%)")
        
        # Carregar base de dezembro apenas para merchant services (se necessário)
        if os.path.exists(ALT_BASE_PATH_DEZ):
            print(f"  📂 Enriquecendo com dados de DEZEMBRO (merchant services)...")
            df_dez = pd.read_csv(ALT_BASE_PATH_DEZ, low_memory=False)
            df_dez = df_dez[df_dez['merchant_finance_status'] == 'paying'].copy()
            
            # Campos a buscar de dezembro (apenas merchant services)
            campos_dez = ['id_store', 'nuvempago', 'nuvemenvio', 'nuvemmarketing', 'nuvemchat', 'pdv']
            
            # Se não tiver churn em janeiro, buscar de dezembro também
            if 'is_potential_churn' not in df_jan.columns:
                campos_dez.extend(['predictive_churn_probability', 'predictive_churn', 
                                  'predictive_churn_life_stage', 'predictive_churn_profile'])
            
            campos_disponiveis = [c for c in campos_dez if c in df_dez.columns]
            
            # Remover duplicatas de dezembro antes do merge (pegar a primeira ocorrência)
            df_dez_unique = df_dez[campos_disponiveis].drop_duplicates(subset='id_store', keep='first')
            
            df_jan = df_jan.merge(
                df_dez_unique,
                on='id_store',
                how='left'
            )
            
            lojas_com_ms = df_jan['nuvempago'].notna().sum()
            print(f"  ✅ Merchant Services disponível para {lojas_com_ms:,} de {len(df_jan):,} lojas ({lojas_com_ms/len(df_jan)*100:.1f}%)")
            
            # Lojas sem merchant services
            lojas_sem_ms = df_jan['nuvempago'].isna().sum()
            if lojas_sem_ms > 0:
                campos_nao_disponiveis.append(f"Merchant Services: {lojas_sem_ms:,} lojas sem dados (novas)")
        else:
            # Sem base de dezembro
            for col in ['nuvempago', 'nuvemenvio', 'nuvemmarketing', 'nuvemchat', 'pdv']:
                df_jan[col] = None
            campos_nao_disponiveis.append("Merchant Services: não disponível (base dez não encontrada)")
        
        bases['2026-01'] = df_jan
        
        # Informar campos não disponíveis
        if campos_nao_disponiveis:
            print(f"  ⚠️ CAMPOS NÃO ATUALIZADOS:")
            for campo in campos_nao_disponiveis:
                print(f"     - {campo}")
    
    # Fallback para base de dezembro apenas
    elif not bases and os.path.exists(ALT_BASE_PATH_DEZ):
        print(f"  📂 Usando base de DEZEMBRO (fallback): {os.path.basename(ALT_BASE_PATH_DEZ)}")
        df = pd.read_csv(ALT_BASE_PATH_DEZ, low_memory=False)
        df = df[df['merchant_finance_status'] == 'paying'].copy()
        bases['2024-12'] = df
    
    return bases

def load_projeto(projeto_nome, alt_path=None):
    """Carrega base de um projeto"""
    data_folder = os.path.join(DATA_DIR, 'projetos', projeto_nome)
    latest = find_latest_file(data_folder)
    
    if latest:
        print(f"  📂 {projeto_nome}: {os.path.basename(latest)}")
        return pd.read_csv(latest, low_memory=False)
    elif alt_path and os.path.exists(alt_path):
        print(f"  📂 {projeto_nome}: usando arquivo alternativo")
        return pd.read_csv(alt_path, low_memory=False)
    else:
        print(f"  ⚠️ {projeto_nome}: base não encontrada")
        return None

def load_new_sellers():
    """Carrega todas as bases de new sellers por mês"""
    data_folder = os.path.join(DATA_DIR, 'new_sellers')
    files = find_all_files_sorted(data_folder)
    
    new_sellers_por_mes = {}
    
    if files:
        for filepath, date_str in files:
            print(f"  📂 New Sellers {date_str}: {os.path.basename(filepath)}")
            try:
                df = pd.read_csv(filepath, low_memory=False)
            except:
                df = pd.read_csv(filepath, encoding='utf-16-le', sep='\t', low_memory=False)
            new_sellers_por_mes[date_str] = df
    
    if not new_sellers_por_mes and os.path.exists(ALT_NEWSELLERS_PATH):
        print(f"  📂 New Sellers: usando arquivo alternativo")
        try:
            df = pd.read_csv(ALT_NEWSELLERS_PATH, encoding='utf-16-le', sep='\t', low_memory=False)
        except:
            df = pd.read_csv(ALT_NEWSELLERS_PATH, low_memory=False)
        new_sellers_por_mes['2026-01'] = df
    
    return new_sellers_por_mes

def classify_risk(prob, status=None):
    """Classifica risco em categorias (binário: 0 = sem risco, 1 = com risco)"""
    if pd.isna(prob):
        return 'Não Classificado'
    elif prob == 0:
        return 'Sem Risco'
    elif prob == 1:
        return 'Com Risco de Churn'
    else:
        # Para probabilidades contínuas (base antiga)
        if prob <= 0.25:
            return 'Sem Risco'
        else:
            return 'Com Risco de Churn'

def get_status_tier(status):
    """Retorna o nível do status para comparação"""
    if status not in STATUS_ORDER:
        return -1
    return STATUS_ORDER.index(status)

def get_transition_type(status_de, status_para):
    """
    Classifica o tipo de transição considerando regras especiais.
    - Lojas "not informed" só são upgrade se forem para struggling ou melhor
    - "not informed" → "no-seller" é downgrade (negativo)
    """
    tier_de = get_status_tier(status_de)
    tier_para = get_status_tier(status_para)
    
    # Regra especial: "not informed" → "no-seller" é downgrade
    if status_de == 'not informed':
        if status_para == 'no-seller':
            return 'downgrade'
        elif status_para == 'not informed':
            return 'estavel'
        else:
            return 'upgrade'
    
    # Regra padrão para outros status
    if tier_para > tier_de:
        return 'upgrade'
    elif tier_para < tier_de:
        return 'downgrade'
    else:
        return 'estavel'

def get_product_combo(row):
    """Gera string da combinação de produtos"""
    produtos = []
    for col in MERCHANT_COLS:
        if row.get(col, False):
            produtos.append(PRODUTO_NAMES[col])
    return ' + '.join(sorted(produtos)) if produtos else 'Nenhum'

# =============================================================================
# CARREGAR DADOS
# =============================================================================
print("\n📂 Carregando dados...")

# Bases gerais
bases_mensais = load_base_geral()
meses_disponiveis = sorted(bases_mensais.keys(), reverse=True)
print(f"  ✅ Meses disponíveis: {', '.join(meses_disponiveis)}")

# Base atual
mes_atual = meses_disponiveis[0] if meses_disponiveis else '2024-12'
lojas_ativas = bases_mensais[mes_atual].copy()
print(f"  ✅ Base atual ({mes_atual}): {len(lojas_ativas):,} lojas pagantes")

# Projeto Webinars
webinars_df = load_projeto('webinars', ALT_WEBINAR_PATH)
webinar_funil = {'total_registros': 0, 'total_live': 0, 'total_ondemand': 0, 'total_participaram': 0, 'por_mes': []}

if webinars_df is not None:
    webinars_com_cobertura = webinars_df[webinars_df['Cobertura'].str.strip() == 'Com cobertura'].copy()
    ids_webinar = set(webinars_com_cobertura['store_id'].unique())
    print(f"  ✅ Lojas com Webinar: {len(ids_webinar):,}")
    
    # Análise do funil
    print("  📊 Analisando funil de webinars...")
    
    # Contagem por status (na base completa, não só com cobertura)
    status_counts = webinars_df['webinar_status'].value_counts()
    webinar_funil['total_registros'] = int(status_counts.get('registered', 0))
    webinar_funil['total_live'] = int(status_counts.get('live', 0))
    webinar_funil['total_ondemand'] = int(status_counts.get('on-demand', 0))
    webinar_funil['total_participaram'] = webinar_funil['total_live'] + webinar_funil['total_ondemand']
    
    # Total geral (todos os registros únicos)
    webinar_funil['total_geral'] = len(webinars_df)
    
    # Percentuais
    total = webinar_funil['total_geral']
    if total > 0:
        webinar_funil['pct_live'] = round(webinar_funil['total_live'] / total * 100, 1)
        webinar_funil['pct_ondemand'] = round(webinar_funil['total_ondemand'] / total * 100, 1)
        webinar_funil['pct_participaram'] = round(webinar_funil['total_participaram'] / total * 100, 1)
    
    # Análise mensal
    if 'Data do Webinar (mês)' in webinars_df.columns:
        mes_col = 'Data do Webinar (mês)'
        meses = webinars_df[mes_col].dropna().unique()
        
        for mes in sorted(meses):
            df_mes = webinars_df[webinars_df[mes_col] == mes]
            total_mes = len(df_mes)
            
            if total_mes > 0:
                status_mes = df_mes['webinar_status'].value_counts()
                registros = int(status_mes.get('registered', 0))
                live = int(status_mes.get('live', 0))
                ondemand = int(status_mes.get('on-demand', 0))
                participaram = live + ondemand
                
                # Extrair nome curto do mês
                mes_nome = mes.replace('Month ', '').split(' - ')[0] if 'Month' in str(mes) else str(mes)
                
                webinar_funil['por_mes'].append({
                    'mes': mes,
                    'mes_curto': mes_nome,
                    'total': total_mes,
                    'registros': registros,
                    'live': live,
                    'ondemand': ondemand,
                    'participaram': participaram,
                    'pct_live': round(live / total_mes * 100, 1) if total_mes > 0 else 0,
                    'pct_ondemand': round(ondemand / total_mes * 100, 1) if total_mes > 0 else 0,
                    'pct_participaram': round(participaram / total_mes * 100, 1) if total_mes > 0 else 0,
                })
        
        # Ordenar por mês
        webinar_funil['por_mes'].sort(key=lambda x: x['mes'])
    
    print(f"  ✅ Funil: {webinar_funil['total_geral']:,} total → {webinar_funil['total_live']:,} live ({webinar_funil.get('pct_live', 0)}%) + {webinar_funil['total_ondemand']:,} on-demand ({webinar_funil.get('pct_ondemand', 0)}%)")
else:
    ids_webinar = set()

# New Sellers
new_sellers_por_mes = load_new_sellers()

# Onboarding V2 - Grupo Teste
print("\n📂 Carregando bases de Onboarding...")
onboarding_grupo_teste = None
onboarding_potential = None
onboarding_path_teste = os.path.join(DATA_DIR, 'onboarding_grupo_teste.csv')
onboarding_path_potential = os.path.join(DATA_DIR, 'onboarding_potential_sellers.csv')

if os.path.exists(onboarding_path_teste):
    onboarding_grupo_teste = pd.read_csv(onboarding_path_teste, low_memory=False)
    print(f"  ✅ Onboarding Grupo Teste: {len(onboarding_grupo_teste):,} lojas")
else:
    print(f"  ⚠️ Arquivo não encontrado: {onboarding_path_teste}")

if os.path.exists(onboarding_path_potential):
    onboarding_potential = pd.read_csv(onboarding_path_potential, low_memory=False)
    print(f"  ✅ Onboarding Potential Sellers: {len(onboarding_potential):,} lojas")
else:
    print(f"  ⚠️ Arquivo não encontrado: {onboarding_path_potential}")

# =============================================================================
# PREPARAR FLAGS E MÉTRICAS
# =============================================================================
print("\n🔧 Preparando dados...")

# Identificar coluna de ID
id_col = 'id_store' if 'id_store' in lojas_ativas.columns else 'store_id'

# Flag de webinar
lojas_ativas['tem_webinar'] = lojas_ativas[id_col].isin(ids_webinar)

# Quantidade de webinars
if webinars_df is not None:
    webinars_por_loja = webinars_com_cobertura.groupby('store_id').size().reset_index(name='qtd_webinars')
    lojas_ativas = lojas_ativas.merge(webinars_por_loja, left_on=id_col, right_on='store_id', how='left')
    lojas_ativas['qtd_webinars'] = lojas_ativas['qtd_webinars'].fillna(0).astype(int)
else:
    lojas_ativas['qtd_webinars'] = 0

# Flag de onboarding
ids_onboarding = set()
if onboarding_grupo_teste is not None:
    ids_onboarding = set(onboarding_grupo_teste['Store ID'].dropna().astype(int))
lojas_ativas['tem_onboarding'] = lojas_ativas[id_col].isin(ids_onboarding)

# Merchant Services
for col in MERCHANT_COLS:
    if col in lojas_ativas.columns:
        lojas_ativas[col] = lojas_ativas[col].astype(str).str.lower().isin(['true', '1', 'yes'])
    else:
        lojas_ativas[col] = False
lojas_ativas['qtd_merchant_services'] = lojas_ativas[MERCHANT_COLS].sum(axis=1)

# Combinação de produtos
lojas_ativas['combo_produtos'] = lojas_ativas.apply(get_product_combo, axis=1)

# Classificar risco (considerando status para identificar não classificados)
lojas_ativas['risk_quartile'] = lojas_ativas.apply(
    lambda row: classify_risk(row['predictive_churn_probability'], row['status_seller']), axis=1
)

# Aging
lojas_ativas['aging_clean'] = pd.to_numeric(lojas_ativas['aging'], errors='coerce')

def categorize_aging_simple(days):
    if pd.isna(days): return 'N/A'
    elif days <= 90: return '0-90 dias'
    elif days <= 365: return '91-365 dias'
    elif days <= 730: return '1-2 anos'
    else: return '2+ anos'

lojas_ativas['aging_faixa_simples'] = lojas_ativas['aging_clean'].apply(categorize_aging_simple)

# =============================================================================
# MATRIZ DE TRANSIÇÃO (Dezembro → Janeiro)
# =============================================================================
print("\n📊 Calculando Matriz de Transição...")

matriz_transicao = {
    'disponivel': False,
    'mes_anterior': None,
    'mes_atual': mes_atual,
    'upgrade': 0,
    'downgrade': 0,
    'estavel': 0,
    'pct_upgrade': 0,
    'pct_downgrade': 0,
    'pct_estavel': 0,
    'detalhes': [],
    'top_upgrades': [],
    'top_downgrades': []
}

# Tentar carregar base de dezembro para comparação
base_dezembro = None
if os.path.exists(ALT_BASE_PATH_DEZ):
    print(f"  📂 Carregando base de Dezembro para comparação...")
    base_dezembro = pd.read_csv(ALT_BASE_PATH_DEZ, low_memory=False)
    base_dezembro = base_dezembro[base_dezembro['merchant_finance_status'] == 'paying'].copy()

if base_dezembro is not None:
    base_anterior = base_dezembro
    base_atual = lojas_ativas
    mes_anterior = '2024-12'
    
    print(f"  📈 Comparando: {mes_anterior} → {mes_atual}")
    
    id_col_ant = 'id_store' if 'id_store' in base_anterior.columns else 'store_id'
    id_col_atu = 'id_store' if 'id_store' in base_atual.columns else 'store_id'
    
    merged = base_anterior[[id_col_ant, 'status_seller']].merge(
        base_atual[[id_col_atu, 'status_seller']],
        left_on=id_col_ant, right_on=id_col_atu,
        how='inner',  # Apenas lojas em ambas
        suffixes=('_antes', '_depois')
    )
    
    merged['tier_antes'] = merged['status_seller_antes'].apply(get_status_tier)
    merged['tier_depois'] = merged['status_seller_depois'].apply(get_status_tier)
    
    # Incluir todas as lojas com status no STATUS_ORDER (agora inclui "not informed")
    lojas_continuam = merged[(merged['tier_antes'] >= 0) & (merged['tier_depois'] >= 0)]
    
    # Usar get_transition_type para classificar corretamente
    lojas_continuam = lojas_continuam.copy()
    lojas_continuam['tipo_transicao'] = lojas_continuam.apply(
        lambda x: get_transition_type(x['status_seller_antes'], x['status_seller_depois']), axis=1
    )
    
    # Separar lojas que eram "not informed" em dezembro (para não distorcer números)
    lojas_not_informed = lojas_continuam[lojas_continuam['status_seller_antes'] == 'not informed']
    lojas_com_status = lojas_continuam[lojas_continuam['status_seller_antes'] != 'not informed']
    
    # Calcular totais APENAS para lojas que tinham status em dezembro
    upgrade = len(lojas_com_status[lojas_com_status['tipo_transicao'] == 'upgrade'])
    downgrade = len(lojas_com_status[lojas_com_status['tipo_transicao'] == 'downgrade'])
    estavel = len(lojas_com_status[lojas_com_status['tipo_transicao'] == 'estavel'])
    
    total = upgrade + downgrade + estavel
    
    # Métricas para "not informed" separadas
    ni_total = len(lojas_not_informed)
    ni_virou_seller = len(lojas_not_informed[lojas_not_informed['tipo_transicao'] == 'upgrade'])
    ni_virou_no_seller = len(lojas_not_informed[lojas_not_informed['status_seller_depois'] == 'no-seller'])
    ni_pct_seller = round(ni_virou_seller / ni_total * 100, 1) if ni_total > 0 else 0
    ni_pct_no_seller = round(ni_virou_no_seller / ni_total * 100, 1) if ni_total > 0 else 0
    
    # Calcular top transições (excluindo not informed)
    lojas_upgrade = lojas_com_status[lojas_com_status['tipo_transicao'] == 'upgrade']
    lojas_downgrade = lojas_com_status[lojas_com_status['tipo_transicao'] == 'downgrade']
    
    top_upgrades = lojas_upgrade.groupby(['status_seller_antes', 'status_seller_depois']).size().sort_values(ascending=False).head(5)
    top_downgrades = lojas_downgrade.groupby(['status_seller_antes', 'status_seller_depois']).size().sort_values(ascending=False).head(5)
    
    # Calcular entradas e saídas
    jan_ids = set(base_atual[id_col_atu].dropna().astype(int))
    dez_ids = set(base_anterior[id_col_ant].dropna().astype(int))
    
    lojas_novas = len(jan_ids - dez_ids)
    lojas_sairam = len(dez_ids - jan_ids)
    
    # Criar matriz de transição completa (crosstab)
    matriz_crosstab = pd.crosstab(
        lojas_continuam['status_seller_antes'], 
        lojas_continuam['status_seller_depois'],
        margins=False
    )
    
    # Reordenar pelo STATUS_ORDER
    status_presentes = [s for s in STATUS_ORDER if s in matriz_crosstab.index or s in matriz_crosstab.columns]
    
    # Garantir que todos os status estejam na matriz
    for status in status_presentes:
        if status not in matriz_crosstab.index:
            matriz_crosstab.loc[status] = 0
        if status not in matriz_crosstab.columns:
            matriz_crosstab[status] = 0
    
    # Reordenar
    matriz_crosstab = matriz_crosstab.reindex(index=status_presentes, columns=status_presentes, fill_value=0)
    
    # Converter para formato serializável
    matriz_visual = []
    for status_de in status_presentes:
        row = {
            'de': status_de,
            'de_label': STATUS_LABELS.get(status_de, status_de),
            'transicoes': []
        }
        total_de = int(matriz_crosstab.loc[status_de].sum())
        for status_para in status_presentes:
            count = int(matriz_crosstab.loc[status_de, status_para])
            pct = round(count / total_de * 100, 1) if total_de > 0 else 0
            
            # Determinar tipo de transição usando a nova função
            tipo = get_transition_type(status_de, status_para)
            
            row['transicoes'].append({
                'para': status_para,
                'para_label': STATUS_LABELS.get(status_para, status_para),
                'count': count,
                'pct': pct,
                'tipo': tipo
            })
        row['total'] = total_de
        matriz_visual.append(row)
    
    # Calcular fluxo líquido por status com detalhamento de origem/destino
    fluxo_liquido = []
    for status in status_presentes:
        # Quantos estavam nesse status em dezembro
        antes = int((lojas_continuam['status_seller_antes'] == status).sum())
        # Quantos estão nesse status em janeiro (dentre os que continuam)
        depois = int((lojas_continuam['status_seller_depois'] == status).sum())
        # Variação líquida
        variacao = depois - antes
        pct_var = round((variacao / antes * 100), 1) if antes > 0 else 0
        
        # Detalhamento: de onde vieram os novos (entradas) e para onde foram os que saíram (saídas)
        # Entradas: lojas que NÃO estavam nesse status e agora estão
        entradas_df = lojas_continuam[(lojas_continuam['status_seller_antes'] != status) & 
                                       (lojas_continuam['status_seller_depois'] == status)]
        entradas_por_origem = entradas_df['status_seller_antes'].value_counts().head(5).to_dict()
        entradas_detalhe = [
            {'de': STATUS_LABELS.get(orig, orig), 'count': int(cnt)}
            for orig, cnt in entradas_por_origem.items()
        ]
        
        # Saídas: lojas que ESTAVAM nesse status e agora não estão
        saidas_df = lojas_continuam[(lojas_continuam['status_seller_antes'] == status) & 
                                     (lojas_continuam['status_seller_depois'] != status)]
        saidas_por_destino = saidas_df['status_seller_depois'].value_counts().head(5).to_dict()
        saidas_detalhe = [
            {'para': STATUS_LABELS.get(dest, dest), 'count': int(cnt)}
            for dest, cnt in saidas_por_destino.items()
        ]
        
        fluxo_liquido.append({
            'status': status,
            'label': STATUS_LABELS.get(status, status),
            'antes': antes,
            'depois': depois,
            'variacao': variacao,
            'pct_variacao': pct_var,
            'entradas': int(len(entradas_df)),
            'saidas': int(len(saidas_df)),
            'entradas_detalhe': entradas_detalhe,
            'saidas_detalhe': saidas_detalhe
        })
    
    # Ordenar pelo maior ganho/perda
    fluxo_liquido = sorted(fluxo_liquido, key=lambda x: x['variacao'], reverse=True)
    
    matriz_transicao = {
        'disponivel': True,
        'mes_anterior': mes_anterior,
        'mes_atual': mes_atual,
        'upgrade': upgrade,
        'downgrade': downgrade,
        'estavel': estavel,
        'pct_upgrade': round(upgrade / total * 100, 1) if total > 0 else 0,
        'pct_downgrade': round(downgrade / total * 100, 1) if total > 0 else 0,
        'pct_estavel': round(estavel / total * 100, 1) if total > 0 else 0,
        'lojas_novas': lojas_novas,
        'lojas_sairam': lojas_sairam,
        'total_comparado': total,
        # Dados de "não informados" separados
        'not_informed': {
            'total': ni_total,
            'virou_seller': ni_virou_seller,
            'virou_no_seller': ni_virou_no_seller,
            'pct_seller': ni_pct_seller,
            'pct_no_seller': ni_pct_no_seller
        },
        'top_upgrades': [
            {'de': STATUS_LABELS.get(de, de), 'para': STATUS_LABELS.get(para, para), 'count': int(count)}
            for (de, para), count in top_upgrades.items()
        ],
        'top_downgrades': [
            {'de': STATUS_LABELS.get(de, de), 'para': STATUS_LABELS.get(para, para), 'count': int(count)}
            for (de, para), count in top_downgrades.items()
        ],
        'matriz_visual': matriz_visual,
        'status_order': [STATUS_LABELS.get(s, s) for s in status_presentes],
        'fluxo_liquido': fluxo_liquido,
        'detalhes': []
    }
    
    print(f"  ✅ Upgrade: {upgrade:,} ({matriz_transicao['pct_upgrade']}%)")
    print(f"  ➡️ Estável: {estavel:,} ({matriz_transicao['pct_estavel']}%)")
    print(f"  ⬇️ Downgrade: {downgrade:,} ({matriz_transicao['pct_downgrade']}%)")
    print(f"  📊 Não Classificados (Dez): {ni_total:,} → {ni_virou_seller:,} viraram seller ({ni_pct_seller}%)")
    print(f"  🆕 Lojas novas: {lojas_novas:,} | 🚪 Saíram: {lojas_sairam:,}")

elif len(meses_disponiveis) >= 2:
    mes_anterior = meses_disponiveis[1]
    base_anterior = bases_mensais[mes_anterior]
    base_atual = bases_mensais[mes_atual]
    
    print(f"  📈 Comparando: {mes_anterior} → {mes_atual}")
    
    id_col_ant = 'id_store' if 'id_store' in base_anterior.columns else 'store_id'
    id_col_atu = 'id_store' if 'id_store' in base_atual.columns else 'store_id'
    
    merged = base_anterior[[id_col_ant, 'status_seller']].merge(
        base_atual[[id_col_atu, 'status_seller']],
        left_on=id_col_ant, right_on=id_col_atu,
        how='outer',
        suffixes=('_antes', '_depois')
    )
    
    merged['tier_antes'] = merged['status_seller_antes'].apply(get_status_tier)
    merged['tier_depois'] = merged['status_seller_depois'].apply(get_status_tier)
    
    lojas_continuam = merged[(merged['tier_antes'] >= 0) & (merged['tier_depois'] >= 0)]
    
    # Usar get_transition_type para classificar corretamente
    lojas_continuam = lojas_continuam.copy()
    lojas_continuam['tipo_transicao'] = lojas_continuam.apply(
        lambda x: get_transition_type(x['status_seller_antes'], x['status_seller_depois']), axis=1
    )
    
    upgrade = len(lojas_continuam[lojas_continuam['tipo_transicao'] == 'upgrade'])
    downgrade = len(lojas_continuam[lojas_continuam['tipo_transicao'] == 'downgrade'])
    estavel = len(lojas_continuam[lojas_continuam['tipo_transicao'] == 'estavel'])
    
    total = upgrade + downgrade + estavel
    
    matriz_transicao = {
        'disponivel': True,
        'mes_anterior': mes_anterior,
        'mes_atual': mes_atual,
        'upgrade': upgrade,
        'downgrade': downgrade,
        'estavel': estavel,
        'pct_upgrade': round(upgrade / total * 100, 1) if total > 0 else 0,
        'pct_downgrade': round(downgrade / total * 100, 1) if total > 0 else 0,
        'pct_estavel': round(estavel / total * 100, 1) if total > 0 else 0,
        'top_upgrades': [],
        'top_downgrades': [],
        'detalhes': []
    }
    
    print(f"  ✅ Upgrade: {upgrade:,} | Estável: {estavel:,} | Downgrade: {downgrade:,}")
else:
    print("  ⚠️ Apenas 1 mês disponível")

# Calcular Matriz de Transição por ICP (agora que temos base_dezembro)
# O ICP é fixo - usamos o valor de janeiro para classificar as lojas
# e comparamos status_seller de dezembro vs janeiro

ICP_ORDER = ['ICP 1', 'ICP 2', 'ICP 3', 'ICP 4', 'Não Classificado']

# Criar coluna ICP em lojas_ativas
if 'model_icp' in lojas_ativas.columns:
    lojas_ativas['icp'] = lojas_ativas['model_icp'].fillna('Não Classificado')
    lojas_ativas['icp'] = lojas_ativas['icp'].replace({'Fall Back': 'Não Classificado'})

icp_transicao = []

if matriz_transicao['disponivel'] and base_dezembro is not None and 'icp' in lojas_ativas.columns:
    print("  📊 Calculando matriz de transição por ICP...")
    
    # Preparar base de dezembro
    base_dez = base_dezembro.copy()
    if 'id_store' not in base_dez.columns and 'store_id' in base_dez.columns:
        base_dez = base_dez.rename(columns={'store_id': 'id_store'})
    
    for icp in ICP_ORDER:
        if icp == 'Não Classificado':
            continue
        
        # Lojas com esse ICP em janeiro (ICP é fixo)
        lojas_icp = lojas_ativas[lojas_ativas['icp'] == icp][['id_store', 'status_seller']].copy()
        lojas_icp = lojas_icp.rename(columns={'status_seller': 'status_jan'})
        
        # Merge com dezembro para pegar status anterior
        merged = lojas_icp.merge(
            base_dez[['id_store', 'status_seller']].rename(columns={'status_seller': 'status_dez'}),
            on='id_store',
            how='inner'
        )
        
        if len(merged) > 0:
            # Calcular transições usando vetorização
            merged['tipo'] = merged.apply(
                lambda x: get_transition_type(x['status_dez'], x['status_jan']), axis=1
            )
            
            upgrades = len(merged[merged['tipo'] == 'upgrade'])
            downgrades = len(merged[merged['tipo'] == 'downgrade'])
            estaveis = len(merged[merged['tipo'] == 'estavel'])
            total_icp = len(merged)
            
            icp_transicao.append({
                'icp': icp,
                'total': total_icp,
                'upgrade': upgrades,
                'downgrade': downgrades,
                'estavel': estaveis,
                'pct_upgrade': round(upgrades / total_icp * 100, 1) if total_icp > 0 else 0,
                'pct_downgrade': round(downgrades / total_icp * 100, 1) if total_icp > 0 else 0,
                'pct_estavel': round(estaveis / total_icp * 100, 1) if total_icp > 0 else 0
            })
    
    if icp_transicao:
        for t in icp_transicao:
            print(f"    {t['icp']}: ↑{t['pct_upgrade']}% | →{t['pct_estavel']}% | ↓{t['pct_downgrade']}%")

# =============================================================================
# ANÁLISE DE NEW SELLERS
# =============================================================================
print("\n🆕 Analisando New Sellers...")

new_sellers_analysis = {'total': 0, 'por_mes': [], 'soma_total': 0, 'impacto_por_projeto': [], 'uplift_onboarding': None}

for mes_ns, df_ns in sorted(new_sellers_por_mes.items(), reverse=True):
    ns_id_col = 'store_id' if 'store_id' in df_ns.columns else 'id_store'
    df_ns = df_ns.copy()
    ids_new_sellers = set(df_ns[ns_id_col].unique())
    total_ns = len(ids_new_sellers)
    
    # Converter datas
    if 'created_at' in df_ns.columns:
        df_ns['created_at'] = pd.to_datetime(df_ns['created_at'], dayfirst=True, errors='coerce')
    if 'first_seller_at' in df_ns.columns:
        df_ns['first_seller_at'] = pd.to_datetime(df_ns['first_seller_at'], dayfirst=True, errors='coerce')
    
    # Classificar em 3 grupos: Com Onboarding, Sem Onboarding, Base Antiga
    def classificar_ns(row):
        store_id = row[ns_id_col]
        created = row.get('created_at')
        if store_id in ids_onboarding:
            return 'onboarding'
        elif pd.notna(created) and created >= pd.Timestamp('2025-10-01'):
            return 'grupo_controle'
        else:
            return 'base_antiga'
    
    df_ns['grupo_ns'] = df_ns.apply(classificar_ns, axis=1)
    
    # Contar por grupo
    n_onboarding = len(df_ns[df_ns['grupo_ns'] == 'onboarding'])
    n_controle = len(df_ns[df_ns['grupo_ns'] == 'grupo_controle'])
    n_base_antiga = len(df_ns[df_ns['grupo_ns'] == 'base_antiga'])
    n_webinar = len(ids_new_sellers.intersection(ids_webinar))
    
    pct_onboarding = round(n_onboarding / total_ns * 100, 2) if total_ns > 0 else 0
    pct_controle = round(n_controle / total_ns * 100, 2) if total_ns > 0 else 0
    pct_base_antiga = round(n_base_antiga / total_ns * 100, 2) if total_ns > 0 else 0
    pct_webinar = round(n_webinar / total_ns * 100, 2) if total_ns > 0 else 0
    
    # Calcular uplift: tempo até virar new seller
    uplift_data = None
    if 'first_seller_at' in df_ns.columns and 'created_at' in df_ns.columns:
        df_ns['dias_ate_seller'] = (df_ns['first_seller_at'] - df_ns['created_at']).dt.days
        
        dias_onb = df_ns[df_ns['grupo_ns'] == 'onboarding']['dias_ate_seller'].dropna()
        dias_ctrl = df_ns[df_ns['grupo_ns'] == 'grupo_controle']['dias_ate_seller'].dropna()
        
        if len(dias_onb) > 10 and len(dias_ctrl) > 10:
            media_onb = dias_onb.mean()
            media_ctrl = dias_ctrl.mean()
            mediana_onb = dias_onb.median()
            mediana_ctrl = dias_ctrl.median()
            
            # Uplift (redução no tempo)
            uplift_pct = round(((media_ctrl - media_onb) / media_ctrl) * 100, 1) if media_ctrl > 0 else 0
            
            # Teste t para significância
            from scipy import stats
            t_stat, p_value = stats.ttest_ind(dias_onb, dias_ctrl)
            significativo = p_value < 0.05
            
            # Teste de proporção para significância do tamanho das amostras
            # Usando teste chi-quadrado para comparar se proporções são significativamente diferentes
            n_total = n_onboarding + n_controle
            prop_onb = n_onboarding / n_total if n_total > 0 else 0
            prop_ctrl = n_controle / n_total if n_total > 0 else 0
            
            # Poder estatístico aproximado (baseado em tamanho de amostra mínimo para detectar efeitos)
            tamanho_minimo = 30  # Regra prática para amostras
            amostra_suficiente = len(dias_onb) >= tamanho_minimo and len(dias_ctrl) >= tamanho_minimo
            
            uplift_data = {
                'metrica': 'Tempo até virar New Seller',
                'grupo_teste': {
                    'nome': 'Com Onboarding',
                    'n': int(len(dias_onb)),
                    'media': float(round(media_onb, 1)),
                    'mediana': float(round(mediana_onb, 0))
                },
                'grupo_controle': {
                    'nome': 'Sem Onboarding',
                    'n': int(len(dias_ctrl)),
                    'media': float(round(media_ctrl, 1)),
                    'mediana': float(round(mediana_ctrl, 0))
                },
                'uplift_pct': float(uplift_pct),
                'p_value': float(round(p_value, 4)),
                'significativo': bool(significativo),
                'amostra_suficiente': bool(amostra_suficiente),
                'tamanho_amostra_analise': {
                    'n_teste': int(n_onboarding),
                    'n_controle': int(n_controle),
                    'n_total': int(n_total),
                    'pct_teste': float(round(prop_onb * 100, 1)),
                    'pct_controle': float(round(prop_ctrl * 100, 1)),
                    'suficiente_teste': bool(n_onboarding >= tamanho_minimo),
                    'suficiente_controle': bool(n_controle >= tamanho_minimo)
                }
            }
            print(f"      📊 Uplift: {uplift_pct}% mais rápido | p-value: {p_value:.4f} {'✅' if significativo else '⚠️'}")
            print(f"      📊 Amostras: Teste={n_onboarding} | Controle={n_controle} | {'✅ Suficiente' if amostra_suficiente else '⚠️ Amostra pequena'}")
    
    # Análise de churn por grupo (merge com base geral)
    churn_analysis = None
    if 'predictive_churn_probability' in lojas_ativas.columns:
        # Merge new sellers com base para pegar dados de churn
        df_ns_churn = df_ns.merge(
            lojas_ativas[[id_col, 'predictive_churn_probability', 'status_seller']],
            left_on=ns_id_col,
            right_on=id_col,
            how='left'
        )
        
        # Calcular métricas de churn por grupo
        churn_by_group = {}
        for grupo in ['onboarding', 'grupo_controle', 'base_antiga']:
            subset = df_ns_churn[df_ns_churn['grupo_ns'] == grupo]
            churn_valid = subset[subset['predictive_churn_probability'].notna()]
            
            if len(churn_valid) > 0:
                # Identificar não classificados (churn = 0 E status = not informed)
                nao_class = (churn_valid['predictive_churn_probability'] == 0) & \
                           (churn_valid['status_seller'] == 'not informed')
                classificados = churn_valid[~nao_class]
                churn_classificado = classificados['predictive_churn_probability']
                
                # Calcular quartis para lojas classificadas
                q_nc = int(nao_class.sum())
                q1 = int((churn_classificado <= 0.25).sum())
                q2 = int(((churn_classificado > 0.25) & (churn_classificado <= 0.50)).sum())
                q3 = int(((churn_classificado > 0.50) & (churn_classificado <= 0.75)).sum())
                q4 = int((churn_classificado > 0.75).sum())
                total_q = len(churn_valid)
                
                churn_by_group[grupo] = {
                    'n_total': int(len(subset)),
                    'n_com_churn': int(len(churn_valid)),
                    'n_classificados': int(len(classificados)),
                    'churn_medio': float(round(churn_classificado.mean() * 100, 1)) if len(churn_classificado) > 0 else 0,
                    'churn_mediana': float(round(churn_classificado.median() * 100, 1)) if len(churn_classificado) > 0 else 0,
                    'quartis': {
                        'nao_classificado': {'n': q_nc, 'pct': float(round(q_nc/total_q*100, 1))},
                        'baixo': {'n': q1, 'pct': float(round(q1/total_q*100, 1))},
                        'moderado': {'n': q2, 'pct': float(round(q2/total_q*100, 1))},
                        'alto': {'n': q3, 'pct': float(round(q3/total_q*100, 1))},
                        'critico': {'n': q4, 'pct': float(round(q4/total_q*100, 1))}
                    }
                }
        
        # Teste estatístico entre onboarding e controle
        churn_onb = df_ns_churn[df_ns_churn['grupo_ns'] == 'onboarding']['predictive_churn_probability'].dropna()
        churn_ctrl = df_ns_churn[df_ns_churn['grupo_ns'] == 'grupo_controle']['predictive_churn_probability'].dropna()
        
        churn_test = None
        if len(churn_onb) > 10 and len(churn_ctrl) > 10:
            t_stat_churn, p_value_churn = stats.ttest_ind(churn_onb, churn_ctrl)
            diff_pp = float(round((churn_ctrl.mean() - churn_onb.mean()) * 100, 1))
            
            churn_test = {
                'media_onb': float(round(churn_onb.mean() * 100, 1)),
                'media_ctrl': float(round(churn_ctrl.mean() * 100, 1)),
                'diff_pp': diff_pp,
                'p_value': float(round(p_value_churn, 4)),
                'significativo': bool(p_value_churn < 0.05)
            }
            print(f"      📊 Churn: Onb={churn_test['media_onb']}% vs Ctrl={churn_test['media_ctrl']}% | Diff={diff_pp}pp | p={p_value_churn:.4f}")
        
        churn_analysis = {
            'por_grupo': churn_by_group,
            'teste_estatistico': churn_test
        }
        
        # Status distribution por grupo
        status_by_group = {}
        for grupo in ['onboarding', 'grupo_controle', 'base_antiga']:
            subset = df_ns_churn[df_ns_churn['grupo_ns'] == grupo]
            status_dist = subset['status_seller'].value_counts().to_dict()
            status_by_group[grupo] = {str(k): int(v) for k, v in status_dist.items()}
        
        churn_analysis['status_por_grupo'] = status_by_group
    
    new_sellers_analysis['por_mes'].append({
        'mes': mes_ns,
        'total_new_sellers': total_ns,
        'com_lifecycle': n_onboarding + n_webinar,
        'pct_cobertura': round((n_onboarding + n_webinar) / total_ns * 100, 2) if total_ns > 0 else 0,
        'por_grupo': {
            'onboarding': {'n': n_onboarding, 'pct': pct_onboarding},
            'grupo_controle': {'n': n_controle, 'pct': pct_controle},
            'base_antiga': {'n': n_base_antiga, 'pct': pct_base_antiga},
            'webinar': {'n': n_webinar, 'pct': pct_webinar}
        },
        'uplift': uplift_data,
        'churn_analysis': churn_analysis
    })
    new_sellers_analysis['soma_total'] += total_ns
    print(f"  📅 {mes_ns}: {total_ns:,} new sellers")
    print(f"      Com Onboarding: {n_onboarding} ({pct_onboarding}%) | Sem Onboarding: {n_controle} ({pct_controle}%) | Base Antiga: {n_base_antiga} ({pct_base_antiga}%)")

new_sellers_analysis['total'] = new_sellers_analysis['soma_total']

# Resumo de impacto por projeto (agregado)
if new_sellers_analysis['por_mes']:
    ultimo_mes = new_sellers_analysis['por_mes'][0]
    new_sellers_analysis['impacto_por_projeto'] = [
        {
            'projeto': 'Onboarding V2',
            'n': ultimo_mes['por_grupo']['onboarding']['n'],
            'pct': ultimo_mes['por_grupo']['onboarding']['pct']
        },
        {
            'projeto': 'Sem Onboarding',
            'n': ultimo_mes['por_grupo']['grupo_controle']['n'],
            'pct': ultimo_mes['por_grupo']['grupo_controle']['pct']
        },
        {
            'projeto': 'Base Antiga',
            'n': ultimo_mes['por_grupo']['base_antiga']['n'],
            'pct': ultimo_mes['por_grupo']['base_antiga']['pct']
        },
        {
            'projeto': 'Webinars',
            'n': ultimo_mes['por_grupo']['webinar']['n'],
            'pct': ultimo_mes['por_grupo']['webinar']['pct']
        }
    ]
    new_sellers_analysis['uplift_onboarding'] = ultimo_mes.get('uplift')
    new_sellers_analysis['churn_onboarding'] = ultimo_mes.get('churn_analysis')

# =============================================================================
# ANÁLISE DE RISCO
# =============================================================================
print("\n🚨 Analisando Risco...")

# Verificar se churn é binário (0/1) ou probabilidade (0-1)
churn_values = lojas_ativas['predictive_churn_probability'].dropna().unique()
is_binary_churn = len(churn_values) <= 3 and all(v in [0, 1, 0.0, 1.0] for v in churn_values if pd.notna(v))
print(f"  📊 Tipo de churn: {'Binário (0/1)' if is_binary_churn else 'Probabilidade (0-1)'}")

# Total de lojas com dados de churn
lojas_com_churn = lojas_ativas[lojas_ativas['predictive_churn_probability'].notna()].copy()
lojas_sem_churn = lojas_ativas[lojas_ativas['predictive_churn_probability'].isna()].copy()
print(f"  📊 Total lojas com dados de churn: {len(lojas_com_churn):,}")
print(f"  ⚪ Lojas sem classificação: {len(lojas_sem_churn):,}")

# Classificar lojas por risco
lojas_sem_risco = lojas_com_churn[lojas_com_churn['predictive_churn_probability'] == 0].copy()
lojas_com_risco = lojas_com_churn[lojas_com_churn['predictive_churn_probability'] == 1].copy()
print(f"  ✅ Sem Risco (churn=0): {len(lojas_sem_risco):,}")
print(f"  🚨 Com Risco (churn=1): {len(lojas_com_risco):,}")

risk_quartiles_data = []
risk_quartiles_lojas = {}  # Armazena lista de lojas por quartil

for i, q in enumerate(RISK_QUARTILES):
    # Categoria especial: Não Classificado
    if q.get('special') == 'not_classified':
        lojas_quartil = lojas_sem_churn.copy()
    elif q['name'] == 'Sem Risco':
        lojas_quartil = lojas_sem_risco.copy()
    elif q['name'] == 'Com Risco de Churn':
        lojas_quartil = lojas_com_risco.copy()
    else:
        # Fallback para probabilidades contínuas
        mask = (lojas_com_churn['predictive_churn_probability'] > q['min']) & \
               (lojas_com_churn['predictive_churn_probability'] <= q['max'])
        lojas_quartil = lojas_com_churn[mask].copy()
    count = len(lojas_quartil)
    # Usar total de lojas ativas para porcentagem (inclui não classificadas)
    total_base = len(lojas_ativas)
    pct = round(count / total_base * 100, 1) if total_base > 0 else 0
    gmv = lojas_quartil['gmv_mes_local'].sum()
    
    # Estatísticas do quartil
    prob_mean = lojas_quartil['predictive_churn_probability'].mean() if count > 0 else 0
    stats = {
        'gmv_medio': round(lojas_quartil['gmv_mes_local'].mean(), 2) if count > 0 else 0,
        'orders_medio': round(lojas_quartil['orders_mes'].mean(), 1) if count > 0 else 0,
        'prob_media': round(prob_mean * 100, 2) if pd.notna(prob_mean) else 0,
        'aging_medio': round(lojas_quartil['aging_clean'].mean(), 0) if count > 0 else 0,
    }
    
    # Distribuição por status no quartil
    status_dist = lojas_quartil['status_seller'].value_counts().to_dict()
    status_dist_formatted = {STATUS_LABELS.get(k, k): v for k, v in status_dist.items()}
    
    # Lista de lojas (top 500 por GMV para não sobrecarregar)
    lojas_lista = lojas_quartil.nlargest(500, 'gmv_mes_local')[[
        id_col, 'store_name', 'status_seller', 'gmv_mes_local', 'orders_mes', 
        'predictive_churn_probability', 'aging', 'main_user'
    ]].copy()
    lojas_lista['predictive_churn_probability'] = (lojas_lista['predictive_churn_probability'] * 100).round(2)
    lojas_lista['gmv_mes_local'] = lojas_lista['gmv_mes_local'].round(2)
    lojas_lista['status_seller'] = lojas_lista['status_seller'].map(lambda x: STATUS_LABELS.get(x, x))
    lojas_lista = lojas_lista.rename(columns={
        id_col: 'store_id',
        'store_name': 'nome',
        'status_seller': 'status',
        'gmv_mes_local': 'gmv',
        'orders_mes': 'pedidos',
        'predictive_churn_probability': 'prob_churn',
        'aging': 'idade_dias',
        'main_user': 'email'
    })
    
    risk_quartiles_lojas[q['name']] = lojas_lista.to_dict('records')
    
    # Definir prob_range apropriado para cada categoria
    if q.get('special') == 'not_classified':
        prob_range = 'Sem dados'
    elif q['name'] == 'Sem Risco':
        prob_range = 'Sem risco'
    elif q['name'] == 'Com Risco de Churn':
        prob_range = 'Potencial churn'
    else:
        prob_range = f"{int(q['min']*100)}%-{int(q['max']*100)}%"
    
    risk_quartiles_data.append({
        'name': q['name'],
        'color': q['color'],
        'count': count,
        'pct': pct,
        'gmv_total': round(gmv, 2),
        'prob_range': prob_range,
        'stats': stats,
        'status_distribution': status_dist_formatted,
        'is_not_classified': q.get('special') == 'not_classified'
    })

# Evolução do risco por mês
risco_evolucao = []
for mes, base in sorted(bases_mensais.items()):
    base_com_churn = base[base['predictive_churn_probability'] > 0]
    if len(base_com_churn) > 0:
        prob_media = base_com_churn['predictive_churn_probability'].mean() * 100
        risco_evolucao.append({
            'mes': mes,
            'prob_media': round(prob_media, 2),
            'lojas': len(base_com_churn)
        })

# =============================================================================
# MERCHANT SERVICES - ANÁLISE COMPLETA
# =============================================================================
print("\n🛒 Analisando Merchant Services...")

# Distribuição por quantidade
ms_dist = lojas_ativas['qtd_merchant_services'].value_counts().sort_index()

# Por produto
ms_por_produto = []
for col in MERCHANT_COLS:
    total = int(lojas_ativas[col].sum())
    pct = round(lojas_ativas[col].mean() * 100, 1)
    ms_por_produto.append({
        'produto': PRODUTO_NAMES[col],
        'codigo': col,
        'lojas': total,
        'pct': pct
    })

# Top combinações
combo_counts = lojas_ativas['combo_produtos'].value_counts().head(15)
ms_combinacoes = [
    {'combo': combo, 'count': int(count), 'pct': round(count/len(lojas_ativas)*100, 1)}
    for combo, count in combo_counts.items()
]

# Oportunidades de Cross-sell
cross_sell = []
cross_sell_lojas = {}  # Armazena lista de lojas por produto

for col in MERCHANT_COLS:
    # Lojas que NÃO tem o produto
    sem_produto = lojas_ativas[lojas_ativas[col] == False]
    if len(sem_produto) > 0:
        # Dessas, quantas tem pelo menos 1 outro produto
        sem_produto_com_outros = sem_produto[sem_produto['qtd_merchant_services'] >= 1].copy()
        
        # Lista de lojas potenciais (top 500 por GMV)
        lojas_potenciais = sem_produto_com_outros.nlargest(500, 'gmv_mes_local')[[
            id_col, 'store_name', 'status_seller', 'gmv_mes_local', 'orders_mes',
            'qtd_merchant_services', 'combo_produtos', 'main_user'
        ]].copy()
        lojas_potenciais['gmv_mes_local'] = lojas_potenciais['gmv_mes_local'].round(2)
        lojas_potenciais['status_seller'] = lojas_potenciais['status_seller'].map(lambda x: STATUS_LABELS.get(x, x))
        lojas_potenciais = lojas_potenciais.rename(columns={
            id_col: 'store_id',
            'store_name': 'nome',
            'status_seller': 'status',
            'gmv_mes_local': 'gmv',
            'orders_mes': 'pedidos',
            'qtd_merchant_services': 'produtos_atuais',
            'combo_produtos': 'produtos',
            'main_user': 'email'
        })
        
        cross_sell_lojas[col] = lojas_potenciais.to_dict('records')
        
        cross_sell.append({
            'produto': PRODUTO_NAMES[col],
            'codigo': col,
            'potencial': len(sem_produto_com_outros),
            'pct_potencial': round(len(sem_produto_com_outros) / len(lojas_ativas) * 100, 1),
            'ja_tem': int(lojas_ativas[col].sum()),
            'gmv_potencial': round(sem_produto_com_outros['gmv_mes_local'].sum(), 2)
        })

cross_sell.sort(key=lambda x: x['potencial'], reverse=True)

# Análise de afinidade entre produtos (quem tem X, também tem Y)
afinidade_produtos = []
for col1 in MERCHANT_COLS:
    tem_produto = lojas_ativas[lojas_ativas[col1] == True]
    if len(tem_produto) > 0:
        afinidades = []
        for col2 in MERCHANT_COLS:
            if col1 != col2:
                pct_tambem_tem = round(tem_produto[col2].mean() * 100, 1)
                afinidades.append({
                    'produto': PRODUTO_NAMES[col2],
                    'pct': pct_tambem_tem
                })
        # Ordenar por maior afinidade
        afinidades.sort(key=lambda x: x['pct'], reverse=True)
        
        afinidade_produtos.append({
            'produto': PRODUTO_NAMES[col1],
            'codigo': col1,
            'total_clientes': int(lojas_ativas[col1].sum()),
            'produtos_relacionados': afinidades[:3]  # Top 3
        })

# =============================================================================
# MÉTRICAS GERAIS
# =============================================================================
print("\n📊 Calculando métricas gerais...")

lojas_sellers = lojas_ativas[lojas_ativas['status_seller'].isin(SELLER_STATUS)]
lojas_com_status = lojas_ativas[lojas_ativas['status_seller'] != 'not informed']
lojas_ativas['tem_alguma_acao'] = lojas_ativas['tem_webinar'] | lojas_ativas['tem_onboarding']
lojas_cobertas = lojas_ativas[lojas_ativas['tem_alguma_acao'] == True]
com_webinar = lojas_ativas[lojas_ativas['tem_webinar'] == True]
sem_webinar = lojas_ativas[lojas_ativas['tem_webinar'] == False]
com_onboarding = lojas_ativas[lojas_ativas['tem_onboarding'] == True]
sem_onboarding = lojas_ativas[lojas_ativas['tem_onboarding'] == False]

# =============================================================================
# MONTAR DADOS DO DASHBOARD
# =============================================================================
dashboard_data = {}

# Resumo
gmv_total = lojas_ativas['gmv_mes_local'].sum()
n_sellers = len(lojas_sellers)
pct_sellers = n_sellers / len(lojas_ativas) * 100 if len(lojas_ativas) > 0 else 0
n_cobertas = len(lojas_cobertas)
pct_cobertura = n_cobertas / len(lojas_ativas) * 100 if len(lojas_ativas) > 0 else 0

dashboard_data['resumo'] = {
    'total_lojas_ativas': len(lojas_ativas),
    'total_lojas_sellers': n_sellers,
    'pct_sellers': round(pct_sellers, 1),
    'gmv_total': round(gmv_total, 2),
    'gmv_medio': round(lojas_ativas['gmv_mes_local'].mean(), 2),
    'orders_total': int(lojas_ativas['orders_mes'].sum()),
    'n_cobertas': n_cobertas,
    'pct_cobertura': round(pct_cobertura, 1),
    'data_base': mes_atual,
    'churn_prob_media': round(lojas_com_churn['predictive_churn_probability'].mean() * 100, 2)
}

dashboard_data['new_sellers'] = new_sellers_analysis
dashboard_data['matriz_transicao'] = matriz_transicao
dashboard_data['risk_quartiles'] = risk_quartiles_data
dashboard_data['risk_quartiles_lojas'] = risk_quartiles_lojas
dashboard_data['risco_evolucao'] = risco_evolucao

# Cobertura por projeto
dashboard_data['cobertura_projetos'] = [
    {
        'projeto': 'Webinars',
        'lojas': len(com_webinar),
        'pct': round(len(com_webinar) / len(lojas_ativas) * 100, 1),
        'status': 'ativo'
    },
    {
        'projeto': 'Onboarding V2',
        'lojas': len(com_onboarding),
        'pct': round(len(com_onboarding) / len(lojas_ativas) * 100, 1) if len(lojas_ativas) > 0 else 0,
        'status': 'ativo' if len(com_onboarding) > 0 else 'em breve'
    },
    {'projeto': 'Human in the Loop', 'lojas': 0, 'pct': 0, 'status': 'em breve'},
    {'projeto': 'Atrai e Cresce', 'lojas': 0, 'pct': 0, 'status': 'em breve'}
]

# Status da base
dashboard_data['status_base'] = {
    'total_com_status': len(lojas_com_status),
    'distribuicao': []
}

for status in STATUS_ORDER:
    subset = lojas_ativas[lojas_ativas['status_seller'] == status]
    if len(subset) > 0:
        dashboard_data['status_base']['distribuicao'].append({
            'status': status,
            'label': STATUS_LABELS.get(status, status),
            'count': len(subset),
            'pct': round(len(subset) / len(lojas_com_status) * 100, 1) if len(lojas_com_status) > 0 else 0,
            'gmv_medio': round(subset['gmv_mes_local'].mean(), 2),
            'gmv_total': round(subset['gmv_mes_local'].sum(), 2),
            'orders_medio': round(subset['orders_mes'].mean(), 1),
            'churn_prob': round(subset['predictive_churn_probability'].mean() * 100, 2)
        })

# Merchant Services
dashboard_data['merchant_services'] = {
    'media': round(lojas_ativas['qtd_merchant_services'].mean(), 2),
    'distribuicao': [
        {'qtd': int(k), 'count': int(v), 'pct': round(v/len(lojas_ativas)*100, 1)}
        for k, v in ms_dist.items()
    ],
    'por_produto': ms_por_produto,
    'combinacoes': ms_combinacoes,
    'cross_sell': cross_sell,
    'cross_sell_lojas': cross_sell_lojas,  # Lista de lojas para download
    'afinidade': afinidade_produtos  # Produtos relacionados (quem tem X também tem Y)
}

# Churn
dashboard_data['churn'] = {
    'lojas_com_dados': len(lojas_com_churn),
    'prob_media': round(lojas_com_churn['predictive_churn_probability'].mean() * 100, 2),
    'por_status': []
}

for status in STATUS_ORDER:
    subset = lojas_com_churn[lojas_com_churn['status_seller'] == status]
    if len(subset) >= 10:
        dashboard_data['churn']['por_status'].append({
            'status': status,
            'label': STATUS_LABELS.get(status, status),
            'prob_media': round(subset['predictive_churn_probability'].mean() * 100, 2),
            'lojas': len(subset)
        })

# =============================================================================
# ANÁLISE POR ICP (Ideal Customer Profile)
# =============================================================================
print("🎯 Analisando ICP...")

# Padronizar coluna de ICP
lojas_ativas['icp'] = lojas_ativas['model_icp'].fillna('Não Classificado')
lojas_ativas['icp'] = lojas_ativas['icp'].replace({'Fall Back': 'Não Classificado'})

# Ordenar ICPs
ICP_ORDER = ['ICP 1', 'ICP 2', 'ICP 3', 'ICP 4', 'Não Classificado']

# Análise por ICP
icp_analysis = {
    'disponivel': True,
    'total_classificados': len(lojas_ativas[lojas_ativas['icp'] != 'Não Classificado']),
    'total_nao_classificados': len(lojas_ativas[lojas_ativas['icp'] == 'Não Classificado']),
    'por_icp': []
}

for icp in ICP_ORDER:
    subset = lojas_ativas[lojas_ativas['icp'] == icp]
    if len(subset) > 0:
        # Status de sellers
        sellers = subset[subset['status_seller'].isin(SELLER_STATUS)]
        pct_sellers = round(len(sellers) / len(subset) * 100, 1) if len(subset) > 0 else 0
        
        # Distribuição por status
        status_dist = []
        for status in STATUS_ORDER:
            status_subset = subset[subset['status_seller'] == status]
            if len(status_subset) > 0:
                status_dist.append({
                    'status': status,
                    'label': STATUS_LABELS.get(status, status),
                    'count': len(status_subset),
                    'pct': round(len(status_subset) / len(subset) * 100, 1)
                })
        
        # New sellers
        new_sellers_icp = subset[subset['status_seller'] == 'new-seller'] if 'new-seller' in subset['status_seller'].values else pd.DataFrame()
        pct_new_sellers = round(len(new_sellers_icp) / len(subset) * 100, 2) if len(subset) > 0 else 0
        
        # Risco de churn
        subset_com_churn = subset[subset['predictive_churn_probability'].notna()]
        pct_risco = round(subset_com_churn['predictive_churn_probability'].mean() * 100, 1) if len(subset_com_churn) > 0 else 0
        lojas_com_risco = len(subset_com_churn[subset_com_churn['predictive_churn_probability'] > 0])
        pct_lojas_risco = round(lojas_com_risco / len(subset_com_churn) * 100, 1) if len(subset_com_churn) > 0 else 0
        
        # Participação no onboarding
        onb_icp = subset[subset['tem_onboarding'] == True]
        pct_onboarding = round(len(onb_icp) / len(subset) * 100, 1) if len(subset) > 0 else 0
        
        # Participação em webinars
        web_icp = subset[subset['tem_webinar'] == True]
        pct_webinar = round(len(web_icp) / len(subset) * 100, 1) if len(subset) > 0 else 0
        
        # GMV médio
        gmv_medio = round(subset['gmv_mes_local'].mean(), 2) if subset['gmv_mes_local'].notna().any() else 0
        gmv_total = round(subset['gmv_mes_local'].sum(), 2) if subset['gmv_mes_local'].notna().any() else 0
        
        icp_analysis['por_icp'].append({
            'icp': icp,
            'total': len(subset),
            'pct_base': round(len(subset) / len(lojas_ativas) * 100, 1),
            'pct_sellers': pct_sellers,
            'n_sellers': len(sellers),
            'status_dist': status_dist,
            'pct_new_sellers': pct_new_sellers,
            'pct_risco_churn': pct_risco,
            'pct_lojas_com_risco': pct_lojas_risco,
            'lojas_com_risco': lojas_com_risco,
            'pct_onboarding': pct_onboarding,
            'n_onboarding': len(onb_icp),
            'pct_webinar': pct_webinar,
            'n_webinar': len(web_icp),
            'gmv_medio': gmv_medio,
            'gmv_total': gmv_total
        })

dashboard_data['icp'] = icp_analysis

print(f"  ✅ Total classificados: {icp_analysis['total_classificados']:,} lojas")
print(f"  ⚪ Não classificados: {icp_analysis['total_nao_classificados']:,} lojas")
for icp_data in icp_analysis['por_icp']:
    if icp_data['icp'] != 'Não Classificado':
        print(f"  📊 {icp_data['icp']}: {icp_data['total']:,} lojas ({icp_data['pct_sellers']}% sellers, {icp_data['pct_risco_churn']}% risco)")

# Análise de Idade por ICP (quadrantes tempo x status)
print("  📊 Analisando idade das lojas por ICP...")

# Definir faixas de idade (em dias)
AGING_RANGES = [
    {'label': '0-30 dias', 'min': 0, 'max': 30},
    {'label': '31-90 dias', 'min': 31, 'max': 90},
    {'label': '91-180 dias', 'min': 91, 'max': 180},
    {'label': '181-365 dias', 'min': 181, 'max': 365},
    {'label': '+1 ano', 'min': 366, 'max': 999999}
]

icp_aging_analysis = []
for icp in ICP_ORDER:
    if icp == 'Não Classificado':
        continue
    subset = lojas_ativas[lojas_ativas['icp'] == icp]
    if len(subset) == 0:
        continue
    
    aging_data = {
        'icp': icp,
        'total': len(subset),
        'aging_medio': round(subset['aging_clean'].mean(), 0) if subset['aging_clean'].notna().any() else 0,
        'por_faixa': [],
        'quadrantes': []
    }
    
    # Análise por faixa de idade
    for faixa in AGING_RANGES:
        faixa_subset = subset[(subset['aging_clean'] >= faixa['min']) & (subset['aging_clean'] <= faixa['max'])]
        if len(faixa_subset) > 0:
            sellers_faixa = faixa_subset[faixa_subset['status_seller'].isin(SELLER_STATUS)]
            no_sellers_faixa = faixa_subset[faixa_subset['status_seller'] == 'no-seller']
            aging_data['por_faixa'].append({
                'faixa': faixa['label'],
                'total': len(faixa_subset),
                'pct': round(len(faixa_subset) / len(subset) * 100, 1),
                'sellers': len(sellers_faixa),
                'pct_sellers': round(len(sellers_faixa) / len(faixa_subset) * 100, 1) if len(faixa_subset) > 0 else 0,
                'no_sellers': len(no_sellers_faixa),
                'pct_no_sellers': round(len(no_sellers_faixa) / len(faixa_subset) * 100, 1) if len(faixa_subset) > 0 else 0
            })
    
    # Quadrantes: Tempo x Status (simplificado: Novo/Antigo x Seller/No-Seller)
    idade_mediana = subset['aging_clean'].median()
    novos = subset[subset['aging_clean'] <= idade_mediana]
    antigos = subset[subset['aging_clean'] > idade_mediana]
    
    aging_data['quadrantes'] = [
        {
            'quadrante': 'Novos + Sellers',
            'descricao': 'Conversão rápida (bom)',
            'count': len(novos[novos['status_seller'].isin(SELLER_STATUS)]),
            'pct': round(len(novos[novos['status_seller'].isin(SELLER_STATUS)]) / len(subset) * 100, 1) if len(subset) > 0 else 0,
            'cor': '#22c55e'
        },
        {
            'quadrante': 'Novos + No-Seller',
            'descricao': 'Em evolução (potencial)',
            'count': len(novos[novos['status_seller'] == 'no-seller']),
            'pct': round(len(novos[novos['status_seller'] == 'no-seller']) / len(subset) * 100, 1) if len(subset) > 0 else 0,
            'cor': '#f97316'
        },
        {
            'quadrante': 'Antigos + Sellers',
            'descricao': 'Base consolidada',
            'count': len(antigos[antigos['status_seller'].isin(SELLER_STATUS)]),
            'pct': round(len(antigos[antigos['status_seller'].isin(SELLER_STATUS)]) / len(subset) * 100, 1) if len(subset) > 0 else 0,
            'cor': '#0059d5'
        },
        {
            'quadrante': 'Antigos + No-Seller',
            'descricao': 'Risco (não converteram)',
            'count': len(antigos[antigos['status_seller'] == 'no-seller']),
            'pct': round(len(antigos[antigos['status_seller'] == 'no-seller']) / len(subset) * 100, 1) if len(subset) > 0 else 0,
            'cor': '#ef4444'
        }
    ]
    
    icp_aging_analysis.append(aging_data)

dashboard_data['icp']['aging'] = icp_aging_analysis

# Matriz de Transição por ICP - já foi calculada após a matriz geral
dashboard_data['icp']['transicao'] = icp_transicao

# =============================================================================
# WEBINARS - COM COMPARATIVO DE MERCHANT SERVICES
# =============================================================================
print("🎓 Analisando Webinars...")

# Comparativo de Merchant Services com/sem webinar
ms_com_webinar = {
    'media': round(com_webinar['qtd_merchant_services'].mean(), 2),
    'por_produto': []
}
ms_sem_webinar = {
    'media': round(sem_webinar['qtd_merchant_services'].mean(), 2),
    'por_produto': []
}

for col in MERCHANT_COLS:
    pct_com = round(com_webinar[col].mean() * 100, 1) if len(com_webinar) > 0 else 0
    pct_sem = round(sem_webinar[col].mean() * 100, 1) if len(sem_webinar) > 0 else 0
    diff = round(pct_com - pct_sem, 1)
    
    ms_com_webinar['por_produto'].append({
        'produto': PRODUTO_NAMES[col],
        'pct': pct_com
    })
    ms_sem_webinar['por_produto'].append({
        'produto': PRODUTO_NAMES[col],
        'pct': pct_sem,
        'diff': diff
    })

dashboard_data['webinars'] = {
    'total_participantes': len(com_webinar),
    'pct_base': round(len(com_webinar) / len(lojas_ativas) * 100, 2),
    'funil': webinar_funil,  # Dados do funil
    'performance': {
        'gmv_com': round(com_webinar['gmv_mes_local'].mean(), 2),
        'gmv_sem': round(sem_webinar['gmv_mes_local'].mean(), 2),
        'gmv_diff_pct': round((com_webinar['gmv_mes_local'].mean() - sem_webinar['gmv_mes_local'].mean()) / sem_webinar['gmv_mes_local'].mean() * 100, 1) if sem_webinar['gmv_mes_local'].mean() > 0 else 0,
        'orders_com': round(com_webinar['orders_mes'].mean(), 1),
        'orders_sem': round(sem_webinar['orders_mes'].mean(), 1),
    },
    'churn': {
        'prob_com': round(com_webinar[com_webinar['predictive_churn_probability'] > 0]['predictive_churn_probability'].mean() * 100, 2),
        'prob_sem': round(sem_webinar[sem_webinar['predictive_churn_probability'] > 0]['predictive_churn_probability'].mean() * 100, 2),
    },
    'merchant_services': {
        'com_webinar': ms_com_webinar,
        'sem_webinar': ms_sem_webinar,
        'diff_media': round(ms_com_webinar['media'] - ms_sem_webinar['media'], 2)
    },
    'new_sellers_impacto': new_sellers_analysis['por_mes']
}

dashboard_data['webinars']['churn']['diff_pp'] = round(
    dashboard_data['webinars']['churn']['prob_com'] - dashboard_data['webinars']['churn']['prob_sem'], 2
)

# Análise de risco por categoria: com vs sem webinar
print("  📊 Calculando risco por categoria (com vs sem webinar)...")
com_webinar_churn = com_webinar[com_webinar['predictive_churn_probability'].notna()]
sem_webinar_churn = sem_webinar[sem_webinar['predictive_churn_probability'].notna()]

# Total por grupo (para calcular % incluindo não classificados)
total_com = len(com_webinar)
total_sem = len(sem_webinar)

# Categorias de churn binário
com_sem_risco = int((com_webinar['predictive_churn_probability'] == 0).sum())
com_com_risco = int((com_webinar['predictive_churn_probability'] == 1).sum())
com_nao_class = int(com_webinar['predictive_churn_probability'].isna().sum())

sem_sem_risco = int((sem_webinar['predictive_churn_probability'] == 0).sum())
sem_com_risco = int((sem_webinar['predictive_churn_probability'] == 1).sum())
sem_nao_class = int(sem_webinar['predictive_churn_probability'].isna().sum())

risk_quartiles_webinar = []
for i, q in enumerate(RISK_QUARTILES):
    if q.get('special') == 'not_classified':
        count_com = com_nao_class
        count_sem = sem_nao_class
    elif q['name'] == 'Sem Risco':
        count_com = com_sem_risco
        count_sem = sem_sem_risco
    elif q['name'] == 'Com Risco de Churn':
        count_com = com_com_risco
        count_sem = sem_com_risco
    else:
        count_com = 0
        count_sem = 0
    
    pct_com = round(count_com / total_com * 100, 1) if total_com > 0 else 0
    pct_sem = round(count_sem / total_sem * 100, 1) if total_sem > 0 else 0
    
    risk_quartiles_webinar.append({
        'name': q['name'],
        'color': q['color'],
        'count_com': count_com,
        'pct_com': pct_com,
        'count_sem': count_sem,
        'pct_sem': pct_sem,
        'diff_pp': round(pct_com - pct_sem, 1),
        'is_not_classified': q.get('special') == 'not_classified'
    })

dashboard_data['webinars']['risk_quartiles_comparison'] = risk_quartiles_webinar

# Perfil por status
participantes_com_status = com_webinar[com_webinar['status_seller'] != 'not informed']
base_com_status = lojas_ativas[lojas_ativas['status_seller'] != 'not informed']

dashboard_data['webinars']['perfil_status'] = []
for status in STATUS_ORDER:
    count_part = len(participantes_com_status[participantes_com_status['status_seller'] == status])
    count_base = len(base_com_status[base_com_status['status_seller'] == status])
    
    if count_part > 0 or count_base > 0:
        pct_part = (count_part / len(participantes_com_status) * 100) if len(participantes_com_status) > 0 else 0
        pct_base = (count_base / len(base_com_status) * 100) if len(base_com_status) > 0 else 0
        indice = round((pct_part / pct_base * 100), 0) if pct_base > 0 else 0
        
        dashboard_data['webinars']['perfil_status'].append({
            'status': status,
            'label': STATUS_LABELS.get(status, status),
            'count': count_part,
            'pct_webinar': round(pct_part, 1),
            'pct_base': round(pct_base, 1),
            'indice': indice
        })

# Top webinars
if webinars_df is not None:
    webinars_populares = webinars_com_cobertura['webinar_name'].value_counts().head(10)
    dashboard_data['webinars']['top_webinars'] = [
        {'nome': nome, 'participantes': int(count)}
        for nome, count in webinars_populares.items()
    ]
else:
    dashboard_data['webinars']['top_webinars'] = []

# Análise pareada
lojas_pareamento = lojas_ativas[
    (lojas_ativas['status_seller'] != 'not informed') & 
    (lojas_ativas['aging_faixa_simples'] != 'N/A') &
    (lojas_ativas['gmv_mes_local'].notna())  # Garantir GMV válido
].copy()
lojas_pareamento['grupo'] = lojas_pareamento['status_seller'] + ' | ' + lojas_pareamento['aging_faixa_simples']

resultados_pareados = []
for grupo in lojas_pareamento['grupo'].unique():
    subset = lojas_pareamento[lojas_pareamento['grupo'] == grupo]
    com_web = subset[subset['tem_webinar'] == True]
    sem_web = subset[subset['tem_webinar'] == False]
    
    if len(com_web) >= 5 and len(sem_web) >= 5:
        gmv_com = com_web['gmv_mes_local'].mean()
        gmv_sem = sem_web['gmv_mes_local'].mean()
        
        # Validar valores antes de usar
        if pd.isna(gmv_com) or pd.isna(gmv_sem) or gmv_sem == 0:
            continue
            
        churn_com = com_web['predictive_churn_probability'].mean() * 100
        churn_sem = sem_web['predictive_churn_probability'].mean() * 100
        
        # Separar status e idade
        partes = grupo.split(' | ')
        status = partes[0] if len(partes) > 0 else grupo
        idade = partes[1] if len(partes) > 1 else 'N/A'
        
        resultados_pareados.append({
            'grupo': grupo,
            'status': STATUS_LABELS.get(status, status),
            'idade': idade,
            'n_com': len(com_web),
            'n_sem': len(sem_web),
            'gmv_com': round(gmv_com, 2),
            'gmv_sem': round(gmv_sem, 2),
            'gmv_diff_pct': round((gmv_com - gmv_sem) / gmv_sem * 100, 1) if gmv_sem > 0 else 0,
            'churn_com': round(churn_com, 2),
            'churn_sem': round(churn_sem, 2),
            'churn_diff_pp': round(churn_com - churn_sem, 2),
        })

# Ordenar por GMV diferença (maior impacto primeiro)
resultados_pareados.sort(key=lambda x: x['gmv_diff_pct'], reverse=True)

total_com = sum(r['n_com'] for r in resultados_pareados)
total_sem = sum(r['n_sem'] for r in resultados_pareados)

if total_com > 0 and total_sem > 0:
    gmv_pond_com = sum(r['gmv_com'] * r['n_com'] for r in resultados_pareados) / total_com
    gmv_pond_sem = sum(r['gmv_sem'] * r['n_sem'] for r in resultados_pareados) / total_sem
    churn_pond_com = sum(r['churn_com'] * r['n_com'] for r in resultados_pareados) / total_com
    churn_pond_sem = sum(r['churn_sem'] * r['n_sem'] for r in resultados_pareados) / total_sem
    
    dashboard_data['webinars']['analise_pareada'] = {
        'total_grupos': len(resultados_pareados),
        'gmv_com': round(gmv_pond_com, 2),
        'gmv_sem': round(gmv_pond_sem, 2),
        'gmv_diff_pct': round((gmv_pond_com - gmv_pond_sem) / gmv_pond_sem * 100, 1) if gmv_pond_sem > 0 else 0,
        'churn_com': round(churn_pond_com, 2),
        'churn_sem': round(churn_pond_sem, 2),
        'churn_diff_pp': round(churn_pond_com - churn_pond_sem, 2),
        'grupos': resultados_pareados  # Detalhes de cada grupo
    }
else:
    dashboard_data['webinars']['analise_pareada'] = {
        'total_grupos': 0, 'gmv_com': 0, 'gmv_sem': 0, 'gmv_diff_pct': 0,
        'churn_com': 0, 'churn_sem': 0, 'churn_diff_pp': 0, 'grupos': []
    }

# Churn pareado (média ponderada dos grupos pareados)
churn_pareado_com = dashboard_data['webinars']['analise_pareada']['churn_com']
churn_pareado_sem = dashboard_data['webinars']['analise_pareada']['churn_sem']
churn_pareado_diff = dashboard_data['webinars']['analise_pareada']['churn_diff_pp']

dashboard_data['webinars']['churn_pareado'] = {
    'churn_com': churn_pareado_com,
    'churn_sem': churn_pareado_sem,
    'diff_pp': churn_pareado_diff
}

# Matriz de transição específica para webinars
print("  📊 Calculando matriz de transição de webinars...")

matriz_webinar = {
    'disponivel': False,
    'upgrade': 0,
    'downgrade': 0,
    'estavel': 0,
    'pct_upgrade': 0,
    'pct_downgrade': 0,
    'pct_estavel': 0,
    'fluxo_liquido': [],
    'comparativo': None
}

if base_dezembro is not None and len(com_webinar) > 0:
    # IDs das lojas com webinar
    webinar_ids = set(com_webinar[id_col].dropna().astype(int))
    
    # Filtrar apenas lojas que estão em ambas as bases E participaram de webinar
    id_col_dez = 'id_store' if 'id_store' in base_dezembro.columns else 'store_id'
    
    # Base de dezembro - lojas com webinar
    dez_webinar = base_dezembro[base_dezembro[id_col_dez].isin(webinar_ids)][[id_col_dez, 'status_seller']].copy()
    jan_webinar = lojas_ativas[lojas_ativas[id_col].isin(webinar_ids)][[id_col, 'status_seller']].copy()
    
    # Merge para transição
    merged_web = dez_webinar.merge(
        jan_webinar,
        left_on=id_col_dez, right_on=id_col,
        how='inner',
        suffixes=('_antes', '_depois')
    )
    
    if len(merged_web) > 0:
        merged_web['tier_antes'] = merged_web['status_seller_antes'].apply(get_status_tier)
        merged_web['tier_depois'] = merged_web['status_seller_depois'].apply(get_status_tier)
        
        lojas_web_validas = merged_web[(merged_web['tier_antes'] >= 0) & (merged_web['tier_depois'] >= 0)]
        
        # Usar get_transition_type para classificar corretamente
        lojas_web_validas = lojas_web_validas.copy()
        lojas_web_validas['tipo_transicao'] = lojas_web_validas.apply(
            lambda x: get_transition_type(x['status_seller_antes'], x['status_seller_depois']), axis=1
        )
        
        up_web = len(lojas_web_validas[lojas_web_validas['tipo_transicao'] == 'upgrade'])
        down_web = len(lojas_web_validas[lojas_web_validas['tipo_transicao'] == 'downgrade'])
        estavel_web = len(lojas_web_validas[lojas_web_validas['tipo_transicao'] == 'estavel'])
        total_web = up_web + down_web + estavel_web
        
        # Fluxo líquido por status
        fluxo_web = []
        status_presentes_web = [s for s in STATUS_ORDER if s in lojas_web_validas['status_seller_antes'].values or s in lojas_web_validas['status_seller_depois'].values]
        
        for status in status_presentes_web:
            antes = int((lojas_web_validas['status_seller_antes'] == status).sum())
            depois = int((lojas_web_validas['status_seller_depois'] == status).sum())
            variacao = depois - antes
            pct_var = round((variacao / antes * 100), 1) if antes > 0 else 0
            
            fluxo_web.append({
                'status': status,
                'label': STATUS_LABELS.get(status, status),
                'antes': antes,
                'depois': depois,
                'variacao': variacao,
                'pct_variacao': pct_var
            })
        
        fluxo_web = sorted(fluxo_web, key=lambda x: x['variacao'], reverse=True)
        
        # Comparar com base geral
        pct_up_web = round(up_web / total_web * 100, 1) if total_web > 0 else 0
        pct_down_web = round(down_web / total_web * 100, 1) if total_web > 0 else 0
        pct_estavel_web = round(estavel_web / total_web * 100, 1) if total_web > 0 else 0
        
        # Diferença vs base geral
        diff_up = round(pct_up_web - matriz_transicao['pct_upgrade'], 1)
        diff_down = round(pct_down_web - matriz_transicao['pct_downgrade'], 1)
        
        matriz_webinar = {
            'disponivel': True,
            'total': total_web,
            'upgrade': up_web,
            'downgrade': down_web,
            'estavel': estavel_web,
            'pct_upgrade': pct_up_web,
            'pct_downgrade': pct_down_web,
            'pct_estavel': pct_estavel_web,
            'fluxo_liquido': fluxo_web,
            'comparativo': {
                'diff_upgrade': diff_up,
                'diff_downgrade': diff_down,
                'base_upgrade': matriz_transicao['pct_upgrade'],
                'base_downgrade': matriz_transicao['pct_downgrade']
            }
        }
        
        print(f"      Webinars: Upgrade {pct_up_web}% | Downgrade {pct_down_web}% | Estável {pct_estavel_web}%")
        print(f"      vs Base:  Upgrade {'+' if diff_up > 0 else ''}{diff_up}pp | Downgrade {'+' if diff_down > 0 else ''}{diff_down}pp")

dashboard_data['webinars']['matriz_transicao'] = matriz_webinar

# =============================================================================
# ANÁLISE DE ONBOARDING V2
# =============================================================================
print("\n📊 Analisando Onboarding V2...")

dashboard_data['onboarding'] = {
    'disponivel': False,
    'grupo_teste': {'total': 0, 'na_base': 0, 'pct_na_base': 0},
    'potential_sellers': {'total': 0, 'na_base': 0, 'pct_na_base': 0},
    'funil_steps': [],
    'status_pedidos': [],
    'cobertura_produtos': [],
    'qualificacao': [],
    'gmv_total': 0,
    'pct_sellers': 0,
    'lista_lojas': []
}

if onboarding_grupo_teste is not None and len(onboarding_grupo_teste) > 0:
    dashboard_data['onboarding']['disponivel'] = True
    onb = onboarding_grupo_teste.copy()
    
    # Resumo geral
    total_grupo = len(onb)
    onb_ids = set(onb['Store ID'].dropna().astype(int))
    
    # Cruzar com base geral para obter dados de GMV e Status
    lojas_onb_na_base = lojas_ativas[lojas_ativas[id_col].isin(onb_ids)].copy()
    ids_na_base = len(lojas_onb_na_base)
    
    dashboard_data['onboarding']['grupo_teste'] = {
        'total': total_grupo,
        'na_base': ids_na_base,
        'pct_na_base': round(ids_na_base / total_grupo * 100, 1) if total_grupo > 0 else 0
    }
    
    # GMV e Status da BASE GERAL (não da planilha de onboarding)
    gmv_total_base = lojas_onb_na_base['gmv_mes_local'].sum()
    dashboard_data['onboarding']['gmv_total'] = round(gmv_total_base, 2)
    
    # % Sellers da base geral
    sellers_onb = lojas_onb_na_base[lojas_onb_na_base['status_seller'].isin(SELLER_STATUS)]
    pct_sellers_onb = round(len(sellers_onb) / ids_na_base * 100, 1) if ids_na_base > 0 else 0
    dashboard_data['onboarding']['pct_sellers'] = pct_sellers_onb
    
    # Status por pedidos - DA BASE GERAL
    status_dist_base = lojas_onb_na_base['status_seller'].value_counts()
    for status, count in status_dist_base.items():
        label = STATUS_LABELS.get(status, status)
        dashboard_data['onboarding']['status_pedidos'].append({
            'status': str(status),
            'label': label,
            'count': int(count),
            'pct': round(count / ids_na_base * 100, 1) if ids_na_base > 0 else 0
        })
    
    # Potential Sellers (subset do grupo teste)
    if onboarding_potential is not None:
        pot = onboarding_potential.copy()
        total_pot = len(pot)
        pot_ids = set(pot['Store ID'].dropna().astype(int))
        lojas_pot_na_base = lojas_ativas[lojas_ativas[id_col].isin(pot_ids)]
        pot_na_base = len(lojas_pot_na_base)
        
        dashboard_data['onboarding']['potential_sellers'] = {
            'total': total_pot,
            'na_base': pot_na_base,
            'pct_na_base': round(pot_na_base / total_pot * 100, 1) if total_pot > 0 else 0,
            'gmv_total': round(lojas_pot_na_base['gmv_mes_local'].sum(), 2),
            'pct_sellers': round(len(lojas_pot_na_base[lojas_pot_na_base['status_seller'].isin(SELLER_STATUS)]) / pot_na_base * 100, 1) if pot_na_base > 0 else 0
        }
    
    # =========================================================================
    # DADOS ESPECÍFICOS DO ONBOARDING (da planilha de onboarding)
    # =========================================================================
    
    # Funil de Onboarding Steps (da planilha)
    steps_col = 'Onboarding - Steps completed'
    if steps_col in onb.columns:
        step_names = ['Layout', 'Products', 'Shipping', 'Payment']
        step_counts = {s: 0 for s in step_names}
        
        for val in onb[steps_col].dropna():
            for step in step_names:
                if step in str(val):
                    step_counts[step] += 1
        
        total_lojas = len(onb)
        for step in step_names:
            dashboard_data['onboarding']['funil_steps'].append({
                'step': step,
                'count': step_counts[step],
                'pct': round(step_counts[step] / total_lojas * 100, 1) if total_lojas > 0 else 0
            })
        
        # Combinações mais comuns
        steps_dist = onb[steps_col].value_counts().head(10)
        dashboard_data['onboarding']['steps_combinacoes'] = [
            {'combo': str(k), 'count': int(v), 'pct': round(v/total_lojas*100, 1)}
            for k, v in steps_dist.items()
        ]
    
    # Cobertura de produtos (da planilha de onboarding)
    if 'has_nuvemenvio' in onb.columns:
        ne_count = onb['has_nuvemenvio'].astype(str).str.lower().isin(['true', '1']).sum()
        dashboard_data['onboarding']['cobertura_produtos'].append({
            'produto': 'Nuvem Envio',
            'count': int(ne_count),
            'pct': round(ne_count / total_grupo * 100, 1)
        })
    
    if 'active_gateways_fintech' in onb.columns:
        np_count = onb['active_gateways_fintech'].str.contains('Nuvem Pago', case=False, na=False).sum()
        dashboard_data['onboarding']['cobertura_produtos'].append({
            'produto': 'Nuvem Pago',
            'count': int(np_count),
            'pct': round(np_count / total_grupo * 100, 1)
        })
        mp_count = onb['active_gateways_fintech'].str.contains('Mercado Pago', case=False, na=False).sum()
        dashboard_data['onboarding']['cobertura_produtos'].append({
            'produto': 'Mercado Pago',
            'count': int(mp_count),
            'pct': round(mp_count / total_grupo * 100, 1)
        })
    
    # Qualificação (da planilha de onboarding)
    qual_col = '[LCY BR] Qualificação - Potencial Sellers'
    if qual_col in onb.columns:
        qual_dist = onb[qual_col].value_counts().sort_index()
        for score, count in qual_dist.items():
            if pd.notna(score):
                dashboard_data['onboarding']['qualificacao'].append({
                    'score': int(score) if pd.notna(score) else 'N/A',
                    'count': int(count),
                    'pct': round(count / total_grupo * 100, 1)
                })
    
    # Lista de lojas para download - CRUZANDO base geral + dados do onboarding
    # Pegar dados da base geral (GMV, Status, Pedidos)
    lojas_base_para_lista = lojas_onb_na_base[[id_col, 'store_name', 'status_seller', 'gmv_mes_local', 'orders_mes', 'main_user']].copy()
    lojas_base_para_lista = lojas_base_para_lista.rename(columns={
        id_col: 'ID',
        'store_name': 'Nome',
        'status_seller': 'Status',
        'gmv_mes_local': 'GMV',
        'orders_mes': 'Pedidos',
        'main_user': 'Email'
    })
    
    # Pegar dados específicos do onboarding (Steps, Score)
    onb_dados = onb[['Store ID', steps_col, qual_col]].copy() if steps_col in onb.columns and qual_col in onb.columns else onb[['Store ID']].copy()
    if steps_col in onb.columns:
        onb_dados = onb_dados.rename(columns={steps_col: 'Steps Onboarding'})
    if qual_col in onb.columns:
        onb_dados = onb_dados.rename(columns={qual_col: 'Score'})
    onb_dados = onb_dados.rename(columns={'Store ID': 'ID'})
    
    # Merge: base geral + dados do onboarding
    lojas_lista = lojas_base_para_lista.merge(onb_dados, on='ID', how='left')
    
    # Ordenar por GMV e pegar top 500
    lojas_lista = lojas_lista.nlargest(500, 'GMV')
    
    # Formatar
    lojas_lista['GMV'] = lojas_lista['GMV'].round(2)
    lojas_lista['Score'] = lojas_lista['Score'].fillna(0).astype(int) if 'Score' in lojas_lista.columns else 0
    
    dashboard_data['onboarding']['lista_lojas'] = lojas_lista.to_dict('records')
    
    print(f"  ✅ Onboarding: {total_grupo:,} lojas no grupo teste")
    print(f"  ✅ Na base geral: {ids_na_base:,} lojas | GMV: R$ {gmv_total_base/1e6:.2f}M | {pct_sellers_onb}% sellers")
    print(f"  ✅ {dashboard_data['onboarding']['potential_sellers']['total']:,} potential sellers")
    
    # =========================================================================
    # ANÁLISE DE CHURN EXPANDIDA: GRUPO TESTE COMPLETO vs BASE GERAL
    # =========================================================================
    print("  📊 Analisando churn do grupo teste completo...")
    
    from scipy import stats
    
    def calc_churn_metrics(df, name):
        """Calcula métricas de churn para um DataFrame, incluindo não classificados"""
        df_valid = df[df['predictive_churn_probability'].notna()]
        if len(df_valid) == 0:
            return None
        
        # Identificar não classificados (churn = 0 E status = not informed)
        nao_class = (df_valid['predictive_churn_probability'] == 0) & \
                    (df_valid['status_seller'] == 'not informed')
        classificados = df_valid[~nao_class]
        churn = classificados['predictive_churn_probability']
        
        q_nc = int(nao_class.sum())
        q1 = int((churn <= 0.25).sum())
        q2 = int(((churn > 0.25) & (churn <= 0.50)).sum())
        q3 = int(((churn > 0.50) & (churn <= 0.75)).sum())
        q4 = int((churn > 0.75).sum())
        total = len(df_valid)
        
        return {
            'nome': name,
            'n': int(total),
            'n_classificados': int(len(classificados)),
            'churn_medio': float(round(churn.mean() * 100, 1)) if len(churn) > 0 else 0,
            'churn_mediana': float(round(churn.median() * 100, 1)) if len(churn) > 0 else 0,
            'quartis': {
                'nao_classificado': {'n': q_nc, 'pct': float(round(q_nc/total*100, 1))},
                'baixo': {'n': q1, 'pct': float(round(q1/total*100, 1))},
                'moderado': {'n': q2, 'pct': float(round(q2/total*100, 1))},
                'alto': {'n': q3, 'pct': float(round(q3/total*100, 1))},
                'critico': {'n': q4, 'pct': float(round(q4/total*100, 1))}
            }
        }
    
    # Lojas do grupo teste na base
    lojas_grupo_teste = lojas_ativas[lojas_ativas[id_col].isin(onb_ids)].copy()
    
    # Potential Sellers
    pot_ids = set()
    if onboarding_potential is not None:
        pot_ids = set(onboarding_potential['Store ID'].dropna().astype(int))
    lojas_potential = lojas_ativas[lojas_ativas[id_col].isin(pot_ids)].copy()
    
    # Resto do grupo teste (não potential)
    resto_onb_ids = onb_ids - pot_ids
    lojas_resto_teste = lojas_ativas[lojas_ativas[id_col].isin(resto_onb_ids)].copy()
    
    # Base geral (sem onboarding)
    lojas_sem_onb = lojas_ativas[~lojas_ativas[id_col].isin(onb_ids)].copy()
    
    # Calcular métricas
    churn_grupo_teste = calc_churn_metrics(lojas_grupo_teste, 'Grupo Teste (Onboarding)')
    churn_potential = calc_churn_metrics(lojas_potential, 'Potential Sellers')
    churn_resto_teste = calc_churn_metrics(lojas_resto_teste, 'Resto Grupo Teste')
    churn_base_geral = calc_churn_metrics(lojas_sem_onb, 'Base Geral (sem Onboarding)')
    
    # Testes estatísticos
    def calc_test(df1, df2, name1, name2):
        churn1 = df1['predictive_churn_probability'].dropna()
        churn2 = df2['predictive_churn_probability'].dropna()
        if len(churn1) > 10 and len(churn2) > 10:
            t_stat, p_value = stats.ttest_ind(churn1, churn2)
            return {
                'grupo1': name1,
                'grupo2': name2,
                'media1': float(round(churn1.mean() * 100, 1)),
                'media2': float(round(churn2.mean() * 100, 1)),
                'diff_pp': float(round((churn2.mean() - churn1.mean()) * 100, 1)),
                'p_value': float(round(p_value, 4)),
                'significativo': bool(p_value < 0.05)
            }
        return None
    
    teste_vs_base = calc_test(lojas_grupo_teste, lojas_sem_onb, 'Grupo Teste', 'Base Geral')
    teste_potential_vs_resto = calc_test(lojas_potential, lojas_resto_teste, 'Potential Sellers', 'Resto Grupo Teste')
    
    # Armazenar análise expandida
    dashboard_data['onboarding']['churn_expandido'] = {
        'grupo_teste': churn_grupo_teste,
        'potential_sellers': churn_potential,
        'resto_teste': churn_resto_teste,
        'base_geral': churn_base_geral,
        'teste_vs_base': teste_vs_base,
        'potential_vs_resto': teste_potential_vs_resto
    }
    
    if teste_vs_base:
        print(f"      Grupo Teste: {teste_vs_base['media1']}% vs Base Geral: {teste_vs_base['media2']}% | Diff: {teste_vs_base['diff_pp']}pp")
    if teste_potential_vs_resto:
        print(f"      Potential: {teste_potential_vs_resto['media1']}% vs Resto: {teste_potential_vs_resto['media2']}% | Diff: {teste_potential_vs_resto['diff_pp']}pp")
    
    # =========================================================================
    # MATRIZ DE TRANSIÇÃO: COM ONBOARDING vs SEM ONBOARDING (mesma idade)
    # =========================================================================
    print("  📊 Calculando matriz de transição de onboarding...")
    
    matriz_onboarding = {
        'disponivel': False,
        'com_onboarding': None,
        'sem_onboarding': None,
        'comparativo': None
    }
    
    if base_dezembro is not None:
        # IDs das lojas com onboarding
        onb_ids_set = set(onb_ids)
        
        # Filtrar lojas com onboarding em ambas as bases
        id_col_dez = 'id_store' if 'id_store' in base_dezembro.columns else 'store_id'
        
        # Lojas com onboarding que estão em dezembro e janeiro
        dez_onb = base_dezembro[base_dezembro[id_col_dez].isin(onb_ids_set)][[id_col_dez, 'status_seller', 'aging']].copy()
        jan_onb = lojas_ativas[lojas_ativas[id_col].isin(onb_ids_set)][[id_col, 'status_seller', 'aging_clean']].copy()
        
        # Merge
        merged_onb = dez_onb.merge(
            jan_onb,
            left_on=id_col_dez, right_on=id_col,
            how='inner',
            suffixes=('_antes', '_depois')
        )
        
        print(f"      Lojas onboarding em dezembro: {len(dez_onb):,}")
        print(f"      Lojas onboarding em janeiro: {len(jan_onb):,}")
        print(f"      Lojas em ambas as bases: {len(merged_onb):,}")
        
        if len(merged_onb) > 100:
            merged_onb['tier_antes'] = merged_onb['status_seller_antes'].apply(get_status_tier)
            merged_onb['tier_depois'] = merged_onb['status_seller_depois'].apply(get_status_tier)
            
            # Verificar se há status válido em dezembro
            pct_not_informed = (merged_onb['status_seller_antes'] == 'not informed').mean() * 100
            print(f"      Lojas 'not informed' em dezembro: {pct_not_informed:.1f}%")
            
            # Se a maioria era "not informed", analisar evolução desde "not informed"
            if pct_not_informed > 80:
                print(f"      ⚠️ Maioria sem status em dezembro - analisando evolução desde criação")
                
                # Análise: onde estão agora em janeiro
                status_jan_onb = merged_onb['status_seller_depois'].value_counts()
                total_onb_analysis = len(merged_onb)
                
                # Calcular quantos evoluíram (saíram de not-informed)
                ficaram_no_seller = (merged_onb['status_seller_depois'] == 'no-seller').sum()
                evoluiram = total_onb_analysis - ficaram_no_seller
                pct_evoluiram = round(evoluiram / total_onb_analysis * 100, 1) if total_onb_analysis > 0 else 0
                
                # Separar por tier atual
                merged_onb['tier_atual'] = merged_onb['status_seller_depois'].apply(get_status_tier)
                tier_dist_onb = {}
                for tier_val, tier_name in [(0, 'no-seller'), (1, 'struggling-seller'), (2, 'tiny-seller'), 
                                            (3, 'small-seller'), (4, 'medium-seller'), (5, 'large-seller'), (6, 'top-seller')]:
                    count = int((merged_onb['tier_atual'] == tier_val).sum())
                    tier_dist_onb[tier_name] = {
                        'count': count,
                        'pct': round(count / total_onb_analysis * 100, 1) if total_onb_analysis > 0 else 0
                    }
            
            # Calcular faixa de aging do grupo onboarding
            aging_onb_medio = merged_onb['aging'].median() if 'aging' in merged_onb.columns else 0
            aging_onb_min = merged_onb['aging'].quantile(0.25) if 'aging' in merged_onb.columns else 0
            aging_onb_max = merged_onb['aging'].quantile(0.75) if 'aging' in merged_onb.columns else 365
            
            # Apenas com status válido (para matriz tradicional)
            onb_validos = merged_onb[(merged_onb['tier_antes'] >= 0) & (merged_onb['tier_depois'] >= 0)]
            
            # Se a maioria era "not informed" em dezembro, fazer análise de evolução
            if pct_not_informed > 80:
                # Análise alternativa: comparar distribuição atual de status
                total_onb_analise = len(merged_onb)
                
                # Status atual - Com Onboarding
                dist_status_com = []
                for status in STATUS_ORDER:
                    if status in merged_onb['status_seller_depois'].values:
                        count = int((merged_onb['status_seller_depois'] == status).sum())
                        dist_status_com.append({
                            'status': status,
                            'label': STATUS_LABELS.get(status, status),
                            'count': count,
                            'pct': round(count / total_onb_analise * 100, 1) if total_onb_analise > 0 else 0
                        })
                
                # Calcular taxa de evolução (saíram de no-seller)
                no_seller_count = int((merged_onb['status_seller_depois'] == 'no-seller').sum())
                evoluiram = total_onb_analise - no_seller_count
                pct_evoluiram_onb = round(evoluiram / total_onb_analise * 100, 1) if total_onb_analise > 0 else 0
                
                matriz_onboarding['com_onboarding'] = {
                    'tipo': 'evolucao',  # Indica análise alternativa
                    'total': total_onb_analise,
                    'pct_evoluiram': pct_evoluiram_onb,
                    'evoluiram': evoluiram,
                    'no_seller': no_seller_count,
                    'dist_status': dist_status_com
                }
                
                print(f"      Com Onboarding: {pct_evoluiram_onb}% evoluíram para seller ({evoluiram:,} de {total_onb_analise:,})")
                
            else:
                # Análise tradicional de upgrade/downgrade
                # Usar get_transition_type para classificar corretamente
                onb_validos = onb_validos.copy()
                onb_validos['tipo_transicao'] = onb_validos.apply(
                    lambda x: get_transition_type(x['status_seller_antes'], x['status_seller_depois']), axis=1
                )
                
                up_onb = len(onb_validos[onb_validos['tipo_transicao'] == 'upgrade'])
                down_onb = len(onb_validos[onb_validos['tipo_transicao'] == 'downgrade'])
                estavel_onb = len(onb_validos[onb_validos['tipo_transicao'] == 'estavel'])
                total_onb = up_onb + down_onb + estavel_onb
                
                # Fluxo líquido por status - Com Onboarding
                fluxo_onb = []
                status_presentes_onb = [s for s in STATUS_ORDER if s in onb_validos['status_seller_antes'].values or s in onb_validos['status_seller_depois'].values]
                
                for status in status_presentes_onb:
                    antes = int((onb_validos['status_seller_antes'] == status).sum())
                    depois = int((onb_validos['status_seller_depois'] == status).sum())
                    variacao = depois - antes
                    pct_var = round((variacao / antes * 100), 1) if antes > 0 else 0
                    
                    fluxo_onb.append({
                        'status': status,
                        'label': STATUS_LABELS.get(status, status),
                        'antes': antes,
                        'depois': depois,
                        'variacao': variacao,
                        'pct_variacao': pct_var
                    })
                
                fluxo_onb = sorted(fluxo_onb, key=lambda x: x['variacao'], reverse=True)
                
                # Criar matriz visual para onboarding
                matriz_crosstab_onb = pd.crosstab(
                    onb_validos['status_seller_antes'], 
                    onb_validos['status_seller_depois'],
                    margins=False
                )
                
                status_presentes_mat = [s for s in STATUS_ORDER if s in matriz_crosstab_onb.index or s in matriz_crosstab_onb.columns]
                for s in status_presentes_mat:
                    if s not in matriz_crosstab_onb.index:
                        matriz_crosstab_onb.loc[s] = 0
                    if s not in matriz_crosstab_onb.columns:
                        matriz_crosstab_onb[s] = 0
                matriz_crosstab_onb = matriz_crosstab_onb.reindex(index=status_presentes_mat, columns=status_presentes_mat, fill_value=0)
                
                matriz_visual_onb = []
                max_count_onb = 1
                if matriz_crosstab_onb.size > 0:
                    max_val = matriz_crosstab_onb.values.max()
                    if max_val > 0:
                        max_count_onb = max_val
                
                for status_de in status_presentes_mat:
                    row = {'de': status_de, 'de_label': STATUS_LABELS.get(status_de, status_de), 'transicoes': []}
                    total_de = int(matriz_crosstab_onb.loc[status_de].sum())
                    for status_para in status_presentes_mat:
                        count = int(matriz_crosstab_onb.loc[status_de, status_para])
                        pct = round(count / total_de * 100, 1) if total_de > 0 else 0
                        # Usar função de classificação de transição
                        tipo = get_transition_type(status_de, status_para)
                        intensidade = round(count / max_count_onb, 2)
                        row['transicoes'].append({
                            'para': status_para,
                            'para_label': STATUS_LABELS.get(status_para, status_para),
                            'count': count,
                            'pct': pct,
                            'tipo': tipo,
                            'intensidade': intensidade
                        })
                    row['total'] = total_de
                    matriz_visual_onb.append(row)
                
                matriz_onboarding['com_onboarding'] = {
                    'tipo': 'transicao',
                    'total': total_onb,
                    'upgrade': up_onb,
                    'downgrade': down_onb,
                    'estavel': estavel_onb,
                    'pct_upgrade': round(up_onb / total_onb * 100, 1) if total_onb > 0 else 0,
                    'pct_downgrade': round(down_onb / total_onb * 100, 1) if total_onb > 0 else 0,
                    'pct_estavel': round(estavel_onb / total_onb * 100, 1) if total_onb > 0 else 0,
                    'fluxo_liquido': fluxo_onb,
                    'matriz_visual': matriz_visual_onb,
                    'status_order': [STATUS_LABELS.get(s, s) for s in status_presentes_mat]
                }
            
            # Agora criar grupo SEM onboarding com mesma faixa de aging
            # Usar aging atual (janeiro) para comparação justa
            aging_jan_onb = lojas_ativas[lojas_ativas[id_col].isin(onb_ids_set)]['aging_clean']
            aging_jan_min = aging_jan_onb.quantile(0.25) if len(aging_jan_onb) > 0 else 0
            aging_jan_max = aging_jan_onb.quantile(0.75) if len(aging_jan_onb) > 0 else 365
            
            sem_onb_ids = set(lojas_ativas[~lojas_ativas[id_col].isin(onb_ids_set)][id_col])
            
            # Filtrar lojas sem onboarding pela idade em JANEIRO (comparação justa)
            jan_sem_todas = lojas_ativas[
                (~lojas_ativas[id_col].isin(onb_ids_set)) &
                (lojas_ativas['aging_clean'] >= aging_jan_min) &
                (lojas_ativas['aging_clean'] <= aging_jan_max)
            ][[id_col, 'status_seller']].copy()
            
            print(f"      Faixa de aging (Jan): {aging_jan_min:.0f}-{aging_jan_max:.0f} dias")
            print(f"      Lojas sem onboarding (mesma idade atual): {len(jan_sem_todas):,}")
            
            # Para análise de evolução, buscar status em dezembro dessas lojas
            dez_sem = base_dezembro[
                base_dezembro[id_col_dez].isin(jan_sem_todas[id_col].values)
            ][[id_col_dez, 'status_seller']].copy()
            
            merged_sem = dez_sem.merge(
                jan_sem_todas,
                left_on=id_col_dez, right_on=id_col,
                how='inner',
                suffixes=('_antes', '_depois')
            )
            
            if len(merged_sem) > 100:
                merged_sem['tier_antes'] = merged_sem['status_seller_antes'].apply(get_status_tier)
                merged_sem['tier_depois'] = merged_sem['status_seller_depois'].apply(get_status_tier)
                
                # Verificar também o % de "not informed" no grupo sem onboarding
                pct_not_informed_sem = (merged_sem['status_seller_antes'] == 'not informed').mean() * 100
                
                # Se análise é de evolução (maioria era not informed)
                if pct_not_informed > 80:
                    # Análise de evolução para grupo sem onboarding
                    total_sem_analise = len(merged_sem)
                    
                    # Status atual - Sem Onboarding
                    dist_status_sem = []
                    for status in STATUS_ORDER:
                        if status in merged_sem['status_seller_depois'].values:
                            count = int((merged_sem['status_seller_depois'] == status).sum())
                            dist_status_sem.append({
                                'status': status,
                                'label': STATUS_LABELS.get(status, status),
                                'count': count,
                                'pct': round(count / total_sem_analise * 100, 1) if total_sem_analise > 0 else 0
                            })
                    
                    # Calcular taxa de evolução (saíram de no-seller)
                    no_seller_count_sem = int((merged_sem['status_seller_depois'] == 'no-seller').sum())
                    evoluiram_sem = total_sem_analise - no_seller_count_sem
                    pct_evoluiram_sem = round(evoluiram_sem / total_sem_analise * 100, 1) if total_sem_analise > 0 else 0
                    
                    matriz_onboarding['sem_onboarding'] = {
                        'tipo': 'evolucao',
                        'total': total_sem_analise,
                        'pct_evoluiram': pct_evoluiram_sem,
                        'evoluiram': evoluiram_sem,
                        'no_seller': no_seller_count_sem,
                        'dist_status': dist_status_sem,
                        'aging_range': f"{int(aging_jan_min)}-{int(aging_jan_max)} dias"
                    }
                    
                    print(f"      Sem Onboarding: {pct_evoluiram_sem}% evoluíram para seller ({evoluiram_sem:,} de {total_sem_analise:,})")
                    
                    # Comparativo de evolução com teste estatístico
                    pct_evoluiram_onb = matriz_onboarding['com_onboarding'].get('pct_evoluiram', 0)
                    diff_evolucao = round(pct_evoluiram_onb - pct_evoluiram_sem, 1)
                    
                    # Teste estatístico de proporções (z-test)
                    n_com = matriz_onboarding['com_onboarding'].get('total', 0)
                    n_sem = total_sem_analise
                    sucesso_com = matriz_onboarding['com_onboarding'].get('evoluiram', 0)
                    sucesso_sem = evoluiram_sem
                    
                    significativo = False
                    p_value = 1.0
                    if n_com > 30 and n_sem > 30:
                        # Proporções
                        p1 = sucesso_com / n_com if n_com > 0 else 0
                        p2 = sucesso_sem / n_sem if n_sem > 0 else 0
                        # Proporção pooled
                        p_pool = (sucesso_com + sucesso_sem) / (n_com + n_sem)
                        # Erro padrão
                        se = np.sqrt(p_pool * (1 - p_pool) * (1/n_com + 1/n_sem)) if p_pool > 0 and p_pool < 1 else 0.001
                        # Z-score
                        z = (p1 - p2) / se if se > 0 else 0
                        # P-value (two-tailed)
                        p_value = float(round(2 * (1 - stats.norm.cdf(abs(z))), 4))
                        significativo = bool(p_value < 0.05)
                    
                    matriz_onboarding['comparativo'] = {
                        'tipo': 'evolucao',
                        'diff_evolucao': diff_evolucao,
                        'pct_com': pct_evoluiram_onb,
                        'pct_sem': pct_evoluiram_sem,
                        'aging_range': f"{int(aging_jan_min)}-{int(aging_jan_max)} dias",
                        'p_value': p_value,
                        'significativo': significativo
                    }
                    
                    matriz_onboarding['disponivel'] = True
                    sig_str = "✅ Significativo" if significativo else "⚠️ Não significativo"
                    print(f"      Diferença: {'+' if diff_evolucao > 0 else ''}{diff_evolucao}pp em taxa de evolução | p-value: {p_value} | {sig_str}")
                    
                else:
                    # Análise tradicional de upgrade/downgrade
                    sem_validos = merged_sem[(merged_sem['tier_antes'] >= 0) & (merged_sem['tier_depois'] >= 0)]
                    
                    # Usar get_transition_type para classificar corretamente
                    sem_validos = sem_validos.copy()
                    sem_validos['tipo_transicao'] = sem_validos.apply(
                        lambda x: get_transition_type(x['status_seller_antes'], x['status_seller_depois']), axis=1
                    )
                    
                    up_sem = len(sem_validos[sem_validos['tipo_transicao'] == 'upgrade'])
                    down_sem = len(sem_validos[sem_validos['tipo_transicao'] == 'downgrade'])
                    estavel_sem = len(sem_validos[sem_validos['tipo_transicao'] == 'estavel'])
                    total_sem = up_sem + down_sem + estavel_sem
                    
                    if total_sem > 0:
                        # Obter status_presentes_mat do grupo com onboarding
                        status_presentes_mat = [s for s in STATUS_ORDER if s in sem_validos['status_seller_antes'].values or s in sem_validos['status_seller_depois'].values]
                        
                        # Fluxo líquido sem onboarding
                        fluxo_sem = []
                        for status in status_presentes_mat:
                            antes = int((sem_validos['status_seller_antes'] == status).sum())
                            depois = int((sem_validos['status_seller_depois'] == status).sum())
                            variacao = depois - antes
                            pct_var = round((variacao / antes * 100), 1) if antes > 0 else 0
                            fluxo_sem.append({
                                'status': status,
                                'label': STATUS_LABELS.get(status, status),
                                'antes': antes,
                                'depois': depois,
                                'variacao': variacao,
                                'pct_variacao': pct_var
                            })
                        fluxo_sem = sorted(fluxo_sem, key=lambda x: x['variacao'], reverse=True)
                        
                        # Matriz visual sem onboarding
                        matriz_crosstab_sem = pd.crosstab(
                            sem_validos['status_seller_antes'], 
                            sem_validos['status_seller_depois'],
                            margins=False
                        )
                        
                        for s in status_presentes_mat:
                            if s not in matriz_crosstab_sem.index:
                                matriz_crosstab_sem.loc[s] = 0
                            if s not in matriz_crosstab_sem.columns:
                                matriz_crosstab_sem[s] = 0
                        matriz_crosstab_sem = matriz_crosstab_sem.reindex(index=status_presentes_mat, columns=status_presentes_mat, fill_value=0)
                        
                        matriz_visual_sem = []
                        max_count_sem = 1
                        if matriz_crosstab_sem.size > 0:
                            max_val_sem = matriz_crosstab_sem.values.max()
                            if max_val_sem > 0:
                                max_count_sem = max_val_sem
                        
                        for status_de in status_presentes_mat:
                            row = {'de': status_de, 'de_label': STATUS_LABELS.get(status_de, status_de), 'transicoes': []}
                            total_de = int(matriz_crosstab_sem.loc[status_de].sum())
                            for status_para in status_presentes_mat:
                                count = int(matriz_crosstab_sem.loc[status_de, status_para])
                                pct = round(count / total_de * 100, 1) if total_de > 0 else 0
                                # Usar função de classificação de transição
                                tipo = get_transition_type(status_de, status_para)
                                intensidade = round(count / max_count_sem, 2)
                                row['transicoes'].append({
                                    'para': status_para,
                                    'para_label': STATUS_LABELS.get(status_para, status_para),
                                    'count': count,
                                    'pct': pct,
                                    'tipo': tipo,
                                    'intensidade': intensidade
                                })
                            row['total'] = total_de
                            matriz_visual_sem.append(row)
                        
                        pct_up_sem = round(up_sem / total_sem * 100, 1) if total_sem > 0 else 0
                        pct_down_sem = round(down_sem / total_sem * 100, 1) if total_sem > 0 else 0
                        
                        matriz_onboarding['sem_onboarding'] = {
                            'tipo': 'transicao',
                            'total': total_sem,
                            'upgrade': up_sem,
                            'downgrade': down_sem,
                            'estavel': estavel_sem,
                            'pct_upgrade': pct_up_sem,
                            'pct_downgrade': pct_down_sem,
                            'pct_estavel': round(estavel_sem / total_sem * 100, 1) if total_sem > 0 else 0,
                            'fluxo_liquido': fluxo_sem,
                            'matriz_visual': matriz_visual_sem,
                            'status_order': [STATUS_LABELS.get(s, s) for s in status_presentes_mat],
                            'aging_range': f"{int(aging_onb_min)}-{int(aging_onb_max)} dias"
                        }
                        
                        # Comparativo tradicional
                        pct_up_onb = matriz_onboarding['com_onboarding'].get('pct_upgrade', 0)
                        pct_down_onb = matriz_onboarding['com_onboarding'].get('pct_downgrade', 0)
                        
                        matriz_onboarding['comparativo'] = {
                            'tipo': 'transicao',
                            'diff_upgrade': round(pct_up_onb - pct_up_sem, 1),
                            'diff_downgrade': round(pct_down_onb - pct_down_sem, 1),
                            'aging_range': f"{int(aging_onb_min)}-{int(aging_onb_max)} dias"
                        }
                        
                        matriz_onboarding['disponivel'] = True
                        
                        print(f"      Com Onboarding: Upgrade {pct_up_onb}% | Downgrade {pct_down_onb}%")
                        print(f"      Sem Onboarding: Upgrade {pct_up_sem}% | Downgrade {pct_down_sem}%")
                        print(f"      Diferença: Upgrade {matriz_onboarding['comparativo']['diff_upgrade']:+.1f}pp | Downgrade {matriz_onboarding['comparativo']['diff_downgrade']:+.1f}pp")
    
    dashboard_data['onboarding']['matriz_transicao'] = matriz_onboarding
    
else:
    print("  ⚠️ Dados de onboarding não disponíveis")

# =============================================================================
# GERAR HTML
# =============================================================================
print("\n🎨 Gerando HTML...")

# Função para gerar seção de uplift do onboarding
def generate_onboarding_uplift_section():
    """Gera HTML para a seção de resultados do experimento de onboarding"""
    uplift = dashboard_data.get('new_sellers', {}).get('uplift_onboarding')
    if not uplift:
        return '<div class="insight-box"><p>Dados de uplift não disponíveis. Aguardando mais dados para análise.</p></div>'
    
    # Determinação de cores e status
    sig_class = "positive" if uplift['significativo'] else "negative"
    sig_text = "✅ Sim" if uplift['significativo'] else "⚠️ Não"
    amostra_ok = uplift.get('amostra_suficiente', True)
    amostra_class = "positive" if amostra_ok else "warning"
    amostra_text = "✅ Suficiente" if amostra_ok else "⚠️ Amostra pequena"
    
    tamanho = uplift.get('tamanho_amostra_analise', {})
    
    html = f'''
            <h2 class="section-title">📊 Resultado do Experimento: Onboarding vs Controle</h2>
            <div class="card">
                <div class="card-title">Análise de Significância Estatística</div>
                <div class="insight-box {"positive" if uplift["significativo"] else "neutral"}">
                    <h4>Métrica Principal: {uplift['metrica']}</h4>
                    <p style="margin-top:8px;">Comparação entre lojas que passaram pelo onboarding e grupo controle (lojas criadas a partir de Out/2025 sem onboarding).</p>
                </div>
                
                <div class="two-columns" style="margin-top:16px;">
                    <div>
                        <h4 style="margin-bottom:12px;">Tempo até Virar New Seller</h4>
                        <table>
                            <thead><tr><th>Grupo</th><th>N</th><th>Média (dias)</th><th>Mediana (dias)</th></tr></thead>
                            <tbody>
                                <tr>
                                    <td><strong>{uplift['grupo_teste']['nome']}</strong></td>
                                    <td>{uplift['grupo_teste']['n']}</td>
                                    <td class="positive">{uplift['grupo_teste']['media']}</td>
                                    <td>{int(uplift['grupo_teste']['mediana'])}</td>
                                </tr>
                                <tr>
                                    <td><strong>{uplift['grupo_controle']['nome']}</strong></td>
                                    <td>{uplift['grupo_controle']['n']}</td>
                                    <td>{uplift['grupo_controle']['media']}</td>
                                    <td>{int(uplift['grupo_controle']['mediana'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div>
                        <h4 style="margin-bottom:12px;">Resultado Estatístico</h4>
                        <div style="display:flex;flex-direction:column;gap:12px;">
                            <div class="card" style="background:var(--bg-secondary);padding:16px;">
                                <span class="text-muted">Uplift (redução no tempo):</span>
                                <div class="positive" style="font-size:2rem;font-weight:700;">{uplift['uplift_pct']}%</div>
                                <span class="text-muted" style="font-size:0.75rem;">mais rápido para virar New Seller</span>
                            </div>
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                                <div class="card" style="background:var(--bg-secondary);padding:12px;text-align:center;">
                                    <span class="text-muted" style="font-size:0.75rem;">p-value</span>
                                    <div style="font-weight:600;">{uplift['p_value']}</div>
                                </div>
                                <div class="card" style="background:var(--bg-secondary);padding:12px;text-align:center;">
                                    <span class="text-muted" style="font-size:0.75rem;">Significativo?</span>
                                    <div class="{sig_class}" style="font-weight:600;">{sig_text}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border-color);">
                    <h4 style="margin-bottom:12px;">Análise do Tamanho da Amostra</h4>
                    <div class="grid grid-4" style="margin-top:12px;">
                        <div class="card" style="background:var(--bg-secondary);padding:12px;text-align:center;">
                            <span class="text-muted" style="font-size:0.75rem;">N Grupo Teste</span>
                            <div style="font-weight:600;">{tamanho.get('n_teste', uplift['grupo_teste']['n'])}</div>
                            <span class="text-muted" style="font-size:0.7rem;">{tamanho.get('pct_teste', 0)}% do total</span>
                        </div>
                        <div class="card" style="background:var(--bg-secondary);padding:12px;text-align:center;">
                            <span class="text-muted" style="font-size:0.75rem;">N Sem Onboarding</span>
                            <div style="font-weight:600;">{tamanho.get('n_controle', uplift['grupo_controle']['n'])}</div>
                            <span class="text-muted" style="font-size:0.7rem;">{tamanho.get('pct_controle', 0)}% do total</span>
                        </div>
                        <div class="card" style="background:var(--bg-secondary);padding:12px;text-align:center;">
                            <span class="text-muted" style="font-size:0.75rem;">Total Analisado</span>
                            <div style="font-weight:600;">{tamanho.get('n_total', uplift['grupo_teste']['n'] + uplift['grupo_controle']['n'])}</div>
                            <span class="text-muted" style="font-size:0.7rem;">new sellers</span>
                        </div>
                        <div class="card" style="background:var(--bg-secondary);padding:12px;text-align:center;">
                            <span class="text-muted" style="font-size:0.75rem;">Amostra</span>
                            <div class="{amostra_class}" style="font-weight:600;">{amostra_text}</div>
                            <span class="text-muted" style="font-size:0.7rem;">mín. 30 por grupo</span>
                        </div>
                    </div>
                </div>
            </div>
    '''
    
    # Adicionar seção de análise de churn
    churn = dashboard_data.get('new_sellers', {}).get('churn_onboarding')
    if churn and churn.get('teste_estatistico'):
        test = churn['teste_estatistico']
        por_grupo = churn.get('por_grupo', {})
        
        # Determinar cores baseado no resultado
        churn_sig_class = "positive" if test['significativo'] else "neutral"
        churn_sig_text = "✅ Sim" if test['significativo'] else "⚠️ Não"
        diff_class = "positive" if test['diff_pp'] > 0 else "negative"
        
        # Gerar linhas da tabela de quartis
        quartis_names = [
            ('baixo', 'Baixo (0-25%)', '#00c87b'),
            ('moderado', 'Moderado (25-50%)', '#c87b00'),
            ('alto', 'Alto (50-75%)', '#f77a7c'),
            ('critico', 'Crítico (75-100%)', '#c80003')
        ]
        
        quartis_comparison = []
        onb_data = por_grupo.get('onboarding', {}).get('quartis', {})
        ctrl_data = por_grupo.get('grupo_controle', {}).get('quartis', {})
        
        for key, name, color in quartis_names:
            pct_onb = onb_data.get(key, {}).get('pct', 0)
            pct_ctrl = ctrl_data.get(key, {}).get('pct', 0)
            diff = round(pct_onb - pct_ctrl, 1)
            # Para quartis de baixo risco, ter mais é bom. Para alto risco, ter menos é bom.
            is_good = (key == 'baixo' and diff > 0) or (key in ['alto', 'critico'] and diff < 0)
            quartis_comparison.append({
                'name': name,
                'color': color,
                'pct_onb': pct_onb,
                'pct_ctrl': pct_ctrl,
                'diff': diff,
                'is_good': is_good
            })
        
        html += f'''
            <h2 class="section-title" style="margin-top:32px;">🚨 Risco Preditivo de Churn: Onboarding vs Controle</h2>
            <div class="card">
                <div class="card-title">Comparação de Risco de Churn entre Grupos</div>
                <div class="insight-box {churn_sig_class}">
                    <h4>Métrica: Probabilidade de Churn Preditivo</h4>
                    <p style="margin-top:8px;">Análise do risco de churn entre lojas que passaram pelo onboarding vs grupo controle.</p>
                </div>
                
                <div class="two-columns" style="margin-top:16px;">
                    <div>
                        <h4 style="margin-bottom:12px;">Média de Risco por Grupo</h4>
                        <table>
                            <thead><tr><th>Grupo</th><th>N</th><th>Churn Médio</th><th>Churn Mediana</th></tr></thead>
                            <tbody>
                                <tr>
                                    <td><strong>Com Onboarding</strong></td>
                                    <td>{por_grupo.get('onboarding', {}).get('n_com_churn', 0)}</td>
                                    <td class="positive">{por_grupo.get('onboarding', {}).get('churn_medio', 0)}%</td>
                                    <td>{por_grupo.get('onboarding', {}).get('churn_mediana', 0)}%</td>
                                </tr>
                                <tr>
                                    <td><strong>Sem Onboarding</strong></td>
                                    <td>{por_grupo.get('grupo_controle', {}).get('n_com_churn', 0)}</td>
                                    <td>{por_grupo.get('grupo_controle', {}).get('churn_medio', 0)}%</td>
                                    <td>{por_grupo.get('grupo_controle', {}).get('churn_mediana', 0)}%</td>
                                </tr>
                                <tr style="background:var(--bg-secondary);">
                                    <td><strong>Base Antiga</strong></td>
                                    <td>{por_grupo.get('base_antiga', {}).get('n_com_churn', 0)}</td>
                                    <td class="negative">{por_grupo.get('base_antiga', {}).get('churn_medio', 0)}%</td>
                                    <td>{por_grupo.get('base_antiga', {}).get('churn_mediana', 0)}%</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div>
                        <h4 style="margin-bottom:12px;">Resultado Estatístico</h4>
                        <div style="display:flex;flex-direction:column;gap:12px;">
                            <div class="card" style="background:var(--bg-secondary);padding:16px;">
                                <span class="text-muted">Diferença (Ctrl - Onb):</span>
                                <div class="{diff_class}" style="font-size:2rem;font-weight:700;">{test['diff_pp']}pp</div>
                                <span class="text-muted" style="font-size:0.75rem;">{"menor risco no onboarding" if test['diff_pp'] > 0 else "maior risco no onboarding"}</span>
                            </div>
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                                <div class="card" style="background:var(--bg-secondary);padding:12px;text-align:center;">
                                    <span class="text-muted" style="font-size:0.75rem;">p-value</span>
                                    <div style="font-weight:600;">{test['p_value']}</div>
                                </div>
                                <div class="card" style="background:var(--bg-secondary);padding:12px;text-align:center;">
                                    <span class="text-muted" style="font-size:0.75rem;">Significativo?</span>
                                    <div class="{churn_sig_class}" style="font-weight:600;">{churn_sig_text}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border-color);">
                    <h4 style="margin-bottom:12px;">Distribuição por Quartil de Risco (New Sellers)</h4>
                    <p class="text-muted" style="margin-bottom:12px;">Comparação da distribuição de lojas em cada faixa de risco. Diferenças negativas nos quartis de maior risco indicam que o onboarding ajuda a reduzir o risco.</p>
                    <div class="quartile-comparison">
                        {''.join([f'<div class="quartile-card" style="background:{q["color"]}15;border:2px solid {q["color"]};"><h4 style="color:{q["color"]};">{q["name"]}</h4><div class="quartile-row"><span class="quartile-label">Onboarding</span><span class="quartile-value" style="color:{q["color"]};">{q["pct_onb"]}%</span></div><div class="quartile-row"><span class="quartile-label">Controle</span><span class="quartile-value">{q["pct_ctrl"]}%</span></div><div class="quartile-row"><span class="quartile-label">Diferença</span><span class="quartile-value {"positive" if q["is_good"] else "negative" if not q["is_good"] and q["diff"]!=0 else ""}">{("+" if q["diff"]>0 else "")}{q["diff"]}pp</span></div></div>' for q in quartis_comparison])}
                    </div>
                </div>
            </div>
        '''
    
    # Adicionar análise expandida: Grupo Teste Completo vs Base Geral
    churn_exp = dashboard_data.get('onboarding', {}).get('churn_expandido')
    if churn_exp:
        grupo_teste = churn_exp.get('grupo_teste', {})
        potential = churn_exp.get('potential_sellers', {})
        resto = churn_exp.get('resto_teste', {})
        base_geral = churn_exp.get('base_geral', {})
        teste_vs_base = churn_exp.get('teste_vs_base', {})
        pot_vs_resto = churn_exp.get('potential_vs_resto', {})
        
        # Quartis para comparação expandida
        quartis_names = [
            ('baixo', 'Baixo (0-25%)', '#00c87b'),
            ('moderado', 'Moderado (25-50%)', '#c87b00'),
            ('alto', 'Alto (50-75%)', '#f77a7c'),
            ('critico', 'Crítico (75-100%)', '#c80003')
        ]
        
        # Comparação Grupo Teste vs Base Geral
        quartis_teste_base = []
        if grupo_teste and base_geral:
            for key, name, color in quartis_names:
                pct_teste = grupo_teste.get('quartis', {}).get(key, {}).get('pct', 0)
                pct_base = base_geral.get('quartis', {}).get(key, {}).get('pct', 0)
                diff = round(pct_teste - pct_base, 1)
                is_good = (key == 'baixo' and diff > 0) or (key in ['alto', 'critico'] and diff < 0)
                quartis_teste_base.append({
                    'name': name, 'color': color, 'pct_teste': pct_teste, 
                    'pct_base': pct_base, 'diff': diff, 'is_good': is_good
                })
        
        # Comparação Potential vs Resto
        quartis_pot_resto = []
        if potential and resto:
            for key, name, color in quartis_names:
                pct_pot = potential.get('quartis', {}).get(key, {}).get('pct', 0)
                pct_resto = resto.get('quartis', {}).get(key, {}).get('pct', 0)
                diff = round(pct_pot - pct_resto, 1)
                is_good = (key == 'baixo' and diff > 0) or (key in ['alto', 'critico'] and diff < 0)
                quartis_pot_resto.append({
                    'name': name, 'color': color, 'pct_pot': pct_pot,
                    'pct_resto': pct_resto, 'diff': diff, 'is_good': is_good
                })
        
        # Gerar HTML dos quartis fora do f-string
        def make_quartil_card(q, label1, label2, key1, key2):
            diff_class = "positive" if q["is_good"] else ("negative" if not q["is_good"] and q["diff"]!=0 else "")
            diff_sign = "+" if q["diff"] > 0 else ""
            return f'<div class="quartile-card" style="background:{q["color"]}15;border:2px solid {q["color"]};"><h4 style="color:{q["color"]};">{q["name"]}</h4><div class="quartile-row"><span class="quartile-label">{label1}</span><span class="quartile-value" style="color:{q["color"]};">{q[key1]}%</span></div><div class="quartile-row"><span class="quartile-label">{label2}</span><span class="quartile-value">{q[key2]}%</span></div><div class="quartile-row"><span class="quartile-label">Diferença</span><span class="quartile-value {diff_class}">{diff_sign}{q["diff"]}pp</span></div></div>'
        
        quartis_teste_base_html = "".join([make_quartil_card(q, "Grupo Teste", "Base Geral", "pct_teste", "pct_base") for q in quartis_teste_base]) if quartis_teste_base else "<p>Dados não disponíveis</p>"
        quartis_pot_resto_html = "".join([make_quartil_card(q, "Potential", "Resto", "pct_pot", "pct_resto") for q in quartis_pot_resto]) if quartis_pot_resto else "<p>Dados não disponíveis</p>"
        
        # Gerar HTML do teste estatístico
        def make_test_html(test_data):
            if not test_data:
                return "<p>Dados insuficientes</p>"
            sig_class = "positive" if test_data.get("significativo") else "neutral"
            sig_text = "✅ Sim" if test_data.get("significativo") else "⚠️ Não"
            return f'<div style="display:flex;flex-direction:column;gap:8px;"><div class="card" style="background:var(--bg-secondary);padding:12px;"><span class="text-muted">Diferença:</span> <strong>{test_data.get("diff_pp", 0)}pp</strong></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;"><div class="card" style="background:var(--bg-secondary);padding:8px;text-align:center;"><span class="text-muted" style="font-size:0.7rem;">p-value</span><div style="font-weight:600;">{test_data.get("p_value", "N/A")}</div></div><div class="card" style="background:var(--bg-secondary);padding:8px;text-align:center;"><span class="text-muted" style="font-size:0.7rem;">Significativo?</span><div class="{sig_class}" style="font-weight:600;">{sig_text}</div></div></div></div>'
        
        teste_vs_base_html = make_test_html(teste_vs_base)
        pot_vs_resto_html = make_test_html(pot_vs_resto)
        
        html += f'''
            <h2 class="section-title" style="margin-top:32px;">📊 Análise Expandida: Grupo Teste Completo (20k lojas)</h2>
            <div class="insight-box">
                <h4>Contexto</h4>
                <p>Esta análise compara <strong>todo o grupo teste do Onboarding</strong> (20k lojas) com a <strong>base geral</strong>. 
                Note que o grupo de onboarding são lojas mais novas, que naturalmente têm maior risco de churn comparado a lojas estabelecidas.</p>
            </div>
            
            <div class="card" style="margin-top:16px;">
                <div class="card-title">Grupo Teste vs Base Geral</div>
                <div class="two-columns" style="margin-top:16px;">
                    <div>
                        <h4 style="margin-bottom:12px;">Score de Risco por Grupo</h4>
                        <table>
                            <thead><tr><th>Grupo</th><th>N</th><th>Churn Médio</th><th>Mediana</th></tr></thead>
                            <tbody>
                                <tr>
                                    <td><strong>Grupo Teste (Onboarding)</strong></td>
                                    <td>{grupo_teste.get('n', 0):,}</td>
                                    <td>{grupo_teste.get('churn_medio', 0)}%</td>
                                    <td>{grupo_teste.get('churn_mediana', 0)}%</td>
                                </tr>
                                <tr>
                                    <td><strong>Base Geral (sem Onboarding)</strong></td>
                                    <td>{base_geral.get('n', 0):,}</td>
                                    <td class="positive">{base_geral.get('churn_medio', 0)}%</td>
                                    <td>{base_geral.get('churn_mediana', 0)}%</td>
                                </tr>
                            </tbody>
                        </table>
                        <p class="text-muted" style="margin-top:8px;font-size:0.75rem;">* Lojas novas têm maior risco de churn naturalmente</p>
                    </div>
                    <div>
                        <h4 style="margin-bottom:12px;">Teste Estatístico</h4>
                        {teste_vs_base_html}
                    </div>
                </div>
                
                <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border-color);">
                    <h4 style="margin-bottom:12px;">Distribuição por Quartil de Risco</h4>
                    <div class="quartile-comparison">
                        {quartis_teste_base_html}
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-top:16px;">
                <div class="card-title">Potential Sellers vs Resto do Grupo Teste</div>
                <div class="insight-box">
                    <p>Análise para verificar se os <strong>Potential Sellers</strong> (lojas identificadas com alto potencial) performam diferente do resto do grupo teste.</p>
                </div>
                <div class="two-columns" style="margin-top:16px;">
                    <div>
                        <h4 style="margin-bottom:12px;">Score de Risco</h4>
                        <table>
                            <thead><tr><th>Grupo</th><th>N</th><th>Churn Médio</th><th>Mediana</th></tr></thead>
                            <tbody>
                                <tr>
                                    <td><strong>Potential Sellers</strong></td>
                                    <td>{potential.get('n', 0):,}</td>
                                    <td>{potential.get('churn_medio', 0)}%</td>
                                    <td>{potential.get('churn_mediana', 0)}%</td>
                                </tr>
                                <tr>
                                    <td><strong>Resto Grupo Teste</strong></td>
                                    <td>{resto.get('n', 0):,}</td>
                                    <td class="positive">{resto.get('churn_medio', 0)}%</td>
                                    <td>{resto.get('churn_mediana', 0)}%</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div>
                        <h4 style="margin-bottom:12px;">Teste Estatístico</h4>
                        {pot_vs_resto_html}
                    </div>
                </div>
                
                <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border-color);">
                    <h4 style="margin-bottom:12px;">Distribuição por Quartil de Risco</h4>
                    <div class="quartile-comparison">
                        {quartis_pot_resto_html}
                    </div>
                </div>
            </div>
        '''
    
    return html

def generate_conversion_rate_onboarding():
    """Calcula taxa de conversão do grupo de onboarding baseado nos New Sellers"""
    uplift = dashboard_data.get('new_sellers', {}).get('uplift_onboarding')
    if uplift:
        n_teste = uplift['grupo_teste']['n']
        n_total_onb = 0
        # Buscar total de new sellers no onboarding do último mês
        por_mes = dashboard_data.get('new_sellers', {}).get('por_mes', [])
        if por_mes:
            n_total_onb = por_mes[0].get('por_grupo', {}).get('onboarding', {}).get('n', 0)
        
        if n_total_onb > 0:
            # n_teste são os que viraram seller (que têm first_seller_at)
            taxa = round(n_teste / n_total_onb * 100, 1) if n_total_onb > 0 else 0
            return f"{taxa}%"
    return "N/A"

def generate_onboarding_status_section():
    """Gera seção de status apenas se houver dados válidos"""
    onb = dashboard_data.get('onboarding', {})
    status_pedidos = onb.get('status_pedidos', [])
    cobertura_produtos = onb.get('cobertura_produtos', [])
    
    # Verificar se há dados válidos (não só "not informed")
    has_valid_status = any(s.get('status') != 'not informed' and s.get('count', 0) > 0 for s in status_pedidos)
    has_valid_products = any(p.get('count', 0) > 0 for p in cobertura_produtos)
    
    if not has_valid_status and not has_valid_products:
        return '''
            <div class="insight-box" style="margin-top:16px;">
                <h4>📋 Status e Cobertura de Produtos</h4>
                <p>Dados de status e cobertura de produtos não estão disponíveis para este grupo na base atual. Atualize a base geral com dados mais recentes para visualizar estas métricas.</p>
            </div>
        '''
    
    html = ''
    
    if has_valid_status:
        status_rows = ''.join([f'<tr><td><strong>{s.get("label", s["status"])}</strong></td><td>{s["count"]:,}</td><td>{s["pct"]}%</td></tr>' for s in status_pedidos if s.get('status') != 'not informed'])
        html += f'''
            <h2 class="section-title">Status por Pedidos (Base Geral)</h2>
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">Distribuição por Status</div>
                    <div class="chart-container"><canvas id="chartOnboardingStatus"></canvas></div>
                </div>
                <div class="card">
                    <table>
                        <thead><tr><th>Status</th><th>Lojas</th><th>%</th></tr></thead>
                        <tbody>{status_rows}</tbody>
                    </table>
                </div>
            </div>
        '''
    
    if has_valid_products:
        products_html = ''.join([f'<div class="card"><div class="card-title">{p["produto"]}</div><div class="card-value {"positive" if p["pct"]>50 else ""}">{p["pct"]}%</div><div class="card-subtitle">{p["count"]:,} lojas</div></div>' for p in cobertura_produtos])
        html += f'''
            <h2 class="section-title">Cobertura de Produtos</h2>
            <div class="grid grid-3">{products_html}</div>
        '''
    
    return html

def generate_onboarding_insights():
    """Gera insights automáticos para a aba de Onboarding"""
    insights = []
    
    uplift = dashboard_data.get('new_sellers', {}).get('uplift_onboarding')
    onb = dashboard_data.get('onboarding', {})
    
    # Insight sobre uplift
    if uplift and uplift.get('significativo'):
        insights.append(f"<strong>🚀 Resultado Positivo:</strong> O Onboarding V2 reduz o tempo para virar New Seller em <span class='positive'>{uplift['uplift_pct']}%</span>, de {uplift['grupo_controle']['media']} dias para {uplift['grupo_teste']['media']} dias em média. Resultado estatisticamente significativo (p-value = {uplift['p_value']}).")
    elif uplift:
        insights.append(f"<strong>⚠️ Atenção:</strong> A diferença observada ({uplift['uplift_pct']}% mais rápido) ainda não é estatisticamente significativa (p-value = {uplift['p_value']}). Recomenda-se aguardar mais dados.")
    
    # Insight sobre tamanho de amostra
    if uplift and uplift.get('amostra_suficiente'):
        insights.append(f"<strong>📊 Amostra Robusta:</strong> Análise com {uplift['grupo_teste']['n']} lojas no grupo teste e {uplift['grupo_controle']['n']} no controle - amostras suficientes para conclusões estatísticas.")
    elif uplift:
        insights.append(f"<strong>⚠️ Amostra Limitada:</strong> Embora haja diferença, o tamanho atual das amostras (Teste: {uplift['grupo_teste']['n']}, Controle: {uplift['grupo_controle']['n']}) pode limitar a confiança nos resultados.")
    
    # Insight sobre cobertura na base
    if onb.get('disponivel') and onb.get('grupo_teste', {}).get('pct_na_base', 0) < 50:
        insights.append(f"<strong>📋 Nota sobre Base:</strong> Apenas {onb['grupo_teste']['pct_na_base']}% das lojas do grupo teste estão na base geral de dezembro. Isso ocorre porque o onboarding é mais recente. Atualize a base para dados mais precisos de GMV e Status.")
    
    # Insight sobre funnel de steps
    steps = onb.get('funil_steps', [])
    if steps:
        step_mais_completado = max(steps, key=lambda x: x['pct'])
        step_menos_completado = min(steps, key=lambda x: x['pct'])
        if step_mais_completado['pct'] - step_menos_completado['pct'] > 20:
            insights.append(f"<strong>📈 Funil de Steps:</strong> {step_mais_completado['step']} é a etapa mais completada ({step_mais_completado['pct']}%), enquanto {step_menos_completado['step']} tem menor adesão ({step_menos_completado['pct']}%). Considere melhorar a experiência de {step_menos_completado['step']}.")
    
    # Insight sobre potential sellers
    pot = onb.get('potential_sellers', {})
    if pot.get('total', 0) > 0:
        insights.append(f"<strong>🎯 Potential Sellers:</strong> {pot['total']:,} lojas identificadas como potential sellers representam oportunidade de conversão.")
    
    # Insight sobre churn
    churn = dashboard_data.get('new_sellers', {}).get('churn_onboarding')
    if churn and churn.get('teste_estatistico'):
        test = churn['teste_estatistico']
        if test.get('significativo') and test.get('diff_pp', 0) > 0:
            insights.append(f"<strong>🛡️ Menor Risco de Churn:</strong> O grupo de onboarding apresenta <span class='positive'>{test['diff_pp']}pp menos risco de churn</span> ({test['media_onb']}% vs {test['media_ctrl']}% do controle). Resultado estatisticamente significativo (p-value = {test['p_value']}).")
        elif test.get('significativo'):
            insights.append(f"<strong>⚠️ Risco de Churn:</strong> O grupo de onboarding apresenta {abs(test['diff_pp'])}pp mais risco de churn que o controle. Necessário investigar.")
        else:
            insights.append(f"<strong>📊 Churn:</strong> Diferença de {test['diff_pp']}pp no risco de churn ainda não é estatisticamente significativa (p-value = {test['p_value']}).")
    
    if not insights:
        insights.append("<strong>📊 Aguardando Dados:</strong> Insights serão gerados quando houver dados suficientes para análise.")
    
    html = '''
            <h2 class="section-title">💡 Principais Insights</h2>
            <div class="insights-section">
    '''
    for ins in insights:
        html += f'<div class="insight-item">{ins}</div>'
    html += '</div>'
    
    return html

def generate_onboarding_transicao_section():
    """Gera seção de análise de evolução/transição comparativa para onboarding"""
    matriz = dashboard_data.get('onboarding', {}).get('matriz_transicao', {})
    if not matriz.get('disponivel'):
        return '<div class="insight-box warning"><p>Análise de transição não disponível. Carregue uma base do mês anterior para análise.</p></div>'
    
    com_onb = matriz.get('com_onboarding', {})
    sem_onb = matriz.get('sem_onboarding', {})
    comp = matriz.get('comparativo', {})
    
    if not com_onb or not sem_onb:
        return ''
    
    tipo_analise = com_onb.get('tipo', 'transicao')
    aging_range = comp.get('aging_range', 'similar')
    
    # Se é análise de evolução (lojas novas sem status anterior)
    if tipo_analise == 'evolucao':
        pct_com = com_onb.get('pct_evoluiram', 0)
        pct_sem = sem_onb.get('pct_evoluiram', 0)
        diff_evolucao = comp.get('diff_evolucao', 0)
        diff_class = 'positive' if diff_evolucao > 0 else ('negative' if diff_evolucao < 0 else '')
        p_value = comp.get('p_value', 1.0)
        significativo = comp.get('significativo', False)
        sig_badge = '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.6875rem;background:var(--success-surface);color:var(--success-text);margin-top:8px;">✅ Estatisticamente Significativo</span>' if significativo else '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.6875rem;background:var(--warning-surface);color:var(--warning-text);margin-top:8px;">⚠️ Não Significativo</span>'
        
        # Gerar gráfico comparativo unificado
        dist_com = com_onb.get('dist_status', [])
        dist_sem = sem_onb.get('dist_status', [])
        
        # Preparar dados para gráfico comparativo
        status_labels = [d['label'] for d in dist_com]
        pct_com_list = [d['pct'] for d in dist_com]
        pct_sem_list = []
        for s in [d['status'] for d in dist_com]:
            found = next((d['pct'] for d in dist_sem if d['status'] == s), 0)
            pct_sem_list.append(found)
        
        # Gerar linhas comparativas
        comparative_rows = ''
        max_pct = max(max(pct_com_list) if pct_com_list else 1, max(pct_sem_list) if pct_sem_list else 1)
        for i, d in enumerate(dist_com):
            pct_c = d['pct']
            pct_s = pct_sem_list[i] if i < len(pct_sem_list) else 0
            diff = round(pct_c - pct_s, 1)
            diff_txt = f'+{diff}' if diff > 0 else str(diff)
            diff_color = 'var(--success-text)' if diff > 0 else ('var(--danger-text)' if diff < 0 else 'var(--nimbus-neutral-text-low)')
            
            bar_width_c = round(pct_c / max_pct * 100, 1) if max_pct > 0 else 0
            bar_width_s = round(pct_s / max_pct * 100, 1) if max_pct > 0 else 0
            
            # Cor baseada no status
            status_class = 'positive' if d['status'] not in ['not informed', 'no-seller', 'struggling-seller'] else ('warning' if d['status'] == 'struggling-seller' else 'negative')
            bar_color_c = 'var(--nimbus-primary-interactive)'
            bar_color_s = 'var(--nimbus-neutral-text-disabled)'
            
            comparative_rows += f'''
            <div style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="font-size:0.75rem;font-weight:500;">{d['label']}</span>
                    <span style="font-size:0.75rem;color:{diff_color};font-weight:600;">{diff_txt}pp</span>
                </div>
                <div style="display:flex;gap:4px;align-items:center;">
                    <div style="flex:1;height:12px;background:var(--nimbus-neutral-surface-highlight);border-radius:4px;overflow:hidden;position:relative;">
                        <div style="width:{bar_width_c}%;height:100%;background:{bar_color_c};position:absolute;top:0;left:0;opacity:0.9;"></div>
                    </div>
                    <span style="font-size:0.6875rem;width:40px;text-align:right;color:var(--nimbus-primary-interactive);">{pct_c}%</span>
                </div>
                <div style="display:flex;gap:4px;align-items:center;margin-top:2px;">
                    <div style="flex:1;height:12px;background:var(--nimbus-neutral-surface-highlight);border-radius:4px;overflow:hidden;position:relative;">
                        <div style="width:{bar_width_s}%;height:100%;background:{bar_color_s};position:absolute;top:0;left:0;"></div>
                    </div>
                    <span style="font-size:0.6875rem;width:40px;text-align:right;color:var(--nimbus-neutral-text-low);">{pct_s}%</span>
                </div>
            </div>
            '''
        
        html = f'''
            <h2 class="section-title">📊 Evolução de Status - Lojas Novas</h2>
            <div class="insight-box info">
                <h4>Comparativo: Com Onboarding vs Sem Onboarding</h4>
                <p>As lojas do Onboarding V2 eram novas e não tinham status em Dezembro. Comparamos sua evolução com lojas de mesma idade ({aging_range}) que <strong>não</strong> participaram do onboarding.</p>
            </div>
            
            <div class="grid-3" style="margin-top:16px;">
                <div class="card" style="text-align:center;background:var(--nimbus-primary-surface);border:1px solid var(--nimbus-primary-interactive);">
                    <div class="card-title">🎓 Com Onboarding</div>
                    <div class="card-value gradient" style="font-size:2rem;">{pct_com}%</div>
                    <div class="card-subtitle">evoluíram para seller</div>
                    <p class="text-muted" style="font-size:0.6875rem;margin-top:4px;">{com_onb.get('evoluiram', 0):,} de {com_onb.get('total', 0):,} lojas</p>
                </div>
                <div class="card" style="text-align:center;">
                    <div class="card-title">📋 Sem Onboarding</div>
                    <div class="card-value" style="font-size:2rem;color:var(--nimbus-neutral-text-low);">{pct_sem}%</div>
                    <div class="card-subtitle">evoluíram para seller</div>
                    <p class="text-muted" style="font-size:0.6875rem;margin-top:4px;">{sem_onb.get('evoluiram', 0):,} de {sem_onb.get('total', 0):,} lojas</p>
                </div>
                <div class="card" style="text-align:center;">
                    <div class="card-title">📈 Diferença</div>
                    <div style="font-size:2rem;font-weight:700;" class="{diff_class}">{("+" if diff_evolucao > 0 else "")}{diff_evolucao}pp</div>
                    <div class="card-subtitle">p-value: {p_value}</div>
                    {sig_badge}
                </div>
            </div>
            
            <div class="card" style="margin-top:16px;">
                <div class="card-title">📊 Distribuição Comparativa por Status</div>
                <p class="text-muted" style="font-size:0.6875rem;margin-bottom:16px;">
                    <span style="display:inline-block;width:12px;height:12px;background:var(--nimbus-primary-interactive);border-radius:2px;margin-right:4px;"></span> Com Onboarding ({com_onb.get('total', 0):,} lojas) 
                    <span style="margin-left:16px;display:inline-block;width:12px;height:12px;background:var(--nimbus-neutral-text-disabled);border-radius:2px;margin-right:4px;"></span> Sem Onboarding ({sem_onb.get('total', 0):,} lojas)
                </p>
                {comparative_rows}
            </div>
        '''
        
        return html
    
    # Análise tradicional de transição (upgrade/downgrade)
    diff_up = comp.get('diff_upgrade', 0)
    diff_down = comp.get('diff_downgrade', 0)
    diff_up_class = 'positive' if diff_up > 0 else ('negative' if diff_up < 0 else '')
    diff_down_class = 'positive' if diff_down < 0 else ('negative' if diff_down > 0 else '')
    
    def generate_matriz_visual_html(data, titulo):
        matriz_visual = data.get('matriz_visual', [])
        status_order = data.get('status_order', [])
        if not matriz_visual:
            return ''
        
        header_cells = '<th>De / Para</th>'
        for status in status_order:
            header_cells += f'<th class="matriz-header">{status}</th>'
        
        body_rows = ''
        for row in matriz_visual:
            # Calcular max POR LINHA para cada tipo de transição
            row_upgrades = [t['count'] for t in row['transicoes'] if t['tipo'] == 'upgrade' and t['count'] > 0]
            row_downgrades = [t['count'] for t in row['transicoes'] if t['tipo'] == 'downgrade' and t['count'] > 0]
            row_estavel = [t['count'] for t in row['transicoes'] if t['tipo'] == 'estavel' and t['count'] > 0]
            
            max_upgrade_row = max(row_upgrades) if row_upgrades else 1
            max_downgrade_row = max(row_downgrades) if row_downgrades else 1
            max_estavel_row = max(row_estavel) if row_estavel else 1
            
            cells = f'<td class="matriz-row-header">{row["de_label"]}</td>'
            for t in row['transicoes']:
                tipo_class = f'matriz-{t["tipo"]}'
                
                # Calcular intensidade POR LINHA
                if t['count'] > 0:
                    if t['tipo'] == 'upgrade':
                        intensity = t['count'] / max_upgrade_row
                    elif t['tipo'] == 'downgrade':
                        intensity = t['count'] / max_downgrade_row
                    else:
                        intensity = t['count'] / max_estavel_row
                else:
                    intensity = 0
                
                opacity = 0.15 + (intensity * 0.6)
                
                if t['tipo'] == 'upgrade':
                    bg = f'rgba(34, 197, 94, {opacity})'
                elif t['tipo'] == 'downgrade':
                    bg = f'rgba(239, 68, 68, {opacity})'
                else:
                    bg = f'rgba(156, 163, 175, {opacity})'
                
                cells += f'<td class="matriz-cell {tipo_class}" style="background:{bg};">{t["count"]:,}<br><span class="matriz-pct">{t["pct"]}%</span></td>'
            body_rows += f'<tr>{cells}</tr>'
        
        return f'''
        <div class="card" style="margin-top:12px;overflow-x:auto;">
            <div class="card-title">{titulo}</div>
            <table class="matriz-table">
                <thead><tr>{header_cells}</tr></thead>
                <tbody>{body_rows}</tbody>
            </table>
            <div class="matriz-legenda">
                <span class="legenda-item"><span class="legenda-cor matriz-upgrade"></span> Upgrade</span>
                <span class="legenda-item"><span class="legenda-cor matriz-estavel"></span> Manteve</span>
                <span class="legenda-item"><span class="legenda-cor matriz-downgrade"></span> Downgrade</span>
                <span class="legenda-item" style="margin-left:16px;"><em>Escala de cor = volume por linha</em></span>
            </div>
        </div>
        '''
    
    html = f'''
            <h2 class="section-title">📊 Matriz de Transição de Status</h2>
            <div class="insight-box info">
                <h4>Comparativo: Com Onboarding vs Sem Onboarding</h4>
                <p>Comparação de lojas que participaram do Onboarding V2 com lojas de mesma idade ({aging_range}) que <strong>não</strong> participaram. Análise do período Dezembro → Janeiro.</p>
            </div>
            
            <div class="grid-2">
                <div>
                    <h3 style="font-size:0.875rem;margin-bottom:12px;color:var(--nimbus-primary-interactive);">🎓 Com Onboarding ({com_onb.get("total", 0):,} lojas)</h3>
                    <div class="risk-matrix" style="grid-template-columns: repeat(3, 1fr);">
                        <div class="risk-card" style="background:#22c55e20;border:2px solid #22c55e;">
                            <h3 style="color:#22c55e;">{com_onb.get('upgrade', 0):,}</h3>
                            <p style="color:#22c55e;font-weight:600;">⬆️ Upgrade</p>
                            <p>{com_onb.get('pct_upgrade', 0)}%</p>
                        </div>
                        <div class="risk-card" style="background:#6b728020;border:2px solid #6b7280;">
                            <h3 style="color:#6b7280;">{com_onb.get('estavel', 0):,}</h3>
                            <p style="color:#6b7280;font-weight:600;">➡️ Estável</p>
                            <p>{com_onb.get('pct_estavel', 0)}%</p>
                        </div>
                        <div class="risk-card" style="background:#ef444420;border:2px solid #ef4444;">
                            <h3 style="color:#ef4444;">{com_onb.get('downgrade', 0):,}</h3>
                            <p style="color:#ef4444;font-weight:600;">⬇️ Downgrade</p>
                            <p>{com_onb.get('pct_downgrade', 0)}%</p>
                        </div>
                    </div>
                </div>
                <div>
                    <h3 style="font-size:0.875rem;margin-bottom:12px;color:var(--nimbus-neutral-text-low);">📋 Sem Onboarding ({sem_onb.get("total", 0):,} lojas)</h3>
                    <div class="risk-matrix" style="grid-template-columns: repeat(3, 1fr);">
                        <div class="risk-card" style="background:#22c55e20;border:2px solid #22c55e;">
                            <h3 style="color:#22c55e;">{sem_onb.get('upgrade', 0):,}</h3>
                            <p style="color:#22c55e;font-weight:600;">⬆️ Upgrade</p>
                            <p>{sem_onb.get('pct_upgrade', 0)}%</p>
                        </div>
                        <div class="risk-card" style="background:#6b728020;border:2px solid #6b7280;">
                            <h3 style="color:#6b7280;">{sem_onb.get('estavel', 0):,}</h3>
                            <p style="color:#6b7280;font-weight:600;">➡️ Estável</p>
                            <p>{sem_onb.get('pct_estavel', 0)}%</p>
                        </div>
                        <div class="risk-card" style="background:#ef444420;border:2px solid #ef4444;">
                            <h3 style="color:#ef4444;">{sem_onb.get('downgrade', 0):,}</h3>
                            <p style="color:#ef4444;font-weight:600;">⬇️ Downgrade</p>
                            <p>{sem_onb.get('pct_downgrade', 0)}%</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-top:16px;text-align:center;">
                <div class="card-title">📈 Diferença (Com Onboarding vs Sem Onboarding)</div>
                <div class="grid-2" style="max-width:400px;margin:0 auto;">
                    <div>
                        <div style="font-size:0.75rem;color:var(--nimbus-neutral-text-low);">Upgrade</div>
                        <div style="font-size:1.5rem;font-weight:700;" class="{diff_up_class}">{("+" if diff_up > 0 else "")}{diff_up}pp</div>
                    </div>
                    <div>
                        <div style="font-size:0.75rem;color:var(--nimbus-neutral-text-low);">Downgrade</div>
                        <div style="font-size:1.5rem;font-weight:700;" class="{diff_down_class}">{("+" if diff_down > 0 else "")}{diff_down}pp</div>
                    </div>
                </div>
            </div>
            
            <div class="grid-2" style="margin-top:16px;">
                <div>{generate_matriz_visual_html(com_onb, "📊 Matriz - Com Onboarding")}</div>
                <div>{generate_matriz_visual_html(sem_onb, "📊 Matriz - Sem Onboarding")}</div>
            </div>
    '''
    
    return html

# Helpers para tabelas
ns_rows = ''.join([f"<tr><td>{m['mes']}</td><td>{m['total_new_sellers']:,}</td><td>{m['com_lifecycle']}</td><td class='{'positive' if m['pct_cobertura']>5 else 'neutral' if m['pct_cobertura']>2 else ''}'>{m['pct_cobertura']}%</td></tr>" for m in dashboard_data['new_sellers']['por_mes'][:6]])

# Helper para gerar setas de tendência
def generate_trend_arrow(current_value, previous_value, is_lower_better=False):
    """Gera HTML de seta de tendência comparando valores"""
    if previous_value is None or previous_value == 0:
        return ''
    
    diff = current_value - previous_value
    pct_change = abs(diff / previous_value * 100) if previous_value != 0 else 0
    
    # Se não houve mudança significativa
    if abs(pct_change) < 0.5:
        return ''
    
    # Determina se a mudança é positiva ou negativa
    if is_lower_better:
        is_positive = diff < 0
    else:
        is_positive = diff > 0
    
    arrow_class = 'up' if is_positive else 'down'
    arrow_svg = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 14l5-5 5 5H7z"/></svg>' if is_positive else '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 10l5 5 5-5H7z"/></svg>'
    
    return f'<span class="trend-arrow {arrow_class}">{arrow_svg}{abs(diff):.1f}pp</span>'

# Para comparativo de período anterior (se disponível)
# Por agora, usamos dados do mês anterior se existir
previous_period_data = None
if len(meses_disponiveis) >= 2:
    mes_anterior = meses_disponiveis[1]
    base_anterior = bases_mensais[mes_anterior]
    
    # Calcular métricas do período anterior
    base_anterior_ids = set(base_anterior[id_col if id_col in base_anterior.columns else 'id_store' if 'id_store' in base_anterior.columns else 'store_id'].unique())
    
    com_webinar_ant = base_anterior[base_anterior[id_col if id_col in base_anterior.columns else 'id_store' if 'id_store' in base_anterior.columns else 'store_id'].isin(ids_webinar)]
    sem_webinar_ant = base_anterior[~base_anterior[id_col if id_col in base_anterior.columns else 'id_store' if 'id_store' in base_anterior.columns else 'store_id'].isin(ids_webinar)]
    
    churn_com_ant = com_webinar_ant[com_webinar_ant['predictive_churn_probability'] > 0]['predictive_churn_probability'].mean() * 100 if len(com_webinar_ant[com_webinar_ant['predictive_churn_probability'] > 0]) > 0 else 0
    churn_sem_ant = sem_webinar_ant[sem_webinar_ant['predictive_churn_probability'] > 0]['predictive_churn_probability'].mean() * 100 if len(sem_webinar_ant[sem_webinar_ant['predictive_churn_probability'] > 0]) > 0 else 0
    gmv_com_ant = com_webinar_ant['gmv_mes_local'].mean() if len(com_webinar_ant) > 0 else 0
    gmv_sem_ant = sem_webinar_ant['gmv_mes_local'].mean() if len(sem_webinar_ant) > 0 else 0
    gmv_diff_pct_ant = ((gmv_com_ant - gmv_sem_ant) / gmv_sem_ant * 100) if gmv_sem_ant > 0 else 0
    churn_diff_ant = churn_com_ant - churn_sem_ant
    
    previous_period_data = {
        'mes': mes_anterior,
        'gmv_diff_pct': round(gmv_diff_pct_ant, 1),
        'churn_diff_pp': round(churn_diff_ant, 2),
        'churn_com': round(churn_com_ant, 2),
        'churn_sem': round(churn_sem_ant, 2),
        'participantes': len(com_webinar_ant)
    }
    dashboard_data['webinars']['periodo_anterior'] = previous_period_data
    print(f"  📅 Período anterior ({mes_anterior}): GMV diff {gmv_diff_pct_ant:.1f}%, Churn diff {churn_diff_ant:.2f}pp")

# Gerar HTML das setas de tendência para webinars
trend_gmv = ''
trend_churn = ''
trend_pareada = ''
trend_churn_pareada = ''

if previous_period_data:
    # GMV: maior é melhor
    current_gmv_diff = dashboard_data['webinars']['performance']['gmv_diff_pct']
    prev_gmv_diff = previous_period_data['gmv_diff_pct']
    if prev_gmv_diff != 0:
        gmv_change = current_gmv_diff - prev_gmv_diff
        if abs(gmv_change) >= 1:
            arrow_class = 'up' if gmv_change > 0 else 'down'
            arrow_svg = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 14l5-5 5 5H7z"/></svg>' if gmv_change > 0 else '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 10l5 5 5-5H7z"/></svg>'
            trend_gmv = f'<span class="trend-arrow {arrow_class}">{arrow_svg}{abs(gmv_change):.0f}pp</span>'
    
    # Churn: menor é melhor (diff negativo é bom)
    current_churn_diff = dashboard_data['webinars']['churn']['diff_pp']
    prev_churn_diff = previous_period_data['churn_diff_pp']
    churn_change = current_churn_diff - prev_churn_diff  # Se ficou mais negativo, melhorou
    if abs(churn_change) >= 0.5:
        is_better = churn_change < 0  # Mais negativo = melhor
        arrow_class = 'up' if is_better else 'down'
        arrow_svg = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 14l5-5 5 5H7z"/></svg>' if is_better else '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 10l5 5 5-5H7z"/></svg>'
        trend_churn = f'<span class="trend-arrow {arrow_class}">{arrow_svg}{abs(churn_change):.1f}pp</span>'

def generate_afinidade_rows():
    """Gera rows da tabela de afinidade de produtos"""
    rows = []
    for a in dashboard_data['merchant_services']['afinidade']:
        relacionados = ', '.join([f"{p['produto']} ({p['pct']}%)" for p in a['produtos_relacionados']])
        rows.append(f"<tr><td><strong>{a['produto']}</strong></td><td>{a['total_clientes']:,}</td><td>{relacionados}</td></tr>")
    return ''.join(rows)

# =============================================================================
# GERAR INSIGHTS AUTOMÁTICOS PARA CADA ABA
# =============================================================================
print("💡 Gerando insights automáticos...")

def generate_insights_html(insights, title="Principais Insights"):
    """Gera HTML de uma seção de insights"""
    if not insights:
        return ''
    
    items = ''.join([f'<li>{i}</li>' for i in insights])
    return f'''
    <div class="insights-section">
        <h2 class="section-title">💡 {title}</h2>
        <div class="insights-box">
            <ul class="insights-list">{items}</ul>
        </div>
    </div>
    '''

# Insights do Resumo Executivo
insights_resumo = []
pct_sellers = dashboard_data['resumo']['pct_sellers']
pct_cobertura = dashboard_data['resumo']['pct_cobertura']
churn_medio = dashboard_data['resumo']['churn_prob_media']

if pct_sellers < 25:
    insights_resumo.append(f"<strong>Oportunidade:</strong> Apenas {pct_sellers}% das lojas são sellers ativos. Há grande potencial de ativação na base.")
else:
    insights_resumo.append(f"<strong>Destaque:</strong> {pct_sellers}% das lojas são sellers ativos, um bom nível de engajamento.")

if pct_cobertura < 5:
    insights_resumo.append(f"<strong>Atenção:</strong> Cobertura de Lifecycle está em {pct_cobertura}%. Expandir ações pode trazer ganhos significativos.")
elif pct_cobertura < 15:
    insights_resumo.append(f"<strong>Progresso:</strong> Cobertura de {pct_cobertura}% - há espaço para crescimento das ações de Lifecycle.")

if churn_medio > 30:
    insights_resumo.append(f"<strong>Alerta:</strong> Risco médio de churn está em {churn_medio}%. Priorizar ações de retenção.")
elif churn_medio > 20:
    insights_resumo.append(f"<strong>Monitorar:</strong> Risco médio de {churn_medio}% requer atenção contínua.")

# Insights sobre quartis de risco
alto_risco = next((q for q in dashboard_data['risk_quartiles'] if q['name'] == 'Alto Risco'), None)
if alto_risco and alto_risco['pct'] > 5:
    insights_resumo.append(f"<strong>Foco:</strong> {alto_risco['count']:,} lojas ({alto_risco['pct']}%) estão em alto risco de churn. GMV em risco: R$ {alto_risco['gmv_total']/1000000:.1f}M.")

# Insights da Visão da Base
insights_base = []
status_dist = dashboard_data['status_base']['distribuicao']

# Encontrar status com maior e menor churn
if status_dist:
    maior_churn = max(status_dist, key=lambda x: x['churn_prob'])
    menor_churn = min([s for s in status_dist if s['churn_prob'] > 0], key=lambda x: x['churn_prob'])
    
    insights_base.append(f"<strong>Maior risco:</strong> Lojas <em>{maior_churn['label']}</em> têm {maior_churn['churn_prob']}% de probabilidade de churn - foco em retenção para este segmento.")
    insights_base.append(f"<strong>Mais estáveis:</strong> Lojas <em>{menor_churn['label']}</em> têm apenas {menor_churn['churn_prob']}% de risco - modelo de sucesso a ser replicado.")
    
    # Top 2 status por volume
    top_status = sorted(status_dist, key=lambda x: x['count'], reverse=True)[:2]
    insights_base.append(f"<strong>Composição:</strong> {top_status[0]['label']} ({top_status[0]['pct']}%) e {top_status[1]['label']} ({top_status[1]['pct']}%) representam quase metade da base.")
    
    # Status com maior GMV
    maior_gmv = max(status_dist, key=lambda x: x['gmv_total'])
    insights_base.append(f"<strong>Receita:</strong> Lojas <em>{maior_gmv['label']}</em> geram R$ {maior_gmv['gmv_total']/1000000:.1f}M em GMV ({maior_gmv['count']:,} lojas com ticket médio de R$ {maior_gmv['gmv_medio']:,.0f}).")

# Insights de Merchant Services
insights_ms = []
ms_data = dashboard_data['merchant_services']

insights_ms.append(f"<strong>Adoção média:</strong> Lojas têm em média {ms_data['media']:.1f} produtos de Merchant Services.")

# Produto mais adotado
mais_adotado = max([p for p in ms_data['por_produto'] if p['pct'] > 0], key=lambda x: x['pct'], default=None)
if mais_adotado:
    insights_ms.append(f"<strong>Líder:</strong> {mais_adotado['produto']} é o produto mais adotado com {mais_adotado['pct']}% de penetração ({mais_adotado['lojas']:,} lojas).")

# Maior oportunidade de cross-sell
if ms_data['cross_sell']:
    maior_potencial = max([c for c in ms_data['cross_sell'] if c['ja_tem'] > 0], key=lambda x: x['potencial'], default=None)
    if maior_potencial:
        insights_ms.append(f"<strong>Cross-sell:</strong> {maior_potencial['produto']} tem potencial de {maior_potencial['potencial']:,} novas adoções entre lojas que já usam outros produtos.")

# Lojas sem nenhum produto
sem_produto = next((d for d in ms_data['distribuicao'] if d['qtd'] == 0), None)
if sem_produto and sem_produto['pct'] > 5:
    insights_ms.append(f"<strong>Oportunidade:</strong> {sem_produto['count']:,} lojas ({sem_produto['pct']}%) não usam nenhum produto MS - grande potencial de first-sell.")

# Combinação mais comum
if ms_data['combinacoes']:
    combo_top = ms_data['combinacoes'][0]
    insights_ms.append(f"<strong>Combo popular:</strong> \"{combo_top['combo']}\" é a combinação mais comum com {combo_top['count']:,} lojas ({combo_top['pct']}%).")

# Insights de Risco de Churn
insights_risco = []
churn_data = dashboard_data['churn']

# Status mais crítico
if churn_data['por_status']:
    mais_critico = max(churn_data['por_status'], key=lambda x: x['prob_media'])
    menos_critico = min(churn_data['por_status'], key=lambda x: x['prob_media'])
    
    insights_risco.append(f"<strong>Segmento crítico:</strong> {mais_critico['label']} tem {mais_critico['prob_media']}% de risco médio - {mais_critico['lojas']:,} lojas precisam de atenção.")
    insights_risco.append(f"<strong>Benchmark:</strong> {menos_critico['label']} tem apenas {menos_critico['prob_media']}% de risco - entender o que diferencia este grupo.")

# Distribuição de quartis
sem_risco = next((q for q in dashboard_data['risk_quartiles'] if q['name'] == 'Sem Risco'), None)
alto_risco = next((q for q in dashboard_data['risk_quartiles'] if q['name'] == 'Alto Risco'), None)
if sem_risco and alto_risco:
    insights_risco.append(f"<strong>Polarização:</strong> {sem_risco['pct']}% das lojas estão sem risco enquanto {alto_risco['pct']}% estão em alto risco - estratégias diferenciadas são necessárias.")

# GMV em risco
medio_risco = next((q for q in dashboard_data['risk_quartiles'] if q['name'] == 'Médio Risco'), None)
if medio_risco and alto_risco:
    gmv_em_risco = medio_risco['gmv_total'] + alto_risco['gmv_total']
    insights_risco.append(f"<strong>Impacto financeiro:</strong> R$ {gmv_em_risco/1000000:.1f}M de GMV está concentrado em lojas de médio e alto risco.")

# Insights de Cobertura
insights_cobertura = []
cobertura_data = dashboard_data['cobertura_projetos']

projetos_ativos = [p for p in cobertura_data if p['status'] == 'ativo']
projetos_breve = [p for p in cobertura_data if p['status'] == 'em breve']

if projetos_ativos:
    total_cobertas = sum(p['lojas'] for p in projetos_ativos)
    insights_cobertura.append(f"<strong>Alcance atual:</strong> {len(projetos_ativos)} projeto(s) ativo(s) impactando {total_cobertas:,} lojas.")

if projetos_breve:
    insights_cobertura.append(f"<strong>Pipeline:</strong> {len(projetos_breve)} projeto(s) em desenvolvimento que vão expandir a cobertura.")

lojas_nao_impactadas = dashboard_data['resumo']['total_lojas_ativas'] - dashboard_data['resumo']['n_cobertas']
insights_cobertura.append(f"<strong>Espaço para crescer:</strong> {lojas_nao_impactadas:,} lojas ainda não foram impactadas por nenhuma ação de Lifecycle.")

# Se cobertura < 10%
if pct_cobertura < 10:
    insights_cobertura.append(f"<strong>Prioridade:</strong> Com apenas {pct_cobertura}% de cobertura, há grande oportunidade de escalar as ações atuais.")

# Insights de Webinars
insights_webinars = []
web_data = dashboard_data['webinars']

# Impacto em GMV
gmv_diff = web_data['performance']['gmv_diff_pct']
if gmv_diff > 100:
    insights_webinars.append(f"<strong>Impacto em vendas:</strong> Lojas com webinar têm GMV {gmv_diff}% maior que lojas sem webinar - resultado expressivo.")
elif gmv_diff > 50:
    insights_webinars.append(f"<strong>Impacto em vendas:</strong> Lojas com webinar têm GMV {gmv_diff}% maior que lojas sem webinar.")

# Impacto em Churn
churn_diff = web_data['churn']['diff_pp']
if churn_diff < -5:
    insights_webinars.append(f"<strong>Retenção:</strong> Webinars reduzem o risco de churn em {abs(churn_diff):.1f}pp - ferramenta eficaz de retenção.")

# Análise pareada
if web_data['analise_pareada']['total_grupos'] > 0:
    gmv_pareado = web_data['analise_pareada']['gmv_diff_pct']
    churn_pareado = web_data['churn_pareado']['diff_pp']
    insights_webinars.append(f"<strong>Evidência causal:</strong> Na análise pareada (mesmo perfil), webinars entregam +{gmv_pareado}% em GMV e {churn_pareado:.1f}pp em churn.")

# Funil
funil = web_data['funil']
if funil['total_geral'] > 0:
    taxa_participacao = funil.get('pct_participaram', 0)
    insights_webinars.append(f"<strong>Conversão:</strong> {taxa_participacao}% dos inscritos participam (live ou on-demand) - {funil['total_participaram']:,} de {funil['total_geral']:,} registros.")

# Risco por quartil
risk_comp = web_data.get('risk_quartiles_comparison', [])
if risk_comp:
    alto_risco_web = next((q for q in risk_comp if q['name'] == 'Alto Risco'), None)
    if alto_risco_web and alto_risco_web['diff_pp'] < -2:
        insights_webinars.append(f"<strong>Proteção:</strong> Apenas {alto_risco_web['pct_com']}% das lojas com webinar estão em alto risco vs {alto_risco_web['pct_sem']}% sem webinar (diferença de {alto_risco_web['diff_pp']}pp).")

# Top status beneficiado
perfil = web_data.get('perfil_status', [])
if perfil:
    mais_engajado = max([p for p in perfil if p['indice'] > 100], key=lambda x: x['indice'], default=None)
    if mais_engajado:
        insights_webinars.append(f"<strong>Perfil engajado:</strong> {mais_engajado['label']} tem índice {int(mais_engajado['indice'])} de participação - {mais_engajado['pct_webinar']}% dos participantes vs {mais_engajado['pct_base']}% da base.")

# Gerar HTML dos insights
insights_resumo_html = generate_insights_html(insights_resumo)
insights_base_html = generate_insights_html(insights_base)
insights_ms_html = generate_insights_html(insights_ms)
insights_risco_html = generate_insights_html(insights_risco)
insights_cobertura_html = generate_insights_html(insights_cobertura)
insights_webinars_html = generate_insights_html(insights_webinars)

# =============================================================================
# GERAR HTML DA ABA DE ICP
# =============================================================================
def get_icp_color(icp):
    colors = {'ICP 1': '#0059d5', 'ICP 2': '#22c55e', 'ICP 3': '#f97316', 'ICP 4': '#ef4444'}
    return colors.get(icp, '#6b7280')

def get_icp_bg(icp):
    bgs = {'ICP 1': '#0059d520', 'ICP 2': '#22c55e20', 'ICP 3': '#f9731620', 'ICP 4': '#ef444420'}
    return bgs.get(icp, '#6b728020')

# Cards de resumo por ICP
icp_cards_html = ''
for d in dashboard_data['icp']['por_icp']:
    icp_name = d['icp']
    color = get_icp_color(icp_name)
    bg = get_icp_bg(icp_name)
    icp_cards_html += f'''<div class="risk-card" style="background:{bg};border:2px solid {color};">
        <h3 style="color:{color};">{d['total']:,}</h3>
        <p style="color:{color};font-weight:600;">{icp_name}</p>
        <p>{d['pct_base']}% da base</p>
    </div>'''

# Tabela comparativa
icp_table_rows_html = ''
for d in dashboard_data['icp']['por_icp']:
    if d['icp'] == 'Não Classificado':
        continue
    icp_name = d['icp']
    color = get_icp_color(icp_name)
    sellers_class = 'positive' if d['pct_sellers'] > 30 else ('neutral' if d['pct_sellers'] > 15 else 'negative')
    churn_class = 'positive' if d['pct_risco_churn'] < 20 else ('neutral' if d['pct_risco_churn'] < 30 else 'negative')
    icp_table_rows_html += f'''<tr>
        <td><strong style="color:{color};">{icp_name}</strong></td>
        <td>{d['total']:,}</td>
        <td class="{sellers_class}">{d['pct_sellers']}%</td>
        <td>R$ {d['gmv_medio']:,.0f}</td>
        <td class="{churn_class}">{d['pct_risco_churn']}%</td>
        <td>{d['pct_onboarding']}% ({d['n_onboarding']:,})</td>
        <td>{d['pct_webinar']}% ({d['n_webinar']:,})</td>
    </tr>'''

# Distribuição de status por ICP
icp_status_cards_html = ''
for d in dashboard_data['icp']['por_icp']:
    if d['icp'] == 'Não Classificado':
        continue
    icp_name = d['icp']
    status_bars = ''
    for s in d['status_dist'][:6]:
        bar_color = '#22c55e' if s['status'] in SELLER_STATUS else ('#ef4444' if s['status'] == 'no-seller' else '#f97316')
        status_bars += f'''<div style="display:flex;align-items:center;margin-bottom:4px;">
            <div style="width:100px;font-size:0.75rem;">{s['label']}</div>
            <div style="flex:1;height:16px;background:var(--nimbus-neutral-surface-highlight);border-radius:4px;overflow:hidden;">
                <div style="width:{s['pct']}%;height:100%;background:{bar_color};"></div>
            </div>
            <div style="width:60px;text-align:right;font-size:0.75rem;">{s['pct']}%</div>
        </div>'''
    icp_status_cards_html += f'''<div class="card">
        <div class="card-title">{icp_name}</div>
        <p class="text-muted">{d['total']:,} lojas | {d['pct_sellers']}% sellers | GMV Total: R$ {d['gmv_total']:,.0f}</p>
        {status_bars}
    </div>'''

# Insights de ICP
icp_insights_html = ''
for d in dashboard_data['icp']['por_icp']:
    if d['icp'] == 'Não Classificado':
        continue
    icp_insights_html += f'<li><strong>{d["icp"]}:</strong> {d["total"]:,} lojas ({d["pct_base"]}%), {d["pct_sellers"]}% são sellers, risco médio de {d["pct_risco_churn"]}%</li>'

# Matriz de transição por ICP
icp_transicao_html = ''
if dashboard_data['icp'].get('transicao') and len(dashboard_data['icp']['transicao']) > 0:
    icp_transicao_html = '''<h2 class="section-title" style="margin-top:32px;">📈 Matriz de Transição por ICP (Dez → Jan)</h2>
    <div class="risk-matrix" style="grid-template-columns: repeat(4, 1fr);">'''
    
    for t in dashboard_data['icp']['transicao']:
        color = get_icp_color(t['icp'])
        bg = get_icp_bg(t['icp'])
        icp_transicao_html += f'''
        <div class="card" style="border-left:4px solid {color};">
            <div class="card-title" style="color:{color};">{t['icp']}</div>
            <p class="text-muted">{t['total']:,} lojas comparadas</p>
            <div style="display:flex;gap:8px;margin-top:8px;">
                <div style="flex:1;text-align:center;padding:8px;background:#22c55e20;border-radius:8px;">
                    <div style="font-size:1.25rem;font-weight:700;color:#22c55e;">↑ {t['pct_upgrade']}%</div>
                    <div style="font-size:0.7rem;color:#666;">Upgrade ({t['upgrade']:,})</div>
                </div>
                <div style="flex:1;text-align:center;padding:8px;background:#6b728020;border-radius:8px;">
                    <div style="font-size:1.25rem;font-weight:700;color:#6b7280;">→ {t['pct_estavel']}%</div>
                    <div style="font-size:0.7rem;color:#666;">Estável ({t['estavel']:,})</div>
                </div>
                <div style="flex:1;text-align:center;padding:8px;background:#ef444420;border-radius:8px;">
                    <div style="font-size:1.25rem;font-weight:700;color:#ef4444;">↓ {t['pct_downgrade']}%</div>
                    <div style="font-size:0.7rem;color:#666;">Downgrade ({t['downgrade']:,})</div>
                </div>
            </div>
        </div>'''
    
    icp_transicao_html += '</div>'

# Quadrantes de Idade x Status por ICP
icp_aging_html = ''
if dashboard_data['icp'].get('aging') and len(dashboard_data['icp']['aging']) > 0:
    icp_aging_html = '''<h2 class="section-title" style="margin-top:32px;">🕐 Quadrantes: Tempo x Status por ICP</h2>
    <div class="insight-box info">
        <h4>📊 Análise de maturidade</h4>
        <p>Entenda se os no-sellers estão em fase inicial (ainda vão converter) ou se são lojas antigas que nunca converteram (risco de abandono).</p>
    </div>
    <div class="grid-2" style="margin-top:16px;">'''
    
    for aging in dashboard_data['icp']['aging']:
        color = get_icp_color(aging['icp'])
        icp_aging_html += f'''
        <div class="card">
            <div class="card-title" style="color:{color};">{aging['icp']} - Idade média: {int(aging['aging_medio'])} dias</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;">'''
        
        for q in aging['quadrantes']:
            icp_aging_html += f'''
                <div style="padding:12px;background:{q['cor']}15;border-radius:8px;border-left:3px solid {q['cor']};">
                    <div style="font-size:1.5rem;font-weight:700;color:{q['cor']};">{q['pct']}%</div>
                    <div style="font-size:0.8rem;font-weight:600;">{q['quadrante']}</div>
                    <div style="font-size:0.7rem;color:#666;">{q['descricao']} ({q['count']:,})</div>
                </div>'''
        
        icp_aging_html += '''
            </div>
            <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--nimbus-neutral-surface-highlight);">
                <div style="font-size:0.75rem;color:#666;font-weight:600;">Distribuição por faixa de idade:</div>
                <div style="display:flex;gap:4px;margin-top:4px;">'''
        
        for f in aging['por_faixa']:
            bar_width = max(f['pct'] * 2, 10)
            icp_aging_html += f'''<div style="flex:0 0 {bar_width}px;text-align:center;">
                    <div style="height:30px;background:linear-gradient(to top, #22c55e {f['pct_sellers']}%, #ef4444 {f['pct_sellers']}%);border-radius:4px;" title="{f['faixa']}: {f['pct_sellers']}% sellers"></div>
                    <div style="font-size:0.6rem;color:#888;margin-top:2px;">{f['faixa'].replace(' dias','d').replace(' ano','a')}</div>
                </div>'''
        
        icp_aging_html += '''
                </div>
            </div>
        </div>'''
    
    icp_aging_html += '</div>'

matriz_html = ''
if matriz_transicao['disponivel']:
    # Top transições HTML
    top_up_html = ''
    if matriz_transicao.get('top_upgrades'):
        top_up_rows = ''.join([
            f"<tr><td>{t['de']}</td><td>→</td><td>{t['para']}</td><td class='positive'>{t['count']:,}</td></tr>"
            for t in matriz_transicao['top_upgrades']
        ])
        top_up_html = f'''
        <div class="card" style="margin-top:16px;">
            <div class="card-title">🔝 Top Upgrades</div>
            <table class="mini-table">
                <thead><tr><th>De</th><th></th><th>Para</th><th>Lojas</th></tr></thead>
                <tbody>{top_up_rows}</tbody>
            </table>
        </div>
        '''
    
    top_down_html = ''
    if matriz_transicao.get('top_downgrades'):
        top_down_rows = ''.join([
            f"<tr><td>{t['de']}</td><td>→</td><td>{t['para']}</td><td class='negative'>{t['count']:,}</td></tr>"
            for t in matriz_transicao['top_downgrades']
        ])
        top_down_html = f'''
        <div class="card" style="margin-top:16px;">
            <div class="card-title">🔻 Top Downgrades</div>
            <table class="mini-table">
                <thead><tr><th>De</th><th></th><th>Para</th><th>Lojas</th></tr></thead>
                <tbody>{top_down_rows}</tbody>
            </table>
        </div>
        '''
    
    # Entradas e saídas (removido - agora incluído na matriz com "not informed")
    entradas_saidas_html = ''
    
    # Gerar tabela visual da matriz de transição com escala de cores POR LINHA
    matriz_visual_html = ''
    if matriz_transicao.get('matriz_visual'):
        status_headers = matriz_transicao.get('status_order', [])
        header_row = '<th class="matriz-corner">De \\ Para</th>' + ''.join([f'<th class="matriz-header">{s}</th>' for s in status_headers]) + '<th class="matriz-total">Total</th>'
        
        body_rows = ''
        for row in matriz_transicao['matriz_visual']:
            # Calcular max POR LINHA para cada tipo de transição
            row_upgrades = [t['count'] for t in row['transicoes'] if t['tipo'] == 'upgrade' and t['count'] > 0]
            row_downgrades = [t['count'] for t in row['transicoes'] if t['tipo'] == 'downgrade' and t['count'] > 0]
            row_estavel = [t['count'] for t in row['transicoes'] if t['tipo'] == 'estavel' and t['count'] > 0]
            
            max_upgrade_row = max(row_upgrades) if row_upgrades else 1
            max_downgrade_row = max(row_downgrades) if row_downgrades else 1
            max_estavel_row = max(row_estavel) if row_estavel else 1
            
            cells = f'<td class="matriz-row-header">{row["de_label"]}</td>'
            for t in row['transicoes']:
                if t['count'] > 0:
                    # Calcular intensidade baseada no tipo - ESCALA POR LINHA
                    if t['tipo'] == 'upgrade':
                        intensity = t['count'] / max_upgrade_row
                        # Verde: de claro (0.2) a escuro (0.8) - usando rgb(34, 197, 94)
                        opacity = 0.15 + (intensity * 0.65)
                        bg_color = f'rgba(34, 197, 94, {opacity})'
                    elif t['tipo'] == 'downgrade':
                        intensity = t['count'] / max_downgrade_row
                        # Vermelho: de claro (0.2) a escuro (0.8) - usando rgb(239, 68, 68)
                        opacity = 0.15 + (intensity * 0.65)
                        bg_color = f'rgba(239, 68, 68, {opacity})'
                    else:
                        intensity = t['count'] / max_estavel_row
                        # Cinza: de claro a mais visível
                        opacity = 0.1 + (intensity * 0.4)
                        bg_color = f'rgba(156, 163, 175, {opacity})'
                    
                    css_class = 'matriz-upgrade' if t['tipo'] == 'upgrade' else ('matriz-downgrade' if t['tipo'] == 'downgrade' else 'matriz-estavel')
                    cells += f'<td class="matriz-cell {css_class}" style="background:{bg_color};" title="{t["pct"]}%"><span class="matriz-count">{t["count"]:,}</span><span class="matriz-pct">{t["pct"]}%</span></td>'
                else:
                    cells += f'<td class="matriz-cell matriz-zero">-</td>'
            cells += f'<td class="matriz-total-cell">{row["total"]:,}</td>'
            body_rows += f'<tr>{cells}</tr>'
        
        matriz_visual_html = f'''
        <div class="card" style="margin-top:16px;overflow-x:auto;">
            <div class="card-title">📊 Matriz de Transição Completa</div>
            <p class="text-muted" style="margin-bottom:12px;">Linhas = Status em Dezembro | Colunas = Status em Janeiro | Intensidade da cor = volume por linha</p>
            <table class="matriz-table">
                <thead><tr>{header_row}</tr></thead>
                <tbody>{body_rows}</tbody>
            </table>
            <div class="matriz-legenda">
                <span class="legenda-item"><span class="legenda-cor" style="background:rgba(34, 197, 94, 0.3);"></span> Upgrade (claro)</span>
                <span class="legenda-item"><span class="legenda-cor" style="background:rgba(34, 197, 94, 0.8);"></span> Upgrade (intenso)</span>
                <span class="legenda-item"><span class="legenda-cor" style="background:rgba(239, 68, 68, 0.3);"></span> Downgrade (claro)</span>
                <span class="legenda-item"><span class="legenda-cor" style="background:rgba(239, 68, 68, 0.8);"></span> Downgrade (intenso)</span>
                <span class="legenda-item"><span class="legenda-cor" style="background:rgba(156, 163, 175, 0.3);"></span> Manteve</span>
            </div>
        </div>
        '''
    
    # Gerar insights de fluxo líquido com detalhamento
    fluxo_liquido_html = ''
    if matriz_transicao.get('fluxo_liquido'):
        fluxo = matriz_transicao['fluxo_liquido']
        
        # Separar ganhadores e perdedores
        ganhadores = [f for f in fluxo if f['variacao'] > 0]
        perdedores = [f for f in fluxo if f['variacao'] < 0]
        
        # Ganhadores com detalhamento
        ganhadores_html = ''
        for i, g in enumerate(ganhadores[:4]):
            entradas_detalhe = g.get('entradas_detalhe', [])
            saidas_detalhe = g.get('saidas_detalhe', [])
            entradas_str = ', '.join([f"{e['de']}: {e['count']:,}" for e in entradas_detalhe[:3]]) if entradas_detalhe else 'N/A'
            saidas_str = ', '.join([f"{s['para']}: {s['count']:,}" for s in saidas_detalhe[:3]]) if saidas_detalhe else 'N/A'
            
            ganhadores_html += f'''
            <div class="fluxo-item fluxo-positivo fluxo-expandable" onclick="toggleFluxoDetalhe('ganhador-{i}')">
                <div class="fluxo-main">
                    <span class="fluxo-status">{g["label"]}</span>
                    <span class="fluxo-valor">+{g["variacao"]:,}</span>
                    <span class="fluxo-pct">(+{g["pct_variacao"]}%)</span>
                    <span class="fluxo-expand-icon">▼</span>
                </div>
                <div id="ganhador-{i}" class="fluxo-detalhe" style="display:none;">
                    <div class="fluxo-detalhe-row"><strong>Entradas ({g.get("entradas", 0):,}):</strong> {entradas_str}</div>
                    <div class="fluxo-detalhe-row"><strong>Saídas ({g.get("saidas", 0):,}):</strong> {saidas_str}</div>
                </div>
            </div>'''
        
        # Perdedores com detalhamento
        perdedores_html = ''
        for i, p in enumerate(perdedores[:4]):
            entradas_detalhe = p.get('entradas_detalhe', [])
            saidas_detalhe = p.get('saidas_detalhe', [])
            entradas_str = ', '.join([f"{e['de']}: {e['count']:,}" for e in entradas_detalhe[:3]]) if entradas_detalhe else 'N/A'
            saidas_str = ', '.join([f"{s['para']}: {s['count']:,}" for s in saidas_detalhe[:3]]) if saidas_detalhe else 'N/A'
            
            perdedores_html += f'''
            <div class="fluxo-item fluxo-negativo fluxo-expandable" onclick="toggleFluxoDetalhe('perdedor-{i}')">
                <div class="fluxo-main">
                    <span class="fluxo-status">{p["label"]}</span>
                    <span class="fluxo-valor">{p["variacao"]:,}</span>
                    <span class="fluxo-pct">({p["pct_variacao"]}%)</span>
                    <span class="fluxo-expand-icon">▼</span>
                </div>
                <div id="perdedor-{i}" class="fluxo-detalhe" style="display:none;">
                    <div class="fluxo-detalhe-row"><strong>Entradas ({p.get("entradas", 0):,}):</strong> {entradas_str}</div>
                    <div class="fluxo-detalhe-row"><strong>Saídas ({p.get("saidas", 0):,}):</strong> {saidas_str}</div>
                </div>
            </div>'''
        
        # Calcular balanço líquido geral
        balanco = matriz_transicao['upgrade'] - matriz_transicao['downgrade']
        balanco_class = 'positive' if balanco > 0 else 'negative' if balanco < 0 else ''
        balanco_sinal = '+' if balanco > 0 else ''
        
        fluxo_liquido_html = f'''
        <div class="card" style="margin-top:16px;">
            <div class="card-title">📈 Fluxo Líquido por Status</div>
            <p class="text-muted" style="margin-bottom:12px;">Clique em cada status para ver de onde vieram as entradas e para onde foram as saídas</p>
            <div class="insight-box info" style="margin-bottom:16px;">
                <p><strong>Balanço Geral:</strong> <span class="{balanco_class}">{balanco_sinal}{balanco:,} lojas</span> — Diferença entre upgrades ({matriz_transicao['upgrade']:,}) e downgrades ({matriz_transicao['downgrade']:,})</p>
            </div>
            <div class="grid-2">
                <div>
                    <h4 style="color:var(--success-text);margin-bottom:8px;">📈 Status que Ganharam Lojas</h4>
                    <div class="fluxo-lista">{ganhadores_html if ganhadores_html else '<p class="text-muted">Nenhum status com ganho</p>'}</div>
                </div>
                <div>
                    <h4 style="color:var(--danger-text);margin-bottom:8px;">📉 Status que Perderam Lojas</h4>
                    <div class="fluxo-lista">{perdedores_html if perdedores_html else '<p class="text-muted">Nenhum status com perda</p>'}</div>
                </div>
            </div>
        </div>
        '''
    
    ni_data = matriz_transicao.get('not_informed', {})
    ni_total = ni_data.get('total', 0)
    ni_virou_seller = ni_data.get('virou_seller', 0)
    ni_virou_no_seller = ni_data.get('virou_no_seller', 0)
    ni_pct_seller = ni_data.get('pct_seller', 0)
    ni_pct_no_seller = ni_data.get('pct_no_seller', 0)
    
    matriz_html = f'''
    <div class="insight-box info" style="margin-bottom:16px;">
        <h4>📊 Lojas com Status Definido em {matriz_transicao['mes_anterior']}</h4>
        <p>Análise de transição apenas para lojas que já tinham status definido (não inclui "não classificados").</p>
    </div>
    <div class="risk-matrix" style="grid-template-columns: repeat(3, 1fr);">
        <div class="risk-card" style="background:#22c55e20;border:2px solid #22c55e;">
            <h3 style="color:#22c55e;">{matriz_transicao['upgrade']:,}</h3>
            <p style="color:#22c55e;font-weight:600;">⬆️ Upgrade</p>
            <p>{matriz_transicao['pct_upgrade']}%</p>
        </div>
        <div class="risk-card" style="background:#6b728020;border:2px solid #6b7280;">
            <h3 style="color:#6b7280;">{matriz_transicao['estavel']:,}</h3>
            <p style="color:#6b7280;font-weight:600;">➡️ Estável</p>
            <p>{matriz_transicao['pct_estavel']}%</p>
        </div>
        <div class="risk-card" style="background:#ef444420;border:2px solid #ef4444;">
            <h3 style="color:#ef4444;">{matriz_transicao['downgrade']:,}</h3>
            <p style="color:#ef4444;font-weight:600;">⬇️ Downgrade</p>
            <p>{matriz_transicao['pct_downgrade']}%</p>
        </div>
    </div>
    <p class="text-center text-muted">Lojas com status definido: {matriz_transicao.get('total_comparado', 0):,}</p>
    
    <div class="insight-box warning" style="margin-top:24px;margin-bottom:16px;">
        <h4>🆕 Lojas Novas (Não Classificadas em {matriz_transicao['mes_anterior']})</h4>
        <p>Estas {ni_total:,} lojas eram "não classificadas" em dezembro e agora têm status definido.</p>
    </div>
    <div class="risk-matrix" style="grid-template-columns: repeat(2, 1fr);">
        <div class="risk-card" style="background:#22c55e20;border:2px solid #22c55e;">
            <h3 style="color:#22c55e;">{ni_virou_seller:,}</h3>
            <p style="color:#22c55e;font-weight:600;">✅ Viraram Seller</p>
            <p>{ni_pct_seller}% das lojas novas</p>
        </div>
        <div class="risk-card" style="background:#f9731620;border:2px solid #f97316;">
            <h3 style="color:#f97316;">{ni_virou_no_seller:,}</h3>
            <p style="color:#f97316;font-weight:600;">⚠️ Viraram No-Seller</p>
            <p>{ni_pct_no_seller}% das lojas novas</p>
        </div>
    </div>
    <p class="text-center text-muted">Total de lojas não classificadas em {matriz_transicao['mes_anterior']}: {ni_total:,}</p>
    {entradas_saidas_html}
    {matriz_visual_html}
    {fluxo_liquido_html}
    <div class="grid-2">
        {top_up_html}
        {top_down_html}
    </div>
    '''
else:
    matriz_html = '<div class="insight-box warning"><h4>📊 Matriz de Transição</h4><p>Carregue uma base do mês anterior na pasta <code>data/base_geral/</code></p></div>'

# Matriz de transição de webinars
webinar_transicao_html = ''
matriz_web = dashboard_data['webinars'].get('matriz_transicao', {})
if matriz_web.get('disponivel'):
    # Cards de resumo
    comp = matriz_web.get('comparativo', {})
    diff_up = comp.get('diff_upgrade', 0)
    diff_down = comp.get('diff_downgrade', 0)
    
    diff_up_class = 'positive' if diff_up > 0 else ('negative' if diff_up < 0 else '')
    diff_down_class = 'negative' if diff_down > 0 else ('positive' if diff_down < 0 else '')
    
    # Fluxo líquido de webinars
    fluxo_web = matriz_web.get('fluxo_liquido', [])
    ganhadores_web = [f for f in fluxo_web if f['variacao'] > 0]
    perdedores_web = [f for f in fluxo_web if f['variacao'] < 0]
    
    ganhadores_web_html = ''
    for g in ganhadores_web[:4]:
        ganhadores_web_html += f'<div class="fluxo-item fluxo-positivo"><span class="fluxo-status">{g["label"]}</span><span class="fluxo-valor">+{g["variacao"]:,}</span><span class="fluxo-pct">(+{g["pct_variacao"]}%)</span></div>'
    
    perdedores_web_html = ''
    for p in perdedores_web[:4]:
        perdedores_web_html += f'<div class="fluxo-item fluxo-negativo"><span class="fluxo-status">{p["label"]}</span><span class="fluxo-valor">{p["variacao"]:,}</span><span class="fluxo-pct">({p["pct_variacao"]}%)</span></div>'
    
    # Balanço líquido
    balanco_web = matriz_web['upgrade'] - matriz_web['downgrade']
    balanco_web_class = 'positive' if balanco_web > 0 else ('negative' if balanco_web < 0 else '')
    balanco_web_sinal = '+' if balanco_web > 0 else ''
    
    webinar_transicao_html = f'''
    <div class="insight-box info">
        <h4>📊 Transição de Status - Dezembro → Janeiro</h4>
        <p>Análise de como as <strong>{matriz_web.get("total", 0):,} lojas</strong> que participaram de webinars evoluíram de status ao longo do período.</p>
    </div>
    <div class="risk-matrix" style="grid-template-columns: repeat(3, 1fr);">
        <div class="risk-card" style="background:#22c55e20;border:2px solid #22c55e;">
            <h3 style="color:#22c55e;">{matriz_web['upgrade']:,}</h3>
            <p style="color:#22c55e;font-weight:600;">⬆️ Upgrade</p>
            <p>{matriz_web['pct_upgrade']}% <span class="{diff_up_class}">({("+" if diff_up > 0 else "")}{diff_up}pp vs base)</span></p>
        </div>
        <div class="risk-card" style="background:#6b728020;border:2px solid #6b7280;">
            <h3 style="color:#6b7280;">{matriz_web['estavel']:,}</h3>
            <p style="color:#6b7280;font-weight:600;">➡️ Estável</p>
            <p>{matriz_web['pct_estavel']}%</p>
        </div>
        <div class="risk-card" style="background:#ef444420;border:2px solid #ef4444;">
            <h3 style="color:#ef4444;">{matriz_web['downgrade']:,}</h3>
            <p style="color:#ef4444;font-weight:600;">⬇️ Downgrade</p>
            <p>{matriz_web['pct_downgrade']}% <span class="{diff_down_class}">({("+" if diff_down > 0 else "")}{diff_down}pp vs base)</span></p>
        </div>
    </div>
    <div class="card" style="margin-top:16px;">
        <div class="card-title">📈 Fluxo Líquido por Status (Impactados por Webinar)</div>
        <div class="insight-box info" style="margin-bottom:16px;">
            <p><strong>Balanço Geral:</strong> <span class="{balanco_web_class}">{balanco_web_sinal}{balanco_web:,} lojas</span> — Upgrades ({matriz_web['upgrade']:,}) menos downgrades ({matriz_web['downgrade']:,})</p>
        </div>
        <div class="grid-2">
            <div>
                <h4 style="color:var(--success-text);margin-bottom:8px;">📈 Status que Ganharam Lojas</h4>
                <div class="fluxo-lista">{ganhadores_web_html if ganhadores_web_html else '<p class="text-muted">Nenhum status com ganho</p>'}</div>
            </div>
            <div>
                <h4 style="color:var(--danger-text);margin-bottom:8px;">📉 Status que Perderam Lojas</h4>
                <div class="fluxo-lista">{perdedores_web_html if perdedores_web_html else '<p class="text-muted">Nenhum status com perda</p>'}</div>
            </div>
        </div>
    </div>
    '''
else:
    webinar_transicao_html = '<div class="insight-box warning"><p>Matriz de transição não disponível. Carregue a base de dezembro para comparar.</p></div>'

# Comparativo MS webinar
ms_comparison_rows = ''.join([
    f"<tr><td><strong>{p['produto']}</strong></td><td>{dashboard_data['webinars']['merchant_services']['com_webinar']['por_produto'][i]['pct']}%</td><td>{p['pct']}%</td><td class='{'positive' if p['diff']>0 else 'negative' if p['diff']<0 else ''}'>{'+' if p['diff']>0 else ''}{p['diff']}pp</td></tr>"
    for i, p in enumerate(dashboard_data['webinars']['merchant_services']['sem_webinar']['por_produto'])
])

html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Impacto - Lifecycle BR</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Geist Font from Vercel (Nimbus Typography) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        @font-face {{
            font-family: 'Geist';
            src: url('https://assets.vercel.com/raw/upload/v1713981000/geist/Geist-Regular.woff2') format('woff2');
            font-weight: 400;
            font-style: normal;
            font-display: swap;
        }}
        @font-face {{
            font-family: 'Geist';
            src: url('https://assets.vercel.com/raw/upload/v1713981000/geist/Geist-Medium.woff2') format('woff2');
            font-weight: 500;
            font-style: normal;
            font-display: swap;
        }}
        @font-face {{
            font-family: 'Geist';
            src: url('https://assets.vercel.com/raw/upload/v1713981000/geist/Geist-SemiBold.woff2') format('woff2');
            font-weight: 600;
            font-style: normal;
            font-display: swap;
        }}
        @font-face {{
            font-family: 'Geist';
            src: url('https://assets.vercel.com/raw/upload/v1713981000/geist/Geist-Bold.woff2') format('woff2');
            font-weight: 700;
            font-style: normal;
            font-display: swap;
        }}
    </style>
    <style>
        /* ========================================
           NIMBUS DESIGN SYSTEM - DARK THEME
           Fonte: Geist | Cores: Nimbus + Semáforo
           ======================================== */
        
        :root {{
            /* Nimbus Primary */
            --nimbus-primary-surface: #1a2744;
            --nimbus-primary-surface-highlight: #96c1fc;
            --nimbus-primary-interactive: #0059d5;
            --nimbus-primary-interactive-hover: #00429f;
            --nimbus-primary-text-low: #96c1fc;
            --nimbus-primary-text-high: #eef5ff;
            
            /* Nimbus Neutral (Dark Theme) */
            --nimbus-neutral-background: #0a0a0a;
            --nimbus-neutral-surface: #141414;
            --nimbus-neutral-surface-highlight: #1f1f1f;
            --nimbus-neutral-interactive: #2a2a2a;
            --nimbus-neutral-text-disabled: #6d6d6d;
            --nimbus-neutral-text-low: #888888;
            --nimbus-neutral-text-high: #f6f6f6;
            
            /* Semáforo - Success (Verde) */
            --success-surface: rgba(0, 200, 123, 0.1);
            --success-interactive: #00c87b;
            --success-text: #7af7c7;
            
            /* Semáforo - Warning (Amarelo/Laranja) */
            --warning-surface: rgba(200, 123, 0, 0.1);
            --warning-interactive: #c87b00;
            --warning-text: #f7c77a;
            
            /* Semáforo - Danger (Vermelho) */
            --danger-surface: rgba(200, 0, 3, 0.1);
            --danger-interactive: #c80003;
            --danger-text: #f77a7c;
            
            /* Spacing */
            --spacing-1: 4px;
            --spacing-2: 8px;
            --spacing-3: 12px;
            --spacing-4: 16px;
            --spacing-5: 20px;
            --spacing-6: 24px;
            --spacing-8: 32px;
            
            /* Border Radius */
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Geist', 'Inter', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', arial, sans-serif;
            background: var(--nimbus-neutral-background);
            min-height: 100vh;
            color: var(--nimbus-neutral-text-high);
            font-size: 14px;
            line-height: 1.5;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(90deg, var(--nimbus-primary-interactive) 0%, #00347d 100%);
            padding: var(--spacing-6) 40px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{ 
            font-size: 1.5rem; 
            font-weight: 600; 
            letter-spacing: -0.02em;
            color: #ffffff;
        }}
        .header p {{ 
            opacity: 0.85; 
            font-size: 0.875rem; 
            margin-top: var(--spacing-1);
            font-weight: 400;
        }}
        
        /* Tabs Navigation */
        .tabs {{
            display: flex;
            background: var(--nimbus-neutral-surface);
            padding: 0 40px;
            border-bottom: 1px solid var(--nimbus-neutral-interactive);
            overflow-x: auto;
        }}
        .tab {{
            padding: var(--spacing-4) var(--spacing-5);
            cursor: pointer;
            border-bottom: 3px solid transparent;
            font-weight: 500;
            color: var(--nimbus-neutral-text-low);
            white-space: nowrap;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }}
        .tab:hover {{ 
            color: var(--nimbus-neutral-text-high); 
            background: var(--nimbus-neutral-surface-highlight); 
        }}
        .tab.active {{ 
            color: var(--nimbus-primary-interactive); 
            border-bottom-color: var(--nimbus-primary-interactive);
            font-weight: 600;
        }}
        .tab.disabled {{ 
            color: var(--nimbus-neutral-text-disabled); 
            cursor: not-allowed; 
        }}
        
        /* Badges */
        .badge {{ 
            background: var(--nimbus-neutral-interactive); 
            padding: 2px 8px; 
            border-radius: 100px; 
            font-size: 0.6875rem; 
            margin-left: var(--spacing-2);
            font-weight: 500;
        }}
        .badge.soon {{ 
            background: var(--warning-surface); 
            color: var(--warning-text);
            border: 1px solid var(--warning-interactive);
        }}
        
        /* Content Area */
        .content {{ 
            padding: var(--spacing-8) 40px; 
            max-width: 1600px; 
            margin: 0 auto; 
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        
        /* Grid System */
        .grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
            gap: var(--spacing-4); 
            margin-bottom: var(--spacing-6); 
        }}
        .grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
        .grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
        .grid-4 {{ grid-template-columns: repeat(4, 1fr); }}
        .grid-5 {{ grid-template-columns: repeat(5, 1fr); }}
        
        /* Cards */
        .card {{
            background: var(--nimbus-neutral-surface);
            border-radius: var(--radius-lg);
            padding: var(--spacing-5);
            border: 1px solid var(--nimbus-neutral-interactive);
            transition: border-color 0.2s ease;
        }}
        .card:hover {{
            border-color: var(--nimbus-neutral-text-disabled);
        }}
        .card-title {{ 
            font-size: 0.6875rem; 
            text-transform: uppercase; 
            letter-spacing: 0.08em; 
            color: var(--nimbus-neutral-text-low); 
            margin-bottom: var(--spacing-2);
            font-weight: 500;
        }}
        .card-value {{ 
            font-size: 1.75rem; 
            font-weight: 700; 
            color: var(--nimbus-neutral-text-high);
            letter-spacing: -0.02em;
        }}
        .card-value.gradient {{ 
            background: linear-gradient(90deg, var(--nimbus-primary-interactive), var(--nimbus-primary-surface-highlight)); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .card-subtitle {{ 
            font-size: 0.75rem; 
            color: var(--nimbus-neutral-text-low); 
            margin-top: var(--spacing-1); 
        }}
        
        /* Status Colors - Semáforo */
        .positive {{ color: var(--success-text); }}
        .negative {{ color: var(--danger-text); }}
        .neutral {{ color: var(--warning-text); }}
        
        /* Section Titles */
        .section-title {{ 
            font-size: 1rem; 
            font-weight: 600; 
            margin: var(--spacing-8) 0 var(--spacing-4) 0; 
            padding-bottom: var(--spacing-3); 
            border-bottom: 1px solid var(--nimbus-neutral-interactive);
            color: var(--nimbus-neutral-text-high);
        }}
        
        /* Charts */
        .chart-container {{ position: relative; height: 280px; }}
        
        /* Tables */
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: var(--spacing-3); 
        }}
        th, td {{ 
            padding: var(--spacing-3); 
            text-align: left; 
            border-bottom: 1px solid var(--nimbus-neutral-interactive); 
            font-size: 0.8125rem; 
        }}
        th {{ 
            font-size: 0.625rem; 
            text-transform: uppercase; 
            letter-spacing: 0.08em; 
            color: var(--nimbus-neutral-text-low);
            font-weight: 600;
        }}
        tr:hover {{ background: var(--nimbus-neutral-surface-highlight); }}
        
        /* Mini Tables (for matrix transitions) */
        .mini-table {{ margin-top: var(--spacing-2); }}
        .mini-table th, .mini-table td {{ 
            padding: var(--spacing-2); 
            font-size: 0.75rem; 
        }}
        .mini-table td:nth-child(2) {{ 
            text-align: center; 
            color: var(--nimbus-neutral-text-low); 
        }}
        .mini-table td:last-child {{ text-align: right; font-weight: 600; }}
        
        /* Matriz de Transição Visual */
        .matriz-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.75rem;
            margin-top: var(--spacing-3);
        }}
        .matriz-table th, .matriz-table td {{
            padding: var(--spacing-2);
            text-align: center;
            border: 1px solid var(--nimbus-neutral-interactive);
        }}
        .matriz-corner {{
            background: var(--nimbus-neutral-surface-highlight);
            font-weight: 600;
            font-size: 0.625rem;
            text-transform: uppercase;
        }}
        .matriz-header {{
            background: var(--nimbus-neutral-surface-highlight);
            font-weight: 600;
            font-size: 0.625rem;
            white-space: nowrap;
        }}
        .matriz-row-header {{
            background: var(--nimbus-neutral-surface-highlight);
            font-weight: 600;
            text-align: left !important;
            white-space: nowrap;
        }}
        .matriz-cell {{
            position: relative;
            min-width: 60px;
            padding: var(--spacing-2) !important;
        }}
        .matriz-count {{
            display: block;
            font-weight: 600;
            font-size: 0.8125rem;
        }}
        .matriz-pct {{
            display: block;
            font-size: 0.625rem;
            color: var(--nimbus-neutral-text-low);
        }}
        .matriz-upgrade {{
            background: rgba(34, 197, 94, 0.15);
        }}
        .matriz-upgrade .matriz-count {{ color: var(--success-text); }}
        .matriz-estavel {{
            background: rgba(156, 163, 175, 0.15);
        }}
        .matriz-estavel .matriz-count {{ color: var(--nimbus-neutral-text-high); font-weight: 700; }}
        .matriz-downgrade {{
            background: rgba(239, 68, 68, 0.15);
        }}
        .matriz-downgrade .matriz-count {{ color: var(--danger-text); }}
        .matriz-zero {{
            color: var(--nimbus-neutral-text-disabled);
        }}
        .matriz-total {{
            background: var(--nimbus-neutral-surface);
            font-weight: 600;
        }}
        .matriz-total-cell {{
            background: var(--nimbus-neutral-surface-highlight);
            font-weight: 600;
        }}
        .matriz-legenda {{
            display: flex;
            gap: var(--spacing-4);
            margin-top: var(--spacing-3);
            justify-content: center;
        }}
        .legenda-item {{
            display: flex;
            align-items: center;
            gap: var(--spacing-2);
            font-size: 0.75rem;
            color: var(--nimbus-neutral-text-low);
        }}
        .legenda-cor {{
            width: 16px;
            height: 16px;
            border-radius: var(--radius-sm);
        }}
        .legenda-cor.matriz-upgrade {{ background: rgba(34, 197, 94, 0.4); }}
        .legenda-cor.matriz-estavel {{ background: rgba(156, 163, 175, 0.4); }}
        .legenda-cor.matriz-downgrade {{ background: rgba(239, 68, 68, 0.4); }}
        
        /* Fluxo Líquido */
        .fluxo-lista {{
            display: flex;
            flex-direction: column;
            gap: var(--spacing-2);
        }}
        .fluxo-item {{
            display: flex;
            flex-direction: column;
            gap: var(--spacing-2);
            padding: var(--spacing-2) var(--spacing-3);
            border-radius: var(--radius-sm);
        }}
        .fluxo-expandable {{
            cursor: pointer;
            transition: background 0.2s;
        }}
        .fluxo-expandable:hover {{
            filter: brightness(0.95);
        }}
        .fluxo-main {{
            display: flex;
            align-items: center;
            gap: var(--spacing-3);
        }}
        .fluxo-positivo {{
            background: rgba(34, 197, 94, 0.1);
        }}
        .fluxo-negativo {{
            background: rgba(239, 68, 68, 0.1);
        }}
        .fluxo-status {{
            flex: 1;
            font-weight: 500;
        }}
        .fluxo-valor {{
            font-weight: 700;
            font-size: 0.9375rem;
        }}
        .fluxo-positivo .fluxo-valor {{ color: var(--success-text); }}
        .fluxo-negativo .fluxo-valor {{ color: var(--danger-text); }}
        .fluxo-pct {{
            font-size: 0.75rem;
            color: var(--nimbus-neutral-text-low);
        }}
        .fluxo-expand-icon {{
            font-size: 0.625rem;
            color: var(--nimbus-neutral-text-low);
            transition: transform 0.2s;
        }}
        .fluxo-item.expanded .fluxo-expand-icon {{
            transform: rotate(180deg);
        }}
        .fluxo-detalhe {{
            padding: var(--spacing-2) var(--spacing-3);
            background: rgba(0,0,0,0.1);
            border-radius: var(--radius-sm);
            font-size: 0.75rem;
        }}
        .fluxo-detalhe-row {{
            padding: 2px 0;
        }}
        
        /* Matriz com escala de cores */
        .matriz-cell.intensidade-alta {{
            font-weight: 700;
        }}
        
        /* Insight Boxes */
        .insight-box {{
            background: var(--nimbus-primary-surface);
            border-left: 4px solid var(--nimbus-primary-interactive);
            padding: var(--spacing-4) var(--spacing-5);
            border-radius: 0 var(--radius-md) var(--radius-md) 0;
            margin: var(--spacing-4) 0;
        }}
        .insight-box h4 {{ 
            color: var(--nimbus-primary-surface-highlight); 
            margin-bottom: var(--spacing-2); 
            font-size: 0.8125rem;
            font-weight: 600;
        }}
        .insight-box p {{ 
            font-size: 0.75rem; 
            color: var(--nimbus-neutral-text-low); 
            line-height: 1.6; 
        }}
        .insight-box.warning {{ 
            background: var(--warning-surface);
            border-left-color: var(--warning-interactive); 
        }}
        .insight-box.warning h4 {{ color: var(--warning-text); }}
        
        /* Two Columns Layout */
        .two-columns {{ display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-5); }}
        
        /* Risk Matrix */
        .risk-matrix {{ 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: var(--spacing-3); 
            margin: var(--spacing-4) 0; 
        }}
        .risk-card {{ 
            padding: var(--spacing-4); 
            border-radius: var(--radius-md); 
            text-align: center; 
        }}
        .risk-card h3 {{ 
            font-size: 1.5rem; 
            font-weight: 700; 
            margin-bottom: var(--spacing-2);
            letter-spacing: -0.02em;
        }}
        .risk-card p {{ font-size: 0.6875rem; }}
        
        /* Status Dot */
        .status-dot {{ 
            display: inline-block; 
            width: 10px; 
            height: 10px; 
            border-radius: 50%; 
            margin-right: var(--spacing-2); 
        }}
        
        /* Transition Cards */
        .upgrade-card {{ 
            background: var(--success-surface); 
            border: 1px solid var(--success-interactive); 
        }}
        .upgrade-card .card-value {{ color: var(--success-text); }}
        
        .stable-card {{ 
            background: var(--nimbus-neutral-surface-highlight); 
            border: 1px solid var(--nimbus-neutral-text-disabled); 
        }}
        .stable-card .card-value {{ color: var(--nimbus-neutral-text-low); }}
        
        .downgrade-card {{ 
            background: var(--danger-surface); 
            border: 1px solid var(--danger-interactive); 
        }}
        .downgrade-card .card-value {{ color: var(--danger-text); }}
        
        /* Utilities */
        .text-center {{ text-align: center; }}
        .text-muted {{ color: var(--nimbus-neutral-text-low); font-size: 0.75rem; margin-top: var(--spacing-3); }}
        code {{ 
            background: var(--nimbus-neutral-interactive); 
            padding: 2px 6px; 
            border-radius: var(--radius-sm); 
            font-size: 0.6875rem;
            font-family: 'Geist Mono', monospace;
        }}
        
        /* Comparison */
        .comparison {{ display: flex; gap: var(--spacing-6); margin-top: var(--spacing-3); }}
        .comparison-item {{ flex: 1; }}
        .comparison-label {{ 
            font-size: 0.625rem; 
            color: var(--nimbus-neutral-text-low); 
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: var(--spacing-1); 
        }}
        .comparison-value {{ font-size: 1.375rem; font-weight: 600; }}
        
        /* Trend Arrows */
        .trend-arrow {{ 
            display: inline-flex; 
            align-items: center; 
            font-size: 0.875rem; 
            margin-left: var(--spacing-2); 
            font-weight: 600; 
        }}
        .trend-arrow.up {{ color: var(--success-text); }}
        .trend-arrow.down {{ color: var(--danger-text); }}
        .trend-arrow svg {{ width: 16px; height: 16px; margin-right: 2px; }}
        .card-value-row {{ display: flex; align-items: center; flex-wrap: wrap; }}
        
        /* Insights Section */
        .insights-section {{ margin-top: var(--spacing-8); }}
        .insights-box {{
            background: var(--nimbus-primary-surface);
            border-radius: var(--radius-lg);
            padding: var(--spacing-6);
            border: 1px solid rgba(0, 89, 213, 0.3);
        }}
        .insights-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .insights-list li {{
            padding: var(--spacing-3) 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.875rem;
            line-height: 1.6;
            color: var(--nimbus-neutral-text-low);
        }}
        .insights-list li:last-child {{ border-bottom: none; }}
        .insights-list li strong {{ color: var(--nimbus-primary-surface-highlight); }}
        .insights-list li em {{ color: var(--warning-text); font-style: normal; }}
        
        /* Quartile Comparison */
        .quartile-comparison {{ 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: var(--spacing-3); 
            margin: var(--spacing-4) 0; 
        }}
        .quartile-card {{ 
            padding: var(--spacing-4); 
            border-radius: var(--radius-md); 
            text-align: center; 
        }}
        .quartile-card h4 {{ 
            font-size: 0.75rem; 
            font-weight: 600; 
            margin-bottom: var(--spacing-3); 
        }}
        .quartile-row {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: var(--spacing-2) 0; 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
        }}
        .quartile-row:last-child {{ border-bottom: none; }}
        .quartile-label {{ font-size: 0.625rem; color: var(--nimbus-neutral-text-low); }}
        .quartile-value {{ font-size: 0.875rem; font-weight: 600; }}
        
        /* Modal */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            padding: var(--spacing-4);
        }}
        .modal-overlay.active {{ display: flex; }}
        .modal {{
            background: var(--nimbus-neutral-surface);
            border-radius: var(--radius-lg);
            max-width: 900px;
            width: 100%;
            max-height: 85vh;
            overflow: hidden;
            border: 1px solid var(--nimbus-neutral-interactive);
            display: flex;
            flex-direction: column;
        }}
        .modal-header {{
            padding: var(--spacing-5);
            border-bottom: 1px solid var(--nimbus-neutral-interactive);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .modal-header h3 {{ font-size: 1.125rem; font-weight: 600; }}
        .modal-close {{
            background: none;
            border: none;
            color: var(--nimbus-neutral-text-low);
            font-size: 1.5rem;
            cursor: pointer;
            padding: var(--spacing-2);
            line-height: 1;
        }}
        .modal-close:hover {{ color: var(--nimbus-neutral-text-high); }}
        .modal-body {{
            padding: var(--spacing-5);
            overflow-y: auto;
            flex: 1;
        }}
        .modal-stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: var(--spacing-3);
            margin-bottom: var(--spacing-5);
        }}
        .modal-stat {{
            background: var(--nimbus-neutral-surface-highlight);
            padding: var(--spacing-4);
            border-radius: var(--radius-md);
            text-align: center;
        }}
        .modal-stat-label {{ font-size: 0.625rem; color: var(--nimbus-neutral-text-low); text-transform: uppercase; letter-spacing: 0.08em; }}
        .modal-stat-value {{ font-size: 1.25rem; font-weight: 600; margin-top: var(--spacing-1); }}
        .modal-table-container {{
            max-height: 350px;
            overflow-y: auto;
            border: 1px solid var(--nimbus-neutral-interactive);
            border-radius: var(--radius-md);
        }}
        .modal-table {{ margin: 0; }}
        .modal-table th {{ position: sticky; top: 0; background: var(--nimbus-neutral-surface); }}
        .modal-footer {{
            padding: var(--spacing-4) var(--spacing-5);
            border-top: 1px solid var(--nimbus-neutral-interactive);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        /* Buttons */
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: var(--spacing-2);
            padding: var(--spacing-2) var(--spacing-4);
            border-radius: var(--radius-md);
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
            font-family: inherit;
        }}
        .btn-primary {{
            background: var(--nimbus-primary-interactive);
            color: white;
        }}
        .btn-primary:hover {{ background: var(--nimbus-primary-interactive-hover); }}
        .btn-secondary {{
            background: var(--nimbus-neutral-interactive);
            color: var(--nimbus-neutral-text-high);
        }}
        .btn-secondary:hover {{ background: var(--nimbus-neutral-surface-highlight); }}
        .btn svg {{ width: 16px; height: 16px; }}
        
        /* Clickable Cards */
        .risk-card.clickable {{
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .risk-card.clickable:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        .cross-sell-row {{
            cursor: pointer;
            transition: background 0.2s;
        }}
        .cross-sell-row:hover {{
            background: var(--nimbus-neutral-surface-highlight) !important;
        }}
        .download-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: var(--radius-sm);
            background: var(--nimbus-primary-surface);
            color: var(--nimbus-primary-interactive);
            cursor: pointer;
            transition: all 0.2s;
        }}
        .download-icon:hover {{
            background: var(--nimbus-primary-interactive);
            color: white;
        }}
        
        /* Responsive */
        @media (max-width: 1000px) {{ 
            .two-columns, .grid-3, .grid-4, .grid-5, .risk-matrix, .quartile-comparison {{ 
                grid-template-columns: 1fr 1fr; 
            }} 
        }}
        @media (max-width: 600px) {{ 
            .two-columns, .grid-3, .grid-4, .grid-5, .risk-matrix, .quartile-comparison {{ 
                grid-template-columns: 1fr; 
            }}
            .content {{ padding: var(--spacing-4); }}
            .header {{ padding: var(--spacing-4); }}
            .tabs {{ padding: 0 var(--spacing-4); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dashboard Impacto - Lifecycle BR</h1>
        <p>Base: {dashboard_data['resumo']['data_base']} | {len(meses_disponiveis)} mês(es) carregado(s)</p>
    </div>
    
    <div class="tabs">
        <div class="tab active" onclick="showTab('resumo')">Resumo Executivo</div>
        <div class="tab" onclick="showTab('base')">Visão da Base</div>
        <div class="tab" onclick="showTab('icp')">Análise por ICP</div>
        <div class="tab" onclick="showTab('merchant')">Merchant Services <span class="badge soon">em atualização</span></div>
        <div class="tab" onclick="showTab('risco')">Risco de Churn</div>
        <div class="tab" onclick="showTab('cobertura')">Cobertura Lifecycle</div>
        <div class="tab" onclick="showTab('webinars')">Projeto: Webinars</div>
        <div class="tab" onclick="showTab('onboarding')">Projeto: Onboarding</div>
        <div class="tab disabled">Human in the Loop <span class="badge soon">em breve</span></div>
    </div>
    
    <div class="content">
        <!-- RESUMO -->
        <div id="resumo" class="tab-content active">
            <h2 class="section-title">Big Numbers</h2>
            <div class="grid grid-5">
                <div class="card"><div class="card-title">Lojas Ativas</div><div class="card-value gradient">{dashboard_data['resumo']['total_lojas_ativas']:,}</div><div class="card-subtitle">pagantes</div></div>
                <div class="card"><div class="card-title">Lojas Sellers</div><div class="card-value">{dashboard_data['resumo']['total_lojas_sellers']:,}</div><div class="card-subtitle">{dashboard_data['resumo']['pct_sellers']}%</div></div>
                <div class="card"><div class="card-title">GMV Total</div><div class="card-value">R$ {dashboard_data['resumo']['gmv_total']/1000000:.1f}M</div></div>
                <div class="card"><div class="card-title">Cobertura</div><div class="card-value positive">{dashboard_data['resumo']['pct_cobertura']}%</div><div class="card-subtitle">{dashboard_data['resumo']['n_cobertas']:,} lojas</div></div>
                <div class="card"><div class="card-title">Risco Médio</div><div class="card-value negative">{dashboard_data['resumo']['churn_prob_media']}%</div></div>
            </div>
            
            <h2 class="section-title">Impacto em New Sellers por Projeto</h2>
            <div class="grid grid-5">
                <div class="card"><div class="card-title">Total New Sellers</div><div class="card-value gradient">{dashboard_data['new_sellers']['soma_total']:,}</div><div class="card-subtitle">último mês</div></div>
                {''.join([f'<div class="card"><div class="card-title">{p["projeto"]}</div><div class="card-value {"positive" if p["projeto"]=="Onboarding V2" else ""}">{p["pct"]}%</div><div class="card-subtitle">{p["n"]:,} lojas</div></div>' for p in dashboard_data['new_sellers']['impacto_por_projeto']])}
            </div>
            <div class="card" style="margin-top:16px;">
                <div class="card-title">Detalhamento por Grupo</div>
                <table>
                    <thead><tr><th>Grupo</th><th>New Sellers</th><th>% do Total</th><th>Descrição</th></tr></thead>
                    <tbody>
                        <tr><td><strong>Com Onboarding</strong></td><td>{dashboard_data['new_sellers']['impacto_por_projeto'][0]['n']:,}</td><td class="positive">{dashboard_data['new_sellers']['impacto_por_projeto'][0]['pct']}%</td><td>Participantes do Onboarding V2</td></tr>
                        <tr><td><strong>Sem Onboarding</strong></td><td>{dashboard_data['new_sellers']['impacto_por_projeto'][1]['n']:,}</td><td>{dashboard_data['new_sellers']['impacto_por_projeto'][1]['pct']}%</td><td>Criados a partir de Out/2025, sem onboarding</td></tr>
                        <tr><td><strong>Base Antiga</strong></td><td>{dashboard_data['new_sellers']['impacto_por_projeto'][2]['n']:,}</td><td>{dashboard_data['new_sellers']['impacto_por_projeto'][2]['pct']}%</td><td>Criados antes de Out/2025</td></tr>
                        <tr><td><strong>Webinars</strong></td><td>{dashboard_data['new_sellers']['impacto_por_projeto'][3]['n']:,}</td><td>{dashboard_data['new_sellers']['impacto_por_projeto'][3]['pct']}%</td><td>Participaram de webinars</td></tr>
                    </tbody>
                </table>
            </div>
            
            
            <h2 class="section-title">Matriz de Transição</h2>
            {matriz_html}
            
            <h2 class="section-title">Matriz de Risco</h2>
            <div class="risk-matrix">
                {''.join([f'<div class="risk-card" style="background:{q["color"]}20;border:2px solid {q["color"]};"><h3 style="color:{q["color"]};">{q["count"]:,}</h3><p style="color:{q["color"]};font-weight:600;">{q["name"]}</p><p>{q["pct"]}%</p></div>' for q in dashboard_data['risk_quartiles']])}
            </div>
            
            {insights_resumo_html}
        </div>
        
        <!-- BASE -->
        <div id="base" class="tab-content">
            <h2 class="section-title">Distribuição por Status</h2>
            <div class="two-columns">
                <div class="card"><div class="card-title">Pirâmide de Status</div><div class="chart-container"><canvas id="chartStatusBase"></canvas></div></div>
                <div class="card"><div class="card-title">Performance por Status</div><table><thead><tr><th>Status</th><th>Lojas</th><th>GMV Médio</th><th>Risco de Churn</th></tr></thead><tbody>{''.join([f'<tr><td><span class="status-dot" style="background:{["#888888","#c80003","#c87b00","#f7c77a","#7af7c7","#00c87b","#00935b","#0059d5"][STATUS_ORDER.index(s["status"]) if s["status"] in STATUS_ORDER else 0]};"></span><strong>{s["label"]}</strong></td><td>{s["count"]:,}</td><td>R$ {s["gmv_medio"]:,.0f}</td><td class="{"positive" if s["churn_prob"]<25 else "neutral" if s["churn_prob"]<45 else "negative"}">{s["churn_prob"]}%</td></tr>' for s in dashboard_data['status_base']['distribuicao']])}</tbody></table></div>
            </div>
            
            <h2 class="section-title">Matriz de Transição</h2>
            {matriz_html}
            
            {insights_base_html}
        </div>
        
        <!-- ICP ANALYSIS -->
        <div id="icp" class="tab-content">
            <h2 class="section-title">Análise por ICP (Ideal Customer Profile)</h2>
            
            <div class="insight-box info">
                <h4>📊 Sobre a análise de ICP</h4>
                <p>Comparativo de performance entre os perfis de cliente ideal (ICP 1 a 4), incluindo taxa de conversão para seller, risco de churn e participação em projetos de lifecycle.</p>
            </div>
            
            <div class="risk-matrix" style="grid-template-columns: repeat(5, 1fr);">
                {icp_cards_html}
            </div>
            
            <h2 class="section-title" style="margin-top:32px;">Comparativo de Performance por ICP</h2>
            
            <div class="card" style="overflow-x:auto;">
                <table style="width:100%;">
                    <thead>
                        <tr>
                            <th>ICP</th>
                            <th>Lojas</th>
                            <th>% Sellers</th>
                            <th>GMV Médio</th>
                            <th>Risco Churn</th>
                            <th>% Onboarding</th>
                            <th>% Webinars</th>
                        </tr>
                    </thead>
                    <tbody>
                        {icp_table_rows_html}
                    </tbody>
                </table>
            </div>
            
            {icp_transicao_html}
            
            {icp_aging_html}
            
            <h2 class="section-title" style="margin-top:32px;">Distribuição de Status por ICP</h2>
            <div class="grid-2">
                {icp_status_cards_html}
            </div>
            
            <div class="insights-section">
                <h3>💡 Insights de ICP</h3>
                <ul>
                    {icp_insights_html}
                </ul>
            </div>
        </div>
        
        <!-- MERCHANT SERVICES -->
        <div id="merchant" class="tab-content">
            <h2 class="section-title">Visão Geral de Merchant Services</h2>
            <div class="grid grid-4">
                <div class="card"><div class="card-title">Média Produtos/Loja</div><div class="card-value gradient">{dashboard_data['merchant_services']['media']}</div></div>
                {''.join([f'<div class="card"><div class="card-title">{p["produto"]}</div><div class="card-value">{p["pct"]}%</div><div class="card-subtitle">{p["lojas"]:,} lojas</div></div>' for p in dashboard_data['merchant_services']['por_produto'][:3]])}
            </div>
            
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">Distribuição por Quantidade de Produtos</div>
                    <div class="chart-container"><canvas id="chartMSDistribuicao"></canvas></div>
                </div>
                <div class="card">
                    <div class="card-title">Adoção por Produto</div>
                    <div class="chart-container"><canvas id="chartMSProdutos"></canvas></div>
                </div>
            </div>
            
            <h2 class="section-title">Oportunidades de Cross-Sell</h2>
            <p class="text-muted" style="margin-top:-8px;margin-bottom:16px;">Clique no botão de download para baixar a lista de lojas potenciais</p>
            <div class="card">
                <table>
                    <thead><tr><th>Produto</th><th>Já tem</th><th>Potencial</th><th>GMV Potencial</th><th>% Base</th><th>Ação</th></tr></thead>
                    <tbody>
                        {''.join([f'<tr class="cross-sell-row"><td><strong>{c["produto"]}</strong></td><td>{c["ja_tem"]:,}</td><td class="positive">{c["potencial"]:,}</td><td>R$ {c["gmv_potencial"]/1000000:.1f}M</td><td>{c["pct_potencial"]}%</td><td><span class="download-icon" onclick="downloadCrossSell(&quot;{c["codigo"]}&quot;, &quot;{c["produto"]}&quot;)" title="Baixar lista"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></span></td></tr>' for c in dashboard_data['merchant_services']['cross_sell']])}
                    </tbody>
                </table>
            </div>
            
            <h2 class="section-title">Top Combinações de Produtos</h2>
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">Combinações Mais Comuns</div>
                    <table>
                        <thead><tr><th>Combinação</th><th>Lojas</th><th>%</th></tr></thead>
                        <tbody>
                            {''.join([f'<tr><td>{c["combo"]}</td><td>{c["count"]:,}</td><td>{c["pct"]}%</td></tr>' for c in dashboard_data['merchant_services']['combinacoes'][:10]])}
                        </tbody>
                    </table>
                </div>
                <div class="card">
                    <div class="card-title">Produtos Relacionados</div>
                    <p style="font-size:11px;color:#64748b;margin-bottom:12px;">Quem tem o produto X, também tem...</p>
                    <table>
                        <thead><tr><th>Produto</th><th>Clientes</th><th>Também tem (top 3)</th></tr></thead>
                        <tbody>
                            {generate_afinidade_rows()}
                        </tbody>
                    </table>
                </div>
            </div>
            
            {insights_ms_html}
        </div>
        
        <!-- RISCO -->
        <div id="risco" class="tab-content">
            <h2 class="section-title">Matriz de Quartis de Risco</h2>
            <p class="text-muted" style="margin-top:-8px;margin-bottom:16px;">Clique em um quartil para ver detalhes e baixar a lista de lojas</p>
            <div class="risk-matrix">
                {''.join([f'<div class="risk-card clickable" onclick="showRiskModal(&quot;{q["name"]}&quot;)" style="background:{q["color"]}20;border:2px solid {q["color"]};"><h3 style="color:{q["color"]};">{q["count"]:,}</h3><p style="color:{q["color"]};font-weight:600;">{q["name"]}</p><p>{q["pct"]}% | GMV: R$ {q["gmv_total"]/1000000:.1f}M</p></div>' for q in dashboard_data['risk_quartiles']])}
            </div>
            
            <div class="two-columns">
                <div class="card"><div class="card-title">Risco por Status</div><div class="chart-container"><canvas id="chartChurnStatus"></canvas></div></div>
                <div class="card"><div class="card-title">Detalhamento</div><table><thead><tr><th>Status</th><th>Lojas</th><th>Prob. Média</th></tr></thead><tbody>{''.join([f'<tr><td><strong>{s["label"]}</strong></td><td>{s["lojas"]:,}</td><td class="{"positive" if s["prob_media"]<25 else "neutral" if s["prob_media"]<45 else "negative"}">{s["prob_media"]}%</td></tr>' for s in dashboard_data['churn']['por_status']])}</tbody></table></div>
            </div>
            
            {'<div class="insight-box warning"><h4>📈 Evolução do Risco</h4><p>Carregue bases de múltiplos meses para ver a evolução</p></div>' if len(risco_evolucao) <= 1 else f'<h2 class="section-title">Evolução do Risco</h2><div class="card"><div class="chart-container"><canvas id="chartRiscoEvolucao"></canvas></div></div>'}
            
            {insights_risco_html}
        </div>
        
        <!-- COBERTURA -->
        <div id="cobertura" class="tab-content">
            <h2 class="section-title">Cobertura Lifecycle</h2>
            <div class="grid">
                <div class="card"><div class="card-title">Lojas Impactadas</div><div class="card-value gradient">{dashboard_data['resumo']['n_cobertas']:,}</div><div class="card-subtitle">{dashboard_data['resumo']['pct_cobertura']}%</div></div>
                <div class="card"><div class="card-title">Não Impactadas</div><div class="card-value">{dashboard_data['resumo']['total_lojas_ativas'] - dashboard_data['resumo']['n_cobertas']:,}</div></div>
            </div>
            <div class="card">
                <table><thead><tr><th>Projeto</th><th>Status</th><th>Lojas</th><th>%</th></tr></thead><tbody>{''.join([f'<tr><td><strong>{p["projeto"]}</strong></td><td><span class="badge {"badge-positive" if p["status"]=="ativo" else ""}">{p["status"]}</span></td><td>{p["lojas"]:,}</td><td>{p["pct"]}%</td></tr>' for p in dashboard_data['cobertura_projetos']])}</tbody></table>
            </div>
            
            {insights_cobertura_html}
        </div>
        
        <!-- WEBINARS -->
        <div id="webinars" class="tab-content">
            <h2 class="section-title">Funil de Webinars</h2>
            <div class="grid grid-5">
                <div class="card"><div class="card-title">Total Registros</div><div class="card-value gradient">{dashboard_data['webinars']['funil']['total_geral']:,}</div><div class="card-subtitle">inscrições</div></div>
                <div class="card"><div class="card-title">Ao Vivo</div><div class="card-value positive">{dashboard_data['webinars']['funil']['total_live']:,}</div><div class="card-subtitle">{dashboard_data['webinars']['funil'].get('pct_live', 0)}% do total</div></div>
                <div class="card"><div class="card-title">On Demand</div><div class="card-value">{dashboard_data['webinars']['funil']['total_ondemand']:,}</div><div class="card-subtitle">{dashboard_data['webinars']['funil'].get('pct_ondemand', 0)}% do total</div></div>
                <div class="card"><div class="card-title">Total Participaram</div><div class="card-value positive">{dashboard_data['webinars']['funil']['total_participaram']:,}</div><div class="card-subtitle">{dashboard_data['webinars']['funil'].get('pct_participaram', 0)}% do total</div></div>
                <div class="card"><div class="card-title">Lojas na Base</div><div class="card-value">{dashboard_data['webinars']['total_participantes']:,}</div><div class="card-subtitle">{dashboard_data['webinars']['pct_base']}% da base ativa</div></div>
            </div>
            
            <h2 class="section-title">Participação Mensal</h2>
            <div class="card">
                <div class="card-title">% de Participação por Mês (sobre total de registros)</div>
                <div class="chart-container" style="height:320px;"><canvas id="chartFunilMensal"></canvas></div>
            </div>
            
            <h2 class="section-title">Impacto na Base</h2>
            <div class="grid grid-5">
                <div class="card"><div class="card-title">Lojas com Cobertura</div><div class="card-value gradient">{dashboard_data['webinars']['total_participantes']:,}</div><div class="card-subtitle">{dashboard_data['webinars']['pct_base']}% da base</div></div>
                <div class="card"><div class="card-title">GMV</div><div class="card-value-row"><span class="card-value positive">+{dashboard_data['webinars']['performance']['gmv_diff_pct']}%</span>{trend_gmv}</div><div class="card-subtitle">vs sem webinar</div></div>
                <div class="card"><div class="card-title">Churn</div><div class="card-value-row"><span class="card-value positive">{dashboard_data['webinars']['churn']['diff_pp']}pp</span>{trend_churn}</div><div class="card-subtitle">vs sem webinar</div></div>
                <div class="card"><div class="card-title">GMV Pareado</div><div class="card-value positive">+{dashboard_data['webinars']['analise_pareada']['gmv_diff_pct']}%</div><div class="card-subtitle">mesmo perfil</div></div>
                <div class="card"><div class="card-title">Churn Pareado</div><div class="card-value positive">{dashboard_data['webinars']['churn_pareado']['diff_pp']}pp</div><div class="card-subtitle">mesmo perfil</div></div>
            </div>
            
            <h2 class="section-title">Risco Preditivo: Com vs Sem Webinar</h2>
            <div class="insight-box">
                <h4>Distribuição por Quartil de Risco</h4>
                <p>Comparação da distribuição de lojas em cada faixa de risco entre lojas <strong>com webinar</strong> e <strong>sem webinar</strong>. Diferenças negativas nos quartis de maior risco indicam que webinars ajudam a reduzir o risco.</p>
            </div>
            <div class="quartile-comparison">
                {''.join([f'<div class="quartile-card" style="background:{q["color"]}15;border:2px solid {q["color"]};"><h4 style="color:{q["color"]};">{q["name"]}</h4><div class="quartile-row"><span class="quartile-label">Com Webinar</span><span class="quartile-value" style="color:{q["color"]};">{q["pct_com"]}%</span></div><div class="quartile-row"><span class="quartile-label">Sem Webinar</span><span class="quartile-value">{q["pct_sem"]}%</span></div><div class="quartile-row"><span class="quartile-label">Diferença</span><span class="quartile-value {"positive" if q["diff_pp"]<0 else "negative" if q["diff_pp"]>0 else ""}">{("+" if q["diff_pp"]>0 else "")}{q["diff_pp"]}pp</span></div></div>' for q in dashboard_data['webinars']['risk_quartiles_comparison']])}
            </div>
            
            <h2 class="section-title">Transição de Status: Impactados por Webinar</h2>
            {webinar_transicao_html}
            
            <h2 class="section-title">Impacto em New Sellers</h2>
            <div class="card">
                <table><thead><tr><th>Mês</th><th>New Sellers</th><th>Com Webinar</th><th>%</th></tr></thead><tbody>{''.join([f'<tr><td>{m["mes"]}</td><td>{m["total_new_sellers"]:,}</td><td>{m["por_grupo"]["webinar"]["n"]}</td><td class="{"positive" if m["por_grupo"]["webinar"]["pct"]>5 else "neutral" if m["por_grupo"]["webinar"]["pct"]>2 else ""}">{m["por_grupo"]["webinar"]["pct"]}%</td></tr>' for m in dashboard_data['webinars']['new_sellers_impacto'][:6]])}</tbody></table>
            </div>
            
            <h2 class="section-title">Impacto em Adoção de Merchant Services</h2>
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">Comparativo Com vs Sem Webinar</div>
                    <table>
                        <thead><tr><th>Produto</th><th>Com Webinar</th><th>Sem Webinar</th><th>Diferença</th></tr></thead>
                        <tbody>{ms_comparison_rows}</tbody>
                    </table>
                    <div style="margin-top:16px;">
                        <div class="card-title">Média de Produtos</div>
                        <div class="comparison">
                            <div class="comparison-item"><div class="comparison-label">Com Webinar</div><div class="comparison-value positive">{dashboard_data['webinars']['merchant_services']['com_webinar']['media']}</div></div>
                            <div class="comparison-item"><div class="comparison-label">Sem Webinar</div><div class="comparison-value">{dashboard_data['webinars']['merchant_services']['sem_webinar']['media']}</div></div>
                            <div class="comparison-item"><div class="comparison-label">Diferença</div><div class="comparison-value positive">+{dashboard_data['webinars']['merchant_services']['diff_media']}</div></div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">Adoção por Produto</div>
                    <div class="chart-container"><canvas id="chartWebinarMS"></canvas></div>
                </div>
            </div>
            
            <h2 class="section-title">Perfil dos Participantes</h2>
            <div class="two-columns">
                <div class="card"><div class="card-title">Por Status</div><div class="chart-container"><canvas id="chartWebinarStatus"></canvas></div></div>
                <div class="card"><div class="card-title">Representatividade</div><table><thead><tr><th>Status</th><th>% Webinar</th><th>% Base</th><th>Índice</th></tr></thead><tbody>{''.join([f'<tr><td><strong>{s["label"]}</strong></td><td>{s["pct_webinar"]}%</td><td>{s["pct_base"]}%</td><td class="{"positive" if s["indice"]>110 else "negative" if s["indice"]<90 else ""}">{int(s["indice"])}</td></tr>' for s in dashboard_data['webinars']['perfil_status']])}</tbody></table></div>
            </div>
            
            <h2 class="section-title">Análise Pareada por Grupo</h2>
            <div class="insight-box">
                <h4>O que é a análise pareada?</h4>
                <p>Comparamos lojas COM e SEM webinar que têm o <strong>mesmo perfil</strong> (status de seller + idade da loja). Isso elimina o viés de seleção e mostra o impacto real dos webinars.</p>
            </div>
            <div class="card">
                <div class="card-title">Comparativo por Grupo (Status + Idade)</div>
                <table>
                    <thead>
                        <tr><th>Status</th><th>Idade</th><th>Com Web</th><th>Sem Web</th><th>GMV Com</th><th>GMV Sem</th><th>Δ GMV</th><th>Churn Com</th><th>Churn Sem</th><th>Δ Churn</th></tr>
                    </thead>
                    <tbody>
                        {''.join([f'<tr><td><strong>{g["status"]}</strong></td><td>{g["idade"]}</td><td>{g["n_com"]:,}</td><td>{g["n_sem"]:,}</td><td>R$ {g["gmv_com"]:,.0f}</td><td>R$ {g["gmv_sem"]:,.0f}</td><td class="{"positive" if g["gmv_diff_pct"]>0 else "negative"}">{("+" if g["gmv_diff_pct"]>0 else "")}{g["gmv_diff_pct"]}%</td><td>{g["churn_com"]}%</td><td>{g["churn_sem"]}%</td><td class="{"positive" if g["churn_diff_pp"]<0 else "negative"}">{("+" if g["churn_diff_pp"]>0 else "")}{g["churn_diff_pp"]}pp</td></tr>' for g in dashboard_data['webinars']['analise_pareada'].get('grupos', [])[:15]])}
                    </tbody>
                </table>
                <p class="text-muted" style="margin-top:12px;">Total de {dashboard_data['webinars']['analise_pareada']['total_grupos']} grupos analisados (mínimo 5 lojas em cada lado)</p>
            </div>
            
            <h2 class="section-title">Top Webinars</h2>
            <div class="card">
                <table><thead><tr><th>#</th><th>Webinar</th><th>Participantes</th></tr></thead><tbody>{''.join([f'<tr><td>{i+1}</td><td>{w["nome"]}</td><td>{w["participantes"]:,}</td></tr>' for i, w in enumerate(dashboard_data['webinars']['top_webinars'][:10])])}</tbody></table>
            </div>
            
            {insights_webinars_html}
        </div>
        
        <!-- ONBOARDING -->
        <div id="onboarding" class="tab-content">
            <h2 class="section-title">Visão Geral do Onboarding V2</h2>
            <div class="insight-box warning">
                <h4>⚠️ Nota sobre Dados</h4>
                <p>A base geral disponível é de <strong>{dashboard_data['resumo']['data_base']}</strong>. Como o Onboarding V2 é um experimento recente (2026), as lojas ainda não possuem histórico de GMV e Status nesta base. Os dados de conversão (tempo até virar New Seller) vêm da base de New Sellers que é mais atual.</p>
            </div>
            <div class="grid grid-4">
                <div class="card"><div class="card-title">Grupo Teste</div><div class="card-value gradient">{dashboard_data['onboarding']['grupo_teste']['total']:,}</div><div class="card-subtitle">lojas no experimento</div></div>
                <div class="card"><div class="card-title">Na Base Geral</div><div class="card-value">{dashboard_data['onboarding']['grupo_teste']['na_base']:,}</div><div class="card-subtitle">{dashboard_data['onboarding']['grupo_teste']['pct_na_base']}% encontradas</div></div>
                <div class="card"><div class="card-title">Potential Sellers</div><div class="card-value positive">{dashboard_data['onboarding']['potential_sellers']['total']:,}</div><div class="card-subtitle">alta qualificação</div></div>
                <div class="card"><div class="card-title">Taxa de Conversão</div><div class="card-value positive">{generate_conversion_rate_onboarding()}</div><div class="card-subtitle">viraram seller</div></div>
            </div>
            
            <h2 class="section-title">Funil de Onboarding Steps</h2>
            <div class="insight-box">
                <h4>Etapas completadas no onboarding</h4>
                <p>Cada loja pode completar múltiplas etapas: Layout, Products, Shipping, Payment.</p>
            </div>
            <div class="grid grid-4">
                {''.join([f'<div class="card"><div class="card-title">{s["step"]}</div><div class="card-value">{s["count"]:,}</div><div class="card-subtitle">{s["pct"]}% das lojas</div></div>' for s in dashboard_data['onboarding']['funil_steps']])}
            </div>
            
            <h2 class="section-title">Combinações de Steps mais Comuns</h2>
            <div class="card">
                <table>
                    <thead><tr><th>Combinação</th><th>Lojas</th><th>%</th></tr></thead>
                    <tbody>
                        {''.join([f'<tr><td><strong>{c["combo"]}</strong></td><td>{c["count"]:,}</td><td>{c["pct"]}%</td></tr>' for c in dashboard_data['onboarding'].get('steps_combinacoes', [])[:10]])}
                    </tbody>
                </table>
            </div>
            
            {generate_onboarding_status_section()}
            
            {generate_onboarding_uplift_section()}
            
            {generate_onboarding_transicao_section()}
            
            {generate_onboarding_insights()}
        </div>
    </div>
    
    <!-- Modal de Detalhes -->
    <div id="riskModal" class="modal-overlay" onclick="closeModalOnOverlay(event)">
        <div class="modal">
            <div class="modal-header">
                <h3 id="modalTitle">Detalhes do Quartil</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="modal-stats" id="modalStats"></div>
                <h4 style="margin-bottom:12px;font-size:0.875rem;">Distribuição por Status</h4>
                <div id="modalStatusDist" style="margin-bottom:20px;"></div>
                <h4 style="margin-bottom:12px;font-size:0.875rem;">Lista de Lojas (Top 500 por GMV)</h4>
                <div class="modal-table-container">
                    <table class="modal-table" id="modalTable">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nome</th>
                                <th>Status</th>
                                <th>GMV</th>
                                <th>Pedidos</th>
                                <th>Prob. Churn</th>
                                <th>Email</th>
                            </tr>
                        </thead>
                        <tbody id="modalTableBody"></tbody>
                    </table>
                </div>
            </div>
            <div class="modal-footer">
                <span id="modalCount" class="text-muted"></span>
                <button class="btn btn-primary" id="downloadBtn" onclick="downloadCurrentList()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Baixar Lista CSV
                </button>
            </div>
        </div>
    </div>
    
    <script>
        const data = {json.dumps(dashboard_data, ensure_ascii=False)};
        
        /* Nimbus Color Palette for Status */
        const statusColors = {{
            'not informed': '#888888',   /* Neutral - cinza (Não Classificado) */
            'no-seller': '#c80003',      /* Danger - vermelho */
            'struggling-seller': '#c87b00', /* Warning - laranja */
            'tiny-seller': '#f7c77a',    /* Warning light */
            'small-seller': '#7af7c7',   /* Success light */
            'medium-seller': '#00c87b',  /* Success */
            'large-seller': '#00935b',   /* Success dark */
            'top-seller': '#0059d5'      /* Primary - azul Nimbus */
        }};
        
        /* Nimbus Chart Colors */
        const nimbusColors = {{
            primary: '#0059d5',
            primaryLight: '#96c1fc',
            success: '#00c87b',
            successLight: '#7af7c7',
            warning: '#c87b00',
            warningLight: '#f7c77a',
            danger: '#c80003',
            dangerLight: '#f77a7c',
            neutral: '#888888',
            neutralLight: '#b0b0b0'
        }};
        
        function showTab(id) {{
            document.querySelectorAll('.tab-content').forEach(e => e.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(e => e.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.target.classList.add('active');
            setTimeout(initCharts, 50);
        }}
        
        /* Toggle Fluxo Detalhe */
        function toggleFluxoDetalhe(id) {{
            const el = document.getElementById(id);
            const parent = el.closest('.fluxo-item');
            if (el.style.display === 'none') {{
                el.style.display = 'block';
                parent.classList.add('expanded');
            }} else {{
                el.style.display = 'none';
                parent.classList.remove('expanded');
            }}
        }}
        
        /* Chart.js Global Config - Nimbus Theme */
        Chart.defaults.color = '#888888';
        Chart.defaults.borderColor = '#2a2a2a';
        Chart.defaults.font.family = "'Geist', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
        
        /* ========================================
           MODAL E DOWNLOAD FUNCTIONS
           ======================================== */
        
        let currentDownloadData = null;
        let currentDownloadName = '';
        
        function showRiskModal(quartilName) {{
            const quartil = data.risk_quartiles.find(q => q.name === quartilName);
            const lojas = data.risk_quartiles_lojas[quartilName] || [];
            
            if (!quartil) return;
            
            // Título
            document.getElementById('modalTitle').innerHTML = `<span style="color:${{quartil.color}}">●</span> ${{quartilName}} - ${{quartil.prob_range}}`;
            
            // Stats
            const stats = quartil.stats || {{}};
            document.getElementById('modalStats').innerHTML = `
                <div class="modal-stat">
                    <div class="modal-stat-label">Total Lojas</div>
                    <div class="modal-stat-value">${{quartil.count.toLocaleString()}}</div>
                </div>
                <div class="modal-stat">
                    <div class="modal-stat-label">GMV Total</div>
                    <div class="modal-stat-value">R$ ${{(quartil.gmv_total/1000000).toFixed(1)}}M</div>
                </div>
                <div class="modal-stat">
                    <div class="modal-stat-label">GMV Médio</div>
                    <div class="modal-stat-value">R$ ${{stats.gmv_medio?.toLocaleString() || '0'}}</div>
                </div>
                <div class="modal-stat">
                    <div class="modal-stat-label">Prob. Média</div>
                    <div class="modal-stat-value">${{stats.prob_media || 0}}%</div>
                </div>
            `;
            
            // Distribuição por status
            const statusDist = quartil.status_distribution || {{}};
            let statusHtml = '<div style="display:flex;gap:8px;flex-wrap:wrap;">';
            for (const [status, count] of Object.entries(statusDist)) {{
                statusHtml += `<span style="background:var(--nimbus-neutral-surface-highlight);padding:4px 12px;border-radius:100px;font-size:0.75rem;">${{status}}: <strong>${{count.toLocaleString()}}</strong></span>`;
            }}
            statusHtml += '</div>';
            document.getElementById('modalStatusDist').innerHTML = statusHtml;
            
            // Tabela de lojas
            let tableHtml = '';
            lojas.forEach(loja => {{
                tableHtml += `<tr>
                    <td>${{loja.store_id}}</td>
                    <td>${{loja.nome || '-'}}</td>
                    <td>${{loja.status || '-'}}</td>
                    <td>R$ ${{loja.gmv?.toLocaleString() || '0'}}</td>
                    <td>${{loja.pedidos || 0}}</td>
                    <td class="${{loja.prob_churn > 50 ? 'negative' : loja.prob_churn > 25 ? 'neutral' : 'positive'}}">${{loja.prob_churn || 0}}%</td>
                    <td style="font-size:0.75rem;">${{loja.email || '-'}}</td>
                </tr>`;
            }});
            document.getElementById('modalTableBody').innerHTML = tableHtml;
            
            // Footer
            document.getElementById('modalCount').textContent = `Mostrando ${{lojas.length}} de ${{quartil.count.toLocaleString()}} lojas`;
            
            // Salvar dados para download
            currentDownloadData = lojas;
            currentDownloadName = `lojas_${{quartilName.toLowerCase().replace(/ /g, '_')}}_${{new Date().toISOString().split('T')[0]}}`;
            
            // Mostrar modal
            document.getElementById('riskModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }}
        
        function closeModal() {{
            document.getElementById('riskModal').classList.remove('active');
            document.body.style.overflow = '';
        }}
        
        function closeModalOnOverlay(event) {{
            if (event.target.classList.contains('modal-overlay')) {{
                closeModal();
            }}
        }}
        
        function downloadCurrentList() {{
            if (!currentDownloadData || currentDownloadData.length === 0) {{
                alert('Não há dados para download');
                return;
            }}
            downloadCSV(currentDownloadData, currentDownloadName);
        }}
        
        function downloadCrossSell(codigo, produto) {{
            const lojas = data.merchant_services.cross_sell_lojas[codigo] || [];
            if (lojas.length === 0) {{
                alert('Não há dados para download');
                return;
            }}
            const filename = `cross_sell_${{codigo}}_${{new Date().toISOString().split('T')[0]}}`;
            downloadCSV(lojas, filename);
        }}
        
        function downloadOnboardingList() {{
            const lojas = data.onboarding.lista_lojas || [];
            if (lojas.length === 0) {{
                alert('Não há dados para download');
                return;
            }}
            const filename = `onboarding_grupo_teste_${{new Date().toISOString().split('T')[0]}}`;
            downloadCSV(lojas, filename);
        }}
        
        function downloadCSV(dataArray, filename) {{
            if (!dataArray || dataArray.length === 0) return;
            
            const NL = String.fromCharCode(10);
            const headers = Object.keys(dataArray[0]);
            
            let csv = headers.join(';') + NL;
            dataArray.forEach(row => {{
                const values = headers.map(h => {{
                    let val = row[h] ?? '';
                    if (typeof val === 'string' && (val.includes(';') || val.includes('"') || val.includes(NL))) {{
                        val = '"' + val.replace(/"/g, '""') + '"';
                    }}
                    return val;
                }});
                csv += values.join(';') + NL;
            }});
            
            const BOM = String.fromCharCode(0xFEFF);
            const blob = new Blob([BOM + csv], {{ type: 'text/csv;charset=utf-8;' }});
            
            // Download
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename + '.csv';
            link.click();
            URL.revokeObjectURL(link.href);
        }}
        
        // Fechar modal com ESC
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') closeModal();
        }});
        
        function initCharts() {{
            // Status Base
            const ctxStatus = document.getElementById('chartStatusBase');
            if (ctxStatus && !ctxStatus.chart) {{
                ctxStatus.chart = new Chart(ctxStatus, {{
                    type: 'bar',
                    data: {{ labels: data.status_base.distribuicao.map(d => d.label), datasets: [{{ data: data.status_base.distribuicao.map(d => d.count), backgroundColor: data.status_base.distribuicao.map(d => statusColors[d.status]), borderRadius: 4 }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
                }});
            }}
            
            // Churn Status
            const ctxChurn = document.getElementById('chartChurnStatus');
            if (ctxChurn && !ctxChurn.chart) {{
                ctxChurn.chart = new Chart(ctxChurn, {{
                    type: 'line',
                    data: {{ labels: data.churn.por_status.map(d => d.label), datasets: [{{ data: data.churn.por_status.map(d => d.prob_media), borderColor: nimbusColors.danger, backgroundColor: 'rgba(200,0,3,0.1)', fill: true, tension: 0.4 }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ max: 100 }} }} }}
                }});
            }}
            
            // Webinar Status
            const ctxWebinar = document.getElementById('chartWebinarStatus');
            if (ctxWebinar && !ctxWebinar.chart) {{
                ctxWebinar.chart = new Chart(ctxWebinar, {{
                    type: 'doughnut',
                    data: {{ labels: data.webinars.perfil_status.map(d => d.label), datasets: [{{ data: data.webinars.perfil_status.map(d => d.count), backgroundColor: data.webinars.perfil_status.map(d => statusColors[d.status]), borderWidth: 0 }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right' }} }} }}
                }});
            }}
            
            // MS Distribuição
            const ctxMSDist = document.getElementById('chartMSDistribuicao');
            if (ctxMSDist && !ctxMSDist.chart) {{
                ctxMSDist.chart = new Chart(ctxMSDist, {{
                    type: 'bar',
                    data: {{ labels: data.merchant_services.distribuicao.map(d => d.qtd + ' produto(s)'), datasets: [{{ data: data.merchant_services.distribuicao.map(d => d.count), backgroundColor: [nimbusColors.neutral, nimbusColors.primary, nimbusColors.primaryLight, nimbusColors.success, nimbusColors.successLight], borderRadius: 4 }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
                }});
            }}
            
            // MS Produtos
            const ctxMSProd = document.getElementById('chartMSProdutos');
            if (ctxMSProd && !ctxMSProd.chart) {{
                ctxMSProd.chart = new Chart(ctxMSProd, {{
                    type: 'bar',
                    data: {{ labels: data.merchant_services.por_produto.map(d => d.produto), datasets: [{{ data: data.merchant_services.por_produto.map(d => d.pct), backgroundColor: nimbusColors.primary, borderRadius: 4 }}] }},
                    options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ max: 100 }} }} }}
                }});
            }}
            
            // Webinar MS Comparison
            const ctxWebMS = document.getElementById('chartWebinarMS');
            if (ctxWebMS && !ctxWebMS.chart) {{
                ctxWebMS.chart = new Chart(ctxWebMS, {{
                    type: 'bar',
                    data: {{
                        labels: data.webinars.merchant_services.com_webinar.por_produto.map(d => d.produto),
                        datasets: [
                            {{ label: 'Com Webinar', data: data.webinars.merchant_services.com_webinar.por_produto.map(d => d.pct), backgroundColor: nimbusColors.success, borderRadius: 4 }},
                            {{ label: 'Sem Webinar', data: data.webinars.merchant_services.sem_webinar.por_produto.map(d => d.pct), backgroundColor: nimbusColors.neutral, borderRadius: 4 }}
                        ]
                    }},
                    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ max: 100 }} }} }}
                }});
            }}
            
            // Risco Evolução
            const ctxRiscoEvo = document.getElementById('chartRiscoEvolucao');
            if (ctxRiscoEvo && !ctxRiscoEvo.chart && data.risco_evolucao && data.risco_evolucao.length > 1) {{
                ctxRiscoEvo.chart = new Chart(ctxRiscoEvo, {{
                    type: 'line',
                    data: {{ labels: data.risco_evolucao.map(d => d.mes), datasets: [{{ label: 'Prob. Média (%)', data: data.risco_evolucao.map(d => d.prob_media), borderColor: nimbusColors.danger, backgroundColor: 'rgba(200,0,3,0.1)', fill: true, tension: 0.4 }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ min: 0, max: 100 }} }} }}
                }});
            }}
            
            // Funil Mensal de Webinars
            const ctxFunilMensal = document.getElementById('chartFunilMensal');
            if (ctxFunilMensal && !ctxFunilMensal.chart && data.webinars.funil.por_mes && data.webinars.funil.por_mes.length > 0) {{
                const funilData = data.webinars.funil.por_mes;
                ctxFunilMensal.chart = new Chart(ctxFunilMensal, {{
                    type: 'bar',
                    data: {{
                        labels: funilData.map(d => d.mes_curto),
                        datasets: [
                            {{ label: '% Ao Vivo', data: funilData.map(d => d.pct_live), backgroundColor: nimbusColors.success, borderRadius: 4 }},
                            {{ label: '% On Demand', data: funilData.map(d => d.pct_ondemand), backgroundColor: nimbusColors.primary, borderRadius: 4 }},
                            {{ label: '% Total Participação', data: funilData.map(d => d.pct_participaram), backgroundColor: 'rgba(0,89,213,0.3)', borderColor: nimbusColors.primaryLight, borderWidth: 2, type: 'line', tension: 0.4 }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ position: 'top' }},
                            tooltip: {{
                                callbacks: {{
                                    afterBody: function(context) {{
                                        const idx = context[0].dataIndex;
                                        const d = funilData[idx];
                                        return `Total: ${{d.total.toLocaleString()}} registros`;
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                max: 100,
                                ticks: {{ callback: v => v + '%' }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Onboarding Status Chart
            const ctxOnbStatus = document.getElementById('chartOnboardingStatus');
            if (ctxOnbStatus && !ctxOnbStatus.chart && data.onboarding.status_pedidos && data.onboarding.status_pedidos.length > 0) {{
                const statusData = data.onboarding.status_pedidos;
                const statusColorMap = {{
                    'no-seller': nimbusColors.danger,
                    'struggling-seller': nimbusColors.warning,
                    'tiny-seller': nimbusColors.warningLight,
                    'small-seller': nimbusColors.successLight,
                    'medium-seller': nimbusColors.success,
                    'large-seller': '#00935b',
                    'top-seller': nimbusColors.primary,
                    'Not Informed': nimbusColors.neutral
                }};
                ctxOnbStatus.chart = new Chart(ctxOnbStatus, {{
                    type: 'doughnut',
                    data: {{
                        labels: statusData.map(d => d.status),
                        datasets: [{{
                            data: statusData.map(d => d.count),
                            backgroundColor: statusData.map(d => statusColorMap[d.status] || nimbusColors.neutral),
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ position: 'right' }} }}
                    }}
                }});
            }}
            
            // Onboarding Qualificação Chart
            const ctxOnbQual = document.getElementById('chartOnboardingQual');
            if (ctxOnbQual && !ctxOnbQual.chart && data.onboarding.qualificacao && data.onboarding.qualificacao.length > 0) {{
                const qualData = data.onboarding.qualificacao;
                ctxOnbQual.chart = new Chart(ctxOnbQual, {{
                    type: 'bar',
                    data: {{
                        labels: qualData.map(d => 'Score ' + d.score),
                        datasets: [{{
                            label: 'Lojas',
                            data: qualData.map(d => d.count),
                            backgroundColor: nimbusColors.primary,
                            borderRadius: 4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }}
                    }}
                }});
            }}
            
            // Preencher tabela de onboarding
            const onbTableBody = document.getElementById('onboardingTableBody');
            if (onbTableBody && data.onboarding.lista_lojas && data.onboarding.lista_lojas.length > 0) {{
                const lojas = data.onboarding.lista_lojas.slice(0, 50); // Top 50 na tabela
                onbTableBody.innerHTML = lojas.map(l => `
                    <tr>
                        <td>${{l.ID || l['Store ID'] || '-'}}</td>
                        <td>${{l.Nome || l['Nome da empresa'] || '-'}}</td>
                        <td>${{l.Status || '-'}}</td>
                        <td>R$ ${{(l.GMV || 0).toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}</td>
                        <td>${{l['Pedidos Total'] || l['total_orders'] || 0}}</td>
                        <td>${{l['Steps Onboarding'] || l['Onboarding - Steps completed'] || '-'}}</td>
                        <td>${{l.Score || l['[LCY BR] Qualificação - Potencial Sellers'] || '-'}}</td>
                    </tr>
                `).join('');
            }}
        }}
        
        document.addEventListener('DOMContentLoaded', initCharts);
    </script>
</body>
</html>
'''

# Salvar
output_path = os.path.join(BASE_DIR, 'index.html')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n✅ Dashboard gerado: {output_path}")
print(f"\n{'='*70}")
print("RESUMO")
print(f"{'='*70}")
print(f"  Lojas Ativas: {dashboard_data['resumo']['total_lojas_ativas']:,}")
print(f"  New Sellers: {dashboard_data['new_sellers']['soma_total']:,}")
print(f"  Cobertura: {dashboard_data['resumo']['pct_cobertura']}%")
