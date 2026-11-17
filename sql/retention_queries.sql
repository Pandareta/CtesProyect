-- ============================================================================
-- Consultas analíticas de retención y churn (SaaS / Telecom)
-- Tabla de trabajo: subscriptions (versión limpia de data/raw/saas_subscriptions.csv)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- (a) ¿Cuánto churn y MRR perdido genera cada tipo de contrato?
--     CTE + SUM() OVER () para calcular la participación sobre el total perdido.
-- ----------------------------------------------------------------------------
WITH contract_summary AS (
    SELECT
        contract_type,
        COUNT(*)                                            AS total_customers,
        SUM(CASE WHEN churn = 'Sí' THEN 1 ELSE 0 END)       AS churned_customers,
        SUM(CASE WHEN churn = 'Sí' THEN monthly_charges ELSE 0 END) AS mrr_lost,
        SUM(CASE WHEN churn = 'No' THEN monthly_charges ELSE 0 END) AS mrr_active
    FROM subscriptions
    GROUP BY contract_type
)
SELECT
    contract_type,
    total_customers,
    churned_customers,
    ROUND(100.0 * churned_customers / total_customers, 2)          AS churn_rate_pct,
    ROUND(mrr_lost, 2)                                             AS mrr_lost,
    ROUND(100.0 * mrr_lost / SUM(mrr_lost) OVER (), 2)             AS pct_of_total_mrr_lost
FROM contract_summary
ORDER BY churn_rate_pct DESC;


-- ----------------------------------------------------------------------------
-- (b) ¿Cómo escala la probabilidad de baja con los tickets de soporte?
--     Agregación condicional por cantidad de tickets.
-- ----------------------------------------------------------------------------
SELECT
    support_tickets,
    COUNT(*)                                                       AS total_customers,
    SUM(CASE WHEN churn = 'Sí' THEN 1 ELSE 0 END)                  AS churned_customers,
    ROUND(100.0 * SUM(CASE WHEN churn = 'Sí' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                           AS churn_rate_pct,
    ROUND(AVG(CASE WHEN churn = 'Sí' THEN monthly_charges END), 2) AS avg_mrr_lost_per_churn
FROM subscriptions
GROUP BY support_tickets
ORDER BY support_tickets;


-- ----------------------------------------------------------------------------
-- (c) ¿Qué canal de adquisición retiene mejor y aporta más LTV?
--     DENSE_RANK sobre retención y LTV promedio (LTV = cargo mensual * antigüedad).
-- ----------------------------------------------------------------------------
WITH channel_metrics AS (
    SELECT
        acquisition_channel,
        COUNT(*)                                                       AS total_customers,
        ROUND(100.0 * SUM(CASE WHEN churn = 'No' THEN 1 ELSE 0 END)
              / COUNT(*), 2)                                           AS retention_rate_pct,
        ROUND(AVG(monthly_charges), 2)                                 AS arpu,
        ROUND(AVG(monthly_charges * tenure_months), 2)                 AS avg_ltv
    FROM subscriptions
    GROUP BY acquisition_channel
)
SELECT
    acquisition_channel,
    total_customers,
    retention_rate_pct,
    arpu,
    avg_ltv,
    DENSE_RANK() OVER (ORDER BY retention_rate_pct DESC) AS retention_rank,
    DENSE_RANK() OVER (ORDER BY avg_ltv DESC)            AS ltv_rank
FROM channel_metrics
ORDER BY retention_rank, ltv_rank;


-- ----------------------------------------------------------------------------
-- (d) ¿Qué combinación de plan y contrato es el segmento más volátil?
--     Matriz de riesgo con ranking y peso sobre el MRR perdido total.
-- ----------------------------------------------------------------------------
WITH segment_risk AS (
    SELECT
        plan_type,
        contract_type,
        COUNT(*)                                                       AS total_customers,
        SUM(CASE WHEN churn = 'Sí' THEN 1 ELSE 0 END)                  AS churned_customers,
        ROUND(100.0 * SUM(CASE WHEN churn = 'Sí' THEN 1 ELSE 0 END)
              / COUNT(*), 2)                                           AS churn_rate_pct,
        ROUND(SUM(CASE WHEN churn = 'Sí' THEN monthly_charges ELSE 0 END), 2) AS mrr_lost
    FROM subscriptions
    GROUP BY plan_type, contract_type
)
SELECT
    plan_type,
    contract_type,
    total_customers,
    churned_customers,
    churn_rate_pct,
    mrr_lost,
    RANK() OVER (ORDER BY churn_rate_pct DESC)                     AS risk_rank,
    ROUND(100.0 * mrr_lost / SUM(mrr_lost) OVER (), 2)             AS pct_of_total_mrr_lost
FROM segment_risk
ORDER BY risk_rank, mrr_lost DESC;
