import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalDashboardPage() {
  const [me, setMe] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    apiGet("/api/auth/me").then(setMe).catch((err) => setError(err.message))
  }, [])

  return (
    <ClientPortalLayout user={me?.user}>
      <ProtectedRoute loading={!me && !error} error={error}>
        <div className="grid gap-6 md:grid-cols-[1fr_1fr]">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Portal Layer</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">My Profile and Passengers</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Phase 2 establishes the client/passenger CRM foundation. Production portal account
              mapping is not implemented yet, so this area remains a safe read-only placeholder.
            </p>
          </section>
          <EmptyState
            title="Requests will appear here when portal access is connected"
            body="Request submission and portal-visible request timelines wait for production auth and client/passenger permission mapping."
          />
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
