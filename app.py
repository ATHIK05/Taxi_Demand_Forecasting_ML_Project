from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)

try:
    print("🔄 Loading model...")
    model = joblib.load("taxi_demand_model.pkl")
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    model = None

@app.route("/")
def home():
    return "🚖 Taxi Demand Forecasting API is running!"

@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    data = request.json
    df = pd.DataFrame([data["features"]])
    prediction = model.predict(df)[0]
    return jsonify({"prediction": float(prediction)})
