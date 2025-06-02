
# Datalogger API


Cette application fournit une API REST pour gérer les mesures collectées par plusieurs dataloggers.  
Elle permet de récupérer des données agrégées (moyennes, sommes) selon différents intervalles de temps (heure, jour) et types de métriques (température, humidité, précipitations).  
L'API permet aussi d'accéder aux données brutes et d'ajouter de nouvelles mesures via une requête POST.

L'API suit la spécification OpenAPI disponible dans le fichier `openAPI-specs.json`.

L'API a été testée avec `django_rest_framework` qui fournit des outils de tests suffisants pour les besoins de l'application, 30 tests ont été écrits en tout, testant l’intégrité des données, le renvoi des erreurs, etc. 

Le code et les commentaires sont en anglais pour rester cohérent avec les standards de développement et faciliter la collaboration.

Un hook de pre-commit qui lance ruff et mypy sur le code a été ajouté pour formater le code et vérifier le typing.

## Technologies utilisées

- **Python 3.12.10**
- **Django 5.2.1**
- **Django REST Framework 3.16.0**
- **PostgreSQL 17.5**
- **Outils qualité :** `ruff`, `mypy` et `pre-commit` pour garantir un code propre et typé.

---

## Installation

1. Cloner le dépôt :

```bash
git clone https://github.com/yerok/weenat_test
cd weenat_test
```

2. Créer et activer un environnement virtuel Python :

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

1. Configurer PostgreSQL :

```sql
sudo -u postgres psql
CREATE DATABASE weenat_test_db;
CREATE USER weenat_tester WITH PASSWORD 'weenat_tester';
GRANT ALL PRIVILEGES ON DATABASE weenat_test_db TO weenat_tester;
```

5. Appliquer les migrations Django :

```bash
python manage.py migrate
```

## Utilisation

Lancer le serveur de développement :

```bash
python manage.py runserver
```

Lancer les tests du dossiers tests :

```bash
python manage.py test
```

L'API est accessible à l'adresse :  
http://localhost:8000/api/

## Endpoints API

| Endpoint       | Méthode | Description                                      | Paramètres                     |
|----------------|---------|--------------------------------------------------|---------------------------------|
| `/api/data`    | GET     | Récupération des données brutes                 | `since`, `before`, `datalogger` |
| `/api/summary` | GET     | Récupération des données agrégées (ou brutes)   | `since`, `before`, `span`, `datalogger` |
| `/api/ingest`  | POST    | Insertion de nouvelles mesures                  | Payload JSON avec données à insérer |

## Commandes Django à but de test

| Commande            | Description                                      | Paramètres |
|---------------------|--------------------------------------------------|------------|
| `/api/populate_db`  | Remplit la base avec des données de test         | `--dataloggers` (int, défaut: 3) Nombre de dataloggers<br>`--measurements` (int, défaut: 50) Mesures par datalogger |
| `/api/check_db`     | Indique le nombre de dataloggers et de mesures en base | - |
| `/api/clear_db`     | Vide la base de données                         | - |

