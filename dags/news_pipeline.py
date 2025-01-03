from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import pandas as pd
import sqlite3
import os

# Konfigurasi API News
load_dotenv()  # Memuat file .env
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://newsapi.org/v2/top-headlines"

def fetch_news():
    """Mengambil berita dari News API dan menyimpan sebagai CSV."""
    params = {
        "country": "us",
        "category": "technology",
        "apiKey": API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    
    # Ambil artikel dan simpan ke file
    articles = data.get("articles", [])
    df = pd.DataFrame(articles)
    output_path = f"{os.getenv('AIRFLOW_HOME')}/news_data.csv"
    df.to_csv(output_path, index=False)

def process_news():
    """Membersihkan dan memproses data berita."""
    # Load data dari CSV
    input_path = f"{os.getenv('AIRFLOW_HOME')}/news_data.csv"
    df = pd.read_csv(input_path)
    
    # Mengambil nama sumber dari objek 'source' (yang berupa dictionary)
    df['source_name'] = df['source'].apply(lambda x: eval(x)['name'] if isinstance(x, str) else None)
    
    # Pilih kolom yang diperlukan
    df = df[["source_name", "title", "description", "url", "publishedAt"]]
    df["publishedAt"] = pd.to_datetime(df["publishedAt"])
    
    # Simpan data yang sudah diproses
    output_path = f"{os.getenv('AIRFLOW_HOME')}/processed_news_data.csv"
    df.to_csv(output_path, index=False)

def store_news():
    """Menyimpan data ke SQLite database."""
    # Load data yang sudah diproses
    input_path = f"{os.getenv('AIRFLOW_HOME')}/processed_news_data.csv"
    df = pd.read_csv(input_path)
    
    # Simpan ke database SQLite
    db_path = f"{os.getenv('AIRFLOW_HOME')}/news.db"
    conn = sqlite3.connect(db_path)
    df.to_sql("news", conn, if_exists="replace", index=False)
    conn.close()

# Konfigurasi default untuk DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Definisi DAG
with DAG(
    "news_pipeline",
    default_args=default_args,
    description="Pipeline sederhana untuk News API",
    schedule_interval=timedelta(hours=1),
    start_date=datetime(2024, 12, 22),
    catchup=False,
) as dag:
    
    fetch_task = PythonOperator(
        task_id="fetch_news",
        python_callable=fetch_news,
    )
    
    process_task = PythonOperator(
        task_id="process_news",
        python_callable=process_news,
    )
    
    store_task = PythonOperator(
        task_id="store_news",
        python_callable=store_news,
    )
    
    # Menentukan urutan tugas
    fetch_task >> process_task >> store_task