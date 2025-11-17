import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "metadata.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS datasets (
        id TEXT PRIMARY KEY,
        filename TEXT,
        uploaded_at TEXT,
        columns_json TEXT,
        sample_rows_json TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS analyses (
        id TEXT PRIMARY KEY,
        dataset_id TEXT,
        model_type TEXT,
        metrics_json TEXT,
        artifacts_json TEXT,
        created_at TEXT
    )
    ''')
    conn.commit()
    conn.close()

def insert_dataset(id, filename, uploaded_at, columns, samples):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO datasets (id, filename, uploaded_at, columns_json, sample_rows_json) VALUES (?, ?, ?, ?, ?)',
        (id, filename, uploaded_at, json.dumps(columns), json.dumps(samples))
    )
    conn.commit()
    conn.close()

def insert_analysis(id, dataset_id, model_type, metrics, artifacts, created_at):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO analyses (id, dataset_id, model_type, metrics_json, artifacts_json, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (id, dataset_id, model_type, json.dumps(metrics), json.dumps(artifacts), created_at)
    )
    conn.commit()
    conn.close()

def list_analyses():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM analyses')
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_analysis(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM analyses WHERE id = ?', (id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
