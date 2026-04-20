"""
Clustering Module — DBSCAN & KMeans for Geospatial Intelligence.
Detects hotspots and clusters geospatial intelligence data.
"""

import numpy as np
from typing import Dict, List, Optional
from collections import Counter

try:
    from sklearn.cluster import DBSCAN, KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class IntelClusterer:
    """Geospatial clustering for intelligence hotspot detection."""

    def __init__(self):
        self.simulation_mode = not SKLEARN_AVAILABLE

    def cluster(
        self,
        coordinates: List[List[float]],
        algorithm: str = "dbscan",
        params: Optional[dict] = None,
    ) -> Dict:
        """
        Cluster geospatial coordinates to identify hotspots.

        Args:
            coordinates: List of [latitude, longitude] pairs
            algorithm: 'dbscan' or 'kmeans'
            params: Optional algorithm parameters

        Returns:
            Dict with cluster assignments, hotspots, and metadata
        """
        if not coordinates or len(coordinates) < 2:
            return {"clusters": [], "hotspots": [], "total_clusters": 0, "algorithm": algorithm}

        if self.simulation_mode:
            return self._simulate_clustering(coordinates, algorithm)

        params = params or {}

        try:
            data = np.array(coordinates, dtype=np.float64)

            if algorithm == "dbscan":
                return self._dbscan_cluster(data, params)
            elif algorithm == "kmeans":
                return self._kmeans_cluster(data, params)
            else:
                return {"error": f"Unknown algorithm: {algorithm}", "clusters": [], "hotspots": [], "total_clusters": 0}

        except Exception as e:
            return {"error": str(e), "clusters": [], "hotspots": [], "total_clusters": 0, "algorithm": algorithm}

    def _dbscan_cluster(self, data: np.ndarray, params: dict) -> Dict:
        """DBSCAN clustering with haversine-appropriate eps."""
        eps = params.get("eps", 0.5)  # ~55km at equator
        min_samples = params.get("min_samples", 3)

        model = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean")
        labels = model.fit_predict(data)

        return self._build_result(data, labels, "dbscan")

    def _kmeans_cluster(self, data: np.ndarray, params: dict) -> Dict:
        """KMeans clustering."""
        n_clusters = params.get("n_clusters", min(5, len(data)))
        n_clusters = min(n_clusters, len(data))

        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = model.fit_predict(data)

        return self._build_result(data, labels, "kmeans")

    def _build_result(self, data: np.ndarray, labels: np.ndarray, algorithm: str) -> Dict:
        """Build standardized result from cluster labels."""
        unique_labels = set(labels)
        unique_labels.discard(-1)  # Remove noise label for DBSCAN

        clusters = []
        hotspots = []

        for label in sorted(unique_labels):
            mask = labels == label
            cluster_points = data[mask]
            center = cluster_points.mean(axis=0)
            density = len(cluster_points) / max(1, len(data))

            cluster_info = {
                "cluster_id": int(label),
                "center": {"lat": round(float(center[0]), 4), "lon": round(float(center[1]), 4)},
                "size": int(mask.sum()),
                "density": round(density, 4),
                "points": [{"lat": round(float(p[0]), 4), "lon": round(float(p[1]), 4)} for p in cluster_points],
            }
            clusters.append(cluster_info)

            # Mark as hotspot if density is significant
            if density >= 0.15 or mask.sum() >= 5:
                risk_level = "critical" if density > 0.3 else ("high" if density > 0.2 else "medium")
                hotspots.append({
                    "cluster_id": int(label),
                    "center": cluster_info["center"],
                    "density": round(density, 4),
                    "point_count": int(mask.sum()),
                    "risk_level": risk_level,
                    "radius_km": round(float(np.std(cluster_points) * 111), 2),  # Rough km conversion
                })

        # Add noise points for DBSCAN
        noise_count = int(np.sum(labels == -1))

        return {
            "clusters": clusters,
            "hotspots": hotspots,
            "total_clusters": len(clusters),
            "noise_points": noise_count,
            "total_points": len(data),
            "algorithm": algorithm,
            "simulation": False,
        }

    def _simulate_clustering(self, coordinates: List[List[float]], algorithm: str) -> Dict:
        """Simulate clustering when sklearn is unavailable."""
        import random

        # Simple grid-based clustering simulation
        grid_size = 2.0
        grid_clusters = {}

        for i, coord in enumerate(coordinates):
            grid_key = (round(coord[0] / grid_size) * grid_size, round(coord[1] / grid_size) * grid_size)
            if grid_key not in grid_clusters:
                grid_clusters[grid_key] = []
            grid_clusters[grid_key].append(coord)

        clusters = []
        hotspots = []

        for idx, (center, points) in enumerate(grid_clusters.items()):
            density = len(points) / max(len(coordinates), 1)
            clusters.append({
                "cluster_id": idx,
                "center": {"lat": round(center[0], 4), "lon": round(center[1], 4)},
                "size": len(points),
                "density": round(density, 4),
                "points": [{"lat": round(p[0], 4), "lon": round(p[1], 4)} for p in points],
            })

            if density >= 0.15:
                hotspots.append({
                    "cluster_id": idx,
                    "center": {"lat": round(center[0], 4), "lon": round(center[1], 4)},
                    "density": round(density, 4),
                    "point_count": len(points),
                    "risk_level": "high" if density > 0.25 else "medium",
                    "radius_km": round(random.uniform(5, 50), 2),
                })

        return {
            "clusters": clusters,
            "hotspots": hotspots,
            "total_clusters": len(clusters),
            "noise_points": 0,
            "total_points": len(coordinates),
            "algorithm": f"{algorithm} (simulated)",
            "simulation": True,
        }
