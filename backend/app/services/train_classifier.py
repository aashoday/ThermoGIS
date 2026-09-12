"""
Trains a LightGBM multiclass classifier on heuristic-labeled hotspot
features, writes predictions (predicted_class + prediction_confidence)
back to the hotspots table, and saves the trained model to disk for
reuse by the API layer.
"""
import os

import joblib
import lightgbm as lgb
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import text

from app.database import SessionLocal
from app.services.features import load_feature_dataframe, FEATURE_COLUMNS
from app.services.heuristic_labels import apply_heuristic_labels, LABELS

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "model_artifacts")
MODEL_PATH = os.path.join(MODEL_DIR, "lightgbm_classifier.joblib")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.joblib")

UPDATE_PREDICTION_SQL = text("""
    UPDATE hotspots
    SET predicted_class = :predicted_class,
        prediction_confidence = :prediction_confidence
    WHERE id = :hotspot_id
""")


def train_and_predict():
    db = SessionLocal()
    try:
        df = load_feature_dataframe(db)
        if df.empty:
            print("No feature data available — run spatial_join and cluster_hotspots first.")
            return

        df = apply_heuristic_labels(df)

        print(f"Training on {len(df)} hotspots.")
        print("Heuristic label distribution:")
        print(df["heuristic_label"].value_counts())

        X = df[FEATURE_COLUMNS]
        y_raw = df["heuristic_label"]

        encoder = LabelEncoder()
        encoder.fit(LABELS)  # fixed label set, so encoding is stable even if a class is absent this run
        y = encoder.transform(y_raw)

        model = lgb.LGBMClassifier(
            n_estimators=100,
            max_depth=4,          # shallow trees — appropriate for a small dataset, avoids overfitting
            num_leaves=8,
            min_child_samples=2,  # small dataset needs a low leaf-size floor
            learning_rate=0.1,
            objective="multiclass",
            num_class=len(LABELS),
            verbosity=-1,
        )
        model.fit(X, y)

        y_pred = model.predict(X)
        print("\nTraining-fit classification report (NOT a held-out test — sanity check only):")
        all_label_indices = list(range(len(LABELS)))
        print(classification_report(
            y, y_pred,
            labels=all_label_indices,
            target_names=encoder.classes_,
            zero_division=0,
        ))
        probabilities = model.predict_proba(X)
        predicted_labels = encoder.inverse_transform(y_pred)
        confidences = probabilities.max(axis=1)

        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        joblib.dump(encoder, ENCODER_PATH)
        print(f"\nModel saved to {MODEL_PATH}")

        for hotspot_id, label, confidence in zip(df["id"], predicted_labels, confidences):
            db.execute(UPDATE_PREDICTION_SQL, {
                "predicted_class": label,
                "prediction_confidence": float(confidence),
                "hotspot_id": hotspot_id,
            })
        db.commit()
        print(f"Wrote predictions back to {len(df)} hotspots.")

        print("\nFeature importance:")
        for feat, imp in zip(FEATURE_COLUMNS, model.feature_importances_):
            print(f"  {feat}: {imp}")

    finally:
        db.close()


if __name__ == "__main__":
    train_and_predict()