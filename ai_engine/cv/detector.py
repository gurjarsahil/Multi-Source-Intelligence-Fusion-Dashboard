"""
Computer Vision Module — YOLOv8 Pretrained Object Detection.
Performs person, vehicle, and general object detection on uploaded images.
Falls back to simulation mode if ultralytics is not installed.
"""

import os
import json
from typing import Dict, List, Optional
import random

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class CVDetector:
    """YOLOv8-based object detector for intelligence imagery analysis."""

    # COCO classes of intelligence interest
    INTEL_CLASSES = {
        0: "person", 1: "bicycle", 2: "car", 3: "motorcycle",
        5: "bus", 7: "truck", 14: "bird", 15: "cat", 16: "dog",
        24: "backpack", 25: "umbrella", 26: "handbag", 27: "tie",
        28: "suitcase", 39: "bottle", 56: "chair", 63: "laptop",
        64: "mouse", 66: "keyboard", 67: "cell phone",
    }

    THREAT_OBJECTS = {"person", "car", "truck", "bus", "motorcycle", "backpack", "suitcase"}

    def __init__(self):
        self.model = None
        self.simulation_mode = not YOLO_AVAILABLE
        if YOLO_AVAILABLE:
            try:
                self.model = YOLO("yolov8n.pt")
                self.simulation_mode = False
            except Exception:
                self.simulation_mode = True

    def detect(self, image_path: str, confidence_threshold: float = 0.25) -> Dict:
        """
        Run object detection on an image.

        Args:
            image_path: Path to the image file
            confidence_threshold: Minimum confidence for detections

        Returns:
            Dict with detections, threat assessment, and metadata
        """
        if self.simulation_mode:
            return self._simulate_detection(image_path)

        if not os.path.exists(image_path):
            return {"error": "Image file not found", "detections": [], "total_objects": 0}

        try:
            results = self.model(image_path, conf=confidence_threshold, verbose=False)
            detections = []

            for result in results:
                boxes = result.boxes
                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i])
                    conf = float(boxes.conf[i])
                    bbox = boxes.xyxy[i].tolist()
                    class_name = result.names.get(cls_id, f"class_{cls_id}")

                    detections.append({
                        "class": class_name,
                        "class_id": cls_id,
                        "confidence": round(conf, 4),
                        "bbox": {
                            "x1": round(bbox[0], 1),
                            "y1": round(bbox[1], 1),
                            "x2": round(bbox[2], 1),
                            "y2": round(bbox[3], 1),
                        },
                        "is_threat_object": class_name in self.THREAT_OBJECTS,
                    })

            # Compute threat assessment
            threat_objects = [d for d in detections if d["is_threat_object"]]
            person_count = len([d for d in detections if d["class"] == "person"])
            vehicle_count = len([d for d in detections if d["class"] in {"car", "truck", "bus", "motorcycle"}])

            return {
                "detections": detections,
                "total_objects": len(detections),
                "threat_objects": len(threat_objects),
                "person_count": person_count,
                "vehicle_count": vehicle_count,
                "model": "yolov8n",
                "simulation": False,
            }

        except Exception as e:
            return {"error": str(e), "detections": [], "total_objects": 0, "model": "yolov8n"}

    def _simulate_detection(self, image_path: str) -> Dict:
        """Generate realistic simulated detections when YOLO is unavailable."""
        sim_objects = [
            {"class": "person", "confidence": 0.92, "bbox": {"x1": 120, "y1": 80, "x2": 220, "y2": 380}},
            {"class": "car", "confidence": 0.87, "bbox": {"x1": 300, "y1": 200, "x2": 550, "y2": 400}},
            {"class": "person", "confidence": 0.78, "bbox": {"x1": 450, "y1": 100, "x2": 530, "y2": 350}},
            {"class": "backpack", "confidence": 0.65, "bbox": {"x1": 140, "y1": 150, "x2": 200, "y2": 250}},
            {"class": "truck", "confidence": 0.81, "bbox": {"x1": 50, "y1": 250, "x2": 280, "y2": 420}},
            {"class": "cell phone", "confidence": 0.55, "bbox": {"x1": 190, "y1": 200, "x2": 210, "y2": 240}},
        ]

        # Random subset
        count = random.randint(2, len(sim_objects))
        selected = random.sample(sim_objects, count)

        for det in selected:
            det["class_id"] = [k for k, v in self.INTEL_CLASSES.items() if v == det["class"]][0] if det["class"] in self.INTEL_CLASSES.values() else 0
            det["is_threat_object"] = det["class"] in self.THREAT_OBJECTS
            det["confidence"] = round(det["confidence"] + random.uniform(-0.1, 0.05), 4)

        person_count = len([d for d in selected if d["class"] == "person"])
        vehicle_count = len([d for d in selected if d["class"] in {"car", "truck", "bus"}])

        return {
            "detections": selected,
            "total_objects": len(selected),
            "threat_objects": len([d for d in selected if d["is_threat_object"]]),
            "person_count": person_count,
            "vehicle_count": vehicle_count,
            "model": "yolov8n (simulated)",
            "simulation": True,
        }
