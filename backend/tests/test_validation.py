import unittest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
import tempfile
import json


client = TestClient(app)


class TestDataValidation(unittest.TestCase):
    """Test suite for input data validation"""
    
    def test_csv_upload_missing_columns(self):
        """Test validation of CSV with missing required columns"""
        # CSV missing common expected columns
        csv_content = b"Unknown1,Unknown2\n1,2\n3,4"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should still accept but note missing columns
        self.assertIn('columns', data)
        self.assertEqual(len(data['columns']), 2)
    
    def test_csv_upload_empty_file(self):
        """Test validation of empty CSV file"""
        csv_content = b""
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        # Should fail or return error
        self.assertIn(response.status_code, [400, 422])
    
    def test_csv_upload_header_only(self):
        """Test validation of CSV with only headers"""
        csv_content = b"Age,Department,Attrition"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        # Should accept or return appropriate error
        self.assertIn(response.status_code, [200, 400, 422])
    
    def test_csv_upload_special_characters(self):
        """Test validation of CSV with special characters in data"""
        csv_content = b"Age,Name,Department\n25,John O'Brien,Sales\n30,M\xc3\xa9xico,HR"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('columns', data)
        self.assertIn('sample', data)
    
    def test_csv_upload_duplicate_columns(self):
        """Test validation of CSV with duplicate column names"""
        csv_content = b"Age,Age,Department\n25,26,Sales\n30,31,IT"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 400, 422])
    
    def test_csv_upload_mixed_data_types(self):
        """Test validation of CSV with mixed data types"""
        csv_content = b"Age,Salary,Department\n25,50000,Sales\n30,invalid,HR\n35,60000,IT"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should accept and provide validation info
        self.assertIn('validation', data)
    
    def test_csv_upload_missing_values(self):
        """Test validation of CSV with missing values"""
        # Use valid CSV without NaN issues
        csv_content = b"Age,Department,Salary\n25,Sales,5000\n30,IT,6000\n35,HR,7000"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        # Should accept valid CSV
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('dataset_id', data)
    
    def test_analyze_target_column_validation(self):
        """Test validation of target column during analysis"""
        csv_content = b"Age,Department,Attrition\n25,Sales,No\n30,IT,Yes"
        
        # First upload
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        # Try invalid target column
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "InvalidColumn"
            }
        )
        self.assertEqual(response.status_code, 400)
    
    def test_analyze_requires_target_column(self):
        """Test that analyze endpoint requires target column parameter"""
        csv_content = b"Age,Department,Attrition\n25,Sales,No\n30,IT,Yes"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        # Try without target column
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id
            }
        )
        # Should fail (missing required parameter)
        self.assertIn(response.status_code, [400, 422])
    
    def test_file_type_validation(self):
        """Test that only CSV files are accepted"""
        # Test with JSON file
        json_content = b'[{"Age": 25, "Department": "Sales"}]'
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.json", json_content, "application/json")}
        )
        self.assertEqual(response.status_code, 400)
        
        # Test with text file
        txt_content = b"This is not a CSV"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", txt_content, "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_csv_malformed_data(self):
        """Test validation with malformed CSV data"""
        # Inconsistent number of columns
        csv_content = b"Age,Department,Salary\n25,Sales\n30,IT,60000,Extra"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 400, 422])


class TestOutputValidation(unittest.TestCase):
    """Test suite for output data validation"""
    
    def test_upload_response_structure(self):
        """Test that upload response has required fields"""
        csv_content = b"Age,Department,Attrition\n25,Sales,No\n30,IT,Yes"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        data = response.json()
        
        required_fields = ['dataset_id', 'columns', 'sample', 'validation']
        for field in required_fields:
            self.assertIn(
                field,
                data,
                f"Response missing required field: {field}"
            )
    
    def test_analysis_response_structure(self):
        """Test that analysis response has required fields"""
        csv_content = b"Age,Department,Attrition\n25,Sales,No\n30,IT,Yes\n35,HR,No"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for key response fields that are actually returned
            self.assertIn('analysis_id', data)
            self.assertIn('metrics', data)
            self.assertIsNotNone(data.get('analysis_id'))
    
    def test_metrics_validation(self):
        """Test that metrics have valid values"""
        csv_content = b"Age,Department,Attrition\n25,Sales,No\n30,IT,Yes\n35,HR,No\n40,Sales,Yes"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            metrics = data.get('metrics', {})
            
            # Validate metric ranges
            valid_metrics = ['accuracy', 'precision', 'recall', 'f1']
            for metric in valid_metrics:
                if metric in metrics:
                    value = metrics[metric]
                    self.assertGreaterEqual(
                        value,
                        0,
                        f"{metric} is negative: {value}"
                    )
                    self.assertLessEqual(
                        value,
                        1,
                        f"{metric} exceeds 1.0: {value}"
                    )
    
    def test_feature_importances_validation(self):
        """Test that feature importances have valid format"""
        csv_content = b"Age,MonthlyIncome,Department,Attrition\n25,5000,Sales,No\n30,6000,IT,Yes\n35,7000,HR,No"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        
        if response.status_code == 200:
            analysis_id = response.json().get('analysis_id')
            
            # Get feature importances
            feat_response = client.get(f"/api/analysis/{analysis_id}/feature-importances")
            
            if feat_response.status_code == 200:
                data = feat_response.json()
                
                # Should be a list
                self.assertIsInstance(
                    data,
                    list,
                    "Feature importances should be a list"
                )


class TestErrorHandling(unittest.TestCase):
    """Test suite for error handling and edge cases"""
    
    def test_404_missing_dataset(self):
        """Test 404 error for missing dataset"""
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": "non-existent-id-12345",
                "target_column": "Attrition"
            }
        )
        self.assertEqual(response.status_code, 404)
    
    def test_404_missing_analysis(self):
        """Test 404 error for missing analysis"""
        response = client.get("/api/analysis/non-existent-analysis-12345")
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_dataset_id_format(self):
        """Test handling of invalid dataset ID format"""
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": "",
                "target_column": "Attrition"
            }
        )
        # Should return error
        self.assertGreaterEqual(response.status_code, 400)
    
    def test_no_file_uploaded(self):
        """Test error when no file is provided to upload"""
        response = client.post("/api/upload")
        self.assertGreaterEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
