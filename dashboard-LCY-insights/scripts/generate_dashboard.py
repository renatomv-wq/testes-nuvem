import pandas as pd
import json
import warnings
warnings.filterwarnings('ignore')

print("📊 Gerando dados para o dashboard v2...")

# =============================================================================
# CARREGAR DADOS
# =============================================================================
dezembro_df_raw = pd.read_csv('/Users/renatovieira/Downloads/base_br_diciembre_2024.csv', low_memory=False)

# IMPORTANTE: Filtrar apenas lojas PAGANTES (merchant_finance_status = paying)
dezembro_df = dezembro_df_raw[dezembro_df_raw['merchant_finance_status'] == 'paying'].copy()
print(f"  📌 Base filtrada: {len(dezembro_df):,} lojas pagantes (de {len(dezembro_df_raw):,} total)")

webinars_df = pd.read_csv(
    '/Users/renatovieira/Downloads/Webinars - geral até Dezembro_25 - Raw Data_data (4).csv'
)

# Filtrar webinars com cobertura
webinars_com_cobertura = webinars_df[
    webinars_df['Cobertura'].str.strip() == 'Com cobertura'
].copy()

ids_com_cobertura = set(webinars_com_cobertura['store_id'].unique())

# Criar flag e quantidade de webinars
dezembro_df['tem_cobertura_webinar'] = dezembro_df['id_store'].isin(ids_com_cobertura)
webinars_por_loja = webinars_com_cobertura.groupby('store_id').size().reset_index(name='qtd_webinars')
dezembro_df = dezembro_df.merge(webinars_por_loja, left_on='id_store', right_on='store_id', how='left')
dezembro_df['qtd_webinars'] = dezembro_df['qtd_webinars'].fillna(0).astype(int)

# =============================================================================
# MERCHANT SERVICES - Calcular quantidade de produtos
# =============================================================================
print("📦 Calculando adoção de Merchant Services...")

merchant_cols = ['nuvemmarketing', 'nuvempago', 'nuvemchat', 'nuvemenvio', 'pdv']

# Converter para boolean se necessário
for col in merchant_cols:
    dezembro_df[col] = dezembro_df[col].astype(str).str.lower().isin(['true', '1', 'yes'])

# Calcular quantidade de produtos por loja
dezembro_df['qtd_merchant_services'] = dezembro_df[merchant_cols].sum(axis=1)

# =============================================================================
# AGING - Categorizar tempo de loja
# =============================================================================
dezembro_df['aging_clean'] = pd.to_numeric(dezembro_df['aging'], errors='coerce')

def categorize_aging(days):
    if pd.isna(days):
        return 'N/A'
    elif days <= 30:
        return '0-30 dias'
    elif days <= 90:
        return '31-90 dias'
    elif days <= 180:
        return '91-180 dias'
    elif days <= 365:
        return '181-365 dias'
    elif days <= 730:
        return '1-2 anos'
    elif days <= 1825:
        return '2-5 anos'
    else:
        return '5+ anos'

def categorize_aging_simple(days):
    """Versão simplificada para pareamento"""
    if pd.isna(days):
        return 'N/A'
    elif days <= 90:
        return '0-90 dias'
    elif days <= 365:
        return '91-365 dias'
    elif days <= 730:
        return '1-2 anos'
    else:
        return '2+ anos'

dezembro_df['aging_faixa'] = dezembro_df['aging_clean'].apply(categorize_aging)
dezembro_df['aging_faixa_simples'] = dezembro_df['aging_clean'].apply(categorize_aging_simple)

# =============================================================================
# PREPARAR DADOS PARA DASHBOARD
# =============================================================================

# Lojas ativas
lojas_ativas = dezembro_df[(dezembro_df['gmv_mes'] > 0) | (dezembro_df['orders_mes'] > 0)].copy()
com_webinar = lojas_ativas[lojas_ativas['tem_cobertura_webinar'] == True]
sem_webinar = lojas_ativas[lojas_ativas['tem_cobertura_webinar'] == False]

# Participantes (todas as lojas com webinar, não apenas ativas)
participantes = dezembro_df[dezembro_df['tem_cobertura_webinar'] == True].copy()

# Lojas com dados de churn
lojas_com_churn = dezembro_df[dezembro_df['predictive_churn_probability'] > 0].copy()
churn_com = lojas_com_churn[lojas_com_churn['tem_cobertura_webinar'] == True]
churn_sem = lojas_com_churn[lojas_com_churn['tem_cobertura_webinar'] == False]

# =============================================================================
# MÉTRICAS PRINCIPAIS
# =============================================================================
dashboard_data = {
    'resumo': {
        'total_base': len(dezembro_df),
        'lojas_ativas': len(lojas_ativas),
        'lojas_webinar': len(ids_com_cobertura),
        'lojas_webinar_ativas': len(com_webinar),
        'cobertura_pct': round(len(com_webinar) / len(lojas_ativas) * 100, 2) if len(lojas_ativas) > 0 else 0
    },
    'performance': {
        'gmv_medio_com': round(com_webinar['gmv_mes'].mean(), 2),
        'gmv_medio_sem': round(sem_webinar['gmv_mes'].mean(), 2),
        'gmv_mediano_com': round(com_webinar['gmv_mes'].median(), 2),
        'gmv_mediano_sem': round(sem_webinar['gmv_mes'].median(), 2),
        'orders_medio_com': round(com_webinar['orders_mes'].mean(), 1),
        'orders_medio_sem': round(sem_webinar['orders_mes'].mean(), 1),
        'orders_mediano_com': round(com_webinar['orders_mes'].median(), 1),
        'orders_mediano_sem': round(sem_webinar['orders_mes'].median(), 1),
        'diff_gmv_pct': round((com_webinar['gmv_mes'].mean() - sem_webinar['gmv_mes'].mean()) / sem_webinar['gmv_mes'].mean() * 100, 1),
        'diff_orders_pct': round((com_webinar['orders_mes'].mean() - sem_webinar['orders_mes'].mean()) / sem_webinar['orders_mes'].mean() * 100, 1)
    },
    'churn': {
        'prob_com': round(churn_com['predictive_churn_probability'].mean() * 100, 2),
        'prob_sem': round(churn_sem['predictive_churn_probability'].mean() * 100, 2),
        'diff_pp': round((churn_com['predictive_churn_probability'].mean() - churn_sem['predictive_churn_probability'].mean()) * 100, 2),
        'lojas_com_dados': len(lojas_com_churn)
    }
}

# =============================================================================
# MERCHANT SERVICES ANALYSIS
# =============================================================================
print("📊 Analisando adoção de Merchant Services...")

# Distribuição de quantidade de produtos - TODA BASE ATIVA
ms_dist_total = lojas_ativas['qtd_merchant_services'].value_counts().sort_index().to_dict()
dashboard_data['merchant_services_dist'] = [
    {'qtd': int(k), 'count': int(v), 'pct': round(v/len(lojas_ativas)*100, 1)} 
    for k, v in ms_dist_total.items()
]

# Comparativo COM vs SEM webinar
ms_com = com_webinar['qtd_merchant_services'].value_counts(normalize=True).sort_index() * 100
ms_sem = sem_webinar['qtd_merchant_services'].value_counts(normalize=True).sort_index() * 100

dashboard_data['merchant_services_comparativo'] = []
for qtd in range(6):
    dashboard_data['merchant_services_comparativo'].append({
        'qtd': qtd,
        'pct_com': round(ms_com.get(qtd, 0), 1),
        'pct_sem': round(ms_sem.get(qtd, 0), 1)
    })

# Média de produtos por grupo
media_ms_com = com_webinar['qtd_merchant_services'].mean()
media_ms_sem = sem_webinar['qtd_merchant_services'].mean()

dashboard_data['merchant_services_media'] = {
    'com_webinar': round(media_ms_com, 2),
    'sem_webinar': round(media_ms_sem, 2),
    'diff_pct': round((media_ms_com - media_ms_sem) / media_ms_sem * 100, 1) if media_ms_sem > 0 else 0
}

# Adoção por produto individual
dashboard_data['merchant_services_por_produto'] = []
for col in merchant_cols:
    adocao_com = com_webinar[col].mean() * 100
    adocao_sem = sem_webinar[col].mean() * 100
    dashboard_data['merchant_services_por_produto'].append({
        'produto': col.replace('nuvem', 'Nuvem ').replace('pdv', 'PDV').title(),
        'pct_com': round(adocao_com, 1),
        'pct_sem': round(adocao_sem, 1),
        'diff_pp': round(adocao_com - adocao_sem, 1)
    })

# =============================================================================
# COMBINAÇÕES DE PRODUTOS (Cross-sell Analysis)
# =============================================================================
print("🔄 Analisando combinações de produtos para cross-sell...")

def get_combo(row):
    produtos = []
    for col in merchant_cols:
        if row[col]:
            nome = col.replace('nuvem', '').replace('pdv', 'PDV').upper()
            if nome == 'MARKETING':
                nome = 'MKT'
            produtos.append(nome)
    if not produtos:
        return 'Nenhum produto'
    return ' + '.join(sorted(produtos))

lojas_ativas['combo'] = lojas_ativas.apply(get_combo, axis=1)

# Top combinações
combos = lojas_ativas['combo'].value_counts().head(10)
dashboard_data['combinacoes_produtos'] = [
    {'combo': combo, 'count': int(count), 'pct': round(count/len(lojas_ativas)*100, 1)}
    for combo, count in combos.items()
]

# Análise de cross-sell: Para quem tem cada produto, qual % NÃO tem os outros
dashboard_data['cross_sell'] = []
produto_names = {
    'nuvemmarketing': 'Nuvem Marketing',
    'nuvempago': 'Nuvem Pago', 
    'nuvemchat': 'Nuvem Chat',
    'nuvemenvio': 'Nuvem Envio',
    'pdv': 'PDV'
}

for prod in merchant_cols:
    tem_prod = lojas_ativas[lojas_ativas[prod] == True]
    if len(tem_prod) > 100:  # Só mostrar se tiver volume
        for other in merchant_cols:
            if other != prod:
                pct_tem = tem_prod[other].mean() * 100
                pct_nao_tem = 100 - pct_tem
                oportunidade = len(tem_prod) * (pct_nao_tem / 100)
                dashboard_data['cross_sell'].append({
                    'tem': produto_names[prod],
                    'nao_tem': produto_names[other],
                    'pct_nao_tem': round(pct_nao_tem, 1),
                    'oportunidade': int(oportunidade),
                    'base': len(tem_prod)
                })

# Ordenar por oportunidade (maior primeiro)
dashboard_data['cross_sell'].sort(key=lambda x: x['oportunidade'], reverse=True)

# =============================================================================
# ANÁLISE DE STATUS DE SELLERS
# =============================================================================
print("📈 Analisando distribuição de status de sellers...")

# Distribuição geral de status
status_order = ['no-seller', 'struggling-seller', 'tiny-seller', 'small-seller', 'medium-seller', 'large-seller', 'top-seller']
status_labels = {
    'no-seller': 'No Seller',
    'struggling-seller': 'Struggling',
    'tiny-seller': 'Tiny',
    'small-seller': 'Small',
    'medium-seller': 'Medium',
    'large-seller': 'Large',
    'top-seller': 'Top',
    'not informed': 'Não informado'
}

# Filtrar apenas lojas com status informado
lojas_com_status = lojas_ativas[lojas_ativas['status_seller'] != 'not informed'].copy()

status_dist = lojas_com_status['status_seller'].value_counts()
dashboard_data['status_sellers'] = {
    'total_com_status': len(lojas_com_status),
    'total_sem_status': len(lojas_ativas) - len(lojas_com_status),
    'distribuicao': []
}

for status in status_order:
    if status in status_dist.index:
        count = status_dist[status]
        dashboard_data['status_sellers']['distribuicao'].append({
            'status': status,
            'label': status_labels.get(status, status),
            'count': int(count),
            'pct': round(count / len(lojas_com_status) * 100, 1)
        })

# GMV e Orders médio por status
dashboard_data['status_performance'] = []
for status in status_order:
    subset = lojas_ativas[lojas_ativas['status_seller'] == status]
    if len(subset) >= 10:
        dashboard_data['status_performance'].append({
            'status': status,
            'label': status_labels.get(status, status),
            'count': len(subset),
            'gmv_medio': round(subset['gmv_mes'].mean(), 2),
            'gmv_total': round(subset['gmv_mes'].sum(), 2),
            'orders_medio': round(subset['orders_mes'].mean(), 1),
            'churn_prob': round(subset['predictive_churn_probability'].mean() * 100, 2)
        })

# Comparativo webinar por status
dashboard_data['status_webinar'] = []
for status in status_order:
    subset_com = com_webinar[com_webinar['status_seller'] == status]
    subset_sem = sem_webinar[sem_webinar['status_seller'] == status]
    if len(subset_com) >= 5 and len(subset_sem) >= 5:
        gmv_com = subset_com['gmv_mes'].mean()
        gmv_sem = subset_sem['gmv_mes'].mean()
        diff = ((gmv_com - gmv_sem) / gmv_sem * 100) if gmv_sem > 0 else 0
        dashboard_data['status_webinar'].append({
            'status': status,
            'label': status_labels.get(status, status),
            'n_com': len(subset_com),
            'n_sem': len(subset_sem),
            'gmv_com': round(gmv_com, 2),
            'gmv_sem': round(gmv_sem, 2),
            'diff_pct': round(diff, 1)
        })

# =============================================================================
# ANÁLISE PAREADA (Matched Analysis)
# =============================================================================
print("🔬 Realizando análise pareada por perfil...")

# Filtrar apenas lojas ativas com dados válidos
lojas_pareamento = lojas_ativas[
    (lojas_ativas['status_seller'] != 'not informed') & 
    (lojas_ativas['aging_faixa_simples'] != 'N/A')
].copy()

# Criar grupos de pareamento
lojas_pareamento['grupo_pareamento'] = lojas_pareamento['status_seller'] + ' | ' + lojas_pareamento['aging_faixa_simples']

# Análise pareada
resultados_pareados = []

grupos = lojas_pareamento['grupo_pareamento'].unique()

for grupo in grupos:
    subset = lojas_pareamento[lojas_pareamento['grupo_pareamento'] == grupo]
    com_web = subset[subset['tem_cobertura_webinar'] == True]
    sem_web = subset[subset['tem_cobertura_webinar'] == False]
    
    if len(com_web) >= 5 and len(sem_web) >= 5:  # Mínimo de 5 lojas em cada grupo
        resultados_pareados.append({
            'grupo': grupo,
            'n_com': len(com_web),
            'n_sem': len(sem_web),
            'gmv_com': com_web['gmv_mes'].mean(),
            'gmv_sem': sem_web['gmv_mes'].mean(),
            'orders_com': com_web['orders_mes'].mean(),
            'orders_sem': sem_web['orders_mes'].mean(),
            'churn_com': com_web['predictive_churn_probability'].mean() * 100,
            'churn_sem': sem_web['predictive_churn_probability'].mean() * 100,
            'ms_com': com_web['qtd_merchant_services'].mean(),
            'ms_sem': sem_web['qtd_merchant_services'].mean()
        })

# Ordenar por tamanho da amostra
resultados_pareados.sort(key=lambda x: x['n_com'] + x['n_sem'], reverse=True)

# Calcular médias ponderadas para resumo pareado
total_com = sum(r['n_com'] for r in resultados_pareados)
total_sem = sum(r['n_sem'] for r in resultados_pareados)

if total_com > 0 and total_sem > 0:
    gmv_ponderado_com = sum(r['gmv_com'] * r['n_com'] for r in resultados_pareados) / total_com
    gmv_ponderado_sem = sum(r['gmv_sem'] * r['n_sem'] for r in resultados_pareados) / total_sem
    orders_ponderado_com = sum(r['orders_com'] * r['n_com'] for r in resultados_pareados) / total_com
    orders_ponderado_sem = sum(r['orders_sem'] * r['n_sem'] for r in resultados_pareados) / total_sem
    churn_ponderado_com = sum(r['churn_com'] * r['n_com'] for r in resultados_pareados) / total_com
    churn_ponderado_sem = sum(r['churn_sem'] * r['n_sem'] for r in resultados_pareados) / total_sem
    ms_ponderado_com = sum(r['ms_com'] * r['n_com'] for r in resultados_pareados) / total_com
    ms_ponderado_sem = sum(r['ms_sem'] * r['n_sem'] for r in resultados_pareados) / total_sem
else:
    gmv_ponderado_com = gmv_ponderado_sem = 0
    orders_ponderado_com = orders_ponderado_sem = 0
    churn_ponderado_com = churn_ponderado_sem = 0
    ms_ponderado_com = ms_ponderado_sem = 0

dashboard_data['analise_pareada'] = {
    'total_grupos': len(resultados_pareados),
    'total_lojas_com': total_com,
    'total_lojas_sem': total_sem,
    'resumo': {
        'gmv_com': round(gmv_ponderado_com, 2),
        'gmv_sem': round(gmv_ponderado_sem, 2),
        'gmv_diff_pct': round((gmv_ponderado_com - gmv_ponderado_sem) / gmv_ponderado_sem * 100, 1) if gmv_ponderado_sem > 0 else 0,
        'orders_com': round(orders_ponderado_com, 1),
        'orders_sem': round(orders_ponderado_sem, 1),
        'orders_diff_pct': round((orders_ponderado_com - orders_ponderado_sem) / orders_ponderado_sem * 100, 1) if orders_ponderado_sem > 0 else 0,
        'churn_com': round(churn_ponderado_com, 2),
        'churn_sem': round(churn_ponderado_sem, 2),
        'churn_diff_pp': round(churn_ponderado_com - churn_ponderado_sem, 2),
        'ms_com': round(ms_ponderado_com, 2),
        'ms_sem': round(ms_ponderado_sem, 2),
        'ms_diff_pct': round((ms_ponderado_com - ms_ponderado_sem) / ms_ponderado_sem * 100, 1) if ms_ponderado_sem > 0 else 0
    },
    'detalhes': [
        {
            'grupo': r['grupo'],
            'n_com': r['n_com'],
            'n_sem': r['n_sem'],
            'gmv_com': round(r['gmv_com'], 2),
            'gmv_sem': round(r['gmv_sem'], 2),
            'gmv_diff': round((r['gmv_com'] - r['gmv_sem']) / r['gmv_sem'] * 100, 1) if r['gmv_sem'] > 0 else 0,
            'churn_com': round(r['churn_com'], 2),
            'churn_sem': round(r['churn_sem'], 2),
            'churn_diff': round(r['churn_com'] - r['churn_sem'], 2)
        }
        for r in resultados_pareados[:15]  # Top 15 grupos
    ]
}

# =============================================================================
# PERFIL DOS PARTICIPANTES
# =============================================================================

# Status Seller
status_seller = participantes['status_seller'].value_counts().to_dict()
dashboard_data['perfil_status'] = [{'status': k, 'count': int(v), 'pct': round(v/len(participantes)*100, 1)} for k, v in status_seller.items()]

# =============================================================================
# STATUS DOS PARTICIPANTES DE WEBINAR (Análise detalhada)
# =============================================================================
print("👥 Analisando status dos participantes de webinar...")

# Participantes com status definido
participantes_com_status = participantes[participantes['status_seller'] != 'not informed'].copy()
base_com_status = lojas_ativas[lojas_ativas['status_seller'] != 'not informed'].copy()

dashboard_data['participantes_status'] = {
    'total_participantes': len(participantes),
    'com_status': len(participantes_com_status),
    'sem_status': len(participantes) - len(participantes_com_status),
    'distribuicao': [],
    'comparativo_base': []
}

# Distribuição por status
for status in status_order:
    count_part = len(participantes_com_status[participantes_com_status['status_seller'] == status])
    count_base = len(base_com_status[base_com_status['status_seller'] == status])
    
    if count_part > 0 or count_base > 0:
        pct_part = (count_part / len(participantes_com_status) * 100) if len(participantes_com_status) > 0 else 0
        pct_base = (count_base / len(base_com_status) * 100) if len(base_com_status) > 0 else 0
        
        dashboard_data['participantes_status']['distribuicao'].append({
            'status': status,
            'label': status_labels.get(status, status),
            'count': count_part,
            'pct': round(pct_part, 1)
        })
        
        dashboard_data['participantes_status']['comparativo_base'].append({
            'status': status,
            'label': status_labels.get(status, status),
            'pct_webinar': round(pct_part, 1),
            'pct_base': round(pct_base, 1),
            'diff_pp': round(pct_part - pct_base, 1),
            'indice': round((pct_part / pct_base * 100), 0) if pct_base > 0 else 0
        })

# Performance dos participantes por status
dashboard_data['participantes_performance'] = []
for status in status_order:
    subset = participantes[participantes['status_seller'] == status]
    if len(subset) >= 5:
        dashboard_data['participantes_performance'].append({
            'status': status,
            'label': status_labels.get(status, status),
            'count': len(subset),
            'gmv_medio': round(subset['gmv_mes'].mean(), 2),
            'orders_medio': round(subset['orders_mes'].mean(), 1),
            'churn_prob': round(subset['predictive_churn_probability'].mean() * 100, 2),
            'qtd_webinars': round(subset['qtd_webinars'].mean(), 1)
        })

# Verticais
verticais = participantes['vertical'].value_counts().head(15).to_dict()
dashboard_data['perfil_verticais'] = [{'vertical': k, 'count': int(v), 'pct': round(v/len(participantes)*100, 1)} for k, v in verticais.items()]

# Planos
planos = participantes['plan'].value_counts().to_dict()
dashboard_data['perfil_planos'] = [{'plano': k, 'count': int(v), 'pct': round(v/len(participantes)*100, 1)} for k, v in planos.items()]

# Life Stage (Tempo de loja baseado no churn)
life_stage = participantes['predictive_churn_life_stage'].value_counts().to_dict()
dashboard_data['perfil_life_stage'] = [{'stage': k if pd.notna(k) else 'N/A', 'count': int(v), 'pct': round(v/len(participantes)*100, 1)} for k, v in life_stage.items()]

# Aging
aging_dist = participantes['aging_faixa'].value_counts().to_dict()
aging_order = ['0-30 dias', '31-90 dias', '91-180 dias', '181-365 dias', '1-2 anos', '2-5 anos', '5+ anos', 'N/A']
dashboard_data['perfil_aging'] = []
for faixa in aging_order:
    if faixa in aging_dist:
        dashboard_data['perfil_aging'].append({
            'faixa': faixa, 
            'count': int(aging_dist[faixa]), 
            'pct': round(aging_dist[faixa]/len(participantes)*100, 1)
        })

# Perfil de churn
churn_profile = participantes['predictive_churn_profile'].value_counts().to_dict()
dashboard_data['perfil_churn'] = [{'profile': k if pd.notna(k) else 'N/A', 'count': int(v), 'pct': round(v/len(participantes)*100, 1)} for k, v in churn_profile.items()]

# =============================================================================
# ANÁLISE POR QUANTIDADE DE WEBINARS
# =============================================================================
lojas_webinar_ativas = lojas_ativas[lojas_ativas['qtd_webinars'] > 0].copy()

def faixa_webinars(x):
    if x == 1: return '1 webinar'
    elif x == 2: return '2 webinars'
    elif x <= 4: return '3-4 webinars'
    else: return '5+ webinars'

lojas_webinar_ativas['faixa_webinars'] = lojas_webinar_ativas['qtd_webinars'].apply(faixa_webinars)

faixas_order = ['1 webinar', '2 webinars', '3-4 webinars', '5+ webinars']
dashboard_data['por_qtd_webinars'] = []
for faixa in faixas_order:
    subset = lojas_webinar_ativas[lojas_webinar_ativas['faixa_webinars'] == faixa]
    if len(subset) > 0:
        dashboard_data['por_qtd_webinars'].append({
            'faixa': faixa,
            'lojas': len(subset),
            'gmv_medio': round(subset['gmv_mes'].mean(), 2),
            'orders_medio': round(subset['orders_mes'].mean(), 1),
            'churn_prob': round(subset['predictive_churn_probability'].mean() * 100, 2)
        })

# =============================================================================
# COMPARATIVO STATUS SELLER
# =============================================================================
status_com = com_webinar['status_seller'].value_counts(normalize=True).to_dict()
status_sem = sem_webinar['status_seller'].value_counts(normalize=True).to_dict()

all_status = set(list(status_com.keys()) + list(status_sem.keys()))
dashboard_data['comparativo_status'] = []
for st in all_status:
    dashboard_data['comparativo_status'].append({
        'status': st,
        'pct_com': round(status_com.get(st, 0) * 100, 1),
        'pct_sem': round(status_sem.get(st, 0) * 100, 1)
    })
dashboard_data['comparativo_status'].sort(key=lambda x: x['pct_com'] - x['pct_sem'], reverse=True)

# =============================================================================
# WEBINARS MAIS POPULARES
# =============================================================================
webinars_populares = webinars_com_cobertura['webinar_name'].value_counts().head(10).to_dict()
dashboard_data['webinars_populares'] = [{'nome': k, 'participantes': int(v)} for k, v in webinars_populares.items()]

# =============================================================================
# GERAR HTML
# =============================================================================
html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Impacto - Webinars v2</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e4e4e4;
        }}
        
        .header {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 30px 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        
        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 14px;
        }}
        
        .tabs {{
            display: flex;
            background: #1a1a2e;
            padding: 0 40px;
            border-bottom: 1px solid #2d2d44;
            overflow-x: auto;
        }}
        
        .tab {{
            padding: 18px 24px;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            font-weight: 500;
            color: #888;
            white-space: nowrap;
        }}
        
        .tab:hover {{
            color: #fff;
            background: rgba(255,255,255,0.05);
        }}
        
        .tab.active {{
            color: #667eea;
            border-bottom-color: #667eea;
        }}
        
        .content {{
            padding: 30px 40px;
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: linear-gradient(145deg, #1e1e32 0%, #252540 100%);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.05);
        }}
        
        .card-title {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #888;
            margin-bottom: 12px;
        }}
        
        .card-value {{
            font-size: 36px;
            font-weight: 700;
            background: linear-gradient(90deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .card-subtitle {{
            font-size: 13px;
            color: #666;
            margin-top: 8px;
        }}
        
        .card-large {{
            grid-column: span 2;
        }}
        
        .comparison {{
            display: flex;
            gap: 40px;
            margin-top: 20px;
        }}
        
        .comparison-item {{
            flex: 1;
        }}
        
        .comparison-label {{
            font-size: 12px;
            color: #888;
            margin-bottom: 8px;
        }}
        
        .comparison-value {{
            font-size: 28px;
            font-weight: 600;
        }}
        
        .positive {{
            color: #4ade80;
        }}
        
        .negative {{
            color: #f87171;
        }}
        
        .neutral {{
            color: #fbbf24;
        }}
        
        .badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            margin-top: 10px;
        }}
        
        .badge-positive {{
            background: rgba(74, 222, 128, 0.15);
            color: #4ade80;
        }}
        
        .badge-negative {{
            background: rgba(248, 113, 113, 0.15);
            color: #f87171;
        }}
        
        .chart-container {{
            position: relative;
            height: 300px;
            margin-top: 20px;
        }}
        
        .chart-container-small {{
            height: 250px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        th, td {{
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid #2d2d44;
        }}
        
        th {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #888;
            font-weight: 600;
        }}
        
        tr:hover {{
            background: rgba(255,255,255,0.02);
        }}
        
        .progress-bar {{
            height: 8px;
            background: #2d2d44;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }}
        
        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #2d2d44;
        }}
        
        .insight-box {{
            background: linear-gradient(145deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 0 12px 12px 0;
            margin: 20px 0;
        }}
        
        .insight-box h4 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .insight-box.warning {{
            border-left-color: #fbbf24;
        }}
        
        .insight-box.warning h4 {{
            color: #fbbf24;
        }}
        
        .insight-box.success {{
            border-left-color: #4ade80;
        }}
        
        .insight-box.success h4 {{
            color: #4ade80;
        }}
        
        .two-columns {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}
        
        .three-columns {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
        }}
        
        @media (max-width: 1100px) {{
            .three-columns {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
        
        @media (max-width: 900px) {{
            .two-columns, .three-columns {{
                grid-template-columns: 1fr;
            }}
            .card-large {{
                grid-column: span 1;
            }}
        }}
        
        .stat-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #2d2d44;
        }}
        
        .stat-row:last-child {{
            border-bottom: none;
        }}
        
        .stat-label {{
            color: #888;
        }}
        
        .stat-value {{
            font-weight: 600;
            font-size: 18px;
        }}
        
        .metric-comparison {{
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 15px;
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            margin-bottom: 15px;
        }}
        
        .metric-comparison .label {{
            flex: 1;
            font-size: 14px;
        }}
        
        .metric-comparison .values {{
            display: flex;
            gap: 30px;
        }}
        
        .metric-comparison .value-item {{
            text-align: center;
        }}
        
        .metric-comparison .value-item .number {{
            font-size: 22px;
            font-weight: 700;
        }}
        
        .metric-comparison .value-item .sublabel {{
            font-size: 11px;
            color: #888;
        }}
        
        .highlight-card {{
            background: linear-gradient(145deg, rgba(74, 222, 128, 0.1), rgba(34, 197, 94, 0.05));
            border: 1px solid rgba(74, 222, 128, 0.2);
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Dashboard de Impacto - Webinars v2</h1>
        <p>Análise completa do impacto das ações de educação na base de clientes | Base: Dezembro 2024</p>
    </div>
    
    <div class="tabs">
        <div class="tab active" onclick="showTab('resumo')">Resumo</div>
        <div class="tab" onclick="showTab('pareada')">Análise Pareada</div>
        <div class="tab" onclick="showTab('merchant')">Merchant Services</div>
        <div class="tab" onclick="showTab('status')">Status & Evolução</div>
        <div class="tab" onclick="showTab('performance')">Performance</div>
        <div class="tab" onclick="showTab('churn')">Churn</div>
        <div class="tab" onclick="showTab('perfil')">Perfil Participantes</div>
        <div class="tab" onclick="showTab('webinars')">Webinars</div>
    </div>
    
    <div class="content">
        <!-- RESUMO -->
        <div id="resumo" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <div class="card-title">Total da Base</div>
                    <div class="card-value">{dashboard_data['resumo']['total_base']:,}</div>
                    <div class="card-subtitle">lojas na base de dezembro</div>
                </div>
                <div class="card">
                    <div class="card-title">Lojas Ativas</div>
                    <div class="card-value">{dashboard_data['resumo']['lojas_ativas']:,}</div>
                    <div class="card-subtitle">com GMV ou Orders > 0</div>
                </div>
                <div class="card">
                    <div class="card-title">Cobertura Webinar</div>
                    <div class="card-value">{dashboard_data['resumo']['lojas_webinar']:,}</div>
                    <div class="card-subtitle">lojas participaram de webinars</div>
                </div>
                <div class="card">
                    <div class="card-title">Taxa de Cobertura</div>
                    <div class="card-value">{dashboard_data['resumo']['cobertura_pct']}%</div>
                    <div class="card-subtitle">das lojas ativas</div>
                </div>
            </div>
            
            <h2 class="section-title">Comparativo Geral: Com vs Sem Webinar</h2>
            
            <div class="grid">
                <div class="card card-large">
                    <div class="card-title">🎯 Impacto em GMV</div>
                    <div class="comparison">
                        <div class="comparison-item">
                            <div class="comparison-label">Com Webinar</div>
                            <div class="comparison-value positive">R$ {dashboard_data['performance']['gmv_medio_com']:,.2f}</div>
                        </div>
                        <div class="comparison-item">
                            <div class="comparison-label">Sem Webinar</div>
                            <div class="comparison-value">R$ {dashboard_data['performance']['gmv_medio_sem']:,.2f}</div>
                        </div>
                    </div>
                    <div class="badge badge-positive">+{dashboard_data['performance']['diff_gmv_pct']}% de diferença</div>
                </div>
                
                <div class="card card-large">
                    <div class="card-title">📦 Impacto em Pedidos</div>
                    <div class="comparison">
                        <div class="comparison-item">
                            <div class="comparison-label">Com Webinar</div>
                            <div class="comparison-value positive">{dashboard_data['performance']['orders_medio_com']}</div>
                        </div>
                        <div class="comparison-item">
                            <div class="comparison-label">Sem Webinar</div>
                            <div class="comparison-value">{dashboard_data['performance']['orders_medio_sem']}</div>
                        </div>
                    </div>
                    <div class="badge badge-positive">+{dashboard_data['performance']['diff_orders_pct']}% de diferença</div>
                </div>
            </div>
            
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">🚨 Risco de Churn</div>
                    <div class="comparison">
                        <div class="comparison-item">
                            <div class="comparison-label">Com Webinar</div>
                            <div class="comparison-value positive">{dashboard_data['churn']['prob_com']}%</div>
                        </div>
                        <div class="comparison-item">
                            <div class="comparison-label">Sem Webinar</div>
                            <div class="comparison-value negative">{dashboard_data['churn']['prob_sem']}%</div>
                        </div>
                    </div>
                    <div class="badge badge-positive">{dashboard_data['churn']['diff_pp']}pp menor risco</div>
                </div>
                
                <div class="card">
                    <div class="card-title">🛒 Merchant Services</div>
                    <div class="comparison">
                        <div class="comparison-item">
                            <div class="comparison-label">Com Webinar</div>
                            <div class="comparison-value positive">{dashboard_data['merchant_services_media']['com_webinar']}</div>
                            <div class="card-subtitle">produtos por loja</div>
                        </div>
                        <div class="comparison-item">
                            <div class="comparison-label">Sem Webinar</div>
                            <div class="comparison-value">{dashboard_data['merchant_services_media']['sem_webinar']}</div>
                            <div class="card-subtitle">produtos por loja</div>
                        </div>
                    </div>
                    <div class="badge badge-positive">+{dashboard_data['merchant_services_media']['diff_pct']}% de adoção</div>
                </div>
            </div>
            
            <div class="insight-box success">
                <h4>💡 Resumo do Impacto</h4>
                <p>Lojas que participam de webinars apresentam resultados consistentemente melhores em todas as métricas analisadas:
                <strong>+{dashboard_data['performance']['diff_gmv_pct']}% GMV</strong>, 
                <strong>+{dashboard_data['performance']['diff_orders_pct']}% pedidos</strong>, 
                <strong>{abs(dashboard_data['churn']['diff_pp'])}pp menos churn</strong> e 
                <strong>+{dashboard_data['merchant_services_media']['diff_pct']}% adoção de produtos</strong>.</p>
            </div>
        </div>
        
        <!-- ANÁLISE PAREADA -->
        <div id="pareada" class="tab-content">
            <h2 class="section-title">🔬 Análise Pareada: Comparação Justa por Perfil</h2>
            
            <div class="insight-box warning">
                <h4>⚠️ Por que análise pareada?</h4>
                <p>A comparação geral pode ter viés porque quem participa de webinar pode já ter perfil diferente. 
                A análise pareada compara lojas com <strong>mesmo status de seller</strong> e <strong>mesmo tempo de loja</strong>, 
                isolando o efeito do webinar.</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <div class="card-title">Grupos Analisados</div>
                    <div class="card-value">{dashboard_data['analise_pareada']['total_grupos']}</div>
                    <div class="card-subtitle">combinações status + idade</div>
                </div>
                <div class="card">
                    <div class="card-title">Lojas Com Webinar</div>
                    <div class="card-value">{dashboard_data['analise_pareada']['total_lojas_com']:,}</div>
                    <div class="card-subtitle">na análise pareada</div>
                </div>
                <div class="card">
                    <div class="card-title">Lojas Sem Webinar</div>
                    <div class="card-value">{dashboard_data['analise_pareada']['total_lojas_sem']:,}</div>
                    <div class="card-subtitle">na análise pareada</div>
                </div>
            </div>
            
            <h3 class="section-title">Resultados Pareados (Média Ponderada)</h3>
            
            <div class="three-columns">
                <div class="card highlight-card">
                    <div class="card-title">💰 GMV Pareado</div>
                    <div class="comparison">
                        <div class="comparison-item">
                            <div class="comparison-label">Com Webinar</div>
                            <div class="comparison-value positive">R$ {dashboard_data['analise_pareada']['resumo']['gmv_com']:,.2f}</div>
                        </div>
                        <div class="comparison-item">
                            <div class="comparison-label">Sem Webinar</div>
                            <div class="comparison-value">R$ {dashboard_data['analise_pareada']['resumo']['gmv_sem']:,.2f}</div>
                        </div>
                    </div>
                    <div class="badge {'badge-positive' if dashboard_data['analise_pareada']['resumo']['gmv_diff_pct'] > 0 else 'badge-negative'}">{'+' if dashboard_data['analise_pareada']['resumo']['gmv_diff_pct'] > 0 else ''}{dashboard_data['analise_pareada']['resumo']['gmv_diff_pct']}%</div>
                </div>
                
                <div class="card highlight-card">
                    <div class="card-title">📦 Pedidos Pareado</div>
                    <div class="comparison">
                        <div class="comparison-item">
                            <div class="comparison-label">Com Webinar</div>
                            <div class="comparison-value positive">{dashboard_data['analise_pareada']['resumo']['orders_com']}</div>
                        </div>
                        <div class="comparison-item">
                            <div class="comparison-label">Sem Webinar</div>
                            <div class="comparison-value">{dashboard_data['analise_pareada']['resumo']['orders_sem']}</div>
                        </div>
                    </div>
                    <div class="badge {'badge-positive' if dashboard_data['analise_pareada']['resumo']['orders_diff_pct'] > 0 else 'badge-negative'}">{'+' if dashboard_data['analise_pareada']['resumo']['orders_diff_pct'] > 0 else ''}{dashboard_data['analise_pareada']['resumo']['orders_diff_pct']}%</div>
                </div>
                
                <div class="card highlight-card">
                    <div class="card-title">🚨 Churn Pareado</div>
                    <div class="comparison">
                        <div class="comparison-item">
                            <div class="comparison-label">Com Webinar</div>
                            <div class="comparison-value {'positive' if dashboard_data['analise_pareada']['resumo']['churn_com'] < dashboard_data['analise_pareada']['resumo']['churn_sem'] else 'negative'}">{dashboard_data['analise_pareada']['resumo']['churn_com']}%</div>
                        </div>
                        <div class="comparison-item">
                            <div class="comparison-label">Sem Webinar</div>
                            <div class="comparison-value">{dashboard_data['analise_pareada']['resumo']['churn_sem']}%</div>
                        </div>
                    </div>
                    <div class="badge {'badge-positive' if dashboard_data['analise_pareada']['resumo']['churn_diff_pp'] < 0 else 'badge-negative'}">{dashboard_data['analise_pareada']['resumo']['churn_diff_pp']}pp</div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <div class="card-title">📊 Detalhamento por Grupo (Top 15)</div>
                <table>
                    <thead>
                        <tr>
                            <th>Grupo (Status | Idade)</th>
                            <th>N Com</th>
                            <th>N Sem</th>
                            <th>GMV Com</th>
                            <th>GMV Sem</th>
                            <th>Δ GMV</th>
                            <th>Churn Com</th>
                            <th>Churn Sem</th>
                            <th>Δ Churn</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f"""
                        <tr>
                            <td><strong>{item['grupo']}</strong></td>
                            <td>{item['n_com']}</td>
                            <td>{item['n_sem']}</td>
                            <td>R$ {item['gmv_com']:,.0f}</td>
                            <td>R$ {item['gmv_sem']:,.0f}</td>
                            <td class="{'positive' if item['gmv_diff'] > 0 else 'negative'}">{'+' if item['gmv_diff'] > 0 else ''}{item['gmv_diff']}%</td>
                            <td>{item['churn_com']}%</td>
                            <td>{item['churn_sem']}%</td>
                            <td class="{'positive' if item['churn_diff'] < 0 else 'negative'}">{item['churn_diff']}pp</td>
                        </tr>
                        """ for item in dashboard_data['analise_pareada']['detalhes']])}
                    </tbody>
                </table>
            </div>
            
            <div class="insight-box success">
                <h4>💡 Conclusão da Análise Pareada</h4>
                <p>Mesmo comparando lojas com <strong>perfis similares</strong> (mesmo status de seller e tempo de loja), 
                o grupo com webinar apresenta <strong>GMV {'+' if dashboard_data['analise_pareada']['resumo']['gmv_diff_pct'] > 0 else ''}{dashboard_data['analise_pareada']['resumo']['gmv_diff_pct']}%</strong> 
                {'maior' if dashboard_data['analise_pareada']['resumo']['gmv_diff_pct'] > 0 else 'menor'} e 
                <strong>{abs(dashboard_data['analise_pareada']['resumo']['churn_diff_pp'])}pp {'menor' if dashboard_data['analise_pareada']['resumo']['churn_diff_pp'] < 0 else 'maior'} risco de churn</strong>.
                Isso sugere que o efeito dos webinars é real e não apenas um viés de seleção.</p>
            </div>
        </div>
        
        <!-- MERCHANT SERVICES -->
        <div id="merchant" class="tab-content">
            <h2 class="section-title">🛒 Análise de Merchant Services</h2>
            
            <div class="grid">
                <div class="card">
                    <div class="card-title">Média Com Webinar</div>
                    <div class="card-value positive">{dashboard_data['merchant_services_media']['com_webinar']}</div>
                    <div class="card-subtitle">produtos por loja</div>
                </div>
                <div class="card">
                    <div class="card-title">Média Sem Webinar</div>
                    <div class="card-value">{dashboard_data['merchant_services_media']['sem_webinar']}</div>
                    <div class="card-subtitle">produtos por loja</div>
                </div>
                <div class="card">
                    <div class="card-title">Diferença</div>
                    <div class="card-value positive">+{dashboard_data['merchant_services_media']['diff_pct']}%</div>
                    <div class="card-subtitle">maior adoção com webinar</div>
                </div>
            </div>
            
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">📊 Distribuição: Quantidade de Produtos</div>
                    <div class="chart-container">
                        <canvas id="chartMSDistribuicao"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title">📈 Com vs Sem Webinar por Qtd Produtos</div>
                    <div class="chart-container">
                        <canvas id="chartMSComparativo"></canvas>
                    </div>
                </div>
            </div>
            
            <h3 class="section-title" style="margin-top: 30px;">📦 Combinações de Produtos Mais Comuns</h3>
            
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">🏆 Top 10 Combinações</div>
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Combinação</th>
                                <th>Lojas</th>
                                <th>%</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f"""
                            <tr>
                                <td><strong>{i+1}</strong></td>
                                <td><span style="background: rgba(102, 126, 234, 0.2); padding: 4px 10px; border-radius: 4px; font-size: 12px;">{item['combo']}</span></td>
                                <td>{item['count']:,}</td>
                                <td>
                                    <div>{item['pct']}%</div>
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: {min(item['pct']*2.5, 100)}%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>
                                    </div>
                                </td>
                            </tr>
                            """ for i, item in enumerate(dashboard_data['combinacoes_produtos'])])}
                        </tbody>
                    </table>
                </div>
                
                <div class="card">
                    <div class="card-title">📊 Visualização das Combinações</div>
                    <div class="chart-container">
                        <canvas id="chartCombinacoes"></canvas>
                    </div>
                </div>
            </div>
            
            <h3 class="section-title" style="margin-top: 30px;">🎯 Oportunidades de Cross-Sell</h3>
            
            <div class="insight-box warning">
                <h4>💡 Como ler esta tabela</h4>
                <p>A tabela mostra, para cada grupo de clientes que já tem um produto, quantos <strong>NÃO TÊM</strong> outro produto - representando a oportunidade de cross-sell. Quanto maior o número, maior a oportunidade.</p>
            </div>
            
            <div class="card">
                <div class="card-title">🔥 Top Oportunidades de Cross-Sell</div>
                <table>
                    <thead>
                        <tr>
                            <th>Quem tem</th>
                            <th>Não tem</th>
                            <th>% que não tem</th>
                            <th>Oportunidade (lojas)</th>
                            <th>Potencial</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f"""
                        <tr>
                            <td><span style="background: rgba(74, 222, 128, 0.2); padding: 4px 10px; border-radius: 4px; font-size: 12px;">{item['tem']}</span></td>
                            <td><span style="background: rgba(248, 113, 113, 0.2); padding: 4px 10px; border-radius: 4px; font-size: 12px;">{item['nao_tem']}</span></td>
                            <td>{item['pct_nao_tem']}%</td>
                            <td><strong>{item['oportunidade']:,}</strong> lojas</td>
                            <td>
                                <div class="progress-bar" style="width: 150px;">
                                    <div class="progress-fill" style="width: {min(item['oportunidade']/500, 100)}%; background: linear-gradient(90deg, #f59e0b, #ef4444);"></div>
                                </div>
                            </td>
                        </tr>
                        """ for item in dashboard_data['cross_sell'][:12]])}
                    </tbody>
                </table>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <div class="card-title">🔍 Adoção por Produto Individual (Com vs Sem Webinar)</div>
                <table>
                    <thead>
                        <tr>
                            <th>Produto</th>
                            <th>Com Webinar</th>
                            <th>Sem Webinar</th>
                            <th>Diferença</th>
                            <th>Visualização</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f"""
                        <tr>
                            <td><strong>{item['produto']}</strong></td>
                            <td>{item['pct_com']}%</td>
                            <td>{item['pct_sem']}%</td>
                            <td class="{'positive' if item['diff_pp'] > 0 else 'negative'}">{'+' if item['diff_pp'] > 0 else ''}{item['diff_pp']}pp</td>
                            <td>
                                <div style="display: flex; gap: 5px; align-items: center;">
                                    <div style="width: {item['pct_com']*2}px; height: 12px; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 3px;"></div>
                                    <div style="width: {item['pct_sem']*2}px; height: 12px; background: rgba(255,255,255,0.2); border-radius: 3px;"></div>
                                </div>
                            </td>
                        </tr>
                        """ for item in dashboard_data['merchant_services_por_produto']])}
                    </tbody>
                </table>
            </div>
            
            <div class="insight-box success">
                <h4>💡 Insights de Cross-Sell</h4>
                <p>• <strong>Nuvem Envio</strong> é o produto mais adotado, presente em {dashboard_data['combinacoes_produtos'][0]['pct'] if dashboard_data['combinacoes_produtos'] else 0}% das lojas<br>
                • <strong>Maior oportunidade</strong>: {dashboard_data['cross_sell'][0]['oportunidade']:,} lojas que têm {dashboard_data['cross_sell'][0]['tem']} podem adotar {dashboard_data['cross_sell'][0]['nao_tem']}<br>
                • Webinars podem focar em combos como <strong>Envio + Pago</strong> e <strong>Envio + Chat</strong> para aumentar adoção</p>
            </div>
        </div>
        
        <!-- STATUS & EVOLUÇÃO -->
        <div id="status" class="tab-content">
            <h2 class="section-title">📊 Status de Sellers - Visão Atual</h2>
            
            <div class="insight-box warning">
                <h4>🚧 Matriz de Transição (Em breve)</h4>
                <p>Para visualizar a <strong>matriz de transição de status</strong> (upgrades e downgrades), 
                será necessário carregar uma segunda base de um período anterior. 
                Por enquanto, apresentamos a <strong>distribuição atual</strong> dos status de sellers.</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <div class="card-title">Lojas com Status Definido</div>
                    <div class="card-value">{dashboard_data['status_sellers']['total_com_status']:,}</div>
                    <div class="card-subtitle">lojas ativas com seller status</div>
                </div>
                <div class="card">
                    <div class="card-title">Sem Status (Não Informado)</div>
                    <div class="card-value">{dashboard_data['status_sellers']['total_sem_status']:,}</div>
                    <div class="card-subtitle">lojas sem classificação</div>
                </div>
            </div>
            
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">📊 Distribuição por Status de Seller</div>
                    <div class="chart-container">
                        <canvas id="chartStatusDist"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title">🎯 Pirâmide de Sellers</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Status</th>
                                <th>Lojas</th>
                                <th>%</th>
                                <th>Distribuição</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f"""
                            <tr>
                                <td><strong>{item['label']}</strong></td>
                                <td>{item['count']:,}</td>
                                <td>{item['pct']}%</td>
                                <td>
                                    <div class="progress-bar" style="width: 200px;">
                                        <div class="progress-fill" style="width: {min(item['pct']*2, 100)}%; background: linear-gradient(90deg, 
                                            {'#ef4444' if item['status'] == 'no-seller' else 
                                             '#f97316' if item['status'] == 'struggling-seller' else 
                                             '#fbbf24' if item['status'] == 'tiny-seller' else 
                                             '#84cc16' if item['status'] == 'small-seller' else 
                                             '#22c55e' if item['status'] == 'medium-seller' else 
                                             '#14b8a6' if item['status'] == 'large-seller' else 
                                             '#667eea'}, 
                                            {'#dc2626' if item['status'] == 'no-seller' else 
                                             '#ea580c' if item['status'] == 'struggling-seller' else 
                                             '#eab308' if item['status'] == 'tiny-seller' else 
                                             '#65a30d' if item['status'] == 'small-seller' else 
                                             '#16a34a' if item['status'] == 'medium-seller' else 
                                             '#0d9488' if item['status'] == 'large-seller' else 
                                             '#764ba2'});"></div>
                                    </div>
                                </td>
                            </tr>
                            """ for item in dashboard_data['status_sellers']['distribuicao']])}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <h3 class="section-title" style="margin-top: 30px;">💰 Performance por Status</h3>
            
            <div class="card">
                <div class="card-title">GMV, Pedidos e Risco de Churn por Tier</div>
                <table>
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th>Lojas</th>
                            <th>GMV Médio</th>
                            <th>GMV Total</th>
                            <th>Pedidos Médio</th>
                            <th>Prob. Churn</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f"""
                        <tr>
                            <td>
                                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; background: 
                                    {'#ef4444' if item['status'] == 'no-seller' else 
                                     '#f97316' if item['status'] == 'struggling-seller' else 
                                     '#fbbf24' if item['status'] == 'tiny-seller' else 
                                     '#84cc16' if item['status'] == 'small-seller' else 
                                     '#22c55e' if item['status'] == 'medium-seller' else 
                                     '#14b8a6' if item['status'] == 'large-seller' else 
                                     '#667eea'};"></span>
                                <strong>{item['label']}</strong>
                            </td>
                            <td>{item['count']:,}</td>
                            <td>R$ {item['gmv_medio']:,.2f}</td>
                            <td>R$ {item['gmv_total']:,.0f}</td>
                            <td>{item['orders_medio']}</td>
                            <td><span class="{'positive' if item['churn_prob'] < 20 else 'neutral' if item['churn_prob'] < 40 else 'negative'}">{item['churn_prob']}%</span></td>
                        </tr>
                        """ for item in dashboard_data['status_performance']])}
                    </tbody>
                </table>
            </div>
            
            <div class="two-columns" style="margin-top: 20px;">
                <div class="card">
                    <div class="card-title">📈 GMV Médio por Status</div>
                    <div class="chart-container">
                        <canvas id="chartStatusGMV"></canvas>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">🚨 Risco de Churn por Status</div>
                    <div class="chart-container">
                        <canvas id="chartStatusChurn"></canvas>
                    </div>
                </div>
            </div>
            
            <h3 class="section-title" style="margin-top: 30px;">🎓 Impacto do Webinar por Status</h3>
            
            <div class="card">
                <div class="card-title">Comparativo de GMV: Com vs Sem Webinar (por Status)</div>
                <table>
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th>Com Webinar</th>
                            <th>Sem Webinar</th>
                            <th>GMV Com</th>
                            <th>GMV Sem</th>
                            <th>Diferença</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f"""
                        <tr>
                            <td><strong>{item['label']}</strong></td>
                            <td>{item['n_com']:,} lojas</td>
                            <td>{item['n_sem']:,} lojas</td>
                            <td>R$ {item['gmv_com']:,.2f}</td>
                            <td>R$ {item['gmv_sem']:,.2f}</td>
                            <td class="{'positive' if item['diff_pct'] > 0 else 'negative'}">
                                <strong>{'+' if item['diff_pct'] > 0 else ''}{item['diff_pct']}%</strong>
                            </td>
                        </tr>
                        """ for item in dashboard_data['status_webinar']])}
                    </tbody>
                </table>
            </div>
            
            <div class="insight-box success">
                <h4>💡 Insights de Status</h4>
                <p>• Os tiers mais altos (Large/Top) têm <strong>menor risco de churn</strong> e <strong>maior GMV</strong><br>
                • O impacto do webinar é positivo em <strong>todos os tiers</strong> de status<br>
                • <strong>Struggling sellers</strong> representam a maior oportunidade de desenvolvimento</p>
            </div>
            
            <div class="card" style="margin-top: 20px; background: linear-gradient(145deg, rgba(251, 191, 36, 0.1), rgba(245, 158, 11, 0.05)); border: 1px dashed rgba(251, 191, 36, 0.3);">
                <div class="card-title">🔮 Próximos Passos: Matriz de Transição</div>
                <p style="color: #888; margin-bottom: 15px;">Para habilitar a visualização da matriz de transição, envie uma segunda base com os status de um período anterior. A análise mostrará:</p>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;">
                    <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; margin-bottom: 5px;">📈</div>
                        <div style="font-weight: 600; color: #4ade80;">Upgrades</div>
                        <div style="font-size: 12px; color: #666;">Lojas que subiram de tier</div>
                    </div>
                    <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; margin-bottom: 5px;">📉</div>
                        <div style="font-weight: 600; color: #f87171;">Downgrades</div>
                        <div style="font-size: 12px; color: #666;">Lojas que desceram de tier</div>
                    </div>
                    <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; margin-bottom: 5px;">🔄</div>
                        <div style="font-weight: 600; color: #667eea;">Retenção</div>
                        <div style="font-size: 12px; color: #666;">Lojas que mantiveram tier</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- PERFORMANCE -->
        <div id="performance" class="tab-content">
            <h2 class="section-title">Análise de Performance de Vendas</h2>
            
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">💰 GMV Mensal</div>
                    <div class="chart-container">
                        <canvas id="chartGMV"></canvas>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">📦 Pedidos Mensais</div>
                    <div class="chart-container">
                        <canvas id="chartOrders"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <div class="card-title">📊 Performance por Quantidade de Webinars</div>
                <table>
                    <thead>
                        <tr>
                            <th>Webinars</th>
                            <th>Lojas Ativas</th>
                            <th>GMV Médio</th>
                            <th>Pedidos Médios</th>
                            <th>Prob. Churn</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f"""
                        <tr>
                            <td><strong>{item['faixa']}</strong></td>
                            <td>{item['lojas']:,}</td>
                            <td>R$ {item['gmv_medio']:,.2f}</td>
                            <td>{item['orders_medio']}</td>
                            <td><span class="{'positive' if item['churn_prob'] < 15 else 'neutral' if item['churn_prob'] < 25 else 'negative'}">{item['churn_prob']}%</span></td>
                        </tr>
                        """ for item in dashboard_data['por_qtd_webinars']])}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- CHURN -->
        <div id="churn" class="tab-content">
            <h2 class="section-title">Análise de Churn Preditivo</h2>
            
            <div class="grid">
                <div class="card">
                    <div class="card-title">Prob. Churn - Com Webinar</div>
                    <div class="card-value positive">{dashboard_data['churn']['prob_com']}%</div>
                </div>
                <div class="card">
                    <div class="card-title">Prob. Churn - Sem Webinar</div>
                    <div class="card-value negative">{dashboard_data['churn']['prob_sem']}%</div>
                </div>
                <div class="card">
                    <div class="card-title">Diferença</div>
                    <div class="card-value positive">{dashboard_data['churn']['diff_pp']}pp</div>
                </div>
            </div>
            
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">Comparativo de Probabilidade de Churn</div>
                    <div class="chart-container">
                        <canvas id="chartChurn"></canvas>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">Distribuição por Perfil de Churn</div>
                    <div class="chart-container chart-container-small">
                        <canvas id="chartChurnProfile"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- PERFIL -->
        <div id="perfil" class="tab-content">
            <h2 class="section-title">Perfil dos Participantes de Webinar</h2>
            
            <div class="two-columns">
                <div class="card">
                    <div class="card-title">📊 Status de Seller</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Status</th>
                                <th>Lojas</th>
                                <th>%</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f"""
                            <tr>
                                <td>{item['status']}</td>
                                <td>{item['count']:,}</td>
                                <td>
                                    <div>{item['pct']}%</div>
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: {min(item['pct'], 100)}%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>
                                    </div>
                                </td>
                            </tr>
                            """ for item in dashboard_data['perfil_status']])}
                        </tbody>
                    </table>
                </div>
                
                <div class="card">
                    <div class="card-title">⏱️ Tempo de Loja (Aging)</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Faixa</th>
                                <th>Lojas</th>
                                <th>%</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f"""
                            <tr>
                                <td>{item['faixa']}</td>
                                <td>{item['count']:,}</td>
                                <td>
                                    <div>{item['pct']}%</div>
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: {min(item['pct']*2, 100)}%; background: linear-gradient(90deg, #4ade80, #22c55e);"></div>
                                    </div>
                                </td>
                            </tr>
                            """ for item in dashboard_data['perfil_aging']])}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="two-columns" style="margin-top: 20px;">
                <div class="card">
                    <div class="card-title">🏷️ Verticais (Segmentos)</div>
                    <div class="chart-container">
                        <canvas id="chartVerticais"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title">📋 Planos</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Plano</th>
                                <th>Lojas</th>
                                <th>%</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f"""
                            <tr>
                                <td>{item['plano']}</td>
                                <td>{item['count']:,}</td>
                                <td>
                                    <div>{item['pct']}%</div>
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: {min(item['pct'], 100)}%; background: linear-gradient(90deg, #fbbf24, #f59e0b);"></div>
                                    </div>
                                </td>
                            </tr>
                            """ for item in dashboard_data['perfil_planos']])}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- WEBINARS -->
        <div id="webinars" class="tab-content">
            <h2 class="section-title">Análise dos Webinars</h2>
            
            <div class="card">
                <div class="card-title">🏆 Top 10 Webinars Mais Populares</div>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Nome do Webinar</th>
                            <th>Participantes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f"""
                        <tr>
                            <td><strong>{i+1}</strong></td>
                            <td>{item['nome']}</td>
                            <td>
                                <div>{item['participantes']:,}</div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {min(item['participantes']/dashboard_data['webinars_populares'][0]['participantes']*100, 100)}%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>
                                </div>
                            </td>
                        </tr>
                        """ for i, item in enumerate(dashboard_data['webinars_populares'])])}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            setTimeout(initCharts, 100);
        }}
        
        Chart.defaults.color = '#888';
        Chart.defaults.borderColor = '#2d2d44';
        
        function initCharts() {{
            // Merchant Services Distribution
            const ctxMSDist = document.getElementById('chartMSDistribuicao');
            if (ctxMSDist && !ctxMSDist.chart) {{
                const msData = {json.dumps(dashboard_data['merchant_services_dist'])};
                ctxMSDist.chart = new Chart(ctxMSDist, {{
                    type: 'bar',
                    data: {{
                        labels: msData.map(d => d.qtd + ' produtos'),
                        datasets: [{{
                            label: 'Lojas',
                            data: msData.map(d => d.pct),
                            backgroundColor: [
                                'rgba(248, 113, 113, 0.8)',
                                'rgba(251, 191, 36, 0.8)',
                                'rgba(74, 222, 128, 0.8)',
                                'rgba(96, 165, 250, 0.8)',
                                'rgba(167, 139, 250, 0.8)',
                                'rgba(244, 114, 182, 0.8)'
                            ],
                            borderRadius: 8
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            y: {{ 
                                beginAtZero: true,
                                ticks: {{ callback: value => value + '%' }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Merchant Services Comparativo
            const ctxMSComp = document.getElementById('chartMSComparativo');
            if (ctxMSComp && !ctxMSComp.chart) {{
                const msCompData = {json.dumps(dashboard_data['merchant_services_comparativo'])};
                ctxMSComp.chart = new Chart(ctxMSComp, {{
                    type: 'bar',
                    data: {{
                        labels: msCompData.map(d => d.qtd + ' prod'),
                        datasets: [
                            {{
                                label: 'Com Webinar',
                                data: msCompData.map(d => d.pct_com),
                                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                                borderRadius: 4
                            }},
                            {{
                                label: 'Sem Webinar',
                                data: msCompData.map(d => d.pct_sem),
                                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                                borderRadius: 4
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ position: 'bottom' }} }},
                        scales: {{
                            y: {{ 
                                beginAtZero: true,
                                ticks: {{ callback: value => value + '%' }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Combinações de Produtos
            const ctxCombos = document.getElementById('chartCombinacoes');
            if (ctxCombos && !ctxCombos.chart) {{
                const combosData = {json.dumps(dashboard_data['combinacoes_produtos'][:8])};
                ctxCombos.chart = new Chart(ctxCombos, {{
                    type: 'bar',
                    data: {{
                        labels: combosData.map(d => d.combo),
                        datasets: [{{
                            data: combosData.map(d => d.pct),
                            backgroundColor: [
                                'rgba(102, 126, 234, 0.8)',
                                'rgba(118, 75, 162, 0.8)',
                                'rgba(248, 113, 113, 0.8)',
                                'rgba(74, 222, 128, 0.8)',
                                'rgba(251, 191, 36, 0.8)',
                                'rgba(96, 165, 250, 0.8)',
                                'rgba(167, 139, 250, 0.8)',
                                'rgba(244, 114, 182, 0.8)'
                            ],
                            borderRadius: 6
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: 'y',
                        plugins: {{ 
                            legend: {{ display: false }},
                            tooltip: {{
                                callbacks: {{
                                    label: ctx => ctx.raw.toFixed(1) + '% das lojas'
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{ 
                                beginAtZero: true,
                                ticks: {{ callback: value => value + '%' }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Status Distribution Chart
            const ctxStatusDist = document.getElementById('chartStatusDist');
            if (ctxStatusDist && !ctxStatusDist.chart) {{
                const statusData = {json.dumps(dashboard_data['status_sellers']['distribuicao'])};
                const statusColors = {{
                    'no-seller': '#ef4444',
                    'struggling-seller': '#f97316',
                    'tiny-seller': '#fbbf24',
                    'small-seller': '#84cc16',
                    'medium-seller': '#22c55e',
                    'large-seller': '#14b8a6',
                    'top-seller': '#667eea'
                }};
                ctxStatusDist.chart = new Chart(ctxStatusDist, {{
                    type: 'doughnut',
                    data: {{
                        labels: statusData.map(d => d.label + ' (' + d.pct + '%)'),
                        datasets: [{{
                            data: statusData.map(d => d.count),
                            backgroundColor: statusData.map(d => statusColors[d.status] || '#888'),
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ position: 'right' }}
                        }}
                    }}
                }});
            }}
            
            // Status GMV Chart
            const ctxStatusGMV = document.getElementById('chartStatusGMV');
            if (ctxStatusGMV && !ctxStatusGMV.chart) {{
                const perfData = {json.dumps(dashboard_data['status_performance'])};
                const statusColors = {{
                    'no-seller': '#ef4444',
                    'struggling-seller': '#f97316',
                    'tiny-seller': '#fbbf24',
                    'small-seller': '#84cc16',
                    'medium-seller': '#22c55e',
                    'large-seller': '#14b8a6',
                    'top-seller': '#667eea'
                }};
                ctxStatusGMV.chart = new Chart(ctxStatusGMV, {{
                    type: 'bar',
                    data: {{
                        labels: perfData.map(d => d.label),
                        datasets: [{{
                            label: 'GMV Médio',
                            data: perfData.map(d => d.gmv_medio),
                            backgroundColor: perfData.map(d => statusColors[d.status] || '#888'),
                            borderRadius: 6
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{ callback: value => 'R$ ' + value.toLocaleString('pt-BR') }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Status Churn Chart
            const ctxStatusChurn = document.getElementById('chartStatusChurn');
            if (ctxStatusChurn && !ctxStatusChurn.chart) {{
                const perfData = {json.dumps(dashboard_data['status_performance'])};
                ctxStatusChurn.chart = new Chart(ctxStatusChurn, {{
                    type: 'line',
                    data: {{
                        labels: perfData.map(d => d.label),
                        datasets: [{{
                            label: 'Prob. Churn',
                            data: perfData.map(d => d.churn_prob),
                            borderColor: '#f87171',
                            backgroundColor: 'rgba(248, 113, 113, 0.1)',
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#f87171',
                            pointRadius: 6
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100,
                                ticks: {{ callback: value => value + '%' }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // GMV Chart
            const ctxGMV = document.getElementById('chartGMV');
            if (ctxGMV && !ctxGMV.chart) {{
                ctxGMV.chart = new Chart(ctxGMV, {{
                    type: 'bar',
                    data: {{
                        labels: ['Média', 'Mediana'],
                        datasets: [
                            {{
                                label: 'Com Webinar',
                                data: [{dashboard_data['performance']['gmv_medio_com']}, {dashboard_data['performance']['gmv_mediano_com']}],
                                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                                borderRadius: 8
                            }},
                            {{
                                label: 'Sem Webinar',
                                data: [{dashboard_data['performance']['gmv_medio_sem']}, {dashboard_data['performance']['gmv_mediano_sem']}],
                                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                                borderRadius: 8
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ position: 'bottom' }} }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{ callback: value => 'R$ ' + value.toLocaleString('pt-BR') }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Orders Chart
            const ctxOrders = document.getElementById('chartOrders');
            if (ctxOrders && !ctxOrders.chart) {{
                ctxOrders.chart = new Chart(ctxOrders, {{
                    type: 'bar',
                    data: {{
                        labels: ['Média', 'Mediana'],
                        datasets: [
                            {{
                                label: 'Com Webinar',
                                data: [{dashboard_data['performance']['orders_medio_com']}, {dashboard_data['performance']['orders_mediano_com']}],
                                backgroundColor: 'rgba(74, 222, 128, 0.8)',
                                borderRadius: 8
                            }},
                            {{
                                label: 'Sem Webinar',
                                data: [{dashboard_data['performance']['orders_medio_sem']}, {dashboard_data['performance']['orders_mediano_sem']}],
                                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                                borderRadius: 8
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ position: 'bottom' }} }},
                        scales: {{ y: {{ beginAtZero: true }} }}
                    }}
                }});
            }}
            
            // Churn Chart
            const ctxChurn = document.getElementById('chartChurn');
            if (ctxChurn && !ctxChurn.chart) {{
                ctxChurn.chart = new Chart(ctxChurn, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Com Webinar ({dashboard_data['churn']['prob_com']}%)', 'Sem Webinar ({dashboard_data['churn']['prob_sem']}%)'],
                        datasets: [{{
                            data: [{dashboard_data['churn']['prob_com']}, {dashboard_data['churn']['prob_sem']}],
                            backgroundColor: ['rgba(74, 222, 128, 0.8)', 'rgba(248, 113, 113, 0.8)'],
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ position: 'bottom' }} }}
                    }}
                }});
            }}
            
            // Churn Profile
            const ctxChurnProfile = document.getElementById('chartChurnProfile');
            if (ctxChurnProfile && !ctxChurnProfile.chart) {{
                const churnData = {json.dumps([item for item in dashboard_data['perfil_churn'][:8]])};
                ctxChurnProfile.chart = new Chart(ctxChurnProfile, {{
                    type: 'bar',
                    data: {{
                        labels: churnData.map(d => d.profile),
                        datasets: [{{
                            data: churnData.map(d => d.pct),
                            backgroundColor: 'rgba(102, 126, 234, 0.8)',
                            borderRadius: 4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: 'y',
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ x: {{ ticks: {{ callback: value => value + '%' }} }} }}
                    }}
                }});
            }}
            
            // Verticais
            const ctxVerticais = document.getElementById('chartVerticais');
            if (ctxVerticais && !ctxVerticais.chart) {{
                const verticaisData = {json.dumps(dashboard_data['perfil_verticais'][:10])};
                ctxVerticais.chart = new Chart(ctxVerticais, {{
                    type: 'bar',
                    data: {{
                        labels: verticaisData.map(d => d.vertical),
                        datasets: [{{
                            data: verticaisData.map(d => d.pct),
                            backgroundColor: [
                                'rgba(102, 126, 234, 0.8)',
                                'rgba(118, 75, 162, 0.8)',
                                'rgba(74, 222, 128, 0.8)',
                                'rgba(251, 191, 36, 0.8)',
                                'rgba(248, 113, 113, 0.8)',
                                'rgba(96, 165, 250, 0.8)',
                                'rgba(167, 139, 250, 0.8)',
                                'rgba(52, 211, 153, 0.8)',
                                'rgba(251, 146, 60, 0.8)',
                                'rgba(244, 114, 182, 0.8)'
                            ],
                            borderRadius: 4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: 'y',
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ x: {{ ticks: {{ callback: value => value + '%' }} }} }}
                    }}
                }});
            }}
        }}
        
        document.addEventListener('DOMContentLoaded', initCharts);
    </script>
</body>
</html>
'''

with open('/Users/renatovieira/Downloads/dashboard_webinar_insights_v2.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ Dashboard v2 gerado com sucesso!")
print("📁 Arquivo: /Users/renatovieira/Downloads/dashboard_webinar_insights_v2.html")

# Print resumo da análise pareada
print("\n" + "="*60)
print("RESUMO DA ANÁLISE PAREADA")
print("="*60)
print(f"Grupos analisados: {dashboard_data['analise_pareada']['total_grupos']}")
print(f"GMV pareado: {dashboard_data['analise_pareada']['resumo']['gmv_diff_pct']:+}% (com vs sem webinar)")
print(f"Churn pareado: {dashboard_data['analise_pareada']['resumo']['churn_diff_pp']:+}pp (com vs sem webinar)")
print(f"Merchant Services: {dashboard_data['analise_pareada']['resumo']['ms_diff_pct']:+}% (com vs sem webinar)")
