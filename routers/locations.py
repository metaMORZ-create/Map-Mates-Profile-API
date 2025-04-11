from fastapi import APIRouter, Depends, HTTPException, Body
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

@router.get("/visited_polygons")
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
