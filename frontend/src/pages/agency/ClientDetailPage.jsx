import { useEffect, useState } from "react"
import ClientForm from "../../components/ClientForm"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import RelationshipEditor from "../../components/RelationshipEditor"
import StatusBadge from "../../components/StatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function ClientDetailPage({ clientId }) {
  const [state, setState] = useState(null)
  const [showEdit, setShowEdit] = useState(false)
  const [showLink, setShowLink] = useState(false)
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/clients/${clientId}`)
    const allPassengers = await apiGet(`/api/agencies/${context.agency.id}/passengers`)
    setState({ ...context, ...detail, allPassengers: allPassengers.items })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [clientId])

  async function saveClient(payload) {
    const allowed = [
      "client_type",
      "display_name",
      "legal_name",
      "primary_email",
      "primary_phone",
      "country",
      "city",
      "address_line_1",
      "address_line_2",
      "postal_code",
      "preferred_language",
      "default_currency",
      "tax_id",
      "company_registration_number",
      "portal_status",
      "marketing_consent",
      "data_processing_consent",
      "internal_notes",
      "client_visible_notes",
      "status",
    ]
    const cleanPayload = Object.fromEntries(allowed.map((key) => [key, payload[key]]).filter(([, value]) => value !== undefined))
    await apiPut(`/api/agencies/${state.agency.id}/clients/${clientId}`, cleanPayload)
    setShowEdit(false)
    await load()
  }

  async function archiveOrRestore() {
    const action = state.client.status === "archived" ? "restore" : "archive"
    await apiPost(`/api/agencies/${state.agency.id}/clients/${clientId}/${action}`)
    await load()
  }

  async function linkPassenger(payload) {
    await apiPost(`/api/agencies/${state.agency.id}/client-passenger-relationships`, payload)
    setShowLink(false)
    await load()
  }

  const passengerById = Object.fromEntries((state?.passengers || []).map((passenger) => [passenger.id, passenger]))

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/clients">Back to clients</a>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">{state?.client?.display_name}</h2>
              <p className="mt-1 text-sm text-slate-600">Client account/contact record, not necessarily a traveler.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge status={state?.client?.status} />
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" onClick={() => setShowEdit((value) => !value)}>Edit</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" onClick={archiveOrRestore}>
                {state?.client?.status === "archived" ? "Restore" : "Archive"}
              </button>
            </div>
          </div>
          {showEdit ? <ClientForm initial={state.client} onSubmit={saveClient} /> : null}
          <section className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Overview</h3>
              <dl className="mt-4 space-y-3 text-sm">
                <Info label="Type" value={state?.client?.client_type?.replaceAll("_", " ")} />
                <Info label="Legal name" value={state?.client?.legal_name || "Not set"} />
                <Info label="Email" value={state?.client?.primary_email} />
                <Info label="Phone" value={state?.client?.primary_phone || "Not set"} />
                <Info label="City" value={state?.client?.city || "Not set"} />
              </dl>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Portal Access</h3>
              <p className="mt-3 text-sm text-slate-600">Portal status: {state?.client?.portal_status?.replaceAll("_", " ")}</p>
              <p className="mt-2 text-sm text-slate-600">Data processing consent: {state?.client?.data_processing_consent ? "Granted" : "Not granted"}</p>
              <p className="mt-2 text-sm text-slate-600">Marketing consent: {state?.client?.marketing_consent ? "Granted" : "Not granted"}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Notes</h3>
              <p className="mt-3 text-sm font-medium text-slate-700">Internal</p>
              <p className="mt-1 text-sm text-slate-600">{state?.client?.internal_notes || "None"}</p>
              <p className="mt-3 text-sm font-medium text-slate-700">Client-visible</p>
              <p className="mt-1 text-sm text-slate-600">{state?.client?.client_visible_notes || "None"}</p>
            </div>
          </section>
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-950">Associated passengers</h3>
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" onClick={() => setShowLink((value) => !value)}>
                {showLink ? "Close link form" : "Link passenger"}
              </button>
            </div>
            {showLink ? (
              <RelationshipEditor clients={[state.client]} passengers={state.allPassengers} initial={{ client_id: state.client.id }} onSubmit={linkPassenger} />
            ) : null}
            {state?.relationships?.length ? (
              <div className="grid gap-3 md:grid-cols-2">
                {state.relationships.map((relationship) => {
                  const passenger = passengerById[relationship.passenger_id]
                  return (
                    <a className="rounded-lg border border-slate-200 bg-white p-4" href={`/agency/passengers/${relationship.passenger_id}`} key={relationship.id}>
                      <h4 className="font-semibold text-slate-950">{passenger?.display_name || "Passenger"}</h4>
                      <p className="mt-1 text-sm text-slate-600">{relationship.relationship_type.replaceAll("_", " ")} · {relationship.consent_status.replaceAll("_", " ")}</p>
                      <p className="mt-2 text-xs text-slate-500">
                        View {relationship.can_view ? "yes" : "no"} · Edit {relationship.can_edit ? "yes" : "no"} · Pay {relationship.can_pay ? "yes" : "no"}
                      </p>
                    </a>
                  )
                })}
              </div>
            ) : (
              <EmptyState title="No passengers linked" body="Link passenger profiles through explicit permission relationships." />
            )}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Info({ label, value }) {
  return (
    <div>
      <dt className="font-medium text-slate-700">{label}</dt>
      <dd className="mt-1 text-slate-600">{value}</dd>
    </div>
  )
}
