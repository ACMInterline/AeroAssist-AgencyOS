import { useEffect, useState } from "react"
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js"
import Clock3 from "lucide-react/dist/esm/icons/clock-3.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalOfferDeliveriesPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => { Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/offer-deliveries")]).then(([me, data]) => setState({ me, items: data.items || [] })).catch((err) => setError(err.message)) }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-6"><header><p className="text-sm font-semibold uppercase text-blue-700">Your Travel Options</p><h2 className="mt-2 text-2xl font-semibold text-slate-950">Review Your Offers</h2><p className="mt-1 max-w-3xl text-sm text-slate-600">Compare routes, fares, baggage, flexibility, and assistance suitability from the exact version released by your travel agency.</p></header>{!state?.items?.length ? <EmptyState title="No travel options available" body="Your agency will release a reviewed comparison here when it is ready." /> : <div className="grid gap-4 md:grid-cols-2">{state.items.map((item) => <a href={`/portal/travel-options/${item.id}`} className="rounded-md border border-slate-200 bg-white p-5 transition hover:border-blue-400 hover:shadow-sm" key={item.id}><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase text-blue-700">{item.delivery_code}</p><h3 className="mt-1 text-lg font-semibold text-slate-950">{item.title}</h3></div><Plane className="h-5 w-5 text-blue-700" /></div><div className="mt-4 flex items-center justify-between gap-3 text-sm"><span className="inline-flex items-center gap-2 text-slate-600"><Clock3 className="h-4 w-4" />Expires {dateTime(item.expires_at)}</span><span className="inline-flex items-center gap-1 font-semibold text-blue-700">Review <ArrowRight className="h-4 w-4" /></span></div></a>)}</div>}</div></ProtectedRoute></ClientPortalLayout>
}
function dateTime(value) { return value ? new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "when your agency advises" }
