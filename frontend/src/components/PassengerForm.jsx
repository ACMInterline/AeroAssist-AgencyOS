import { useState } from "react"
import CountrySelect from "./reference/CountrySelect"
import PtcSelect from "./reference/PtcSelect"
import ReferenceSelect from "./reference/ReferenceSelect"
import { passengerTypeCompatibilityCode } from "../lib/referenceData"

const emptyPassenger = {
  first_name: "",
  middle_name: "",
  last_name: "",
  display_name: "",
  date_of_birth: "",
  passenger_type: "ADT",
  passenger_type_code_id: "",
  passenger_type_code: "ADT",
  passenger_type_label: "Adult",
  gender: "",
  nationality: "",
  nationality_reference_id: "",
  nationality_label: "",
  residence_country: "",
  residence_country_reference_id: "",
  residence_country_label: "",
  primary_language: "en",
  primary_language_reference_id: "",
  primary_language_label: "English",
  passport_number: "",
  passport_country: "",
  passport_country_reference_id: "",
  passport_country_label: "",
  travel_document_type_id: "",
  travel_document_type_code: "",
  travel_document_type_label: "",
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
        <PtcSelect
          required
          value={form.passenger_type_code_id || ""}
          selectedCode={form.passenger_type_code || form.passenger_type || ""}
          selectedLabel={form.passenger_type_label || ""}
          onChange={(option) => setForm((current) => ({
            ...current,
            passenger_type_code_id: option?.id || "",
            passenger_type_code: option?.code || "",
            passenger_type_label: option?.label || "",
            passenger_type: passengerTypeCompatibilityCode(option),
          }))}
        />
        <CountrySelect
          label="Nationality"
          value={form.nationality_reference_id || ""}
          selectedCode={form.nationality || ""}
          selectedLabel={form.nationality_label || ""}
          onChange={(option) => setForm((current) => ({
            ...current,
            nationality_reference_id: option?.id || "",
            nationality: option?.code || "",
            nationality_label: option?.label || "",
          }))}
        />
        <CountrySelect
          label="Residence country"
          value={form.residence_country_reference_id || ""}
          selectedCode={form.residence_country || ""}
          selectedLabel={form.residence_country_label || ""}
          onChange={(option) => setForm((current) => ({
            ...current,
            residence_country_reference_id: option?.id || "",
            residence_country: option?.code || "",
            residence_country_label: option?.label || "",
          }))}
        />
        <ReferenceSelect
          domain="languages"
          label="Primary language"
          value={form.primary_language_reference_id || ""}
          selectedCode={form.primary_language || ""}
          selectedLabel={form.primary_language_label || ""}
          onChange={(option) => setForm((current) => ({
            ...current,
            primary_language_reference_id: option?.id || "",
            primary_language: option?.code || "",
            primary_language_label: option?.label || "",
          }))}
        />
        <label className="text-sm font-medium text-slate-700">
          Passport number
          <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.passport_number || ""} onChange={(event) => setField("passport_number", event.target.value)} />
        </label>
        <CountrySelect
          label="Passport issuing country"
          value={form.passport_country_reference_id || ""}
          selectedCode={form.passport_country || ""}
          selectedLabel={form.passport_country_label || ""}
          onChange={(option) => setForm((current) => ({
            ...current,
            passport_country_reference_id: option?.id || "",
            passport_country: option?.code || "",
            passport_country_label: option?.label || "",
          }))}
        />
        <ReferenceSelect
          domain="document_types"
          label="Travel document type"
          value={form.travel_document_type_id || ""}
          selectedCode={form.travel_document_type_code || ""}
          selectedLabel={form.travel_document_type_label || ""}
          onChange={(option) => setForm((current) => ({
            ...current,
            travel_document_type_id: option?.id || "",
            travel_document_type_code: option?.code || "",
            travel_document_type_label: option?.label || "",
          }))}
        />
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
