"""
Intelligence Service — Core business logic for risk scoring, alerting, and data processing.
"""

import json
import random
from typing import Dict, List, Optional
from datetime import datetime


class IntelligenceService:
    """Central intelligence processing and risk scoring engine."""

    # Risk formula weights
    ANOMALY_WEIGHT = 0.4
    THREAT_WEIGHT = 0.4
    CLUSTER_WEIGHT = 0.2

    # Thresholds
    ALERT_THRESHOLD = 0.55
    CRITICAL_THRESHOLD = 0.8

    @staticmethod
    def compute_risk_score(
        anomaly_score: float = 0.0,
        threat_score: float = 0.0,
        cluster_density: float = 0.0,
    ) -> Dict:
        """
        Compute composite risk score using the intelligence fusion formula.

        Risk Score = 0.4 * anomaly_score + 0.4 * threat_score + 0.2 * cluster_density
        """
        risk_score = (
            IntelligenceService.ANOMALY_WEIGHT * anomaly_score
            + IntelligenceService.THREAT_WEIGHT * threat_score
            + IntelligenceService.CLUSTER_WEIGHT * cluster_density
        )
        risk_score = round(min(max(risk_score, 0.0), 1.0), 4)

        if risk_score >= IntelligenceService.CRITICAL_THRESHOLD:
            severity = "critical"
        elif risk_score >= 0.65:
            severity = "high"
        elif risk_score >= IntelligenceService.ALERT_THRESHOLD:
            severity = "medium"
        else:
            severity = "low"

        should_alert = risk_score >= IntelligenceService.ALERT_THRESHOLD

        return {
            "risk_score": risk_score,
            "severity": severity,
            "should_alert": should_alert,
            "components": {
                "anomaly_score": round(anomaly_score, 4),
                "threat_score": round(threat_score, 4),
                "cluster_density": round(cluster_density, 4),
            },
        }

    @staticmethod
    def generate_alert(
        risk_result: Dict,
        data_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        context: str = "",
    ) -> Optional[Dict]:
        """Generate an alert if risk score exceeds threshold."""
        if not risk_result.get("should_alert"):
            return None

        severity = risk_result["severity"]
        risk_score = risk_result["risk_score"]

        alert_type = "threat" if risk_result["components"]["threat_score"] > 0.6 else "anomaly"

        title_map = {
            "critical": f"CRITICAL: High-risk {alert_type} detected",
            "high": f"WARNING: Elevated {alert_type} level",
            "medium": f"NOTICE: Moderate {alert_type} activity",
        }

        return {
            "type": alert_type,
            "severity": severity,
            "title": title_map.get(severity, f"Alert: {alert_type}"),
            "description": f"{context}. Risk score: {risk_score:.2f}. "
                          f"Anomaly: {risk_result['components']['anomaly_score']:.2f}, "
                          f"Threat: {risk_result['components']['threat_score']:.2f}, "
                          f"Cluster: {risk_result['components']['cluster_density']:.2f}",
            "risk_score": risk_score,
            "latitude": latitude,
            "longitude": longitude,
            "data_id": data_id,
            "created_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def process_csv_data(content: str) -> List[Dict]:
        """Parse CSV content into structured intelligence records."""
        import csv
        import io

        records = []
        reader = csv.DictReader(io.StringIO(content))

        for row in reader:
            record = {
                "source": row.get("source", "CSV_UPLOAD"),
                "type": row.get("type", "OSINT"),
                "latitude": float(row["latitude"]) if "latitude" in row and row["latitude"] else None,
                "longitude": float(row["longitude"]) if "longitude" in row and row["longitude"] else None,
                "data": json.dumps({k: v for k, v in row.items() if k not in ("latitude", "longitude")}),
                "timestamp": row.get("timestamp", datetime.utcnow().isoformat()),
            }
            records.append(record)

        return records

    @staticmethod
    def process_json_data(content: dict) -> List[Dict]:
        """Parse JSON content into structured intelligence records."""
        records = []

        # Handle both single record and array
        items = content if isinstance(content, list) else [content]

        for item in items:
            record = {
                "source": item.get("source", "JSON_UPLOAD"),
                "type": item.get("type", "SIGINT"),
                "latitude": item.get("latitude") or item.get("lat"),
                "longitude": item.get("longitude") or item.get("lon"),
                "data": json.dumps(item.get("data", item)),
                "timestamp": item.get("timestamp", datetime.utcnow().isoformat()),
            }
            records.append(record)

        return records
