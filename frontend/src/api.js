// Centralized API configuration
const API_BASE_URL = 'http://localhost:8000/api';

export const API = {
  // Auth endpoints
  signup: `${API_BASE_URL}/auth/signup`,
  login: `${API_BASE_URL}/auth/login`,
  getUser: (userId) => `${API_BASE_URL}/auth/user/${userId}`,
  listUsers: `${API_BASE_URL}/auth/users`,
  
  // Analysis endpoints
  upload: `${API_BASE_URL}/upload`,
  analyze: (datasetId, targetColumn) => `${API_BASE_URL}/analyze?dataset_id=${datasetId}&target_column=${encodeURIComponent(targetColumn)}`,
  getAnalyses: `${API_BASE_URL}/analyses`,
  getAnalysis: (analysisId) => `${API_BASE_URL}/analysis/${analysisId}`,
  getFeatureImportances: (analysisId) => `${API_BASE_URL}/analysis/${analysisId}/feature_importances`,
  getAtRiskEmployees: (analysisId) => `${API_BASE_URL}/at_risk_employees/${analysisId}`,
  predict: `${API_BASE_URL}/predict`,
  
  // Download endpoints
  downloadModel: (analysisId) => `${API_BASE_URL}/download/model/${analysisId}`,
  downloadPredictions: (analysisId) => `${API_BASE_URL}/download/predictions/${analysisId}`,
  downloadPDF: (analysisId) => `${API_BASE_URL}/download/analysis/${analysisId}/pdf`,
};

export default API;
