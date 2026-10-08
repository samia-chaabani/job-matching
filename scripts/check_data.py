from pymongo import MongoClient
from collections import Counter

client = MongoClient("mongodb://localhost:27017")
col = client["jobs"]["jobs_raw"]

print("=" * 60)
print("📊 ÉTAT DE LA BASE MONGODB")
print("=" * 60)

# 1. Total global
total = col.count_documents({})
print(f"\n📦 Total documents : {total}")

if total == 0:
    print("❌ Base vide ! Lance les scrapers d'abord.")
    exit()

# 2. Nombre par source
print("\n📂 Répartition par source :")
pipeline = [
    {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
]
for x in col.aggregate(pipeline):
    source = x["_id"] or "(sans source)"
    pct = (x["count"] / total) * 100
    print(f"   {source:20s} : {x['count']:5d}  ({pct:5.1f}%)")

# 3. Qualité des données (champs non vides)
print("\n✅ Qualité des données (champs remplis) :")
champs = ["titre", "entreprise", "lieu", "description", "url", "date_publication",
          "experience", "niveau_etudes", "type_contrat"]
for champ in champs:
    count = col.count_documents({champ: {"$exists": True, "$nin": [None, ""]}})
    pct = (count / total) * 100 if total else 0
    barre = "█" * int(pct / 5)
    print(f"   {champ:20s} : {count:5d} ({pct:5.1f}%) {barre}")

# 4. Top 10 lieux
print("\n🗺️  Top 10 lieux (toutes sources) :")
pipeline = [
    {"$match": {"lieu": {"$nin": [None, ""]}}},
    {"$group": {"_id": "$lieu", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 10},
]
for x in col.aggregate(pipeline):
    print(f"   {x['count']:5d} × {x['_id']}")

# 5. Top 10 entreprises
print("\n🏢 Top 10 entreprises :")
pipeline = [
    {"$match": {"entreprise": {"$nin": [None, ""]}}},
    {"$group": {"_id": "$entreprise", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 10},
]
for x in col.aggregate(pipeline):
    print(f"   {x['count']:5d} × {x['_id']}")

# 6. Top 10 types de contrat
print("\n📄 Types de contrat :")
pipeline = [
    {"$match": {"type_contrat": {"$nin": [None, ""]}}},
    {"$group": {"_id": "$type_contrat", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 10},
]
for x in col.aggregate(pipeline):
    print(f"   {x['count']:5d} × {x['_id']}")

# 7. Exemple de document (le plus récent)
print("\n📄 Exemple de document (dernier scrapé) :")
doc = col.find_one(sort=[("scraped_at", -1)])
if doc:
    for k, v in doc.items():
        if k in ["_id", "markdown"]:
            continue
        v_str = str(v)
        if len(v_str) > 80:
            v_str = v_str[:80] + "..."
        print(f"   {k:20s} : {v_str}")

# 8. Fraîcheur des données
print("\n⏰ Derniers scrapings par source :")
pipeline = [
    {"$match": {"scraped_at": {"$exists": True}}},
    {"$group": {"_id": "$source", "last": {"$max": "$scraped_at"}}},
    {"$sort": {"last": -1}},
]
for x in col.aggregate(pipeline):
    print(f"   {x['_id']:20s} : {x['last']}")

print("\n" + "=" * 60)
print("✅ Vérification terminée")
print("=" * 60)