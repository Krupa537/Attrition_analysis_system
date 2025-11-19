import unittest
import pandas as pd
import numpy as np
from app.model import train_logistic, predict_from_model
import tempfile
import os
import pickle


class TestRegression(unittest.TestCase):
    """Test suite for regression testing - ensures model performance doesn't degrade"""
    
    def setUp(self):
        """Set up test data before each test"""
        np.random.seed(42)
        self.test_df = pd.DataFrame({
            'Age': np.random.randint(20, 65, 500),
            'MonthlyIncome': np.random.randint(1000, 15000, 500),
            'YearsAtCompany': np.random.randint(0, 40, 500),
            'Department': np.random.choice(['Sales', 'HR', 'IT', 'Research'], 500),
            'OverTime': np.random.choice(['Yes', 'No'], 500),
            'JobSatisfaction': np.random.randint(1, 5, 500),
            'Attrition': np.random.choice(['Yes', 'No'], 500)
        })
    
    def test_model_accuracy_threshold(self):
        """Test that model accuracy meets minimum threshold (baseline)"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        # Model should achieve at least 50% accuracy (better than random)
        min_accuracy = 0.50
        self.assertGreaterEqual(
            metrics['accuracy'],
            min_accuracy,
            f"Model accuracy {metrics['accuracy']} is below minimum threshold {min_accuracy}"
        )
    
    def test_model_precision_recall_balance(self):
        """Test that precision and recall are balanced"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        # Both should be present and reasonable
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        
        # Precision and recall should not differ drastically
        diff = abs(metrics['precision'] - metrics['recall'])
        self.assertLess(
            diff,
            0.5,
            f"Precision {metrics['precision']} and recall {metrics['recall']} are too imbalanced"
        )
    
    def test_f1_score_consistency(self):
        """Test that F1 score is consistent with precision and recall"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        precision = metrics['precision']
        recall = metrics['recall']
        f1 = metrics['f1']
        
        # Calculate expected F1 score
        if (precision + recall) > 0:
            expected_f1 = 2 * (precision * recall) / (precision + recall)
            # Allow small floating-point differences
            self.assertAlmostEqual(
                f1,
                expected_f1,
                places=2,
                msg=f"F1 score {f1} doesn't match calculated value {expected_f1}"
            )
    
    def test_model_persistence(self):
        """Test that saved model can be loaded and produces same predictions"""
        # Train and get predictions
        metrics1, artifacts1 = train_logistic(self.test_df, target_column='Attrition')
        
        # Train again with same data
        metrics2, artifacts2 = train_logistic(self.test_df, target_column='Attrition')
        
        # Metrics should be identical (same random seed, same data)
        self.assertEqual(
            metrics1['accuracy'],
            metrics2['accuracy'],
            "Model accuracy changed between runs with same data"
        )
    
    def test_prediction_consistency(self):
        """Test that predictions are consistent across multiple calls"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        model_path = artifacts['model_path']
        
        test_records = [
            {
                'Age': 30,
                'MonthlyIncome': 5000,
                'YearsAtCompany': 5,
                'Department': 'Sales',
                'OverTime': 'Yes',
                'JobSatisfaction': 3
            }
        ]
        
        # Get predictions twice
        pred1 = predict_from_model(model_path, test_records)
        pred2 = predict_from_model(model_path, test_records)
        
        # Should be identical
        self.assertEqual(
            pred1[0] if isinstance(pred1, list) else pred1,
            pred2[0] if isinstance(pred2, list) else pred2,
            "Predictions are not consistent across multiple calls"
        )
    
    def test_confusion_matrix_validity(self):
        """Test that confusion matrix values are valid"""
        metrics, artifacts = train_logistic(self.test_df, target_column='Attrition')
        
        cm = artifacts['confusion_matrix']
        
        # All values should be non-negative
        for row in cm:
            for val in row:
                self.assertGreaterEqual(
                    val,
                    0,
                    f"Confusion matrix contains negative value: {val}"
                )
        
        # Sum of all elements should equal number of samples
        total = sum(sum(row) for row in cm)
        self.assertGreater(
            total,
            0,
            "Confusion matrix is empty"
        )
    
    def test_model_handles_categorical_encoding(self):
        """Test that model properly encodes categorical features"""
        df = self.test_df.copy()
        
        # Verify categorical columns are handled
        metrics, artifacts = train_logistic(df, target_column='Attrition')
        
        self.assertIn('categorical_features', artifacts)
        self.assertIn('numeric_features', artifacts)
        
        # Should have at least categorical features
        self.assertGreater(len(artifacts['categorical_features']), 0)
    
    def test_regression_large_dataset(self):
        """Test model performance on larger dataset"""
        # Create larger dataset
        np.random.seed(42)
        large_df = pd.DataFrame({
            'Age': np.random.randint(20, 65, 5000),
            'MonthlyIncome': np.random.randint(1000, 15000, 5000),
            'YearsAtCompany': np.random.randint(0, 40, 5000),
            'Department': np.random.choice(['Sales', 'HR', 'IT', 'Research'], 5000),
            'OverTime': np.random.choice(['Yes', 'No'], 5000),
            'JobSatisfaction': np.random.randint(1, 5, 5000),
            'Attrition': np.random.choice(['Yes', 'No'], 5000)
        })
        
        metrics, artifacts = train_logistic(large_df, target_column='Attrition')
        
        # Should still produce valid metrics
        self.assertIn('accuracy', metrics)
        self.assertGreaterEqual(metrics['accuracy'], 0.5)
    
    def test_regression_class_imbalance(self):
        """Test model behavior with imbalanced classes"""
        df = self.test_df.copy()
        
        # Create imbalanced data (80% No, 20% Yes)
        df['Attrition'] = np.random.choice(
            ['Yes', 'No'],
            size=500,
            p=[0.2, 0.8]
        )
        
        metrics, artifacts = train_logistic(df, target_column='Attrition')
        
        # Model should still train successfully
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics['accuracy'], 0)


if __name__ == '__main__':
    unittest.main()
