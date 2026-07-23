import CircleHelp from "lucide-react/dist/esm/icons/circle-help.js"

const guidance = {
  onboarding: {
    title: "Pilot setup help",
    body: "Complete each step, create the synthetic demo workspace, then review the setup before opening daily operations.",
    next: "Next: finish the current setup step. Progress is saved automatically.",
  },
  operations: {
    title: "Start with what needs attention",
    body: "Review overdue and urgent work first, then open the linked request, booking, document, or passenger service.",
    next: "Next: choose one actionable item and use its guarded update.",
  },
  requests: {
    title: "Capture the travel need first",
    body: "Keep the client, passengers, route, dates, and service requirements together before creating downstream work.",
    next: "Next: open a request or create one for a new client need.",
  },
  offers: {
    title: "Prepare choices from resolved context",
    body: "Check the linked trip, passengers, services, pricing notes, and client-safe content before recording a response.",
    next: "Next: open an offer requiring action or prepare a new comparison.",
  },
  booking: {
    title: "Booking remains operator controlled",
    body: "Use an accepted offer and readiness context where available. AeroAssist does not create a live supplier booking.",
    next: "Next: resolve visible blockers before recording booking metadata.",
  },
  passengers: {
    title: "One operational identity per traveller",
    body: "Record identity, documents, preferences, and assistance needs carefully. Do not add unnecessary sensitive detail.",
    next: "Next: open an existing passenger before creating a possible duplicate.",
  },
  documents: {
    title: "Track requirements and review state",
    body: "Document records describe what is required, received, and verified. They do not send or externally store files.",
    next: "Next: review travel-critical requirements and deadlines.",
  },
  tasks: {
    title: "Keep ownership and blockers visible",
    body: "Use the canonical queue to assign work, record blockers, and complete follow-ups with an audit trail.",
    next: "Next: start with overdue, urgent, or unassigned work.",
  },
}

export default function PilotGuidance({ area }) {
  const item = guidance[area] || guidance.operations
  const query = new URLSearchParams({ affected_area: area })
  return (
    <aside aria-label={`${item.title} guidance`} className="flex flex-wrap items-start justify-between gap-4 border-y border-blue-200 bg-blue-50 px-4 py-3">
      <div className="flex min-w-0 gap-3">
        <CircleHelp aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-blue-700" />
        <div>
          <h2 className="text-sm font-semibold text-blue-950">{item.title}</h2>
          <p className="mt-1 text-sm leading-5 text-blue-900">{item.body}</p>
          <p className="mt-1 text-xs font-semibold text-blue-800">{item.next}</p>
        </div>
      </div>
      <div className="flex shrink-0 flex-wrap gap-3 text-sm font-semibold">
        <a className="text-blue-800 hover:underline" href={`/agency/pilot-feedback?${query}#pilot-guides`}>Open pilot guide</a>
        <a className="text-blue-800 hover:underline" href={`/agency/pilot-feedback?${query}#submit-feedback`}>Send feedback</a>
      </div>
    </aside>
  )
}
