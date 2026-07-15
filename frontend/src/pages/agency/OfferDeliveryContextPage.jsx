import { useEffect, useMemo, useState } from "react"
import OfferDeliveryPanel from "../../components/offers/OfferDeliveryPanel"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { loadCurrentAgency } from "../../lib/agency"

export default function OfferDeliveryContextPage() {
  const query = useMemo(() => new URLSearchParams(window.location.search), [])
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => { loadCurrentAgency().then(setState).catch((err) => setError(err.message)) }, [])

  return <AgencyLayout user={state?.me?.user} agency={state?.agency}><ProtectedRoute loading={!state && !error} error={error}>{state ? <div className="space-y-4"><a className="text-sm font-semibold text-blue-700" href={query.get("offer_id") ? `/agency/offers/${encodeURIComponent(query.get("offer_id"))}?section=delivery` : "/agency/offers"}>Back to Offer Workspace</a><OfferDeliveryPanel agency={state.agency} offerId={query.get("offer_id") || ""} initialDeliveryId={query.get("delivery_id") || ""} clientId={query.get("client_id") || ""} passengerId={query.get("passenger_id") || ""} presentationId={query.get("presentation_id") || ""} /></div> : null}</ProtectedRoute></AgencyLayout>
}
