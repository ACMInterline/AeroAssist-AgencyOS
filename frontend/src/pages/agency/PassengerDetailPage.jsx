import { useEffect, useState } from "react"
import Archive from "lucide-react/dist/esm/icons/archive.js"
import Pencil from "lucide-react/dist/esm/icons/pencil.js"
import ConfirmationDialog from "../../components/ConfirmationDialog"
import DestructiveButton from "../../components/DestructiveButton"
import EmptyState from "../../components/EmptyState"
import PageHeader from "../../components/PageHeader"
import PassengerForm from "../../components/PassengerForm"
import ProtectedRoute from "../../components/ProtectedRoute"
import RelationshipEditor from "../../components/RelationshipEditor"
import SecondaryButton from "../../components/SecondaryButton"
import StatusBadge from "../../components/StatusBadge"
import WorkflowContinuityPanel from "../../components/WorkflowContinuityPanel"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function PassengerDetailPage({ passengerId }) {
  const [state, setState] = useState(null)
  const [showEdit, setShowEdit] = useState(false)
  const [showLink, setShowLink] = useState(false)
  const [mergeTarget, setMergeTarget] = useState("")
  const [mergeReason, setMergeReason] = useState("")
  const [confirmation, setConfirmation] = useState("")
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
    if (state.passenger.status !== "archived") {
      setConfirmation("archive")
      return
    }
    const action = state.passenger.status === "archived" ? "restore" : "archive"
    await apiPost(`/api/agencies/${state.agency.id}/passengers/${passengerId}/${action}`)
    await load()
  }

  async function confirmArchive() {
    await apiPost(`/api/agencies/${state.agency.id}/passengers/${passengerId}/archive`)
    setConfirmation("")
    await load()
  }

  async function linkClient(payload) {
    await apiPost(`/api/agencies/${state.agency.id}/client-passenger-relationships`, payload)
    setShowLink(false)
    await load()
  }

  async function mergePassenger(event) {
    event.preventDefault()
    setConfirmation("merge")
  }

  async function confirmMerge() {
    await apiPost(`/api/agencies/${state.agency.id}/passengers/${passengerId}/merge`, {
      target_passenger_id: mergeTarget,
      reason: mergeReason || "Duplicate passenger record",
      retained_fields_summary: { retained_profile: mergeTarget },
    })
    setConfirmation("")
    await load()
  }

  const clientById = Object.fromEntries((state?.clients || []).map((client) => [client.id, client]))
  const mergeOptions = (state?.allPassengers || []).filter((passenger) => passenger.id !== passengerId && passenger.status !== "duplicate_merged")
  const firstRelationship = state?.relationships?.find((relationship) => relationship.status === "active")
  const passengerActive = !["archived", "duplicate_merged"].includes(state?.passenger?.status)

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Passengers", href: "/agency/passengers" }, { label: state?.passenger?.display_name || "Passenger" }]}
            eyebrow="Passenger profile"
            title={state?.passenger?.display_name}
            description="Identity, travel documents, assistance needs, preferences, and linked clients."
            status={<StatusBadge status={state?.passenger?.status} />}
            actions={<><SecondaryButton icon={Pencil} onClick={() => setShowEdit((value) => !value)}>{showEdit ? "Close edit form" : "Edit passenger"}</SecondaryButton><SecondaryButton icon={Archive} onClick={archiveOrRestore}>{state?.passenger?.status === "archived" ? "Restore passenger" : "Archive passenger"}</SecondaryButton></>}
          />
          <WorkflowContinuityPanel
            breadcrumbs={[{ label: "Passengers", href: "/agency/passengers" }]}
            currentLabel={state?.passenger?.display_name || "Passenger"}
            status={state?.passenger?.status}
            validation={firstRelationship && passengerActive
              ? { state: "ready", label: "Request context ready", reason: "Client ownership and passenger relationship are available." }
              : { state: passengerActive ? "warning" : "blocked", label: passengerActive ? "Client relationship required" : "Passenger unavailable", reason: passengerActive ? "Link this traveler to a client before creating a request." : "Restore or use the retained passenger identity before continuing." }}
            previous={firstRelationship ? { label: "Previous: client", href: `/agency/clients/${firstRelationship.client_id}` } : { label: "Passengers", href: "/agency/passengers" }}
            next={{
              label: "Continue to request",
              href: firstRelationship ? `/agency/requests/new?client_id=${encodeURIComponent(firstRelationship.client_id)}&passenger_id=${encodeURIComponent(passengerId)}` : undefined,
              enabled: Boolean(firstRelationship && passengerActive),
              reason: "An active client relationship is required.",
            }}
            relatedRecords={[{ label: "Clients", value: state?.relationships?.length || 0 }]}
          />
          {showEdit ? <PassengerForm initial={state.passenger} onSubmit={savePassenger} /> : null}
          <section className="grid gap-4 lg:grid-cols-3">
            <InfoCard title="Overview" rows={[
              ["Date of birth", state?.passenger?.date_of_birth],
              ["Passenger type", state?.passenger?.passenger_type],
              ["Nationality", state?.passenger?.nationality || "Not set"],
              ["Residence", state?.passenger?.residence_country || "Not set"],
            ]} />
            <InfoCard title="Travel Documents" rows={[
              ["Passport", state?.passenger?.passport_number || "Not set"],
              ["Passport country", state?.passenger?.passport_country || "Not set"],
              ["Passport expiry", state?.passenger?.passport_expiry || "Not set"],
              ["Notes", state?.passenger?.travel_document_notes || "None"],
            ]} />
            <InfoCard title="Assistance and preferences" rows={[
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
              <EmptyState title="No client linked" body="Link this passenger to the client who can view or request travel for them." />
            )}
          </section>
          <details className="rounded-lg border border-slate-200 bg-white p-5">
            <summary className="cursor-pointer text-sm font-semibold text-slate-900">Resolve a duplicate passenger</summary>
            <p className="mt-3 text-sm text-slate-600">Choose the passenger profile to keep. This profile will be archived as a duplicate and its history will remain available.</p>
            {mergeOptions.length && state?.passenger?.status !== "duplicate_merged" ? (
              <form className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]" onSubmit={mergePassenger}>
                <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={mergeTarget} onChange={(event) => setMergeTarget(event.target.value)}>
                  {mergeOptions.map((passenger) => (
                    <option key={passenger.id} value={passenger.id}>{passenger.display_name}</option>
                  ))}
                </select>
                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Merge reason" value={mergeReason} onChange={(event) => setMergeReason(event.target.value)} />
                <DestructiveButton type="submit">Merge profiles</DestructiveButton>
              </form>
            ) : (
              <p className="mt-3 text-sm text-slate-500">No merge targets available.</p>
            )}
          </details>
          <ConfirmationDialog
            confirmLabel="Archive passenger"
            destructive
            message="The passenger will no longer appear in active work. Their history and linked travel details will remain available."
            onCancel={() => setConfirmation("")}
            onConfirm={confirmArchive}
            open={confirmation === "archive"}
            title="Archive this passenger?"
          />
          <ConfirmationDialog
            confirmLabel="Merge profiles"
            destructive
            message="This profile will be marked as a duplicate and future work should use the selected passenger profile. Existing history will not be deleted."
            onCancel={() => setConfirmation("")}
            onConfirm={confirmMerge}
            open={confirmation === "merge"}
            title="Merge these passenger profiles?"
          />
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
