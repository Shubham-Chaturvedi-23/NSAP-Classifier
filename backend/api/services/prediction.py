"""
Module: api/services/prediction.py
Description: CatBoost model loading and inference service.
             Handles feature engineering, scheme prediction,
             confidence thresholding and SHAP explanations.
"""

import json
import pickle
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from fastapi import HTTPException

from api.config import (
    ALL_FEATURES, CAT_FEATURES,
    CONF_THRESHOLD, PRIORITY_ORDER,
    CATBOOST_MODEL_PATH, LABEL_ENCODER_PATH,
    FEATURE_COLUMNS_PATH, SCHEME_LABELS,
    SCHEME_LABELS_HI, engineer_features,
)

# ─── Global Model State ───────────────────────────────────────
# Loaded once on startup via load_model_artifacts()
# and reused across all requests.
_model    = None
_encoder  = None
_features = None


# ─── Startup Loader ───────────────────────────────────────────
def load_model_artifacts():
    """
    Load CatBoost model, label encoder and feature columns from disk.
    Called once during FastAPI application startup in app.py lifespan.

    Raises:
        RuntimeError: If any model artifact file is missing or corrupt.
    """
    global _model, _encoder, _features

    # Load CatBoost model
    try:
        _model = CatBoostClassifier()
        _model.load_model(str(CATBOOST_MODEL_PATH))
        print(f"✅ CatBoost model loaded from {CATBOOST_MODEL_PATH.name}")
    except Exception as e:
        raise RuntimeError(f"Failed to load CatBoost model: {e}")

    # Load label encoder
    try:
        with open(LABEL_ENCODER_PATH, "rb") as f:
            _encoder = pickle.load(f)
        print(f"✅ Label encoder loaded — classes: {list(_encoder.classes_)}")
    except Exception as e:
        raise RuntimeError(f"Failed to load label encoder: {e}")

    # Load feature columns
    try:
        with open(FEATURE_COLUMNS_PATH, "rb") as f:
            _features = pickle.load(f)
        print(f"✅ Feature columns loaded — {len(_features)} features")
    except Exception as e:
        raise RuntimeError(f"Failed to load feature columns: {e}")


# ─── Model Getter ─────────────────────────────────────────────
def get_model():
    """
    Return loaded model artifacts.
    Raises HTTP 503 if model not loaded yet.

    Returns:
        tuple: (CatBoostClassifier, LabelEncoder, list of feature names)
    """
    if _model is None or _encoder is None or _features is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Check server startup logs."
        )
    return _model, _encoder, _features


# ─── Core Prediction ──────────────────────────────────────────
def run_prediction(applicant_data: dict) -> dict:
    """
    Run full inference pipeline on a single applicant.

    Pipeline:
        1. Engineer interaction features
        2. Select and order features
        3. Run CatBoost inference
        4. Apply priority-based scheme selection
        5. Compute SHAP values for explainability

    Args:
        applicant_data (dict): Raw applicant fields matching
                               training feature set.

    Returns:
        dict: {
            predicted_scheme    (str),
            scheme_full_name    (str),
            scheme_full_name_hi (str),
            confidence_score    (float),
            needs_review        (bool),
            all_probabilities   (dict),
            shap_values         (dict or None)
        }

    Raises:
        HTTPException 503: If model not loaded.
        HTTPException 400: If required features are missing.
    """
    model, encoder, features = get_model()

    # Step 1 — Build DataFrame and engineer features
    try:
        df = pd.DataFrame([applicant_data])
        df = engineer_features(df)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Feature engineering failed: {e}"
        )

    # Step 2 — Validate all required features are present
    missing = [f for f in ALL_FEATURES if f not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required features: {missing}"
        )

    # Step 3 — Select features in exact training order
    df_input = df[ALL_FEATURES]

    # Step 4 — Run inference
    try:
        proba   = model.predict_proba(df_input)[0]
        classes = list(encoder.classes_)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model inference failed: {e}"
        )

    # Step 5 — Priority-based scheme selection
    # Collect all schemes above confidence threshold
    qualifying = [
        classes[i] for i, p in enumerate(proba)
        if p >= CONF_THRESHOLD and classes[i] != "NOT_ELIGIBLE"
    ]

    # Pick first match by NSAP priority order (WP > DP > OAP)
    predicted  = "NOT_ELIGIBLE"
    confidence = float(np.max(proba))

    for scheme in PRIORITY_ORDER:
        if scheme in qualifying:
            predicted  = scheme
            confidence = float(proba[classes.index(scheme)])
            break

    # Step 6 — SHAP values for explainability
    shap_values = _compute_shap(df_input, predicted, classes)

    return {
        "predicted_scheme":    predicted,
        "scheme_full_name":    SCHEME_LABELS.get(predicted, ""),
        "scheme_full_name_hi": SCHEME_LABELS_HI.get(predicted, ""),
        "confidence_score":    round(confidence, 4),
        "needs_review":        confidence < CONF_THRESHOLD,
        "all_probabilities":   {
            cls: round(float(p), 4)
            for cls, p in zip(classes, proba)
        },
        "shap_values": shap_values,
    }


# ─── SHAP Explainability ──────────────────────────────────────
def _compute_shap(df_input: pd.DataFrame,
                  predicted_scheme: str,
                  classes: list) -> dict:
    """
    Compute SHAP feature contributions for the predicted scheme.
    Returns top 6 most influential features for officer review.

    Args:
        df_input (pd.DataFrame): Preprocessed input features.
        predicted_scheme (str):  The predicted scheme code.
        classes (list):          List of class names from encoder.

    Returns:
        dict: {feature_name: shap_value} for top 6 features,
              or None if SHAP computation fails.
    """
    try:
        import shap
        model, _, _ = get_model()

        explainer = shap.TreeExplainer(model)
        raw_vals = explainer.shap_values(df_input)
        class_idx = classes.index(predicted_scheme)

        # SHAP output shape varies by version/model:
        # - ndarray (n_samples, n_features, n_classes)
        # - ndarray (n_samples, n_features)
        # - list[class] of (n_samples, n_features)
        shap_for_class = None
        if isinstance(raw_vals, np.ndarray):
            if raw_vals.ndim == 3:
                shap_for_class = raw_vals[0, :, class_idx]
            elif raw_vals.ndim == 2:
                shap_for_class = raw_vals[0, :]
        elif isinstance(raw_vals, list) and raw_vals:
            if class_idx < len(raw_vals):
                shap_for_class = np.asarray(raw_vals[class_idx])[0]

        if shap_for_class is None:
            return None

        feature_names = list(df_input.columns)
        feature_shap = dict(zip(feature_names, np.asarray(shap_for_class).tolist()))

        top_features = sorted(
            feature_shap.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:8]

        return {k: round(float(v), 4) for k, v in top_features}

    except Exception:
        # SHAP is best-effort — don't fail prediction if it errors.
        return None


# ─── Batch Prediction ─────────────────────────────────────────
def run_batch_prediction(applicants: list[dict]) -> list[dict]:
    """
    Run inference on a list of applicants.
    Returns list of prediction results in same order as input.

    Args:
        applicants (list[dict]): List of raw applicant data dicts.

    Returns:
        list[dict]: List of prediction result dicts.
    """
    return [run_prediction(applicant) for applicant in applicants]


# ─── Model Info ───────────────────────────────────────────────
def get_model_info() -> dict:
    """
    Return basic model metadata for health check and admin dashboard.

    Returns:
        dict: model type, class names, feature count, threshold.
    """
    _, encoder, features = get_model()
    return {
        "model_type":    "CatBoost",
        "classes":       list(encoder.classes_),
        "feature_count": len(features),
        "conf_threshold": CONF_THRESHOLD,
        "priority_order": PRIORITY_ORDER,
    }