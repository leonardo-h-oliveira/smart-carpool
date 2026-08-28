from datetime import date, time, timedelta

from sqlalchemy import select

from .database import SessionLocal
from .models import Ride, User, Vehicle
from .security import hash_password


def seed():
    db = SessionLocal()
    try:
        driver = db.scalar(
            select(User).where(User.email == "motorista@unifal.br")
        )
        if not driver:
            driver = User(
                name="Marina Costa",
                email="motorista@unifal.br",
                password_hash=hash_password("123456"),
                phone="35999990000",
            )
            db.add(driver)

        passenger = db.scalar(
            select(User).where(User.email == "passageiro@unifal.br")
        )
        if not passenger:
            db.add(
                User(
                    name="Leonardo Oliveira",
                    email="passageiro@unifal.br",
                    password_hash=hash_password("123456"),
                    phone="35999991111",
                )
            )

        db.flush()
        car = db.scalar(
            select(Vehicle).where(
                Vehicle.owner_id == driver.id,
                Vehicle.plate == "ABC1D23",
            )
        )
        if not car:
            car = Vehicle(
                owner_id=driver.id,
                model="Honda Civic",
                color="Prata",
                plate="ABC1D23",
            )
            db.add(car)
            db.flush()

        future_demo_ride = db.scalar(
            select(Ride).where(
                Ride.driver_id == driver.id,
                Ride.status == "open",
                Ride.ride_date >= date.today(),
            )
        )
        if not future_demo_ride:
            db.add_all(
                [
                    Ride(
                        driver_id=driver.id,
                        vehicle_id=car.id,
                        origin="Centro de Poços de Caldas",
                        destination="UNIFAL-MG",
                        ride_date=date.today() + timedelta(days=1),
                        ride_time=time(18, 30),
                        seats_total=3,
                        seats_available=3,
                        notes="Encontro na Praça Pedro Sanches",
                    ),
                    Ride(
                        driver_id=driver.id,
                        vehicle_id=car.id,
                        origin="Jardim Country Club",
                        destination="UNIFAL-MG",
                        ride_date=date.today() + timedelta(days=2),
                        ride_time=time(7, 10),
                        seats_total=2,
                        seats_available=2,
                    ),
                ]
            )

        db.commit()
        print("Demo data is ready.")
    finally:
        db.close()


if __name__ == "__main__": seed()

