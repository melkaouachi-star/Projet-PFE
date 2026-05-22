"""
Dimensionality reduction & 2-D fraud visualisation maps.

Three techniques are compared:
- PCA (linear, fast, baseline)
- t-SNE (non-linear, slow, captures local structure)
- UMAP (non-linear, faster than t-SNE, preserves global structure)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from src.utils.config import PROJECT_ROOT, get_config
from src.utils.logger import get_logger

log = get_logger("features.dimensionality")


def _fig_dir() -> Path:
    p = PROJECT_ROOT / get_config().paths.reports_figures
    p.mkdir(parents=True, exist_ok=True)
    return p


def _scatter_2d(emb: np.ndarray, y: np.ndarray, title: str, fname: str) -> Path:
    fig, ax = plt.subplots(figsize=(7, 6))
    # Plot legitimate first (background), fraud on top (visible)
    legit = y == 0
    ax.scatter(emb[legit, 0], emb[legit, 1], s=2, alpha=0.2, color="#3b7dd8", label="Legitimate")
    ax.scatter(emb[~legit, 0], emb[~legit, 1], s=12, alpha=0.9, color="#d8423b", label="Fraud")
    ax.set_title(title)
    ax.set_xlabel("Component 1"); ax.set_ylabel("Component 2")
    ax.legend()
    out = _fig_dir() / fname
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    log.info(f"Saved {out}")
    return out


def reduce_pca(X: pd.DataFrame, y: pd.Series) -> Path:
    log.info("Running PCA(2)...")
    emb = PCA(n_components=2, random_state=42).fit_transform(X)
    return _scatter_2d(emb, y.values, "PCA projection of credit-card transactions", "10_pca_2d.png")


def reduce_tsne(X: pd.DataFrame, y: pd.Series, sample: int = 10000) -> Path:
    log.info(f"Running t-SNE(2) on {sample:,} sampled rows...")
    idx = _balanced_sample(y, sample)
    Xs, ys = X.iloc[idx].values, y.iloc[idx].values
    emb = TSNE(n_components=2, perplexity=40, init="pca",
               learning_rate="auto", random_state=42).fit_transform(Xs)
    return _scatter_2d(emb, ys, "t-SNE projection of credit-card transactions", "11_tsne_2d.png")


def reduce_umap(X: pd.DataFrame, y: pd.Series, sample: int = 20000) -> Path:
    try:
        import umap
    except ImportError as exc:
        raise ImportError("Install umap-learn to use this function.") from exc
    log.info(f"Running UMAP(2) on {sample:,} sampled rows...")
    idx = _balanced_sample(y, sample)
    Xs, ys = X.iloc[idx].values, y.iloc[idx].values
    emb = umap.UMAP(n_components=2, n_neighbors=30, min_dist=0.1, random_state=42).fit_transform(Xs)
    return _scatter_2d(emb, ys, "UMAP projection of credit-card transactions", "12_umap_2d.png")


def _balanced_sample(y: pd.Series, total: int) -> np.ndarray:
    """Return indices keeping all fraud + a random sample of legitimates."""
    fraud_idx = np.where(y.values == 1)[0]
    legit_idx = np.where(y.values == 0)[0]
    n_legit = max(total - len(fraud_idx), 0)
    rng = np.random.default_rng(42)
    legit_sample = rng.choice(legit_idx, size=min(n_legit, len(legit_idx)), replace=False)
    return np.concatenate([fraud_idx, legit_sample])
