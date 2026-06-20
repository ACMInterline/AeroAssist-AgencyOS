from fastapi import APIRouter, Depends

from auth import require_platform_role
from database import Database, get_database
from models import GlobalReferenceCreate, GlobalReferenceRecord
from services.seed_service import seed_core_data

router = APIRouter(prefix="/api/reference", tags=["reference"])


@router.get("")
async def list_reference(db: Database = Depends(get_database)) -> dict:
    return {"items": await db.collection("global_reference_records").find_many({"is_active": True})}


@router.get("/{domain}")
async def list_reference_domain(domain: str, db: Database = Depends(get_database)) -> dict:
    return {"domain": domain, "items": await db.collection("global_reference_records").find_many({"domain": domain, "is_active": True})}


@router.post("")
async def create_reference_record(
    payload: GlobalReferenceCreate,
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin"])),
    db: Database = Depends(get_database),
) -> dict:
    existing = await db.collection("global_reference_records").find_one({"domain": payload.domain, "key": payload.key})
    if existing:
        return {"record": existing, "created": False}
    record = GlobalReferenceRecord(**payload.model_dump())
    created = await db.collection("global_reference_records").insert_one(record.model_dump(mode="json"))
    return {"record": created, "created": True, "actor_user_id": user["id"]}


@router.post("/seed")
async def seed_reference(
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin"])),
    db: Database = Depends(get_database),
) -> dict:
    result = await seed_core_data(db)
    return {"ok": True, "seed": result, "actor_user_id": user["id"]}
