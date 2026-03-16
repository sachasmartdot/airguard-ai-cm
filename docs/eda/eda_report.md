# Rapport EDA — AirGuard AI CM

**Sprint :** 1  
**Date :** 2026-03-13  
**Dataset :** 92 079 obs · 42 villes · 10 régions · 2020–2025  

---

## 1. Structure des données

| Indicateur | Valeur |
|-----------|--------|
| Lignes | 92 079 |
| Colonnes | 20 |
| Villes | 42 |
| Régions | 10 |
| Types climatiques | 6 (⚠ 1 non documenté dans schema.yml) |
| Période | 2020-01-01 → 2025-12-31 |

---

## 2. Valeurs manquantes

**Conclusion : MAR (Missing At Random — lié à la ville)**

- Taux moyen : ~10% sur toutes les variables météo
- Taux min : 2.5% | max : 22.8% | écart-type : 7.3%
- Écart-type élevé → les manquants dépendent de la ville

**Stratégie d'imputation retenue :**
Médiane par ville + par mois (imputation conditionnelle)

---

## 3. Anomalies détectées et décisions

| Variable | Anomalie | Décision | Justification |
|----------|----------|----------|---------------|
| `humidite_pct` | max = 1011.9% | Capping [0, 100] | Physiquement impossible |
| `vitesse_vent_ms` | max = 146.1 m/s | Capping [0, 40] | Dépasse tout record mondial |
| `precipitations_mm` | max = 4686.6 mm | Capping [0, 300] | Record mondial = 1825 mm/j |
| `rafale_max_ms` | max = 218.8 m/s | Capping [0, 60] | Physiquement impossible |
| `ensoleillement_h` | max = 31.2h | Capping à duree_jour_h | Impossible > durée du jour |
| `rayonnement_wm2` | max = 1538 W/m² | Capping [0, 1200] | Max solaire théorique |
| `direction_vent_deg` | min=-19.5°, max=378.5° | Modulo 360 / NaN | Angle circulaire [0,360] |
| `pm25_proxy_ugm3` | max = 2965.5 µg/m³ | **Conserver** | Harmattan réel (Nord/Extrême-Nord) |

---

## 4. Distributions et transformations nécessaires

| Variable | Asymétrie | Action Sprint 2 |
|----------|-----------|----------------|
| `pm25_proxy_ugm3` | 11.80 | log-transform |
| `precipitations_mm` | 44.77 | log-transform |
| `vitesse_vent_ms` | 8.39 | log-transform |
| `rafale_max_ms` | 8.57 | log-transform |
| `humidite_pct` | 9.12 | log-transform (après capping) |
| `temp_mean_c` | 0.92 | aucune |
| `rayonnement_wm2` | 0.48 | aucune |
| `ensoleillement_h` | 0.37 | aucune |

---

## 5. Corrélations avec PM2.5

| Variable | r de Pearson | Interprétation |
|----------|-------------|----------------|
| `rayonnement_wm2` | +0.230 | Meilleure feature individuelle |
| `ensoleillement_h` | +0.194 | Corrélée au rayonnement |
| `rafale_max_ms` | +0.124 | Vent fort = harmattan = poussière |
| `vitesse_vent_ms` | +0.106 | Idem (contre-intuitif — voir note) |
| `duree_jour_h` | -0.136 | Saison sèche = jours courts |
| `humidite_pct` | -0.060 | Pluie nettoie l'air |
| `precipitations_mm` | -0.015 | Quasi nulle |
| `temp_mean_c` | +0.006 | Quasi nulle |

> **Note :** La corrélation positive vent/PM2.5 s'explique par
> le contexte géographique : dans le Nord, les vents forts
> correspondent à l'harmattan (transport de poussière saharienne).
> Une analyse par région sera réalisée au Sprint 2.

> **Conclusion :** Toutes les corrélations sont faibles (max 0.23).
> Les relations sont probablement non-linéaires.
> Random Forest / XGBoost sont adaptés car ils capturent
> ces relations sans transformation linéaire.

---

## 6. Patterns temporels et géographiques

### Saisonnalité
- Mois le plus pollué : **Janvier** (28.7 µg/m³) — harmattan
- Mois le moins pollué : **Octobre** (23.8 µg/m³) — saison des pluies

### Tendance annuelle
- 2020 : 25.7 µg/m³ | 2025 : 25.7 µg/m³
- **Pollution structurelle stable** — pas de dégradation progressive

### Géographie
- Régions les plus exposées : Nord, Extrême-Nord, Adamaoua
- Régions les moins exposées : Centre, Est, Ouest

---

## 7. Décisions pour le Sprint 2

1. Identifier le 6ème type climatique non documenté
2. Imputation conditionnelle (médiane ville × mois)
3. Capping des anomalies physiquement impossibles
4. Log-transform des variables asymétriques
5. Construction du Star Schema (FAIT + 4 dimensions)
6. Feature engineering (lag features, rolling average, saison)
7. Analyse des corrélations PAR RÉGION
