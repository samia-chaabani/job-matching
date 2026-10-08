from pymongo import MongoClient
from collections import Counter

client = MongoClient("mongodb://localhost:27017")
col = client["jobs"]["jobs_raw"]

total = col.count_documents({})
print("=" * 60)
print(f"📊 ANALYSE DES DOUBLONS ({total} documents)")
print("=" * 60)

# ============================================================
# 1. Doublons parfaits (même source_id)
# ============================================================
print("\n🔴 1. Doublons parfaits (même source_id) :")
pipeline = [
    {"$group": {"_id": "$source_id", "count": {"$sum": 1}}},
    {"$match": {"count": {"$gt": 1}}},
    {"$sort": {"count": -1}},
]
doublons_parfaits = list(col.aggregate(pipeline))
if doublons_parfaits:
    for x in doublons_parfaits[:10]:
        print(f"   ⚠️  {x['_id']} apparaît {x['count']} fois")
    print(f"   → Total : {len(doublons_parfaits)} source_id en doublon")
else:
    print("   ✅ Aucun doublon parfait !")

# ============================================================
# 2. Doublons par titre + entreprise
# ============================================================
print("\n🟡 2. Doublons par titre + entreprise :")
pipeline = [
    {"$match": {
        "titre": {"$nin": [None, ""]},
        "entreprise": {"$nin": [None, ""]},
    }},
    {"$group": {
        "_id": {"titre": "$titre", "entreprise": "$entreprise"},
        "count": {"$sum": 1},
        "sources": {"$addToSet": "$source"},
    }},
    {"$match": {"count": {"$gt": 1}}},
    {"$sort": {"count": -1}},
]
doublons_titre = list(col.aggregate(pipeline))
if doublons_titre:
    for x in doublons_titre[:10]:
        sources = ", ".join(x["sources"])
        print(f"   ⚠️  [{x['count']}×] {x['_id']['titre'][:50]} | {x['_id']['entreprise'][:30]} | ({sources})")
    print(f"   → Total : {len(doublons_titre)} paires en doublon")
else:
    print("   ✅ Aucun doublon titre+entreprise !")

# ============================================================
# 3. Doublons par titre + lieu
# ============================================================
print("\n🟠 3. Doublons par titre + lieu :")
pipeline = [
    {"$match": {
        "titre": {"$nin": [None, ""]},
        "lieu": {"$nin": [None, ""]},
    }},
    {"$group": {
        "_id": {"titre": "$titre", "lieu": "$lieu"},
        "count": {"$sum": 1},
    }},
    {"$match": {"count": {"$gt": 1}}},
    {"$sort": {"count": -1}},
]
doublons_lieu = list(col.aggregate(pipeline))
if doublons_lieu:
    for x in doublons_lieu[:5]:
        print(f"   ⚠️  [{x['count']}×] {x['_id']['titre'][:50]} | {x['_id']['lieu'][:30]}")
    print(f"   → Total : {len(doublons_lieu)} paires en doublon")
else:
    print("   ✅ Aucun doublon titre+lieu !")

# ============================================================
# 4. Statistiques par source
# ============================================================
print("\n📊 4. Répartition par source :")
for x in col.aggregate([
    {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
]):
    print(f"   {x['_id']:20s} : {x['count']}")

# ============================================================
# 5. Résumé
# ============================================================
print("\n" + "=" * 60)
print("📋 RÉSUMÉ")
print("=" * 60)
print(f"   Total documents              : {total}")
print(f"   source_id uniques            : {len(col.distinct('source_id'))}")
print(f"   titres uniques               : {len(col.distinct('titre'))}")
print(f"   entreprises uniques          : {len(col.distinct('entreprise'))}")
print(f"   lieux uniques                : {len(col.distinct('lieu'))}")
print()
if len(doublons_parfaits) == 0:
    print("   ✅ Aucun doublon critique (source_id)")
else:
    print(f"   🔴 {len(doublons_parfaits)} source_id en doublon → à nettoyer")