"""
Intelligence Data Routes — CRUD, map data, and dashboard stats.
"""

import json
from fastapi import APIRouter, Depends, Query
from backend.auth import get_current_user
from backend.database import get_db

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.get("/data")
async def get_intelligence_data(
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    type: str = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get paginated intelligence records."""
    db = await get_db()
    try:
        if type:
            cursor = await db.execute(
                "SELECT * FROM intelligence_data WHERE type = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (type, limit, offset)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM intelligence_data ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
        rows = await cursor.fetchall()
        records = []
        for r in rows:
            data_val = r[6]
            try:
                data_val = json.loads(r[6]) if r[6] else {}
            except Exception:
                pass
            records.append({
                "id": r[0], "source": r[1], "type": r[2],
                "timestamp": r[3], "latitude": r[4], "longitude": r[5],
                "data": data_val, "raw_file": r[7], "status": r[8],
            })

        count_cursor = await db.execute("SELECT COUNT(*) FROM intelligence_data")
        total = (await count_cursor.fetchone())[0]
        return {"records": records, "total": total, "limit": limit, "offset": offset}
    finally:
        await db.close()


@router.get("/map")
async def get_map_data(current_user: dict = Depends(get_current_user)):
    """Get all geospatial data for map rendering."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT idata.id, idata.source, idata.type, idata.timestamp, idata.latitude, idata.longitude,
                      idata.data, ap.prediction, ap.confidence, ap.details
               FROM intelligence_data idata
               LEFT JOIN ai_predictions ap ON ap.data_id = idata.id
               WHERE idata.latitude IS NOT NULL AND idata.longitude IS NOT NULL
               ORDER BY idata.timestamp DESC LIMIT 500"""
        )
        rows = await cursor.fetchall()
        points = []
        for r in rows:
            details = {}
            try:
                details = json.loads(r[9]) if r[9] else {}
            except Exception:
                pass
            data_val = {}
            try:
                data_val = json.loads(r[6]) if r[6] else {}
            except Exception:
                pass
            points.append({
                "id": r[0], "source": r[1], "type": r[2], "timestamp": r[3],
                "lat": r[4], "lon": r[5], "data": data_val,
                "prediction": r[7], "confidence": r[8],
                "risk_score": details.get("risk", {}).get("risk_score", r[8] or 0),
                "severity": details.get("risk", {}).get("severity", "low"),
            })

        alerts_cursor = await db.execute(
            "SELECT id, type, severity, title, latitude, longitude, risk_score FROM alerts WHERE latitude IS NOT NULL LIMIT 200"
        )
        alert_rows = await alerts_cursor.fetchall()
        alerts = [
            {"id": a[0], "type": a[1], "severity": a[2], "title": a[3], "lat": a[4], "lon": a[5], "risk_score": a[6]}
            for a in alert_rows if a[4] and a[5]
        ]

        return {"points": points, "alerts": alerts, "total_points": len(points)}
    finally:
        await db.close()


@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard summary statistics."""
    db = await get_db()
    try:
        total_intel = (await (await db.execute("SELECT COUNT(*) FROM intelligence_data")).fetchone())[0]
        total_alerts = (await (await db.execute("SELECT COUNT(*) FROM alerts")).fetchone())[0]
        critical_alerts = (await (await db.execute("SELECT COUNT(*) FROM alerts WHERE severity = 'critical'")).fetchone())[0]
        active_threats = (await (await db.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = 0")).fetchone())[0]

        avg_row = await (await db.execute("SELECT AVG(risk_score) FROM alerts")).fetchone()
        avg_risk = round(avg_row[0] or 0.0, 3)

        type_cursor = await db.execute("SELECT type, COUNT(*) FROM intelligence_data GROUP BY type")
        data_by_type = {r[0]: r[1] for r in await type_cursor.fetchall()}

        sev_cursor = await db.execute("SELECT severity, COUNT(*) FROM alerts GROUP BY severity")
        alerts_by_severity = {r[0]: r[1] for r in await sev_cursor.fetchall()}

        recent_cursor = await db.execute(
            "SELECT id, source, type, timestamp, status FROM intelligence_data ORDER BY timestamp DESC LIMIT 10"
        )
        recent = [{"id": r[0], "source": r[1], "type": r[2], "timestamp": r[3], "status": r[4]}
                  for r in await recent_cursor.fetchall()]

        return {
            "total_intelligence": total_intel,
            "total_alerts": total_alerts,
            "critical_alerts": critical_alerts,
            "active_threats": active_threats,
            "avg_risk_score": avg_risk,
            "data_by_type": data_by_type,
            "alerts_by_severity": alerts_by_severity,
            "recent_activity": recent,
        }
    finally:
        await db.close()
