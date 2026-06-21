import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import PassengerForm from "../../components/PassengerForm"
import ProtectedRoute from "../../components/ProtectedRoute"
import RelationshipEditor from "../../components/RelationshipEditor"
import StatusBadge from "../../components/StatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function PassengerDetailPage({ passengerId }) {
  const [state, setState] = useState(null)
  const [showEdit, setShowEdit] = useState(false)
  const [showLink, setShowLink] = useState(false)
  const [mergeTarget, setMergeTarget] = useState("")
  const [mergeReason, setMergeReason] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/passengers/${passengerId}`)
    const clients = await apiGet(`/api/agencies/${context.agency.id}/clients`)
    const passengers = await apiGet(`/api/agencies/${context.agency.id}/passengers`)
    setState({ ...context, ...detail, allClients: clients.items, allPassengers: passengers.items })
    const firstMergeTarget = passengers.items.find((passenger) => passenger.id !== passengerId && passenger.status !== "duplicate_merged")
    setMergeTarget(firstMergeTarget?.id || "")
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [passengerId])

  async function savePassenger(payload) {
    const allowed = [
      "first_name",
      "middle_name",
      "last_name",
      "display_name",
      "date_of_birth",
      "passenger_type",
      "gender",
      "nationality",
      "residence_country",
      "primary_language",
      "passport_number",
      "passport_country",
      "passport_expiry",
      "travel_document_notes",
      "known_assistance_needs",
      "medical_notes_internal",
      "meal_preferences",
      "loyalty_numbers",
      "status",
    ]
    const cleanPayload = Object.fromEntries(allowed.map((key) => [key, payload[key]]).filter(([, value]) => value !== undefined && value !== ""))
    await apiPut(`/api/agencies/${state.agency.id}/passengers/${passengerId}`, cleanPayload)
    setShowEdit(false)
    await load()
  }

  async function archiveOrRestore() {
    const action = state.passenger.status === "archived" ? "restore" : "archive"
    await apiPost(`/api/agencies/${state.agency.id}/passengers/${passengerId}/${action}`)
    await load()
  }

  async function linkClient(payload) {
    await apiPost(`/api/agencies/${state.agency.id}/client-passenger-relationships`, payload)
    setShowLink(false)
    await load()
  }

  async function mergePassenger(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/passengers/${passengerId}/merge`, {
      target_passenger_id: mergeTarget,
      reason: mergeReason || "Duplicate passenger record",
      retained_fields_summary: { retained_profile: mergeTarget },
    })
    await load()
  }

  const clientById = Object.fromEntries((state?.clients || []).map((client) => [client.id, client]))
  const mergeOptions = (state?.allPassengers || []).filter((passenger) => passenger.id !== passengerId && passenger.status !== "duplicate_merged")

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/passengers">Back to passengers</a>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">{state?.passenger?.display_name}</h2>
              <p className="mt-1 text-sm text-slate-600">Traveler profile. Access is granted through client/passenger relationships.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge status={state?.passenger?.status} />
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" onClick={() => setShowEdit((value) => !value)}>Edit</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" onClick={archiveOrRestore}>
                {state?.passenger?.status === "archived" ? "Restore" : "Archive"}
              </button>
            </div>
          </div>
          {showEdit ? <PassengerForm initial={state.passenger} onSubmit={savePassenger} /> : null}
          <section className="grid gap-4 lg:grid-cols-3">
            <InfoCard title="Overview" rows={[
              ["DOB", state?.passenger?.date_of_birth],
              ["PTC", state?.passenger?.passenger_type],
              ["Nationality", state?.passenger?.nationality || "Not set"],
              ["Residence", state?.passenger?.residence_country || "Not set"],
            ]} />
            <InfoCard title="Travel Documents" rows={[
              ["Passport", state?.passenger?.passport_number || "Not set"],
              ["Passport country", state?.passenger?.passport_country || "Not set"],
              ["Passport expiry", state?.passenger?.passport_expiry || "Not set"],
              ["Notes", state?.passenger?.travel_document_notes || "None"],
            ]} />
            <InfoCard title="Assistance / Preferences" rows={[
              ["Assistance", state?.passenger?.known_assistance_needs || "None"],
              ["Medical internal", state?.passenger?.medical_notes_internal || "None"],
              ["Meals", state?.passenger?.meal_preferences || "None"],
            ]} />
          </section>
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-950">Associated clients</h3>
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" onClick={() => setShowLink((value) => !value)}>
                {showLink ? "Close link form" : "Link client"}
              </button>
            </div>
            {showLink ? (
              <RelationshipEditor clients={state.allClients} passengers={[state.passenger]} initial={{ passenger_id: state.passenger.id }} onSubmit={linkClient} />
            ) : null}
            {state?.relationships?.length ? (
              <div className="grid gap-3 md:grid-cols-2">
                {state.relationships.map((relationship) => {
                  const client = clientById[relationship.client_id]
                  return (
                    <a className="rounded-lg border border-slate-200 bg-white p-4" href={`/agency/clients/${relationship.client_id}`} key={relationship.id}>
                      <h4 className="font-semibold text-slate-950">{client?.display_name || "Client"}</h4>
                      <p className="mt-1 text-sm text-slate-600">{relationship.relationship_type.replaceAll("_", " ")} · {relationship.consent_status.replaceAll("_", " ")}</p>
                      <p className="mt-2 text-xs text-slate-500">
                        View {relationship.can_view ? "yes" : "no"} · Edit {relationship.can_edit ? "yes" : "no"} · Upload {relationship.can_upload_documents ? "yes" : "no"}
                      </p>
                    </a>
                  )
                })}
              </div>
            ) : (
              <EmptyState title="No clients linked" body="Passenger access must be granted through explicit relationship permissions." />
            )}
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Merge duplicate passenger</h3>
            <p className="mt-2 text-sm text-slate-600">Merge is non-destructive. This profile becomes duplicate_merged and future records should follow merged_into_passenger_id.</p>
            {mergeOptions.length && state?.passenger?.status !== "duplicate_merged" ? (
              <form className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]" onSubmit={mergePassenger}>
                <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={mergeTarget} onChange={(event) => setMergeTarget(event.target.value)}>
                  {mergeOptions.map((passenger) => (
                    <option key={passenger.id} value={passenger.id}>{passenger.display_name}</option>
                  ))}
                </select>
                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Merge reason" value={mergeReason} onChange={(event) => setMergeReason(event.target.value)} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="submit">Merge</button>
              </form>
            ) : (
              <p className="mt-3 text-sm text-slate-500">No merge targets available.</p>
            )}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function InfoCard({ title, rows }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      <dl className="mt-4 space-y-3 text-sm">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt className="font-medium text-slate-700">{label}</dt>
            <dd className="mt-1 text-slate-600">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
