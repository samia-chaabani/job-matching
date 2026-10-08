import requests
import time
from datetime import datetime, timezone
from pymongo import MongoClient

API_URL = "https://www.arbeitnow.com/api/job-board-api"
HEADERS = {"User-Agent": "Mozilla/5.0 (projet etudiant data engineering)"}


def fetch_page(page):
    """Récupère une page de l'API Arbeitnow."""
    try:
        r = requests.get(API_URL, params={"page": page}, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print(f"  ❌ Erreur page {page}: {e}")
        return []


def normalize(job):
    """Normalise une offre Arbeitnow au format commun."""
    return {
        "source": "arbeitnow",
        "source_id": f"arbeitnow-{job.get('slug')}",
        "titre": job.get("title"),
        "entreprise": job.get("company_name"),
        "lieu": job.get("location") or "Non spécifié",
        "type_contrat": ", ".join(job.get("job_types", [])),
        "remote": job.get("remote", False),
        "date_publication": datetime.fromtimestamp(job.get("created_at", 0), tz=timezone.utc).strftime("%Y-%m-%d") if job.get("created_at") else None,
        "description": job.get("description", ""),
        "url": job.get("url"),
        "tags": job.get("tags", []),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def main(max_pages=20):
    col = MongoClient("mongodb://localhost:27017")["jobs"]["jobs_raw"]
    col.create_index("source_id", unique=True)

    total_new = 0
    total_skip = 0

    for page in range(1, max_pages + 1):
        print(f"\n📄 Page {page}")
        jobs = fetch_page(page)
        if not jobs:
            print("   ⏹️  Plus d'offres, on s'arrête.")
            break

        for job in jobs:
            doc = normalize(job)
            if col.find_one({"source_id": doc["source_id"]}):
                total_skip += 1
                continue
            col.insert_one(doc)
            total_new += 1

        print(f"   → {len(jobs)} offres | Nouvelles: {total_new} | Skip: {total_skip}")
        time.sleep(1)

    print(f"\n{'='*50}")
    print(f"✅ Nouvelles offres Arbeitnow : {total_new}")
    print(f"📊 Total Arbeitnow en base    : {col.count_documents({'source': 'arbeitnow'})}")
    print(f"📦 Total global en base       : {col.count_documents({})}")


if __name__ == "__main__":
    main()