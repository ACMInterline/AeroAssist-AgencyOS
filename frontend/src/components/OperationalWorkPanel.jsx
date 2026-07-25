import { useEffect, useMemo, useState } from "react"
import CircleAlert from "lucide-react/dist/esm/icons/circle-alert.js"
import Clock3 from "lucide-react/dist/esm/icons/clock-3.js"
import ListChecks from "lucide-react/dist/esm/icons/list-checks.js"
import EmptyState from "./EmptyState"
import ProductTable from "./ProductTable"
import StatusBadge from "./StatusBadge"
import { apiGet } from "../lib/api"

export default function OperationalWorkPanel({ agencyId, entityId, entityType }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(Boolean(agencyId && entityId && entityType))
  const [error, setError] = useState("")

  useEffect(() => {
    if (!agencyId || !entityId || !entityType) {
      setItems([])
      setLoading(false)
      return undefined
    }
    let active = true
    setLoading(true)
    setError("")
    const query = new URLSearchParams({
      source_entity_type: entityType,
      source_entity_id: entityId,
      include_completed: "true",
    })
    apiGet(`/api/agencies/${agencyId}/work-queue?${query.toString()}`)
      .then((response) => {
        if (active) setItems(response.items || [])
      })
      .catch((requestError) => {
        if (active) setError(requestError.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [agencyId, entityId, entityType])

  const openItems = useMemo(
    () => items.filter((item) => !["completed", "cancelled"].includes(item.status)),
    [items],
  )
  const completedItems = items.filter((item) => item.status === "completed")
  const approvalCount = openItems.filter((item) => item.approval_required).length
  const blockerCount = openItems.filter((item) => item.blocker_status === "blocked" || item.status === "blocked").length
  const columns = [
    {
      key: "work",
      label: "Work",
      render: (item) => (
        <div>
          <p className="font-semibold text-slate-950">{item.title}</p>
          <p className="mt-1 text-xs text-slate-500">{format(item.work_item_type)}</p>
        </div>
      ),
      sortValue: (item) => item.title,
    },
    {
      key: "owner",
      label: "Owner and queue",
      render: (item) => (
        <div>
          <p>{item.assigned_user_label || item.assigned_user_name || item.assigned_user_id || "Unassigned"}</p>
          <p className="mt-1 text-xs text-slate-500">{format(item.queue_key || item.queue_code)}</p>
        </div>
      ),
      sortValue: (item) => item.assigned_user_label || item.assigned_user_id || "",
    },
    {
      key: "status",
      label: "Status",
      render: (item) => (
        <div className="space-y-1">
          <StatusBadge status={item.status} />
          <p className="text-xs text-slate-500">{format(item.priority)} priority</p>
        </div>
      ),
      sortValue: (item) => item.status,
    },
    {
      key: "deadline",
      label: "Deadline",
      render: (item) => (
        <div>
          <p>{formatDateTime(item.due_at)}</p>
          <p className="mt-1 text-xs text-slate-500">{format(item.sla_status)}</p>
        </div>
      ),
      sortValue: (item) => item.due_at || "9999",
    },
    {
      key: "next",
      label: "Next safe action",
      render: (item) => (
        <div>
          <p className="font-medium text-slate-800">{format(item.next_recommended_safe_action || "review")}</p>
          <p className="mt-1 text-xs text-slate-500">Open the operations queue to act</p>
        </div>
      ),
      sortValue: (item) => item.next_recommended_safe_action || "review",
    },
    {
      key: "controls",
      label: "Dependencies and approval",
      render: (item) => (
        <div className="space-y-1 text-xs">
          <p>{(item.dependencies || []).length} dependencies</p>
          <p>{(item.blockers || []).length} blockers</p>
          <p>{item.approval_required ? `Approval ${format(item.approval_status || "requested")}` : "No approval required"}</p>
        </div>
      ),
    },
  ]

  if (!agencyId || !entityId || !entityType) return null

  return (
    <section className="border-b border-slate-200 bg-slate-50 py-4" aria-label="Work and deadlines">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="inline-flex items-center gap-2 text-sm font-semibold text-slate-950">
            <ListChecks aria-hidden="true" className="h-4 w-4" />
            Work and deadlines
          </h3>
          <p className="mt-1 text-xs text-slate-600">Canonical tasks linked to this record.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
          <span>{openItems.length} open</span>
          <span className="inline-flex items-center gap-1"><CircleAlert aria-hidden="true" className="h-3.5 w-3.5" />{blockerCount} blocked</span>
          <span>{approvalCount} approvals</span>
          <span>{completedItems.length} completed</span>
          <a className="font-semibold text-blue-700 hover:underline" href={`/agency/work-queue?source_entity_type=${encodeURIComponent(entityType)}&source_entity_id=${encodeURIComponent(entityId)}`}>Open operations queue</a>
        </div>
      </div>
      {loading ? <p className="text-sm text-slate-600" role="status">Loading linked work…</p> : null}
      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">Linked work could not be loaded: {error}</div> : null}
      {!loading && !error ? (
        <ProductTable
          caption={`Work linked to ${entityType}`}
          columns={columns}
          defaultSort={{ key: "deadline", direction: "asc" }}
          emptyBody="Tasks, deadlines, approvals, and blockers will appear here when canonical events require operator action."
          emptyTitle="No linked operational work"
          getRowHref={(item) => `/agency/work-queue?work_item_id=${encodeURIComponent(item.id)}`}
          pageSize={8}
          rows={items}
        />
      ) : null}
      {openItems.some((item) => item.latest_automation_explanation) ? (
        <details className="mt-3 rounded-md border border-slate-200 bg-white p-3 text-xs text-slate-600">
          <summary className="cursor-pointer font-semibold text-slate-800">Advanced automation explanation</summary>
          <div className="mt-2 space-y-2">
            {openItems.filter((item) => item.latest_automation_explanation).slice(0, 5).map((item) => (
              <p key={item.id}>
                <strong>{item.title}:</strong> rule {item.source_automation_rule_id || "unknown"}, source event {item.source_timeline_entry_id || "unknown"}, result {format(item.latest_automation_explanation.status)}.
              </p>
            ))}
          </div>
        </details>
      ) : null}
      {openItems.some((item) => item.due_at) ? <p className="mt-3 inline-flex items-center gap-1 text-xs text-slate-500"><Clock3 aria-hidden="true" className="h-3.5 w-3.5" />Deadlines remain governed by their recorded policy version and manual override history.</p> : null}
    </section>
  )
}

function format(value) {
  return String(value || "not set").replaceAll("_", " ")
}

function formatDateTime(value) {
  if (!value) return "No deadline"
  const parsed = new Date(value)
  return Number.isNaN(parsed.valueOf()) ? String(value) : parsed.toLocaleString()
}
