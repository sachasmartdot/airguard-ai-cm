"""
validate_schema.py
==================
Valide que le dataset chargé est conforme au contrat schema.yml.
Principe : le pipeline ne démarre JAMAIS avec des données non conformes.

Usage:
    python config/validate_schema.py --data data/raw/cameroon_meteo_hackathon.csv

Auteur : AirGuard Team
Version : 1.0.0
"""

import argparse
import sys
import pandas as pd
import yaml
from pathlib import Path


def load_schema(schema_path: str) -> dict:
    """Charge le fichier de schéma YAML."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(data_path: str, schema_path: str = "config/schema.yml") -> bool:
    """
    Valide un dataset contre le schéma défini.

    Parameters
    ----------
    data_path : str
        Chemin vers le fichier CSV à valider.
    schema_path : str
        Chemin vers le fichier schema.yml.

    Returns
    -------
    bool
        True si le dataset est conforme, False sinon.
    """
    print(f"\n{'='*55}")
    print("  AirGuard — Validation du contrat de données")
    print(f"{'='*55}\n")

    schema = load_schema(schema_path)
    df = pd.read_csv(data_path)

    errors = []
    warnings = []

    # ── 1. Vérification des colonnes attendues ───────────────
    print("[ 1/4 ] Vérification des colonnes...")
    expected_cols = [c["name"] for c in schema["columns"]]
    actual_cols = df.columns.tolist()

    missing_cols = [c for c in expected_cols if c not in actual_cols]
    extra_cols = [c for c in actual_cols if c not in expected_cols]

    if missing_cols:
        errors.append(f"Colonnes manquantes : {missing_cols}")
    if extra_cols:
        warnings.append(f"Colonnes supplémentaires (non définies) : {extra_cols}")

    print(f"    Colonnes attendues  : {len(expected_cols)}")
    print(f"    Colonnes présentes  : {len(actual_cols)}")
    print(f"    Colonnes manquantes : {len(missing_cols)}")

    # ── 2. Vérification des types ────────────────────────────
    print("\n[ 2/4 ] Vérification des types...")
    type_map = {"date": "object", "string": "object",
                "float": "float64", "int": "int64"}

    for col_def in schema["columns"]:
        col = col_def["name"]
        if col not in df.columns:
            continue
        if col_def["type"] == "date":
            try:
                pd.to_datetime(df[col])
            except Exception:
                errors.append(f"Colonne '{col}' : format date invalide")

    # ── 3. Vérification des valeurs manquantes ───────────────
    print("\n[ 3/4 ] Vérification des valeurs manquantes...")
    for col_def in schema["columns"]:
        col = col_def["name"]
        if col not in df.columns:
            continue
        threshold = col_def.get("missing_threshold", 0)
        nullable = col_def.get("nullable", True)
        missing_ratio = df[col].isnull().mean()

        if not nullable and missing_ratio > 0:
            errors.append(
                f"Colonne '{col}' : non nullable mais "
                f"{missing_ratio:.1%} de valeurs manquantes"
            )
        elif threshold and missing_ratio > threshold:
            warnings.append(
                f"Colonne '{col}' : {missing_ratio:.1%} manquants "
                f"(seuil: {threshold:.0%})"
            )

    # ── 4. Vérification des plages de valeurs ────────────────
    print("\n[ 4/4 ] Vérification des plages de valeurs...")
    for col_def in schema["columns"]:
        col = col_def["name"]
        if col not in df.columns:
            continue
        if "range" in col_def and col_def["type"] == "float":
            vmin, vmax = col_def["range"]
            out_of_range = ((df[col] < vmin) | (df[col] > vmax)).sum()
            if out_of_range > 0:
                warnings.append(
                    f"Colonne '{col}' : {out_of_range} valeurs "
                    f"hors plage [{vmin}, {vmax}]"
                )

    # ── Rapport final ────────────────────────────────────────
    print(f"\n{'─'*55}")
    print("  RAPPORT DE VALIDATION")
    print(f"{'─'*55}")
    print(f"  Lignes         : {len(df):,}")
    print(f"  Colonnes       : {len(df.columns)}")
    print(f"  Erreurs        : {len(errors)}")
    print(f"  Avertissements : {len(warnings)}")

    if warnings:
        print("\n  ⚠  AVERTISSEMENTS :")
        for w in warnings:
            print(f"     • {w}")

    if errors:
        print("\n  ✗  ERREURS BLOQUANTES :")
        for e in errors:
            print(f"     • {e}")
        print("\n  ✗  Dataset NON CONFORME — pipeline arrêté.\n")
        return False

    print("\n  ✓  Dataset conforme au schéma.\n")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Valide un dataset contre le schéma AirGuard."
    )
    parser.add_argument(
        "--data",
        default="data/raw/cameroon_meteo_hackathon.csv",
        help="Chemin vers le fichier CSV"
    )
    parser.add_argument(
        "--schema",
        default="config/schema.yml",
        help="Chemin vers le fichier schema.yml"
    )
    args = parser.parse_args()

    success = validate(args.data, args.schema)
    sys.exit(0 if success else 1)
