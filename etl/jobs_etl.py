"""
ETL PySpark : MongoDB -> nettoyage -> PostgreSQL (modele en etoile)
Compatible PySpark 4.0+
"""
import os

# ==== Configuration Hadoop Windows (OBLIGATOIRE) ====
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
os.environ["hadoop.home.dir"] = r"C:\hadoop"

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, trim, when, lit, regexp_extract,
    try_to_date, year, month, quarter, dayofmonth,
    explode, length, udf
)
from pyspark.sql.types import IntegerType, StringType, ArrayType

# ============================================================
# CONFIG
# ============================================================
MONGO_URI = "mongodb://localhost:27017/jobs.jobs_raw"
PG_URL = "jdbc:postgresql://localhost:5434/jobs_dw"
PG_PROPS = {
    "user": "admin",
    "password": "admin",
    "driver": "org.postgresql.Driver",
}

# ============================================================
# DICTIONNAIRE DE COMPETENCES
# ============================================================
SKILLS = {
    "python": "Langage", "java": "Langage", "javascript": "Langage",
    "typescript": "Langage", "c#": "Langage", "c++": "Langage",
    "php": "Langage", "ruby": "Langage", "go": "Langage", "rust": "Langage",
    "scala": "Langage", "kotlin": "Langage", "swift": "Langage",
    "r": "Langage", "matlab": "Langage", "sql": "Langage", "nosql": "Langage",
    "react": "Framework", "vue": "Framework", "angular": "Framework",
    "next.js": "Framework", "svelte": "Framework", "html": "Frontend",
    "css": "Frontend", "sass": "Frontend", "tailwind": "Frontend",
    "bootstrap": "Frontend", "jquery": "Frontend",
    "node.js": "Framework", "express": "Framework", "django": "Framework",
    "flask": "Framework", "fastapi": "Framework", "spring": "Framework",
    "laravel": "Framework", "symfony": "Framework", ".net": "Framework",
    "spark": "Big Data", "hadoop": "Big Data", "kafka": "Big Data",
    "airflow": "Big Data", "hive": "Big Data", "flink": "Big Data",
    "elasticsearch": "Big Data", "mongodb": "Base de donnees",
    "postgresql": "Base de donnees", "mysql": "Base de donnees",
    "oracle": "Base de donnees", "sql server": "Base de donnees",
    "redis": "Base de donnees", "cassandra": "Base de donnees",
    "snowflake": "Base de donnees", "bigquery": "Base de donnees",
    "docker": "DevOps", "kubernetes": "DevOps", "aws": "Cloud",
    "azure": "Cloud", "gcp": "Cloud", "terraform": "DevOps",
    "ansible": "DevOps", "jenkins": "DevOps", "gitlab": "DevOps",
    "github": "DevOps", "git": "DevOps", "ci/cd": "DevOps",
    "linux": "Systeme", "bash": "Systeme",
    "machine learning": "IA", "deep learning": "IA", "tensorflow": "IA",
    "pytorch": "IA", "scikit-learn": "IA", "nlp": "IA", "computer vision": "IA",
    "pandas": "Data Science", "numpy": "Data Science",
    "power bi": "BI", "tableau": "BI", "looker": "BI", "qlik": "BI",
    "excel": "BI", "metabase": "BI",
    "agile": "Methode", "scrum": "Methode", "kanban": "Methode",
    "devops": "Methode", "tdd": "Methode",
}


def extract_skills_udf(text):
    if not text:
        return []
    import re
    text_lower = text.lower()
    found = set()
    for skill in SKILLS.keys():
        if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
            found.add(skill)
    return sorted(list(found))


extract_skills = udf(extract_skills_udf, ArrayType(StringType()))


def parse_experience_udf(exp_str):
    if not exp_str:
        return (None, None)
    import re
    exp_str = exp_str.lower()
    if "aucune" in exp_str or "sans experience" in exp_str:
        return (0, 0)
    if "moins d'un an" in exp_str:
        return (0, 1)
    m = re.search(r"entre\s+(\d+)\s+et\s+(\d+)", exp_str)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = re.search(r"(\d+)\s*ans?\s*(et\s*\+|\+)", exp_str)
    if m:
        return (int(m.group(1)), None)
    return (None, None)


parse_experience = udf(parse_experience_udf, ArrayType(IntegerType()))


def main():
    spark = (
        SparkSession.builder
        .appName("JobMarketETL")
        .config("spark.jars.packages",
                "org.mongodb.spark:mongo-spark-connector_2.13:11.0.0,"
                "org.postgresql:postgresql:42.7.3")
        .config("spark.mongodb.read.connection.uri", MONGO_URI)
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    print("\n" + "=" * 60)
    print("[ETL] PySpark : MongoDB -> PostgreSQL")
    print("=" * 60)

    print("\n[EXTRACT] Lecture MongoDB...")
    df = spark.read.format("mongodb").load()
    print(f"   Total documents : {df.count()}")

    print("\n[TRANSFORM] Nettoyage...")

    df_clean = df.select(
        col("source_id"),
        trim(col("titre")).alias("titre"),
        trim(col("entreprise")).alias("entreprise"),
        trim(col("lieu")).alias("lieu"),
        trim(col("type_contrat")).alias("type_contrat"),
        trim(col("niveau_etudes")).alias("niveau_etudes"),
        col("experience"),
        col("description"),
        col("url"),
        try_to_date(col("date_publication"), "yyyy-MM-dd").alias("date_publication"),
        col("source"),
        col("scraped_at"),
    )

    df_clean = df_clean.filter(
        col("titre").isNotNull() & (length(col("titre")) > 0)
    )

    print("   Dedoublonnage sur titre + entreprise...")
    df_clean = df_clean.dropDuplicates(["titre", "entreprise"])

    print("   Extraction des competences...")
    df_clean = df_clean.withColumn("competences", extract_skills(col("description")))

    print("   Parsing de l'experience...")
    df_clean = df_clean.withColumn("exp_parsed", parse_experience(col("experience")))
    df_clean = (
        df_clean
        .withColumn("experience_min", col("exp_parsed")[0])
        .withColumn("experience_max", col("exp_parsed")[1])
        .drop("exp_parsed")
    )

    print("   Normalisation des lieux...")
    df_clean = df_clean.withColumn(
        "ville",
        when(col("lieu").contains(","), regexp_extract(col("lieu"), r"^([^,]+)", 1))
        .otherwise(col("lieu"))
    )

    df_clean.cache()
    total_final = df_clean.count()
    print(f"   [OK] Apres nettoyage : {total_final} offres")

    print("\n[LOAD] Ecriture PostgreSQL...")

    print("   -> dim_temps")
    df_temps = (
        df_clean
        .filter(col("date_publication").isNotNull())
        .select("date_publication")
        .distinct()
        .withColumn("jour", dayofmonth("date_publication"))
        .withColumn("mois", month("date_publication"))
        .withColumn("trimestre", quarter("date_publication"))
        .withColumn("annee", year("date_publication"))
        .withColumnRenamed("date_publication", "date_complete")
    )
    df_temps.write.jdbc(url=PG_URL, table="dim_temps", mode="append", properties=PG_PROPS)

    print("   -> dim_lieu")
    df_lieu = (
        df_clean
        .filter(col("ville").isNotNull() & (length(col("ville")) > 0))
        .select(col("ville"), lit("Tunisie").alias("pays"))
        .distinct()
    )
    df_lieu.write.jdbc(url=PG_URL, table="dim_lieu", mode="append", properties=PG_PROPS)

    print("   -> dim_entreprise")
    df_entreprise = (
        df_clean
        .filter(col("entreprise").isNotNull() & (length(col("entreprise")) > 0))
        .select(col("entreprise").alias("nom"), lit(None).cast(StringType()).alias("secteur"))
        .distinct()
    )
    df_entreprise.write.jdbc(url=PG_URL, table="dim_entreprise", mode="append", properties=PG_PROPS)

    print("   -> dim_contrat")
    df_contrat = (
        df_clean
        .filter(col("type_contrat").isNotNull())
        .select(col("type_contrat"), lit(None).cast(StringType()).alias("mode_travail"))
        .distinct()
    )
    df_contrat.write.jdbc(url=PG_URL, table="dim_contrat", mode="append", properties=PG_PROPS)

    print("   -> dim_competence")
    df_comp = (
        df_clean
        .select(explode(col("competences")).alias("nom"))
        .distinct()
        .withColumn("categorie", lit(None).cast(StringType()))
    )
    df_comp.write.jdbc(url=PG_URL, table="dim_competence", mode="append", properties=PG_PROPS)

    print("   -> fait_offres (avec jointures)")
    dim_lieu_db = spark.read.jdbc(url=PG_URL, table="dim_lieu", properties=PG_PROPS)
    dim_ent_db = spark.read.jdbc(url=PG_URL, table="dim_entreprise", properties=PG_PROPS)
    dim_temps_db = spark.read.jdbc(url=PG_URL, table="dim_temps", properties=PG_PROPS)
    dim_contrat_db = spark.read.jdbc(url=PG_URL, table="dim_contrat", properties=PG_PROPS)

    df_fait = (
        df_clean
        .join(dim_lieu_db, df_clean["ville"] == dim_lieu_db["ville"], "left")
        .join(dim_ent_db, df_clean["entreprise"] == dim_ent_db["nom"], "left")
        .join(dim_temps_db, df_clean["date_publication"] == dim_temps_db["date_complete"], "left")
        .join(dim_contrat_db, df_clean["type_contrat"] == dim_contrat_db["type_contrat"], "left")
        .select(
            col("source_id"),
            col("titre"),
            col("id_entreprise"),
            col("id_lieu"),
            col("id_contrat"),
            col("id_temps"),
            col("experience_min"),
            col("experience_max"),
            col("niveau_etudes"),
            lit(None).cast(StringType()).alias("langues"),
            col("description"),
            col("url"),
            col("scraped_at").cast("timestamp"),
        )
    )
    df_fait.write.jdbc(url=PG_URL, table="fait_offres", mode="append", properties=PG_PROPS)

    print("   -> offre_competence")
    dim_comp_db = spark.read.jdbc(url=PG_URL, table="dim_competence", properties=PG_PROPS)
    fait_db = spark.read.jdbc(url=PG_URL, table="fait_offres", properties=PG_PROPS)

    df_offre_comp = (
        df_clean
        .select(col("source_id"), explode(col("competences")).alias("nom"))
        .join(dim_comp_db, "nom", "left")
        .join(fait_db.select("id_offre", "source_id"), "source_id", "left")
        .select("id_offre", "id_competence")
        .filter(col("id_offre").isNotNull() & col("id_competence").isNotNull())
        .distinct()
    )
    df_offre_comp.write.jdbc(url=PG_URL, table="offre_competence", mode="append", properties=PG_PROPS)

    print("\n" + "=" * 60)
    print("[OK] ETL termine avec succes !")
    print("=" * 60)

    spark.stop()


if __name__ == "__main__":
    main()