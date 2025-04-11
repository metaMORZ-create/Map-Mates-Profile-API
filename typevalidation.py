from pydantic import BaseModel
from typing import List
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str
    disabled: bool = False
    password: str

class LoginUser(BaseModel):
    username: str
    password: str

class AddLocation(BaseModel):
    user_id: int
    latitude: float
    longitude: float

class FriendRequestInput(BaseModel):
    sender_id: int
    receiver_id: int

class AcceptRequestInput(BaseModel):
    self_user_id: int
    sender_user_id: int

class LocationEntry(BaseModel):
    user_id: int
    latitude: float
    longitude: float
    timestamp: datetime

class BatchVisitedZones(BaseModel):
    locations: List[LocationEntry]

class BatchLocations(BaseModel):
    locations: List[LocationEntry]

class ZoneInput(BaseModel):
    latitude: float
    longitude: float
    radius: float = 5.0
    last_visited: Optional[str] = None

