import { useEffect, useState } from "react"
import BookingStatusBadge from "../../components/BookingStatusBadge"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalBookingsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => { Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/bookings")]).then(([me, data]) => setState({ me, items: data.items })).catch((err) => setError(err.message)) }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-6"><Header title="Bookings" body="Read-only booking and itinerary summaries." />{!state.items.length ? <EmptyState title="No bookings visible" body="Bookings appear after your agency creates client-visible tracking records." /> : <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">{state.items.map((item) => <a className="block p-4 text-sm hover:bg-slate-50" href={`/portal/bookings/${item.id}`} key={item.id}><span className="font-semibold text-slate-950">{item.booking_reference} · PNR {item.pnr || "not set"}</span><span className="mt-2 flex items-center gap-2 text-slate-600"><BookingStatusBadge status={item.status} />Due {item.amount_due} {item.currency}</span></a>)}</div>}</div></ProtectedRoute></ClientPortalLayout>
}

function Header({ title, body }) { return <div><p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Client portal</p><h2 className="mt-2 text-2xl font-semibold text-slate-950">{title}</h2><p className="mt-1 text-sm text-slate-600">{body}</p></div> }
