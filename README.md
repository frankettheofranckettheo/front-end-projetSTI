# 🏥 Projet STI : Générateur de Cas Cliniques (Backend Extraction)

Ce projet constitue le module backend responsable de l'extraction, de la transformation et de la mise à disposition des données médicales issues de l'hôpital **Fultang**.

Il agit comme un pont sécurisé entre le système hospitalier (API Fultang) et le Module Expert (IA/LLM), en garantissant l'anonymisation, l'intégrité des données et une structuration pédagogique stricte.

---

## 🚀 Fonctionnalités Clés

Ce module répond aux exigences du cahier des charges (Point 2.1) :

* **🔄 Extraction ETL (Extract-Transform-Load) :** Connexion automatisée à l'API Fultang pour récupérer les données brutes.
* **🛡️ Preuve d'Intégrité :** Calcul et stockage d'une signature numérique (**SHA-256**) pour certifier que les données n'ont pas été altérées après extraction.
* **🕵️ Anonymisation Avancée (RGPD) :** Pseudonymisation des identifiants patients et calcul d'âge, suppression des noms/prénoms tout en conservant les données épidémiologiques (Sexe, Région).
* **structure "Figure 1" :** Transformation des données plates en une structure hiérarchique complexe (Mode de vie, Antécédents, Symptômes).
* **🔍 Filtrage Intelligent :** Capacité à isoler des cohortes spécifiques (ex: *Paludisme chez les sujets de > 60 ans*).
* **🎓 Mode Pédagogique Progressif :** API capable de masquer certaines informations (examens, diagnostics) selon le niveau de l'étudiant (Débutant, Intermédiaire, Expert).

---

## 📂 Structure du Projet

```text
📦 extraction-fultang
 ┣ 📜 api.py                 # Serveur FastAPI (Interface avec le Frontend)
 ┣ 📜 extractor.py           # Script de connexion et téléchargement sécurisé
 ┣ 📜 transformer.py         # Moteur de transformation (Données brutes -> Cas Cliniques)
 ┣ 📜 models.py              # Définition des schémas de données (Pydantic / Figure 1)
 ┣ 📜 filter_manager.py      # Logique de filtrage et recherche
 ┣ 📜 reporter.py            # Générateur de rapports de validation (Texte/Markdown)
 ┣ 📜 requirements.txt       # Liste des dépendances Python
 ┗ 📂 raw_data_archive       # Stockage des extractions brutes (avec signatures)
```

---

## 🛠️ Installation

### Pré-requis

* Python 3.8 ou supérieur
* Accès réseau à l'API Fultang (VPN ou Internet)

### 1. Cloner le projet et installer les dépendances

```bash
# Installation des librairies nécessaires
pip install requests fastapi uvicorn pydantic python-dotenv
```

---

## ⚙️ Utilisation

### Étape 1 : Extraction et Transformation (ETL)

Ce script récupère les données, génère la preuve d'intégrité et transforme les données en JSON structuré.

```bash
python transformer.py
```

**Sortie :**

* Crée un fichier `dataset_cas_cliniques_final.json`
* Archive les données dans `raw_data_archive/`

**Note :** Si l'API Fultang est vide, le script passe automatiquement en mode simulation (génération de cas tests : Paludisme, Grippe...).

---

### Étape 2 : Lancement de l'API (Serveur)

Pour rendre les données accessibles au Frontend ou au Module Expert.

```bash
python api.py
```

Le serveur démarrera sur :
👉 `http://0.0.0.0:8000`

---

## 📖 Documentation de l'API

Une fois le serveur lancé, la documentation interactive (Swagger UI) est disponible à l'adresse :

👉 `http://127.0.0.1:8000/docs`

### Principaux Endpoints

| Méthode | URL                        | Description                                                                  |
| ------- | -------------------------- | ---------------------------------------------------------------------------- |
| GET     | `/api/cases`               | Liste tous les cas. Supporte les filtres `keyword`, `min_age`, `max_age`.    |
| GET     | `/api/cases/{id}`          | Détails complets d'un cas clinique spécifique.                               |
| GET     | `/api/cases/{id}/learning` | Mode pédagogique. Paramètre `level` (`debutant`, `intermediaire`, `expert`). |
| POST    | `/api/extract/refresh`     | Déclenche manuellement une nouvelle extraction depuis Fultang.               |

---

## 🧪 Scénarios de Test (Démonstration)

Pour valider le fonctionnement lors de la soutenance :

### Filtrage Métier

Recherche des cas de Paludisme critique :

```bash
curl "http://127.0.0.1:8000/api/cases?keyword=Palu&min_age=60"
```

### Apprentissage (Niveau Expert)

Récupération d'un cas sans les examens ni le diagnostic (l'étudiant doit deviner) :

```bash
curl "http://127.0.0.1:8000/api/cases/CASE-XXX/learning?level=expert"
```

---

## 🔒 Sécurité et Intégrité

Chaque extraction génère un hash **SHA-256** unique basé sur le contenu brut.

Ce hash est :

* Stocké dans le fichier d'archive (`meta.integrity_hash_sha256`)
* Propagé dans chaque objet **CasClinique** (`hash_authentification`)

Cela permet à tout moment d'auditer un cas clinique utilisé par le LLM et de certifier son origine exacte.
