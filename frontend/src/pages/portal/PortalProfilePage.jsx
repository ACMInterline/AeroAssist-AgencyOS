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

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <Header title="Profile" subtitle="Read-only client profile details held by your agency." />
          <section className="grid gap-4 md:grid-cols-2">
            <Info title="Client" rows={[["Display name", state.profile.client.display_name], ["Legal name", state.profile.client.legal_name], ["Type", state.profile.client.client_type], ["Status", state.profile.client.status]]} />
            <Info title="Contact" rows={[["Email", state.profile.client.primary_email], ["Phone", state.profile.client.primary_phone], ["Country", state.profile.client.country], ["City", state.profile.client.city], ["Language", state.profile.client.preferred_language]]} />
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-semibold text-slate-950">Portal access</h3>
              <PortalStatusBadge status={state.profile.portal_account.portal_status} />
            </div>
            <p className="mt-3 text-sm text-slate-600">{state.profile.client.client_visible_notes || "No client-visible notes."}</p>
          </section>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Header({ title, subtitle }) {
  return <div><p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Client portal</p><h2 className="mt-2 text-2xl font-semibold text-slate-950">{title}</h2><p className="mt-1 text-sm text-slate-600">{subtitle}</p></div>
}

function Info({ title, rows }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value || "Not set"}</dd></div>)}</dl></section>
}
