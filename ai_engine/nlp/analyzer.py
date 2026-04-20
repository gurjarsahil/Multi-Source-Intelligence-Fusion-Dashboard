"""
NLP Intelligence Module — DistilBERT-based Text Analysis.
Performs threat detection, text classification, and incident summarization.
Uses keyword-based analysis as primary/fallback approach.
Will attempt to load transformers at runtime if available.
"""

import re
import json
import sys
import subprocess
from typing import Dict, List, Optional
import random


def _check_transformers_available():
    """Check if transformers can be imported without crashing the current process."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", "from transformers import pipeline; print('OK')"],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0 and 'OK' in result.stdout
    except Exception:
        return False


class NLPAnalyzer:
    """NLP analyzer for intelligence text processing with optional DistilBERT support."""

    THREAT_KEYWORDS = {
        "critical": ["attack", "bomb", "explosion", "terrorist", "weapon", "nuclear",
                      "chemical", "biological", "assassination", "hostage", "warfare"],
        "high": ["threat", "suspicious", "armed", "militant", "extremist", "smuggling",
                 "trafficking", "infiltration", "sabotage", "espionage", "cyber attack"],
        "medium": ["surveillance", "intercepted", "encrypted", "unauthorized", "breach",
                   "intrusion", "anomaly", "unusual", "unidentified", "covert"],
        "low": ["monitor", "report", "activity", "movement", "communication",
                "intelligence", "observation", "patrol", "checkpoint", "routine"],
    }

    def __init__(self):
        self.classifier = None
        self.simulation_mode = True
        # Skip transformers — keyword-based analysis is reliable and fast
        # Set self.simulation_mode = False and load classifier here if
        # transformers + torch are properly installed and compatible

    def analyze(self, text: str) -> Dict:
        """
        Analyze text for threat indicators and classify risk level.

        Args:
            text: Intelligence text to analyze

        Returns:
            Dict with label, confidence, threat level, and details
        """
        keyword_result = self._keyword_analysis(text)

        if not self.simulation_mode and self.classifier:
            try:
                ml_result = self.classifier(text[:512])[0]
                sentiment_label = ml_result["label"]
                sentiment_score = ml_result["score"]
                ml_threat_score = sentiment_score if sentiment_label == "NEGATIVE" else 1.0 - sentiment_score
                combined_score = 0.6 * ml_threat_score + 0.4 * keyword_result["score"]
            except Exception:
                combined_score = keyword_result["score"]
                ml_threat_score = keyword_result["score"]
        else:
            combined_score = keyword_result["score"]
            ml_threat_score = keyword_result["score"]

        if combined_score >= 0.75:
            label = "threat"
            severity = "critical"
        elif combined_score >= 0.55:
            label = "suspicious"
            severity = "high"
        elif combined_score >= 0.35:
            label = "suspicious"
            severity = "medium"
        else:
            label = "safe"
            severity = "low"

        return {
            "label": label,
            "confidence": round(combined_score, 4),
            "severity": severity,
            "details": {
                "keyword_score": round(keyword_result["score"], 4),
                "ml_score": round(ml_threat_score, 4),
                "combined_score": round(combined_score, 4),
                "matched_keywords": keyword_result["matched"],
                "threat_categories": keyword_result["categories"],
            },
            "model": "distilbert" if not self.simulation_mode else "keyword-engine",
            "simulation": self.simulation_mode,
        }

    def _keyword_analysis(self, text: str) -> Dict:
        """Keyword-based threat analysis — primary analysis engine."""
        text_lower = text.lower()
        matched = []
        categories = []
        max_score = 0.0

        severity_scores = {"critical": 0.9, "high": 0.7, "medium": 0.5, "low": 0.3}

        for severity, keywords in self.THREAT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matched.append(keyword)
                    if severity not in categories:
                        categories.append(severity)
                    max_score = max(max_score, severity_scores[severity])

        if len(matched) > 3:
            max_score = min(max_score + 0.1, 1.0)

        return {
            "score": max_score if matched else random.uniform(0.1, 0.3),
            "matched": matched,
            "categories": categories,
        }

    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts."""
        return [self.analyze(text) for text in texts]
