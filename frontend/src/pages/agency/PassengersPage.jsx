import { useEffect, useMemo, useState } from "react"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import EmptyState from "../../components/EmptyState"
import FilterBar from "../../components/FilterBar"
import PageHeader from "../../components/PageHeader"
import PilotGuidance from "../../components/PilotGuidance"
import PassengerForm from "../../components/PassengerForm"
import PrimaryButton from "../../components/PrimaryButton"
import ProtectedRoute from "../../components/ProtectedRoute"
import SecondaryButton from "../../components/SecondaryButton"
import StatusBadge from "../../components/StatusBadge"
import PtcSelect from "../../components/reference/PtcSelect"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"
import { passengerTypeLabel } from "../../lib/productLanguage"

export default function PassengersPage() {
  const query = new URLSearchParams(window.location.search)
  const sourceClientId = query.get("client_id") || ""
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", passenger_type: "", status: "" })
  const [showCreate, setShowCreate] = useState(query.get("create") === "1")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const passengers = context.agency ? await apiGet(`/api/agencies/${context.agency.id}/passengers`) : { items: [] }
    setState({ ...context, passengers: passengers.items })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const filteredPassengers = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.passengers || []).filter((passenger) => {
      const matchesSearch = !search || [passenger.display_name, passenger.first_name, passenger.last_name, passenger.nationality].some((value) => String(value || "").toLowerCase().includes(search))
      return matchesSearch
        && (!filters.passenger_type || (passenger.passenger_type_code || passenger.passenger_type) === filters.passenger_type)
        && (!filters.status || passenger.status === filters.status)
    })
  }, [filters, state])

  async function createPassenger(payload) {
    const cleanPayload = Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== ""))
    const result = await apiPost(`/api/agencies/${state.agency.id}/passengers`, cleanPayload)
    if (sourceClientId) {
      await apiPost(`/api/agencies/${state.agency.id}/client-passenger-relationships`, {
        client_id: sourceClientId,
        passenger_id: result.passenger.id,
        relationship_type: "self",
        can_view: true,
        can_request_travel: true,
        consent_status: "pending",
        notes: "Created from the canonical Client to Passenger workflow.",
      })
    }
    setShowCreate(false)
    window.location.href = `/agency/passengers/${result.passenger.id}`
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <PageHeader
            eyebrow="Passenger profiles"
            title="Passengers"
            description={`Keep identity, travel documents, preferences, and assistance needs together.${sourceClientId ? " The new passenger will be linked to the selected client." : ""}`}
            actions={showCreate
              ? <SecondaryButton onClick={() => setShowCreate(false)}>Close form</SecondaryButton>
              : <PrimaryButton icon={Plus} onClick={() => setShowCreate(true)}>Create passenger</PrimaryButton>}
          />
          <PilotGuidance area="passengers" />
          {showCreate ? <PassengerForm onSubmit={createPassenger} submitLabel="Create passenger" /> : null}
          <FilterBar onClear={() => setFilters({ search: "", passenger_type: "", status: "" })} resultCount={filteredPassengers.length} title="Filter passengers">
            <div className="grid gap-3 md:grid-cols-3">
              <label className="grid gap-1 text-sm font-medium text-slate-700">
                Search
                <input className="field" placeholder="Passenger name or nationality" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
              </label>
              <PtcSelect
                label="Passenger type"
                placeholder="All passenger types"
                selectedCode={filters.passenger_type}
                value={filters.passenger_type}
                valueMode="code"
                onChange={(option) => setFilters({ ...filters, passenger_type: option?.code || "" })}
              />
              <label className="grid gap-1 text-sm font-medium text-slate-700">
                Current status
                <select className="field" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
                  <option value="">All statuses</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="archived">Archived</option>
                  <option value="duplicate_merged">Merged duplicate</option>
                </select>
              </label>
            </div>
          </FilterBar>
          {filteredPassengers.length ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {filteredPassengers.map((passenger) => (
                <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={`/agency/passengers/${passenger.id}`} key={passenger.id}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-slate-950">{passenger.display_name}</h3>
                      <p className="mt-1 text-sm text-slate-600">{passenger.passenger_type_label || passengerTypeLabel(passenger.passenger_type_code || passenger.passenger_type)} · born {passenger.date_of_birth}</p>
                    </div>
                    <StatusBadge status={passenger.status} />
                  </div>
                  <p className="mt-4 text-sm text-slate-600">{passenger.nationality || "Nationality not set"} / {passenger.residence_country || "Residence not set"}</p>
                </a>
              ))}
            </div>
          ) : (
            <EmptyState title="No passengers match these filters" body="Clear the filters or create a passenger profile for the person who will travel.">
              <PrimaryButton icon={Plus} onClick={() => setShowCreate(true)}>Create passenger</PrimaryButton>
            </EmptyState>
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
