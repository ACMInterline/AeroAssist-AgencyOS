import { useEffect, useMemo, useState } from "react"
import MessageSquareText from "lucide-react/dist/esm/icons/message-square-text.js"
import EmptyState from "../../components/EmptyState"
import FilterBar from "../../components/FilterBar"
import OperationalAlert from "../../components/OperationalAlert"
import PageHeader from "../../components/PageHeader"
import PrimaryButton from "../../components/PrimaryButton"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPatch } from "../../lib/api"
import { productLabel } from "../../lib/productLanguage"

export default function PilotFeedbackReviewPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ agency_id: "", status: "", category: "", urgency: "" })
  const [selectedId, setSelectedId] = useState("")
  const [review, setReview] = useState({ status: "reviewing", review_notes: "" })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load(nextFilters = filters) {
    const params = new URLSearchParams(Object.entries(nextFilters).filter(([, value]) => value))
    const [me, agencies, feedback] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/pilot-feedback?${params}`),
    ])
    setState({ me, agencies: agencies.items || [], feedback })
    setError("")
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selected = useMemo(() => state?.feedback?.items?.find((item) => item.id === selectedId), [selectedId, state])

  function choose(item) {
    setSelectedId(item.id)
    setReview({ status: item.status === "submitted" ? "reviewing" : item.status, review_notes: item.review_notes || "" })
    setMessage("")
  }

  async function submitReview(event) {
    event.preventDefault()
    setBusy(true)
    setError("")
    try {
      await apiPatch(`/api/platform/pilot-feedback/${selected.id}`, review)
      setMessage("Review status saved with an audit event.")
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <main className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Platform", href: "/platform" }, { label: "Pilot feedback review" }]}
            eyebrow="Commercial Pilot"
            title="Pilot feedback review"
            description="Review tenant-scoped pilot feedback without exposing one agency’s records to another or creating an external ticketing workflow."
          />
          {error ? <OperationalAlert title="Pilot feedback could not be updated" tone="error">{error}</OperationalAlert> : null}
          {message ? <OperationalAlert title="Review saved" tone="success">{message}</OperationalAlert> : null}

          <FilterBar onClear={() => { const next = { agency_id: "", status: "", category: "", urgency: "" }; setFilters(next); load(next).catch((err) => setError(err.message)) }} resultCount={state?.feedback?.items?.length || 0} title="Filter pilot feedback">
            <div className="grid gap-3 md:grid-cols-4">
              <Select label="Agency" value={filters.agency_id} options={(state?.agencies || []).map((item) => [item.id, item.name])} onChange={(value) => setFilters({ ...filters, agency_id: value })} />
              <Select label="Status" value={filters.status} options={(state?.feedback?.filters?.statuses || []).map((item) => [item, productLabel(item)])} onChange={(value) => setFilters({ ...filters, status: value })} />
              <Select label="Category" value={filters.category} options={(state?.feedback?.filters?.categories || []).map((item) => [item, productLabel(item)])} onChange={(value) => setFilters({ ...filters, category: value })} />
              <Select label="Urgency" value={filters.urgency} options={(state?.feedback?.filters?.urgencies || []).map((item) => [item, productLabel(item)])} onChange={(value) => setFilters({ ...filters, urgency: value })} />
            </div>
            <PrimaryButton onClick={() => load().catch((err) => setError(err.message))}>Apply filters</PrimaryButton>
          </FilterBar>

          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
            <section>
              <h2 className="text-base font-semibold text-slate-950">Submissions</h2>
              {(state?.feedback?.items || []).length ? <div className="mt-3 divide-y divide-slate-200 border-y border-slate-200 bg-white">{state.feedback.items.map((item) => <button className={`block w-full px-4 py-4 text-left hover:bg-slate-50 ${selectedId === item.id ? "bg-blue-50" : ""}`} key={item.id} onClick={() => choose(item)} type="button"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase text-slate-500">{item.agency_name} · {productLabel(item.category)}</p><p className="mt-1 font-semibold text-slate-950">{item.title}</p></div><StatusBadge status={item.status} /></div><p className="mt-2 line-clamp-2 text-sm text-slate-600">{item.description}</p><p className="mt-2 text-xs text-slate-500">{productLabel(item.affected_area)} · {productLabel(item.urgency)} · {new Date(item.submitted_at).toLocaleString()}</p></button>)}</div> : <div className="mt-3"><EmptyState icon={MessageSquareText} title="No feedback matches these filters" body="Clear the filters or wait for an Agency user to submit pilot feedback." /></div>}
            </section>

            <aside>
              <h2 className="text-base font-semibold text-slate-950">Review detail</h2>
              {selected ? <form className="mt-3 space-y-4 border-y border-slate-200 bg-white px-5 py-5" onSubmit={submitReview}><div><p className="text-xs font-semibold uppercase text-slate-500">{selected.agency_name}</p><h3 className="mt-1 font-semibold text-slate-950">{selected.title}</h3><p className="mt-3 text-sm leading-6 text-slate-600">{selected.description}</p></div>{selected.related_record_label ? <div className="border-l-2 border-blue-200 pl-3 text-sm text-slate-600"><p className="font-semibold text-slate-800">Related record</p><p>{selected.related_record_label}</p><p className="mt-1 break-all text-xs">{selected.related_record_type} · {selected.related_record_id}</p></div> : null}<Select label="Next status" value={review.status} options={(state?.feedback?.filters?.statuses || []).map((item) => [item, productLabel(item)])} allowAll={false} onChange={(value) => setReview({ ...review, status: value })} /><label className="grid gap-1 text-sm font-medium text-slate-700">Review notes<textarea className="field min-h-28" maxLength="2000" value={review.review_notes} onChange={(event) => setReview({ ...review, review_notes: event.target.value })} placeholder="Decision, next action, or closure context" /></label><p className="text-xs text-slate-500">Lifecycle transitions are validated by the API. References and original submission text remain unchanged.</p><PrimaryButton disabled={busy} type="submit">{busy ? "Saving..." : "Save review"}</PrimaryButton></form> : <div className="mt-3"><EmptyState title="Select a submission" body="Choose feedback from the list to review its context and record a governed status update." /></div>}
            </aside>
          </div>
        </main>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Select({ allowAll = true, label, onChange, options, value }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="field" value={value} onChange={(event) => onChange(event.target.value)}>{allowAll ? <option value="">All</option> : null}{options.map(([key, optionLabel]) => <option value={key} key={key}>{optionLabel}</option>)}</select></label>
}
