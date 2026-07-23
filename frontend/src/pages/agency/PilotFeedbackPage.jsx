import { useEffect, useMemo, useState } from "react"
import BookOpen from "lucide-react/dist/esm/icons/book-open.js"
import MessageSquarePlus from "lucide-react/dist/esm/icons/message-square-plus.js"
import EmptyState from "../../components/EmptyState"
import FormSection from "../../components/FormSection"
import OperationalAlert from "../../components/OperationalAlert"
import PageHeader from "../../components/PageHeader"
import PrimaryButton from "../../components/PrimaryButton"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"
import { productLabel } from "../../lib/productLanguage"

const query = new URLSearchParams(window.location.search)
const initialArea = query.get("affected_area") || "operations"

const quickGuides = {
  onboarding: ["Complete each setup step", "Create a synthetic demo workspace", "Review the summary before completing onboarding"],
  operations: ["Review urgent and overdue work", "Open the linked operational record", "Use guarded actions and leave a clear audit reason"],
  requests: ["Confirm client and passengers", "Capture route, dates, and service needs", "Resolve critical gaps before downstream handoff"],
  offers: ["Start from a resolved trip context", "Separate internal notes from client wording", "Record the accepted option before booking handoff"],
  booking: ["Use the accepted offer snapshot", "Resolve readiness blockers", "Record metadata only; no live supplier action occurs"],
  passengers: ["Search before creating a profile", "Keep operational identity and requirements current", "Avoid unnecessary sensitive notes"],
  documents: ["Track required, received, and verified states", "Review deadlines and travel-critical gaps", "Do not treat metadata as proof of external delivery"],
  tasks: ["Start with urgent, overdue, and unassigned work", "Keep ownership and blockers current", "Complete work with an auditable reason"],
}

const areaHrefs = {
  onboarding: "/agency/onboarding",
  operations: "/agency",
  requests: "/agency/requests",
  offers: "/agency/offers",
  booking: "/agency/booking-workspaces",
  passengers: "/agency/passengers",
  documents: "/agency/document-workspaces",
  tasks: "/agency/work-queue",
}

const emptyForm = {
  category: "usability",
  title: "",
  description: "",
  affected_area: initialArea,
  urgency: "normal",
  related_record_type: query.get("related_record_type") || "",
  related_record_id: query.get("related_record_id") || "",
}

export default function PilotFeedbackPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load(suppliedContext) {
    const context = suppliedContext || await loadCurrentAgency()
    if (!context.agency) return setState({ ...context, feedback: { items: [], filters: {}, documentation: [] } })
    const feedback = await apiGet(`/api/agencies/${context.agency.id}/pilot-feedback`)
    setState({ ...context, feedback })
    setError("")
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const guideItems = quickGuides[form.affected_area] || quickGuides.operations
  const canSubmit = state?.feedback?.permissions?.can_submit !== false
  const relevantDocs = useMemo(() => {
    const documents = state?.feedback?.documentation || []
    const preferred = {
      onboarding: ["onboarding", "first_day", "demo_workspace"],
      operations: ["consultant", "daily_operations", "incidents"],
      requests: ["consultant", "daily_operations"],
      offers: ["consultant", "daily_operations"],
      booking: ["consultant", "daily_operations"],
      passengers: ["consultant", "daily_operations"],
      documents: ["consultant", "daily_operations"],
      tasks: ["consultant", "daily_operations"],
    }[form.affected_area] || ["overview", "feedback"]
    return documents.filter((item) => preferred.includes(item.key))
  }, [form.affected_area, state])

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError("")
    setMessage("")
    try {
      const payload = {
        ...form,
        related_record_type: form.related_record_type || null,
        related_record_id: form.related_record_id || null,
      }
      await apiPost(`/api/agencies/${state.agency.id}/pilot-feedback`, payload)
      setForm({ ...emptyForm, affected_area: form.affected_area })
      setMessage("Feedback submitted. Your agency can track its review status here.")
      await load(state)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <main className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Operations", href: "/agency" }, { label: "Pilot help & feedback" }]}
            eyebrow="Commercial Pilot"
            title="Pilot help & feedback"
            description="Use the concise operating guides, report what affected your work, and follow the review status. This does not contact an external support system."
          />

          {error ? <OperationalAlert title="Feedback could not be saved" tone="error">{error}</OperationalAlert> : null}
          {message ? <OperationalAlert title="Feedback recorded" tone="success">{message}</OperationalAlert> : null}

          <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]" id="pilot-guides">
            <div className="border-y border-slate-200 bg-white px-5 py-5">
              <div className="flex items-start gap-3">
                <BookOpen aria-hidden="true" className="mt-0.5 h-5 w-5 text-blue-700" />
                <div>
                  <h2 className="text-base font-semibold text-slate-950">{productLabel(form.affected_area)} pilot guide</h2>
                  <p className="mt-1 text-sm text-slate-600">A short operating prompt for the current workspace.</p>
                </div>
              </div>
              <ol className="mt-4 grid gap-3">
                {guideItems.map((item, index) => <li className="flex gap-3 text-sm text-slate-700" key={item}><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-50 text-xs font-semibold text-blue-700">{index + 1}</span><span className="pt-0.5">{item}</span></li>)}
              </ol>
              <a className="mt-5 inline-flex text-sm font-semibold text-blue-700 hover:underline" href={areaHrefs[form.affected_area] || "/agency"}>Return to {productLabel(form.affected_area)}</a>
            </div>
            <div className="border-y border-slate-200 bg-slate-50 px-5 py-5">
              <h2 className="text-sm font-semibold text-slate-950">Related pilot documents</h2>
              <div className="mt-3 space-y-3">
                {relevantDocs.map((item) => <div key={item.key}><p className="text-sm font-medium text-slate-800">{item.label}</p><p className="mt-1 break-all text-xs text-slate-500">{item.path}</p></div>)}
              </div>
              <p className="mt-4 text-xs leading-5 text-slate-500">Repository documentation is the controlled source. Follow your deployment’s approved document-access procedure.</p>
            </div>
          </section>

          {canSubmit ? <form className="space-y-6 border-y border-slate-200 bg-white px-5 py-6" id="submit-feedback" onSubmit={submit}>
            <FormSection title="Describe the feedback" description="Do not include credentials, payment details, passport data, medical detail, or raw logs.">
              <div className="grid gap-4 md:grid-cols-2">
                <Select label="Category" value={form.category} options={state?.feedback?.filters?.categories || []} onChange={(value) => setForm({ ...form, category: value })} />
                <Select label="Affected area" value={form.affected_area} options={state?.feedback?.filters?.affected_areas || []} onChange={(value) => setForm({ ...form, affected_area: value })} />
                <Select label="Urgency" value={form.urgency} options={state?.feedback?.filters?.urgencies || []} onChange={(value) => setForm({ ...form, urgency: value })} />
                <label className="grid gap-1 text-sm font-medium text-slate-700">Title<input className="field" maxLength="160" required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="What needs attention?" /></label>
              </div>
              <label className="mt-4 grid gap-1 text-sm font-medium text-slate-700">Description<textarea className="field min-h-32" maxLength="4000" required value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="What happened, what did you expect, and how did it affect the work?" /></label>
            </FormSection>

            <FormSection title="Optional related record" description="Both fields are required when linking a record. The backend confirms that the record exists in this agency before saving the feedback.">
              <div className="grid gap-4 md:grid-cols-2">
                <Select label="Record type" value={form.related_record_type} options={state?.feedback?.filters?.related_record_types || []} allowEmpty onChange={(value) => setForm({ ...form, related_record_type: value })} />
                <label className="grid gap-1 text-sm font-medium text-slate-700">Record ID<input className="field" value={form.related_record_id} onChange={(event) => setForm({ ...form, related_record_id: event.target.value })} placeholder="Canonical record ID" /></label>
              </div>
              {Boolean(form.related_record_type || form.related_record_id) ? <p className="mt-3 text-xs font-medium text-amber-800">The link will be rejected if the record is missing, belongs to another agency, or does not match the selected type.</p> : null}
            </FormSection>

            <PrimaryButton disabled={busy} icon={MessageSquarePlus} type="submit">{busy ? "Submitting..." : "Submit feedback"}</PrimaryButton>
          </form> : <OperationalAlert title="Pilot feedback is read-only for your role" tone="info">You can review your agency’s submissions and guides. Ask an Agency Owner, Administrator, Agent, or Accountant to submit new feedback.</OperationalAlert>}

          <section>
            <h2 className="text-base font-semibold text-slate-950">Your agency’s feedback</h2>
            <p className="mt-1 text-sm text-slate-600">Newest submissions appear first. Review notes are read-only for Agency users.</p>
            {(state?.feedback?.items || []).length ? (
              <div className="mt-4 divide-y divide-slate-200 border-y border-slate-200 bg-white">
                {state.feedback.items.map((item) => <article className="px-4 py-4" key={item.id}><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase text-slate-500">{productLabel(item.category)} · {productLabel(item.affected_area)}</p><h3 className="mt-1 font-semibold text-slate-950">{item.title}</h3></div><StatusBadge status={item.status} /></div><p className="mt-2 text-sm text-slate-600">{item.description}</p>{item.related_record_label ? <p className="mt-2 text-xs font-medium text-slate-500">Related: {item.related_record_label}</p> : null}{item.review_notes ? <p className="mt-3 border-l-2 border-blue-200 pl-3 text-sm text-slate-600">Platform review: {item.review_notes}</p> : null}<p className="mt-3 text-xs text-slate-500">Submitted {new Date(item.submitted_at).toLocaleString()}</p></article>)}
              </div>
            ) : <div className="mt-4"><EmptyState title="No pilot feedback yet" body="Use the form above when a workflow, screen, data point, or guide needs attention." /></div>}
          </section>
        </main>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Select({ allowEmpty = false, label, onChange, options, value }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="field" required={!allowEmpty} value={value} onChange={(event) => onChange(event.target.value)}>{allowEmpty ? <option value="">No related record</option> : null}{options.map((item) => <option value={item} key={item}>{productLabel(item)}</option>)}</select></label>
}
