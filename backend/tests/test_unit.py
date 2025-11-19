import unittest
import pandas as pd
import numpy as np
from app.model import train_logistic, predict_from_model
import tempfile
import os
import uuid
from datetime import datetime


class TestDatabaseUnit(unittest.TestCase):
    """Unit tests for database functions"""
    
    def test_init_db_creates_tables(self):
        """Test database initialization creates required tables"""
        from app.db import init_db
        
        # Initialize database
        init_db()
        
        from app.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check for datasets table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='datasets'"
        )
        self.assertIsNotNone(cursor.fetchone())
        
        # Check for analyses table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='analyses'"
        )
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_insert_and_retrieve_dataset(self):
        """Test inserting and retrieving dataset"""
        from app.db import init_db, insert_dataset, get_connection
        
        init_db()
        
        dataset_id = str(uuid.uuid4())
        insert_dataset(
            dataset_id,
            "test.csv",
            datetime.now().isoformat(),
            ["col1", "col2"],
            [{"col1": "val1", "col2": "val2"}]
        )
        
        # Verify it was inserted
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        conn.close()
    
    def test_insert_and_retrieve_analysis(self):
        """Test inserting and retrieving analysis"""
        from app.db import init_db, insert_dataset, insert_analysis, get_connection
        
        init_db()
        
        dataset_id = str(uuid.uuid4())
        analysis_id = str(uuid.uuid4())
        
        insert_dataset(
            dataset_id,
            "test.csv",
            datetime.now().isoformat(),
            ["col1"],
            [{"col1": "val"}]
        )
        
        insert_analysis(
            analysis_id,
            dataset_id,
            "logistic",
            {"accuracy": 0.85},
            {"model_path": "/path"},
            datetime.now().isoformat()
        )
        
        # Verify it was inserted
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        conn.close()


class TestModelUnit(unittest.TestCase):
    """Unit tests for model functions"""
    
    def setUp(self):
        """Create test data"""
        np.random.seed(42)
        self.test_df = pd.DataFrame({
            'Age': np.random.randint(20, 65, 100),
            'Salary': np.random.randint(1000, 10000, 100),
            'Department': np.random.choice(['Sales', 'IT', 'HR'], 100),
            'Attrition': np.random.choice(['Yes', 'No'], 100)
        })
    
    def test_train_logistic_returns_metrics(self):
        """Test model training returns metrics"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        # Verify all expected metrics are present
        expected_metrics = ['accuracy', 'precision', 'recall', 'f1']
        for metric in expected_metrics:
            self.assertIn(metric, metrics)
            self.assertIsInstance(metrics[metric], float)
    
    def test_train_logistic_returns_artifacts(self):
        """Test model training returns artifacts"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        # Verify artifacts structure
        self.assertIn('model_path', artifacts)
        self.assertIn('confusion_matrix', artifacts)
        self.assertIn('numeric_features', artifacts)
        self.assertIn('categorical_features', artifacts)
    
    def test_train_logistic_model_file_exists(self):
        """Test that model file is created"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        model_path = artifacts['model_path']
        self.assertTrue(os.path.exists(model_path))
    
    def test_confusion_matrix_correct_shape(self):
        """Test confusion matrix has correct shape"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        cm = artifacts['confusion_matrix']
        self.assertEqual(len(cm), 2)  # Binary classification
        self.assertEqual(len(cm[0]), 2)
        self.assertEqual(len(cm[1]), 2)
    
    def test_predict_from_model_returns_predictions(self):
        """Test predict function returns predictions"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        model_path = artifacts['model_path']
        
        test_records = [
            {'Age': 30, 'Salary': 5000, 'Department': 'Sales'},
            {'Age': 40, 'Salary': 7000, 'Department': 'IT'}
        ]
        
        predictions = predict_from_model(model_path, test_records)
        
        self.assertIsNotNone(predictions)
        self.assertIsInstance(predictions, list)
        self.assertEqual(len(predictions), 2)
    
    def test_metrics_in_valid_range(self):
        """Test metrics are within valid ranges"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        for metric_name in ['accuracy', 'precision', 'recall', 'f1']:
            value = metrics[metric_name]
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 1)


class TestSchemas(unittest.TestCase):
    """Unit tests for Pydantic response schemas"""
    
    def test_upload_response_validation(self):
        """Test UploadResponse schema validates correctly"""
        from app.schemas import UploadResponse
        
        valid_data = {
            'dataset_id': 'test-id',
            'columns': ['col1', 'col2'],
            'sample': [{'col1': 'val1', 'col2': 'val2'}]
        }
        
        response = UploadResponse(**valid_data)
        self.assertEqual(response.dataset_id, 'test-id')
        self.assertEqual(len(response.columns), 2)
    
    def test_analyze_response_validation(self):
        """Test AnalyzeResponse schema validates correctly"""
        from app.schemas import AnalyzeResponse
        
        valid_data = {
            'analysis_id': 'test-id',
            'metrics': {'accuracy': 0.85},
            'artifacts': {'model_path': '/path/to/model'}
        }
        
        response = AnalyzeResponse(**valid_data)
        self.assertEqual(response.analysis_id, 'test-id')
        self.assertIn('accuracy', response.metrics)


if __name__ == '__main__':
    unittest.main()
