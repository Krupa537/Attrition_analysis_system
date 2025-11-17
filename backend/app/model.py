import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
from pathlib import Path
import uuid

STORAGE_DIR = Path(__file__).resolve().parents[1] / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def train_logistic(df, target_column='Attrition', test_size=0.2, random_state=42):
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataframe")

    X = df.drop(columns=[target_column])
    y = df[target_column].map({'Yes': 1, 'No': 0}) if df[target_column].dtype == object else df[target_column]

    # simple preprocessing: separate numeric and categorical
    numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

    numeric_transformer = Pipeline(steps=[('imputer', SimpleImputer(strategy='median'))])
    # create a OneHotEncoder instance that is compatible across sklearn versions
    try:
        onehot = OneHotEncoder(handle_unknown='ignore', sparse=False)
    except TypeError:
        # newer sklearn versions renamed `sparse` to `sparse_output`
        onehot = OneHotEncoder(handle_unknown='ignore', sparse_output=False)

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', onehot)
    ])

    preprocessor = ColumnTransformer(transformers=[
        ('num', numeric_transformer, numeric_cols),
        ('cat', categorical_transformer, cat_cols)
    ], remainder='drop')

    clf = Pipeline(steps=[('preprocessor', preprocessor),
                          ('classifier', LogisticRegression(max_iter=1000, class_weight='balanced'))])

    # Try stratified split to preserve class balance. For very small datasets this can
    # fail (e.g. test_size results in fewer samples than classes). Fall back to a
    # non-stratified split in that case.
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
    except ValueError:
        # fallback: split without stratify
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=None
        )

    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1] if hasattr(clf, 'predict_proba') else None

    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, zero_division=0)),
    }
    if y_proba is not None:
        try:
            metrics['roc_auc'] = float(roc_auc_score(y_test, y_proba))
        except Exception:
            metrics['roc_auc'] = None

    cm = confusion_matrix(y_test, y_pred).tolist()

    model_id = str(uuid.uuid4())
    model_path = STORAGE_DIR / f"model_{model_id}.joblib"
    joblib.dump(clf, model_path)

    artifacts = {
        'model_path': str(model_path),
        'confusion_matrix': cm,
        'numeric_features': numeric_cols,
        'categorical_features': cat_cols
    }

    return metrics, artifacts


def predict_from_model(model_path, records):
    clf = joblib.load(model_path)
    df = pd.DataFrame(records)
    proba = clf.predict_proba(df)[:, 1] if hasattr(clf, 'predict_proba') else None
    preds = clf.predict(df)
    results = []
    for i, _ in df.iterrows():
        results.append({
            'index': int(i),
            'predicted_label': int(preds[i]),
            'probability': float(proba[i]) if proba is not None else None
        })
    return results
