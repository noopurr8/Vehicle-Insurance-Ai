import joblib
import pandas as pd

MODEL_PATH = r"C:\Users\noopu\Desktop\vehicle-insurance-ai\ai\fraud_detection\fraud_model.pkl"

model = joblib.load(MODEL_PATH)


def predict_fraud(claim_data):
    df = pd.DataFrame([claim_data])

    probability = float(model.predict_proba(df)[0][1])
    prediction = int(model.predict(df)[0])

    return {
        "fraud_probability": round(probability, 3),
        "fraud_prediction": prediction
    }


if __name__ == "__main__":
    print("Fraud detection service ready.")