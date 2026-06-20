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
    CLIENT_PORTAL = "client_portal"
    PHONE = "phone"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WALK_IN = "walk_in"
    IMPORTED = "imported"


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
    route_summary: Optional[str] = None
    service_summary: Optional[str] = None
    passenger_count: int = 0
    service_count: int = 0
    urgency_reason: Optional[str] = None
    client_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    assigned_user_id: Optional[str] = None
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
    route_summary: Optional[str] = None
    service_summary: Optional[str] = None
    urgency_reason: Optional[str] = None
    client_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    assigned_user_id: Optional[str] = None


class TravelRequestUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    title: Optional[str] = None
    status: Optional[RequestStatus] = None
    priority: Optional[RequestPriority] = None
    source: Optional[RequestSource] = None
    requested_departure_date: Optional[date] = None
    requested_return_date: Optional[date] = None
    route_summary: Optional[str] = None
    service_summary: Optional[str] = None
    urgency_reason: Optional[str] = None
    client_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    client_visible_notes: Optional[str] = None
    assigned_user_id: Optional[str] = None


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
    client_visible_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    requires_documents: Optional[bool] = None
    requires_airline_approval: Optional[bool] = None


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
