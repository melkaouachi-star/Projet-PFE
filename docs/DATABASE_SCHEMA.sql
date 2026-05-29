-- PostgreSQL schema for the enterprise real-time banking fraud platform.
-- SQLAlchemy can create the same operational tables automatically at API
-- startup. This DDL is provided for database reviews, Power BI integration,
-- manual provisioning, and thesis documentation.

-- ---------------------------------------------------------------------
-- Legacy ML API tables
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(64),
    time_seconds DOUBLE PRECISION NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    raw_payload JSONB NOT NULL,
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_transactions_external_id ON transactions(external_id);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    fraud_probability DOUBLE PRECISION NOT NULL,
    risk_score INTEGER NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    decision VARCHAR(32) NOT NULL,
    explanation JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_predictions_transaction_id ON predictions(transaction_id);
CREATE INDEX IF NOT EXISTS ix_predictions_decision ON predictions(decision);

CREATE TABLE IF NOT EXISTS fraud_alerts (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL,
    prediction_id INTEGER NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'HIGH',
    message TEXT NOT NULL,
    acknowledged INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- Realistic banking simulation tables
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS banking_customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    full_name VARCHAR(128),
    age INTEGER,
    country VARCHAR(64),
    city VARCHAR(64),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    account_age_days INTEGER,
    average_spending DOUBLE PRECISION,
    risk_profile VARCHAR(32),
    behavior_pattern VARCHAR(64),
    known_devices JSONB,
    usual_countries JSONB,
    fraud_history_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_banking_customers_country ON banking_customers(country);
CREATE INDEX IF NOT EXISTS ix_banking_customers_risk_profile ON banking_customers(risk_profile);

CREATE TABLE IF NOT EXISTS banking_transactions (
    transaction_id VARCHAR(80) PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    customer_name VARCHAR(128),
    customer_age INTEGER,
    customer_risk_category VARCHAR(32),
    timestamp TIMESTAMP,
    country VARCHAR(64),
    city VARCHAR(64),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    ip_address VARCHAR(64),
    device_id VARCHAR(96),
    browser VARCHAR(64),
    operating_system VARCHAR(64),
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(8) DEFAULT 'USD',
    transaction_amount DOUBLE PRECISION,
    transaction_currency VARCHAR(8),
    transaction_date VARCHAR(16),
    transaction_time VARCHAR(16),
    merchant_name VARCHAR(128),
    merchant_category VARCHAR(64),
    payment_method VARCHAR(48),
    card_type VARCHAR(48),
    scenario VARCHAR(64),
    fraud_probability DOUBLE PRECISION,
    risk_score INTEGER,
    fraud_level VARCHAR(32),
    decision VARCHAR(32),
    transaction_status VARCHAR(32),
    model_version VARCHAR(64),
    raw_payload JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_banking_transactions_customer_id ON banking_transactions(customer_id);
CREATE INDEX IF NOT EXISTS ix_banking_transactions_timestamp ON banking_transactions(timestamp);
CREATE INDEX IF NOT EXISTS ix_banking_transactions_country ON banking_transactions(country);
CREATE INDEX IF NOT EXISTS ix_banking_transactions_merchant_category ON banking_transactions(merchant_category);
CREATE INDEX IF NOT EXISTS ix_banking_transactions_scenario ON banking_transactions(scenario);
CREATE INDEX IF NOT EXISTS ix_banking_transactions_decision ON banking_transactions(decision);
CREATE INDEX IF NOT EXISTS ix_banking_transactions_risk_score ON banking_transactions(risk_score);
CREATE INDEX IF NOT EXISTS ix_banking_transactions_created_at ON banking_transactions(created_at);

CREATE TABLE IF NOT EXISTS banking_alerts (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(80) NOT NULL,
    customer_id VARCHAR(64),
    customer_name VARCHAR(128),
    severity VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
    fraud_level VARCHAR(32),
    risk_score INTEGER,
    fraud_probability DOUBLE PRECISION,
    decision VARCHAR(32),
    amount DOUBLE PRECISION,
    currency VARCHAR(8),
    country VARCHAR(64),
    city VARCHAR(64),
    ip_address VARCHAR(64),
    message TEXT NOT NULL,
    top_reasons JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_banking_alerts_transaction_id ON banking_alerts(transaction_id);
CREATE INDEX IF NOT EXISTS ix_banking_alerts_customer_id ON banking_alerts(customer_id);
CREATE INDEX IF NOT EXISTS ix_banking_alerts_severity ON banking_alerts(severity);
CREATE INDEX IF NOT EXISTS ix_banking_alerts_created_at ON banking_alerts(created_at);

CREATE TABLE IF NOT EXISTS banking_shap_explanations (
    transaction_id VARCHAR(80) PRIMARY KEY,
    base_value DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    feature_names JSONB NOT NULL,
    shap_values JSONB NOT NULL,
    top_reasons JSONB NOT NULL,
    risk_contribution_score JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- Optional Power BI / thesis artifact tables
-- CSV exports also provide these datasets when direct PostgreSQL access is
-- unavailable.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_benchmark_results (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(96) NOT NULL,
    threshold_strategy VARCHAR(64),
    precision DOUBLE PRECISION,
    recall DOUBLE PRECISION,
    f1 DOUBLE PRECISION,
    mcc DOUBLE PRECISION,
    roc_auc DOUBLE PRECISION,
    pr_auc DOUBLE PRECISION,
    specificity DOUBLE PRECISION,
    balanced_accuracy DOUBLE PRECISION,
    false_positives INTEGER,
    false_negatives INTEGER,
    total_estimated_cost DOUBLE PRECISION,
    cost_saving_vs_default DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS threshold_optimization (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(96) NOT NULL,
    strategy VARCHAR(64) NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    tp INTEGER,
    fp INTEGER,
    tn INTEGER,
    fn INTEGER,
    precision DOUBLE PRECISION,
    recall DOUBLE PRECISION,
    f1 DOUBLE PRECISION,
    mcc DOUBLE PRECISION,
    fraud_loss DOUBLE PRECISION,
    fp_cost DOUBLE PRECISION,
    total_cost DOUBLE PRECISION,
    savings_vs_default DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cost_analysis (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(96) NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    tp INTEGER,
    fp INTEGER,
    tn INTEGER,
    fn INTEGER,
    precision DOUBLE PRECISION,
    recall DOUBLE PRECISION,
    f1 DOUBLE PRECISION,
    mcc DOUBLE PRECISION,
    specificity DOUBLE PRECISION,
    fraud_loss DOUBLE PRECISION,
    fp_cost DOUBLE PRECISION,
    total_cost DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS simulation_runs (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    rate_tps INTEGER,
    fraud_ratio DOUBLE PRECISION,
    generated_transactions INTEGER DEFAULT 0,
    detected_frauds INTEGER DEFAULT 0,
    missed_frauds INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    avoided_loss DOUBLE PRECISION DEFAULT 0,
    status VARCHAR(32) DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS powerbi_exports (
    id SERIAL PRIMARY KEY,
    export_name VARCHAR(128) NOT NULL,
    file_name VARCHAR(256) NOT NULL,
    row_count INTEGER,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- Power BI views
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW live_transactions AS
SELECT
    transaction_id,
    customer_id,
    customer_name,
    timestamp,
    country,
    city,
    latitude,
    longitude,
    ip_address,
    amount,
    currency,
    merchant_name,
    merchant_category,
    scenario,
    fraud_probability,
    risk_score,
    fraud_level,
    decision,
    transaction_status,
    model_version,
    created_at
FROM banking_transactions;

CREATE OR REPLACE VIEW fraud_alerts_powerbi AS
SELECT
    id,
    transaction_id,
    customer_id,
    customer_name,
    severity,
    fraud_level,
    risk_score,
    fraud_probability,
    decision,
    amount,
    currency,
    country,
    city,
    ip_address,
    message,
    created_at
FROM banking_alerts;

CREATE OR REPLACE VIEW shap_feature_importance AS
SELECT
    transaction_id,
    base_value,
    feature_names,
    shap_values,
    top_reasons,
    risk_contribution_score,
    created_at
FROM banking_shap_explanations;

CREATE OR REPLACE VIEW simulation_summary AS
SELECT
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE decision = 'BLOCKED') AS blocked_transactions,
    COUNT(*) FILTER (WHERE decision IN ('SUSPICIOUS', 'REVIEW')) AS suspicious_transactions,
    COUNT(*) FILTER (WHERE scenario <> 'normal') AS simulated_frauds,
    COUNT(*) FILTER (WHERE scenario <> 'normal' AND decision = 'BLOCKED') AS detected_frauds,
    COUNT(*) FILTER (WHERE scenario <> 'normal' AND decision <> 'BLOCKED') AS missed_frauds,
    COUNT(*) FILTER (WHERE scenario = 'normal' AND decision = 'BLOCKED') AS false_positives,
    COALESCE(SUM(amount) FILTER (WHERE scenario <> 'normal' AND decision = 'BLOCKED'), 0) AS estimated_avoided_loss
FROM banking_transactions;
