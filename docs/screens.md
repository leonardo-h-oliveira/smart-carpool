# Screens: from UniCar to Smart Carpool

## 1. Screen1 — access and registration

The original prototype combined initialization, TinyDB, Firebase authentication, `localId` and user/vehicle registration. Smart Carpool separates this work into login, account creation, profile and vehicle screens.

## 2. Screen4 — main menu

This was the decision point between offering and requesting a ride. It became the main dashboard, with shortcuts for both actions and a list of upcoming rides.

## 3. Screen3 — publishing a ride

The driver selects a vehicle, origin, destination, date, time, number of seats and optional notes. Each ride has an explicit state (`open`, `completed` or `cancelled`) and controlled seat availability.

## 4. Screen2 — requesting a ride

The passenger searches by origin, destination and date, opens a ride and submits a booking request. A new request starts with the `pending` status.

## 5. Screen5 — boarding and contact

The prototype combined boarding details and WhatsApp contact. Smart Carpool represents this work in **My trips**, where drivers approve or reject requests and passengers follow their status. Contact information is released only after approval.

## Additional screens in the web version

- Vehicles
- Profile
- My trips
- Empty, loading, success and error states for each workflow
