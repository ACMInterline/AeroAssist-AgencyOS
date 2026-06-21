import { useState } from "react"

const emptyPassenger = {
  first_name: "",
  middle_name: "",
  last_name: "",
  display_name: "",
  date_of_birth: "",
  passenger_type: "ADT",
  gender: "",
  nationality: "SK",
  residence_country: "SK",
  primary_language: "en",
  passport_number: "",
  passport_country: "",
  passport_expiry: "",
  travel_document_notes: "",
  known_assistance_needs: "",
  medical_notes_internal: "",
  meal_preferences: "",
  loyalty_numbers: [],
}

export default function PassengerForm({ initial = {}, onSubmit, submitLabel = "Save passenger" }) {
  const [form, setForm] = useState({ ...emptyPassenger, ...initial })

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
          First name
          <input required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.first_name} onChange={(event) => setField("first_name", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Last name
          <input required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.last_name} onChange={(event) => setField("last_name", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Middle name
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.middle_name || ""} onChange={(event) => setField("middle_name", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Display name
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.display_name || ""} onChange={(event) => setField("display_name", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Date of birth
          <input required type="date" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.date_of_birth} onChange={(event) => setField("date_of_birth", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          PTC
          <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.passenger_type} onChange={(event) => setField("passenger_type", event.target.value)}>
            {["ADT", "CHD", "INF", "YTH", "SRC", "STU", "UMNR", "INS", "other"].map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Nationality
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.nationality || ""} onChange={(event) => setField("nationality", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Residence country
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.residence_country || ""} onChange={(event) => setField("residence_country", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Passport number
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.passport_number || ""} onChange={(event) => setField("passport_number", event.target.value)} />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Passport expiry
          <input type="date" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.passport_expiry || ""} onChange={(event) => setField("passport_expiry", event.target.value)} />
        </label>
      </div>
      <label className="text-sm font-medium text-slate-700">
        Assistance needs
        <textarea className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" rows="2" value={form.known_assistance_needs || ""} onChange={(event) => setField("known_assistance_needs", event.target.value)} />
      </label>
      <label className="text-sm font-medium text-slate-700">
        Internal medical notes
        <textarea className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" rows="2" value={form.medical_notes_internal || ""} onChange={(event) => setField("medical_notes_internal", event.target.value)} />
      </label>
      <label className="text-sm font-medium text-slate-700">
        Meal preferences
        <textarea className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" rows="2" value={form.meal_preferences || ""} onChange={(event) => setField("meal_preferences", event.target.value)} />
      </label>
      <button className="justify-self-start rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">
        {submitLabel}
      </button>
    </form>
  )
}
