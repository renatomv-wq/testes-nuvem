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

new_sellers_analysis = {'total': 0, 'por_mes': [], 'soma_total': 0}

for mes_ns, df_ns in sorted(new_sellers_por_mes.items(), reverse=True):
    ns_id_col = 'store_id' if 'store_id' in df_ns.columns else 'id_store'
    ids_new_sellers = set(df_ns[ns_id_col].unique())
    total_ns = len(ids_new_sellers)
    
    ns_com_lifecycle = ids_new_sellers.intersection(ids_webinar)
    pct = round(len(ns_com_lifecycle) / total_ns * 100, 2) if total_ns > 0 else 0
    
    new_sellers_analysis['por_mes'].append({
        'mes': mes_ns,
        'total_new_sellers': total_ns,
        'com_lifecycle': len(ns_com_lifecycle),
        'pct_cobertura': pct
    })
    new_sellers_analysis['soma_total'] += total_ns
    print(f"  📅 {mes_ns}: {total_ns:,} new sellers, {len(ns_com_lifecycle)} com lifecycle ({pct}%)")

new_sellers_analysis['total'] = new_sellers_analysis['soma_total']

# =============================================================================
# ANÁLISE DE RISCO
# =============================================================================
print("\n🚨 Analisando Risco...")

lojas_com_churn = lojas_ativas[lojas_ativas['predictive_churn_probability'] > 0]

risk_quartiles_data = []
for q in RISK_QUARTILES:
    mask = (lojas_com_churn['predictive_churn_probability'] > q['min']) & \
           (lojas_com_churn['predictive_churn_probability'] <= q['max'])
    count = len(lojas_com_churn[mask])
    pct = round(count / len(lojas_com_churn) * 100, 1) if len(lojas_com_churn) > 0 else 0
    gmv = lojas_com_churn[mask]['gmv_mes'].sum()
    
    risk_quartiles_data.append({
        'name': q['name'],
        'color': q['color'],
        'count': count,
        'pct': pct,
        'gmv_total': round(gmv, 2),
        'prob_range': f"{int(q['min']*100)}%-{int(q['max']*100)}%"
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
for col in MERCHANT_COLS:
    # Lojas que NÃO tem o produto
    sem_produto = lojas_ativas[lojas_ativas[col] == False]
    if len(sem_produto) > 0:
        # Dessas, quantas tem pelo menos 1 outro produto
        sem_produto_com_outros = sem_produto[sem_produto['qtd_merchant_services'] >= 1]
        cross_sell.append({
            'produto': PRODUTO_NAMES[col],
            'codigo': col,
            'potencial': len(sem_produto_com_outros),
            'pct_potencial': round(len(sem_produto_com_outros) / len(lojas_ativas) * 100, 1),
            'ja_tem': int(lojas_ativas[col].sum())
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
lojas_ativas['tem_alguma_acao'] = lojas_ativas['tem_webinar']
lojas_cobertas = lojas_ativas[lojas_ativas['tem_alguma_acao'] == True]
com_webinar = lojas_ativas[lojas_ativas['tem_webinar'] == True]
sem_webinar = lojas_ativas[lojas_ativas['tem_webinar'] == False]

# =============================================================================
# MONTAR DADOS DO DASHBOARD
# =============================================================================
dashboard_data = {}

# Resumo
gmv_total = lojas_ativas['gmv_mes'].sum()
n_sellers = len(lojas_sellers)
pct_sellers = n_sellers / len(lojas_ativas) * 100 if len(lojas_ativas) > 0 else 0
n_cobertas = len(lojas_cobertas)
pct_cobertura = n_cobertas / len(lojas_ativas) * 100 if len(lojas_ativas) > 0 else 0

dashboard_data['resumo'] = {
    'total_lojas_ativas': len(lojas_ativas),
    'total_lojas_sellers': n_sellers,
    'pct_sellers': round(pct_sellers, 1),
    'gmv_total': round(gmv_total, 2),
    'gmv_medio': round(lojas_ativas['gmv_mes'].mean(), 2),
    'orders_total': int(lojas_ativas['orders_mes'].sum()),
    'n_cobertas': n_cobertas,
    'pct_cobertura': round(pct_cobertura, 1),
    'data_base': mes_atual,
    'churn_prob_media': round(lojas_com_churn['predictive_churn_probability'].mean() * 100, 2)
}

dashboard_data['new_sellers'] = new_sellers_analysis
dashboard_data['matriz_transicao'] = matriz_transicao
dashboard_data['risk_quartiles'] = risk_quartiles_data
dashboard_data['risco_evolucao'] = risco_evolucao

# Cobertura por projeto
dashboard_data['cobertura_projetos'] = [
    {
        'projeto': 'Webinars',
        'lojas': len(com_webinar),
        'pct': round(len(com_webinar) / len(lojas_ativas) * 100, 1),
        'status': 'ativo'
    },
    {'projeto': 'Onboarding', 'lojas': 0, 'pct': 0, 'status': 'em breve'},
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
            'gmv_medio': round(subset['gmv_mes'].mean(), 2),
            'gmv_total': round(subset['gmv_mes'].sum(), 2),
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
        'gmv_com': round(com_webinar['gmv_mes'].mean(), 2),
        'gmv_sem': round(sem_webinar['gmv_mes'].mean(), 2),
        'gmv_diff_pct': round((com_webinar['gmv_mes'].mean() - sem_webinar['gmv_mes'].mean()) / sem_webinar['gmv_mes'].mean() * 100, 1) if sem_webinar['gmv_mes'].mean() > 0 else 0,
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
        gmv_com = com_web['gmv_mes'].mean()
        gmv_sem = sem_web['gmv_mes'].mean()
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

# =============================================================================
# GERAR HTML
# =============================================================================
print("\n🎨 Gerando HTML...")

# Helpers para tabelas
ns_rows = ''.join([f"<tr><td>{m['mes']}</td><td>{m['total_new_sellers']:,}</td><td>{m['com_lifecycle']}</td><td class='{'positive' if m['pct_cobertura']>5 else 'neutral' if m['pct_cobertura']>2 else ''}'>{m['pct_cobertura']}%</td></tr>" for m in dashboard_data['new_sellers']['por_mes'][:6]])

def generate_afinidade_rows():
    """Gera rows da tabela de afinidade de produtos"""
    rows = []
    for a in dashboard_data['merchant_services']['afinidade']:
        relacionados = ', '.join([f"{p['produto']} ({p['pct']}%)" for p in a['produtos_relacionados']])
        rows.append(f"<tr><td><strong>{a['produto']}</strong></td><td>{a['total_clientes']:,}</td><td>{relacionados}</td></tr>")
    return ''.join(rows)

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
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            color: #e2e8f0;
        }}
        .header {{
            background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
            padding: 24px 40px;
        }}
        .header h1 {{ font-size: 24px; font-weight: 700; }}
        .header p {{ opacity: 0.9; font-size: 13px; margin-top: 4px; }}
        .tabs {{
            display: flex;
            background: #0f172a;
            padding: 0 40px;
            border-bottom: 1px solid #334155;
            overflow-x: auto;
        }}
        .tab {{
            padding: 14px 20px;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            font-weight: 500;
            color: #64748b;
            white-space: nowrap;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .tab:hover {{ color: #e2e8f0; background: rgba(255,255,255,0.05); }}
        .tab.active {{ color: #3b82f6; border-bottom-color: #3b82f6; }}
        .tab.disabled {{ color: #475569; cursor: not-allowed; }}
        .badge {{ background: #334155; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 6px; }}
        .badge.soon {{ background: #854d0e; color: #fef3c7; }}
        .content {{ padding: 30px 40px; max-width: 1600px; margin: 0 auto; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
        .grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
        .grid-4 {{ grid-template-columns: repeat(4, 1fr); }}
        .grid-5 {{ grid-template-columns: repeat(5, 1fr); }}
        .card {{
            background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .card-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #64748b; margin-bottom: 8px; }}
        .card-value {{ font-size: 28px; font-weight: 700; color: #f8fafc; }}
        .card-value.gradient {{ background: linear-gradient(90deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .card-subtitle {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
        .positive {{ color: #4ade80; }}
        .negative {{ color: #f87171; }}
        .neutral {{ color: #fbbf24; }}
        .section-title {{ font-size: 16px; font-weight: 600; margin: 28px 0 16px 0; padding-bottom: 10px; border-bottom: 1px solid #334155; }}
        .chart-container {{ position: relative; height: 280px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 13px; }}
        th {{ font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #64748b; }}
        tr:hover {{ background: rgba(255,255,255,0.02); }}
        .insight-box {{
            background: rgba(59, 130, 246, 0.1);
            border-left: 4px solid #3b82f6;
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            margin: 16px 0;
        }}
        .insight-box h4 {{ color: #3b82f6; margin-bottom: 6px; font-size: 13px; }}
        .insight-box p {{ font-size: 12px; color: #94a3b8; line-height: 1.5; }}
        .insight-box.warning {{ border-left-color: #f59e0b; }}
        .insight-box.warning h4 {{ color: #f59e0b; }}
        .two-columns {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .risk-matrix {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }}
        .risk-card {{ padding: 16px; border-radius: 10px; text-align: center; }}
        .risk-card h3 {{ font-size: 24px; font-weight: 700; margin-bottom: 6px; }}
        .risk-card p {{ font-size: 11px; }}
        .status-dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }}
        .upgrade-card {{ background: rgba(74,222,128,0.15); border: 1px solid #4ade80; }}
        .upgrade-card .card-value {{ color: #4ade80; }}
        .stable-card {{ background: rgba(148,163,184,0.15); border: 1px solid #94a3b8; }}
        .stable-card .card-value {{ color: #94a3b8; }}
        .downgrade-card {{ background: rgba(248,113,113,0.15); border: 1px solid #f87171; }}
        .downgrade-card .card-value {{ color: #f87171; }}
        .text-center {{ text-align: center; }}
        .text-muted {{ color: #64748b; font-size: 12px; margin-top: 12px; }}
        code {{ background: #334155; padding: 2px 6px; border-radius: 4px; font-size: 11px; }}
        .comparison {{ display: flex; gap: 24px; margin-top: 12px; }}
        .comparison-item {{ flex: 1; }}
        .comparison-label {{ font-size: 10px; color: #64748b; text-transform: uppercase; margin-bottom: 4px; }}
        .comparison-value {{ font-size: 22px; font-weight: 600; }}
        @media (max-width: 1000px) {{ .two-columns, .grid-3, .grid-4, .grid-5, .risk-matrix {{ grid-template-columns: 1fr 1fr; }} }}
        @media (max-width: 600px) {{ .two-columns, .grid-3, .grid-4, .grid-5, .risk-matrix {{ grid-template-columns: 1fr; }} }}
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
        <div class="tab disabled">Onboarding <span class="badge soon">em breve</span></div>
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
            
            <h2 class="section-title">New Sellers</h2>
            <div class="grid grid-4">
                <div class="card"><div class="card-title">Total New Sellers</div><div class="card-value gradient">{dashboard_data['new_sellers']['soma_total']:,}</div></div>
                <div class="card" style="grid-column:span 3;"><div class="card-title">Impacto por Mês</div><table><thead><tr><th>Mês</th><th>New Sellers</th><th>Com Lifecycle</th><th>%</th></tr></thead><tbody>{ns_rows}</tbody></table></div>
            </div>
            
            <h2 class="section-title">Matriz de Transição</h2>
            {matriz_html}
            
            <h2 class="section-title">Matriz de Risco</h2>
            <div class="risk-matrix">
                {''.join([f'<div class="risk-card" style="background:{q["color"]}20;border:2px solid {q["color"]};"><h3 style="color:{q["color"]};">{q["count"]:,}</h3><p style="color:{q["color"]};font-weight:600;">{q["name"]}</p><p>{q["pct"]}%</p></div>' for q in dashboard_data['risk_quartiles']])}
            </div>
        </div>
        
        <!-- BASE -->
        <div id="base" class="tab-content">
            <h2 class="section-title">Distribuição por Status</h2>
            <div class="two-columns">
                <div class="card"><div class="card-title">Pirâmide de Status</div><div class="chart-container"><canvas id="chartStatusBase"></canvas></div></div>
                <div class="card"><div class="card-title">Performance por Status</div><table><thead><tr><th>Status</th><th>Lojas</th><th>GMV Médio</th><th>Churn</th></tr></thead><tbody>{''.join([f'<tr><td><span class="status-dot" style="background:{["#ef4444","#f97316","#fbbf24","#84cc16","#22c55e","#14b8a6","#3b82f6"][STATUS_ORDER.index(s["status"]) if s["status"] in STATUS_ORDER else 0]};"></span><strong>{s["label"]}</strong></td><td>{s["count"]:,}</td><td>R$ {s["gmv_medio"]:,.0f}</td><td class="{"positive" if s["churn_prob"]<25 else "neutral" if s["churn_prob"]<45 else "negative"}">{s["churn_prob"]}%</td></tr>' for s in dashboard_data['status_base']['distribuicao']])}</tbody></table></div>
            </div>
            
            <h2 class="section-title">Matriz de Transição</h2>
            {matriz_html}
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
            <div class="card">
                <table>
                    <thead><tr><th>Produto</th><th>Já tem</th><th>Potencial (lojas com outros produtos)</th><th>% Base</th></tr></thead>
                    <tbody>
                        {''.join([f'<tr><td><strong>{c["produto"]}</strong></td><td>{c["ja_tem"]:,}</td><td class="positive">{c["potencial"]:,}</td><td>{c["pct_potencial"]}%</td></tr>' for c in dashboard_data['merchant_services']['cross_sell']])}
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
        </div>
        
        <!-- RISCO -->
        <div id="risco" class="tab-content">
            <h2 class="section-title">Matriz de Quartis de Risco</h2>
            <div class="risk-matrix">
                {''.join([f'<div class="risk-card" style="background:{q["color"]}20;border:2px solid {q["color"]};"><h3 style="color:{q["color"]};">{q["count"]:,}</h3><p style="color:{q["color"]};font-weight:600;">{q["name"]}</p><p>{q["pct"]}% | GMV: R$ {q["gmv_total"]/1000000:.1f}M</p></div>' for q in dashboard_data['risk_quartiles']])}
            </div>
            
            <div class="two-columns">
                <div class="card"><div class="card-title">Risco por Status</div><div class="chart-container"><canvas id="chartChurnStatus"></canvas></div></div>
                <div class="card"><div class="card-title">Detalhamento</div><table><thead><tr><th>Status</th><th>Lojas</th><th>Prob. Média</th></tr></thead><tbody>{''.join([f'<tr><td><strong>{s["label"]}</strong></td><td>{s["lojas"]:,}</td><td class="{"positive" if s["prob_media"]<25 else "neutral" if s["prob_media"]<45 else "negative"}">{s["prob_media"]}%</td></tr>' for s in dashboard_data['churn']['por_status']])}</tbody></table></div>
            </div>
            
            {'<div class="insight-box warning"><h4>📈 Evolução do Risco</h4><p>Carregue bases de múltiplos meses para ver a evolução</p></div>' if len(risco_evolucao) <= 1 else f'<h2 class="section-title">Evolução do Risco</h2><div class="card"><div class="chart-container"><canvas id="chartRiscoEvolucao"></canvas></div></div>'}
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
            <div class="grid grid-4">
                <div class="card"><div class="card-title">Lojas com Cobertura</div><div class="card-value gradient">{dashboard_data['webinars']['total_participantes']:,}</div><div class="card-subtitle">{dashboard_data['webinars']['pct_base']}% da base</div></div>
                <div class="card"><div class="card-title">GMV</div><div class="card-value positive">+{dashboard_data['webinars']['performance']['gmv_diff_pct']}%</div><div class="card-subtitle">vs sem webinar</div></div>
                <div class="card"><div class="card-title">Churn</div><div class="card-value positive">{dashboard_data['webinars']['churn']['diff_pp']}pp</div><div class="card-subtitle">vs sem webinar</div></div>
                <div class="card"><div class="card-title">Pareada</div><div class="card-value positive">+{dashboard_data['webinars']['analise_pareada']['gmv_diff_pct']}%</div><div class="card-subtitle">mesmo perfil</div></div>
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
        </div>
    </div>
    
    <script>
        const data = {json.dumps(dashboard_data, ensure_ascii=False)};
        const statusColors = {{'no-seller':'#ef4444','struggling-seller':'#f97316','tiny-seller':'#fbbf24','small-seller':'#84cc16','medium-seller':'#22c55e','large-seller':'#14b8a6','top-seller':'#3b82f6'}};
        
        function showTab(id) {{
            document.querySelectorAll('.tab-content').forEach(e => e.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(e => e.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.target.classList.add('active');
            setTimeout(initCharts, 50);
        }}
        
        Chart.defaults.color = '#64748b';
        Chart.defaults.borderColor = '#334155';
        
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
                    data: {{ labels: data.churn.por_status.map(d => d.label), datasets: [{{ data: data.churn.por_status.map(d => d.prob_media), borderColor: '#f87171', backgroundColor: 'rgba(248,113,113,0.1)', fill: true, tension: 0.4 }}] }},
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
                    data: {{ labels: data.merchant_services.distribuicao.map(d => d.qtd + ' produto(s)'), datasets: [{{ data: data.merchant_services.distribuicao.map(d => d.count), backgroundColor: ['#64748b','#3b82f6','#8b5cf6','#ec4899','#f59e0b','#22c55e'], borderRadius: 4 }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
                }});
            }}
            
            // MS Produtos
            const ctxMSProd = document.getElementById('chartMSProdutos');
            if (ctxMSProd && !ctxMSProd.chart) {{
                ctxMSProd.chart = new Chart(ctxMSProd, {{
                    type: 'bar',
                    data: {{ labels: data.merchant_services.por_produto.map(d => d.produto), datasets: [{{ data: data.merchant_services.por_produto.map(d => d.pct), backgroundColor: '#3b82f6', borderRadius: 4 }}] }},
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
                            {{ label: 'Com Webinar', data: data.webinars.merchant_services.com_webinar.por_produto.map(d => d.pct), backgroundColor: '#4ade80', borderRadius: 4 }},
                            {{ label: 'Sem Webinar', data: data.webinars.merchant_services.sem_webinar.por_produto.map(d => d.pct), backgroundColor: '#64748b', borderRadius: 4 }}
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
                    data: {{ labels: data.risco_evolucao.map(d => d.mes), datasets: [{{ label: 'Prob. Média (%)', data: data.risco_evolucao.map(d => d.prob_media), borderColor: '#f87171', backgroundColor: 'rgba(248,113,113,0.1)', fill: true, tension: 0.4 }}] }},
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
                            {{ label: '% Ao Vivo', data: funilData.map(d => d.pct_live), backgroundColor: '#4ade80', borderRadius: 4 }},
                            {{ label: '% On Demand', data: funilData.map(d => d.pct_ondemand), backgroundColor: '#3b82f6', borderRadius: 4 }},
                            {{ label: '% Total Participação', data: funilData.map(d => d.pct_participaram), backgroundColor: 'rgba(139, 92, 246, 0.5)', borderColor: '#8b5cf6', borderWidth: 2, type: 'line', tension: 0.4 }}
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
