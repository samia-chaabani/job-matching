import requests
from datetime import datetime, timezone
from pymongo import MongoClient

API_URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "Mozilla/5.0 (projet etudiant data engineering)"}


def normalize(job):
    """Normalise une offre RemoteOK."""
    return {
        "source": "remoteok",
        "source_id": f"remoteok-{job.get('id')}",
        "titre": job.get("position"),
        "entreprise": job.get("company"),
        "lieu": job.get("location") or "Remote",
        "type_contrat": "Remote",
        "date_publication": job.get("date", "")[:10] if job.get("date") else None,
        "description": job.get("description", ""),
        "url": job.get("url"),
        "tags": job.get("tags", []),
        "salaire_min": job.get("salary_min"),
        "salaire_max": job.get("salary_max"),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    col = MongoClient("mongodb://localhost:27017")["jobs"]["jobs_raw"]
    col.create_index("source_id", unique=True)

    r = requests.get(API_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Le 1er élément est un objet "legal", on le skip
    jobs = [j for j in data if isinstance(j, dict) and j.get("id")]

    total_new = 0
    for job in jobs:
        doc = normalize(job)
        if col.find_one({"source_id": doc["source_id"]}):
            continue
        col.insert_one(doc)
        total_new += 1

    print(f"✅ Nouvelles offres RemoteOK : {total_new}")
    print(f"📊 Total RemoteOK en base    : {col.count_documents({'source': 'remoteok'})}")
    print(f"📦 Total global en base       : {col.count_documents({})}")


if __name__ == "__main__":
    main()