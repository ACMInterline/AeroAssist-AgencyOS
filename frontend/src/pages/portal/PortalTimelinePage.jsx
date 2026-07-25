import { useEffect, useState } from "react"
import { PortalPageHeader, PortalTimeline } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalTimelinePage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/timeline")])
      .then(([me, data]) => setState({ me, items: data.items || [] }))
      .catch((err) => setError(err.message))
  }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-6"><PortalPageHeader eyebrow="Shared journey history" title="Timeline" description="Client-visible operational events, approvals, and milestones in newest-first order." /><PortalTimeline items={state?.items} /></div></ProtectedRoute></ClientPortalLayout>
}
