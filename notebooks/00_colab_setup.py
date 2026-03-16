"""
00_colab_setup.py
=================
Script de configuration pour Google Colab.
À convertir en notebook .ipynb pour la démo hackathon.

Ce script :
1. Clone le repo depuis GitHub
2. Installe les dépendances
3. Monte les données
4. Vérifie que tout fonctionne

Auteur  : AirGuard Team
Version : 1.0.0
"""

# ── Cellule 1 : Clone du repo ────────────────────────────────
# À exécuter uniquement dans Google Colab
# (décommente les lignes suivantes dans Colab)

# !git clone https://github.com/TON_USERNAME/airguard-ai-cm.git
# %cd airguard-ai-cm
# !pip install -r requirements.txt -q

# ── Cellule 2 : Upload des données dans Colab ────────────────
# Colab ne peut pas accéder à ton disque local directement
# Deux options :

# Option A — Upload manuel (simple pour la démo)
# from google.colab import files
# uploaded = files.upload()  # sélectionne cameroon_meteo_hackathon.csv
# import shutil
# shutil.move("cameroon_meteo_hackathon.csv", "data/raw/")

# Option B — Depuis Google Drive (recommandé pour le travail régulier)
# from google.colab import drive
# drive.mount('/content/drive')
# import shutil
# shutil.copy(
#     '/content/drive/MyDrive/airguard/cameroon_meteo_hackathon.csv',
#     'data/raw/cameroon_meteo_hackathon.csv'
# )

# ── Cellule 3 : Vérification ─────────────────────────────────
# import subprocess
# result = subprocess.run(
#     ["python", "config/validate_schema.py"],
#     capture_output=True, text=True
# )
# print(result.stdout)

print("Configuration Colab documentée.")
print("Voir les commentaires pour les instructions d'utilisation.")
```

---

## Stratégie Git pour Colab

La bonne pratique est de **toujours travailler localement et pousser sur GitHub**. Colab tire depuis GitHub. Le flux est :
```
Tu codes localement
      ↓
git push origin feature/ml-pipeline
      ↓
Colab : !git pull origin feature/ml-pipeline
      ↓
Colab exécute le code à jour
