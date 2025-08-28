from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)

# Load trained model
model = joblib.load("taxi_demand_model.pkl.gz")

# Root route for testing in browser
@app.route("/")
def home():
    return "🚖 Taxi Demand Forecasting API is running!"

# Prediction route
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json  # expects {"features": [values]}
        
        if not data or "features" not in data:
            return jsonify({"error": "Invalid input. Provide JSON with 'features'"}), 400

        # Convert input into DataFrame
        df = pd.DataFrame([data["features"]])

        # Predict
        prediction = model.predict(df)[0]

        return jsonify({"prediction": float(prediction)})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Only needed for local testing; Render uses gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
