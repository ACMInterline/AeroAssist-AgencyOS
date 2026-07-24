import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalPageHeader, PortalPill, PortalRecordList, formatDate, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalDocumentsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/document-center")])
      .then(([me, data]) => setState({ me, items: data.items || [] }))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <PortalPageHeader eyebrow="Travel documents" title={state?.me?.subject_type === "passenger" ? "My Documents" : "Document Centre"} description="Travel documents, validity, verification, and requested uploads." />
          <PortalRecordList items={state?.items} emptyTitle="No documents visible" emptyBody="Documents shared by your agency will appear here." href={(item) => `/portal/documents/${item.id}`}>
            {(item) => <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(170px,0.5fr)_auto] sm:items-center"><div><p className="font-semibold text-slate-950">{item.title}</p><div className="mt-1 flex flex-wrap gap-2"><PortalPill>{titleCase(item.type)}</PortalPill>{item.required_for_travel ? <PortalPill tone="amber">Required for travel</PortalPill> : null}</div></div><p className="text-sm text-slate-600">{item.deadline ? `Due ${formatDate(item.deadline)}` : item.passenger_name || "General document"}</p><PortalStatusBadge status={item.status} /></div>}
          </PortalRecordList>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
