import pytest
from fastapi.testclient import TestClient
import sys
import os

# add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app

# Raise server exceptions during tests so failures surface with tracebacks
client = TestClient(app, raise_server_exceptions=True)

def test_upload_and_analyze():
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ibm_attrition_sample.csv')
    with open(csv_path, 'rb') as f:
        files = {'file': ('ibm_sample.csv', f, 'text/csv')}
        res = client.post('/api/upload', files=files)
        assert res.status_code == 200
        data = res.json()
        assert 'dataset_id' in data
        dataset_id = data['dataset_id']

    # Run analysis
    res2 = client.post(f'/api/analyze?dataset_id={dataset_id}')
    if res2.status_code != 200:
        # show response body to aid debugging
        try:
            print('ANALYZE RESPONSE:', res2.json())
        except Exception:
            print('ANALYZE RESPONSE TEXT:', res2.text)
    assert res2.status_code == 200
    data2 = res2.json()
    assert 'analysis_id' in data2
    assert 'metrics' in data2
