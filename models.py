from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    disabled = Column(Boolean, default=False)
    hashed_password = Column(String)

    locations = relationship("UserLocation", back_populates="user", cascade="all, delete-orphan")

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