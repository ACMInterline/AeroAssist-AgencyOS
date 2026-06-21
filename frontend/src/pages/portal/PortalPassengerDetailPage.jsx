import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalPassengerDetailPage({ passengerId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/passengers/${passengerId}`)]).then(([me, detail]) => setState({ me, passenger: detail.passenger })).catch((err) => setError(err.message))
  }, [passengerId])

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div><a className="text-sm font-medium text-blue-700" href="/portal/passengers">Back to passengers</a><h2 className="mt-2 text-2xl font-semibold text-slate-950">{state.passenger.display_name}</h2><p className="mt-1 text-sm text-slate-600">Read-only passenger profile.</p></div>
          <section className="grid gap-4 md:grid-cols-2">
            <Info title="Identity" rows={[["First name", state.passenger.first_name], ["Middle name", state.passenger.middle_name], ["Last name", state.passenger.last_name], ["Date of birth", state.passenger.date_of_birth], ["Passenger type", state.passenger.passenger_type]]} />
            <Info title="Travel Preferences" rows={[["Nationality", state.passenger.nationality], ["Residence", state.passenger.residence_country], ["Language", state.passenger.primary_language], ["Assistance", state.passenger.known_assistance_needs], ["Meals", state.passenger.meal_preferences]]} />
          </section>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Info({ title, rows }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value || "Not set"}</dd></div>)}</dl></section>
}
