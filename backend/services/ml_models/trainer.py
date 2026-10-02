"""CyberShield 360 - Machine Learning Model Trainer.

Trains Random Forest Classifier for URL Threat Analysis and TF-IDF + Logistic Regression
for SMS/Email Text Threat Classification using curated threat datasets.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

from services.ml_models.url_features import extract_url_features

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASETS_DIR = os.path.join(BASE_DIR, "ml_models", "datasets")
MODELS_DIR = os.path.join(BASE_DIR, "ml_models")


class ThreatMLTrainer:
    """Trainer class for CyberShield 360 threat classification models."""

    def __init__(self):
        os.makedirs(DATASETS_DIR, exist_ok=True)
        os.makedirs(MODELS_DIR, exist_ok=True)

    def train_url_model(self) -> dict:
        """Train Random Forest model on URL threat dataset."""
        dataset_path = os.path.join(DATASETS_DIR, "url_threats_dataset.csv")
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"URL dataset not found at {dataset_path}")

        df = pd.read_csv(dataset_path)
        print(f"[URL Model] Loaded {len(df)} samples from dataset.")

        X = np.array([extract_url_features(url) for url in df["url"]])
        y = df["label"].values

        # Split into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )

        model = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"[URL Model] Accuracy: {acc * 100:.2f}%")

        model_path = os.path.join(MODELS_DIR, "url_rf_model.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
        print(f"[URL Model] Saved trained model to {model_path}")

        return {
            "dataset_size": len(df),
            "accuracy": round(float(acc), 4),
            "model_path": model_path
        }

    def train_text_model(self) -> dict:
        """Train TF-IDF + Classifier model on text threat dataset."""
        dataset_path = os.path.join(DATASETS_DIR, "text_threats_dataset.csv")
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Text dataset not found at {dataset_path}")

        df = pd.read_csv(dataset_path)
        print(f"[Text Model] Loaded {len(df)} samples from dataset.")

        X = df["text"].values
        y = df["label"].values

        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words="english")),
            ("clf", LogisticRegression(C=1.5, max_iter=200, random_state=42))
        ])

        # Train on entire dataset for maximum vocabulary & coverage
        pipeline.fit(X, y)

        y_pred = pipeline.predict(X)
        acc = accuracy_score(y, y_pred)
        print(f"[Text Model] Training Accuracy: {acc * 100:.2f}%")

        model_path = os.path.join(MODELS_DIR, "text_threat_model.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(pipeline, f)
        print(f"[Text Model] Saved trained model to {model_path}")

        return {
            "dataset_size": len(df),
            "accuracy": round(float(acc), 4),
            "model_path": model_path
        }

    def train_all(self) -> dict:
        url_res = self.train_url_model()
        text_res = self.train_text_model()
        return {
            "url_model": url_res,
            "text_model": text_res,
            "status": "success"
        }


def run_training():
    trainer = ThreatMLTrainer()
    print("==========================================")
    print(" CyberShield 360 ML Model Training ")
    print("==========================================")
    url_res = trainer.train_url_model()
    text_res = trainer.train_text_model()
    print("\nTraining completed successfully!")
    return {"url": url_res, "text": text_res}


if __name__ == "__main__":
    run_training()
