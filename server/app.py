from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
import os
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
from joblib import Parallel, delayed

app = Flask(__name__)
CORS(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"]
)

models = {
    f'Load{i}': joblib.load(os.getenv(f'LOAD{i}_MODEL_PATH', f'load{i}_status_model.pkl'))
    for i in range(1, 6)
}

def calculate_cost(data):

    base_rate = 4.80  # ₹/kWh base rate
    peak_factor = 0.25  
    off_peak_factor = 0.0

    # Calculate effective rates
    peak_rate = base_rate * (1 + peak_factor)  # 6.00 ₹/kWh
    off_peak_rate = base_rate * (1 + off_peak_factor)  # 4.80 ₹/kWh

    # Tamil Nadu peak hours (5-9 AM and 6-10 PM)
    hour = datetime.now().hour
    is_peak = (5 <= hour < 9) or (18 <= hour < 22)
    rate = peak_rate if is_peak else off_peak_rate

    # Calculate total power consumption
    total_power = sum(
        data.get(f'Load{i}_Power', 0) * (1 if data.get(f'Load{i}_Status', 'OFF') == 'ON' else 0)
        for i in range(1, 6)
    )

    return (total_power * rate) / 1000

def generate_mock_data():
    return {
        f'Load{i}_Power': max(0, np.random.normal(500, 100))
        for i in range(1, 6)
    }

def predict_load(model, features):
    try:
        pred = model.predict(features)[0]
        return 'ON' if pred == 1 else 'OFF'
    except Exception as e:
        return 'OFF'

@app.route('/api/status', methods=['GET'])
@limiter.limit("30 per minute")
def get_status():
    try:
        np.random.seed(42)
        current_data = generate_mock_data()
        
        features = pd.DataFrame([list(current_data.values())])
        predictions = Parallel(n_jobs=-1)(
            delayed(predict_load)(model, features)
            for model in models.values()
        )
        
        for i, (load_name, pred) in enumerate(zip(models.keys(), predictions)):
            current_data[f'{load_name}_Status'] = pred
        
        cost = calculate_cost(current_data)
        
        return jsonify({
            'status': dict(zip(models.keys(), predictions)),
            'power': current_data,
            'cost': round(cost, 2) 
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
@limiter.limit("20 per minute")
def get_history():
    try:
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(24, -1, -1)]
        
        history = [
            {
                'timestamp': ts.isoformat(),
                'cost': round(np.random.uniform(2.5, 8.5), 2),  # INR values
                **generate_mock_data(),
                **{f'Load{i}_Status': np.random.choice(['ON', 'OFF']) for i in range(1, 6)}
            }
            for ts in timestamps
        ]
        
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

if __name__ == '__main__':
    app.run(debug=True)