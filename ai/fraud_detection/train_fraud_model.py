import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score
)

# =========================
# 1. Load dataset
# =========================

DATA_PATH = r"D:\Downloads\fraud_oracle.csv"

df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)
print("\nFraud distribution:")
print(df["FraudFound_P"].value_counts())

# =========================
# 2. Separate features/target
# =========================

X = df.drop(columns=["FraudFound_P", "PolicyNumber"])
y = df["FraudFound_P"]

# =========================
# 3. Identify columns
# =========================

categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()
numeric_cols = X.select_dtypes(exclude=["object"]).columns.tolist()

print("\nCategorical columns:", len(categorical_cols))
print("Numeric columns:", len(numeric_cols))

# =========================
# 4. Preprocessing
# =========================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_cols
        ),
        (
            "numeric",
            "passthrough",
            numeric_cols
        )
    ]
)

# =========================
# 5. Random Forest
# =========================

model = RandomForestClassifier(
    n_estimators=300,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
    max_depth=15
)

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)

# =========================
# 6. Train/test split
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    stratify=y,
    random_state=42
)

print("\nTraining records:", len(X_train))
print("Testing records:", len(X_test))

# =========================
# 7. Train
# =========================

print("\nTraining Random Forest...")

pipeline.fit(X_train, y_train)

print("Training complete!")

# =========================
# 8. Predictions
# =========================

y_pred = pipeline.predict(X_test)
y_prob = pipeline.predict_proba(X_test)[:, 1]

# =========================
# 9. Evaluation
# =========================

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nROC-AUC:", roc_auc_score(y_test, y_prob))
print("PR-AUC:", average_precision_score(y_test, y_prob))

# =========================
# 10. Save model
# =========================

os.makedirs("ai/fraud_detection", exist_ok=True)

MODEL_PATH = "ai/fraud_detection/fraud_model.pkl"

joblib.dump(pipeline, MODEL_PATH)

print("\nModel saved to:", MODEL_PATH)