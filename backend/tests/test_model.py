import unittest
import pandas as pd
import numpy as np
from app.model import train_logistic, predict_from_model
import tempfile
import os


class TestModel(unittest.TestCase):
    
    def setUp(self):
        """Set up test data before each test"""
        # Create a simple test dataset
        np.random.seed(42)
        self.test_df = pd.DataFrame({
            'Age': np.random.randint(20, 65, 100),
            'MonthlyIncome': np.random.randint(1000, 10000, 100),
            'YearsAtCompany': np.random.randint(0, 40, 100),
            'Department': np.random.choice(['Sales', 'HR', 'IT'], 100),
            'OverTime': np.random.choice(['Yes', 'No'], 100),
            'Attrition': np.random.choice(['Yes', 'No'], 100)
        })
    
    def test_train_logistic_success(self):
        """Test successful model training"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        # Verify metrics are returned
        self.assertIsNotNone(metrics)
        self.assertIsNotNone(artifacts)
        
        # Check for expected metrics
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1', metrics)
        
        # Verify metrics are in valid range
        self.assertGreaterEqual(metrics['accuracy'], 0)
        self.assertLessEqual(metrics['accuracy'], 1)
    
    def test_train_logistic_artifacts(self):
        """Test that artifacts are properly created"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        # Check artifacts
        self.assertIn('model_path', artifacts)
        self.assertIn('confusion_matrix', artifacts)
        self.assertIn('numeric_features', artifacts)
        self.assertIn('categorical_features', artifacts)
        
        # Verify model file exists
        self.assertTrue(os.path.exists(artifacts['model_path']))
    
    def test_train_logistic_missing_target(self):
        """Test training with missing target column"""
        with self.assertRaises(ValueError):
            train_logistic(self.test_df, target_column='NonExistent')
    
    def test_train_logistic_binary_target(self):
        """Test training with binary target column"""
        df = self.test_df.copy()
        df['Attrition'] = df['Attrition'].map({'Yes': 1, 'No': 0})
        
        metrics, artifacts = train_logistic(df, target_column='Attrition')
        
        self.assertIsNotNone(metrics)
        self.assertIn('accuracy', metrics)
    
    def test_confusion_matrix_shape(self):
        """Test that confusion matrix has correct shape"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        cm = artifacts['confusion_matrix']
        self.assertEqual(len(cm), 2)  # Binary classification
        self.assertEqual(len(cm[0]), 2)
        self.assertEqual(len(cm[1]), 2)
    
    def test_predict_from_model(self):
        """Test making predictions with trained model"""
        # Train model
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        model_path = artifacts['model_path']
        
        # Create test records
        test_records = [
            {
                'Age': 30,
                'MonthlyIncome': 5000,
                'YearsAtCompany': 5,
                'Department': 'Sales',
                'OverTime': 'Yes'
            },
            {
                'Age': 45,
                'MonthlyIncome': 8000,
                'YearsAtCompany': 10,
                'Department': 'IT',
                'OverTime': 'No'
            }
        ]
        
        # Make predictions
        results = predict_from_model(model_path, test_records)
        
        # Verify results
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn('index', result)
            self.assertIn('predicted_label', result)
            self.assertIn('probability', result)
            self.assertIn(result['predicted_label'], [0, 1])
            self.assertGreaterEqual(result['probability'], 0)
            self.assertLessEqual(result['probability'], 1)


class TestModelEdgeCases(unittest.TestCase):
    
    def test_train_with_missing_values(self):
        """Test training with missing values"""
        df = pd.DataFrame({
            'Age': [25, 30, np.nan, 35],
            'MonthlyIncome': [5000, np.nan, 6000, 7000],
            'Department': ['Sales', 'IT', 'HR', 'Sales'],
            'Attrition': ['Yes', 'No', 'Yes', 'No']
        })
        
        metrics, artifacts = train_logistic(df, target_column='Attrition')
        self.assertIsNotNone(metrics)
    
    def test_train_with_small_dataset(self):
        """Test training with very small dataset"""
        df = pd.DataFrame({
            'Age': [25, 30, 35],
            'Department': ['Sales', 'IT', 'HR'],
            'Attrition': ['Yes', 'No', 'Yes']
        })
        
        metrics, artifacts = train_logistic(df, target_column='Attrition', test_size=0.33)
        self.assertIsNotNone(metrics)


if __name__ == '__main__':
    unittest.main()
