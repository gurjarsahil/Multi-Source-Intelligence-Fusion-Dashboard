"""
AI Module Routes — CV, NLP, Anomaly Detection, and Clustering endpoints.
"""

import os
import json
from fastapi import APIRouter, HTTPException, Depends
from backend.auth import get_current_user, require_role
from backend.database import get_db
from backend.models.schemas import (
    NLPAnalysisRequest, AnomalyRequest, ClusteringRequest,
)
from ai_engine.cv.detector import CVDetector
from ai_engine.nlp.analyzer import NLPAnalyzer
from ai_engine.anomaly.detector import AnomalyDetector
from ai_engine.clustering.clusterer import IntelClusterer
from backend.services.intelligence import IntelligenceService

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])

cv_detector = CVDetector()
nlp_analyzer = NLPAnalyzer()
anomaly_detector = AnomalyDetector()
clusterer = IntelClusterer()


@router.post("/cv/detect")
async def cv_detect(data_id: int = None, current_user: dict = Depends(get_current_user)):
    """Run YOLOv8 object detection on an uploaded image."""
    if data_id:
        db = await get_db()
        try:
            cursor = await db.execute("SELECT raw_file FROM intelligence_data WHERE id = ?", (data_id,))
            row = await cursor.fetchone()
            if not row or not row[0]:
                raise HTTPException(status_code=404, detail="Image not found")
            image_path = row[0]
        finally:
            await db.close()
    else:
        image_path = "simulation"
    result = cv_detector.detect(image_path)
    if data_id:
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO ai_predictions (data_id, model, prediction, confidence, details) VALUES (?, ?, ?, ?, ?)",
                (data_id, "yolov8", f"objects:{result.get('total_objects', 0)}",
                 result.get('threat_objects', 0) / max(result.get('total_objects', 1), 1), json.dumps(result)))
            await db.commit()
        finally:
            await db.close()
    return result


@router.post("/nlp/analyze")
async def nlp_analyze(request: NLPAnalysisRequest, current_user: dict = Depends(get_current_user)):
    """Analyze text for threat indicators using DistilBERT."""
    return nlp_analyzer.analyze(request.text)


@router.post("/anomaly")
async def detect_anomalies(request: AnomalyRequest, current_user: dict = Depends(get_current_user)):
    """Detect anomalies using Isolation Forest."""
    if not request.features or len(request.features) < 2:
        raise HTTPException(status_code=400, detail="At least 2 feature vectors required")
    return anomaly_detector.detect(request.features, request.feature_names)


@router.post("/clustering")
async def cluster_data(request: ClusteringRequest, current_user: dict = Depends(get_current_user)):
    """Cluster geospatial coordinates to identify hotspots."""
    if not request.coordinates or len(request.coordinates) < 2:
        raise HTTPException(status_code=400, detail="At least 2 coordinate pairs required")
    return clusterer.cluster(request.coordinates, request.algorithm, request.params)


@router.post("/process/{data_id}")
async def process_intelligence(data_id: int, current_user: dict = Depends(require_role("analyst"))):
    """Run full AI pipeline on a single intelligence record."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM intelligence_data WHERE id = ?", (data_id,))
        record = await cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        data_content = json.loads(record[6]) if record[6] else {}
        text = data_content.get("description", json.dumps(data_content))
        nlp_result = nlp_analyzer.analyze(text)
        risk_result = IntelligenceService.compute_risk_score(
            anomaly_score=0.5, threat_score=nlp_result["confidence"], cluster_density=0.3)
        results = {"nlp": nlp_result, "risk": risk_result}

        alert = IntelligenceService.generate_alert(
            risk_result, data_id=data_id, latitude=record[4], longitude=record[5], context=text[:200])
        if alert:
            await db.execute(
                "INSERT INTO alerts (type, severity, title, description, latitude, longitude, risk_score, data_id) VALUES (?,?,?,?,?,?,?,?)",
                (alert["type"], alert["severity"], alert["title"], alert["description"],
                 alert.get("latitude"), alert.get("longitude"), alert["risk_score"], data_id))
            results["alert"] = alert

        await db.execute(
            "INSERT INTO ai_predictions (data_id, model, prediction, confidence, details) VALUES (?,?,?,?,?)",
            (data_id, "ensemble", nlp_result["label"], risk_result["risk_score"], json.dumps(results)))
        await db.execute("UPDATE intelligence_data SET status = 'processed' WHERE id = ?", (data_id,))
        await db.commit()
        return results
    finally:
        await db.close()
