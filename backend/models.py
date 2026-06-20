from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class PlatformRole(str, Enum):
    PLATFORM_OWNER = "platform_owner"
    PLATFORM_ADMIN = "platform_admin"
    PLATFORM_KNOWLEDGE_EDITOR = "platform_knowledge_editor"
    PLATFORM_SUPPORT = "platform_support"


class AgencyRole(str, Enum):
    AGENCY_OWNER = "agency_owner"
    AGENCY_ADMIN = "agency_admin"
    AGENCY_AGENT = "agency_agent"
    AGENCY_ACCOUNTANT = "agency_accountant"
    AGENCY_READONLY = "agency_readonly"


class UserStatus(str, Enum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class AgencyStatus(str, Enum):
    PROSPECT = "prospect"
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class WorkspaceStatus(str, Enum):
    SETUP = "setup"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class WebsiteStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class PortalStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class BaseDocument(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class PlatformUser(BaseDocument):
    email: EmailStr
    full_name: str
    global_role: Optional[PlatformRole] = None
    status: UserStatus = UserStatus.ACTIVE


class PlatformUserCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    email: EmailStr
    full_name: str
    global_role: Optional[PlatformRole] = None
    status: UserStatus = UserStatus.ACTIVE


class Agency(BaseDocument):
    name: str
    slug: str
    legal_name: str
    status: AgencyStatus = AgencyStatus.ONBOARDING
    subscription_status: SubscriptionStatus = SubscriptionStatus.TRIAL
    default_currency: str = "EUR"
    country: str = "SK"
    timezone: str = "Europe/Bratislava"


class AgencyCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    name: str
    slug: str
    legal_name: str
    status: AgencyStatus = AgencyStatus.ONBOARDING
    subscription_status: SubscriptionStatus = SubscriptionStatus.TRIAL
    default_currency: str = "EUR"
    country: str = "SK"
    timezone: str = "Europe/Bratislava"


class AgencyUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    name: Optional[str] = None
    slug: Optional[str] = None
    legal_name: Optional[str] = None
    status: Optional[AgencyStatus] = None
    subscription_status: Optional[SubscriptionStatus] = None
    default_currency: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None


class AgencyWorkspace(BaseDocument):
    agency_id: str
    brand_name: str
    logo_url: Optional[str] = None
    primary_color: str = "#2563eb"
    secondary_color: str = "#0f172a"
    font_family: str = "Inter"
    website_status: WebsiteStatus = WebsiteStatus.NOT_CONFIGURED
    portal_status: PortalStatus = PortalStatus.NOT_CONFIGURED


class AgencyWorkspaceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    website_status: Optional[WebsiteStatus] = None
    portal_status: Optional[PortalStatus] = None


class AgencyStaffMembership(BaseDocument):
    agency_id: str
    user_id: str
    agency_role: AgencyRole
    status: UserStatus = UserStatus.INVITED
    invited_at: Optional[datetime] = Field(default_factory=now_utc)
    joined_at: Optional[datetime] = None


class AgencyStaffCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    email: EmailStr
    full_name: str
    agency_role: AgencyRole = AgencyRole.AGENCY_AGENT
    status: UserStatus = UserStatus.INVITED


class GlobalReferenceRecord(BaseDocument):
    domain: str
    key: str
    label: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class GlobalReferenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str
    key: str
    label: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    event_type: str
    entity_type: str
    entity_id: str
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)


class DemoLoginRequest(BaseModel):
    email: EmailStr = "owner@aeroassist.dev"


class ApiMessage(BaseModel):
    message: str
