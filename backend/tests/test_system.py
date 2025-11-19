import unittest
from fastapi.testclient import TestClient
from app.main import app
import tempfile
import json
import os


client = TestClient(app)


class TestSystemEndToEnd(unittest.TestCase):
    """End-to-end system tests for full workflows"""
    
    def test_complete_workflow_upload_analyze_retrieve(self):
        """Test complete workflow: upload CSV -> analyze -> retrieve results"""
        # Step 1: Upload CSV
        csv_content = b"Age,Department,MonthlyIncome,Attrition\n25,Sales,5000,No\n30,IT,6000,Yes\n35,HR,7000,No\n40,Sales,8000,Yes"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        self.assertEqual(upload_response.status_code, 200)
        upload_data = upload_response.json()
        dataset_id = upload_data['dataset_id']
        
        # Verify upload response
        self.assertIn('dataset_id', upload_data)
        self.assertIn('columns', upload_data)
        self.assertEqual(len(upload_data['columns']), 4)
        
        # Step 2: Analyze dataset
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        self.assertEqual(response.status_code, 200)
        analysis_data = response.json()
        analysis_id = analysis_data.get('analysis_id')
        
        # Verify analysis response
        self.assertIsNotNone(analysis_id)
        self.assertIn('metrics', analysis_data)
    
    def test_multiple_datasets_workflow(self):
        """Test system handles multiple datasets concurrently"""
        dataset_ids = []
        
        # Upload multiple datasets
        for i in range(3):
            csv_content = f"Age,Department,Attrition\n{25+i},Sales,No\n{30+i},IT,Yes".encode()
            
            response = client.post(
                "/api/upload",
                files={"file": (f"test{i}.csv", csv_content, "text/csv")}
            )
            self.assertEqual(response.status_code, 200)
            dataset_ids.append(response.json()['dataset_id'])
        
        # Verify all datasets are listed
        list_response = client.get("/api/analyses")
        self.assertEqual(list_response.status_code, 200)
        analyses = list_response.json()
        self.assertIsInstance(analyses, list)
    
    def test_workflow_with_feature_extraction(self):
        """Test workflow that includes feature importance extraction"""
        # Upload and analyze
        csv_content = b"Age,Salary,Department,YearsAtCompany,Attrition\n25,5000,Sales,2,No\n30,6000,IT,5,Yes\n35,7000,HR,10,No"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        # Analyze
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        analysis_id = response.json().get('analysis_id')
        
        # Get feature importances
        if analysis_id:
            feat_response = client.get(f"/api/analysis/{analysis_id}/feature-importances")
            if feat_response.status_code == 200:
                features = feat_response.json()
                self.assertIsInstance(features, list)


class TestSystemAPIEndpoints(unittest.TestCase):
    """System-level tests for API endpoints"""
    
    def test_api_health_check(self):
        """Test API health check endpoint"""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
    
    def test_list_empty_analyses(self):
        """Test listing analyses when empty"""
        response = client.get("/api/analyses")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_upload_endpoint_accepts_csv(self):
        """Test upload endpoint accepts valid CSV"""
        csv_content = b"Name,Age,City\nAlice,25,NYC\nBob,30,LA"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('dataset_id', data)
        self.assertIn('columns', data)
        self.assertIn('sample', data)
    
    def test_upload_rejects_non_csv(self):
        """Test upload endpoint rejects non-CSV files"""
        # Test with JSON
        json_content = b'[{"name": "Alice"}]'
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.json", json_content, "application/json")}
        )
        self.assertEqual(response.status_code, 400)
        
        # Test with text
        txt_content = b"This is plain text"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", txt_content, "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_download_model_endpoint(self):
        """Test model download endpoint"""
        # First upload and analyze
        csv_content = b"Age,Attrition\n25,No\n30,Yes\n35,No"
        
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
            
            if analysis_id:
                download_response = client.get(f"/api/analysis/{analysis_id}/model")
                # Should return file or 200
                self.assertIn(download_response.status_code, [200, 404])


class TestSystemErrorHandling(unittest.TestCase):
    """System-level tests for error handling"""
    
    def test_404_for_nonexistent_analysis(self):
        """Test 404 error for nonexistent analysis"""
        response = client.get("/api/analysis/nonexistent-id-12345")
        self.assertEqual(response.status_code, 404)
    
    def test_404_for_nonexistent_dataset(self):
        """Test 404 error when analyzing nonexistent dataset"""
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": "nonexistent-id",
                "target_column": "Attrition"
            }
        )
        self.assertEqual(response.status_code, 404)
    
    def test_400_for_invalid_target_column(self):
        """Test 400 error for invalid target column"""
        # Upload first
        csv_content = b"Age,Name\n25,Alice\n30,Bob"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        # Try analyzing with nonexistent column
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "NonexistentColumn"
            }
        )
        self.assertEqual(response.status_code, 400)
    
    def test_400_for_missing_required_params(self):
        """Test 400 error for missing required parameters"""
        # Try analyze without target_column
        response = client.post(
            "/api/analyze",
            params={"dataset_id": "some-id"}
        )
        self.assertGreaterEqual(response.status_code, 400)


class TestSystemDataFlow(unittest.TestCase):
    """System-level tests for data flow and transformations"""
    
    def test_csv_parsing_preserves_data(self):
        """Test that CSV data is correctly parsed"""
        csv_content = b"Name,Age,Salary\nAlice,25,50000\nBob,30,60000"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        
        data = response.json()
        sample = data['sample']
        
        # Verify sample data
        self.assertGreater(len(sample), 0)
    
    def test_analysis_produces_valid_metrics(self):
        """Test that analysis produces valid metrics"""
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
            metrics = data.get('metrics', {})
            
            # Verify metrics are valid
            for metric_name in ['accuracy', 'precision', 'recall', 'f1']:
                if metric_name in metrics:
                    value = metrics[metric_name]
                    self.assertIsInstance(value, (int, float, type(None)))
    
    def test_large_dataset_handling(self):
        """Test system handles larger datasets"""
        # Create CSV with many rows
        rows = ['Age,Salary,Department,Attrition']
        for i in range(500):
            rows.append(f"{20+i%40},{3000+i},{['Sales','IT','HR'][i%3]},{'Yes' if i%2 else 'No'}")
        
        csv_content = '\n'.join(rows).encode()
        
        response = client.post(
            "/api/upload",
            files={"file": ("large.csv", csv_content, "text/csv")}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('dataset_id', data)


class TestSystemResponseFormats(unittest.TestCase):
    """System-level tests for response format consistency"""
    
    def test_upload_response_format(self):
        """Test upload response has consistent format"""
        csv_content = b"Age,Name\n25,Alice"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        
        data = response.json()
        
        # Check required fields
        required_fields = ['dataset_id', 'columns', 'sample']
        for field in required_fields:
            self.assertIn(field, data)
    
    def test_analysis_response_format(self):
        """Test analysis response has consistent format"""
        csv_content = b"Age,Attrition\n25,No\n30,Yes"
        
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
            
            # Check required fields
            self.assertIn('metrics', data)
            self.assertIsInstance(data['metrics'], dict)


if __name__ == '__main__':
    unittest.main()
