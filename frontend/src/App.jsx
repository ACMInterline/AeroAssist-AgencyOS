import AgencyDashboardPage from "./pages/agency/AgencyDashboardPage"
import AirlineIntelligenceDetailPage from "./pages/agency/AirlineIntelligenceDetailPage"
import AirlineIntelligencePage from "./pages/agency/AirlineIntelligencePage"
import AirlineKnowledgeViewPage from "./pages/agency/AirlineKnowledgeViewPage"
import BookingCreatePage from "./pages/agency/BookingCreatePage"
import BookingDetailPage from "./pages/agency/BookingDetailPage"
import BookingsPage from "./pages/agency/BookingsPage"
import ClientDetailPage from "./pages/agency/ClientDetailPage"
import ClientsPage from "./pages/agency/ClientsPage"
import InvoiceDetailPage from "./pages/agency/InvoiceDetailPage"
import InvoicesPage from "./pages/agency/InvoicesPage"
import OfferCreatePage from "./pages/agency/OfferCreatePage"
import OfferDetailPage from "./pages/agency/OfferDetailPage"
import OffersPage from "./pages/agency/OffersPage"
import PassengerDetailPage from "./pages/agency/PassengerDetailPage"
import PassengersPage from "./pages/agency/PassengersPage"
import PaymentsPage from "./pages/agency/PaymentsPage"
import RequestCreatePage from "./pages/agency/RequestCreatePage"
import RequestDetailPage from "./pages/agency/RequestDetailPage"
import RequestsPage from "./pages/agency/RequestsPage"
import LoginPage from "./pages/auth/LoginPage"
import AirlineDetailPage from "./pages/platform/AirlineDetailPage"
import AirlineKnowledgeDetailPage from "./pages/platform/AirlineKnowledgeDetailPage"
import AirlinesPage from "./pages/platform/AirlinesPage"
import PlatformDashboardPage from "./pages/platform/PlatformDashboardPage"
import PortalDashboardPage from "./pages/portal/PortalDashboardPage"
import HomePage from "./pages/public/HomePage"

const routes = {
  "/": HomePage,
  "/login": LoginPage,
  "/platform": PlatformDashboardPage,
  "/platform/airlines": AirlinesPage,
  "/agency": AgencyDashboardPage,
  "/agency/airline-intelligence": AirlineIntelligencePage,
  "/portal": PortalDashboardPage,
}

export default function App() {
  if (window.location.pathname === "/agency/requests/new") {
    return <RequestCreatePage />
  }

  if (window.location.pathname === "/agency/offers/new") {
    return <OfferCreatePage />
  }

  if (window.location.pathname === "/agency/bookings/new") {
    return <BookingCreatePage />
  }

  const clientMatch = window.location.pathname.match(/^\/agency\/clients\/([^/]+)$/)
  if (clientMatch) {
    return <ClientDetailPage clientId={clientMatch[1]} />
  }

  const passengerMatch = window.location.pathname.match(/^\/agency\/passengers\/([^/]+)$/)
  if (passengerMatch) {
    return <PassengerDetailPage passengerId={passengerMatch[1]} />
  }

  const requestMatch = window.location.pathname.match(/^\/agency\/requests\/([^/]+)$/)
  if (requestMatch) {
    return <RequestDetailPage requestId={requestMatch[1]} />
  }

  const offerMatch = window.location.pathname.match(/^\/agency\/offers\/([^/]+)$/)
  if (offerMatch) {
    return <OfferDetailPage offerId={offerMatch[1]} />
  }

  const bookingMatch = window.location.pathname.match(/^\/agency\/bookings\/([^/]+)$/)
  if (bookingMatch) {
    return <BookingDetailPage bookingId={bookingMatch[1]} />
  }

  const invoiceMatch = window.location.pathname.match(/^\/agency\/invoices\/([^/]+)$/)
  if (invoiceMatch) {
    return <InvoiceDetailPage invoiceId={invoiceMatch[1]} />
  }

  const agencyAirlineMatch = window.location.pathname.match(/^\/agency\/airline-intelligence\/([^/]+)$/)
  if (agencyAirlineMatch) {
    return <AirlineIntelligenceDetailPage airlineId={agencyAirlineMatch[1]} />
  }

  const agencyKnowledgeMatch = window.location.pathname.match(/^\/agency\/airline-knowledge\/([^/]+)$/)
  if (agencyKnowledgeMatch) {
    return <AirlineKnowledgeViewPage knowledgeId={agencyKnowledgeMatch[1]} />
  }

  const platformAirlineMatch = window.location.pathname.match(/^\/platform\/airlines\/([^/]+)$/)
  if (platformAirlineMatch) {
    return <AirlineDetailPage airlineId={platformAirlineMatch[1]} />
  }

  const platformKnowledgeMatch = window.location.pathname.match(/^\/platform\/airline-knowledge\/([^/]+)$/)
  if (platformKnowledgeMatch) {
    return <AirlineKnowledgeDetailPage knowledgeId={platformKnowledgeMatch[1]} />
  }

  if (window.location.pathname === "/agency/clients") {
    return <ClientsPage />
  }

  if (window.location.pathname === "/agency/passengers") {
    return <PassengersPage />
  }

  if (window.location.pathname === "/agency/requests") {
    return <RequestsPage />
  }

  if (window.location.pathname === "/agency/offers") {
    return <OffersPage />
  }

  if (window.location.pathname === "/agency/bookings") {
    return <BookingsPage />
  }

  if (window.location.pathname === "/agency/invoices") {
    return <InvoicesPage />
  }

  if (window.location.pathname === "/agency/payments") {
    return <PaymentsPage />
  }

  const Page = routes[window.location.pathname] || HomePage
  return <Page />
}
