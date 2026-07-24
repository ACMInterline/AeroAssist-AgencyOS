import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalFacts, PortalPageHeader, PortalRecordList, PortalSection, PortalTimeline, formatDate, formatMoney, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalEmdDetailPage({ emdId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/emds/${emdId}`)])
      .then(([me, detail]) => setState({ me, ...detail }))
      .catch((err) => setError(err.message))
  }, [emdId])
  const emd = state?.emd || {}
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-8"><PortalPageHeader eyebrow="Electronic miscellaneous document" title={emd.emd_number || "EMD pending"} description={emd.service_name || emd.service_code || "Ancillary service"} status={emd.status} backHref="/portal/emds" backLabel="Back to EMDs" /><PortalSection title="Service document details"><PortalFacts columns={3} rows={[["Passenger", emd.passenger_name || emd.passenger?.display_name], ["Service", emd.service_name || emd.service_code], ["Type", titleCase(emd.type)], ["RFIC", emd.rfic], ["RFISC", emd.rfisc], ["Issued", formatDate(emd.issue_date)], ["Total", formatMoney(emd.total_amount, emd.currency)], ["Status", titleCase(emd.status)]]} /></PortalSection><PortalSection title="Service coupons"><PortalRecordList items={state?.coupons} emptyTitle="No coupon details" emptyBody="Service coupon status will appear when available.">{(item) => <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold text-slate-950">Coupon {item.coupon_number}</p><p className="text-sm text-slate-600">{item.service_label || item.service_key || "Service"}</p></div><PortalStatusBadge status={item.status} /></div>}</PortalRecordList></PortalSection><div className="grid gap-8 lg:grid-cols-2"><PortalSection title="Refund status"><LedgerRows items={state?.refunds} /></PortalSection><PortalSection title="Exchange status"><LedgerRows items={state?.exchanges} /></PortalSection></div><PortalSection title="Documents"><PortalRecordList items={state?.documents} emptyTitle="No EMD documents" emptyBody="Visible receipts and service documents will appear here." href={(item) => `/portal/documents/${item.id}`}>{(item) => <div className="flex flex-wrap items-center justify-between gap-3"><p className="font-semibold text-slate-950">{item.title}</p><PortalStatusBadge status={item.status} /></div>}</PortalRecordList></PortalSection><PortalSection title="Service timeline"><PortalTimeline items={state?.timeline} /></PortalSection></div></ProtectedRoute></ClientPortalLayout>
}

function LedgerRows({ items }) {
  return items?.length ? <div className="divide-y divide-slate-200 border-y border-slate-200">{items.map((item) => <div className="flex items-center justify-between gap-3 py-3" key={item.id}><span className="text-sm text-slate-700">{item.reference || item.id}</span><PortalStatusBadge status={item.status} /></div>)}</div> : <p className="text-sm text-slate-500">No record linked.</p>
}
