import { useState } from "react"

const emptyClient = {
  client_type: "individual",
  display_name: "",
  legal_name: "",
  primary_email: "",
  primary_phone: "",
  country: "SK",
  city: "",
  preferred_language: "en",
  default_currency: "EUR",
  portal_status: "no_portal_access",
  marketing_consent: false,
  data_processing_consent: false,
  internal_notes: "",
  client_visible_notes: "",
}

export default function ClientForm({ initial = {}, onSubmit, submitLabel = "Save client" }) {
  const [form, setForm] = useState({ ...emptyClient, ...initial })

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  function handleSubmit(event) {
    event.preventDefault()
    onSubmit(form)
  }

  return (
    <form className="grid gap-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={handleSubmit}>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-medium text-slate-700">
          Client type
          <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.client_type} onChange={(event) => setField("client_type", event.target.value)}>
            <option value="individual">Individual</option>
            <option value="family_household">Family / household</option>
            <option value="organization">Organization</option>
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Portal status
          <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.portal_status} onChange={(event) => setField("portal_status", event.target.value)}>
            <option value="no_portal_access">No portal access</option>
            <option value="invited">Invited</option>
            <option value="email_unverified">Email unverified</option>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
            <option value="archived">Archived</option>
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Display name
          <input required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.display_name} onChange={(event) => setField("display_name", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Legal name
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.legal_name || ""} onChange={(event) => setField("legal_name", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Primary email
          <input required type="email" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.primary_email} onChange={(event) => setField("primary_email", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Primary phone
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.primary_phone || ""} onChange={(event) => setField("primary_phone", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          City
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.city || ""} onChange={(event) => setField("city", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Country
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.country || ""} onChange={(event) => setField("country", event.target.value)} />
        </label>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" checked={form.marketing_consent} onChange={(event) => setField("marketing_consent", event.target.checked)} />
          Marketing consent
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" checked={form.data_processing_consent} onChange={(event) => setField("data_processing_consent", event.target.checked)} />
          Data processing consent
        </label>
      </div>
      <label className="text-sm font-medium text-slate-700">
        Internal notes
        <textarea className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" rows="3" value={form.internal_notes || ""} onChange={(event) => setField("internal_notes", event.target.value)} />
      </label>
      <label className="text-sm font-medium text-slate-700">
        Client-visible notes
        <textarea className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" rows="2" value={form.client_visible_notes || ""} onChange={(event) => setField("client_visible_notes", event.target.value)} />
      </label>
      <button className="justify-self-start rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">
        {submitLabel}
      </button>
    </form>
  )
}
