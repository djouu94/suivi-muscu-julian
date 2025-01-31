# Suivi d'Entraînement - Application Streamlit

Application de suivi d'entraînement développée avec Streamlit.

## Installation

1. Créer un environnement virtuel :
```bash
python -m venv venv
```

2. Activer l'environnement virtuel :
```bash
# Windows
venv\Scripts\activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Lancement de l'application

```bash
streamlit run app.py
```

## Fonctionnalités

- Sélection du programme d'entraînement
- Suivi des séries et répétitions
- Historique des exercices
- Visualisation des dernières séances
- Base de données SQLite pour le stockage

## Structure du projet

- `app.py` : Application principale
- `requirements.txt` : Dépendances Python
- `workout.db` : Base de données SQLite (créée automatiquement)
