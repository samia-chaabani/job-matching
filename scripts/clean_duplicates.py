from pymongo import MongoClient
from collections import defaultdict

client = MongoClient("mongodb://localhost:27017")
col = client["jobs"]["jobs_raw"]

print("🧹 Nettoyage des doublons parfaits...")

# Grouper par source_id
pipeline = [
    {"$group": {
        "_id": "$source_id",
        "ids": {"$push": "$_id"},
        "count": {"$sum": 1},
    }},
    {"$match": {"count": {"$gt": 1}}},
]

supprimes = 0
for doc in col.aggregate(pipeline):
    # Garder le 1er, supprimer les autres
    ids_a_supprimer = doc["ids"][1:]
    result = col.delete_many({"_id": {"$in": ids_a_supprimer}})
    supprimes += result.deleted_count
    print(f"   🗑️  {doc['_id']} → {result.deleted_count} supprimés")

print(f"\n✅ Total supprimés : {supprimes}")
print(f"📊 Total restant    : {col.count_documents({})}")