# Simple schemas (can be extended)
from pydantic import BaseModel
from typing import List, Any

class UploadResponse(BaseModel):
    dataset_id: str
    columns: List[str]
    sample: List[Any]

class AnalyzeRequest(BaseModel):
    dataset_id: str
    target_column: str = 'Attrition'

class AnalyzeResponse(BaseModel):
    analysis_id: str
    metrics: dict
    artifacts: dict

class PredictRequest(BaseModel):
    analysis_id: str
    records: List[dict]

class PredictResponse(BaseModel):
    predictions: List[dict]
