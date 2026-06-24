from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
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
    EMAIL_UNVERIFIED = "email_unverified"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class AuthIdentityType(str, Enum):
    PLATFORM_USER = "platform_user"
    AGENCY_STAFF = "agency_staff"
    CLIENT_PORTAL = "client_portal"


class AuthSessionStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class InvitationType(str, Enum):
    PLATFORM_USER = "platform_user"
    AGENCY_STAFF = "agency_staff"
    CLIENT_PORTAL = "client_portal"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CANCELLED = "cancelled"


class PortalActionType(str, Enum):
    REQUEST_SUBMITTED = "request_submitted"
    MESSAGE_SENT = "message_sent"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_REJECTED = "offer_rejected"
    DOCUMENT_ACKNOWLEDGED = "document_acknowledged"


class PortalActionStatus(str, Enum):
    RECEIVED = "received"
    STAFF_REVIEW_REQUIRED = "staff_review_required"
    PROCESSED = "processed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class PortalActionSourceEntityType(str, Enum):
    REQUEST = "request"
    OFFER = "offer"
    DOCUMENT = "document"
    CLIENT = "client"
    PASSENGER = "passenger"


class DocumentAcknowledgementType(str, Enum):
    VIEWED = "viewed"
    ACKNOWLEDGED = "acknowledged"
    ACCEPTED_TERMS = "accepted_terms"
    REJECTED = "rejected"


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


class WebsitePageStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class WebsitePageType(str, Enum):
    HOME = "home"
    ABOUT = "about"
    SERVICES = "services"
    CONTACT = "contact"
    CUSTOM = "custom"


class WebsiteSectionType(str, Enum):
    HERO = "hero"
    TEXT = "text"
    SERVICES = "services"
    CTA = "cta"
    CONTACT = "contact"
    INTAKE_LINK = "intake_link"
    SERVICE_CARDS = "service_cards"
    FEATURE_GRID = "feature_grid"
    PROCESS_STEPS = "process_steps"
    FAQ = "faq"
    CONTACT_CTA = "contact_cta"
    REQUEST_FORM_CTA = "request_form_cta"
    TESTIMONIALS = "testimonials"
    TRUST_BADGES = "trust_badges"
    IMAGE_TEXT = "image_text"
    CONTACT_DETAILS = "contact_details"
    LEGAL_TEXT = "legal_text"


class PortalStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class BrandingThemeMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class BrandingFontKey(str, Enum):
    INTER = "inter"
    QUICKSAND = "quicksand"
    MANROPE = "manrope"
    NUNITO_SANS = "nunito_sans"
    LATO = "lato"
    SOURCE_SANS_3 = "source_sans_3"
    IBM_PLEX_SANS = "ibm_plex_sans"
    PLUS_JAKARTA_SANS = "plus_jakarta_sans"
    ROBOTO = "roboto"
    SYSTEM_UI = "system_ui"


class BrandingRadiusKey(str, Enum):
    SQUARE = "square"
    SUBTLE = "subtle"
    ROUNDED = "rounded"
    SOFT = "soft"
    PILL = "pill"


class BrandingDensityKey(str, Enum):
    COMPACT = "compact"
    COMFORTABLE = "comfortable"
    SPACIOUS = "spacious"


class BrandingPaletteKey(str, Enum):
    AERO_BLUE = "aero_blue"
    MIDNIGHT_NAVY = "midnight_navy"
    GRAPHITE = "graphite"
    EMERALD_AVIATION = "emerald_aviation"
    SKY_CYAN = "sky_cyan"
    VIOLET_PREMIUM = "violet_premium"
    BURGUNDY_EXECUTIVE = "burgundy_executive"
    SANDSTONE = "sandstone"
    SLATE_MINIMAL = "slate_minimal"
    BLACK_GLASS = "black_glass"


class BrandingFieldStyleKey(str, Enum):
    OUTLINE = "outline"
    FILLED = "filled"
    SOFT_GLASS = "soft_glass"


class BrandingButtonStyleKey(str, Enum):
    SOLID = "solid"
    SOFT = "soft"
    OUTLINE = "outline"


class BrandingCalendarStyleKey(str, Enum):
    NATIVE_POLISHED = "native_polished"
    COMPACT = "compact"
    CARD = "card"


class BrandingCardStyleKey(str, Enum):
    FLAT = "flat"
    RAISED = "raised"
    OUTLINE = "outline"


class ClientType(str, Enum):
    INDIVIDUAL = "individual"
    FAMILY_HOUSEHOLD = "family_household"
    ORGANIZATION = "organization"


class ClientPortalStatus(str, Enum):
    NO_PORTAL_ACCESS = "no_portal_access"
    INVITED = "invited"
    EMAIL_UNVERIFIED = "email_unverified"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class ClientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class PassengerType(str, Enum):
    ADT = "ADT"
    CHD = "CHD"
    INF = "INF"
    YTH = "YTH"
    SRC = "SRC"
    STU = "STU"
    UMNR = "UMNR"
    INS = "INS"
    OTHER = "other"


class PassengerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DUPLICATE_MERGED = "duplicate_merged"


class RelationshipType(str, Enum):
    SELF = "self"
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"
    GUARDIAN = "guardian"
    EMPLOYEE = "employee"
    ASSISTANT = "assistant"
    COMPANY_TRAVELER = "company_traveler"
    OTHER = "other"


class ConsentStatus(str, Enum):
    PENDING = "pending"
    GRANTED = "granted"
    REVOKED = "revoked"
    EXPIRED = "expired"
    NOT_REQUIRED = "not_required"


class RelationshipStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class RequestStatus(str, Enum):
    DRAFT = "draft"
    NEW = "new"
    TRIAGE = "triage"
    WAITING_FOR_CLIENT = "waiting_for_client"
    IN_PROGRESS = "in_progress"
    READY_FOR_OFFER = "ready_for_offer"
    OFFER_CREATED = "offer_created"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class RequestPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RequestSource(str, Enum):
    STAFF_CREATED = "staff_created"
    WEBSITE_FORM = "website_form"
    PUBLIC_WEBSITE = "public_website"
    CLIENT_PORTAL = "client_portal"
    PHONE = "phone"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WALK_IN = "walk_in"
    IMPORTED = "imported"
    INTERNAL = "internal"


class RequestIntakeSource(str, Enum):
    PUBLIC_WEBSITE = "public_website"
    AGENCY_WEBSITE = "agency_website"
    STAFF_MANUAL = "staff_manual"
    IMPORTED = "imported"
    INTERNAL = "internal"
    CLIENT_PORTAL = "client_portal"


class RequestIntakeStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    CONVERTED = "converted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    ARCHIVED = "archived"


class TripType(str, Enum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"
    MULTI_CITY = "multi_city"
    UNKNOWN = "unknown"


class OperationalServiceCategory(str, Enum):
    MOBILITY_ASSISTANCE = "mobility_assistance"
    MEDICAL_TRAVEL = "medical_travel"
    PET_TRAVEL = "pet_travel"
    UNACCOMPANIED_MINOR = "unaccompanied_minor"
    CHILD_TRAVEL_SUPPORT = "child_travel_support"
    SPECIAL_BAGGAGE = "special_baggage"
    SPORTS_EQUIPMENT = "sports_equipment"
    DOCUMENTS_VISA = "documents_visa"
    BOOKING_PLANNING = "booking_planning"
    DISRUPTION_SUPPORT = "disruption_support"
    REFUND_EXCHANGE = "refund_exchange"
    CLAIMS_SUPPORT = "claims_support"
    AIRPORT_ASSISTANCE = "airport_assistance"
    OTHER = "other"


class RequestPassengerRole(str, Enum):
    TRAVELER = "traveler"
    BENEFICIARY = "beneficiary"
    ACCOMPANYING_ADULT = "accompanying_adult"
    GUARDIAN = "guardian"
    EMERGENCY_CONTACT = "emergency_contact"
    PAYER_CONTACT = "payer_contact"


class RequestedServiceStatus(str, Enum):
    REQUESTED = "requested"
    INFO_NEEDED = "info_needed"
    CHECKING = "checking"
    FEASIBLE = "feasible"
    CONDITIONAL = "conditional"
    NOT_AVAILABLE = "not_available"
    CANCELLED = "cancelled"


class MessageSenderType(str, Enum):
    STAFF = "staff"
    CLIENT = "client"
    SYSTEM = "system"


class Visibility(str, Enum):
    INTERNAL = "internal"
    CLIENT_VISIBLE = "client_visible"


class RequestTaskStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    DONE = "done"
    CANCELLED = "cancelled"


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


class AuthIdentity(BaseDocument):
    email: EmailStr
    normalized_email: str
    password_hash: str
    identity_type: AuthIdentityType
    status: UserStatus = UserStatus.INVITED
    last_login_at: Optional[datetime] = None
    failed_login_count: int = 0
    password_reset_required: bool = False


class AuthSession(BaseDocument):
    identity_id: str
    token_hash: str
    status: AuthSessionStatus = AuthSessionStatus.ACTIVE
    issued_at: datetime = Field(default_factory=now_utc)
    expires_at: datetime
    last_seen_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class Invitation(BaseDocument):
    agency_id: Optional[str] = None
    workspace_id: Optional[str] = None
    invited_email: EmailStr
    invited_name: Optional[str] = None
    normalized_email: str
    invitation_type: InvitationType
    target_role: Optional[str] = None
    target_client_id: Optional[str] = None
    target_user_id: Optional[str] = None
    accepted_by_user_id: Optional[str] = None
    accepted_by_identity_id: Optional[str] = None
    invited_by_user_id: Optional[str] = None
    status: InvitationStatus = InvitationStatus.PENDING
    token_hash: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoked_by_user_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str


class InvitationAcceptRequest(BaseModel):
    token: str
    password: str
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None


class StaffInvitationCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    email: EmailStr
    invited_name: Optional[str] = None
    full_name: Optional[str] = None
    workspace_id: Optional[str] = None
    agency_role: AgencyRole = AgencyRole.AGENCY_AGENT


class ClientPortalInvitationCreate(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None


class PortalActionEvent(BaseDocument):
    agency_id: str
    client_id: str
    portal_account_id: Optional[str] = None
    actor_identity_id: Optional[str] = None
    action_type: PortalActionType
    source_entity_type: PortalActionSourceEntityType
    source_entity_id: Optional[str] = None
    status: PortalActionStatus = PortalActionStatus.STAFF_REVIEW_REQUIRED
    summary: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class DocumentAcknowledgement(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    rendered_document_id: str
    client_id: str
    portal_account_id: Optional[str] = None
    acknowledged_by_identity_id: Optional[str] = None
    acknowledgement_type: DocumentAcknowledgementType = DocumentAcknowledgementType.ACKNOWLEDGED
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)


class PortalRequestSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    route_summary: Optional[str] = None
    requested_departure_date: Optional[date] = None
    requested_return_date: Optional[date] = None
    passenger_ids: List[str] = Field(default_factory=list)
    requested_services: List[str] = Field(default_factory=list)
    client_notes: Optional[str] = None


class PortalMessageSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_text: str
    requires_follow_up: bool = True


class PortalOfferDecisionSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: Optional[str] = None


class PortalDocumentAcknowledgeSubmit(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    acknowledgement_type: DocumentAcknowledgementType = DocumentAcknowledgementType.ACKNOWLEDGED
    message: Optional[str] = None


class PortalActionProcessSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: PortalActionStatus = PortalActionStatus.PROCESSED


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
    name: Optional[str] = None
    brand_name: str
    status: UserStatus = UserStatus.ACTIVE
    default_currency: Optional[str] = None
    timezone: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str = "#2563eb"
    secondary_color: str = "#0f172a"
    font_family: str = "Inter"
    website_status: WebsiteStatus = WebsiteStatus.NOT_CONFIGURED
    portal_status: PortalStatus = PortalStatus.NOT_CONFIGURED


class AgencyWorkspaceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    name: str
    brand_name: Optional[str] = None
    default_currency: str = "EUR"
    timezone: str = "Europe/Bratislava"
    status: UserStatus = UserStatus.ACTIVE


class AgencyWorkspaceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    name: Optional[str] = None
    brand_name: Optional[str] = None
    status: Optional[UserStatus] = None
    default_currency: Optional[str] = None
    timezone: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    website_status: Optional[WebsiteStatus] = None
    portal_status: Optional[PortalStatus] = None


class AgencyBrandingSettings(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    logo_storage_record_id: Optional[str] = None
    logo_url: Optional[str] = None
    brand_name: Optional[str] = None
    font_family_key: BrandingFontKey = BrandingFontKey.INTER
    corner_radius_key: BrandingRadiusKey = BrandingRadiusKey.ROUNDED
    density_key: BrandingDensityKey = BrandingDensityKey.COMFORTABLE
    theme_mode: BrandingThemeMode = BrandingThemeMode.LIGHT
    color_palette_key: BrandingPaletteKey = BrandingPaletteKey.AERO_BLUE
    field_style_key: BrandingFieldStyleKey = BrandingFieldStyleKey.OUTLINE
    button_style_key: BrandingButtonStyleKey = BrandingButtonStyleKey.SOLID
    calendar_style_key: BrandingCalendarStyleKey = BrandingCalendarStyleKey.NATIVE_POLISHED
    card_style_key: BrandingCardStyleKey = BrandingCardStyleKey.OUTLINE
    updated_by_user_id: Optional[str] = None
    updated_by_email: Optional[EmailStr] = None
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)


class AgencyBrandingSettingsUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    workspace_id: Optional[str] = None
    brand_name: Optional[str] = None
    font_family_key: Optional[BrandingFontKey] = None
    corner_radius_key: Optional[BrandingRadiusKey] = None
    density_key: Optional[BrandingDensityKey] = None
    theme_mode: Optional[BrandingThemeMode] = None
    color_palette_key: Optional[BrandingPaletteKey] = None
    field_style_key: Optional[BrandingFieldStyleKey] = None
    button_style_key: Optional[BrandingButtonStyleKey] = None
    calendar_style_key: Optional[BrandingCalendarStyleKey] = None
    card_style_key: Optional[BrandingCardStyleKey] = None


class AgencyLogoUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    content_type: str
    data_base64: str


class AgencyWebsiteSettings(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    site_name: str
    slug: str
    tagline: Optional[str] = None
    status: WebsiteStatus = WebsiteStatus.DRAFT
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    show_request_cta: bool = True
    published_at: Optional[datetime] = None
    updated_by_user_id: Optional[str] = None
    updated_by_email: Optional[EmailStr] = None
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)


class AgencyWebsiteSettingsUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    workspace_id: Optional[str] = None
    site_name: Optional[str] = None
    slug: Optional[str] = None
    tagline: Optional[str] = None
    status: Optional[WebsiteStatus] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    show_request_cta: Optional[bool] = None


class AgencyWebsiteSection(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    section_type: WebsiteSectionType = WebsiteSectionType.TEXT
    eyebrow: Optional[str] = None
    heading: str
    headline: Optional[str] = None
    subheadline: Optional[str] = None
    body: Optional[str] = None
    cta_label: Optional[str] = None
    cta_href: Optional[str] = None
    primary_cta_label: Optional[str] = None
    primary_cta_target: Optional[str] = None
    secondary_cta_label: Optional[str] = None
    secondary_cta_target: Optional[str] = None
    image_asset_id: Optional[str] = None
    alignment: Optional[str] = None
    image_position: Optional[str] = None
    items: List[str] = Field(default_factory=list)
    cards: List[Dict[str, Any]] = Field(default_factory=list)
    sort_order: int = 0


class AgencyWebsitePage(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    page_type: WebsitePageType = WebsitePageType.CUSTOM
    title: str
    slug: str
    status: WebsitePageStatus = WebsitePageStatus.DRAFT
    sections: List[AgencyWebsiteSection] = Field(default_factory=list)
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    published_at: Optional[datetime] = None
    updated_by_user_id: Optional[str] = None
    updated_by_email: Optional[EmailStr] = None
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)


class AgencyWebsitePageCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    workspace_id: Optional[str] = None
    page_type: WebsitePageType = WebsitePageType.CUSTOM
    title: str
    slug: str
    status: WebsitePageStatus = WebsitePageStatus.DRAFT
    sections: List[AgencyWebsiteSection] = Field(default_factory=list)
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None


class AgencyWebsitePageUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    workspace_id: Optional[str] = None
    page_type: Optional[WebsitePageType] = None
    title: Optional[str] = None
    slug: Optional[str] = None
    status: Optional[WebsitePageStatus] = None
    sections: Optional[List[AgencyWebsiteSection]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None


class AgencyStaffMembership(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    user_id: str
    identity_id: Optional[str] = None
    email: Optional[EmailStr] = None
    normalized_email: Optional[str] = None
    agency_role: AgencyRole
    status: UserStatus = UserStatus.INVITED
    invited_at: Optional[datetime] = Field(default_factory=now_utc)
    joined_at: Optional[datetime] = None
    created_from_invitation_id: Optional[str] = None


class AgencyStaffCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    email: EmailStr
    full_name: str
    agency_role: AgencyRole = AgencyRole.AGENCY_AGENT
    status: UserStatus = UserStatus.INVITED


class ClientProfile(BaseDocument):
    agency_id: str
    client_type: ClientType = ClientType.INDIVIDUAL
    display_name: str
    legal_name: Optional[str] = None
    primary_email: EmailStr
    primary_phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    postal_code: Optional[str] = None
    preferred_language: str = "en"
    default_currency: str = "EUR"
    tax_id: Optional[str] = None
    company_registration_number: Optional[str] = None
    portal_status: ClientPortalStatus = ClientPortalStatus.NO_PORTAL_ACCESS
    marketing_consent: bool = False
    data_processing_consent: bool = False
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    status: ClientStatus = ClientStatus.ACTIVE


class ClientProfileCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_type: ClientType = ClientType.INDIVIDUAL
    display_name: str
    legal_name: Optional[str] = None
    primary_email: EmailStr
    primary_phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    postal_code: Optional[str] = None
    preferred_language: str = "en"
    default_currency: str = "EUR"
    tax_id: Optional[str] = None
    company_registration_number: Optional[str] = None
    portal_status: ClientPortalStatus = ClientPortalStatus.NO_PORTAL_ACCESS
    marketing_consent: bool = False
    data_processing_consent: bool = False
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    status: ClientStatus = ClientStatus.ACTIVE


class ClientProfileUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_type: Optional[ClientType] = None
    display_name: Optional[str] = None
    legal_name: Optional[str] = None
    primary_email: Optional[EmailStr] = None
    primary_phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    postal_code: Optional[str] = None
    preferred_language: Optional[str] = None
    default_currency: Optional[str] = None
    tax_id: Optional[str] = None
    company_registration_number: Optional[str] = None
    portal_status: Optional[ClientPortalStatus] = None
    marketing_consent: Optional[bool] = None
    data_processing_consent: Optional[bool] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    status: Optional[ClientStatus] = None


class PortalAccessMapping(BaseDocument):
    agency_id: str
    client_id: str
    user_email: EmailStr
    portal_status: ClientPortalStatus = ClientPortalStatus.ACTIVE
    display_name: str
    last_login_at: Optional[datetime] = None


class PassengerProfile(BaseDocument):
    agency_id: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    display_name: str
    date_of_birth: date
    passenger_type: PassengerType = PassengerType.ADT
    gender: Optional[str] = None
    nationality: Optional[str] = None
    residence_country: Optional[str] = None
    primary_language: str = "en"
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    passport_expiry: Optional[date] = None
    travel_document_notes: Optional[str] = None
    known_assistance_needs: Optional[str] = None
    medical_notes_internal: Optional[str] = None
    meal_preferences: Optional[str] = None
    loyalty_numbers: List[Dict[str, str]] = Field(default_factory=list)
    status: PassengerStatus = PassengerStatus.ACTIVE
    merged_into_passenger_id: Optional[str] = None


class PassengerProfileCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    display_name: Optional[str] = None
    date_of_birth: date
    passenger_type: PassengerType = PassengerType.ADT
    gender: Optional[str] = None
    nationality: Optional[str] = None
    residence_country: Optional[str] = None
    primary_language: str = "en"
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    passport_expiry: Optional[date] = None
    travel_document_notes: Optional[str] = None
    known_assistance_needs: Optional[str] = None
    medical_notes_internal: Optional[str] = None
    meal_preferences: Optional[str] = None
    loyalty_numbers: List[Dict[str, str]] = Field(default_factory=list)
    status: PassengerStatus = PassengerStatus.ACTIVE


class PassengerProfileUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    passenger_type: Optional[PassengerType] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    residence_country: Optional[str] = None
    primary_language: Optional[str] = None
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    passport_expiry: Optional[date] = None
    travel_document_notes: Optional[str] = None
    known_assistance_needs: Optional[str] = None
    medical_notes_internal: Optional[str] = None
    meal_preferences: Optional[str] = None
    loyalty_numbers: Optional[List[Dict[str, str]]] = None
    status: Optional[PassengerStatus] = None


class ClientPassengerRelationship(BaseDocument):
    agency_id: str
    client_id: str
    passenger_id: str
    relationship_type: RelationshipType
    can_view: bool = True
    can_edit: bool = False
    can_upload_documents: bool = False
    can_request_travel: bool = True
    can_pay: bool = False
    can_receive_notifications: bool = True
    consent_status: ConsentStatus = ConsentStatus.PENDING
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    status: RelationshipStatus = RelationshipStatus.ACTIVE
    notes: Optional[str] = None


class ClientPassengerRelationshipCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_id: str
    passenger_id: str
    relationship_type: RelationshipType
    can_view: bool = True
    can_edit: bool = False
    can_upload_documents: bool = False
    can_request_travel: bool = True
    can_pay: bool = False
    can_receive_notifications: bool = True
    consent_status: ConsentStatus = ConsentStatus.PENDING
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    status: RelationshipStatus = RelationshipStatus.ACTIVE
    notes: Optional[str] = None


class ClientPassengerRelationshipUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    relationship_type: Optional[RelationshipType] = None
    can_view: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_upload_documents: Optional[bool] = None
    can_request_travel: Optional[bool] = None
    can_pay: Optional[bool] = None
    can_receive_notifications: Optional[bool] = None
    consent_status: Optional[ConsentStatus] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    status: Optional[RelationshipStatus] = None
    notes: Optional[str] = None


class PassengerMergeRequest(BaseModel):
    target_passenger_id: str
    reason: str
    retained_fields_summary: Dict[str, Any] = Field(default_factory=dict)


class PassengerMergeAudit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    source_passenger_id: str
    target_passenger_id: str
    merged_by_user_id: str
    reason: str
    retained_fields_summary: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)


class TravelRequest(BaseDocument):
    agency_id: str
    client_id: str
    created_by_user_id: str
    request_reference: str
    title: str
    status: RequestStatus = RequestStatus.NEW
    priority: RequestPriority = RequestPriority.NORMAL
    source: RequestSource = RequestSource.STAFF_CREATED
    requested_departure_date: Optional[date] = None
    requested_return_date: Optional[date] = None
    trip_type: TripType = TripType.UNKNOWN
    route_summary: Optional[str] = None
    service_summary: Optional[str] = None
    passenger_count: int = 0
    service_count: int = 0
    urgency_reason: Optional[str] = None
    client_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    assigned_user_id: Optional[str] = None
    source_intake_id: Optional[str] = None
    intake_payload_snapshot: Dict[str, Any] = Field(default_factory=dict)
    builder_payload_snapshot: Dict[str, Any] = Field(default_factory=dict)
    closed_at: Optional[datetime] = None


class TravelRequestCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_id: str
    title: str
    status: RequestStatus = RequestStatus.NEW
    priority: RequestPriority = RequestPriority.NORMAL
    source: RequestSource = RequestSource.STAFF_CREATED
    requested_departure_date: Optional[date] = None
    requested_return_date: Optional[date] = None
    trip_type: TripType = TripType.UNKNOWN
    route_summary: Optional[str] = None
    service_summary: Optional[str] = None
    urgency_reason: Optional[str] = None
    client_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    assigned_user_id: Optional[str] = None
    source_intake_id: Optional[str] = None
    intake_payload_snapshot: Dict[str, Any] = Field(default_factory=dict)
    builder_payload_snapshot: Dict[str, Any] = Field(default_factory=dict)


class TravelRequestUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    title: Optional[str] = None
    status: Optional[RequestStatus] = None
    priority: Optional[RequestPriority] = None
    source: Optional[RequestSource] = None
    requested_departure_date: Optional[date] = None
    requested_return_date: Optional[date] = None
    trip_type: Optional[TripType] = None
    route_summary: Optional[str] = None
    service_summary: Optional[str] = None
    urgency_reason: Optional[str] = None
    client_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    assigned_user_id: Optional[str] = None
    source_intake_id: Optional[str] = None
    intake_payload_snapshot: Optional[Dict[str, Any]] = None
    builder_payload_snapshot: Optional[Dict[str, Any]] = None


class RequestIntakeContactSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    marketing_consent: bool = False
    data_processing_consent: bool = False
    privacy_policy_accepted: bool = False


class RequestIntakeTravelSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    passenger_count: int = 1
    itinerary_notes: Optional[str] = None


class RequestIntakeServiceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_service_categories: List[str] = Field(default_factory=list)
    mobility_assistance: bool = False
    medical_travel: bool = False
    pet_travel: bool = False
    child_or_unaccompanied_minor: bool = False
    special_baggage: bool = False
    documents_or_visa: bool = False
    disruption_or_claims: bool = False
    booking_or_planning: bool = False
    other: bool = False
    other_details: Optional[str] = None


class RequestIntake(BaseDocument):
    agency_id: Optional[str] = None
    workspace_id: Optional[str] = None
    source_site_slug: Optional[str] = None
    source_page_slug: Optional[str] = None
    source_website_profile_id: Optional[str] = None
    source_website_page_id: Optional[str] = None
    reference_code: str
    source: RequestIntakeSource = RequestIntakeSource.PUBLIC_WEBSITE
    status: RequestIntakeStatus = RequestIntakeStatus.NEW
    contact_snapshot: RequestIntakeContactSnapshot
    travel_summary: RequestIntakeTravelSummary
    service_summary: RequestIntakeServiceSummary
    canonical_payload: Dict[str, Any] = Field(default_factory=dict)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    normalized_payload: Optional[Dict[str, Any]] = None
    priority: RequestPriority = RequestPriority.NORMAL
    assigned_to: Optional[str] = None
    triage_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    converted_request_id: Optional[str] = None
    converted_at: Optional[datetime] = None
    converted_by: Optional[str] = None
    duplicate_of_intake_id: Optional[str] = None
    action_reason: Optional[str] = None


class PublicRequestIntakeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contact: RequestIntakeContactSnapshot
    travel: RequestIntakeTravelSummary
    services: RequestIntakeServiceSummary
    request_details: Optional[str] = None


class StaffRequestIntakeCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    workspace_id: Optional[str] = None
    source: RequestIntakeSource = RequestIntakeSource.STAFF_MANUAL
    contact: RequestIntakeContactSnapshot
    travel: RequestIntakeTravelSummary
    services: RequestIntakeServiceSummary
    priority: RequestPriority = RequestPriority.NORMAL
    assigned_to: Optional[str] = None
    triage_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    request_details: Optional[str] = None


class RequestIntakeTriageUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    workspace_id: Optional[str] = None
    priority: Optional[RequestPriority] = None
    assigned_to: Optional[str] = None
    triage_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class RequestIntakeAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: Optional[str] = None
    duplicate_of_intake_id: Optional[str] = None


class RequestStatusUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: RequestStatus
    summary: Optional[str] = None


class RequestPassenger(BaseDocument):
    agency_id: str
    request_id: str
    passenger_id: str
    client_passenger_relationship_id: Optional[str] = None
    role_in_request: RequestPassengerRole = RequestPassengerRole.TRAVELER
    is_primary_traveler: bool = False
    service_needs_summary: Optional[str] = None
    snapshot_display_name: str
    snapshot_date_of_birth: date
    snapshot_passenger_type: str
    status: str = "active"


class RequestPassengerCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    passenger_id: str
    client_passenger_relationship_id: Optional[str] = None
    role_in_request: RequestPassengerRole = RequestPassengerRole.TRAVELER
    is_primary_traveler: bool = False
    service_needs_summary: Optional[str] = None


class RequestPassengerUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_passenger_relationship_id: Optional[str] = None
    role_in_request: Optional[RequestPassengerRole] = None
    is_primary_traveler: Optional[bool] = None
    service_needs_summary: Optional[str] = None


class RequestSegment(BaseDocument):
    agency_id: str
    request_id: str
    sequence: int
    origin_text: str
    origin_airport_code: Optional[str] = None
    origin_city: Optional[str] = None
    origin_country: Optional[str] = None
    destination_text: str
    destination_airport_code: Optional[str] = None
    destination_city: Optional[str] = None
    destination_country: Optional[str] = None
    departure_date: Optional[date] = None
    departure_time_window: Optional[str] = None
    arrival_date: Optional[date] = None
    arrival_time_window: Optional[str] = None
    marketing_airline: Optional[str] = None
    operating_airline: Optional[str] = None
    preferred_airline_code: Optional[str] = None
    preferred_flight_number: Optional[str] = None
    cabin_preference: Optional[str] = None
    notes: Optional[str] = None
    status: str = "active"


class RequestSegmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    origin_text: str
    origin_airport_code: Optional[str] = None
    origin_city: Optional[str] = None
    origin_country: Optional[str] = None
    destination_text: str
    destination_airport_code: Optional[str] = None
    destination_city: Optional[str] = None
    destination_country: Optional[str] = None
    departure_date: Optional[date] = None
    departure_time_window: Optional[str] = None
    arrival_date: Optional[date] = None
    arrival_time_window: Optional[str] = None
    marketing_airline: Optional[str] = None
    operating_airline: Optional[str] = None
    preferred_airline_code: Optional[str] = None
    preferred_flight_number: Optional[str] = None
    cabin_preference: Optional[str] = None
    notes: Optional[str] = None


class RequestSegmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: Optional[int] = None
    origin_text: Optional[str] = None
    origin_airport_code: Optional[str] = None
    origin_city: Optional[str] = None
    origin_country: Optional[str] = None
    destination_text: Optional[str] = None
    destination_airport_code: Optional[str] = None
    destination_city: Optional[str] = None
    destination_country: Optional[str] = None
    departure_date: Optional[date] = None
    departure_time_window: Optional[str] = None
    arrival_date: Optional[date] = None
    arrival_time_window: Optional[str] = None
    marketing_airline: Optional[str] = None
    operating_airline: Optional[str] = None
    preferred_airline_code: Optional[str] = None
    preferred_flight_number: Optional[str] = None
    cabin_preference: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class RequestedService(BaseDocument):
    agency_id: str
    request_id: str
    passenger_id: Optional[str] = None
    service_code: str
    service_name: str
    service_category: str
    status: RequestedServiceStatus = RequestedServiceStatus.REQUESTED
    details: Optional[str] = None
    detail_payload: Dict[str, Any] = Field(default_factory=dict)
    passenger_ids: List[str] = Field(default_factory=list)
    segment_ids: List[str] = Field(default_factory=list)
    applies_to_all_passengers: bool = True
    applies_to_all_segments: bool = True
    client_visible_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    requires_documents: bool = False
    requires_airline_approval: bool = False


class RequestedServiceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    passenger_id: Optional[str] = None
    service_code: str
    service_name: str
    service_category: str
    status: RequestedServiceStatus = RequestedServiceStatus.REQUESTED
    details: Optional[str] = None
    detail_payload: Dict[str, Any] = Field(default_factory=dict)
    passenger_ids: List[str] = Field(default_factory=list)
    segment_ids: List[str] = Field(default_factory=list)
    applies_to_all_passengers: bool = True
    applies_to_all_segments: bool = True
    client_visible_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    requires_documents: bool = False
    requires_airline_approval: bool = False


class RequestedServiceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    passenger_id: Optional[str] = None
    service_code: Optional[str] = None
    service_name: Optional[str] = None
    service_category: Optional[str] = None
    status: Optional[RequestedServiceStatus] = None
    details: Optional[str] = None
    detail_payload: Optional[Dict[str, Any]] = None
    passenger_ids: Optional[List[str]] = None
    segment_ids: Optional[List[str]] = None
    applies_to_all_passengers: Optional[bool] = None
    applies_to_all_segments: Optional[bool] = None
    client_visible_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    requires_documents: Optional[bool] = None
    requires_airline_approval: Optional[bool] = None


class OperationalRequestBuilderClient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    notes: Optional[str] = None


class OperationalRequestBuilderPassenger(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passenger_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    passenger_type: str = "adult"
    mobility_notes: Optional[str] = None
    medical_notes: Optional[str] = None
    notes: Optional[str] = None


class OperationalRequestBuilderSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    origin_text: str
    destination_text: str
    departure_date: Optional[date] = None
    departure_time_window: Optional[str] = None
    arrival_date: Optional[date] = None
    arrival_time_window: Optional[str] = None
    marketing_airline: Optional[str] = None
    operating_airline: Optional[str] = None
    flight_number: Optional[str] = None
    cabin_preference: Optional[str] = None
    notes: Optional[str] = None


class OperationalRequestBuilderService(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    category: OperationalServiceCategory
    details: Dict[str, Any] = Field(default_factory=dict)
    passenger_ids: List[str] = Field(default_factory=list)
    segment_ids: List[str] = Field(default_factory=list)
    applies_to_all_passengers: bool = True
    applies_to_all_segments: bool = True
    notes: Optional[str] = None


class OperationalRequestBuilderCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client: OperationalRequestBuilderClient
    passengers: List[OperationalRequestBuilderPassenger] = Field(default_factory=list)
    trip_type: TripType = TripType.UNKNOWN
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    route_notes: Optional[str] = None
    segments: List[OperationalRequestBuilderSegment] = Field(default_factory=list)
    services: List[OperationalRequestBuilderService] = Field(default_factory=list)
    title: Optional[str] = None
    status: RequestStatus = RequestStatus.NEW
    priority: RequestPriority = RequestPriority.NORMAL
    source: RequestSource = RequestSource.STAFF_CREATED
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class RequestMessage(BaseDocument):
    agency_id: str
    request_id: str
    sender_user_id: Optional[str] = None
    sender_type: MessageSenderType = MessageSenderType.STAFF
    visibility: Visibility = Visibility.INTERNAL
    message_text: str


class RequestMessageCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    sender_type: MessageSenderType = MessageSenderType.STAFF
    visibility: Visibility = Visibility.INTERNAL
    message_text: str


class RequestTask(BaseDocument):
    agency_id: str
    request_id: str
    assigned_user_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: RequestTaskStatus = RequestTaskStatus.OPEN
    priority: RequestPriority = RequestPriority.NORMAL
    due_at: Optional[datetime] = None
    visibility: Visibility = Visibility.INTERNAL
    completed_at: Optional[datetime] = None


class RequestTaskCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    assigned_user_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: RequestTaskStatus = RequestTaskStatus.OPEN
    priority: RequestPriority = RequestPriority.NORMAL
    due_at: Optional[datetime] = None
    visibility: Visibility = Visibility.INTERNAL


class RequestTaskUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    assigned_user_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[RequestTaskStatus] = None
    priority: Optional[RequestPriority] = None
    due_at: Optional[datetime] = None
    visibility: Optional[Visibility] = None


class RequestTimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    request_id: str
    event_type: str
    actor_user_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    visibility: Visibility = Visibility.INTERNAL
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)


class OfferStatus(str, Enum):
    DRAFT = "draft"
    READY_TO_SEND = "ready_to_send"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    ARCHIVED = "archived"


class OfferSource(str, Enum):
    REQUEST = "request"
    CLIENT_PROFILE = "client_profile"
    PASSENGER_PROFILE = "passenger_profile"
    AIRLINE_RESEARCH = "airline_research"
    MANUAL = "manual"
    IMPORTED_GDS_TEXT = "imported_gds_text"
    OTHER = "other"


class OfferRouteStatus(str, Enum):
    DRAFT = "draft"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    WITHDRAWN = "withdrawn"


class SourceChannel(str, Enum):
    GDS = "gds"
    AIRLINE_PORTAL = "airline_portal"
    OTA_AFFILIATE = "ota_affiliate"
    DIRECT_AIRLINE_WEBSITE = "direct_airline_website"
    SUPPLIER_EMAIL = "supplier_email"
    PHONE = "phone"
    MANUAL = "manual"
    MIXED = "mixed"


class ConnectionQuality(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    RISKY = "risky"
    NOT_RECOMMENDED = "not_recommended"
    UNKNOWN = "unknown"


class FareOptionStatus(str, Enum):
    DRAFT = "draft"
    COMPLETE = "complete"
    UNAVAILABLE = "unavailable"
    WITHDRAWN = "withdrawn"


class RefundableStatus(str, Enum):
    NON_REFUNDABLE = "non_refundable"
    PARTIALLY_REFUNDABLE = "partially_refundable"
    REFUNDABLE = "refundable"
    UNKNOWN = "unknown"


class ChangeabilityStatus(str, Enum):
    NO_CHANGES = "no_changes"
    CHANGES_WITH_FEE = "changes_with_fee"
    FLEXIBLE = "flexible"
    UNKNOWN = "unknown"


class PriceLineType(str, Enum):
    AIRFARE = "airfare"
    TAXES = "taxes"
    AIRLINE_ANCILLARY = "airline_ancillary"
    AGENCY_SERVICE_FEE = "agency_service_fee"
    DOCUMENT_SERVICE_FEE = "document_service_fee"
    SPECIAL_ASSISTANCE_FEE = "special_assistance_fee"
    DISCOUNT = "discount"
    MARKUP = "markup"
    OTHER = "other"


class ServiceSupportStatus(str, Enum):
    SUPPORTED = "supported"
    LIKELY_SUPPORTED = "likely_supported"
    NEEDS_AIRLINE_CONFIRMATION = "needs_airline_confirmation"
    DOCUMENTS_REQUIRED = "documents_required"
    CHARGEABLE = "chargeable"
    NOT_SUPPORTED = "not_supported"
    UNKNOWN = "unknown"


class Offer(BaseDocument):
    agency_id: str
    offer_reference: str
    client_id: str
    request_id: Optional[str] = None
    created_by_user_id: str
    assigned_user_id: Optional[str] = None
    title: str
    status: OfferStatus = OfferStatus.DRAFT
    source: OfferSource = OfferSource.MANUAL
    currency: str = "EUR"
    client_language: str = "en"
    valid_until: Optional[date] = None
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    internal_notes: Optional[str] = None
    client_visible_intro: Optional[str] = None
    client_visible_terms: Optional[str] = None
    snapshot_at_send: Optional[datetime] = None
    sent_snapshot: Optional[Dict[str, Any]] = None
    route_alternative_count: int = 0
    fare_option_count: int = 0
    total_min_amount: Optional[float] = None
    total_max_amount: Optional[float] = None
    recommended_route_alternative_id: Optional[str] = None
    recommended_fare_option_id: Optional[str] = None


class OfferCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_id: str
    request_id: Optional[str] = None
    assigned_user_id: Optional[str] = None
    title: str
    status: OfferStatus = OfferStatus.DRAFT
    source: OfferSource = OfferSource.MANUAL
    currency: str = "EUR"
    client_language: str = "en"
    valid_until: Optional[date] = None
    internal_notes: Optional[str] = None
    client_visible_intro: Optional[str] = None
    client_visible_terms: Optional[str] = None


class OfferUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    title: Optional[str] = None
    status: Optional[OfferStatus] = None
    assigned_user_id: Optional[str] = None
    currency: Optional[str] = None
    client_language: Optional[str] = None
    valid_until: Optional[date] = None
    internal_notes: Optional[str] = None
    client_visible_intro: Optional[str] = None
    client_visible_terms: Optional[str] = None
    recommended_route_alternative_id: Optional[str] = None
    recommended_fare_option_id: Optional[str] = None


class CreateOfferFromRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    currency: str = "EUR"
    client_language: str = "en"
    valid_until: Optional[date] = None
    client_visible_intro: Optional[str] = None
    client_visible_terms: Optional[str] = None


class OfferPassenger(BaseDocument):
    agency_id: str
    offer_id: str
    passenger_id: Optional[str] = None
    request_passenger_id: Optional[str] = None
    snapshot_display_name: str
    snapshot_date_of_birth: date
    snapshot_passenger_type: str
    role_in_offer: str = "traveler"
    is_primary_traveler: bool = False
    status: str = "active"


class OfferPassengerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passenger_id: str
    request_passenger_id: Optional[str] = None
    role_in_offer: str = "traveler"
    is_primary_traveler: bool = False


class OfferPassengerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_in_offer: Optional[str] = None
    is_primary_traveler: Optional[bool] = None
    status: Optional[str] = None


class OfferRouteAlternative(BaseDocument):
    agency_id: str
    offer_id: str
    sequence: int
    label: str
    title: str
    status: OfferRouteStatus = OfferRouteStatus.DRAFT
    source_channel: SourceChannel = SourceChannel.MANUAL
    carrier_summary: Optional[str] = None
    route_summary: Optional[str] = None
    schedule_summary: Optional[str] = None
    total_travel_time_minutes: Optional[int] = None
    stop_count: int = 0
    connection_quality: ConnectionQuality = ConnectionQuality.UNKNOWN
    service_support_summary: Optional[str] = None
    recommendation_label: Optional[str] = None
    agent_recommendation_reason: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class OfferRouteAlternativeCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    sequence: int
    label: str
    title: str
    status: OfferRouteStatus = OfferRouteStatus.DRAFT
    source_channel: SourceChannel = SourceChannel.MANUAL
    carrier_summary: Optional[str] = None
    route_summary: Optional[str] = None
    schedule_summary: Optional[str] = None
    total_travel_time_minutes: Optional[int] = None
    stop_count: int = 0
    connection_quality: ConnectionQuality = ConnectionQuality.UNKNOWN
    service_support_summary: Optional[str] = None
    recommendation_label: Optional[str] = None
    agent_recommendation_reason: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class OfferRouteAlternativeUpdate(OfferRouteAlternativeCreate):
    sequence: Optional[int] = None
    label: Optional[str] = None
    title: Optional[str] = None


class OfferSegment(BaseDocument):
    agency_id: str
    offer_id: str
    route_alternative_id: str
    sequence: int
    marketing_airline_code: str
    marketing_airline_name: Optional[str] = None
    operating_airline_code: Optional[str] = None
    operating_airline_name: Optional[str] = None
    flight_number: Optional[str] = None
    origin_airport_code: str
    origin_city: Optional[str] = None
    destination_airport_code: str
    destination_city: Optional[str] = None
    departure_datetime: Optional[datetime] = None
    arrival_datetime: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    cabin: Optional[str] = None
    booking_class: Optional[str] = None
    fare_basis: Optional[str] = None
    segment_status: str = "proposed"
    baggage_summary: Optional[str] = None
    notes: Optional[str] = None


class OfferSegmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    marketing_airline_code: str
    marketing_airline_name: Optional[str] = None
    operating_airline_code: Optional[str] = None
    operating_airline_name: Optional[str] = None
    flight_number: Optional[str] = None
    origin_airport_code: str
    origin_city: Optional[str] = None
    destination_airport_code: str
    destination_city: Optional[str] = None
    departure_datetime: Optional[datetime] = None
    arrival_datetime: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    cabin: Optional[str] = None
    booking_class: Optional[str] = None
    fare_basis: Optional[str] = None
    segment_status: str = "proposed"
    baggage_summary: Optional[str] = None
    notes: Optional[str] = None


class OfferSegmentUpdate(OfferSegmentCreate):
    sequence: Optional[int] = None
    marketing_airline_code: Optional[str] = None
    origin_airport_code: Optional[str] = None
    destination_airport_code: Optional[str] = None


class OfferFareOption(BaseDocument):
    agency_id: str
    offer_id: str
    route_alternative_id: str
    sequence: int
    label: str
    branded_fare_name: Optional[str] = None
    fare_family_code: Optional[str] = None
    status: FareOptionStatus = FareOptionStatus.DRAFT
    currency: str = "EUR"
    base_fare_amount: float = 0
    taxes_amount: float = 0
    airline_fees_amount: float = 0
    agency_service_fee_amount: float = 0
    total_amount: float = 0
    refundable_status: RefundableStatus = RefundableStatus.UNKNOWN
    changeability_status: ChangeabilityStatus = ChangeabilityStatus.UNKNOWN
    baggage_summary: Optional[str] = None
    seat_selection_summary: Optional[str] = None
    meal_summary: Optional[str] = None
    special_service_summary: Optional[str] = None
    client_visible_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    is_recommended: bool = False


class OfferFareOptionCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    sequence: int
    label: str
    branded_fare_name: Optional[str] = None
    fare_family_code: Optional[str] = None
    status: FareOptionStatus = FareOptionStatus.DRAFT
    currency: str = "EUR"
    base_fare_amount: float = 0
    taxes_amount: float = 0
    airline_fees_amount: float = 0
    agency_service_fee_amount: float = 0
    total_amount: float = 0
    refundable_status: RefundableStatus = RefundableStatus.UNKNOWN
    changeability_status: ChangeabilityStatus = ChangeabilityStatus.UNKNOWN
    baggage_summary: Optional[str] = None
    seat_selection_summary: Optional[str] = None
    meal_summary: Optional[str] = None
    special_service_summary: Optional[str] = None
    client_visible_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    is_recommended: bool = False


class OfferFareOptionUpdate(OfferFareOptionCreate):
    sequence: Optional[int] = None
    label: Optional[str] = None


class OfferPriceLine(BaseDocument):
    agency_id: str
    offer_id: str
    route_alternative_id: str
    fare_option_id: str
    line_type: PriceLineType
    description: str
    service_code: Optional[str] = None
    passenger_id: Optional[str] = None
    quantity: float = 1
    unit_amount: float = 0
    total_amount: float = 0
    currency: str = "EUR"
    supplier_pass_through: bool = False
    client_visible: bool = True
    internal_notes: Optional[str] = None
    status: str = "active"


class OfferPriceLineCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    line_type: PriceLineType
    description: str
    service_code: Optional[str] = None
    passenger_id: Optional[str] = None
    quantity: float = 1
    unit_amount: float = 0
    total_amount: Optional[float] = None
    currency: str = "EUR"
    supplier_pass_through: bool = False
    client_visible: bool = True
    internal_notes: Optional[str] = None


class OfferPriceLineUpdate(OfferPriceLineCreate):
    line_type: Optional[PriceLineType] = None
    description: Optional[str] = None


class OfferServiceCheck(BaseDocument):
    agency_id: str
    offer_id: str
    route_alternative_id: Optional[str] = None
    fare_option_id: Optional[str] = None
    passenger_id: Optional[str] = None
    service_code: str
    service_name: str
    support_status: ServiceSupportStatus = ServiceSupportStatus.UNKNOWN
    client_visible_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    requires_documents: bool = False
    requires_airline_confirmation: bool = False
    estimated_fee_amount: Optional[float] = None
    currency: Optional[str] = None
    status: str = "active"


class OfferServiceCheckCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    route_alternative_id: Optional[str] = None
    fare_option_id: Optional[str] = None
    passenger_id: Optional[str] = None
    service_code: str
    service_name: str
    support_status: ServiceSupportStatus = ServiceSupportStatus.UNKNOWN
    client_visible_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    requires_documents: bool = False
    requires_airline_confirmation: bool = False
    estimated_fee_amount: Optional[float] = None
    currency: Optional[str] = None


class OfferServiceCheckUpdate(OfferServiceCheckCreate):
    service_code: Optional[str] = None
    service_name: Optional[str] = None


class OfferTimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    offer_id: str
    event_type: str
    actor_user_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    visibility: Visibility = Visibility.INTERNAL
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)



class RefundExchangeCaseType(str, Enum):
    REFUND = "refund"
    EXCHANGE = "exchange"
    VOID = "void"
    SCHEDULE_CHANGE = "schedule_change"
    INVOLUNTARY_CHANGE = "involuntary_change"
    CANCELLATION = "cancellation"
    OTHER = "other"


class RefundExchangeCaseStatus(str, Enum):
    DRAFT = "draft"
    CLIENT_REQUESTED = "client_requested"
    REVIEW_NEEDED = "review_needed"
    CHECKING_SUPPLIER_RULES = "checking_supplier_rules"
    WAITING_FOR_CLIENT = "waiting_for_client"
    WAITING_FOR_SUPPLIER = "waiting_for_supplier"
    APPROVED = "approved"
    PROCESSING_EXTERNALLY = "processing_externally"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class RefundExchangeCasePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RefundExchangeCaseReasonCategory(str, Enum):
    CLIENT_REQUEST = "client_request"
    ILLNESS = "illness"
    VISA_DOCUMENT_ISSUE = "visa_document_issue"
    SCHEDULE_CHANGE = "schedule_change"
    DISRUPTION = "disruption"
    DUPLICATE_BOOKING = "duplicate_booking"
    WRONG_NAME = "wrong_name"
    FARE_RULE_CHANGE = "fare_rule_change"
    AGENCY_ERROR = "agency_error"
    AIRLINE_ERROR = "airline_error"
    OTHER = "other"


class RefundExchangeItemType(str, Enum):
    TICKET = "ticket"
    EMD = "emd"
    INVOICE = "invoice"
    PAYMENT = "payment"
    BOOKING_SEGMENT = "booking_segment"
    PASSENGER = "passenger"
    OTHER = "other"


class RefundExchangeItemStatus(str, Enum):
    PENDING = "pending"
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"
    CANCELLED = "cancelled"


class RefundExchangeMessageSenderType(str, Enum):
    STAFF = "staff"
    CLIENT = "client"
    SYSTEM = "system"


class RefundExchangeMessageVisibility(str, Enum):
    INTERNAL = "internal"
    CLIENT_VISIBLE = "client_visible"


class RefundExchangeTimelineVisibility(str, Enum):
    INTERNAL = "internal"
    CLIENT_VISIBLE = "client_visible"


class RefundExchangeFinancialLineType(str, Enum):
    REFUNDABLE_FARE = "refundable_fare"
    REFUNDABLE_TAXES = "refundable_taxes"
    AIRLINE_PENALTY = "airline_penalty"
    SUPPLIER_FEE = "supplier_fee"
    AGENCY_FEE = "agency_fee"
    EXCHANGE_FARE_DIFFERENCE = "exchange_fare_difference"
    EXCHANGE_TAX_DIFFERENCE = "exchange_tax_difference"
    PAYMENT_REFUND = "payment_refund"
    CREDIT_VOUCHER = "credit_voucher"
    DISCOUNT = "discount"
    OTHER = "other"


class RefundExchangeFinancialDirection(str, Enum):
    DUE_TO_CLIENT = "due_to_client"
    DUE_FROM_CLIENT = "due_from_client"
    NEUTRAL = "neutral"


class RefundExchangeCase(BaseDocument):
    agency_id: str
    case_reference: str
    case_type: RefundExchangeCaseType
    client_id: str
    booking_id: str | None = None
    request_id: str | None = None
    offer_id: str | None = None
    created_by_user_id: str | None = None
    assigned_user_id: str | None = None
    status: RefundExchangeCaseStatus = RefundExchangeCaseStatus.DRAFT
    priority: RefundExchangeCasePriority = RefundExchangeCasePriority.NORMAL
    reason_category: RefundExchangeCaseReasonCategory = RefundExchangeCaseReasonCategory.OTHER
    client_reason_text: str | None = None
    internal_summary: str | None = None
    client_visible_summary: str | None = None
    supplier_reference: str | None = None
    expected_supplier_response_at: datetime | None = None
    deadline_at: datetime | None = None
    estimated_refund_amount: float | None = 0
    estimated_penalty_amount: float | None = 0
    estimated_exchange_difference_amount: float | None = 0
    estimated_agency_fee_amount: float | None = 0
    estimated_total_due_from_client: float | None = 0
    estimated_total_due_to_client: float | None = 0
    final_refund_amount: float | None = None
    final_penalty_amount: float | None = None
    final_exchange_difference_amount: float | None = None
    final_agency_fee_amount: float | None = None
    final_total_due_from_client: float | None = None
    final_total_due_to_client: float | None = None
    currency: str = "EUR"
    client_visible: bool = True
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None


class RefundExchangeCaseCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_id: str
    case_type: RefundExchangeCaseType
    status: RefundExchangeCaseStatus = RefundExchangeCaseStatus.DRAFT
    priority: RefundExchangeCasePriority = RefundExchangeCasePriority.NORMAL
    reason_category: RefundExchangeCaseReasonCategory = RefundExchangeCaseReasonCategory.OTHER
    booking_id: str | None = None
    request_id: str | None = None
    offer_id: str | None = None
    assigned_user_id: str | None = None
    client_reason_text: str | None = None
    internal_summary: str | None = None
    client_visible_summary: str | None = None
    supplier_reference: str | None = None
    expected_supplier_response_at: datetime | None = None
    deadline_at: datetime | None = None
    estimated_refund_amount: float | None = None
    estimated_penalty_amount: float | None = None
    estimated_exchange_difference_amount: float | None = None
    estimated_agency_fee_amount: float | None = None
    estimated_total_due_from_client: float | None = None
    estimated_total_due_to_client: float | None = None
    final_refund_amount: float | None = None
    final_penalty_amount: float | None = None
    final_exchange_difference_amount: float | None = None
    final_agency_fee_amount: float | None = None
    final_total_due_from_client: float | None = None
    final_total_due_to_client: float | None = None
    currency: str = "EUR"
    client_visible: bool = True


class RefundExchangeCaseUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    case_type: RefundExchangeCaseType | None = None
    priority: RefundExchangeCasePriority | None = None
    reason_category: RefundExchangeCaseReasonCategory | None = None
    assigned_user_id: str | None = None
    client_reason_text: str | None = None
    internal_summary: str | None = None
    client_visible_summary: str | None = None
    supplier_reference: str | None = None
    expected_supplier_response_at: datetime | None = None
    deadline_at: datetime | None = None
    estimated_refund_amount: float | None = None
    estimated_penalty_amount: float | None = None
    estimated_exchange_difference_amount: float | None = None
    estimated_agency_fee_amount: float | None = None
    estimated_total_due_from_client: float | None = None
    estimated_total_due_to_client: float | None = None
    final_refund_amount: float | None = None
    final_penalty_amount: float | None = None
    final_exchange_difference_amount: float | None = None
    final_agency_fee_amount: float | None = None
    final_total_due_from_client: float | None = None
    final_total_due_to_client: float | None = None
    currency: str | None = None
    client_visible: bool | None = None


class RefundExchangeCaseStatusUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: RefundExchangeCaseStatus


class RefundExchangeFromBookingCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    case_type: RefundExchangeCaseType
    reason_category: RefundExchangeCaseReasonCategory = RefundExchangeCaseReasonCategory.OTHER
    priority: RefundExchangeCasePriority = RefundExchangeCasePriority.NORMAL
    status: RefundExchangeCaseStatus = RefundExchangeCaseStatus.CLIENT_REQUESTED
    client_reason_text: str | None = None
    internal_summary: str | None = None
    client_visible_summary: str | None = None
    supplier_reference: str | None = None
    expected_supplier_response_at: datetime | None = None
    deadline_at: datetime | None = None
    estimated_refund_amount: float | None = None
    estimated_penalty_amount: float | None = None
    estimated_exchange_difference_amount: float | None = None
    estimated_agency_fee_amount: float | None = None
    estimated_total_due_from_client: float | None = None
    estimated_total_due_to_client: float | None = None
    currency: str = "EUR"
    client_visible: bool = True
    link_ticket_ids: list[str] = Field(default_factory=list)
    link_emd_ids: list[str] = Field(default_factory=list)
    link_invoice_ids: list[str] = Field(default_factory=list)
    link_payment_ids: list[str] = Field(default_factory=list)
    link_passenger_ids: list[str] = Field(default_factory=list)


class RefundExchangeItem(BaseDocument):
    agency_id: str
    case_id: str
    item_type: RefundExchangeItemType
    item_id: str | None = None
    passenger_id: str | None = None
    ticket_id: str | None = None
    emd_id: str | None = None
    invoice_id: str | None = None
    payment_id: str | None = None
    description: str
    status: RefundExchangeItemStatus = RefundExchangeItemStatus.PENDING
    estimated_amount: float = 0
    final_amount: float | None = None
    currency: str = "EUR"
    internal_notes: str | None = None
    client_visible_notes: str | None = None

class RefundExchangeItemCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    item_type: RefundExchangeItemType
    item_id: str | None = None
    passenger_id: str | None = None
    ticket_id: str | None = None
    emd_id: str | None = None
    invoice_id: str | None = None
    payment_id: str | None = None
    description: str
    status: RefundExchangeItemStatus = RefundExchangeItemStatus.PENDING
    estimated_amount: float = 0
    final_amount: float | None = None
    currency: str = "EUR"
    internal_notes: str | None = None
    client_visible_notes: str | None = None


class RefundExchangeItemUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    item_type: RefundExchangeItemType | None = None
    status: RefundExchangeItemStatus | None = None
    item_id: str | None = None
    passenger_id: str | None = None
    ticket_id: str | None = None
    emd_id: str | None = None
    invoice_id: str | None = None
    payment_id: str | None = None
    description: str | None = None
    estimated_amount: float | None = None
    final_amount: float | None = None
    currency: str | None = None
    internal_notes: str | None = None
    client_visible_notes: str | None = None


class RefundExchangeMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    case_id: str
    sender_user_id: Optional[str] = None
    sender_type: RefundExchangeMessageSenderType = RefundExchangeMessageSenderType.STAFF
    visibility: RefundExchangeMessageVisibility = RefundExchangeMessageVisibility.INTERNAL
    message_text: str
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class RefundExchangeMessageCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    sender_user_id: Optional[str] = None
    sender_type: RefundExchangeMessageSenderType = RefundExchangeMessageSenderType.STAFF
    visibility: RefundExchangeMessageVisibility = RefundExchangeMessageVisibility.INTERNAL
    message_text: str


class RefundExchangeTimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    case_id: str
    event_type: str
    actor_user_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    visibility: RefundExchangeTimelineVisibility = RefundExchangeTimelineVisibility.INTERNAL
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)


class RefundExchangeFinancialLine(BaseDocument):
    agency_id: str
    case_id: str
    line_type: RefundExchangeFinancialLineType
    description: str
    amount: float = 0
    currency: str = "EUR"
    direction: RefundExchangeFinancialDirection = RefundExchangeFinancialDirection.NEUTRAL
    supplier_pass_through: bool = False
    client_visible: bool = True
    internal_notes: str | None = None


class RefundExchangeFinancialLineCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    line_type: RefundExchangeFinancialLineType
    description: str
    amount: float = 0
    currency: str = "EUR"
    direction: RefundExchangeFinancialDirection = RefundExchangeFinancialDirection.NEUTRAL
    supplier_pass_through: bool = False
    client_visible: bool = True
    internal_notes: str | None = None


class RefundExchangeFinancialLineUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    line_type: RefundExchangeFinancialLineType | None = None
    description: str | None = None
    amount: float | None = None
    currency: str | None = None
    direction: RefundExchangeFinancialDirection | None = None
    supplier_pass_through: bool | None = None
    client_visible: bool | None = None
    internal_notes: str | None = None

class BookingStatus(str, Enum):
    DRAFT = "draft"
    PENDING_RESERVATION = "pending_reservation"
    RESERVED = "reserved"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    TICKETING_PENDING = "ticketing_pending"
    TICKETED = "ticketed"
    PARTIALLY_TICKETED = "partially_ticketed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class BookingChannel(str, Enum):
    GDS = "gds"
    AIRLINE_PORTAL = "airline_portal"
    OTA_AFFILIATE = "ota_affiliate"
    DIRECT_AIRLINE_WEBSITE = "direct_airline_website"
    SUPPLIER_EMAIL = "supplier_email"
    PHONE = "phone"
    MANUAL = "manual"
    MIXED = "mixed"


class BookingPassengerTicketStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    ISSUED = "issued"
    VOIDED = "voided"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"


class BookingSegmentStatus(str, Enum):
    BOOKED = "booked"
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    CANCELLED = "cancelled"
    FLOWN = "flown"
    INFO_ONLY = "info_only"


class TicketStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    VOIDED = "voided"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"
    CANCELLED = "cancelled"


class EmdType(str, Enum):
    EMD_S = "emd_s"
    EMD_A = "emd_a"
    UNKNOWN = "unknown"


class EmdStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    VOIDED = "voided"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"
    CANCELLED = "cancelled"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    VOIDED = "voided"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class InvoiceLineType(str, Enum):
    AIRFARE = "airfare"
    TAXES = "taxes"
    AIRLINE_ANCILLARY = "airline_ancillary"
    AGENCY_SERVICE_FEE = "agency_service_fee"
    DOCUMENT_SERVICE_FEE = "document_service_fee"
    SPECIAL_ASSISTANCE_FEE = "special_assistance_fee"
    TICKET_FEE = "ticket_fee"
    EMD_FEE = "emd_fee"
    DISCOUNT = "discount"
    MARKUP = "markup"
    OTHER = "other"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    RECEIVED = "received"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CARD_OFFLINE = "card_offline"
    PAYMENT_LINK_EXTERNAL = "payment_link_external"
    AGENCY_CREDIT = "agency_credit"
    OTHER = "other"


class ReconciliationStatus(str, Enum):
    UNRECONCILED = "unreconciled"
    PARTIALLY_RECONCILED = "partially_reconciled"
    RECONCILED = "reconciled"
    DISPUTED = "disputed"


class Booking(BaseDocument):
    agency_id: str
    booking_reference: str
    client_id: str
    request_id: Optional[str] = None
    offer_id: Optional[str] = None
    selected_route_alternative_id: Optional[str] = None
    selected_fare_option_id: Optional[str] = None
    created_by_user_id: str
    assigned_user_id: Optional[str] = None
    status: BookingStatus = BookingStatus.DRAFT
    pnr: Optional[str] = None
    validating_airline_code: Optional[str] = None
    booking_channel: BookingChannel = BookingChannel.MANUAL
    currency: str = "EUR"
    total_amount: float = 0
    amount_paid: float = 0
    amount_due: float = 0
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    booking_snapshot: Optional[Dict[str, Any]] = None
    confirmed_at: Optional[datetime] = None
    ticketed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


class BookingCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_id: str
    request_id: Optional[str] = None
    offer_id: Optional[str] = None
    selected_route_alternative_id: Optional[str] = None
    selected_fare_option_id: Optional[str] = None
    assigned_user_id: Optional[str] = None
    status: BookingStatus = BookingStatus.DRAFT
    pnr: Optional[str] = None
    validating_airline_code: Optional[str] = None
    booking_channel: BookingChannel = BookingChannel.MANUAL
    currency: str = "EUR"
    total_amount: float = 0
    amount_paid: float = 0
    amount_due: float = 0
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class BookingUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    assigned_user_id: Optional[str] = None
    status: Optional[BookingStatus] = None
    pnr: Optional[str] = None
    validating_airline_code: Optional[str] = None
    booking_channel: Optional[BookingChannel] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    amount_paid: Optional[float] = None
    amount_due: Optional[float] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class CreateBookingFromOffer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_route_alternative_id: Optional[str] = None
    selected_fare_option_id: Optional[str] = None
    pnr: Optional[str] = None
    booking_channel: BookingChannel = BookingChannel.MANUAL
    status: BookingStatus = BookingStatus.DRAFT
    assigned_user_id: Optional[str] = None
    internal_notes: Optional[str] = None
    accept_offer: bool = True


class BookingPassenger(BaseDocument):
    agency_id: str
    booking_id: str
    passenger_id: Optional[str] = None
    offer_passenger_id: Optional[str] = None
    snapshot_display_name: str
    snapshot_date_of_birth: Optional[date] = None
    snapshot_passenger_type: str = "ADT"
    is_primary_traveler: bool = False
    ticket_status: BookingPassengerTicketStatus = BookingPassengerTicketStatus.PENDING


class BookingPassengerCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    passenger_id: Optional[str] = None
    offer_passenger_id: Optional[str] = None
    snapshot_display_name: Optional[str] = None
    snapshot_date_of_birth: Optional[date] = None
    snapshot_passenger_type: str = "ADT"
    is_primary_traveler: bool = False
    ticket_status: BookingPassengerTicketStatus = BookingPassengerTicketStatus.PENDING


class BookingPassengerUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_display_name: Optional[str] = None
    snapshot_date_of_birth: Optional[date] = None
    snapshot_passenger_type: Optional[str] = None
    is_primary_traveler: Optional[bool] = None
    ticket_status: Optional[BookingPassengerTicketStatus] = None


class BookingSegment(BaseDocument):
    agency_id: str
    booking_id: str
    offer_segment_id: Optional[str] = None
    sequence: int
    marketing_airline_code: str
    marketing_airline_name: Optional[str] = None
    operating_airline_code: Optional[str] = None
    operating_airline_name: Optional[str] = None
    flight_number: Optional[str] = None
    origin_airport_code: str
    origin_city: Optional[str] = None
    destination_airport_code: str
    destination_city: Optional[str] = None
    departure_datetime: Optional[datetime] = None
    arrival_datetime: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    cabin: Optional[str] = None
    booking_class: Optional[str] = None
    fare_basis: Optional[str] = None
    segment_status: BookingSegmentStatus = BookingSegmentStatus.BOOKED
    baggage_summary: Optional[str] = None
    notes: Optional[str] = None


class BookingSegmentCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    sequence: int
    marketing_airline_code: str
    marketing_airline_name: Optional[str] = None
    operating_airline_code: Optional[str] = None
    operating_airline_name: Optional[str] = None
    flight_number: Optional[str] = None
    origin_airport_code: str
    origin_city: Optional[str] = None
    destination_airport_code: str
    destination_city: Optional[str] = None
    departure_datetime: Optional[datetime] = None
    arrival_datetime: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    cabin: Optional[str] = None
    booking_class: Optional[str] = None
    fare_basis: Optional[str] = None
    segment_status: BookingSegmentStatus = BookingSegmentStatus.BOOKED
    baggage_summary: Optional[str] = None
    notes: Optional[str] = None


class BookingSegmentUpdate(BookingSegmentCreate):
    sequence: Optional[int] = None
    marketing_airline_code: Optional[str] = None
    origin_airport_code: Optional[str] = None
    destination_airport_code: Optional[str] = None


class TicketRecord(BaseDocument):
    agency_id: str
    booking_id: str
    passenger_id: Optional[str] = None
    booking_passenger_id: Optional[str] = None
    ticket_number: str
    validating_airline_code: str
    issue_date: Optional[date] = None
    status: TicketStatus = TicketStatus.DRAFT
    base_fare_amount: float = 0
    taxes_amount: float = 0
    total_amount: float = 0
    currency: str = "EUR"
    fare_basis: Optional[str] = None
    coupon_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class TicketRecordCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    passenger_id: Optional[str] = None
    booking_passenger_id: Optional[str] = None
    ticket_number: str
    validating_airline_code: str
    issue_date: Optional[date] = None
    status: TicketStatus = TicketStatus.DRAFT
    base_fare_amount: float = 0
    taxes_amount: float = 0
    total_amount: Optional[float] = None
    currency: str = "EUR"
    fare_basis: Optional[str] = None
    coupon_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class TicketRecordUpdate(TicketRecordCreate):
    ticket_number: Optional[str] = None
    validating_airline_code: Optional[str] = None


class EMDRecord(BaseDocument):
    agency_id: str
    booking_id: str
    passenger_id: Optional[str] = None
    booking_passenger_id: Optional[str] = None
    ticket_id: Optional[str] = None
    service_code: str
    service_name: str
    emd_number: str
    emd_type: EmdType = EmdType.UNKNOWN
    rfic_code: Optional[str] = None
    rfisc_code: Optional[str] = None
    reason_for_issuance: Optional[str] = None
    issue_date: Optional[date] = None
    status: EmdStatus = EmdStatus.DRAFT
    amount: float = 0
    currency: str = "EUR"
    associated_segment_ids: List[str] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class EMDRecordCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    passenger_id: Optional[str] = None
    booking_passenger_id: Optional[str] = None
    ticket_id: Optional[str] = None
    service_code: str
    service_name: str
    emd_number: str
    emd_type: EmdType = EmdType.UNKNOWN
    rfic_code: Optional[str] = None
    rfisc_code: Optional[str] = None
    reason_for_issuance: Optional[str] = None
    issue_date: Optional[date] = None
    status: EmdStatus = EmdStatus.DRAFT
    amount: float = 0
    currency: str = "EUR"
    associated_segment_ids: List[str] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class EMDRecordUpdate(EMDRecordCreate):
    service_code: Optional[str] = None
    service_name: Optional[str] = None
    emd_number: Optional[str] = None


class Invoice(BaseDocument):
    agency_id: str
    invoice_number: str
    client_id: str
    booking_id: Optional[str] = None
    offer_id: Optional[str] = None
    status: InvoiceStatus = InvoiceStatus.DRAFT
    currency: str = "EUR"
    subtotal_amount: float = 0
    tax_amount: float = 0
    total_amount: float = 0
    paid_amount: float = 0
    due_amount: float = 0
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    client_visible_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    issued_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None


class InvoiceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    invoice_number: Optional[str] = None
    client_id: str
    booking_id: Optional[str] = None
    offer_id: Optional[str] = None
    status: InvoiceStatus = InvoiceStatus.DRAFT
    currency: str = "EUR"
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    client_visible_notes: Optional[str] = None
    internal_notes: Optional[str] = None


class InvoiceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: Optional[InvoiceStatus] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    client_visible_notes: Optional[str] = None
    internal_notes: Optional[str] = None


class InvoiceLineItem(BaseDocument):
    agency_id: str
    invoice_id: str
    booking_id: Optional[str] = None
    ticket_id: Optional[str] = None
    emd_id: Optional[str] = None
    line_type: InvoiceLineType
    description: str
    service_code: Optional[str] = None
    quantity: float = 1
    unit_amount: float = 0
    total_amount: float = 0
    currency: str = "EUR"
    supplier_pass_through: bool = False
    client_visible: bool = True
    status: str = "active"


class InvoiceLineItemCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    booking_id: Optional[str] = None
    ticket_id: Optional[str] = None
    emd_id: Optional[str] = None
    line_type: InvoiceLineType
    description: str
    service_code: Optional[str] = None
    quantity: float = 1
    unit_amount: float = 0
    total_amount: Optional[float] = None
    currency: str = "EUR"
    supplier_pass_through: bool = False
    client_visible: bool = True


class InvoiceLineItemUpdate(InvoiceLineItemCreate):
    line_type: Optional[InvoiceLineType] = None
    description: Optional[str] = None


class PaymentRecord(BaseDocument):
    agency_id: str
    invoice_id: str
    booking_id: Optional[str] = None
    client_id: str
    status: PaymentStatus = PaymentStatus.PENDING
    method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    amount: float = 0
    currency: str = "EUR"
    received_at: Optional[datetime] = None
    external_reference: Optional[str] = None
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.UNRECONCILED
    reconciliation_notes: Optional[str] = None
    internal_notes: Optional[str] = None


class PaymentRecordCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    invoice_id: str
    booking_id: Optional[str] = None
    client_id: str
    status: PaymentStatus = PaymentStatus.PENDING
    method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    amount: float
    currency: str = "EUR"
    received_at: Optional[datetime] = None
    external_reference: Optional[str] = None
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.UNRECONCILED
    reconciliation_notes: Optional[str] = None
    internal_notes: Optional[str] = None


class PaymentRecordUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: Optional[PaymentStatus] = None
    method: Optional[PaymentMethod] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    received_at: Optional[datetime] = None
    external_reference: Optional[str] = None
    reconciliation_status: Optional[ReconciliationStatus] = None
    reconciliation_notes: Optional[str] = None
    internal_notes: Optional[str] = None


class BookingTimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    booking_id: str
    event_type: str
    actor_user_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    visibility: Visibility = Visibility.INTERNAL
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)


class AirlineStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    MERGED = "merged"
    ARCHIVED = "archived"


class AirlineKnowledgeCategory(str, Enum):
    BOOKING_POLICY = "booking_policy"
    SERVICING_POLICY = "servicing_policy"
    SPECIAL_SERVICE = "special_service"
    BAGGAGE = "baggage"
    PET_TRAVEL = "pet_travel"
    ACCESSIBILITY = "accessibility"
    UNACCOMPANIED_MINOR = "unaccompanied_minor"
    MEDICAL_TRAVEL = "medical_travel"
    DOCUMENTS = "documents"
    CONTACT = "contact"
    PAYMENT = "payment"
    REFUND_EXCHANGE = "refund_exchange"
    SCHEDULE_CHANGE = "schedule_change"
    DISRUPTION = "disruption"
    EMD = "emd"
    FARE_FAMILY = "fare_family"
    OPERATIONAL_NOTE = "operational_note"
    OTHER = "other"


class KnowledgeReviewStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    VERIFIED = "verified"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class KnowledgeConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    OFFICIAL_SOURCE = "official_source"


class AirlineProcedureType(str, Enum):
    RESERVATION = "reservation"
    TICKETING = "ticketing"
    REISSUE = "reissue"
    REFUND = "refund"
    EMD = "emd"
    SPECIAL_SERVICE_REQUEST = "special_service_request"
    PET_BOOKING = "pet_booking"
    WHEELCHAIR_ASSISTANCE = "wheelchair_assistance"
    UMNR = "umnr"
    MEDICAL_CLEARANCE = "medical_clearance"
    GROUP_BOOKING = "group_booking"
    DISRUPTION = "disruption"
    AGENCY_SUPPORT = "agency_support"
    OTHER = "other"


class AirlineProcedureChannel(str, Enum):
    GDS = "gds"
    AIRLINE_PORTAL = "airline_portal"
    EMAIL = "email"
    PHONE = "phone"
    WEBFORM = "webform"
    SALES_OFFICE = "sales_office"
    AIRPORT = "airport"
    OTHER = "other"


class AirlineEmdAppliesTo(str, Enum):
    PETC = "petc"
    AVIH = "avih"
    WCHR = "wchr"
    WCHS = "wchs"
    WCHC = "wchc"
    UMNR = "umnr"
    BAGGAGE = "baggage"
    SEAT = "seat"
    MEAL = "meal"
    MEDICAL = "medical"
    OTHER = "other"


class AirlineKnowledgeSourceType(str, Enum):
    AIRLINE_WEBSITE = "airline_website"
    AIRLINE_PDF = "airline_pdf"
    GDS_ENTRY = "gds_entry"
    EMAIL_FROM_AIRLINE = "email_from_airline"
    PHONE_NOTE = "phone_note"
    AGENCY_EXPERIENCE = "agency_experience"
    ATPCO_IATA_REFERENCE = "atpco_iata_reference"
    INTERNAL_NOTE = "internal_note"
    OTHER = "other"


class SourceReliability(str, Enum):
    OFFICIAL = "official"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ANECDOTAL = "anecdotal"


class AgencyOverrideTargetType(str, Enum):
    AIRLINE_PROFILE = "airline_profile"
    KNOWLEDGE_ITEM = "knowledge_item"
    PROCEDURE = "procedure"
    EMD_RULE_NOTE = "emd_rule_note"
    SOURCE = "source"


class AgencyOverrideMode(str, Enum):
    REPLACE = "replace"
    AUGMENT = "augment"
    ANNOTATE = "annotate"


class AgencyOverrideStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AirlineUsageContextType(str, Enum):
    REQUEST = "request"
    OFFER = "offer"
    BOOKING = "booking"
    TICKET = "ticket"
    EMD = "emd"
    INVOICE = "invoice"
    MANUAL_SEARCH = "manual_search"


class AirlineProfile(BaseDocument):
    airline_code: str
    icao_code: Optional[str] = None
    airline_name: str
    country: str
    alliance: Optional[str] = None
    status: AirlineStatus = AirlineStatus.ACTIVE
    website_url: Optional[str] = None
    notes: Optional[str] = None


class AirlineProfileCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    icao_code: Optional[str] = None
    airline_name: str
    country: str
    alliance: Optional[str] = None
    status: AirlineStatus = AirlineStatus.ACTIVE
    website_url: Optional[str] = None
    notes: Optional[str] = None


class AirlineProfileUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    icao_code: Optional[str] = None
    airline_name: Optional[str] = None
    country: Optional[str] = None
    alliance: Optional[str] = None
    status: Optional[AirlineStatus] = None
    website_url: Optional[str] = None
    notes: Optional[str] = None


class AirlineKnowledgeItem(BaseDocument):
    airline_id: str
    category: AirlineKnowledgeCategory
    title: str
    summary: str
    detailed_text: str
    service_code: Optional[str] = None
    passenger_type: Optional[str] = None
    region_scope: Optional[str] = None
    cabin_scope: Optional[str] = None
    route_scope: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    review_status: KnowledgeReviewStatus = KnowledgeReviewStatus.DRAFT
    confidence: KnowledgeConfidence = KnowledgeConfidence.MEDIUM
    source_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    client_visible_allowed: bool = False
    internal_warning: bool = False
    created_by_user_id: Optional[str] = None
    reviewed_by_user_id: Optional[str] = None
    published_at: Optional[datetime] = None


class AirlineKnowledgeItemCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    category: AirlineKnowledgeCategory
    title: str
    summary: str
    detailed_text: str
    service_code: Optional[str] = None
    passenger_type: Optional[str] = None
    region_scope: Optional[str] = None
    cabin_scope: Optional[str] = None
    route_scope: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    review_status: KnowledgeReviewStatus = KnowledgeReviewStatus.DRAFT
    confidence: KnowledgeConfidence = KnowledgeConfidence.MEDIUM
    source_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    client_visible_allowed: bool = False
    internal_warning: bool = False


class AirlineKnowledgeItemUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    category: Optional[AirlineKnowledgeCategory] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    detailed_text: Optional[str] = None
    service_code: Optional[str] = None
    passenger_type: Optional[str] = None
    region_scope: Optional[str] = None
    cabin_scope: Optional[str] = None
    route_scope: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    review_status: Optional[KnowledgeReviewStatus] = None
    confidence: Optional[KnowledgeConfidence] = None
    source_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    client_visible_allowed: Optional[bool] = None
    internal_warning: Optional[bool] = None
    reviewed_by_user_id: Optional[str] = None
    published_at: Optional[datetime] = None


class AirlineProcedure(BaseDocument):
    airline_id: str
    procedure_type: AirlineProcedureType
    title: str
    channel: AirlineProcedureChannel
    contact_value: Optional[str] = None
    instructions: str
    required_fields: List[str] = Field(default_factory=list)
    expected_response_time: Optional[str] = None
    region_scope: Optional[str] = None
    review_status: KnowledgeReviewStatus = KnowledgeReviewStatus.DRAFT
    confidence: KnowledgeConfidence = KnowledgeConfidence.MEDIUM
    source_ids: List[str] = Field(default_factory=list)


class AirlineProcedureCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    procedure_type: AirlineProcedureType
    title: str
    channel: AirlineProcedureChannel
    contact_value: Optional[str] = None
    instructions: str
    required_fields: List[str] = Field(default_factory=list)
    expected_response_time: Optional[str] = None
    region_scope: Optional[str] = None
    review_status: KnowledgeReviewStatus = KnowledgeReviewStatus.DRAFT
    confidence: KnowledgeConfidence = KnowledgeConfidence.MEDIUM
    source_ids: List[str] = Field(default_factory=list)


class AirlineProcedureUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    procedure_type: Optional[AirlineProcedureType] = None
    title: Optional[str] = None
    channel: Optional[AirlineProcedureChannel] = None
    contact_value: Optional[str] = None
    instructions: Optional[str] = None
    required_fields: Optional[List[str]] = None
    expected_response_time: Optional[str] = None
    region_scope: Optional[str] = None
    review_status: Optional[KnowledgeReviewStatus] = None
    confidence: Optional[KnowledgeConfidence] = None
    source_ids: Optional[List[str]] = None


class AirlineEmdRuleNote(BaseDocument):
    airline_id: str
    service_code: str
    service_name: str
    rfic_code: Optional[str] = None
    rfisc_code: Optional[str] = None
    emd_type: EmdType = EmdType.UNKNOWN
    reason_for_issuance: str
    applies_to: AirlineEmdAppliesTo = AirlineEmdAppliesTo.OTHER
    pricing_note: Optional[str] = None
    issuance_note: Optional[str] = None
    refundability_note: Optional[str] = None
    source_ids: List[str] = Field(default_factory=list)
    review_status: KnowledgeReviewStatus = KnowledgeReviewStatus.DRAFT
    confidence: KnowledgeConfidence = KnowledgeConfidence.MEDIUM


class AirlineEmdRuleNoteCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    service_code: str
    service_name: str
    rfic_code: Optional[str] = None
    rfisc_code: Optional[str] = None
    emd_type: EmdType = EmdType.UNKNOWN
    reason_for_issuance: str
    applies_to: AirlineEmdAppliesTo = AirlineEmdAppliesTo.OTHER
    pricing_note: Optional[str] = None
    issuance_note: Optional[str] = None
    refundability_note: Optional[str] = None
    source_ids: List[str] = Field(default_factory=list)
    review_status: KnowledgeReviewStatus = KnowledgeReviewStatus.DRAFT
    confidence: KnowledgeConfidence = KnowledgeConfidence.MEDIUM


class AirlineEmdRuleNoteUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    service_code: Optional[str] = None
    service_name: Optional[str] = None
    rfic_code: Optional[str] = None
    rfisc_code: Optional[str] = None
    emd_type: Optional[EmdType] = None
    reason_for_issuance: Optional[str] = None
    applies_to: Optional[AirlineEmdAppliesTo] = None
    pricing_note: Optional[str] = None
    issuance_note: Optional[str] = None
    refundability_note: Optional[str] = None
    source_ids: Optional[List[str]] = None
    review_status: Optional[KnowledgeReviewStatus] = None
    confidence: Optional[KnowledgeConfidence] = None


class AirlineKnowledgeSource(BaseDocument):
    airline_id: Optional[str] = None
    source_type: AirlineKnowledgeSourceType
    title: str
    url: Optional[str] = None
    document_reference: Optional[str] = None
    source_date: Optional[date] = None
    captured_by_user_id: Optional[str] = None
    reliability: SourceReliability = SourceReliability.MEDIUM
    notes: Optional[str] = None


class AirlineKnowledgeSourceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_id: Optional[str] = None
    source_type: AirlineKnowledgeSourceType
    title: str
    url: Optional[str] = None
    document_reference: Optional[str] = None
    source_date: Optional[date] = None
    reliability: SourceReliability = SourceReliability.MEDIUM
    notes: Optional[str] = None


class AgencyAirlineOverride(BaseDocument):
    agency_id: str
    airline_id: str
    target_type: AgencyOverrideTargetType
    target_id: str
    override_mode: AgencyOverrideMode = AgencyOverrideMode.ANNOTATE
    title: Optional[str] = None
    override_text: str
    internal_warning: bool = False
    applies_to_agency_only: bool = True
    status: AgencyOverrideStatus = AgencyOverrideStatus.ACTIVE
    created_by_user_id: Optional[str] = None


class AgencyAirlineOverrideCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    target_type: AgencyOverrideTargetType
    target_id: str
    override_mode: AgencyOverrideMode = AgencyOverrideMode.ANNOTATE
    title: Optional[str] = None
    override_text: str
    internal_warning: bool = False
    applies_to_agency_only: bool = True
    status: AgencyOverrideStatus = AgencyOverrideStatus.ACTIVE


class AgencyAirlineOverrideUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    override_mode: Optional[AgencyOverrideMode] = None
    title: Optional[str] = None
    override_text: Optional[str] = None
    internal_warning: Optional[bool] = None
    applies_to_agency_only: Optional[bool] = None
    status: Optional[AgencyOverrideStatus] = None


class AirlineKnowledgeUsageEvent(BaseDocument):
    agency_id: str
    airline_id: str
    target_type: AgencyOverrideTargetType
    target_id: str
    used_in_context_type: AirlineUsageContextType = AirlineUsageContextType.MANUAL_SEARCH
    used_in_context_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    note: Optional[str] = None


class AirlineKnowledgeUsageEventCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    used_in_context_type: AirlineUsageContextType = AirlineUsageContextType.MANUAL_SEARCH
    used_in_context_id: Optional[str] = None
    note: Optional[str] = None


class DocumentTemplateScope(str, Enum):
    PLATFORM_DEFAULT = "platform_default"
    AGENCY_CUSTOM = "agency_custom"


class DocumentType(str, Enum):
    OFFER_SUMMARY = "offer_summary"
    BOOKING_CONFIRMATION = "booking_confirmation"
    ITINERARY_SUMMARY = "itinerary_summary"
    TICKET_RECEIPT_SUMMARY = "ticket_receipt_summary"
    EMD_RECEIPT_SUMMARY = "emd_receipt_summary"
    INVOICE_SUMMARY = "invoice_summary"
    SERVICE_SUMMARY = "service_summary"


class DocumentTemplateStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class RenderedDocumentSourceType(str, Enum):
    OFFER = "offer"
    BOOKING = "booking"
    TICKET = "ticket"
    EMD = "emd"
    INVOICE = "invoice"
    REQUEST = "request"


class RenderedDocumentStatus(str, Enum):
    DRAFT = "draft"
    RENDERED = "rendered"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class DocumentTemplate(BaseDocument):
    agency_id: Optional[str] = None
    template_scope: DocumentTemplateScope = DocumentTemplateScope.PLATFORM_DEFAULT
    document_type: DocumentType
    name: str
    description: Optional[str] = None
    status: DocumentTemplateStatus = DocumentTemplateStatus.ACTIVE
    language: str = "en"
    version: int = 1
    template_config: Dict[str, Any] = Field(default_factory=dict)
    created_by_user_id: Optional[str] = None


class DocumentTemplateCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    template_scope: DocumentTemplateScope = DocumentTemplateScope.AGENCY_CUSTOM
    document_type: DocumentType
    name: str
    description: Optional[str] = None
    status: DocumentTemplateStatus = DocumentTemplateStatus.ACTIVE
    language: str = "en"
    version: int = 1
    template_config: Dict[str, Any] = Field(default_factory=dict)


class DocumentTemplateUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[DocumentTemplateStatus] = None
    language: Optional[str] = None
    version: Optional[int] = None
    template_config: Optional[Dict[str, Any]] = None


class RenderDocumentRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    document_type: Optional[DocumentType] = None
    template_id: Optional[str] = None
    client_visible: bool = True
    internal_notes: Optional[str] = None
    language: str = "en"


class RenderedDocument(BaseDocument):
    agency_id: str
    document_type: DocumentType
    template_id: Optional[str] = None
    source_entity_type: RenderedDocumentSourceType
    source_entity_id: str
    client_id: Optional[str] = None
    passenger_id: Optional[str] = None
    title: str
    status: RenderedDocumentStatus = RenderedDocumentStatus.RENDERED
    language: str = "en"
    brand_snapshot: Dict[str, Any] = Field(default_factory=dict)
    source_snapshot: Dict[str, Any] = Field(default_factory=dict)
    rendered_html: str
    client_visible: bool = True
    internal_notes: Optional[str] = None
    rendered_by_user_id: Optional[str] = None
    rendered_at: datetime = Field(default_factory=now_utc)


class DocumentTimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    rendered_document_id: str
    event_type: str
    actor_user_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    visibility: Visibility = Visibility.INTERNAL
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)


class DocumentExportType(str, Enum):
    PDF = "pdf"
    PRINT_HTML = "print_html"


class DocumentExportStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentExportStorageMode(str, Enum):
    INLINE_BASE64 = "inline_base64"
    FILE_PATH = "file_path"
    EXTERNAL_STORAGE = "external_storage"
    NOT_GENERATED = "not_generated"


class DocumentExportRetentionPolicy(str, Enum):
    NONE = "none"
    KEEP_30_DAYS = "keep_30_days"
    KEEP_90_DAYS = "keep_90_days"
    KEEP_1_YEAR = "keep_1_year"
    KEEP_UNTIL_ARCHIVED = "keep_until_archived"


class DocumentStorageBackend(str, Enum):
    LOCAL_FILESYSTEM = "local_filesystem"


class DocumentStorageStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    MISSING = "missing"
    FAILED = "failed"


class DocumentDeliveryType(str, Enum):
    EMAIL = "email"
    MANUAL_DOWNLOAD = "manual_download"
    PORTAL_VISIBLE = "portal_visible"
    OTHER = "other"


class DocumentDeliveryStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class DocumentDeliveryProvider(str, Enum):
    SMTP = "smtp"
    MANUAL = "manual"
    DEV_CONSOLE = "dev_console"
    NONE = "none"


class DocumentDeliveryRetryStatus(str, Enum):
    NONE = "none"
    RETRY_AVAILABLE = "retry_available"
    RETRY_SCHEDULED = "retry_scheduled"
    MAX_RETRIES_REACHED = "max_retries_reached"


class DocumentDeliveryAttemptStatus(str, Enum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentDeliveryProcessingState(str, Enum):
    MANUAL_ONLY = "manual_only"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgencyEmailMode(str, Enum):
    DISABLED = "disabled"
    DEV_CONSOLE = "dev_console"
    SMTP = "smtp"


class AgencyEmailSettingsStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class DocumentExport(BaseDocument):
    agency_id: str
    rendered_document_id: str
    export_type: DocumentExportType
    status: DocumentExportStatus = DocumentExportStatus.PENDING
    filename: str
    content_type: str
    storage_mode: DocumentExportStorageMode = DocumentExportStorageMode.NOT_GENERATED
    file_data_base64: Optional[str] = None
    file_path: Optional[str] = None
    storage_key: Optional[str] = None
    storage_bucket: Optional[str] = None
    retention_policy: DocumentExportRetentionPolicy = DocumentExportRetentionPolicy.KEEP_90_DAYS
    retention_expires_at: Optional[datetime] = None
    checksum_sha256: Optional[str] = None
    file_size_bytes: Optional[int] = None
    generated_by_user_id: Optional[str] = None
    generated_at: Optional[datetime] = None
    generated_from_snapshot_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    archived_by_user_id: Optional[str] = None
    error_message: Optional[str] = None
    client_visible: bool = False


class DocumentStorageRecord(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    related_entity_type: str
    related_entity_id: str
    document_type: str
    filename_original: Optional[str] = None
    filename_stored: Optional[str] = None
    storage_key: Optional[str] = None
    storage_backend: DocumentStorageBackend = DocumentStorageBackend.LOCAL_FILESYSTEM
    storage_status: DocumentStorageStatus = DocumentStorageStatus.ACTIVE
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum_sha256: Optional[str] = None
    created_by_user_id: Optional[str] = None
    created_by_email: Optional[EmailStr] = None
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    retention_until: Optional[datetime] = None
    delivery_allowed: bool = False
    public_access_allowed: bool = False
    internal_notes: Optional[str] = None
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentExportCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    export_type: DocumentExportType = DocumentExportType.PRINT_HTML
    client_visible: bool = False


class DocumentDelivery(BaseDocument):
    agency_id: str
    rendered_document_id: str
    export_id: Optional[str] = None
    delivery_type: DocumentDeliveryType = DocumentDeliveryType.EMAIL
    status: DocumentDeliveryStatus = DocumentDeliveryStatus.DRAFT
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    subject: str
    message_text: str
    sent_by_user_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    provider: DocumentDeliveryProvider = DocumentDeliveryProvider.NONE
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    queued_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None
    locked_by: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    processing_state: DocumentDeliveryProcessingState = DocumentDeliveryProcessingState.MANUAL_ONLY
    attempt_count: int = 0
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    retry_status: DocumentDeliveryRetryStatus = DocumentDeliveryRetryStatus.NONE
    max_attempts: int = 3
    last_error_message: Optional[str] = None
    client_visible: bool = False


class DocumentDeliveryAttempt(BaseDocument):
    agency_id: str
    delivery_id: str
    rendered_document_id: str
    export_id: Optional[str] = None
    attempt_number: int
    status: DocumentDeliveryAttemptStatus = DocumentDeliveryAttemptStatus.PENDING
    provider: DocumentDeliveryProvider = DocumentDeliveryProvider.NONE
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DocumentDeliveryCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    export_id: Optional[str] = None
    delivery_type: DocumentDeliveryType = DocumentDeliveryType.EMAIL
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    subject: str
    message_text: str
    client_visible: bool = False


class AgencyEmailSettings(BaseDocument):
    agency_id: str
    sender_name: str
    sender_email: EmailStr
    reply_to_email: Optional[EmailStr] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password_secret_ref: Optional[str] = None
    smtp_password_is_configured: bool = False
    smtp_use_tls: bool = True
    mode: AgencyEmailMode = AgencyEmailMode.DISABLED
    status: AgencyEmailSettingsStatus = AgencyEmailSettingsStatus.ACTIVE
    verified_at: Optional[datetime] = None
    last_validation_error: Optional[str] = None


class AgencyEmailSettingsUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    sender_name: Optional[str] = None
    sender_email: Optional[EmailStr] = None
    reply_to_email: Optional[EmailStr] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password_secret_ref: Optional[str] = None
    smtp_password_is_configured: Optional[bool] = None
    smtp_use_tls: Optional[bool] = None
    mode: Optional[AgencyEmailMode] = None
    status: Optional[AgencyEmailSettingsStatus] = None


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
