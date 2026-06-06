-- ======================================================================
-- Power BI analytical views — SQLite (local dev / Import-mode testing)
-- ======================================================================
-- SQLite has no Power BI DirectQuery connector. These mirror the PostgreSQL
-- views so they can be validated locally and consumed in Power BI Import
-- mode via an ODBC driver or the CSV/API bundle. Production DirectQuery uses
-- sql/powerbi_views_postgres.sql.
--
-- Differences vs PostgreSQL:
--   * DROP VIEW IF EXISTS + CREATE VIEW (no CREATE OR REPLACE).
--   * SUM(CASE WHEN ...) instead of COUNT(*) FILTER (WHERE ...).
--   * json_each() (JSON1 extension, on by default) instead of jsonb_array_elements.
--   * 1.0 * x for float division.
-- Economic constants mirror configs/config.yaml (FP unit cost 12.5,
-- block threshold 70 on the 0..100 risk scale).
-- ======================================================================

-- 1. Live transactions -------------------------------------------------
DROP VIEW IF EXISTS vw_powerbi_live_transactions;
CREATE VIEW vw_powerbi_live_transactions AS
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
    t.fraud_probability,
    t.fraud_probability / 100.0                            AS fraud_probability_pct,
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
    CAST(strftime('%H', COALESCE(t.timestamp, t.created_at)) AS INTEGER) AS transaction_hour
FROM banking_transactions t;

-- 2. Live KPI snapshot -------------------------------------------------
DROP VIEW IF EXISTS vw_powerbi_live_kpis;
CREATE VIEW vw_powerbi_live_kpis AS
SELECT
    COUNT(*)                                                                                       AS total_transactions,
    SUM(CASE WHEN decision = 'APPROVED' THEN 1 ELSE 0 END)                                         AS approved,
    SUM(CASE WHEN decision IN ('SUSPICIOUS', 'REVIEW') THEN 1 ELSE 0 END)                          AS suspicious,
    SUM(CASE WHEN decision = 'BLOCKED' THEN 1 ELSE 0 END)                                          AS blocked,
    SUM(CASE WHEN COALESCE(scenario, 'normal') <> 'normal' THEN 1 ELSE 0 END)                      AS real_frauds,
    SUM(CASE WHEN COALESCE(scenario, 'normal') <> 'normal' AND decision = 'BLOCKED' THEN 1 ELSE 0 END) AS detected_frauds,
    SUM(CASE WHEN COALESCE(scenario, 'normal') <> 'normal' AND decision <> 'BLOCKED' THEN 1 ELSE 0 END) AS missed_frauds,
    SUM(CASE WHEN COALESCE(scenario, 'normal') = 'normal' AND decision = 'BLOCKED' THEN 1 ELSE 0 END)   AS false_positives,
    COALESCE(SUM(COALESCE(amount, transaction_amount, 0)), 0)                                      AS total_amount,
    COALESCE(SUM(CASE WHEN COALESCE(scenario, 'normal') <> 'normal'
                      THEN COALESCE(amount, transaction_amount, 0) ELSE 0 END), 0)                 AS total_fraud_amount,
    COALESCE(SUM(CASE WHEN COALESCE(scenario, 'normal') <> 'normal' AND decision = 'BLOCKED'
                      THEN COALESCE(amount, transaction_amount, 0) ELSE 0 END), 0)                 AS estimated_avoided_loss,
    SUM(CASE WHEN COALESCE(scenario, 'normal') = 'normal' AND decision = 'BLOCKED' THEN 1 ELSE 0 END) * 12.5 AS false_positive_cost,
    COALESCE(AVG(risk_score), 0)                                                                   AS avg_risk_score,
    COALESCE(AVG(fraud_probability), 0)                                                            AS avg_fraud_probability,
    MAX(created_at)                                                                                AS last_transaction_at
FROM banking_transactions;

-- 3. Fraud alerts ------------------------------------------------------
DROP VIEW IF EXISTS vw_powerbi_fraud_alerts;
CREATE VIEW vw_powerbi_fraud_alerts AS
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

-- 4. SHAP explanations, unnested to long format -----------------------
DROP VIEW IF EXISTS vw_powerbi_shap_explanations;
CREATE VIEW vw_powerbi_shap_explanations AS
SELECT
    s.transaction_id || '-' || (fn.key + 1)                AS explanation_id,
    s.transaction_id,
    fn.value                                               AS feature_name,
    json_extract(s.risk_contribution_score, '$.' || fn.value || '.value')  AS feature_value,
    sv.value                                               AS shap_value,
    CASE WHEN sv.value >= 0 THEN 'increases_risk' ELSE 'decreases_risk' END AS contribution_direction,
    json_extract(s.risk_contribution_score, '$.' || fn.value || '.reason') AS explanation_text,
    fn.key + 1                                             AS rank_importance,
    s.base_value,
    s.created_at
FROM banking_shap_explanations s,
     json_each(s.feature_names) fn,
     json_each(s.shap_values) sv
WHERE fn.key = sv.key;

-- 5. Model benchmark ---------------------------------------------------
DROP VIEW IF EXISTS vw_powerbi_model_benchmark;
CREATE VIEW vw_powerbi_model_benchmark AS
SELECT
    model_name, threshold_type, threshold_value,
    precision, recall, f1, mcc, roc_auc, pr_auc, specificity, balanced_accuracy,
    training_time, inference_time,
    fp AS false_positives, fn AS false_negatives, tp, tn,
    total_estimated_cost, estimated_avoided_loss, model_rank, selected_best_model
FROM model_benchmark_results;

-- 6. Cost comparison summary -------------------------------------------
DROP VIEW IF EXISTS vw_powerbi_cost_comparison;
CREATE VIEW vw_powerbi_cost_comparison AS
SELECT
    model_name, strategy AS threshold_type, threshold AS threshold_value,
    tp AS true_positives, tn AS true_negatives, fp AS false_positives, fn AS false_negatives,
    precision, recall, f1, mcc, pr_auc, roc_auc,
    fraud_loss AS fraud_loss_cost, fp_cost AS false_positive_cost, total_cost,
    savings_vs_default, savings_pct_vs_default, is_optimal_threshold
FROM cost_comparison_summary;

-- 7. Threshold optimization sweep --------------------------------------
DROP VIEW IF EXISTS vw_powerbi_threshold_optimization;
CREATE VIEW vw_powerbi_threshold_optimization AS
SELECT
    model_name, threshold AS threshold_value,
    precision, recall, f1, mcc, specificity,
    fp AS false_positives, fn AS false_negatives, tp, tn,
    fraud_loss, fp_cost, total_cost,
    is_f1_optimal, is_mcc_optimal, is_cost_optimal
FROM cost_analysis_sweep;

-- 8. Simulation effectiveness ------------------------------------------
DROP VIEW IF EXISTS vw_powerbi_simulation_effectiveness;
CREATE VIEW vw_powerbi_simulation_effectiveness AS
SELECT
    run_id AS simulation_run_id,
    started_at, stopped_at, status, rate_tps, fraud_ratio, model_version,
    generated_transactions, approved, suspicious, blocked,
    simulated_frauds, detected_frauds, missed_frauds, false_positives,
    estimated_avoided_loss,
    CASE WHEN simulated_frauds > 0 THEN 1.0 * detected_frauds / simulated_frauds ELSE 0 END AS detection_rate,
    CASE WHEN (detected_frauds + false_positives) > 0
         THEN 1.0 * detected_frauds / (detected_frauds + false_positives) ELSE 0 END        AS precision_on_blocked,
    CASE WHEN simulated_frauds > 0 THEN 1.0 * detected_frauds / simulated_frauds ELSE 0 END AS recall_on_fraud,
    CASE WHEN (generated_transactions - simulated_frauds) > 0
         THEN 1.0 * false_positives / (generated_transactions - simulated_frauds) ELSE 0 END AS false_positive_rate
FROM simulation_runs;

-- 9. Moroccan-context demonstration data (synthetic, clearly labelled) -
DROP VIEW IF EXISTS vw_powerbi_moroccan_context;
CREATE VIEW vw_powerbi_moroccan_context AS
SELECT
    t.city,
    COUNT(*)                                                                          AS transactions,
    SUM(CASE WHEN COALESCE(t.scenario, 'normal') <> 'normal' THEN 1 ELSE 0 END)       AS simulated_frauds,
    SUM(CASE WHEN t.decision = 'BLOCKED' THEN 1 ELSE 0 END)                           AS blocked,
    COALESCE(SUM(COALESCE(t.amount, t.transaction_amount, 0)), 0)                     AS total_amount,
    COALESCE(AVG(t.risk_score), 0)                                                    AS avg_risk_score,
    'Données synthétiques de démonstration — non représentatives de la fraude bancaire réelle au Maroc.' AS data_label,
    -- Same column order as the PostgreSQL view (lat/lon/fraud_rate appended last).
    AVG(t.latitude)                                                                   AS latitude,
    AVG(t.longitude)                                                                  AS longitude,
    CASE WHEN COUNT(*) > 0
         THEN 1.0 * SUM(CASE WHEN COALESCE(t.scenario, 'normal') <> 'normal' THEN 1 ELSE 0 END) / COUNT(*)
         ELSE 0 END                                                                  AS fraud_rate
FROM banking_transactions t
WHERE t.country = 'Morocco'
GROUP BY t.city;
