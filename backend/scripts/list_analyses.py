import sqlite3
import json
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / 'metadata.db'
if not DB.exists():
    print('metadata.db not found at', DB)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute('SELECT id, dataset_id, created_at, metrics_json, artifacts_json FROM analyses')
rows = cur.fetchall()
if not rows:
    print('No analyses found in the database')
else:
    for r in rows:
        aid, did, created, metrics_json, artifacts_json = r
        print('ANALYSIS_ID:', aid)
        print(' DATASET_ID:', did)
        print(' CREATED_AT:', created)
        try:
            metrics = json.loads(metrics_json) if metrics_json else None
        except Exception:
            metrics = metrics_json
        try:
            artifacts = json.loads(artifacts_json) if artifacts_json else None
        except Exception:
            artifacts = artifacts_json
        print(' METRICS_KEYS:', list(metrics.keys()) if isinstance(metrics, dict) else metrics)
        print(' ARTIFACTS_KEYS:', list(artifacts.keys()) if isinstance(artifacts, dict) else artifacts)
        print('---')

conn.close()
