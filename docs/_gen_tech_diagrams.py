# -*- coding: utf-8 -*-
"""Real technical-architecture diagram + corrected 9-page Power BI map."""
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
GREY="#475569"; GREY_L="#F1F5F9"; DOCK="#0B6FB8"; DOCK_L="#E0F2FE"
plt.rcParams["font.family"]="DejaVu Sans"

def box(ax,x,y,w,h,text,fc,ec,tc=INK,fs=9,bold=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.012,rounding_size=0.04",
                 linewidth=1.5,edgecolor=ec,facecolor=fc,mutation_aspect=1))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=fs,color=tc,
            fontweight="bold" if bold else "normal",zorder=5)

def arrow(ax,x1,y1,x2,y2,color=GREY,lw=1.6,style="-|>",ls="-"):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle=style,mutation_scale=13,
                 linewidth=lw,color=color,linestyle=ls,shrinkA=2,shrinkB=2,zorder=2))

def group(ax,x,y,w,h,title,color):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.01,rounding_size=0.03",
                 linewidth=1.5,edgecolor=color,facecolor="none",linestyle=(0,(6,3)),zorder=1))
    ax.text(x+0.14,y+h-0.22,title,ha="left",va="center",fontsize=10,color=color,fontweight="bold")

def save(fig,name):
    fig.savefig(os.path.join(OUT,name),dpi=200,bbox_inches="tight",facecolor="white",pad_inches=0.15)
    plt.close(fig); print("wrote",name)

# =========================================================
# FIG 7 — Real technical / deployment architecture
# =========================================================
fig,ax=plt.subplots(figsize=(13.5,7.6)); ax.set_xlim(0,16); ax.set_ylim(0,10); ax.axis("off")
ax.text(8,9.6,"Architecture technique reelle (conteneurs Docker, backend, base, frontend, Power BI)",
        ha="center",fontsize=12.5,fontweight="bold",color=INK)

# Clients (top)
box(ax,0.6,7.9,3.6,1.2,"Navigateur\nFrontend /dashboard\n(React 18 UMD, Chart.js, Leaflet)",GREEN_L,GREEN,fs=8.5,bold=True)
box(ax,11.8,7.9,3.6,1.2,"Power BI Desktop\n/ Service\n(DirectQuery)",VIOLET_L,VIOLET,fs=9,bold=True)

# Docker group
group(ax,0.4,1.4,15.2,5.7,"Reseau Docker Compose",DOCK)

# API container
box(ax,1.2,3.6,7.0,2.9,"",DOCK_L,DOCK)
ax.text(4.7,6.2,"Conteneur  fraud-api  (port 8080)",ha="center",fontsize=9.5,color=DOCK,fontweight="bold")
box(ax,1.6,5.0,3.0,0.95,"FastAPI + Uvicorn\nrouters REST / SSE / WS",BLUE_L,BLUE,fs=8.2)
box(ax,4.9,5.0,2.9,0.95,"Service de simulation\n+ broker d'evenements",GREEN_L,GREEN,fs=8.2)
box(ax,1.6,3.8,3.0,0.95,"Moteur dynamique\n(transactions live)",AMBER_L,AMBER,fs=8.2)
box(ax,4.9,3.8,2.9,0.95,"Moteur ML\n(/predict offline)",BLUE_L,BLUE,fs=8.2)

# DB container
box(ax,9.0,3.6,6.0,2.9,"",DOCK_L,DOCK)
ax.text(12.0,6.2,"Conteneur  fraud-db  (PostgreSQL 16, port 5432)",ha="center",fontsize=9.2,color=DOCK,fontweight="bold")
box(ax,9.4,4.7,5.2,1.05,"Tables ORM SQLAlchemy : banking_transactions,\nbanking_alerts, shap, customers, simulation_runs",AMBER_L,AMBER,fs=7.8)
box(ax,9.4,3.75,5.2,0.8,"Vues analytiques  vw_powerbi_*  (lecture seule)",VIOLET_L,VIOLET,fs=8)

# models_store volume
box(ax,3.2,1.7,4.2,0.85,"Volume  models_store/  (modeles .pkl, pretraitements)",GREY_L,GREY,fs=8,bold=True)

# arrows
arrow(ax,2.4,7.9,2.4,6.55,GREEN,lw=1.8)
ax.text(1.0,7.25,"HTTP /\nSSE / WS",fontsize=7.2,color=GREEN)
arrow(ax,13.6,7.9,13.0,6.55,VIOLET,lw=1.8)
ax.text(14.6,7.25,"SQL\nDirectQuery",fontsize=7.2,color=VIOLET,ha="center")
arrow(ax,8.2,5.0,9.0,5.0,GREY,lw=1.8)  # api -> db
ax.text(8.6,5.25,"psycopg2",fontsize=7,color=GREY,ha="center")
arrow(ax,4.6,3.8,5.0,2.55,GREY,ls=(0,(3,2)))  # ML engine -> models_store
arrow(ax,11.8,7.95,9.5,4.55,VIOLET,ls=(0,(4,2)),lw=1.3)  # powerbi -> views (logical)
save(fig,"fig7_tech_architecture.png")

# =========================================================
# FIG 6 (corrected) — real 9-page Power BI map
# =========================================================
fig,ax=plt.subplots(figsize=(13.5,7.0)); ax.set_xlim(0,16); ax.set_ylim(0,10); ax.axis("off")
ax.text(8,9.6,"Rapport Power BI reel — 9 pages observees dans le tableau de bord",
        ha="center",fontsize=13,fontweight="bold",color=INK)

# Live
group(ax,0.3,5.1,9.6,3.6,"Supervision temps reel (moteur dynamique)",GREEN)
box(ax,0.7,7.2,2.8,1.2,"P1\nMonitoring\nexecutif",GREEN_L,GREEN,fs=9,bold=True)
box(ax,3.7,7.2,2.8,1.2,"P2\nTransactions\nlive",GREEN_L,GREEN,fs=9,bold=True)
box(ax,6.7,7.2,2.8,1.2,"P3\nAlertes\noperationnelles",GREEN_L,GREEN,fs=9,bold=True)
box(ax,1.5,5.4,7.0,1.2,"KPIs : Total 48K · Approved/Suspicious/Blocked · Fraud Rate · "
    "carte · alertes (sev. CRITICAL/MEDIUM)",GREEN_L,GREEN,fs=7.8)

# Economic
group(ax,10.2,5.1,5.5,3.6,"Analyse economique",AMBER)
box(ax,10.6,7.2,2.4,1.2,"P4\nPertes evitees\n(waterfall)",AMBER_L,AMBER,fs=8.5,bold=True)
box(ax,13.1,7.2,2.4,1.2,"P7\nOptimisation\ndu seuil",AMBER_L,AMBER,fs=8.5,bold=True)
box(ax,10.6,5.4,4.9,1.2,"Pertes evitees · Taux 96,65% · Cout FP · "
    "cout total vs seuil",AMBER_L,AMBER,fs=7.6)

# Model
group(ax,0.3,1.5,7.4,3.0,"Modeles (apprentissage offline)",BLUE)
box(ax,0.7,2.9,3.2,1.2,"P5\nBenchmark\n7 modeles",BLUE_L,BLUE,fs=9,bold=True)
box(ax,4.1,2.9,3.2,1.2,"P6\nCout & economies\npar modele",BLUE_L,BLUE,fs=9,bold=True)
box(ax,0.7,1.7,6.6,1.0,"Precision/Recall/F1/MCC/ROC-AUC · cost_saved · FP/FN cost",BLUE_L,BLUE,fs=7.8)

# Explainability
group(ax,8.0,1.5,3.3,3.0,"Explicabilite",CYAN)
box(ax,8.35,2.9,2.6,1.2,"P8\nSHAP\n(par transaction)",CYAN_L,CYAN,fs=8.8,bold=True)
box(ax,8.35,1.7,2.6,1.0,"shap_value · libelle metier",CYAN_L,CYAN,fs=7.6)

# Context
group(ax,11.6,1.5,4.1,3.0,"Contexte marocain",VIOLET)
box(ax,11.95,2.9,3.4,1.2,"P9\nRepartition\ngeographique Maroc",VIOLET_L,VIOLET,fs=8.6,bold=True)
box(ax,11.95,1.7,3.4,1.0,"volume/ville · fraud_rate · disclaimer",VIOLET_L,VIOLET,fs=7.2)

save(fig,"fig6_powerbi_pages_map.png")
print("DONE")
