import requests
import time
from datetime import datetime, timezone
from pymongo import MongoClient

HN_API = "https://hacker-news.firebaseio.com/v0"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_item(item_id):
    try:
        r = requests.get(f"{HN_API}/item/{item_id}.json", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def normalize(item):
    return {
        "source": "hackernews",
        "source_id": f"hn-{item.get('id')}",
        "titre": item.get("title"),
        "entreprise": "HN Who's Hiring",
        "lieu": "Remote / Mondial",
        "type_contrat": "Full-time",
        "date_publication": datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc).strftime("%Y-%m-%d"),
        "description": item.get("text", "") or "",
        "url": item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    col = MongoClient("mongodb://localhost:27017")["jobs"]["jobs_raw"]
    col.create_index("source_id", unique=True)

    # Top 500 stories
    r = requests.get(f"{HN_API}/topstories.json", headers=HEADERS, timeout=30)
    story_ids = r.json()[:500]

    total_new = 0
    total_skip = 0

    for i, sid in enumerate(story_ids):
        item = fetch_item(sid)
        if not item:
            continue

        title = (item.get("title") or "").lower()
        # On garde seulement les posts "Who is hiring"
        if "hiring" not in title and "job" not in title and "remote" not in title:
            continue

        doc = normalize(item)
        if col.find_one({"source_id": doc["source_id"]}):
            total_skip += 1
            continue
        col.insert_one(doc)
        total_new += 1

        if total_new % 20 == 0:
            print(f"  → {total_new} nouvelles offres HN")

        time.sleep(0.1)  # API HN tolère bien

    print(f"\n✅ Nouvelles offres HN : {total_new}")
    print(f"📊 Total HN en base    : {col.count_documents({'source': 'hackernews'})}")


if __name__ == "__main__":
    main()