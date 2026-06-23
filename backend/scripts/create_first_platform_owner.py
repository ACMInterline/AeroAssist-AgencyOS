#!/usr/bin/env python3
import argparse
import asyncio
import getpass
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import get_database
from models import AuthIdentity, AuthIdentityType, PlatformRole, PlatformUser, UserStatus
from security import hash_password, normalize_email


MIN_PASSWORD_LENGTH = 12


def prompt_required(label: str) -> str:
    value = input(f"{label}: ").strip()
    if not value:
        raise ValueError(f"{label} is required.")
    return value


def prompt_password() -> str:
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise ValueError("Passwords do not match.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    return password


async def create_owner(allow_existing_identities: bool) -> dict:
    db = await get_database()
    await db.connect()

    identity_count = await db.collection("auth_identities").count()
    if identity_count and not allow_existing_identities:
        raise RuntimeError(
            "Refusing to run because auth identities already exist. "
            "Use --allow-existing-identities only after verifying this is a controlled recovery/bootstrap action."
        )

    email = prompt_required("Owner email")
    full_name = prompt_required("Full name")
    password = prompt_password()
    normalized_email = normalize_email(email)

    existing_identity = await db.collection("auth_identities").find_one({"normalized_email": normalized_email})
    if existing_identity:
        raise RuntimeError("An auth identity already exists for that email.")

    existing_user = await db.collection("platform_users").find_one({"email": email})
    if existing_user:
        raise RuntimeError("A platform user already exists for that email.")

    user = PlatformUser(
        email=email,
        full_name=full_name,
        global_role=PlatformRole.PLATFORM_OWNER,
        status=UserStatus.ACTIVE,
    )
    created_user = await db.collection("platform_users").insert_one(user.model_dump(mode="json"))

    identity = AuthIdentity(
        email=email,
        normalized_email=normalized_email,
        password_hash=hash_password(password),
        identity_type=AuthIdentityType.PLATFORM_USER,
        status=UserStatus.ACTIVE,
        password_reset_required=False,
    )
    created_identity = await db.collection("auth_identities").insert_one(identity.model_dump(mode="json"))

    return {
        "platform_user_id": created_user["id"],
        "auth_identity_id": created_identity["id"],
        "email": created_user["email"],
        "role": created_user["global_role"],
        "status": created_user["status"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the first production platform owner.")
    parser.add_argument(
        "--allow-existing-identities",
        action="store_true",
        help="Allow running when other auth identities already exist. Duplicate email checks still apply.",
    )
    args = parser.parse_args()

    try:
        result = asyncio.run(create_owner(args.allow_existing_identities))
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: platform owner created.")
    print(f"platform_user_id: {result['platform_user_id']}")
    print(f"auth_identity_id: {result['auth_identity_id']}")
    print(f"email: {result['email']}")
    print(f"role: {result['role']}")
    print(f"status: {result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
