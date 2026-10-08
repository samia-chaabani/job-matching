import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Test 1 : API sans paramètre (devrait tout retourner)
r = requests.get("https://remotive.com/api/remote-jobs", headers=HEADERS, timeout=30)
data = r.json()
print("=" * 50)
print("TEST 1 : Sans paramètre")
print(f"  Nombre total d'offres retournées : {data.get('job-count', 'N/A')}")
print(f"  Nombre d'offres dans la liste    : {len(data.get('jobs', []))}")

# Test 2 : API avec un limit élevé
r2 = requests.get("https://remotive.com/api/remote-jobs?limit=1000", headers=HEADERS, timeout=30)
data2 = r2.json()
print("=" * 50)
print("TEST 2 : Avec limit=1000")
print(f"  Nombre total d'offres retournées : {data2.get('job-count', 'N/A')}")
print(f"  Nombre d'offres dans la liste    : {len(data2.get('jobs', []))}")

# Test 3 : Une catégorie spécifique
r3 = requests.get("https://remotive.com/api/remote-jobs?category=data", headers=HEADERS, timeout=30)
data3 = r3.json()
print("=" * 50)
print("TEST 3 : category=data")
print(f"  Nombre d'offres : {len(data3.get('jobs', []))}")

# Test 4 : Voir les catégories disponibles dans les résultats
if data2.get("jobs"):
    cats = set(j.get("category") for j in data2["jobs"])
    print("=" * 50)
    print("Catégories disponibles dans l'API :")
    for c in sorted(cats):
        print(f"  - {c}")