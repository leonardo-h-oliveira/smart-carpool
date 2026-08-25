from datetime import date, time, timedelta

from sqlalchemy import select

from .database import Base, SessionLocal, engine
from .models import Ride, User, Vehicle
from .security import hash_password


def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    if db.scalar(select(User).where(User.email == "motorista@unifal.br")):
        print("Demo data already exists."); return
    driver = User(name="Marina Costa", email="motorista@unifal.br", password_hash=hash_password("123456"), phone="35999990000")
    passenger = User(name="Leonardo Oliveira", email="passageiro@unifal.br", password_hash=hash_password("123456"), phone="35999991111")
    db.add_all([driver, passenger]); db.flush()
    car = Vehicle(owner_id=driver.id, model="Honda Civic", color="Prata", plate="ABC1D23")
    db.add(car); db.flush()
    db.add_all([
        Ride(driver_id=driver.id, vehicle_id=car.id, origin="Centro de Poços de Caldas", destination="UNIFAL-MG", ride_date=date.today()+timedelta(days=1), ride_time=time(18, 30), seats_total=3, seats_available=3, notes="Encontro na Praça Pedro Sanches"),
        Ride(driver_id=driver.id, vehicle_id=car.id, origin="Jardim Country Club", destination="UNIFAL-MG", ride_date=date.today()+timedelta(days=2), ride_time=time(7, 10), seats_total=2, seats_available=2),
    ])
    db.commit(); db.close(); print("Demo data created.")


if __name__ == "__main__": seed()

