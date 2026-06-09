"""
Livrables mémoire (modèle Random Forest) :

  1. Top 10 des variables par importance SHAP  -> valeurs (CSV) + figures (bar + beeswarm)
  2. Distribution des montants & analyse temporelle  -> valeurs (CSV) + figures

Exécution :
    python scripts/run_rf_shap_amount_time.py
Sorties :
    reports/tables/   (CSV de valeurs)
    reports/figures/  (PNG 300 dpi)
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.config import PROJECT_ROOT, get_config  # noqa: E402
from src.utils.io import load_model  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

log = get_logger("scripts.rf_shap_amount_time")

cfg = get_config()
FIG_DIR = PROJECT_ROOT / cfg.paths.reports_figures
TAB_DIR = PROJECT_ROOT / cfg.paths.reports_tables
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "font.size": 11,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

FRAUD_C = "#d62728"
LEGIT_C = "#1f77b4"


def _underlying_rf(model):
    """Extract the raw RandomForestClassifier from a CalibratedClassifierCV(FrozenEstimator)."""
    from sklearn.ensemble import RandomForestClassifier

    est = model
    if hasattr(est, "calibrated_classifiers_"):
        est = est.calibrated_classifiers_[0].estimator  # FrozenEstimator
    # FrozenEstimator proxies attributes, so unwrap by type until we reach the RF
    while not isinstance(est, RandomForestClassifier) and hasattr(est, "estimator"):
        est = est.estimator
    return est


# ======================================================================
# 1. TOP 10 SHAP - RANDOM FOREST
# ======================================================================
def shap_top10(X: pd.DataFrame, y: pd.Series, sample: int = 2500) -> pd.DataFrame:
    log.info("Chargement du modèle random_forest...")
    rf = _underlying_rf(load_model("random_forest"))

    # Échantillon stratifié : sous-échantillon de légitimes + TOUTES les fraudes
    rng = np.random.RandomState(42)
    legit_idx = X.index[y == 0]
    fraud_idx = X.index[y == 1]
    n_legit = min(sample, len(legit_idx))
    chosen = np.concatenate([
        rng.choice(legit_idx, n_legit, replace=False),
        fraud_idx.to_numpy(),
    ])
    Xs = X.loc[chosen]
    log.info(f"Calcul SHAP sur {len(Xs)} transactions ({len(fraud_idx)} fraudes)...")

    explainer = shap.TreeExplainer(rf)
    sv = explainer(Xs, check_additivity=False)
    values = np.array(sv.values)
    if values.ndim == 3:           # (n, features, classes) -> classe fraude
        values = values[:, :, 1]

    mean_abs = np.abs(values).mean(axis=0)
    imp = (pd.DataFrame({"feature": Xs.columns, "mean_abs_shap": mean_abs})
           .sort_values("mean_abs_shap", ascending=False)
           .reset_index(drop=True))
    imp["rank"] = imp.index + 1
    imp["share_pct"] = 100 * imp["mean_abs_shap"] / imp["mean_abs_shap"].sum()

    top10 = imp.head(10).copy()

    # --- Valeurs (CSV) ---
    out_csv = TAB_DIR / "shap_top10_random_forest.csv"
    top10[["rank", "feature", "mean_abs_shap", "share_pct"]].to_csv(out_csv, index=False)
    log.info(f"CSV valeurs SHAP -> {out_csv}")

    # --- Figure bar Top 10 ---
    fig, ax = plt.subplots(figsize=(9, 6))
    order = top10.iloc[::-1]
    bars = ax.barh(order["feature"], order["mean_abs_shap"], color="#2a9d8f")
    ax.set_xlabel("Importance SHAP moyenne  ( mean |SHAP value| )")
    ax.set_title("Top 10 des variables par importance SHAP — Random Forest", fontweight="bold")
    for b, v, p in zip(bars, order["mean_abs_shap"], order["share_pct"]):
        ax.text(v, b.get_y() + b.get_height() / 2, f"  {v:.4f} ({p:.1f}%)",
                va="center", ha="left", fontsize=9)
    ax.margins(x=0.18)
    fig.tight_layout()
    p_bar = FIG_DIR / "34_shap_top10_random_forest.png"
    fig.savefig(p_bar, bbox_inches="tight"); plt.close(fig)
    log.info(f"Figure bar Top 10 -> {p_bar}")

    # --- Figure beeswarm (Top 10) ---
    top_names = top10["feature"].tolist()
    col_idx = [Xs.columns.get_loc(c) for c in top_names]
    plt.figure(figsize=(10, 7))
    shap.summary_plot(values[:, col_idx], Xs[top_names], show=False, plot_size=None)
    plt.title("Distribution des contributions SHAP (Top 10) — Random Forest", fontweight="bold")
    p_bee = FIG_DIR / "35_shap_beeswarm_top10_random_forest.png"
    plt.savefig(p_bee, bbox_inches="tight"); plt.close()
    log.info(f"Figure beeswarm Top 10 -> {p_bee}")

    # --- Figure dependence plot sur la variable dominante (V14) ---
    top_feature = top10.iloc[0]["feature"]
    plt.figure(figsize=(8, 5.5))
    shap.dependence_plot(top_feature, values, Xs, show=False)
    plt.title(f"Dependence plot SHAP — {top_feature} (Random Forest)", fontweight="bold")
    p_dep = FIG_DIR / f"38_shap_dependence_{top_feature}_random_forest.png"
    plt.savefig(p_dep, bbox_inches="tight"); plt.close()
    log.info(f"Figure dependence -> {p_dep}")

    # --- Figure waterfall : explication locale d'une fraude réelle ---
    base = np.array(sv.base_values)
    base_fraud = float(base[..., 1].flatten()[0]) if base.ndim > 1 else float(base.flatten()[0])
    pos = Xs.index.get_indexer([fraud_idx[0]])[0]  # 1re fraude présente dans l'échantillon
    exp = shap.Explanation(
        values=values[pos],
        base_values=base_fraud,
        data=Xs.iloc[pos].values,
        feature_names=list(Xs.columns),
    )
    plt.figure(figsize=(9, 6))
    shap.plots.waterfall(exp, max_display=12, show=False)
    plt.title("Explication SHAP locale d'une fraude réelle — Random Forest", fontweight="bold")
    p_wf = FIG_DIR / "39_shap_waterfall_fraude_random_forest.png"
    plt.savefig(p_wf, bbox_inches="tight"); plt.close()
    log.info(f"Figure waterfall -> {p_wf}")

    print("\n================ TOP 10 SHAP — RANDOM FOREST ================")
    print(top10[["rank", "feature", "mean_abs_shap", "share_pct"]]
          .to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    return top10


# ======================================================================
# 2. DISTRIBUTION DES MONTANTS & ANALYSE TEMPORELLE
# ======================================================================
def amount_and_time(df: pd.DataFrame) -> None:
    legit = df[df["Class"] == 0]
    fraud = df[df["Class"] == 1]

    # ---------- 2.a Tableau récapitulatif des montants ----------
    def _stats(s: pd.Series) -> dict:
        return {
            "n": int(s.size), "mean": s.mean(), "median": s.median(),
            "std": s.std(), "min": s.min(), "p95": s.quantile(0.95),
            "max": s.max(), "sum": s.sum(),
        }

    amt_tbl = pd.DataFrame({
        "Légitime": _stats(legit["Amount"]),
        "Fraude": _stats(fraud["Amount"]),
    }).T
    amt_tbl.index.name = "classe"
    amt_csv = TAB_DIR / "amount_distribution_by_class.csv"
    amt_tbl.to_csv(amt_csv)
    log.info(f"CSV distribution montants -> {amt_csv}")

    # ---------- 2.b Figure distribution des montants ----------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Histogramme densité (échelle log sur le montant)
    bins = np.logspace(0, np.log10(max(df["Amount"].max(), 1)), 50)
    axes[0].hist(legit["Amount"].clip(lower=0.01), bins=bins, density=True,
                 alpha=0.55, color=LEGIT_C, label="Légitime")
    axes[0].hist(fraud["Amount"].clip(lower=0.01), bins=bins, density=True,
                 alpha=0.65, color=FRAUD_C, label="Fraude")
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Montant (€, échelle log)")
    axes[0].set_ylabel("Densité")
    axes[0].set_title("Distribution des montants — Fraude vs Légitime")
    axes[0].legend()

    # Boxplot comparatif
    axes[1].boxplot([legit["Amount"], fraud["Amount"]], tick_labels=["Légitime", "Fraude"],
                    showfliers=False, patch_artist=True,
                    boxprops=dict(facecolor="#e9ecef"),
                    medianprops=dict(color="#d62728", linewidth=2))
    axes[1].set_ylabel("Montant (€)")
    axes[1].set_title("Comparaison des montants (hors valeurs extrêmes)")
    axes[1].text(0.02, 0.95,
                 f"Médiane légitime : {legit['Amount'].median():.2f} €\n"
                 f"Médiane fraude  : {fraud['Amount'].median():.2f} €",
                 transform=axes[1].transAxes, va="top", fontsize=10,
                 bbox=dict(boxstyle="round", fc="white", ec="#ced4da"))
    fig.suptitle("Analyse de la distribution des montants", fontweight="bold")
    fig.tight_layout()
    p_amt = FIG_DIR / "36_amount_distribution.png"
    fig.savefig(p_amt, bbox_inches="tight"); plt.close(fig)
    log.info(f"Figure distribution montants -> {p_amt}")

    # ---------- 2.c Analyse temporelle ----------
    # 'Hour' = heure dérivée (0-23) ; sinon reconstruite depuis 'Time' (secondes).
    if "Hour" in df.columns:
        df = df.assign(_hour=df["Hour"].round().astype(int).clip(0, 23))
    else:
        df = df.assign(_hour=((df["Time"] // 3600) % 24).astype(int))

    by_hour = df.groupby("_hour").agg(
        total=("Class", "size"),
        fraudes=("Class", "sum"),
    )
    by_hour["taux_fraude_pct"] = 100 * by_hour["fraudes"] / by_hour["total"]
    by_hour = by_hour.reindex(range(24), fill_value=0)
    time_csv = TAB_DIR / "fraud_by_hour.csv"
    by_hour.to_csv(time_csv)
    log.info(f"CSV analyse temporelle -> {time_csv}")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Volume vs taux de fraude par heure
    ax1 = axes[0]
    ax1.bar(by_hour.index, by_hour["total"], color=LEGIT_C, alpha=0.55, label="Volume total")
    ax1.set_xlabel("Heure de la journée")
    ax1.set_ylabel("Nombre de transactions", color=LEGIT_C)
    ax1.set_xticks(range(0, 24, 2))
    ax2 = ax1.twinx()
    ax2.plot(by_hour.index, by_hour["taux_fraude_pct"], color=FRAUD_C,
             marker="o", linewidth=2, label="Taux de fraude (%)")
    ax2.set_ylabel("Taux de fraude (%)", color=FRAUD_C)
    ax2.grid(False)
    ax1.set_title("Volume & taux de fraude par heure")

    # Jour vs Nuit
    if "Is_Night" in df.columns:
        night_flag = df["Is_Night"].astype(int)
    else:
        night_flag = ((df["_hour"] < 6) | (df["_hour"] >= 22)).astype(int)
    seg = df.assign(_night=night_flag).groupby("_night").agg(
        total=("Class", "size"), fraudes=("Class", "sum"))
    seg["taux_fraude_pct"] = 100 * seg["fraudes"] / seg["total"]
    seg = seg.reindex([0, 1], fill_value=0)
    labels = ["Jour (06h-22h)", "Nuit (22h-06h)"]
    axes[1].bar(labels, seg["taux_fraude_pct"], color=["#457b9d", "#1d3557"])
    axes[1].set_ylabel("Taux de fraude (%)")
    axes[1].set_title("Taux de fraude — Jour vs Nuit")
    for i, v in enumerate(seg["taux_fraude_pct"]):
        axes[1].text(i, v, f"{v:.3f}%", ha="center", va="bottom", fontsize=10)

    fig.suptitle("Analyse temporelle des transactions", fontweight="bold")
    fig.tight_layout()
    p_time = FIG_DIR / "37_temporal_analysis.png"
    fig.savefig(p_time, bbox_inches="tight"); plt.close(fig)
    log.info(f"Figure analyse temporelle -> {p_time}")

    print("\n================ DISTRIBUTION DES MONTANTS ================")
    print(amt_tbl.to_string(float_format=lambda x: f"{x:,.2f}"))
    print("\n================ TAUX DE FRAUDE PAR HEURE (extrait) ================")
    print(by_hour.sort_values("taux_fraude_pct", ascending=False).head(8)
          .to_string(float_format=lambda x: f"{x:.3f}"))
    print("\n================ JOUR vs NUIT ================")
    print(seg.to_string(float_format=lambda x: f"{x:.3f}"))


def main() -> None:
    # Livrable 1 : SHAP sur les features du modèle (jeu de test traité)
    test = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "test_features.parquet")
    shap_top10(test.drop(columns=["Class"]), test["Class"])

    # Livrable 2 : montants réels (€) + temps réel -> jeu BRUT (Amount/Time non standardisés)
    raw = pd.read_csv(PROJECT_ROOT / cfg.paths.data_raw)
    amount_and_time(raw)
    log.info("Terminé : 2 livrables (SHAP Top 10 + montants/temporel) générés.")


if __name__ == "__main__":
    main()
