import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalPageHeader, PortalRecordList, formatDateTime, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalApprovalsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/approvals")])
      .then(([me, data]) => setState({ me, items: data.items || [] }))
      .catch((err) => setError(err.message))
  }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-6"><PortalPageHeader eyebrow="Decision history" title="Approvals" description="Offer, quote, service, document, and consent decisions shared in your journey timeline." /><PortalRecordList items={state?.items} emptyTitle="No approvals visible" emptyBody="Approval requests and completed decisions will appear here.">{(item) => <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.5fr)_auto] sm:items-center"><div><p className="font-semibold text-slate-950">{titleCase(item.approval_type)}</p><p className="mt-1 text-sm text-slate-600">{typeof item.summary === "string" ? item.summary : "Decision recorded against the journey."}</p></div><p className="text-sm text-slate-600">{formatDateTime(item.occurred_at)}</p><PortalStatusBadge status={item.status} /></div>}</PortalRecordList></div></ProtectedRoute></ClientPortalLayout>
}
