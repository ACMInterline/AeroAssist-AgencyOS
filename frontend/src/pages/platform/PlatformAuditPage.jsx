import { useEffect, useMemo, useState } from "react"
import FilterBar from "../../components/FilterBar"
import PageHeader from "../../components/PageHeader"
import ProductTable from "../../components/ProductTable"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkspacePage from "../../components/WorkspacePage"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

export default function PlatformAuditPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ agency: "", event: "", entity: "" })
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([
      apiGet("/api/platform/summary"),
      apiGet("/api/platform/audit-events?limit=200"),
    ]).then(([summary, audit]) => setState({ summary, events: audit.items || [] }))
      .catch((err) => setError(err.message))
  }, [])

  const events = useMemo(() => (state?.events || []).filter((event) => (
    (!filters.agency || String(event.agency_id || "").toLowerCase().includes(filters.agency.toLowerCase()))
    && (!filters.event || String(event.event_type || "").toLowerCase().includes(filters.event.toLowerCase()))
    && (!filters.entity || [event.entity_type, event.entity_id].some((value) => String(value || "").toLowerCase().includes(filters.entity.toLowerCase())))
  )), [filters, state])

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute error={error} loading={!state && !error}>
        <WorkspacePage as="main" className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Platform", href: "/platform" }, { label: "Audit" }]}
            eyebrow="Governed activity"
            title="Audit"
            description="Review authorized Platform and Agency changes without exposing records outside their recorded tenant scope."
          />
          <FilterBar onClear={() => setFilters({ agency: "", event: "", entity: "" })} resultCount={events.length} title="Filter audit activity">
            <div className="grid gap-3 md:grid-cols-3">
              <Field label="Agency reference" value={filters.agency} onChange={(value) => setFilters({ ...filters, agency: value })} />
              <Field label="Activity type" value={filters.event} onChange={(value) => setFilters({ ...filters, event: value })} />
              <Field label="Related record" value={filters.entity} onChange={(value) => setFilters({ ...filters, entity: value })} />
            </div>
          </FilterBar>
          <ProductTable
            caption="Platform audit activity"
            columns={[
              { key: "activity", label: "Activity", render: (item) => item.summary || formatLabel(item.event_type), sortValue: (item) => item.summary || item.event_type || "" },
              { key: "agency", label: "Agency", render: (item) => item.agency_id || "Platform", sortValue: (item) => item.agency_id || "" },
              { key: "record", label: "Related record", render: (item) => [formatLabel(item.entity_type), item.entity_id].filter(Boolean).join(" · ") || "Not linked", sortValue: (item) => `${item.entity_type || ""}:${item.entity_id || ""}` },
              { key: "actor", label: "Actor", render: (item) => item.actor_display_name || item.actor_user_id || "System", sortValue: (item) => item.actor_display_name || item.actor_user_id || "" },
              { key: "time", label: "Time", render: (item) => formatDateTime(item.created_at), sortValue: (item) => item.created_at || "" },
            ]}
            defaultSort={{ key: "time", direction: "desc" }}
            emptyBody="Governed activity will appear after authorized actions are recorded."
            emptyTitle="No audit activity matches"
            rows={events}
          />
        </WorkspacePage>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Field({ label, onChange, value }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="field" onChange={(event) => onChange(event.target.value)} value={value} /></label>
}

function formatLabel(value) {
  return String(value || "").replaceAll("_", " ")
}

function formatDateTime(value) {
  if (!value) return "Time unavailable"
  const parsed = new Date(value)
  return Number.isNaN(parsed.valueOf()) ? String(value) : parsed.toLocaleString()
}
