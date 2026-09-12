from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import hotspots, assets

app = FastAPI(title="ThermoGIS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hotspots.router)
app.include_router(assets.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}