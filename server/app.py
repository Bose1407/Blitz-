from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
CORS(app)

# Load the trained models
models = {
    f'Load{i}': joblib.load(f'load{i}_status_model.pkl') 
    for i in range(1, 6)
}

def calculate_cost(data):
    peak_rate = 0.20  # $/kWh during peak hours (8 AM to 8 PM)
    off_peak_rate = 0.10  # $/kWh during off-peak hours
    
    hour = datetime.now().hour
    rate = peak_rate if 8 <= hour < 20 else off_peak_rate
    
    total_power = sum(
        power * (1 if status == 'ON' else 0)
        for power, status in zip(
            [data[f'Load{i}_Power'] for i in range(1, 6)],
            [data[f'Load{i}_Status'] for i in range(1, 6)]
        )
    )
    
    return (total_power * rate) / 1000  # Convert to kWh

@app.route('/api/status', methods=['GET'])
def get_status():
    # Generate mock current data
    current_data = {
        f'Load{i}_Power': np.random.normal(500, 100)
        for i in range(1, 6)
    }
    
    # Get predictions from models
    predictions = {}
    features = pd.DataFrame([list(current_data.values())])
    
    for load_name, model in models.items():
        pred = model.predict(features)[0]
        predictions[load_name] = 'ON' if pred == 1 else 'OFF'
        current_data[f'{load_name}_Status'] = predictions[load_name]
    
    cost = calculate_cost(current_data)
    
    return jsonify({
        'status': predictions,
        'power': current_data,
        'cost': cost
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    # Generate mock historical data
    timestamps = [
        datetime.now() - timedelta(hours=i)
        for i in range(24, -1, -1)
    ]
    
    history = []
    for ts in timestamps:
        data = {
            'timestamp': ts.isoformat(),
            'cost': np.random.uniform(0.1, 0.5),
            **{
                f'Load{i}_Power': np.random.normal(500, 100)
                for i in range(1, 6)
            },
            **{
                f'Load{i}_Status': np.random.choice(['ON', 'OFF'])
                for i in range(1, 6)
            }
        }
        history.append(data)
    
    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True)