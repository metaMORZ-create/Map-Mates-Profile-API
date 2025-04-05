from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from db import get_db
from hashing import hash_password, verify_password
import models as tables
from typevalidation import AddLocation
from datetime import datetime
from utils import is_within_radius


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
