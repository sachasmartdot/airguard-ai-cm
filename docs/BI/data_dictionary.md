# Data Dictionary — AirGuard AI CM

**Version :** 1.0.0  
**Date :** 2026-03-13  
**Source :** IndabaX Hackathon Cameroun 2026  
**Grain :** 1 ligne = 1 ville × 1 jour  
**Volume :** 92 079 observations · 42 villes · 10 régions · 2020–2025  

---

## Table : FAIT_POLLUTION

| Colonne | Type | Rôle | Description | Plage attendue | Manquants |
|---------|------|------|-------------|---------------|-----------|
| `date` | date | Dimension | Date de mesure (YYYY-MM-DD) | 2020–2025 | 0% |
| `ville` | string | Dimension | Nom de la ville | 42 valeurs | 0% |
| `region` | string | Dimension | Région administrative | 10 valeurs | 0% |
| `latitude` | float | Dimension | Latitude géographique | [1.5, 13.2] | 0% |
| `longitude` | float | Dimension | Longitude géographique | [8.3, 16.3] | 0% |
| `altitude_m` | float | Dimension | Altitude en mètres | [0, 4000] | 0% |
| `type_climat` | string | Dimension | Catégorie climatique | 5 valeurs | 0% |
| `temp_min_c` | float | Mesure | Température minimale (°C) | [-5, 50] | ~9.9% |
| `temp_max_c` | float | Mesure | Température maximale (°C) | [0, 55] | ~9.9% |
| `temp_mean_c` | float | Mesure | Température moyenne (°C) | [-2, 52] | ~9.9% |
| `humidite_pct` | float | Mesure | Humidité relative (%) | [0, 100] | ~9.9% |
| `precipitations_mm` | float | Mesure | Précipitations (mm/jour) | [0, 300] | ~9.8% |
| `vitesse_vent_ms` | float | Mesure | Vitesse du vent (m/s) | [0, 40] | ~10.0% |
| `direction_vent_deg` | float | Mesure | Direction du vent (°) | [0, 360] | ~9.0% |
| `rafale_max_ms` | float | Mesure | Rafale maximale (m/s) | [0, 60] | ~9.1% |
| `ensoleillement_h` | float | Mesure | Ensoleillement (heures) | [0, 14] | ~9.9% |
| `duree_jour_h` | float | Mesure | Durée astronomique du jour (h) | [10, 14] | 0% |
| `rayonnement_wm2` | float | Mesure | Rayonnement solaire (W/m²) | [0, 1200] | ~10.1% |
| `pm25_proxy_ugm3` | float | **Cible ML** | Proxy PM2.5 (µg/m³) | [0, 3000] | ~9.9% |
| `qualite_capteur` | string | Métadonnée | Qualité de la mesure | high/medium/low | 0% |

---

## Anomalies détectées — Sprint 0 (Validation initiale)

| Colonne | Nb anomalies | Hypothèse | Action prévue |
|---------|-------------|-----------|---------------|
| `rayonnement_wm2` | 2 844 | Dépassement capteur / calibration | Capping + investigation Sprint 1 |
| `humidite_pct` | 1 878 | Erreur capteur (>100% impossible) | Capping à [0,100] Sprint 1 |
| `ensoleillement_h` | 1 697 | Durée > durée du jour (impossible) | Capping à `duree_jour_h` Sprint 1 |
| `temp_mean_c` | 679 | Plage schéma conservatrice ? | Vérifier distribution Sprint 1 |
| `vitesse_vent_ms` | 927 | Pics extrêmes (tempêtes harmattan) | Vérifier avant suppression Sprint 1 |
| `rafale_max_ms` | 805 | Idem vitesse vent | Vérifier avant suppression Sprint 1 |
| `temp_min_c` | 514 | Plage schéma conservatrice ? | Vérifier distribution Sprint 1 |
| `temp_max_c` | 479 | Idem temp_min | Vérifier distribution Sprint 1 |
| `precipitations_mm` | 399 | Événements extrêmes réels ? | Vérifier avec historique Sprint 1 |
| `direction_vent_deg` | 60 | Valeurs hors [0,360] impossible | Modulo 360 ou suppression Sprint 1 |

---

## Dimensions BI

### DIM_DATE
Dérivée de la colonne `date` lors du feature engineering.

| Attribut | Description |
|----------|-------------|
| `jour` | Jour du mois (1–31) |
| `mois` | Mois (1–12) |
| `trimestre` | Trimestre (1–4) |
| `annee` | Année (2020–2025) |
| `saison` | saison_seche / saison_pluies |
| `is_harmattan` | Bool — période harmattan (Nov–Fév, zones Nord) |
| `is_weekend` | Bool |

### DIM_VILLE
Dérivée des colonnes géographiques.

| Attribut | Description |
|----------|-------------|
| `nom` | Nom de la ville |
| `region` | Région administrative |
| `latitude` | Coordonnée géographique |
| `longitude` | Coordonnée géographique |
| `altitude_m` | Altitude |
| `type_climat` | Catégorie climatique |
| `zone_risque_historique` | Calculé Sprint 2 (BI) |

### DIM_CLIMAT: apres investigation - 16/03/2026

| id | type_climat | description |
|----|-------------|-------------|
| 1 | equatorial | Chaud et humide, pluies toute l'année |
| 2 | equatorial_coastal | Équatorial côtier, influence atlantique |
| 3 | highland | Tempéré d'altitude, températures fraîches |
| 4 | sudano_guinean | Transition savane-forêt, 2 saisons |
| 5 | sudanian | Savane soudanienne, saison sèche marquée |
| 6 | tropical | Saison sèche et saison des pluies marquées |
| 7 | sahelian | Semi-aride, harmattan intense, peu de pluies |

**Villes par type :**
- equatorial_coastal : Buea, Douala, Edéa, Kribi, Limbe
- sudanian : Figuil, Garoua, Guider, Poli, Rey-Bouba

### DIM_RISQUE
Définie dans `config/schema.yml` — seuils PM2.5.

| Niveau | Seuil min | Seuil max | Couleur |
|--------|-----------|-----------|---------|
| Faible | 0 | 20 | #22c55e |
| Modéré | 20 | 35 | #eab308 |
| Élevé | 35 | 55 | #f97316 |
| Critique | 55 | ∞ | #ef4444 |

---

## KPIs définis

| ID | Nom | Formule | Dimension d'analyse |
|----|-----|---------|-------------------|
| KPI-01 | PM2.5 moyen | `mean(pm25_proxy_ugm3)` | ville, région, période |
| KPI-02 | Jours critiques | `count(pm25 > 55)` | ville, année |
| KPI-03 | Taux exposition critique | `KPI-02 / total_jours` | région, type_climat |
| KPI-04 | Indice risque composite | `f(pm25, vent, humidité)` | ville, jour |
| KPI-05 | Tendance mensuelle | `(mois_n - mois_n-1) / mois_n-1` | ville |
| KPI-06 | Score prédiction J+1 | Sortie modèle ML | ville, jour |
| KPI-07 | Villes en alerte active | `count(risk = critical)` | national, jour |
