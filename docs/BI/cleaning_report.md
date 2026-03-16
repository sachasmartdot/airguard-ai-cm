# Rapport Nettoyage — AirGuard AI CM

**Sprint :** 2  
**Date :** 2026-03-13  
**Input :** data/raw/cameroon_meteo_hackathon.csv (92 079 lignes)  
**Output :** data/processed/dataset_clean.csv (92 079 lignes)  

---

## Résumé des transformations

| Étape | Action | Résultat |
|-------|--------|----------|
| Capping | 7 variables corrigées | 0 anomalie physique restante |
| Imputation | Médiane ville × mois (cascade) | 0 manquant restant |
| Log-transform | 4 variables (pm25, pluie, vent, rafale) | Skew réduit à < 2 |
| DIM_DATE | 9 features temporelles ajoutées | Saisonnalité capturée |
| DIM_RISQUE | Niveaux de risque calculés | 4 catégories |

---

## Décisions importantes

### Log-transform humidité annulée
- Avant capping : skew = +9.12 → log recommandé
- Après capping [0,100] : skew = -0.57 → acceptable
- Après log : skew = -2.28 → aggravé
- **Décision : utiliser humidite_pct directement**

### Types climatiques enrichis
- 2 types découverts dans l'EDA : equatorial_coastal, sudanian
- Conservés — géographiquement cohérents
- schema.yml mis à jour

---

## Star Schema produit

| Table | Lignes | Taille |
|-------|--------|--------|
| dim_date.csv | 2 192 | 95 KB |
| dim_ville.csv | 42 | 3 KB |
| dim_climat.csv | 7 | < 1 KB |
| dim_risque.csv | 4 | < 1 KB |
| fait_pollution.csv | 92 079 | 16.5 MB |

---

## KPI clés calculés

| KPI | Valeur nationale |
|-----|-----------------|
| PM2.5 médian | 25.7 µg/m³ |
| Jours critiques | 18.4% |
| Jours critiques Nord/Adamaoua/Extrême-Nord | ~43% |
| Jours harmattan (zones Nord) | 12 276 |

---

## Features pour le modèle ML (Sprint 3)
```
Variables météo (originales) :
  temp_min_c, temp_max_c, temp_mean_c
  humidite_pct (pas de log)
  precipitations_mm_log
  vitesse_vent_ms_log
  rafale_max_ms_log
  ensoleillement_h
  duree_jour_h
  rayonnement_wm2
  direction_vent_deg

Variables temporelles :
  mois, trimestre, saison, is_harmattan
  nb_jours_depuis_debut

Variable cible :
  pm25_proxy_ugm3_log (pour l'entraînement)
  pm25_proxy_ugm3     (pour l'affichage dashboard)
```
