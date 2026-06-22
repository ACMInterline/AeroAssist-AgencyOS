import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import RefundExchangeStatusBadge from "../../components/RefundExchangeStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const CASE_TYPES = [
  "refund",
  "exchange",
  "void",
  "schedule_change",
  "involuntary_change",
  "cancellation",
  "other",
]

const CASE_REASONS = [
  "client_request",
  "illness",
  "visa_document_issue",
  "schedule_change",
  "disruption",
  "duplicate_booking",
  "wrong_name",
  "fare_rule_change",
  "agency_error",
  "airline_error",
  "other",
]

const CASE_PRIORITIES = ["low", "normal", "high", "urgent"]
const CASE_STATUSES = [
  "draft",
  "client_requested",
  "review_needed",
  "checking_supplier_rules",
  "waiting_for_client",
  "waiting_for_supplier",
  "approved",
  "processing_externally",
  "completed",
  "rejected",
  "cancelled",
  "archived",
]

const ITEM_TYPES = ["ticket", "emd", "invoice", "payment", "booking_segment", "passenger", "other"]
const ITEM_STATUSES = ["pending", "eligible", "not_eligible", "submitted", "approved", "rejected", "processed", "cancelled"]

const FINANCIAL_LINE_TYPES = [
  "refundable_fare",
  "refundable_taxes",
  "airline_penalty",
  "supplier_fee",
  "agency_fee",
  "exchange_fare_difference",
  "exchange_tax_difference",
  "payment_refund",
  "credit_voucher",
  "discount",
  "other",
]

const FINANCIAL_DIRECTIONS = ["due_to_client", "due_from_client", "neutral"]

const INITIAL_CASE_FORM = {
  case_type: "refund",
  priority: "normal",
  reason_category: "client_request",
  client_reason_text: "",
  internal_summary: "",
  client_visible_summary: "",
  supplier_reference: "",
  expected_supplier_response_at: "",
  deadline_at: "",
  estimated_refund_amount: "",
  estimated_penalty_amount: "",
  estimated_exchange_difference_amount: "",
  estimated_agency_fee_amount: "",
  estimated_total_due_from_client: "",
  estimated_total_due_to_client: "",
  final_refund_amount: "",
  final_penalty_amount: "",
  final_exchange_difference_amount: "",
  final_agency_fee_amount: "",
  final_total_due_from_client: "",
  final_total_due_to_client: "",
  currency: "EUR",
  client_visible: true,
}

const INITIAL_ITEM_FORM = {
  item_type: "ticket",
  ref_id: "",
  description: "",
  status: "pending",
  estimated_amount: "",
  final_amount: "",
  currency: "EUR",
  internal_notes: "",
  client_visible_notes: "",
}

const INITIAL_LINE_FORM = {
  line_type: "refundable_fare",
  description: "",
  amount: "",
  currency: "EUR",
  direction: "neutral",
  supplier_pass_through: false,
  client_visible: true,
  internal_notes: "",
}

export default function RefundExchangeCaseDetailPage({ caseId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  const [status, setStatus] = useState("draft")
  const [caseForm, setCaseForm] = useState(INITIAL_CASE_FORM)
  const [itemForm, setItemForm] = useState(INITIAL_ITEM_FORM)
  const [lineForm, setLineForm] = useState(INITIAL_LINE_FORM)
  const [message, setMessage] = useState("")
  const [messageVisibility, setMessageVisibility] = useState("internal")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/refund-exchange-cases/${caseId}`)
    const caseObj = detail.case
    setState({ ...context, ...detail })
    setStatus(caseObj.status)
    setCaseForm((current) => ({
      ...current,
      case_type: caseObj.case_type || current.case_type,
      priority: caseObj.priority || current.priority,
      reason_category: caseObj.reason_category || current.reason_category,
      client_reason_text: caseObj.client_reason_text || "",
      internal_summary: caseObj.internal_summary || "",
      client_visible_summary: caseObj.client_visible_summary || "",
      supplier_reference: caseObj.supplier_reference || "",
      expected_supplier_response_at: caseObj.expected_supplier_response_at || "",
      deadline_at: caseObj.deadline_at || "",
      estimated_refund_amount: caseObj.estimated_refund_amount ?? "",
      estimated_penalty_amount: caseObj.estimated_penalty_amount ?? "",
      estimated_exchange_difference_amount: caseObj.estimated_exchange_difference_amount ?? "",
      estimated_agency_fee_amount: caseObj.estimated_agency_fee_amount ?? "",
      estimated_total_due_from_client: caseObj.estimated_total_due_from_client ?? "",
      estimated_total_due_to_client: caseObj.estimated_total_due_to_client ?? "",
      final_refund_amount: caseObj.final_refund_amount ?? "",
      final_penalty_amount: caseObj.final_penalty_amount ?? "",
      final_exchange_difference_amount: caseObj.final_exchange_difference_amount ?? "",
      final_agency_fee_amount: caseObj.final_agency_fee_amount ?? "",
      final_total_due_from_client: caseObj.final_total_due_from_client ?? "",
      final_total_due_to_client: caseObj.final_total_due_to_client ?? "",
      currency: caseObj.currency || "EUR",
      client_visible: caseObj.client_visible !== false,
    }))

    setItemForm((current) => ({
      ...current,
      currency: caseObj.currency || current.currency,
    }))
    setLineForm((current) => ({
      ...current,
      currency: caseObj.currency || current.currency,
    }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [caseId])

  function updateCaseForm(name, value) {
    setCaseForm((current) => ({ ...current, [name]: value }))
  }

  function updateItemForm(name, value) {
    setItemForm((current) => ({ ...current, [name]: value }))
  }

  function updateLineForm(name, value) {
    setLineForm((current) => ({ ...current, [name]: value }))
  }

  function asNumber(value) {
    if (value === "" || value === undefined || value === null) return undefined
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : undefined
  }

  function buildCasePayload() {
    return {
      case_type: caseForm.case_type,
      priority: caseForm.priority,
      reason_category: caseForm.reason_category,
      client_reason_text: caseForm.client_reason_text || undefined,
      internal_summary: caseForm.internal_summary || undefined,
      client_visible_summary: caseForm.client_visible_summary || undefined,
      supplier_reference: caseForm.supplier_reference || undefined,
      expected_supplier_response_at: caseForm.expected_supplier_response_at || undefined,
      deadline_at: caseForm.deadline_at || undefined,
      estimated_refund_amount: asNumber(caseForm.estimated_refund_amount),
      estimated_penalty_amount: asNumber(caseForm.estimated_penalty_amount),
      estimated_exchange_difference_amount: asNumber(caseForm.estimated_exchange_difference_amount),
      estimated_agency_fee_amount: asNumber(caseForm.estimated_agency_fee_amount),
      estimated_total_due_from_client: asNumber(caseForm.estimated_total_due_from_client),
      estimated_total_due_to_client: asNumber(caseForm.estimated_total_due_to_client),
      final_refund_amount: asNumber(caseForm.final_refund_amount),
      final_penalty_amount: asNumber(caseForm.final_penalty_amount),
      final_exchange_difference_amount: asNumber(caseForm.final_exchange_difference_amount),
      final_agency_fee_amount: asNumber(caseForm.final_agency_fee_amount),
      final_total_due_from_client: asNumber(caseForm.final_total_due_from_client),
      final_total_due_to_client: asNumber(caseForm.final_total_due_to_client),
      currency: caseForm.currency || "EUR",
      client_visible: caseForm.client_visible,
    }
  }

  function buildItemPayload() {
    const payload = {
      item_type: itemForm.item_type,
      description: itemForm.description || undefined,
      status: itemForm.status,
      estimated_amount: asNumber(itemForm.estimated_amount),
      final_amount: asNumber(itemForm.final_amount),
      currency: itemForm.currency || "EUR",
      internal_notes: itemForm.internal_notes || undefined,
      client_visible_notes: itemForm.client_visible_notes || undefined,
    }

    if (itemForm.item_type === "ticket") payload.ticket_id = itemForm.ref_id || undefined
    else if (itemForm.item_type === "emd") payload.emd_id = itemForm.ref_id || undefined
    else if (itemForm.item_type === "invoice") payload.invoice_id = itemForm.ref_id || undefined
    else if (itemForm.item_type === "payment") payload.payment_id = itemForm.ref_id || undefined
    else if (itemForm.item_type === "booking_segment") payload.item_id = itemForm.ref_id || undefined
    else if (itemForm.item_type === "passenger") payload.passenger_id = itemForm.ref_id || undefined
    return payload
  }

  function buildFinancialLinePayload() {
    return {
      line_type: lineForm.line_type,
      description: lineForm.description,
      amount: asNumber(lineForm.amount),
      currency: lineForm.currency || "EUR",
      direction: lineForm.direction,
      supplier_pass_through: !!lineForm.supplier_pass_through,
      client_visible: !!lineForm.client_visible,
      internal_notes: lineForm.internal_notes || undefined,
    }
  }

  async function saveCase(event) {
    event.preventDefault()
    const payload = buildCasePayload()
    await apiPut(`/api/agencies/${state.agency.id}/refund-exchange-cases/${caseId}`, payload)
    await load()
  }

  async function saveStatus(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/refund-exchange-cases/${caseId}/status`, { status })
    await load()
  }

  async function archiveCase() {
    await apiPost(`/api/agencies/${state.agency.id}/refund-exchange-cases/${caseId}/archive`)
    window.location.href = "/agency/refunds-exchanges"
  }

  async function addItem(event) {
    event.preventDefault()
    const payload = buildItemPayload()
    await apiPost(`/api/agencies/${state.agency.id}/refund-exchange-cases/${caseId}/items`, payload)
    setItemForm(INITIAL_ITEM_FORM)
    await load()
  }

  async function addFinancialLine(event) {
    event.preventDefault()
    const payload = buildFinancialLinePayload()
    await apiPost(`/api/agencies/${state.agency.id}/refund-exchange-cases/${caseId}/financial-lines`, payload)
    setLineForm(INITIAL_LINE_FORM)
    await load()
  }

  async function sendMessage(event) {
    event.preventDefault()
    if (!message.trim()) return
    await apiPost(`/api/agencies/${state.agency.id}/refund-exchange-cases/${caseId}/messages`, {
      sender_type: "staff",
      visibility: messageVisibility,
      message_text: message,
    })
    setMessage("")
    await load()
  }

  const amountValues = [
    ["Estimated Refund", state?.case?.estimated_refund_amount],
    ["Estimated Penalty", state?.case?.estimated_penalty_amount],
    ["Estimated Exchange", state?.case?.estimated_exchange_difference_amount],
    ["Estimated Agency Fee", state?.case?.estimated_agency_fee_amount],
    ["Estimated Due From Client", state?.case?.estimated_total_due_from_client],
    ["Estimated Due To Client", state?.case?.estimated_total_due_to_client],
    ["Final Refund", state?.case?.final_refund_amount],
    ["Final Penalty", state?.case?.final_penalty_amount],
    ["Final Exchange", state?.case?.final_exchange_difference_amount],
    ["Final Agency Fee", state?.case?.final_agency_fee_amount],
    ["Final Due From Client", state?.case?.final_total_due_from_client],
    ["Final Due To Client", state?.case?.final_total_due_to_client],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/refunds-exchanges">Back to refunds/exchanges</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state?.case?.case_reference}</p>
              <h2 className="text-2xl font-semibold text-slate-950">Case detail · {state?.case?.case_type.replaceAll("_", " ")}</h2>
              <p className="mt-1 text-sm text-slate-600">Manual tracking layer for refunds and exchanges. No execution is performed here.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <RefundExchangeStatusBadge status={state?.case?.status} />
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" type="button" onClick={archiveCase}>
                Archive
              </button>
            </div>
          </div>

          <section className="grid gap-4 lg:grid-cols-3">
            <InfoCard
              title="Overview"
              rows={[
                ["Client", state?.client?.display_name || "Unknown"],
                ["Type", state?.case?.case_type],
                ["Priority", state?.case?.priority],
                ["Reason", state?.case?.reason_category],
                ["Currency", state?.case?.currency],
                ["Client Visible", String(state?.case?.client_visible)],
                ["Booking", state?.booking?.booking_reference || "No booking"],
              ]}
            />
            <InfoCard
              title="Status"
              rows={[
                ["Current status", state?.case?.status],
                ["Supplier reference", state?.case?.supplier_reference || "n/a"],
                ["Expected supplier response", state?.case?.expected_supplier_response_at || "n/a"],
                ["Deadline", state?.case?.deadline_at || "n/a"],
              ]}
            />
            <form className="rounded-lg border border-slate-200 bg-white p-5" onSubmit={saveStatus}>
              <h3 className="font-semibold text-slate-950">Status</h3>
              <select className="mt-4 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={status} onChange={(event) => setStatus(event.target.value)}>
                {CASE_STATUSES.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}
              </select>
              <button className="mt-3 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Update status</button>
            </form>
          </section>

          <Panel title="Overview Notes / Core Fields">
            <form className="grid gap-4" onSubmit={saveCase}>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <select className="rounded-md border border-slate-300 px-3 py-2" value={caseForm.case_type} onChange={(event) => updateCaseForm("case_type", event.target.value)}>
                  {CASE_TYPES.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                </select>
                <select className="rounded-md border border-slate-300 px-3 py-2" value={caseForm.priority} onChange={(event) => updateCaseForm("priority", event.target.value)}>
                  {CASE_PRIORITIES.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
                <select className="rounded-md border border-slate-300 px-3 py-2" value={caseForm.reason_category} onChange={(event) => updateCaseForm("reason_category", event.target.value)}>
                  {CASE_REASONS.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                </select>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <input className="rounded-md border border-slate-300 px-3 py-2" value={caseForm.supplier_reference} onChange={(event) => updateCaseForm("supplier_reference", event.target.value)} placeholder="Supplier reference" />
                <input type="datetime-local" className="rounded-md border border-slate-300 px-3 py-2" value={caseForm.expected_supplier_response_at} onChange={(event) => updateCaseForm("expected_supplier_response_at", event.target.value)} />
                <input type="datetime-local" className="rounded-md border border-slate-300 px-3 py-2" value={caseForm.deadline_at} onChange={(event) => updateCaseForm("deadline_at", event.target.value)} />
                <label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={caseForm.client_visible} onChange={(event) => updateCaseForm("client_visible", event.target.checked)} /> Client-visible</label>
              </div>
              <label className="text-sm font-medium text-slate-700">
                Client reason
                <textarea className="mt-1 min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={caseForm.client_reason_text} onChange={(event) => updateCaseForm("client_reason_text", event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Internal summary
                <textarea className="mt-1 min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={caseForm.internal_summary} onChange={(event) => updateCaseForm("internal_summary", event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Client-visible summary
                <textarea className="mt-1 min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={caseForm.client_visible_summary} onChange={(event) => updateCaseForm("client_visible_summary", event.target.value)} />
              </label>
              <button className="justify-self-start rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Save changes</button>
            </form>
          </Panel>

          <Panel title="Financial Estimates / Outcome">
            <dl className="mt-4 grid gap-2 text-sm">
              {amountValues.map(([label, value]) => <div className="rounded-md bg-slate-50 p-2" key={label}><dt className="text-slate-500">{label}</dt><dd className="font-medium text-slate-900">{value ?? 0} {state?.case?.currency}</dd></div>)}
            </dl>
            <form className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3" onSubmit={saveCase}>
              {[
                ["estimated_refund_amount", "Estimated Refund"],
                ["estimated_penalty_amount", "Estimated Penalty"],
                ["estimated_exchange_difference_amount", "Estimated Exchange"],
                ["estimated_agency_fee_amount", "Estimated Agency Fee"],
                ["estimated_total_due_from_client", "Estimated Due From Client"],
                ["estimated_total_due_to_client", "Estimated Due To Client"],
                ["final_refund_amount", "Final Refund"],
                ["final_penalty_amount", "Final Penalty"],
                ["final_exchange_difference_amount", "Final Exchange"],
                ["final_agency_fee_amount", "Final Agency Fee"],
                ["final_total_due_from_client", "Final Due From Client"],
                ["final_total_due_to_client", "Final Due To Client"],
              ].map(([name, label]) => (
                <label className="text-sm text-slate-700" key={name}>
                  {label}
                  <input type="number" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={caseForm[name]} onChange={(event) => updateCaseForm(name, event.target.value)} />
                </label>
              ))}
              <label className="text-sm text-slate-700 md:col-span-2">
                Currency
                <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={caseForm.currency} onChange={(event) => updateCaseForm("currency", event.target.value)} />
              </label>
              <button className="justify-self-start rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Save financial data</button>
            </form>
          </Panel>

          <section className="grid gap-4 md:grid-cols-2">
            <Panel title="Linked Items">
              <form className="grid gap-3" onSubmit={addItem}>
                <div className="grid gap-3 md:grid-cols-2">
                  <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={itemForm.item_type} onChange={(event) => updateItemForm("item_type", event.target.value)}>
                    {ITEM_TYPES.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                  </select>
                  <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={itemForm.status} onChange={(event) => updateItemForm("status", event.target.value)}>
                    {ITEM_STATUSES.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                  </select>
                </div>
                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Reference ID (ticket/emd/invoice/payment/segment/passenger)" value={itemForm.ref_id} onChange={(event) => updateItemForm("ref_id", event.target.value)} />
                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Description" value={itemForm.description} onChange={(event) => updateItemForm("description", event.target.value)} />
                <div className="grid gap-3 md:grid-cols-3">
                  <input type="number" className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Estimated amount" value={itemForm.estimated_amount} onChange={(event) => updateItemForm("estimated_amount", event.target.value)} />
                  <input type="number" className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Final amount" value={itemForm.final_amount} onChange={(event) => updateItemForm("final_amount", event.target.value)} />
                  <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={itemForm.currency} onChange={(event) => updateItemForm("currency", event.target.value)} />
                </div>
                <textarea rows="2" className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Internal notes" value={itemForm.internal_notes} onChange={(event) => updateItemForm("internal_notes", event.target.value)} />
                <textarea rows="2" className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Client-visible notes" value={itemForm.client_visible_notes} onChange={(event) => updateItemForm("client_visible_notes", event.target.value)} />
                <button className="justify-self-start rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add item</button>
              </form>
              <Rows title="items" items={state?.items} empty="No items" render={(item) => `${item.item_type.replaceAll("_", " ")} · ${item.description} · ${item.status} · ${item.estimated_amount} ${item.currency}`} />
            </Panel>

            <Panel title="Financial Lines">
              <form className="grid gap-3" onSubmit={addFinancialLine}>
                <div className="grid gap-3 md:grid-cols-2">
                  <select className="rounded-md border border-slate-300 px-3 py-2" value={lineForm.line_type} onChange={(event) => updateLineForm("line_type", event.target.value)}>
                    {FINANCIAL_LINE_TYPES.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                  </select>
                  <select className="rounded-md border border-slate-300 px-3 py-2" value={lineForm.direction} onChange={(event) => updateLineForm("direction", event.target.value)}>
                    {FINANCIAL_DIRECTIONS.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                  </select>
                </div>
                <input className="rounded-md border border-slate-300 px-3 py-2" placeholder="Description" value={lineForm.description} onChange={(event) => updateLineForm("description", event.target.value)} />
                <div className="grid gap-3 md:grid-cols-3">
                  <input type="number" className="rounded-md border border-slate-300 px-3 py-2" value={lineForm.amount} onChange={(event) => updateLineForm("amount", event.target.value)} />
                  <input className="rounded-md border border-slate-300 px-3 py-2" value={lineForm.currency} onChange={(event) => updateLineForm("currency", event.target.value)} />
                  <label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={lineForm.client_visible} onChange={(event) => updateLineForm("client_visible", event.target.checked)} /> Client-visible</label>
                </div>
                <label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={lineForm.supplier_pass_through} onChange={(event) => updateLineForm("supplier_pass_through", event.target.checked)} /> Supplier pass-through</label>
                <textarea rows="2" className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Internal notes" value={lineForm.internal_notes} onChange={(event) => updateLineForm("internal_notes", event.target.value)} />
                <button className="justify-self-start rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add line</button>
              </form>
              <Rows title="lines" items={state?.financial_lines} empty="No financial lines" render={(line) => `${line.line_type.replaceAll("_", " ")} · ${line.amount} ${line.currency} · ${line.direction}`} />
            </Panel>
          </section>

          <Panel title="Messages">
            <form className="grid gap-3" onSubmit={sendMessage}>
              <div className="grid gap-3 md:grid-cols-[120px_1fr]">
                <select className="rounded-md border border-slate-300 px-3 py-2" value={messageVisibility} onChange={(event) => setMessageVisibility(event.target.value)}>
                  <option value="internal">Internal</option>
                  <option value="client_visible">Client visible</option>
                </select>
                <input className="rounded-md border border-slate-300 px-3 py-2" value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Add message" />
              </div>
              <button className="justify-self-start rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Post message</button>
            </form>
            <Rows title="messages" items={state?.messages} empty="No messages" render={(item) => `${item.sender_type} · ${item.visibility} · ${item.message_text}`} />
          </Panel>

          <Panel title="Timeline">
            <Rows title="timeline" items={state?.timeline} empty="No timeline events" render={(item) => `${item.title}${item.summary ? ` · ${item.summary}` : ""}`} />
          </Panel>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Panel({ title, children }) {
  return (
    <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      {children}
    </section>
  )
}

function InfoCard({ title, rows }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      <dl className="mt-4 space-y-3 text-sm">
        {rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value || "n/a"}</dd></div>)}
      </dl>
    </section>
  )
}

function Rows({ title, items, empty, render }) {
  if (!items?.length) return <EmptyState title={empty} body={`No ${title} yet.`} />
  return <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>)}</div>
}
