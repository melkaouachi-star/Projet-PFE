# -*- coding: utf-8 -*-
"""Generate Power BI schematic diagrams (star schema + 10-page map)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.join(os.path.dirname(__file__), "_empirical_figures")
os.makedirs(OUT, exist_ok=True)

INK="#0F172A"; BLUE="#2563EB"; BLUE_L="#DBEAFE"; CYAN="#0891B2"; CYAN_L="#CFFAFE"
GREEN="#059669"; GREEN_L="#D1FAE5"; AMBER="#D97706"; AMBER_L="#FEF3C7"
RED="#DC2626"; RED_L="#FEE2E2"; VIOLET="#7C3AED"; VIOLET_L="#EDE9FE"
GREY="#475569"; GREY_L="#F1F5F9"
plt.rcParams["font.family"]="DejaVu Sans"

def box(ax,x,y,w,h,text,fc,ec,tc=INK,fs=9,bold=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.012,rounding_size=0.04",
                 linewidth=1.5,edgecolor=ec,facecolor=fc,mutation_aspect=1))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=fs,color=tc,
            fontweight="bold" if bold else "normal",zorder=5)

def arrow(ax,x1,y1,x2,y2,color=GREY,lw=1.6,style="-",ls="-"):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle=style,mutation_scale=12,
                 linewidth=lw,color=color,linestyle=ls,shrinkA=2,shrinkB=2,zorder=2))

def save(fig,name):
    fig.savefig(os.path.join(OUT,name),dpi=200,bbox_inches="tight",facecolor="white",pad_inches=0.15)
    plt.close(fig); print("wrote",name)

# =========================================================
# FIG 5 — Star schema
# =========================================================
fig,ax=plt.subplots(figsize=(13.5,7.6)); ax.set_xlim(0,16); ax.set_ylim(0,10); ax.axis("off")
ax.text(8,9.6,"Modele en etoile du rapport Power BI (DirectQuery)",ha="center",
        fontsize=13,fontweight="bold",color=INK)

# central fact
box(ax,6.2,4.3,3.6,1.4,"fact_transactions\n(transactions live)",BLUE_L,BLUE,fs=11,bold=True)

# conformed dims
box(ax,6.4,7.6,3.2,1.0,"dim_date\n(calendrier)",GREY_L,GREY,fs=9)
box(ax,1.0,6.2,3.0,1.0,"dim_customer\n(clients)",GREY_L,GREY,fs=9)
box(ax,1.0,3.6,3.0,1.0,"dim_decision_status\n(APPROVED/SUSP./BLOCKED)",GREY_L,GREY,fs=8.3)
box(ax,6.4,1.6,3.2,1.0,"dim_risk_level\n(Low / Watch / High)",GREY_L,GREY,fs=9)

# related facts
box(ax,12.0,6.4,3.4,1.1,"fact_fraud_alerts\n(alertes)",RED_L,RED,fs=9,bold=True)
box(ax,12.0,3.5,3.4,1.1,"fact_shap\n(explications SHAP)",CYAN_L,CYAN,fs=9,bold=True)

# relationships to central fact
arrow(ax,8.0,7.6,8.0,5.7,GREY); arrow(ax,4.0,6.6,6.2,5.4,GREY)
arrow(ax,4.0,4.0,6.2,4.7,GREY); arrow(ax,8.0,2.6,8.0,4.3,GREY)
arrow(ax,12.0,6.7,9.8,5.4,RED); arrow(ax,12.0,4.0,9.8,4.8,CYAN)
ax.text(8.0,5.85,"1 — *",fontsize=7.5,color=GREY,ha="center")

# unrelated facts (separate grain)
ax.text(8,0.95,"Tables a grain distinct (filtrees par leurs propres segments, sans relation) :",
        ha="center",fontsize=9,color=INK,style="italic")
unrel=[("fact_model_benchmark",AMBER_L,AMBER),("fact_cost_analysis",AMBER_L,AMBER),
       ("fact_threshold_optim.",AMBER_L,AMBER),("fact_simulation",GREEN_L,GREEN),
       ("dim_moroccan_context",VIOLET_L,VIOLET),("live_kpis",BLUE_L,BLUE)]
x=0.4
for t,fc,ec in unrel:
    box(ax,x,0.1,2.5,0.62,t,fc,ec,fs=8); x+=2.6
save(fig,"fig5_powerbi_star_schema.png")

# =========================================================
# FIG 6 — 10-page map
# =========================================================
fig,ax=plt.subplots(figsize=(13.5,7.2)); ax.set_xlim(0,16); ax.set_ylim(0,10); ax.axis("off")
ax.text(8,9.6,"Cartographie du tableau de bord Power BI — 10 pages, 5 thematiques",
        ha="center",fontsize=13,fontweight="bold",color=INK)

def group(x,y,w,h,title,color):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.01,rounding_size=0.03",
                 linewidth=1.4,edgecolor=color,facecolor="none",linestyle=(0,(6,3)),zorder=1))
    ax.text(x+0.12,y+h-0.22,title,ha="left",va="center",fontsize=10,color=color,fontweight="bold")

# Live / operational
group(0.3,5.0,9.4,3.7,"Supervision temps reel",GREEN)
box(ax,0.7,7.1,2.0,1.2,"P1\nMonitoring\nexecutif",GREEN_L,GREEN,fs=9,bold=True)
box(ax,2.9,7.1,2.0,1.2,"P2\nTransactions\nlive",GREEN_L,GREEN,fs=9,bold=True)
box(ax,5.1,7.1,2.0,1.2,"P3\nTaux fraude\n& alertes",GREEN_L,GREEN,fs=9,bold=True)
box(ax,7.3,7.1,2.0,1.2,"P10\nEfficacite\nsimulation",GREEN_L,GREEN,fs=9,bold=True)
box(ax,2.0,5.3,5.9,1.2,"KPIs : Total / Approved / Suspicious / Blocked · Fraud Rate · "
    "Recall · Precision · detection_rate",GREEN_L,GREEN,fs=8)

# Economic
group(10.0,5.0,5.7,3.7,"Analyse economique",AMBER)
box(ax,10.4,7.1,2.4,1.2,"P4\nPertes evitees\n& cout",AMBER_L,AMBER,fs=9,bold=True)
box(ax,13.0,7.1,2.4,1.2,"P7\nOptimisation\ndu seuil",AMBER_L,AMBER,fs=9,bold=True)
box(ax,10.4,5.3,5.3,1.2,"C(s) = FN·C_FN + FP·C_FP · Pertes evitees · "
    "Cout FP (12,5) · seuil optimal",AMBER_L,AMBER,fs=8)

# Model
group(0.3,1.5,7.0,3.0,"Modeles",BLUE)
box(ax,0.7,2.9,3.0,1.2,"P5\nBenchmark\n7 modeles",BLUE_L,BLUE,fs=9,bold=True)
box(ax,3.9,2.9,3.0,1.2,"P6\nMeilleur modele\n(deep dive)",BLUE_L,BLUE,fs=9,bold=True)
box(ax,0.7,1.7,6.2,1.0,"Precision/Recall/F1/MCC/PR-AUC · matrice de confusion · meilleur modele",BLUE_L,BLUE,fs=8)

# Explainability
group(7.6,1.5,3.4,3.0,"Explicabilite",CYAN)
box(ax,7.9,2.9,2.8,1.2,"P8\nSHAP\n(raisons)",CYAN_L,CYAN,fs=9,bold=True)
box(ax,7.9,1.7,2.8,1.0,"Top features · libelle metier",CYAN_L,CYAN,fs=8)

# Context
group(11.3,1.5,4.4,3.0,"Contexte & deploiement",VIOLET)
box(ax,11.7,2.9,3.6,1.2,"P9\nContexte marocain\n& applicabilite",VIOLET_L,VIOLET,fs=9,bold=True)
box(ax,11.7,1.7,3.6,1.0,"Carte (donnees synthetiques — disclaimer)",VIOLET_L,VIOLET,fs=7.6)

save(fig,"fig6_powerbi_pages_map.png")
print("DONE")
