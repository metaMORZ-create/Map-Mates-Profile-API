from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from db import get_db
from hashing import hash_password, verify_password
import models as tables
from typevalidation import AddLocation

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


