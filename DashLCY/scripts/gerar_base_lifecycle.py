#!/usr/bin/env python3
"""
Gera base CSV anonimizada para o desafio Lifecycle (10k lojas).
- merchant_id: números únicos fictícios
- Proporções de status_seller alinhadas à base BR (Lifecycle Jan)
- GMV e numero_vendas condizentes com o tier do status_seller
- Sem canal_principal_comunicacao nem ultima_abertura_email_dias
"""

import csv
import random
from pathlib import Path

# Semente para reprodutibilidade
random.seed(42)

# Proporções de status_seller (base BR - Base Stores para Lifecycle - Jan ok)
# NaN redistribuído como no-seller
PROPORCOES_STATUS_SELLER = {
    "no-seller": 0.5113,
    "struggling-seller": 0.2587,
    "tiny-seller": 0.1271,
    "small-seller": 0.0825,
    "medium-seller": 0.0427,
    "large-seller": 0.0081,
    "top-seller": 0.0061,
}

# Faixas de vendas em 90 dias por tier (inclusive)
VENDAS_90D_POR_TIER = {
    "no-seller": (0, 0),
    "struggling-seller": (1, 6),
    "tiny-seller": (7, 30),
    "small-seller": (31, 150),
    "medium-seller": (151, 750),
    "large-seller": (751, 1500),
    "top-seller": (1501, 5000),
}

# status_conta (distribuição típica)
PROPORCOES_STATUS_CONTA = {
    "trial": 0.03,
    "ativo": 0.90,
    "churnado": 0.05,
    "cancelado": 0.02,
}

# Adoção produtos (base não tinha preenchido; valores plausíveis)
PROB_NUVEM_MARKETING = 0.18
PROB_NUVEM_CHAT = 0.12
PROB_USA_CONCORRENTE = 0.10

NUM_LOJAS = 10_000
MERCHANT_ID_INICIO = 100001  # IDs fictícios únicos


def escolher_status_seller():
    segmentos = list(PROPORCOES_STATUS_SELLER.keys())
    pesos = list(PROPORCOES_STATUS_SELLER.values())
    return random.choices(segmentos, weights=pesos, k=1)[0]


def escolher_status_conta():
    r = random.random()
    acum = 0.0
    for status, p in PROPORCOES_STATUS_CONTA.items():
        acum += p
        if r < acum:
            return status
    return "ativo"


def vendas_90d_para_tier(tier):
    lo, hi = VENDAS_90D_POR_TIER[tier]
    if lo == hi:
        return lo
    return random.randint(lo, hi)


def gmv_para_vendas(num_vendas_90d, tier):
    """GMV em 90d coerente com número de vendas (ticket médio por faixa)."""
    if num_vendas_90d == 0:
        return 0
    # Ticket médio aproximado por tier (em reais)
    ticket_medio = {
        "struggling-seller": random.uniform(80, 250),
        "tiny-seller": random.uniform(150, 400),
        "small-seller": random.uniform(200, 500),
        "medium-seller": random.uniform(300, 600),
        "large-seller": random.uniform(400, 700),
        "top-seller": random.uniform(500, 900),
    }
    ticket = ticket_medio.get(tier, 200)
    base = num_vendas_90d * ticket
    # Variação ±15%
    return round(base * random.uniform(0.85, 1.15))


def main():
    out_path = Path(__file__).resolve().parent.parent / "data" / "base_lifecycle_10k.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    colunas = [
        "merchant_id",
        "status_conta",
        "status_seller",
        "dias_desde_ativacao",
        "idade_loja_dias",
        "gmv_ultimos_30d",
        "gmv_ultimos_90d",
        "numero_vendas_30d",
        "numero_vendas_90d",
        "usa_nuvem_marketing",
        "usa_nuvem_chat",
        "usa_concorrente",
    ]

    rows = []
    for i in range(NUM_LOJAS):
        merchant_id = MERCHANT_ID_INICIO + i
        status_conta = escolher_status_conta()
        status_seller = escolher_status_seller()

        # Dias: distribuição realista
        idade_loja_dias = random.choices(
            range(30, 3500),
            weights=[1.0 / (d + 100) for d in range(30, 3500)],
            k=1,
        )[0]
        dias_desde_ativacao = random.randint(0, min(idade_loja_dias, 800))

        numero_vendas_90d = vendas_90d_para_tier(status_seller)
        gmv_90d = gmv_para_vendas(numero_vendas_90d, status_seller)

        # 30d: ~1/3 do 90d com variação
        if numero_vendas_90d == 0:
            numero_vendas_30d = 0
            gmv_30d = 0
        else:
            ratio_30_90 = random.uniform(0.25, 0.45)
            numero_vendas_30d = max(0, round(numero_vendas_90d * ratio_30_90))
            gmv_30d = round(gmv_90d * (numero_vendas_30d / numero_vendas_90d) * random.uniform(0.9, 1.1))

        usa_nuvem_marketing = "sim" if random.random() < PROB_NUVEM_MARKETING else "nao"
        usa_nuvem_chat = "sim" if random.random() < PROB_NUVEM_CHAT else "nao"
        usa_concorrente = "sim" if random.random() < PROB_USA_CONCORRENTE else "nao"

        rows.append({
            "merchant_id": merchant_id,
            "status_conta": status_conta,
            "status_seller": status_seller,
            "dias_desde_ativacao": dias_desde_ativacao,
            "idade_loja_dias": idade_loja_dias,
            "gmv_ultimos_30d": gmv_30d,
            "gmv_ultimos_90d": gmv_90d,
            "numero_vendas_30d": numero_vendas_30d,
            "numero_vendas_90d": numero_vendas_90d,
            "usa_nuvem_marketing": usa_nuvem_marketing,
            "usa_nuvem_chat": usa_nuvem_chat,
            "usa_concorrente": usa_concorrente,
        })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas)
        w.writeheader()
        w.writerows(rows)

    print(f"Base gerada: {out_path}")
    print(f"Total de linhas (excl. cabeçalho): {len(rows)}")

    # Resumo de status_seller
    from collections import Counter
    seg = Counter(r["status_seller"] for r in rows)
    print("\nDistribuição status_seller:")
    for s, c in sorted(seg.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c} ({100*c/NUM_LOJAS:.1f}%)")


if __name__ == "__main__":
    main()
