import os
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:///./test_smart_carpool.db"

from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app


client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)


def register(email):
    response = client.post("/api/auth/register", json={"name":"Test User","email":email,"password":"123456","university":"UNIFAL-MG"})
    assert response.status_code == 201
    return {"Authorization": "Bearer " + response.json()["token"]}


def test_complete_booking_flow():
    driver = register("driver@test.com")
    passenger = register("passenger@test.com")
    vehicle = client.post("/api/vehicles", headers=driver, json={"model":"Gol","color":"Prata","plate":"ABC1D23"}).json()
    ride = client.post("/api/rides", headers=driver, json={"vehicle_id":vehicle["id"],"origin":"Centro","destination":"UNIFAL","ride_date":str(date.today()+timedelta(days=1)),"ride_time":"18:30","seats":1}).json()
    booking = client.post(f'/api/rides/{ride["id"]}/book', headers=passenger)
    assert booking.status_code == 201
    accepted = client.patch(f'/api/bookings/{booking.json()["id"]}', headers=driver, json={"status":"accepted"})
    assert accepted.status_code == 200
    assert accepted.json()["seats_available"] == 0


def test_driver_cannot_book_own_ride():
    driver = register("driver@test.com")
    vehicle = client.post("/api/vehicles", headers=driver, json={"model":"Gol","color":"Prata","plate":"ABC1D23"}).json()
    ride = client.post("/api/rides", headers=driver, json={"vehicle_id":vehicle["id"],"origin":"Centro","destination":"UNIFAL","ride_date":str(date.today()+timedelta(days=1)),"ride_time":"18:30","seats":1}).json()
    assert client.post(f'/api/rides/{ride["id"]}/book', headers=driver).status_code == 409


def test_driver_contact_is_private_until_booking_is_accepted():
    driver = register("driver@test.com")
    passenger = register("passenger@test.com")
    vehicle = client.post("/api/vehicles", headers=driver, json={"model":"Gol","color":"Prata","plate":"ABC1D23"}).json()
    ride = client.post("/api/rides", headers=driver, json={"vehicle_id":vehicle["id"],"origin":"Centro","destination":"UNIFAL","ride_date":str(date.today()+timedelta(days=1)),"ride_time":"18:30","seats":1}).json()

    public_ride = client.get("/api/rides").json()[0]
    assert "phone" not in public_ride["driver"]
    assert "plate" not in public_ride["vehicle"]

    booking = client.post(f'/api/rides/{ride["id"]}/book', headers=passenger).json()
    before_acceptance = client.get("/api/dashboard", headers=passenger).json()["bookings"][0]["ride"]
    assert "phone" not in before_acceptance["driver"]

    client.patch(f'/api/bookings/{booking["id"]}', headers=driver, json={"status":"accepted"})
    after_acceptance = client.get("/api/dashboard", headers=passenger).json()["bookings"][0]["ride"]
    assert "phone" in after_acceptance["driver"]
    assert after_acceptance["vehicle"]["plate"] == "ABC1D23"


def test_closed_booking_cannot_be_reopened():
    driver = register("driver@test.com")
    passenger = register("passenger@test.com")
    vehicle = client.post("/api/vehicles", headers=driver, json={"model":"Gol","color":"Prata","plate":"ABC1D23"}).json()
    ride = client.post("/api/rides", headers=driver, json={"vehicle_id":vehicle["id"],"origin":"Centro","destination":"UNIFAL","ride_date":str(date.today()+timedelta(days=1)),"ride_time":"18:30","seats":1}).json()
    booking = client.post(f'/api/rides/{ride["id"]}/book', headers=passenger).json()

    assert client.patch(f'/api/bookings/{booking["id"]}', headers=driver, json={"status":"rejected"}).status_code == 200
    assert client.patch(f'/api/bookings/{booking["id"]}', headers=driver, json={"status":"accepted"}).status_code == 409


def test_health_check_confirms_database_connection():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "sqlite"}


def test_private_routes_require_authentication():
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/vehicles").status_code == 401


def test_passenger_can_cancel_an_accepted_booking_and_restore_the_seat():
    driver = register("driver@test.com")
    passenger = register("passenger@test.com")
    vehicle = client.post(
        "/api/vehicles",
        headers=driver,
        json={"model": "Gol", "color": "Prata", "plate": "ABC1D23"},
    ).json()
    ride = client.post(
        "/api/rides",
        headers=driver,
        json={
            "vehicle_id": vehicle["id"],
            "origin": "Centro",
            "destination": "UNIFAL",
            "ride_date": str(date.today() + timedelta(days=1)),
            "ride_time": "18:30",
            "seats": 1,
        },
    ).json()
    booking = client.post(
        f'/api/rides/{ride["id"]}/book', headers=passenger
    ).json()
    client.patch(
        f'/api/bookings/{booking["id"]}',
        headers=driver,
        json={"status": "accepted"},
    )

    cancelled = client.patch(
        f'/api/bookings/{booking["id"]}',
        headers=passenger,
        json={"status": "cancelled"},
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["seats_available"] == 1


def test_driver_can_cancel_a_ride_and_its_active_requests():
    driver = register("driver@test.com")
    passenger = register("passenger@test.com")
    vehicle = client.post(
        "/api/vehicles",
        headers=driver,
        json={"model": "Gol", "color": "Prata", "plate": "ABC1D23"},
    ).json()
    ride = client.post(
        "/api/rides",
        headers=driver,
        json={
            "vehicle_id": vehicle["id"],
            "origin": "Centro",
            "destination": "UNIFAL",
            "ride_date": str(date.today() + timedelta(days=1)),
            "ride_time": "18:30",
            "seats": 1,
        },
    ).json()
    client.post(f'/api/rides/{ride["id"]}/book', headers=passenger)

    cancelled = client.patch(
        f'/api/rides/{ride["id"]}',
        headers=driver,
        json={"status": "cancelled"},
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert client.get("/api/rides").json() == []
    passenger_booking = client.get(
        "/api/dashboard", headers=passenger
    ).json()["bookings"][0]
    assert passenger_booking["status"] == "cancelled"


def test_passenger_cannot_cancel_a_ride_offered_by_another_user():
    driver = register("driver@test.com")
    passenger = register("passenger@test.com")
    vehicle = client.post(
        "/api/vehicles",
        headers=driver,
        json={"model": "Gol", "color": "Prata", "plate": "ABC1D23"},
    ).json()
    ride = client.post(
        "/api/rides",
        headers=driver,
        json={
            "vehicle_id": vehicle["id"],
            "origin": "Centro",
            "destination": "UNIFAL",
            "ride_date": str(date.today() + timedelta(days=1)),
            "ride_time": "18:30",
            "seats": 1,
        },
    ).json()

    response = client.patch(
        f'/api/rides/{ride["id"]}',
        headers=passenger,
        json={"status": "cancelled"},
    )

    assert response.status_code == 403
