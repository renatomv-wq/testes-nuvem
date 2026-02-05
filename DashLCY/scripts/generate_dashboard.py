#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Impacto - Lifecycle BR
Gerador de dashboard para análise de impacto das ações de Lifecycle
"""

import pandas as pd
import json
import warnings
import os
import glob
import re
from datetime import datetime
from collections import Counter
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
ALT_BASE_PATH = '/Users/renatovieira/Downloads/base_br_diciembre_2024.csv'
ALT_WEBINAR_PATH = '/Users/renatovieira/Downloads/Webinars - geral até Dezembro_25 - Raw Data_data (4).csv'
ALT_NEWSELLERS_PATH = '/Users/renatovieira/Downloads/Raw Data Total Stores (2).csv'

STATUS_ORDER = ['no-seller', 'struggling-seller', 'tiny-seller', 'small-seller', 
                'medium-seller', 'large-seller', 'top-seller']
STATUS_LABELS = {
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

# Quartis de risco
RISK_QUARTILES = [
    {'name': 'Sem Risco', 'min': 0, 'max': 0.25, 'color': '#22c55e'},
    {'name': 'Baixo Risco', 'min': 0.25, 'max': 0.50, 'color': '#fbbf24'},
    {'name': 'Médio Risco', 'min': 0.50, 'max': 0.75, 'color': '#f97316'},
    {'name': 'Alto Risco', 'min': 0.75, 'max': 1.01, 'color': '#ef4444'},
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
    """Carrega todas as bases gerais de lojas"""
    data_folder = os.path.join(DATA_DIR, 'base_geral')
    files = find_all_files_sorted(data_folder)
    
    bases = {}
    
    if files:
        for filepath, date_str in files:
            print(f"  📂 Base encontrada: {os.path.basename(filepath)} ({date_str})")
            df = pd.read_csv(filepath, low_memory=False)
            df = df[df['merchant_finance_status'] == 'paying'].copy()
            bases[date_str] = df
    
    if not bases and os.path.exists(ALT_BASE_PATH):
        print(f"  📂 Usando base alternativa: {os.path.basename(ALT_BASE_PATH)}")
        df = pd.read_csv(ALT_BASE_PATH, low_memory=False)
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

def classify_risk(prob):
    """Classifica risco em quartis"""
    if pd.isna(prob) or prob <= 0:
        return 'Sem dados'
    elif prob <= 0.25:
        return 'Sem Risco'
    elif prob <= 0.50:
        return 'Baixo Risco'
    elif prob <= 0.75:
        return 'Médio Risco'
    else:
        return 'Alto Risco'

def get_status_tier(status):
    """Retorna o nível do status para comparação"""
    if status not in STATUS_ORDER:
        return -1
    return STATUS_ORDER.index(status)

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

# Classificar risco
lojas_ativas['risk_quartile'] = lojas_ativas['predictive_churn_probability'].apply(classify_risk)

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
# MATRIZ DE TRANSIÇÃO
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
    'detalhes': []
}

if len(meses_disponiveis) >= 2:
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
    
    upgrade = len(lojas_continuam[lojas_continuam['tier_depois'] > lojas_continuam['tier_antes']])
    downgrade = len(lojas_continuam[lojas_continuam['tier_depois'] < lojas_continuam['tier_antes']])
    estavel = len(lojas_continuam[lojas_continuam['tier_depois'] == lojas_continuam['tier_antes']])
    
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
        'detalhes': []
    }
    
    print(f"  ✅ Upgrade: {upgrade:,} | Estável: {estavel:,} | Downgrade: {downgrade:,}")
else:
    print("  ⚠️ Apenas 1 mês disponível")

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
    
    # Classificar em 3 grupos: Onboarding, Grupo Controle, Base Antiga
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
                    'nome': 'Grupo Controle',
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
            churn_valid = subset['predictive_churn_probability'].dropna()
            
            if len(churn_valid) > 0:
                # Calcular quartis
                q1 = int((churn_valid <= 0.25).sum())
                q2 = int(((churn_valid > 0.25) & (churn_valid <= 0.50)).sum())
                q3 = int(((churn_valid > 0.50) & (churn_valid <= 0.75)).sum())
                q4 = int((churn_valid > 0.75).sum())
                total_q = len(churn_valid)
                
                churn_by_group[grupo] = {
                    'n_total': int(len(subset)),
                    'n_com_churn': int(len(churn_valid)),
                    'churn_medio': float(round(churn_valid.mean() * 100, 1)),
                    'churn_mediana': float(round(churn_valid.median() * 100, 1)),
                    'quartis': {
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
    print(f"      Onboarding: {n_onboarding} ({pct_onboarding}%) | Grupo Controle: {n_controle} ({pct_controle}%) | Base Antiga: {n_base_antiga} ({pct_base_antiga}%)")

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
            'projeto': 'Grupo Controle',
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

lojas_com_churn = lojas_ativas[lojas_ativas['predictive_churn_probability'] > 0]

risk_quartiles_data = []
risk_quartiles_lojas = {}  # Armazena lista de lojas por quartil

for q in RISK_QUARTILES:
    mask = (lojas_com_churn['predictive_churn_probability'] > q['min']) & \
           (lojas_com_churn['predictive_churn_probability'] <= q['max'])
    lojas_quartil = lojas_com_churn[mask].copy()
    count = len(lojas_quartil)
    pct = round(count / len(lojas_com_churn) * 100, 1) if len(lojas_com_churn) > 0 else 0
    gmv = lojas_quartil['gmv_mes_local'].sum()
    
    # Estatísticas do quartil
    stats = {
        'gmv_medio': round(lojas_quartil['gmv_mes_local'].mean(), 2) if count > 0 else 0,
        'orders_medio': round(lojas_quartil['orders_mes'].mean(), 1) if count > 0 else 0,
        'prob_media': round(lojas_quartil['predictive_churn_probability'].mean() * 100, 2) if count > 0 else 0,
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
    
    risk_quartiles_data.append({
        'name': q['name'],
        'color': q['color'],
        'count': count,
        'pct': pct,
        'gmv_total': round(gmv, 2),
        'prob_range': f"{int(q['min']*100)}%-{int(q['max']*100)}%",
        'stats': stats,
        'status_distribution': status_dist_formatted
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

# Análise de risco por quartil: com vs sem webinar
print("  📊 Calculando risco por quartil (com vs sem webinar)...")
com_webinar_churn = com_webinar[com_webinar['predictive_churn_probability'] > 0]
sem_webinar_churn = sem_webinar[sem_webinar['predictive_churn_probability'] > 0]

risk_quartiles_webinar = []
for q in RISK_QUARTILES:
    # Com webinar
    mask_com = (com_webinar_churn['predictive_churn_probability'] > q['min']) & \
               (com_webinar_churn['predictive_churn_probability'] <= q['max'])
    count_com = len(com_webinar_churn[mask_com])
    pct_com = round(count_com / len(com_webinar_churn) * 100, 1) if len(com_webinar_churn) > 0 else 0
    
    # Sem webinar
    mask_sem = (sem_webinar_churn['predictive_churn_probability'] > q['min']) & \
               (sem_webinar_churn['predictive_churn_probability'] <= q['max'])
    count_sem = len(sem_webinar_churn[mask_sem])
    pct_sem = round(count_sem / len(sem_webinar_churn) * 100, 1) if len(sem_webinar_churn) > 0 else 0
    
    risk_quartiles_webinar.append({
        'name': q['name'],
        'color': q['color'],
        'count_com': count_com,
        'pct_com': pct_com,
        'count_sem': count_sem,
        'pct_sem': pct_sem,
        'diff_pp': round(pct_com - pct_sem, 1)
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
    (lojas_ativas['aging_faixa_simples'] != 'N/A')
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
                            <span class="text-muted" style="font-size:0.75rem;">N Grupo Controle</span>
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
                                    <td><strong>Grupo Controle</strong></td>
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
                    <h4 style="margin-bottom:12px;">Distribuição por Quartil de Risco</h4>
                    <p class="text-muted" style="margin-bottom:12px;">Comparação da distribuição de lojas em cada faixa de risco. Diferenças negativas nos quartis de maior risco indicam que o onboarding ajuda a reduzir o risco.</p>
                    <div class="quartile-comparison">
                        {''.join([f'<div class="quartile-card" style="background:{q["color"]}15;border:2px solid {q["color"]};"><h4 style="color:{q["color"]};">{q["name"]}</h4><div class="quartile-row"><span class="quartile-label">Onboarding</span><span class="quartile-value" style="color:{q["color"]};">{q["pct_onb"]}%</span></div><div class="quartile-row"><span class="quartile-label">Controle</span><span class="quartile-value">{q["pct_ctrl"]}%</span></div><div class="quartile-row"><span class="quartile-label">Diferença</span><span class="quartile-value {"positive" if q["is_good"] else "negative" if not q["is_good"] and q["diff"]!=0 else ""}">{("+" if q["diff"]>0 else "")}{q["diff"]}pp</span></div></div>' for q in quartis_comparison])}
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

matriz_html = ''
if matriz_transicao['disponivel']:
    matriz_html = f'''
    <div class="grid-3">
        <div class="card upgrade-card">
            <div class="card-title">⬆️ Upgrade</div>
            <div class="card-value">{matriz_transicao['upgrade']:,}</div>
            <div class="card-subtitle">{matriz_transicao['pct_upgrade']}%</div>
        </div>
        <div class="card stable-card">
            <div class="card-title">➡️ Estável</div>
            <div class="card-value">{matriz_transicao['estavel']:,}</div>
            <div class="card-subtitle">{matriz_transicao['pct_estavel']}%</div>
        </div>
        <div class="card downgrade-card">
            <div class="card-title">⬇️ Downgrade</div>
            <div class="card-value">{matriz_transicao['downgrade']:,}</div>
            <div class="card-subtitle">{matriz_transicao['pct_downgrade']}%</div>
        </div>
    </div>
    <p class="text-center text-muted">Comparativo: {matriz_transicao['mes_anterior']} → {matriz_transicao['mes_atual']}</p>
    '''
else:
    matriz_html = '<div class="insight-box warning"><h4>📊 Matriz de Transição</h4><p>Carregue uma base do mês anterior na pasta <code>data/base_geral/</code></p></div>'

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
        <div class="tab" onclick="showTab('merchant')">Merchant Services</div>
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
                        <tr><td><strong>Onboarding V2</strong></td><td>{dashboard_data['new_sellers']['impacto_por_projeto'][0]['n']:,}</td><td class="positive">{dashboard_data['new_sellers']['impacto_por_projeto'][0]['pct']}%</td><td>Grupo Teste</td></tr>
                        <tr><td><strong>Grupo Controle</strong></td><td>{dashboard_data['new_sellers']['impacto_por_projeto'][1]['n']:,}</td><td>{dashboard_data['new_sellers']['impacto_por_projeto'][1]['pct']}%</td><td>Criados a partir de Out/2025, sem onboarding</td></tr>
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
                <div class="card"><div class="card-title">Performance por Status</div><table><thead><tr><th>Status</th><th>Lojas</th><th>GMV Médio</th><th>Churn</th></tr></thead><tbody>{''.join([f'<tr><td><span class="status-dot" style="background:{["#c80003","#c87b00","#f7c77a","#7af7c7","#00c87b","#00935b","#0059d5"][STATUS_ORDER.index(s["status"]) if s["status"] in STATUS_ORDER else 0]};"></span><strong>{s["label"]}</strong></td><td>{s["count"]:,}</td><td>R$ {s["gmv_medio"]:,.0f}</td><td class="{"positive" if s["churn_prob"]<25 else "neutral" if s["churn_prob"]<45 else "negative"}">{s["churn_prob"]}%</td></tr>' for s in dashboard_data['status_base']['distribuicao']])}</tbody></table></div>
            </div>
            
            <h2 class="section-title">Matriz de Transição</h2>
            {matriz_html}
            
            {insights_base_html}
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
            
            <h2 class="section-title">Impacto em New Sellers</h2>
            <div class="card">
                <table><thead><tr><th>Mês</th><th>New Sellers</th><th>Com Webinar</th><th>%</th></tr></thead><tbody>{''.join([f'<tr><td>{m["mes"]}</td><td>{m["total_new_sellers"]:,}</td><td>{m["com_lifecycle"]}</td><td class="{"positive" if m["pct_cobertura"]>5 else "neutral" if m["pct_cobertura"]>2 else ""}">{m["pct_cobertura"]}%</td></tr>' for m in dashboard_data['webinars']['new_sellers_impacto'][:6]])}</tbody></table>
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
