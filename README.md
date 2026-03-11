# AirGuard AI CM

**Système Intelligent d'Aide à la Décision Climatique et Sanitaire**  
IndabaX Hackathon Cameroun 2026

## Objectif
Prédire les indicateurs de pollution atmosphérique (proxy PM2.5) à partir
des données météorologiques quotidiennes des 42 villes du Cameroun,
et diffuser des alertes actionnables aux populations exposées.

## Structure
```
airguard-ai-cm/
├── data/
│   ├── raw/          # Données brutes (non versionnées)
│   └── processed/    # Données nettoyées
├── notebooks/        # EDA + modélisation
├── models/           # Scripts ML + artefacts
├── dashboard/        # Interface visuelle
├── alerts/           # Système d'alerte multicanal
└── docs/             # Documentation
```

## Stack
- Python · Pandas · Scikit-learn · XGBoost
- HTML/CSS/JS vanilla · Chart.js · SVG
- Africa's Talking API (SMS)

## Équipe
SachaSmart·IndabaX2026
