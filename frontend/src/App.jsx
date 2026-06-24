import AgencyDashboardPage from "./pages/agency/AgencyDashboardPage"
import AgencySettingsPage from "./pages/agency/AgencySettingsPage"
import AirlineIntelligenceDetailPage from "./pages/agency/AirlineIntelligenceDetailPage"
import AirlineIntelligencePage from "./pages/agency/AirlineIntelligencePage"
import AirlineKnowledgeViewPage from "./pages/agency/AirlineKnowledgeViewPage"
import BookingCreatePage from "./pages/agency/BookingCreatePage"
import BookingDetailPage from "./pages/agency/BookingDetailPage"
import BookingsPage from "./pages/agency/BookingsPage"
import ClientDetailPage from "./pages/agency/ClientDetailPage"
import ClientsPage from "./pages/agency/ClientsPage"
import DocumentDetailPage from "./pages/agency/DocumentDetailPage"
import DocumentStoragePage from "./pages/agency/DocumentStoragePage"
import DocumentTemplatesPage from "./pages/agency/DocumentTemplatesPage"
import DocumentsPage from "./pages/agency/DocumentsPage"
import InvoiceDetailPage from "./pages/agency/InvoiceDetailPage"
import InvoicesPage from "./pages/agency/InvoicesPage"
import OfferCreatePage from "./pages/agency/OfferCreatePage"
import OfferDetailPage from "./pages/agency/OfferDetailPage"
import OffersPage from "./pages/agency/OffersPage"
import RefundExchangeCaseCreatePage from "./pages/agency/RefundExchangeCaseCreatePage"
import RefundExchangeCaseDetailPage from "./pages/agency/RefundExchangeCaseDetailPage"
import RefundExchangeCasesPage from "./pages/agency/RefundExchangeCasesPage"
import ReferenceDataPage from "./pages/agency/ReferenceDataPage"
import FormProfilesPage from "./pages/agency/FormProfilesPage"
import PassengerDetailPage from "./pages/agency/PassengerDetailPage"
import PassengersPage from "./pages/agency/PassengersPage"
import PaymentsPage from "./pages/agency/PaymentsPage"
import AgencyPortalActionsPage from "./pages/agency/PortalActionsPage"
import RequestCreatePage from "./pages/agency/RequestCreatePage"
import RequestDetailPage from "./pages/agency/RequestDetailPage"
import RequestIntakeDetailPage from "./pages/agency/RequestIntakeDetailPage"
import RequestIntakesListPage from "./pages/agency/RequestIntakesListPage"
import RequestsPage from "./pages/agency/RequestsPage"
import WebsiteBuilderPage from "./pages/agency/WebsiteBuilderPage"
import WebsiteMediaLibraryPage from "./pages/agency/WebsiteMediaLibraryPage"
import LoginPage from "./pages/auth/LoginPage"
import InviteAcceptPage from "./pages/auth/InviteAcceptPage"
import AirlineDetailPage from "./pages/platform/AirlineDetailPage"
import AirlineKnowledgeDetailPage from "./pages/platform/AirlineKnowledgeDetailPage"
import AirlinesPage from "./pages/platform/AirlinesPage"
import PlatformAgenciesPage from "./pages/platform/PlatformAgenciesPage"
import PlatformAgencyDetailPage from "./pages/platform/PlatformAgencyDetailPage"
import PlatformDashboardPage from "./pages/platform/PlatformDashboardPage"
import PlatformReferenceDataPage from "./pages/platform/PlatformReferenceDataPage"
import PortalBookingDetailPage from "./pages/portal/PortalBookingDetailPage"
import PortalActionsPage from "./pages/portal/PortalActionsPage"
import PortalBookingsPage from "./pages/portal/PortalBookingsPage"
import PortalDashboardPage from "./pages/portal/PortalDashboardPage"
import PortalDocumentDetailPage from "./pages/portal/PortalDocumentDetailPage"
import PortalDocumentsPage from "./pages/portal/PortalDocumentsPage"
import PortalInvoiceDetailPage from "./pages/portal/PortalInvoiceDetailPage"
import PortalInvoicesPage from "./pages/portal/PortalInvoicesPage"
import PortalOfferDetailPage from "./pages/portal/PortalOfferDetailPage"
import PortalOffersPage from "./pages/portal/PortalOffersPage"
import PortalPassengerDetailPage from "./pages/portal/PortalPassengerDetailPage"
import PortalPassengersPage from "./pages/portal/PortalPassengersPage"
import PortalPaymentsPage from "./pages/portal/PortalPaymentsPage"
import PortalProfilePage from "./pages/portal/PortalProfilePage"
import PortalRequestDetailPage from "./pages/portal/PortalRequestDetailPage"
import PortalRequestCreatePage from "./pages/portal/PortalRequestCreatePage"
import PortalRequestsPage from "./pages/portal/PortalRequestsPage"
import PortalRefundExchangeCaseDetailPage from "./pages/portal/PortalRefundExchangeCaseDetailPage"
import PortalRefundExchangeCasesPage from "./pages/portal/PortalRefundExchangeCasesPage"
import HomePage from "./pages/public/HomePage"
import PublicAgencyWebsitePage from "./pages/public/PublicAgencyWebsitePage"

const routes = {
  "/": HomePage,
  "/invite/accept": InviteAcceptPage,
  "/login": LoginPage,
  "/platform": PlatformDashboardPage,
  "/platform/agencies": PlatformAgenciesPage,
  "/platform/airlines": AirlinesPage,
  "/platform/reference": PlatformReferenceDataPage,
  "/agency": AgencyDashboardPage,
  "/agency/settings": AgencySettingsPage,
  "/agency/website": WebsiteBuilderPage,
  "/agency/website/media": WebsiteMediaLibraryPage,
  "/agency/reference": ReferenceDataPage,
  "/agency/settings/forms": FormProfilesPage,
  "/agency/airline-intelligence": AirlineIntelligencePage,
  "/agency/documents": DocumentsPage,
  "/agency/document-storage": DocumentStoragePage,
  "/agency/document-templates": DocumentTemplatesPage,
  "/agency/portal-actions": AgencyPortalActionsPage,
  "/agency/request-intakes": RequestIntakesListPage,
  "/agency/refunds-exchanges": RefundExchangeCasesPage,
  "/agency/refunds-exchanges/new": RefundExchangeCaseCreatePage,
  "/portal": PortalDashboardPage,
  "/portal/actions": PortalActionsPage,
  "/portal/profile": PortalProfilePage,
  "/portal/passengers": PortalPassengersPage,
  "/portal/refunds-exchanges": PortalRefundExchangeCasesPage,
  "/portal/requests": PortalRequestsPage,
  "/portal/requests/new": PortalRequestCreatePage,
  "/portal/offers": PortalOffersPage,
  "/portal/bookings": PortalBookingsPage,
  "/portal/documents": PortalDocumentsPage,
  "/portal/invoices": PortalInvoicesPage,
  "/portal/payments": PortalPaymentsPage,
}

export default function App() {
  const publicWebsiteRequestMatch = window.location.pathname.match(/^\/site\/([^/]+)\/request$/)
  if (publicWebsiteRequestMatch) {
    return <PublicAgencyWebsitePage slug={publicWebsiteRequestMatch[1]} requestMode />
  }

  const publicWebsitePageMatch = window.location.pathname.match(/^\/site\/([^/]+)\/([^/]+)$/)
  if (publicWebsitePageMatch) {
    return <PublicAgencyWebsitePage slug={publicWebsitePageMatch[1]} pageSlug={publicWebsitePageMatch[2]} />
  }

  const publicWebsiteMatch = window.location.pathname.match(/^\/site\/([^/]+)$/)
  if (publicWebsiteMatch) {
    return <PublicAgencyWebsitePage slug={publicWebsiteMatch[1]} />
  }

  if (window.location.pathname === "/agency/requests/new") {
    return <RequestCreatePage />
  }

  if (window.location.pathname === "/agency/offers/new") {
    return <OfferCreatePage />
  }

  if (window.location.pathname === "/agency/bookings/new") {
    return <BookingCreatePage />
  }

  if (window.location.pathname === "/agency/refunds-exchanges") {
    return <RefundExchangeCasesPage />
  }

  if (window.location.pathname === "/agency/refunds-exchanges/new") {
    return <RefundExchangeCaseCreatePage />
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

  const requestIntakeMatch = window.location.pathname.match(/^\/agency\/request-intakes\/([^/]+)$/)
  if (requestIntakeMatch) {
    return <RequestIntakeDetailPage intakeId={requestIntakeMatch[1]} />
  }

  const offerMatch = window.location.pathname.match(/^\/agency\/offers\/([^/]+)$/)
  if (offerMatch) {
    return <OfferDetailPage offerId={offerMatch[1]} />
  }

  const bookingMatch = window.location.pathname.match(/^\/agency\/bookings\/([^/]+)$/)
  if (bookingMatch) {
    return <BookingDetailPage bookingId={bookingMatch[1]} />
  }

  const refundExchangeMatch = window.location.pathname.match(/^\/agency\/refunds-exchanges\/([^/]+)$/)
  if (refundExchangeMatch) {
    return <RefundExchangeCaseDetailPage caseId={refundExchangeMatch[1]} />
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

  const documentMatch = window.location.pathname.match(/^\/agency\/documents\/([^/]+)$/)
  if (documentMatch) {
    return <DocumentDetailPage documentId={documentMatch[1]} />
  }

  const platformAirlineMatch = window.location.pathname.match(/^\/platform\/airlines\/([^/]+)$/)
  if (platformAirlineMatch) {
    return <AirlineDetailPage airlineId={platformAirlineMatch[1]} />
  }

  const platformKnowledgeMatch = window.location.pathname.match(/^\/platform\/airline-knowledge\/([^/]+)$/)
  if (platformKnowledgeMatch) {
    return <AirlineKnowledgeDetailPage knowledgeId={platformKnowledgeMatch[1]} />
  }

  const platformAgencyMatch = window.location.pathname.match(/^\/platform\/agencies\/([^/]+)$/)
  if (platformAgencyMatch) {
    return <PlatformAgencyDetailPage agencyId={platformAgencyMatch[1]} />
  }

  const platformReferenceRecordMatch = window.location.pathname.match(/^\/platform\/reference\/records\/([^/]+)$/)
  if (platformReferenceRecordMatch) {
    return <PlatformReferenceDataPage recordId={platformReferenceRecordMatch[1]} />
  }

  const portalPassengerMatch = window.location.pathname.match(/^\/portal\/passengers\/([^/]+)$/)
  if (portalPassengerMatch) {
    return <PortalPassengerDetailPage passengerId={portalPassengerMatch[1]} />
  }

  if (window.location.pathname === "/portal/requests/new") {
    return <PortalRequestCreatePage />
  }

  if (window.location.pathname === "/portal/refunds-exchanges") {
    return <PortalRefundExchangeCasesPage />
  }

  const portalRequestMatch = window.location.pathname.match(/^\/portal\/requests\/([^/]+)$/)
  if (portalRequestMatch) {
    return <PortalRequestDetailPage requestId={portalRequestMatch[1]} />
  }

  const portalOfferMatch = window.location.pathname.match(/^\/portal\/offers\/([^/]+)$/)
  if (portalOfferMatch) {
    return <PortalOfferDetailPage offerId={portalOfferMatch[1]} />
  }

  const portalBookingMatch = window.location.pathname.match(/^\/portal\/bookings\/([^/]+)$/)
  if (portalBookingMatch) {
    return <PortalBookingDetailPage bookingId={portalBookingMatch[1]} />
  }

  const portalRefundExchangeMatch = window.location.pathname.match(/^\/portal\/refunds-exchanges\/([^/]+)$/)
  if (portalRefundExchangeMatch) {
    return <PortalRefundExchangeCaseDetailPage caseId={portalRefundExchangeMatch[1]} />
  }

  const portalDocumentMatch = window.location.pathname.match(/^\/portal\/documents\/([^/]+)$/)
  if (portalDocumentMatch) {
    return <PortalDocumentDetailPage documentId={portalDocumentMatch[1]} />
  }

  const portalInvoiceMatch = window.location.pathname.match(/^\/portal\/invoices\/([^/]+)$/)
  if (portalInvoiceMatch) {
    return <PortalInvoiceDetailPage invoiceId={portalInvoiceMatch[1]} />
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
