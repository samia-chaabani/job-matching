import requests, time

HEADERS = {"User-Agent": "Mozilla/5.0 (projet etudiant; contact: ton@email.com)"}
URLS = {
    "robots": "https://www.tanitjobs.com/robots.txt",
    "liste": "https://www.tanitjobs.com/emploi/informatique-tunisie/",
    "recherche": "https://www.tanitjobs.com/jobs/?keywords=developpeur",
}

for name, url in URLS.items():
    r = requests.get(url, headers=HEADERS, timeout=30)
    print(name, r.status_code, len(r.text), "octets")
    with open(f"data/{name}.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    time.sleep(3)