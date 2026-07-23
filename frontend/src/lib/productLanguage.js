const productLabels = {
  draft_metadata: "Draft",
  duplicate_merged: "Merged duplicate",
  ready_to_book: "Ready to book",
  booking_in_progress: "Booking in progress",
  waiting_for_client: "Waiting for client",
  waiting_client: "Waiting for client",
  waiting_documents: "Waiting for documents",
  waiting_approval: "Waiting for approval",
  waiting_payment: "Waiting for payment",
  ready_for_offer: "Ready for offer",
  offer_created: "Offer created",
  partially_confirmed: "Partially confirmed",
  not_configured: "Not configured",
  configuration_pending: "Setup in progress",
  configured_unverified: "Configured, not verified",
  not_required: "Not required",
  in_progress: "In progress",
  due_soon: "Due soon",
  urgent_critical: "Urgent and critical",
  knowledge_gap_queue: "Knowledge follow-up",
  workflow_blocker_queue: "Blocked follow-ups",
  staff_created: "Created by staff",
  client_portal: "Client portal",
  public_website: "Public website",
  website_form: "Website form",
  imported_gds_text: "Imported booking text",
  client_profile: "Client profile",
  passenger_profile: "Passenger profile",
  airline_research: "Airline research",
}

export function productLabel(value, fallback = "Not set") {
  if (value === null || value === undefined || value === "") return fallback
  const key = String(value)
  const label = productLabels[key] || key.replaceAll("_", " ")
  return label.charAt(0).toUpperCase() + label.slice(1)
}

export function passengerTypeLabel(value) {
  const labels = {
    ADT: "Adult",
    CHD: "Child",
    INF: "Infant",
    YTH: "Young passenger",
    SRC: "Senior passenger",
    STU: "Student",
    UMNR: "Unaccompanied minor",
    INS: "Infant with seat",
  }
  return labels[value] || productLabel(value)
}
