"""
Data Ingestion Routes — CSV, JSON, and Image upload endpoints.
"""

import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from backend.auth import get_current_user, require_role
from backend.database import get_db
from backend.services.intelligence import IntelligenceService

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")

router = APIRouter(prefix="/upload", tags=["Data Ingestion"])


@router.post("/csv")
async def upload_csv(file: UploadFile = File(...), current_user: dict = Depends(require_role("analyst"))):
    """Upload and process a CSV intelligence file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    text_content = content.decode("utf-8")

    records = IntelligenceService.process_csv_data(text_content)

    db = await get_db()
    try:
        inserted_ids = []
        for record in records:
            cursor = await db.execute(
                """INSERT INTO intelligence_data (source, type, timestamp, latitude, longitude, data, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (record["source"], record["type"], record["timestamp"],
                 record.get("latitude"), record.get("longitude"),
                 record["data"], "pending")
            )
            inserted_ids.append(cursor.lastrowid)
        await db.commit()

        return {
            "message": f"Successfully ingested {len(records)} records from CSV",
            "record_count": len(records),
            "record_ids": inserted_ids,
        }
    finally:
        await db.close()


@router.post("/json")
async def upload_json(file: UploadFile = File(...), current_user: dict = Depends(require_role("analyst"))):
    """Upload and process a JSON intelligence file."""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="File must be a JSON file")

    content = await file.read()
    try:
        json_content = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    records = IntelligenceService.process_json_data(json_content)

    db = await get_db()
    try:
        inserted_ids = []
        for record in records:
            cursor = await db.execute(
                """INSERT INTO intelligence_data (source, type, timestamp, latitude, longitude, data, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (record["source"], record["type"], record["timestamp"],
                 record.get("latitude"), record.get("longitude"),
                 record["data"], "pending")
            )
            inserted_ids.append(cursor.lastrowid)
        await db.commit()

        return {
            "message": f"Successfully ingested {len(records)} records from JSON",
            "record_count": len(records),
            "record_ids": inserted_ids,
        }
    finally:
        await db.close()


@router.post("/image")
async def upload_image(file: UploadFile = File(...), current_user: dict = Depends(require_role("analyst"))):
    """Upload an image for CV analysis."""
    allowed = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported image format. Allowed: {allowed}")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Store reference in DB
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO intelligence_data (source, type, timestamp, data, raw_file, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("IMAGE_UPLOAD", "GEOINT", datetime.utcnow().isoformat(),
             json.dumps({"filename": filename, "original_name": file.filename, "size": len(content)}),
             filepath, "pending")
        )
        await db.commit()
        data_id = cursor.lastrowid

        return {
            "message": "Image uploaded successfully",
            "data_id": data_id,
            "filename": filename,
            "filepath": filepath,
        }
    finally:
        await db.close()
