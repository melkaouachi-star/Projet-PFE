-- Enterprise banking fraud-detection schema.
-- SQLAlchemy creates these tables automatically, but this PostgreSQL DDL is
-- included for architecture reviews, audits, and manual database provisioning.

CREATE TABLE banking_customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(64) UNIQUE NOT NULL,
    full_name VARCHAR(128) NOT NULL,
    age INTEGER NOT NULL,
    country VARCHAR(64) NOT NULL,
    city VARCHAR(64) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    account_age_days INTEGER NOT NULL,
    average_spending DOUBLE PRECISION NOT NULL,
    risk_profile VARCHAR(32) NOT NULL,
    behavior_pattern VARCHAR(64) NOT NULL,
    known_devices JSONB NOT NULL,
    usual_countries JSONB NOT NULL,
    fraud_history_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    country VARCHAR(64) NOT NULL,
    city VARCHAR(64) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    risk_score INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_locations_country_city ON locations(country, city);

CREATE TABLE ip_addresses (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(64) UNIQUE NOT NULL,
    reputation VARCHAR(32) NOT NULL,
    risk_score INTEGER NOT NULL DEFAULT 0,
    country VARCHAR(64),
    city VARCHAR(64),
    is_vpn BOOLEAN NOT NULL DEFAULT FALSE,
    is_tor BOOLEAN NOT NULL DEFAULT FALSE,
    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE device_information (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(96) UNIQUE NOT NULL,
    customer_id VARCHAR(64),
    browser VARCHAR(64) NOT NULL,
    operating_system VARCHAR(64) NOT NULL,
    trusted BOOLEAN NOT NULL DEFAULT FALSE,
    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_device_information_customer_id ON device_information(customer_id);

CREATE TABLE banking_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(96) UNIQUE NOT NULL,
    customer_id VARCHAR(64) NOT NULL,
    customer_name VARCHAR(128) NOT NULL,
    customer_age INTEGER NOT NULL,
    customer_risk_category VARCHAR(32) NOT NULL,
    transaction_amount DOUBLE PRECISION NOT NULL,
    transaction_currency VARCHAR(8) NOT NULL,
    merchant_name VARCHAR(128) NOT NULL,
    merchant_category VARCHAR(64) NOT NULL,
    transaction_date VARCHAR(16) NOT NULL,
    transaction_time VARCHAR(16) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    country VARCHAR(64) NOT NULL,
    city VARCHAR(64) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    ip_address VARCHAR(64) NOT NULL,
    device_id VARCHAR(96) NOT NULL,
    browser VARCHAR(64) NOT NULL,
    operating_system VARCHAR(64) NOT NULL,
    payment_method VARCHAR(48) NOT NULL,
    card_type VARCHAR(48) NOT NULL,
    transaction_status VARCHAR(32) NOT NULL,
    scenario VARCHAR(64) NOT NULL DEFAULT 'normal',
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_banking_transactions_timestamp ON banking_transactions(timestamp);
CREATE INDEX ix_banking_transactions_customer_id ON banking_transactions(customer_id);
CREATE INDEX ix_banking_transactions_country_city ON banking_transactions(country, city);
CREATE INDEX ix_banking_transactions_ip_address ON banking_transactions(ip_address);
CREATE INDEX ix_banking_transactions_device_id ON banking_transactions(device_id);

CREATE TABLE fraud_scores (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(96) NOT NULL,
    fraud_probability DOUBLE PRECISION NOT NULL,
    risk_score INTEGER NOT NULL,
    fraud_level VARCHAR(32) NOT NULL,
    decision VARCHAR(32) NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    dynamic_features JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_fraud_scores_transaction_id ON fraud_scores(transaction_id);
CREATE INDEX ix_fraud_scores_decision ON fraud_scores(decision);

CREATE TABLE shap_explanations (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(96) NOT NULL,
    base_value DOUBLE PRECISION NOT NULL,
    feature_names JSONB NOT NULL,
    shap_values JSONB NOT NULL,
    top_reasons JSONB NOT NULL,
    risk_contribution_score JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_shap_explanations_transaction_id ON shap_explanations(transaction_id);

CREATE TABLE banking_fraud_alerts (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(96) NOT NULL,
    customer_id VARCHAR(64) NOT NULL,
    customer_name VARCHAR(128) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    country VARCHAR(64) NOT NULL,
    city VARCHAR(64) NOT NULL,
    risk_score INTEGER NOT NULL,
    status VARCHAR(32) NOT NULL,
    message TEXT NOT NULL,
    acknowledged INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_banking_fraud_alerts_created_at ON banking_fraud_alerts(created_at);
CREATE INDEX ix_banking_fraud_alerts_customer_id ON banking_fraud_alerts(customer_id);

