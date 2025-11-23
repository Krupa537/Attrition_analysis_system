import unittest
from fastapi.testclient import TestClient
from app.main import app
import json
import tempfile
from pathlib import Path


client = TestClient(app)


class TestAPIEndpoints(unittest.TestCase):
    
    def test_root_endpoint(self):
        """Test root endpoint returns status"""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
    
    def test_list_analyses_endpoint(self):
        """Test listing analyses endpoint"""
        response = client.get("/api/analyses")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_upload_csv_invalid_format(self):
        """Test upload endpoint with invalid file format"""
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            tmp.write(b"This is not a CSV")
            tmp.seek(0)
            
            response = client.post(
                "/api/upload",
                files={"file": ("test.txt", tmp, "text/plain")}
            )
            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertIn("Only CSV files are accepted", data['detail'])
    
    def test_upload_csv_valid(self):
        """Test upload endpoint with valid CSV"""
        csv_content = b"Age,Department,Attrition\n25,Sales,No\n30,IT,Yes"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('dataset_id', data)
        self.assertIn('columns', data)
        self.assertIn('sample', data)
        self.assertIn('validation', data)
        
        # Verify columns
        self.assertIn('Age', data['columns'])
        self.assertIn('Department', data['columns'])
        self.assertIn('Attrition', data['columns'])
    
    def test_analyze_missing_dataset(self):
        """Test analyze endpoint with non-existent dataset"""
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": "non-existent-id",
                "target_column": "Attrition"
            }
        )
        self.assertEqual(response.status_code, 404)
    
    def test_analyze_missing_target_column(self):
        """Test analyze endpoint with invalid target column"""
        # First upload a dataset
        csv_content = b"Age,Department\n25,Sales\n30,IT"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        # Try to analyze with non-existent target column
        response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "NonExistent"
            }
        )
        self.assertEqual(response.status_code, 400)


class TestAPIErrors(unittest.TestCase):
    
    def test_analysis_not_found(self):
        """Test retrieving non-existent analysis"""
        response = client.get("/api/analysis/non-existent-id")
        self.assertEqual(response.status_code, 404)
    
    def test_download_model_not_found(self):
        """Test downloading model for non-existent analysis"""
        response = client.get("/api/download/model/non-existent-id")
        self.assertEqual(response.status_code, 404)
    
    def test_download_predictions_not_found(self):
        """Test downloading predictions for non-existent analysis"""
        response = client.get("/api/download/predictions/non-existent-id")
        self.assertEqual(response.status_code, 404)
    
    def test_feature_importances_not_found(self):
        """Test getting feature importances for non-existent analysis"""
        response = client.get("/api/analysis/non-existent-id/feature_importances")
        self.assertEqual(response.status_code, 404)


class TestAPIIntegration(unittest.TestCase):
    
    def test_full_workflow(self):
        """Test complete workflow: upload -> analyze -> retrieve"""
        # Step 1: Upload dataset
        csv_content = b"Age,Department,Attrition,OverTime\n25,Sales,No,Yes\n30,IT,Yes,No\n35,HR,No,No\n40,Sales,Yes,Yes\n28,IT,No,No"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        self.assertEqual(upload_response.status_code, 200)
        dataset_id = upload_response.json()['dataset_id']
        
        # Step 2: Analyze dataset
        analysis_response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        self.assertEqual(analysis_response.status_code, 200)
        analysis_data = analysis_response.json()
        analysis_id = analysis_data['analysis_id']
        
        self.assertIn('metrics', analysis_data)
        self.assertIn('artifacts', analysis_data)
        
        # Step 3: Retrieve analysis
        retrieve_response = client.get(f"/api/analysis/{analysis_id}")
        self.assertEqual(retrieve_response.status_code, 200)
        
        retrieved_data = retrieve_response.json()
        self.assertEqual(retrieved_data['id'], analysis_id)
        self.assertEqual(retrieved_data['dataset_id'], dataset_id)
    
    def test_download_model_workflow(self):
        """Test downloading trained model"""
        # Upload and analyze
        csv_content = b"Age,Department,Attrition,OverTime\n25,Sales,No,Yes\n30,IT,Yes,No\n35,HR,No,No\n40,Sales,Yes,Yes\n28,IT,No,No"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        analysis_response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        analysis_id = analysis_response.json()['analysis_id']
        
        # Download model
        model_response = client.get(f"/api/download/model/{analysis_id}")
        self.assertEqual(model_response.status_code, 200)
        self.assertEqual(model_response.headers['content-type'], 'application/octet-stream')
    
    def test_download_predictions_workflow(self):
        """Test downloading predictions CSV"""
        # Upload and analyze
        csv_content = b"Age,Department,Attrition,OverTime\n25,Sales,No,Yes\n30,IT,Yes,No\n35,HR,No,No\n40,Sales,Yes,Yes\n28,IT,No,No"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        analysis_response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        analysis_id = analysis_response.json()['analysis_id']
        
        # Download predictions
        predictions_response = client.get(f"/api/download/predictions/{analysis_id}")
        self.assertEqual(predictions_response.status_code, 200)
        self.assertEqual(predictions_response.headers['content-type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', predictions_response.headers['content-disposition'])
    
    def test_download_pdf_workflow(self):
        """Test downloading analysis PDF report"""
        # Upload and analyze
        csv_content = b"Age,Department,Attrition,OverTime\n25,Sales,No,Yes\n30,IT,Yes,No\n35,HR,No,No\n40,Sales,Yes,Yes\n28,IT,No,No"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        analysis_response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        analysis_id = analysis_response.json()['analysis_id']
        
        # Download PDF
        pdf_response = client.get(f"/api/download/analysis/{analysis_id}/pdf")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response.headers['content-type'], 'application/pdf')
    

    def test_at_risk_employees_endpoint(self):
        """Test at-risk employees endpoint"""
        # Upload and analyze
        csv_content = b"Age,Department,Attrition,OverTime\n25,Sales,No,Yes\n30,IT,Yes,No\n35,HR,No,No\n40,Sales,Yes,Yes\n28,IT,No,No\n45,Sales,Yes,Yes\n50,IT,Yes,No"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        analysis_response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        analysis_id = analysis_response.json()['analysis_id']
        
        # Get at-risk employees
        risk_response = client.get(f"/api/at_risk_employees/{analysis_id}")
        self.assertEqual(risk_response.status_code, 200)
        
        risk_data = risk_response.json()
        self.assertIn('total_employees', risk_data)
        self.assertIn('at_risk_count', risk_data)
        self.assertIn('critical_count', risk_data)
        self.assertIn('risk_percentage', risk_data)
        self.assertIn('at_risk_employees', risk_data)
        self.assertIsInstance(risk_data['at_risk_employees'], list)
    
    def test_at_risk_employees_custom_threshold(self):
        """Test at-risk employees with custom threshold"""
        # Upload and analyze
        csv_content = b"Age,Department,Attrition,OverTime\n25,Sales,No,Yes\n30,IT,Yes,No\n35,HR,No,No\n40,Sales,Yes,Yes\n28,IT,No,No"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        analysis_response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        analysis_id = analysis_response.json()['analysis_id']
        
        # Get at-risk employees with threshold
        risk_response = client.get(
            f"/api/at_risk_employees/{analysis_id}",
            params={"risk_threshold": 0.3}
        )
        self.assertEqual(risk_response.status_code, 200)
        risk_data = risk_response.json()
        self.assertIn('at_risk_employees', risk_data)
    
    def test_feature_importances_available(self):
        """Test that feature importances are available after analysis"""
        # Upload and analyze
        csv_content = b"Age,Department,Attrition,OverTime\n25,Sales,No,Yes\n30,IT,Yes,No\n35,HR,No,No\n40,Sales,Yes,Yes\n28,IT,No,No"
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        dataset_id = upload_response.json()['dataset_id']
        
        analysis_response = client.post(
            "/api/analyze",
            params={
                "dataset_id": dataset_id,
                "target_column": "Attrition"
            }
        )
        analysis_id = analysis_response.json()['analysis_id']
        
        # Get feature importances
        features_response = client.get(
            f"/api/analysis/{analysis_id}/feature_importances"
        )
        self.assertEqual(features_response.status_code, 200)
        
        features_data = features_response.json()
        self.assertIn('features', features_data)
        self.assertIsInstance(features_data['features'], list)
        
        # Verify feature structure
        for feature in features_data['features']:
            self.assertIn('feature', feature)
            self.assertIn('coef', feature)
            self.assertIn('abs', feature)


if __name__ == '__main__':
    unittest.main()
   
