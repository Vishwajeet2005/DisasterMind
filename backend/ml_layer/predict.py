import os
import numpy as np
import pandas as pd
import onnxruntime as rt

class MLPredictor:
    def __init__(self):
        self.flood_model_path = os.path.join(os.path.dirname(__file__), 'flood_model.onnx')
        self.severity_model_path = os.path.join(os.path.dirname(__file__), 'severity_model.onnx')
        
        self.flood_session = None
        self.severity_session = None
        
        if os.path.exists(self.flood_model_path):
            try:
                self.flood_session = rt.InferenceSession(self.flood_model_path)
            except Exception as e:
                print(f"Failed to load flood model: {e}")
        else:
            print(f"Warning: {self.flood_model_path} not found.")
            
        if os.path.exists(self.severity_model_path):
            try:
                self.severity_session = rt.InferenceSession(self.severity_model_path)
            except Exception as e:
                print(f"Failed to load severity model: {e}")
        else:
            print(f"Warning: {self.severity_model_path} not found.")
            
        self.severity_map = {0: 'LOW', 1: 'MODERATE', 2: 'HIGH', 3: 'CRITICAL'}

    def predict_flood_risk(self, rainfall: float, temp: float, discharge: float, 
                           water_level: float, elevation: float, pop_density: float, 
                           infrastructure: float, history: float):
        if not self.flood_session:
            # Fallback heuristic
            prob = min(1.0, (rainfall / 500) + (water_level / 10))
            return float(prob), "High" if prob > 0.5 else "Low"
            
        try:
            input_name = self.flood_session.get_inputs()[0].name
            input_data = np.array([[rainfall, temp, discharge, water_level, elevation, 
                                    pop_density, infrastructure, history]], dtype=np.float32)
            
            pred_onx = self.flood_session.run(None, {input_name: input_data})
            label = pred_onx[0][0]
            
            # The structure of probabilities returned by ONNX for XGBoost depends on the converter
            # Sometimes it's a list of dictionaries, sometimes an array.
            if isinstance(pred_onx[1], list) and isinstance(pred_onx[1][0], dict):
                prob = pred_onx[1][0].get(1, 0.0)
            else:
                prob = pred_onx[1][0][1] if len(pred_onx[1][0]) > 1 else 0.0
            
            risk_label = "High" if label == 1 else "Low"
            return float(prob), risk_label
        except Exception as e:
            print(f"Flood prediction failed: {e}")
            return 0.0, "Low"

    def predict_severity(self, disaster_type: str, deaths: float, affected: float, 
                         damage: float, year: float, month: float):
        if not self.severity_session:
            # Fallback heuristic
            if deaths > 100 or affected > 500000: return 3, 'CRITICAL'
            elif deaths > 20 or affected > 50000: return 2, 'HIGH'
            elif deaths > 5 or affected > 5000: return 1, 'MODERATE'
            else: return 0, 'LOW'
            
        # Create input DataFrame
        input_data = pd.DataFrame([{
            'Disaster_Type': str(disaster_type),
            'Total_Deaths': float(deaths),
            'Total_Affected': float(affected),
            'Total_Damage___000_US__': float(damage),
            'Start_Year': float(year),
            'Start_Month': float(month)
        }])
        
        inputs = {}
        for inp in self.severity_session.get_inputs():
            col = inp.name
            if col in input_data.columns:
                if inp.type == 'tensor(string)':
                    inputs[col] = input_data[col].values.astype(object).reshape(-1, 1)
                elif inp.type == 'tensor(double)':
                    inputs[col] = input_data[col].values.astype(np.float64).reshape(-1, 1)
                elif inp.type == 'tensor(float)':
                    inputs[col] = input_data[col].values.astype(np.float32).reshape(-1, 1)
                elif inp.type == 'tensor(int64)':
                    inputs[col] = input_data[col].values.astype(np.int64).reshape(-1, 1)
                else:
                    inputs[col] = input_data[col].values.reshape(-1, 1)
                    
        try:
            pred_onx = self.severity_session.run(None, inputs)
            score = int(pred_onx[0][0])
            label = self.severity_map.get(score, "UNKNOWN")
            return score, label
        except Exception as e:
            print(f"Severity prediction failed: {e}")
            return 0, 'LOW'
            
    def get_combined_prediction(self, sensor_data: dict):
        prob, flood_label = self.predict_flood_risk(
            float(sensor_data.get('rainfall', 0.0)),
            float(sensor_data.get('temp', 25.0)),
            float(sensor_data.get('discharge', 0.0)),
            float(sensor_data.get('water_level', 0.0)),
            float(sensor_data.get('elevation', 0.0)),
            float(sensor_data.get('pop_density', 0.0)),
            float(sensor_data.get('infrastructure', 0.0)),
            float(sensor_data.get('history', 0.0))
        )
        
        score, severity_label = self.predict_severity(
            str(sensor_data.get('disaster_type', 'Flood')),
            float(sensor_data.get('deaths', 0.0)),
            float(sensor_data.get('affected', 0.0)),
            float(sensor_data.get('damage', 0.0)),
            float(sensor_data.get('year', 2026.0)),
            float(sensor_data.get('month', 1.0))
        )
        
        return {
            'flood_probability': prob,
            'flood_risk': flood_label,
            'severity_score': score,
            'severity_label': severity_label,
            'ml_confidence': prob * 0.9 if score > 0 else 0.5
        }

predictor = MLPredictor()
