import re
from datetime import date, time
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    university: str = "UNIFAL-MG"
    phone: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    university: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=30)

    @field_validator("name", "university")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("Informe pelo menos 2 caracteres")
        return normalized

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if not value or not value.strip():
            return None
        digits = re.sub(r"\D", "", value)
        if not 10 <= len(digits) <= 15:
            raise ValueError("Informe um telefone válido com DDD")
        return digits


class VehicleIn(BaseModel):
    model: str = Field(min_length=2, max_length=80)
    color: str = Field(min_length=2, max_length=40)
    plate: str = Field(min_length=7, max_length=8)

    @field_validator("model", "color")
    @classmethod
    def normalize_vehicle_text(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("Informe pelo menos 2 caracteres")
        return normalized

    @field_validator("plate")
    @classmethod
    def normalize_plate(cls, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9]", "", value).upper()
        if len(normalized) != 7:
            raise ValueError("Informe uma placa válida com 7 caracteres")
        return normalized


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
