import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkflowContinuityPanel from "../../components/WorkflowContinuityPanel"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const caseTypes = [
  "voluntary_change",
  "schedule_change",
  "cancellation",
  "refund",
  "ticket_exchange",
  "emd_exchange_refund",
  "claim",
  "service_amendment",
  "passenger_document_amendment",
  "disruption_irregular_operation",
]

const defaultForm = {
  case_type: "voluntary_change",
  case_priority: "normal",
  case_title: "",
  case_summary: "",
  trip_workspace_id: "",
  booking_workspace_id: "",
  ticket_workspace_id: "",
  emd_workspace_id: "",
  passenger_workspace_id: "",
  passenger_service_request_id: "",
  invoice_id: "",
  payment_record_id: "",
  invoice_line_item_id: "",
  ticket_record_id: "",
  emd_record_id: "",
  accepted_offer_snapshot_id: "",
  affected_segment_ref: "",
  residual_value_summary: "",
  penalty_summary: "",
  fare_difference_summary: "",
  service_fee_summary: "",
  refundability_summary: "",
  client_approval_required: false,
  supplier_communication_required: false,
}

const defaultImpact = {
  amount_category: "unknown", amount: "", currency: "EUR", invoice_id: "", invoice_line_item_id: "",
  payment_record_id: "", ticket_record_id: "", emd_record_id: "", approval_state: "not_reviewed",
  accepted_offer_snapshot_id: "", settlement_state: "not_settled", reconciliation_state: "unreconciled",
  mismatch: "", proposed_notes: "", final_notes: "",
}

export default function AfterSalesPage() {
  const [state, setState] = useState(null)
  const query = useMemo(() => new URLSearchParams(window.location.search), [])
  const [form, setForm] = useState(() => ({
    ...defaultForm,
    booking_workspace_id: query.get("booking_workspace_id") || "",
    ticket_workspace_id: query.get("ticket_workspace_id") || "",
    emd_workspace_id: query.get("emd_workspace_id") || "",
    passenger_service_request_id: query.get("passenger_service_request_id") || "",
    ticket_record_id: query.get("ticket_record_id") || "",
    emd_record_id: query.get("emd_record_id") || "",
    invoice_id: query.get("invoice_id") || "",
  }))
  const [filters, setFilters] = useState({ status: "", case_type: "" })
  const [selectedId, setSelectedId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [impactForm, setImpactForm] = useState(defaultImpact)
  const selected = useMemo(
    () => state?.selectedCase?.id === selectedId
      ? state.selectedCase
      : state?.items?.find((item) => item.id === selectedId) || state?.items?.[0] || null,
    [state, selectedId],
  )
  const linkOptions = state?.linkOptions || {}
  const caseWarnings = useMemo(() => selectionWarnings(form, linkOptions), [form, linkOptions])

  async function load(nextFilters = filters, preferredId = selectedId) {
    const context = await loadCurrentAgency()
    const [response, options] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/after-sales${queryString(nextFilters)}`),
      apiGet(`/api/agencies/${context.agency.id}/after-sales/link-options`),
    ])
    const caseId = response.items?.some((item) => item.id === preferredId) ? preferredId : response.items?.[0]?.id || ""
    const detail = caseId
      ? await apiGet(`/api/agencies/${context.agency.id}/after-sales/${caseId}`)
      : { case: null }
    setState({ ...context, ...response, linkOptions: options.items || {}, selectedCase: detail.case })
    setSelectedId(caseId)
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  function setField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function createCase(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    const payload = {
      case_type: form.case_type,
      case_priority: form.case_priority,
      case_title: form.case_title || `${formatType(form.case_type)} case`,
      case_summary: form.case_summary || undefined,
      trip_workspace_id: form.trip_workspace_id || undefined,
      booking_workspace_id: form.booking_workspace_id || undefined,
      ticket_workspace_ids: form.ticket_workspace_id ? [form.ticket_workspace_id] : [],
      emd_workspace_ids: form.emd_workspace_id ? [form.emd_workspace_id] : [],
      passenger_workspace_ids: form.passenger_workspace_id ? [form.passenger_workspace_id] : [],
      passenger_service_request_ids: form.passenger_service_request_id ? [form.passenger_service_request_id] : [],
      invoice_ids: form.invoice_id ? [form.invoice_id] : [],
      invoice_line_item_ids: form.invoice_line_item_id ? [form.invoice_line_item_id] : [],
      payment_record_ids: form.payment_record_id ? [form.payment_record_id] : [],
      ticket_record_ids: form.ticket_record_id ? [form.ticket_record_id] : [],
      emd_record_ids: form.emd_record_id ? [form.emd_record_id] : [],
      accepted_offer_snapshot_id: form.accepted_offer_snapshot_id || undefined,
      affected_segment_refs: form.affected_segment_ref ? [form.affected_segment_ref] : [],
      residual_value_summary: form.residual_value_summary || undefined,
      penalty_summary: form.penalty_summary || undefined,
      fare_difference_summary: form.fare_difference_summary || undefined,
      service_fee_summary: form.service_fee_summary || undefined,
      refundability_summary: form.refundability_summary || undefined,
      client_approval_required: form.client_approval_required,
      supplier_communication_required: form.supplier_communication_required,
      internal_message_json: { note: "Created from agency after-sales workspace." },
      generated_advice_json: { advice_status: "draft_metadata", execution_disabled: true },
      metadata: { ui_route: "/agency/after-sales" },
    }
    const result = await apiPost(`/api/agencies/${state.agency.id}/after-sales`, payload)
    setSelectedId(result.case.id)
    setMessage(`After-sales case ${result.case.case_reference} created as metadata only.`)
    setForm(defaultForm)
    await load(filters, result.case.id)
  }

  async function recordFinancialImpact(event) {
    event.preventDefault()
    if (!selected?.id) return
    setError("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/after-sales/${selected.id}/financial-impacts`, {
        impact_type: impactForm.amount_category,
        amount_category: impactForm.amount_category,
        estimate_status: "manual_review",
        amount: impactForm.amount === "" ? undefined : Number(impactForm.amount),
        currency: impactForm.currency || undefined,
        invoice_ids: impactForm.invoice_id ? [impactForm.invoice_id] : [],
        invoice_line_item_ids: impactForm.invoice_line_item_id ? [impactForm.invoice_line_item_id] : [],
        payment_record_ids: impactForm.payment_record_id ? [impactForm.payment_record_id] : [],
        ticket_record_ids: impactForm.ticket_record_id ? [impactForm.ticket_record_id] : [],
        emd_record_ids: impactForm.emd_record_id ? [impactForm.emd_record_id] : [],
        accepted_offer_snapshot_id: impactForm.accepted_offer_snapshot_id || undefined,
        approval_state: impactForm.approval_state,
        settlement_state: impactForm.settlement_state,
        reconciliation_state: impactForm.reconciliation_state,
        unresolved_mismatches_json: impactForm.mismatch ? [{ code: "manual_financial_mismatch", message: impactForm.mismatch }] : [],
        proposed_financial_impact_snapshot_json: { operator_notes: impactForm.proposed_notes, manual_metadata: true },
        final_reconciled_financial_snapshot_json: impactForm.reconciliation_state === "reconciled" && impactForm.final_notes ? { operator_notes: impactForm.final_notes, reviewed_metadata: true } : {},
        calculation_basis: "Manual affected-record review; no payment, settlement, fare recalculation, or ledger mutation performed.",
      })
      setImpactForm(defaultImpact)
      setMessage("Affected financial records and impact snapshot recorded for manual reconciliation.")
      await load(filters, selected.id)
    } catch (err) {
      setError(err.message)
    }
  }

  async function updateStatus(caseStatus) {
    if (!selected?.id) return
    setError("")
    const result = await apiPut(`/api/agencies/${state.agency.id}/after-sales/${selected.id}`, { case_status: caseStatus })
    setSelectedId(result.case.id)
    setMessage(`Case status recorded as ${formatType(caseStatus)}.`)
    await load(filters, result.case.id)
  }

  async function selectCase(caseId) {
    setError("")
    try {
      const detail = await apiGet(`/api/agencies/${state.agency.id}/after-sales/${caseId}`)
      setSelectedId(caseId)
      setState((current) => ({ ...current, selectedCase: detail.case }))
    } catch (err) {
      setError(err.message)
    }
  }

  function applyFilters(next) {
    setFilters(next)
    load(next).catch((err) => setError(err.message))
  }

  const previousRecord = selected?.invoice_ids?.[0]
    ? { label: "Previous: finance", href: `/agency/invoices/${selected.invoice_ids[0]}` }
    : selected?.passenger_service_request_ids?.[0] ? { label: "Previous: passenger service", href: `/agency/passenger-services?service_id=${encodeURIComponent(selected.passenger_service_request_ids[0])}` }
      : selected?.ticket_record_ids?.[0] ? { label: "Previous: ticket", href: `/agency/tickets/${selected.ticket_record_ids[0]}` }
        : selected?.booking_workspace_id ? { label: "Previous: booking", href: `/agency/booking-workspaces/${selected.booking_workspace_id}` }
          : { label: "Operations", href: "/agency/operations-command-center" }
  const caseResolved = ["resolved", "rejected", "cancelled", "archived"].includes(selected?.case_status)

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Servicing</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">After-Sales</h2>
              <p className="mt-1 text-sm text-slate-600">Unified servicing workflow metadata for changes, refunds, exchanges, claims, amendments, and disruptions. This workspace does not mutate tickets or EMDs, commit money, call providers, send messages, use AI, or automate execution.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Human authority final</span>
            </div>
          </div>

          <WorkflowContinuityPanel
            breadcrumbs={[{ label: "Finance", href: "/agency/invoices" }, { label: "After Sales", href: "/agency/after-sales" }]}
            currentLabel={selected?.case_reference || "After-Sales Case"}
            status={selected?.case_status || "not opened"}
            validation={!selected
              ? { state: "warning", label: "Case not opened", reason: "Select canonical affected records before creating a case." }
              : caseResolved ? { state: "ready", label: "Operational resolution recorded", reason: "The case is complete and source records remain immutable." }
                : { state: "warning", label: "Resolution pending", reason: "Complete decisions, approvals, communications, and resolution before closing the workflow." }}
            previous={previousRecord}
            next={{ label: "Complete workflow", href: caseResolved ? (selected?.trip_workspace_id ? `/agency/trips/${selected.trip_workspace_id}` : "/agency/operations-command-center") : undefined, enabled: caseResolved, reason: "Record a terminal case resolution first." }}
            relatedRecords={[
              { label: "Affected records", value: selected?.items?.length || 0 },
              { label: "Invoices", value: selected?.invoice_ids?.length || 0, href: selected?.invoice_ids?.[0] ? `/agency/invoices/${selected.invoice_ids[0]}` : undefined },
              { label: "Workflow", value: selected?.workflow_instance_id || "not linked" },
            ]}
          />

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            <Metric label="Cases" value={state?.summary?.case_count || 0} />
            <Metric label="Open" value={state?.summary?.open_case_count || 0} />
            <Metric label="Client approvals" value={state?.summary?.requires_client_approval_count || 0} />
            <Metric label="Supplier contact" value={state?.summary?.requires_supplier_communication_count || 0} />
            <Metric label="Financial placeholders" value={state?.recent_financial_impacts?.length || 0} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createCase}>
              <h3 className="font-semibold text-slate-950">Open case metadata</h3>
              <p className="text-xs text-slate-500">Search by operational label, review the context preview, then link existing agency records.</p>
              <SelectField label="Case type" value={form.case_type} onChange={(value) => setField("case_type", value)} options={caseTypes} />
              <SelectField label="Priority" value={form.case_priority} onChange={(value) => setField("case_priority", value)} options={["low", "normal", "high", "urgent", "critical"]} />
              <TextField label="Title" value={form.case_title} onChange={(value) => setField("case_title", value)} />
              <TextArea label="Summary" value={form.case_summary} onChange={(value) => setField("case_summary", value)} />
              <div className="grid gap-4">
                <EntitySelector label="Trip" value={form.trip_workspace_id} onChange={(value) => setField("trip_workspace_id", value)} items={linkOptions.trips} />
                <EntitySelector label="Booking" value={form.booking_workspace_id} onChange={(value) => setField("booking_workspace_id", value)} items={linkOptions.bookings} />
                <EntitySelector label="Ticket workspace" value={form.ticket_workspace_id} onChange={(value) => setField("ticket_workspace_id", value)} items={linkOptions.ticket_workspaces} />
                <EntitySelector label="EMD workspace" value={form.emd_workspace_id} onChange={(value) => setField("emd_workspace_id", value)} items={linkOptions.emd_workspaces} />
                <EntitySelector label="Passenger" value={form.passenger_workspace_id} onChange={(value) => setField("passenger_workspace_id", value)} items={linkOptions.passengers} />
                <EntitySelector label="Passenger service" value={form.passenger_service_request_id} onChange={(value) => setField("passenger_service_request_id", value)} items={linkOptions.passenger_services} />
                <EntitySelector label="Trip segment" value={form.affected_segment_ref} onChange={(value) => setField("affected_segment_ref", value)} items={linkOptions.segments} />
                <EntitySelector label="Accepted offer" value={form.accepted_offer_snapshot_id} onChange={(value) => setField("accepted_offer_snapshot_id", value)} items={linkOptions.accepted_offer_snapshots} />
                <EntitySelector label="Invoice" value={form.invoice_id} onChange={(value) => setField("invoice_id", value)} items={linkOptions.invoices} />
                <EntitySelector label="Invoice line" value={form.invoice_line_item_id} onChange={(value) => setField("invoice_line_item_id", value)} items={contextItems(linkOptions.invoice_lines, "invoice_id", form.invoice_id)} />
                <EntitySelector label="Payment" value={form.payment_record_id} onChange={(value) => setField("payment_record_id", value)} items={contextItems(linkOptions.payments, "invoice_id", form.invoice_id)} />
                <EntitySelector label="Ticket" value={form.ticket_record_id} onChange={(value) => setField("ticket_record_id", value)} items={linkOptions.tickets} />
                <EntitySelector label="EMD" value={form.emd_record_id} onChange={(value) => setField("emd_record_id", value)} items={linkOptions.emds} />
              </div>
              <SelectionWarnings warnings={caseWarnings} />
              <SelectionPreview title="Selected operating context" values={selectedOptions(form, linkOptions)} />
              <TextArea label="Financial estimate notes" value={form.refundability_summary} onChange={(value) => setField("refundability_summary", value)} />
              <div className="grid gap-2 text-sm text-slate-700">
                <label className="flex items-center gap-2"><input type="checkbox" checked={form.client_approval_required} onChange={(event) => setField("client_approval_required", event.target.checked)} /> Client approval required</label>
                <label className="flex items-center gap-2"><input type="checkbox" checked={form.supplier_communication_required} onChange={(event) => setField("supplier_communication_required", event.target.checked)} /> Supplier communication required</label>
              </div>
              <button className="aa-primary-action w-full rounded-md px-3 py-2 text-sm font-semibold" type="submit">Create case metadata</button>
            </form>

            <div className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h3 className="font-semibold text-slate-950">Case list</h3>
                  <div className="grid gap-2 md:grid-cols-2">
                    <SelectField label="Status" value={filters.status} onChange={(value) => applyFilters({ ...filters, status: value })} options={["", "opened", "assessing", "awaiting_approval", "processing", "resolved", "cancelled"]} />
                    <SelectField label="Type" value={filters.case_type} onChange={(value) => applyFilters({ ...filters, case_type: value })} options={["", ...caseTypes]} />
                  </div>
                </div>
                {!state?.items?.length ? <EmptyState title="No after-sales cases" body="Create metadata for a servicing, claim, refund, exchange, amendment, or disruption case." /> : (
                  <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                    {state.items.map((item) => (
                      <button className={`grid w-full gap-3 px-4 py-3 text-left text-sm hover:bg-slate-50 lg:grid-cols-[1.2fr_0.8fr_0.8fr_0.7fr] ${item.id === selected?.id ? "bg-blue-50" : ""}`} key={item.id} type="button" onClick={() => selectCase(item.id)}>
                        <span className="font-semibold text-slate-950">{item.case_reference}</span>
                        <span>{formatType(item.case_type)}</span>
                        <span>{formatType(item.case_status)}</span>
                        <span>{formatType(item.case_priority)}</span>
                      </button>
                    ))}
                  </div>
                )}
              </section>

              <CaseWorkspace selected={selected} onUpdateStatus={updateStatus} impactForm={impactForm} setImpactForm={setImpactForm} onRecordFinancialImpact={recordFinancialImpact} linkOptions={linkOptions} />
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function CaseWorkspace({ selected, onUpdateStatus, impactForm, setImpactForm, onRecordFinancialImpact, linkOptions }) {
  if (!selected) return <EmptyState title="No case selected" body="Select a case to review after-sales workspace metadata." />
  return (
    <section className="space-y-4">
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">{formatType(selected.case_status)}</p>
            <h3 className="mt-1 font-semibold text-slate-950">{selected.case_title}</h3>
            <p className="mt-1 text-sm text-slate-600">{selected.case_summary || "No summary recorded."}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {["assessing", "awaiting_approval", "processing", "resolved"].map((statusValue) => (
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700" key={statusValue} type="button" onClick={() => onUpdateStatus(statusValue)}>{formatType(statusValue)}</button>
            ))}
          </div>
        </div>
      </div>

      <Card title="Affected records">
        <CompactTable rows={(selected.items || []).map(withSourceLabel)} columns={["item_type", "source_entity_type", "source_label", "impact_status"]} />
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Financial estimate">
          <CompactTable rows={selected.financial_impacts || []} columns={["amount_category", "estimate_status", "reconciliation_state", "manual_unreconciled", "currency", "amount"]} />
        </Card>
        <Card title="Decisions and approvals">
          <CompactTable rows={selected.decisions || []} columns={["decision_type", "decision_status", "client_approval_status", "decision_summary"]} />
        </Card>
      </div>
      <form className="rounded-lg border border-slate-200 bg-white p-5" onSubmit={onRecordFinancialImpact}>
        <h3 className="font-semibold text-slate-950">Link affected financial records</h3>
        <p className="mt-1 text-sm text-slate-600">Select existing source records and preserve a proposed impact snapshot. This does not process payment, settle funds, recalculate fares, or mutate issued invoices.</p>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <EntitySelector label="Invoice" value={impactForm.invoice_id} onChange={(value) => setImpactForm({ ...impactForm, invoice_id: value })} items={linkOptions.invoices} compact />
          <EntitySelector label="Invoice line" value={impactForm.invoice_line_item_id} onChange={(value) => setImpactForm({ ...impactForm, invoice_line_item_id: value })} items={contextItems(linkOptions.invoice_lines, "invoice_id", impactForm.invoice_id)} compact />
          <EntitySelector label="Payment" value={impactForm.payment_record_id} onChange={(value) => setImpactForm({ ...impactForm, payment_record_id: value })} items={contextItems(linkOptions.payments, "invoice_id", impactForm.invoice_id)} compact />
          <EntitySelector label="Ticket" value={impactForm.ticket_record_id} onChange={(value) => setImpactForm({ ...impactForm, ticket_record_id: value })} items={linkOptions.tickets} compact />
          <EntitySelector label="EMD" value={impactForm.emd_record_id} onChange={(value) => setImpactForm({ ...impactForm, emd_record_id: value })} items={linkOptions.emds} compact />
          <EntitySelector label="Accepted offer" value={impactForm.accepted_offer_snapshot_id} onChange={(value) => setImpactForm({ ...impactForm, accepted_offer_snapshot_id: value })} items={linkOptions.accepted_offer_snapshots} compact />
          <SelectField label="Amount category" value={impactForm.amount_category} onChange={(value) => setImpactForm({ ...impactForm, amount_category: value })} options={["fare_difference", "penalty", "agency_fee", "supplier_fee", "refund", "credit", "residual_value", "commission_adjustment", "tax_adjustment", "unknown"].map((item) => [item, formatType(item)])} />
          <TextField label="Amount" value={impactForm.amount} onChange={(value) => setImpactForm({ ...impactForm, amount: value })} />
          <TextField label="Currency" value={impactForm.currency} onChange={(value) => setImpactForm({ ...impactForm, currency: value.toUpperCase() })} />
          <SelectField label="Approval" value={impactForm.approval_state} onChange={(value) => setImpactForm({ ...impactForm, approval_state: value })} options={["not_reviewed", "pending", "approved", "rejected"].map((item) => [item, formatType(item)])} />
          <SelectField label="Reconciliation" value={impactForm.reconciliation_state} onChange={(value) => setImpactForm({ ...impactForm, reconciliation_state: value })} options={["unreconciled", "manual_review", "partially_reconciled", "reconciled", "unknown"].map((item) => [item, formatType(item)])} />
          <TextField label="Mismatch" value={impactForm.mismatch} onChange={(value) => setImpactForm({ ...impactForm, mismatch: value })} />
          <TextField label="Proposed impact notes" value={impactForm.proposed_notes} onChange={(value) => setImpactForm({ ...impactForm, proposed_notes: value })} />
          <TextField label="Final reconciliation notes" value={impactForm.final_notes} onChange={(value) => setImpactForm({ ...impactForm, final_notes: value })} />
        </div>
        <SelectionWarnings warnings={selectionWarnings(impactForm, linkOptions)} />
        <SelectionPreview title="Financial linkage preview" values={selectedOptions(impactForm, linkOptions)} />
        <button className="aa-primary-action mt-4 rounded-md px-3 py-2 text-sm font-semibold" type="submit">Record affected finance metadata</button>
      </form>
      <Card title="Affected financial records">
        <JsonPreview label="Read-only source summary" value={selected.affected_financial_records} />
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Communications">
          <CompactTable rows={selected.communications || []} columns={["communication_type", "audience", "channel", "summary"]} />
        </Card>
        <Card title="Resolution">
          <CompactTable rows={selected.resolutions || []} columns={["resolution_type", "resolution_status", "resolution_summary"]} />
        </Card>
      </div>
      <Card title="Documents, tasks, deadlines, workflow">
        <div className="grid gap-3 text-sm md:grid-cols-3">
          <Info label="Documents" value={(selected.document_workspace_ids || []).join(", ") || "Not linked"} />
          <Info label="Tasks" value={(selected.task_ids || []).join(", ") || "No generated tasks"} />
          <Info label="Deadlines" value={(selected.deadline_ids || []).join(", ") || "Not set"} />
          <Info label="Work items" value={(selected.work_item_ids || []).join(", ") || "Not set"} />
          <Info label="Workflow" value={selected.workflow_instance_id || "Not linked"} />
          <Info label="Timeline" value={(selected.timeline_entry_ids || []).join(", ") || "Not recorded"} />
        </div>
      </Card>
      <Card title="Coupon and impact scope">
        <JsonPreview label="Coupon status awareness" value={selected.coupon_status_snapshot_json} />
        <JsonPreview label="Impact scope" value={selected.impact_scope_json} />
      </Card>
    </section>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function Card({ title, children }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><div className="mt-4">{children}</div></section>
}

function Info({ label, value }) {
  return <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 break-words text-slate-800">{value}</p></div>
}

function CompactTable({ rows, columns }) {
  if (!rows?.length) return <EmptyState title="No metadata" body="After-sales child metadata will appear here." />
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
              {columns.map((column) => <td className="max-w-xs px-3 py-2 text-slate-700" key={column}>{formatValue(row[column])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function JsonPreview({ label, value }) {
  return <div className="mt-3 rounded-md bg-slate-950 p-3 text-xs text-slate-100"><p className="mb-2 font-semibold text-blue-200">{label}</p><pre className="max-h-48 overflow-auto whitespace-pre-wrap">{JSON.stringify(value || {}, null, 2)}</pre></div>
}

function TextField({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function TextArea({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function SelectField({ label, value, onChange, options }) {
  const normalized = options.map((option) => Array.isArray(option) ? option : [option, option ? formatType(option) : "All"])
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{normalized.map(([option, text]) => <option value={option} key={option}>{text}</option>)}</select></label>
}

function EntitySelector({ label, value, onChange, items = [], compact = false }) {
  const [search, setSearch] = useState("")
  const selected = items.find((item) => item.id === value)
  const filtered = items.filter((item) => item.id === value || `${item.label} ${item.context_preview || ""} ${item.status || ""}`.toLowerCase().includes(search.toLowerCase()))
  return (
    <div className={`grid gap-1 text-sm font-medium text-slate-700 ${compact ? "md:col-span-1" : ""}`}>
      <span>{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={search} onChange={(event) => setSearch(event.target.value)} placeholder={`Search ${label.toLowerCase()}`} />
      <select className="min-w-0 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Not linked</option>
        {filtered.map((item) => <option value={item.id} key={item.id}>{item.label}</option>)}
      </select>
      {selected ? <p className="break-words text-xs font-normal text-slate-500">{selected.context_preview || formatType(selected.status)}{selected.immutable_reference ? " · immutable reference" : ""}</p> : null}
    </div>
  )
}

function SelectionWarnings({ warnings }) {
  if (!warnings.length) return null
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
      <p className="font-semibold">Review before linking</p>
      <ul className="mt-1 list-disc space-y-1 pl-4">{warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
    </div>
  )
}

function SelectionPreview({ title, values }) {
  if (!values.length) return null
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
      <p className="font-semibold text-slate-900">{title}</p>
      <div className="mt-2 grid gap-2">{values.map(({ field, item }) => <div key={field}><span className="font-semibold">{formatType(field)}:</span> {item.label}{item.context_preview ? ` · ${item.context_preview}` : ""}</div>)}</div>
    </div>
  )
}

const selectorFields = [
  ["trip_workspace_id", "trips"],
  ["booking_workspace_id", "bookings"],
  ["ticket_workspace_id", "ticket_workspaces"],
  ["emd_workspace_id", "emd_workspaces"],
  ["passenger_workspace_id", "passengers"],
  ["passenger_service_request_id", "passenger_services"],
  ["affected_segment_ref", "segments"],
  ["accepted_offer_snapshot_id", "accepted_offer_snapshots"],
  ["invoice_id", "invoices"],
  ["invoice_line_item_id", "invoice_lines"],
  ["payment_record_id", "payments"],
  ["ticket_record_id", "tickets"],
  ["emd_record_id", "emds"],
]

function selectedOptions(values, options) {
  return selectorFields.flatMap(([field, group]) => {
    const item = (options[group] || []).find((candidate) => candidate.id === values[field])
    return item ? [{ field, item }] : []
  })
}

function contextItems(items = [], field, value) {
  if (!value) return items
  return items.filter((item) => item.context?.[field] === value)
}

function withSourceLabel(item) {
  const snapshot = item.snapshot_json || {}
  const sourceLabel = snapshot.invoice_number || snapshot.ticket_number || snapshot.emd_number || snapshot.booking_reference
    || snapshot.trip_reference || snapshot.passenger_reference || snapshot.service_label || snapshot.description
    || formatType(item.item_type)
  return { ...item, source_label: sourceLabel }
}

function selectionWarnings(values, options) {
  const selected = selectedOptions(values, options)
  const warnings = selected.flatMap(({ item }) => item.warnings || [])
  if (values.invoice_line_item_id && !values.invoice_id) warnings.push("Select the invoice that owns the invoice line.")
  if (values.payment_record_id && !values.invoice_id) warnings.push("Select the invoice that owns the payment.")
  const invoiceLine = (options.invoice_lines || []).find((item) => item.id === values.invoice_line_item_id)
  const payment = (options.payments || []).find((item) => item.id === values.payment_record_id)
  if (invoiceLine && values.invoice_id && invoiceLine.context?.invoice_id !== values.invoice_id) warnings.push("Invoice line and invoice contexts do not match.")
  if (payment && values.invoice_id && payment.context?.invoice_id !== values.invoice_id) warnings.push("Payment and invoice contexts do not match.")

  const trip = (options.trips || []).find((item) => item.id === values.trip_workspace_id)
  const booking = (options.bookings || []).find((item) => item.id === values.booking_workspace_id)
  const tripIds = new Set([trip?.id, trip?.context?.trip_id].filter(Boolean))
  const bookingIds = new Set([booking?.id, booking?.context?.booking_id, booking?.context?.booking_record_id].filter(Boolean))
  selected.forEach(({ field, item }) => {
    if (["trip_workspace_id", "booking_workspace_id"].includes(field)) return
    const itemTripIds = [item.context?.trip_workspace_id, item.context?.trip_id].filter(Boolean)
    const itemBookingIds = [item.context?.booking_workspace_id, item.context?.booking_record_id, item.context?.booking_id].filter(Boolean)
    if (tripIds.size && itemTripIds.length && !itemTripIds.some((id) => tripIds.has(id))) warnings.push(`${formatType(field)} belongs to a different trip context.`)
    if (bookingIds.size && itemBookingIds.length && !itemBookingIds.some((id) => bookingIds.has(id))) warnings.push(`${formatType(field)} belongs to a different booking context.`)
  })
  return [...new Set(warnings)]
}

function queryString(values) {
  const params = new URLSearchParams()
  Object.entries(values || {}).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  if (typeof value === "object") return JSON.stringify(value)
  return formatType(value)
}

function formatType(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  return String(value).replaceAll("_", " ")
}
