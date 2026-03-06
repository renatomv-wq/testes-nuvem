# Desafio – Analista de CRM Lifecycle
## Nuvem Marketing e Nuvem Chat

---

## Formato e prazo

- **Entrega:** apresentação em PowerPoint (PPT) com no máximo **20 minutos** de apresentação.
- **Prazo:** **3 a 4 dias** entre o envio do desafio (incluindo a base de dados) e a data da apresentação.
- **Profundidade esperada:** análise básica a intermediária, com conclusões e recomendações claras.

---

## Contexto

Na Nuvemshop, o Lifecycle é responsável por campanhas e comunicações que levam o merchant a **adotar** e a fazer **cross-sell** de produtos como **Nuvem Marketing** e **Nuvem Chat**, além da melhoria contínua da jornada e das trilhas de comunicação.

O sucesso é medido por métricas como adoção desses produtos, cross-sell, engajamento com comunicações e retenção.

---

## Sua missão

Desenhar um **plano de campanhas para aumentar adoção e cross-sell de Nuvem Marketing e Nuvem Chat**. Você receberá uma **base de dados** com informações de merchants — use-a para embasar suas decisões do início ao fim.

---

## O que você receberá

Uma **base de dados** (CSV ou planilha) de merchants e um **dicionário** descrevendo os campos disponíveis. A partir daí, é com você: analise como achar mais útil e traga conclusões que sustentem seu plano.

---

## O que você precisa apresentar (PPT – máx. 20 min)

Sua apresentação deve cobrir, na ordem e profundidade que fizer sentido para você:

1. **Leitura dos dados** — O que você analisou, o que encontrou e como isso orienta suas decisões.
2. **Hipóteses e experimentação** — O que você testaria para validar ou melhorar o plano e como.
3. **Estratégia de comunicação** — Como você desenharia as campanhas com base no que os dados mostraram.
4. **Monitoramento e próximos passos** — Como acompanharia resultados e manteria o plano sustentado em dados.

O importante: que cada decisão (onde atuar, em quem, quando, como) esteja **embasada na análise**, e que isso fique claro na sua fala.

---

## O que estamos avaliando

Capacidade analítica, embasamento das decisões em dados, segmentação e priorização, experimentação e clareza da apresentação (estrutura e uso do tempo).

---

## Instruções de entrega

- Enviar o **arquivo da apresentação (PPT/PPTX)** até a data combinada.
- A apresentação será feita em reunião (presencial ou remota), com **até 20 minutos** de fala.
- Trazer dúvidas sobre a base ou o desafio antes da apresentação, se necessário (canal a ser definido pelo recrutamento).

---

*O bloco abaixo é para uso interno (construção do dataset). Não enviar ao candidato.*

---

## Especificação da base de dados (para construção do dataset)

A tabela abaixo descreve os campos sugeridos para a base que será enviada aos candidatos. A base pode ser anonimizada e com volumes compatíveis com análise em planilha (ex.: até 5–10 mil linhas).

| Campo | Descrição | Exemplo / valores |
|-------|------------|-------------------|
| `merchant_id` | Identificador único do merchant (anonimizado) | Número fictício único |
| `status_conta` | Status da conta | trial, ativo, churnado, cancelado |
| `status_seller` | Tier do seller (classificação por estágio/vendas) | no-seller, struggling-seller, tiny-seller, small-seller, medium-seller, large-seller, top-seller |
| `dias_desde_ativacao` | Dias desde a primeira ativação da loja | 0–365+ |
| `idade_loja_dias` | Idade da loja em dias (desde criação) | 0–365+ |
| `gmv_ultimos_30d` ou `gmv_ultimos_90d` | GMV (faturamento) no período | Valor numérico (pode ser em faixas: baixo, médio, alto) |
| `numero_vendas_30d` ou `numero_vendas_90d` | Quantidade de vendas no período (90d define o tier) | Inteiro; no-seller=0, struggling=1–6, tiny=7–30, small=31–150, medium=151–750, large=751–1500, top=1501+ |
| `usa_nuvem_marketing` | Se já utiliza Nuvem Marketing | sim / não |
| `usa_nuvem_chat` | Se já utiliza Nuvem Chat | sim / não |
| `usa_concorrente` | Se utiliza produto de concorrente (ex.: chat/marketing de outra plataforma) | sim / não |

**Sugestão de uso:**

- **Momento de jornada:** `dias_desde_ativacao`, `idade_loja_dias`, `status_conta`.
- **Tamanho da base impactável:** contagem por `status_conta`, por `status_seller` (tier), por faixa de `dias_desde_ativacao`, por uso de produto (`usa_nuvem_marketing`, `usa_nuvem_chat`, `usa_concorrente`).
- **Segmentação para campanhas:** cruzamentos entre GMV, idade da loja, número de vendas, status da conta, tier do seller e uso dos produtos.

Com essa base, o candidato consegue fazer análises básicas a intermediárias (tabelas dinâmicas, gráficos, proporções) e sustentar as recomendações na apresentação.
