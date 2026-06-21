from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import database
from routers import agencies, airline_intelligence, auth, bookings, clients, documents, finance, offers, passengers, platform, portal, reference, requests
from services.seed_service import seed_core_data

app = FastAPI(
    title="AeroAssist AgencyOS API",
    version="0.1.0",
    description="AeroAssist AgencyOS API foundation through Phase 8 read-only client portal visibility.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    await database.connect()
    await seed_core_data(database)


@app.get("/api/health")
async def root_health() -> dict:
    return {"ok": True, "service": "AeroAssist AgencyOS API"}


@app.get("/api/audit-events")
async def audit_events() -> dict:
    return {"items": await database.collection("audit_events").find_many()}


app.include_router(auth.router)
app.include_router(platform.router)
app.include_router(agencies.router)
app.include_router(clients.router)
app.include_router(passengers.router)
app.include_router(requests.router)
app.include_router(offers.router)
app.include_router(bookings.router)
app.include_router(finance.router)
app.include_router(airline_intelligence.router)
app.include_router(documents.router)
app.include_router(portal.router)
app.include_router(reference.router)
