import { useEffect, useMemo, useState } from "react"
import Search from "lucide-react/dist/esm/icons/search.js"
import PageHeader from "../../components/PageHeader"
import ProductTable from "../../components/ProductTable"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import WorkspacePage from "../../components/WorkspacePage"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function CommunicationsPage() {
  const [state, setState] = useState(null)
  const [query, setQuery] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const result = await apiGet(`/api/agencies/${context.agency.id}/operational-collaboration/threads?limit=200`)
      setState({ ...context, threads: result.items || [] })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return (state?.threads || []).filter((thread) => !needle || [
      thread.subject,
      thread.status,
      ...(thread.entity_references || []).flatMap((item) => [item.label, item.entity_type, item.entity_id]),
    ].some((value) => String(value || "").toLowerCase().includes(needle)))
  }, [query, state])

  return (
    <AgencyLayout agency={state?.agency} user={state?.me?.user}>
      <ProtectedRoute error={error} loading={!state && !error}>
        <WorkspacePage as="main" className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Dashboard", href: "/agency" }, { label: "Communications" }]}
            eyebrow="Client and supplier follow-up"
            title="Communications"
            description="Find conversations by client, passenger, trip, request, or booking, then continue from the linked operational record."
            status={<StatusBadge label={`${rows.length} visible`} status="default" />}
          />

          <section aria-label="Communication search" className="rounded-lg border border-slate-200 bg-white p-4">
            <label className="text-sm font-semibold text-slate-800" htmlFor="communication-search">Search conversations</label>
            <div className="mt-2 flex max-w-xl items-center gap-2 rounded-md border border-slate-300 bg-white px-3">
              <Search aria-hidden="true" className="h-4 w-4 shrink-0 text-slate-400" />
              <input
                className="min-w-0 flex-1 border-0 bg-transparent py-2.5 text-sm outline-none"
                id="communication-search"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Client, passenger, trip, request, or subject"
                value={query}
              />
            </div>
          </section>

          <ProductTable
            caption="Agency conversations"
            columns={[
              { key: "subject", label: "Conversation", render: (item) => item.subject || "Operational conversation", sortValue: (item) => item.subject || "" },
              { key: "context", label: "Related record", render: (item) => contextLabel(item), sortValue: contextLabel },
              { key: "status", label: "Status", render: (item) => <StatusBadge status={item.status || "open"} />, sortValue: (item) => item.status || "" },
              { key: "updated", label: "Last activity", render: (item) => formatDateTime(item.last_message_at || item.updated_at || item.created_at), sortValue: (item) => item.last_message_at || item.updated_at || item.created_at || "" },
            ]}
            defaultSort={{ key: "updated", direction: "desc" }}
            emptyBody={query ? "Clear the search or try a client, passenger, trip, request, or booking reference." : "Conversations appear when a message or internal note is recorded from an operational record."}
            emptyTitle={query ? "No conversations match" : "No conversations yet"}
            getRowHref={(item) => relatedHref(item)}
            rows={rows}
          />

          <p className="text-xs leading-5 text-slate-500">
            AeroAssist records communication evidence here. Email, SMS, chat, and supplier delivery remain manual and disabled.
          </p>
        </WorkspacePage>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function primaryReference(thread) {
  return (thread.entity_references || [])[0] || {}
}

function contextLabel(thread) {
  const reference = primaryReference(thread)
  return reference.label || [formatLabel(reference.entity_type), reference.entity_id].filter(Boolean).join(" · ") || "General agency conversation"
}

function relatedHref(thread) {
  const reference = primaryReference(thread)
  const id = reference.entity_id
  const type = String(reference.entity_type || "").toLowerCase()
  if (!id) return "/agency/communications"
  if (type.includes("request")) return `/agency/requests/${id}`
  if (type.includes("trip")) return `/agency/trips/${id}`
  if (type.includes("offer")) return `/agency/offers/${id}`
  if (type.includes("booking")) return `/agency/bookings/${id}`
  if (type.includes("passenger")) return `/agency/passengers/${id}`
  if (type.includes("client")) return `/agency/clients/${id}`
  if (type.includes("ticket")) return `/agency/tickets/${id}`
  if (type.includes("emd")) return `/agency/emds/${id}`
  if (type.includes("document")) return `/agency/documents/${id}`
  if (type.includes("invoice")) return `/agency/invoices/${id}`
  return "/agency/communications"
}

function formatLabel(value) {
  return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatDateTime(value) {
  if (!value) return "No activity yet"
  const parsed = new Date(value)
  return Number.isNaN(parsed.valueOf()) ? String(value) : parsed.toLocaleString()
}
