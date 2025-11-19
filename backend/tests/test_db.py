import unittest
import json
import tempfile
import os
from pathlib import Path
from app.db import (
    init_db, insert_dataset, insert_analysis, list_analyses, 
    get_analysis, get_connection
)


class TestDatabase(unittest.TestCase):
    
    def setUp(self):
        """Set up test database before each test"""
        self.temp_dir = tempfile.mkdtemp()
        # Override DB_PATH for testing
        import app.db as db_module
        self.original_db_path = db_module.DB_PATH
        db_module.DB_PATH = Path(self.temp_dir) / "test.db"
        init_db()
    
    def tearDown(self):
        """Clean up test database after each test"""
        import app.db as db_module
        db_module.DB_PATH = self.original_db_path
        if os.path.exists(Path(self.temp_dir) / "test.db"):
            os.remove(Path(self.temp_dir) / "test.db")
        os.rmdir(self.temp_dir)
    
    def test_init_db(self):
        """Test database initialization"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        conn.close()
        
        self.assertIn('datasets', tables)
        self.assertIn('analyses', tables)
    
    def test_insert_dataset(self):
        """Test inserting a dataset"""
        dataset_id = "test-dataset-1"
        filename = "test.csv"
        uploaded_at = "2025-11-18T10:00:00"
        columns = ["Age", "Department", "Attrition"]
        samples = [{"Age": 25, "Department": "Sales", "Attrition": "No"}]
        
        insert_dataset(dataset_id, filename, uploaded_at, columns, samples)
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        row = cur.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row['filename'], filename)
        self.assertEqual(json.loads(row['columns_json']), columns)
    
    def test_insert_analysis(self):
        """Test inserting an analysis"""
        analysis_id = "test-analysis-1"
        dataset_id = "test-dataset-1"
        model_type = "logistic_regression"
        metrics = {"accuracy": 0.85, "precision": 0.90}
        artifacts = {"model_path": "/tmp/model.pkl", "confusion_matrix": [[10, 2], [1, 15]]}
        created_at = "2025-11-18T10:05:00"
        
        insert_analysis(analysis_id, dataset_id, model_type, metrics, artifacts, created_at)
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
        row = cur.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row['dataset_id'], dataset_id)
        self.assertEqual(row['model_type'], model_type)
    
    def test_list_analyses(self):
        """Test listing all analyses"""
        # Insert multiple analyses
        for i in range(3):
            analysis_id = f"test-analysis-{i}"
            dataset_id = f"test-dataset-{i}"
            insert_analysis(analysis_id, dataset_id, "logistic_regression", 
                          {"accuracy": 0.85}, {"model_path": "/tmp/model.pkl"}, 
                          "2025-11-18T10:05:00")
        
        analyses = list_analyses()
        self.assertGreaterEqual(len(analyses), 3)
    
    def test_get_analysis(self):
        """Test retrieving a specific analysis"""
        analysis_id = "test-analysis-retrieve"
        dataset_id = "test-dataset-retrieve"
        metrics = {"accuracy": 0.92, "precision": 0.88}
        artifacts = {"model_path": "/tmp/model.pkl"}
        
        insert_analysis(analysis_id, dataset_id, "logistic_regression", 
                       metrics, artifacts, "2025-11-18T10:05:00")
        
        result = get_analysis(analysis_id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], analysis_id)
        self.assertEqual(result['dataset_id'], dataset_id)
        self.assertEqual(json.loads(result['metrics_json']), metrics)
    
    def test_get_analysis_not_found(self):
        """Test retrieving non-existent analysis"""
        result = get_analysis("non-existent-id")
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
