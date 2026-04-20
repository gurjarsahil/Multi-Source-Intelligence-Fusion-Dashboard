"""
Anomaly Detection Module — Isolation Forest.
Detects unusual patterns and abnormal behavior in intelligence data.
"""

import numpy as np
from typing import Dict, List, Optional

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class AnomalyDetector:
    """Isolation Forest-based anomaly detector for intelligence data."""

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.simulation_mode = not SKLEARN_AVAILABLE
        self.model = None
        self.scaler = None

        if SKLEARN_AVAILABLE:
            self.model = IsolationForest(
                contamination=contamination,
                random_state=random_state,
                n_estimators=100,
                max_samples="auto",
            )
            self.scaler = StandardScaler()

    def detect(self, features: List[List[float]], feature_names: Optional[List[str]] = None) -> Dict:
        """
        Detect anomalies in feature data.

        Args:
            features: 2D list of feature vectors
            feature_names: Optional names for each feature dimension

        Returns:
            Dict with per-sample results, summary, and model info
        """
        if not features or len(features) == 0:
            return {"results": [], "total_anomalies": 0, "model": "isolation_forest"}

        if self.simulation_mode:
            return self._simulate_detection(features, feature_names)

        try:
            data = np.array(features, dtype=np.float64)

            # Scale features
            scaled_data = self.scaler.fit_transform(data)

            # Fit and predict
            predictions = self.model.fit_predict(scaled_data)
            scores = self.model.decision_function(scaled_data)

            # Normalize scores to [0, 1] range (higher = more anomalous)
            min_score = scores.min()
            max_score = scores.max()
            if max_score - min_score > 0:
                normalized_scores = 1 - (scores - min_score) / (max_score - min_score)
            else:
                normalized_scores = np.full_like(scores, 0.5)

            results = []
            for i in range(len(features)):
                is_anomaly = predictions[i] == -1
                results.append({
                    "index": i,
                    "is_anomaly": bool(is_anomaly),
                    "anomaly_score": round(float(normalized_scores[i]), 4),
                    "raw_score": round(float(scores[i]), 4),
                    "features": features[i],
                    "feature_names": feature_names if feature_names else [f"f{j}" for j in range(len(features[i]))],
                })

            total_anomalies = int(np.sum(predictions == -1))

            return {
                "results": results,
                "total_anomalies": total_anomalies,
                "total_samples": len(features),
                "anomaly_rate": round(total_anomalies / len(features), 4),
                "model": "isolation_forest",
                "simulation": False,
            }

        except Exception as e:
            return {"error": str(e), "results": [], "total_anomalies": 0, "model": "isolation_forest"}

    def _simulate_detection(self, features: List[List[float]], feature_names: Optional[List[str]] = None) -> Dict:
        """Simulate anomaly detection when sklearn is unavailable."""
        import random
        results = []
        total_anomalies = 0

        for i, feat in enumerate(features):
            # Simple heuristic: values far from mean are "anomalies"
            mean_val = sum(feat) / len(feat) if feat else 0
            deviation = sum(abs(f - mean_val) for f in feat) / len(feat) if feat else 0
            score = min(deviation / 10.0, 1.0)  # Normalize
            score = score + random.uniform(-0.1, 0.1)
            score = max(0.0, min(1.0, score))
            is_anomaly = score > 0.65

            if is_anomaly:
                total_anomalies += 1

            results.append({
                "index": i,
                "is_anomaly": is_anomaly,
                "anomaly_score": round(score, 4),
                "raw_score": round(-score, 4),
                "features": feat,
                "feature_names": feature_names if feature_names else [f"f{j}" for j in range(len(feat))],
            })

        return {
            "results": results,
            "total_anomalies": total_anomalies,
            "total_samples": len(features),
            "anomaly_rate": round(total_anomalies / max(len(features), 1), 4),
            "model": "isolation_forest (simulated)",
            "simulation": True,
        }
