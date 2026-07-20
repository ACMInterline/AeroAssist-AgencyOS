import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkflowContinuityPanel from "../../components/WorkflowContinuityPanel"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const initialParams = new URLSearchParams(window.location.search)

const defaultForm = {
  acceptance_id: initialParams.get("acceptance_id") || "",
  booking_readiness_package_id: initialParams.get("booking_readiness_package_id") || "",
  trip_id: initialParams.get("trip_id") || "",
  offer_workspace_id: initialParams.get("offer_workspace_id") || "",
  booking_mode: initialParams.get("booking_mode") || "manual",
  provider_target: initialParams.get("provider_target") || "manual",
}

export default function BookingHandoffsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaultForm)
  const [selectedId, setSelectedId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const selected = useMemo(() => state?.items?.find((item) => item.id === selectedId) || state?.items?.[0] || null, [state, selectedId])
  const canonicalSourceReady = Boolean(form.acceptance_id && form.booking_readiness_package_id)
  const canCreateSelected = Boolean(selected && ["ready", "conditional", "handed_off", "booking_created"].includes(selected.handoff_status))

  async function load(nextForm = form) {
    const context = await loadCurrentAgency()
    const response = await apiGet(`/api/agencies/${context.agency.id}/booking-handoffs${queryString(nextForm)}`)
    setState({ ...context, ...response })
    if (!selectedId && response.items?.[0]?.id) setSelectedId(response.items[0].id)
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  function setField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function buildHandoff(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    if (!canonicalSourceReady) {
      setError("Open Booking Handoff from an accepted offer with a booking readiness package.")
      return
    }
    const payload = Object.fromEntries(Object.entries(form).filter(([, value]) => value !== ""))
    const result = await apiPost(`/api/agencies/${state.agency.id}/booking-handoffs`, {
      ...payload,
      metadata: { ui_route: "/agency/booking-handoffs" },
    })
    setSelectedId(result.handoff.id)
    setMessage(`Handoff ${formatType(result.handoff.handoff_status)} created from accepted-offer snapshot metadata.`)
    await load()
  }

  async function createBookingWorkspace() {
    if (!selected?.id) return
    setError("")
    setMessage("")
    const result = await apiPost(`/api/agencies/${state.agency.id}/booking-handoffs/${selected.id}/create-booking-workspace`, {
      booking_mode: selected.booking_mode || form.booking_mode,
      provider_target: selected.provider_target || form.provider_target,
      create_draft_record: true,
      allow_conditional: true,
      internal_notes: "Created from offer-to-booking handoff readiness metadata.",
    })
    setMessage(`Booking workspace ${result.booking_workspace?.workspace_number || result.booking_workspace?.id} is linked to the handoff.`)
    await load()
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Booking Handoffs</h2>
              <p className="mt-1 text-sm text-slate-600">Accepted-offer to booking readiness metadata. This page consumes frozen accepted snapshots and existing booking readiness packages. It does not recreate prices from mutable offers, book live inventory, issue tickets, process payments, call providers, use AI, or run background workers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Human controlled</span>
            </div>
          </div>

          <WorkflowContinuityPanel
            breadcrumbs={[{ label: "Offers", href: "/agency/offers" }, { label: "Booking handoffs", href: "/agency/booking-handoffs" }]}
            currentLabel={selected?.handoff_reference || "Booking Handoff"}
            status={selected?.handoff_status || "draft"}
            validation={selected
              ? { state: selected.blocker_count ? "blocked" : selected.warning_count ? "warning" : "ready", label: selected.blocker_count ? "Handoff blocked" : selected.warning_count ? "Conditional review" : "Booking handoff ready", reason: selected.blocker_count ? "Resolve readiness blockers before creating a booking workspace." : "The accepted snapshot and mappings remain the source." }
              : { state: canonicalSourceReady ? "warning" : "blocked", label: canonicalSourceReady ? "Assessment required" : "Canonical source required", reason: canonicalSourceReady ? "Build the assessed handoff from this accepted offer." : "Return to an accepted offer; IDs cannot be entered manually here." }}
            previous={(form.offer_workspace_id || selected?.offer_workspace_id) ? { label: "Previous: accepted offer", href: `/agency/offers/${form.offer_workspace_id || selected.offer_workspace_id}` } : { label: "Offers", href: "/agency/offers" }}
            next={selected?.booking_workspace_id
              ? { label: "Continue to booking", href: `/agency/booking-workspaces/${selected.booking_workspace_id}` }
              : { label: "Create booking workspace", onClick: createBookingWorkspace, enabled: canCreateSelected, reason: "A ready or explicitly conditional handoff is required." }}
            relatedRecords={[
              { label: "Acceptance", value: form.acceptance_id ? "frozen" : "missing" },
              { label: "Readiness", value: selected?.readiness_status || (form.booking_readiness_package_id ? "linked" : "missing") },
              { label: "Trip", value: form.trip_id || selected?.trip_id || "missing", href: (form.trip_id || selected?.trip_id) ? `/agency/trips/${form.trip_id || selected.trip_id}` : undefined },
            ]}
          />

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            <Metric label="Handoffs" value={state?.summary?.handoff_count || 0} />
            <Metric label="Blocked" value={state?.summary?.blocked_count || 0} />
            <Metric label="Conditional" value={state?.summary?.conditional_count || 0} />
            <Metric label="Ready" value={state?.summary?.ready_count || 0} />
            <Metric label="Booking created" value={state?.summary?.booking_created_count || 0} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={buildHandoff}>
              <h3 className="font-semibold text-slate-950">Build handoff</h3>
              <div className={`rounded-md border p-3 text-sm ${canonicalSourceReady ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "border-red-200 bg-red-50 text-red-800"}`}>
                <p className="font-semibold">Accepted-offer source</p>
                <p className="mt-1">{canonicalSourceReady ? "Frozen acceptance and booking readiness are locked from the source Offer." : "No accepted-offer source is present. Open this workspace from an accepted Offer."}</p>
                {form.offer_workspace_id ? <a className="mt-2 inline-flex font-semibold text-blue-700 underline" href={`/agency/offers/${form.offer_workspace_id}`}>Review source offer</a> : null}
              </div>
              <SelectField label="Booking mode" value={form.booking_mode} onChange={(value) => setField("booking_mode", value)} options={["manual", "pnr_import", "imported_gds", "imported_confirmation", "supplier_reference"]} />
              <SelectField label="Provider target" value={form.provider_target} onChange={(value) => setField("provider_target", value)} options={["manual", "travelport", "amadeus", "ndc", "supplier", "other"]} />
              <button className="aa-primary-action w-full rounded-md px-3 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50" type="submit" disabled={!canonicalSourceReady}>Build readiness handoff</button>
            </form>

            <div className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h3 className="font-semibold text-slate-950">Handoff list</h3>
                  {selected?.booking_workspace_id ? <a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href={`/agency/booking-workspaces/${selected.booking_workspace_id}`}>Open booking workspace</a> : null}
                </div>
                {!state?.items?.length ? <EmptyState title="No booking handoffs" body="Build a handoff from an accepted offer or booking readiness package." /> : (
                  <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                    {state.items.map((item) => (
                      <button className={`grid w-full gap-3 px-4 py-3 text-left text-sm hover:bg-slate-50 lg:grid-cols-[1.2fr_0.8fr_0.8fr_0.8fr] ${item.id === selected?.id ? "bg-blue-50" : ""}`} key={item.id} type="button" onClick={() => setSelectedId(item.id)}>
                        <span className="font-semibold text-slate-950">{item.handoff_reference}</span>
                        <span>{formatType(item.handoff_status)}</span>
                        <span>{item.warning_count || 0} warnings</span>
                        <span>{item.blocker_count || 0} blockers</span>
                      </button>
                    ))}
                  </div>
                )}
              </section>

              <HandoffDetail handoff={selected} onCreateBookingWorkspace={createBookingWorkspace} />
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function HandoffDetail({ handoff, onCreateBookingWorkspace }) {
  if (!handoff) return <EmptyState title="No handoff selected" body="Select or build a handoff to review readiness." />
  const checks = handoff.checks || []
  const mappings = handoff.mappings || []
  const instructions = handoff.instructions || []
  const canCreate = ["ready", "conditional", "handed_off", "booking_created"].includes(handoff.handoff_status)
  return (
    <section className="space-y-4">
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">{formatType(handoff.handoff_status)}</p>
            <h3 className="mt-1 font-semibold text-slate-950">{handoff.handoff_reference}</h3>
            <p className="mt-1 text-sm text-slate-600">Readiness: {formatType(handoff.readiness_status)} · Mode: {formatType(handoff.booking_mode)} · Provider: {formatType(handoff.provider_target)}</p>
          </div>
          {handoff.booking_workspace_id ? (
            <a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href={`/agency/booking-workspaces/${handoff.booking_workspace_id}`}>Open booking workspace</a>
          ) : (
            <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" disabled={!canCreate} onClick={onCreateBookingWorkspace}>Create booking workspace</button>
          )}
        </div>
      </div>
      <Card title="Readiness checklist">
        <div className="grid gap-2 md:grid-cols-2">
          {checks.map((check) => <CheckRow check={check} key={check.id || check.check_key} />)}
        </div>
      </Card>
      <Card title="Passenger / segment / service mappings">
        <CompactTable rows={mappings} columns={["mapping_type", "source_entity_type", "target_entity_type", "mapping_status"]} />
      </Card>
      <Card title="Booking instructions">
        {instructions.map((instruction) => (
          <div className="rounded-md border border-slate-200 p-3" key={instruction.id}>
            <p className="font-semibold text-slate-950">{instruction.title}</p>
            <p className="mt-1 text-sm text-slate-600">{instruction.summary}</p>
            <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
              <span>Status: {formatType(instruction.instruction_status)}</span>
              <span>Mode: {formatType(instruction.booking_mode)}</span>
              <span>Ticket expected: {instruction.ticket_expectations_json?.ticket_expected ? "yes" : "review"}</span>
              <span>EMD possible: {instruction.emd_expectations_json?.emd_possible ? "yes" : "review"}</span>
            </div>
          </div>
        ))}
      </Card>
      <Card title="Trace separation">
        <div className="grid gap-3 md:grid-cols-2">
          <JsonPreview label="Client-facing trace" value={handoff.client_trace_json} />
          <JsonPreview label="Internal trace" value={handoff.internal_trace_json} />
        </div>
      </Card>
    </section>
  )
}

function CheckRow({ check }) {
  const tone = check.status === "blocked" ? "border-red-200 bg-red-50 text-red-800" : check.status === "warning" ? "border-amber-200 bg-amber-50 text-amber-900" : "border-slate-200 bg-slate-50 text-slate-700"
  return (
    <div className={`rounded-md border p-3 text-sm ${tone}`}>
      <p className="font-semibold">{check.label}</p>
      <p className="mt-1">{formatType(check.status)} · {formatType(check.category)}</p>
      <p className="mt-1 text-xs">{check.details}</p>
    </div>
  )
}

function CompactTable({ rows, columns }) {
  if (!rows?.length) return <EmptyState title="No rows" body="Metadata will appear after a handoff is built." />
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
            {columns.map((column) => <th className="px-3 py-2" key={column}>{formatType(column)}</th>)}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row) => (
            <tr key={row.id}>
              {columns.map((column) => <td className="px-3 py-2 text-slate-700" key={column}>{formatType(row[column])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function JsonPreview({ label, value }) {
  return (
    <details className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <summary className="cursor-pointer text-sm font-semibold text-slate-950">{label}</summary>
      <pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap text-xs text-slate-600">{JSON.stringify(value || {}, null, 2)}</pre>
    </details>
  )
}

function Card({ title, children }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><div className="mt-4">{children}</div></section>
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function SelectField({ label, value, onChange, options }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{formatType(option)}</option>)}</select></label>
}

function queryString(values) {
  const params = new URLSearchParams()
  Object.entries(values || {}).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function formatType(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  return String(value).replaceAll("_", " ")
}
