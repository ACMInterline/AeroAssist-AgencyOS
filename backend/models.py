from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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


class BrandingLogoFitMode(str, Enum):
    CONTAIN = "contain"
    COVER = "cover"
    CENTER = "center"


class BrandingLogoUsageKey(str, Enum):
    SQUARE = "square"
    HORIZONTAL = "horizontal"
    COMPACT = "compact"


class BrandingLogoVariantKey(str, Enum):
    ORIGINAL = "original"
    SQUARE = "square"
    HORIZONTAL = "horizontal"
    COMPACT = "compact"
    FAVICON = "favicon"
    DARK = "dark"
    LIGHT = "light"


class WebsiteMediaAssetType(str, Enum):
    IMAGE = "image"
    ICON = "icon"
    DOCUMENT = "document"
    BACKGROUND = "background"
    ILLUSTRATION = "illustration"


class WebsiteMediaUsageContext(str, Enum):
    HERO = "hero"
    SECTION_IMAGE = "section_image"
    CARD_IMAGE = "card_image"
    GALLERY = "gallery"
    BACKGROUND = "background"
    DOCUMENT = "document"
    GENERAL = "general"


class WebsiteMediaStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


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


class RequestPurpose(str, Enum):
    NEW_TRIP = "new_trip"
    TRIP_CHANGE = "trip_change"
    EXCHANGE_QUOTE = "exchange_quote"
    REFUND_QUOTE = "refund_quote"
    SERVICE_ONLY = "service_only"


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
    OPEN_JAW = "open_jaw"
    COMPLEX = "complex"
    UNKNOWN = "unknown"


class SubmissionChannel(str, Enum):
    PUBLIC_WEBSITE = "public_website"
    AGENCY_WEBSITE = "agency_website"
    CLIENT_PORTAL = "client_portal"
    STAFF_CONSOLE = "staff_console"
    IMPORT = "import"
    API = "api"
    UNKNOWN = "unknown"


class AccountOriginAtSubmission(str, Enum):
    EXISTING_CLIENT = "existing_client"
    NEW_PUBLIC_CONTACT = "new_public_contact"
    PORTAL_ACCOUNT = "portal_account"
    STAFF_CREATED = "staff_created"
    IMPORTED = "imported"
    UNKNOWN = "unknown"


class PassengerLinkMode(str, Enum):
    EXISTING = "existing"
    NEW_INLINE = "new_inline"
    UNRESOLVED = "unresolved"


class TripStatus(str, Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    QUOTED = "quoted"
    BOOKED = "booked"
    TICKETED = "ticketed"
    IN_TRAVEL = "in_travel"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TripDossierSource(str, Enum):
    MANUAL = "manual"
    REQUEST_CONVERSION = "request_conversion"
    INTAKE_CONVERSION = "intake_conversion"
    IMPORTED = "imported"


class TripPassengerType(str, Enum):
    ADULT = "adult"
    CHILD = "child"
    INFANT = "infant"
    YOUTH = "youth"
    SENIOR = "senior"
    UNKNOWN = "unknown"


class TripSegmentStatus(str, Enum):
    PLANNED = "planned"
    QUOTED = "quoted"
    BOOKED = "booked"
    TICKETED = "ticketed"
    FLOWN = "flown"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class TripServiceStatus(str, Enum):
    REQUESTED = "requested"
    CHECKING = "checking"
    QUOTED = "quoted"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    FULFILLED = "fulfilled"


class OfferPurpose(str, Enum):
    NEW_BOOKING = "new_booking"
    TRIP_CHANGE = "trip_change"
    TICKET_EXCHANGE = "ticket_exchange"
    EMD_EXCHANGE = "emd_exchange"
    SERVICE_ONLY = "service_only"


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
    logo_fit_mode: BrandingLogoFitMode = BrandingLogoFitMode.CONTAIN
    preferred_logo_usage: BrandingLogoUsageKey = BrandingLogoUsageKey.HORIZONTAL
    logo_public_usage_allowed: bool = True
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
    logo_fit_mode: Optional[BrandingLogoFitMode] = None
    preferred_logo_usage: Optional[BrandingLogoUsageKey] = None
    logo_public_usage_allowed: Optional[bool] = None
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


class AgencyBrandingLogoAsset(BaseDocument):
    agency_id: str
    branding_settings_id: str
    storage_record_id: Optional[str] = None
    original_asset_id: Optional[str] = None
    variant_key: BrandingLogoVariantKey
    filename: str
    mime_type: str
    width_px: int
    height_px: int
    file_size_bytes: int
    checksum_sha256: str
    data_base64: str
    created_by_user_id: Optional[str] = None
    created_by_email: Optional[EmailStr] = None
    is_public_safe: bool = False
    public_usage_allowed: bool = False
    transparent_background_preserved: bool = False
    fit_mode: BrandingLogoFitMode = BrandingLogoFitMode.CONTAIN


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


class AgencyWebsiteMediaVariant(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    variant_key: str
    mime_type: str
    width_px: int
    height_px: int
    file_size_bytes: int
    checksum_sha256: str
    data_base64: str
    is_public_safe: bool = True


class AgencyWebsiteMediaAsset(BaseDocument):
    agency_id: str
    website_profile_id: Optional[str] = None
    storage_record_id: Optional[str] = None
    asset_type: WebsiteMediaAssetType = WebsiteMediaAssetType.IMAGE
    title: str
    alt_text: str
    caption: Optional[str] = None
    usage_context: WebsiteMediaUsageContext = WebsiteMediaUsageContext.GENERAL
    mime_type: str
    width_px: int
    height_px: int
    file_size_bytes: int
    checksum_sha256: str
    original_filename: str
    public_usage_allowed: bool = True
    is_public_safe: bool = True
    status: WebsiteMediaStatus = WebsiteMediaStatus.ACTIVE
    variants: List[AgencyWebsiteMediaVariant] = Field(default_factory=list)
    created_by_user_id: Optional[str] = None
    created_by_email: Optional[EmailStr] = None
    updated_by_user_id: Optional[str] = None
    updated_by_email: Optional[EmailStr] = None
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)


class AgencyWebsiteMediaUpload(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    filename: str
    content_type: str
    data_base64: str
    title: str
    alt_text: str
    caption: Optional[str] = None
    asset_type: WebsiteMediaAssetType = WebsiteMediaAssetType.IMAGE
    usage_context: WebsiteMediaUsageContext = WebsiteMediaUsageContext.GENERAL
    public_usage_allowed: bool = True


class AgencyWebsiteMediaUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    title: Optional[str] = None
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    usage_context: Optional[WebsiteMediaUsageContext] = None
    public_usage_allowed: Optional[bool] = None
    status: Optional[WebsiteMediaStatus] = None


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
    workspace_id: Optional[str] = None
    client_id: str
    created_by_user_id: str
    trip_id: Optional[str] = None
    existing_trip_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    request_purpose: RequestPurpose = RequestPurpose.NEW_TRIP
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
    pet_count: int = 0
    special_service_count: int = 0
    origin_summary: Optional[str] = None
    destination_summary: Optional[str] = None
    first_departure_date: Optional[date] = None
    last_arrival_date: Optional[date] = None
    requires_medical_review: bool = False
    requires_airline_policy_review: bool = False
    requires_document_followup: bool = False
    has_existing_passenger_links: bool = False
    urgency_reason: Optional[str] = None
    client_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    assigned_user_id: Optional[str] = None
    source_intake_id: Optional[str] = None
    source_entry_path: Optional[str] = None
    submission_channel: SubmissionChannel = SubmissionChannel.STAFF_CONSOLE
    account_origin_at_submission: AccountOriginAtSubmission = AccountOriginAtSubmission.STAFF_CREATED
    canonical_alignment_notes: Dict[str, Any] = Field(default_factory=dict)
    intake_payload_snapshot: Dict[str, Any] = Field(default_factory=dict)
    builder_payload_snapshot: Dict[str, Any] = Field(default_factory=dict)
    closed_at: Optional[datetime] = None


class TravelRequestCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_id: str
    trip_id: Optional[str] = None
    existing_trip_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    request_purpose: RequestPurpose = RequestPurpose.NEW_TRIP
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
    source_entry_path: Optional[str] = None
    submission_channel: SubmissionChannel = SubmissionChannel.STAFF_CONSOLE
    account_origin_at_submission: AccountOriginAtSubmission = AccountOriginAtSubmission.STAFF_CREATED
    canonical_alignment_notes: Dict[str, Any] = Field(default_factory=dict)
    intake_payload_snapshot: Dict[str, Any] = Field(default_factory=dict)
    builder_payload_snapshot: Dict[str, Any] = Field(default_factory=dict)


class TravelRequestUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    title: Optional[str] = None
    trip_id: Optional[str] = None
    existing_trip_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    request_purpose: Optional[RequestPurpose] = None
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
    source_entry_path: Optional[str] = None
    submission_channel: Optional[SubmissionChannel] = None
    account_origin_at_submission: Optional[AccountOriginAtSubmission] = None
    canonical_alignment_notes: Optional[Dict[str, Any]] = None
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
    source_entry_path: Optional[str] = None
    submission_channel: SubmissionChannel = SubmissionChannel.UNKNOWN
    account_origin_at_submission: AccountOriginAtSubmission = AccountOriginAtSubmission.UNKNOWN
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
    agency_custom_fields: Dict[str, Any] = Field(default_factory=dict)
    source_entry_path: Optional[str] = None
    submission_channel: SubmissionChannel = SubmissionChannel.PUBLIC_WEBSITE
    account_origin_at_submission: AccountOriginAtSubmission = AccountOriginAtSubmission.NEW_PUBLIC_CONTACT


class StaffRequestIntakeCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    workspace_id: Optional[str] = None
    source: RequestIntakeSource = RequestIntakeSource.STAFF_MANUAL
    source_entry_path: Optional[str] = None
    submission_channel: SubmissionChannel = SubmissionChannel.STAFF_CONSOLE
    account_origin_at_submission: AccountOriginAtSubmission = AccountOriginAtSubmission.STAFF_CREATED
    contact: RequestIntakeContactSnapshot
    travel: RequestIntakeTravelSummary
    services: RequestIntakeServiceSummary
    priority: RequestPriority = RequestPriority.NORMAL
    assigned_to: Optional[str] = None
    triage_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    request_details: Optional[str] = None
    agency_custom_fields: Dict[str, Any] = Field(default_factory=dict)


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


class TripDossier(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    primary_client_id: Optional[str] = None
    primary_request_id: Optional[str] = None
    linked_request_ids: List[str] = Field(default_factory=list)
    trip_reference: str
    trip_title: str
    trip_status: TripStatus = TripStatus.DRAFT
    trip_type: TripType = TripType.UNKNOWN
    passenger_count: int = 0
    segment_count: int = 0
    service_count: int = 0
    route_summary: Optional[str] = None
    date_summary: Optional[str] = None
    service_summary: Optional[str] = None
    operational_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    source: TripDossierSource = TripDossierSource.MANUAL
    raw_source_payloads: List[Dict[str, Any]] = Field(default_factory=list)
    created_by_user_id: Optional[str] = None
    updated_by_user_id: Optional[str] = None
    archived_at: Optional[datetime] = None
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)


class TripPassenger(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    trip_id: str
    source_request_passenger_id: Optional[str] = None
    passenger_profile_id: Optional[str] = None
    display_name: str
    passenger_type: TripPassengerType = TripPassengerType.UNKNOWN
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    document_summary: Optional[str] = None
    assistance_summary: Optional[str] = None
    service_summary: Optional[str] = None
    sort_order: int = 0


class TripSegment(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    trip_id: str
    source_request_segment_id: Optional[str] = None
    segment_order: int
    origin_airport_code: str
    destination_airport_code: str
    departure_date: Optional[date] = None
    departure_time: Optional[str] = None
    arrival_date: Optional[date] = None
    arrival_time: Optional[str] = None
    marketing_airline_code: Optional[str] = None
    operating_airline_code: Optional[str] = None
    flight_number: Optional[str] = None
    cabin: Optional[str] = None
    booking_class: Optional[str] = None
    segment_status: TripSegmentStatus = TripSegmentStatus.PLANNED


class TripServiceItem(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    trip_id: str
    source_request_service_id: Optional[str] = None
    source_passenger_segment_service_id: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    service_key: Optional[str] = None
    service_catalogue_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    service_code: str
    service_label: str
    service_catalogue_category: Optional[str] = None
    service_family_code: Optional[str] = None
    passenger_ids: List[str] = Field(default_factory=list)
    segment_ids: List[str] = Field(default_factory=list)
    status: TripServiceStatus = TripServiceStatus.REQUESTED
    notes: Optional[str] = None


class TripTimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    workspace_id: Optional[str] = None
    trip_id: str
    actor_user_id: Optional[str] = None
    event_type: str
    title: str
    summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)


class TripDossierCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    workspace_id: Optional[str] = None
    primary_client_id: Optional[str] = None
    trip_title: str
    trip_status: TripStatus = TripStatus.DRAFT
    trip_type: TripType = TripType.UNKNOWN
    route_summary: Optional[str] = None
    date_summary: Optional[str] = None
    service_summary: Optional[str] = None
    operational_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class TripDossierUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    trip_title: Optional[str] = None
    trip_status: Optional[TripStatus] = None
    trip_type: Optional[TripType] = None
    primary_client_id: Optional[str] = None
    route_summary: Optional[str] = None
    date_summary: Optional[str] = None
    service_summary: Optional[str] = None
    operational_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None


class TripLinkRequestPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str


class RequestCaseFlag(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    request_id: str
    travel_request_id: Optional[str] = None
    flag_code: str
    flag_label: str
    severity: str = "info"
    source: str = "manual"
    details: Optional[str] = None
    generated_key: Optional[str] = None
    status: str = "active"


class RequestPassengerSegmentService(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    request_id: str
    travel_request_id: Optional[str] = None
    requested_service_id: Optional[str] = None
    request_passenger_id: Optional[str] = None
    request_segment_id: Optional[str] = None
    passenger_id: Optional[str] = None
    segment_id: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    service_key: Optional[str] = None
    service_catalogue_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    service_family_code: Optional[str] = None
    service_code: str
    service_label: Optional[str] = None
    service_details_json: Dict[str, Any] = Field(default_factory=dict)
    applicability_status: str = "requested"
    generated_key: Optional[str] = None
    notes: Optional[str] = None


class RequestPet(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    request_id: str
    travel_request_id: Optional[str] = None
    request_passenger_id: Optional[str] = None
    passenger_id: Optional[str] = None
    pet_name: Optional[str] = None
    species: str
    breed: Optional[str] = None
    breed_free_text: Optional[str] = None
    snub_nosed_flag: bool = False
    age_months: Optional[int] = None
    pet_weight_kg: Optional[float] = None
    container_weight_kg: Optional[float] = None
    combined_weight_kg: Optional[float] = None
    requested_transport_mode: Optional[str] = None
    carrier_dimensions_cm: Dict[str, Any] = Field(default_factory=dict)
    documentation_status: Optional[str] = None
    special_requirements: Optional[str] = None
    carrier_required: bool = True
    service_animal: bool = False
    generated_key: Optional[str] = None
    notes: Optional[str] = None
    status: str = "active"


class RequestPetSegmentTransport(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    request_id: str
    travel_request_id: Optional[str] = None
    request_pet_id: str
    request_segment_id: str
    service_catalogue_id: Optional[str] = None
    requested_transport_mode: Optional[str] = None
    transport_mode: Optional[str] = None
    generated_key: Optional[str] = None
    status: str = "requested"
    raw_policy_snapshot: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class RequestSpecialItem(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    request_id: str
    travel_request_id: Optional[str] = None
    request_passenger_id: Optional[str] = None
    owner_passenger_id: Optional[str] = None
    item_type: str
    item_category_code: Optional[str] = None
    item_name: Optional[str] = None
    description: str
    quantity: int = 1
    weight_kg: Optional[float] = None
    dimensions_cm: Dict[str, Any] = Field(default_factory=dict)
    battery_type: Optional[str] = None
    battery_wh: Optional[float] = None
    transport_location: Optional[str] = None
    usage_in_cabin_flag: bool = False
    special_handling_instructions: Optional[str] = None
    documentation_status: Optional[str] = None
    dimensions_text: Optional[str] = None
    weight_text: Optional[str] = None
    requires_policy_check: bool = True
    generated_key: Optional[str] = None
    notes: Optional[str] = None
    status: str = "active"


class RequestSpecialItemSegment(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    request_id: str
    travel_request_id: Optional[str] = None
    request_special_item_id: str
    request_segment_id: str
    transport_location: Optional[str] = None
    applicability_status: str = "requested"
    generated_key: Optional[str] = None
    raw_policy_snapshot: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class RequestPassenger(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    request_id: str
    travel_request_id: Optional[str] = None
    passenger_id: Optional[str] = None
    passenger_link_mode: PassengerLinkMode = PassengerLinkMode.EXISTING
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
    passenger_link_mode: PassengerLinkMode = PassengerLinkMode.EXISTING
    client_passenger_relationship_id: Optional[str] = None
    role_in_request: RequestPassengerRole = RequestPassengerRole.TRAVELER
    is_primary_traveler: bool = False
    service_needs_summary: Optional[str] = None


class RequestPassengerUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_passenger_relationship_id: Optional[str] = None
    passenger_link_mode: Optional[PassengerLinkMode] = None
    role_in_request: Optional[RequestPassengerRole] = None
    is_primary_traveler: Optional[bool] = None
    service_needs_summary: Optional[str] = None


class RequestSegment(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    request_id: str
    travel_request_id: Optional[str] = None
    trip_segment_id: Optional[str] = None
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
    trip_segment_id: Optional[str] = None
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
    trip_segment_id: Optional[str] = None
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
    workspace_id: Optional[str] = None
    request_id: str
    travel_request_id: Optional[str] = None
    request_passenger_segment_service_ids: List[str] = Field(default_factory=list)
    passenger_id: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    service_key: Optional[str] = None
    service_catalogue_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    service_family_code: Optional[str] = None
    service_code: str
    service_name: str
    service_category: str
    service_details_json: Dict[str, Any] = Field(default_factory=dict)
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
    request_passenger_segment_service_ids: List[str] = Field(default_factory=list)
    service_catalogue_id: Optional[str] = None
    service_key: Optional[str] = None
    service_catalogue_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
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
    request_passenger_segment_service_ids: Optional[List[str]] = None
    service_catalogue_id: Optional[str] = None
    service_key: Optional[str] = None
    service_catalogue_snapshot_json: Optional[Dict[str, Any]] = None
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
    passenger_link_mode: PassengerLinkMode = PassengerLinkMode.UNRESOLVED
    request_passenger_key: Optional[str] = None
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
    segment_key: Optional[str] = None
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
    service_code: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    service_family_code: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    passenger_ids: List[str] = Field(default_factory=list)
    segment_ids: List[str] = Field(default_factory=list)
    applies_to_all_passengers: bool = True
    applies_to_all_segments: bool = True
    notes: Optional[str] = None


class OperationalRequestBuilderPetSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_key: Optional[str] = None
    request_segment_id: Optional[str] = None
    requested_transport_mode: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    notes: Optional[str] = None


class OperationalRequestBuilderPet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pet_key: Optional[str] = None
    request_passenger_key: Optional[str] = None
    request_passenger_id: Optional[str] = None
    passenger_id: Optional[str] = None
    pet_name: Optional[str] = None
    species: str = "dog"
    breed: Optional[str] = None
    breed_free_text: Optional[str] = None
    snub_nosed_flag: bool = False
    age_months: Optional[int] = None
    pet_weight_kg: Optional[float] = None
    container_weight_kg: Optional[float] = None
    combined_weight_kg: Optional[float] = None
    requested_transport_mode: Optional[str] = "petc"
    carrier_dimensions_cm: Dict[str, Any] = Field(default_factory=dict)
    documentation_status: Optional[str] = None
    special_requirements: Optional[str] = None
    segment_transports: List[OperationalRequestBuilderPetSegment] = Field(default_factory=list)
    notes: Optional[str] = None


class OperationalRequestBuilderSpecialItemSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_key: Optional[str] = None
    request_segment_id: Optional[str] = None
    transport_location: Optional[str] = None
    notes: Optional[str] = None


class OperationalRequestBuilderSpecialItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_key: Optional[str] = None
    request_passenger_key: Optional[str] = None
    request_passenger_id: Optional[str] = None
    owner_passenger_id: Optional[str] = None
    item_category_code: str = "other"
    item_name: Optional[str] = None
    description: str = "Special item"
    quantity: int = 1
    weight_kg: Optional[float] = None
    dimensions_cm: Dict[str, Any] = Field(default_factory=dict)
    battery_type: Optional[str] = None
    battery_wh: Optional[float] = None
    transport_location: Optional[str] = "checked_baggage"
    usage_in_cabin_flag: bool = False
    special_handling_instructions: Optional[str] = None
    documentation_status: Optional[str] = None
    segment_transports: List[OperationalRequestBuilderSpecialItemSegment] = Field(default_factory=list)
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
    pets: List[OperationalRequestBuilderPet] = Field(default_factory=list)
    special_items: List[OperationalRequestBuilderSpecialItem] = Field(default_factory=list)
    title: Optional[str] = None
    status: RequestStatus = RequestStatus.NEW
    priority: RequestPriority = RequestPriority.NORMAL
    source: RequestSource = RequestSource.STAFF_CREATED
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    agency_custom_fields: Dict[str, Any] = Field(default_factory=dict)


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


class OfferWorkspaceStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    SHARED = "shared"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class OfferOptionType(str, Enum):
    FLIGHT = "flight"
    PACKAGE = "package"
    SERVICE_ONLY = "service_only"
    MANUAL = "manual"


class OfferOptionStatus(str, Enum):
    DRAFT = "draft"
    RECOMMENDED = "recommended"
    ALTERNATE = "alternate"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class OfferProviderName(str, Enum):
    MANUAL = "manual"
    TRAVELPORT = "travelport"
    AMADEUS = "amadeus"
    NDC = "ndc"
    SUPPLIER = "supplier"
    OTHER = "other"


class OfferBuilderPricingLineType(str, Enum):
    BASE_FARE = "base_fare"
    TAX = "tax"
    SURCHARGE = "surcharge"
    SERVICE_FEE = "service_fee"
    COMMISSION = "commission"
    DISCOUNT = "discount"
    ANCILLARY = "ancillary"
    OTHER = "other"


class OfferWorkspace(BaseDocument):
    agency_id: str
    request_id: Optional[str] = None
    trip_id: Optional[str] = None
    existing_trip_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    offer_purpose: OfferPurpose = OfferPurpose.NEW_BOOKING
    title: str
    status: OfferWorkspaceStatus = OfferWorkspaceStatus.DRAFT
    currency: str = "EUR"
    client_summary_json: Dict[str, Any] = Field(default_factory=dict)
    internal_notes: Optional[str] = None
    created_by_user_id: Optional[str] = None
    updated_by_user_id: Optional[str] = None


class OfferWorkspaceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    request_id: Optional[str] = None
    trip_id: Optional[str] = None
    existing_trip_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    offer_purpose: OfferPurpose = OfferPurpose.NEW_BOOKING
    title: str
    status: OfferWorkspaceStatus = OfferWorkspaceStatus.DRAFT
    currency: str = "EUR"
    client_summary_json: Dict[str, Any] = Field(default_factory=dict)
    internal_notes: Optional[str] = None


class OfferWorkspaceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    request_id: Optional[str] = None
    trip_id: Optional[str] = None
    existing_trip_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    offer_purpose: Optional[OfferPurpose] = None
    title: Optional[str] = None
    status: Optional[OfferWorkspaceStatus] = None
    currency: Optional[str] = None
    client_summary_json: Optional[Dict[str, Any]] = None
    internal_notes: Optional[str] = None


class OfferOption(BaseDocument):
    agency_id: str
    workspace_id: str
    request_id: Optional[str] = None
    trip_id: Optional[str] = None
    existing_trip_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    offer_purpose: OfferPurpose = OfferPurpose.NEW_BOOKING
    label: str
    option_type: OfferOptionType = OfferOptionType.FLIGHT
    status: OfferOptionStatus = OfferOptionStatus.DRAFT
    recommendation_rank: Optional[int] = None
    recommendation_tag: Optional[str] = None
    main_airline_id: Optional[str] = None
    main_airline_code: Optional[str] = None
    provider_name: OfferProviderName = OfferProviderName.MANUAL
    source_payload_json: Dict[str, Any] = Field(default_factory=dict)
    rules_summary_json: Dict[str, Any] = Field(default_factory=dict)
    service_feasibility_json: Dict[str, Any] = Field(default_factory=dict)
    pricing_summary_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    internal_notes: Optional[str] = None


class OfferOptionCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    existing_trip_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    offer_purpose: OfferPurpose = OfferPurpose.NEW_BOOKING
    label: str
    option_type: OfferOptionType = OfferOptionType.FLIGHT
    status: OfferOptionStatus = OfferOptionStatus.DRAFT
    recommendation_rank: Optional[int] = None
    recommendation_tag: Optional[str] = None
    main_airline_id: Optional[str] = None
    main_airline_code: Optional[str] = None
    provider_name: OfferProviderName = OfferProviderName.MANUAL
    source_payload_json: Dict[str, Any] = Field(default_factory=dict)
    rules_summary_json: Dict[str, Any] = Field(default_factory=dict)
    service_feasibility_json: Dict[str, Any] = Field(default_factory=dict)
    pricing_summary_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    internal_notes: Optional[str] = None


class OfferOptionUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    existing_trip_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    offer_purpose: Optional[OfferPurpose] = None
    label: Optional[str] = None
    option_type: Optional[OfferOptionType] = None
    status: Optional[OfferOptionStatus] = None
    recommendation_rank: Optional[int] = None
    recommendation_tag: Optional[str] = None
    main_airline_id: Optional[str] = None
    main_airline_code: Optional[str] = None
    provider_name: Optional[OfferProviderName] = None
    source_payload_json: Optional[Dict[str, Any]] = None
    rules_summary_json: Optional[Dict[str, Any]] = None
    service_feasibility_json: Optional[Dict[str, Any]] = None
    pricing_summary_json: Optional[Dict[str, Any]] = None
    warnings_json: Optional[List[Dict[str, Any]]] = None
    internal_notes: Optional[str] = None


class OfferRoutingOption(BaseDocument):
    agency_id: str
    option_id: str
    origin_airport: str
    destination_airport: str
    route_path_json: List[Dict[str, Any]] = Field(default_factory=list)
    total_duration_minutes: Optional[int] = None
    stops_count: int = 0
    validating_carrier_code: Optional[str] = None
    marketing_carriers_json: List[Dict[str, Any]] = Field(default_factory=list)
    operating_carriers_json: List[Dict[str, Any]] = Field(default_factory=list)
    mileage_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)


class OfferRoutingOptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin_airport: str
    destination_airport: str
    route_path_json: List[Dict[str, Any]] = Field(default_factory=list)
    total_duration_minutes: Optional[int] = None
    stops_count: int = 0
    validating_carrier_code: Optional[str] = None
    marketing_carriers_json: List[Dict[str, Any]] = Field(default_factory=list)
    operating_carriers_json: List[Dict[str, Any]] = Field(default_factory=list)
    mileage_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)


class OfferBuilderSegment(BaseDocument):
    agency_id: str
    option_id: str
    routing_id: Optional[str] = None
    sequence: int
    marketing_airline_code: str
    operating_airline_code: Optional[str] = None
    flight_number: Optional[str] = None
    origin_airport: str
    destination_airport: str
    departure_at: Optional[datetime] = None
    arrival_at: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    cabin_class: Optional[str] = None
    booking_class: Optional[str] = None
    fare_basis: Optional[str] = None
    segment_status: str = "proposed"
    source_payload_json: Dict[str, Any] = Field(default_factory=dict)


class OfferBuilderSegmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    routing_id: Optional[str] = None
    sequence: int
    marketing_airline_code: str
    operating_airline_code: Optional[str] = None
    flight_number: Optional[str] = None
    origin_airport: str
    destination_airport: str
    departure_at: Optional[datetime] = None
    arrival_at: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    cabin_class: Optional[str] = None
    booking_class: Optional[str] = None
    fare_basis: Optional[str] = None
    segment_status: str = "proposed"
    source_payload_json: Dict[str, Any] = Field(default_factory=dict)


class OfferFareBundle(BaseDocument):
    agency_id: str
    option_id: str
    fare_family_name: str
    cabin_class: str
    booking_class: Optional[str] = None
    included_baggage_json: Dict[str, Any] = Field(default_factory=dict)
    seat_selection_rules_json: Dict[str, Any] = Field(default_factory=dict)
    change_rules_json: Dict[str, Any] = Field(default_factory=dict)
    refund_rules_json: Dict[str, Any] = Field(default_factory=dict)
    meal_rules_json: Dict[str, Any] = Field(default_factory=dict)
    lounge_rules_json: Dict[str, Any] = Field(default_factory=dict)
    priority_rules_json: Dict[str, Any] = Field(default_factory=dict)
    upgrade_eligibility_json: Dict[str, Any] = Field(default_factory=dict)
    restrictions_json: Dict[str, Any] = Field(default_factory=dict)


class OfferFareBundleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fare_family_name: str
    cabin_class: str
    booking_class: Optional[str] = None
    included_baggage_json: Dict[str, Any] = Field(default_factory=dict)
    seat_selection_rules_json: Dict[str, Any] = Field(default_factory=dict)
    change_rules_json: Dict[str, Any] = Field(default_factory=dict)
    refund_rules_json: Dict[str, Any] = Field(default_factory=dict)
    meal_rules_json: Dict[str, Any] = Field(default_factory=dict)
    lounge_rules_json: Dict[str, Any] = Field(default_factory=dict)
    priority_rules_json: Dict[str, Any] = Field(default_factory=dict)
    upgrade_eligibility_json: Dict[str, Any] = Field(default_factory=dict)
    restrictions_json: Dict[str, Any] = Field(default_factory=dict)


class OfferPricingLine(BaseDocument):
    agency_id: str
    option_id: str
    line_type: OfferBuilderPricingLineType
    label: str
    amount: float = 0
    currency: str = "EUR"
    passenger_scope: Optional[str] = None
    segment_scope: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferPricingLineCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    line_type: OfferBuilderPricingLineType
    label: str
    amount: float = 0
    currency: str = "EUR"
    passenger_scope: Optional[str] = None
    segment_scope: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferComparisonSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    workspace_id: str
    matrix_json: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=now_utc)
    generated_by_user_id: Optional[str] = None


class OfferRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    option_id: str
    tag: Optional[str] = None
    rank: Optional[int] = None


class OfferAcceptanceSource(str, Enum):
    INTERNAL = "internal"
    CLIENT_PREVIEW = "client_preview"
    MANUAL = "manual"
    IMPORTED = "imported"


class OfferAcceptanceStatus(str, Enum):
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"


class BookingReadinessStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    BLOCKED = "blocked"
    BOOKED = "booked"
    CANCELLED = "cancelled"


class BookingProviderTarget(str, Enum):
    MANUAL = "manual"
    TRAVELPORT = "travelport"
    AMADEUS = "amadeus"
    NDC = "ndc"
    SUPPLIER = "supplier"
    OTHER = "other"


class BookingWorkspaceStatus(str, Enum):
    DRAFT = "draft"
    READY_TO_BOOK = "ready_to_book"
    BOOKING_IN_PROGRESS = "booking_in_progress"
    BOOKED = "booked"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class BookingRecordProviderStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    HELD = "held"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BookingRecordStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PARTIALLY_CONFIRMED = "partially_confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BookingSourceContext(str, Enum):
    OFFER_READINESS = "offer_readiness"
    STANDALONE_MANUAL = "standalone_manual"
    IMPORTED_GDS = "imported_gds"
    IMPORTED_CONFIRMATION = "imported_confirmation"
    EXISTING_TRIP_CHANGE = "existing_trip_change"


class TicketSourceContext(str, Enum):
    BOOKING_RECORD = "booking_record"
    STANDALONE_MANUAL = "standalone_manual"
    IMPORTED_GDS = "imported_gds"
    IMPORTED_CONFIRMATION = "imported_confirmation"
    EXCHANGE_REISSUE = "exchange_reissue"
    EXISTING_TRIP_CHANGE = "existing_trip_change"


class EmdSourceContext(str, Enum):
    BOOKING_SERVICE = "booking_service"
    STANDALONE_MANUAL = "standalone_manual"
    IMPORTED_GDS = "imported_gds"
    IMPORTED_CONFIRMATION = "imported_confirmation"
    EXCHANGE_REISSUE = "exchange_reissue"
    EXISTING_TRIP_CHANGE = "existing_trip_change"


class BookingImportDraftSourceType(str, Enum):
    CRYPTIC_GDS = "cryptic_gds"
    ITINERARY_CONFIRMATION_TEXT = "itinerary_confirmation_text"
    MANUAL_TEXT = "manual_text"
    EMAIL_IMPORT = "email_import"
    PDF_IMPORT = "pdf_import"
    OTHER = "other"


class BookingImportParserStatus(str, Enum):
    DRAFT = "draft"
    PARSED = "parsed"
    NEEDS_REVIEW = "needs_review"
    IMPORTED = "imported"
    FAILED = "failed"


class BookingImportContext(str, Enum):
    NEW_BOOKING = "new_booking"
    EXISTING_TRIP_CHANGE = "existing_trip_change"
    STANDALONE_TICKET = "standalone_ticket"
    STANDALONE_EMD = "standalone_emd"
    OTHER = "other"


class TripChangeOperationType(str, Enum):
    ITINERARY_CHANGE = "itinerary_change"
    BOOKING_CHANGE = "booking_change"
    TICKET_EXCHANGE = "ticket_exchange"
    TICKET_REISSUE = "ticket_reissue"
    EMD_EXCHANGE = "emd_exchange"
    EMD_REISSUE = "emd_reissue"
    CANCELLATION = "cancellation"
    REFUND_QUOTE = "refund_quote"
    SERVICE_CHANGE = "service_change"
    OTHER = "other"


class TripChangeOperationStatus(str, Enum):
    DRAFT = "draft"
    EVALUATING = "evaluating"
    QUOTED = "quoted"
    ACCEPTED = "accepted"
    MIRRORED = "mirrored"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TicketExchangeOperationType(str, Enum):
    EXCHANGE = "exchange"
    REISSUE = "reissue"
    VOID = "void"
    REFUND = "refund"
    NAME_CORRECTION = "name_correction"
    SCHEDULE_CHANGE_REISSUE = "schedule_change_reissue"
    OTHER = "other"


class EmdExchangeOperationType(str, Enum):
    EXCHANGE = "exchange"
    REISSUE = "reissue"
    VOID = "void"
    REFUND = "refund"
    SERVICE_CHANGE = "service_change"
    OTHER = "other"


class ExchangeOperationStatus(str, Enum):
    DRAFT = "draft"
    QUOTED = "quoted"
    ACCEPTED = "accepted"
    MIRRORED = "mirrored"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OfferAcceptance(BaseDocument):
    agency_id: str
    workspace_id: str
    option_id: str
    request_id: Optional[str] = None
    trip_id: Optional[str] = None
    accepted_by_user_id: Optional[str] = None
    accepted_at: datetime = Field(default_factory=now_utc)
    acceptance_source: OfferAcceptanceSource = OfferAcceptanceSource.INTERNAL
    status: OfferAcceptanceStatus = OfferAcceptanceStatus.ACCEPTED
    accepted_pricing_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    accepted_routing_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    accepted_fare_bundle_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    accepted_services_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    accepted_pets_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    accepted_special_items_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    rules_feasibility_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    client_visible_summary_json: Dict[str, Any] = Field(default_factory=dict)
    internal_notes: Optional[str] = None


class OfferAcceptanceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    acceptance_source: OfferAcceptanceSource = OfferAcceptanceSource.INTERNAL
    provider_target: BookingProviderTarget = BookingProviderTarget.MANUAL
    client_visible_summary_json: Dict[str, Any] = Field(default_factory=dict)
    internal_notes: Optional[str] = None


class TripAcceptedOfferSnapshot(BaseDocument):
    agency_id: str
    trip_id: str
    request_id: Optional[str] = None
    workspace_id: str
    option_id: str
    acceptance_id: str
    confirmed_segments_json: List[Dict[str, Any]] = Field(default_factory=list)
    confirmed_passengers_json: List[Dict[str, Any]] = Field(default_factory=list)
    confirmed_fare_bundle_json: Dict[str, Any] = Field(default_factory=dict)
    confirmed_pricing_json: Dict[str, Any] = Field(default_factory=dict)
    confirmed_services_json: Dict[str, Any] = Field(default_factory=dict)
    confirmed_pets_json: Dict[str, Any] = Field(default_factory=dict)
    confirmed_special_items_json: Dict[str, Any] = Field(default_factory=dict)
    ssr_osi_preview_json: Dict[str, Any] = Field(default_factory=dict)
    booking_readiness_json: Dict[str, Any] = Field(default_factory=dict)


class BookingReadinessPackage(BaseDocument):
    agency_id: str
    trip_id: str
    request_id: Optional[str] = None
    workspace_id: Optional[str] = None
    option_id: Optional[str] = None
    acceptance_id: Optional[str] = None
    status: BookingReadinessStatus = BookingReadinessStatus.DRAFT
    provider_target: BookingProviderTarget = BookingProviderTarget.MANUAL
    passengers_snapshot_json: List[Dict[str, Any]] = Field(default_factory=list)
    segments_snapshot_json: List[Dict[str, Any]] = Field(default_factory=list)
    pricing_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    services_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    pets_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    special_items_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    ssr_json: List[Dict[str, Any]] = Field(default_factory=list)
    osi_json: List[Dict[str, Any]] = Field(default_factory=list)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    required_documents_json: List[Dict[str, Any]] = Field(default_factory=list)
    policy_violations_json: List[Dict[str, Any]] = Field(default_factory=list)
    readiness_checks_json: Dict[str, Any] = Field(default_factory=dict)
    created_by_user_id: Optional[str] = None


class BookingWorkspace(BaseDocument):
    agency_id: str
    source_context: BookingSourceContext = BookingSourceContext.OFFER_READINESS
    client_id: Optional[str] = None
    passenger_ids: List[str] = Field(default_factory=list)
    trip_id: Optional[str] = None
    request_id: Optional[str] = None
    offer_workspace_id: Optional[str] = None
    offer_option_id: Optional[str] = None
    offer_acceptance_id: Optional[str] = None
    booking_readiness_package_id: Optional[str] = None
    import_draft_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    booking_record_id: Optional[str] = None
    workspace_number: str
    title: str
    status: BookingWorkspaceStatus = BookingWorkspaceStatus.DRAFT
    provider_target: BookingProviderTarget = BookingProviderTarget.MANUAL
    source_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    passengers_snapshot_json: List[Dict[str, Any]] = Field(default_factory=list)
    segments_snapshot_json: List[Dict[str, Any]] = Field(default_factory=list)
    pricing_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    services_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    pets_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    special_items_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    required_documents_json: List[Dict[str, Any]] = Field(default_factory=list)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    policy_violations_json: List[Dict[str, Any]] = Field(default_factory=list)
    ssr_json: List[Dict[str, Any]] = Field(default_factory=list)
    osi_json: List[Dict[str, Any]] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    created_by_user_id: Optional[str] = None


class BookingRecord(BaseDocument):
    agency_id: str
    booking_workspace_id: str
    source_context: BookingSourceContext = BookingSourceContext.OFFER_READINESS
    client_id: Optional[str] = None
    passenger_ids: List[str] = Field(default_factory=list)
    trip_id: Optional[str] = None
    request_id: Optional[str] = None
    booking_readiness_package_id: Optional[str] = None
    offer_acceptance_id: Optional[str] = None
    import_draft_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    original_booking_record_id: Optional[str] = None
    revision_reason: Optional[str] = None
    pnr_locator: Optional[str] = None
    provider: BookingProviderTarget = BookingProviderTarget.MANUAL
    provider_status: BookingRecordProviderStatus = BookingRecordProviderStatus.DRAFT
    booking_status: BookingRecordStatus = BookingRecordStatus.DRAFT
    passengers_json: List[Dict[str, Any]] = Field(default_factory=list)
    segments_json: List[Dict[str, Any]] = Field(default_factory=list)
    pricing_json: Dict[str, Any] = Field(default_factory=dict)
    services_json: Dict[str, Any] = Field(default_factory=dict)
    pets_json: Dict[str, Any] = Field(default_factory=dict)
    special_items_json: Dict[str, Any] = Field(default_factory=dict)
    ssr_json: List[Dict[str, Any]] = Field(default_factory=list)
    osi_json: List[Dict[str, Any]] = Field(default_factory=list)
    provider_payload_json: Dict[str, Any] = Field(default_factory=dict)
    provider_response_json: Dict[str, Any] = Field(default_factory=dict)
    internal_pnr_mirror_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    created_by_user_id: Optional[str] = None


class BookingCreateFromReadinessRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    booking_readiness_package_id: str
    provider_target: Optional[BookingProviderTarget] = None
    internal_notes: Optional[str] = None
    create_draft_record: bool = True


class ManualBookingWorkspaceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    client_id: Optional[str] = None
    passenger_ids: List[str] = Field(default_factory=list)
    trip_id: Optional[str] = None
    title: Optional[str] = None
    provider_target: BookingProviderTarget = BookingProviderTarget.MANUAL
    pnr_locator: Optional[str] = None
    passengers_json: List[Dict[str, Any]] = Field(default_factory=list)
    segments_json: List[Dict[str, Any]] = Field(default_factory=list)
    pricing_json: Dict[str, Any] = Field(default_factory=dict)
    services_json: Dict[str, Any] = Field(default_factory=dict)
    pets_json: Dict[str, Any] = Field(default_factory=dict)
    special_items_json: Dict[str, Any] = Field(default_factory=dict)
    ssr_json: List[Dict[str, Any]] = Field(default_factory=list)
    osi_json: List[Dict[str, Any]] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    create_draft_record: bool = True
    source_context: BookingSourceContext = BookingSourceContext.STANDALONE_MANUAL
    import_draft_id: Optional[str] = None
    trip_change_operation_id: Optional[str] = None
    original_booking_record_id: Optional[str] = None
    revision_reason: Optional[str] = None


class BookingWorkspaceStatusUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: BookingWorkspaceStatus
    internal_notes: Optional[str] = None


class BookingRecordUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    pnr_locator: Optional[str] = None
    provider_status: Optional[BookingRecordProviderStatus] = None
    booking_status: Optional[BookingRecordStatus] = None
    passengers_json: Optional[List[Dict[str, Any]]] = None
    segments_json: Optional[List[Dict[str, Any]]] = None
    pricing_json: Optional[Dict[str, Any]] = None
    services_json: Optional[Dict[str, Any]] = None
    pets_json: Optional[Dict[str, Any]] = None
    special_items_json: Optional[Dict[str, Any]] = None
    ssr_json: Optional[List[Dict[str, Any]]] = None
    osi_json: Optional[List[Dict[str, Any]]] = None
    provider_payload_json: Optional[Dict[str, Any]] = None
    provider_response_json: Optional[Dict[str, Any]] = None
    internal_notes: Optional[str] = None


class BookingImportDraft(BaseDocument):
    agency_id: str
    created_by_user_id: Optional[str] = None
    source_type: BookingImportDraftSourceType = BookingImportDraftSourceType.CRYPTIC_GDS
    raw_text: str
    parsed_json: Dict[str, Any] = Field(default_factory=dict)
    parser_status: BookingImportParserStatus = BookingImportParserStatus.DRAFT
    latest_parser_run_id: Optional[str] = None
    parser_profile_id: Optional[str] = None
    parser_version_id: Optional[str] = None
    overall_confidence: Optional[float] = None
    parsed_entity_counts_json: Dict[str, Any] = Field(default_factory=dict)
    normalized_preview_json: Dict[str, Any] = Field(default_factory=dict)
    linked_client_id: Optional[str] = None
    linked_passenger_ids: List[str] = Field(default_factory=list)
    linked_trip_id: Optional[str] = None
    import_context: BookingImportContext = BookingImportContext.NEW_BOOKING
    linked_booking_workspace_id: Optional[str] = None
    linked_booking_record_id: Optional[str] = None
    linked_ticket_record_ids: List[str] = Field(default_factory=list)
    linked_emd_record_ids: List[str] = Field(default_factory=list)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    error_json: Dict[str, Any] = Field(default_factory=dict)


class BookingImportDraftCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    source_type: BookingImportDraftSourceType = BookingImportDraftSourceType.CRYPTIC_GDS
    raw_text: str
    linked_client_id: Optional[str] = None
    linked_passenger_ids: List[str] = Field(default_factory=list)
    linked_trip_id: Optional[str] = None
    import_context: BookingImportContext = BookingImportContext.NEW_BOOKING


class BookingImportDraftImportRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    title: Optional[str] = None
    provider_target: BookingProviderTarget = BookingProviderTarget.MANUAL
    create_draft_record: bool = True
    create_ticket_mirrors: bool = False
    create_emd_mirrors: bool = False
    internal_notes: Optional[str] = None


class TripChangeOperation(BaseDocument):
    agency_id: str
    trip_id: str
    request_id: Optional[str] = None
    offer_workspace_id: Optional[str] = None
    offer_option_id: Optional[str] = None
    source_booking_workspace_id: Optional[str] = None
    source_booking_record_id: Optional[str] = None
    new_booking_workspace_id: Optional[str] = None
    new_booking_record_id: Optional[str] = None
    operation_type: TripChangeOperationType
    status: TripChangeOperationStatus = TripChangeOperationStatus.DRAFT
    reason: Optional[str] = None
    change_summary_json: Dict[str, Any] = Field(default_factory=dict)
    original_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    proposed_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    accepted_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    created_by_user_id: Optional[str] = None


class TripChangeOperationCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    request_id: Optional[str] = None
    source_booking_workspace_id: Optional[str] = None
    source_booking_record_id: Optional[str] = None
    operation_type: TripChangeOperationType
    reason: Optional[str] = None
    change_summary_json: Dict[str, Any] = Field(default_factory=dict)
    original_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    proposed_snapshot_json: Dict[str, Any] = Field(default_factory=dict)


class TicketExchangeOperation(BaseDocument):
    agency_id: str
    trip_id: Optional[str] = None
    booking_record_id: Optional[str] = None
    original_ticket_record_id: str
    new_ticket_record_id: Optional[str] = None
    operation_type: TicketExchangeOperationType
    status: ExchangeOperationStatus = ExchangeOperationStatus.DRAFT
    reason: Optional[str] = None
    residual_value_amount: Optional[float] = None
    additional_collection_amount: Optional[float] = None
    penalty_amount: Optional[float] = None
    tax_difference_amount: Optional[float] = None
    currency: Optional[str] = None
    fare_difference_json: Dict[str, Any] = Field(default_factory=dict)
    original_ticket_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    new_ticket_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    created_by_user_id: Optional[str] = None


class TicketExchangeOperationCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    trip_id: Optional[str] = None
    booking_record_id: Optional[str] = None
    original_ticket_record_id: str
    operation_type: TicketExchangeOperationType
    reason: Optional[str] = None
    residual_value_amount: Optional[float] = None
    additional_collection_amount: Optional[float] = None
    penalty_amount: Optional[float] = None
    tax_difference_amount: Optional[float] = None
    currency: Optional[str] = None
    fare_difference_json: Dict[str, Any] = Field(default_factory=dict)


class EmdExchangeOperation(BaseDocument):
    agency_id: str
    trip_id: Optional[str] = None
    booking_record_id: Optional[str] = None
    original_emd_record_id: str
    new_emd_record_id: Optional[str] = None
    operation_type: EmdExchangeOperationType
    status: ExchangeOperationStatus = ExchangeOperationStatus.DRAFT
    reason: Optional[str] = None
    residual_value_amount: Optional[float] = None
    additional_collection_amount: Optional[float] = None
    penalty_amount: Optional[float] = None
    currency: Optional[str] = None
    original_emd_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    new_emd_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    created_by_user_id: Optional[str] = None


class EmdExchangeOperationCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    trip_id: Optional[str] = None
    booking_record_id: Optional[str] = None
    original_emd_record_id: str
    operation_type: EmdExchangeOperationType
    reason: Optional[str] = None
    residual_value_amount: Optional[float] = None
    additional_collection_amount: Optional[float] = None
    penalty_amount: Optional[float] = None
    currency: Optional[str] = None


class AiTraceType(str, Enum):
    PARSING = "parsing"
    OFFER_BUILDER = "offer_builder"
    PNR_FIX = "pnr_fix"
    RULES_SERVICES = "rules_services"
    AIRLINE_INTELLIGENCE = "airline_intelligence"
    ADM_RISK = "adm_risk"
    DOCUMENT_GENERATION = "document_generation"
    DEBUG_CONSOLE = "debug_console"


class AdmRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GdsParseSampleMode(str, Enum):
    PNR = "pnr"
    AVAIL = "avail"
    FARE = "fare"
    TICKETING = "ticketing"
    OTHER = "other"


class GdsParseSampleSource(str, Enum):
    MANUAL = "manual"
    BOOKING_IMPORT_DRAFT = "booking_import_draft"
    PARSER_RUN = "parser_run"
    MANUAL_UPLOAD = "manual_upload"
    SYNTHETIC = "synthetic"
    TRAVELPORT = "travelport"
    AMADEUS = "amadeus"
    SUPPLIER = "supplier"
    OTHER = "other"


class GdsProviderFamily(str, Enum):
    AMADEUS = "amadeus"
    SABRE = "sabre"
    TRAVELPORT = "travelport"
    GENERIC_GDS = "generic_gds"
    AIRLINE_CONFIRMATION = "airline_confirmation"
    AGENCY_ITINERARY = "agency_itinerary"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class GdsInputFormat(str, Enum):
    CRYPTIC_PNR = "cryptic_pnr"
    ITINERARY_TEXT = "itinerary_text"
    TICKET_TEXT = "ticket_text"
    EMD_TEXT = "emd_text"
    PRICING_TEXT = "pricing_text"
    QUEUE_MESSAGE = "queue_message"
    EMAIL_CONFIRMATION = "email_confirmation"
    MIXED_TEXT = "mixed_text"
    UNKNOWN = "unknown"


class GdsParserStrategy(str, Enum):
    REGEX_RULES = "regex_rules"
    SECTION_RULES = "section_rules"
    HYBRID_RULES = "hybrid_rules"
    MANUAL_REVIEW_ONLY = "manual_review_only"


class GdsParserVersionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class GdsParserRunStatus(str, Enum):
    PARSED = "parsed"
    PARTIAL = "partial"
    FAILED = "failed"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class GdsParsedEntityType(str, Enum):
    PASSENGER = "passenger"
    SEGMENT = "segment"
    TICKET = "ticket"
    TICKET_COUPON = "ticket_coupon"
    EMD = "emd"
    EMD_COUPON = "emd_coupon"
    SSR = "ssr"
    OSI = "osi"
    PRICING = "pricing"
    FARE_BASIS = "fare_basis"
    BAGGAGE = "baggage"
    CONTACT = "contact"
    REMARK = "remark"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class GdsParsedEntityStatus(str, Enum):
    EXTRACTED = "extracted"
    ACCEPTED = "accepted"
    CORRECTED = "corrected"
    REJECTED = "rejected"
    IGNORED = "ignored"


class GdsParseCorrectionType(str, Enum):
    ACCEPT = "accept"
    CORRECT = "correct"
    REJECT = "reject"
    IGNORE = "ignore"
    ADD_MISSING = "add_missing"


class GdsParseSampleScope(str, Enum):
    PLATFORM = "platform"
    AGENCY = "agency"


class GdsParseSampleStatus(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROMOTED = "promoted"


class GdsParseSampleDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EDGE_CASE = "edge_case"


class GdsParseSampleRedactionStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    REDACTED = "redacted"


class GdsParserEvaluationStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AirlineBrandAssetType(str, Enum):
    LOGO = "logo"
    COLOR_PALETTE = "color_palette"
    TYPOGRAPHY = "typography"
    GUIDELINE = "guideline"
    IMAGE = "image"
    OTHER = "other"


class AiTraceEvent(BaseDocument):
    agency_id: Optional[str] = None
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_type: AiTraceType
    source_module: str
    input_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    output_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = None
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    error_json: Dict[str, Any] = Field(default_factory=dict)
    provider: Optional[str] = None
    model_name: Optional[str] = None


class AdmRiskEvent(BaseDocument):
    agency_id: Optional[str] = None
    trip_id: Optional[str] = None
    request_id: Optional[str] = None
    offer_workspace_id: Optional[str] = None
    offer_option_id: Optional[str] = None
    booking_workspace_id: Optional[str] = None
    booking_record_id: Optional[str] = None
    ticket_record_id: Optional[str] = None
    emd_record_id: Optional[str] = None
    airline_id: Optional[str] = None
    risk_level: AdmRiskLevel = AdmRiskLevel.LOW
    risk_factors_json: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_actions_json: List[Dict[str, Any]] = Field(default_factory=list)
    source_context_json: Dict[str, Any] = Field(default_factory=dict)
    created_by_user_id: Optional[str] = None


class GdsParseSample(BaseDocument):
    agency_id: Optional[str] = None
    created_by_user_id: Optional[str] = None
    scope: GdsParseSampleScope = GdsParseSampleScope.AGENCY
    booking_import_draft_id: Optional[str] = None
    parser_run_id: Optional[str] = None
    provider_family: GdsProviderFamily = GdsProviderFamily.UNKNOWN
    input_format: GdsInputFormat = GdsInputFormat.UNKNOWN
    sample_title: Optional[str] = None
    mode: GdsParseSampleMode = GdsParseSampleMode.PNR
    raw_text: str
    parsed_json: Dict[str, Any] = Field(default_factory=dict)
    expected_payload_json: Dict[str, Any] = Field(default_factory=dict)
    corrected_payload_json: Optional[Dict[str, Any]] = None
    sample_status: GdsParseSampleStatus = GdsParseSampleStatus.DRAFT
    difficulty: GdsParseSampleDifficulty = GdsParseSampleDifficulty.MEDIUM
    tags: List[str] = Field(default_factory=list)
    redaction_status: GdsParseSampleRedactionStatus = GdsParseSampleRedactionStatus.NOT_REQUIRED
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    source: GdsParseSampleSource = GdsParseSampleSource.MANUAL
    notes: Optional[str] = None


class GdsParserProfile(BaseDocument):
    profile_key: str
    title: str
    description: Optional[str] = None
    provider_family: GdsProviderFamily = GdsProviderFamily.GENERIC_GDS
    input_format: GdsInputFormat = GdsInputFormat.CRYPTIC_PNR
    active: bool = True
    default_for_provider_family: bool = False
    parser_strategy: GdsParserStrategy = GdsParserStrategy.HYBRID_RULES
    confidence_threshold_import: float = 0.80
    confidence_threshold_warning: float = 0.60
    created_by_user_id: Optional[str] = None


class GdsParserVersion(BaseDocument):
    parser_profile_id: str
    version_label: str
    status: GdsParserVersionStatus = GdsParserVersionStatus.DRAFT
    rules_json: Dict[str, Any] = Field(default_factory=dict)
    extraction_schema_json: Dict[str, Any] = Field(default_factory=dict)
    known_limitations_json: List[Dict[str, Any]] = Field(default_factory=list)
    change_notes: Optional[str] = None
    created_by_user_id: Optional[str] = None
    activated_at: Optional[datetime] = None


class GdsParserRun(BaseDocument):
    agency_id: str
    booking_import_draft_id: Optional[str] = None
    parser_profile_id: Optional[str] = None
    parser_version_id: Optional[str] = None
    input_hash: str
    input_excerpt: str
    provider_family_detected: GdsProviderFamily = GdsProviderFamily.UNKNOWN
    input_format_detected: GdsInputFormat = GdsInputFormat.UNKNOWN
    parse_status: GdsParserRunStatus = GdsParserRunStatus.MANUAL_REVIEW_REQUIRED
    overall_confidence: float = 0.0
    extracted_passenger_count: int = 0
    extracted_segment_count: int = 0
    extracted_ticket_count: int = 0
    extracted_emd_count: int = 0
    extracted_ssr_count: int = 0
    extracted_osi_count: int = 0
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    errors_json: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_payload_json: Dict[str, Any] = Field(default_factory=dict)
    normalized_preview_json: Dict[str, Any] = Field(default_factory=dict)
    created_by_user_id: Optional[str] = None


class GdsParsedEntity(BaseDocument):
    agency_id: str
    parser_run_id: str
    booking_import_draft_id: Optional[str] = None
    entity_type: GdsParsedEntityType
    entity_key: Optional[str] = None
    source_text: str
    normalized_json: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    status: GdsParsedEntityStatus = GdsParsedEntityStatus.EXTRACTED
    correction_json: Optional[Dict[str, Any]] = None
    corrected_by_user_id: Optional[str] = None
    corrected_at: Optional[datetime] = None


class GdsParseCorrection(BaseDocument):
    agency_id: str
    parser_run_id: str
    parsed_entity_id: Optional[str] = None
    booking_import_draft_id: Optional[str] = None
    correction_type: GdsParseCorrectionType
    entity_type: GdsParsedEntityType = GdsParsedEntityType.UNKNOWN
    before_json: Dict[str, Any] = Field(default_factory=dict)
    after_json: Dict[str, Any] = Field(default_factory=dict)
    correction_reason: Optional[str] = None
    created_by_user_id: Optional[str] = None


class GdsParserEvaluationRun(BaseDocument):
    parser_profile_id: str
    parser_version_id: str
    sample_ids: List[str] = Field(default_factory=list)
    evaluation_status: GdsParserEvaluationStatus = GdsParserEvaluationStatus.RUNNING
    sample_count: int = 0
    exact_match_count: int = 0
    partial_match_count: int = 0
    failed_count: int = 0
    average_confidence: float = 0.0
    passenger_accuracy: Optional[float] = None
    segment_accuracy: Optional[float] = None
    ticket_accuracy: Optional[float] = None
    emd_accuracy: Optional[float] = None
    ssr_osi_accuracy: Optional[float] = None
    pricing_accuracy: Optional[float] = None
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    results_json: List[Dict[str, Any]] = Field(default_factory=list)
    created_by_user_id: Optional[str] = None


class GdsParserVersionCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    version_label: str
    rules_json: Dict[str, Any] = Field(default_factory=dict)
    extraction_schema_json: Dict[str, Any] = Field(default_factory=dict)
    known_limitations_json: List[Dict[str, Any]] = Field(default_factory=list)
    change_notes: Optional[str] = None


class GdsParserParseTextRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    raw_text: str
    parser_profile_id: Optional[str] = None
    parser_version_id: Optional[str] = None
    booking_import_draft_id: Optional[str] = None


class GdsParserCorrectionCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    parser_run_id: str
    parsed_entity_id: Optional[str] = None
    booking_import_draft_id: Optional[str] = None
    correction_type: GdsParseCorrectionType
    entity_type: GdsParsedEntityType = GdsParsedEntityType.UNKNOWN
    before_json: Dict[str, Any] = Field(default_factory=dict)
    after_json: Dict[str, Any] = Field(default_factory=dict)
    correction_reason: Optional[str] = None


class GdsParseTrainingSampleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    scope: GdsParseSampleScope = GdsParseSampleScope.AGENCY
    sample_title: Optional[str] = None
    expected_payload_json: Dict[str, Any] = Field(default_factory=dict)
    corrected_payload_json: Optional[Dict[str, Any]] = None
    difficulty: GdsParseSampleDifficulty = GdsParseSampleDifficulty.MEDIUM
    tags: List[str] = Field(default_factory=list)
    redaction_status: GdsParseSampleRedactionStatus = GdsParseSampleRedactionStatus.NOT_REQUIRED


class GdsParseTrainingSampleReview(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    sample_status: GdsParseSampleStatus
    corrected_payload_json: Optional[Dict[str, Any]] = None
    review_notes: Optional[str] = None
    redaction_status: Optional[GdsParseSampleRedactionStatus] = None


class GdsParserEvaluationCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    parser_profile_id: str
    parser_version_id: str
    sample_ids: List[str] = Field(default_factory=list)


class AirlinePolicyScope(str, Enum):
    PLATFORM = "platform"
    AGENCY = "agency"


class AirlinePolicySourceType(str, Enum):
    PASTED_TEXT = "pasted_text"
    UPLOADED_TEXT = "uploaded_text"
    AIRLINE_WEBSITE_COPY = "airline_website_copy"
    TRADE_SUPPORT_COPY = "trade_support_copy"
    GDS_HELPDESK_COPY = "gds_helpdesk_copy"
    EMAIL_POLICY_COPY = "email_policy_copy"
    MANUAL_NOTE = "manual_note"
    OTHER = "other"


class AirlinePolicyRedactionStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    REDACTED = "redacted"


class AirlinePolicyIngestionStatus(str, Enum):
    DRAFT = "draft"
    EXTRACTED = "extracted"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class AirlinePolicySectionCategory(str, Enum):
    GENERAL = "general"
    APPLICABILITY = "applicability"
    EMBARGOES = "embargoes"
    HOW_TO_BOOK = "how_to_book"
    MANDATORY_OPTIONAL = "mandatory_optional"
    PRICING = "pricing"
    SERVICES = "services"
    AIRPORT_HANDLING = "airport_handling"
    DOCUMENTS = "documents"
    COUNTRY_RESTRICTIONS = "country_restrictions"
    CHANGES_REFUNDS = "changes_refunds"
    DISRUPTION = "disruption"
    DISTRIBUTION = "distribution"
    GDS_NDC = "gds_ndc"
    SSR_OSI = "ssr_osi"
    EMD_PAYMENT = "emd_payment"
    INTERLINE = "interline"
    EXCEPTIONS = "exceptions"
    OTHER = "other"


class AirlinePolicyExtractionStatus(str, Enum):
    EXTRACTED = "extracted"
    PARTIAL = "partial"
    FAILED = "failed"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class AirlinePolicyRuleType(str, Enum):
    APPLICABILITY = "applicability"
    MANDATORY_OPTIONAL = "mandatory_optional"
    ELIGIBILITY = "eligibility"
    BOOKING_DEADLINE = "booking_deadline"
    ROUTE_RESTRICTION = "route_restriction"
    AIRPORT_RESTRICTION = "airport_restriction"
    CONNECTION_RESTRICTION = "connection_restriction"
    CABIN_RESTRICTION = "cabin_restriction"
    AIRCRAFT_RESTRICTION = "aircraft_restriction"
    PASSENGER_AGE = "passenger_age"
    PASSENGER_TYPE = "passenger_type"
    REQUIRED_DOCUMENT = "required_document"
    OPERATIONAL_REQUIREMENT = "operational_requirement"
    REFUND_CHANGE = "refund_change"
    DISRUPTION = "disruption"
    OTHER = "other"


class AirlinePolicyCandidateStatus(str, Enum):
    EXTRACTED = "extracted"
    ACCEPTED = "accepted"
    CORRECTED = "corrected"
    REJECTED = "rejected"
    PROMOTED = "promoted"


class AirlinePolicyMandatoryOptional(str, Enum):
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    BOTH = "both"
    UNKNOWN = "unknown"


class AirlinePolicyPriceType(str, Enum):
    SERVICE_FEE = "service_fee"
    ANCILLARY_FEE = "ancillary_fee"
    FARE_INCLUDED = "fare_included"
    EMD_FEE = "emd_fee"
    AIRPORT_COLLECTED = "airport_collected"
    AIRLINE_DIRECT_COLLECTED = "airline_direct_collected"
    UNKNOWN = "unknown"


class AirlinePolicyPriceBasis(str, Enum):
    PER_PASSENGER = "per_passenger"
    PER_DIRECTION = "per_direction"
    PER_SEGMENT = "per_segment"
    PER_JOURNEY = "per_journey"
    PER_BOOKING = "per_booking"
    ROUNDTRIP_DOUBLED = "roundtrip_doubled"
    UNKNOWN = "unknown"


class AirlinePolicyDirectConnecting(str, Enum):
    DIRECT = "direct"
    CONNECTING = "connecting"
    BOTH = "both"
    UNKNOWN = "unknown"


class AirlinePolicyCommunicationType(str, Enum):
    SSR = "ssr"
    OSI = "osi"
    OTHS = "oths"
    GDS_ENTRY = "gds_entry"
    NDC = "ndc"
    MANUAL_AIRLINE_CONTACT = "manual_airline_contact"
    AIRLINE_PORTAL = "airline_portal"
    OTHER = "other"


class AirlinePolicyGdsSystem(str, Enum):
    AMADEUS = "amadeus"
    SABRE = "sabre"
    TRAVELPORT = "travelport"
    GENERIC = "generic"
    UNKNOWN = "unknown"


class AirlinePolicyEmdType(str, Enum):
    EMD_A = "emd_a"
    EMD_S = "emd_s"
    EITHER = "either"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class AirlinePolicyExceptionType(str, Enum):
    EMBARGO = "embargo"
    ROUTE_BLOCK = "route_block"
    AIRPORT_BLOCK = "airport_block"
    CONNECTION_BLOCK = "connection_block"
    OVERNIGHT_FORBIDDEN = "overnight_forbidden"
    AIRPORT_CHANGE_FORBIDDEN = "airport_change_forbidden"
    TRAIN_BUS_FORBIDDEN = "train_bus_forbidden"
    PARTNER_AIRLINE_LIMITATION = "partner_airline_limitation"
    COUNTRY_DOCUMENT_RULE = "country_document_rule"
    CABIN_LIMITATION = "cabin_limitation"
    AIRCRAFT_LIMITATION = "aircraft_limitation"
    WEATHER_TEMPERATURE = "weather_temperature"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    OTHER = "other"


class AirlinePolicyReviewTargetType(str, Enum):
    RULE = "rule"
    PRICE = "price"
    COMMUNICATION_RULE = "communication_rule"
    EMD_RULE = "emd_rule"
    EXCEPTION = "exception"
    SECTION = "section"
    SOURCE = "source"


class AirlinePolicyCorrectionType(str, Enum):
    ACCEPT = "accept"
    CORRECT = "correct"
    REJECT = "reject"
    PROMOTE = "promote"
    ARCHIVE = "archive"
    ADD_MISSING = "add_missing"


class AirlinePolicyKnowledgeType(str, Enum):
    APPLICABILITY_RULE = "applicability_rule"
    PRICING_RULE = "pricing_rule"
    COMMUNICATION_RULE = "communication_rule"
    EMD_RULE = "emd_rule"
    EXCEPTION_RULE = "exception_rule"
    DOCUMENT_REQUIREMENT = "document_requirement"
    OPERATIONAL_REQUIREMENT = "operational_requirement"
    DISTRIBUTION_RULE = "distribution_rule"
    LIFECYCLE_RULE = "lifecycle_rule"


class AirlinePolicyApprovedKnowledgeStatus(str, Enum):
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class AirlinePolicySource(BaseDocument):
    scope: AirlinePolicyScope = AirlinePolicyScope.PLATFORM
    agency_id: Optional[str] = None
    airline_id: Optional[str] = None
    airline_iata_code: Optional[str] = None
    airline_name_snapshot: Optional[str] = None
    service_domain: Optional[str] = None
    service_family: Optional[str] = None
    source_type: AirlinePolicySourceType = AirlinePolicySourceType.PASTED_TEXT
    source_title: str
    source_url: Optional[str] = None
    source_date: Optional[date] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    raw_text: str
    raw_text_hash: str
    language: str = "en"
    redaction_status: AirlinePolicyRedactionStatus = AirlinePolicyRedactionStatus.NOT_REQUIRED
    ingestion_status: AirlinePolicyIngestionStatus = AirlinePolicyIngestionStatus.DRAFT
    confidence_overall: Optional[float] = None
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    created_by_user_id: Optional[str] = None


class AirlinePolicySection(BaseDocument):
    policy_source_id: str
    airline_id: Optional[str] = None
    section_key: str
    section_title: str
    section_order: int = 0
    section_text: str
    detected_category: AirlinePolicySectionCategory = AirlinePolicySectionCategory.OTHER
    confidence: float = 0.0
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)


class AirlinePolicyExtractionRun(BaseDocument):
    policy_source_id: str
    airline_id: Optional[str] = None
    extractor_version: str = "phase_36_7_deterministic_v1"
    extraction_status: AirlinePolicyExtractionStatus = AirlinePolicyExtractionStatus.MANUAL_REVIEW_REQUIRED
    overall_confidence: float = 0.0
    extracted_rule_count: int = 0
    extracted_price_count: int = 0
    extracted_exception_count: int = 0
    extracted_ssr_osi_count: int = 0
    extracted_emd_rule_count: int = 0
    extracted_distribution_count: int = 0
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    errors_json: List[Dict[str, Any]] = Field(default_factory=list)
    extraction_summary_json: Dict[str, Any] = Field(default_factory=dict)
    created_by_user_id: Optional[str] = None


class AirlinePolicyExtractedRule(BaseDocument):
    extraction_run_id: str
    policy_source_id: str
    section_id: Optional[str] = None
    airline_id: Optional[str] = None
    service_domain: Optional[str] = None
    service_family: Optional[str] = None
    service_variant: Optional[str] = None
    rule_type: AirlinePolicyRuleType = AirlinePolicyRuleType.OTHER
    normalized_condition_json: Dict[str, Any] = Field(default_factory=dict)
    normalized_action_json: Dict[str, Any] = Field(default_factory=dict)
    source_excerpt: str
    confidence: float = 0.0
    status: AirlinePolicyCandidateStatus = AirlinePolicyCandidateStatus.EXTRACTED
    correction_json: Optional[Dict[str, Any]] = None
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class AirlinePolicyExtractedPrice(BaseDocument):
    extraction_run_id: str
    policy_source_id: str
    section_id: Optional[str] = None
    airline_id: Optional[str] = None
    service_domain: Optional[str] = None
    service_family: Optional[str] = None
    service_variant: Optional[str] = None
    mandatory_optional: AirlinePolicyMandatoryOptional = AirlinePolicyMandatoryOptional.UNKNOWN
    price_type: AirlinePolicyPriceType = AirlinePolicyPriceType.UNKNOWN
    currency: Optional[str] = None
    amount: Optional[float] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    price_basis: AirlinePolicyPriceBasis = AirlinePolicyPriceBasis.UNKNOWN
    route_band: Optional[str] = None
    direct_connecting: AirlinePolicyDirectConnecting = AirlinePolicyDirectConnecting.UNKNOWN
    origin_scope_json: Dict[str, Any] = Field(default_factory=dict)
    destination_scope_json: Dict[str, Any] = Field(default_factory=dict)
    cabin_scope_json: Dict[str, Any] = Field(default_factory=dict)
    age_scope_json: Dict[str, Any] = Field(default_factory=dict)
    fare_basis_or_designator: Optional[str] = None
    emd_required: Optional[bool] = None
    source_excerpt: str
    confidence: float = 0.0
    status: AirlinePolicyCandidateStatus = AirlinePolicyCandidateStatus.EXTRACTED
    correction_json: Optional[Dict[str, Any]] = None
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class AirlinePolicyExtractedCommunicationRule(BaseDocument):
    extraction_run_id: str
    policy_source_id: str
    section_id: Optional[str] = None
    airline_id: Optional[str] = None
    service_domain: Optional[str] = None
    service_family: Optional[str] = None
    service_variant: Optional[str] = None
    communication_type: AirlinePolicyCommunicationType = AirlinePolicyCommunicationType.OTHER
    ssr_code: Optional[str] = None
    osi_keyword: Optional[str] = None
    gds_system: Optional[AirlinePolicyGdsSystem] = None
    input_template: Optional[str] = None
    example_text: Optional[str] = None
    passenger_association_required: Optional[bool] = None
    segment_association_required: Optional[bool] = None
    airline_confirmation_required: Optional[bool] = None
    confirmation_statuses_json: List[Dict[str, Any]] = Field(default_factory=list)
    rejection_patterns_json: List[Dict[str, Any]] = Field(default_factory=list)
    ndc_supported: Optional[bool] = None
    source_excerpt: str
    confidence: float = 0.0
    status: AirlinePolicyCandidateStatus = AirlinePolicyCandidateStatus.EXTRACTED
    correction_json: Optional[Dict[str, Any]] = None
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class AirlinePolicyExtractedEmdRule(BaseDocument):
    extraction_run_id: str
    policy_source_id: str
    section_id: Optional[str] = None
    airline_id: Optional[str] = None
    service_domain: Optional[str] = None
    service_family: Optional[str] = None
    service_variant: Optional[str] = None
    emd_required: Optional[bool] = None
    fee_included_in_fare: Optional[bool] = None
    emd_type: AirlinePolicyEmdType = AirlinePolicyEmdType.UNKNOWN
    rfic: Optional[str] = None
    rfisc: Optional[str] = None
    reason_for_issuance_description: Optional[str] = None
    service_subcode: Optional[str] = None
    asvc_available: Optional[bool] = None
    icw_ticket_required: Optional[bool] = None
    icw_coupon_required: Optional[bool] = None
    standalone_allowed: Optional[bool] = None
    associated_ssr_code: Optional[str] = None
    validating_carrier_rule: Optional[str] = None
    plating_carrier_rule: Optional[str] = None
    interline_allowed: Optional[bool] = None
    interline_restricted: Optional[bool] = None
    refundable: Optional[bool] = None
    exchangeable: Optional[bool] = None
    voidable: Optional[bool] = None
    refund_conditions_json: Dict[str, Any] = Field(default_factory=dict)
    change_conditions_json: Dict[str, Any] = Field(default_factory=dict)
    issuance_channel_json: Dict[str, Any] = Field(default_factory=dict)
    gds_command_examples_json: List[Dict[str, Any]] = Field(default_factory=list)
    source_excerpt: str
    confidence: float = 0.0
    status: AirlinePolicyCandidateStatus = AirlinePolicyCandidateStatus.EXTRACTED
    correction_json: Optional[Dict[str, Any]] = None
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class AirlinePolicyExtractedException(BaseDocument):
    extraction_run_id: str
    policy_source_id: str
    section_id: Optional[str] = None
    airline_id: Optional[str] = None
    service_domain: Optional[str] = None
    service_family: Optional[str] = None
    exception_type: AirlinePolicyExceptionType = AirlinePolicyExceptionType.OTHER
    normalized_condition_json: Dict[str, Any] = Field(default_factory=dict)
    normalized_action_json: Dict[str, Any] = Field(default_factory=dict)
    source_excerpt: str
    confidence: float = 0.0
    status: AirlinePolicyCandidateStatus = AirlinePolicyCandidateStatus.EXTRACTED
    correction_json: Optional[Dict[str, Any]] = None
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class AirlinePolicyReviewCorrection(BaseDocument):
    policy_source_id: str
    extraction_run_id: Optional[str] = None
    target_type: AirlinePolicyReviewTargetType
    target_id: Optional[str] = None
    correction_type: AirlinePolicyCorrectionType
    before_json: Dict[str, Any] = Field(default_factory=dict)
    after_json: Dict[str, Any] = Field(default_factory=dict)
    correction_reason: Optional[str] = None
    created_by_user_id: Optional[str] = None


class AirlinePolicyApprovedKnowledgeRecord(BaseDocument):
    policy_source_id: str
    extraction_run_id: Optional[str] = None
    airline_id: Optional[str] = None
    service_domain: str
    service_family: str
    service_variant: Optional[str] = None
    knowledge_type: AirlinePolicyKnowledgeType
    normalized_payload_json: Dict[str, Any] = Field(default_factory=dict)
    source_excerpt: str
    source_section_id: Optional[str] = None
    confidence: float = 0.0
    status: AirlinePolicyApprovedKnowledgeStatus = AirlinePolicyApprovedKnowledgeStatus.APPROVED
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None


class AirlinePolicySourceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_id: Optional[str] = None
    airline_iata_code: Optional[str] = None
    airline_name_snapshot: Optional[str] = None
    service_domain: Optional[str] = None
    service_family: Optional[str] = None
    source_type: AirlinePolicySourceType = AirlinePolicySourceType.PASTED_TEXT
    source_title: str
    source_url: Optional[str] = None
    source_date: Optional[date] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    raw_text: str
    language: str = "en"
    notes: Optional[str] = None


class AirlinePolicyExtractionRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    extractor_version: Optional[str] = None
    service_domain: Optional[str] = None
    service_family: Optional[str] = None


class AirlinePolicyReviewCorrectionCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    policy_source_id: str
    extraction_run_id: Optional[str] = None
    target_type: AirlinePolicyReviewTargetType
    target_id: Optional[str] = None
    correction_type: AirlinePolicyCorrectionType
    before_json: Dict[str, Any] = Field(default_factory=dict)
    after_json: Dict[str, Any] = Field(default_factory=dict)
    correction_reason: Optional[str] = None


class AirlinePolicyPromoteCandidateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    policy_source_id: str
    extraction_run_id: Optional[str] = None
    target_type: AirlinePolicyReviewTargetType
    target_id: str
    knowledge_type: Optional[AirlinePolicyKnowledgeType] = None


class ServiceTaxonomyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ServiceTaxonomyGovernanceStatus(str, Enum):
    SEED = "seed"
    PLATFORM_APPROVED = "platform_approved"
    PLATFORM_REVIEW = "platform_review"
    AGENCY_SUGGESTED = "agency_suggested"
    DEPRECATED = "deprecated"


class AirlineServiceAliasType(str, Enum):
    POLICY_TERM = "policy_term"
    COMMERCIAL_NAME = "commercial_name"
    SSR_CODE = "ssr_code"
    GDS_CODE = "gds_code"
    NDC_LABEL = "ndc_label"
    INTERNAL_LABEL = "internal_label"
    OTHER = "other"


class ServiceTaxonomyReviewStatus(str, Enum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class ServiceApplicabilityValueType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    ENUM = "enum"
    REGION = "region"
    AIRPORT = "airport"
    COUNTRY = "country"
    CARRIER = "carrier"
    DURATION = "duration"
    MONEY = "money"
    JSON = "json"


class ServicePolicyOutcomeSeverity(str, Enum):
    INFO = "info"
    ADVISORY = "advisory"
    WARNING = "warning"
    BLOCKER = "blocker"


class ServiceTaxonomyMatchType(str, Enum):
    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"
    TOKEN = "token"
    SSR_CODE = "ssr_code"


class ServiceTaxonomyRuleScope(str, Enum):
    GLOBAL = "global"
    AGENCY = "agency"


class PolicyCandidateTaxonomyCandidateType(str, Enum):
    EXTRACTED_RULE = "extracted_rule"
    EXTRACTED_PRICE = "extracted_price"
    EXTRACTED_COMMUNICATION = "extracted_communication"
    EXTRACTED_EMD_RULE = "extracted_emd_rule"
    EXTRACTED_EXCEPTION = "extracted_exception"
    APPROVED_KNOWLEDGE = "approved_knowledge"


class ServiceTaxonomyCorrectionScope(str, Enum):
    AGENCY_LOCAL = "agency_local"
    PLATFORM_GLOBAL_REVIEW = "platform_global_review"


class ServiceTaxonomyPromotionStatus(str, Enum):
    NOT_REQUESTED = "not_requested"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class CanonicalServiceDomain(BaseDocument):
    code: str
    name: str
    description: Optional[str] = None
    sort_order: int = 100
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE
    is_global: bool = True
    governance_status: ServiceTaxonomyGovernanceStatus = ServiceTaxonomyGovernanceStatus.SEED
    created_by_user_id: Optional[str] = None
    updated_by_user_id: Optional[str] = None


class CanonicalServiceFamily(BaseDocument):
    domain_id: Optional[str] = None
    domain_code: str
    code: str
    name: str
    description: Optional[str] = None
    default_ssr_codes: List[str] = Field(default_factory=list)
    related_service_catalogue_keys: List[str] = Field(default_factory=list)
    sort_order: int = 100
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE
    is_global: bool = True
    governance_status: ServiceTaxonomyGovernanceStatus = ServiceTaxonomyGovernanceStatus.SEED


class CanonicalServiceVariant(BaseDocument):
    domain_code: str
    family_code: str
    code: str
    name: str
    description: Optional[str] = None
    standard_ssr_code: Optional[str] = None
    known_airline_terms: List[str] = Field(default_factory=list)
    sort_order: int = 100
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE
    is_global: bool = True
    governance_status: ServiceTaxonomyGovernanceStatus = ServiceTaxonomyGovernanceStatus.SEED


class AirlineServiceAlias(BaseDocument):
    airline_code: Optional[str] = None
    alias_text: str
    alias_type: AirlineServiceAliasType = AirlineServiceAliasType.POLICY_TERM
    normalized_alias_text: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    confidence_score: float = 0.75
    review_status: ServiceTaxonomyReviewStatus = ServiceTaxonomyReviewStatus.SUGGESTED
    source_policy_id: Optional[str] = None
    source_extraction_run_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    agency_id: Optional[str] = None
    is_global: bool = True
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE


class ServiceApplicabilityDimension(BaseDocument):
    code: str
    name: str
    value_type: ServiceApplicabilityValueType = ServiceApplicabilityValueType.TEXT
    description: Optional[str] = None
    sort_order: int = 100
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE


class ServicePolicyOutcomeType(BaseDocument):
    code: str
    name: str
    description: Optional[str] = None
    severity: ServicePolicyOutcomeSeverity = ServicePolicyOutcomeSeverity.INFO
    sort_order: int = 100
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE


class ServiceTaxonomyMappingRule(BaseDocument):
    rule_name: str
    airline_code: Optional[str] = None
    match_type: ServiceTaxonomyMatchType = ServiceTaxonomyMatchType.EXACT
    match_value: str
    normalized_match_value: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    alias_type: AirlineServiceAliasType = AirlineServiceAliasType.POLICY_TERM
    confidence_score: float = 0.75
    priority: int = 100
    scope: ServiceTaxonomyRuleScope = ServiceTaxonomyRuleScope.GLOBAL
    agency_id: Optional[str] = None
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE
    created_by_user_id: Optional[str] = None
    notes: Optional[str] = None


class PolicyCandidateTaxonomyLink(BaseDocument):
    agency_id: Optional[str] = None
    policy_source_id: Optional[str] = None
    extraction_run_id: Optional[str] = None
    candidate_type: PolicyCandidateTaxonomyCandidateType
    candidate_id: str
    airline_code: Optional[str] = None
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    mapping_rule_id: Optional[str] = None
    alias_id: Optional[str] = None
    confidence_score: float = 0.0
    review_status: ServiceTaxonomyReviewStatus = ServiceTaxonomyReviewStatus.SUGGESTED
    reviewer_notes: Optional[str] = None
    evidence_text: Optional[str] = None


class ServiceTaxonomyReviewCorrection(BaseDocument):
    agency_id: Optional[str] = None
    policy_candidate_taxonomy_link_id: Optional[str] = None
    candidate_type: PolicyCandidateTaxonomyCandidateType
    candidate_id: str
    previous_domain_code: Optional[str] = None
    previous_family_code: Optional[str] = None
    previous_variant_code: Optional[str] = None
    corrected_domain_code: str
    corrected_family_code: str
    corrected_variant_code: Optional[str] = None
    correction_reason: Optional[str] = None
    reviewer_user_id: Optional[str] = None
    correction_scope: ServiceTaxonomyCorrectionScope = ServiceTaxonomyCorrectionScope.PLATFORM_GLOBAL_REVIEW
    promotion_requested: bool = False
    promotion_status: ServiceTaxonomyPromotionStatus = ServiceTaxonomyPromotionStatus.NOT_REQUESTED


class CanonicalServiceDomainCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    code: str
    name: str
    description: Optional[str] = None
    sort_order: int = 100
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE
    is_global: bool = True
    governance_status: ServiceTaxonomyGovernanceStatus = ServiceTaxonomyGovernanceStatus.PLATFORM_APPROVED


class CanonicalServiceDomainUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[ServiceTaxonomyStatus] = None
    is_global: Optional[bool] = None
    governance_status: Optional[ServiceTaxonomyGovernanceStatus] = None


class CanonicalServiceFamilyCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    domain_id: Optional[str] = None
    domain_code: str
    code: str
    name: str
    description: Optional[str] = None
    default_ssr_codes: List[str] = Field(default_factory=list)
    related_service_catalogue_keys: List[str] = Field(default_factory=list)
    sort_order: int = 100
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE
    is_global: bool = True
    governance_status: ServiceTaxonomyGovernanceStatus = ServiceTaxonomyGovernanceStatus.PLATFORM_APPROVED


class CanonicalServiceFamilyUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    domain_id: Optional[str] = None
    domain_code: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    default_ssr_codes: Optional[List[str]] = None
    related_service_catalogue_keys: Optional[List[str]] = None
    sort_order: Optional[int] = None
    status: Optional[ServiceTaxonomyStatus] = None
    is_global: Optional[bool] = None
    governance_status: Optional[ServiceTaxonomyGovernanceStatus] = None


class CanonicalServiceVariantCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    domain_code: str
    family_code: str
    code: str
    name: str
    description: Optional[str] = None
    standard_ssr_code: Optional[str] = None
    known_airline_terms: List[str] = Field(default_factory=list)
    sort_order: int = 100
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE
    is_global: bool = True
    governance_status: ServiceTaxonomyGovernanceStatus = ServiceTaxonomyGovernanceStatus.PLATFORM_APPROVED


class CanonicalServiceVariantUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    standard_ssr_code: Optional[str] = None
    known_airline_terms: Optional[List[str]] = None
    sort_order: Optional[int] = None
    status: Optional[ServiceTaxonomyStatus] = None
    is_global: Optional[bool] = None
    governance_status: Optional[ServiceTaxonomyGovernanceStatus] = None


class AirlineServiceAliasCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    alias_text: str
    alias_type: AirlineServiceAliasType = AirlineServiceAliasType.POLICY_TERM
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    confidence_score: float = 0.75
    review_status: ServiceTaxonomyReviewStatus = ServiceTaxonomyReviewStatus.CONFIRMED
    source_policy_id: Optional[str] = None
    source_extraction_run_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    agency_id: Optional[str] = None
    is_global: bool = True
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE


class AirlineServiceAliasUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    alias_text: Optional[str] = None
    alias_type: Optional[AirlineServiceAliasType] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    confidence_score: Optional[float] = None
    review_status: Optional[ServiceTaxonomyReviewStatus] = None
    status: Optional[ServiceTaxonomyStatus] = None


class ServiceTaxonomyMappingRuleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rule_name: str
    airline_code: Optional[str] = None
    match_type: ServiceTaxonomyMatchType = ServiceTaxonomyMatchType.EXACT
    match_value: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    alias_type: AirlineServiceAliasType = AirlineServiceAliasType.POLICY_TERM
    confidence_score: float = 0.75
    priority: int = 100
    scope: ServiceTaxonomyRuleScope = ServiceTaxonomyRuleScope.GLOBAL
    agency_id: Optional[str] = None
    status: ServiceTaxonomyStatus = ServiceTaxonomyStatus.ACTIVE
    notes: Optional[str] = None


class ServiceTaxonomyMappingRuleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rule_name: Optional[str] = None
    airline_code: Optional[str] = None
    match_type: Optional[ServiceTaxonomyMatchType] = None
    match_value: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    alias_type: Optional[AirlineServiceAliasType] = None
    confidence_score: Optional[float] = None
    priority: Optional[int] = None
    scope: Optional[ServiceTaxonomyRuleScope] = None
    agency_id: Optional[str] = None
    status: Optional[ServiceTaxonomyStatus] = None
    notes: Optional[str] = None


class ServiceTaxonomyMapCandidateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    text: str
    airline_code: Optional[str] = None
    candidate_type: Optional[PolicyCandidateTaxonomyCandidateType] = None
    agency_id: Optional[str] = None


class PolicyCandidateTaxonomyLinkCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    policy_source_id: Optional[str] = None
    extraction_run_id: Optional[str] = None
    candidate_type: PolicyCandidateTaxonomyCandidateType
    candidate_id: str
    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    mapping_rule_id: Optional[str] = None
    alias_id: Optional[str] = None
    confidence_score: Optional[float] = None
    review_status: ServiceTaxonomyReviewStatus = ServiceTaxonomyReviewStatus.SUGGESTED
    reviewer_notes: Optional[str] = None
    evidence_text: Optional[str] = None


class PolicyCandidateTaxonomyLinkUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    mapping_rule_id: Optional[str] = None
    alias_id: Optional[str] = None
    confidence_score: Optional[float] = None
    review_status: Optional[ServiceTaxonomyReviewStatus] = None
    reviewer_notes: Optional[str] = None
    evidence_text: Optional[str] = None


class ServiceTaxonomyReviewCorrectionCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    policy_candidate_taxonomy_link_id: Optional[str] = None
    candidate_type: PolicyCandidateTaxonomyCandidateType
    candidate_id: str
    previous_domain_code: Optional[str] = None
    previous_family_code: Optional[str] = None
    previous_variant_code: Optional[str] = None
    corrected_domain_code: str
    corrected_family_code: str
    corrected_variant_code: Optional[str] = None
    correction_reason: Optional[str] = None
    correction_scope: ServiceTaxonomyCorrectionScope = ServiceTaxonomyCorrectionScope.PLATFORM_GLOBAL_REVIEW
    promotion_requested: bool = False
    promotion_status: ServiceTaxonomyPromotionStatus = ServiceTaxonomyPromotionStatus.NOT_REQUESTED


class ServiceMechanicsStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ServiceMechanicsReviewStatus(str, Enum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class ServiceMechanicsCommunicationChannel(str, Enum):
    GDS = "gds"
    NDC = "ndc"
    AIRLINE_PORTAL = "airline_portal"
    EMAIL = "email"
    PHONE = "phone"
    MANUAL = "manual"
    OTHER = "other"


class ServiceMechanicsGdsSystem(str, Enum):
    AMADEUS = "amadeus"
    SABRE = "sabre"
    TRAVELPORT = "travelport"
    GALILEO = "galileo"
    WORLDSPAN = "worldspan"
    OTHER = "other"


class ServiceMechanicsRequestMethod(str, Enum):
    SSR = "ssr"
    OSI = "osi"
    OTHS = "oths"
    REMARK = "remark"
    MANUAL_CONTACT = "manual_contact"
    NDC_SERVICE = "ndc_service"
    OTHER = "other"


class SsrOsiTemplateType(str, Enum):
    SSR = "ssr"
    OSI = "osi"
    OTHS = "oths"
    REMARK = "remark"
    OTHER = "other"


class SsrOsiRequirementType(str, Enum):
    PASSENGER_DATA = "passenger_data"
    SEGMENT_DATA = "segment_data"
    DOCUMENT = "document"
    MEDICAL_FORM = "medical_form"
    AGE = "age"
    CONTACT = "contact"
    FREE_TEXT = "free_text"
    APPROVAL = "approval"
    DEADLINE = "deadline"
    OTHER = "other"


class ServiceMechanicsMatchType(str, Enum):
    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"
    TOKEN = "token"


class SsrRecognizedStatus(str, Enum):
    REQUESTED = "requested"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    WAITLISTED = "waitlisted"
    UNABLE = "unable"
    UNKNOWN = "unknown"


class AirlineRejectionReasonCategory(str, Enum):
    AGE_RESTRICTION = "age_restriction"
    ROUTE_RESTRICTION = "route_restriction"
    CONNECTION_RESTRICTION = "connection_restriction"
    EQUIPMENT_RESTRICTION = "equipment_restriction"
    CAPACITY = "capacity"
    DOCUMENTATION = "documentation"
    DEADLINE = "deadline"
    INTERLINE = "interline"
    CHANNEL_NOT_SUPPORTED = "channel_not_supported"
    PAYMENT_REQUIRED = "payment_required"
    UNKNOWN = "unknown"


class ServiceMechanicsSeverity(str, Enum):
    INFO = "info"
    ADVISORY = "advisory"
    WARNING = "warning"
    BLOCKER = "blocker"


class ServicePaymentTiming(str, Enum):
    BEFORE_TICKETING = "before_ticketing"
    AFTER_TICKETING = "after_ticketing"
    BEFORE_DEPARTURE = "before_departure"
    AT_AIRPORT = "at_airport"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class AirlineEmdType(str, Enum):
    EMD_A = "emd_a"
    EMD_S = "emd_s"
    UNKNOWN = "unknown"
    NOT_REQUIRED = "not_required"


class PolicyCandidateMechanicsType(str, Enum):
    COMMUNICATION_RULE = "communication_rule"
    SSR_OSI_TEMPLATE = "ssr_osi_template"
    REQUIREMENT = "requirement"
    STATUS_RECOGNITION = "status_recognition"
    REJECTION_PATTERN = "rejection_pattern"
    PAYMENT_RULE = "payment_rule"
    EMD_ISSUANCE_RULE = "emd_issuance_rule"
    RFIC_RFISC_MAPPING = "rfic_rfisc_mapping"
    INTERLINE_RULE = "interline_rule"
    LIFECYCLE_RULE = "lifecycle_rule"


class AirlineServiceCommunicationRule(BaseDocument):
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    canonical_service_label: Optional[str] = None
    communication_channel: ServiceMechanicsCommunicationChannel = ServiceMechanicsCommunicationChannel.GDS
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    request_method: ServiceMechanicsRequestMethod = ServiceMechanicsRequestMethod.SSR
    ssr_code: Optional[str] = None
    osi_required: bool = False
    oths_required: bool = False
    passenger_association_required: bool = True
    segment_association_required: bool = True
    airline_confirmation_required: bool = True
    manual_contact_required: bool = False
    ndc_supported: Optional[bool] = None
    gds_supported: Optional[bool] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE
    review_status: ServiceMechanicsReviewStatus = ServiceMechanicsReviewStatus.SUGGESTED
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    is_global: bool = True
    agency_id: Optional[str] = None
    notes: Optional[str] = None


class SsrOsiTemplate(BaseDocument):
    communication_rule_id: Optional[str] = None
    airline_code: Optional[str] = None
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    gds_system: ServiceMechanicsGdsSystem = ServiceMechanicsGdsSystem.AMADEUS
    template_type: SsrOsiTemplateType = SsrOsiTemplateType.SSR
    ssr_code: Optional[str] = None
    template_text: str
    example_text: Optional[str] = None
    required_fields: List[str] = Field(default_factory=list)
    passenger_placeholder_supported: bool = True
    segment_placeholder_supported: bool = True
    free_text_allowed: bool = True
    max_length: Optional[int] = None
    validation_notes: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE
    is_global: bool = True
    agency_id: Optional[str] = None


class SsrOsiRequirement(BaseDocument):
    communication_rule_id: Optional[str] = None
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    requirement_type: SsrOsiRequirementType = SsrOsiRequirementType.OTHER
    requirement_code: str
    requirement_label: str
    mandatory: bool = True
    applies_to_passenger: bool = True
    applies_to_segment: bool = False
    validation_hint: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class SsrStatusRecognitionRule(BaseDocument):
    airline_code: Optional[str] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    ssr_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    match_type: ServiceMechanicsMatchType = ServiceMechanicsMatchType.CONTAINS
    match_value: str
    normalized_match_value: str
    recognized_status: SsrRecognizedStatus = SsrRecognizedStatus.UNKNOWN
    confidence_score: float = 0.75
    priority: int = 100
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class AirlineRejectionPattern(BaseDocument):
    airline_code: Optional[str] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    rejection_code: Optional[str] = None
    pattern_text: str
    normalized_pattern_text: str
    reason_category: AirlineRejectionReasonCategory = AirlineRejectionReasonCategory.UNKNOWN
    severity: ServiceMechanicsSeverity = ServiceMechanicsSeverity.WARNING
    suggested_action: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class AirlineServicePaymentRule(BaseDocument):
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    payment_required: bool = False
    fee_included_in_fare: bool = False
    separate_emd_required: bool = False
    payment_timing: ServicePaymentTiming = ServicePaymentTiming.UNKNOWN
    validating_carrier_required: Optional[bool] = None
    plating_carrier_restriction: Optional[str] = None
    passenger_association_required: bool = True
    segment_association_required: bool = True
    interline_allowed: Optional[bool] = None
    refundable: Optional[bool] = None
    exchangeable: Optional[bool] = None
    voidable: Optional[bool] = None
    no_show_refundable: Optional[bool] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE
    review_status: ServiceMechanicsReviewStatus = ServiceMechanicsReviewStatus.SUGGESTED
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    is_global: bool = True
    agency_id: Optional[str] = None
    notes: Optional[str] = None


class AirlineEmdIssuanceRule(BaseDocument):
    payment_rule_id: Optional[str] = None
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    emd_type: AirlineEmdType = AirlineEmdType.UNKNOWN
    rfic: Optional[str] = None
    rfisc: Optional[str] = None
    service_subcode: Optional[str] = None
    reason_for_issuance_description: Optional[str] = None
    asvc_available: Optional[bool] = None
    icw_ticket_required: Optional[bool] = None
    icw_coupon_required: Optional[bool] = None
    standalone_allowed: Optional[bool] = None
    validating_carrier_rules: Optional[str] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    issuance_command_example: Optional[str] = None
    refund_command_example: Optional[str] = None
    exchange_command_example: Optional[str] = None
    void_command_example: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class AirlineRficRfiscMapping(BaseDocument):
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    rfic: str
    rfisc: str
    service_subcode: Optional[str] = None
    commercial_name: Optional[str] = None
    reason_for_issuance_description: Optional[str] = None
    emd_type: AirlineEmdType = AirlineEmdType.UNKNOWN
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None


class AirlineEmdInterlineRule(BaseDocument):
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    interline_allowed: bool = False
    plating_carrier_required: Optional[str] = None
    validating_carrier_must_equal_operating: Optional[bool] = None
    validating_carrier_must_equal_marketing: Optional[bool] = None
    partner_airline_restrictions: List[str] = Field(default_factory=list)
    restriction_text: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class AirlineEmdLifecycleRule(BaseDocument):
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    refundable: Optional[bool] = None
    exchangeable: Optional[bool] = None
    voidable: Optional[bool] = None
    reissuable: Optional[bool] = None
    refund_conditions: Optional[str] = None
    exchange_conditions: Optional[str] = None
    void_conditions: Optional[str] = None
    no_show_policy: Optional[str] = None
    residual_value_policy: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class PolicyCandidateMechanicsLink(BaseDocument):
    agency_id: Optional[str] = None
    policy_source_id: Optional[str] = None
    extraction_run_id: Optional[str] = None
    candidate_type: PolicyCandidateTaxonomyCandidateType
    candidate_id: Optional[str] = None
    taxonomy_link_id: Optional[str] = None
    mechanics_type: PolicyCandidateMechanicsType
    mechanics_record_id: str
    airline_code: Optional[str] = None
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    confidence_score: float = 0.0
    review_status: ServiceMechanicsReviewStatus = ServiceMechanicsReviewStatus.SUGGESTED
    evidence_text: Optional[str] = None
    reviewer_notes: Optional[str] = None


class AirlineServiceCommunicationRuleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    canonical_service_label: Optional[str] = None
    communication_channel: ServiceMechanicsCommunicationChannel = ServiceMechanicsCommunicationChannel.GDS
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    request_method: ServiceMechanicsRequestMethod = ServiceMechanicsRequestMethod.SSR
    ssr_code: Optional[str] = None
    osi_required: bool = False
    oths_required: bool = False
    passenger_association_required: bool = True
    segment_association_required: bool = True
    airline_confirmation_required: bool = True
    manual_contact_required: bool = False
    ndc_supported: Optional[bool] = None
    gds_supported: Optional[bool] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE
    review_status: ServiceMechanicsReviewStatus = ServiceMechanicsReviewStatus.SUGGESTED
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    is_global: bool = True
    agency_id: Optional[str] = None
    notes: Optional[str] = None


class AirlineServiceCommunicationRuleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    canonical_service_label: Optional[str] = None
    communication_channel: Optional[ServiceMechanicsCommunicationChannel] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    request_method: Optional[ServiceMechanicsRequestMethod] = None
    ssr_code: Optional[str] = None
    osi_required: Optional[bool] = None
    oths_required: Optional[bool] = None
    passenger_association_required: Optional[bool] = None
    segment_association_required: Optional[bool] = None
    airline_confirmation_required: Optional[bool] = None
    manual_contact_required: Optional[bool] = None
    ndc_supported: Optional[bool] = None
    gds_supported: Optional[bool] = None
    status: Optional[ServiceMechanicsStatus] = None
    review_status: Optional[ServiceMechanicsReviewStatus] = None
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    is_global: Optional[bool] = None
    agency_id: Optional[str] = None
    notes: Optional[str] = None


class SsrOsiTemplateCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    communication_rule_id: Optional[str] = None
    airline_code: Optional[str] = None
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    gds_system: ServiceMechanicsGdsSystem = ServiceMechanicsGdsSystem.AMADEUS
    template_type: SsrOsiTemplateType = SsrOsiTemplateType.SSR
    ssr_code: Optional[str] = None
    template_text: str
    example_text: Optional[str] = None
    required_fields: List[str] = Field(default_factory=list)
    passenger_placeholder_supported: bool = True
    segment_placeholder_supported: bool = True
    free_text_allowed: bool = True
    max_length: Optional[int] = None
    validation_notes: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE
    is_global: bool = True
    agency_id: Optional[str] = None


class SsrOsiTemplateUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    communication_rule_id: Optional[str] = None
    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    template_type: Optional[SsrOsiTemplateType] = None
    ssr_code: Optional[str] = None
    template_text: Optional[str] = None
    example_text: Optional[str] = None
    required_fields: Optional[List[str]] = None
    passenger_placeholder_supported: Optional[bool] = None
    segment_placeholder_supported: Optional[bool] = None
    free_text_allowed: Optional[bool] = None
    max_length: Optional[int] = None
    validation_notes: Optional[str] = None
    status: Optional[ServiceMechanicsStatus] = None
    is_global: Optional[bool] = None
    agency_id: Optional[str] = None


class SsrOsiRequirementCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    communication_rule_id: Optional[str] = None
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    requirement_type: SsrOsiRequirementType = SsrOsiRequirementType.OTHER
    requirement_code: str
    requirement_label: str
    mandatory: bool = True
    applies_to_passenger: bool = True
    applies_to_segment: bool = False
    validation_hint: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class SsrOsiRequirementUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    communication_rule_id: Optional[str] = None
    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    requirement_type: Optional[SsrOsiRequirementType] = None
    requirement_code: Optional[str] = None
    requirement_label: Optional[str] = None
    mandatory: Optional[bool] = None
    applies_to_passenger: Optional[bool] = None
    applies_to_segment: Optional[bool] = None
    validation_hint: Optional[str] = None
    status: Optional[ServiceMechanicsStatus] = None


class SsrStatusRecognitionRuleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    ssr_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    match_type: ServiceMechanicsMatchType = ServiceMechanicsMatchType.CONTAINS
    match_value: str
    recognized_status: SsrRecognizedStatus = SsrRecognizedStatus.UNKNOWN
    confidence_score: float = 0.75
    priority: int = 100
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class SsrStatusRecognitionRuleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    ssr_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    match_type: Optional[ServiceMechanicsMatchType] = None
    match_value: Optional[str] = None
    recognized_status: Optional[SsrRecognizedStatus] = None
    confidence_score: Optional[float] = None
    priority: Optional[int] = None
    status: Optional[ServiceMechanicsStatus] = None


class AirlineRejectionPatternCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    rejection_code: Optional[str] = None
    pattern_text: str
    reason_category: AirlineRejectionReasonCategory = AirlineRejectionReasonCategory.UNKNOWN
    severity: ServiceMechanicsSeverity = ServiceMechanicsSeverity.WARNING
    suggested_action: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class AirlineRejectionPatternUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    rejection_code: Optional[str] = None
    pattern_text: Optional[str] = None
    reason_category: Optional[AirlineRejectionReasonCategory] = None
    severity: Optional[ServiceMechanicsSeverity] = None
    suggested_action: Optional[str] = None
    status: Optional[ServiceMechanicsStatus] = None


class AirlineServicePaymentRuleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    payment_required: bool = False
    fee_included_in_fare: bool = False
    separate_emd_required: bool = False
    payment_timing: ServicePaymentTiming = ServicePaymentTiming.UNKNOWN
    validating_carrier_required: Optional[bool] = None
    plating_carrier_restriction: Optional[str] = None
    passenger_association_required: bool = True
    segment_association_required: bool = True
    interline_allowed: Optional[bool] = None
    refundable: Optional[bool] = None
    exchangeable: Optional[bool] = None
    voidable: Optional[bool] = None
    no_show_refundable: Optional[bool] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE
    review_status: ServiceMechanicsReviewStatus = ServiceMechanicsReviewStatus.SUGGESTED
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    is_global: bool = True
    agency_id: Optional[str] = None
    notes: Optional[str] = None


class AirlineServicePaymentRuleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    payment_required: Optional[bool] = None
    fee_included_in_fare: Optional[bool] = None
    separate_emd_required: Optional[bool] = None
    payment_timing: Optional[ServicePaymentTiming] = None
    validating_carrier_required: Optional[bool] = None
    plating_carrier_restriction: Optional[str] = None
    passenger_association_required: Optional[bool] = None
    segment_association_required: Optional[bool] = None
    interline_allowed: Optional[bool] = None
    refundable: Optional[bool] = None
    exchangeable: Optional[bool] = None
    voidable: Optional[bool] = None
    no_show_refundable: Optional[bool] = None
    status: Optional[ServiceMechanicsStatus] = None
    review_status: Optional[ServiceMechanicsReviewStatus] = None
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    is_global: Optional[bool] = None
    agency_id: Optional[str] = None
    notes: Optional[str] = None


class AirlineEmdIssuanceRuleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    payment_rule_id: Optional[str] = None
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    emd_type: AirlineEmdType = AirlineEmdType.UNKNOWN
    rfic: Optional[str] = None
    rfisc: Optional[str] = None
    service_subcode: Optional[str] = None
    reason_for_issuance_description: Optional[str] = None
    asvc_available: Optional[bool] = None
    icw_ticket_required: Optional[bool] = None
    icw_coupon_required: Optional[bool] = None
    standalone_allowed: Optional[bool] = None
    validating_carrier_rules: Optional[str] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    issuance_command_example: Optional[str] = None
    refund_command_example: Optional[str] = None
    exchange_command_example: Optional[str] = None
    void_command_example: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class AirlineEmdIssuanceRuleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    payment_rule_id: Optional[str] = None
    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    emd_type: Optional[AirlineEmdType] = None
    rfic: Optional[str] = None
    rfisc: Optional[str] = None
    service_subcode: Optional[str] = None
    reason_for_issuance_description: Optional[str] = None
    asvc_available: Optional[bool] = None
    icw_ticket_required: Optional[bool] = None
    icw_coupon_required: Optional[bool] = None
    standalone_allowed: Optional[bool] = None
    validating_carrier_rules: Optional[str] = None
    gds_system: Optional[ServiceMechanicsGdsSystem] = None
    issuance_command_example: Optional[str] = None
    refund_command_example: Optional[str] = None
    exchange_command_example: Optional[str] = None
    void_command_example: Optional[str] = None
    status: Optional[ServiceMechanicsStatus] = None


class AirlineRficRfiscMappingCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    rfic: str
    rfisc: str
    service_subcode: Optional[str] = None
    commercial_name: Optional[str] = None
    reason_for_issuance_description: Optional[str] = None
    emd_type: AirlineEmdType = AirlineEmdType.UNKNOWN
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None


class AirlineRficRfiscMappingUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    rfic: Optional[str] = None
    rfisc: Optional[str] = None
    service_subcode: Optional[str] = None
    commercial_name: Optional[str] = None
    reason_for_issuance_description: Optional[str] = None
    emd_type: Optional[AirlineEmdType] = None
    status: Optional[ServiceMechanicsStatus] = None
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None


class AirlineEmdInterlineRuleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    interline_allowed: bool = False
    plating_carrier_required: Optional[str] = None
    validating_carrier_must_equal_operating: Optional[bool] = None
    validating_carrier_must_equal_marketing: Optional[bool] = None
    partner_airline_restrictions: List[str] = Field(default_factory=list)
    restriction_text: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class AirlineEmdInterlineRuleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    interline_allowed: Optional[bool] = None
    plating_carrier_required: Optional[str] = None
    validating_carrier_must_equal_operating: Optional[bool] = None
    validating_carrier_must_equal_marketing: Optional[bool] = None
    partner_airline_restrictions: Optional[List[str]] = None
    restriction_text: Optional[str] = None
    status: Optional[ServiceMechanicsStatus] = None


class AirlineEmdLifecycleRuleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    refundable: Optional[bool] = None
    exchangeable: Optional[bool] = None
    voidable: Optional[bool] = None
    reissuable: Optional[bool] = None
    refund_conditions: Optional[str] = None
    exchange_conditions: Optional[str] = None
    void_conditions: Optional[str] = None
    no_show_policy: Optional[str] = None
    residual_value_policy: Optional[str] = None
    status: ServiceMechanicsStatus = ServiceMechanicsStatus.ACTIVE


class AirlineEmdLifecycleRuleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    refundable: Optional[bool] = None
    exchangeable: Optional[bool] = None
    voidable: Optional[bool] = None
    reissuable: Optional[bool] = None
    refund_conditions: Optional[str] = None
    exchange_conditions: Optional[str] = None
    void_conditions: Optional[str] = None
    no_show_policy: Optional[str] = None
    residual_value_policy: Optional[str] = None
    status: Optional[ServiceMechanicsStatus] = None


class PolicyCandidateMechanicsLinkCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    policy_source_id: Optional[str] = None
    extraction_run_id: Optional[str] = None
    candidate_type: PolicyCandidateTaxonomyCandidateType
    candidate_id: Optional[str] = None
    taxonomy_link_id: Optional[str] = None
    mechanics_type: PolicyCandidateMechanicsType
    mechanics_record_id: str
    airline_code: Optional[str] = None
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    confidence_score: float = 0.0
    review_status: ServiceMechanicsReviewStatus = ServiceMechanicsReviewStatus.SUGGESTED
    evidence_text: Optional[str] = None
    reviewer_notes: Optional[str] = None


class PolicyCandidateMechanicsLinkUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    policy_source_id: Optional[str] = None
    extraction_run_id: Optional[str] = None
    candidate_type: Optional[PolicyCandidateTaxonomyCandidateType] = None
    candidate_id: Optional[str] = None
    taxonomy_link_id: Optional[str] = None
    mechanics_type: Optional[PolicyCandidateMechanicsType] = None
    mechanics_record_id: Optional[str] = None
    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    confidence_score: Optional[float] = None
    review_status: Optional[ServiceMechanicsReviewStatus] = None
    evidence_text: Optional[str] = None
    reviewer_notes: Optional[str] = None


class ServiceMechanicsLookupRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None


class AncillaryPricingStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class AncillaryPricingReviewStatus(str, Enum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class AncillaryPriceComponentType(str, Enum):
    BASE_FEE = "base_fee"
    SERVICE_FEE = "service_fee"
    DIRECTION_FEE = "direction_fee"
    SEGMENT_FEE = "segment_fee"
    CONNECTION_FEE = "connection_fee"
    DOCUMENT_FEE = "document_fee"
    AIRPORT_FEE = "airport_fee"
    CHILD_FEE = "child_fee"
    ADULT_FEE = "adult_fee"
    OTHER = "other"


class AncillaryAmountType(str, Enum):
    FIXED = "fixed"
    RANGE = "range"
    PERCENTAGE = "percentage"
    INCLUDED = "included"
    UNKNOWN = "unknown"


class AncillaryAppliesPer(str, Enum):
    PASSENGER = "passenger"
    DIRECTION = "direction"
    SEGMENT = "segment"
    JOURNEY = "journey"
    BOOKING = "booking"
    COUPON = "coupon"
    EMD = "emd"
    OTHER = "other"


class AncillaryApplicabilityOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    MIN = "min"
    MAX = "max"
    BETWEEN = "between"
    CONTAINS = "contains"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    ANY = "any"


class AncillaryApplicabilityAppliesAs(str, Enum):
    CONDITION = "condition"
    EXCLUSION = "exclusion"
    SURCHARGE = "surcharge"
    DISCOUNT = "discount"
    MANUAL_REVIEW = "manual_review"


class AncillaryPricingScope(str, Enum):
    GLOBAL = "global"
    AGENCY = "agency"


class AirlineServiceExceptionTypeExpanded(str, Enum):
    SERVICE_NOT_PERMITTED = "service_not_permitted"
    PRICING_NOT_AVAILABLE = "pricing_not_available"
    ROUTE_RESTRICTION = "route_restriction"
    CONNECTION_RESTRICTION = "connection_restriction"
    AGE_RESTRICTION = "age_restriction"
    COUNTRY_RESTRICTION = "country_restriction"
    AIRPORT_RESTRICTION = "airport_restriction"
    INTERLINE_RESTRICTION = "interline_restriction"
    AIRCRAFT_RESTRICTION = "aircraft_restriction"
    CABIN_RESTRICTION = "cabin_restriction"
    DEADLINE_RESTRICTION = "deadline_restriction"
    DOCUMENT_REQUIRED = "document_required"
    MANUAL_CONTACT_REQUIRED = "manual_contact_required"
    EMD_REQUIRED = "emd_required"
    PAYMENT_RESTRICTION = "payment_restriction"
    UNKNOWN = "unknown"


class AirlineServiceExceptionOutcome(str, Enum):
    PERMITTED = "permitted"
    NOT_PERMITTED = "not_permitted"
    MANUAL_REVIEW = "manual_review"
    SURCHARGE_REQUIRED = "surcharge_required"
    DOCUMENT_REQUIRED = "document_required"
    AIRLINE_CONFIRMATION_REQUIRED = "airline_confirmation_required"
    PAYMENT_REQUIRED = "payment_required"
    UNKNOWN = "unknown"


class AirlineServicePriceQuoteEvaluationStatus(str, Enum):
    PRICED = "priced"
    NO_PRICE_FOUND = "no_price_found"
    MANUAL_REVIEW = "manual_review"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class PolicyCandidatePricingRecordType(str, Enum):
    PRICING_RULE = "pricing_rule"
    PRICE_COMPONENT = "price_component"
    APPLICABILITY = "applicability"
    PRICING_MATRIX = "pricing_matrix"
    PRICING_MATRIX_ROW = "pricing_matrix_row"
    EXCEPTION_RULE = "exception_rule"


class AirlineAncillaryPricingRule(BaseDocument):
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    pricing_rule_name: str
    pricing_status: AncillaryPricingStatus = AncillaryPricingStatus.DRAFT
    review_status: AncillaryPricingReviewStatus = AncillaryPricingReviewStatus.SUGGESTED
    mandatory_service: bool = False
    optional_service: bool = True
    fee_included_in_fare: bool = False
    separate_fee_required: bool = False
    emd_required: Optional[bool] = None
    payment_rule_id: Optional[str] = None
    emd_issuance_rule_id: Optional[str] = None
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    is_global: bool = True
    agency_id: Optional[str] = None
    validity_start_date: Optional[date] = None
    validity_end_date: Optional[date] = None
    notes: Optional[str] = None


class AirlineAncillaryPriceComponent(BaseDocument):
    pricing_rule_id: str
    component_type: AncillaryPriceComponentType = AncillaryPriceComponentType.SERVICE_FEE
    amount: Optional[float] = None
    currency: Optional[str] = None
    amount_type: AncillaryAmountType = AncillaryAmountType.UNKNOWN
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    tax_included: Optional[bool] = None
    applies_per: AncillaryAppliesPer = AncillaryAppliesPer.PASSENGER
    roundtrip_doubling_rule: bool = False
    sequence: int = 100
    status: AncillaryPricingStatus = AncillaryPricingStatus.ACTIVE
    notes: Optional[str] = None


class AirlineAncillaryPricingApplicability(BaseDocument):
    pricing_rule_id: str
    dimension_code: str
    operator: AncillaryApplicabilityOperator = AncillaryApplicabilityOperator.ANY
    value: Optional[str] = None
    value_json: Dict[str, Any] = Field(default_factory=dict)
    applies_as: AncillaryApplicabilityAppliesAs = AncillaryApplicabilityAppliesAs.CONDITION
    status: AncillaryPricingStatus = AncillaryPricingStatus.ACTIVE


class AirlineAncillaryPricingMatrix(BaseDocument):
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    matrix_name: str
    currency: Optional[str] = None
    scope: AncillaryPricingScope = AncillaryPricingScope.GLOBAL
    agency_id: Optional[str] = None
    status: AncillaryPricingStatus = AncillaryPricingStatus.ACTIVE
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None


class AirlineAncillaryPricingMatrixRow(BaseDocument):
    matrix_id: str
    pricing_rule_id: Optional[str] = None
    row_label: str
    route_band: Optional[str] = None
    direct_vs_connecting: Optional[str] = None
    origin_region: Optional[str] = None
    destination_region: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    airport_pair: Optional[str] = None
    passenger_type: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    cabin: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    applies_per: AncillaryAppliesPer = AncillaryAppliesPer.PASSENGER
    emd_required: Optional[bool] = None
    notes: Optional[str] = None
    status: AncillaryPricingStatus = AncillaryPricingStatus.ACTIVE
    sort_order: int = 100


class AirlineServiceExceptionRule(BaseDocument):
    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    exception_name: str
    exception_type: AirlineServiceExceptionTypeExpanded = AirlineServiceExceptionTypeExpanded.UNKNOWN
    severity: ServiceMechanicsSeverity = ServiceMechanicsSeverity.WARNING
    outcome: AirlineServiceExceptionOutcome = AirlineServiceExceptionOutcome.UNKNOWN
    condition_json: Dict[str, Any] = Field(default_factory=dict)
    explanation: str
    suggested_action: Optional[str] = None
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    pricing_rule_id: Optional[str] = None
    mechanics_record_id: Optional[str] = None
    is_global: bool = True
    agency_id: Optional[str] = None
    status: AncillaryPricingStatus = AncillaryPricingStatus.ACTIVE


class AirlineServicePriceQuoteScenario(BaseDocument):
    agency_id: Optional[str] = None
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    scenario_name: str
    passenger_age: Optional[int] = None
    passenger_type: Optional[str] = None
    route_type: Optional[str] = None
    direct_vs_connecting: Optional[str] = None
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    cabin: Optional[str] = None
    segment_count: Optional[int] = None
    direction_count: Optional[int] = None
    currency: Optional[str] = None
    context_json: Dict[str, Any] = Field(default_factory=dict)


class AirlineServicePriceQuoteResult(BaseDocument):
    scenario_id: str
    pricing_rule_ids: List[str] = Field(default_factory=list)
    exception_rule_ids: List[str] = Field(default_factory=list)
    estimated_amount: Optional[float] = None
    currency: Optional[str] = None
    amount_breakdown_json: List[Dict[str, Any]] = Field(default_factory=list)
    evaluation_status: AirlineServicePriceQuoteEvaluationStatus = AirlineServicePriceQuoteEvaluationStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    explanation: str


class PolicyCandidatePricingLink(BaseDocument):
    agency_id: Optional[str] = None
    policy_source_id: Optional[str] = None
    extraction_run_id: Optional[str] = None
    candidate_type: PolicyCandidateTaxonomyCandidateType
    candidate_id: Optional[str] = None
    taxonomy_link_id: Optional[str] = None
    mechanics_link_id: Optional[str] = None
    pricing_record_type: PolicyCandidatePricingRecordType
    pricing_record_id: str
    airline_code: Optional[str] = None
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    confidence_score: float = 0.0
    review_status: AncillaryPricingReviewStatus = AncillaryPricingReviewStatus.SUGGESTED
    evidence_text: Optional[str] = None
    reviewer_notes: Optional[str] = None


class AirlineAncillaryPricingRuleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    pricing_rule_name: str
    pricing_status: AncillaryPricingStatus = AncillaryPricingStatus.DRAFT
    review_status: AncillaryPricingReviewStatus = AncillaryPricingReviewStatus.SUGGESTED
    mandatory_service: bool = False
    optional_service: bool = True
    fee_included_in_fare: bool = False
    separate_fee_required: bool = False
    emd_required: Optional[bool] = None
    payment_rule_id: Optional[str] = None
    emd_issuance_rule_id: Optional[str] = None
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    is_global: bool = True
    agency_id: Optional[str] = None
    validity_start_date: Optional[date] = None
    validity_end_date: Optional[date] = None
    notes: Optional[str] = None


class AirlineAncillaryPricingRuleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    pricing_rule_name: Optional[str] = None
    pricing_status: Optional[AncillaryPricingStatus] = None
    review_status: Optional[AncillaryPricingReviewStatus] = None
    mandatory_service: Optional[bool] = None
    optional_service: Optional[bool] = None
    fee_included_in_fare: Optional[bool] = None
    separate_fee_required: Optional[bool] = None
    emd_required: Optional[bool] = None
    payment_rule_id: Optional[str] = None
    emd_issuance_rule_id: Optional[str] = None
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    is_global: Optional[bool] = None
    agency_id: Optional[str] = None
    validity_start_date: Optional[date] = None
    validity_end_date: Optional[date] = None
    notes: Optional[str] = None


class AirlineAncillaryPriceComponentCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    pricing_rule_id: str
    component_type: AncillaryPriceComponentType = AncillaryPriceComponentType.SERVICE_FEE
    amount: Optional[float] = None
    currency: Optional[str] = None
    amount_type: AncillaryAmountType = AncillaryAmountType.UNKNOWN
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    tax_included: Optional[bool] = None
    applies_per: AncillaryAppliesPer = AncillaryAppliesPer.PASSENGER
    roundtrip_doubling_rule: bool = False
    sequence: int = 100
    status: AncillaryPricingStatus = AncillaryPricingStatus.ACTIVE
    notes: Optional[str] = None


class AirlineAncillaryPriceComponentUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    pricing_rule_id: Optional[str] = None
    component_type: Optional[AncillaryPriceComponentType] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    amount_type: Optional[AncillaryAmountType] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    tax_included: Optional[bool] = None
    applies_per: Optional[AncillaryAppliesPer] = None
    roundtrip_doubling_rule: Optional[bool] = None
    sequence: Optional[int] = None
    status: Optional[AncillaryPricingStatus] = None
    notes: Optional[str] = None


class AirlineAncillaryPricingApplicabilityCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    pricing_rule_id: str
    dimension_code: str
    operator: AncillaryApplicabilityOperator = AncillaryApplicabilityOperator.ANY
    value: Optional[str] = None
    value_json: Dict[str, Any] = Field(default_factory=dict)
    applies_as: AncillaryApplicabilityAppliesAs = AncillaryApplicabilityAppliesAs.CONDITION
    status: AncillaryPricingStatus = AncillaryPricingStatus.ACTIVE


class AirlineAncillaryPricingApplicabilityUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    pricing_rule_id: Optional[str] = None
    dimension_code: Optional[str] = None
    operator: Optional[AncillaryApplicabilityOperator] = None
    value: Optional[str] = None
    value_json: Optional[Dict[str, Any]] = None
    applies_as: Optional[AncillaryApplicabilityAppliesAs] = None
    status: Optional[AncillaryPricingStatus] = None


class AirlineAncillaryPricingMatrixCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    matrix_name: str
    currency: Optional[str] = None
    scope: AncillaryPricingScope = AncillaryPricingScope.GLOBAL
    agency_id: Optional[str] = None
    status: AncillaryPricingStatus = AncillaryPricingStatus.ACTIVE
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None


class AirlineAncillaryPricingMatrixUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    matrix_name: Optional[str] = None
    currency: Optional[str] = None
    scope: Optional[AncillaryPricingScope] = None
    agency_id: Optional[str] = None
    status: Optional[AncillaryPricingStatus] = None
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None


class AirlineAncillaryPricingMatrixRowCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    matrix_id: str
    pricing_rule_id: Optional[str] = None
    row_label: str
    route_band: Optional[str] = None
    direct_vs_connecting: Optional[str] = None
    origin_region: Optional[str] = None
    destination_region: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    airport_pair: Optional[str] = None
    passenger_type: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    cabin: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    applies_per: AncillaryAppliesPer = AncillaryAppliesPer.PASSENGER
    emd_required: Optional[bool] = None
    notes: Optional[str] = None
    status: AncillaryPricingStatus = AncillaryPricingStatus.ACTIVE
    sort_order: int = 100


class AirlineAncillaryPricingMatrixRowUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    matrix_id: Optional[str] = None
    pricing_rule_id: Optional[str] = None
    row_label: Optional[str] = None
    route_band: Optional[str] = None
    direct_vs_connecting: Optional[str] = None
    origin_region: Optional[str] = None
    destination_region: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    airport_pair: Optional[str] = None
    passenger_type: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    cabin: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    applies_per: Optional[AncillaryAppliesPer] = None
    emd_required: Optional[bool] = None
    notes: Optional[str] = None
    status: Optional[AncillaryPricingStatus] = None
    sort_order: Optional[int] = None


class AirlineServiceExceptionRuleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    exception_name: str
    exception_type: AirlineServiceExceptionTypeExpanded = AirlineServiceExceptionTypeExpanded.UNKNOWN
    severity: ServiceMechanicsSeverity = ServiceMechanicsSeverity.WARNING
    outcome: AirlineServiceExceptionOutcome = AirlineServiceExceptionOutcome.UNKNOWN
    condition_json: Dict[str, Any] = Field(default_factory=dict)
    explanation: str
    suggested_action: Optional[str] = None
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    pricing_rule_id: Optional[str] = None
    mechanics_record_id: Optional[str] = None
    is_global: bool = True
    agency_id: Optional[str] = None
    status: AncillaryPricingStatus = AncillaryPricingStatus.ACTIVE


class AirlineServiceExceptionRuleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    exception_name: Optional[str] = None
    exception_type: Optional[AirlineServiceExceptionTypeExpanded] = None
    severity: Optional[ServiceMechanicsSeverity] = None
    outcome: Optional[AirlineServiceExceptionOutcome] = None
    condition_json: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    suggested_action: Optional[str] = None
    source_policy_id: Optional[str] = None
    approved_knowledge_record_id: Optional[str] = None
    pricing_rule_id: Optional[str] = None
    mechanics_record_id: Optional[str] = None
    is_global: Optional[bool] = None
    agency_id: Optional[str] = None
    status: Optional[AncillaryPricingStatus] = None


class AirlineServicePriceQuoteScenarioCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    scenario_name: str
    passenger_age: Optional[int] = None
    passenger_type: Optional[str] = None
    route_type: Optional[str] = None
    direct_vs_connecting: Optional[str] = None
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    cabin: Optional[str] = None
    segment_count: Optional[int] = None
    direction_count: Optional[int] = None
    currency: Optional[str] = None
    context_json: Dict[str, Any] = Field(default_factory=dict)


class AirlineServicePriceQuoteScenarioUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    scenario_name: Optional[str] = None
    passenger_age: Optional[int] = None
    passenger_type: Optional[str] = None
    route_type: Optional[str] = None
    direct_vs_connecting: Optional[str] = None
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    cabin: Optional[str] = None
    segment_count: Optional[int] = None
    direction_count: Optional[int] = None
    currency: Optional[str] = None
    context_json: Optional[Dict[str, Any]] = None


class AirlineServicePriceQuoteEvaluationRequest(AirlineServicePriceQuoteScenarioCreate):
    scenario_id: Optional[str] = None
    store_result: bool = True


class PolicyCandidatePricingLinkCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    policy_source_id: Optional[str] = None
    extraction_run_id: Optional[str] = None
    candidate_type: PolicyCandidateTaxonomyCandidateType
    candidate_id: Optional[str] = None
    taxonomy_link_id: Optional[str] = None
    mechanics_link_id: Optional[str] = None
    pricing_record_type: PolicyCandidatePricingRecordType
    pricing_record_id: str
    airline_code: Optional[str] = None
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    confidence_score: float = 0.0
    review_status: AncillaryPricingReviewStatus = AncillaryPricingReviewStatus.SUGGESTED
    evidence_text: Optional[str] = None
    reviewer_notes: Optional[str] = None


class PolicyCandidatePricingLinkUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    policy_source_id: Optional[str] = None
    extraction_run_id: Optional[str] = None
    candidate_type: Optional[PolicyCandidateTaxonomyCandidateType] = None
    candidate_id: Optional[str] = None
    taxonomy_link_id: Optional[str] = None
    mechanics_link_id: Optional[str] = None
    pricing_record_type: Optional[PolicyCandidatePricingRecordType] = None
    pricing_record_id: Optional[str] = None
    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    confidence_score: Optional[float] = None
    review_status: Optional[AncillaryPricingReviewStatus] = None
    evidence_text: Optional[str] = None
    reviewer_notes: Optional[str] = None


class AncillaryPricingLookupRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None


class PolicyComparisonReviewStatus(str, Enum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class PolicyComparisonStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class PolicyComparisonGeneratedFrom(str, Enum):
    MANUAL = "manual"
    POLICY_LOOKUP = "policy_lookup"
    REQUEST_CONTEXT = "request_context"
    OFFER_CONTEXT = "offer_context"
    OTHER = "other"


class PolicyComparisonWarningLevel(str, Enum):
    NONE = "none"
    INFO = "info"
    ADVISORY = "advisory"
    WARNING = "warning"
    BLOCKER = "blocker"


class ServiceAdvisorResultStatus(str, Enum):
    EVALUATED = "evaluated"
    NO_DATA = "no_data"
    MANUAL_REVIEW = "manual_review"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class AirlinePolicyComparisonProfile(BaseDocument):
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    display_name: str
    commercial_names: List[str] = Field(default_factory=list)
    taxonomy_summary_json: Dict[str, Any] = Field(default_factory=dict)
    communication_summary_json: Dict[str, Any] = Field(default_factory=dict)
    payment_summary_json: Dict[str, Any] = Field(default_factory=dict)
    pricing_summary_json: Dict[str, Any] = Field(default_factory=dict)
    exception_summary_json: Dict[str, Any] = Field(default_factory=dict)
    source_policy_ids: List[str] = Field(default_factory=list)
    approved_knowledge_record_ids: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    review_status: PolicyComparisonReviewStatus = PolicyComparisonReviewStatus.SUGGESTED
    status: PolicyComparisonStatus = PolicyComparisonStatus.ACTIVE
    is_global: bool = True
    agency_id: Optional[str] = None
    notes: Optional[str] = None


class AirlinePolicyComparisonSnapshot(BaseDocument):
    agency_id: Optional[str] = None
    snapshot_name: str
    airline_codes: List[str] = Field(default_factory=list)
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    route_context_json: Dict[str, Any] = Field(default_factory=dict)
    passenger_context_json: Dict[str, Any] = Field(default_factory=dict)
    service_context_json: Dict[str, Any] = Field(default_factory=dict)
    comparison_rows_json: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    generated_from: PolicyComparisonGeneratedFrom = PolicyComparisonGeneratedFrom.MANUAL


class AirlinePolicyComparisonRow(BaseDocument):
    snapshot_id: Optional[str] = None
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    commercial_name: Optional[str] = None
    mandatory_optional_summary: Optional[str] = None
    age_rules_summary: Optional[str] = None
    route_restrictions_summary: Optional[str] = None
    connection_restrictions_summary: Optional[str] = None
    documents_required_summary: Optional[str] = None
    deadline_summary: Optional[str] = None
    ssr_osi_summary: Optional[str] = None
    confirmation_summary: Optional[str] = None
    emd_required: Optional[bool] = None
    emd_type: Optional[str] = None
    rfic: Optional[str] = None
    rfisc: Optional[str] = None
    pricing_summary: Optional[str] = None
    refund_change_summary: Optional[str] = None
    ndc_gds_support_summary: Optional[str] = None
    manual_contact_required: Optional[bool] = None
    warning_level: PolicyComparisonWarningLevel = PolicyComparisonWarningLevel.NONE
    operational_complexity_score: Optional[int] = None
    confidence_score: Optional[float] = None
    source_summary: Optional[str] = None
    row_json: Dict[str, Any] = Field(default_factory=dict)


class AirlineServiceAdvisorScenario(BaseDocument):
    agency_id: Optional[str] = None
    scenario_name: str
    airline_codes: List[str] = Field(default_factory=list)
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    passenger_age: Optional[int] = None
    passenger_type: Optional[str] = None
    route_type: Optional[str] = None
    direct_vs_connecting: Optional[str] = None
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    cabin: Optional[str] = None
    segment_count: Optional[int] = None
    direction_count: Optional[int] = None
    requested_service_context_json: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None


class AirlineServiceAdvisorResult(BaseDocument):
    scenario_id: str
    result_status: ServiceAdvisorResultStatus = ServiceAdvisorResultStatus.UNKNOWN
    advisory_rows_json: List[Dict[str, Any]] = Field(default_factory=list)
    comparison_snapshot_id: Optional[str] = None
    operational_warnings: List[str] = Field(default_factory=list)
    blocker_count: int = 0
    warning_count: int = 0
    advisory_count: int = 0
    manual_contact_required_count: int = 0
    emd_required_count: int = 0
    estimated_price_available_count: int = 0
    explanation: str


class AirlinePolicyComparisonSavedView(BaseDocument):
    agency_id: Optional[str] = None
    view_name: str
    airline_codes: List[str] = Field(default_factory=list)
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    visible_columns: List[str] = Field(default_factory=list)
    filters_json: Dict[str, Any] = Field(default_factory=dict)
    sort_json: Dict[str, Any] = Field(default_factory=dict)
    is_global: bool = True
    status: PolicyComparisonStatus = PolicyComparisonStatus.ACTIVE


class AirlinePolicyComparisonProfileCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    display_name: Optional[str] = None
    commercial_names: List[str] = Field(default_factory=list)
    taxonomy_summary_json: Dict[str, Any] = Field(default_factory=dict)
    communication_summary_json: Dict[str, Any] = Field(default_factory=dict)
    payment_summary_json: Dict[str, Any] = Field(default_factory=dict)
    pricing_summary_json: Dict[str, Any] = Field(default_factory=dict)
    exception_summary_json: Dict[str, Any] = Field(default_factory=dict)
    source_policy_ids: List[str] = Field(default_factory=list)
    approved_knowledge_record_ids: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    review_status: PolicyComparisonReviewStatus = PolicyComparisonReviewStatus.SUGGESTED
    status: PolicyComparisonStatus = PolicyComparisonStatus.ACTIVE
    is_global: bool = True
    agency_id: Optional[str] = None
    notes: Optional[str] = None


class AirlinePolicyComparisonProfileUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    display_name: Optional[str] = None
    commercial_names: Optional[List[str]] = None
    taxonomy_summary_json: Optional[Dict[str, Any]] = None
    communication_summary_json: Optional[Dict[str, Any]] = None
    payment_summary_json: Optional[Dict[str, Any]] = None
    pricing_summary_json: Optional[Dict[str, Any]] = None
    exception_summary_json: Optional[Dict[str, Any]] = None
    source_policy_ids: Optional[List[str]] = None
    approved_knowledge_record_ids: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    review_status: Optional[PolicyComparisonReviewStatus] = None
    status: Optional[PolicyComparisonStatus] = None
    is_global: Optional[bool] = None
    agency_id: Optional[str] = None
    notes: Optional[str] = None


class AirlinePolicyComparisonBuildRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    display_name: Optional[str] = None
    review_status: PolicyComparisonReviewStatus = PolicyComparisonReviewStatus.SUGGESTED
    notes: Optional[str] = None
    is_global: bool = True


class AirlinePolicyComparisonRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_name: Optional[str] = None
    airline_codes: List[str] = Field(default_factory=list)
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    route_context_json: Dict[str, Any] = Field(default_factory=dict)
    passenger_context_json: Dict[str, Any] = Field(default_factory=dict)
    service_context_json: Dict[str, Any] = Field(default_factory=dict)
    generated_from: PolicyComparisonGeneratedFrom = PolicyComparisonGeneratedFrom.MANUAL


class AirlinePolicyComparisonSnapshotCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    snapshot_name: str
    airline_codes: List[str] = Field(default_factory=list)
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    route_context_json: Dict[str, Any] = Field(default_factory=dict)
    passenger_context_json: Dict[str, Any] = Field(default_factory=dict)
    service_context_json: Dict[str, Any] = Field(default_factory=dict)
    comparison_rows_json: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    generated_from: PolicyComparisonGeneratedFrom = PolicyComparisonGeneratedFrom.MANUAL


class AirlineServiceAdvisorScenarioCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    scenario_name: str
    airline_codes: List[str] = Field(default_factory=list)
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    passenger_age: Optional[int] = None
    passenger_type: Optional[str] = None
    route_type: Optional[str] = None
    direct_vs_connecting: Optional[str] = None
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    cabin: Optional[str] = None
    segment_count: Optional[int] = None
    direction_count: Optional[int] = None
    requested_service_context_json: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None


class AirlineServiceAdvisorEvaluationRequest(AirlineServiceAdvisorScenarioCreate):
    scenario_id: Optional[str] = None


class AirlinePolicyComparisonSavedViewCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    view_name: str
    airline_codes: List[str] = Field(default_factory=list)
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    visible_columns: List[str] = Field(default_factory=list)
    filters_json: Dict[str, Any] = Field(default_factory=dict)
    sort_json: Dict[str, Any] = Field(default_factory=dict)
    is_global: bool = True
    status: PolicyComparisonStatus = PolicyComparisonStatus.ACTIVE


class AirlinePolicyComparisonSavedViewUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    view_name: Optional[str] = None
    airline_codes: Optional[List[str]] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    visible_columns: Optional[List[str]] = None
    filters_json: Optional[Dict[str, Any]] = None
    sort_json: Optional[Dict[str, Any]] = None
    is_global: Optional[bool] = None
    status: Optional[PolicyComparisonStatus] = None


class OfferPolicyAdvisorContextStatus(str, Enum):
    BUILT = "built"
    EVALUATED = "evaluated"
    ATTACHED = "attached"
    ARCHIVED = "archived"


class OfferPolicyAdvisorDecisionNoteStatus(str, Enum):
    DRAFT = "draft"
    RECORDED = "recorded"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


class OfferPolicyAdvisorWarningSource(str, Enum):
    CONTEXT = "context"
    POLICY_COMPARISON = "policy_comparison"
    SERVICE_ADVISOR = "service_advisor"
    ANCILLARY_PRICING = "ancillary_pricing"
    SERVICE_MECHANICS = "service_mechanics"
    MANUAL_NOTE = "manual_note"


class OfferPolicyAdvisorContext(BaseDocument):
    agency_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    context_name: str
    context_status: OfferPolicyAdvisorContextStatus = OfferPolicyAdvisorContextStatus.BUILT
    airline_codes: List[str] = Field(default_factory=list)
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    policy_comparison_snapshot_id: Optional[str] = None
    advisor_scenario_id: Optional[str] = None
    advisor_result_id: Optional[str] = None
    quote_result_ids: List[str] = Field(default_factory=list)
    service_mechanics_lookup_json: Dict[str, Any] = Field(default_factory=dict)
    taxonomy_refs_json: Dict[str, Any] = Field(default_factory=dict)
    offer_workspace_summary_json: Dict[str, Any] = Field(default_factory=dict)
    offer_option_summary_json: Dict[str, Any] = Field(default_factory=dict)
    route_context_json: Dict[str, Any] = Field(default_factory=dict)
    passenger_context_json: Dict[str, Any] = Field(default_factory=dict)
    service_context_json: Dict[str, Any] = Field(default_factory=dict)
    source_links_json: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    warning_count: int = 0
    manual_review_required: bool = False
    metadata_only: bool = True
    auto_recommendation_disabled: bool = True
    provider_execution_disabled: bool = True
    emd_issuance_disabled: bool = True
    payment_invoice_settlement_disabled: bool = True
    created_by_user_id: Optional[str] = None


class OfferPolicyAdvisorAirlineRow(BaseDocument):
    agency_id: str
    context_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    airline_code: str
    domain_code: str
    family_code: str
    variant_code: Optional[str] = None
    policy_comparison_snapshot_id: Optional[str] = None
    policy_comparison_row_id: Optional[str] = None
    advisor_result_id: Optional[str] = None
    quote_result_id: Optional[str] = None
    service_mechanics_lookup_json: Dict[str, Any] = Field(default_factory=dict)
    ancillary_pricing_quote_json: Dict[str, Any] = Field(default_factory=dict)
    taxonomy_refs_json: Dict[str, Any] = Field(default_factory=dict)
    warning_level: PolicyComparisonWarningLevel = PolicyComparisonWarningLevel.NONE
    operational_complexity_score: Optional[int] = None
    manual_contact_required: bool = False
    emd_required: bool = False
    pricing_summary: Optional[str] = None
    advisor_summary: Optional[str] = None
    row_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferPolicyAdvisorWarning(BaseDocument):
    agency_id: str
    context_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    airline_code: Optional[str] = None
    warning_level: PolicyComparisonWarningLevel = PolicyComparisonWarningLevel.INFO
    warning_type: str
    message: str
    source: OfferPolicyAdvisorWarningSource = OfferPolicyAdvisorWarningSource.CONTEXT
    source_record_id: Optional[str] = None
    human_review_required: bool = True
    metadata_only: bool = True


class OfferPolicyAdvisorDecisionNote(BaseDocument):
    agency_id: str
    context_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    airline_code: Optional[str] = None
    note_title: str
    note_body: str
    note_status: OfferPolicyAdvisorDecisionNoteStatus = OfferPolicyAdvisorDecisionNoteStatus.RECORDED
    policy_comparison_snapshot_id: Optional[str] = None
    advisor_result_id: Optional[str] = None
    created_by_user_id: Optional[str] = None
    human_reviewed: bool = True
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    auto_recommendation_disabled: bool = True


class OfferPolicyAdvisorSavedSnapshot(BaseDocument):
    agency_id: str
    context_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    snapshot_name: str
    policy_comparison_snapshot_id: Optional[str] = None
    advisor_scenario_id: Optional[str] = None
    advisor_result_id: Optional[str] = None
    quote_result_ids: List[str] = Field(default_factory=list)
    airline_row_ids: List[str] = Field(default_factory=list)
    warning_ids: List[str] = Field(default_factory=list)
    decision_note_ids: List[str] = Field(default_factory=list)
    snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferPolicyAdvisorContextBuildRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    context_name: Optional[str] = None
    airline_codes: List[str] = Field(default_factory=list)
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    route_context_json: Dict[str, Any] = Field(default_factory=dict)
    passenger_context_json: Dict[str, Any] = Field(default_factory=dict)
    service_context_json: Dict[str, Any] = Field(default_factory=dict)


class OfferPolicyAdvisorEvaluationRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_codes: Optional[List[str]] = None
    route_context_json: Optional[Dict[str, Any]] = None
    passenger_context_json: Optional[Dict[str, Any]] = None
    service_context_json: Optional[Dict[str, Any]] = None


class OfferPolicyAdvisorAttachmentRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    policy_comparison_snapshot_id: Optional[str] = None
    advisor_scenario_id: Optional[str] = None
    advisor_result_id: Optional[str] = None
    quote_result_ids: List[str] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferPolicyAdvisorDecisionNoteCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    offer_option_id: Optional[str] = None
    airline_code: Optional[str] = None
    note_title: str
    note_body: str
    note_status: OfferPolicyAdvisorDecisionNoteStatus = OfferPolicyAdvisorDecisionNoteStatus.RECORDED
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferPolicyAdvisorSavedSnapshotCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_name: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionPackStatus(str, Enum):
    BUILT = "built"
    REBUILT = "rebuilt"
    SNAPSHOTTED = "snapshotted"
    ARCHIVED = "archived"


class OfferDecisionPackEvidenceType(str, Enum):
    OFFER_OPTION = "offer_option"
    ADVISOR_CONTEXT = "advisor_context"
    ADVISOR_SNAPSHOT = "advisor_snapshot"
    ADVISOR_AIRLINE_ROW = "advisor_airline_row"
    POLICY_COMPARISON = "policy_comparison"
    ANCILLARY_PRICING = "ancillary_pricing"
    SERVICE_MECHANICS = "service_mechanics"
    TAXONOMY = "taxonomy"
    MANUAL_REVIEW = "manual_review"


class OfferDecisionPackWarningSource(str, Enum):
    OFFER_CONTEXT = "offer_context"
    ADVISOR_CONTEXT = "advisor_context"
    ADVISOR_SNAPSHOT = "advisor_snapshot"
    ADVISOR_AIRLINE_ROW = "advisor_airline_row"
    POLICY_COMPARISON = "policy_comparison"
    ANCILLARY_PRICING = "ancillary_pricing"
    SERVICE_MECHANICS = "service_mechanics"
    REVIEW_NOTE = "review_note"


class OfferDecisionPackReviewNoteStatus(str, Enum):
    DRAFT = "draft"
    RECORDED = "recorded"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class OfferDecisionPack(BaseDocument):
    agency_id: str
    offer_workspace_id: str
    pack_name: str
    pack_status: OfferDecisionPackStatus = OfferDecisionPackStatus.BUILT
    rebuilt_from_pack_id: Optional[str] = None
    offer_policy_advisor_context_ids: List[str] = Field(default_factory=list)
    advisor_saved_snapshot_ids: List[str] = Field(default_factory=list)
    policy_comparison_snapshot_ids: List[str] = Field(default_factory=list)
    advisor_result_ids: List[str] = Field(default_factory=list)
    quote_result_ids: List[str] = Field(default_factory=list)
    service_mechanics_record_ids: List[str] = Field(default_factory=list)
    airline_codes: List[str] = Field(default_factory=list)
    taxonomy_refs_json: Dict[str, Any] = Field(default_factory=dict)
    offer_workspace_summary_json: Dict[str, Any] = Field(default_factory=dict)
    option_summary_json: Dict[str, Any] = Field(default_factory=dict)
    passenger_context_json: Dict[str, Any] = Field(default_factory=dict)
    request_context_json: Dict[str, Any] = Field(default_factory=dict)
    service_context_json: Dict[str, Any] = Field(default_factory=dict)
    operational_complexity_score: int = 0
    warning_level: PolicyComparisonWarningLevel = PolicyComparisonWarningLevel.NONE
    option_count: int = 0
    evidence_count: int = 0
    unresolved_warning_count: int = 0
    review_note_count: int = 0
    saved_snapshot_count: int = 0
    manual_review_required: bool = True
    human_review_required: bool = True
    metadata_only: bool = True
    auto_recommendation_disabled: bool = True
    offer_price_mutation_disabled: bool = True
    provider_execution_disabled: bool = True
    booking_execution_disabled: bool = True
    ticket_emd_issuance_disabled: bool = True
    payment_invoice_settlement_disabled: bool = True
    created_by_user_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionPackOption(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    offer_option_id: str
    airline_code: Optional[str] = None
    option_label: Optional[str] = None
    option_status: Optional[str] = None
    advisor_context_id: Optional[str] = None
    advisor_saved_snapshot_id: Optional[str] = None
    policy_comparison_snapshot_id: Optional[str] = None
    advisor_result_id: Optional[str] = None
    quote_result_ids: List[str] = Field(default_factory=list)
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    operational_complexity_score: int = 0
    warning_level: PolicyComparisonWarningLevel = PolicyComparisonWarningLevel.NONE
    evidence_count: int = 0
    unresolved_warning_count: int = 0
    manual_review_required: bool = True
    pricing_summary_json: Dict[str, Any] = Field(default_factory=dict)
    option_summary_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    auto_recommendation_disabled: bool = True
    offer_price_mutation_disabled: bool = True


class OfferDecisionPackEvidence(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    airline_code: Optional[str] = None
    evidence_type: OfferDecisionPackEvidenceType
    evidence_title: str
    evidence_summary: Optional[str] = None
    source_collection: Optional[str] = None
    source_record_id: Optional[str] = None
    advisor_context_id: Optional[str] = None
    advisor_saved_snapshot_id: Optional[str] = None
    policy_comparison_snapshot_id: Optional[str] = None
    policy_comparison_row_id: Optional[str] = None
    advisor_result_id: Optional[str] = None
    quote_result_id: Optional[str] = None
    service_mechanics_record_id: Optional[str] = None
    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    variant_code: Optional[str] = None
    passenger_context_json: Dict[str, Any] = Field(default_factory=dict)
    request_context_json: Dict[str, Any] = Field(default_factory=dict)
    service_context_json: Dict[str, Any] = Field(default_factory=dict)
    evidence_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionPackWarning(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    airline_code: Optional[str] = None
    warning_level: PolicyComparisonWarningLevel = PolicyComparisonWarningLevel.INFO
    warning_type: str
    message: str
    source: OfferDecisionPackWarningSource = OfferDecisionPackWarningSource.OFFER_CONTEXT
    source_record_id: Optional[str] = None
    human_review_required: bool = True
    resolved: bool = False
    metadata_only: bool = True


class OfferDecisionPackReviewNote(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    airline_code: Optional[str] = None
    note_title: str
    note_body: str
    note_status: OfferDecisionPackReviewNoteStatus = OfferDecisionPackReviewNoteStatus.RECORDED
    created_by_user_id: Optional[str] = None
    human_reviewed: bool = True
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    auto_recommendation_disabled: bool = True


class OfferDecisionPackSnapshot(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    snapshot_name: str
    option_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    warning_ids: List[str] = Field(default_factory=list)
    review_note_ids: List[str] = Field(default_factory=list)
    source_advisor_snapshot_ids: List[str] = Field(default_factory=list)
    snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    immutable: bool = True
    metadata_only: bool = True
    human_review_required: bool = True


class OfferDecisionPackBuildRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    offer_workspace_id: str
    pack_name: Optional[str] = None
    advisor_context_ids: List[str] = Field(default_factory=list)
    advisor_saved_snapshot_ids: List[str] = Field(default_factory=list)
    rebuild_from_pack_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionPackAdvisorAttachmentRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    advisor_context_id: Optional[str] = None
    advisor_saved_snapshot_id: Optional[str] = None
    offer_option_id: Optional[str] = None
    airline_code: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionPackReviewNoteCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    offer_option_id: Optional[str] = None
    airline_code: Optional[str] = None
    note_title: str
    note_body: str
    note_status: OfferDecisionPackReviewNoteStatus = OfferDecisionPackReviewNoteStatus.RECORDED
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionPackReviewNoteUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    note_title: Optional[str] = None
    note_body: Optional[str] = None
    note_status: Optional[OfferDecisionPackReviewNoteStatus] = None
    metadata_json: Optional[Dict[str, Any]] = None


class OfferDecisionPackSnapshotCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_name: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExplanationType(str, Enum):
    OPERATIONAL = "operational"
    POLICY = "policy"
    PRICING = "pricing"
    MECHANICS = "mechanics"
    WARNING = "warning"
    EVIDENCE = "evidence"
    REVIEW = "review"
    COMPARISON = "comparison"
    SUMMARY = "summary"
    DETAILED_EXPLANATION = "detailed_explanation"


class OfferDecisionTimelineEventType(str, Enum):
    CREATED = "created"
    ADVISOR_ATTACHED = "advisor_attached"
    COMPARISON_GENERATED = "comparison_generated"
    WARNING_ADDED = "warning_added"
    REVIEW_STARTED = "review_started"
    REVIEW_COMPLETED = "review_completed"
    NOTE_ADDED = "note_added"
    SNAPSHOT_SAVED = "snapshot_saved"
    DECISION_PACK_CLOSED = "decision_pack_closed"
    MANUAL_OVERRIDE_RECORDED = "manual_override_recorded"


class OfferDecisionActorType(str, Enum):
    AGENCY = "agency"
    PLATFORM = "platform"
    SYSTEM = "system"


class OfferDecisionEvidenceReferenceType(str, Enum):
    ADVISOR_RESULT = "advisor_result"
    COMPARISON_SNAPSHOT = "comparison_snapshot"
    PRICING_RULE = "pricing_rule"
    MECHANICS_RULE = "mechanics_rule"
    POLICY_RECORD = "policy_record"
    TAXONOMY = "taxonomy"
    EXCEPTION = "exception"
    WARNING = "warning"
    REVIEW_NOTE = "review_note"
    KNOWLEDGE_RECORD = "knowledge_record"


class OfferDecisionReasonCategory(str, Enum):
    POLICY = "policy"
    COMMERCIAL = "commercial"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"
    AIRLINE = "airline"
    MANUAL = "manual"
    PRICING = "pricing"
    MECHANICS = "mechanics"
    RISK = "risk"


class OfferDecisionReasonImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OfferDecisionAcknowledgementType(str, Enum):
    READ = "read"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REQUIRES_FOLLOWUP = "requires_followup"


class OfferDecisionExplanation(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    title: str
    explanation_type: OfferDecisionExplanationType = OfferDecisionExplanationType.SUMMARY
    explanation_text: str
    created_by: Optional[str] = None
    finalized: bool = False
    finalized_at: Optional[datetime] = None
    archived: bool = False
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    immutable_once_finalized: bool = True
    metadata_only: bool = True
    human_review_only: bool = True
    automatic_recommendation_disabled: bool = True
    provider_execution_disabled: bool = True


class OfferDecisionTimelineEvent(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=now_utc)
    event_type: OfferDecisionTimelineEventType = OfferDecisionTimelineEventType.CREATED
    actor: Optional[str] = None
    actor_type: OfferDecisionActorType = OfferDecisionActorType.SYSTEM
    description: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    workflow_automation_disabled: bool = True


class OfferDecisionEvidenceReference(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    reference_type: OfferDecisionEvidenceReferenceType
    reference_id: str
    display_name: str
    summary: Optional[str] = None
    source_collection: Optional[str] = None
    source_record_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    immutable_reference: bool = True
    metadata_only: bool = True


class OfferDecisionReason(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    offer_option_id: Optional[str] = None
    reason_category: OfferDecisionReasonCategory = OfferDecisionReasonCategory.MANUAL
    importance: OfferDecisionReasonImportance = OfferDecisionReasonImportance.MEDIUM
    text: str
    created_by: Optional[str] = None
    archived: bool = False
    ai_generated: bool = False
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    human_review_only: bool = True


class OfferDecisionAcknowledgement(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    acknowledged_by: str
    acknowledged_at: datetime = Field(default_factory=now_utc)
    acknowledgement_type: OfferDecisionAcknowledgementType = OfferDecisionAcknowledgementType.REVIEWED
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    human_review_only: bool = True


class OfferDecisionAuditSnapshot(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    snapshot_name: str
    explanation_ids: List[str] = Field(default_factory=list)
    timeline_event_ids: List[str] = Field(default_factory=list)
    evidence_reference_ids: List[str] = Field(default_factory=list)
    reason_ids: List[str] = Field(default_factory=list)
    acknowledgement_ids: List[str] = Field(default_factory=list)
    snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    immutable: bool = True
    metadata_only: bool = True
    human_review_only: bool = True


class OfferDecisionExplanationCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    decision_pack_id: str
    offer_option_id: Optional[str] = None
    title: str
    explanation_type: OfferDecisionExplanationType = OfferDecisionExplanationType.SUMMARY
    explanation_text: str
    finalized: bool = False
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExplanationUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    title: Optional[str] = None
    explanation_type: Optional[OfferDecisionExplanationType] = None
    explanation_text: Optional[str] = None
    finalized: Optional[bool] = None
    archived: Optional[bool] = None
    metadata_json: Optional[Dict[str, Any]] = None


class OfferDecisionTimelineEventCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    decision_pack_id: str
    offer_option_id: Optional[str] = None
    event_type: OfferDecisionTimelineEventType = OfferDecisionTimelineEventType.CREATED
    actor: Optional[str] = None
    actor_type: OfferDecisionActorType = OfferDecisionActorType.AGENCY
    description: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionReasonCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    decision_pack_id: str
    offer_option_id: Optional[str] = None
    reason_category: OfferDecisionReasonCategory = OfferDecisionReasonCategory.MANUAL
    importance: OfferDecisionReasonImportance = OfferDecisionReasonImportance.MEDIUM
    text: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionReasonUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    reason_category: Optional[OfferDecisionReasonCategory] = None
    importance: Optional[OfferDecisionReasonImportance] = None
    text: Optional[str] = None
    archived: Optional[bool] = None
    metadata_json: Optional[Dict[str, Any]] = None


class OfferDecisionAcknowledgementCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    decision_pack_id: str
    acknowledged_by: str
    acknowledgement_type: OfferDecisionAcknowledgementType = OfferDecisionAcknowledgementType.REVIEWED
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionAuditSnapshotCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    decision_pack_id: str
    snapshot_name: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportStatus(str, Enum):
    GENERATED = "generated"
    ARCHIVED = "archived"


class OfferDecisionExportSectionKey(str, Enum):
    DECISION_PACK = "decision_pack"
    OPTIONS = "options"
    EVIDENCE = "evidence"
    WARNINGS = "warnings"
    REVIEW_NOTES = "review_notes"
    EXPLANATIONS = "explanations"
    TIMELINE = "timeline"
    REASONS = "reasons"
    ACKNOWLEDGEMENTS = "acknowledgements"
    AUDIT_SNAPSHOTS = "audit_snapshots"


class OfferDecisionExportArtifactType(str, Enum):
    PDF_METADATA = "pdf_metadata"
    REVIEW_JSON_SNAPSHOT = "review_json_snapshot"


class OfferDecisionExportRecipientType(str, Enum):
    INTERNAL = "internal"
    CLIENT_REVIEW = "client_review"
    AGENCY_REVIEW = "agency_review"


class OfferDecisionExportAuditEventType(str, Enum):
    GENERATED = "generated"
    VIEWED = "viewed"
    RECIPIENT_DRAFT_CREATED = "recipient_draft_created"


class OfferDecisionExport(BaseDocument):
    agency_id: str
    decision_pack_id: str
    offer_workspace_id: str
    export_name: str
    export_status: OfferDecisionExportStatus = OfferDecisionExportStatus.GENERATED
    generated_by: Optional[str] = None
    generated_at: datetime = Field(default_factory=now_utc)
    section_count: int = 0
    artifact_count: int = 0
    recipient_draft_count: int = 0
    export_summary_json: Dict[str, Any] = Field(default_factory=dict)
    source_counts_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    pdf_export_metadata_enabled: bool = True
    automatic_sending_disabled: bool = True
    public_links_disabled: bool = True
    offer_price_mutation_disabled: bool = True
    provider_execution_disabled: bool = True
    booking_execution_disabled: bool = True
    ticket_emd_issuance_disabled: bool = True
    payment_invoice_settlement_disabled: bool = True


class OfferDecisionExportSection(BaseDocument):
    agency_id: str
    export_id: str
    decision_pack_id: str
    offer_workspace_id: str
    section_key: OfferDecisionExportSectionKey
    section_title: str
    section_order: int
    record_count: int = 0
    section_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportArtifact(BaseDocument):
    agency_id: str
    export_id: str
    decision_pack_id: str
    offer_workspace_id: str
    artifact_type: OfferDecisionExportArtifactType = OfferDecisionExportArtifactType.PDF_METADATA
    artifact_name: str
    filename: Optional[str] = None
    mime_type: str = "application/json"
    artifact_json: Dict[str, Any] = Field(default_factory=dict)
    file_generated: bool = False
    binary_storage_disabled: bool = True
    public_link_created: bool = False
    automatic_sending_disabled: bool = True
    metadata_only: bool = True


class OfferDecisionExportRecipientDraft(BaseDocument):
    agency_id: str
    export_id: str
    decision_pack_id: str
    offer_workspace_id: str
    recipient_type: OfferDecisionExportRecipientType = OfferDecisionExportRecipientType.INTERNAL
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    subject: str
    message_body: str
    delivery_status: str = "draft"
    sent_at: Optional[datetime] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    automatic_sending_disabled: bool = True
    public_links_disabled: bool = True
    metadata_only: bool = True


class OfferDecisionExportAuditEvent(BaseDocument):
    agency_id: str
    export_id: str
    decision_pack_id: str
    offer_workspace_id: str
    event_type: OfferDecisionExportAuditEventType = OfferDecisionExportAuditEventType.GENERATED
    actor: Optional[str] = None
    actor_type: OfferDecisionActorType = OfferDecisionActorType.SYSTEM
    description: str
    event_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    workflow_automation_disabled: bool = True


class OfferDecisionExportGenerateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    decision_pack_id: str
    export_name: Optional[str] = None
    include_recipient_draft: bool = False
    recipient_type: OfferDecisionExportRecipientType = OfferDecisionExportRecipientType.INTERNAL
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    subject: Optional[str] = None
    message_body: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportPreviewStatus(str, Enum):
    GENERATED = "generated"
    VALIDATED = "validated"
    SNAPSHOT_SAVED = "snapshot_saved"
    ARCHIVED = "archived"


class OfferDecisionExportPreviewSectionKey(str, Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    SELECTED_DECISION_PACK_OVERVIEW = "selected_decision_pack_overview"
    OPTION_COMPARISON = "option_comparison"
    ADVISOR_EVIDENCE = "advisor_evidence"
    WARNINGS = "warnings"
    HUMAN_REVIEW_NOTES = "human_review_notes"
    EXPLANATION_NARRATIVE = "explanation_narrative"
    DECISION_TIMELINE = "decision_timeline"
    ACKNOWLEDGEMENT_STATUS = "acknowledgement_status"
    EXPORT_ARTIFACT_METADATA = "export_artifact_metadata"
    RECIPIENT_DRAFT_METADATA = "recipient_draft_metadata"
    AUDIT_TRAIL = "audit_trail"


class OfferDecisionExportPreviewBlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    KEY_VALUE_TABLE = "key_value_table"
    WARNING_LIST = "warning_list"
    EVIDENCE_LIST = "evidence_list"
    TIMELINE_LIST = "timeline_list"
    RECIPIENT_DRAFT = "recipient_draft"
    ARTIFACT_REFERENCE = "artifact_reference"
    SAFETY_DISCLAIMER = "safety_disclaimer"


class OfferDecisionExportPreviewValidationKey(str, Enum):
    MISSING_DECISION_PACK = "missing_decision_pack"
    MISSING_EXPLANATION = "missing_explanation"
    MISSING_TIMELINE = "missing_timeline"
    MISSING_ACKNOWLEDGEMENTS = "missing_acknowledgements"
    MISSING_RECIPIENT_DRAFT = "missing_recipient_draft"
    MISSING_ARTIFACT_METADATA = "missing_artifact_metadata"
    MISSING_INTERNAL_REVIEWER = "missing_internal_reviewer"
    SAFETY_BOUNDARY_REMINDER = "safety_boundary_reminder"


class OfferDecisionExportPreviewValidationStatus(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    REMINDER = "reminder"


class OfferDecisionExportPreview(BaseDocument):
    agency_id: str
    export_id: str
    decision_pack_id: Optional[str] = None
    explanation_id: Optional[str] = None
    offer_workspace_id: Optional[str] = None
    source_artifact_ids: List[str] = Field(default_factory=list)
    preview_status: OfferDecisionExportPreviewStatus = OfferDecisionExportPreviewStatus.GENERATED
    render_profile: str = "internal_review"
    template_profile: str = "metadata_preview"
    generated_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    generated_at: datetime = Field(default_factory=now_utc)
    reviewed_at: Optional[datetime] = None
    section_count: int = 0
    block_count: int = 0
    validation_count: int = 0
    snapshot_count: int = 0
    preview_summary_json: Dict[str, Any] = Field(default_factory=dict)
    source_counts_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    metadata_only_rendering_enabled: bool = True
    automatic_sending_disabled: bool = True
    public_links_disabled: bool = True
    real_pdf_delivery_disabled: bool = True
    offer_price_mutation_disabled: bool = True
    provider_execution_disabled: bool = True
    booking_execution_disabled: bool = True
    ticket_emd_issuance_disabled: bool = True
    payment_invoice_settlement_disabled: bool = True


class OfferDecisionExportPreviewSection(BaseDocument):
    agency_id: str
    preview_id: str
    export_id: str
    decision_pack_id: Optional[str] = None
    section_key: OfferDecisionExportPreviewSectionKey
    section_title: str
    section_order: int
    block_count: int = 0
    section_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportPreviewBlock(BaseDocument):
    agency_id: str
    preview_id: str
    section_id: str
    export_id: str
    decision_pack_id: Optional[str] = None
    section_key: OfferDecisionExportPreviewSectionKey
    block_type: OfferDecisionExportPreviewBlockType
    block_title: Optional[str] = None
    block_order: int
    block_json: Dict[str, Any] = Field(default_factory=dict)
    source_record_type: Optional[str] = None
    source_record_id: Optional[str] = None
    metadata_only: bool = True


class OfferDecisionExportPreviewValidation(BaseDocument):
    agency_id: str
    preview_id: str
    export_id: str
    decision_pack_id: Optional[str] = None
    validation_key: OfferDecisionExportPreviewValidationKey
    validation_status: OfferDecisionExportPreviewValidationStatus = OfferDecisionExportPreviewValidationStatus.PASS
    severity: str = "info"
    message: str
    checked_by: Optional[str] = None
    checked_at: datetime = Field(default_factory=now_utc)
    validation_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportPreviewSnapshot(BaseDocument):
    agency_id: str
    preview_id: str
    export_id: str
    decision_pack_id: Optional[str] = None
    snapshot_name: str
    snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    saved_by: Optional[str] = None
    saved_at: datetime = Field(default_factory=now_utc)
    immutable: bool = True
    metadata_only: bool = True


class OfferDecisionExportPreviewGenerateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    export_id: str
    render_profile: str = "internal_review"
    template_profile: str = "metadata_preview"
    reviewed_by: Optional[str] = None
    source_artifact_ids: List[str] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportPreviewValidateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    internal_reviewer: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportPreviewSnapshotCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_name: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportApprovalStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class OfferDecisionExportApprovalCheckpointType(str, Enum):
    PREVIEW_REVIEW = "preview_review"
    ARTIFACT_METADATA_REVIEW = "artifact_metadata_review"
    RECIPIENT_DRAFT_REVIEW = "recipient_draft_review"
    SAFETY_BOUNDARY_REVIEW = "safety_boundary_review"
    INTERNAL_APPROVAL = "internal_approval"
    MANUAL_RELEASE_READINESS = "manual_release_readiness"


class OfferDecisionExportApprovalCheckpointStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    WAIVED = "waived"


class OfferDecisionExportReleaseReadinessStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready_for_manual_release"
    BLOCKED = "blocked"
    SUPERSEDED = "superseded"


class OfferDecisionExportReleaseHoldType(str, Enum):
    MISSING_APPROVAL = "missing_approval"
    MISSING_PREVIEW_SNAPSHOT = "missing_preview_snapshot"
    MISSING_VALIDATION = "missing_validation"
    SAFETY_BOUNDARY = "safety_boundary"
    MANUAL_REVIEW = "manual_review"
    OTHER = "other"


class OfferDecisionExportReleaseHoldStatus(str, Enum):
    ACTIVE = "active"
    RELEASED = "released"


class OfferDecisionExportApproval(BaseDocument):
    agency_id: str
    preview_id: str
    export_id: str
    decision_pack_id: Optional[str] = None
    approval_name: str
    approval_status: OfferDecisionExportApprovalStatus = OfferDecisionExportApprovalStatus.DRAFT
    requested_by: Optional[str] = None
    assigned_reviewer: Optional[str] = None
    status_updated_by: Optional[str] = None
    status_updated_at: Optional[datetime] = None
    status_reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    checkpoint_count: int = 0
    readiness_count: int = 0
    approval_summary_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    human_approval_required_enabled: bool = True
    automatic_sending_disabled: bool = True
    public_links_disabled: bool = True
    real_pdf_delivery_disabled: bool = True
    offer_price_mutation_disabled: bool = True
    provider_execution_disabled: bool = True
    booking_execution_disabled: bool = True
    ticket_emd_issuance_disabled: bool = True
    payment_invoice_settlement_disabled: bool = True


class OfferDecisionExportApprovalCheckpoint(BaseDocument):
    agency_id: str
    approval_id: str
    preview_id: str
    export_id: str
    decision_pack_id: Optional[str] = None
    checkpoint_type: OfferDecisionExportApprovalCheckpointType = OfferDecisionExportApprovalCheckpointType.PREVIEW_REVIEW
    checkpoint_status: OfferDecisionExportApprovalCheckpointStatus = OfferDecisionExportApprovalCheckpointStatus.PENDING
    checkpoint_title: str
    notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    sequence_order: int = 1
    checkpoint_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportReleaseReadiness(BaseDocument):
    agency_id: str
    preview_id: str
    export_id: str
    decision_pack_id: Optional[str] = None
    approval_id: Optional[str] = None
    readiness_name: str
    readiness_status: OfferDecisionExportReleaseReadinessStatus = OfferDecisionExportReleaseReadinessStatus.DRAFT
    prepared_by: Optional[str] = None
    prepared_at: datetime = Field(default_factory=now_utc)
    ready_for_manual_release: bool = False
    human_approval_required_enabled: bool = True
    active_hold_count: int = 0
    released_hold_count: int = 0
    snapshot_count: int = 0
    readiness_summary_json: Dict[str, Any] = Field(default_factory=dict)
    source_counts_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    automatic_sending_disabled: bool = True
    public_links_disabled: bool = True
    real_pdf_delivery_disabled: bool = True
    offer_price_mutation_disabled: bool = True
    provider_execution_disabled: bool = True
    booking_execution_disabled: bool = True
    ticket_emd_issuance_disabled: bool = True
    payment_invoice_settlement_disabled: bool = True


class OfferDecisionExportReleaseHold(BaseDocument):
    agency_id: str
    readiness_id: str
    approval_id: Optional[str] = None
    preview_id: str
    export_id: str
    decision_pack_id: Optional[str] = None
    hold_type: OfferDecisionExportReleaseHoldType = OfferDecisionExportReleaseHoldType.MANUAL_REVIEW
    hold_status: OfferDecisionExportReleaseHoldStatus = OfferDecisionExportReleaseHoldStatus.ACTIVE
    severity: str = "medium"
    title: str
    reason: str
    created_by: Optional[str] = None
    released_by: Optional[str] = None
    released_at: Optional[datetime] = None
    release_notes: Optional[str] = None
    hold_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    automatic_sending_disabled: bool = True
    public_links_disabled: bool = True


class OfferDecisionExportReleaseSnapshot(BaseDocument):
    agency_id: str
    readiness_id: str
    approval_id: Optional[str] = None
    preview_id: str
    export_id: str
    decision_pack_id: Optional[str] = None
    snapshot_name: str
    snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    saved_by: Optional[str] = None
    saved_at: datetime = Field(default_factory=now_utc)
    immutable: bool = True
    metadata_only: bool = True


class OfferDecisionExportApprovalCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    preview_id: str
    approval_name: Optional[str] = None
    assigned_reviewer: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportApprovalCheckpointCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    checkpoint_type: OfferDecisionExportApprovalCheckpointType = OfferDecisionExportApprovalCheckpointType.PREVIEW_REVIEW
    checkpoint_status: OfferDecisionExportApprovalCheckpointStatus = OfferDecisionExportApprovalCheckpointStatus.PENDING
    checkpoint_title: str
    notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    checkpoint_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportApprovalStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    approval_status: OfferDecisionExportApprovalStatus
    status_reason: Optional[str] = None
    status_updated_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportReleaseReadinessCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    preview_id: Optional[str] = None
    approval_id: Optional[str] = None
    readiness_name: Optional[str] = None
    prepared_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportReleaseHoldCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    hold_type: OfferDecisionExportReleaseHoldType = OfferDecisionExportReleaseHoldType.MANUAL_REVIEW
    severity: str = "medium"
    title: str
    reason: str
    hold_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportReleaseHoldReleaseRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    released_by: Optional[str] = None
    release_notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportReleaseSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_name: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryHandoffStatus(str, Enum):
    DRAFT = "draft"
    PREPARED = "prepared"
    HELD = "held"
    HANDED_TO_HUMAN = "handed_to_human"
    CANCELLED = "cancelled"


class OfferDecisionExportDeliveryMethod(str, Enum):
    MANUAL_EMAIL = "manual_email"
    MANUAL_PORTAL_UPLOAD = "manual_portal_upload"
    MANUAL_PRINT = "manual_print"
    MANUAL_OTHER = "manual_other"


class OfferDecisionExportDeliveryRecipientType(str, Enum):
    CLIENT = "client"
    PASSENGER = "passenger"
    CORPORATE_CONTACT = "corporate_contact"
    AGENCY_USER = "agency_user"
    EXTERNAL_CONTACT = "external_contact"
    OTHER = "other"


class OfferDecisionExportDeliveryRecipientStatus(str, Enum):
    PENDING_MANUAL_ACTION = "pending_manual_action"
    MANUALLY_COMPLETED = "manually_completed"
    SKIPPED = "skipped"
    HELD = "held"


class OfferDecisionExportDeliveryAttachmentFileType(str, Enum):
    PDF_METADATA = "pdf_metadata"
    JSON_METADATA = "json_metadata"
    TEXT_METADATA = "text_metadata"
    OTHER_METADATA = "other_metadata"


class OfferDecisionExportDeliveryAttachmentSourceType(str, Enum):
    EXPORT_ARTIFACT_METADATA = "export_artifact_metadata"
    PREVIEW_METADATA = "preview_metadata"
    MANUALLY_DESCRIBED_METADATA = "manually_described_metadata"


class OfferDecisionExportDeliveryInstructionType(str, Enum):
    EMAIL_COPY = "email_copy"
    PORTAL_UPLOAD_NOTE = "portal_upload_note"
    PRINT_NOTE = "print_note"
    COMPLIANCE_NOTE = "compliance_note"
    INTERNAL_NOTE = "internal_note"
    OTHER = "other"


class OfferDecisionExportDeliverySnapshotType(str, Enum):
    PREPARED = "prepared"
    HANDED_TO_HUMAN = "handed_to_human"
    CANCELLED = "cancelled"
    HELD = "held"


class OfferDecisionExportDeliveryHandoff(BaseDocument):
    agency_id: str
    export_id: str
    preview_id: Optional[str] = None
    approval_id: Optional[str] = None
    release_readiness_id: Optional[str] = None
    title: str
    status: OfferDecisionExportDeliveryHandoffStatus = OfferDecisionExportDeliveryHandoffStatus.DRAFT
    delivery_method: OfferDecisionExportDeliveryMethod = OfferDecisionExportDeliveryMethod.MANUAL_EMAIL
    recipient_count: int = 0
    attachment_count: int = 0
    instruction_count: int = 0
    checklist_count: int = 0
    snapshot_count: int = 0
    safety_summary: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None
    status_reason: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    manual_delivery_only_enabled: bool = True
    automatic_sending_disabled: bool = True
    sms_sending_disabled: bool = True
    public_links_disabled: bool = True
    real_pdf_delivery_disabled: bool = True
    offer_price_mutation_disabled: bool = True
    provider_execution_disabled: bool = True
    booking_execution_disabled: bool = True
    ticket_emd_issuance_disabled: bool = True
    payment_invoice_settlement_disabled: bool = True


class OfferDecisionExportDeliveryRecipient(BaseDocument):
    agency_id: str
    handoff_id: str
    recipient_type: OfferDecisionExportDeliveryRecipientType = OfferDecisionExportDeliveryRecipientType.CLIENT
    display_name: str
    email_metadata: Optional[str] = None
    phone_metadata: Optional[str] = None
    delivery_method: OfferDecisionExportDeliveryMethod = OfferDecisionExportDeliveryMethod.MANUAL_EMAIL
    delivery_status: OfferDecisionExportDeliveryRecipientStatus = OfferDecisionExportDeliveryRecipientStatus.PENDING_MANUAL_ACTION
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    automatic_sending_disabled: bool = True
    sms_sending_disabled: bool = True


class OfferDecisionExportDeliveryAttachment(BaseDocument):
    agency_id: str
    handoff_id: str
    artifact_id: Optional[str] = None
    preview_id: Optional[str] = None
    filename: str
    file_type: OfferDecisionExportDeliveryAttachmentFileType = OfferDecisionExportDeliveryAttachmentFileType.PDF_METADATA
    source_type: OfferDecisionExportDeliveryAttachmentSourceType = OfferDecisionExportDeliveryAttachmentSourceType.MANUALLY_DESCRIBED_METADATA
    size_label: Optional[str] = None
    storage_reference_metadata: Optional[str] = None
    public_link_created: bool = False
    real_file_delivered: bool = False
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportDeliveryInstruction(BaseDocument):
    agency_id: str
    handoff_id: str
    instruction_type: OfferDecisionExportDeliveryInstructionType = OfferDecisionExportDeliveryInstructionType.INTERNAL_NOTE
    title: str
    body: str
    required: bool = True
    completed: bool = False
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportDeliverySnapshot(BaseDocument):
    agency_id: str
    handoff_id: str
    snapshot_type: OfferDecisionExportDeliverySnapshotType = OfferDecisionExportDeliverySnapshotType.PREPARED
    payload: Dict[str, Any] = Field(default_factory=dict)
    immutable: bool = True
    created_by: Optional[str] = None
    metadata_only: bool = True


class OfferDecisionExportDeliveryHandoffCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    export_id: str
    preview_id: Optional[str] = None
    approval_id: Optional[str] = None
    release_readiness_id: Optional[str] = None
    title: Optional[str] = None
    delivery_method: OfferDecisionExportDeliveryMethod = OfferDecisionExportDeliveryMethod.MANUAL_EMAIL
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryHandoffStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: OfferDecisionExportDeliveryHandoffStatus
    status_reason: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryRecipientCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    recipient_type: OfferDecisionExportDeliveryRecipientType = OfferDecisionExportDeliveryRecipientType.CLIENT
    display_name: str
    email_metadata: Optional[str] = None
    phone_metadata: Optional[str] = None
    delivery_method: OfferDecisionExportDeliveryMethod = OfferDecisionExportDeliveryMethod.MANUAL_EMAIL
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryRecipientStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    delivery_status: OfferDecisionExportDeliveryRecipientStatus
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryAttachmentCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    artifact_id: Optional[str] = None
    preview_id: Optional[str] = None
    filename: str
    file_type: OfferDecisionExportDeliveryAttachmentFileType = OfferDecisionExportDeliveryAttachmentFileType.PDF_METADATA
    source_type: OfferDecisionExportDeliveryAttachmentSourceType = OfferDecisionExportDeliveryAttachmentSourceType.MANUALLY_DESCRIBED_METADATA
    size_label: Optional[str] = None
    storage_reference_metadata: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryInstructionCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    instruction_type: OfferDecisionExportDeliveryInstructionType = OfferDecisionExportDeliveryInstructionType.INTERNAL_NOTE
    title: str
    body: str
    required: bool = True
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryInstructionCompletionRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    completed: bool = True
    completed_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliverySnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_type: OfferDecisionExportDeliverySnapshotType = OfferDecisionExportDeliverySnapshotType.PREPARED
    created_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryOutcomeStatus(str, Enum):
    PENDING = "pending"
    MANUALLY_SENT = "manually_sent"
    FAILED = "failed"
    CORRECTED = "corrected"
    RESENT = "resent"
    ACKNOWLEDGED = "acknowledged"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class OfferDecisionExportDeliveryOutcomeEventType(str, Enum):
    SENT_RECORDED = "sent_recorded"
    FAILED_RECORDED = "failed_recorded"
    CORRECTION_RECORDED = "correction_recorded"
    RESEND_RECORDED = "resend_recorded"
    ACKNOWLEDGEMENT_RECORDED = "acknowledgement_recorded"
    ISSUE_RECORDED = "issue_recorded"
    ISSUE_RESOLVED = "issue_resolved"
    CLOSED = "closed"


class OfferDecisionExportDeliveryReceiptType(str, Enum):
    CLIENT_ACKNOWLEDGEMENT = "client_acknowledgement"
    INTERNAL_CONFIRMATION = "internal_confirmation"
    EXTERNAL_REFERENCE = "external_reference"
    MANUAL_NOTE = "manual_note"


class OfferDecisionExportDeliveryIssueType(str, Enum):
    WRONG_RECIPIENT = "wrong_recipient"
    MISSING_ATTACHMENT = "missing_attachment"
    OUTDATED_EXPORT = "outdated_export"
    CLIENT_CORRECTION_REQUESTED = "client_correction_requested"
    DELIVERY_FAILED = "delivery_failed"
    OTHER = "other"


class OfferDecisionExportDeliveryIssueStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    HELD = "held"


class OfferDecisionExportDeliveryActorType(str, Enum):
    AGENCY_USER = "agency_user"
    PLATFORM_USER = "platform_user"
    EXTERNAL_RECIPIENT = "external_recipient"
    SYSTEM = "system"


class OfferDecisionExportDeliveryOutcomeSnapshotType(str, Enum):
    OUTCOME_RECORDED = "outcome_recorded"
    ACKNOWLEDGED = "acknowledged"
    ISSUE_REVIEW = "issue_review"
    CLOSED = "closed"
    MANUAL = "manual"


class OfferDecisionExportDeliveryOutcome(BaseDocument):
    agency_id: str
    handoff_id: str
    export_id: Optional[str] = None
    preview_id: Optional[str] = None
    release_readiness_id: Optional[str] = None
    title: str
    outcome_status: OfferDecisionExportDeliveryOutcomeStatus = OfferDecisionExportDeliveryOutcomeStatus.PENDING
    status_reason: Optional[str] = None
    actor_type: OfferDecisionExportDeliveryActorType = OfferDecisionExportDeliveryActorType.AGENCY_USER
    recorded_by: Optional[str] = None
    event_count: int = 0
    receipt_count: int = 0
    issue_count: int = 0
    unresolved_issue_count: int = 0
    snapshot_count: int = 0
    outcome_summary: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    manual_tracking_only_enabled: bool = True
    automatic_sending_disabled: bool = True
    sms_sending_disabled: bool = True
    public_links_disabled: bool = True
    real_pdf_delivery_disabled: bool = True
    provider_execution_disabled: bool = True
    booking_execution_disabled: bool = True
    pnr_mutation_disabled: bool = True
    ticket_emd_issuance_disabled: bool = True
    payment_invoice_settlement_disabled: bool = True


class OfferDecisionExportDeliveryOutcomeEvent(BaseDocument):
    agency_id: str
    outcome_id: str
    handoff_id: str
    event_type: OfferDecisionExportDeliveryOutcomeEventType = OfferDecisionExportDeliveryOutcomeEventType.SENT_RECORDED
    actor_type: OfferDecisionExportDeliveryActorType = OfferDecisionExportDeliveryActorType.AGENCY_USER
    actor_label: Optional[str] = None
    event_title: Optional[str] = None
    event_note: Optional[str] = None
    occurred_at: datetime = Field(default_factory=now_utc)
    event_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    automatic_sending_disabled: bool = True
    provider_execution_disabled: bool = True


class OfferDecisionExportDeliveryReceipt(BaseDocument):
    agency_id: str
    outcome_id: str
    handoff_id: str
    receipt_type: OfferDecisionExportDeliveryReceiptType = OfferDecisionExportDeliveryReceiptType.MANUAL_NOTE
    reference_label: Optional[str] = None
    received_from: Optional[str] = None
    received_at: Optional[datetime] = None
    notes: Optional[str] = None
    external_reference_metadata: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    automatic_sending_disabled: bool = True
    public_links_disabled: bool = True


class OfferDecisionExportDeliveryIssue(BaseDocument):
    agency_id: str
    outcome_id: str
    handoff_id: str
    issue_type: OfferDecisionExportDeliveryIssueType = OfferDecisionExportDeliveryIssueType.OTHER
    issue_status: OfferDecisionExportDeliveryIssueStatus = OfferDecisionExportDeliveryIssueStatus.OPEN
    severity: str = "medium"
    title: str
    description: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    manual_tracking_only_enabled: bool = True


class OfferDecisionExportDeliveryOutcomeSnapshot(BaseDocument):
    agency_id: str
    outcome_id: str
    handoff_id: str
    snapshot_type: OfferDecisionExportDeliveryOutcomeSnapshotType = OfferDecisionExportDeliveryOutcomeSnapshotType.OUTCOME_RECORDED
    payload: Dict[str, Any] = Field(default_factory=dict)
    immutable: bool = True
    created_by: Optional[str] = None
    metadata_only: bool = True


class OfferDecisionExportDeliveryOutcomeCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    handoff_id: str
    title: Optional[str] = None
    outcome_status: OfferDecisionExportDeliveryOutcomeStatus = OfferDecisionExportDeliveryOutcomeStatus.PENDING
    actor_type: OfferDecisionExportDeliveryActorType = OfferDecisionExportDeliveryActorType.AGENCY_USER
    recorded_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryOutcomeUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    outcome_status: OfferDecisionExportDeliveryOutcomeStatus
    status_reason: Optional[str] = None
    actor_type: OfferDecisionExportDeliveryActorType = OfferDecisionExportDeliveryActorType.AGENCY_USER
    recorded_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryOutcomeEventCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    event_type: OfferDecisionExportDeliveryOutcomeEventType = OfferDecisionExportDeliveryOutcomeEventType.SENT_RECORDED
    actor_type: OfferDecisionExportDeliveryActorType = OfferDecisionExportDeliveryActorType.AGENCY_USER
    actor_label: Optional[str] = None
    event_title: Optional[str] = None
    event_note: Optional[str] = None
    occurred_at: Optional[datetime] = None
    event_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryReceiptCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    receipt_type: OfferDecisionExportDeliveryReceiptType = OfferDecisionExportDeliveryReceiptType.MANUAL_NOTE
    reference_label: Optional[str] = None
    received_from: Optional[str] = None
    received_at: Optional[datetime] = None
    notes: Optional[str] = None
    external_reference_metadata: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryIssueCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    issue_type: OfferDecisionExportDeliveryIssueType = OfferDecisionExportDeliveryIssueType.OTHER
    severity: str = "medium"
    title: str
    description: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryIssueUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    issue_status: OfferDecisionExportDeliveryIssueStatus
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportDeliveryOutcomeSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_type: OfferDecisionExportDeliveryOutcomeSnapshotType = OfferDecisionExportDeliveryOutcomeSnapshotType.OUTCOME_RECORDED
    created_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportAuditReviewStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    HELD = "held"
    CANCELLED = "cancelled"


class OfferDecisionExportAuditReviewScope(str, Enum):
    FULL_LIFECYCLE = "full_lifecycle"
    EXPORT_ONLY = "export_only"
    DELIVERY_ONLY = "delivery_only"
    OUTCOME_ONLY = "outcome_only"


class OfferDecisionExportAuditFindingType(str, Enum):
    MISSING_DECISION_PACK = "missing_decision_pack"
    MISSING_EXPLANATION = "missing_explanation"
    MISSING_EXPORT = "missing_export"
    MISSING_PREVIEW = "missing_preview"
    MISSING_RELEASE_READINESS = "missing_release_readiness"
    MISSING_HANDOFF = "missing_handoff"
    MISSING_OUTCOME = "missing_outcome"
    UNRESOLVED_DELIVERY_ISSUE = "unresolved_delivery_issue"
    MISSING_IMMUTABLE_SNAPSHOT = "missing_immutable_snapshot"
    METADATA_GAP = "metadata_gap"
    OTHER = "other"


class OfferDecisionExportAuditFindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OfferDecisionExportAuditFindingStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"


class OfferDecisionExportAuditChecklistStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


class OfferDecisionExportAuditReviewSnapshotType(str, Enum):
    REVIEW_CREATED = "review_created"
    CHECKLIST_REVIEW = "checklist_review"
    FINAL_REVIEW = "final_review"
    MANUAL = "manual"


class OfferDecisionExportAuditReview(BaseDocument):
    agency_id: str
    review_scope: OfferDecisionExportAuditReviewScope = OfferDecisionExportAuditReviewScope.FULL_LIFECYCLE
    review_status: OfferDecisionExportAuditReviewStatus = OfferDecisionExportAuditReviewStatus.DRAFT
    title: str
    decision_pack_id: Optional[str] = None
    explanation_id: Optional[str] = None
    export_id: Optional[str] = None
    preview_id: Optional[str] = None
    release_readiness_id: Optional[str] = None
    handoff_id: Optional[str] = None
    outcome_id: Optional[str] = None
    finding_count: int = 0
    unresolved_finding_count: int = 0
    checklist_count: int = 0
    passed_checklist_count: int = 0
    snapshot_count: int = 0
    completion_score: int = 0
    coverage_summary: Dict[str, Any] = Field(default_factory=dict)
    reviewed_by: Optional[str] = None
    status_reason: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    audit_review_only_enabled: bool = True
    automatic_sending_disabled: bool = True
    sms_sending_disabled: bool = True
    public_links_disabled: bool = True
    real_pdf_delivery_disabled: bool = True
    offer_price_mutation_disabled: bool = True
    automatic_recommendation_disabled: bool = True
    provider_execution_disabled: bool = True
    booking_execution_disabled: bool = True
    pnr_mutation_disabled: bool = True
    ticket_emd_issuance_disabled: bool = True
    payment_invoice_settlement_disabled: bool = True


class OfferDecisionExportAuditReviewFinding(BaseDocument):
    agency_id: str
    review_id: str
    finding_type: OfferDecisionExportAuditFindingType = OfferDecisionExportAuditFindingType.OTHER
    severity: OfferDecisionExportAuditFindingSeverity = OfferDecisionExportAuditFindingSeverity.MEDIUM
    finding_status: OfferDecisionExportAuditFindingStatus = OfferDecisionExportAuditFindingStatus.OPEN
    title: str
    description: Optional[str] = None
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportAuditReviewChecklistItem(BaseDocument):
    agency_id: str
    review_id: str
    item_key: str
    label: str
    item_status: OfferDecisionExportAuditChecklistStatus = OfferDecisionExportAuditChecklistStatus.PENDING
    required: bool = True
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportAuditReviewSnapshot(BaseDocument):
    agency_id: str
    review_id: str
    snapshot_type: OfferDecisionExportAuditReviewSnapshotType = OfferDecisionExportAuditReviewSnapshotType.REVIEW_CREATED
    payload: Dict[str, Any] = Field(default_factory=dict)
    immutable: bool = True
    created_by: Optional[str] = None
    metadata_only: bool = True


class OfferDecisionExportAuditReviewCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    review_scope: OfferDecisionExportAuditReviewScope = OfferDecisionExportAuditReviewScope.FULL_LIFECYCLE
    title: Optional[str] = None
    export_id: Optional[str] = None
    preview_id: Optional[str] = None
    release_readiness_id: Optional[str] = None
    handoff_id: Optional[str] = None
    outcome_id: Optional[str] = None
    reviewed_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportAuditReviewStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    review_status: OfferDecisionExportAuditReviewStatus
    status_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportAuditReviewFindingCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    finding_type: OfferDecisionExportAuditFindingType = OfferDecisionExportAuditFindingType.OTHER
    severity: OfferDecisionExportAuditFindingSeverity = OfferDecisionExportAuditFindingSeverity.MEDIUM
    title: str
    description: Optional[str] = None
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportAuditReviewFindingUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    finding_status: OfferDecisionExportAuditFindingStatus
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportAuditReviewChecklistItemCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    item_key: str
    label: str
    item_status: OfferDecisionExportAuditChecklistStatus = OfferDecisionExportAuditChecklistStatus.PENDING
    required: bool = True
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportAuditReviewChecklistItemUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    item_status: OfferDecisionExportAuditChecklistStatus
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportAuditReviewSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_type: OfferDecisionExportAuditReviewSnapshotType = OfferDecisionExportAuditReviewSnapshotType.REVIEW_CREATED
    created_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportGovernanceScope(str, Enum):
    EXPORT_LIFECYCLE = "export_lifecycle"
    AUDIT_REVIEW = "audit_review"
    DELIVERY_OUTCOME = "delivery_outcome"
    RETENTION = "retention"
    LEGAL_BASIS = "legal_basis"
    ARCHIVE = "archive"


class OfferDecisionExportGovernanceStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    REVIEW_NEEDED = "review_needed"
    HELD = "held"
    ARCHIVED_METADATA_ONLY = "archived_metadata_only"
    CANCELLED = "cancelled"


class OfferDecisionExportGovernanceRuleType(str, Enum):
    RETENTION = "retention"
    LEGAL_BASIS = "legal_basis"
    ARCHIVE = "archive"
    ACCESS_REVIEW = "access_review"
    EXCEPTION_REVIEW = "exception_review"
    SNAPSHOT_COVERAGE = "snapshot_coverage"
    OTHER = "other"


class OfferDecisionExportGovernanceRuleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class OfferDecisionExportRetentionAction(str, Enum):
    RETAIN = "retain"
    REVIEW = "review"
    HOLD = "hold"
    ARCHIVE_METADATA_ONLY = "archive_metadata_only"


class OfferDecisionExportLegalBasisType(str, Enum):
    CONTRACT = "contract"
    CLIENT_CONSENT = "client_consent"
    LEGAL_OBLIGATION = "legal_obligation"
    LEGITIMATE_INTEREST = "legitimate_interest"
    AGENCY_POLICY = "agency_policy"
    OTHER = "other"


class OfferDecisionExportArchiveStatusType(str, Enum):
    NOT_ARCHIVED = "not_archived"
    ELIGIBLE_FOR_METADATA_ARCHIVE = "eligible_for_metadata_archive"
    ARCHIVED_METADATA_ONLY = "archived_metadata_only"
    HOLD = "hold"
    EXCEPTION_PENDING = "exception_pending"


class OfferDecisionExportGovernanceExceptionType(str, Enum):
    RETENTION_EXCEPTION = "retention_exception"
    LEGAL_BASIS_GAP = "legal_basis_gap"
    ARCHIVE_HOLD = "archive_hold"
    POLICY_OVERRIDE = "policy_override"
    SNAPSHOT_COVERAGE_GAP = "snapshot_coverage_gap"
    OTHER = "other"


class OfferDecisionExportGovernanceExceptionStatus(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    RESOLVED = "resolved"
    WAIVED = "waived"


class OfferDecisionExportGovernanceSnapshotType(str, Enum):
    GOVERNANCE_CREATED = "governance_created"
    POLICY_REVIEW = "policy_review"
    ARCHIVE_REVIEW = "archive_review"
    LEGAL_REVIEW = "legal_review"
    MANUAL = "manual"


class OfferDecisionExportGovernanceRecord(BaseDocument):
    agency_id: str
    governance_scope: OfferDecisionExportGovernanceScope = OfferDecisionExportGovernanceScope.EXPORT_LIFECYCLE
    governance_status: OfferDecisionExportGovernanceStatus = OfferDecisionExportGovernanceStatus.DRAFT
    title: str
    export_id: Optional[str] = None
    audit_review_id: Optional[str] = None
    decision_pack_id: Optional[str] = None
    outcome_id: Optional[str] = None
    owner_label: Optional[str] = None
    policy_summary_json: Dict[str, Any] = Field(default_factory=dict)
    rule_count: int = 0
    retention_policy_count: int = 0
    legal_basis_count: int = 0
    archive_status_count: int = 0
    exception_count: int = 0
    open_exception_count: int = 0
    snapshot_count: int = 0
    status_reason: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    governance_only_enabled: bool = True
    automatic_sending_disabled: bool = True
    sms_sending_disabled: bool = True
    public_links_disabled: bool = True
    real_pdf_delivery_disabled: bool = True
    offer_mutation_disabled: bool = True
    price_mutation_disabled: bool = True
    recommendation_disabled: bool = True
    provider_execution_disabled: bool = True
    booking_execution_disabled: bool = True
    pnr_mutation_disabled: bool = True
    ticketing_disabled: bool = True
    emd_issuance_disabled: bool = True
    payment_disabled: bool = True
    invoice_disabled: bool = True
    settlement_disabled: bool = True
    scraping_disabled: bool = True
    external_ai_disabled: bool = True


class OfferDecisionExportGovernanceRule(BaseDocument):
    agency_id: str
    governance_record_id: Optional[str] = None
    rule_type: OfferDecisionExportGovernanceRuleType = OfferDecisionExportGovernanceRuleType.OTHER
    rule_status: OfferDecisionExportGovernanceRuleStatus = OfferDecisionExportGovernanceRuleStatus.DRAFT
    rule_name: str
    rule_text: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportRetentionPolicy(BaseDocument):
    agency_id: str
    governance_record_id: Optional[str] = None
    policy_name: str
    retention_period_days: int = 365
    retention_action: OfferDecisionExportRetentionAction = OfferDecisionExportRetentionAction.REVIEW
    review_required: bool = True
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    destructive_delete_disabled: bool = True


class OfferDecisionExportLegalBasis(BaseDocument):
    agency_id: str
    governance_record_id: Optional[str] = None
    basis_type: OfferDecisionExportLegalBasisType = OfferDecisionExportLegalBasisType.OTHER
    basis_label: str
    notes: Optional[str] = None
    evidence_reference_metadata: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportArchiveStatus(BaseDocument):
    agency_id: str
    governance_record_id: Optional[str] = None
    export_id: Optional[str] = None
    archive_status: OfferDecisionExportArchiveStatusType = OfferDecisionExportArchiveStatusType.NOT_ARCHIVED
    status_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    archive_reference_metadata: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    real_archive_execution_disabled: bool = True


class OfferDecisionExportGovernanceException(BaseDocument):
    agency_id: str
    governance_record_id: Optional[str] = None
    exception_type: OfferDecisionExportGovernanceExceptionType = OfferDecisionExportGovernanceExceptionType.OTHER
    exception_status: OfferDecisionExportGovernanceExceptionStatus = OfferDecisionExportGovernanceExceptionStatus.OPEN
    severity: str = "medium"
    title: str
    description: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportGovernanceSnapshot(BaseDocument):
    agency_id: str
    governance_record_id: str
    snapshot_type: OfferDecisionExportGovernanceSnapshotType = OfferDecisionExportGovernanceSnapshotType.GOVERNANCE_CREATED
    payload: Dict[str, Any] = Field(default_factory=dict)
    immutable: bool = True
    created_by: Optional[str] = None
    metadata_only: bool = True


class OfferDecisionExportGovernanceRecordCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    governance_scope: OfferDecisionExportGovernanceScope = OfferDecisionExportGovernanceScope.EXPORT_LIFECYCLE
    title: Optional[str] = None
    export_id: Optional[str] = None
    audit_review_id: Optional[str] = None
    outcome_id: Optional[str] = None
    owner_label: Optional[str] = None
    policy_summary_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportGovernanceRecordUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    governance_status: OfferDecisionExportGovernanceStatus
    status_reason: Optional[str] = None
    owner_label: Optional[str] = None
    policy_summary_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportGovernanceRuleCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rule_type: OfferDecisionExportGovernanceRuleType = OfferDecisionExportGovernanceRuleType.OTHER
    rule_status: OfferDecisionExportGovernanceRuleStatus = OfferDecisionExportGovernanceRuleStatus.DRAFT
    rule_name: str
    rule_text: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportGovernanceRuleUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rule_status: OfferDecisionExportGovernanceRuleStatus
    rule_text: Optional[str] = None
    effective_to: Optional[datetime] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportRetentionPolicyCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    policy_name: str
    retention_period_days: int = 365
    retention_action: OfferDecisionExportRetentionAction = OfferDecisionExportRetentionAction.REVIEW
    review_required: bool = True
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportRetentionPolicyUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    retention_action: OfferDecisionExportRetentionAction
    review_required: bool = True
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportLegalBasisCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    basis_type: OfferDecisionExportLegalBasisType = OfferDecisionExportLegalBasisType.OTHER
    basis_label: str
    notes: Optional[str] = None
    evidence_reference_metadata: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportLegalBasisUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    notes: Optional[str] = None
    evidence_reference_metadata: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportArchiveStatusCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    archive_status: OfferDecisionExportArchiveStatusType = OfferDecisionExportArchiveStatusType.NOT_ARCHIVED
    status_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    archive_reference_metadata: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportArchiveStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    archive_status: OfferDecisionExportArchiveStatusType
    status_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    archive_reference_metadata: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportGovernanceExceptionCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    exception_type: OfferDecisionExportGovernanceExceptionType = OfferDecisionExportGovernanceExceptionType.OTHER
    severity: str = "medium"
    title: str
    description: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportGovernanceExceptionUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    exception_status: OfferDecisionExportGovernanceExceptionStatus
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportGovernanceSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_type: OfferDecisionExportGovernanceSnapshotType = OfferDecisionExportGovernanceSnapshotType.GOVERNANCE_CREATED
    created_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceEvidenceScope(str, Enum):
    GOVERNANCE_RECORD = "governance_record"
    AUDIT_REVIEW = "audit_review"
    EXPORT_LIFECYCLE = "export_lifecycle"
    RETENTION = "retention"
    LEGAL_BASIS = "legal_basis"
    ARCHIVE = "archive"
    MANUAL = "manual"


class OfferDecisionExportComplianceEvidenceStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    SATISFIED = "satisfied"
    EXCEPTION = "exception"
    INCOMPLETE = "incomplete"
    WAIVED = "waived"


class OfferDecisionExportComplianceRequirementType(str, Enum):
    RETENTION = "retention"
    LEGAL_BASIS = "legal_basis"
    ARCHIVE = "archive"
    SNAPSHOT_COVERAGE = "snapshot_coverage"
    APPROVAL_TRAIL = "approval_trail"
    HANDOFF_TRAIL = "handoff_trail"
    OUTCOME_TRAIL = "outcome_trail"
    GOVERNANCE_RULE = "governance_rule"
    OTHER = "other"


class OfferDecisionExportComplianceRequirementStatus(str, Enum):
    PENDING = "pending"
    SATISFIED = "satisfied"
    FAILED = "failed"
    WAIVED = "waived"
    EXCEPTION = "exception"


class OfferDecisionExportComplianceCheckType(str, Enum):
    COMPLETENESS = "completeness"
    PRESENCE = "presence"
    MATCH = "match"
    MANUAL_REVIEW = "manual_review"
    SNAPSHOT_IMMUTABILITY = "snapshot_immutability"
    SAFETY_BOUNDARY = "safety_boundary"
    OTHER = "other"


class OfferDecisionExportComplianceCheckStatus(str, Enum):
    NOT_STARTED = "not_started"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    WAIVED = "waived"


class OfferDecisionExportComplianceResultStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"


class OfferDecisionExportComplianceExceptionType(str, Enum):
    REQUIREMENT_GAP = "requirement_gap"
    CHECK_FAILURE = "check_failure"
    EVIDENCE_GAP = "evidence_gap"
    POLICY_EXCEPTION = "policy_exception"
    SNAPSHOT_GAP = "snapshot_gap"
    OTHER = "other"


class OfferDecisionExportComplianceExceptionStatus(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    RESOLVED = "resolved"
    WAIVED = "waived"


class OfferDecisionExportComplianceSnapshotType(str, Enum):
    EVIDENCE_CREATED = "evidence_created"
    REQUIREMENT_REVIEW = "requirement_review"
    CHECK_REVIEW = "check_review"
    RESULT_REVIEW = "result_review"
    EXCEPTION_REVIEW = "exception_review"
    MANUAL = "manual"


class OfferDecisionExportComplianceEvidence(BaseDocument):
    agency_id: str
    evidence_scope: OfferDecisionExportComplianceEvidenceScope = OfferDecisionExportComplianceEvidenceScope.GOVERNANCE_RECORD
    evidence_status: OfferDecisionExportComplianceEvidenceStatus = OfferDecisionExportComplianceEvidenceStatus.DRAFT
    title: str
    governance_record_id: Optional[str] = None
    audit_review_id: Optional[str] = None
    export_id: Optional[str] = None
    decision_pack_id: Optional[str] = None
    outcome_id: Optional[str] = None
    owner_label: Optional[str] = None
    evidence_summary_json: Dict[str, Any] = Field(default_factory=dict)
    requirement_count: int = 0
    check_count: int = 0
    result_count: int = 0
    failed_check_count: int = 0
    exception_count: int = 0
    open_exception_count: int = 0
    snapshot_count: int = 0
    status_reason: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    compliance_only_enabled: bool = True
    automatic_sending_disabled: bool = True
    sms_sending_disabled: bool = True
    public_links_disabled: bool = True
    real_pdf_delivery_disabled: bool = True
    offer_mutation_disabled: bool = True
    price_mutation_disabled: bool = True
    recommendation_disabled: bool = True
    provider_execution_disabled: bool = True
    booking_execution_disabled: bool = True
    pnr_mutation_disabled: bool = True
    ticketing_disabled: bool = True
    emd_issuance_disabled: bool = True
    payment_disabled: bool = True
    invoice_disabled: bool = True
    settlement_disabled: bool = True
    scraping_disabled: bool = True
    external_ai_disabled: bool = True


class OfferDecisionExportComplianceRequirement(BaseDocument):
    agency_id: str
    evidence_id: Optional[str] = None
    requirement_type: OfferDecisionExportComplianceRequirementType = OfferDecisionExportComplianceRequirementType.OTHER
    requirement_status: OfferDecisionExportComplianceRequirementStatus = OfferDecisionExportComplianceRequirementStatus.PENDING
    requirement_name: str
    description: Optional[str] = None
    source_reference_metadata: Optional[str] = None
    required: bool = True
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportComplianceCheck(BaseDocument):
    agency_id: str
    evidence_id: Optional[str] = None
    requirement_id: Optional[str] = None
    check_type: OfferDecisionExportComplianceCheckType = OfferDecisionExportComplianceCheckType.OTHER
    check_status: OfferDecisionExportComplianceCheckStatus = OfferDecisionExportComplianceCheckStatus.NOT_STARTED
    check_name: str
    check_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    performed_by: Optional[str] = None
    performed_at: Optional[datetime] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportComplianceResult(BaseDocument):
    agency_id: str
    evidence_id: Optional[str] = None
    requirement_id: Optional[str] = None
    check_id: Optional[str] = None
    result_status: OfferDecisionExportComplianceResultStatus = OfferDecisionExportComplianceResultStatus.WARNING
    result_name: str
    result_summary: Optional[str] = None
    evidence_reference_metadata: Optional[str] = None
    evaluated_by: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportComplianceException(BaseDocument):
    agency_id: str
    evidence_id: Optional[str] = None
    requirement_id: Optional[str] = None
    check_id: Optional[str] = None
    exception_type: OfferDecisionExportComplianceExceptionType = OfferDecisionExportComplianceExceptionType.OTHER
    exception_status: OfferDecisionExportComplianceExceptionStatus = OfferDecisionExportComplianceExceptionStatus.OPEN
    severity: str = "medium"
    title: str
    description: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True


class OfferDecisionExportComplianceSnapshot(BaseDocument):
    agency_id: str
    evidence_id: str
    snapshot_type: OfferDecisionExportComplianceSnapshotType = OfferDecisionExportComplianceSnapshotType.EVIDENCE_CREATED
    payload: Dict[str, Any] = Field(default_factory=dict)
    immutable: bool = True
    created_by: Optional[str] = None
    metadata_only: bool = True


class OfferDecisionExportComplianceEvidenceCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    evidence_scope: OfferDecisionExportComplianceEvidenceScope = OfferDecisionExportComplianceEvidenceScope.GOVERNANCE_RECORD
    title: Optional[str] = None
    governance_record_id: Optional[str] = None
    audit_review_id: Optional[str] = None
    export_id: Optional[str] = None
    outcome_id: Optional[str] = None
    owner_label: Optional[str] = None
    evidence_summary_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceEvidenceUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    evidence_status: OfferDecisionExportComplianceEvidenceStatus
    status_reason: Optional[str] = None
    owner_label: Optional[str] = None
    evidence_summary_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceRequirementCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    requirement_type: OfferDecisionExportComplianceRequirementType = OfferDecisionExportComplianceRequirementType.OTHER
    requirement_status: OfferDecisionExportComplianceRequirementStatus = OfferDecisionExportComplianceRequirementStatus.PENDING
    requirement_name: str
    description: Optional[str] = None
    source_reference_metadata: Optional[str] = None
    required: bool = True
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceRequirementUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    requirement_status: OfferDecisionExportComplianceRequirementStatus
    description: Optional[str] = None
    source_reference_metadata: Optional[str] = None
    required: Optional[bool] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceCheckCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    requirement_id: Optional[str] = None
    check_type: OfferDecisionExportComplianceCheckType = OfferDecisionExportComplianceCheckType.OTHER
    check_status: OfferDecisionExportComplianceCheckStatus = OfferDecisionExportComplianceCheckStatus.NOT_STARTED
    check_name: str
    check_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    performed_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceCheckUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    check_status: OfferDecisionExportComplianceCheckStatus
    check_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    performed_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceResultCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    requirement_id: Optional[str] = None
    check_id: Optional[str] = None
    result_status: OfferDecisionExportComplianceResultStatus = OfferDecisionExportComplianceResultStatus.WARNING
    result_name: str
    result_summary: Optional[str] = None
    evidence_reference_metadata: Optional[str] = None
    evaluated_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceResultUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    result_status: OfferDecisionExportComplianceResultStatus
    result_summary: Optional[str] = None
    evidence_reference_metadata: Optional[str] = None
    evaluated_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceExceptionCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    requirement_id: Optional[str] = None
    check_id: Optional[str] = None
    exception_type: OfferDecisionExportComplianceExceptionType = OfferDecisionExportComplianceExceptionType.OTHER
    severity: str = "medium"
    title: str
    description: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceExceptionUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    exception_status: OfferDecisionExportComplianceExceptionStatus
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class OfferDecisionExportComplianceSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_type: OfferDecisionExportComplianceSnapshotType = OfferDecisionExportComplianceSnapshotType.EVIDENCE_CREATED
    created_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class AirlineIntelligenceDataPackType(str, Enum):
    STARTER_PACK = "starter_pack"
    AIRLINE_PROFILE_PACK = "airline_profile_pack"
    FLEET_PACK = "fleet_pack"
    FARE_PACK = "fare_pack"
    SPECIAL_SERVICES_PACK = "special_services_pack"
    CMS_BRANDING_PACK = "cms_branding_pack"
    MIXED_PACK = "mixed_pack"


class AirlineIntelligenceDataPackSourceType(str, Enum):
    MANUAL = "manual"
    CURATED = "curated"
    AGENCY_SUPPLIED = "agency_supplied"
    PLATFORM_SUPPLIED = "platform_supplied"
    DEMO_SAMPLE = "demo_sample"
    IMPORTED_FILE = "imported_file"


class AirlineIntelligenceDataPackVerificationStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETIRED = "retired"


class AirlineIntelligenceDataPackTargetDomain(str, Enum):
    AIRLINE_PROFILE = "airline_profile"
    AIRLINE_CONTACTS = "airline_contacts"
    FLEET = "fleet"
    TAIL_NUMBERS = "tail_numbers"
    AIRCRAFT_CONFIGURATIONS = "aircraft_configurations"
    SEATMAPS = "seatmaps"
    ROUTES = "routes"
    FARE_FAMILIES = "fare_families"
    RBD_MATRIX = "rbd_matrix"
    FARE_RULES = "fare_rules"
    ANCILLARIES = "ancillaries"
    INTERLINE = "interline"
    DISTRIBUTION = "distribution"
    PSS_PARAMETERS = "pss_parameters"
    GDS_PARAMETERS = "gds_parameters"
    EXCEPTION_RULES = "exception_rules"
    BRAND_ASSETS = "brand_assets"
    SPECIAL_SERVICES_RULES = "special_services_rules"
    CMS_CONTENT = "cms_content"
    CLIENT_PORTAL_DISPLAY_METADATA = "client_portal_display_metadata"


class AirlineIntelligenceDataPackItemProposedAction(str, Enum):
    INSERT = "insert"
    UPDATE = "update"
    SKIP = "skip"
    REVIEW_ONLY = "review_only"


class AirlineIntelligenceDataPackItemValidationStatus(str, Enum):
    NOT_CHECKED = "not_checked"
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"


class AirlineIntelligenceDataPackItemVerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class AirlineIntelligenceDataPackIssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AirlineIntelligenceDataPackIssueStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class AirlineIntelligenceDataPackImportRunType(str, Enum):
    DRY_RUN = "dry_run"
    VALIDATION = "validation"
    STAGING = "staging"


class AirlineIntelligenceDataPackImportRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AirlineIntelligenceDataPackImportSourceFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    MANUAL = "manual"


class AirlineIntelligenceDataPackReviewNoteType(str, Enum):
    REVIEW = "review"
    SOURCE = "source"
    VERIFICATION = "verification"
    AGENCY_DISPLAY = "agency_display"
    CMS_DISPLAY = "cms_display"
    CLIENT_PORTAL = "client_portal"
    OFFER_BUILDER = "offer_builder"


class AirlineIntelligenceDataPack(BaseDocument):
    name: str
    slug: str
    description: Optional[str] = None
    pack_type: AirlineIntelligenceDataPackType = AirlineIntelligenceDataPackType.MIXED_PACK
    airline_codes: List[str] = Field(default_factory=list)
    target_airline_ids: List[str] = Field(default_factory=list)
    target_domains: List[str] = Field(default_factory=list)
    source_type: AirlineIntelligenceDataPackSourceType = AirlineIntelligenceDataPackSourceType.MANUAL
    source_reference: Optional[str] = None
    source_url: Optional[str] = None
    source_notes: Optional[str] = None
    version_label: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_demo_data: bool = False
    is_operationally_verified: bool = False
    safe_for_agency_internal_crm: bool = False
    safe_for_agency_display: bool = False
    safe_for_cms_display: bool = False
    safe_for_client_portal_later: bool = False
    safe_for_offer_builder: bool = False
    verification_status: AirlineIntelligenceDataPackVerificationStatus = AirlineIntelligenceDataPackVerificationStatus.DRAFT
    confidence_score: float = 0.0
    human_summary: Optional[str] = None
    operator_guidance: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    metadata_only: bool = True
    automatic_promotion_disabled: bool = True


class AirlineIntelligenceDataPackItem(BaseDocument):
    pack_id: str
    airline_id: Optional[str] = None
    airline_iata_code: Optional[str] = None
    target_domain: Optional[AirlineIntelligenceDataPackTargetDomain] = None
    target_record_key: Optional[str] = None
    display_name: str
    plain_language_summary: Optional[str] = None
    proposed_action: AirlineIntelligenceDataPackItemProposedAction = AirlineIntelligenceDataPackItemProposedAction.REVIEW_ONLY
    payload: Dict[str, Any] = Field(default_factory=dict)
    normalized_payload: Dict[str, Any] = Field(default_factory=dict)
    validation_status: AirlineIntelligenceDataPackItemValidationStatus = AirlineIntelligenceDataPackItemValidationStatus.NOT_CHECKED
    verification_status: AirlineIntelligenceDataPackItemVerificationStatus = AirlineIntelligenceDataPackItemVerificationStatus.UNVERIFIED
    confidence_score: float = 0.0
    issue_count: int = 0
    warning_count: int = 0
    source_reference: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_demo_data: bool = False
    is_operationally_verified: bool = False
    safe_for_agency_internal_crm: bool = False
    safe_for_agency_display: bool = False
    safe_for_cms_display: bool = False
    safe_for_client_portal_later: bool = False
    safe_for_offer_builder: bool = False
    metadata_only: bool = True
    automatic_promotion_disabled: bool = True


class AirlineIntelligenceDataPackValidationIssue(BaseDocument):
    pack_id: str
    item_id: Optional[str] = None
    severity: AirlineIntelligenceDataPackIssueSeverity = AirlineIntelligenceDataPackIssueSeverity.WARNING
    issue_code: str
    technical_message: Optional[str] = None
    user_friendly_message: str
    suggested_resolution: Optional[str] = None
    field_path: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    status: AirlineIntelligenceDataPackIssueStatus = AirlineIntelligenceDataPackIssueStatus.OPEN
    metadata_only: bool = True


class AirlineIntelligenceDataPackImportRun(BaseDocument):
    pack_id: str
    run_type: AirlineIntelligenceDataPackImportRunType = AirlineIntelligenceDataPackImportRunType.DRY_RUN
    status: AirlineIntelligenceDataPackImportRunStatus = AirlineIntelligenceDataPackImportRunStatus.QUEUED
    source_format: AirlineIntelligenceDataPackImportSourceFormat = AirlineIntelligenceDataPackImportSourceFormat.MANUAL
    total_items: int = 0
    valid_items: int = 0
    warning_items: int = 0
    invalid_items: int = 0
    skipped_items: int = 0
    inserted_proposals: int = 0
    updated_proposals: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    summary: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata_only: bool = True


class AirlineIntelligenceDataPackReviewNote(BaseDocument):
    pack_id: str
    item_id: Optional[str] = None
    note_type: AirlineIntelligenceDataPackReviewNoteType = AirlineIntelligenceDataPackReviewNoteType.REVIEW
    note: str
    created_by: Optional[str] = None
    metadata_only: bool = True


class AirlineIntelligenceCoverageSnapshot(BaseDocument):
    snapshot_label: str
    airline_count: int = 0
    airlines_with_profiles: int = 0
    airlines_with_contacts: int = 0
    airlines_with_fleet: int = 0
    airlines_with_routes: int = 0
    airlines_with_fare_families: int = 0
    airlines_with_rbd_matrix: int = 0
    airlines_with_fare_rules: int = 0
    airlines_with_ancillaries: int = 0
    airlines_with_interline: int = 0
    airlines_with_distribution: int = 0
    airlines_with_pss_parameters: int = 0
    airlines_with_gds_parameters: int = 0
    airlines_with_exception_rules: int = 0
    airlines_with_brand_assets: int = 0
    airlines_with_special_services_rules: int = 0
    airlines_safe_for_agency_internal_crm: int = 0
    airlines_safe_for_agency_display: int = 0
    airlines_safe_for_cms_display: int = 0
    airlines_safe_for_client_portal_later: int = 0
    airlines_safe_for_offer_builder: int = 0
    generated_at: datetime = Field(default_factory=now_utc)
    diagnostic: Optional[str] = None
    metadata_only: bool = True


class AirlineIntelligenceDataPackCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    pack_type: AirlineIntelligenceDataPackType = AirlineIntelligenceDataPackType.MIXED_PACK
    airline_codes: List[str] = Field(default_factory=list)
    target_airline_ids: List[str] = Field(default_factory=list)
    target_domains: List[AirlineIntelligenceDataPackTargetDomain] = Field(default_factory=list)
    source_type: AirlineIntelligenceDataPackSourceType = AirlineIntelligenceDataPackSourceType.MANUAL
    source_reference: Optional[str] = None
    source_url: Optional[str] = None
    source_notes: Optional[str] = None
    version_label: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_demo_data: bool = False
    is_operationally_verified: bool = False
    safe_for_agency_internal_crm: bool = False
    safe_for_agency_display: bool = False
    safe_for_cms_display: bool = False
    safe_for_client_portal_later: bool = False
    safe_for_offer_builder: bool = False
    verification_status: AirlineIntelligenceDataPackVerificationStatus = AirlineIntelligenceDataPackVerificationStatus.DRAFT
    confidence_score: float = 0.0
    human_summary: Optional[str] = None
    operator_guidance: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class AirlineIntelligenceDataPackUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    pack_type: Optional[AirlineIntelligenceDataPackType] = None
    airline_codes: Optional[List[str]] = None
    target_airline_ids: Optional[List[str]] = None
    target_domains: Optional[List[AirlineIntelligenceDataPackTargetDomain]] = None
    source_type: Optional[AirlineIntelligenceDataPackSourceType] = None
    source_reference: Optional[str] = None
    source_url: Optional[str] = None
    source_notes: Optional[str] = None
    version_label: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_demo_data: Optional[bool] = None
    is_operationally_verified: Optional[bool] = None
    safe_for_agency_internal_crm: Optional[bool] = None
    safe_for_agency_display: Optional[bool] = None
    safe_for_cms_display: Optional[bool] = None
    safe_for_client_portal_later: Optional[bool] = None
    safe_for_offer_builder: Optional[bool] = None
    verification_status: Optional[AirlineIntelligenceDataPackVerificationStatus] = None
    confidence_score: Optional[float] = None
    human_summary: Optional[str] = None
    operator_guidance: Optional[str] = None
    warnings: Optional[List[str]] = None


class AirlineIntelligenceDataPackItemCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_id: Optional[str] = None
    airline_iata_code: Optional[str] = None
    target_domain: Optional[AirlineIntelligenceDataPackTargetDomain] = None
    target_record_key: Optional[str] = None
    display_name: str
    plain_language_summary: Optional[str] = None
    proposed_action: AirlineIntelligenceDataPackItemProposedAction = AirlineIntelligenceDataPackItemProposedAction.REVIEW_ONLY
    payload: Dict[str, Any] = Field(default_factory=dict)
    normalized_payload: Dict[str, Any] = Field(default_factory=dict)
    validation_status: AirlineIntelligenceDataPackItemValidationStatus = AirlineIntelligenceDataPackItemValidationStatus.NOT_CHECKED
    verification_status: AirlineIntelligenceDataPackItemVerificationStatus = AirlineIntelligenceDataPackItemVerificationStatus.UNVERIFIED
    confidence_score: float = 0.0
    source_reference: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_demo_data: bool = False
    is_operationally_verified: bool = False
    safe_for_agency_internal_crm: bool = False
    safe_for_agency_display: bool = False
    safe_for_cms_display: bool = False
    safe_for_client_portal_later: bool = False
    safe_for_offer_builder: bool = False


class AirlineIntelligenceDataPackItemUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_id: Optional[str] = None
    airline_iata_code: Optional[str] = None
    target_domain: Optional[AirlineIntelligenceDataPackTargetDomain] = None
    target_record_key: Optional[str] = None
    display_name: Optional[str] = None
    plain_language_summary: Optional[str] = None
    proposed_action: Optional[AirlineIntelligenceDataPackItemProposedAction] = None
    payload: Optional[Dict[str, Any]] = None
    normalized_payload: Optional[Dict[str, Any]] = None
    validation_status: Optional[AirlineIntelligenceDataPackItemValidationStatus] = None
    verification_status: Optional[AirlineIntelligenceDataPackItemVerificationStatus] = None
    confidence_score: Optional[float] = None
    source_reference: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_demo_data: Optional[bool] = None
    is_operationally_verified: Optional[bool] = None
    safe_for_agency_internal_crm: Optional[bool] = None
    safe_for_agency_display: Optional[bool] = None
    safe_for_cms_display: Optional[bool] = None
    safe_for_client_portal_later: Optional[bool] = None
    safe_for_offer_builder: Optional[bool] = None


class AirlineIntelligenceDataPackInlineJsonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inline_json: str
    created_by: Optional[str] = None


class AirlineIntelligenceDataPackInlineCsvRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inline_csv: str
    created_by: Optional[str] = None


class AirlineIntelligenceDataPackImportRunCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    run_type: AirlineIntelligenceDataPackImportRunType = AirlineIntelligenceDataPackImportRunType.VALIDATION
    source_format: AirlineIntelligenceDataPackImportSourceFormat = AirlineIntelligenceDataPackImportSourceFormat.MANUAL
    created_by: Optional[str] = None
    summary: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class AirlineIntelligenceDataPackValidationIssueAcknowledgeRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: AirlineIntelligenceDataPackIssueStatus = AirlineIntelligenceDataPackIssueStatus.ACKNOWLEDGED
    resolved_by: Optional[str] = None


class AirlineIntelligenceDataPackReviewNoteCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    item_id: Optional[str] = None
    note_type: AirlineIntelligenceDataPackReviewNoteType = AirlineIntelligenceDataPackReviewNoteType.REVIEW
    note: str
    created_by: Optional[str] = None


class AirlineIntelligenceCoverageSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_label: Optional[str] = None


class AirlineIntelligenceDataPackReviewStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROMOTION_READY = "promotion_ready"
    BLOCKED = "blocked"


class AirlineIntelligenceDataPackChecklistScope(str, Enum):
    PACK = "pack"
    ITEM = "item"


class AirlineIntelligenceDataPackChecklistStatus(str, Enum):
    OPEN = "open"
    PASSED = "passed"
    FAILED = "failed"
    WAIVED = "waived"


class AirlineIntelligenceDataPackFieldMappingStatus(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class AirlineIntelligenceDataPackConflictType(str, Enum):
    DUPLICATE_STAGED_ITEM = "duplicate_staged_item"
    FIELD_VALUE_CONFLICT = "field_value_conflict"
    MISSING_FIELD_MAPPING = "missing_field_mapping"
    MISSING_TARGET_REFERENCE = "missing_target_reference"
    UNSAFE_SURFACE_FLAG = "unsafe_surface_flag"


class AirlineIntelligenceDataPackConflictStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class AirlineIntelligenceDataPackPromotionReadinessStatus(str, Enum):
    NOT_READY = "not_ready"
    NEEDS_REVIEW = "needs_review"
    READY = "ready"
    BLOCKED = "blocked"
    REJECTED = "rejected"


class AirlineIntelligenceDataPackReviewSnapshotType(str, Enum):
    REVIEW_CREATED = "review_created"
    CHECKLIST_UPDATED = "checklist_updated"
    FIELD_MAPPING_UPDATED = "field_mapping_updated"
    CONFLICTS_DETECTED = "conflicts_detected"
    READINESS_MARKED = "readiness_marked"
    STATUS_CHANGED = "status_changed"


class AirlineIntelligenceDataPackReview(BaseDocument):
    pack_id: str
    status: AirlineIntelligenceDataPackReviewStatus = AirlineIntelligenceDataPackReviewStatus.DRAFT
    review_title: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    plain_language_coverage_summary: Optional[str] = None
    decision_notes: Optional[str] = None
    checklist_total_count: int = 0
    checklist_passed_count: int = 0
    checklist_failed_count: int = 0
    field_mapping_count: int = 0
    open_conflict_count: int = 0
    promotion_ready: bool = False
    safe_for_agency_internal_crm: bool = False
    safe_for_agency_display: bool = False
    safe_for_cms_display: bool = False
    safe_for_client_portal_later: bool = False
    safe_for_offer_builder: bool = False
    metadata_only: bool = True
    automatic_promotion_disabled: bool = True


class AirlineIntelligenceDataPackReviewChecklistItem(BaseDocument):
    review_id: str
    pack_id: str
    item_id: Optional[str] = None
    scope: AirlineIntelligenceDataPackChecklistScope = AirlineIntelligenceDataPackChecklistScope.PACK
    label: str
    description: Optional[str] = None
    status: AirlineIntelligenceDataPackChecklistStatus = AirlineIntelligenceDataPackChecklistStatus.OPEN
    required: bool = True
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    metadata_only: bool = True


class AirlineIntelligenceDataPackFieldMapping(BaseDocument):
    pack_id: str
    item_id: Optional[str] = None
    source_payload_path: str
    target_collection: str
    target_field_path: str
    target_record_key: Optional[str] = None
    target_record_id: Optional[str] = None
    mapping_status: AirlineIntelligenceDataPackFieldMappingStatus = AirlineIntelligenceDataPackFieldMappingStatus.DRAFT
    mapping_confidence: float = 0.0
    transformation_notes: Optional[str] = None
    would_create_record: bool = False
    would_update_record: bool = False
    safe_for_agency_internal_crm: bool = False
    safe_for_agency_display: bool = False
    safe_for_cms_display: bool = False
    safe_for_client_portal_later: bool = False
    safe_for_offer_builder: bool = False
    metadata_only: bool = True
    automatic_promotion_disabled: bool = True


class AirlineIntelligenceDataPackConflict(BaseDocument):
    pack_id: str
    item_id: Optional[str] = None
    target_collection: Optional[str] = None
    target_record_key: Optional[str] = None
    conflict_type: AirlineIntelligenceDataPackConflictType = AirlineIntelligenceDataPackConflictType.FIELD_VALUE_CONFLICT
    severity: AirlineIntelligenceDataPackIssueSeverity = AirlineIntelligenceDataPackIssueSeverity.WARNING
    status: AirlineIntelligenceDataPackConflictStatus = AirlineIntelligenceDataPackConflictStatus.OPEN
    plain_language_summary: str
    technical_summary: Optional[str] = None
    staged_value: Optional[Any] = None
    existing_value: Optional[Any] = None
    suggested_resolution: Optional[str] = None
    detected_by: Optional[str] = None
    detected_at: datetime = Field(default_factory=now_utc)
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    metadata_only: bool = True


class AirlineIntelligenceDataPackPromotionReadiness(BaseDocument):
    pack_id: str
    review_id: Optional[str] = None
    status: AirlineIntelligenceDataPackPromotionReadinessStatus = AirlineIntelligenceDataPackPromotionReadinessStatus.NOT_READY
    ready_for_promotion: bool = False
    checklist_complete: bool = False
    approved_mapping_count: int = 0
    open_conflict_count: int = 0
    blocked_reason: Optional[str] = None
    readiness_summary: Optional[str] = None
    marked_by: Optional[str] = None
    marked_at: datetime = Field(default_factory=now_utc)
    safe_for_agency_internal_crm: bool = False
    safe_for_agency_display: bool = False
    safe_for_cms_display: bool = False
    safe_for_client_portal_later: bool = False
    safe_for_offer_builder: bool = False
    metadata_only: bool = True
    automatic_promotion_disabled: bool = True


class AirlineIntelligenceDataPackReviewSnapshot(BaseDocument):
    pack_id: str
    review_id: Optional[str] = None
    snapshot_type: AirlineIntelligenceDataPackReviewSnapshotType = AirlineIntelligenceDataPackReviewSnapshotType.REVIEW_CREATED
    snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None
    immutable: bool = True
    metadata_only: bool = True


class AirlineIntelligenceDataPackReviewCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_title: Optional[str] = None
    reviewed_by: Optional[str] = None
    plain_language_coverage_summary: Optional[str] = None
    decision_notes: Optional[str] = None
    safe_for_agency_internal_crm: bool = False
    safe_for_agency_display: bool = False
    safe_for_cms_display: bool = False
    safe_for_client_portal_later: bool = False
    safe_for_offer_builder: bool = False


class AirlineIntelligenceDataPackReviewUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: Optional[AirlineIntelligenceDataPackReviewStatus] = None
    review_title: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    plain_language_coverage_summary: Optional[str] = None
    decision_notes: Optional[str] = None
    safe_for_agency_internal_crm: Optional[bool] = None
    safe_for_agency_display: Optional[bool] = None
    safe_for_cms_display: Optional[bool] = None
    safe_for_client_portal_later: Optional[bool] = None
    safe_for_offer_builder: Optional[bool] = None


class AirlineIntelligenceDataPackChecklistItemCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    item_id: Optional[str] = None
    scope: AirlineIntelligenceDataPackChecklistScope = AirlineIntelligenceDataPackChecklistScope.PACK
    label: str
    description: Optional[str] = None
    status: AirlineIntelligenceDataPackChecklistStatus = AirlineIntelligenceDataPackChecklistStatus.OPEN
    required: bool = True
    completed_by: Optional[str] = None
    notes: Optional[str] = None


class AirlineIntelligenceDataPackChecklistItemUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: Optional[AirlineIntelligenceDataPackChecklistStatus] = None
    completed_by: Optional[str] = None
    notes: Optional[str] = None


class AirlineIntelligenceDataPackFieldMappingCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    item_id: Optional[str] = None
    source_payload_path: str
    target_collection: str
    target_field_path: str
    target_record_key: Optional[str] = None
    target_record_id: Optional[str] = None
    mapping_status: AirlineIntelligenceDataPackFieldMappingStatus = AirlineIntelligenceDataPackFieldMappingStatus.DRAFT
    mapping_confidence: float = 0.0
    transformation_notes: Optional[str] = None
    would_create_record: bool = False
    would_update_record: bool = False
    safe_for_agency_internal_crm: bool = False
    safe_for_agency_display: bool = False
    safe_for_cms_display: bool = False
    safe_for_client_portal_later: bool = False
    safe_for_offer_builder: bool = False


class AirlineIntelligenceDataPackFieldMappingUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    source_payload_path: Optional[str] = None
    target_collection: Optional[str] = None
    target_field_path: Optional[str] = None
    target_record_key: Optional[str] = None
    target_record_id: Optional[str] = None
    mapping_status: Optional[AirlineIntelligenceDataPackFieldMappingStatus] = None
    mapping_confidence: Optional[float] = None
    transformation_notes: Optional[str] = None
    would_create_record: Optional[bool] = None
    would_update_record: Optional[bool] = None
    safe_for_agency_internal_crm: Optional[bool] = None
    safe_for_agency_display: Optional[bool] = None
    safe_for_cms_display: Optional[bool] = None
    safe_for_client_portal_later: Optional[bool] = None
    safe_for_offer_builder: Optional[bool] = None


class AirlineIntelligenceDataPackConflictUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: AirlineIntelligenceDataPackConflictStatus
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class AirlineIntelligenceDataPackPromotionReadinessRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    review_id: Optional[str] = None
    status: Optional[AirlineIntelligenceDataPackPromotionReadinessStatus] = None
    marked_by: Optional[str] = None
    blocked_reason: Optional[str] = None
    readiness_summary: Optional[str] = None
    safe_for_agency_internal_crm: Optional[bool] = None
    safe_for_agency_display: Optional[bool] = None
    safe_for_cms_display: Optional[bool] = None
    safe_for_client_portal_later: Optional[bool] = None
    safe_for_offer_builder: Optional[bool] = None


class AirlineIntelligenceDataPackReviewSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_type: AirlineIntelligenceDataPackReviewSnapshotType = AirlineIntelligenceDataPackReviewSnapshotType.REVIEW_CREATED
    created_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class AirlineIntelligenceKnowledgeVersionStatus(str, Enum):
    DRAFT = "draft"
    FROZEN = "frozen"
    APPROVED = "approved"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    ROLLED_BACK = "rolled_back"
    ARCHIVED = "archived"


class AirlineIntelligenceKnowledgeAgencyVisibilityMode(str, Enum):
    HIDDEN = "hidden"
    PREVIEW = "preview"
    VISIBLE = "visible"


class AirlineIntelligenceKnowledgeVersionItemInclusionStatus(str, Enum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    NEEDS_REVIEW = "needs_review"


class AirlineIntelligenceKnowledgeReleaseChannelAudience(str, Enum):
    PLATFORM = "platform"
    PILOT_AGENCIES = "pilot_agencies"
    ALL_AGENCIES = "all_agencies"
    INTERNAL_ONLY = "internal_only"


class AirlineIntelligenceKnowledgeReleaseAssignmentStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    SUPERSEDED = "superseded"
    ROLLED_BACK = "rolled_back"


class AirlineIntelligenceKnowledgeRollbackPlanStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    EXECUTED_METADATA_ONLY = "executed_metadata_only"
    CANCELLED = "cancelled"


class AirlineIntelligenceKnowledgeVersionSnapshotType(str, Enum):
    VERSION_CREATED = "version_created"
    VERSION_FROZEN = "version_frozen"
    VERSION_APPROVED = "version_approved"
    VERSION_PUBLISHED_METADATA = "version_published_metadata"
    VERSION_COMPARISON = "version_comparison"
    ROLLBACK_PLAN = "rollback_plan"
    MANUAL = "manual"


class AirlineIntelligenceKnowledgeVersion(BaseDocument):
    version_code: str
    title: str
    description: Optional[str] = None
    status: AirlineIntelligenceKnowledgeVersionStatus = AirlineIntelligenceKnowledgeVersionStatus.DRAFT
    source_pack_ids: List[str] = Field(default_factory=list)
    source_review_ids: List[str] = Field(default_factory=list)
    source_promotion_readiness_ids: List[str] = Field(default_factory=list)
    coverage_summary: Optional[str] = None
    publication_scope_metadata: Dict[str, Any] = Field(default_factory=dict)
    agency_visibility_mode: AirlineIntelligenceKnowledgeAgencyVisibilityMode = AirlineIntelligenceKnowledgeAgencyVisibilityMode.HIDDEN
    crm_safe: bool = False
    cms_safe: bool = False
    client_portal_safe: bool = False
    offer_builder_safe: bool = False
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    published_by: Optional[str] = None
    frozen_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    metadata_only: bool = True
    operational_promotion_disabled: bool = True


class AirlineIntelligenceKnowledgeVersionItem(BaseDocument):
    version_id: str
    source_pack_item_id: str
    target_domain: Optional[str] = None
    target_record_key: Optional[str] = None
    target_airline_code: Optional[str] = None
    field_mapping_id: Optional[str] = None
    conflict_ids: List[str] = Field(default_factory=list)
    readiness_id: Optional[str] = None
    inclusion_status: AirlineIntelligenceKnowledgeVersionItemInclusionStatus = AirlineIntelligenceKnowledgeVersionItemInclusionStatus.INCLUDED
    inclusion_reason: Optional[str] = None
    normalized_payload_preview: Dict[str, Any] = Field(default_factory=dict)
    agency_plain_language_summary: Optional[str] = None
    metadata_only: bool = True
    operational_promotion_disabled: bool = True


class AirlineIntelligenceKnowledgeReleaseChannel(BaseDocument):
    channel_code: str
    name: str
    description: Optional[str] = None
    audience: AirlineIntelligenceKnowledgeReleaseChannelAudience = AirlineIntelligenceKnowledgeReleaseChannelAudience.INTERNAL_ONLY
    is_active: bool = True
    metadata_only: bool = True


class AirlineIntelligenceKnowledgeReleaseAssignment(BaseDocument):
    channel_id: str
    version_id: str
    agency_id: Optional[str] = None
    status: AirlineIntelligenceKnowledgeReleaseAssignmentStatus = AirlineIntelligenceKnowledgeReleaseAssignmentStatus.PLANNED
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    notes: Optional[str] = None
    metadata_only: bool = True
    operational_promotion_disabled: bool = True


class AirlineIntelligenceKnowledgeVersionComparison(BaseDocument):
    base_version_id: str
    compare_version_id: str
    summary: Optional[str] = None
    added_items: List[Dict[str, Any]] = Field(default_factory=list)
    changed_items: List[Dict[str, Any]] = Field(default_factory=list)
    removed_items: List[Dict[str, Any]] = Field(default_factory=list)
    conflict_summary: Optional[str] = None
    agency_impact_summary: Optional[str] = None
    cms_impact_summary: Optional[str] = None
    client_portal_impact_summary: Optional[str] = None
    offer_builder_impact_summary: Optional[str] = None
    metadata_only: bool = True


class AirlineIntelligenceKnowledgeRollbackPlan(BaseDocument):
    from_version_id: str
    to_version_id: str
    channel_id: Optional[str] = None
    reason: str
    impact_summary: Optional[str] = None
    checklist: List[Dict[str, Any]] = Field(default_factory=list)
    status: AirlineIntelligenceKnowledgeRollbackPlanStatus = AirlineIntelligenceKnowledgeRollbackPlanStatus.DRAFT
    metadata_only: bool = True
    operational_promotion_disabled: bool = True


class AirlineIntelligenceKnowledgeVersionSnapshot(BaseDocument):
    version_id: str
    snapshot_type: AirlineIntelligenceKnowledgeVersionSnapshotType = AirlineIntelligenceKnowledgeVersionSnapshotType.MANUAL
    frozen_payload: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None
    immutable: bool = True
    metadata_only: bool = True


class AirlineIntelligenceKnowledgeVersionCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    version_code: str
    title: str
    description: Optional[str] = None
    source_pack_ids: List[str] = Field(default_factory=list)
    source_review_ids: List[str] = Field(default_factory=list)
    source_promotion_readiness_ids: List[str] = Field(default_factory=list)
    coverage_summary: Optional[str] = None
    publication_scope_metadata: Dict[str, Any] = Field(default_factory=dict)
    agency_visibility_mode: AirlineIntelligenceKnowledgeAgencyVisibilityMode = AirlineIntelligenceKnowledgeAgencyVisibilityMode.HIDDEN
    crm_safe: bool = False
    cms_safe: bool = False
    client_portal_safe: bool = False
    offer_builder_safe: bool = False
    created_by: Optional[str] = None


class AirlineIntelligenceKnowledgeVersionUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AirlineIntelligenceKnowledgeVersionStatus] = None
    source_pack_ids: Optional[List[str]] = None
    source_review_ids: Optional[List[str]] = None
    source_promotion_readiness_ids: Optional[List[str]] = None
    coverage_summary: Optional[str] = None
    publication_scope_metadata: Optional[Dict[str, Any]] = None
    agency_visibility_mode: Optional[AirlineIntelligenceKnowledgeAgencyVisibilityMode] = None
    crm_safe: Optional[bool] = None
    cms_safe: Optional[bool] = None
    client_portal_safe: Optional[bool] = None
    offer_builder_safe: Optional[bool] = None
    approved_by: Optional[str] = None
    published_by: Optional[str] = None


class AirlineIntelligenceKnowledgeVersionItemCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    source_pack_item_id: str
    target_domain: Optional[str] = None
    target_record_key: Optional[str] = None
    target_airline_code: Optional[str] = None
    field_mapping_id: Optional[str] = None
    conflict_ids: List[str] = Field(default_factory=list)
    readiness_id: Optional[str] = None
    inclusion_status: AirlineIntelligenceKnowledgeVersionItemInclusionStatus = AirlineIntelligenceKnowledgeVersionItemInclusionStatus.INCLUDED
    inclusion_reason: Optional[str] = None
    normalized_payload_preview: Dict[str, Any] = Field(default_factory=dict)
    agency_plain_language_summary: Optional[str] = None


class AirlineIntelligenceKnowledgeVersionItemUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    field_mapping_id: Optional[str] = None
    conflict_ids: Optional[List[str]] = None
    readiness_id: Optional[str] = None
    inclusion_status: Optional[AirlineIntelligenceKnowledgeVersionItemInclusionStatus] = None
    inclusion_reason: Optional[str] = None
    normalized_payload_preview: Optional[Dict[str, Any]] = None
    agency_plain_language_summary: Optional[str] = None


class AirlineIntelligenceKnowledgeReleaseChannelCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    channel_code: str
    name: str
    description: Optional[str] = None
    audience: AirlineIntelligenceKnowledgeReleaseChannelAudience = AirlineIntelligenceKnowledgeReleaseChannelAudience.INTERNAL_ONLY
    is_active: bool = True


class AirlineIntelligenceKnowledgeReleaseChannelUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    name: Optional[str] = None
    description: Optional[str] = None
    audience: Optional[AirlineIntelligenceKnowledgeReleaseChannelAudience] = None
    is_active: Optional[bool] = None


class AirlineIntelligenceKnowledgeReleaseAssignmentCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    channel_id: str
    version_id: str
    agency_id: Optional[str] = None
    status: AirlineIntelligenceKnowledgeReleaseAssignmentStatus = AirlineIntelligenceKnowledgeReleaseAssignmentStatus.PLANNED
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    notes: Optional[str] = None


class AirlineIntelligenceKnowledgeReleaseAssignmentUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: Optional[AirlineIntelligenceKnowledgeReleaseAssignmentStatus] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    notes: Optional[str] = None


class AirlineIntelligenceKnowledgeVersionComparisonCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_version_id: str
    compare_version_id: str


class AirlineIntelligenceKnowledgeRollbackPlanCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    from_version_id: str
    to_version_id: str
    channel_id: Optional[str] = None
    reason: str
    impact_summary: Optional[str] = None
    checklist: List[Dict[str, Any]] = Field(default_factory=list)
    status: AirlineIntelligenceKnowledgeRollbackPlanStatus = AirlineIntelligenceKnowledgeRollbackPlanStatus.DRAFT


class AirlineIntelligenceKnowledgeRollbackPlanUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: Optional[AirlineIntelligenceKnowledgeRollbackPlanStatus] = None
    impact_summary: Optional[str] = None
    checklist: Optional[List[Dict[str, Any]]] = None


class AirlineIntelligenceKnowledgeVersionSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    snapshot_type: AirlineIntelligenceKnowledgeVersionSnapshotType = AirlineIntelligenceKnowledgeVersionSnapshotType.MANUAL
    created_by: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class AirlineIntelligenceAgencyConsumptionProfileStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    VISIBLE = "visible"
    DISABLED = "disabled"


class AirlineIntelligenceAgencyUsageArea(str, Enum):
    CRM = "crm"
    CMS = "cms"
    CLIENT_PORTAL = "client_portal"
    OFFER_BUILDER = "offer_builder"


class AirlineIntelligenceAgencyUsageReadinessStatus(str, Enum):
    NOT_AVAILABLE = "not_available"
    NEEDS_REVIEW = "needs_review"
    READY = "ready"
    BLOCKED = "blocked"


class AirlineIntelligenceAgencyConsumptionNoteType(str, Enum):
    PLATFORM_INTERNAL = "platform_internal"
    AGENCY_GUIDANCE = "agency_guidance"
    CRM_USAGE = "crm_usage"
    CMS_USAGE = "cms_usage"
    CLIENT_PORTAL_PLANNING = "client_portal_planning"
    OFFER_BUILDER_PLANNING = "offer_builder_planning"


class AirlineIntelligenceAgencyConsumptionSnapshotType(str, Enum):
    PROFILE_CREATED = "profile_created"
    PROFILE_UPDATED = "profile_updated"
    USAGE_READINESS_CALCULATED = "usage_readiness_calculated"
    NOTE_CREATED = "note_created"
    MANUAL = "manual"


class AirlineIntelligenceAgencyConsumptionProfile(BaseDocument):
    agency_id: str
    knowledge_version_id: str
    release_channel_id: Optional[str] = None
    status: AirlineIntelligenceAgencyConsumptionProfileStatus = AirlineIntelligenceAgencyConsumptionProfileStatus.DRAFT
    crm_safe: bool = False
    cms_safe: bool = False
    client_portal_safe: bool = False
    offer_builder_safe: bool = False
    plain_language_summary: Optional[str] = None
    allowed_usage_notes: Optional[str] = None
    blocked_usage_notes: Optional[str] = None
    internal_owner_notes: Optional[str] = None
    visible_to_agency: bool = False
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    metadata_only: bool = True
    automatic_publishing_disabled: bool = True


class AirlineIntelligenceAgencyKnowledgeAssignmentView(BaseDocument):
    agency_id: str
    knowledge_version_id: str
    release_channel_id: Optional[str] = None
    release_assignment_id: Optional[str] = None
    profile_id: Optional[str] = None
    status: AirlineIntelligenceAgencyConsumptionProfileStatus = AirlineIntelligenceAgencyConsumptionProfileStatus.DRAFT
    crm_safe: bool = False
    cms_safe: bool = False
    client_portal_safe: bool = False
    offer_builder_safe: bool = False
    plain_language_summary: Optional[str] = None
    allowed_usage_notes: Optional[str] = None
    blocked_usage_notes: Optional[str] = None
    metadata_only: bool = True
    payloads_hidden: bool = True


class AirlineIntelligenceAgencyUsageReadiness(BaseDocument):
    agency_id: str
    knowledge_version_id: str
    release_channel_id: Optional[str] = None
    profile_id: Optional[str] = None
    usage_area: AirlineIntelligenceAgencyUsageArea
    status: AirlineIntelligenceAgencyUsageReadinessStatus = AirlineIntelligenceAgencyUsageReadinessStatus.NOT_AVAILABLE
    safe_for_usage: bool = False
    plain_language_summary: Optional[str] = None
    allowed_usage_notes: Optional[str] = None
    blocked_usage_notes: Optional[str] = None
    calculated_by: Optional[str] = None
    calculated_at: Optional[datetime] = None
    metadata_only: bool = True
    automatic_publishing_disabled: bool = True


class AirlineIntelligenceAgencyConsumptionNote(BaseDocument):
    agency_id: str
    knowledge_version_id: str
    release_channel_id: Optional[str] = None
    profile_id: Optional[str] = None
    note_type: AirlineIntelligenceAgencyConsumptionNoteType = AirlineIntelligenceAgencyConsumptionNoteType.AGENCY_GUIDANCE
    note: str
    created_by: Optional[str] = None
    visible_to_agency: bool = False
    metadata_only: bool = True


class AirlineIntelligenceAgencyConsumptionSnapshot(BaseDocument):
    agency_id: str
    knowledge_version_id: Optional[str] = None
    profile_id: Optional[str] = None
    snapshot_type: AirlineIntelligenceAgencyConsumptionSnapshotType = AirlineIntelligenceAgencyConsumptionSnapshotType.MANUAL
    snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None
    immutable: bool = True
    metadata_only: bool = True


class AirlineIntelligenceAgencyConsumptionProfileCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: str
    knowledge_version_id: str
    release_channel_id: Optional[str] = None
    status: AirlineIntelligenceAgencyConsumptionProfileStatus = AirlineIntelligenceAgencyConsumptionProfileStatus.DRAFT
    crm_safe: Optional[bool] = None
    cms_safe: Optional[bool] = None
    client_portal_safe: Optional[bool] = None
    offer_builder_safe: Optional[bool] = None
    plain_language_summary: Optional[str] = None
    allowed_usage_notes: Optional[str] = None
    blocked_usage_notes: Optional[str] = None
    internal_owner_notes: Optional[str] = None
    visible_to_agency: Optional[bool] = None
    created_by: Optional[str] = None


class AirlineIntelligenceAgencyConsumptionProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    release_channel_id: Optional[str] = None
    status: Optional[AirlineIntelligenceAgencyConsumptionProfileStatus] = None
    crm_safe: Optional[bool] = None
    cms_safe: Optional[bool] = None
    client_portal_safe: Optional[bool] = None
    offer_builder_safe: Optional[bool] = None
    plain_language_summary: Optional[str] = None
    allowed_usage_notes: Optional[str] = None
    blocked_usage_notes: Optional[str] = None
    internal_owner_notes: Optional[str] = None
    visible_to_agency: Optional[bool] = None
    updated_by: Optional[str] = None


class AirlineIntelligenceAgencyUsageReadinessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_version_id: Optional[str] = None
    profile_id: Optional[str] = None
    usage_area: Optional[AirlineIntelligenceAgencyUsageArea] = None
    calculated_by: Optional[str] = None


class AirlineIntelligenceAgencyConsumptionNoteCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: str
    knowledge_version_id: str
    release_channel_id: Optional[str] = None
    profile_id: Optional[str] = None
    note_type: AirlineIntelligenceAgencyConsumptionNoteType = AirlineIntelligenceAgencyConsumptionNoteType.AGENCY_GUIDANCE
    note: str
    created_by: Optional[str] = None
    visible_to_agency: bool = False


class AirlineIntelligenceAgencyConsumptionSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: str
    knowledge_version_id: Optional[str] = None
    profile_id: Optional[str] = None
    snapshot_type: AirlineIntelligenceAgencyConsumptionSnapshotType = AirlineIntelligenceAgencyConsumptionSnapshotType.MANUAL
    snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None


class SaaSSubscriptionPlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class SaaSSubscriptionTier(str, Enum):
    STARTER = "starter"
    GROWTH = "growth"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class SaaSEntitlementScope(str, Enum):
    MODULE = "module"
    AIRLINE_INTELLIGENCE_DOMAIN = "airline_intelligence_domain"
    DATA_PACK_CHANNEL = "data_pack_channel"
    CRM = "crm"
    CMS = "cms"
    CLIENT_PORTAL = "client_portal"
    OFFER_BUILDER = "offer_builder"
    DOCUMENTS = "documents"
    CUSTOM = "custom"


class AgencySubscriptionAssignmentStatus(str, Enum):
    DRAFT = "draft"
    TRIAL = "trial"
    ACTIVE = "active"
    REVIEW = "review"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AgencyEntitlementReadinessStatus(str, Enum):
    NOT_READY = "not_ready"
    NEEDS_REVIEW = "needs_review"
    READY = "ready"
    BLOCKED = "blocked"


class AgencySubscriptionReviewNoteType(str, Enum):
    PLATFORM_INTERNAL = "platform_internal"
    AGENCY_VISIBLE = "agency_visible"
    ENTITLEMENT_REVIEW = "entitlement_review"
    RENEWAL_REVIEW = "renewal_review"
    MANUAL_EXCEPTION = "manual_exception"


class AgencySubscriptionSnapshotType(str, Enum):
    PLAN_CREATED = "plan_created"
    PLAN_UPDATED = "plan_updated"
    ENTITLEMENT_CREATED = "entitlement_created"
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_UPDATED = "assignment_updated"
    READINESS_RECALCULATED = "readiness_recalculated"
    NOTE_CREATED = "note_created"
    MANUAL = "manual"


class AgencyFeatureFlagState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    HIDDEN = "hidden"
    BETA = "beta"
    PILOT = "pilot"


class SaaSSubscriptionPlan(BaseDocument):
    plan_name: str
    plan_code: str
    tier: SaaSSubscriptionTier = SaaSSubscriptionTier.STARTER
    status: SaaSSubscriptionPlanStatus = SaaSSubscriptionPlanStatus.DRAFT
    description: Optional[str] = None
    included_modules: List[str] = Field(default_factory=list)
    included_airline_intelligence_domains: List[str] = Field(default_factory=list)
    included_data_pack_channels: List[str] = Field(default_factory=list)
    visibility_flags: Dict[str, bool] = Field(default_factory=dict)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    metadata_only: bool = True
    billing_disabled: bool = True
    payment_disabled: bool = True


class SaaSPlanEntitlement(BaseDocument):
    plan_id: str
    entitlement_scope: SaaSEntitlementScope = SaaSEntitlementScope.MODULE
    entitlement_key: str
    label: str
    description: Optional[str] = None
    visibility_flags: Dict[str, bool] = Field(default_factory=dict)
    included: bool = True
    manual_review_required: bool = False
    metadata_only: bool = True


class AgencySubscriptionAssignment(BaseDocument):
    agency_id: str
    plan_id: str
    assignment_status: AgencySubscriptionAssignmentStatus = AgencySubscriptionAssignmentStatus.DRAFT
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    manual_review_required: bool = False
    visibility_flags: Dict[str, bool] = Field(default_factory=dict)
    included_modules: List[str] = Field(default_factory=list)
    included_airline_intelligence_domains: List[str] = Field(default_factory=list)
    included_data_pack_channels: List[str] = Field(default_factory=list)
    assigned_by: Optional[str] = None
    updated_by: Optional[str] = None
    metadata_only: bool = True
    automatic_access_enforcement_disabled: bool = True


class AgencyEntitlementReadiness(BaseDocument):
    agency_id: str
    assignment_id: Optional[str] = None
    plan_id: Optional[str] = None
    entitlement_scope: SaaSEntitlementScope = SaaSEntitlementScope.MODULE
    entitlement_key: str
    status: AgencyEntitlementReadinessStatus = AgencyEntitlementReadinessStatus.NEEDS_REVIEW
    crm_ready: bool = False
    cms_ready: bool = False
    client_portal_ready: bool = False
    offer_builder_ready: bool = False
    airline_intelligence_ready: bool = False
    manual_review_required: bool = False
    plain_language_summary: Optional[str] = None
    calculated_by: Optional[str] = None
    calculated_at: Optional[datetime] = None
    metadata_only: bool = True
    automatic_access_enforcement_disabled: bool = True


class AgencySubscriptionReviewNote(BaseDocument):
    agency_id: str
    assignment_id: Optional[str] = None
    plan_id: Optional[str] = None
    note_type: AgencySubscriptionReviewNoteType = AgencySubscriptionReviewNoteType.AGENCY_VISIBLE
    note: str
    created_by: Optional[str] = None
    visible_to_agency: bool = False
    metadata_only: bool = True


class AgencySubscriptionSnapshot(BaseDocument):
    agency_id: Optional[str] = None
    assignment_id: Optional[str] = None
    plan_id: Optional[str] = None
    snapshot_type: AgencySubscriptionSnapshotType = AgencySubscriptionSnapshotType.MANUAL
    snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None
    immutable: bool = True
    metadata_only: bool = True


class SaaSSubscriptionPlanCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    plan_name: str
    plan_code: str
    tier: SaaSSubscriptionTier = SaaSSubscriptionTier.STARTER
    status: SaaSSubscriptionPlanStatus = SaaSSubscriptionPlanStatus.DRAFT
    description: Optional[str] = None
    included_modules: List[str] = Field(default_factory=list)
    included_airline_intelligence_domains: List[str] = Field(default_factory=list)
    included_data_pack_channels: List[str] = Field(default_factory=list)
    visibility_flags: Dict[str, bool] = Field(default_factory=dict)
    created_by: Optional[str] = None


class SaaSSubscriptionPlanUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    plan_name: Optional[str] = None
    tier: Optional[SaaSSubscriptionTier] = None
    status: Optional[SaaSSubscriptionPlanStatus] = None
    description: Optional[str] = None
    included_modules: Optional[List[str]] = None
    included_airline_intelligence_domains: Optional[List[str]] = None
    included_data_pack_channels: Optional[List[str]] = None
    visibility_flags: Optional[Dict[str, bool]] = None
    updated_by: Optional[str] = None


class SaaSPlanEntitlementCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    plan_id: str
    entitlement_scope: SaaSEntitlementScope = SaaSEntitlementScope.MODULE
    entitlement_key: str
    label: str
    description: Optional[str] = None
    visibility_flags: Dict[str, bool] = Field(default_factory=dict)
    included: bool = True
    manual_review_required: bool = False


class AgencySubscriptionAssignmentCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: str
    plan_id: str
    assignment_status: AgencySubscriptionAssignmentStatus = AgencySubscriptionAssignmentStatus.DRAFT
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    manual_review_required: bool = False
    visibility_flags: Dict[str, bool] = Field(default_factory=dict)
    included_modules: List[str] = Field(default_factory=list)
    included_airline_intelligence_domains: List[str] = Field(default_factory=list)
    included_data_pack_channels: List[str] = Field(default_factory=list)
    assigned_by: Optional[str] = None


class AgencySubscriptionAssignmentUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    assignment_status: Optional[AgencySubscriptionAssignmentStatus] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    manual_review_required: Optional[bool] = None
    visibility_flags: Optional[Dict[str, bool]] = None
    included_modules: Optional[List[str]] = None
    included_airline_intelligence_domains: Optional[List[str]] = None
    included_data_pack_channels: Optional[List[str]] = None
    updated_by: Optional[str] = None


class AgencyEntitlementReadinessCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: str
    assignment_id: Optional[str] = None
    plan_id: Optional[str] = None
    entitlement_scope: SaaSEntitlementScope = SaaSEntitlementScope.MODULE
    entitlement_key: str
    status: AgencyEntitlementReadinessStatus = AgencyEntitlementReadinessStatus.NEEDS_REVIEW
    crm_ready: bool = False
    cms_ready: bool = False
    client_portal_ready: bool = False
    offer_builder_ready: bool = False
    airline_intelligence_ready: bool = False
    manual_review_required: bool = False
    plain_language_summary: Optional[str] = None
    calculated_by: Optional[str] = None


class AgencySubscriptionReviewNoteCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: str
    assignment_id: Optional[str] = None
    plan_id: Optional[str] = None
    note_type: AgencySubscriptionReviewNoteType = AgencySubscriptionReviewNoteType.AGENCY_VISIBLE
    note: str
    created_by: Optional[str] = None
    visible_to_agency: bool = False


class AgencySubscriptionSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    assignment_id: Optional[str] = None
    plan_id: Optional[str] = None
    snapshot_type: AgencySubscriptionSnapshotType = AgencySubscriptionSnapshotType.MANUAL
    snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None


class AgencyFeatureFlag(BaseDocument):
    agency_id: str
    module_key: str
    feature_key: str
    display_name: str
    state: AgencyFeatureFlagState = AgencyFeatureFlagState.DISABLED
    visibility_note: Optional[str] = None
    metadata_only: bool = True
    automatic_enforcement_disabled: bool = True


class AgencyFeatureFlagReview(BaseDocument):
    agency_id: str
    reviewer: Optional[str] = None
    notes: str
    metadata_only: bool = True


class AgencyFeatureFlagSnapshot(BaseDocument):
    agency_id: str
    snapshot_date: datetime = Field(default_factory=now_utc)
    immutable_json: Dict[str, Any] = Field(default_factory=dict)
    immutable: bool = True
    metadata_only: bool = True


class AgencyFeatureFlagAudit(BaseDocument):
    agency_id: str
    feature_key: str
    previous_state: Optional[AgencyFeatureFlagState] = None
    proposed_state: AgencyFeatureFlagState = AgencyFeatureFlagState.DISABLED
    changed_by: Optional[str] = None
    changed_at: datetime = Field(default_factory=now_utc)
    reason: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    automatic_enforcement_disabled: bool = True
    feature_blocking_disabled: bool = True


class AgencyFeatureFlagReadiness(BaseDocument):
    agency_id: str
    feature_key: str
    documentation_complete: bool = False
    ui_complete: bool = False
    backend_complete: bool = False
    api_complete: bool = False
    testing_complete: bool = False
    deployment_ready: bool = False
    rollout_ready: bool = False
    last_reviewed: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    metadata_only: bool = True
    automatic_enforcement_disabled: bool = True
    feature_blocking_disabled: bool = True


class FeatureFlagBundleMember(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    module_key: str
    feature_key: str
    display_name: str
    description: Optional[str] = None
    metadata_only: bool = True


class BundleReadiness(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    documentation_complete: bool = False
    bundle_review_complete: bool = False
    member_flags_reviewed: bool = False
    agency_visibility_reviewed: bool = False
    testing_complete: bool = False
    deployment_ready: bool = False
    rollout_ready: bool = False
    last_reviewed: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    metadata_only: bool = True


class FeatureFlagBundle(BaseDocument):
    bundle_key: str
    bundle_name: str
    description: Optional[str] = None
    category: str = "general"
    members: List[FeatureFlagBundleMember] = Field(default_factory=list)
    review_status: str = "draft"
    readiness: BundleReadiness = Field(default_factory=BundleReadiness)
    visible_to_agencies: bool = True
    metadata_only: bool = True
    runtime_enforcement_disabled: bool = True
    entitlement_checks_disabled: bool = True
    rollout_disabled: bool = True


class FeatureFlagBundleSummary(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    bundle_id: str
    bundle_key: str
    bundle_name: str
    description: Optional[str] = None
    category: str = "general"
    flag_count: int = 0
    review_status: str = "draft"
    readiness: BundleReadiness = Field(default_factory=BundleReadiness)
    last_updated: Optional[datetime] = None
    metadata_only: bool = True


class FeatureFlagBundleReview(BaseDocument):
    bundle_id: Optional[str] = None
    bundle_key: str
    reviewer: Optional[str] = None
    review_status: str = "draft"
    notes: Optional[str] = None
    metadata_only: bool = True


class AgencyFeatureBundleAssignment(BaseDocument):
    assignment_id: str = Field(default_factory=new_id)
    agency_id: str
    bundle_id: str
    assigned_by: Optional[str] = None
    assigned_at: datetime = Field(default_factory=now_utc)
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: str = "assigned"
    notes: Optional[str] = None
    review_status: str = "pending_review"
    metadata_only: bool = True
    activation_logic_disabled: bool = True
    entitlement_enforcement_disabled: bool = True
    billing_disabled: bool = True


class AgencyFeatureBundleAssignmentCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    assignment_id: Optional[str] = None
    agency_id: Optional[str] = None
    bundle_id: str
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: str = "assigned"
    notes: Optional[str] = None
    review_status: str = "pending_review"


class AgencyFeatureBundleAssignmentUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    bundle_id: Optional[str] = None
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    review_status: Optional[str] = None


class AgencyFeatureBundleAssignmentHistory(BaseDocument):
    assignment_id: str
    agency_id: str
    bundle_id: str
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: str = "assigned"
    notes: Optional[str] = None
    review_status: str = "pending_review"
    history_event: str = "recorded"
    changed_by: Optional[str] = None
    changed_at: datetime = Field(default_factory=now_utc)
    metadata_only: bool = True
    activation_logic_disabled: bool = True


class FeatureBundleRolloutReadinessStatus(str, Enum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    READY = "ready"
    BLOCKED = "blocked"


class FeatureBundleRolloutChecklistStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    WARNING = "warning"
    BLOCKED = "blocked"


class FeatureBundleRolloutChecklistItem(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    item_key: str
    label: str
    status: FeatureBundleRolloutChecklistStatus = FeatureBundleRolloutChecklistStatus.PENDING
    notes: Optional[str] = None
    metadata_only: bool = True


class FeatureBundleRolloutReadiness(BaseDocument):
    agency_id: str
    bundle_id: str
    assignment_id: str
    readiness_status: FeatureBundleRolloutReadinessStatus = FeatureBundleRolloutReadinessStatus.DRAFT
    checklist_items: List[FeatureBundleRolloutChecklistItem] = Field(default_factory=list)
    notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    metadata_only: bool = True
    activation_logic_disabled: bool = True
    feature_access_enforcement_disabled: bool = True
    billing_disabled: bool = True
    provider_execution_disabled: bool = True


class FeatureBundleRolloutPlanStage(str, Enum):
    DRAFT = "draft"
    READINESS_REVIEW = "readiness_review"
    SCHEDULED = "scheduled"
    PAUSED = "paused"
    ARCHIVED = "archived"


class FeatureBundleRolloutPlan(BaseDocument):
    rollout_plan_id: str = Field(default_factory=new_id)
    agency_id: str
    bundle_id: str
    plan_name: str
    rollout_stage: FeatureBundleRolloutPlanStage = FeatureBundleRolloutPlanStage.DRAFT
    target_start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    rollout_owner: Optional[str] = None
    checklist_summary: Dict[str, Any] = Field(default_factory=dict)
    readiness_snapshot_id: Optional[str] = None
    assigned_bundle_id: Optional[str] = None
    notes: Optional[str] = None
    metadata_only: bool = True
    rollout_execution_disabled: bool = True
    feature_activation_disabled: bool = True
    feature_access_enforcement_disabled: bool = True
    billing_disabled: bool = True
    provider_execution_disabled: bool = True


class FeatureBundleRolloutPlanCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rollout_plan_id: Optional[str] = None
    agency_id: str
    bundle_id: str
    plan_name: str
    rollout_stage: FeatureBundleRolloutPlanStage = FeatureBundleRolloutPlanStage.DRAFT
    target_start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    rollout_owner: Optional[str] = None
    checklist_summary: Dict[str, Any] = Field(default_factory=dict)
    readiness_snapshot_id: Optional[str] = None
    assigned_bundle_id: Optional[str] = None
    notes: Optional[str] = None


class FeatureBundleRolloutPlanUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    bundle_id: Optional[str] = None
    plan_name: Optional[str] = None
    rollout_stage: Optional[FeatureBundleRolloutPlanStage] = None
    target_start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    rollout_owner: Optional[str] = None
    checklist_summary: Optional[Dict[str, Any]] = None
    readiness_snapshot_id: Optional[str] = None
    assigned_bundle_id: Optional[str] = None
    notes: Optional[str] = None


class FeatureBundleRolloutApprovalStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class FeatureBundleRolloutApprovalSummary(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    total_count: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    draft_count: int = 0
    submitted_count: int = 0
    under_review_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    archived_count: int = 0
    metadata_only: bool = True
    read_only: bool = True


class FeatureBundleRolloutApprovalTimelineEntry(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    timeline_entry_id: str = Field(default_factory=new_id)
    approval_id: Optional[str] = None
    rollout_plan_id: str
    agency_id: str
    event_type: str
    status: Optional[FeatureBundleRolloutApprovalStatus] = None
    actor: Optional[str] = None
    occurred_at: datetime = Field(default_factory=now_utc)
    notes: Optional[str] = None
    metadata_only: bool = True
    execution_disabled: bool = True


class FeatureBundleRolloutApproval(BaseDocument):
    approval_id: str = Field(default_factory=new_id)
    rollout_plan_id: str
    agency_id: str
    bundle_id: Optional[str] = None
    status: FeatureBundleRolloutApprovalStatus = FeatureBundleRolloutApprovalStatus.DRAFT
    reviewer: Optional[str] = None
    submitted_by: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    approval_summary: FeatureBundleRolloutApprovalSummary = Field(default_factory=FeatureBundleRolloutApprovalSummary)
    timeline: List[FeatureBundleRolloutApprovalTimelineEntry] = Field(default_factory=list)
    notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    metadata_only: bool = True
    approval_metadata_only: bool = True
    feature_enablement_disabled: bool = True
    feature_activation_disabled: bool = True
    route_blocking_disabled: bool = True
    runtime_gating_disabled: bool = True
    permission_enforcement_disabled: bool = True
    billing_disabled: bool = True
    payments_disabled: bool = True
    stripe_disabled: bool = True
    payment_provider_disabled: bool = True
    provider_execution_disabled: bool = True
    external_api_calls_disabled: bool = True
    authentication_changes_disabled: bool = True
    deployment_automation_disabled: bool = True
    rollout_execution_disabled: bool = True
    background_workers_disabled: bool = True
    cron_disabled: bool = True
    webhook_execution_disabled: bool = True
    email_sending_disabled: bool = True
    sms_sending_disabled: bool = True
    notifications_disabled: bool = True
    ai_execution_disabled: bool = True
    openai_disabled: bool = True
    scraping_disabled: bool = True
    publishing_disabled: bool = True


class FeatureBundleRolloutApprovalNote(BaseDocument):
    note_id: str = Field(default_factory=new_id)
    approval_id: str
    rollout_plan_id: str
    agency_id: str
    note_text: str
    note_type: str = "review_note"
    author: Optional[str] = None
    agency_visible: bool = True
    metadata_only: bool = True
    read_only_for_agency: bool = True
    execution_disabled: bool = True


class FeatureBundleRolloutApprovalCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rollout_plan_id: str
    agency_id: Optional[str] = None
    status: FeatureBundleRolloutApprovalStatus = FeatureBundleRolloutApprovalStatus.DRAFT
    reviewer: Optional[str] = None
    submitted_by: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    notes: Optional[str] = None


class FeatureBundleRolloutApprovalUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: Optional[FeatureBundleRolloutApprovalStatus] = None
    reviewer: Optional[str] = None
    submitted_by: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    notes: Optional[str] = None


class FeatureBundleRolloutApprovalNoteCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    note_text: str
    note_type: str = "review_note"
    agency_visible: bool = True


class FeatureBundleRolloutScheduleStatus(str, Enum):
    PLANNED = "Planned"
    READY = "Ready"
    AWAITING_APPROVAL = "AwaitingApproval"
    APPROVED = "Approved"
    DEFERRED = "Deferred"
    CANCELLED = "Cancelled"
    COMPLETED_METADATA = "CompletedMetadata"


class FeatureBundleRolloutSchedule(BaseDocument):
    schedule_id: str = Field(default_factory=new_id)
    rollout_plan_id: str
    rollout_name: str
    bundle_id: str
    agency_id: str
    schedule_status: FeatureBundleRolloutScheduleStatus = FeatureBundleRolloutScheduleStatus.PLANNED
    planned_start: Optional[datetime] = None
    planned_finish: Optional[datetime] = None
    scheduling_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    maintenance_window: Optional[str] = None
    estimated_duration: Optional[str] = None
    dependency_summary: Dict[str, Any] = Field(default_factory=dict)
    checklist_summary: Dict[str, Any] = Field(default_factory=dict)
    approval_summary: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    scheduling_metadata_only: bool = True
    read_only_planning: bool = True
    rollout_execution_disabled: bool = True
    feature_activation_disabled: bool = True
    entitlement_behavior_disabled: bool = True
    permission_changes_disabled: bool = True
    cron_jobs_disabled: bool = True
    schedulers_disabled: bool = True
    workers_disabled: bool = True
    queues_disabled: bool = True
    timers_disabled: bool = True
    background_execution_disabled: bool = True
    external_api_calls_disabled: bool = True
    ai_execution_disabled: bool = True
    billing_disabled: bool = True
    publishing_disabled: bool = True
    automation_disabled: bool = True


class FeatureBundleRolloutScheduleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rollout_plan_id: str
    rollout_name: Optional[str] = None
    agency_id: Optional[str] = None
    bundle_id: Optional[str] = None
    schedule_status: FeatureBundleRolloutScheduleStatus = FeatureBundleRolloutScheduleStatus.PLANNED
    planned_start: Optional[datetime] = None
    planned_finish: Optional[datetime] = None
    scheduling_notes: Optional[str] = None
    maintenance_window: Optional[str] = None
    estimated_duration: Optional[str] = None
    dependency_summary: Dict[str, Any] = Field(default_factory=dict)
    checklist_summary: Dict[str, Any] = Field(default_factory=dict)
    approval_summary: Dict[str, Any] = Field(default_factory=dict)


class FeatureBundleRolloutScheduleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rollout_name: Optional[str] = None
    schedule_status: Optional[FeatureBundleRolloutScheduleStatus] = None
    planned_start: Optional[datetime] = None
    planned_finish: Optional[datetime] = None
    scheduling_notes: Optional[str] = None
    maintenance_window: Optional[str] = None
    estimated_duration: Optional[str] = None
    dependency_summary: Optional[Dict[str, Any]] = None
    checklist_summary: Optional[Dict[str, Any]] = None
    approval_summary: Optional[Dict[str, Any]] = None


class FeatureBundleRolloutEventType(str, Enum):
    PLAN_CREATED = "plan_created"
    PLAN_EDITED = "plan_edited"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    SCHEDULE_CREATED = "schedule_created"
    SCHEDULE_CHANGED = "schedule_changed"
    ROLLOUT_STARTED = "rollout_started"
    ROLLOUT_COMPLETED = "rollout_completed"
    ROLLBACK_PLANNED = "rollback_planned"
    NOTE_ADDED = "note_added"


class FeatureBundleRolloutActor(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    actor_id: Optional[str] = None
    actor_type: str = "platform_user"
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    metadata_only: bool = True
    permission_changes_disabled: bool = True


class FeatureBundleRolloutTimelineEntry(BaseDocument):
    timeline_entry_id: str = Field(default_factory=new_id)
    rollout_plan_id: str
    agency_id: str
    bundle_id: Optional[str] = None
    event_type: FeatureBundleRolloutEventType
    event_label: Optional[str] = None
    actor: FeatureBundleRolloutActor = Field(default_factory=FeatureBundleRolloutActor)
    occurred_at: datetime = Field(default_factory=now_utc)
    description: Optional[str] = None
    source: str = "platform_metadata"
    related_schedule_id: Optional[str] = None
    related_approval_id: Optional[str] = None
    related_assignment_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    timeline_metadata_only: bool = True
    feature_bundle_enablement_disabled: bool = True
    agency_permission_changes_disabled: bool = True
    rollout_plan_execution_disabled: bool = True
    background_jobs_disabled: bool = True
    provider_calls_disabled: bool = True
    email_sending_disabled: bool = True
    notification_sending_disabled: bool = True
    rollout_state_enforcement_disabled: bool = True
    subscription_modification_disabled: bool = True
    automation_disabled: bool = True
    publishing_disabled: bool = True


class FeatureBundleRolloutTimelineEntryCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    timeline_entry_id: Optional[str] = None
    rollout_plan_id: str
    agency_id: Optional[str] = None
    bundle_id: Optional[str] = None
    event_type: FeatureBundleRolloutEventType
    event_label: Optional[str] = None
    actor: Optional[FeatureBundleRolloutActor] = None
    occurred_at: Optional[datetime] = None
    description: Optional[str] = None
    source: str = "platform_metadata"
    related_schedule_id: Optional[str] = None
    related_approval_id: Optional[str] = None
    related_assignment_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureBundleDependencyType(str, Enum):
    BUNDLE = "bundle"
    CAPABILITY = "capability"
    APPROVAL = "approval"
    ROLLOUT_PLAN = "rollout_plan"
    SCHEDULE = "schedule"
    READINESS_CHECKLIST = "readiness_checklist"
    OTHER = "other"


class FeatureBundleDependencyReference(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    reference_type: FeatureBundleDependencyType
    reference_id: str
    label: Optional[str] = None
    bundle_id: Optional[str] = None
    capability_key: Optional[str] = None
    rollout_plan_id: Optional[str] = None
    schedule_id: Optional[str] = None
    approval_id: Optional[str] = None
    readiness_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    dependency_enforcement_disabled: bool = True


class FeatureBundleDependency(BaseDocument):
    dependency_id: str = Field(default_factory=new_id)
    agency_id: str
    bundle_id: str
    rollout_plan_id: Optional[str] = None
    dependency_type: FeatureBundleDependencyType
    depends_on: FeatureBundleDependencyReference
    status: str = "informational"
    notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    dependency_metadata_only: bool = True
    dependency_enforcement_disabled: bool = True
    rollout_execution_disabled: bool = True
    background_jobs_disabled: bool = True
    rollout_blocking_disabled: bool = True
    feature_bundle_activation_disabled: bool = True
    permission_modification_disabled: bool = True
    notification_sending_disabled: bool = True
    publishing_disabled: bool = True
    provider_calls_disabled: bool = True
    automation_disabled: bool = True


class FeatureBundleDependencyCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    dependency_id: Optional[str] = None
    agency_id: str
    bundle_id: str
    rollout_plan_id: Optional[str] = None
    dependency_type: FeatureBundleDependencyType
    depends_on: FeatureBundleDependencyReference
    status: str = "informational"
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureBundleDependencyUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rollout_plan_id: Optional[str] = None
    dependency_type: Optional[FeatureBundleDependencyType] = None
    depends_on: Optional[FeatureBundleDependencyReference] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureBundleRolloutRiskImpact(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeatureBundleRolloutRiskLikelihood(str, Enum):
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


class FeatureBundleRolloutRiskStatus(str, Enum):
    OPEN = "open"
    REVIEWING = "reviewing"
    MITIGATING = "mitigating"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"
    DELETED = "deleted"


class FeatureBundleRolloutRisk(BaseDocument):
    risk_id: str = Field(default_factory=new_id)
    agency_id: Optional[str] = None
    bundle_id: Optional[str] = None
    rollout_plan_id: Optional[str] = None
    dependency_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    impact: FeatureBundleRolloutRiskImpact = FeatureBundleRolloutRiskImpact.MEDIUM
    likelihood: FeatureBundleRolloutRiskLikelihood = FeatureBundleRolloutRiskLikelihood.POSSIBLE
    status: FeatureBundleRolloutRiskStatus = FeatureBundleRolloutRiskStatus.OPEN
    mitigation_notes: Optional[str] = None
    owner: Optional[str] = None
    review_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    risk_register_metadata_only: bool = True
    rollout_execution_disabled: bool = True
    risk_decision_enforcement_disabled: bool = True
    risk_blocking_disabled: bool = True
    feature_bundle_activation_disabled: bool = True
    notification_sending_disabled: bool = True
    external_provider_calls_disabled: bool = True
    automation_disabled: bool = True


class FeatureBundleRolloutRiskCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    risk_id: Optional[str] = None
    agency_id: Optional[str] = None
    bundle_id: Optional[str] = None
    rollout_plan_id: Optional[str] = None
    dependency_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    impact: FeatureBundleRolloutRiskImpact = FeatureBundleRolloutRiskImpact.MEDIUM
    likelihood: FeatureBundleRolloutRiskLikelihood = FeatureBundleRolloutRiskLikelihood.POSSIBLE
    status: FeatureBundleRolloutRiskStatus = FeatureBundleRolloutRiskStatus.OPEN
    mitigation_notes: Optional[str] = None
    owner: Optional[str] = None
    review_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureBundleRolloutRiskUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    bundle_id: Optional[str] = None
    rollout_plan_id: Optional[str] = None
    dependency_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    impact: Optional[FeatureBundleRolloutRiskImpact] = None
    likelihood: Optional[FeatureBundleRolloutRiskLikelihood] = None
    status: Optional[FeatureBundleRolloutRiskStatus] = None
    mitigation_notes: Optional[str] = None
    owner: Optional[str] = None
    review_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureBundleRolloutIssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeatureBundleRolloutIssueStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    FOLLOW_UP = "follow_up"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DELETED = "deleted"


class FeatureBundleRolloutIssue(BaseDocument):
    issue_id: str = Field(default_factory=new_id)
    agency_id: Optional[str] = None
    bundle_id: Optional[str] = None
    rollout_plan_id: Optional[str] = None
    risk_id: Optional[str] = None
    dependency_id: Optional[str] = None
    approval_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: FeatureBundleRolloutIssueSeverity = FeatureBundleRolloutIssueSeverity.MEDIUM
    status: FeatureBundleRolloutIssueStatus = FeatureBundleRolloutIssueStatus.OPEN
    owner: Optional[str] = None
    resolution_notes: Optional[str] = None
    review_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    issue_log_metadata_only: bool = True
    rollout_execution_disabled: bool = True
    feature_bundle_activation_disabled: bool = True
    rollout_blocking_disabled: bool = True
    blocking_enforcement_disabled: bool = True
    notification_sending_disabled: bool = True
    external_provider_calls_disabled: bool = True
    ai_provider_execution_disabled: bool = True
    automation_disabled: bool = True


class FeatureBundleRolloutIssueCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    issue_id: Optional[str] = None
    agency_id: Optional[str] = None
    bundle_id: Optional[str] = None
    rollout_plan_id: Optional[str] = None
    risk_id: Optional[str] = None
    dependency_id: Optional[str] = None
    approval_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: FeatureBundleRolloutIssueSeverity = FeatureBundleRolloutIssueSeverity.MEDIUM
    status: FeatureBundleRolloutIssueStatus = FeatureBundleRolloutIssueStatus.OPEN
    owner: Optional[str] = None
    resolution_notes: Optional[str] = None
    review_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureBundleRolloutIssueUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    bundle_id: Optional[str] = None
    rollout_plan_id: Optional[str] = None
    risk_id: Optional[str] = None
    dependency_id: Optional[str] = None
    approval_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[FeatureBundleRolloutIssueSeverity] = None
    status: Optional[FeatureBundleRolloutIssueStatus] = None
    owner: Optional[str] = None
    resolution_notes: Optional[str] = None
    review_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureBundleRolloutDecisionCategory(str, Enum):
    READINESS = "readiness"
    APPROVAL = "approval"
    SCHEDULE = "schedule"
    DEPENDENCY = "dependency"
    RISK = "risk"
    ISSUE = "issue"
    ROLLOUT_SCOPE = "rollout_scope"
    OPERATIONAL = "operational"
    GOVERNANCE = "governance"


class FeatureBundleRolloutDecisionStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class FeatureBundleRolloutDecision(BaseDocument):
    rollout_plan_id: str
    rollout_phase: Optional[str] = None
    decision_title: str
    decision_summary: Optional[str] = None
    decision_reason: Optional[str] = None
    decision_category: FeatureBundleRolloutDecisionCategory = FeatureBundleRolloutDecisionCategory.OPERATIONAL
    decision_status: FeatureBundleRolloutDecisionStatus = FeatureBundleRolloutDecisionStatus.DRAFT
    decision_owner: Optional[str] = None
    decision_date: datetime = Field(default_factory=now_utc)
    related_bundle_ids: List[str] = Field(default_factory=list)
    related_dependency_ids: List[str] = Field(default_factory=list)
    related_risk_ids: List[str] = Field(default_factory=list)
    related_issue_ids: List[str] = Field(default_factory=list)
    timeline_reference_ids: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    decision_register_metadata_only: bool = True
    rollout_execution_disabled: bool = True
    deployment_automation_disabled: bool = True
    feature_activation_disabled: bool = True
    entitlement_enforcement_disabled: bool = True
    billing_disabled: bool = True
    provider_integrations_disabled: bool = True
    external_api_calls_disabled: bool = True
    ai_execution_disabled: bool = True
    background_workers_disabled: bool = True
    schedulers_disabled: bool = True
    notification_sending_disabled: bool = True
    email_sending_disabled: bool = True
    webhook_execution_disabled: bool = True
    publishing_disabled: bool = True
    runtime_switching_disabled: bool = True
    automation_disabled: bool = True


class FeatureBundleRolloutDecisionCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: Optional[str] = None
    rollout_plan_id: str
    rollout_phase: Optional[str] = None
    decision_title: str
    decision_summary: Optional[str] = None
    decision_reason: Optional[str] = None
    decision_category: FeatureBundleRolloutDecisionCategory = FeatureBundleRolloutDecisionCategory.OPERATIONAL
    decision_status: FeatureBundleRolloutDecisionStatus = FeatureBundleRolloutDecisionStatus.DRAFT
    decision_owner: Optional[str] = None
    decision_date: Optional[datetime] = None
    related_bundle_ids: List[str] = Field(default_factory=list)
    related_dependency_ids: List[str] = Field(default_factory=list)
    related_risk_ids: List[str] = Field(default_factory=list)
    related_issue_ids: List[str] = Field(default_factory=list)
    timeline_reference_ids: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureBundleRolloutDecisionUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rollout_plan_id: Optional[str] = None
    rollout_phase: Optional[str] = None
    decision_title: Optional[str] = None
    decision_summary: Optional[str] = None
    decision_reason: Optional[str] = None
    decision_category: Optional[FeatureBundleRolloutDecisionCategory] = None
    decision_status: Optional[FeatureBundleRolloutDecisionStatus] = None
    decision_owner: Optional[str] = None
    decision_date: Optional[datetime] = None
    related_bundle_ids: Optional[List[str]] = None
    related_dependency_ids: Optional[List[str]] = None
    related_risk_ids: Optional[List[str]] = None
    related_issue_ids: Optional[List[str]] = None
    timeline_reference_ids: Optional[List[str]] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureBundleRolloutChangeRequestType(str, Enum):
    SCOPE = "scope"
    SCHEDULE = "schedule"
    READINESS = "readiness"
    APPROVAL = "approval"
    DEPENDENCY = "dependency"
    RISK = "risk"
    ISSUE = "issue"
    DECISION = "decision"
    DOCUMENTATION = "documentation"
    OPERATIONAL = "operational"


class FeatureBundleRolloutChangeRequestPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FeatureBundleRolloutChangeRequestImpactLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeatureBundleRolloutChangeRequestStatus(str, Enum):
    DRAFT = "draft"
    REQUESTED = "requested"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class FeatureBundleRolloutChangeRequest(BaseDocument):
    rollout_plan_id: str
    rollout_phase: Optional[str] = None
    change_title: str
    change_summary: Optional[str] = None
    change_reason: Optional[str] = None
    requested_by: Optional[str] = None
    requested_date: datetime = Field(default_factory=now_utc)
    change_type: FeatureBundleRolloutChangeRequestType = FeatureBundleRolloutChangeRequestType.OPERATIONAL
    priority: FeatureBundleRolloutChangeRequestPriority = FeatureBundleRolloutChangeRequestPriority.MEDIUM
    impact_level: FeatureBundleRolloutChangeRequestImpactLevel = FeatureBundleRolloutChangeRequestImpactLevel.MEDIUM
    change_status: FeatureBundleRolloutChangeRequestStatus = FeatureBundleRolloutChangeRequestStatus.DRAFT
    affected_bundle_ids: List[str] = Field(default_factory=list)
    affected_feature_flag_ids: List[str] = Field(default_factory=list)
    related_decision_ids: List[str] = Field(default_factory=list)
    related_issue_ids: List[str] = Field(default_factory=list)
    related_risk_ids: List[str] = Field(default_factory=list)
    related_dependency_ids: List[str] = Field(default_factory=list)
    review_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    change_request_metadata_only: bool = True
    rollout_execution_disabled: bool = True
    deployment_automation_disabled: bool = True
    feature_activation_disabled: bool = True
    entitlement_enforcement_disabled: bool = True
    billing_disabled: bool = True
    provider_integrations_disabled: bool = True
    external_api_calls_disabled: bool = True
    ai_execution_disabled: bool = True
    background_workers_disabled: bool = True
    schedulers_disabled: bool = True
    notification_sending_disabled: bool = True
    email_sending_disabled: bool = True
    webhook_execution_disabled: bool = True
    publishing_disabled: bool = True
    runtime_switching_disabled: bool = True
    automation_disabled: bool = True


class FeatureBundleRolloutChangeRequestCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: Optional[str] = None
    rollout_plan_id: str
    rollout_phase: Optional[str] = None
    change_title: str
    change_summary: Optional[str] = None
    change_reason: Optional[str] = None
    requested_by: Optional[str] = None
    requested_date: Optional[datetime] = None
    change_type: FeatureBundleRolloutChangeRequestType = FeatureBundleRolloutChangeRequestType.OPERATIONAL
    priority: FeatureBundleRolloutChangeRequestPriority = FeatureBundleRolloutChangeRequestPriority.MEDIUM
    impact_level: FeatureBundleRolloutChangeRequestImpactLevel = FeatureBundleRolloutChangeRequestImpactLevel.MEDIUM
    change_status: FeatureBundleRolloutChangeRequestStatus = FeatureBundleRolloutChangeRequestStatus.DRAFT
    affected_bundle_ids: List[str] = Field(default_factory=list)
    affected_feature_flag_ids: List[str] = Field(default_factory=list)
    related_decision_ids: List[str] = Field(default_factory=list)
    related_issue_ids: List[str] = Field(default_factory=list)
    related_risk_ids: List[str] = Field(default_factory=list)
    related_dependency_ids: List[str] = Field(default_factory=list)
    review_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureBundleRolloutChangeRequestUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rollout_plan_id: Optional[str] = None
    rollout_phase: Optional[str] = None
    change_title: Optional[str] = None
    change_summary: Optional[str] = None
    change_reason: Optional[str] = None
    requested_by: Optional[str] = None
    requested_date: Optional[datetime] = None
    change_type: Optional[FeatureBundleRolloutChangeRequestType] = None
    priority: Optional[FeatureBundleRolloutChangeRequestPriority] = None
    impact_level: Optional[FeatureBundleRolloutChangeRequestImpactLevel] = None
    change_status: Optional[FeatureBundleRolloutChangeRequestStatus] = None
    affected_bundle_ids: Optional[List[str]] = None
    affected_feature_flag_ids: Optional[List[str]] = None
    related_decision_ids: Optional[List[str]] = None
    related_issue_ids: Optional[List[str]] = None
    related_risk_ids: Optional[List[str]] = None
    related_dependency_ids: Optional[List[str]] = None
    review_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureBundleRolloutRollbackTrigger(str, Enum):
    MANUAL_REVIEW = "manual_review"
    ISSUE_DETECTED = "issue_detected"
    RISK_THRESHOLD = "risk_threshold"
    DEPENDENCY_UNREADY = "dependency_unready"
    AGENCY_REQUEST = "agency_request"
    SCHEDULE_CONFLICT = "schedule_conflict"
    OPERATIONAL_CONCERN = "operational_concern"
    DOCUMENTATION_GAP = "documentation_gap"
    FUTURE_RUNTIME_SIGNAL = "future_runtime_signal"


class FeatureBundleRolloutRollbackScope(str, Enum):
    BUNDLE = "bundle"
    FEATURE_FLAG = "feature_flag"
    AGENCY = "agency"
    DEPENDENCY = "dependency"
    SCHEDULE = "schedule"
    READINESS = "readiness"
    APPROVAL = "approval"
    OPERATIONAL = "operational"
    DOCUMENTATION = "documentation"


class FeatureBundleRolloutRollbackStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    READY = "ready"
    DEFERRED = "deferred"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class FeatureBundleRolloutRollbackPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FeatureBundleRolloutRollbackPlan(BaseDocument):
    rollout_plan_id: str
    rollout_phase: Optional[str] = None
    rollback_title: str
    rollback_summary: Optional[str] = None
    rollback_reason: Optional[str] = None
    rollback_trigger: FeatureBundleRolloutRollbackTrigger = FeatureBundleRolloutRollbackTrigger.MANUAL_REVIEW
    rollback_scope: FeatureBundleRolloutRollbackScope = FeatureBundleRolloutRollbackScope.BUNDLE
    rollback_status: FeatureBundleRolloutRollbackStatus = FeatureBundleRolloutRollbackStatus.DRAFT
    rollback_owner: Optional[str] = None
    rollback_priority: FeatureBundleRolloutRollbackPriority = FeatureBundleRolloutRollbackPriority.MEDIUM
    affected_bundle_ids: List[str] = Field(default_factory=list)
    affected_feature_flag_ids: List[str] = Field(default_factory=list)
    related_change_request_ids: List[str] = Field(default_factory=list)
    related_decision_ids: List[str] = Field(default_factory=list)
    related_issue_ids: List[str] = Field(default_factory=list)
    related_risk_ids: List[str] = Field(default_factory=list)
    related_dependency_ids: List[str] = Field(default_factory=list)
    rollback_steps: List[str] = Field(default_factory=list)
    validation_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    rollback_plan_metadata_only: bool = True
    rollout_execution_disabled: bool = True
    rollback_execution_disabled: bool = True
    deployment_automation_disabled: bool = True
    feature_activation_disabled: bool = True
    feature_deactivation_disabled: bool = True
    feature_bundle_activation_disabled: bool = True
    feature_bundle_deactivation_disabled: bool = True
    entitlement_enforcement_disabled: bool = True
    billing_disabled: bool = True
    provider_integrations_disabled: bool = True
    external_api_calls_disabled: bool = True
    ai_execution_disabled: bool = True
    background_workers_disabled: bool = True
    schedulers_disabled: bool = True
    notification_sending_disabled: bool = True
    email_sending_disabled: bool = True
    webhook_execution_disabled: bool = True
    publishing_disabled: bool = True
    runtime_switching_disabled: bool = True
    automation_disabled: bool = True


class FeatureBundleRolloutRollbackPlanCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: Optional[str] = None
    rollout_plan_id: str
    rollout_phase: Optional[str] = None
    rollback_title: str
    rollback_summary: Optional[str] = None
    rollback_reason: Optional[str] = None
    rollback_trigger: FeatureBundleRolloutRollbackTrigger = FeatureBundleRolloutRollbackTrigger.MANUAL_REVIEW
    rollback_scope: FeatureBundleRolloutRollbackScope = FeatureBundleRolloutRollbackScope.BUNDLE
    rollback_status: FeatureBundleRolloutRollbackStatus = FeatureBundleRolloutRollbackStatus.DRAFT
    rollback_owner: Optional[str] = None
    rollback_priority: FeatureBundleRolloutRollbackPriority = FeatureBundleRolloutRollbackPriority.MEDIUM
    affected_bundle_ids: List[str] = Field(default_factory=list)
    affected_feature_flag_ids: List[str] = Field(default_factory=list)
    related_change_request_ids: List[str] = Field(default_factory=list)
    related_decision_ids: List[str] = Field(default_factory=list)
    related_issue_ids: List[str] = Field(default_factory=list)
    related_risk_ids: List[str] = Field(default_factory=list)
    related_dependency_ids: List[str] = Field(default_factory=list)
    rollback_steps: List[str] = Field(default_factory=list)
    validation_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureBundleRolloutRollbackPlanUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rollout_plan_id: Optional[str] = None
    rollout_phase: Optional[str] = None
    rollback_title: Optional[str] = None
    rollback_summary: Optional[str] = None
    rollback_reason: Optional[str] = None
    rollback_trigger: Optional[FeatureBundleRolloutRollbackTrigger] = None
    rollback_scope: Optional[FeatureBundleRolloutRollbackScope] = None
    rollback_status: Optional[FeatureBundleRolloutRollbackStatus] = None
    rollback_owner: Optional[str] = None
    rollback_priority: Optional[FeatureBundleRolloutRollbackPriority] = None
    affected_bundle_ids: Optional[List[str]] = None
    affected_feature_flag_ids: Optional[List[str]] = None
    related_change_request_ids: Optional[List[str]] = None
    related_decision_ids: Optional[List[str]] = None
    related_issue_ids: Optional[List[str]] = None
    related_risk_ids: Optional[List[str]] = None
    related_dependency_ids: Optional[List[str]] = None
    rollback_steps: Optional[List[str]] = None
    validation_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureBundleRolloutSummaryPackStatus(str, Enum):
    DRAFT = "draft"
    ASSEMBLED = "assembled"
    REVIEWING = "reviewing"
    READY = "ready"
    ARCHIVED = "archived"


class FeatureBundleRolloutSummaryPackAudience(str, Enum):
    PLATFORM = "platform"
    AGENCY = "agency"
    OPERATIONS = "operations"
    COMPLIANCE = "compliance"
    EXECUTIVE = "executive"


class FeatureBundleRolloutSummaryPack(BaseDocument):
    rollout_plan_id: str
    pack_title: str
    pack_summary: Optional[str] = None
    pack_status: FeatureBundleRolloutSummaryPackStatus = FeatureBundleRolloutSummaryPackStatus.DRAFT
    generated_for_audience: FeatureBundleRolloutSummaryPackAudience = FeatureBundleRolloutSummaryPackAudience.PLATFORM
    covered_bundle_ids: List[str] = Field(default_factory=list)
    readiness_reference_ids: List[str] = Field(default_factory=list)
    approval_reference_ids: List[str] = Field(default_factory=list)
    schedule_reference_ids: List[str] = Field(default_factory=list)
    timeline_reference_ids: List[str] = Field(default_factory=list)
    dependency_reference_ids: List[str] = Field(default_factory=list)
    risk_reference_ids: List[str] = Field(default_factory=list)
    issue_reference_ids: List[str] = Field(default_factory=list)
    decision_reference_ids: List[str] = Field(default_factory=list)
    change_request_reference_ids: List[str] = Field(default_factory=list)
    rollback_plan_reference_ids: List[str] = Field(default_factory=list)
    evidence_notes: Optional[str] = None
    compliance_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    summary_pack_metadata_only: bool = True
    rollout_execution_disabled: bool = True
    deployment_automation_disabled: bool = True
    feature_activation_disabled: bool = True
    feature_deactivation_disabled: bool = True
    feature_bundle_activation_disabled: bool = True
    feature_bundle_deactivation_disabled: bool = True
    entitlement_enforcement_disabled: bool = True
    billing_disabled: bool = True
    provider_integrations_disabled: bool = True
    external_api_calls_disabled: bool = True
    ai_execution_disabled: bool = True
    background_workers_disabled: bool = True
    schedulers_disabled: bool = True
    notification_sending_disabled: bool = True
    email_sending_disabled: bool = True
    webhook_execution_disabled: bool = True
    publishing_disabled: bool = True
    runtime_switching_disabled: bool = True
    pdf_generation_disabled: bool = True
    file_export_disabled: bool = True
    automation_disabled: bool = True


class FeatureBundleRolloutSummaryPackCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: Optional[str] = None
    rollout_plan_id: str
    pack_title: str
    pack_summary: Optional[str] = None
    pack_status: FeatureBundleRolloutSummaryPackStatus = FeatureBundleRolloutSummaryPackStatus.DRAFT
    generated_for_audience: FeatureBundleRolloutSummaryPackAudience = FeatureBundleRolloutSummaryPackAudience.PLATFORM
    covered_bundle_ids: List[str] = Field(default_factory=list)
    readiness_reference_ids: List[str] = Field(default_factory=list)
    approval_reference_ids: List[str] = Field(default_factory=list)
    schedule_reference_ids: List[str] = Field(default_factory=list)
    timeline_reference_ids: List[str] = Field(default_factory=list)
    dependency_reference_ids: List[str] = Field(default_factory=list)
    risk_reference_ids: List[str] = Field(default_factory=list)
    issue_reference_ids: List[str] = Field(default_factory=list)
    decision_reference_ids: List[str] = Field(default_factory=list)
    change_request_reference_ids: List[str] = Field(default_factory=list)
    rollback_plan_reference_ids: List[str] = Field(default_factory=list)
    evidence_notes: Optional[str] = None
    compliance_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureBundleRolloutSummaryPackUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    rollout_plan_id: Optional[str] = None
    pack_title: Optional[str] = None
    pack_summary: Optional[str] = None
    pack_status: Optional[FeatureBundleRolloutSummaryPackStatus] = None
    generated_for_audience: Optional[FeatureBundleRolloutSummaryPackAudience] = None
    covered_bundle_ids: Optional[List[str]] = None
    readiness_reference_ids: Optional[List[str]] = None
    approval_reference_ids: Optional[List[str]] = None
    schedule_reference_ids: Optional[List[str]] = None
    timeline_reference_ids: Optional[List[str]] = None
    dependency_reference_ids: Optional[List[str]] = None
    risk_reference_ids: Optional[List[str]] = None
    issue_reference_ids: Optional[List[str]] = None
    decision_reference_ids: Optional[List[str]] = None
    change_request_reference_ids: Optional[List[str]] = None
    rollback_plan_reference_ids: Optional[List[str]] = None
    evidence_notes: Optional[str] = None
    compliance_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OperationalTravelWorkspaceType(str, Enum):
    GENERAL = "general"
    REQUEST = "request"
    TRIP = "trip"
    OFFER = "offer"
    BOOKING = "booking"
    TICKETING = "ticketing"
    DOCUMENTS = "documents"
    DISRUPTION = "disruption"
    SERVICE_CASE = "service_case"


class OperationalTravelWorkspaceStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    ACTIVE = "active"
    WAITING = "waiting"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class OperationalTravelWorkspacePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class OperationalTravelWorkspace(BaseDocument):
    agency_id: str
    workspace_reference: str
    workspace_title: str
    workspace_type: OperationalTravelWorkspaceType = OperationalTravelWorkspaceType.GENERAL
    workspace_status: OperationalTravelWorkspaceStatus = OperationalTravelWorkspaceStatus.OPEN
    primary_client_id: Optional[str] = None
    primary_passenger_id: Optional[str] = None
    linked_request_ids: List[str] = Field(default_factory=list)
    linked_trip_ids: List[str] = Field(default_factory=list)
    linked_offer_ids: List[str] = Field(default_factory=list)
    linked_booking_ids: List[str] = Field(default_factory=list)
    linked_ticket_ids: List[str] = Field(default_factory=list)
    linked_document_ids: List[str] = Field(default_factory=list)
    priority: OperationalTravelWorkspacePriority = OperationalTravelWorkspacePriority.MEDIUM
    assigned_team: List[str] = Field(default_factory=list)
    assigned_agent: Optional[str] = None
    travel_start_date: Optional[date] = None
    travel_end_date: Optional[date] = None
    origin_summary: Optional[str] = None
    destination_summary: Optional[str] = None
    service_summary: Optional[str] = None
    operational_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    operational_workspace_metadata_only: bool = True
    booking_execution_disabled: bool = True
    ticket_issuance_disabled: bool = True
    gds_live_connectivity_disabled: bool = True
    ndc_connectivity_disabled: bool = True
    payment_processing_disabled: bool = True
    email_sending_disabled: bool = True
    sms_sending_disabled: bool = True
    ai_automation_disabled: bool = True
    external_api_calls_disabled: bool = True
    supplier_integrations_disabled: bool = True
    live_airline_calls_disabled: bool = True
    background_workers_disabled: bool = True
    automation_disabled: bool = True


class OperationalTravelWorkspaceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: Optional[str] = None
    agency_id: str
    workspace_reference: Optional[str] = None
    workspace_title: str
    workspace_type: OperationalTravelWorkspaceType = OperationalTravelWorkspaceType.GENERAL
    workspace_status: OperationalTravelWorkspaceStatus = OperationalTravelWorkspaceStatus.OPEN
    primary_client_id: Optional[str] = None
    primary_passenger_id: Optional[str] = None
    linked_request_ids: List[str] = Field(default_factory=list)
    linked_trip_ids: List[str] = Field(default_factory=list)
    linked_offer_ids: List[str] = Field(default_factory=list)
    linked_booking_ids: List[str] = Field(default_factory=list)
    linked_ticket_ids: List[str] = Field(default_factory=list)
    linked_document_ids: List[str] = Field(default_factory=list)
    priority: OperationalTravelWorkspacePriority = OperationalTravelWorkspacePriority.MEDIUM
    assigned_team: List[str] = Field(default_factory=list)
    assigned_agent: Optional[str] = None
    travel_start_date: Optional[date] = None
    travel_end_date: Optional[date] = None
    origin_summary: Optional[str] = None
    destination_summary: Optional[str] = None
    service_summary: Optional[str] = None
    operational_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OperationalTravelWorkspaceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    workspace_reference: Optional[str] = None
    workspace_title: Optional[str] = None
    workspace_type: Optional[OperationalTravelWorkspaceType] = None
    workspace_status: Optional[OperationalTravelWorkspaceStatus] = None
    primary_client_id: Optional[str] = None
    primary_passenger_id: Optional[str] = None
    linked_request_ids: Optional[List[str]] = None
    linked_trip_ids: Optional[List[str]] = None
    linked_offer_ids: Optional[List[str]] = None
    linked_booking_ids: Optional[List[str]] = None
    linked_ticket_ids: Optional[List[str]] = None
    linked_document_ids: Optional[List[str]] = None
    priority: Optional[OperationalTravelWorkspacePriority] = None
    assigned_team: Optional[List[str]] = None
    assigned_agent: Optional[str] = None
    travel_start_date: Optional[date] = None
    travel_end_date: Optional[date] = None
    origin_summary: Optional[str] = None
    destination_summary: Optional[str] = None
    service_summary: Optional[str] = None
    operational_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TravelRequestWorkspaceType(str, Enum):
    GENERAL = "general"
    FLIGHT = "flight"
    HOTEL = "hotel"
    PACKAGE = "package"
    MULTI_CITY = "multi_city"
    GROUP = "group"
    CORPORATE = "corporate"
    LEISURE = "leisure"
    DISRUPTION = "disruption"
    SERVICE = "service"


class TravelRequestWorkspaceStatus(str, Enum):
    DRAFT = "draft"
    NEW = "new"
    TRIAGE = "triage"
    OPEN = "open"
    RESEARCHING = "researching"
    WAITING = "waiting"
    QUOTED = "quoted"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TravelRequestWorkspacePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TravelRequestWorkspace(BaseDocument):
    agency_id: str
    operational_workspace_id: str
    request_reference: str
    request_title: str
    request_type: TravelRequestWorkspaceType = TravelRequestWorkspaceType.GENERAL
    request_status: TravelRequestWorkspaceStatus = TravelRequestWorkspaceStatus.NEW
    request_priority: TravelRequestWorkspacePriority = TravelRequestWorkspacePriority.MEDIUM
    client_id: Optional[str] = None
    primary_passenger_id: Optional[str] = None
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    requester_phone: Optional[str] = None
    requested_service_categories: List[str] = Field(default_factory=list)
    requested_origin: Optional[str] = None
    requested_destination: Optional[str] = None
    requested_departure_date: Optional[date] = None
    requested_return_date: Optional[date] = None
    passenger_count: int = 1
    passenger_type_summary: Optional[str] = None
    flexibility_notes: Optional[str] = None
    special_service_notes: Optional[str] = None
    budget_notes: Optional[str] = None
    deadline: Optional[date] = None
    assigned_agent: Optional[str] = None
    internal_notes: Optional[str] = None
    linked_trip_ids: List[str] = Field(default_factory=list)
    linked_offer_ids: List[str] = Field(default_factory=list)
    linked_document_ids: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    travel_request_workspace_metadata_only: bool = True
    booking_execution_disabled: bool = True
    ticket_issuance_disabled: bool = True
    gds_live_connectivity_disabled: bool = True
    ndc_connectivity_disabled: bool = True
    payment_processing_disabled: bool = True
    email_sending_disabled: bool = True
    sms_sending_disabled: bool = True
    ai_automation_disabled: bool = True
    external_api_calls_disabled: bool = True
    supplier_integrations_disabled: bool = True
    live_airline_calls_disabled: bool = True
    background_workers_disabled: bool = True
    automatic_trip_creation_disabled: bool = True
    automatic_offer_creation_disabled: bool = True
    automation_disabled: bool = True


class TravelRequestWorkspaceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: Optional[str] = None
    agency_id: str
    operational_workspace_id: str
    request_reference: Optional[str] = None
    request_title: str
    request_type: TravelRequestWorkspaceType = TravelRequestWorkspaceType.GENERAL
    request_status: TravelRequestWorkspaceStatus = TravelRequestWorkspaceStatus.NEW
    request_priority: TravelRequestWorkspacePriority = TravelRequestWorkspacePriority.MEDIUM
    client_id: Optional[str] = None
    primary_passenger_id: Optional[str] = None
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    requester_phone: Optional[str] = None
    requested_service_categories: List[str] = Field(default_factory=list)
    requested_origin: Optional[str] = None
    requested_destination: Optional[str] = None
    requested_departure_date: Optional[date] = None
    requested_return_date: Optional[date] = None
    passenger_count: int = 1
    passenger_type_summary: Optional[str] = None
    flexibility_notes: Optional[str] = None
    special_service_notes: Optional[str] = None
    budget_notes: Optional[str] = None
    deadline: Optional[date] = None
    assigned_agent: Optional[str] = None
    internal_notes: Optional[str] = None
    linked_trip_ids: List[str] = Field(default_factory=list)
    linked_offer_ids: List[str] = Field(default_factory=list)
    linked_document_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TravelRequestWorkspaceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    operational_workspace_id: Optional[str] = None
    request_reference: Optional[str] = None
    request_title: Optional[str] = None
    request_type: Optional[TravelRequestWorkspaceType] = None
    request_status: Optional[TravelRequestWorkspaceStatus] = None
    request_priority: Optional[TravelRequestWorkspacePriority] = None
    client_id: Optional[str] = None
    primary_passenger_id: Optional[str] = None
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    requester_phone: Optional[str] = None
    requested_service_categories: Optional[List[str]] = None
    requested_origin: Optional[str] = None
    requested_destination: Optional[str] = None
    requested_departure_date: Optional[date] = None
    requested_return_date: Optional[date] = None
    passenger_count: Optional[int] = None
    passenger_type_summary: Optional[str] = None
    flexibility_notes: Optional[str] = None
    special_service_notes: Optional[str] = None
    budget_notes: Optional[str] = None
    deadline: Optional[date] = None
    assigned_agent: Optional[str] = None
    internal_notes: Optional[str] = None
    linked_trip_ids: Optional[List[str]] = None
    linked_offer_ids: Optional[List[str]] = None
    linked_document_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class PassengerWorkspaceStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INCOMPLETE = "incomplete"
    REVIEW = "review"
    READY = "ready"
    ARCHIVED = "archived"


class PassengerWorkspace(BaseDocument):
    agency_id: str
    operational_workspace_id: Optional[str] = None
    passenger_reference: str
    passenger_status: PassengerWorkspaceStatus = PassengerWorkspaceStatus.ACTIVE
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    citizenship: Optional[str] = None
    passport_number: Optional[str] = None
    passport_expiry: Optional[date] = None
    passport_country: Optional[str] = None
    identity_document_type: Optional[str] = None
    loyalty_programs: List[Dict[str, Any]] = Field(default_factory=list)
    frequent_flyer_numbers: List[Dict[str, Any]] = Field(default_factory=list)
    known_traveler_numbers: List[str] = Field(default_factory=list)
    emergency_contact: Dict[str, Any] = Field(default_factory=dict)
    mobility_profile: Dict[str, Any] = Field(default_factory=dict)
    medical_profile: Dict[str, Any] = Field(default_factory=dict)
    dietary_profile: Dict[str, Any] = Field(default_factory=dict)
    assistance_profile: Dict[str, Any] = Field(default_factory=dict)
    baggage_profile: Dict[str, Any] = Field(default_factory=dict)
    seating_preferences: Dict[str, Any] = Field(default_factory=dict)
    language_preferences: List[str] = Field(default_factory=list)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    linked_request_ids: List[str] = Field(default_factory=list)
    linked_trip_ids: List[str] = Field(default_factory=list)
    linked_offer_ids: List[str] = Field(default_factory=list)
    linked_booking_ids: List[str] = Field(default_factory=list)
    linked_ticket_ids: List[str] = Field(default_factory=list)
    linked_document_ids: List[str] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    passenger_workspace_metadata_only: bool = True
    booking_execution_disabled: bool = True
    ticket_issuance_disabled: bool = True
    gds_connectivity_disabled: bool = True
    gds_live_connectivity_disabled: bool = True
    ndc_connectivity_disabled: bool = True
    payment_processing_disabled: bool = True
    supplier_integrations_disabled: bool = True
    ai_disabled: bool = True
    ai_automation_disabled: bool = True
    email_disabled: bool = True
    email_sending_disabled: bool = True
    sms_disabled: bool = True
    sms_sending_disabled: bool = True
    background_workers_disabled: bool = True
    external_api_calls_disabled: bool = True
    automatic_profile_matching_disabled: bool = True
    automatic_document_validation_disabled: bool = True
    document_validation_disabled: bool = True
    airline_communication_disabled: bool = True
    automation_disabled: bool = True


class PassengerWorkspaceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: Optional[str] = None
    agency_id: str
    operational_workspace_id: Optional[str] = None
    passenger_reference: Optional[str] = None
    passenger_status: PassengerWorkspaceStatus = PassengerWorkspaceStatus.ACTIVE
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    citizenship: Optional[str] = None
    passport_number: Optional[str] = None
    passport_expiry: Optional[date] = None
    passport_country: Optional[str] = None
    identity_document_type: Optional[str] = None
    loyalty_programs: List[Dict[str, Any]] = Field(default_factory=list)
    frequent_flyer_numbers: List[Dict[str, Any]] = Field(default_factory=list)
    known_traveler_numbers: List[str] = Field(default_factory=list)
    emergency_contact: Dict[str, Any] = Field(default_factory=dict)
    mobility_profile: Dict[str, Any] = Field(default_factory=dict)
    medical_profile: Dict[str, Any] = Field(default_factory=dict)
    dietary_profile: Dict[str, Any] = Field(default_factory=dict)
    assistance_profile: Dict[str, Any] = Field(default_factory=dict)
    baggage_profile: Dict[str, Any] = Field(default_factory=dict)
    seating_preferences: Dict[str, Any] = Field(default_factory=dict)
    language_preferences: List[str] = Field(default_factory=list)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    linked_request_ids: List[str] = Field(default_factory=list)
    linked_trip_ids: List[str] = Field(default_factory=list)
    linked_offer_ids: List[str] = Field(default_factory=list)
    linked_booking_ids: List[str] = Field(default_factory=list)
    linked_ticket_ids: List[str] = Field(default_factory=list)
    linked_document_ids: List[str] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PassengerWorkspaceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    operational_workspace_id: Optional[str] = None
    passenger_reference: Optional[str] = None
    passenger_status: Optional[PassengerWorkspaceStatus] = None
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    citizenship: Optional[str] = None
    passport_number: Optional[str] = None
    passport_expiry: Optional[date] = None
    passport_country: Optional[str] = None
    identity_document_type: Optional[str] = None
    loyalty_programs: Optional[List[Dict[str, Any]]] = None
    frequent_flyer_numbers: Optional[List[Dict[str, Any]]] = None
    known_traveler_numbers: Optional[List[str]] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    mobility_profile: Optional[Dict[str, Any]] = None
    medical_profile: Optional[Dict[str, Any]] = None
    dietary_profile: Optional[Dict[str, Any]] = None
    assistance_profile: Optional[Dict[str, Any]] = None
    baggage_profile: Optional[Dict[str, Any]] = None
    seating_preferences: Optional[Dict[str, Any]] = None
    language_preferences: Optional[List[str]] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    linked_request_ids: Optional[List[str]] = None
    linked_trip_ids: Optional[List[str]] = None
    linked_offer_ids: Optional[List[str]] = None
    linked_booking_ids: Optional[List[str]] = None
    linked_ticket_ids: Optional[List[str]] = None
    linked_document_ids: Optional[List[str]] = None
    internal_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FlightWorkspaceStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SCHEDULE_REVIEW = "schedule_review"
    READY = "ready"
    FLOWN = "flown"
    ARCHIVED = "archived"


class FlightWorkspace(BaseDocument):
    agency_id: str
    operational_workspace_id: Optional[str] = None
    flight_reference: str
    flight_status: FlightWorkspaceStatus = FlightWorkspaceStatus.ACTIVE
    flight_type: Optional[str] = None
    travel_direction: Optional[str] = None
    airline_code: Optional[str] = None
    airline_name: Optional[str] = None
    marketing_carrier: Optional[str] = None
    operating_carrier: Optional[str] = None
    flight_number: Optional[str] = None
    operating_flight_number: Optional[str] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    departure_terminal: Optional[str] = None
    arrival_terminal: Optional[str] = None
    departure_datetime: Optional[datetime] = None
    arrival_datetime: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    cabin_class: Optional[str] = None
    booking_class: Optional[str] = None
    fare_family: Optional[str] = None
    baggage_summary: Optional[str] = None
    connection_summary: Optional[str] = None
    stopover_summary: Optional[str] = None
    elapsed_travel_time: Optional[str] = None
    operating_days: List[str] = Field(default_factory=list)
    passenger_ids: List[str] = Field(default_factory=list)
    linked_request_ids: List[str] = Field(default_factory=list)
    linked_trip_ids: List[str] = Field(default_factory=list)
    linked_offer_ids: List[str] = Field(default_factory=list)
    linked_booking_ids: List[str] = Field(default_factory=list)
    linked_ticket_ids: List[str] = Field(default_factory=list)
    linked_document_ids: List[str] = Field(default_factory=list)
    operational_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    flight_workspace_metadata_only: bool = True
    booking_execution_disabled: bool = True
    live_flight_search_disabled: bool = True
    flight_search_disabled: bool = True
    gds_connectivity_disabled: bool = True
    ndc_connectivity_disabled: bool = True
    airline_apis_disabled: bool = True
    airline_api_calls_disabled: bool = True
    payment_disabled: bool = True
    payment_processing_disabled: bool = True
    ticket_issuance_disabled: bool = True
    schedule_synchronization_disabled: bool = True
    external_api_calls_disabled: bool = True
    ai_disabled: bool = True
    background_workers_disabled: bool = True
    automatic_route_generation_disabled: bool = True
    flight_validation_disabled: bool = True
    airline_lookups_disabled: bool = True
    live_schedule_updates_disabled: bool = True
    automation_disabled: bool = True


class FlightWorkspaceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: Optional[str] = None
    agency_id: str
    operational_workspace_id: Optional[str] = None
    flight_reference: Optional[str] = None
    flight_status: FlightWorkspaceStatus = FlightWorkspaceStatus.ACTIVE
    flight_type: Optional[str] = None
    travel_direction: Optional[str] = None
    airline_code: Optional[str] = None
    airline_name: Optional[str] = None
    marketing_carrier: Optional[str] = None
    operating_carrier: Optional[str] = None
    flight_number: Optional[str] = None
    operating_flight_number: Optional[str] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    departure_terminal: Optional[str] = None
    arrival_terminal: Optional[str] = None
    departure_datetime: Optional[datetime] = None
    arrival_datetime: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    cabin_class: Optional[str] = None
    booking_class: Optional[str] = None
    fare_family: Optional[str] = None
    baggage_summary: Optional[str] = None
    connection_summary: Optional[str] = None
    stopover_summary: Optional[str] = None
    elapsed_travel_time: Optional[str] = None
    operating_days: List[str] = Field(default_factory=list)
    passenger_ids: List[str] = Field(default_factory=list)
    linked_request_ids: List[str] = Field(default_factory=list)
    linked_trip_ids: List[str] = Field(default_factory=list)
    linked_offer_ids: List[str] = Field(default_factory=list)
    linked_booking_ids: List[str] = Field(default_factory=list)
    linked_ticket_ids: List[str] = Field(default_factory=list)
    linked_document_ids: List[str] = Field(default_factory=list)
    operational_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FlightWorkspaceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    operational_workspace_id: Optional[str] = None
    flight_reference: Optional[str] = None
    flight_status: Optional[FlightWorkspaceStatus] = None
    flight_type: Optional[str] = None
    travel_direction: Optional[str] = None
    airline_code: Optional[str] = None
    airline_name: Optional[str] = None
    marketing_carrier: Optional[str] = None
    operating_carrier: Optional[str] = None
    flight_number: Optional[str] = None
    operating_flight_number: Optional[str] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    departure_terminal: Optional[str] = None
    arrival_terminal: Optional[str] = None
    departure_datetime: Optional[datetime] = None
    arrival_datetime: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    cabin_class: Optional[str] = None
    booking_class: Optional[str] = None
    fare_family: Optional[str] = None
    baggage_summary: Optional[str] = None
    connection_summary: Optional[str] = None
    stopover_summary: Optional[str] = None
    elapsed_travel_time: Optional[str] = None
    operating_days: Optional[List[str]] = None
    passenger_ids: Optional[List[str]] = None
    linked_request_ids: Optional[List[str]] = None
    linked_trip_ids: Optional[List[str]] = None
    linked_offer_ids: Optional[List[str]] = None
    linked_booking_ids: Optional[List[str]] = None
    linked_ticket_ids: Optional[List[str]] = None
    linked_document_ids: Optional[List[str]] = None
    operational_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TripWorkspaceStatus(str, Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    ACTIVE = "active"
    READY = "ready"
    TRAVELING = "traveling"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TripWorkspace(BaseDocument):
    agency_id: str
    operational_workspace_id: Optional[str] = None
    trip_reference: str
    trip_status: TripWorkspaceStatus = TripWorkspaceStatus.ACTIVE
    journey_type: Optional[str] = None
    service_type: Optional[str] = None
    client_id: Optional[str] = None
    passenger_ids: List[str] = Field(default_factory=list)
    flight_workspace_ids: List[str] = Field(default_factory=list)
    travel_request_ids: List[str] = Field(default_factory=list)
    offer_ids: List[str] = Field(default_factory=list)
    booking_ids: List[str] = Field(default_factory=list)
    ticket_ids: List[str] = Field(default_factory=list)
    emd_ids: List[str] = Field(default_factory=list)
    document_ids: List[str] = Field(default_factory=list)
    departure_country: Optional[str] = None
    destination_country: Optional[str] = None
    departure_city: Optional[str] = None
    destination_city: Optional[str] = None
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    travel_duration: Optional[str] = None
    passenger_count: Optional[int] = None
    itinerary_summary: Optional[str] = None
    baggage_summary: Optional[str] = None
    service_summary: Optional[str] = None
    operational_priority: Optional[str] = None
    assigned_agent: Optional[str] = None
    assigned_team: List[str] = Field(default_factory=list)
    operational_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    trip_workspace_metadata_only: bool = True
    booking_execution_disabled: bool = True
    ticket_issuance_disabled: bool = True
    gds_connectivity_disabled: bool = True
    ndc_connectivity_disabled: bool = True
    airline_apis_disabled: bool = True
    airline_api_calls_disabled: bool = True
    payment_processing_disabled: bool = True
    invoicing_disabled: bool = True
    ai_disabled: bool = True
    background_workers_disabled: bool = True
    automatic_trip_generation_disabled: bool = True
    automatic_itinerary_generation_disabled: bool = True
    itinerary_generation_disabled: bool = True
    external_integrations_disabled: bool = True
    external_api_calls_disabled: bool = True
    automation_disabled: bool = True


class TripWorkspaceCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    id: Optional[str] = None
    agency_id: str
    operational_workspace_id: Optional[str] = None
    trip_reference: Optional[str] = None
    trip_status: TripWorkspaceStatus = TripWorkspaceStatus.ACTIVE
    journey_type: Optional[str] = None
    service_type: Optional[str] = None
    client_id: Optional[str] = None
    passenger_ids: List[str] = Field(default_factory=list)
    flight_workspace_ids: List[str] = Field(default_factory=list)
    travel_request_ids: List[str] = Field(default_factory=list)
    offer_ids: List[str] = Field(default_factory=list)
    booking_ids: List[str] = Field(default_factory=list)
    ticket_ids: List[str] = Field(default_factory=list)
    emd_ids: List[str] = Field(default_factory=list)
    document_ids: List[str] = Field(default_factory=list)
    departure_country: Optional[str] = None
    destination_country: Optional[str] = None
    departure_city: Optional[str] = None
    destination_city: Optional[str] = None
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    travel_duration: Optional[str] = None
    passenger_count: Optional[int] = None
    itinerary_summary: Optional[str] = None
    baggage_summary: Optional[str] = None
    service_summary: Optional[str] = None
    operational_priority: Optional[str] = None
    assigned_agent: Optional[str] = None
    assigned_team: List[str] = Field(default_factory=list)
    operational_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TripWorkspaceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    operational_workspace_id: Optional[str] = None
    trip_reference: Optional[str] = None
    trip_status: Optional[TripWorkspaceStatus] = None
    journey_type: Optional[str] = None
    service_type: Optional[str] = None
    client_id: Optional[str] = None
    passenger_ids: Optional[List[str]] = None
    flight_workspace_ids: Optional[List[str]] = None
    travel_request_ids: Optional[List[str]] = None
    offer_ids: Optional[List[str]] = None
    booking_ids: Optional[List[str]] = None
    ticket_ids: Optional[List[str]] = None
    emd_ids: Optional[List[str]] = None
    document_ids: Optional[List[str]] = None
    departure_country: Optional[str] = None
    destination_country: Optional[str] = None
    departure_city: Optional[str] = None
    destination_city: Optional[str] = None
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    travel_duration: Optional[str] = None
    passenger_count: Optional[int] = None
    itinerary_summary: Optional[str] = None
    baggage_summary: Optional[str] = None
    service_summary: Optional[str] = None
    operational_priority: Optional[str] = None
    assigned_agent: Optional[str] = None
    assigned_team: Optional[List[str]] = None
    operational_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RolloutDashboardCounts(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    total_count: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_stage: Dict[str, int] = Field(default_factory=dict)
    warning_count: int = 0
    blocker_count: int = 0
    metadata_only: bool = True


class RolloutDashboardSection(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    section_key: str
    title: str
    description: Optional[str] = None
    count: int = 0
    counts: RolloutDashboardCounts = Field(default_factory=RolloutDashboardCounts)
    statuses: Dict[str, int] = Field(default_factory=dict)
    route: Optional[str] = None
    last_updated: Optional[datetime] = None
    read_only: bool = True
    metadata_only: bool = True


class RolloutDashboardFilters(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    bundle_id: Optional[str] = None
    feature_state: Optional[str] = None
    readiness_status: Optional[str] = None
    rollout_stage: Optional[str] = None
    capability_category: Optional[str] = None
    metadata_only: bool = True


class RolloutDashboardSummary(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: Optional[str] = None
    sections: List[RolloutDashboardSection] = Field(default_factory=list)
    counts: RolloutDashboardCounts = Field(default_factory=RolloutDashboardCounts)
    filters: RolloutDashboardFilters = Field(default_factory=RolloutDashboardFilters)
    generated_at: datetime = Field(default_factory=now_utc)
    read_only: bool = True
    metadata_only: bool = True


class RolloutDashboardSnapshot(BaseDocument):
    snapshot_id: str = Field(default_factory=new_id)
    agency_id: Optional[str] = None
    filters: RolloutDashboardFilters = Field(default_factory=RolloutDashboardFilters)
    sections: List[RolloutDashboardSection] = Field(default_factory=list)
    counts: RolloutDashboardCounts = Field(default_factory=RolloutDashboardCounts)
    captured_at: datetime = Field(default_factory=now_utc)
    captured_by: Optional[str] = None
    source: str = "rollout_dashboard_metadata"
    read_only: bool = True
    metadata_only: bool = True
    automation_disabled: bool = True
    rollout_execution_disabled: bool = True
    feature_activation_disabled: bool = True
    billing_disabled: bool = True
    provider_execution_disabled: bool = True


class CapabilityCatalogEntry(BaseDocument):
    code: str
    name: str
    description: Optional[str] = None
    category: str = "general"
    module: str = "general"
    status: str = "active"
    visibility: str = "platform_and_agency"
    tags: List[str] = Field(default_factory=list)
    required_feature_flags: List[str] = Field(default_factory=list)
    required_bundles: List[str] = Field(default_factory=list)
    recommended_bundles: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    ui_routes: List[str] = Field(default_factory=list)
    documentation_links: List[str] = Field(default_factory=list)
    introduced_phase: str = "phase_40_1_capability_catalog_foundation"
    deprecated: bool = False
    notes: Optional[str] = None
    metadata_only: bool = True
    execution_logic_disabled: bool = True
    entitlement_enforcement_disabled: bool = True


class AgencyFeatureFlagCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: str
    module_key: str
    feature_key: str
    display_name: str
    state: AgencyFeatureFlagState = AgencyFeatureFlagState.DISABLED
    visibility_note: Optional[str] = None


class AgencyFeatureFlagUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    module_key: Optional[str] = None
    feature_key: Optional[str] = None
    display_name: Optional[str] = None
    state: Optional[AgencyFeatureFlagState] = None
    visibility_note: Optional[str] = None


class AgencyFeatureFlagReviewCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: str
    reviewer: Optional[str] = None
    notes: str


class AgencyFeatureFlagSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    agency_id: str
    snapshot_date: Optional[datetime] = None
    immutable_json: Dict[str, Any] = Field(default_factory=dict)


class AirlineBrandAsset(BaseDocument):
    airline_id: str
    asset_type: AirlineBrandAssetType = AirlineBrandAssetType.OTHER
    label: str
    asset_url: Optional[str] = None
    asset_json: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True


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
    READY_TO_ISSUE = "ready_to_issue"
    ISSUED = "issued"
    VOIDED = "voided"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"
    CANCELLED = "cancelled"


class TicketType(str, Enum):
    ETICKET = "eticket"
    PAPER = "paper"
    MANUAL_MIRROR = "manual_mirror"
    OTHER = "other"


class TicketCouponStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CHECKED_IN = "checked_in"
    FLOWN = "flown"
    EXCHANGED = "exchanged"
    REFUNDED = "refunded"
    VOIDED = "voided"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class EmdType(str, Enum):
    EMD_S = "emd_s"
    EMD_A = "emd_a"
    MANUAL_MIRROR = "manual_mirror"
    UNKNOWN = "unknown"


class EmdStatus(str, Enum):
    DRAFT = "draft"
    READY_TO_ISSUE = "ready_to_issue"
    ISSUED = "issued"
    VOIDED = "voided"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"
    CANCELLED = "cancelled"


class EmdCouponStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    USED = "used"
    EXCHANGED = "exchanged"
    REFUNDED = "refunded"
    VOIDED = "voided"
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
    booking_id: Optional[str] = None
    source_context: TicketSourceContext = TicketSourceContext.BOOKING_RECORD
    trip_id: Optional[str] = None
    client_id: Optional[str] = None
    request_id: Optional[str] = None
    booking_workspace_id: Optional[str] = None
    booking_record_id: Optional[str] = None
    passenger_id: Optional[str] = None
    original_ticket_record_id: Optional[str] = None
    exchange_operation_id: Optional[str] = None
    import_draft_id: Optional[str] = None
    booking_passenger_id: Optional[str] = None
    passenger_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    ticket_number: Optional[str] = None
    validating_airline_code: Optional[str] = None
    validating_carrier: Optional[str] = None
    issuing_provider: BookingProviderTarget = BookingProviderTarget.MANUAL
    issue_date: Optional[date] = None
    status: TicketStatus = TicketStatus.DRAFT
    issue_status: TicketStatus = TicketStatus.DRAFT
    ticket_type: TicketType = TicketType.MANUAL_MIRROR
    base_fare_amount: Optional[float] = 0
    taxes_amount: Optional[float] = 0
    total_amount: Optional[float] = 0
    currency: Optional[str] = "EUR"
    fare_basis: Optional[str] = None
    coupon_summary: Optional[str] = None
    pricing_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    fare_basis_json: Dict[str, Any] = Field(default_factory=dict)
    fare_bundle_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    rules_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    segments_snapshot_json: List[Dict[str, Any]] = Field(default_factory=list)
    coupons_json: List[Dict[str, Any]] = Field(default_factory=list)
    provider_payload_json: Dict[str, Any] = Field(default_factory=dict)
    provider_response_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    issued_at: Optional[datetime] = None
    voided_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    exchanged_at: Optional[datetime] = None
    created_by_user_id: Optional[str] = None
    updated_by_user_id: Optional[str] = None


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
    validating_carrier: Optional[str] = None
    issue_status: Optional[TicketStatus] = None
    pricing_snapshot_json: Optional[Dict[str, Any]] = None
    provider_payload_json: Optional[Dict[str, Any]] = None
    provider_response_json: Optional[Dict[str, Any]] = None


class TicketCoupon(BaseDocument):
    agency_id: str
    ticket_record_id: str
    booking_record_id: Optional[str] = None
    booking_workspace_id: Optional[str] = None
    trip_id: Optional[str] = None
    passenger_id: Optional[str] = None
    segment_id: Optional[str] = None
    coupon_number: int
    marketing_carrier: Optional[str] = None
    operating_carrier: Optional[str] = None
    flight_number: Optional[str] = None
    origin_airport_code: Optional[str] = None
    destination_airport_code: Optional[str] = None
    departure_at: Optional[datetime] = None
    arrival_at: Optional[datetime] = None
    cabin: Optional[str] = None
    rbd: Optional[str] = None
    fare_basis: Optional[str] = None
    coupon_status: TicketCouponStatus = TicketCouponStatus.DRAFT
    segment_snapshot_json: Dict[str, Any] = Field(default_factory=dict)


class TicketCreateFromBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    booking_record_id: str
    passenger_id: Optional[str] = None
    create_coupons: bool = True
    internal_notes: Optional[str] = None


class ManualTicketCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    booking_record_id: Optional[str] = None
    booking_workspace_id: Optional[str] = None
    trip_id: Optional[str] = None
    client_id: Optional[str] = None
    passenger_id: Optional[str] = None
    passenger_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    segments_snapshot_json: List[Dict[str, Any]] = Field(default_factory=list)
    pricing_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    ticket_number: Optional[str] = None
    validating_carrier: Optional[str] = None
    issuing_provider: BookingProviderTarget = BookingProviderTarget.MANUAL
    issue_status: TicketStatus = TicketStatus.DRAFT
    currency: Optional[str] = None
    base_fare_amount: Optional[float] = None
    taxes_amount: Optional[float] = None
    total_amount: Optional[float] = None
    internal_notes: Optional[str] = None
    create_coupons: bool = True
    source_context: TicketSourceContext = TicketSourceContext.STANDALONE_MANUAL
    original_ticket_record_id: Optional[str] = None
    exchange_operation_id: Optional[str] = None
    import_draft_id: Optional[str] = None


class EMDRecord(BaseDocument):
    agency_id: str
    booking_id: Optional[str] = None
    source_context: EmdSourceContext = EmdSourceContext.BOOKING_SERVICE
    trip_id: Optional[str] = None
    client_id: Optional[str] = None
    request_id: Optional[str] = None
    booking_workspace_id: Optional[str] = None
    booking_record_id: Optional[str] = None
    passenger_id: Optional[str] = None
    original_emd_record_id: Optional[str] = None
    exchange_operation_id: Optional[str] = None
    import_draft_id: Optional[str] = None
    booking_passenger_id: Optional[str] = None
    ticket_id: Optional[str] = None
    ticket_record_id: Optional[str] = None
    passenger_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    service_code: Optional[str] = None
    service_name: Optional[str] = None
    emd_number: Optional[str] = None
    emd_type: EmdType = EmdType.UNKNOWN
    rfic_code: Optional[str] = None
    rfisc_code: Optional[str] = None
    reason_for_issuance_code: Optional[str] = None
    reason_for_issuance_subcode: Optional[str] = None
    reason_for_issuance: Optional[str] = None
    service_key: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    service_label: Optional[str] = None
    service_category: Optional[str] = None
    linked_service_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    linked_segment_ids: List[str] = Field(default_factory=list)
    linked_ticket_coupon_ids: List[str] = Field(default_factory=list)
    issuing_provider: BookingProviderTarget = BookingProviderTarget.MANUAL
    issue_date: Optional[date] = None
    status: EmdStatus = EmdStatus.DRAFT
    issue_status: EmdStatus = EmdStatus.DRAFT
    amount: Optional[float] = 0
    taxes_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "EUR"
    associated_segment_ids: List[str] = Field(default_factory=list)
    pricing_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    provider_payload_json: Dict[str, Any] = Field(default_factory=dict)
    provider_response_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    issued_at: Optional[datetime] = None
    voided_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    exchanged_at: Optional[datetime] = None
    created_by_user_id: Optional[str] = None
    updated_by_user_id: Optional[str] = None


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


class EmdRecordUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    emd_number: Optional[str] = None
    emd_type: Optional[EmdType] = None
    reason_for_issuance_code: Optional[str] = None
    reason_for_issuance_subcode: Optional[str] = None
    issue_status: Optional[EmdStatus] = None
    currency: Optional[str] = None
    amount: Optional[float] = None
    taxes_amount: Optional[float] = None
    total_amount: Optional[float] = None
    pricing_snapshot_json: Optional[Dict[str, Any]] = None
    provider_payload_json: Optional[Dict[str, Any]] = None
    provider_response_json: Optional[Dict[str, Any]] = None
    internal_notes: Optional[str] = None


class EmdCoupon(BaseDocument):
    agency_id: str
    emd_record_id: str
    booking_record_id: Optional[str] = None
    booking_workspace_id: Optional[str] = None
    trip_id: Optional[str] = None
    passenger_id: Optional[str] = None
    segment_id: Optional[str] = None
    ticket_coupon_id: Optional[str] = None
    coupon_number: int
    service_key: Optional[str] = None
    service_label: Optional[str] = None
    service_category: Optional[str] = None
    coupon_status: EmdCouponStatus = EmdCouponStatus.DRAFT
    service_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    segment_snapshot_json: Dict[str, Any] = Field(default_factory=dict)


class EmdCreateFromBookingServiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    booking_record_id: str
    passenger_id: Optional[str] = None
    service_key: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    linked_segment_ids: Optional[List[str]] = None
    ticket_record_id: Optional[str] = None
    create_coupons: bool = True
    internal_notes: Optional[str] = None


class ManualEmdCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    booking_record_id: Optional[str] = None
    booking_workspace_id: Optional[str] = None
    ticket_record_id: Optional[str] = None
    trip_id: Optional[str] = None
    client_id: Optional[str] = None
    passenger_id: Optional[str] = None
    service_key: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    service_label: Optional[str] = None
    service_category: Optional[str] = None
    linked_service_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    linked_segment_ids: List[str] = Field(default_factory=list)
    linked_ticket_coupon_ids: List[str] = Field(default_factory=list)
    emd_number: Optional[str] = None
    emd_type: EmdType = EmdType.MANUAL_MIRROR
    issue_status: EmdStatus = EmdStatus.DRAFT
    currency: Optional[str] = None
    amount: Optional[float] = None
    taxes_amount: Optional[float] = None
    total_amount: Optional[float] = None
    internal_notes: Optional[str] = None
    create_coupons: bool = True
    source_context: EmdSourceContext = EmdSourceContext.STANDALONE_MANUAL
    original_emd_record_id: Optional[str] = None
    exchange_operation_id: Optional[str] = None
    import_draft_id: Optional[str] = None


class TicketEmdTimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    agency_id: str
    booking_workspace_id: Optional[str] = None
    booking_record_id: Optional[str] = None
    ticket_record_id: Optional[str] = None
    emd_record_id: Optional[str] = None
    trip_id: Optional[str] = None
    event_type: str
    title: str
    description: Optional[str] = None
    actor_user_id: Optional[str] = None
    payload_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)


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
    booking_id: Optional[str] = None
    booking_workspace_id: Optional[str] = None
    booking_record_id: Optional[str] = None
    trip_id: Optional[str] = None
    event_type: str
    actor_user_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    summary: Optional[str] = None
    visibility: Visibility = Visibility.INTERNAL
    payload_json: Dict[str, Any] = Field(default_factory=dict)
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


class RulesGovernanceStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class UnifiedExceptionCategory(str, Enum):
    PETS = "PETS"
    SERVICE_ANIMAL = "SERVICE_ANIMAL"
    UMNR = "UMNR"
    PRM = "PRM"
    MEDICAL = "MEDICAL"
    CARGO = "CARGO"
    VIP = "VIP"
    SEATING = "SEATING"
    MEAL = "MEAL"
    REFUND = "REFUND"
    REBOOK = "REBOOK"
    GENERAL = "GENERAL"


class UnifiedExceptionAction(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    WARN = "WARN"
    REQUIRE_DOC = "REQUIRE_DOC"
    OVERRIDE = "OVERRIDE"


class PassengerServiceCategory(str, Enum):
    UMNR = "UMNR"
    PRM = "PRM"
    MEDICAL = "MEDICAL"
    PETS = "PETS"
    SERVICE_ANIMAL = "SERVICE_ANIMAL"
    CARGO = "CARGO"
    VIP = "VIP"
    SEATING = "SEATING"
    MEAL = "MEAL"
    OTHER = "OTHER"


class PassengerServiceRequestStatus(str, Enum):
    REQUESTED = "requested"
    VALIDATED = "validated"
    BLOCKED = "blocked"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AirlineIntelligenceProfile(BaseDocument):
    airline_id: Optional[str] = None
    iata_code: Optional[str] = None
    icao_code: Optional[str] = None
    numeric_code: Optional[str] = None
    legal_name: Optional[str] = None
    alliance: Optional[str] = None
    headquarters: Optional[str] = None
    base_country: Optional[str] = None
    hubs_json: List[Dict[str, Any]] = Field(default_factory=list)
    subsidiaries_json: List[Dict[str, Any]] = Field(default_factory=list)
    group_membership: Optional[str] = None
    operational_notes: Optional[str] = None
    brand_assets_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineIntelligenceProfileCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_id: Optional[str] = None
    iata_code: Optional[str] = None
    icao_code: Optional[str] = None
    numeric_code: Optional[str] = None
    legal_name: Optional[str] = None
    alliance: Optional[str] = None
    headquarters: Optional[str] = None
    base_country: Optional[str] = None
    hubs_json: List[Dict[str, Any]] = Field(default_factory=list)
    subsidiaries_json: List[Dict[str, Any]] = Field(default_factory=list)
    group_membership: Optional[str] = None
    operational_notes: Optional[str] = None
    brand_assets_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineIntelligenceProfileUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_id: Optional[str] = None
    iata_code: Optional[str] = None
    icao_code: Optional[str] = None
    numeric_code: Optional[str] = None
    legal_name: Optional[str] = None
    alliance: Optional[str] = None
    headquarters: Optional[str] = None
    base_country: Optional[str] = None
    hubs_json: Optional[List[Dict[str, Any]]] = None
    subsidiaries_json: Optional[List[Dict[str, Any]]] = None
    group_membership: Optional[str] = None
    operational_notes: Optional[str] = None
    brand_assets_json: Optional[Dict[str, Any]] = None
    source_metadata_json: Optional[Dict[str, Any]] = None
    governance_status: Optional[RulesGovernanceStatus] = None


class AirlineContact(BaseDocument):
    airline_id: str
    contact_type: str
    label: str
    value: Optional[str] = None
    region_scope: Optional[str] = None
    service_scope: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineFleetType(BaseDocument):
    airline_id: str
    aircraft_type: str
    manufacturer: Optional[str] = None
    model_name: Optional[str] = None
    fleet_notes: Optional[str] = None
    capabilities_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AircraftTailNumber(BaseDocument):
    airline_id: str
    fleet_type_id: Optional[str] = None
    aircraft_type: Optional[str] = None
    tail_number: str
    registration_country: Optional[str] = None
    status: str = "active"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AircraftConfiguration(BaseDocument):
    airline_id: str
    fleet_type_id: Optional[str] = None
    aircraft_type: str
    configuration_name: str
    cabin_layout_json: Dict[str, Any] = Field(default_factory=dict)
    service_capabilities_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AircraftSeatmap(BaseDocument):
    airline_id: str
    aircraft_configuration_id: Optional[str] = None
    aircraft_type: Optional[str] = None
    seatmap_json: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineRoute(BaseDocument):
    airline_id: str
    origin_airport_code: str
    destination_airport_code: str
    operating_airline_id: Optional[str] = None
    aircraft_types_json: List[Dict[str, Any]] = Field(default_factory=list)
    schedule_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    restrictions_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineFareFamily(BaseDocument):
    airline_id: str
    family_code: str
    family_name: str
    cabin: Optional[str] = None
    benefits_json: Dict[str, Any] = Field(default_factory=dict)
    restrictions_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineRbdMatrixRow(BaseDocument):
    airline_id: str
    rbd_code: str
    cabin: Optional[str] = None
    fare_family_code: Optional[str] = None
    rules_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineFareRule(BaseDocument):
    airline_id: str
    rule_code: Optional[str] = None
    fare_family_code: Optional[str] = None
    rbd_code: Optional[str] = None
    rule_category: str = "general"
    rules_json: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineAncillary(BaseDocument):
    airline_id: str
    service_code: str
    service_name: str
    category: Optional[str] = None
    pricing_json: Dict[str, Any] = Field(default_factory=dict)
    fulfillment_json: Dict[str, Any] = Field(default_factory=dict)
    restrictions_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineInterlineAgreement(BaseDocument):
    airline_id: str
    partner_airline_id: Optional[str] = None
    partner_iata_code: Optional[str] = None
    agreement_type: str = "interline"
    scope_json: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineDistributionProfile(BaseDocument):
    airline_id: str
    channels_json: Dict[str, Any] = Field(default_factory=dict)
    ndc_json: Dict[str, Any] = Field(default_factory=dict)
    gds_json: Dict[str, Any] = Field(default_factory=dict)
    servicing_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlinePssParameters(BaseDocument):
    airline_id: str
    pss_name: Optional[str] = None
    parameters_json: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineGdsParameters(BaseDocument):
    airline_id: str
    gds_code: str
    parameters_json: Dict[str, Any] = Field(default_factory=dict)
    ticketing_json: Dict[str, Any] = Field(default_factory=dict)
    servicing_json: Dict[str, Any] = Field(default_factory=dict)
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineExceptionRule(BaseDocument):
    airline_id: str
    category: str
    rule_name: str
    condition_json: Dict[str, Any] = Field(default_factory=dict)
    action_json: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    active: bool = True
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class AirlineRulesCore(BaseDocument):
    airline_id: str
    iata_code: Optional[str] = None
    umnr_rules_json: Dict[str, Any] = Field(default_factory=dict)
    prm_rules_json: Dict[str, Any] = Field(default_factory=dict)
    medical_rules_json: Dict[str, Any] = Field(default_factory=dict)
    pets_service_animals_rules_json: Dict[str, Any] = Field(default_factory=dict)
    pos_rules_json: Dict[str, Any] = Field(default_factory=dict)
    musical_instruments_rules_json: Dict[str, Any] = Field(default_factory=dict)
    weapons_regulated_items_rules_json: Dict[str, Any] = Field(default_factory=dict)
    cargo_oversized_rules_json: Dict[str, Any] = Field(default_factory=dict)
    vip_protocol_rules_json: Dict[str, Any] = Field(default_factory=dict)
    baggage_rules_json: Dict[str, Any] = Field(default_factory=dict)
    seating_rules_json: Dict[str, Any] = Field(default_factory=dict)
    meal_rules_json: Dict[str, Any] = Field(default_factory=dict)
    general_notes: Optional[str] = None
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT
    created_by_user_id: Optional[str] = None
    updated_by_user_id: Optional[str] = None


class AirlineRulesCorePayload(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    airline_id: Optional[str] = None
    iata_code: Optional[str] = None
    umnr_rules_json: Dict[str, Any] = Field(default_factory=dict)
    prm_rules_json: Dict[str, Any] = Field(default_factory=dict)
    medical_rules_json: Dict[str, Any] = Field(default_factory=dict)
    pets_service_animals_rules_json: Dict[str, Any] = Field(default_factory=dict)
    pos_rules_json: Dict[str, Any] = Field(default_factory=dict)
    musical_instruments_rules_json: Dict[str, Any] = Field(default_factory=dict)
    weapons_regulated_items_rules_json: Dict[str, Any] = Field(default_factory=dict)
    cargo_oversized_rules_json: Dict[str, Any] = Field(default_factory=dict)
    vip_protocol_rules_json: Dict[str, Any] = Field(default_factory=dict)
    baggage_rules_json: Dict[str, Any] = Field(default_factory=dict)
    seating_rules_json: Dict[str, Any] = Field(default_factory=dict)
    meal_rules_json: Dict[str, Any] = Field(default_factory=dict)
    general_notes: Optional[str] = None
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    governance_status: RulesGovernanceStatus = RulesGovernanceStatus.DRAFT


class UnifiedExceptionRule(BaseDocument):
    category: UnifiedExceptionCategory
    service_key: Optional[str] = None
    service_catalogue_category: Optional[str] = None
    airline_id: Optional[str] = None
    iata_code: Optional[str] = None
    airport_code: Optional[str] = None
    route_origin: Optional[str] = None
    route_destination: Optional[str] = None
    aircraft_type: Optional[str] = None
    condition_expression: Optional[Any] = None
    action: UnifiedExceptionAction
    required_documents_json: List[Dict[str, Any]] = Field(default_factory=list)
    notes: Optional[str] = None
    priority: int = 100
    active: bool = True
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)


class UnifiedExceptionRuleCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    category: UnifiedExceptionCategory
    service_key: Optional[str] = None
    service_catalogue_category: Optional[str] = None
    airline_id: Optional[str] = None
    iata_code: Optional[str] = None
    airport_code: Optional[str] = None
    route_origin: Optional[str] = None
    route_destination: Optional[str] = None
    aircraft_type: Optional[str] = None
    condition_expression: Optional[Any] = None
    action: UnifiedExceptionAction
    required_documents_json: List[Dict[str, Any]] = Field(default_factory=list)
    notes: Optional[str] = None
    priority: int = 100
    active: bool = True
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    source_metadata_json: Dict[str, Any] = Field(default_factory=dict)


class UnifiedExceptionRuleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    category: Optional[UnifiedExceptionCategory] = None
    service_key: Optional[str] = None
    service_catalogue_category: Optional[str] = None
    airline_id: Optional[str] = None
    iata_code: Optional[str] = None
    airport_code: Optional[str] = None
    route_origin: Optional[str] = None
    route_destination: Optional[str] = None
    aircraft_type: Optional[str] = None
    condition_expression: Optional[Any] = None
    action: Optional[UnifiedExceptionAction] = None
    required_documents_json: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    priority: Optional[int] = None
    active: Optional[bool] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    source_metadata_json: Optional[Dict[str, Any]] = None


class PassengerServiceRequest(BaseDocument):
    agency_id: str
    request_id: Optional[str] = None
    trip_id: Optional[str] = None
    booking_id: Optional[str] = None
    passenger_id: Optional[str] = None
    segment_id: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    service_key: Optional[str] = None
    service_label: Optional[str] = None
    service_catalogue_category: Optional[str] = None
    service_catalogue_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    category: PassengerServiceCategory
    service_type: str
    ssr_code: Optional[str] = None
    osi_code: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    gds_text: Optional[str] = None
    required_documents_json: List[Dict[str, Any]] = Field(default_factory=list)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    policy_violations_json: List[Dict[str, Any]] = Field(default_factory=list)
    generated_ssr_json: List[Dict[str, Any]] = Field(default_factory=list)
    generated_osi_json: List[Dict[str, Any]] = Field(default_factory=list)
    evaluation_result_json: Dict[str, Any] = Field(default_factory=dict)
    status: PassengerServiceRequestStatus = PassengerServiceRequestStatus.REQUESTED


class PassengerServiceRequestCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    request_id: Optional[str] = None
    trip_id: Optional[str] = None
    booking_id: Optional[str] = None
    passenger_id: Optional[str] = None
    segment_id: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    service_key: Optional[str] = None
    service_label: Optional[str] = None
    service_catalogue_category: Optional[str] = None
    service_catalogue_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    category: PassengerServiceCategory
    service_type: str
    ssr_code: Optional[str] = None
    osi_code: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    gds_text: Optional[str] = None
    required_documents_json: List[Dict[str, Any]] = Field(default_factory=list)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    policy_violations_json: List[Dict[str, Any]] = Field(default_factory=list)
    generated_ssr_json: List[Dict[str, Any]] = Field(default_factory=list)
    generated_osi_json: List[Dict[str, Any]] = Field(default_factory=list)
    evaluation_result_json: Dict[str, Any] = Field(default_factory=dict)
    status: PassengerServiceRequestStatus = PassengerServiceRequestStatus.REQUESTED


class PassengerServiceRequestUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    request_id: Optional[str] = None
    trip_id: Optional[str] = None
    booking_id: Optional[str] = None
    passenger_id: Optional[str] = None
    segment_id: Optional[str] = None
    service_catalogue_id: Optional[str] = None
    service_key: Optional[str] = None
    service_label: Optional[str] = None
    service_catalogue_category: Optional[str] = None
    service_catalogue_snapshot_json: Optional[Dict[str, Any]] = None
    category: Optional[PassengerServiceCategory] = None
    service_type: Optional[str] = None
    ssr_code: Optional[str] = None
    osi_code: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    gds_text: Optional[str] = None
    required_documents_json: Optional[List[Dict[str, Any]]] = None
    warnings_json: Optional[List[Dict[str, Any]]] = None
    policy_violations_json: Optional[List[Dict[str, Any]]] = None
    generated_ssr_json: Optional[List[Dict[str, Any]]] = None
    generated_osi_json: Optional[List[Dict[str, Any]]] = None
    evaluation_result_json: Optional[Dict[str, Any]] = None
    status: Optional[PassengerServiceRequestStatus] = None


class RulesServicesSimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    airline_id: Optional[str] = None
    iata_code: Optional[str] = None
    route_origin: Optional[str] = None
    route_destination: Optional[str] = None
    aircraft_type: Optional[str] = None
    passenger_summary_json: Dict[str, Any] = Field(default_factory=dict)
    service_category: UnifiedExceptionCategory = UnifiedExceptionCategory.GENERAL
    service_type: str
    service_payload_json: Dict[str, Any] = Field(default_factory=dict)
    segment_refs_json: List[Dict[str, Any]] = Field(default_factory=list)


class DocumentTemplateScope(str, Enum):
    PLATFORM_DEFAULT = "platform_default"
    AGENCY_CUSTOM = "agency_custom"


class DocumentType(str, Enum):
    OFFER_SUMMARY = "offer_summary"
    OFFER_COMPARISON = "offer_comparison"
    TRIP_CONFIRMATION = "trip_confirmation"
    BOOKING_CONFIRMATION = "booking_confirmation"
    PNR_MIRROR = "pnr_mirror"
    ITINERARY_SUMMARY = "itinerary_summary"
    TICKET_RECEIPT = "ticket_receipt"
    TICKET_RECEIPT_SUMMARY = "ticket_receipt_summary"
    EMD_RECEIPT = "emd_receipt"
    EMD_RECEIPT_SUMMARY = "emd_receipt_summary"
    SERVICE_CONFIRMATION = "service_confirmation"
    MEDICAL_ASSISTANCE_SUMMARY = "medical_assistance_summary"
    PET_TRAVEL_SUMMARY = "pet_travel_summary"
    SPECIAL_BAGGAGE_SUMMARY = "special_baggage_summary"
    TRIP_CHANGE_SUMMARY = "trip_change_summary"
    EXCHANGE_QUOTE = "exchange_quote"
    EXCHANGE_CONFIRMATION = "exchange_confirmation"
    REFUND_QUOTE = "refund_quote"
    IMPORT_REVIEW_SUMMARY = "import_review_summary"
    BOOKING_IMPORT_REVIEW_SUMMARY = "booking_import_review_summary"
    GDS_PARSE_REVIEW_SUMMARY = "gds_parse_review_summary"
    AIRLINE_POLICY_EXTRACTION_SUMMARY = "airline_policy_extraction_summary"
    AIRLINE_POLICY_REVIEW_SUMMARY = "airline_policy_review_summary"
    INTERNAL_CASE_SUMMARY = "internal_case_summary"
    CUSTOM = "custom"
    INVOICE_SUMMARY = "invoice_summary"
    SERVICE_SUMMARY = "service_summary"


class DocumentSourceContextType(str, Enum):
    REQUEST = "request"
    OFFER_WORKSPACE = "offer_workspace"
    OFFER_OPTION = "offer_option"
    OFFER_ACCEPTANCE = "offer_acceptance"
    TRIP = "trip"
    BOOKING_WORKSPACE = "booking_workspace"
    BOOKING_RECORD = "booking_record"
    TICKET_RECORD = "ticket_record"
    EMD_RECORD = "emd_record"
    BOOKING_IMPORT_DRAFT = "booking_import_draft"
    GDS_PARSER_RUN = "gds_parser_run"
    AIRLINE_POLICY_SOURCE = "airline_policy_source"
    AIRLINE_POLICY_EXTRACTION_RUN = "airline_policy_extraction_run"
    AIRLINE_POLICY_APPROVED_KNOWLEDGE = "airline_policy_approved_knowledge"
    TRIP_CHANGE_OPERATION = "trip_change_operation"
    TICKET_EXCHANGE_OPERATION = "ticket_exchange_operation"
    EMD_EXCHANGE_OPERATION = "emd_exchange_operation"
    SERVICE_REQUEST = "service_request"
    MIXED_CONTEXT = "mixed_context"


class DocumentRenderStatus(str, Enum):
    DRAFT = "draft"
    RENDERED = "rendered"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentRenderFormat(str, Enum):
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    JSON = "json"


class DocumentPackageType(str, Enum):
    OFFER_PACKAGE = "offer_package"
    TRIP_PACKAGE = "trip_package"
    BOOKING_PACKAGE = "booking_package"
    TICKET_EMD_PACKAGE = "ticket_emd_package"
    SERVICE_PACKAGE = "service_package"
    CHANGE_EXCHANGE_PACKAGE = "change_exchange_package"
    IMPORT_REVIEW_PACKAGE = "import_review_package"
    INTERNAL_CASE_PACKAGE = "internal_case_package"
    CUSTOM = "custom"


class DocumentPackageStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    EXPORTED = "exported"
    ARCHIVED = "archived"


class DocumentShareStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    SENT_MANUALLY = "sent_manually"
    REVOKED = "revoked"
    EXPIRED = "expired"


class DocumentShareChannel(str, Enum):
    MANUAL_DOWNLOAD = "manual_download"
    MANUAL_EMAIL = "manual_email"
    PORTAL = "portal"
    INTERNAL = "internal"


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
    scope: Optional[str] = None
    template_key: Optional[str] = None
    template_type: Optional[str] = None
    document_type: DocumentType
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: DocumentTemplateStatus = DocumentTemplateStatus.ACTIVE
    active: bool = True
    language: str = "en"
    locale: str = "en"
    version: int = 1
    branding_profile_id: Optional[str] = None
    template_config: Dict[str, Any] = Field(default_factory=dict)
    layout_json: Dict[str, Any] = Field(default_factory=dict)
    content_blocks_json: List[Dict[str, Any]] = Field(default_factory=list)
    required_context_json: Dict[str, Any] = Field(default_factory=dict)
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


class DocumentContextPreviewRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    source_context_type: DocumentSourceContextType
    source_context_id: Optional[str] = None
    source_context_ids_json: Dict[str, Any] = Field(default_factory=dict)


class DocumentRenderJobCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    template_id: Optional[str] = None
    template_key: Optional[str] = None
    document_type: DocumentType
    source_context_type: DocumentSourceContextType
    source_context_id: Optional[str] = None
    source_context_ids_json: Dict[str, Any] = Field(default_factory=dict)
    render_format: DocumentRenderFormat = DocumentRenderFormat.HTML
    render_context_json: Dict[str, Any] = Field(default_factory=dict)
    internal_notes: Optional[str] = None


class DocumentRenderJob(BaseDocument):
    agency_id: str
    template_id: Optional[str] = None
    template_key: Optional[str] = None
    document_type: DocumentType
    source_context_type: DocumentSourceContextType
    source_context_id: Optional[str] = None
    source_context_ids_json: Dict[str, Any] = Field(default_factory=dict)
    render_status: DocumentRenderStatus = DocumentRenderStatus.DRAFT
    render_format: DocumentRenderFormat = DocumentRenderFormat.HTML
    render_context_json: Dict[str, Any] = Field(default_factory=dict)
    rendered_html: Optional[str] = None
    rendered_text: Optional[str] = None
    rendered_file_record_id: Optional[str] = None
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    error_json: Dict[str, Any] = Field(default_factory=dict)
    internal_notes: Optional[str] = None
    created_by_user_id: Optional[str] = None


class DocumentPackageCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    package_type: DocumentPackageType
    title: str
    source_context_type: DocumentSourceContextType
    source_context_id: Optional[str] = None
    source_context_ids_json: Dict[str, Any] = Field(default_factory=dict)
    document_render_job_ids: List[str] = Field(default_factory=list)


class DocumentPackage(BaseDocument):
    agency_id: str
    package_type: DocumentPackageType
    title: str
    source_context_type: DocumentSourceContextType
    source_context_id: Optional[str] = None
    source_context_ids_json: Dict[str, Any] = Field(default_factory=dict)
    document_render_job_ids: List[str] = Field(default_factory=list)
    status: DocumentPackageStatus = DocumentPackageStatus.DRAFT
    created_by_user_id: Optional[str] = None


class DocumentShareRecordCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    document_render_job_id: Optional[str] = None
    document_package_id: Optional[str] = None
    share_status: DocumentShareStatus = DocumentShareStatus.READY
    share_channel: DocumentShareChannel = DocumentShareChannel.INTERNAL
    recipient_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None


class DocumentShareRecord(BaseDocument):
    agency_id: str
    document_render_job_id: Optional[str] = None
    document_package_id: Optional[str] = None
    share_status: DocumentShareStatus = DocumentShareStatus.DRAFT
    share_channel: DocumentShareChannel = DocumentShareChannel.INTERNAL
    recipient_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    access_token_hash: Optional[str] = None
    expires_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_by_user_id: Optional[str] = None


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


class ReferenceRecordScope(str, Enum):
    GLOBAL = "global"
    AGENCY = "agency"


class ReferenceRecordSourceType(str, Enum):
    SYSTEM = "system"
    PLATFORM = "platform"
    AGENCY = "agency"
    IMPORT = "import"


class ReferenceSuggestionType(str, Enum):
    NEW_RECORD = "new_record"
    CORRECTION = "correction"
    DEACTIVATION_REQUEST = "deactivation_request"
    MERGE_REQUEST = "merge_request"
    MISSING_DOMAIN_VALUE = "missing_domain_value"


class ReferenceSuggestionSourceContext(str, Enum):
    ADMIN_FORM = "admin_form"
    REQUEST_BUILDER = "request_builder"
    IMPORT = "import"
    MANUAL_REFERENCE_PAGE = "manual_reference_page"
    POLICY_OVERRIDE_FUTURE = "policy_override_future"
    OTHER = "other"


class ReferenceSuggestionStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    NEEDS_MORE_INFORMATION = "needs_more_information"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"
    ARCHIVED = "archived"


class ReferenceImportBatchScope(str, Enum):
    GLOBAL = "global"
    AGENCY_SUGGESTION_BATCH = "agency_suggestion_batch"


class ReferenceImportBatchStatus(str, Enum):
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    PARTIALLY_VALID = "partially_valid"
    IMPORTED = "imported"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FieldFamily(str, Enum):
    CONTACT = "contact"
    CLIENT_CONTEXT = "client_context"
    PASSENGER = "passenger"
    ITINERARY_SEGMENT = "itinerary_segment"
    SERVICE = "service"
    PET = "pet"
    SPECIAL_ITEM = "special_item"
    DOCUMENT = "document"
    PRICING = "pricing"
    OFFER_DISPLAY = "offer_display"
    CONSENT = "consent"
    INTERNAL_ADMIN = "internal_admin"


class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    EMAIL = "email"
    PHONE = "phone"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTISELECT = "multiselect"
    REFERENCE_SELECT = "reference_select"
    FILE = "file"
    JSON = "json"


class FieldRequiredLevel(str, Enum):
    SYSTEM_REQUIRED = "system_required"
    POLICY_REQUIRED = "policy_required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"
    INTERNAL_ONLY = "internal_only"


class FormContext(str, Enum):
    PUBLIC_REQUEST = "public_request"
    PORTAL_REQUEST = "portal_request"
    ADMIN_REQUEST = "admin_request"
    OFFER_CLIENT_VIEW = "offer_client_view"
    OFFER_PDF = "offer_pdf"
    TRIP_INTAKE = "trip_intake"
    SERVICE_SPECIFIC = "service_specific"


class ServiceCatalogueBeneficiaryType(str, Enum):
    PASSENGER = "passenger"
    PET = "pet"
    SPECIAL_ITEM = "special_item"


class ServiceCatalogueStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ServiceSegmentScopeDefault(str, Enum):
    ALL_SEGMENTS = "all_segments"
    SELECTED_SEGMENTS = "selected_segments"


class ServiceEmdApplicability(str, Enum):
    NONE = "none"
    OPTIONAL = "optional"
    REQUIRED = "required"
    CONDITIONAL = "conditional"


class ReferenceEnrichmentPackSourceType(str, Enum):
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"
    SEED = "seed"
    EXTERNAL_REFERENCE = "external_reference"
    SYSTEM_GENERATED = "system_generated"


class ReferenceEnrichmentPackStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    APPLIED = "applied"
    ARCHIVED = "archived"


class GlobalReferenceRecord(BaseDocument):
    domain: str
    code: Optional[str] = None
    key: str
    label: str
    workspace_id: Optional[str] = None
    agency_id: Optional[str] = None
    scope: ReferenceRecordScope = ReferenceRecordScope.GLOBAL
    description: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    sort_order: int = 100
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_type: ReferenceRecordSourceType = ReferenceRecordSourceType.SYSTEM
    updated_by_user_id: Optional[str] = None
    created_by_user_id: Optional[str] = None
    is_active: bool = True

    @model_validator(mode="after")
    def align_code_and_key(self) -> "GlobalReferenceRecord":
        if self.code is None:
            self.code = self.key
        if not self.key and self.code:
            self.key = self.code
        return self


class GlobalReferenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: Optional[str] = None
    code: Optional[str] = None
    key: Optional[str] = None
    label: str
    workspace_id: Optional[str] = None
    agency_id: Optional[str] = None
    scope: ReferenceRecordScope = ReferenceRecordScope.GLOBAL
    description: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    sort_order: int = 100
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_type: ReferenceRecordSourceType = ReferenceRecordSourceType.PLATFORM
    is_active: bool = True


class GlobalReferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Optional[str] = None
    key: Optional[str] = None
    label: Optional[str] = None
    workspace_id: Optional[str] = None
    agency_id: Optional[str] = None
    scope: Optional[ReferenceRecordScope] = None
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    sort_order: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    source_type: Optional[ReferenceRecordSourceType] = None
    is_active: Optional[bool] = None


class ReferenceDomainMetadata(BaseDocument):
    domain: str
    label: str
    description: Optional[str] = None
    category: str = "reference"
    is_active: bool = True
    sort_order: int = 100
    metadata_schema_json: Dict[str, Any] = Field(default_factory=dict)
    created_by_user_id: Optional[str] = None
    updated_by_user_id: Optional[str] = None


class ReferenceDomainMetadataCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str
    label: str
    description: Optional[str] = None
    category: str = "reference"
    is_active: bool = True
    sort_order: int = 100
    metadata_schema_json: Dict[str, Any] = Field(default_factory=dict)


class ReferenceDomainMetadataUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    metadata_schema_json: Optional[Dict[str, Any]] = None


class PlatformReferenceRecordCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str
    code: str
    label: str
    description: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    sort_order: int = 100
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PlatformReferenceRecordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: Optional[str] = None
    code: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    sort_order: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ServiceCatalogueRecord(BaseDocument):
    service_code: Optional[str] = None
    service_label: Optional[str] = None
    service_family_code: Optional[str] = None
    service_key: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    active: bool = True
    status: ServiceCatalogueStatus = ServiceCatalogueStatus.ACTIVE
    default_ssr_code: Optional[str] = None
    beneficiary_type: ServiceCatalogueBeneficiaryType = ServiceCatalogueBeneficiaryType.PASSENGER
    requires_segment_scoping: bool = True
    requires_policy_check: bool = True
    requires_document_check: bool = False
    requires_manual_pricing: bool = False
    client_visible: bool = True
    agency_visible: bool = True
    platform_managed: bool = True
    applies_to_passenger_types: List[str] = Field(default_factory=list)
    applies_to_trip_types: List[str] = Field(default_factory=list)
    applies_to_segment_types: List[str] = Field(default_factory=list)
    requires_passenger_scope: bool = False
    requires_segment_scope: bool = True
    segment_scope_default: ServiceSegmentScopeDefault = ServiceSegmentScopeDefault.ALL_SEGMENTS
    segment_scope_allowed: bool = True
    request_form_enabled: bool = True
    default_selected: bool = False
    conditional_fields_json: Dict[str, Any] = Field(default_factory=dict)
    required_fields_json: Dict[str, Any] = Field(default_factory=dict)
    validation_rules_json: Dict[str, Any] = Field(default_factory=dict)
    helper_text: Optional[str] = None
    warning_text: Optional[str] = None
    rules_category: Optional[str] = None
    default_service_type: Optional[str] = None
    maps_to_passenger_service_request: bool = True
    exception_engine_enabled: bool = True
    policy_check_required: bool = True
    ssr_code: Optional[str] = None
    osi_template: Optional[str] = None
    ssr_template: Optional[str] = None
    requires_staff_review: bool = False
    booking_preview_enabled: bool = True
    offer_feasibility_enabled: bool = True
    offer_pricing_enabled: bool = False
    acceptance_snapshot_enabled: bool = True
    booking_readiness_enabled: bool = True
    default_pricing_category: Optional[str] = None
    emd_applicability: ServiceEmdApplicability = ServiceEmdApplicability.NONE
    fee_expected: bool = False
    included_in_fare_possible: bool = False
    required_documents_json: List[Dict[str, Any]] = Field(default_factory=list)
    client_document_summary_enabled: bool = True
    internal_handling_notes: Optional[str] = None
    links_to_pet_taxonomy: bool = False
    links_to_special_item_taxonomy: bool = False
    linked_special_item_categories: List[str] = Field(default_factory=list)
    linked_pet_categories: List[str] = Field(default_factory=list)
    input_schema_json: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    sort_order: int = 100
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    source_type: ReferenceRecordSourceType = ReferenceRecordSourceType.SYSTEM
    updated_by_user_id: Optional[str] = None
    created_by_user_id: Optional[str] = None

    @model_validator(mode="after")
    def align_operational_fields(self) -> "ServiceCatalogueRecord":
        if self.service_key is None and self.service_code:
            self.service_key = self.service_code
        if self.service_code is None and self.service_key:
            self.service_code = self.service_key
        if self.label is None and self.service_label:
            self.label = self.service_label
        if self.service_label is None and self.label:
            self.service_label = self.label
        if self.category is None and self.service_family_code:
            self.category = self.service_family_code
        if self.service_family_code is None and self.category:
            self.service_family_code = self.category
        if self.ssr_code is None and self.default_ssr_code:
            self.ssr_code = self.default_ssr_code
        if self.default_ssr_code is None and self.ssr_code:
            self.default_ssr_code = self.ssr_code
        if self.default_service_type is None and self.service_code:
            self.default_service_type = self.service_code
        status_value = self.status.value if hasattr(self.status, "value") else self.status
        self.active = self.is_active and status_value != ServiceCatalogueStatus.ARCHIVED.value
        return self


class ServiceCatalogueCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_code: Optional[str] = None
    service_label: Optional[str] = None
    service_family_code: Optional[str] = None
    service_key: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    active: bool = True
    status: ServiceCatalogueStatus = ServiceCatalogueStatus.ACTIVE
    default_ssr_code: Optional[str] = None
    beneficiary_type: ServiceCatalogueBeneficiaryType = ServiceCatalogueBeneficiaryType.PASSENGER
    requires_segment_scoping: bool = True
    requires_policy_check: bool = True
    requires_document_check: bool = False
    requires_manual_pricing: bool = False
    client_visible: bool = True
    agency_visible: bool = True
    platform_managed: bool = True
    applies_to_passenger_types: List[str] = Field(default_factory=list)
    applies_to_trip_types: List[str] = Field(default_factory=list)
    applies_to_segment_types: List[str] = Field(default_factory=list)
    requires_passenger_scope: bool = False
    requires_segment_scope: bool = True
    segment_scope_default: ServiceSegmentScopeDefault = ServiceSegmentScopeDefault.ALL_SEGMENTS
    segment_scope_allowed: bool = True
    request_form_enabled: bool = True
    default_selected: bool = False
    conditional_fields_json: Dict[str, Any] = Field(default_factory=dict)
    required_fields_json: Dict[str, Any] = Field(default_factory=dict)
    validation_rules_json: Dict[str, Any] = Field(default_factory=dict)
    helper_text: Optional[str] = None
    warning_text: Optional[str] = None
    rules_category: Optional[str] = None
    default_service_type: Optional[str] = None
    maps_to_passenger_service_request: bool = True
    exception_engine_enabled: bool = True
    policy_check_required: bool = True
    ssr_code: Optional[str] = None
    osi_template: Optional[str] = None
    ssr_template: Optional[str] = None
    requires_staff_review: bool = False
    booking_preview_enabled: bool = True
    offer_feasibility_enabled: bool = True
    offer_pricing_enabled: bool = False
    acceptance_snapshot_enabled: bool = True
    booking_readiness_enabled: bool = True
    default_pricing_category: Optional[str] = None
    emd_applicability: ServiceEmdApplicability = ServiceEmdApplicability.NONE
    fee_expected: bool = False
    included_in_fare_possible: bool = False
    required_documents_json: List[Dict[str, Any]] = Field(default_factory=list)
    client_document_summary_enabled: bool = True
    internal_handling_notes: Optional[str] = None
    links_to_pet_taxonomy: bool = False
    links_to_special_item_taxonomy: bool = False
    linked_special_item_categories: List[str] = Field(default_factory=list)
    linked_pet_categories: List[str] = Field(default_factory=list)
    input_schema_json: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    sort_order: int = 100
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    source_type: ReferenceRecordSourceType = ReferenceRecordSourceType.PLATFORM

    @model_validator(mode="after")
    def align_operational_fields(self) -> "ServiceCatalogueCreate":
        if self.service_key is None and self.service_code:
            self.service_key = self.service_code
        if self.service_code is None and self.service_key:
            self.service_code = self.service_key
        if self.label is None and self.service_label:
            self.label = self.service_label
        if self.service_label is None and self.label:
            self.service_label = self.label
        if self.category is None and self.service_family_code:
            self.category = self.service_family_code
        if self.service_family_code is None and self.category:
            self.service_family_code = self.category
        if not self.service_code or not self.service_label or not self.service_family_code:
            raise ValueError("service_key/label/category are required.")
        if self.ssr_code is None and self.default_ssr_code:
            self.ssr_code = self.default_ssr_code
        if self.default_ssr_code is None and self.ssr_code:
            self.default_ssr_code = self.ssr_code
        if self.default_service_type is None and self.service_code:
            self.default_service_type = self.service_code
        status_value = self.status.value if hasattr(self.status, "value") else self.status
        self.is_active = self.active and status_value != ServiceCatalogueStatus.ARCHIVED.value
        return self


class ServiceCatalogueUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_code: Optional[str] = None
    service_label: Optional[str] = None
    service_family_code: Optional[str] = None
    service_key: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    active: Optional[bool] = None
    status: Optional[ServiceCatalogueStatus] = None
    default_ssr_code: Optional[str] = None
    beneficiary_type: Optional[ServiceCatalogueBeneficiaryType] = None
    requires_segment_scoping: Optional[bool] = None
    requires_policy_check: Optional[bool] = None
    requires_document_check: Optional[bool] = None
    requires_manual_pricing: Optional[bool] = None
    client_visible: Optional[bool] = None
    agency_visible: Optional[bool] = None
    platform_managed: Optional[bool] = None
    applies_to_passenger_types: Optional[List[str]] = None
    applies_to_trip_types: Optional[List[str]] = None
    applies_to_segment_types: Optional[List[str]] = None
    requires_passenger_scope: Optional[bool] = None
    requires_segment_scope: Optional[bool] = None
    segment_scope_default: Optional[ServiceSegmentScopeDefault] = None
    segment_scope_allowed: Optional[bool] = None
    request_form_enabled: Optional[bool] = None
    default_selected: Optional[bool] = None
    conditional_fields_json: Optional[Dict[str, Any]] = None
    required_fields_json: Optional[Dict[str, Any]] = None
    validation_rules_json: Optional[Dict[str, Any]] = None
    helper_text: Optional[str] = None
    warning_text: Optional[str] = None
    rules_category: Optional[str] = None
    default_service_type: Optional[str] = None
    maps_to_passenger_service_request: Optional[bool] = None
    exception_engine_enabled: Optional[bool] = None
    policy_check_required: Optional[bool] = None
    ssr_code: Optional[str] = None
    osi_template: Optional[str] = None
    ssr_template: Optional[str] = None
    requires_staff_review: Optional[bool] = None
    booking_preview_enabled: Optional[bool] = None
    offer_feasibility_enabled: Optional[bool] = None
    offer_pricing_enabled: Optional[bool] = None
    acceptance_snapshot_enabled: Optional[bool] = None
    booking_readiness_enabled: Optional[bool] = None
    default_pricing_category: Optional[str] = None
    emd_applicability: Optional[ServiceEmdApplicability] = None
    fee_expected: Optional[bool] = None
    included_in_fare_possible: Optional[bool] = None
    required_documents_json: Optional[List[Dict[str, Any]]] = None
    client_document_summary_enabled: Optional[bool] = None
    internal_handling_notes: Optional[str] = None
    links_to_pet_taxonomy: Optional[bool] = None
    links_to_special_item_taxonomy: Optional[bool] = None
    linked_special_item_categories: Optional[List[str]] = None
    linked_pet_categories: Optional[List[str]] = None
    input_schema_json: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    source_type: Optional[ReferenceRecordSourceType] = None


class ServiceCatalogueReorderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ordered_ids: List[str] = Field(default_factory=list)


class ReferenceEnrichmentPack(BaseDocument):
    pack_key: str
    label: str
    description: Optional[str] = None
    target_domain: str
    source_type: ReferenceEnrichmentPackSourceType = ReferenceEnrichmentPackSourceType.MANUAL
    status: ReferenceEnrichmentPackStatus = ReferenceEnrichmentPackStatus.DRAFT
    fields_added_or_updated: List[str] = Field(default_factory=list)
    validation_rules_json: Dict[str, Any] = Field(default_factory=dict)
    preview_count: int = 0
    applied_count: int = 0
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)
    created_by_user_id: Optional[str] = None
    applied_by_user_id: Optional[str] = None
    applied_at: Optional[datetime] = None


class ReferenceEnrichmentPackCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_key: str
    label: str
    description: Optional[str] = None
    target_domain: str
    source_type: ReferenceEnrichmentPackSourceType = ReferenceEnrichmentPackSourceType.MANUAL
    status: ReferenceEnrichmentPackStatus = ReferenceEnrichmentPackStatus.DRAFT
    fields_added_or_updated: List[str] = Field(default_factory=list)
    validation_rules_json: Dict[str, Any] = Field(default_factory=dict)
    warnings_json: List[Dict[str, Any]] = Field(default_factory=list)


class ReferenceEnrichmentPackPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    csv_text: Optional[str] = None
    update_mode: str = "update_missing_only"
    source_label: Optional[str] = None
    notes: Optional[str] = None


class ReferenceImportPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str
    filename: Optional[str] = None
    csv_text: str
    mode: str = "upsert"


class ReferenceImportApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str
    filename: Optional[str] = None
    csv_text: str
    mode: str = "upsert"


class ReferenceDataSuggestion(BaseDocument):
    submitting_agency_id: str
    submitting_workspace_id: Optional[str] = None
    submitted_by_user_id: str
    domain: str
    suggested_code: Optional[str] = None
    suggested_label: str
    suggested_description: Optional[str] = None
    suggested_aliases: List[str] = Field(default_factory=list)
    suggested_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    suggestion_type: ReferenceSuggestionType = ReferenceSuggestionType.NEW_RECORD
    target_reference_record_id: Optional[str] = None
    source_context: ReferenceSuggestionSourceContext = ReferenceSuggestionSourceContext.MANUAL_REFERENCE_PAGE
    evidence_note: Optional[str] = None
    evidence_file_ids: List[str] = Field(default_factory=list)
    status: ReferenceSuggestionStatus = ReferenceSuggestionStatus.PENDING_REVIEW
    reviewer_user_id: Optional[str] = None
    reviewer_note: Optional[str] = None
    approved_reference_record_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class ReferenceDataSuggestionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    submitting_agency_id: str
    submitting_workspace_id: Optional[str] = None
    domain: str
    suggested_code: Optional[str] = None
    suggested_label: str
    suggested_description: Optional[str] = None
    suggested_aliases: List[str] = Field(default_factory=list)
    suggested_metadata_json: Dict[str, Any] = Field(default_factory=dict)
    suggestion_type: ReferenceSuggestionType = ReferenceSuggestionType.NEW_RECORD
    target_reference_record_id: Optional[str] = None
    source_context: ReferenceSuggestionSourceContext = ReferenceSuggestionSourceContext.MANUAL_REFERENCE_PAGE
    evidence_note: Optional[str] = None
    evidence_file_ids: List[str] = Field(default_factory=list)


class ReferenceSuggestionReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer_note: Optional[str] = None
    merge_into_reference_record_id: Optional[str] = None


class ReferenceImportBatch(BaseDocument):
    uploaded_by_user_id: str
    scope: ReferenceImportBatchScope = ReferenceImportBatchScope.GLOBAL
    domain: str
    filename: str
    file_hash: str
    status: ReferenceImportBatchStatus = ReferenceImportBatchStatus.UPLOADED
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    inserted_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    error_report_json: Dict[str, Any] = Field(default_factory=dict)
    completed_at: Optional[datetime] = None


class ReferenceImportBatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: ReferenceImportBatchScope = ReferenceImportBatchScope.GLOBAL
    domain: str
    filename: str
    csv_text: str
    dry_run: bool = False


class PlatformReferenceImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: ReferenceImportBatchScope = ReferenceImportBatchScope.GLOBAL
    domain: str
    filename: str
    csv_text: str
    dry_run: bool = True


class ReferenceEnrichmentImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str
    csv_text: str
    update_mode: str = "update_missing_only"
    dry_run: bool = True
    source_label: Optional[str] = None
    notes: Optional[str] = None


class GlobalFieldDefinition(BaseDocument):
    field_key: str
    canonical_path: str
    field_family: FieldFamily
    field_type: FieldType
    label: str
    help_text: Optional[str] = None
    description: Optional[str] = None
    reference_domain: Optional[str] = None
    service_family_code: Optional[str] = None
    required_level: FieldRequiredLevel = FieldRequiredLevel.OPTIONAL
    public_safe: bool = False
    portal_safe: bool = False
    admin_safe: bool = True
    can_be_hidden_by_agency: bool = True
    can_be_required_by_agency: bool = True
    can_label_be_overridden: bool = True
    validation_schema_json: Dict[str, Any] = Field(default_factory=dict)
    default_display_order: int = 100
    is_active: bool = True


class GlobalFieldDefinitionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_key: str
    canonical_path: str
    field_family: FieldFamily
    field_type: FieldType
    label: str
    help_text: Optional[str] = None
    description: Optional[str] = None
    reference_domain: Optional[str] = None
    service_family_code: Optional[str] = None
    required_level: FieldRequiredLevel = FieldRequiredLevel.OPTIONAL
    public_safe: bool = False
    portal_safe: bool = False
    admin_safe: bool = True
    can_be_hidden_by_agency: bool = True
    can_be_required_by_agency: bool = True
    can_label_be_overridden: bool = True
    validation_schema_json: Dict[str, Any] = Field(default_factory=dict)
    default_display_order: int = 100
    is_active: bool = True


class GlobalFieldDefinitionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_path: Optional[str] = None
    field_family: Optional[FieldFamily] = None
    field_type: Optional[FieldType] = None
    label: Optional[str] = None
    help_text: Optional[str] = None
    description: Optional[str] = None
    reference_domain: Optional[str] = None
    service_family_code: Optional[str] = None
    required_level: Optional[FieldRequiredLevel] = None
    public_safe: Optional[bool] = None
    portal_safe: Optional[bool] = None
    admin_safe: Optional[bool] = None
    can_be_hidden_by_agency: Optional[bool] = None
    can_be_required_by_agency: Optional[bool] = None
    can_label_be_overridden: Optional[bool] = None
    validation_schema_json: Optional[Dict[str, Any]] = None
    default_display_order: Optional[int] = None
    is_active: Optional[bool] = None


class AgencyFormProfile(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    profile_key: str
    name: str
    form_context: FormContext
    service_family_code: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    created_by_user_id: Optional[str] = None


class AgencyFormProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: Optional[str] = None
    profile_key: str
    name: str
    form_context: FormContext
    service_family_code: Optional[str] = None
    is_default: bool = False
    is_active: bool = True


class AgencyFormProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: Optional[str] = None
    profile_key: Optional[str] = None
    name: Optional[str] = None
    form_context: Optional[FormContext] = None
    service_family_code: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class AgencyFormFieldSetting(BaseDocument):
    agency_id: str
    workspace_id: Optional[str] = None
    form_profile_id: str
    global_field_definition_id: Optional[str] = None
    field_key: str
    enabled: bool = True
    visible: bool = True
    required_override: Optional[bool] = None
    label_override: Optional[str] = None
    help_text_override: Optional[str] = None
    placeholder_override: Optional[str] = None
    display_order: int = 100
    section_key: str = "general"
    section_label_override: Optional[str] = None
    custom_field: bool = False
    custom_field_schema_json: Optional[Dict[str, Any]] = None
    visibility_condition_json: Optional[Dict[str, Any]] = None
    validation_override_json: Optional[Dict[str, Any]] = None


class AgencyFormFieldSettingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    workspace_id: Optional[str] = None
    global_field_definition_id: Optional[str] = None
    field_key: str
    enabled: bool = True
    visible: bool = True
    required_override: Optional[bool] = None
    label_override: Optional[str] = None
    help_text_override: Optional[str] = None
    placeholder_override: Optional[str] = None
    display_order: int = 100
    section_key: str = "general"
    section_label_override: Optional[str] = None
    custom_field: bool = False
    custom_field_schema_json: Optional[Dict[str, Any]] = None
    visibility_condition_json: Optional[Dict[str, Any]] = None
    validation_override_json: Optional[Dict[str, Any]] = None


class AgencyFormFieldSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: List[AgencyFormFieldSettingInput] = Field(default_factory=list)


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
