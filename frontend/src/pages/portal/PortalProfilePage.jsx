import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalProfilePage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/profile")]).then(([me, profile]) => setState({ me, profile })).catch((err) => setError(err.message))
  }, [])

  const passengerPortal = state?.profile?.subject_type === "passenger"
  const subject = passengerPortal ? state?.profile?.passenger : state?.profile?.client

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <Header title="Profile" subtitle={`Read-only ${passengerPortal ? "passenger" : "client"} profile details held by your agency.`} portalLabel={passengerPortal ? "Passenger portal" : "Client portal"} />
          <section className="grid gap-4 md:grid-cols-2">
            <Info title={passengerPortal ? "Passenger" : "Client"} rows={passengerPortal ? [["Display name", subject?.display_name], ["Passenger type", subject?.passenger_type], ["Nationality", subject?.nationality], ["Status", subject?.status]] : [["Display name", subject?.display_name], ["Legal name", subject?.legal_name], ["Type", subject?.client_type], ["Status", subject?.status]]} />
            <Info title={passengerPortal ? "Travel profile" : "Contact"} rows={passengerPortal ? [["First name", subject?.first_name], ["Middle name", subject?.middle_name], ["Last name", subject?.last_name], ["Language", subject?.primary_language]] : [["Email", subject?.primary_email], ["Phone", subject?.primary_phone], ["Country", subject?.country], ["City", subject?.city], ["Language", subject?.preferred_language]]} />
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-semibold text-slate-950">Portal access</h3>
              <PortalStatusBadge status={state?.profile?.portal_account?.portal_status} />
            </div>
            <p className="mt-3 text-sm text-slate-600">{passengerPortal ? "Access is limited to this explicitly linked Passenger profile." : subject?.client_visible_notes || "No client-visible notes."}</p>
          </section>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Header({ title, subtitle, portalLabel }) {
  return <div><p className="text-sm font-semibold uppercase tracking-wide text-blue-700">{portalLabel}</p><h2 className="mt-2 text-2xl font-semibold text-slate-950">{title}</h2><p className="mt-1 text-sm text-slate-600">{subtitle}</p></div>
}

function Info({ title, rows }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value || "Not set"}</dd></div>)}</dl></section>
}
