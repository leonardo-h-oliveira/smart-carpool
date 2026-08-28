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


def test_index_prevents_stale_visual_assets():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store, max-age=0"
    assert '/static/styles.css?v=' in response.text
    assert '/static/app.js?v=' in response.text


def test_private_routes_require_authentication():
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/vehicles").status_code == 401
    assert client.patch(
        "/api/me",
        json={"name": "Novo Nome", "university": "UNIFAL-MG", "phone": None},
    ).status_code == 401


def test_user_can_update_profile_without_changing_login_email():
    user_headers = register("profile@test.com")

    updated = client.patch(
        "/api/me",
        headers=user_headers,
        json={
            "name": "  Maria   da Silva  ",
            "university": " Universidade Federal de Alfenas ",
            "phone": "(35) 99999-1234",
        },
    )

    assert updated.status_code == 200
    assert updated.json() == {
        "id": 1,
        "name": "Maria da Silva",
        "email": "profile@test.com",
        "university": "Universidade Federal de Alfenas",
        "phone": "35999991234",
    }
    assert client.get("/api/me", headers=user_headers).json() == updated.json()


def test_profile_rejects_invalid_phone_without_losing_current_data():
    user_headers = register("invalid-phone@test.com")

    response = client.patch(
        "/api/me",
        headers=user_headers,
        json={"name": "Outro Nome", "university": "UNIFAL-MG", "phone": "123"},
    )

    assert response.status_code == 422
    profile = client.get("/api/me", headers=user_headers).json()
    assert profile["name"] == "Test User"
    assert profile["phone"] is None


def test_users_only_list_their_own_vehicles():
    first_user = register("first@test.com")
    second_user = register("second@test.com")
    client.post(
        "/api/vehicles",
        headers=first_user,
        json={"model": "Gol", "color": "Prata", "plate": "ABC1D23"},
    )
    client.post(
        "/api/vehicles",
        headers=second_user,
        json={"model": "Onix", "color": "Preto", "plate": "DEF4G56"},
    )

    first_user_vehicles = client.get("/api/vehicles", headers=first_user)

    assert first_user_vehicles.status_code == 200
    assert [vehicle["plate"] for vehicle in first_user_vehicles.json()] == ["ABC1D23"]


def test_owner_can_update_vehicle_and_normalize_its_data():
    owner = register("vehicle-owner@test.com")
    vehicle = client.post(
        "/api/vehicles",
        headers=owner,
        json={"model": "Gol", "color": "Prata", "plate": "ABC1D23"},
    ).json()

    updated = client.patch(
        f'/api/vehicles/{vehicle["id"]}',
        headers=owner,
        json={"model": "  Fiat   Argo ", "color": " Azul ", "plate": "def-4g56"},
    )

    assert updated.status_code == 200
    assert updated.json()["model"] == "Fiat Argo"
    assert updated.json()["color"] == "Azul"
    assert updated.json()["plate"] == "DEF4G56"


def test_vehicle_update_rejects_a_plate_that_already_exists():
    owner = register("duplicate-plate@test.com")
    client.post(
        "/api/vehicles",
        headers=owner,
        json={"model": "Gol", "color": "Prata", "plate": "ABC1D23"},
    )
    second_vehicle = client.post(
        "/api/vehicles",
        headers=owner,
        json={"model": "Onix", "color": "Preto", "plate": "DEF4G56"},
    ).json()

    response = client.patch(
        f'/api/vehicles/{second_vehicle["id"]}',
        headers=owner,
        json={"model": "Onix", "color": "Preto", "plate": "ABC1D23"},
    )

    assert response.status_code == 409
    vehicles = client.get("/api/vehicles", headers=owner).json()
    assert {vehicle["plate"] for vehicle in vehicles} == {"ABC1D23", "DEF4G56"}


def test_user_cannot_change_or_delete_another_users_vehicle():
    owner = register("vehicle-owner@test.com")
    another_user = register("another-user@test.com")
    vehicle = client.post(
        "/api/vehicles",
        headers=owner,
        json={"model": "Gol", "color": "Prata", "plate": "ABC1D23"},
    ).json()

    update = client.patch(
        f'/api/vehicles/{vehicle["id"]}',
        headers=another_user,
        json={"model": "Onix", "color": "Preto", "plate": "DEF4G56"},
    )
    deletion = client.delete(f'/api/vehicles/{vehicle["id"]}', headers=another_user)

    assert update.status_code == 404
    assert deletion.status_code == 404


def test_vehicle_without_rides_can_be_deleted():
    owner = register("delete-vehicle@test.com")
    vehicle = client.post(
        "/api/vehicles",
        headers=owner,
        json={"model": "Gol", "color": "Prata", "plate": "ABC1D23"},
    ).json()

    deletion = client.delete(f'/api/vehicles/{vehicle["id"]}', headers=owner)

    assert deletion.status_code == 204
    assert client.get("/api/vehicles", headers=owner).json() == []


def test_vehicle_linked_to_a_ride_cannot_be_deleted():
    owner = register("linked-vehicle@test.com")
    vehicle = client.post(
        "/api/vehicles",
        headers=owner,
        json={"model": "Gol", "color": "Prata", "plate": "ABC1D23"},
    ).json()
    client.post(
        "/api/rides",
        headers=owner,
        json={
            "vehicle_id": vehicle["id"],
            "origin": "Centro",
            "destination": "UNIFAL",
            "ride_date": str(date.today() + timedelta(days=1)),
            "ride_time": "18:30",
            "seats": 1,
        },
    )

    deletion = client.delete(f'/api/vehicles/{vehicle["id"]}', headers=owner)

    assert deletion.status_code == 409
    assert client.get("/api/vehicles", headers=owner).json()[0]["can_delete"] is False


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
