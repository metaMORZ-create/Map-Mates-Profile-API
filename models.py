from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Float, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    disabled = Column(Boolean, default=False)
    hashed_password = Column(String)

    locations = relationship("UserLocation", back_populates="user", cascade="all, delete-orphan")
    friend_requests_sent = relationship("FriendRequest", foreign_keys="[FriendRequest.sender_id]")
    visited_zones = relationship("VisitedZone", back_populates="user", cascade="all, delete")
    friend_requests_received = relationship("FriendRequest", foreign_keys="[FriendRequest.receiver_id]")
    visited_polygon = relationship("VisitedPolygon", back_populates="user", uselist=False)

class UserLocation(Base):
    __tablename__ = "user_locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Optional: Rückverbindung zum User (nur wenn du sie brauchst)
    user = relationship("User", back_populates="locations")

## Freundes Tabelle
class UserFriend(Base):
    __tablename__ = "user_friends"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Optional für Zugriff über ORM
    user = relationship("User", foreign_keys=[user_id], backref="friends")
    friend = relationship("User", foreign_keys=[friend_id])

## Freundschaftanfragen
class RequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class VisitedZone(Base):
    __tablename__ = "visited_zones"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius = Column(Float, default=5.0)
    visits = Column(Integer, default=1)
    first_visited = Column(DateTime, default=datetime.utcnow)
    last_visited = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="visited_zones")

class VisitedPolygon(Base):
    __tablename__ = "visited_polygons"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    geojson = Column(JSON, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="visited_polygon")