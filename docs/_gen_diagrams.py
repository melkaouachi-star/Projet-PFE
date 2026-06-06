# -*- coding: utf-8 -*-
"""Generate schematic diagrams (schemas) for the empirical-part DOCX."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

OUT = os.path.join(os.path.dirname(__file__), "_empirical_figures")
os.makedirs(OUT, exist_ok=True)

# FinTech palette
INK     = "#0F172A"   # slate-900
SLATE   = "#1E293B"
BLUE    = "#2563EB"
BLUE_L  = "#DBEAFE"
CYAN    = "#0891B2"
CYAN_L  = "#CFFAFE"
GREEN   = "#059669"
GREEN_L = "#D1FAE5"
AMBER   = "#D97706"
AMBER_L = "#FEF3C7"
RED     = "#DC2626"
RED_L   = "#FEE2E2"
VIOLET  = "#7C3AED"
VIOLET_L= "#EDE9FE"
GREY    = "#475569"
GREY_L  = "#F1F5F9"
WHITE   = "#FFFFFF"

plt.rcParams["font.family"] = "DejaVu Sans"


def box(ax, x, y, w, h, text, fc, ec, tc=INK, fs=10, bold=False, rounding=0.04):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0.012,rounding_size={rounding}",
                       linewidth=1.5, edgecolor=ec, facecolor=fc, mutation_aspect=1)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, fontweight="bold" if bold else "normal",
            wrap=True, zorder=5)


def arrow(ax, x1, y1, x2, y2, color=GREY, lw=1.8, style="-|>", ls="-"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                        linewidth=lw, color=color, linestyle=ls,
                        shrinkA=2, shrinkB=2, zorder=3)
    ax.add_patch(a)


def lane(ax, x, y, w, h, title, color):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.03",
                       linewidth=1.4, edgecolor=color, facecolor="none",
                       linestyle=(0, (6, 3)), zorder=1)
    ax.add_patch(p)
    ax.text(x + 0.12, y + h - 0.18, title, ha="left", va="center",
            fontsize=10.5, color=color, fontweight="bold")


def base(figsize):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 16)
    ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches="tight",
                facecolor="white", pad_inches=0.15)
    plt.close(fig)
    print("wrote", name)


# ============================================================
# FIGURE 1 — Architecture globale (deux volets)
# ============================================================
fig, ax = base((13.5, 8.0))
ax.set_ylim(0, 10)

ax.text(8, 9.6, "Architecture generale du systeme — deux volets complementaires",
        ha="center", fontsize=13, fontweight="bold", color=INK)

# Lane A — offline
lane(ax, 0.3, 5.6, 7.2, 3.5, "VOLET 1 — Apprentissage supervise (hors-ligne)", BLUE)
box(ax, 0.7, 8.0, 2.0, 0.9, "Jeu de donnees\ncreditcard.csv\n284 807 tx", BLUE_L, BLUE, fs=8.5)
box(ax, 3.0, 8.0, 2.0, 0.9, "EDA +\nPretraitement\n+ Feature eng.", BLUE_L, BLUE, fs=8.5)
box(ax, 5.3, 8.0, 2.0, 0.9, "Entrainement\n7 modeles\n(CV temporelle)", BLUE_L, BLUE, fs=8.5)
box(ax, 1.85, 6.6, 2.0, 0.9, "Calibration +\nseuil optimal", BLUE_L, BLUE, fs=8.5)
box(ax, 4.15, 6.6, 2.0, 0.9, "Evaluation +\nanalyse de cout", BLUE_L, BLUE, fs=8.5)
arrow(ax, 2.7, 8.45, 3.0, 8.45, BLUE)
arrow(ax, 5.0, 8.45, 5.3, 8.45, BLUE)
arrow(ax, 6.3, 8.0, 5.15, 7.5, BLUE)
arrow(ax, 3.85, 7.05, 4.15, 7.05, BLUE)

# Lane B — real-time
lane(ax, 8.5, 5.6, 7.2, 3.5, "VOLET 2 — Simulation bancaire temps reel", GREEN)
box(ax, 8.9, 8.0, 2.05, 0.9, "Generateur\nsynthetique\nclients + tx", GREEN_L, GREEN, fs=8.5)
box(ax, 11.2, 8.0, 2.05, 0.9, "Moteur de scoring\ndynamique\nexplicable", GREEN_L, GREEN, fs=8.5)
box(ax, 13.5, 8.0, 2.05, 0.9, "Decision\nAPPROVE /\nREVIEW / BLOCK", GREEN_L, GREEN, fs=8.5)
box(ax, 10.05, 6.6, 2.05, 0.9, "Broker\nevenementiel\n(SSE / WS)", GREEN_L, GREEN, fs=8.5)
box(ax, 12.35, 6.6, 2.05, 0.9, "SimulationRun\n(suivi par run)", GREEN_L, GREEN, fs=8.5)
arrow(ax, 10.95, 8.45, 11.2, 8.45, GREEN)
arrow(ax, 13.25, 8.45, 13.5, 8.45, GREEN)
arrow(ax, 12.2, 8.0, 11.1, 7.5, GREEN)
arrow(ax, 12.1, 7.05, 12.35, 7.05, GREEN)

# Shared core
box(ax, 1.6, 3.7, 3.4, 1.1, "models_store/\nmodeles serialises\n+ pretraitements", GREY_L, GREY, fs=9, bold=True)
box(ax, 6.3, 3.7, 3.4, 1.1, "API FastAPI\n/predict /explain\n/stats /alerts", VIOLET_L, VIOLET, fs=9, bold=True)
box(ax, 11.0, 3.7, 3.4, 1.1, "Persistance ORM\nSQLAlchemy\nSQLite / PostgreSQL", AMBER_L, AMBER, fs=9, bold=True)

arrow(ax, 3.3, 6.6, 3.3, 4.8, BLUE, ls=(0, (4, 2)))
arrow(ax, 11.0, 6.6, 8.5, 4.8, GREEN, ls=(0, (4, 2)))
arrow(ax, 5.0, 4.25, 6.3, 4.25, GREY)
arrow(ax, 9.7, 4.25, 11.0, 4.25, VIOLET)
arrow(ax, 12.7, 6.6, 12.7, 4.8, AMBER, ls=(0, (4, 2)))

# Consumption layer
box(ax, 4.2, 1.4, 3.4, 1.1, "Tableau de bord\ntemps reel (/dashboard)", CYAN_L, CYAN, fs=9, bold=True)
box(ax, 8.4, 1.4, 3.4, 1.1, "Power BI\n(vues + DirectQuery)", CYAN_L, CYAN, fs=9, bold=True)
arrow(ax, 7.5, 3.7, 6.0, 2.5, VIOLET)
arrow(ax, 12.7, 3.7, 10.4, 2.5, AMBER)
arrow(ax, 8.0, 3.7, 8.0, 2.5, VIOLET)

save(fig, "fig1_architecture.png")


# ============================================================
# FIGURE 2 — Pipeline hors-ligne (chaine de traitement)
# ============================================================
fig, ax = base((13.5, 6.2))
ax.set_ylim(0, 8)
ax.text(8, 7.6, "Pipeline d'apprentissage supervise — chaine anti-fuite temporelle",
        ha="center", fontsize=13, fontweight="bold", color=INK)

steps = [
    ("1. Chargement\n& validation\ncreditcard.csv", BLUE_L, BLUE),
    ("2. EDA\nfigures de\npublication", BLUE_L, BLUE),
    ("3. Decoupage\nchronologique\n(anti-fuite)", AMBER_L, AMBER),
    ("4. Feature\nengineering\n(fit sur train)", BLUE_L, BLUE),
    ("5. Reequilibrage\nSMOTEENN /\nclass_weight", VIOLET_L, VIOLET),
]
x = 0.5
for t, fc, ec in steps:
    box(ax, x, 5.4, 2.4, 1.4, t, fc, ec, fs=8.8)
    if x > 0.5:
        arrow(ax, x - 0.4, 6.1, x, 6.1, GREY)
    x += 2.95

# second row (reverse flow)
steps2 = [
    ("6. Entrainement\n7 modeles +\nTimeSeriesSplit CV", BLUE_L, BLUE),
    ("7. Optimisation\nOptuna (TPE,\n30 essais)", VIOLET_L, VIOLET),
    ("8. Calibration\nisotonique\nde la proba", GREEN_L, GREEN),
    ("9. Optimisation\ndu seuil\n(F1 / MCC / cout)", AMBER_L, AMBER),
    ("10. Evaluation +\nanalyse de cout\nasymetrique", RED_L, RED),
]
x = 0.5
y2 = 2.9
for t, fc, ec in steps2:
    box(ax, x, y2, 2.4, 1.4, t, fc, ec, fs=8.8)
    if x > 0.5:
        arrow(ax, x, y2 + 0.7, x - 0.55, y2 + 0.7, GREY)  # right-to-left
    x += 2.95
# connector from row1 end down to row2 end
arrow(ax, 12.3, 5.4, 12.3, 4.3, GREY)
ax.text(12.55, 4.85, "", fontsize=8)

# artefacts output
box(ax, 4.8, 0.5, 6.0, 1.1,
    "Sorties : models_store/*.pkl  |  reports/tables/model_comparison.csv  |  reports/figures/*.png",
    GREY_L, GREY, fs=8.5, bold=True)
arrow(ax, 1.7, 2.9, 4.8, 1.6, RED)

save(fig, "fig2_pipeline_offline.png")


# ============================================================
# FIGURE 3 — Moteur de scoring dynamique
# ============================================================
fig, ax = base((13.5, 7.4))
ax.set_ylim(0, 9)
ax.text(8, 8.6, "Moteur de scoring dynamique explicable (volet temps reel)",
        ha="center", fontsize=13, fontweight="bold", color=INK)

# Input signals (left)
signals = [
    "Profil de risque client",
    "Montant & ratio vs moyenne",
    "Heure (fenetre nocturne)",
    "Pays / risque geographique",
    "Reputation IP, Tor / VPN",
    "Appareil connu ?",
    "Categorie marchand / carte",
    "Anciennete & historique fraude",
    "Velocite 60 s",
    "Voyage impossible (haversine)",
    "Rotation d'adresses IP",
    "Scenario injecte",
]
y = 7.9
for s in signals:
    box(ax, 0.4, y, 4.1, 0.52, s, GREEN_L, GREEN, fs=8.3)
    arrow(ax, 4.5, y + 0.26, 5.7, 4.6, GREY, lw=1.0)
    y -= 0.62

# Aggregation
box(ax, 5.7, 4.0, 3.0, 1.3, "Somme additive\ndes contributions\n(points de risque)", AMBER_L, AMBER, fs=10, bold=True)
box(ax, 9.1, 4.0, 2.7, 1.3, "Score 0-100\n(borne)", BLUE_L, BLUE, fs=10, bold=True)
box(ax, 12.1, 4.0, 3.0, 1.3, "Probabilite\nsigmoide 0-100 %", VIOLET_L, VIOLET, fs=10, bold=True)
arrow(ax, 8.7, 4.65, 9.1, 4.65, GREY)
arrow(ax, 11.8, 4.65, 12.1, 4.65, GREY)

# Decision bands
box(ax, 9.6, 1.9, 2.0, 0.9, "< 45\nAPPROVE", GREEN_L, GREEN, fs=9, bold=True)
box(ax, 11.8, 1.9, 2.0, 0.9, "45 - 70\nREVIEW", AMBER_L, AMBER, fs=9, bold=True)
box(ax, 14.0, 1.9, 1.7, 0.9, ">= 70\nBLOCK", RED_L, RED, fs=9, bold=True)
arrow(ax, 13.6, 4.0, 13.6, 2.8, BLUE)
ax.text(13.6, 3.45, "seuils de decision", ha="center", fontsize=8, color=GREY)

# Explainability output
box(ax, 5.7, 1.9, 3.4, 0.9, "Valeurs SHAP-style\n+ top raisons (texte)", CYAN_L, CYAN, fs=8.8, bold=True)
arrow(ax, 7.2, 4.0, 7.3, 2.8, CYAN)

save(fig, "fig3_scoring_engine.png")


# ============================================================
# FIGURE 4 — Sequence temps reel (streaming)
# ============================================================
fig, ax = base((13.5, 6.6))
ax.set_ylim(0, 9)
ax.text(8, 8.6, "Sequence d'execution de la simulation en temps reel",
        ha="center", fontsize=13, fontweight="bold", color=INK)

actors = [
    ("Service de\nsimulation\n(boucle async)", 1.4, GREEN),
    ("Generateur\nde transactions", 4.3, GREEN),
    ("Moteur de\nscoring", 7.2, AMBER),
    ("Base de\ndonnees (CRUD)", 10.1, BLUE),
    ("Broker\n-> Dashboard", 13.0, CYAN),
]
for t, x, c in actors:
    box(ax, x - 1.1, 7.0, 2.2, 1.0, t, "#FFFFFF", c, tc=c, fs=8.6, bold=True)
    ax.add_line(Line2D([x, x], [0.6, 7.0], color=c, lw=1.2, linestyle=(0, (3, 3)), zorder=1))

def msg(y, x1, x2, text, color):
    arrow(ax, x1, y, x2, y, color, lw=1.6)
    mid = (x1 + x2) / 2
    ax.text(mid, y + 0.18, text, ha="center", fontsize=8.2, color=INK)

msg(6.2, 1.4, 4.3, "1. genere un lot (taux TPS, ratio fraude)", GREEN)
msg(5.4, 4.3, 1.4, "transactions synthetiques", GREY)
msg(4.6, 1.4, 7.2, "2. score(transaction)", AMBER)
msg(3.8, 7.2, 1.4, "evaluation + raisons", GREY)
msg(3.0, 1.4, 10.1, "3. enregistre tx + decision + alerte", BLUE)
msg(2.2, 1.4, 13.0, "4. publie l'evenement", CYAN)
msg(1.4, 13.0, 13.0, "5. flux SSE/WebSocket vers le navigateur", CYAN)
ax.text(13.0, 1.0, "(temps reel)", ha="center", fontsize=7.5, color=GREY, style="italic")

save(fig, "fig4_sequence_streaming.png")

print("ALL DIAGRAMS DONE")
