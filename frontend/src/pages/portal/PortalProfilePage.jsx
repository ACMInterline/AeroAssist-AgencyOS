import { useEffect, useState } from "react"
import Save from "lucide-react/dist/esm/icons/save.js"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalFacts, PortalPageHeader, PortalSection, formatDate, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet, apiPatch } from "../../lib/api"

export default function PortalProfilePage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({})
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [saving, setSaving] = useState(false)

  async function load() {
    const [me, profile] = await Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/profile")])
    const passenger = profile.subject_type === "passenger"
    const subject = passenger ? profile.passenger : profile.client
    setState({ me, profile, subject, passenger })
    setForm(buildForm(subject || {}, passenger))
  }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  function change(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function save(event) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setNotice("")
    try {
      await apiPatch("/api/portal/profile", profilePayload(form, state.passenger))
      setNotice("Travel profile updated.")
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const subject = state?.subject || {}
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <form className="space-y-8" onSubmit={save}>
          <PortalPageHeader eyebrow={state?.passenger ? "Passenger profile" : "Client profile"} title="Travel Profile" description="Contact, travel preference, and assistance details held by your agency." status={state?.profile?.portal_account?.portal_status} actions={<button className="primary-button" disabled={saving} type="submit"><Save aria-hidden="true" className="h-4 w-4" />{saving ? "Saving..." : "Save changes"}</button>} />
          {notice ? <p className="border-y border-emerald-200 bg-emerald-50 px-3 py-3 text-sm text-emerald-800" role="status">{notice}</p> : null}
          {error ? <p className="border-y border-rose-200 bg-rose-50 px-3 py-3 text-sm text-rose-800" role="alert">{error}</p> : null}

          <PortalSection title="Identity">
            <PortalFacts columns={3} rows={state?.passenger ? [["Name", subject.display_name], ["Date of birth", formatDate(subject.date_of_birth)], ["Passenger type", titleCase(subject.passenger_type)], ["Nationality", subject.nationality], ["Status", titleCase(subject.status)]] : [["Name", subject.display_name], ["Legal name", subject.legal_name], ["Email", subject.primary_email], ["Status", titleCase(subject.status)]]} />
          </PortalSection>

          {state?.passenger ? <PassengerFields form={form} change={change} /> : <ClientFields form={form} change={change} />}
        </form>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function ClientFields({ form, change }) {
  return <>
    <PortalSection title="Contact details">
      <FieldGrid>
        <Field label="Display name" value={form.display_name} onChange={(value) => change("display_name", value)} />
        <Field label="Legal name" value={form.legal_name} onChange={(value) => change("legal_name", value)} />
        <Field label="Phone" value={form.primary_phone} onChange={(value) => change("primary_phone", value)} />
        <Field label="Country" value={form.country} onChange={(value) => change("country", value)} />
        <Field label="City" value={form.city} onChange={(value) => change("city", value)} />
        <Field label="Postal code" value={form.postal_code} onChange={(value) => change("postal_code", value)} />
        <Field label="Address line 1" value={form.address_line_1} onChange={(value) => change("address_line_1", value)} />
        <Field label="Address line 2" value={form.address_line_2} onChange={(value) => change("address_line_2", value)} />
        <Field label="Preferred language" value={form.preferred_language} onChange={(value) => change("preferred_language", value)} />
        <Field label="Default currency" maxLength={3} value={form.default_currency} onChange={(value) => change("default_currency", value.toUpperCase())} />
      </FieldGrid>
    </PortalSection>
    <PortalSection title="Consent preferences">
      <div className="flex flex-wrap gap-6">
        <Check label="Marketing communications" checked={form.marketing_consent} onChange={(value) => change("marketing_consent", value)} />
        <Check label="Data processing consent" checked={form.data_processing_consent} onChange={(value) => change("data_processing_consent", value)} />
      </div>
    </PortalSection>
  </>
}

function PassengerFields({ form, change }) {
  return <>
    <PortalSection title="Travel identity">
      <FieldGrid>
        <Field label="Middle name" value={form.middle_name} onChange={(value) => change("middle_name", value)} />
        <Field label="Display name" value={form.display_name} onChange={(value) => change("display_name", value)} />
        <Field label="Gender" value={form.gender} onChange={(value) => change("gender", value)} />
        <Field label="Nationality" value={form.nationality} onChange={(value) => change("nationality", value)} />
        <Field label="Country of residence" value={form.residence_country} onChange={(value) => change("residence_country", value)} />
        <Field label="Primary language" value={form.primary_language} onChange={(value) => change("primary_language", value)} />
        <Field label="Passport country" value={form.passport_country} onChange={(value) => change("passport_country", value)} />
        <Field label="Passport expiry" type="date" value={form.passport_expiry} onChange={(value) => change("passport_expiry", value)} />
      </FieldGrid>
    </PortalSection>
    <PortalSection title="Preferences and assistance">
      <FieldGrid>
        <Area label="Known assistance needs" value={form.known_assistance_needs} onChange={(value) => change("known_assistance_needs", value)} />
        <Area label="Meal preferences" value={form.meal_preferences} onChange={(value) => change("meal_preferences", value)} />
        <Area label="Seat preferences" value={form.seating_preferences} onChange={(value) => change("seating_preferences", value)} />
        <Area label="Baggage preferences" value={form.baggage_preferences} onChange={(value) => change("baggage_preferences", value)} />
      </FieldGrid>
    </PortalSection>
    <PortalSection title="Emergency contact">
      <FieldGrid>
        <Field label="Name" value={form.emergency_contact_name} onChange={(value) => change("emergency_contact_name", value)} />
        <Field label="Relationship" value={form.emergency_contact_relationship} onChange={(value) => change("emergency_contact_relationship", value)} />
        <Field label="Phone" value={form.emergency_contact_phone} onChange={(value) => change("emergency_contact_phone", value)} />
        <Field label="Email" type="email" value={form.emergency_contact_email} onChange={(value) => change("emergency_contact_email", value)} />
      </FieldGrid>
    </PortalSection>
    <PortalSection title="Loyalty memberships" description="Enter one membership per line as Airline: Number.">
      <Area label="Memberships" value={form.loyalty_numbers} onChange={(value) => change("loyalty_numbers", value)} />
    </PortalSection>
  </>
}

function FieldGrid({ children }) {
  return <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{children}</div>
}

function Field({ label, value, onChange, type = "text", maxLength = 240 }) {
  return <label className="text-sm font-medium text-slate-700">{label}<input className="field mt-2" maxLength={maxLength} type={type} value={value || ""} onChange={(event) => onChange(event.target.value)} /></label>
}

function Area({ label, value, onChange }) {
  return <label className="text-sm font-medium text-slate-700">{label}<textarea className="field mt-2 min-h-24" maxLength={2000} value={value || ""} onChange={(event) => onChange(event.target.value)} /></label>
}

function Check({ label, checked, onChange }) {
  return <label className="flex items-center gap-3 text-sm text-slate-700"><input checked={Boolean(checked)} type="checkbox" onChange={(event) => onChange(event.target.checked)} />{label}</label>
}

function buildForm(subject, passenger) {
  if (!passenger) return { ...subject }
  const contact = subject.emergency_contact || {}
  return {
    ...subject,
    passport_expiry: subject.passport_expiry ? String(subject.passport_expiry).slice(0, 10) : "",
    emergency_contact_name: contact.name || "",
    emergency_contact_relationship: contact.relationship || "",
    emergency_contact_phone: contact.phone || "",
    emergency_contact_email: contact.email || "",
    loyalty_numbers: (subject.loyalty_numbers || []).map((item) => `${item.program || item.airline || ""}: ${item.number || item.membership_number || ""}`.trim()).join("\n"),
  }
}

function profilePayload(form, passenger) {
  if (!passenger) {
    return pick(form, ["display_name", "legal_name", "primary_phone", "country", "city", "address_line_1", "address_line_2", "postal_code", "preferred_language", "default_currency", "marketing_consent", "data_processing_consent"])
  }
  return {
    ...pick(form, ["middle_name", "display_name", "gender", "nationality", "residence_country", "primary_language", "passport_country", "passport_expiry", "known_assistance_needs", "meal_preferences", "seating_preferences", "baggage_preferences"]),
    emergency_contact: {
      name: form.emergency_contact_name || null,
      relationship: form.emergency_contact_relationship || null,
      phone: form.emergency_contact_phone || null,
      email: form.emergency_contact_email || null,
    },
    loyalty_numbers: String(form.loyalty_numbers || "").split("\n").map((line) => line.trim()).filter(Boolean).map((line) => {
      const [program, ...number] = line.split(":")
      return { program: program.trim(), number: number.join(":").trim() }
    }).filter((item) => item.program && item.number),
  }
}

function pick(source, fields) {
  return Object.fromEntries(fields.map((field) => [field, source[field] === "" ? null : source[field]]))
}
