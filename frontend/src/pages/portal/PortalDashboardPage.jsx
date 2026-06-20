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
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Client portal reserved</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Phase 1 reserves the portal route and layout only. Client accounts, passenger
              permissions, requests, offers, tickets, EMDs, invoices, payments, and documents are
              intentionally not available yet.
            </p>
          </section>
          <EmptyState
            title="No portal workflows in Phase 1"
            body="The next implementation steps must first add CRM and client/passenger relationships before portal records can be safely exposed."
          />
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
