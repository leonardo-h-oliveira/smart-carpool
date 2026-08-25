from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from . import models, schemas
from .database import Base, engine, get_db
from .security import create_token, hash_password, read_token, verify_password


Base.metadata.create_all(bind=engine)
app = FastAPI(title="Smart Carpool API", version="1.0.0")
STATIC = Path(__file__).parent / "static"


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> models.User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    user_id = read_token(authorization[7:])
    user = db.get(models.User, user_id) if user_id else None
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user


def ride_dict(ride: models.Ride, include_contact: bool = False) -> dict:
    data = {
        "id": ride.id, "origin": ride.origin, "destination": ride.destination,
        "date": ride.ride_date.isoformat(), "time": ride.ride_time.strftime("%H:%M"),
        "seats_available": ride.seats_available, "seats_total": ride.seats_total,
        "status": ride.status, "notes": ride.notes,
        "driver": {"id": ride.driver.id, "name": ride.driver.name},
        "vehicle": {"model": ride.vehicle.model, "color": ride.vehicle.color},
    }
    if include_contact:
        data["driver"]["phone"] = ride.driver.phone
        data["vehicle"]["plate"] = ride.vehicle.plate
    return data


@app.post("/api/auth/register", status_code=201)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    user = models.User(name=data.name, email=data.email.lower(), password_hash=hash_password(data.password), university=data.university, phone=data.phone)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered")
    db.refresh(user)
    return {"token": create_token(user.id), "user": {"id": user.id, "name": user.name, "email": user.email}}


@app.post("/api/auth/login")
def login(data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"token": create_token(user.id), "user": {"id": user.id, "name": user.name, "email": user.email}}


@app.get("/api/me")
def me(user: models.User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "university": user.university, "phone": user.phone}


@app.post("/api/vehicles", status_code=201)
def add_vehicle(data: schemas.VehicleIn, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    vehicle = models.Vehicle(owner_id=user.id, model=data.model, color=data.color, plate=data.plate.upper().replace("-", ""))
    db.add(vehicle)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Plate already registered")
    db.refresh(vehicle)
    return {"id": vehicle.id, "model": vehicle.model, "color": vehicle.color, "plate": vehicle.plate}


@app.get("/api/vehicles")
def vehicles(user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    return db.execute(select(models.Vehicle).where(models.Vehicle.owner_id == user.id)).scalars().all()


@app.post("/api/rides", status_code=201)
def create_ride(data: schemas.RideIn, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    vehicle = db.get(models.Vehicle, data.vehicle_id)
    if not vehicle or vehicle.owner_id != user.id:
        raise HTTPException(404, "Vehicle not found")
    if data.ride_date < date.today():
        raise HTTPException(422, "Ride date cannot be in the past")
    ride = models.Ride(driver_id=user.id, vehicle_id=vehicle.id, origin=data.origin, destination=data.destination,
                       ride_date=data.ride_date, ride_time=data.ride_time, seats_total=data.seats,
                       seats_available=data.seats, notes=data.notes)
    db.add(ride); db.commit(); db.refresh(ride)
    ride.driver, ride.vehicle = user, vehicle
    return ride_dict(ride)


@app.get("/api/rides")
def list_rides(origin: str | None = Query(None), destination: str | None = Query(None), ride_date: date | None = Query(None), db: Session = Depends(get_db)):
    query = select(models.Ride).options(joinedload(models.Ride.driver), joinedload(models.Ride.vehicle)).where(models.Ride.status == "open", models.Ride.seats_available > 0, models.Ride.ride_date >= date.today())
    if origin: query = query.where(func.lower(models.Ride.origin).contains(origin.lower()))
    if destination: query = query.where(func.lower(models.Ride.destination).contains(destination.lower()))
    if ride_date: query = query.where(models.Ride.ride_date == ride_date)
    rides = db.execute(query.order_by(models.Ride.ride_date, models.Ride.ride_time)).scalars().all()
    return [ride_dict(ride) for ride in rides]


@app.post("/api/rides/{ride_id}/book", status_code=201)
def request_seat(ride_id: int, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    ride = db.get(models.Ride, ride_id)
    if not ride or ride.status != "open": raise HTTPException(404, "Ride not available")
    if ride.driver_id == user.id: raise HTTPException(409, "Driver cannot book their own ride")
    booking = models.Booking(ride_id=ride_id, passenger_id=user.id)
    db.add(booking)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "You already requested this ride")
    db.refresh(booking)
    return {"id": booking.id, "status": booking.status}


@app.patch("/api/bookings/{booking_id}")
def update_booking(booking_id: int, data: schemas.BookingStatusIn, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    booking = db.execute(select(models.Booking).options(joinedload(models.Booking.ride)).where(models.Booking.id == booking_id).with_for_update()).scalar_one_or_none()
    if not booking: raise HTTPException(404, "Booking not found")
    is_driver = booking.ride.driver_id == user.id
    is_passenger = booking.passenger_id == user.id
    if data.status in {"accepted", "rejected"} and not is_driver: raise HTTPException(403, "Only the driver can decide")
    if data.status == "cancelled" and not (is_driver or is_passenger): raise HTTPException(403, "Not allowed")
    if booking.status in {"rejected", "cancelled"}:
        raise HTTPException(409, "A closed request cannot be changed")
    if data.status == "accepted" and booking.status != "accepted":
        if booking.ride.seats_available < 1: raise HTTPException(409, "No seats available")
        booking.ride.seats_available -= 1
    if data.status in {"rejected", "cancelled"} and booking.status == "accepted": booking.ride.seats_available += 1
    booking.status = data.status; db.commit()
    return {"id": booking.id, "status": booking.status, "seats_available": booking.ride.seats_available}


@app.get("/api/dashboard")
def dashboard(user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    offered = db.execute(select(models.Ride).options(joinedload(models.Ride.driver), joinedload(models.Ride.vehicle)).where(models.Ride.driver_id == user.id)).scalars().all()
    bookings = db.execute(select(models.Booking).options(joinedload(models.Booking.ride).joinedload(models.Ride.driver), joinedload(models.Booking.ride).joinedload(models.Ride.vehicle)).where(models.Booking.passenger_id == user.id)).scalars().all()
    requests = db.execute(select(models.Booking).options(joinedload(models.Booking.passenger), joinedload(models.Booking.ride)).join(models.Ride).where(models.Ride.driver_id == user.id)).scalars().all()
    return {
        "offered": [ride_dict(r) for r in offered],
        "bookings": [
            {"id": b.id, "status": b.status, "ride": ride_dict(b.ride, include_contact=b.status == "accepted")}
            for b in bookings
        ],
        "requests": [
            {"id": b.id, "status": b.status, "passenger": b.passenger.name, "ride_id": b.ride_id}
            for b in requests
        ],
    }


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")
