"""
Database module — SQLite with async support via aiosqlite.
Handles connection management, schema initialization, and demo data seeding.
"""

import aiosqlite
import os
import json
from datetime import datetime, timedelta
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "intelligence.db")


async def get_db():
    """Get async database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    """Initialize database schema and seed demo data."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await get_db()
    try:
        # ─── Users Table ───────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ─── Intelligence Data Table ───────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS intelligence_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                type TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                latitude REAL,
                longitude REAL,
                data TEXT,
                raw_file TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)

        # ─── AI Predictions Table ──────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_id INTEGER,
                model TEXT NOT NULL,
                prediction TEXT NOT NULL,
                confidence REAL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (data_id) REFERENCES intelligence_data(id)
            )
        """)

        # ─── Alerts Table ─────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'low',
                title TEXT NOT NULL,
                description TEXT,
                latitude REAL,
                longitude REAL,
                risk_score REAL,
                data_id INTEGER,
                acknowledged INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (data_id) REFERENCES intelligence_data(id)
            )
        """)

        # ─── Indexes ──────────────────────────────────────
        await db.execute("CREATE INDEX IF NOT EXISTS idx_intel_type ON intelligence_data(type)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_intel_timestamp ON intelligence_data(timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_predictions_data ON ai_predictions(data_id)")

        await db.commit()

        # ─── Seed demo data if empty ──────────────────────
        cursor = await db.execute("SELECT COUNT(*) FROM intelligence_data")
        row = await cursor.fetchone()
        if row[0] == 0:
            await seed_demo_data(db)

    finally:
        await db.close()


async def seed_demo_data(db):
    """Seed the database with realistic demo intelligence data."""
    from passlib.hash import bcrypt

    # Create default admin user
    hashed_pw = bcrypt.hash("admin123")
    await db.execute(
        "INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        ("Admin", "admin@intel.local", hashed_pw, "admin")
    )

    # Demo intelligence locations (major global hotspots)
    locations = [
        {"lat": 33.8938, "lon": 35.5018, "city": "Beirut"},
        {"lat": 36.2021, "lon": 37.1343, "city": "Aleppo"},
        {"lat": 41.0082, "lon": 28.9784, "city": "Istanbul"},
        {"lat": 38.7223, "lon": -9.1393, "city": "Lisbon"},
        {"lat": 48.8566, "lon": 2.3522, "city": "Paris"},
        {"lat": 51.5074, "lon": -0.1278, "city": "London"},
        {"lat": 40.4168, "lon": -3.7038, "city": "Madrid"},
        {"lat": 52.5200, "lon": 13.4050, "city": "Berlin"},
        {"lat": 34.0522, "lon": -118.2437, "city": "Los Angeles"},
        {"lat": 28.6139, "lon": 77.2090, "city": "New Delhi"},
        {"lat": 35.6762, "lon": 139.6503, "city": "Tokyo"},
        {"lat": -33.8688, "lon": 151.2093, "city": "Sydney"},
        {"lat": 55.7558, "lon": 37.6173, "city": "Moscow"},
        {"lat": 39.9042, "lon": 116.4074, "city": "Beijing"},
        {"lat": 1.3521, "lon": 103.8198, "city": "Singapore"},
    ]

    report_types = ["SIGINT", "HUMINT", "OSINT", "GEOINT", "CYBINT"]
    severities = ["low", "medium", "high", "critical"]
    threat_descriptions = [
        "Suspicious communications intercepted in sector",
        "Unusual vehicle movement pattern detected near checkpoint",
        "Cyber intrusion attempt originating from region",
        "Unidentified drone activity in restricted airspace",
        "Increased encrypted radio traffic in urban zone",
        "Supply chain disruption reported at critical infrastructure",
        "Abnormal financial transactions flagged by monitoring system",
        "Personnel movement inconsistent with known patterns",
        "Electromagnetic anomaly detected near military installation",
        "Social media chatter indicates potential coordinated action",
    ]

    now = datetime.utcnow()

    for i in range(50):
        loc = random.choice(locations)
        # Add some random offset to coordinates
        lat = loc["lat"] + random.uniform(-0.5, 0.5)
        lon = loc["lon"] + random.uniform(-0.5, 0.5)
        report_type = random.choice(report_types)
        timestamp = now - timedelta(hours=random.randint(0, 72))
        description = random.choice(threat_descriptions)
        severity = random.choice(severities)

        data_json = json.dumps({
            "city": loc["city"],
            "report_type": report_type,
            "description": f"{description} near {loc['city']}",
            "severity": severity,
            "source_reliability": random.choice(["A", "B", "C", "D"]),
            "info_credibility": random.randint(1, 6),
        })

        await db.execute(
            """INSERT INTO intelligence_data (source, type, timestamp, latitude, longitude, data, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (f"SRC-{random.randint(100,999)}", report_type, timestamp.isoformat(),
             lat, lon, data_json, "processed")
        )

        # Create corresponding predictions
        anomaly_score = random.uniform(0.1, 0.95)
        threat_score = random.uniform(0.1, 0.95)
        cluster_density = random.uniform(0.1, 0.8)
        risk_score = 0.4 * anomaly_score + 0.4 * threat_score + 0.2 * cluster_density

        await db.execute(
            """INSERT INTO ai_predictions (data_id, model, prediction, confidence, details)
               VALUES (?, ?, ?, ?, ?)""",
            (i + 1, "ensemble",
             "threat" if risk_score > 0.6 else ("suspicious" if risk_score > 0.4 else "safe"),
             risk_score,
             json.dumps({
                 "anomaly_score": round(anomaly_score, 3),
                 "threat_score": round(threat_score, 3),
                 "cluster_density": round(cluster_density, 3),
                 "risk_score": round(risk_score, 3),
             }))
        )

        # Create alerts for high-risk items
        if risk_score > 0.6:
            alert_type = "threat" if threat_score > 0.7 else "anomaly"
            await db.execute(
                """INSERT INTO alerts (type, severity, title, description, latitude, longitude, risk_score, data_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (alert_type, severity,
                 f"{report_type} Alert: {loc['city']}",
                 f"{description} near {loc['city']}. Risk score: {risk_score:.2f}",
                 lat, lon, risk_score, i + 1)
            )

    await db.commit()
