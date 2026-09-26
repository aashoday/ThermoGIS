"""
Trains a LightGBM multiclass classifier on heuristic-labeled hotspot
features, writes predictions (predicted_class + prediction_confidence)
back to the hotspots table, and saves the trained model to disk for
reuse by the API layer.
"""
import os

import json
import joblib
import lightgbm as lgb
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import cross_val_predict, StratifiedKFold
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
        prediction_confidence = :prediction_confidence,
        top_features = :top_features
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
        encoder.fit(LABELS)     # fixed label set, so encoding is stable even if a class is absent
        y = encoder.transform(y_raw)

        print("\nFeature dtypes going into the model:")
        print(X.dtypes)
        print("\nCategorical value counts:")
        print(f"  landcover_class: {df['landcover_class'].value_counts().to_dict()}")
        print(f"  nearest_asset_type: {df['nearest_asset_type'].value_counts().to_dict()}")

        model = lgb.LGBMClassifier(
            n_estimators=150,
            max_depth=5,
            num_leaves=16,
            min_child_samples=2,
            learning_rate=0.1,
            feature_fraction=0.7,
            bagging_fraction=0.8,
            bagging_freq=1,
            min_data_per_group=3,     # THE actual fix — default is 100, which silently
                                       # forbids splitting on ANY category with fewer than
                                       # 100 samples. Every value in landcover_class and
                                       # nearest_asset_type has far fewer than that
                                       # (mine_quarry: 3, refinery: 4, Water Bodies: 3), so
                                       # the categorical features were structurally blocked
                                       # from ever being used, independent of tuning above
            cat_smooth=1,              # default (10) over-smooths split gain for exactly
                                       # this kind of low-count category; small dataset
                                       # needs less aggressive smoothing
            objective="multiclass",
            num_class=len(LABELS),
            class_weight="balanced",
            verbosity=-1,
        )
        

        # Confidence must come from genuinely held-out predictions (see the
        # comment history on this function). With 6 classes now instead of
        # 3, some classes may have very few examples — guard against
        # StratifiedKFold failing outright when a class has fewer members
        # than the fold count.
        label_counts = df["heuristic_label"].value_counts()
        smallest_class_count = label_counts.min()

        if smallest_class_count < 2:
            print(
                f"\nWARNING: class '{label_counts.idxmin()}' has only "
                f"{smallest_class_count} sample(s) — too few for cross-validation. "
                f"Falling back to in-sample (optimistic) confidence for this run; "
                f"more data for that class will fix this properly."
            )
            model.fit(X, y)
            oof_probabilities = model.predict_proba(X)
        else:
            n_splits = max(2, min(5, smallest_class_count))
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            oof_probabilities = cross_val_predict(model, X, y, cv=cv, method="predict_proba")
            print(f"\nUsing {n_splits}-fold cross-validation for held-out confidence scores.")

        y_pred_oof = oof_probabilities.argmax(axis=1)
        predicted_labels = encoder.inverse_transform(y_pred_oof)
        confidences = oof_probabilities.max(axis=1)

        all_label_ids = list(range(len(LABELS)))
        print("\nOut-of-fold classification report (genuine held-out signal, not in-sample):")
        print(classification_report(
            y, y_pred_oof, labels=all_label_ids, target_names=encoder.classes_, zero_division=0
        ))

        # Explicit categorical_feature pin here (not just relying on pandas
        # category-dtype auto-detection) — belt-and-suspenders so we know
        # for certain LightGBM is treating these as categorical, not silently
        # falling back to something else.
        model.fit(X, y, categorical_feature=["landcover_class", "nearest_asset_type"])

                # SHAP-style explanation via LightGBM's native TreeSHAP — real
        # per-feature contributions, computed from this final model (the
        # same one used for future live inference).
        n_features = len(FEATURE_COLUMNS)
        contrib = model.booster_.predict(X, pred_contrib=True).reshape(len(X), len(LABELS), n_features + 1)
        final_pred_idx = model.predict(X)
        top_features_list = []
        for i in range(len(X)):
            row_contrib = contrib[i, final_pred_idx[i], :n_features]
            ranked = sorted(zip(FEATURE_COLUMNS, row_contrib), key=lambda x: abs(x[1]), reverse=True)[:3]
            top_features_list.append(json.dumps([
                {"feature": feat, "value": str(X.iloc[i][feat]), "contribution": round(float(val), 4)}
                for feat, val in ranked
            ]))

        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        joblib.dump(encoder, ENCODER_PATH)
        print(f"\nModel saved to {MODEL_PATH}")

        for hotspot_id, label, confidence, top_features in zip(df["id"], predicted_labels, confidences, top_features_list):
            db.execute(UPDATE_PREDICTION_SQL, {
                "predicted_class": label,
                "prediction_confidence": float(confidence),
                "top_features": top_features,
                "hotspot_id": hotspot_id,
        })
        db.commit()
        print(f"Wrote predictions back to {len(df)} hotspots.")

        print("\nFeature importance (from final full-fit model):")
        for feat, imp in zip(FEATURE_COLUMNS, model.feature_importances_):
            print(f"    {feat}: {imp}")

    finally:
        db.close()


if __name__ == "__main__":
    train_and_predict()