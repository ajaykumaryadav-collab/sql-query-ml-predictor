import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Tuple

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "trained_models", "best_model.joblib")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "trained_models", "scaler.joblib")

class PredictionService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = [
            "startup_cost", "total_cost", "plan_rows", "plan_width",
            "parallel_aware", "plan_depth", "number_of_plan_nodes",
            "number_of_tables", "number_of_joins", "number_of_filters",
            "number_of_sort_nodes", "number_of_aggregate_nodes",
            "number_of_seq_scans", "number_of_index_scans",
            "number_of_nested_loop_joins", "number_of_hash_joins",
            "number_of_merge_joins",
            "total_scanned_rows", "max_intermediate_rows", "total_tree_cost",
            "has_hash_join", "has_bitmap_scan", "number_of_bitmap_scans",
            "max_plan_width"
        ]

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception:
                pass
        if os.path.exists(SCALER_PATH):
            try:
                self.scaler = joblib.load(SCALER_PATH)
            except Exception:
                pass

    def predict(self, features: Dict[str, float]) -> float:
        if self.model is None:
            self.load_model()
        
        if not self.model:
            # Fallback if no model is trained yet
            return features.get("total_cost", 0.0) * 0.01

        # Use features expected by the specific model version if available
        model_features = getattr(self.model, "feature_names_in_", None)
        if model_features is not None:
            expected_cols = list(model_features)
        else:
            expected_cols = self.feature_columns

        df = pd.DataFrame([features])
        
        # Ensure all required columns exist
        for col in expected_cols:
            if col not in df.columns:
                df[col] = 0.0
                
        df = df[expected_cols]

        if self.scaler:
            X_scaled = self.scaler.transform(df)
        else:
            X_scaled = df

        raw_pred = self.model.predict(X_scaled)[0]
        
        # Check if the model was trained in log-space (log1p)
        is_log = getattr(self.model, "_is_log_target", False)
        if is_log:
            pred_time = float(np.expm1(raw_pred))
        else:
            pred_time = float(raw_pred)
            
        # execution time cannot be negative
        return max(0.01, round(pred_time, 2))

prediction_service = PredictionService()
