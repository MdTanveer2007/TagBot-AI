from fastapi import FastAPI

app = FastAPI(
    title="TagBot AI API",
    description="The first backend service for TagBot AI.",
    version="0.1.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "status": "online",
        "message": "TagBot AI backend is running.",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }