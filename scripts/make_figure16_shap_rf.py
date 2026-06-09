"""
Figure 16 (mémoire) : Importance globale des variables selon SHAP — Random Forest.
Rendu stylé à partir des VRAIES valeurs SHAP du Random Forest
(reports/tables/shap_top10_random_forest.csv), avec couleurs par catégorie métier.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.config import PROJECT_ROOT, get_config  # noqa: E402

cfg = get_config()
FIG_DIR = PROJECT_ROOT / cfg.paths.reports_figures
TAB = PROJECT_ROOT / cfg.paths.reports_tables / "shap_top10_random_forest.csv"

df = pd.read_csv(TAB)

# Catégorie métier (proxy) -> couleur, cohérente avec la taxonomie du mémoire
CAT = {
    "V14": ("Déviation comportementale", "#c0392b"),
    "V12_x_V10": ("Interaction (feature construite)", "#e67e22"),
    "V14_x_V17": ("Interaction (feature construite)", "#e67e22"),
    "V4": ("Géolocalisation (proxy)", "#2e86c1"),
    "V12": ("Temporalité", "#2980b9"),
    "V17": ("Canal de paiement (CNP)", "#16a085"),
    "V11": ("Pattern transactionnel", "#2980b9"),
    "V10": ("Pattern temporel", "#2980b9"),
    "V16": ("Déviation comportementale", "#c0392b"),
    "Log_Amount": ("Montant (feature construite)", "#e67e22"),
}
colors = [CAT.get(f, ("Autre", "#7f8c8d"))[1] for f in df["feature"]]

plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(11, 6.5))

order = df.iloc[::-1]
ocolors = colors[::-1]
bars = ax.barh(order["feature"], order["mean_abs_shap"], color=ocolors, edgecolor="white")
for b, v, p in zip(bars, order["mean_abs_shap"], order["share_pct"]):
    ax.text(v, b.get_y() + b.get_height() / 2, f"  {v:.4f}  ({p:.1f}%)",
            va="center", ha="left", fontsize=9.5)

ax.set_xlabel("Importance SHAP moyenne absolue  —  mean |SHAP value|  (espace probabilité)")
ax.set_title("Figure 16 : Importance globale des variables selon SHAP — Random Forest",
             fontweight="bold", fontsize=14, pad=14)
ax.margins(x=0.20)
ax.grid(axis="x", alpha=0.25)

# Légende des catégories métier
seen, handles = set(), []
for f, c in zip(df["feature"], colors):
    cat = CAT.get(f, ("Autre", "#7f8c8d"))[0]
    if cat not in seen:
        seen.add(cat)
        handles.append(Patch(facecolor=c, label=cat))
ax.legend(handles=handles, title="Catégorie métier (proxy)", loc="lower right",
          fontsize=8.5, title_fontsize=9, framealpha=0.95)

fig.text(0.5, -0.02,
         "Lecture analytique : V14 et les interactions construites V12×V10 et V14×V17 concentrent "
         "les contributions les plus fortes ; le montant transformé (Log_Amount) reste dans le Top 10.",
         ha="center", fontsize=9.5, style="italic")
fig.text(0.01, -0.06,
         "Source : valeurs SHAP RÉELLES (TreeSHAP) du modèle Random Forest calibré — jeu de test, dataset ULB. "
         "n = 2 575 transactions (75 fraudes + 2 500 légitimes).",
         ha="left", fontsize=8, color="#555555")

fig.tight_layout()
out = FIG_DIR / "Figure_16_shap_top10_random_forest.png"
fig.savefig(out, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"OK -> {out}")
