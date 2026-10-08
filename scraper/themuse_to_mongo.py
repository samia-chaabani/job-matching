import requests
from datetime import datetime, timezone
from pymongo import MongoClient

BASE_URL = "https://www.themuse.com/api/public/jobs"
HEADERS = {"User-Agent": "Mozilla/5.0 (projet etudiant data engineering)"}

# Pages 1 à 20 → ~400-500 offres
MAX_PAGES = 20


def fetch_page(page):
    try:
        r = requests.get(BASE_URL, params={"page": page}, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception as e:
        print(f"  ❌ Erreur page {page}: {e}")
        return []


def normalize(job):
    # Lieu
    locations = job.get("locations", [])
    lieu = locations[0].get("name") if locations else "Non spécifié"

    # Catégorie
    categories = job.get("categories", [])
    categorie = categories[0].get("name") if categories else None

    # Type de contrat (niveau)
    levels = job.get("levels", [])
    niveau = levels[0].get("name") if levels else None

    return {
        "source": "themuse",
        "source_id": f"themuse-{job.get('id')}",
        "titre": job.get("name"),
        "entreprise": job.get("company", {}).get("name"),
        "lieu": lieu,
        "type_contrat": niveau,
        "categorie": categorie,
        "date_publication": job.get("publication_date", "")[:10] if job.get("publication_date") else None,
        "description": job.get("contents", ""),
        "url": job.get("refs", {}).get("landing_page"),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    col = MongoClient("mongodb://localhost:27017")["jobs"]["jobs_raw"]
    col.create_index("source_id", unique=True)

    total_new = 0
    total_skip = 0

    for page in range(1, MAX_PAGES + 1):
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

    print(f"\n{'='*50}")
    print(f"✅ Nouvelles offres The Muse : {total_new}")
    print(f"📊 Total The Muse en base    : {col.count_documents({'source': 'themuse'})}")
    print(f"📦 Total global en base       : {col.count_documents({})}")


if __name__ == "__main__":
    main()