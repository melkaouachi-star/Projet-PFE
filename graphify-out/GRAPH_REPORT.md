# Graph Report - Projet PFE Code New  (2026-06-01)

## Corpus Check
- 95 files · ~119,289 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1382 nodes · 2793 edges · 111 communities (81 shown, 30 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 576 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4fa44ced`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]
- [[_COMMUNITY_Community 107|Community 107]]
- [[_COMMUNITY_Community 108|Community 108]]
- [[_COMMUNITY_Community 109|Community 109]]
- [[_COMMUNITY_Community 110|Community 110]]

## God Nodes (most connected - your core abstractions)
1. `get_config()` - 73 edges
2. `BankingTransaction` - 40 edges
3. `CustomerGenerator` - 40 edges
4. `TransactionGenerator` - 37 edges
5. `get_logger()` - 34 edges
6. `BankingCustomer` - 33 edges
7. `BankingAlert` - 33 edges
8. `ShapExplanationRecord` - 33 edges
9. `CostParameters` - 28 edges
10. `run_full_analysis()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `Temporal validation protections (anti-leakage)` --semantically_similar_to--> `Anti-leakage chronological validation`  [INFERRED] [semantically similar]
  docs/THESIS_DISCUSSION.md → src/training/validation.py
- `Dynamic fraud scoring (ML + rule overlay)` --conceptually_related_to--> `DynamicFraudScoringEngine`  [INFERRED]
  docs/ENTERPRISE.md → src/streaming/simulator.py
- `FraudDecisionEngine` --semantically_similar_to--> `Economic constants (FP cost 12.5, block threshold 70)`  [AMBIGUOUS] [semantically similar]
  src/api/decision_engine.py → sql/powerbi_views_postgres.sql
- `Banking router smoke tests` --references--> `REST API`  [INFERRED]
  tests/test_banking_router.py → README.md
- `Namespace` --uses--> `CostParameters`  [INFERRED]
  scripts/run_cost_analysis.py → src/evaluation/cost_analysis.py

## Import Cycles
- 1-file cycle: `src/api/main.py -> src/api/main.py`
- 1-file cycle: `src/database/crud.py -> src/database/crud.py`
- 1-file cycle: `src/database/models.py -> src/database/models.py`
- 1-file cycle: `src/scoring/dynamic_engine.py -> src/scoring/dynamic_engine.py`
- 1-file cycle: `src/simulation/transactions.py -> src/simulation/transactions.py`
- 1-file cycle: `src/streaming/simulator.py -> src/streaming/simulator.py`

## Hyperedges (group relationships)
- **Power BI DirectQuery analytics pipeline** — load_powerbi_warehouse_main, powerbi_views_postgres_live_transactions, build_powerbi_bundle_build_bundle, dbschema_banking_transactions, fintech_fraud_theme [INFERRED 0.85]
- **ML lifecycle CLI flow (train -> eval -> cost -> shap)** — run_training_main, run_evaluation_main, run_cost_analysis_main, run_shap_main [INFERRED 0.85]
- **Real-time scoring request path** — main_app, dependencies_engine_dep, decision_engine_fraud_decision_engine, decision_engine_score [INFERRED 0.85]
- **Banking score-persist-stream pipeline** — banking_predict_banking_transaction, crud_record_banking_assessment, banking_live_stream [INFERRED 0.85]
- **Asymmetric cost-analysis pipeline** — cost_analysis_threshold_sweep, cost_analysis_find_optimal_thresholds, cost_analysis_run_full_analysis, cost_analysis_cost_comparison_table [EXTRACTED 0.95]
- **Power BI export/warehouse data layer** — exports_bundle_entries, powerbi_query, models_additive_powerbi_layer, plots_model_comparison_csv [INFERRED 0.75]
- **Model builder factories with class_weight interface** — baseline_build_xgboost, baseline_build_lightgbm, baseline_build_catboost, baseline_build_random_forest, baseline_build_logistic_regression [INFERRED 0.85]
- **Class-imbalance resampling strategy family** — imbalance_get_sampler, imbalance_apply_strategy, imbalance_strategy_tradeoff_rationale [INFERRED 0.75]
- **Live transaction streaming + scoring pipeline** — transactions_transactiongenerator, dynamic_engine_dynamicfraudscoringengine, broker_eventbroker, simulator_simulationservice [INFERRED 0.85]
- **Containerised deployment topology (API + Postgres + Render)** — compose_api_service, compose_db_service, render_blueprint [INFERRED 0.85]
- **Anti-leakage temporal validation across code, config and thesis** — validation_time_series_splits, validation_anti_leakage, thesis_temporal_validation [INFERRED 0.85]
- **Cost-analysis subsystem and its test coverage** — test_cost_analysis_suite, test_cost_router_suite, config_yaml_cost_analysis, config_yaml_powerbi [INFERRED 0.75]
- **Power BI Star-Schema Tables** — star_schema_fact_transactions, star_schema_fact_fraud_alerts, star_schema_fact_shap, star_schema_fact_model_benchmark, star_schema_fact_cost_analysis, star_schema_fact_threshold_optimization, star_schema_fact_simulation, star_schema_dim_customer, star_schema_dim_moroccan_context, star_schema_live_kpis [EXTRACTED 1.00]
- **Power BI Report 10 Pages** — page_specifications_page1_executive, page_specifications_page2_transactions, page_specifications_page3_alerts, page_specifications_page4_cost, page_specifications_page5_benchmark, page_specifications_page6_best_model, page_specifications_page7_threshold, page_specifications_page8_shap, page_specifications_page9_morocco, page_specifications_page10_simulation [EXTRACTED 1.00]
- **Atlas Dashboard SPA Pages** — dashboard_html_overview_page, dashboard_html_transactions_page, dashboard_html_alerts_page, dashboard_html_benchmark_page, dashboard_html_cost_page, dashboard_html_threshold_page, dashboard_html_shap_page, dashboard_html_morocco_page, dashboard_html_simulation_page, dashboard_html_exports_page [EXTRACTED 1.00]
- **Headline KPI strip (Transactions, Total Amount, Blocked, Suspicious, Fraud Ratio, Avoided Loss)** —  [EXTRACTED 1.00]
- **Headline Fraud KPIs** —  [EXTRACTED 1.00]

## Communities (111 total, 30 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (106): ExportInventoryItem, ExportInventoryOut, Base, banking_analytics(), bulk_upsert_customers(), _coerce_timestamp(), create_alert(), create_prediction() (+98 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (75): ComputeCostAnalysisIn, CostAnalysisOut, CostAnalysisRowOut, CostOptimumOut, OptimalThresholdOut, POST body for live recompute against the banking_transactions table., ComputeCostAnalysisIn, _closest_row() (+67 more)

### Community 2 - "Community 2"
Cohesion: 0.16
Nodes (47): AlertRecord, BankingAlertRecord, BankingAnalyticsOut, BankingContribution, BankingCustomerOut, BankingDecisionOut, BankingShapExplanationOut, BankingTransactionIn (+39 more)

### Community 3 - "Community 3"
Cohesion: 0.15
Nodes (25): callable, build_catboost(), build_lightgbm(), build_logistic_regression(), build_random_forest(), build_xgboost(), Baseline & gradient-boosting model factories.  Each builder returns a *fresh*, Logistic regression baseline.      Notes     -----     - `n_jobs` was remove (+17 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (58): CostAnalysisSweep, CostComparisonSummary, ModelBenchmarkResult, PowerBIExportLog, Per-model benchmark metrics for Power BI (fact_model_benchmark)., One row per (model, strategy) optimum (fact_cost_analysis summary)., Full per-threshold sweep for one model (fact_threshold_optimization)., Audit log of generated Power BI export bundles. (+50 more)

### Community 5 - "Community 5"
Cohesion: 0.14
Nodes (27): compute_metrics(), Fraud-specific evaluation metrics.  We deliberately favour PR-AUC, MCC and F1, Compute the canonical fraud-detection metrics., comparison_table(), _fig_dir(), plot_confusion_matrix(), plot_metric_comparison(), plot_pr_curves() (+19 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (38): build_bundle (Power BI export bundle builder), Power BI Import-mode bundle (DirectQuery fallback), CatBoost training Logloss log (600 iterations), banking_alerts table, banking_shap_explanations table, banking_transactions table, cost_analysis table, model_benchmark_results table (+30 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (47): Architecture overview, Offline pipeline (eda->training->eval->shap), api service (fraud-api), db service (postgres:16, fraud-db), Config (dot-accessible dict), get_config() central config loader, Single-source-of-truth config principle, cost_analysis config block (asymmetric cost fn) (+39 more)

### Community 8 - "Community 8"
Cohesion: 0.23
Nodes (20): _fig_dir(), plot_amount_distribution(), plot_class_imbalance(), plot_correlation_heatmap(), plot_kde_amount(), plot_temporal_evolution(), plot_top_pca_boxplots(), plot_velocity() (+12 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (35): main(), CLI fraud bot for realistic banking transaction streams., CustomerGenerator, Synthetic customer generator for banking fraud simulations., Synthetic transaction and fraud-scenario generator., TransactionGenerator, Any, float (+27 more)

### Community 10 - "Community 10"
Cohesion: 0.10
Nodes (26): all_builders, build_catboost, build_lightgbm, build_logistic_regression, build_random_forest, build_xgboost, calibrate, Probability calibration importance in fraud (+18 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (39): DynamicFraudScoringEngine, EventBroker, Queue, assessment_dict(), assessment_to_event(), _coerce_datetime(), DynamicFraudScoringEngine, FeatureContribution (+31 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (24): EventBroker (pub/sub), BEHAVIOR_PATTERNS catalog, COUNTRY_CITIES catalog, SCENARIOS catalog, CustomerGenerator, CustomerGenerator.generate_customer, assessment_to_event, DynamicFraudScoringEngine (+16 more)

### Community 13 - "Community 13"
Cohesion: 0.10
Nodes (20): 10. Architecture cloud, 11. Checklist avant soutenance, 1. Verifier le projet en local, 2. Preparer GitHub, 3. Methode recommandee : Render Blueprint, 4.1 Creer PostgreSQL, 4.2 Creer le service API + dashboard, 4. Methode manuelle : Web Service + PostgreSQL (+12 more)

### Community 14 - "Community 14"
Cohesion: 0.24
Nodes (21): cost_summary(), customers(), export_bundle(), fraud_alerts(), kpis(), list_views(), model_benchmark(), moroccan_context() (+13 more)

### Community 15 - "Community 15"
Cohesion: 0.10
Nodes (20): *, bad, center, dataColors, foreground, foregroundNeutralSecondary, foregroundNeutralTertiary, good (+12 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (17): FraudPreprocessor, Robust-scales `Time` and `Amount`; leaves PCA features untouched., all_builders(), Return a name -> builder mapping for every enabled baseline., main(), parse_args(), Namespace, CLI entry point: run the full training pipeline.  Examples --------     pyth (+9 more)

### Community 17 - "Community 17"
Cohesion: 0.13
Nodes (18): EngineDecision, Real-time fraud decision engine.  Wraps the trained model + preprocessor + fea, get_default_explainer(), SHAP-based explainability layer.  Two responsibilities: 1. Offline - generate, Lazy-loaded singleton used by the FastAPI service., Wrap a fitted classifier so it can be explained efficiently., Compute the SHAP explanation of a single transaction., ShapExplainer (+10 more)

### Community 18 - "Community 18"
Cohesion: 0.16
Nodes (17): Alert: Aya Diallo BLOCKED - 1028 MAD Rabat, Risk 89, Alert: John Dubois BLOCKED - 2302 MAD Casablanca, Risk 100, Atlas Fraud AI - Real-time Banking Defense Branding, Concept: Real-time Fraud Detection and Prevention, Concept: Moroccan Banking Context (MAD transactions, Casablanca/Rabat), Atlas Fraud AI - Executive Overview Dashboard (QA), Panel: Fraud Alert Center (4 alerts, blocked critical transactions), Panel: Global Fraud Map (300 events, world map with geo-plotted transactions) (+9 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (16): Conditional formatting (Page 2 table) — Step 23, Power BI Build Walkthrough — follow-along for the 20-step order, Pre-defense checklist (§38–§40), ⚠️ Read first — 3 reconciliations between the guide and the real data, Step 10 — Measures (names match the guide; host on a `_Measures` table), Step 16 — FinTech theme, Step 17 — Automatic Page Refresh, Step 18 — Live test (while a simulation runs) (+8 more)

### Community 20 - "Community 20"
Cohesion: 0.07
Nodes (43): FraudDecisionEngine, get_engine(), Load a small background sample to enable KernelExplainer., Guarantee the inference row matches the training schema exactly.          - Mi, Drill through CalibratedClassifierCV / FrozenEstimator wrappers., Score a single transaction., Produce a list of human-readable bullet points., Singleton-style engine used by the FastAPI service. (+35 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (13): files, code, document, image, paper, video, graphifyignore_patterns, needs_graph (+5 more)

### Community 22 - "Community 22"
Cohesion: 0.15
Nodes (15): Concept: Account Takeover (ATO) Fraud Scenario, Concept: Detection Efficacy (Blocked vs False Positives), Concept: Geolocation of Transactions, Concept: Real-Time Fraud Monitoring, Fraud Command Center Dashboard (QA View), KPI: Blocked = 3, KPI: False Positives = 0, KPI: Frauds/Hour = 3 (+7 more)

### Community 23 - "Community 23"
Cohesion: 0.30
Nodes (14): _balanced_sample(), _fig_dir(), Dimensionality reduction & 2-D fraud visualisation maps.  Three techniques are, Return indices keeping all fraud + a random sample of legitimates., reduce_pca(), reduce_tsne(), reduce_umap(), _scatter_2d() (+6 more)

### Community 24 - "Community 24"
Cohesion: 0.20
Nodes (14): Seven Trained Models (LR/RF/XGB/LGBM/CatBoost/Voting/Stacking), requirements-api.txt (API runtime deps), catboost, requirements-dev.txt (dev deps), fastapi, lightgbm, requirements.txt (full deps), mlflow (+6 more)

### Community 25 - "Community 25"
Cohesion: 0.15
Nodes (13): color, fontFace, fontSize, color, fontFace, fontSize, textClasses, callout (+5 more)

### Community 26 - "Community 26"
Cohesion: 0.13
Nodes (17): FraudFeatureEngineer, Advanced fraud-oriented feature engineering.  All features are deterministic a, Transform a single incoming transaction.          Updates the internal history, Number of transactions occurring within the previous 60 seconds., Stateful feature engineer.      Stores statistics needed at inference time:, # IMPORTANT: always compute rolling features (even for tiny, Any, DataFrame (+9 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (15): load_powerbi_warehouse.py, Power BI Export Page, Live Event Stream + 5s Refresh, Automatic Page Refresh (APR), DirectQuery Connection Path, DirectQuery & Refresh Guide, JSON API / CSV Bundle Fallback, vw_powerbi_* PostgreSQL Views (+7 more)

### Community 28 - "Community 28"
Cohesion: 0.20
Nodes (12): Asymmetric cost C(s)=FN*C_FN+FP*C_FP, cost_comparison_table, CostParameters, find_optimal_thresholds, run_full_analysis runner, threshold_sweep, compute_live_cost_analysis endpoint, offline cost_analysis endpoint (+4 more)

### Community 29 - "Community 29"
Cohesion: 0.15
Nodes (12): DataFrame, int, Series, DataFrame, int, ndarray, optimize_xgboost(), Bayesian hyperparameter optimisation with Optuna.  Optimises XGBoost (the stro (+4 more)

### Community 30 - "Community 30"
Cohesion: 0.23
Nodes (11): chronological_split(), load_creditcard_dataset(), Dataset loader for the European Credit Card Fraud Detection dataset.  The raw, Load the European credit-card fraud dataset.      Parameters     ----------, Ensure the dataset has the expected columns., Split a dataset *chronologically* to avoid temporal leakage.      Random split, _validate_schema(), DataFrame (+3 more)

### Community 31 - "Community 31"
Cohesion: 0.17
Nodes (11): 1. Dataset, 2. Class-Imbalance Strategies, 3. Temporal Validation, 4. Explainability in Banking AI, 5. False Positive Reduction, 6. Concept Drift & Evolving Fraud Strategies, 7. Ethical Concerns, 8. Summary of Contributions (+3 more)

### Community 32 - "Community 32"
Cohesion: 0.18
Nodes (10): iterations, meta, iteration_count, launch_mode, learn_metrics, learn_sets, name, parameters (+2 more)

### Community 33 - "Community 33"
Cohesion: 0.17
Nodes (12): Fraud Alerts Page, Atlas Fraud Intelligence Dashboard (React SPA), Chart.js Visualisation Wrapper, Cost Analysis Page, Leaflet Geographic Map, Executive Overview Page, Simulation Control Page, Threshold Optimization Page (+4 more)

### Community 34 - "Community 34"
Cohesion: 0.18
Nodes (11): Asymmetric Cost Framework C(s)=FN*C_FN+FP*C_FP, Economic Evaluation Measures (asymmetric cost), Power BI Page Specifications, Page 10 — Simulation Effectiveness, Page 2 — Live Transactions Analysis, Page 3 — Fraud Rate & Operational Alerts, Page 4 — Losses Avoided & Cost Analysis, Page 6 — Best Model Deep Dive (+3 more)

### Community 35 - "Community 35"
Cohesion: 0.18
Nodes (11): calloutValue, *, *, *, trend, valueAxis, visualStyles, cardVisual (+3 more)

### Community 36 - "Community 36"
Cohesion: 0.18
Nodes (10): build, builder, dockerfilePath, deploy, healthcheckPath, healthcheckTimeout, restartPolicyMaxRetries, restartPolicyType (+2 more)

### Community 37 - "Community 37"
Cohesion: 0.25
Nodes (10): apply_strategy(), get_sampler(), Class-imbalance handling strategies.  Returns a sklearn-compatible *sampler* o, Return an imblearn sampler. Returns None for 'none'/'class_weight'., Apply a resampling strategy and return the new (X, y)., DataFrame, float, int (+2 more)

### Community 38 - "Community 38"
Cohesion: 0.17
Nodes (11): PAGE 10 — Simulation Effectiveness and Validation, PAGE 1 — Executive Live Fraud Monitoring, PAGE 2 — Live Transactions Analysis, PAGE 3 — Fraud Rate and Operational Alerts, PAGE 4 — Losses Avoided and Cost Analysis, PAGE 5 — Model Benchmarking, PAGE 6 — Best Model Deep Dive, PAGE 7 — Threshold Optimization (+3 more)

### Community 39 - "Community 39"
Cohesion: 0.22
Nodes (10): create_alert, create_prediction, create_transaction, explain_transaction endpoint, Prediction (legacy) ORM model, Transaction (legacy) ORM model, Monitoring router, predict_batch endpoint (+2 more)

### Community 40 - "Community 40"
Cohesion: 0.22
Nodes (9): Avoided Fraud Loss Measure, Confusion Matrix Measures (TP/FP/FN/TN), DAX Measures Library, Fraud Rate Measure, _Measures Hosting Table, Optimal Threshold Measure, Precision / Recall / F1 Score Measures, Time-based Near-Real-Time Measures (+1 more)

### Community 41 - "Community 41"
Cohesion: 0.42
Nodes (9): dim_customer, dim_date (generated), dim_decision_status (generated), dim_risk_level (generated), Power BI Star Schema, fact_fraud_alerts, fact_shap, fact_transactions (+1 more)

### Community 42 - "Community 42"
Cohesion: 0.25
Nodes (9): banking_analytics aggregator, finalize_simulation_run, export_simulation_summary endpoint, Additive Power BI analytical layer, BankingTransaction ORM model, SimulationRun ORM model, SQLAlchemy declarative Base, _ensure_banking_schema_compat migration (+1 more)

### Community 43 - "Community 43"
Cohesion: 0.22
Nodes (9): _decision_out helper, predict_banking_transaction endpoint, shap_explanation endpoint, Legacy vs banking CRUD separation, record_banking_assessment, ShapExplanationRecord ORM model, BankingDecisionOut schema, BankingTransactionIn schema (+1 more)

### Community 44 - "Community 44"
Cohesion: 0.28
Nodes (8): Any, Path, str, dump_json(), I/O helpers shared across the project (model persistence, JSON dumps)., Persist any picklable object to `models_store/<name>.pkl`., Write JSON to disk creating parent directories if needed., save_model()

### Community 45 - "Community 45"
Cohesion: 0.25
Nodes (8): Decision Colour Measure, Power BI Build Walkthrough, FinTech Fraud Theme JSON, No SHAP Double-Count Principle, Guide vs Real Data Reconciliations, Risk Band Calculated Column, transaction_hour Column, One Fact Per Grain / Offline-vs-Live Separation

### Community 46 - "Community 46"
Cohesion: 0.17
Nodes (11): Contents, How the pieces fit (existing backend), Option 1 — DirectQuery (recommended, near-real-time), Option 2 — Import-mode bundle (offline / no DB access), Option 3 — Web/JSON connector (live, no DB driver), Power BI Integration — Fraud Detection Platform, Prerequisite data (so all pages populate), Quick start (+3 more)

### Community 47 - "Community 47"
Cohesion: 0.38
Nodes (6): main(), parse_args(), CostParameters, Namespace, CLI: run the formal asymmetric cost-function evaluation for every trained model, _resolve_params()

### Community 48 - "Community 48"
Cohesion: 0.29
Nodes (7): Moroccan Context Page, SHAP Explainability Page, Honest Labelling / Synthetic Disclaimer Principle, Page 8 — SHAP Explainability, Page 9 — Moroccan Context, dim_moroccan_context, Field Classification (honest reporting)

### Community 49 - "Community 49"
Cohesion: 0.29
Nodes (7): background, header, items, outspace, *, *, slicer

### Community 50 - "Community 50"
Cohesion: 0.40
Nodes (6): _balanced_sample, reduce_pca, reduce_tsne, reduce_umap, _scatter_2d, ShapExplainer.global_plots

### Community 51 - "Community 51"
Cohesion: 0.33
Nodes (6): run_full_eda orchestrator, EDA _save figure helper, load_creditcard_dataset, _validate_schema helper, FraudPreprocessor, Stateful preprocessor reused at inference

### Community 52 - "Community 52"
Cohesion: 0.33
Nodes (6): _bundle_entries helper, export_powerbi_zip endpoint, CSV/ZIP offline Power BI bridge, BankingAlert ORM model, BankingCustomer ORM model, export_bundle endpoint

### Community 53 - "Community 53"
Cohesion: 0.40
Nodes (5): _inventory_items helper, compute_metrics, Prefer PR-AUC/MCC/F1 over ROC-AUC under imbalance, comparison_table writer, model_comparison.csv artefact

### Community 54 - "Community 54"
Cohesion: 0.40
Nodes (5): border, *, categoryLabels, labels, card

### Community 55 - "Community 55"
Cohesion: 0.40
Nodes (5): columnHeaders, grid, *, values, tableEx

### Community 56 - "Community 56"
Cohesion: 0.20
Nodes (9): dict, Any, Path, str, Config, Central configuration loader.  Loads the YAML config file once and exposes a t, Dot-accessible config dictionary., Resolve a path declared in config relative to the project root. (+1 more)

### Community 57 - "Community 57"
Cohesion: 0.15
Nodes (11): Preprocessing pipeline: scaling, NaN handling, feature ordering.  The preproce, calibrate(), Probability calibration utilities.  Calibration is critical in fraud detection, Wrap an already-fitted estimator into a calibrated classifier.      Works on b, str, str, get_logger(), _initialise_logger() (+3 more)

### Community 58 - "Community 58"
Cohesion: 0.18
Nodes (10): A. One-time setup, B.1 Local Docker connection settings, B.2 Fix: "SSL connection requested. No SSL enabled connection", B. Connect Power BI Desktop (DirectQuery), C. Automatic page refresh (near-real-time), D. Power BI Service (optional, scheduled), DirectQuery & Near-Real-Time Refresh Guide, E. Indexes for live analytics (already in the model) (+2 more)

### Community 59 - "Community 59"
Cohesion: 0.50
Nodes (4): Model Benchmarking Page, Best Model Measures, Page 5 — Model Benchmarking, fact_model_benchmark

### Community 60 - "Community 60"
Cohesion: 0.50
Nodes (4): color, fontFace, fontSize, label

### Community 62 - "Community 62"
Cohesion: 0.67
Nodes (3): vw_powerbi_* views single source of truth, list_views endpoint, _query view helper

### Community 105 - "Community 105"
Cohesion: 0.24
Nodes (9): ndarray, str, Tests for the threshold optimiser., With a very high FN cost, the optimal threshold should be lower., test_cost_sensitive_prefers_fewer_misses(), test_f1_threshold_returns_valid_value(), best_threshold(), Decision-threshold optimisation.  The default 0.5 threshold is almost never co (+1 more)

### Community 106 - "Community 106"
Cohesion: 0.20
Nodes (9): 1. Capabilities, 2. Fraud Scenarios, 3. Dynamic Fraud Scoring, 4. WebSocket payload, 5. Operating the platform, Decision bands, Enterprise Fraud Detection Platform - Functional Spec, Fraud levels (+1 more)

### Community 107 - "Community 107"
Cohesion: 0.20
Nodes (9): 1. Basic monitoring, 2. Fraud monitoring (confusion matrix from simulation ground truth), 3. Economic evaluation (asymmetric cost framework), 4. Model analysis (from fact_model_benchmark), 5. Time-based measures (near-real-time), 6. Conditional-formatting helper (decision colour), DAX Measures — FinTech Fraud Detection Dashboard, Important scale & constant notes (do not guess) (+1 more)

### Community 108 - "Community 108"
Cohesion: 0.22
Nodes (8): 1. Local, 2. Docker Compose (recommended), 3. Render, 4. Railway, 5. HuggingFace Spaces, 6. AWS, Deployment guide, Environment variables

### Community 109 - "Community 109"
Cohesion: 0.29
Nodes (6): Classification of fields (for honest reporting), Connecting the sources, Generated (calculated) dimensions, Power BI Star Schema — FinTech Fraud Detection, Relationships, Why this shape

## Ambiguous Edges - Review These
- `Economic constants (FP cost 12.5, block threshold 70)` → `FraudDecisionEngine`  [AMBIGUOUS]
  src/api/decision_engine.py · relation: semantically_similar_to

## Knowledge Gaps
- **318 isolated node(s):** `allow`, `code`, `document`, `paper`, `image` (+313 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Economic constants (FP cost 12.5, block threshold 70)` and `FraudDecisionEngine`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `get_logger()` connect `Community 57` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 37`, `Community 8`, `Community 105`, `Community 11`, `Community 14`, `Community 47`, `Community 16`, `Community 17`, `Community 20`, `Community 23`, `Community 26`, `Community 29`, `Community 30`?**
  _High betweenness centrality (0.214) - this node is a cross-community bridge._
- **Why does `Banking router smoke tests` connect `Community 11` to `Community 43`, `Community 7`?**
  _High betweenness centrality (0.178) - this node is a cross-community bridge._
- **Why does `REST API` connect `Community 7` to `Community 11`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `BankingTransaction` (e.g. with `ComputeCostAnalysisIn` and `ExportInventoryItem`) actually correct?**
  _`BankingTransaction` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `CustomerGenerator` (e.g. with `BankingDecisionOut` and `BankingTransactionIn`) actually correct?**
  _`CustomerGenerator` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `TransactionGenerator` (e.g. with `DynamicFraudScoringEngine` and `EventBroker`) actually correct?**
  _`TransactionGenerator` has 13 INFERRED edges - model-reasoned connections that need verification._