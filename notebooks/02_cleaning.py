"""
02_cleaning.py
==============
Pipeline de nettoyage des données — AirGuard AI CM
Sprint 2 — Data Cleaning & Préparation

Principe fondamental :
    Les données brutes ne sont JAMAIS modifiées.
    On lit depuis data/raw/ et on écrit dans data/processed/
    C'est le principe d'immutabilité des données brutes.

Étapes du pipeline :
    1. Chargement + typage
    2. Correction du 6ème type climatique
    3. Capping des anomalies physiques
    4. Imputation conditionnelle (médiane ville × mois)
    5. Log-transform des variables asymétriques
    6. Ajout des features temporelles (DIM_DATE)
    7. Calcul du niveau de risque (DIM_RISQUE)
    8. Sauvegarde des données nettoyées

Auteur  : AirGuard Team
Version : 1.0.0
Date    : 2026-03-13
"""

import pandas as pd
import numpy as np
import yaml
import json
from pathlib import Path

# ── Chemins ──────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_RAW = ROOT / "data" / "raw" / "cameroon_meteo_hackathon.csv"
DATA_PROCESSED = ROOT / "data" / "processed"
SCHEMA_PATH = ROOT / "config" / "schema.yml"
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)


def load_schema() -> dict:
    """Charge le schéma de configuration."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def log_step(step: int, title: str, details: list = None):
    """
    Affiche un rapport d'étape formaté.

    Parameters
    ----------
    step    : numéro de l'étape
    title   : titre de l'étape
    details : liste de messages à afficher
    """
    print(f"\n{'='*60}")
    print(f"  ÉTAPE {step} — {title}")
    print(f"{'='*60}")
    if details:
        for d in details:
            print(f"  {d}")


# ════════════════════════════════════════════════════════════
# ÉTAPE 1 — Chargement + typage
# ════════════════════════════════════════════════════════════

def load_and_type(schema: dict) -> pd.DataFrame:
    """
    Charge le dataset brut et applique les types corrects.

    Pourquoi typer explicitement ?
    Pandas infère les types automatiquement mais peut se tromper.
    On force les types définis dans schema.yml pour garantir
    la cohérence tout au long du pipeline.

    Parameters
    ----------
    schema : dict — contenu de schema.yml

    Returns
    -------
    pd.DataFrame — dataset avec types corrects
    """
    log_step(1, "Chargement + typage")

    df = pd.read_csv(DATA_RAW)

    # Conversion date
    date_col = schema["pipeline"]["date_column"]
    df[date_col] = pd.to_datetime(df[date_col])

    # Tri chronologique par ville
    df = df.sort_values([
        schema["pipeline"]["city_column"],
        date_col
    ]).reset_index(drop=True)

    print(f"  Lignes chargées : {len(df):,}")
    print(f"  Colonnes        : {len(df.columns)}")
    print(f"  Période         : {df[date_col].min().date()} "
          f"→ {df[date_col].max().date()}")

    return df


# ════════════════════════════════════════════════════════════
# ÉTAPE 2 — Identification et correction du 6ème type climatique
# ════════════════════════════════════════════════════════════

def fix_climate_types(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """
    Identifie et corrige le 6ème type climatique non documenté.

    L'EDA a révélé 6 types alors que le schéma en prévoit 5.
    On identifie le type inconnu et on décide de le garder
    ou de le mapper vers un type existant.

    Parameters
    ----------
    df     : pd.DataFrame
    schema : dict

    Returns
    -------
    pd.DataFrame — types climatiques corrigés
    """
    log_step(2, "Identification du 6ème type climatique")

    # Types attendus selon schema.yml
    col = schema["pipeline"]["climate_column"]
    expected = [c["expected_values"] for c in schema["columns"]
                if c["name"] == col][0]

    # Types réellement présents
    actual = df[col].unique().tolist()
    unknown = [t for t in actual if t not in expected]

    print(f"  Types attendus  : {expected}")
    print(f"  Types présents  : {sorted(actual)}")
    print(f"  Types inconnus  : {unknown}")

    # Afficher les villes concernées
    for t in unknown:
        villes = df[df[col] == t]["ville"].unique()
        regions = df[df[col] == t]["region"].unique()
        print(f"\n  Type '{t}' :")
        print(f"    Villes  : {list(villes)}")
        print(f"    Régions : {list(regions)}")

    # Décision de mapping (à ajuster selon ce qu'on trouve)
    # On conserve tous les types — le schéma sera mis à jour
    print("\n  → Décision : conservation de tous les types")
    print("  → schema.yml sera mis à jour après cette étape")

    return df


# ════════════════════════════════════════════════════════════
# ÉTAPE 3 — Capping des anomalies physiques
# ════════════════════════════════════════════════════════════

def apply_capping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique le capping sur les valeurs physiquement impossibles.

    Règle fondamentale :
    On ne supprime jamais une ligne entière pour une anomalie
    sur une seule colonne. On corrige uniquement la valeur
    aberrante et on conserve toutes les autres mesures.

    Décisions issues de l'EDA (eda_report.md) :
    - humidite_pct      → [0, 100]
    - vitesse_vent_ms   → [0, 40]
    - precipitations_mm → [0, 300]
    - rafale_max_ms     → [0, 60]
    - rayonnement_wm2   → [0, 1200]
    - ensoleillement_h  → [0, duree_jour_h]
    - direction_vent_deg → modulo 360, NaN si négatif
    - pm25_proxy_ugm3   → CONSERVÉ (harmattan réel)

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame — anomalies corrigées
    """
    log_step(3, "Capping des anomalies physiques")

    df = df.copy()
    rapport = []

    # ── 3.1 Humidité ─────────────────────────────────────────
    avant = (df["humidite_pct"] > 100).sum() + (df["humidite_pct"] < 0).sum()
    df["humidite_pct"] = df["humidite_pct"].clip(0, 100)
    rapport.append(f"humidite_pct     : {avant:,} valeurs corrigées → [0, 100]")

    # ── 3.2 Vitesse vent ─────────────────────────────────────
    avant = (df["vitesse_vent_ms"] > 40).sum()
    df["vitesse_vent_ms"] = df["vitesse_vent_ms"].clip(0, 40)
    rapport.append(f"vitesse_vent_ms  : {avant:,} valeurs corrigées → [0, 40]")

    # ── 3.3 Précipitations ───────────────────────────────────
    avant = (df["precipitations_mm"] > 300).sum()
    df["precipitations_mm"] = df["precipitations_mm"].clip(0, 300)
    rapport.append(f"precipitations   : {avant:,} valeurs corrigées → [0, 300]")

    # ── 3.4 Rafales ──────────────────────────────────────────
    avant = (df["rafale_max_ms"] > 60).sum()
    df["rafale_max_ms"] = df["rafale_max_ms"].clip(0, 60)
    rapport.append(f"rafale_max_ms    : {avant:,} valeurs corrigées → [0, 60]")

    # ── 3.5 Rayonnement ──────────────────────────────────────
    avant = (df["rayonnement_wm2"] > 1200).sum()
    df["rayonnement_wm2"] = df["rayonnement_wm2"].clip(0, 1200)
    rapport.append(f"rayonnement_wm2  : {avant:,} valeurs corrigées → [0, 1200]")

    # ── 3.6 Ensoleillement ───────────────────────────────────
    avant = (df["ensoleillement_h"] > df["duree_jour_h"]).sum()
    df["ensoleillement_h"] = df.apply(
        lambda r: min(r["ensoleillement_h"], r["duree_jour_h"])
        if pd.notna(r["ensoleillement_h"]) else r["ensoleillement_h"],
        axis=1
    )
    rapport.append(f"ensoleillement_h : {avant:,} valeurs corrigées → ≤ duree_jour_h")

    # ── 3.7 Direction vent ───────────────────────────────────
    avant_neg = (df["direction_vent_deg"] < 0).sum()
    avant_sup = (df["direction_vent_deg"] > 360).sum()
    df.loc[df["direction_vent_deg"] < 0, "direction_vent_deg"] = np.nan
    df.loc[df["direction_vent_deg"] > 360, "direction_vent_deg"] = (
        df.loc[df["direction_vent_deg"] > 360, "direction_vent_deg"] % 360
    )
    rapport.append(
        f"direction_vent   : {avant_neg} mis à NaN (négatifs), "
        f"{avant_sup} corrigés (modulo 360)"
    )

    for r in rapport:
        print(f"  ✓ {r}")

    # Vérification post-capping
    print("\n  Vérification post-capping :")
    checks = {
        "humidite_pct": (0, 100),
        "vitesse_vent_ms": (0, 40),
        "precipitations_mm": (0, 300),
        "rafale_max_ms": (0, 60),
        "rayonnement_wm2": (0, 1200),
    }
    for col, (vmin, vmax) in checks.items():
        remaining = ((df[col] < vmin) | (df[col] > vmax)).sum()
        status = "✓" if remaining == 0 else "✗"
        print(f"  {status} {col} : {remaining} anomalies restantes")

    return df


# ════════════════════════════════════════════════════════════
# ÉTAPE 4 — Imputation conditionnelle (médiane ville × mois)
# ════════════════════════════════════════════════════════════

def impute_missing(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """
    Impute les valeurs manquantes par médiane conditionnelle.

    Stratégie (issue de l'EDA — MAR confirmé) :
    Pour chaque valeur manquante, on utilise la médiane
    des observations de la MÊME ville pour le MÊME mois.

    Pourquoi cette stratégie ?
    - Respecte la saisonnalité (mois)
    - Respecte les spécificités locales (ville)
    - Si pas assez de données ville×mois → médiane ville
    - Si toujours vide → médiane régionale × mois
    - En dernier recours → médiane globale de la colonne

    C'est une imputation en cascade — du plus précis
    au plus général.

    Parameters
    ----------
    df     : pd.DataFrame
    schema : dict

    Returns
    -------
    pd.DataFrame — valeurs manquantes imputées
    """
    log_step(4, "Imputation conditionnelle (médiane ville × mois)")

    df = df.copy()
    df["_mois"] = df["date"].dt.month

    feature_cols = schema["pipeline"]["feature_columns"]
    target_col = schema["pipeline"]["target_column"]
    cols_to_impute = feature_cols + [target_col]

    rapport = []

    for col in cols_to_impute:
        nb_avant = df[col].isnull().sum()
        if nb_avant == 0:
            continue

        # Niveau 1 : médiane ville × mois
        mediane_ville_mois = df.groupby(
            ["ville", "_mois"]
        )[col].transform("median")
        df[col] = df[col].fillna(mediane_ville_mois)

        # Niveau 2 : médiane ville (si encore manquant)
        mediane_ville = df.groupby("ville")[col].transform("median")
        df[col] = df[col].fillna(mediane_ville)

        # Niveau 3 : médiane région × mois
        mediane_region_mois = df.groupby(
            ["region", "_mois"]
        )[col].transform("median")
        df[col] = df[col].fillna(mediane_region_mois)

        # Niveau 4 : médiane globale
        df[col] = df[col].fillna(df[col].median())

        nb_apres = df[col].isnull().sum()
        rapport.append(
            f"{col:<25} : {nb_avant:,} → {nb_apres} manquants restants"
        )

    df = df.drop(columns=["_mois"])

    print(f"  {'Colonne':<25}   Avant → Après")
    print(f"  {'-'*45}")
    for r in rapport:
        print(f"  {r}")

    total_restant = df[cols_to_impute].isnull().sum().sum()
    print(f"\n  Total manquants restants : {total_restant}")
    if total_restant == 0:
        print("  ✓ Aucune valeur manquante — dataset complet")

    return df


# ════════════════════════════════════════════════════════════
# ÉTAPE 5 — Log-transform des variables asymétriques
# ════════════════════════════════════════════════════════════

def apply_log_transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique log1p sur les variables très asymétriques.

    Pourquoi log1p et pas log ?
    log(0) = -infini → problème si la variable vaut 0
    log1p(x) = log(x + 1) → défini pour x = 0

    Variables concernées (asymétrie > 2, issue de l'EDA) :
    - pm25_proxy_ugm3   (skew = 11.80)
    - precipitations_mm (skew = 44.77)
    - vitesse_vent_ms   (skew = 8.39)
    - rafale_max_ms     (skew = 8.57)
    - humidite_pct      (skew = 9.12 après capping)

    On crée des nouvelles colonnes avec suffixe _log
    pour conserver les valeurs originales (utiles pour
    l'affichage dans le dashboard).

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame — colonnes log ajoutées
    """
    log_step(5, "Log-transform des variables asymétriques")

    df = df.copy()

    cols_to_log = [
        "pm25_proxy_ugm3",
        "precipitations_mm",
        "vitesse_vent_ms",
        "rafale_max_ms",
        "humidite_pct",
    ]

    for col in cols_to_log:
        new_col = f"{col}_log"
        df[new_col] = np.log1p(df[col])
        skew_avant = df[col].skew()
        skew_apres = df[new_col].skew()
        print(f"  {col:<25} : skew {skew_avant:+.2f} → {skew_apres:+.2f}")

    print("\n  ✓ Colonnes _log créées (originales conservées)")
    return df


# ════════════════════════════════════════════════════════════
# ÉTAPE 6 — Construction de DIM_DATE
# ════════════════════════════════════════════════════════════

def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrichit le dataset avec les features temporelles (DIM_DATE).

    Ces features sont critiques pour le modèle ML car elles
    capturent la saisonnalité que les variables météo seules
    ne peuvent pas exprimer.

    Features ajoutées :
    - jour, mois, trimestre, annee
    - jour_semaine (0=lundi ... 6=dimanche)
    - is_weekend
    - saison (seche / pluies — propre au Cameroun)
    - is_harmattan (Nov–Fév, zones Nord/Extrême-Nord/Adamaoua)
    - nb_jours_depuis_debut (feature numérique continue)

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame — features temporelles ajoutées
    """
    log_step(6, "Construction DIM_DATE — Features temporelles")

    df = df.copy()

    df["jour"]        = df["date"].dt.day
    df["mois"]        = df["date"].dt.month
    df["trimestre"]   = df["date"].dt.quarter
    df["annee"]       = df["date"].dt.year
    df["jour_semaine"] = df["date"].dt.dayofweek
    df["is_weekend"]  = df["jour_semaine"].isin([5, 6]).astype(int)

    # Saison au Cameroun (approximation nationale)
    # Saison sèche : Nov–Avr | Saison des pluies : Mai–Oct
    df["saison"] = df["mois"].apply(
        lambda m: "seche" if m in [11, 12, 1, 2, 3, 4] else "pluies"
    )

    # Harmattan : phénomène Nord/Extrême-Nord/Adamaoua
    # Période : Novembre → Février
    regions_harmattan = ["Nord", "Extrême-Nord", "Adamaoua"]
    df["is_harmattan"] = (
        (df["region"].isin(regions_harmattan)) &
        (df["mois"].isin([11, 12, 1, 2]))
    ).astype(int)

    # Feature numérique continue (utile pour les tendances ML)
    date_min = df["date"].min()
    df["nb_jours_depuis_debut"] = (df["date"] - date_min).dt.days

    features_added = [
        "jour", "mois", "trimestre", "annee",
        "jour_semaine", "is_weekend",
        "saison", "is_harmattan",
        "nb_jours_depuis_debut"
    ]
    print(f"  Features ajoutées : {features_added}")
    print(f"\n  Distribution saison :")
    print(df["saison"].value_counts().to_string())
    print(f"\n  Jours harmattan (Nord) : "
          f"{df['is_harmattan'].sum():,}")

    return df


# ════════════════════════════════════════════════════════════
# ÉTAPE 7 — Calcul du niveau de risque (DIM_RISQUE)
# ════════════════════════════════════════════════════════════

def build_dim_risque(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """
    Calcule le niveau de risque PM2.5 pour chaque observation.

    C'est la concrétisation du DIM_RISQUE du Star Schema.
    On transforme une mesure continue (PM2.5 en µg/m³)
    en une catégorie décisionnelle (low/moderate/high/critical).

    Seuils définis dans schema.yml (section risk_thresholds).

    Parameters
    ----------
    df     : pd.DataFrame
    schema : dict

    Returns
    -------
    pd.DataFrame — colonnes risque ajoutées
    """
    log_step(7, "Construction DIM_RISQUE — Niveaux de risque")

    df = df.copy()
    thresholds = schema["risk_thresholds"]

    def get_risk_level(pm25: float) -> str:
        """Classe un niveau PM2.5 en catégorie de risque."""
        if pd.isna(pm25):
            return "unknown"
        if pm25 < thresholds["moderate"]["min"]:
            return "low"
        elif pm25 < thresholds["high"]["min"]:
            return "moderate"
        elif pm25 < thresholds["critical"]["min"]:
            return "high"
        else:
            return "critical"

    df["risk_level"] = df["pm25_proxy_ugm3"].apply(get_risk_level)

    # Encodage numérique pour le ML
    risk_encoding = {"low": 0, "moderate": 1, "high": 2,
                     "critical": 3, "unknown": -1}
    df["risk_score"] = df["risk_level"].map(risk_encoding)

    print("  Distribution des niveaux de risque :")
    dist = df["risk_level"].value_counts()
    total = len(df)
    for level, count in dist.items():
        pct = count / total * 100
        print(f"    {level:<12} : {count:,} ({pct:.1f}%)")

    print("\n  Distribution par région (% jours critiques) :")
    critical_by_region = (
        df[df["risk_level"] == "critical"]
        .groupby("region")
        .size()
        / df.groupby("region").size()
        * 100
    ).sort_values(ascending=False).round(1)
    print(critical_by_region.to_string())

    return df


# ════════════════════════════════════════════════════════════
# ÉTAPE 8 — Construction et sauvegarde du Star Schema
# ════════════════════════════════════════════════════════════

def build_and_save_star_schema(
    df: pd.DataFrame,
    schema: dict
) -> dict:
    """
    Construit les tables du Star Schema et les sauvegarde.

    Tables produites :
    - dim_date.csv       : dimension temporelle
    - dim_ville.csv      : dimension géographique
    - dim_climat.csv     : dimension climatique
    - dim_risque.csv     : dimension de risque
    - fait_pollution.csv : table de faits centrale

    Principe ROLAP :
    Les tables sont relationnelles (CSV).
    Les agrégations sont calculées à la demande
    via Pandas (équivalent SQL).

    Parameters
    ----------
    df     : pd.DataFrame — dataset nettoyé complet
    schema : dict

    Returns
    -------
    dict — dictionnaire des tables du Star Schema
    """
    log_step(8, "Construction du Star Schema (ROLAP)")

    tables = {}

    # ── DIM_DATE ─────────────────────────────────────────────
    dim_date = df[[
        "date", "jour", "mois", "trimestre", "annee",
        "jour_semaine", "is_weekend", "saison",
        "is_harmattan", "nb_jours_depuis_debut"
    ]].drop_duplicates(subset=["date"]).reset_index(drop=True)
    dim_date.insert(0, "id_date", range(1, len(dim_date) + 1))
    tables["dim_date"] = dim_date
    print(f"  ✓ DIM_DATE      : {len(dim_date):,} lignes")

    # ── DIM_VILLE ────────────────────────────────────────────
    dim_ville = df[[
        "ville", "region", "latitude", "longitude",
        "altitude_m", "type_climat"
    ]].drop_duplicates(subset=["ville"]).reset_index(drop=True)
    dim_ville.insert(0, "id_ville", range(1, len(dim_ville) + 1))

    # Calcul du risque historique moyen par ville (KPI BI)
    risk_historique = df.groupby("ville")["pm25_proxy_ugm3"].median()
    dim_ville["pm25_median_historique"] = dim_ville["ville"].map(
        risk_historique
    )
    dim_ville["zone_risque_historique"] = dim_ville[
        "pm25_median_historique"
    ].apply(
        lambda x: "critique" if x > 55
        else "eleve" if x > 35
        else "modere" if x > 20
        else "faible"
    )
    tables["dim_ville"] = dim_ville
    print(f"  ✓ DIM_VILLE     : {len(dim_ville):,} lignes")

    # ── DIM_CLIMAT ───────────────────────────────────────────
    descriptions = {
        "equatorial": "Chaud et humide, pluies toute l'année",
        "highland": "Tempéré d'altitude, températures fraîches",
        "sudano_guinean": "Transition savane-forêt, 2 saisons",
        "tropical": "Saison sèche et saison des pluies marquées",
        "sahelian": "Semi-aride, harmattan intense, peu de pluies",
    }
    dim_climat = pd.DataFrame({
        "id_climat": range(1, len(descriptions) + 1),
        "type_climat": list(descriptions.keys()),
        "description": list(descriptions.values()),
    })
    # Ajouter les types inconnus détectés dans l'EDA
    types_presents = df["type_climat"].unique()
    for t in types_presents:
        if t not in descriptions:
            new_row = pd.DataFrame([{
                "id_climat": len(dim_climat) + 1,
                "type_climat": t,
                "description": "Type identifié lors de l'EDA — à documenter"
            }])
            dim_climat = pd.concat(
                [dim_climat, new_row], ignore_index=True
            )
    tables["dim_climat"] = dim_climat
    print(f"  ✓ DIM_CLIMAT    : {len(dim_climat):,} lignes")

    # ── DIM_RISQUE ───────────────────────────────────────────
    thresholds = schema["risk_thresholds"]
    dim_risque = pd.DataFrame([
        {
            "id_risque": 0,
            "niveau": "low",
            "label_fr": "Faible",
            "seuil_min": thresholds["low"]["min"],
            "seuil_max": thresholds["low"]["max"],
            "couleur": thresholds["low"]["color"],
            "recommandation": thresholds["low"]["recommendation"],
        },
        {
            "id_risque": 1,
            "niveau": "moderate",
            "label_fr": "Modéré",
            "seuil_min": thresholds["moderate"]["min"],
            "seuil_max": thresholds["moderate"]["max"],
            "couleur": thresholds["moderate"]["color"],
            "recommandation": thresholds["moderate"]["recommendation"],
        },
        {
            "id_risque": 2,
            "niveau": "high",
            "label_fr": "Élevé",
            "seuil_min": thresholds["high"]["min"],
            "seuil_max": thresholds["high"]["max"],
            "couleur": thresholds["high"]["color"],
            "recommandation": thresholds["high"]["recommendation"],
        },
        {
            "id_risque": 3,
            "niveau": "critical",
            "label_fr": "Critique",
            "seuil_min": thresholds["critical"]["min"],
            "seuil_max": thresholds["critical"]["max"],
            "couleur": thresholds["critical"]["color"],
            "recommandation": thresholds["critical"]["recommendation"],
        },
    ])
    tables["dim_risque"] = dim_risque
    print(f"  ✓ DIM_RISQUE    : {len(dim_risque):,} lignes")

    # ── FAIT_POLLUTION ───────────────────────────────────────
    # Jointure avec les dimensions pour récupérer les IDs
    df_fact = df.merge(
        dim_date[["id_date", "date"]], on="date", how="left"
    ).merge(
        dim_ville[["id_ville", "ville"]], on="ville", how="left"
    ).merge(
        dim_climat[["id_climat", "type_climat"]],
        on="type_climat", how="left"
    ).merge(
        pd.DataFrame({
            "risk_level": ["low", "moderate", "high", "critical"],
            "id_risque": [0, 1, 2, 3]
        }),
        on="risk_level", how="left"
    )

    # Colonnes de la table de faits
    fact_cols = [
        "id_date", "id_ville", "id_climat", "id_risque",
        # Mesures originales
        "pm25_proxy_ugm3", "temp_min_c", "temp_max_c",
        "temp_mean_c", "humidite_pct", "precipitations_mm",
        "vitesse_vent_ms", "direction_vent_deg", "rafale_max_ms",
        "ensoleillement_h", "duree_jour_h", "rayonnement_wm2",
        # Mesures transformées (ML)
        "pm25_proxy_ugm3_log", "precipitations_mm_log",
        "vitesse_vent_ms_log", "rafale_max_ms_log",
        "humidite_pct_log",
        # Features temporelles
        "saison", "is_harmattan", "nb_jours_depuis_debut",
        # Indicateurs de risque
        "risk_level", "risk_score",
        # Qualité
        "qualite_capteur",
    ]

    fait_pollution = df_fact[fact_cols].reset_index(drop=True)
    fait_pollution.insert(
        0, "id_fait", range(1, len(fait_pollution) + 1)
    )
    tables["fait_pollution"] = fait_pollution
    print(f"  ✓ FAIT_POLLUTION: {len(fait_pollution):,} lignes")

    # ── Sauvegarde ───────────────────────────────────────────
    log_step(9, "Sauvegarde des tables")

    for name, table in tables.items():
        path = DATA_PROCESSED / f"{name}.csv"
        table.to_csv(path, index=False)
        size_kb = path.stat().st_size / 1024
        print(f"  ✓ {name}.csv → {len(table):,} lignes "
              f"({size_kb:.0f} KB)")

    # Sauvegarde aussi du dataset nettoyé complet
    clean_path = DATA_PROCESSED / "dataset_clean.csv"
    df.to_csv(clean_path, index=False)
    size_mb = clean_path.stat().st_size / (1024 * 1024)
    print(f"  ✓ dataset_clean.csv → {len(df):,} lignes "
          f"({size_mb:.1f} MB)")

    return tables


# ════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  AirGuard AI CM — Pipeline de Nettoyage")
    print("  Sprint 2 — Data Cleaning & Star Schema")
    print("="*60)

    schema = load_schema()

    df = load_and_type(schema)
    df = fix_climate_types(df, schema)
    df = apply_capping(df)
    df = impute_missing(df, schema)
    df = apply_log_transform(df)
    df = build_dim_date(df)
    df = build_dim_risque(df, schema)
    tables = build_and_save_star_schema(df, schema)

    print("\n" + "="*60)
    print("  SPRINT 2 TERMINÉ")
    print("="*60)
    print(f"\n  Tables produites dans data/processed/ :")
    print(f"    - dim_date.csv")
    print(f"    - dim_ville.csv")
    print(f"    - dim_climat.csv")
    print(f"    - dim_risque.csv")
    print(f"    - fait_pollution.csv")
    print(f"    - dataset_clean.csv")
    print(f"\n  Prochaine étape : Sprint 3 — Modèle ML\n")
