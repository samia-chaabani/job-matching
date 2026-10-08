import requests
import time
from datetime import datetime, timezone
from pymongo import MongoClient

API_URL = "https://remotive.com/api/remote-jobs"
HEADERS = {"User-Agent": "Mozilla/5.0 (projet etudiant data engineering)"}

# Toutes les catégories Remotive
CATEGORIES = [
    "software-dev",
    "data",
    "design",
    "product",
    "marketing",
    "customer-support",
    "sales",
    "finance-legal",
    "human-resources",
    "qa",
    "writing",
    "business",
    "all-others",
]


def fetch_category(category):
    """Récupère les offres d'une catégorie via l'API Remotive."""
    params = {"category": category} if category != "all-others" else {}
    try:
        r = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("jobs", [])
    except Exception as e:
        print(f"  ❌ Erreur {category}: {e}")
        return []


def normalize(job):
    """Normalise une offre Remotive au format commun."""
    return {
        "source": "remotive",
        "source_id": f"remotive-{job.get('id')}",
        "titre": job.get("title"),
        "entreprise": job.get("company_name"),
        "lieu": job.get("candidate_required_location") or "Remote",
        "type_contrat": job.get("job_type"),
        "categorie": job.get("category"),
        "date_publication": job.get("publication_date", "")[:10] if job.get("publication_date") else None,
        "description": job.get("description", ""),
        "url": job.get("url"),
        "salaire": job.get("salary"),
        "tags": job.get("tags", []),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    col = MongoClient("mongodb://localhost:27017")["jobs"]["jobs_raw"]
    col.create_index("source_id", unique=True)

    total_new = 0
    total_skip = 0
    seen_ids = set()

    for cat in CATEGORIES:
        print(f"\n📂 Catégorie: {cat}")
        jobs = fetch_category(cat)
        print(f"   → {len(jobs)} offres récupérées")

        for job in jobs:
            doc = normalize(job)
            if doc["source_id"] in seen_ids:
                continue
            seen_ids.add(doc["source_id"])

            # Skip si déjà en base
            if col.find_one({"source_id": doc["source_id"]}):
                total_skip += 1
                continue

            col.insert_one(doc)
            total_new += 1

        time.sleep(1)  # pause polie entre catégories

    print(f"\n{'='*50}")
    print(f"✅ Nouvelles offres Remotive : {total_new}")
    print(f"⏭️  Déjà en base (skip)      : {total_skip}")
    print(f"📊 Total Remotive en base    : {col.count_documents({'source': 'remotive'})}")
    print(f"📦 Total global en base      : {col.count_documents({})}")


if __name__ == "__main__":
    main()