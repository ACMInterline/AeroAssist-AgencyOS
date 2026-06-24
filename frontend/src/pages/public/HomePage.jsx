import { useState } from "react"
import PublicLayout from "../../layouts/PublicLayout"
import { apiPost } from "../../lib/api"

const isProduction = import.meta.env.PROD || import.meta.env.VITE_APP_ENV === "production"

export default function HomePage() {
  return (
    <PublicLayout>
      <section className="grid gap-6 md:grid-cols-[1.4fr_1fr] md:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Phase 1 Foundation</p>
          <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-normal text-slate-950 md:text-5xl">
            AeroAssist AgencyOS
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
            Multi-tenant operating platform foundation for micro and small travel agencies.
            This build establishes platform identity, agency workspace setup, roles, reference
            data, and tenant-aware API scaffolding.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" href="/login">
              {isProduction ? "Sign in" : "Open demo login"}
            </a>
            <a className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-800" href="/platform">
              View platform foundation
            </a>
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-base font-semibold text-slate-950">Implemented layers</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>AeroAssist Global / Platform Owner foundation</li>
            <li>Agency Workspace identity and settings foundation</li>
            <li>Global reference data seed layer</li>
            <li>Audit event scaffolding</li>
          </ul>
        </div>
      </section>
      <PublicRequestForm />
    </PublicLayout>
  )
}

function PublicRequestForm() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    origin: "",
    destination: "",
    departure_date: "",
    return_date: "",
    passenger_count: 1,
    service: "booking_or_planning",
    details: "",
    privacy_policy_accepted: false,
  })
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState("")

  async function submit(event) {
    event.preventDefault()
    setError("")
    try {
      const selected = form.service ? [form.service.replaceAll("_", " ")] : []
      const result = await apiPost("/api/public/request-intakes", {
        contact: {
          name: form.name,
          email: form.email || undefined,
          phone: form.phone || undefined,
          privacy_policy_accepted: form.privacy_policy_accepted,
          data_processing_consent: form.privacy_policy_accepted,
        },
        travel: {
          origin: form.origin || undefined,
          destination: form.destination || undefined,
          departure_date: form.departure_date || undefined,
          return_date: form.return_date || undefined,
          passenger_count: Number(form.passenger_count) || 1,
          itinerary_notes: form.details || undefined,
        },
        services: {
          selected_service_categories: selected,
          mobility_assistance: form.service === "mobility_assistance",
          medical_travel: form.service === "medical_travel",
          pet_travel: form.service === "pet_travel",
          child_or_unaccompanied_minor: form.service === "child_or_unaccompanied_minor",
          special_baggage: form.service === "special_baggage",
          documents_or_visa: form.service === "documents_or_visa",
          disruption_or_claims: form.service === "disruption_or_claims",
          booking_or_planning: form.service === "booking_or_planning",
          other: form.service === "other",
          other_details: form.service === "other" ? form.details : undefined,
        },
        request_details: form.details || undefined,
      })
      setSuccess(result.intake)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="mt-10 rounded-lg border border-slate-200 bg-white p-6">
      <div className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Request assistance</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-950">Tell us what you need</h2>
        <p className="mt-2 text-sm text-slate-600">We received your request as an intake first. Our team reviews it before creating any operational case.</p>
      </div>
      {success ? (
        <div className="mt-5 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          We received your request. Our team will review it. Reference: <span className="font-semibold">{success.reference_code}</span>
        </div>
      ) : (
        <form className="mt-5 grid gap-4 md:grid-cols-2" onSubmit={submit}>
          <Field label="Name" value={form.name} onChange={(value) => setForm({ ...form, name: value })} required />
          <Field label="Email" type="email" value={form.email} onChange={(value) => setForm({ ...form, email: value })} />
          <Field label="Phone" value={form.phone} onChange={(value) => setForm({ ...form, phone: value })} />
          <Field label="Origin" value={form.origin} onChange={(value) => setForm({ ...form, origin: value })} />
          <Field label="Destination" value={form.destination} onChange={(value) => setForm({ ...form, destination: value })} />
          <Field label="Departure date" type="date" value={form.departure_date} onChange={(value) => setForm({ ...form, departure_date: value })} />
          <Field label="Return date" type="date" value={form.return_date} onChange={(value) => setForm({ ...form, return_date: value })} />
          <Field label="Passengers" type="number" value={form.passenger_count} onChange={(value) => setForm({ ...form, passenger_count: value })} />
          <label className="block text-sm font-medium text-slate-700">Service type<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.service} onChange={(event) => setForm({ ...form, service: event.target.value })}>{["booking_or_planning", "mobility_assistance", "medical_travel", "pet_travel", "child_or_unaccompanied_minor", "special_baggage", "documents_or_visa", "disruption_or_claims", "other"].map((item) => <option value={item} key={item}>{item.replaceAll("_", " ")}</option>)}</select></label>
          <label className="block text-sm font-medium text-slate-700 md:col-span-2">Travel/request details<textarea className="mt-2 min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.details} required onChange={(event) => setForm({ ...form, details: event.target.value })} /></label>
          <label className="flex gap-2 text-sm text-slate-700 md:col-span-2"><input type="checkbox" checked={form.privacy_policy_accepted} onChange={(event) => setForm({ ...form, privacy_policy_accepted: event.target.checked })} required /> I consent to AeroAssist reviewing this request and contacting me about it.</label>
          {error ? <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800 md:col-span-2">{error}</p> : null}
          <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white md:w-fit" type="submit">Submit request</button>
        </form>
      )}
    </section>
  )
}

function Field({ label, value, onChange, type = "text", required = false }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value} required={required} onChange={(event) => onChange(event.target.value)} /></label>
}
