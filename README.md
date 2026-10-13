\# 🎯 Job Market - Data Engineering Pipeline



Pipeline Data Engineering complet pour la collecte, l'analyse et le matching d'offres d'emploi IT.



\## 📊 Vue d'ensemble



Ce projet collecte automatiquement des offres d'emploi depuis \*\*6 sources internationales\*\*,

les nettoie avec \*\*PySpark\*\*, les stocke dans un \*\*Data Warehouse PostgreSQL\*\* en modèle

en étoile, et propose un \*\*matching sémantique\*\* entre un CV et les offres.



\## 🏗️ Architecture

\[6 Sources Web] → \[Scrapy] → \[MongoDB] → \[PySpark] → \[PostgreSQL] → \[Metabase]

↓

\[Matching CV]

↓

\[Streamlit UI]



text



\## 🛠️ Stack technique



| Composant | Technologie |

| :--- | :--- |

| \*\*Scraping\*\* | Python, Scrapy, Requests |

| \*\*Stockage brut\*\* | MongoDB |

| \*\*Traitement\*\* | PySpark (ETL) |

| \*\*Data Warehouse\*\* | PostgreSQL (modèle en étoile) |

| \*\*NLP\*\* | Sentence-BERT, FAISS |

| \*\*Dashboard\*\* | Metabase |

| \*\*Interface\*\* | Streamlit |

| \*\*Infra\*\* | Docker, Docker Compose |



\## 📈 Chiffres clés



\- \*\*3557 offres\*\* collectées depuis 6 sources

\- \*\*3376 offres\*\* après nettoyage et dédoublonnage

\- \*\*86 compétences\*\* techniques extraites automatiquement

\- \*\*7 tables\*\* dans le Data Warehouse

\- \*\*4340 associations\*\* offres-compétences



\## 🚀 Installation



\### Prérequis



\- Python 3.11

\- Docker Desktop

\- Java 17 (pour PySpark)



\### Lancer le projet



```bash

\# 1. Cloner le repo

git clone https://github.com/TON-USER/job-matching.git

cd job-matching



\# 2. Créer le venv

python -m venv venv

venv\\Scripts\\activate  # Windows



\# 3. Installer les dépendances

pip install -r requirements.txt



\# 4. Lancer Docker

docker compose up -d



\# 5. Scraper les offres

python scraper/keejob\_to\_mongo.py

python scraper/arbeitnow\_to\_mongo.py

\# (autres sources...)



\# 6. Lancer l'ETL

python etl/jobs\_etl.py



\# 7. Lancer l'interface de matching

streamlit run frontend/app.py

📁 Structure du projet

text

job-matching/

├── scraper/           # Scripts de scraping

├── etl/               # Pipeline ETL PySpark + schéma SQL

├── matching/          # Module de matching CV-offres

├── frontend/          # Interface Streamlit

├── scripts/           # Scripts utilitaires

├── docs/              # Documentation et captures

├── docker-compose.yml

└── README.md

🎯 Fonctionnalités

1\. Collecte automatique

Scraping de 6 sources (Keejob, Arbeitnow, The Muse, RemoteOK, WeWorkRemotely, Hacker News)



Stockage brut dans MongoDB



2\. ETL avec PySpark

Nettoyage et dédoublonnage



Extraction de 86 compétences techniques



Parsing de l'expérience et du niveau d'études



3\. Data Warehouse

Modèle en étoile (7 tables)



1 table de faits + 6 dimensions



4\. Dashboard analytique

Top 15 compétences les plus demandées



Top 10 villes qui recrutent



Offres par mois



Répartition par type de contrat



5\. Matching CV

Upload de CV (PDF/DOCX)



Extraction automatique des compétences



Matching sémantique avec Sentence-BERT



Score de pertinence + compétences manquantes



🎓 Compétences démontrées

Data Engineering : ETL, PySpark, modélisation en étoile



Big Data : traitement de données à grande échelle



NLP : Sentence-BERT, FAISS, extraction d'entités



DevOps : Docker, Docker Compose



Web : Scraping, Streamlit, API REST



Bases de données : PostgreSQL, MongoDB



📝 Perspectives

□ Orchestration avec Apache Airflow

□ Monitoring avec Prometheus + Grafana

□ Ajout de nouvelles sources (LinkedIn, Indeed)

□ Amélioration du matching (fine-tuning du modèle)

□ Déploiement cloud (AWS/GCP)

👤 Auteure

Samia Chaabani - Étudiante en cycle ingénieur



Projet personnel réalisé dans le cadre de l'apprentissage du Data Engineering.

