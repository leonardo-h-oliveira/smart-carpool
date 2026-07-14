from fastapi import FastAPI

app = FastAPI(
    title="Smart Carpool API",
    description="Backend API for the Smart Carpool project.",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "Welcome to Smart Carpool!"
    }