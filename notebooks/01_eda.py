"""
01_eda.py
=========
Exploratory Data Analysis — AirGuard AI CM
Sprint 1 — Analyse exploratoire complète

Objectif : comprendre les données avant tout nettoyage.
On documente chaque observation comme un vrai data scientist.

Auteur  : AirGuard Team
Version : 1.0.0
Date    : 2026-03-13
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import yaml
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# ── Configuration globale des graphiques ─────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0a0f1a",
    "axes.facecolor": "#111827",
    "axes.edgecolor": "#1e2d45",
    "axes.labelcolor": "#94a3b8",
    "axes.titlecolor": "#e2e8f0",
    "xtick.color": "#64748b",
    "ytick.color": "#64748b",
    "text.color": "#e2e8f0",
    "grid.color": "#1e2d45",
    "grid.alpha": 0.5,
    "figure.titlesize": 14,
    "axes.titlesize": 11,
    "axes.labelsize": 9,
    "font.family": "monospace",
})

COLORS = {
    "accent": "#00d4ff",
    "green": "#22c55e",
    "yellow": "#eab308",
    "orange": "#f97316",
    "red": "#ef4444",
    "muted": "#64748b",
}

# ── Chemins ──────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "data" / "raw" / "cameroon_meteo_hackathon.csv"
SCHEMA_PATH = ROOT / "config" / "schema.yml"
OUTPUT_DIR = ROOT / "docs" / "eda"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════════════════
# SECTION 1 — Chargement & aperçu général
# ════════════════════════════════════════════════════════════

def load_data() -> pd.DataFrame:
    """
    Charge le dataset et effectue les conversions de types de base.

    Returns
    -------
    pd.DataFrame
        Dataset chargé avec types corrigés.
    """
    print("\n" + "="*60)
    print("  SECTION 1 — Chargement & aperçu général")
    print("="*60)

    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ville", "date"]).reset_index(drop=True)

    print(f"\n  Forme du dataset   : {df.shape[0]:,} lignes × {df.shape[1]} colonnes")
    print(f"  Période couverte   : {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"  Nombre de villes   : {df['ville'].nunique()}")
    print(f"  Nombre de régions  : {df['region'].nunique()}")
    print(f"  Types climatiques  : {df['type_climat'].nunique()}")
    print(f"\n  Villes par région :")
    print(df.groupby("region")["ville"].nunique().sort_values(ascending=False)
            .to_string(header=False))

    return df


# ════════════════════════════════════════════════════════════
# SECTION 2 — Analyse des valeurs manquantes
# ════════════════════════════════════════════════════════════

def analyze_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyse et visualise les valeurs manquantes par colonne.

    Pourquoi c'est important :
    Les valeurs manquantes ~10% sont trop régulières pour être
    aléatoires — probablement des pannes de capteurs périodiques.
    Cette distinction (MCAR vs MAR vs MNAR) détermine la stratégie
    d'imputation.

    MCAR = Missing Completely At Random → imputation simple OK
    MAR  = Missing At Random (dépend d'autres variables) → imputation conditionnelle
    MNAR = Missing Not At Random (dépend de la valeur elle-même) → problème sérieux

    Parameters
    ----------
    df : pd.DataFrame
        Dataset chargé.

    Returns
    -------
    pd.DataFrame
        Tableau récapitulatif des manquants.
    """
    print("\n" + "="*60)
    print("  SECTION 2 — Analyse des valeurs manquantes")
    print("="*60)

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    missing = pd.DataFrame({
        "colonne": numeric_cols,
        "nb_manquants": [df[c].isnull().sum() for c in numeric_cols],
        "pct_manquants": [df[c].isnull().mean() * 100 for c in numeric_cols],
    }).sort_values("pct_manquants", ascending=False)

    print("\n  Valeurs manquantes par colonne :")
    print(missing.to_string(index=False))

    # ── Visualisation ────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("AirGuard — Analyse des Valeurs Manquantes", 
                 fontsize=13, color="#e2e8f0", y=1.01)

    # Graphe 1 : barres horizontales
    cols_with_missing = missing[missing["pct_manquants"] > 0]
    bars = axes[0].barh(
        cols_with_missing["colonne"],
        cols_with_missing["pct_manquants"],
        color=COLORS["accent"], alpha=0.8
    )
    axes[0].axvline(x=15, color=COLORS["red"], linestyle="--",
                    linewidth=1, label="Seuil 15%")
    axes[0].set_xlabel("% valeurs manquantes")
    axes[0].set_title("Taux de manquants par variable")
    axes[0].legend(fontsize=8)
    axes[0].grid(axis="x", alpha=0.3)

    for bar, val in zip(bars, cols_with_missing["pct_manquants"]):
        axes[0].text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                     f"{val:.1f}%", va="center", fontsize=7,
                     color=COLORS["muted"])

    # Graphe 2 : heatmap des manquants par ville (top 10 villes)
    top_cities = df["ville"].value_counts().head(10).index
    missing_matrix = df[df["ville"].isin(top_cities)].groupby("ville")[
        [c for c in numeric_cols if df[c].isnull().any()]
    ].apply(lambda x: x.isnull().mean() * 100)

    sns.heatmap(
        missing_matrix,
        ax=axes[1],
        cmap="YlOrRd",
        annot=True, fmt=".0f",
        annot_kws={"size": 7},
        cbar_kws={"label": "% manquants"},
        linewidths=0.3,
    )
    axes[1].set_title("% Manquants par ville (top 10)")
    axes[1].set_xlabel("")
    axes[1].tick_params(axis="x", rotation=45, labelsize=7)
    axes[1].tick_params(axis="y", labelsize=7)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "01_missing_values.png",
                dpi=150, bbox_inches="tight",
                facecolor="#0a0f1a")
    plt.close()
    print("\n  → Graphique sauvegardé : docs/eda/01_missing_values.png")

    # ── Test MCAR : les manquants sont-ils aléatoires ? ──────
    print("\n  Test MCAR — Les manquants sont-ils liés à la ville ?")
    missing_by_city = df.groupby("ville")["pm25_proxy_ugm3"].apply(
        lambda x: x.isnull().mean() * 100
    ).sort_values(ascending=False)
    print(f"  Taux min : {missing_by_city.min():.1f}% "
          f"| max : {missing_by_city.max():.1f}% "
          f"| écart-type : {missing_by_city.std():.1f}%")
    print("  → Si écart-type élevé : manquants liés à la ville (MAR)")
    print("  → Si écart-type faible : manquants aléatoires (MCAR)")

    return missing


# ════════════════════════════════════════════════════════════
# SECTION 3 — Distribution des variables clés
# ════════════════════════════════════════════════════════════

def analyze_distributions(df: pd.DataFrame) -> None:
    """
    Analyse la distribution de chaque variable numérique.

    Pourquoi c'est important :
    - Une distribution normale → moyenne comme représentant
    - Une distribution asymétrique (skewed) → médiane préférable
    - Des valeurs extrêmes → décider capping vs suppression
    - Le PM2.5 suit souvent une loi log-normale en environnement
    """
    print("\n" + "="*60)
    print("  SECTION 3 — Distribution des variables clés")
    print("="*60)

    feature_cols = [
        "pm25_proxy_ugm3", "temp_mean_c", "humidite_pct",
        "vitesse_vent_ms", "precipitations_mm", "rayonnement_wm2",
        "ensoleillement_h", "rafale_max_ms"
    ]

    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    fig.suptitle("AirGuard — Distribution des Variables Clés",
                 fontsize=13, color="#e2e8f0")
    axes = axes.flatten()

    stats_report = []

    for i, col in enumerate(feature_cols):
        data = df[col].dropna()
        ax = axes[i]

        # Histogramme + KDE
        ax.hist(data, bins=50, color=COLORS["accent"],
                alpha=0.5, density=True, label="Distribution")

        # Statistiques
        mean_val = data.mean()
        median_val = data.median()
        skew_val = data.skew()
        q99 = data.quantile(0.99)

        ax.axvline(mean_val, color=COLORS["red"],
                   linestyle="--", linewidth=1, label=f"Moy: {mean_val:.1f}")
        ax.axvline(median_val, color=COLORS["green"],
                   linestyle="--", linewidth=1, label=f"Méd: {median_val:.1f}")

        ax.set_title(col.replace("_", " "))
        ax.legend(fontsize=6, loc="upper right")
        ax.grid(alpha=0.3)

        stats_report.append({
            "variable": col,
            "moyenne": round(mean_val, 2),
            "mediane": round(median_val, 2),
            "ecart_type": round(data.std(), 2),
            "asymetrie": round(skew_val, 2),
            "q99": round(q99, 2),
            "max": round(data.max(), 2),
            "interpretation": (
                "Très asymétrique → log-transform recommandé"
                if abs(skew_val) > 2
                else "Asymétrique → surveiller"
                if abs(skew_val) > 1
                else "Distribution acceptable"
            )
        })

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "02_distributions.png",
                dpi=150, bbox_inches="tight",
                facecolor="#0a0f1a")
    plt.close()
    print("\n  → Graphique sauvegardé : docs/eda/02_distributions.png")

    stats_df = pd.DataFrame(stats_report)
    print("\n  Statistiques descriptives :")
    print(stats_df.to_string(index=False))

    print("\n  → PM2.5 : asymétrie =",
          round(df["pm25_proxy_ugm3"].skew(), 2),
          "→ log-transform sera appliqué au Sprint 2")


# ════════════════════════════════════════════════════════════
# SECTION 4 — Analyse des anomalies
# ════════════════════════════════════════════════════════════

def analyze_anomalies(df: pd.DataFrame) -> None:
    """
    Investigate les 10 avertissements du validateur.

    Stratégie d'analyse :
    Pour chaque anomalie, on répond à 3 questions :
    1. Est-ce physiquement possible ?
    2. Est-ce localisé (ville/région) ou généralisé ?
    3. Quelle décision de traitement s'impose ?
    """
    print("\n" + "="*60)
    print("  SECTION 4 — Investigation des anomalies")
    print("="*60)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle("AirGuard — Investigation des Anomalies",
                 fontsize=13, color="#e2e8f0")
    axes = axes.flatten()

    anomaly_decisions = []

    # ── 4.1 Humidité > 100% ──────────────────────────────────
    hum_anom = df[df["humidite_pct"] > 100]
    print(f"\n  humidite_pct > 100% : {len(hum_anom)} cas")
    print(f"    Max observé   : {df['humidite_pct'].max():.1f}%")
    print(f"    Villes touchées : {hum_anom['ville'].nunique()}")
    print(f"    Régions : {hum_anom['region'].unique()}")
    print("    → Physiquement impossible. Décision : CAPPING à 100%")

    axes[0].hist(df["humidite_pct"].dropna(), bins=50,
                 color=COLORS["accent"], alpha=0.7)
    axes[0].axvline(100, color=COLORS["red"], linestyle="--",
                    linewidth=2, label="Seuil max (100%)")
    axes[0].set_title("Humidité — anomalies > 100%")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.3)
    anomaly_decisions.append({
        "variable": "humidite_pct",
        "nb_anomalies": len(hum_anom),
        "decision": "Capping [0, 100]",
        "justification": "Physiquement impossible > 100%"
    })

    # ── 4.2 PM2.5 extrêmes ───────────────────────────────────
    pm25_q99 = df["pm25_proxy_ugm3"].quantile(0.99)
    pm25_extreme = df[df["pm25_proxy_ugm3"] > pm25_q99]
    print(f"\n  pm25_proxy_ugm3 extrêmes (> Q99={pm25_q99:.1f}) :")
    print(f"    Nb cas      : {len(pm25_extreme)}")
    print(f"    Max observé : {df['pm25_proxy_ugm3'].max():.1f} µg/m³")
    print(f"    Villes : {pm25_extreme['ville'].value_counts().head(5).to_dict()}")
    print("    → Harmattan réel ou erreur capteur ? Vérifier par ville")

    by_region = df.groupby("region")["pm25_proxy_ugm3"].max().sort_values(ascending=False)
    axes[1].barh(by_region.index, by_region.values,
                 color=[COLORS["red"] if v > 500 else COLORS["orange"]
                        if v > 100 else COLORS["accent"]
                        for v in by_region.values])
    axes[1].set_title("PM2.5 max par région")
    axes[1].set_xlabel("µg/m³")
    axes[1].grid(axis="x", alpha=0.3)

    # ── 4.3 Ensoleillement > durée du jour ───────────────────
    sun_anom = df[df["ensoleillement_h"] > df["duree_jour_h"]]
    print(f"\n  ensoleillement > duree_jour : {len(sun_anom)} cas")
    print(f"    Max ensoleillement : {df['ensoleillement_h'].max():.1f}h")
    print("    → Physiquement impossible. Décision : capping à duree_jour_h")

    axes[2].scatter(df["duree_jour_h"].sample(2000, random_state=42),
                    df["ensoleillement_h"].sample(2000, random_state=42),
                    alpha=0.3, s=5, color=COLORS["accent"])
    lims = [0, 16]
    axes[2].plot(lims, lims, color=COLORS["red"], linestyle="--",
                 linewidth=1.5, label="Limite max (y=x)")
    axes[2].set_xlabel("Durée du jour (h)")
    axes[2].set_ylabel("Ensoleillement (h)")
    axes[2].set_title("Ensoleillement vs Durée du jour")
    axes[2].legend(fontsize=8)
    axes[2].grid(alpha=0.3)
    anomaly_decisions.append({
        "variable": "ensoleillement_h",
        "nb_anomalies": len(sun_anom),
        "decision": "Capping à duree_jour_h",
        "justification": "Ensoleillement ne peut excéder la durée du jour"
    })

    # ── 4.4 Rayonnement > 1200 W/m² ──────────────────────────
    ray_anom = df[df["rayonnement_wm2"] > 1200]
    print(f"\n  rayonnement_wm2 > 1200 : {len(ray_anom)} cas")
    print(f"    Max observé : {df['rayonnement_wm2'].max():.1f} W/m²")
    print("    → Au-delà du maximum solaire théorique. Décision : CAPPING à 1200")

    axes[3].hist(df["rayonnement_wm2"].dropna(), bins=60,
                 color=COLORS["yellow"], alpha=0.7)
    axes[3].axvline(1200, color=COLORS["red"], linestyle="--",
                    linewidth=2, label="Seuil max (1200 W/m²)")
    axes[3].set_title("Rayonnement solaire — anomalies > 1200")
    axes[3].legend(fontsize=8)
    axes[3].grid(alpha=0.3)
    anomaly_decisions.append({
        "variable": "rayonnement_wm2",
        "nb_anomalies": len(ray_anom),
        "decision": "Capping [0, 1200]",
        "justification": "Maximum solaire théorique = 1200 W/m²"
    })

    # ── 4.5 Direction vent hors [0, 360] ─────────────────────
    dir_anom = df[(df["direction_vent_deg"] < 0) |
                  (df["direction_vent_deg"] > 360)]
    print(f"\n  direction_vent hors [0,360] : {len(dir_anom)} cas")
    print(f"    Min : {df['direction_vent_deg'].min():.1f}° "
          f"| Max : {df['direction_vent_deg'].max():.1f}°")
    print("    → Modulo 360 pour les valeurs > 360, suppression si négatif")

    axes[4].hist(df["direction_vent_deg"].dropna(), bins=72,
                 color=COLORS["green"], alpha=0.7)
    axes[4].set_title("Direction du vent (°)")
    axes[4].grid(alpha=0.3)
    anomaly_decisions.append({
        "variable": "direction_vent_deg",
        "nb_anomalies": len(dir_anom),
        "decision": "Modulo 360 si > 360, NaN si < 0",
        "justification": "Direction = angle circulaire [0, 360]"
    })

    # ── 4.6 PM2.5 par type de climat ─────────────────────────
    climate_pm25 = df.groupby("type_climat")["pm25_proxy_ugm3"].median()
    colors_bar = [COLORS["red"] if v > 55 else COLORS["orange"]
                  if v > 35 else COLORS["yellow"]
                  if v > 20 else COLORS["green"]
                  for v in climate_pm25.values]
    axes[5].bar(climate_pm25.index, climate_pm25.values, color=colors_bar)
    axes[5].set_title("PM2.5 médian par type de climat")
    axes[5].set_ylabel("PM2.5 (µg/m³)")
    axes[5].tick_params(axis="x", rotation=30, labelsize=7)
    axes[5].grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "03_anomalies.png",
                dpi=150, bbox_inches="tight",
                facecolor="#0a0f1a")
    plt.close()
    print("\n  → Graphique sauvegardé : docs/eda/03_anomalies.png")

    print("\n  Décisions de traitement :")
    for d in anomaly_decisions:
        print(f"    [{d['variable']}] → {d['decision']}")


# ════════════════════════════════════════════════════════════
# SECTION 5 — Corrélations avec PM2.5
# ════════════════════════════════════════════════════════════

def analyze_correlations(df: pd.DataFrame) -> None:
    """
    Analyse les corrélations entre les variables météo et PM2.5.

    Pourquoi c'est fondamental pour le ML :
    - Une corrélation forte → variable prédictive utile
    - Une corrélation faible → variable potentiellement inutile
    - Corrélations entre features → risque de multicolinéarité
      (problème pour certains modèles comme la régression linéaire,
       moins pour Random Forest)

    Interprétation du coefficient de Pearson (r) :
    |r| > 0.7 → forte    |r| 0.4-0.7 → modérée
    |r| 0.2-0.4 → faible  |r| < 0.2 → négligeable
    """
    print("\n" + "="*60)
    print("  SECTION 5 — Corrélations avec PM2.5")
    print("="*60)

    numeric_cols = [
        "pm25_proxy_ugm3", "temp_min_c", "temp_max_c", "temp_mean_c",
        "humidite_pct", "precipitations_mm", "vitesse_vent_ms",
        "rafale_max_ms", "ensoleillement_h", "rayonnement_wm2",
        "duree_jour_h"
    ]
    corr_df = df[numeric_cols].corr()

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("AirGuard — Corrélations avec PM2.5",
                 fontsize=13, color="#e2e8f0")

    # Heatmap complète
    mask = np.triu(np.ones_like(corr_df, dtype=bool))
    sns.heatmap(
        corr_df, mask=mask, ax=axes[0],
        cmap="coolwarm", center=0,
        annot=True, fmt=".2f", annot_kws={"size": 7},
        linewidths=0.3, vmin=-1, vmax=1,
        cbar_kws={"label": "Pearson r"}
    )
    axes[0].set_title("Matrice de corrélation (triangulaire)")
    axes[0].tick_params(axis="both", labelsize=7)

    # Corrélations avec PM2.5 uniquement
    pm25_corr = corr_df["pm25_proxy_ugm3"].drop("pm25_proxy_ugm3").sort_values()
    colors = [COLORS["red"] if v < -0.3 else
              COLORS["green"] if v > 0.3 else
              COLORS["muted"] for v in pm25_corr.values]
    axes[1].barh(pm25_corr.index, pm25_corr.values, color=colors)
    axes[1].axvline(0, color="white", linewidth=0.5)
    axes[1].axvline(0.3, color=COLORS["green"],
                    linestyle="--", linewidth=1, label="Seuil +0.3")
    axes[1].axvline(-0.3, color=COLORS["red"],
                    linestyle="--", linewidth=1, label="Seuil -0.3")
    axes[1].set_title("Corrélation de chaque variable avec PM2.5")
    axes[1].set_xlabel("Coefficient de Pearson")
    axes[1].legend(fontsize=8)
    axes[1].grid(axis="x", alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "04_correlations.png",
                dpi=150, bbox_inches="tight",
                facecolor="#0a0f1a")
    plt.close()
    print("\n  → Graphique sauvegardé : docs/eda/04_correlations.png")

    print("\n  Corrélations avec PM2.5 (triées) :")
    print(pm25_corr.round(3).to_string())
    print("\n  → Variables les plus prédictives identifiées")


# ════════════════════════════════════════════════════════════
# SECTION 6 — Patterns temporels & géographiques
# ════════════════════════════════════════════════════════════

def analyze_patterns(df: pd.DataFrame) -> None:
    """
    Analyse les tendances temporelles et géographiques du PM2.5.

    En BI, c'est l'analyse OLAP sur l'axe DIM_DATE × DIM_VILLE.
    On fait du "slicing" (couper par mois, par région) et
    du "dicing" (combiner deux dimensions).
    """
    print("\n" + "="*60)
    print("  SECTION 6 — Patterns temporels & géographiques")
    print("="*60)

    fig = plt.figure(figsize=(18, 12))
    fig.patch.set_facecolor("#0a0f1a")
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)
    fig.suptitle("AirGuard — Patterns Temporels & Géographiques",
                 fontsize=13, color="#e2e8f0")

    # ── 6.1 PM2.5 mensuel moyen (toutes villes) ──────────────
    ax1 = fig.add_subplot(gs[0, :2])
    monthly = df.groupby(df["date"].dt.month)["pm25_proxy_ugm3"].median()
    months_fr = ["Jan","Fév","Mar","Avr","Mai","Jun",
                 "Jul","Aoû","Sep","Oct","Nov","Déc"]
    bars = ax1.bar(range(1, 13), monthly.values,
                   color=[COLORS["red"] if v > 55 else
                          COLORS["orange"] if v > 35 else
                          COLORS["yellow"] if v > 20 else
                          COLORS["green"] for v in monthly.values])
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(months_fr)
    ax1.set_title("PM2.5 médian par mois (2020–2025)")
    ax1.set_ylabel("µg/m³")
    ax1.axhline(55, color=COLORS["red"], linestyle="--",
                linewidth=1, label="Seuil critique (55)")
    ax1.legend(fontsize=8)
    ax1.grid(axis="y", alpha=0.3)
    print("\n  Saisonnalité détectée :")
    print(f"    Mois le + pollué  : {months_fr[monthly.idxmax()-1]} "
          f"({monthly.max():.1f} µg/m³)")
    print(f"    Mois le - pollué  : {months_fr[monthly.idxmin()-1]} "
          f"({monthly.min():.1f} µg/m³)")

    # ── 6.2 PM2.5 par région (KPI-01 BI) ─────────────────────
    ax2 = fig.add_subplot(gs[0, 2])
    reg_pm25 = df.groupby("region")["pm25_proxy_ugm3"].median().sort_values()
    ax2.barh(reg_pm25.index, reg_pm25.values,
             color=[COLORS["red"] if v > 55 else
                    COLORS["orange"] if v > 35 else
                    COLORS["yellow"] if v > 20 else
                    COLORS["green"] for v in reg_pm25.values])
    ax2.set_title("PM2.5 médian par région")
    ax2.set_xlabel("µg/m³")
    ax2.axvline(55, color=COLORS["red"], linestyle="--", linewidth=1)
    ax2.grid(axis="x", alpha=0.3)

    # ── 6.3 Tendance annuelle (KPI-05 BI) ────────────────────
    ax3 = fig.add_subplot(gs[1, :2])
    annual = df.groupby(df["date"].dt.year)["pm25_proxy_ugm3"].median()
    ax3.plot(annual.index, annual.values, color=COLORS["accent"],
             linewidth=2.5, marker="o", markersize=7)
    ax3.fill_between(annual.index, annual.values,
                     alpha=0.15, color=COLORS["accent"])
    ax3.set_title("Tendance annuelle PM2.5 médian (2020–2025)")
    ax3.set_ylabel("µg/m³")
    ax3.set_xlabel("Année")
    ax3.grid(alpha=0.3)
    print(f"\n  Tendance 2020→2025 :")
    print(f"    2020 : {annual.get(2020, 'N/A'):.1f} µg/m³")
    print(f"    2025 : {annual.get(2025, 'N/A'):.1f} µg/m³")

    # ── 6.4 Top 10 villes les plus polluées (KPI-01) ─────────
    ax4 = fig.add_subplot(gs[1, 2])
    top10 = df.groupby("ville")["pm25_proxy_ugm3"].median().nlargest(10)
    ax4.barh(top10.index, top10.values, color=COLORS["red"], alpha=0.8)
    ax4.set_title("Top 10 villes les + polluées")
    ax4.set_xlabel("PM2.5 médian (µg/m³)")
    ax4.axvline(55, color=COLORS["yellow"], linestyle="--",
                linewidth=1, label="Seuil critique")
    ax4.legend(fontsize=7)
    ax4.grid(axis="x", alpha=0.3)

    plt.savefig(OUTPUT_DIR / "05_patterns.png",
                dpi=150, bbox_inches="tight",
                facecolor="#0a0f1a")
    plt.close()
    print("\n  → Graphique sauvegardé : docs/eda/05_patterns.png")


# ════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    df = load_data()
    missing = analyze_missing(df)
    analyze_distributions(df)
    analyze_anomalies(df)
    analyze_correlations(df)
    analyze_patterns(df)

    print("\n" + "="*60)
    print("  EDA TERMINÉ")
    print("="*60)
    print(f"\n  5 graphiques sauvegardés dans : docs/eda/")
    print("  Prochaine étape : Sprint 2 — Nettoyage + Star Schema")
    print()
