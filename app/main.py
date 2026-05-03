from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import sensors, alerts


def create_app():
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from app.database import engine, Base
        Base.metadata.create_all(bind=engine)
        yield

    app = FastAPI(
        title="Predictive Maintenance API",
        description="IoT sensor monitoring and anomaly detection — Intelligent IoT Solutions A/S",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(sensors.router)
    app.include_router(alerts.router)

    @app.get("/", tags=["Health"])
    def health_check():
        return {"status": "ok", "service": "Predictive Maintenance API"}

    return app


app = create_app()