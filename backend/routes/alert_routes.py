"""
Alerts Routes — Get, acknowledge, and manage intelligence alerts.
"""

import json
from fastapi import APIRouter, Depends, Query, HTTPException
from backend.auth import get_current_user, require_role
from backend.database import get_db

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
async def get_alerts(
    limit: int = Query(50, le=200),
    severity: str = Query(None),
    unacknowledged_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
):
    """Get alerts with optional filtering."""
    db = await get_db()
    try:
        conditions = []
        params = []
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if unacknowledged_only:
            conditions.append("acknowledged = 0")
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        cursor = await db.execute(
            f"SELECT * FROM alerts {where} ORDER BY created_at DESC LIMIT ?", params
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "type": r[1], "severity": r[2], "title": r[3],
             "description": r[4], "latitude": r[5], "longitude": r[6],
             "risk_score": r[7], "data_id": r[8], "acknowledged": bool(r[9]), "created_at": r[10]}
            for r in rows
        ]
    finally:
        await db.close()


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, current_user: dict = Depends(require_role("analyst"))):
    """Acknowledge an alert."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM alerts WHERE id = ?", (alert_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Alert not found")
        await db.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
        await db.commit()
        return {"message": "Alert acknowledged", "alert_id": alert_id}
    finally:
        await db.close()


@router.get("/summary")
async def alerts_summary(current_user: dict = Depends(get_current_user)):
    """Get alert count summary by severity."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT severity, COUNT(*) as count, SUM(CASE WHEN acknowledged=0 THEN 1 ELSE 0 END) as unack FROM alerts GROUP BY severity"
        )
        rows = await cursor.fetchall()
        return {r[0]: {"total": r[1], "unacknowledged": r[2]} for r in rows}
    finally:
        await db.close()
