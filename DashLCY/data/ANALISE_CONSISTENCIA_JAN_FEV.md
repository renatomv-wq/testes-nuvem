# Análise de consistência – Base Jan x Fev (Lifecycle BR)

## Objetivo
Verificar se as bases de **janeiro** e **fevereiro** são comparáveis para análises mês a mês.

## Arquivos
- **Jan:** `BR - Base Stores para Lifecycle - Jan ok.csv` (reporting_date: 2026-02-13)
- **Fev:** `Base Stores para Lifecycle - 04_03_2026 - Base_BR_Lifecycle.csv` (reporting_date: 2026-03-04)

## Resultado: **comparáveis**

Nenhuma inconsistência que impeça a comparação. Ajustes necessários são triviais.

---

## 1. Estrutura de colunas

| Item | Jan | Fev |
|------|-----|-----|
| Total de colunas | 51 | 52 |
| Diferença | — | 1 coluna a mais em Fev |

**Coluna extra em fevereiro:** `time_to_first_order` (entre `4_steps_completed` e `gmv30`).

- **Tratamento:** ao carregar as duas bases, usar os mesmos nomes de coluna; em janeiro essa coluna pode ser preenchida como ausente (NaN). Todas as demais colunas (incluindo `gmv30`, `gmv90`, `orders30`, `orders90`, `current_segment`, etc.) existem e têm o mesmo nome nos dois arquivos.

---

## 2. Identificador e datas

- **Chave de join:** `store_id` existe e é usado em ambos os arquivos.
- **reporting_date:** Jan = `2026-02-13`, Fev = `2026-03-04` — identificam claramente o snapshot de cada base.

---

## 3. Volumes e overlap

| Métrica | Jan | Fev |
|---------|-----|-----|
| Total de lojas | 104.550 | 101.337 |
| Lojas em **ambos** os meses | — | 96.455 |
| Só em Jan (saíram da base) | — | 8.095 |
| Só em Fev (novas na base) | — | 4.882 |

Interpretação: variação de base entre meses é esperada (churn, novas lojas). A comparação Jan x Fev pode ser feita tanto no **total de cada mês** quanto nas **lojas presentes em ambos** (coorte), conforme a pergunta de análise.

---

## 4. Conclusão

- **Estrutura:** compatível; única diferença é `time_to_first_order` em Fev (tratável com NaN em Jan).
- **Chave e datas:** `store_id` e `reporting_date` permitem alinhar e identificar os períodos.
- **Volumes:** diferença de total de lojas e overlap são coerentes com base mensal e permitem comparações (totais e coorte).

**Recomendação:** usar as duas bases para comparações Jan x Fev, garantindo o alinhamento de colunas (incluindo `time_to_first_order`) no carregamento.
