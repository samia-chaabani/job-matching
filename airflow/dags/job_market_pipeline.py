"""
DAG : Job Market Pipeline
Orchestre le scraping et l'ETL toutes les 6 heures.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# ============================================================
# CONFIG
# ============================================================
PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "samia",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="job_market_pipeline",
    description="Pipeline de collecte et transformation des offres d'emploi",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 */6 * * *",  # Toutes les 6h
    catchup=False,
    tags=["data-engineering", "job-market"],
) as dag:

    # ============================================================
    # TÂCHE 0 : Vérification de l'environnement
    # ============================================================
    check_env = BashOperator(
        task_id="check_env",
        bash_command=f"echo 'Projet : {PROJECT_DIR}' && ls -la {PROJECT_DIR}",
    )

    # ============================================================
    # TÂCHES DE SCRAPING (en parallèle)
    # ============================================================
    scrape_keejob = BashOperator(
        task_id="scrape_keejob",
        bash_command=f"cd {PROJECT_DIR} && python scraper/keejob_to_mongo.py",
        execution_timeout=timedelta(minutes=30),
    )

    scrape_arbeitnow = BashOperator(
        task_id="scrape_arbeitnow",
        bash_command=f"cd {PROJECT_DIR} && python scraper/arbeitnow_to_mongo.py",
        execution_timeout=timedelta(minutes=15),
    )

    scrape_remotive = BashOperator(
        task_id="scrape_remotive",
        bash_command=f"cd {PROJECT_DIR} && python scraper/remotive_to_mongo.py",
        execution_timeout=timedelta(minutes=5),
    )

    # ============================================================
    # TÂCHE ETL (après tous les scrapings)
    # ============================================================
    run_etl = BashOperator(
        task_id="run_etl",
        bash_command=f"cd {PROJECT_DIR} && python etl/jobs_etl.py",
        execution_timeout=timedelta(minutes=60),
    )

    # ============================================================
    # TÂCHE FINALE
    # ============================================================
    done = BashOperator(
        task_id="done",
        bash_command="echo 'Pipeline terminé avec succès !'",
    )

    # ============================================================
    # DÉPENDANCES
    # ============================================================
    # check_env → [scraping en parallèle] → ETL → done
    check_env >> [scrape_keejob, scrape_arbeitnow, scrape_remotive] >> run_etl >> done