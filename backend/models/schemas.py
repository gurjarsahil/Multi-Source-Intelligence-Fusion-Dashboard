"""
Pydantic schemas for request/response validation across all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ─── Auth Schemas ──────────────────────────────────────

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    role: str = Field(default="viewer", pattern="^(admin|analyst|viewer)$")


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str


# ─── Intelligence Data Schemas ─────────────────────────

class IntelligenceDataCreate(BaseModel):
    source: str
    type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    data: Optional[dict] = None


class IntelligenceDataResponse(BaseModel):
    id: int
    source: str
    type: str
    timestamp: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    data: Optional[Any] = None
    status: Optional[str] = None


# ─── AI Prediction Schemas ─────────────────────────────

class CVDetectionRequest(BaseModel):
    image_path: Optional[str] = None


class CVDetectionResponse(BaseModel):
    detections: List[dict]
    total_objects: int
    model: str = "yolov8n"


class NLPAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1)


class NLPAnalysisResponse(BaseModel):
    label: str
    confidence: float
    details: Optional[dict] = None
    model: str = "distilbert"


class AnomalyRequest(BaseModel):
    features: List[List[float]]
    feature_names: Optional[List[str]] = None


class AnomalyResponse(BaseModel):
    results: List[dict]
    total_anomalies: int
    model: str = "isolation_forest"


class ClusteringRequest(BaseModel):
    coordinates: List[List[float]]
    algorithm: str = Field(default="dbscan", pattern="^(dbscan|kmeans)$")
    params: Optional[dict] = None


class ClusteringResponse(BaseModel):
    clusters: List[dict]
    hotspots: List[dict]
    total_clusters: int
    algorithm: str


# ─── Alert Schemas ─────────────────────────────────────

class AlertResponse(BaseModel):
    id: int
    type: str
    severity: str
    title: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    risk_score: Optional[float] = None
    acknowledged: bool = False
    created_at: Optional[str] = None


# ─── Dashboard Schemas ─────────────────────────────────

class DashboardStats(BaseModel):
    total_intelligence: int
    total_alerts: int
    critical_alerts: int
    active_threats: int
    avg_risk_score: float
    data_by_type: dict
    alerts_by_severity: dict
    recent_activity: List[dict]


class MapDataResponse(BaseModel):
    points: List[dict]
    clusters: List[dict]
    alerts: List[dict]
