"""
Build a timestamped Power BI export bundle.

Creates ``exports/powerbi_bundle/YYYYMMDD_HHMMSS/`` containing every dataset a
Power BI report needs, plus a ``manifest.json`` with row counts and data-quality
checks. This is the **Import-mode fallback** to DirectQuery and the artefact you
hand in with the thesis.

It is non-destructive:
* Live datasets are read from the ``vw_powerbi_*`` views (falling back to base
  tables if the views are absent).
* Precomputed thesis CSVs are COPIED from ``reports/tables/`` — never moved or
  overwritten.
* Power BI assets (DAX, theme, data dictionary, readme) are copied from
  ``powerbi/`` when present.
* Each run writes to a fresh timestamped directory, so previous bundles are
  always preserved.

Usage
-----
    python scripts/build_powerbi_bundle.py
    python scripts/build_powerbi_bundle.py --limit 100000
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from sqlalchemy.orm import Session

from src.database.models import PowerBIExportLog
from src.database.session import engine, init_db, session_scope
from src.utils.config import PROJECT_ROOT, get_config
from src.utils.logger import get_logger

log = get_logger("scripts.build_powerbi_bundle")


def _bundle_root() -> Path:
    try:
        rel = get_config().powerbi.get("bundle_dir", "exports/powerbi_bundle")
    except AttributeError:
        rel = "exports/powerbi_bundle"
    p = Path(rel)
    return p if p.is_absolute() else PROJECT_ROOT / p


def _tables_dir() -> Path:
    try:
        rel = get_config().cost_analysis.get("tables_dir", "reports/tables")
    except AttributeError:
        rel = "reports/tables"
    p = Path(rel)
    return p if p.is_absolute() else PROJECT_ROOT / p


def _assets_dir() -> Path:
    return PROJECT_ROOT / "powerbi"


def _dump_sql(sql: str, path: Path, warnings: list) -> Optional[int]:
    """Read a SELECT into a CSV. Returns row count, or None on failure."""
    try:
        df = pd.read_sql(sql, engine)
    except Exception as exc:  # noqa: BLE001 - view/table may be absent
        warnings.append(f"Could not export {path.name}: {exc}")
        return None
    df.to_csv(path, index=False, encoding="utf-8")
    return len(df)


def _dump_with_fallback(view_sql: str, table_sql: str, path: Path, warnings: list) -> Optional[int]:
    try:
        df = pd.read_sql(view_sql, engine)
    except Exception:
        try:
            df = pd.read_sql(table_sql, engine)
            warnings.append(f"{path.name}: view missing, exported base table instead.")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Could not export {path.name}: {exc}")
            return None
    df.to_csv(path, index=False, encoding="utf-8")
    return len(df)


def _copy_artifact(src: Path, dst: Path, warnings: list) -> bool:
    if src.exists():
        shutil.copy2(src, dst)
        return True
    warnings.append(f"Missing artefact (skipped): {src.name}")
    return False


def build_bundle(db: Optional[Session] = None, row_limit: int = 50000,
                 output_root: Optional[Path] = None) -> dict:
    """Build one bundle directory and return its manifest dict."""
    init_db()
    lim = int(row_limit)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    root = (output_root or _bundle_root()) / stamp
    root.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    counts: dict[str, Optional[int]] = {}

    # --- Live datasets (views, with base-table fallback) ---
    counts["banking_transactions"] = _dump_with_fallback(
        f"SELECT * FROM vw_powerbi_live_transactions ORDER BY created_at DESC LIMIT {lim}",
        f"SELECT * FROM banking_transactions ORDER BY created_at DESC LIMIT {lim}",
        root / "banking_transactions.csv", warnings,
    )
    counts["banking_fraud_alerts"] = _dump_with_fallback(
        f"SELECT * FROM vw_powerbi_fraud_alerts ORDER BY timestamp DESC LIMIT {lim}",
        f"SELECT * FROM banking_alerts ORDER BY created_at DESC LIMIT {lim}",
        root / "banking_fraud_alerts.csv", warnings,
    )
    counts["banking_shap_explanations"] = _dump_with_fallback(
        f"SELECT * FROM vw_powerbi_shap_explanations LIMIT {lim}",
        f"SELECT * FROM banking_shap_explanations LIMIT {lim}",
        root / "banking_shap_explanations.csv", warnings,
    )
    counts["banking_customers"] = _dump_sql(
        f"SELECT * FROM banking_customers LIMIT {lim}",
        root / "banking_customers.csv", warnings,
    )
    counts["simulation_effectiveness_summary"] = _dump_with_fallback(
        "SELECT * FROM vw_powerbi_simulation_effectiveness ORDER BY started_at DESC",
        "SELECT * FROM simulation_runs ORDER BY started_at DESC",
        root / "simulation_effectiveness_summary.csv", warnings,
    )

    # --- Precomputed thesis CSV artefacts (copied) ---
    tdir = _tables_dir()
    if _copy_artifact(tdir / "model_comparison.csv", root / "model_benchmark_results.csv", warnings):
        counts["model_benchmark_results"] = _safe_rowcount(root / "model_benchmark_results.csv")
    _copy_artifact(tdir / "cost_comparison_summary.csv", root / "cost_comparison_summary.csv", warnings)
    if tdir.exists():
        for src in sorted(tdir.glob("cost_analysis_*.csv")):
            _copy_artifact(src, root / src.name, warnings)
        for src in sorted(tdir.glob("threshold_optimization_*.csv")):
            _copy_artifact(src, root / src.name, warnings)

    # --- Power BI assets (copied when present) ---
    adir = _assets_dir()
    for name in ("dax_measures.md", "fintech_fraud_theme.json",
                 "data_dictionary.csv", "powerbi_integration_readme.md",
                 "star_schema.md", "page_specifications.md",
                 "directquery_refresh_guide.md"):
        _copy_artifact(adir / name, root / name, warnings)

    # --- Provenance for the manifest ---
    best_model, best_threshold = _best_model_info()
    latest_run = _latest_run_info()

    # --- Data-quality checks ---
    quality = _quality_checks(root, counts, warnings)

    manifest = {
        "export_timestamp": datetime.utcnow().isoformat() + "Z",
        "bundle_dir": str(root),
        "simulation_run_id": latest_run.get("run_id"),
        "simulation_run_status": latest_run.get("status"),
        "best_model": best_model,
        "threshold_used": best_threshold,
        "row_limit": lim,
        "files": sorted(p.name for p in root.glob("*") if p.name != "manifest.json"),
        "row_counts": counts,
        "data_quality_checks": quality,
        "warnings": warnings,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")

    # --- Audit log row ---
    total_rows = sum(v for v in counts.values() if isinstance(v, int))
    _log_export(db, root, latest_run.get("run_id"), len(manifest["files"]), total_rows, warnings)

    log.info(f"Bundle written to {root} ({len(manifest['files'])} files, {total_rows} live rows).")
    if warnings:
        log.warning(f"{len(warnings)} warning(s): " + "; ".join(warnings[:5]))
    return manifest


def _safe_rowcount(path: Path) -> Optional[int]:
    try:
        return int(sum(1 for _ in path.open(encoding="utf-8")) - 1)
    except Exception:  # noqa: BLE001
        return None


def _best_model_info() -> tuple[Optional[str], Optional[float]]:
    try:
        df = pd.read_sql(
            "SELECT model_name, threshold_value FROM model_benchmark_results "
            "WHERE selected_best_model = 1 LIMIT 1",
            engine,
        )
        if not df.empty:
            return str(df.iloc[0]["model_name"]), _opt_float(df.iloc[0]["threshold_value"])
    except Exception:  # noqa: BLE001
        pass
    return None, None


def _latest_run_info() -> dict:
    try:
        df = pd.read_sql(
            "SELECT run_id, status FROM simulation_runs ORDER BY started_at DESC LIMIT 1",
            engine,
        )
        if not df.empty:
            return {"run_id": str(df.iloc[0]["run_id"]), "status": str(df.iloc[0]["status"])}
    except Exception:  # noqa: BLE001
        pass
    return {}


def _opt_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _quality_checks(root: Path, counts: dict, warnings: list) -> dict:
    """Validate joinability + non-empty critical datasets."""
    checks: dict[str, object] = {}
    tx = counts.get("banking_transactions") or 0
    alerts = counts.get("banking_fraud_alerts") or 0
    checks["transactions_present"] = tx > 0
    checks["alerts_not_exceeding_transactions"] = alerts <= tx if tx else True
    checks["benchmark_present"] = bool(counts.get("model_benchmark_results"))

    # Are SHAP transaction_ids a subset of exported transactions?
    try:
        tx_path = root / "banking_transactions.csv"
        shap_path = root / "banking_shap_explanations.csv"
        if tx_path.exists() and shap_path.exists():
            tx_ids = set(pd.read_csv(tx_path, usecols=["transaction_id"])["transaction_id"])
            shap_df = pd.read_csv(shap_path, usecols=["transaction_id"])
            orphans = int((~shap_df["transaction_id"].isin(tx_ids)).sum()) if not shap_df.empty else 0
            checks["shap_orphan_rows"] = orphans
            if orphans:
                warnings.append(f"{orphans} SHAP rows reference transactions outside the export window.")
    except Exception as exc:  # noqa: BLE001
        checks["shap_join_check"] = f"skipped: {exc}"
    return checks


def _log_export(db, root, run_id, file_count, total_rows, warnings):
    def _write(session):
        session.add(PowerBIExportLog(
            export_name="powerbi_bundle",
            bundle_dir=str(root),
            simulation_run_id=run_id,
            file_count=file_count,
            total_rows=total_rows,
            warnings=warnings or None,
        ))
    try:
        if db is not None:
            _write(db)
            db.commit()
        else:
            with session_scope() as session:
                _write(session)
    except Exception as exc:  # noqa: BLE001
        log.warning(f"Could not write export log: {exc}")


def main() -> None:
    p = argparse.ArgumentParser(description="Build a timestamped Power BI export bundle.")
    p.add_argument("--limit", type=int, default=50000, help="Max live rows per dataset.")
    args = p.parse_args()
    manifest = build_bundle(db=None, row_limit=args.limit)
    print(json.dumps({k: manifest[k] for k in ("bundle_dir", "files", "row_counts", "warnings")},
                     indent=2, default=str))


if __name__ == "__main__":
    main()
