from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import uuid
from datetime import datetime, UTC
from pathlib import Path
import aiofiles
import io
import joblib
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import json

from .db import init_db, insert_dataset, insert_analysis, list_analyses, get_analysis
from .model import train_logistic, predict_from_model
from .auth import init_auth_db, create_hr_user, authenticate_hr_user, get_hr_user, list_hr_users
from .schemas import SignupRequest, LoginRequest
import math

app = FastAPI(title="Attrition Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[1]
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize database with error handling
try:
    init_db()
    init_auth_db()
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")
    # Continue anyway; database will be created on first use if needed

@app.post('/api/upload')
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    dataset_id = str(uuid.uuid4())
    out_path = STORAGE_DIR / f"dataset_{dataset_id}.csv"

    # save file
    async with aiofiles.open(out_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # read small sample and columns
    try:
        df = pd.read_csv(out_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unable to parse CSV: {e}")

    columns = df.columns.tolist()
    samples = df.head(5).to_dict(orient='records')

    # basic validation: detect missing expected fields, invalid rows, duplicates
    expected_fields = ['EmployeeID', 'id', 'Age', 'Department']
    missing_expected = [f for f in expected_fields if f in expected_fields and f not in columns]

    # Determine primary id column if present
    id_col = None
    for c in ['EmployeeID', 'id']:
        if c in columns:
            id_col = c
            break

    # invalid rows: rows with NA in any of required columns that exist
    required_for_validation = [c for c in ['Age', 'Department'] if c in columns]
    if required_for_validation:
        invalid_mask = df[required_for_validation].isna().any(axis=1)
        invalid_rows = int(invalid_mask.sum())
        invalid_samples = df[invalid_mask].head(5).to_dict(orient='records')
    else:
        invalid_rows = 0
        invalid_samples = []

    # duplicates: prefer id-based deduplication, otherwise full-row duplicates
    if id_col:
        dup_count = int(df.duplicated(subset=[id_col]).sum())
    else:
        dup_count = int(df.duplicated().sum())

    validation = {
        'record_count': int(len(df)),
        'missing_expected_fields': missing_expected,
        'invalid_rows_count': invalid_rows,
        'invalid_row_samples': invalid_samples,
        'duplicate_count': dup_count
    }

    insert_dataset(dataset_id, file.filename, datetime.now(UTC).isoformat(), columns, samples)

    return JSONResponse({'dataset_id': dataset_id, 'columns': columns, 'sample': samples, 'validation': validation})

@app.post('/api/analyze')
async def analyze(dataset_id: str, target_column: str = 'Attrition'):
    # find dataset file
    dataset_path = STORAGE_DIR / f"dataset_{dataset_id}.csv"
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail='Dataset not found')

    df = pd.read_csv(dataset_path)
    if df is None or df.shape[0] == 0:
        raise HTTPException(status_code=400, detail='Dataset is empty or could not be read')

    # If the target column is not present, return a clear 400 error with available columns
    if target_column not in df.columns:
        available = df.columns.tolist()
        raise HTTPException(status_code=400, detail=f"Target column '{target_column}' not found. Available columns: {', '.join(available)}")

    try:
        metrics, artifacts = train_logistic(df, target_column=target_column)
    except ValueError as e:
        # known validation error (e.g., target missing or invalid mapping)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")

    # sanitize metrics: JSON doesn't allow NaN/Inf; convert such values to None and
    # ensure all metrics are plain Python floats or None
    for k, v in list(metrics.items()):
        try:
            fv = float(v)
            if not math.isfinite(fv):
                metrics[k] = None
            else:
                metrics[k] = fv
        except Exception:
            metrics[k] = None

    analysis_id = str(uuid.uuid4())
    insert_analysis(analysis_id, dataset_id, 'logistic_regression', metrics, artifacts, datetime.now(UTC).isoformat())

    return JSONResponse({'analysis_id': analysis_id, 'metrics': metrics, 'artifacts': artifacts})

@app.get('/api/analyses')
async def get_analyses():
    rows = list_analyses()
    return JSONResponse(rows)

@app.get('/api/analysis/{analysis_id}')
async def get_analysis_route(analysis_id: str):
    row = get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404, detail='Analysis not found')
    # parse JSON fields
    row['metrics_json'] = json.loads(row['metrics_json']) if row.get('metrics_json') else None
    row['artifacts_json'] = json.loads(row['artifacts_json']) if row.get('artifacts_json') else None
    return JSONResponse(row)


@app.get('/api/download/model/{analysis_id}')
async def download_model(analysis_id: str):
    row = get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404, detail='Analysis not found')
    artifacts = json.loads(row['artifacts_json']) if row.get('artifacts_json') else {}
    model_path = artifacts.get('model_path')
    if not model_path or not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail='Model artifact not found')
    # Serve the model file; use .pkl filename for compatibility
    return FileResponse(path=model_path, media_type='application/octet-stream', filename=f"model_{analysis_id}.pkl")


@app.get('/api/download/predictions/{analysis_id}')
async def download_predictions(analysis_id: str):
    row = get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404, detail='Analysis not found')
    artifacts = json.loads(row['artifacts_json']) if row.get('artifacts_json') else {}
    model_path = artifacts.get('model_path')
    dataset_id = row.get('dataset_id')
    if not model_path or not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail='Model artifact not found')
    dataset_path = STORAGE_DIR / f"dataset_{dataset_id}.csv"
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail='Original dataset not found')

    # load dataset
    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to read dataset: {e}")

    # Use existing helper to predict; it expects records
    try:
        records = df.to_dict(orient='records')
        results = predict_from_model(model_path, records)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    preds_df = pd.DataFrame(results).set_index('index')
    combined = df.copy()
    combined['predicted_label'] = preds_df['predicted_label'].reindex(combined.index).values
    combined['predicted_probability'] = preds_df['probability'].reindex(combined.index).values

    csv_bytes = combined.to_csv(index=False).encode('utf-8')
    return StreamingResponse(io.BytesIO(csv_bytes), media_type='text/csv', headers={"Content-Disposition": f"attachment; filename=predictions_{analysis_id}.csv"})


@app.get('/api/download/analysis/{analysis_id}/pdf')
async def download_analysis_pdf(analysis_id: str):
    row = get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404, detail='Analysis not found')
    metrics = json.loads(row['metrics_json']) if row.get('metrics_json') else {}
    artifacts = json.loads(row['artifacts_json']) if row.get('artifacts_json') else {}
    cm = artifacts.get('confusion_matrix')

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    text = c.beginText(40, 750)
    text.setFont("Helvetica", 12)
    text.textLine(f"Analysis ID: {analysis_id}")
    text.textLine("")
    text.textLine("Metrics:")
    for k, v in (metrics or {}).items():
        text.textLine(f" - {k}: {v}")
    text.textLine("")
    text.textLine("Confusion Matrix:")
    if cm:
        for row_cm in cm:
            text.textLine("  " + ", ".join(str(x) for x in row_cm))
    c.drawText(text)
    c.showPage()
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type='application/pdf', headers={"Content-Disposition": f"attachment; filename=analysis_{analysis_id}.pdf"})


@app.get('/api/analysis/{analysis_id}/feature_importances')
async def analysis_feature_importances(analysis_id: str):
    """Compute and return feature importances (coefficients) for a trained model.

    Returns a list of {feature: name, coef: float, abs: float} sorted by absolute importance.
    """
    row = get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404, detail='Analysis not found')
    artifacts = json.loads(row.get('artifacts_json') or '{}')
    model_path = artifacts.get('model_path')
    if not model_path or not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail='Model artifact not found')

    try:
        clf = joblib.load(model_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unable to load model: {e}')

    # try to extract feature names in a robust way
    feature_names = []
    try:
        preprocessor = None
        if hasattr(clf, 'named_steps') and 'preprocessor' in clf.named_steps:
            preprocessor = clf.named_steps['preprocessor']

        # preferred: preprocessor.get_feature_names_out
        if preprocessor is not None and hasattr(preprocessor, 'get_feature_names_out'):
            try:
                # If the preprocessor requires input columns, try to use stored artifact lists
                numeric = artifacts.get('numeric_features') or []
                categorical = artifacts.get('categorical_features') or []
                cols = numeric + categorical
                feature_names = list(preprocessor.get_feature_names_out(cols))
            except Exception:
                try:
                    feature_names = list(preprocessor.get_feature_names_out())
                except Exception:
                    feature_names = []

        # fallback: reconstruct from stored numeric/categorical and encoder categories
        if not feature_names:
            numeric = artifacts.get('numeric_features') or []
            categorical = artifacts.get('categorical_features') or []
            feature_names = []
            feature_names.extend(numeric)
            # one-hot categories
            if preprocessor is not None:
                try:
                    cat_transformer = None
                    if hasattr(preprocessor, 'named_transformers_'):
                        cat_transformer = preprocessor.named_transformers_.get('cat')
                    if cat_transformer is not None and hasattr(cat_transformer, 'named_steps'):
                        onehot = cat_transformer.named_steps.get('onehot') or cat_transformer.named_steps.get('onehotencoder')
                        if onehot is None:
                            onehot = cat_transformer.named_steps.get('onehotencoder')
                        if onehot is not None and hasattr(onehot, 'categories_'):
                            for col, cats in zip(categorical, onehot.categories_):
                                for cat in cats:
                                    feature_names.append(f"{col}_{cat}")
                        else:
                            for col in categorical:
                                feature_names.append(col)
                    else:
                        for col in categorical:
                            feature_names.append(col)
                except Exception:
                    for col in categorical:
                        feature_names.append(col)

    except Exception:
        feature_names = []

    # extract coefficients from classifier
    coefs = None
    try:
        classifier = None
        if hasattr(clf, 'named_steps'):
            classifier = clf.named_steps.get('classifier') or list(clf.named_steps.values())[-1]
        else:
            classifier = clf

        if hasattr(classifier, 'coef_'):
            coef = classifier.coef_
            if coef.ndim == 2:
                coefs = coef[0].tolist()
            else:
                coefs = coef.tolist()
        elif hasattr(classifier, 'feature_importances_'):
            coefs = classifier.feature_importances_.tolist()
        else:
            coefs = None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unable to extract coefficients: {e}')

    if not coefs:
        raise HTTPException(status_code=500, detail='Model does not expose coefficients or feature importances')

    # align feature names length
    if feature_names and len(feature_names) != len(coefs):
        feature_names = [f'feature_{i}' for i in range(len(coefs))]
    elif not feature_names:
        feature_names = [f'feature_{i}' for i in range(len(coefs))]

    items = []
    for n, c in zip(feature_names, coefs):
        try:
            val = float(c)
        except Exception:
            val = 0.0
        items.append({'feature': n, 'coef': val, 'abs': abs(val)})

    items_sorted = sorted(items, key=lambda x: x['abs'], reverse=True)
    return JSONResponse({'features': items_sorted})

@app.post('/api/predict')
async def predict(analysis_id: str, records: list):
    row = get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404, detail='Analysis not found')
    artifacts = json.loads(row['artifacts_json'])
    model_path = artifacts.get('model_path')
    if not model_path or not os.path.exists(model_path):
        raise HTTPException(status_code=500, detail='Model artifact missing')

    try:
        results = predict_from_model(model_path, records)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    return JSONResponse({'predictions': results})


@app.get('/api/at_risk_employees/{analysis_id}')
async def get_at_risk_employees(analysis_id: str, risk_threshold: float = 0.5):
    """Get employees at risk of attrition based on model predictions"""
    row = get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404, detail='Analysis not found')
    
    dataset_id = row.get('dataset_id')
    artifacts = json.loads(row.get('artifacts_json') or '{}')
    model_path = artifacts.get('model_path')
    
    if not dataset_id or not model_path or not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail='Required data not found')
    
    dataset_path = STORAGE_DIR / f"dataset_{dataset_id}.csv"
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail='Dataset not found')
    
    try:
        # Load full dataset
        df = pd.read_csv(dataset_path)
        records = df.to_dict(orient='records')
        
        # Get predictions for all employees
        results = predict_from_model(model_path, records)
        
        # Filter for at-risk employees (those with high attrition probability)
        at_risk = []
        critical_count = 0
        
        for i, result in enumerate(results):
            if result.get('probability', 0) >= risk_threshold and i < len(df):
                risk_level = 'Critical' if result['probability'] >= 0.8 else 'High' if result['probability'] >= 0.6 else 'Moderate'
                if risk_level == 'Critical':
                    critical_count += 1
                
                employee = df.iloc[i].to_dict()
                at_risk.append({
                    'index': result['index'],
                    'attrition_probability': result['probability'],
                    'risk_level': risk_level,
                    'employee_data': employee
                })
        
        # Sort by probability (highest risk first)
        at_risk.sort(key=lambda x: x['attrition_probability'], reverse=True)
        
        return JSONResponse({
            'total_employees': len(df),
            'at_risk_count': len(at_risk),
            'critical_count': critical_count,
            'risk_percentage': (len(at_risk) / len(df) * 100) if len(df) > 0 else 0,
            'at_risk_employees': at_risk[:50]  # Return top 50 at-risk employees
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze at-risk employees: {e}")


@app.get('/')
async def root():
    return JSONResponse({'status': 'ok', 'message': 'Attrition Analysis API'})


# Authentication endpoints for HR
@app.post('/api/auth/signup')
async def signup(request: SignupRequest):
    """Create a new HR user account"""
    try:
        if len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        user = create_hr_user(request.email, request.password, request.full_name, request.department)
        return JSONResponse(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/auth/login')
async def login(request: LoginRequest):
    """Authenticate HR user"""
    try:
        user = authenticate_hr_user(request.email, request.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return JSONResponse(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/auth/user/{user_id}')
async def get_user(user_id: str):
    """Get HR user details"""
    try:
        user = get_hr_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return JSONResponse(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/auth/users')
async def list_users():
    """List all HR users"""
    try:
        users = list_hr_users()
        return JSONResponse(users)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    # Allow starting the backend with: `python -m app.main` or `python main.py`
    # This helps when users run the module directly instead of using uvicorn CLI.
    try:
        import uvicorn
        uvicorn.run(app, host='127.0.0.1', port=8000, reload=True)
    except Exception:
        # uvicorn may not be available in some environments; surface a helpful message.
        print('To run the API use: uvicorn app.main:app --reload --port 8000')
     #PIPELINE
