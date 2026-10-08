import feedparser
from datetime import datetime, timezone
from pymongo import MongoClient

# Flux RSS par catégorie
FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-product-jobs.rss",
    "https://weworkremotely.com/categories/remote-marketing-jobs.rss",
]


def normalize(entry):
    return {
        "source": "weworkremotely",
        "source_id": f"wwr-{entry.get('id', entry.get('link'))}",
        "titre": entry.get("title"),
        "entreprise": entry.get("author", "N/A"),
        "lieu": "Remote",
        "type_contrat": "Remote",
        "date_publication": entry.get("published", "")[:10] if entry.get("published") else None,
        "description": entry.get("summary", ""),
        "url": entry.get("link"),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    col = MongoClient("mongodb://localhost:27017")["jobs"]["jobs_raw"]
    col.create_index("source_id", unique=True)

    total_new = 0
    total_skip = 0

    for feed_url in FEEDS:
        print(f"\n📡 {feed_url.split('/')[-2]}")
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            doc = normalize(entry)
            if col.find_one({"source_id": doc["source_id"]}):
                total_skip += 1
                continue
            col.insert_one(doc)
            total_new += 1

        print(f"   → {len(feed.entries)} offres | Nouvelles: {total_new}")

    print(f"\n{'='*50}")
    print(f"✅ Nouvelles offres WWR : {total_new}")
    print(f"📊 Total WWR en base    : {col.count_documents({'source': 'weworkremotely'})}")
    print(f"📦 Total global en base : {col.count_documents({})}")


if __name__ == "__main__":
    main()