from datetime import date, time
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    university: str = "UNIFAL-MG"
    phone: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class VehicleIn(BaseModel):
    model: str
    color: str
    plate: str


class RideIn(BaseModel):
    vehicle_id: int
    origin: str
    destination: str
    ride_date: date
    ride_time: time
    seats: int = Field(ge=1, le=7)
    notes: str | None = None


class BookingStatusIn(BaseModel):
    status: Literal["accepted", "rejected", "cancelled"]


class RideStatusIn(BaseModel):
    status: Literal["cancelled"]
