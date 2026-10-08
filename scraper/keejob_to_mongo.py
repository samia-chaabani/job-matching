import re
import sys
import time
import requests
from datetime import datetime, timezone
from pymongo import MongoClient

LISTING = "https://www.keejob.com/llms-full.txt"
HEADERS = {"User-Agent": "Mozilla/5.0 (projet etudiant data engineering)"}
DELAY = 2

IT_PATTERN = re.compile(
    r"d[ée]veloppeu|developer|full[\s-]?stack|front|back[\s-]?end|devops|"
    r"data|\bia\b|\bit\b|informatique|software|logiciel|web|mobile|cyber|"
    r"r[ée]seau|syst[èe]me|erp|ux/?ui|helpdesk|service desk|"
    r"support technique|chef de projet (erp|informatique|it)|analyste fonctionnel|"
    r"technicien infrastructure|int[ée]grateur",
    re.IGNORECASE,
)

LINE = re.compile(r"^- \[(.+)\]\((https://[^)]+\.md)\): (.*)$")


def parse_markdown(md):
    """Extrait les champs structurés du markdown Keejob."""
    data = {}

    # Champs "- **Clé** : Valeur"
    patterns = {
        "entreprise": r"-\s*\*\*Entreprise\*\*\s*:\s*\[([^\]]+)\]",
        "lieu": r"-\s*\*\*Lieu\*\*\s*:\s*([^\n]+)",
        "type_contrat": r"-\s*\*\*Type de contrat\*\*\s*:\s*([^\n]+)",
        "mode_travail": r"-\s*\*\*Mode de travail\*\*\s*:\s*([^\n]+)",
        "niveau_etudes": r"-\s*\*\*Niveau d'études\*\*\s*:\s*([^\n]+)",
        "experience": r"-\s*\*\*Expérience\*\*\s*:\s*([^\n]+)",
        "langues": r"-\s*\*\*Langues\*\*\s*:\s*([^\n]+)",
        "metiers": r"-\s*\*\*Métiers\*\*\s*:\s*([^\n]+)",
        "date_publication": r"-\s*\*\*Date de publication\*\*\s*:\s*([^\n]+)",
        "date_expiration": r"-\s*\*\*Date d'expiration\*\*\s*:\s*([^\n]+)",
        "reference": r"-\s*\*\*Référence Keejob\*\*\s*:\s*([^\n]+)",
        "statut": r"-\s*\*\*Statut\*\*\s*:\s*([^\n]+)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, md)
        data[key] = m.group(1).strip() if m else None

    # Description (tout après "## Description")
    desc_match = re.search(r"## Description\s*\n(.*)", md, re.DOTALL)
    data["description"] = desc_match.group(1).strip() if desc_match else ""

    return data


def parse_line(line):
    m = LINE.match(line)
    if not m:
        return None
    titre, url, reste = m.groups()
    id_match = re.search(r"/offres-emploi/(\d+)/", url)
    if not id_match:
        return None

    parts = [p.strip() for p in reste.split(" · ")]
    return {
        "source": "keejob",
        "source_id": f"keejob-{id_match.group(1)}",
        "titre": titre.replace("\\", ""),
        "url": url,
        "lieu_listing": parts[1] if len(parts) > 1 else None,
        "entreprise_listing": parts[0] if parts else None,
    }


def main(limit):
    col = MongoClient("mongodb://localhost:27017")["jobs"]["jobs_raw"]
    col.create_index("source_id", unique=True)

    r = requests.get(LISTING, headers=HEADERS, timeout=30)
    r.raise_for_status()
    offres = [o for o in map(parse_line, r.text.splitlines()) if o]
    print("Offres dans la liste :", len(offres))

   # Plus de filtre IT : on prend TOUT
    it = offres
    print("Offres totales (toutes spécialités) :", len(it))
    if limit:
        it = it[:limit]

    ok = 0
    for o in it:
        # Skip si déjà scrapé avec markdown
        if col.find_one({"source_id": o["source_id"], "description": {"$exists": True, "$ne": ""}}):
            print("SKIP (déjà en base) :", o["titre"][:60])
            continue

        resp = requests.get(o["url"], headers=HEADERS, timeout=30)
        if resp.status_code == 403:
            print("403 reçu : arrêt.")
            break
        if resp.status_code != 200:
            print(resp.status_code, o["url"])
            continue

        resp.encoding = "utf-8"
        o["markdown"] = resp.text
        o["scraped_at"] = datetime.now(timezone.utc).isoformat()

        # Enrichir avec le parsing
        parsed = parse_markdown(resp.text)
        o.update(parsed)

        col.update_one({"source_id": o["source_id"]}, {"$set": o}, upsert=True)
        ok += 1
        print("OK", o["titre"][:60], "|", o.get("experience"), "|", o.get("niveau_etudes"))
        time.sleep(DELAY)

    print("Nouvelles offres :", ok)
    print("Total en base :", col.count_documents({}))
    print("Dont keejob :", col.count_documents({"source": "keejob"}))
    print("Dont avec description :", col.count_documents({"source": "keejob", "description": {"$ne": ""}}))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 0)