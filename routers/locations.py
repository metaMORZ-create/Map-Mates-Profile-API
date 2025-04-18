from fastapi import APIRouter, Depends, HTTPException, Body
from shapely import Polygon, LineString
from sqlalchemy.orm import Session
from typing import Annotated, List
from db import get_db
from hashing import hash_password, verify_password
import models as tables
from typevalidation import AddLocation, BatchVisitedZones, BatchLocations, ZoneInput
from datetime import datetime
from utils import is_within_radius, create_buffered_area, meter_to_degree_lat, cluster_points
from shapely.geometry import Point, MultiPoint, mapping
from shapely.ops import unary_union
from fastapi.responses import JSONResponse


router = APIRouter()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/add_location")
def add_location(location: AddLocation, db: db_dependency):
    user_exists = db.query(tables.User).filter(tables.User.id == location.user_id).first()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User ID not found")
    
    new_location = tables.UserLocation(
        user_id=location.user_id,
        latitude=location.latitude,
        longitude=location.longitude
    )
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return {"message": "Location added", "location_id": new_location.id, "timestamp": new_location.timestamp}

@router.get("/last_location/{user_id}")
def get_last_location(user_id: int, db: db_dependency):
    location = (
        db.query(tables.UserLocation)
        .filter(tables.UserLocation.user_id == user_id)
        .order_by(tables.UserLocation.timestamp.desc())
        .first()
    )

    if not location:
        raise HTTPException(status_code=404, detail="No location found for this user")
    
    return {
        "user_id": location.user_id,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "altitude": location.altitude,
        "timestamp": location.timestamp
    }

@router.post("/visited_zone")
def mark_visited_zone(data: AddLocation, db: db_dependency):
    existing_zones = db.query(tables.VisitedZone).filter_by(user_id=data.user_id).all()

    matched_zone = None
    for zone in existing_zones:
        if is_within_radius(data.latitude, data.longitude, zone.latitude, zone.longitude, zone.radius):
            matched_zone = zone
            break

    if matched_zone:
        matched_zone.last_visited = datetime.utcnow()
        matched_zone.visits += 1
    else:
        new_zone = tables.VisitedZone(
            user_id=data.user_id,
            latitude=data.latitude,
            longitude=data.longitude
        )
        db.add(new_zone)

    db.commit()
    return {"message": "Zone saved/updated"}

@router.post("/batch_visited_zones")
def batch_visited_zones(data: BatchVisitedZones, db: Session = Depends(get_db)):
    for entry in data.locations:
        existing_zones = db.query(tables.VisitedZone).filter_by(user_id=entry.user_id).all()

        matched_zone = None
        for zone in existing_zones:
            if is_within_radius(entry.latitude, entry.longitude, zone.latitude, zone.longitude, zone.radius):
                matched_zone = zone
                break

        if matched_zone:
            matched_zone.last_visited = entry.timestamp
            matched_zone.visits += 1
        else:
            new_zone = tables.VisitedZone(
                user_id=entry.user_id,
                latitude=entry.latitude,
                longitude=entry.longitude,
                last_visited=entry.timestamp
            )
            db.add(new_zone)

    db.commit()
    return {"message": f"{len(data.locations)} zones processed"}


@router.post("/batch_add_locations")
def batch_add_locations(data: BatchLocations, db: Session = Depends(get_db)):
    for entry in data.locations:
        new_loc = tables.UserLocation(
            user_id=entry.user_id,
            latitude=entry.latitude,
            longitude=entry.longitude,
            timestamp=entry.timestamp
        )
        db.add(new_loc)

    db.commit()
    return {"message": f"{len(data.locations)} locations added"}



@router.get("/visited_zones/{user_id}")
def get_visited_zones(user_id: int, db: db_dependency):
    zones = db.query(tables.VisitedZone).filter(
        tables.VisitedZone.user_id == user_id
    ).all()

    return [
        {
            "latitude": zone.latitude,
            "longitude": zone.longitude,
            "radius": zone.radius,
            "last_visited": zone.last_visited.isoformat(),  # optional
        }
        for zone in zones
    ]

@router.post("/visited_polygons")
def get_visited_polygons_from_zones(
    zones: List[ZoneInput] = Body(...),
):
    if not zones:
        return {"features": []}

    shapely_points = [Point(z.longitude, z.latitude) for z in zones]
    clusters = cluster_points(shapely_points, max_distance_m=60)

    features = []
    for cluster in clusters:
        merged = unary_union([p.buffer(30 / 111_111, resolution=6) for p in cluster])
        if merged.geom_type == "Polygon":
            coords = list(merged.exterior.coords)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[list(c) for c in coords]]
                }
            })

    return JSONResponse(content={
        "type": "FeatureCollection",
        "features": features
    })

@router.post("/extend_visited_polygon_alt/{user_id}")
def extend_visited_polygon(
    user_id: int,
    new_zones: List[ZoneInput] = Body(...),
    db: Session = Depends(get_db)
):
    if not new_zones:
        raise HTTPException(status_code=400, detail="No new zones provided.")

    # Bestehendes Polygon abrufen
    existing = db.query(tables.VisitedPolygon).filter_by(user_id=user_id).first()

    # Neue Punkte in Shapely-Form umwandeln
    new_points = [Point(z.longitude, z.latitude) for z in new_zones]
    new_cluster = unary_union([p.buffer(15 / 111_111, resolution=3) for p in new_points])

    # Wenn noch kein Polygon existiert, wird es neu erstellt
    if not existing:
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        if new_cluster.geom_type == "Polygon":
            geojson["features"].append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[list(c) for c in new_cluster.exterior.coords]]
                }
            })

        db.add(tables.VisitedPolygon(
            user_id=user_id,
            geojson=geojson,
            last_updated=datetime.utcnow()
        ))
        db.commit()
        return {"message": "New polygon created from scratch."}

    # Wenn bereits ein Polygon existiert, erweitere es
    old_polygons = []
    for feature in existing.geojson.get("features", []):
        coords = feature["geometry"]["coordinates"][0]
        old_polygons.append(Polygon([(c[0], c[1]) for c in coords]))

    combined = unary_union([*old_polygons, new_cluster])

    new_features = []
    if combined.geom_type == "Polygon":
        new_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[list(c) for c in combined.exterior.coords]]
            }
        })
    elif combined.geom_type == "MultiPolygon":
        for poly in combined.geoms:
            new_features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[list(c) for c in poly.exterior.coords]]
                }
            })

    existing.geojson = {
        "type": "FeatureCollection",
        "features": new_features
    }
    existing.last_updated = datetime.utcnow()
    db.commit()

    return {"message": "Polygon extended successfully."}

@router.get("/stored_polygon/{user_id}")
def get_stored_polygon(user_id: int, db: Session = Depends(get_db)):
    stored = db.query(tables.VisitedPolygon).filter_by(user_id=user_id).first()

    if not stored:
        raise HTTPException(status_code=404, detail="No stored polygon found.")

    return JSONResponse(content=stored.geojson)


@router.post("/rebuild_visited_polygon/{user_id}")
def rebuild_visited_polygon(user_id: int, db: Session = Depends(get_db)):
    visited_zones = db.query(tables.VisitedZone).filter_by(user_id=user_id).all()
    
    if not visited_zones:
        raise HTTPException(status_code=404, detail="Keine Visited Zones gefunden")

    points = [Point(zone.longitude, zone.latitude) for zone in visited_zones]
    clusters = cluster_points(points, max_distance_m=20)

    features = []
    for cluster in clusters:
        buffered = unary_union([p.buffer(30 / 111_111, resolution=8) for p in cluster])
        if buffered.geom_type == "Polygon":
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[list(c) for c in buffered.exterior.coords]]
                }
            })
        elif buffered.geom_type == "MultiPolygon":
            for poly in buffered.geoms:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[list(c) for c in poly.exterior.coords]]
                    }
                })

    new_geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    existing_polygon = db.query(tables.VisitedPolygon).filter_by(user_id=user_id).first()
    if existing_polygon:
        existing_polygon.geojson = new_geojson
        existing_polygon.last_updated = datetime.utcnow()
    else:
        db.add(tables.VisitedPolygon(
            user_id=user_id,
            geojson=new_geojson,
            last_updated=datetime.utcnow()
        ))

    db.commit()
    return {"message": "Polygon wurde vollständig neu berechnet."}


@router.post("/extend_visited_polygon/{user_id}")
def extend_visited_polygon(
    user_id: int,
    new_zones: List[ZoneInput] = Body(...),
    db: Session = Depends(get_db)
):
    if len(new_zones) < 2:
        raise HTTPException(status_code=400, detail="At least two points needed for route buffering.")

    # Bestehendes Polygon abrufen
    existing = db.query(tables.VisitedPolygon).filter_by(user_id=user_id).first()

    # Neue Punkte in Shapely-Form
    points = [Point(z.longitude, z.latitude) for z in new_zones]
    route = LineString(points)

    # Band mit 30m Breite
    buffered = route.buffer(30 / 111_111, resolution=3)

    # Wenn noch nichts existiert → neu erstellen
    if not existing:
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[list(c) for c in buffered.exterior.coords]]
                }
            }]
        }
        db.add(tables.VisitedPolygon(
            user_id=user_id,
            geojson=geojson,
            last_updated=datetime.utcnow()
        ))
        db.commit()
        return {"message": "New buffered route polygon created."}

    # Wenn vorhanden → mit altem vereinen
    old_polys = []
    for f in existing.geojson["features"]:
        coords = f["geometry"]["coordinates"][0]
        old_polys.append(Polygon(coords))

    combined = unary_union([*old_polys, buffered])

    new_features = []
    if combined.geom_type == "Polygon":
        new_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[list(c) for c in combined.exterior.coords]]
            }
        })
    elif combined.geom_type == "MultiPolygon":
        for poly in combined.geoms:
            new_features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[list(c) for c in poly.exterior.coords]]
                }
            })

    existing.geojson = {
        "type": "FeatureCollection",
        "features": new_features
    }
    existing.last_updated = datetime.utcnow()
    db.commit()

    return {"message": "Buffered route polygon extended successfully."}



