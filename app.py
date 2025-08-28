from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)

# Load your trained model (make sure to save it as .pkl in the repo first)
model = joblib.load("taxi_demand_model.pkl.gz")

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json  # expects {"features": [values]}
    df = pd.DataFrame([data["features"]])
    prediction = model.predict(df)[0]
    return jsonify({"prediction": str(prediction)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
