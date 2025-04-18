import math
from shapely.geometry import Point, MultiPoint
from geopy.distance import geodesic

def is_within_radius(lat1, lon1, lat2, lon2, radius_meters=5):
    R = 6371000  # Erdradius in Metern
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance <= radius_meters

def meter_to_degree_lat(meters: float) -> float:
    return meters / 111_000  # Breitengrad ≈ konstant

def create_buffered_area(points: list[dict], padding_m: float = 15.0):
    """
    Erstellt ein Polygon, das alle Punkte umschließt, mit einem Padding von X Metern.
    Punkteformat: [{"latitude": ..., "longitude": ...}, ...]
    """
    if not points:
        return None

    # In Shapely-Punkte konvertieren
    shapely_points = [Point(p["longitude"], p["latitude"]) for p in points]

    # Kombinieren zu einem MultiPoint-Objekt
    multi = MultiPoint(shapely_points)

    # Padding in Grad (Breite)
    padding_deg = meter_to_degree_lat(padding_m)

    # Erzeuge gepuffertes Polygon
    buffered_area = multi.convex_hull.buffer(padding_deg)

    return buffered_area

def cluster_points(points, max_distance_m=10):
    clusters = []

    for point in points:
        added = False
        for cluster in clusters:
            if any(geodesic((point.y, point.x), (other.y, other.x)).meters <= max_distance_m for other in cluster):
                cluster.append(point)
                added = True
                break
        if not added:
            clusters.append([point])
    return clusters

