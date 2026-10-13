"""
Matching CV - Offres d'emploi
"""
import os
import re
import pickle
import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import faiss

# ============================================================
# CONFIG
# ============================================================
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "jobs"
COLLECTION = "jobs_raw"
INDEX_PATH = "matching/faiss_index.pkl"

# ============================================================
# EXTRACTION DE TEXTE
# ============================================================
def extract_text_from_pdf(path):
    import pdfplumber
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text


def extract_text_from_docx(path):
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text(path):
    """Extrait le texte d'un CV (PDF ou DOCX)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext == ".docx":
        return extract_text_from_docx(path)
    else:
        raise ValueError(f"Format non supporté : {ext}")


# ============================================================
# EXTRACTION DE COMPÉTENCES
# ============================================================
SKILLS = [
    "python", "java", "javascript", "typescript", "c#", "c++", "php",
    "sql", "nosql", "react", "vue", "angular", "node.js", "django",
    "flask", "fastapi", "spring", "laravel", "docker", "kubernetes",
    "aws", "azure", "gcp", "terraform", "jenkins", "git", "linux",
    "spark", "hadoop", "kafka", "airflow", "mongodb", "postgresql",
    "mysql", "oracle", "redis", "machine learning", "deep learning",
    "tensorflow", "pytorch", "nlp", "pandas", "numpy", "power bi",
    "tableau", "excel", "agile", "scrum", "devops",
]


def extract_skills(text):
    """Retourne la liste des compétences trouvées dans le texte."""
    text_lower = text.lower()
    found = set()
    for skill in SKILLS:
        if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
            found.add(skill)
    return sorted(found)


# ============================================================
# VECTORISATION + INDEX FAISS
# ============================================================
def build_index():
    """Construit l'index FAISS à partir des offres MongoDB."""
    print("[INFO] Chargement du modèle Sentence-BERT...")
    model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

    print("[INFO] Lecture MongoDB...")
    client = MongoClient(MONGO_URI)
    col = client[DB_NAME][COLLECTION]
    offres = list(col.find({}, {"_id": 0, "source_id": 1, "titre": 1, "entreprise": 1,
                                 "lieu": 1, "description": 1, "url": 1}))

    print(f"[INFO] {len(offres)} offres trouvées")

    # Texte à vectoriser = titre + description
    texts = [
        f"{o.get('titre', '')} {o.get('description', '')[:2000]}"
        for o in offres
    ]

    print("[INFO] Vectorisation en cours...")
    vectors = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    vectors = np.array(vectors).astype("float32")

    # Index FAISS (Inner Product = cosine similarity quand normalisé)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    # Sauvegarde
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"index": index, "offres": offres, "model_name": "paraphrase-multilingual-mpnet-base-v2"}, f)

    print(f"[OK] Index sauvegardé : {INDEX_PATH}")
    return index, offres, model


def load_index():
    """Charge l'index FAISS depuis le disque."""
    if not os.path.exists(INDEX_PATH):
        return build_index()

    with open(INDEX_PATH, "rb") as f:
        data = pickle.load(f)

    model = SentenceTransformer(data["model_name"])
    return data["index"], data["offres"], model


# ============================================================
# MATCHING
# ============================================================
def match_cv(cv_text, top_k=10):
    """Trouve les top_k offres les plus proches du CV."""
    index, offres, model = load_index()

    # Compétences du CV
    cv_skills = set(extract_skills(cv_text))

    # Vectorise le CV
    cv_vector = model.encode([cv_text], normalize_embeddings=True).astype("float32")

    # Recherche FAISS
    scores, indices = index.search(cv_vector, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        offre = offres[idx]
        offre_skills = set(extract_skills(offre.get("description", "")))

        # Score final = similarité sémantique + overlap compétences
        # Score = compétences du CV qui matchent / compétences du CV
        # (au lieu de compétences de l'offre)
        if cv_skills:
            skill_score = len(cv_skills & offre_skills) / len(cv_skills)
        else:
            skill_score = 0
        final_score = 0.8 * float(score) + 0.2 * skill_score

        results.append({
            "titre": offre.get("titre"),
            "entreprise": offre.get("entreprise"),
            "lieu": offre.get("lieu"),
            "url": offre.get("url"),
            "score": round(final_score * 100, 1),
            "similarite": round(float(score) * 100, 1),
            "competences_communes": sorted(cv_skills & offre_skills),
            "competences_manquantes": sorted(offre_skills - cv_skills)[:5],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results, sorted(cv_skills)


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    # Construire l'index (1ère fois seulement)
    build_index()

    # Test avec un CV fictif
    test_cv = """
    Développeur Python avec 3 ans d'expérience.
    Compétences : Python, SQL, Docker, Git, PostgreSQL, Spark.
    Diplôme : Master en Informatique.
    """

    print("\n" + "=" * 60)
    print("TEST DE MATCHING")
    print("=" * 60)

    results, cv_skills = match_cv(test_cv, top_k=5)

    print(f"\nCompétences détectées dans le CV : {cv_skills}\n")
    print("Top 5 offres :\n")

    for i, r in enumerate(results, 1):
        print(f"{i}. {r['titre']} @ {r['entreprise']} ({r['lieu']})")
        print(f"   Score : {r['score']}%  |  Similarité : {r['similarite']}%")
        print(f"   Communes : {r['competences_communes']}")
        print(f"   Manquantes : {r['competences_manquantes']}")
        print()