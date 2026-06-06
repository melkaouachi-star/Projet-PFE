-- ======================================================================
-- Power BI analytical views — PostgreSQL (DirectQuery target)
-- ======================================================================
-- These views are ADDITIVE and read-only. They never modify the live
-- banking_* tables or the precomputed thesis artefacts. Power BI Desktop /
-- Service connects to these views via DirectQuery and slices them with the
-- conformed dimensions documented in powerbi/star_schema.md.
--
-- Conventions
-- -----------
-- * fraud_probability is on a 0..100 scale (dynamic scoring engine). The
--   views expose BOTH the raw value and fraud_probability_pct (0..1).
-- * real_fraud_label is the SIMULATION ground truth (scenario <> 'normal').
--   In a real production bank this label would not be immediately available.
-- * Economic constants (false-positive unit cost = 12.5, block threshold on
--   the 0..100 risk scale = 70) MIRROR configs/config.yaml. Update both
--   together if the cost model changes.
--
-- Apply with:  psql "$DATABASE_URL" -f sql/powerbi_views_postgres.sql
-- (scripts/load_powerbi_warehouse.py applies it automatically.)
-- ======================================================================

-- 1. Live transactions (fact_transactions) ----------------------------
CREATE OR REPLACE VIEW vw_powerbi_live_transactions AS
SELECT
    t.transaction_id,
    t.simulation_run_id,
    t.customer_id,
    t.customer_name,
    t.customer_age,
    t.customer_risk_category,
    t.timestamp,
    t.transaction_date,
    t.transaction_time,
    COALESCE(t.amount, t.transaction_amount, 0)            AS amount,
    COALESCE(t.currency, t.transaction_currency, 'USD')    AS currency,
    t.merchant_name,
    t.merchant_category,
    t.payment_method,
    t.card_type,
    t.country,
    t.city,
    t.latitude,
    t.longitude,
    t.ip_address,
    t.device_id,
    t.scenario,
    CASE WHEN COALESCE(t.scenario, 'normal') = 'normal' THEN 0 ELSE 1 END AS real_fraud_label,
    t.fraud_probability,                                   -- 0..100
    t.fraud_probability / 100.0                            AS fraud_probability_pct,  -- 0..1
    t.risk_score,
    70.0                                                   AS threshold_used,
    CASE WHEN t.decision = 'BLOCKED' THEN 1 ELSE 0 END     AS predicted_class,
    t.decision                                             AS decision_status,
    t.fraud_level,
    t.transaction_status,
    CASE WHEN COALESCE(t.scenario, 'normal') <> 'normal' AND t.decision = 'BLOCKED'
         THEN COALESCE(t.amount, t.transaction_amount, 0) ELSE 0 END AS estimated_avoided_loss,
    CASE WHEN COALESCE(t.scenario, 'normal') = 'normal' AND t.decision = 'BLOCKED'
         THEN 12.5 ELSE 0 END                              AS estimated_false_positive_cost,
    COALESCE(t.model_version, 'dynamic-fraud-engine')      AS model_name,
    t.created_at,
    EXTRACT(HOUR FROM COALESCE(t.timestamp, t.created_at))::int AS transaction_hour
FROM banking_transactions t;

-- 2. Live KPI snapshot (single row) ------------------------------------
CREATE OR REPLACE VIEW vw_powerbi_live_kpis AS
SELECT
    COUNT(*)                                                                                   AS total_transactions,
    COUNT(*) FILTER (WHERE decision = 'APPROVED')                                              AS approved,
    COUNT(*) FILTER (WHERE decision IN ('SUSPICIOUS', 'REVIEW'))                               AS suspicious,
    COUNT(*) FILTER (WHERE decision = 'BLOCKED')                                               AS blocked,
    COUNT(*) FILTER (WHERE COALESCE(scenario, 'normal') <> 'normal')                           AS real_frauds,
    COUNT(*) FILTER (WHERE COALESCE(scenario, 'normal') <> 'normal' AND decision = 'BLOCKED')  AS detected_frauds,
    COUNT(*) FILTER (WHERE COALESCE(scenario, 'normal') <> 'normal' AND decision <> 'BLOCKED') AS missed_frauds,
    COUNT(*) FILTER (WHERE COALESCE(scenario, 'normal') = 'normal' AND decision = 'BLOCKED')   AS false_positives,
    COALESCE(SUM(COALESCE(amount, transaction_amount, 0)), 0)                                  AS total_amount,
    COALESCE(SUM(COALESCE(amount, transaction_amount, 0))
             FILTER (WHERE COALESCE(scenario, 'normal') <> 'normal'), 0)                       AS total_fraud_amount,
    COALESCE(SUM(COALESCE(amount, transaction_amount, 0))
             FILTER (WHERE COALESCE(scenario, 'normal') <> 'normal' AND decision = 'BLOCKED'), 0) AS estimated_avoided_loss,
    (COUNT(*) FILTER (WHERE COALESCE(scenario, 'normal') = 'normal' AND decision = 'BLOCKED')) * 12.5 AS false_positive_cost,
    COALESCE(AVG(risk_score), 0)                                                               AS avg_risk_score,
    COALESCE(AVG(fraud_probability), 0)                                                        AS avg_fraud_probability,
    MAX(created_at)                                                                            AS last_transaction_at
FROM banking_transactions;

-- 3. Fraud alerts (fact_fraud_alerts) ----------------------------------
CREATE OR REPLACE VIEW vw_powerbi_fraud_alerts AS
SELECT
    a.id                                                   AS alert_id,
    a.transaction_id,
    a.created_at                                           AS timestamp,
    a.customer_id,
    a.customer_name,
    a.severity,
    a.fraud_level,
    a.fraud_probability,
    a.risk_score,
    a.decision                                             AS decision_status,
    a.amount,
    a.currency,
    a.country,
    a.city,
    a.ip_address,
    a.message                                              AS alert_reason,
    t.simulation_run_id,
    t.scenario,
    CASE WHEN COALESCE(t.scenario, 'normal') <> 'normal' AND a.decision = 'BLOCKED'
         THEN COALESCE(a.amount, 0) ELSE 0 END             AS estimated_avoided_loss,
    COALESCE(t.model_version, 'dynamic-fraud-engine')      AS model_name
FROM banking_alerts a
LEFT JOIN banking_transactions t ON t.transaction_id = a.transaction_id;

-- 4. SHAP explanations, unnested to long format (fact_shap_explanations)
CREATE OR REPLACE VIEW vw_powerbi_shap_explanations AS
SELECT
    s.transaction_id || '-' || fn.ord                      AS explanation_id,
    s.transaction_id,
    fn.feature_name,
    (s.risk_contribution_score::jsonb -> fn.feature_name ->> 'value')  AS feature_value,
    sv.shap_value::double precision                        AS shap_value,
    CASE WHEN sv.shap_value::double precision >= 0 THEN 'increases_risk'
         ELSE 'decreases_risk' END                         AS contribution_direction,
    (s.risk_contribution_score::jsonb -> fn.feature_name ->> 'reason')  AS explanation_text,
    fn.ord                                                 AS rank_importance,
    s.base_value,
    s.created_at
FROM banking_shap_explanations s
JOIN LATERAL jsonb_array_elements_text(s.feature_names::jsonb)
        WITH ORDINALITY AS fn(feature_name, ord) ON TRUE
JOIN LATERAL jsonb_array_elements_text(s.shap_values::jsonb)
        WITH ORDINALITY AS sv(shap_value, ord2) ON fn.ord = sv.ord2;

-- 5. Model benchmark (fact_model_benchmark) ----------------------------
CREATE OR REPLACE VIEW vw_powerbi_model_benchmark AS
SELECT
    model_name,
    threshold_type,
    threshold_value,
    precision,
    recall,
    f1,
    mcc,
    roc_auc,
    pr_auc,
    specificity,
    balanced_accuracy,
    fp                                                     AS false_positives,
    fn                                                     AS false_negatives,
    tp,
    tn,
    total_estimated_cost,
    estimated_avoided_loss,
    model_rank,
    selected_best_model,
    -- Appended after existing columns so CREATE OR REPLACE VIEW (which forbids
    -- reordering/inserting existing columns) stays valid. Power BI refs by name.
    training_time,
    inference_time
FROM model_benchmark_results;

-- 6. Cost comparison summary (fact_cost_analysis) ----------------------
CREATE OR REPLACE VIEW vw_powerbi_cost_comparison AS
SELECT
    model_name,
    strategy                                               AS threshold_type,
    threshold                                              AS threshold_value,
    tp                                                     AS true_positives,
    tn                                                     AS true_negatives,
    fp                                                     AS false_positives,
    fn                                                     AS false_negatives,
    precision,
    recall,
    f1,
    mcc,
    pr_auc,
    roc_auc,
    fraud_loss                                             AS fraud_loss_cost,
    fp_cost                                                AS false_positive_cost,
    total_cost,
    savings_vs_default,
    savings_pct_vs_default,
    is_optimal_threshold
FROM cost_comparison_summary;

-- 7. Threshold optimization sweep (fact_threshold_optimization) --------
CREATE OR REPLACE VIEW vw_powerbi_threshold_optimization AS
SELECT
    model_name,
    threshold                                              AS threshold_value,
    precision,
    recall,
    f1,
    mcc,
    specificity,
    fp                                                     AS false_positives,
    fn                                                     AS false_negatives,
    tp,
    tn,
    fraud_loss,
    fp_cost,
    total_cost,
    is_f1_optimal,
    is_mcc_optimal,
    is_cost_optimal
FROM cost_analysis_sweep;

-- 8. Simulation effectiveness (dim_simulation_run + metrics) -----------
CREATE OR REPLACE VIEW vw_powerbi_simulation_effectiveness AS
SELECT
    run_id                                                 AS simulation_run_id,
    started_at,
    stopped_at,
    status,
    rate_tps,
    fraud_ratio,
    model_version,
    generated_transactions,
    approved,
    suspicious,
    blocked,
    simulated_frauds,
    detected_frauds,
    missed_frauds,
    false_positives,
    estimated_avoided_loss,
    CASE WHEN simulated_frauds > 0
         THEN detected_frauds::double precision / simulated_frauds ELSE 0 END AS detection_rate,
    CASE WHEN (detected_frauds + false_positives) > 0
         THEN detected_frauds::double precision / (detected_frauds + false_positives) ELSE 0 END AS precision_on_blocked,
    CASE WHEN simulated_frauds > 0
         THEN detected_frauds::double precision / simulated_frauds ELSE 0 END AS recall_on_fraud,
    CASE WHEN (generated_transactions - simulated_frauds) > 0
         THEN false_positives::double precision / (generated_transactions - simulated_frauds) ELSE 0 END AS false_positive_rate
FROM simulation_runs;

-- 9. Moroccan-context demonstration data (synthetic, clearly labelled) -
-- NOTE: derived ONLY from synthetic simulation transactions where
-- country = 'Morocco'. This is NOT real Moroccan fraud data. See the data
-- label column and powerbi/page_specifications.md (Page 9).
CREATE OR REPLACE VIEW vw_powerbi_moroccan_context AS
SELECT
    t.city,
    COUNT(*)                                                                   AS transactions,
    COUNT(*) FILTER (WHERE COALESCE(t.scenario, 'normal') <> 'normal')         AS simulated_frauds,
    COUNT(*) FILTER (WHERE t.decision = 'BLOCKED')                             AS blocked,
    COALESCE(SUM(COALESCE(t.amount, t.transaction_amount, 0)), 0)              AS total_amount,
    COALESCE(AVG(t.risk_score), 0)                                            AS avg_risk_score,
    'Données synthétiques de démonstration — non représentatives de la fraude bancaire réelle au Maroc.' AS data_label,
    -- Appended after data_label so CREATE OR REPLACE VIEW (which forbids
    -- reordering existing columns) stays valid. Power BI references by name.
    AVG(t.latitude)                                                           AS latitude,
    AVG(t.longitude)                                                          AS longitude,
    CASE WHEN COUNT(*) > 0
         THEN SUM(CASE WHEN COALESCE(t.scenario, 'normal') <> 'normal' THEN 1 ELSE 0 END)::double precision / COUNT(*)
         ELSE 0 END                                                          AS fraud_rate
FROM banking_transactions t
WHERE t.country = 'Morocco'
GROUP BY t.city;
