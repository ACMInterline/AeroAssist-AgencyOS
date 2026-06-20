from typing import Any, Dict, Iterable, List

from database import Database
from models import (
    Agency,
    AgencyStaffMembership,
    AgencyWorkspace,
    AuditEvent,
    GlobalReferenceRecord,
    PlatformRole,
    PlatformUser,
    SubscriptionStatus,
)


DEMO_OWNER_EMAIL = "owner@aeroassist.dev"
DEMO_AGENCY_SLUG = "demo-aeroassist-travel"


def reference_record(domain: str, key: str, label: str, description: str = "", metadata: Dict[str, Any] | None = None) -> GlobalReferenceRecord:
    return GlobalReferenceRecord(
        domain=domain,
        key=key,
        label=label,
        description=description or None,
        metadata=metadata or {},
    )


def core_reference_records() -> Iterable[GlobalReferenceRecord]:
    records = [
        reference_record("countries", "SK", "Slovakia"),
        reference_record("countries", "CZ", "Czechia"),
        reference_record("countries", "US", "United States"),
        reference_record("currencies", "EUR", "Euro"),
        reference_record("currencies", "USD", "US Dollar"),
        reference_record("currencies", "CZK", "Czech Koruna"),
        reference_record("timezones", "Europe/Bratislava", "Europe/Bratislava"),
        reference_record("timezones", "UTC", "UTC"),
    ]

    for role in ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]:
        records.append(reference_record("platform_roles", role, role.replace("_", " ").title()))

    for role in ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]:
        records.append(reference_record("agency_roles", role, role.replace("_", " ").title()))

    for status in ["prospect", "onboarding", "active", "suspended", "cancelled", "archived"]:
        records.append(reference_record("agency_statuses", status, status.replace("_", " ").title()))

    for status in ["trial", "active", "past_due", "suspended", "cancelled"]:
        records.append(reference_record("subscription_statuses", status, status.replace("_", " ").title()))

    for status in ["not_configured", "draft", "active", "suspended"]:
        records.append(reference_record("website_statuses", status, status.replace("_", " ").title()))

    for status in ["not_configured", "active", "suspended"]:
        records.append(reference_record("portal_statuses", status, status.replace("_", " ").title()))

    return records


async def seed_core_data(db: Database) -> Dict[str, Any]:
    users = db.collection("platform_users")
    agencies = db.collection("agencies")
    workspaces = db.collection("agency_workspaces")
    memberships = db.collection("agency_staff_memberships")
    references = db.collection("global_reference_records")
    audits = db.collection("audit_events")

    created: List[str] = []

    owner = await users.find_one({"email": DEMO_OWNER_EMAIL})
    if owner is None:
        owner_model = PlatformUser(
            email=DEMO_OWNER_EMAIL,
            full_name="Demo Platform Owner",
            global_role=PlatformRole.PLATFORM_OWNER,
        )
        owner = await users.insert_one(owner_model.model_dump(mode="json"))
        created.append("platform_user")

    agency = await agencies.find_one({"slug": DEMO_AGENCY_SLUG})
    if agency is None:
        agency_model = Agency(
            name="Demo AeroAssist Travel",
            slug=DEMO_AGENCY_SLUG,
            legal_name="Demo AeroAssist Travel s.r.o.",
            subscription_status=SubscriptionStatus.TRIAL,
        )
        agency = await agencies.insert_one(agency_model.model_dump(mode="json"))
        created.append("agency")

    workspace = await workspaces.find_one({"agency_id": agency["id"]})
    if workspace is None:
        workspace_model = AgencyWorkspace(
            agency_id=agency["id"],
            brand_name=agency["name"],
            primary_color="#2563eb",
            secondary_color="#0f172a",
        )
        await workspaces.insert_one(workspace_model.model_dump(mode="json"))
        created.append("agency_workspace")

    membership = await memberships.find_one({"agency_id": agency["id"], "user_id": owner["id"]})
    if membership is None:
        membership_model = AgencyStaffMembership(
            agency_id=agency["id"],
            user_id=owner["id"],
            agency_role="agency_owner",
            status="active",
            joined_at=owner["created_at"],
        )
        await memberships.insert_one(membership_model.model_dump(mode="json"))
        created.append("agency_staff_membership")

    for record in core_reference_records():
        existing = await references.find_one({"domain": record.domain, "key": record.key})
        if existing is None:
            await references.insert_one(record.model_dump(mode="json"))
            created.append(f"reference:{record.domain}:{record.key}")

    if created:
        event = AuditEvent(
            actor_user_id=owner["id"],
            event_type="seed.core_data",
            entity_type="platform",
            entity_id="core",
            summary="Seeded Phase 1 demo platform, agency, membership, and reference records.",
            metadata={"created": created},
        )
        await audits.insert_one(event.model_dump(mode="json"))

    return {
        "created": created,
        "demo_user_email": DEMO_OWNER_EMAIL,
        "demo_agency_slug": DEMO_AGENCY_SLUG,
    }
