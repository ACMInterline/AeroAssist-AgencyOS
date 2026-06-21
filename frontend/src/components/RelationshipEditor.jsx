import { useState } from "react"

export default function RelationshipEditor({ clients = [], passengers = [], initial = {}, onSubmit }) {
  const [form, setForm] = useState({
    client_id: initial.client_id || clients[0]?.id || "",
    passenger_id: initial.passenger_id || passengers[0]?.id || "",
    relationship_type: initial.relationship_type || "self",
    can_view: initial.can_view ?? true,
    can_edit: initial.can_edit ?? false,
    can_upload_documents: initial.can_upload_documents ?? false,
    can_request_travel: initial.can_request_travel ?? true,
    can_pay: initial.can_pay ?? false,
    can_receive_notifications: initial.can_receive_notifications ?? true,
    consent_status: initial.consent_status || "pending",
    notes: initial.notes || "",
  })

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
          Client
          <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.client_id} onChange={(event) => setField("client_id", event.target.value)}>
            {clients.map((client) => (
              <option key={client.id} value={client.id}>{client.display_name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Passenger
          <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.passenger_id} onChange={(event) => setField("passenger_id", event.target.value)}>
            {passengers.map((passenger) => (
              <option key={passenger.id} value={passenger.id}>{passenger.display_name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Relationship type
          <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.relationship_type} onChange={(event) => setField("relationship_type", event.target.value)}>
            {["self", "spouse", "child", "parent", "guardian", "employee", "assistant", "company_traveler", "other"].map((value) => (
              <option key={value} value={value}>{value.replaceAll("_", " ")}</option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Consent
          <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.consent_status} onChange={(event) => setField("consent_status", event.target.value)}>
            {["pending", "granted", "revoked", "expired", "not_required"].map((value) => (
              <option key={value} value={value}>{value.replaceAll("_", " ")}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {[
          ["can_view", "Can view"],
          ["can_edit", "Can edit"],
          ["can_upload_documents", "Can upload documents"],
          ["can_request_travel", "Can request travel"],
          ["can_pay", "Can pay"],
          ["can_receive_notifications", "Can receive notifications"],
        ].map(([name, label]) => (
          <label className="flex items-center gap-2 text-sm text-slate-700" key={name}>
            <input type="checkbox" checked={form[name]} onChange={(event) => setField(name, event.target.checked)} />
            {label}
          </label>
        ))}
      </div>
      <label className="text-sm font-medium text-slate-700">
        Notes
        <textarea className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" rows="2" value={form.notes || ""} onChange={(event) => setField("notes", event.target.value)} />
      </label>
      <button className="justify-self-start rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">
        Link client and passenger
      </button>
    </form>
  )
}
