CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rides (
    id SERIAL PRIMARY KEY,
    driver_id INTEGER NOT NULL,
    origin VARCHAR(150) NOT NULL,
    destination VARCHAR(150) NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    available_seats INTEGER NOT NULL CHECK (available_seats > 0),
    price DECIMAL(10, 2),
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rides_driver
        FOREIGN KEY (driver_id)
        REFERENCES users(id)
);

CREATE TABLE ride_requests (
    id SERIAL PRIMARY KEY,
    ride_id INTEGER NOT NULL,
    passenger_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_requests_ride
        FOREIGN KEY (ride_id)
        REFERENCES rides(id),

    CONSTRAINT fk_requests_passenger
        FOREIGN KEY (passenger_id)
        REFERENCES users(id),

    CONSTRAINT unique_ride_request
        UNIQUE (ride_id, passenger_id)
);