import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, classification_report
import xgboost as xgb
from skl2onnx import to_onnx
from onnxmltools.convert import convert_xgboost
from onnxmltools.convert.common.data_types import FloatTensorType
import onnx

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
FLOOD_DATA_PATH = os.path.join(DATA_DIR, 'flood_risk_dataset_india.csv')
DISASTER_DATA_PATH = os.path.join(DATA_DIR, 'disasterIND.csv')

def train_flood_model():
    print("Training Flood Risk XGBoost Model...")
    df = pd.read_csv(FLOOD_DATA_PATH)
    
    features = ['Rainfall (mm)', 'Temperature (°C)', 'River Discharge (m³/s)', 
                'Water Level (m)', 'Elevation (m)', 'Population Density', 
                'Infrastructure', 'Historical Floods']
    target = 'Flood Occurred'
    
    X = df[features]
    y = df[target]
    
    # Handle missing values
    X = X.fillna(X.mean())
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    model.fit(X_train.values, y_train)
    
    y_pred = model.predict(X_test.values)
    y_prob = model.predict_proba(X_test.values)[:, 1]
    
    print("Flood Model Evaluation:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"F1 Score: {f1_score(y_test, y_pred):.4f}")
    print(f"AUC-ROC: {roc_auc_score(y_test, y_prob):.4f}\n")
    
    # Convert to ONNX
    initial_type = [('float_input', FloatTensorType([None, len(features)]))]
    onnx_model = convert_xgboost(model, initial_types=initial_type, target_opset=12)
    
    onnx_path = os.path.join(os.path.dirname(__file__), 'flood_model.onnx')
    with open(onnx_path, 'wb') as f:
        f.write(onnx_model.SerializeToString())
    print(f"Saved Flood Model to {onnx_path}\n")

def get_severity(row):
    deaths = pd.to_numeric(row['Total Deaths'], errors='coerce')
    affected = pd.to_numeric(row['Total Affected'], errors='coerce')
    
    if pd.isna(deaths): deaths = 0
    if pd.isna(affected): affected = 0
    
    if deaths > 100 or affected > 500000:
        return 3 # CRITICAL
    elif deaths > 20 or affected > 50000:
        return 2 # HIGH
    elif deaths > 5 or affected > 5000:
        return 1 # MODERATE
    else:
        return 0 # LOW

def train_severity_model():
    print("Training Severity Random Forest Model...")
    df = pd.read_csv(DISASTER_DATA_PATH)
    
    features = ['Disaster Type', 'Total Deaths', 'Total Affected', "Total Damage ('000 US$)", 'Start Year', 'Start Month']
    
    df['Total Deaths'] = df['Total Deaths'].fillna(0)
    df['Total Affected'] = df['Total Affected'].fillna(0)
    
    df['Severity'] = df.apply(get_severity, axis=1)
    
    X = df[features].copy()
    y = df['Severity']
    
    X["Total Damage ('000 US$)"] = pd.to_numeric(X["Total Damage ('000 US$)"], errors='coerce').fillna(0)
    X['Start Year'] = pd.to_numeric(X['Start Year'], errors='coerce').fillna(X['Start Year'].mode()[0] if not X['Start Year'].mode().empty else 2000)
    X['Start Month'] = pd.to_numeric(X['Start Month'], errors='coerce').fillna(X['Start Month'].mode()[0] if not X['Start Month'].mode().empty else 1)
    X['Disaster Type'] = X['Disaster Type'].fillna('Unknown')
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    categorical_features = ['Disaster Type']
    numeric_features = ['Total Deaths', 'Total Affected', "Total Damage ('000 US$)", 'Start Year', 'Start Month']
    
    numeric_transformer = 'passthrough'
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                               ('classifier', RandomForestClassifier(random_state=42))])
    
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    print("Severity Model Evaluation:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))
    
    # Convert to ONNX
    onnx_model = to_onnx(pipeline, X_train[:1], target_opset=12)
    onnx_path = os.path.join(os.path.dirname(__file__), 'severity_model.onnx')
    with open(onnx_path, 'wb') as f:
        f.write(onnx_model.SerializeToString())
    print(f"Saved Severity Model to {onnx_path}\n")

if __name__ == "__main__":
    train_flood_model()
    train_severity_model()
