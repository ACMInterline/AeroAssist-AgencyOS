import { lazy } from "react"
import NotFoundPage from "../components/NotFoundPage"
const AgencySettingsPage = lazy(() => import("../pages/agency/AgencySettingsPage"))
const AgencyOnboardingPage = lazy(() => import("../pages/agency/AgencyOnboardingPage"))
const PilotFeedbackPage = lazy(() => import("../pages/agency/PilotFeedbackPage"))
const AssignedBundlesPage = lazy(() => import("../pages/agency/AssignedBundlesPage"))
const BundleRolloutReadinessPage = lazy(() => import("../pages/agency/BundleRolloutReadinessPage"))
const BundleDependenciesPage = lazy(() => import("../pages/agency/BundleDependenciesPage"))
const CapabilitiesPage = lazy(() => import("../pages/agency/CapabilitiesPage"))
const AgencyRolloutDashboardPage = lazy(() => import("../pages/agency/RolloutDashboardPage"))
const RolloutApprovalPage = lazy(() => import("../pages/agency/RolloutApprovalPage"))
const RolloutChangeRequestsPage = lazy(() => import("../pages/agency/RolloutChangeRequestsPage"))
const RolloutDecisionsPage = lazy(() => import("../pages/agency/RolloutDecisionsPage"))
const RolloutIssuesPage = lazy(() => import("../pages/agency/RolloutIssuesPage"))
const RolloutPlansPage = lazy(() => import("../pages/agency/RolloutPlansPage"))
const RolloutRisksPage = lazy(() => import("../pages/agency/RolloutRisksPage"))
const RolloutRollbackPlansPage = lazy(() => import("../pages/agency/RolloutRollbackPlansPage"))
const RolloutSchedulePage = lazy(() => import("../pages/agency/RolloutSchedulePage"))
const RolloutSummaryPacksPage = lazy(() => import("../pages/agency/RolloutSummaryPacksPage"))
const RolloutTimelinePage = lazy(() => import("../pages/agency/RolloutTimelinePage"))
const TimelinePage = lazy(() => import("../pages/agency/TimelinePage"))
const WorkflowEnginePage = lazy(() => import("../pages/agency/WorkflowEnginePage"))
const FlightWorkspacesPage = lazy(() => import("../pages/agency/FlightWorkspacesPage"))
const TripWorkspacesPage = lazy(() => import("../pages/agency/TripWorkspacesPage"))
const JourneyWorkspacePage = lazy(() => import("../pages/agency/JourneyWorkspacePage"))
const JourneyAuthoringWorkspacePage = lazy(() => import("../pages/agency/JourneyAuthoringWorkspacePage"))
const JourneyOptionCompositionWorkspacePage = lazy(() => import("../pages/agency/JourneyOptionCompositionWorkspacePage"))
const JourneyComparisonPresentationWorkspacePage = lazy(() => import("../pages/agency/JourneyComparisonPresentationWorkspacePage"))
const OfferDeliveryContextPage = lazy(() => import("../pages/agency/OfferDeliveryContextPage"))
const TravelRequestsPage = lazy(() => import("../pages/agency/TravelRequestsPage"))
const TravelWorkspacesPage = lazy(() => import("../pages/agency/TravelWorkspacesPage"))
const AirlineIntelligenceDetailPage = lazy(() => import("../pages/agency/AirlineIntelligenceDetailPage"))
const AirlineIntelligenceCoveragePage = lazy(() => import("../pages/agency/AirlineIntelligenceCoveragePage"))
const AgencyAirlineIntelligenceConsumptionPage = lazy(() => import("../pages/agency/AirlineIntelligenceConsumptionPage"))
const AgencyAirlineIntelligenceKnowledgeVersionsPage = lazy(() => import("../pages/agency/AirlineIntelligenceKnowledgeVersionsPage"))
const AirlineIntelligenceReviewCoveragePage = lazy(() => import("../pages/agency/AirlineIntelligenceReviewCoveragePage"))
const AirlineIntelligencePage = lazy(() => import("../pages/agency/AirlineIntelligencePage"))
const AirlineProfilesPage = lazy(() => import("../pages/agency/AirlineProfilesPage"))
const AgencyAirlineEvidencePage = lazy(() => import("../pages/agency/AirlineEvidencePage"))
const AgencyKnowledgeUpdatesPage = lazy(() => import("../pages/agency/KnowledgeUpdatesPage"))
const AgencyAirlineServiceCoveragePage = lazy(() => import("../pages/agency/AirlineServiceCoveragePage"))
const AgencyAirlineDistributionCapabilitiesPage = lazy(() => import("../pages/agency/AirlineDistributionCapabilitiesPage"))
const AgencyInterlineCodeshareAdvisorPage = lazy(() => import("../pages/agency/InterlineCodeshareAdvisorPage"))
const AgencyFareBrandLibraryPage = lazy(() => import("../pages/agency/FareBrandLibraryPage"))
const AgencyAirlineContactDirectoryPage = lazy(() => import("../pages/agency/AirlineContactDirectoryPage"))
const AgencyAirlineIntelligenceReadinessPage = lazy(() => import("../pages/agency/AirlineIntelligenceReadinessPage"))
const AirlineKnowledgeViewPage = lazy(() => import("../pages/agency/AirlineKnowledgeViewPage"))
const CapabilityMatrixPage = lazy(() => import("../pages/agency/CapabilityMatrixPage"))
const KnowledgeAcquisitionPage = lazy(() => import("../pages/agency/KnowledgeAcquisitionPage"))
const KnowledgeGovernancePage = lazy(() => import("../pages/agency/KnowledgeGovernancePage"))
const KnowledgeNormalisationPage = lazy(() => import("../pages/agency/KnowledgeNormalisationPage"))
const IntelligenceCasesPage = lazy(() => import("../pages/agency/IntelligenceCasesPage"))
const OperationalEvaluationsPage = lazy(() => import("../pages/agency/OperationalEvaluationsPage"))
const RecommendationsPage = lazy(() => import("../pages/agency/RecommendationsPage"))
const RequestSegmentServicesPage = lazy(() => import("../pages/agency/RequestSegmentServicesPage"))
const ImportTemplatesPage = lazy(() => import("../pages/agency/ImportTemplatesPage"))
const AgencyReferenceDataEnginePage = lazy(() => import("../pages/agency/ReferenceDataEnginePage"))
const PolicyEditorPage = lazy(() => import("../pages/agency/PolicyEditorPage"))
const AgencyPricingFormulaBuilderPage = lazy(() => import("../pages/agency/PricingFormulaBuilderPage"))
const RuleComposerPage = lazy(() => import("../pages/agency/RuleComposerPage"))
const AgencyKnowledgeQualityAssurancePage = lazy(() => import("../pages/agency/KnowledgeQualityAssurancePage"))
const AgencyPublishedKnowledgePage = lazy(() => import("../pages/agency/PublishedKnowledgePage"))
const AgencyScenarioTestingPage = lazy(() => import("../pages/agency/ScenarioTestingPage"))
const AgencyKnowledgePopulationToolkitPage = lazy(() => import("../pages/agency/KnowledgePopulationToolkitPage"))
const AgencyPilotReadinessPage = lazy(() => import("../pages/agency/PilotReadinessPage"))
const ServiceFeasibilityPage = lazy(() => import("../pages/agency/ServiceFeasibilityPage"))
const ServiceParameterTaxonomiesPage = lazy(() => import("../pages/agency/ServiceParameterTaxonomiesPage"))
const AirlinePolicyLibraryPage = lazy(() => import("../pages/agency/AirlinePolicyLibraryPage"))
const AirlineServiceAdvisorPage = lazy(() => import("../pages/agency/AirlineServiceAdvisorPage"))
const OperationalIntelligencePage = lazy(() => import("../pages/agency/OperationalIntelligencePage"))
const AgencyOperationalConstraintsPage = lazy(() => import("../pages/agency/OperationalConstraintsPage"))
const AgencyOperationalWorkflowsPage = lazy(() => import("../pages/agency/OperationalWorkflowsPage"))
const AgentWorkQueuePage = lazy(() => import("../pages/agency/AgentWorkQueuePage"))
const DeadlinesPage = lazy(() => import("../pages/agency/DeadlinesPage"))
const AgencyTaskAutomationPage = lazy(() => import("../pages/agency/TaskAutomationPage"))
const RequestTripConversionPage = lazy(() => import("../pages/agency/RequestTripConversionPage"))
const BookingHandoffsPage = lazy(() => import("../pages/agency/BookingHandoffsPage"))
const AfterSalesPage = lazy(() => import("../pages/agency/AfterSalesPage"))
const OperationsCommandCenterPage = lazy(() => import("../pages/agency/OperationsCommandCenterPage"))
const AgencyWorkflowMaturityPage = lazy(() => import("../pages/agency/WorkflowMaturityPage"))
const BookingDetailPage = lazy(() => import("../pages/agency/BookingDetailPage"))
const BookingImportsPage = lazy(() => import("../pages/agency/BookingImportsPage"))
const BookingWorkspaceDetailPage = lazy(() => import("../pages/agency/BookingWorkspaceDetailPage"))
const BookingWorkspaceMetadataPage = lazy(() => import("../pages/agency/BookingWorkspaceMetadataPage"))
const BookingWorkspacesPage = lazy(() => import("../pages/agency/BookingWorkspacesPage"))
const BookingsPage = lazy(() => import("../pages/agency/BookingsPage"))
const AgencyClientMasterPage = lazy(() => import("../pages/agency/ClientMasterPage"))
const ClientDetailPage = lazy(() => import("../pages/agency/ClientDetailPage"))
const ClientsPage = lazy(() => import("../pages/agency/ClientsPage"))
const DocumentDetailPage = lazy(() => import("../pages/agency/DocumentDetailPage"))
const DocumentStoragePage = lazy(() => import("../pages/agency/DocumentStoragePage"))
const DocumentTemplatesPage = lazy(() => import("../pages/agency/DocumentTemplatesPage"))
const DocumentsPage = lazy(() => import("../pages/agency/DocumentsPage"))
const DocumentWorkspacesPage = lazy(() => import("../pages/agency/DocumentWorkspacesPage"))
const EmdDetailPage = lazy(() => import("../pages/agency/EmdDetailPage"))
const EmdWorkspaceMetadataPage = lazy(() => import("../pages/agency/EmdWorkspaceMetadataPage"))
const InvoiceDetailPage = lazy(() => import("../pages/agency/InvoiceDetailPage"))
const InvoicesPage = lazy(() => import("../pages/agency/InvoicesPage"))
const FinanceDashboardPage = lazy(() => import("../pages/agency/FinanceDashboardPage"))
const SupplierCostsPage = lazy(() => import("../pages/agency/SupplierCostsPage"))
const OfferCreatePage = lazy(() => import("../pages/agency/OfferCreatePage"))
const OfferBuilderPage = lazy(() => import("../pages/agency/OfferBuilderPage"))
const OfferIntelligencePage = lazy(() => import("../pages/agency/OfferIntelligencePage"))
const AgencyOfferDecisionExportAuditReviewsPage = lazy(() => import("../pages/agency/OfferDecisionExportAuditReviewsPage"))
const AgencyOfferDecisionExportCompliancePage = lazy(() => import("../pages/agency/OfferDecisionExportCompliancePage"))
const AgencyOfferDecisionExportDeliveriesPage = lazy(() => import("../pages/agency/OfferDecisionExportDeliveriesPage"))
const AgencyOfferDecisionExportDeliveryOutcomesPage = lazy(() => import("../pages/agency/OfferDecisionExportDeliveryOutcomesPage"))
const AgencyOfferDecisionExportGovernancePage = lazy(() => import("../pages/agency/OfferDecisionExportGovernancePage"))
const AgencyOfferDecisionExportPreviewsPage = lazy(() => import("../pages/agency/OfferDecisionExportPreviewsPage"))
const AgencyOfferDecisionExportReleasesPage = lazy(() => import("../pages/agency/OfferDecisionExportReleasesPage"))
const AgencyOfferDecisionExportsPage = lazy(() => import("../pages/agency/OfferDecisionExportsPage"))
const AgencyOfferDecisionExplanationsPage = lazy(() => import("../pages/agency/OfferDecisionExplanationsPage"))
const AgencyOfferDecisionPacksPage = lazy(() => import("../pages/agency/OfferDecisionPacksPage"))
const AgencyOfferPolicyAdvisorPage = lazy(() => import("../pages/agency/OfferPolicyAdvisorPage"))
const OfferWorkspaceDetailPage = lazy(() => import("../pages/agency/OfferWorkspaceDetailPage"))
const OfferWorkspaceMetadataPage = lazy(() => import("../pages/agency/OfferWorkspaceMetadataPage"))
const OfferWorkspacesPage = lazy(() => import("../pages/agency/OfferWorkspacesPage"))
const RefundExchangeCaseCreatePage = lazy(() => import("../pages/agency/RefundExchangeCaseCreatePage"))
const RefundExchangeCaseDetailPage = lazy(() => import("../pages/agency/RefundExchangeCaseDetailPage"))
const RefundExchangeCasesPage = lazy(() => import("../pages/agency/RefundExchangeCasesPage"))
const ReferenceDataPage = lazy(() => import("../pages/agency/ReferenceDataPage"))
const FeatureAvailabilityPage = lazy(() => import("../pages/agency/FeatureAvailabilityPage"))
const FeatureBundlesPage = lazy(() => import("../pages/agency/FeatureBundlesPage"))
const FeatureReadinessPage = lazy(() => import("../pages/agency/FeatureReadinessPage"))
const FormProfilesPage = lazy(() => import("../pages/agency/FormProfilesPage"))
const GdsParserPage = lazy(() => import("../pages/agency/GdsParserPage"))
const AgencyAncillaryPricingPage = lazy(() => import("../pages/agency/AncillaryPricingPage"))
const AgencyPolicyComparisonPage = lazy(() => import("../pages/agency/PolicyComparisonPage"))
const AgencyServiceMechanicsPage = lazy(() => import("../pages/agency/ServiceMechanicsPage"))
const AgencyServiceTaxonomyPage = lazy(() => import("../pages/agency/ServiceTaxonomyPage"))
const SpecialServicesPage = lazy(() => import("../pages/agency/SpecialServicesPage"))
const PassengerDetailPage = lazy(() => import("../pages/agency/PassengerDetailPage"))
const AgencyPassengerMasterPage = lazy(() => import("../pages/agency/PassengerMasterPage"))
const PassengerWorkspacesPage = lazy(() => import("../pages/agency/PassengerWorkspacesPage"))
const PassengerServicesPage = lazy(() => import("../pages/agency/PassengerServicesPage"))
const PassengersPage = lazy(() => import("../pages/agency/PassengersPage"))
const PaymentsPage = lazy(() => import("../pages/agency/PaymentsPage"))
const AgencyPortalActionsPage = lazy(() => import("../pages/agency/PortalActionsPage"))
const RequestCreatePage = lazy(() => import("../pages/agency/RequestCreatePage"))
const RequestDetailPage = lazy(() => import("../pages/agency/RequestDetailPage"))
const RequestIntakeDetailPage = lazy(() => import("../pages/agency/RequestIntakeDetailPage"))
const RequestIntakesListPage = lazy(() => import("../pages/agency/RequestIntakesListPage"))
const RequestsPage = lazy(() => import("../pages/agency/RequestsPage"))
const SaaSSubscriptionPage = lazy(() => import("../pages/agency/SaaSSubscriptionPage"))
const TripCreatePage = lazy(() => import("../pages/agency/TripCreatePage"))
const TripDetailPage = lazy(() => import("../pages/agency/TripDetailPage"))
const TripsPage = lazy(() => import("../pages/agency/TripsPage"))
const TicketDetailPage = lazy(() => import("../pages/agency/TicketDetailPage"))
const TicketWorkspaceMetadataPage = lazy(() => import("../pages/agency/TicketWorkspaceMetadataPage"))
const TicketsEmdsPage = lazy(() => import("../pages/agency/TicketsEmdsPage"))
const WebsiteBuilderPage = lazy(() => import("../pages/agency/WebsiteBuilderPage"))
const WebsiteMediaLibraryPage = lazy(() => import("../pages/agency/WebsiteMediaLibraryPage"))
const LoginPage = lazy(() => import("../pages/auth/LoginPage"))
const InviteAcceptPage = lazy(() => import("../pages/auth/InviteAcceptPage"))
const AirlineDetailPage = lazy(() => import("../pages/platform/AirlineDetailPage"))
const AirlineIntelligenceDataPacksPage = lazy(() => import("../pages/platform/AirlineIntelligenceDataPacksPage"))
const AirlineIntelligenceDataPackReviewsPage = lazy(() => import("../pages/platform/AirlineIntelligenceDataPackReviewsPage"))
const AirlineCapabilityMatrixPage = lazy(() => import("../pages/platform/AirlineCapabilityMatrixPage"))
const AirlineKnowledgeAcquisitionPage = lazy(() => import("../pages/platform/AirlineKnowledgeAcquisitionPage"))
const AirlineKnowledgeGovernancePage = lazy(() => import("../pages/platform/AirlineKnowledgeGovernancePage"))
const AirlineKnowledgeNormalisationPage = lazy(() => import("../pages/platform/AirlineKnowledgeNormalisationPage"))
const AirlineOperationalIntelligencePage = lazy(() => import("../pages/platform/AirlineOperationalIntelligencePage"))
const PlatformAirlineRecommendationsPage = lazy(() => import("../pages/platform/AirlineRecommendationsPage"))
const PlatformOperationalIntelligenceCasesPage = lazy(() => import("../pages/platform/OperationalIntelligenceCasesPage"))
const PlatformOperationalEvaluationsPage = lazy(() => import("../pages/platform/OperationalEvaluationsPage"))
const PlatformPassengerServiceFeasibilityPage = lazy(() => import("../pages/platform/PassengerServiceFeasibilityPage"))
const PlatformOperationalConstraintsPage = lazy(() => import("../pages/platform/OperationalConstraintsPage"))
const PlatformOperationalWorkflowsPage = lazy(() => import("../pages/platform/OperationalWorkflowsPage"))
const PlatformWorkQueueGovernancePage = lazy(() => import("../pages/platform/WorkQueueGovernancePage"))
const PlatformSlaPoliciesPage = lazy(() => import("../pages/platform/SlaPoliciesPage"))
const PlatformTaskAutomationPage = lazy(() => import("../pages/platform/TaskAutomationPage"))
const PlatformRequestTripConversionDiagnosticsPage = lazy(() => import("../pages/platform/RequestTripConversionDiagnosticsPage"))
const PlatformBookingHandoffDiagnosticsPage = lazy(() => import("../pages/platform/BookingHandoffDiagnosticsPage"))
const PlatformAfterSalesDiagnosticsPage = lazy(() => import("../pages/platform/AfterSalesDiagnosticsPage"))
const PlatformOperationsGovernancePage = lazy(() => import("../pages/platform/OperationsGovernancePage"))
const PlatformWorkflowMaturityPage = lazy(() => import("../pages/platform/WorkflowMaturityPage"))
const PlatformRequestSegmentServicesPage = lazy(() => import("../pages/platform/RequestSegmentServicesPage"))
const PlatformKnowledgeImportTemplatesPage = lazy(() => import("../pages/platform/KnowledgeImportTemplatesPage"))
const PlatformReferenceDataEnginePage = lazy(() => import("../pages/platform/ReferenceDataEnginePage"))
const PlatformServiceParameterTaxonomiesPage = lazy(() => import("../pages/platform/ServiceParameterTaxonomiesPage"))
const PlatformVisualPolicyEditorPage = lazy(() => import("../pages/platform/VisualPolicyEditorPage"))
const PlatformPricingFormulaBuilderPage = lazy(() => import("../pages/platform/PricingFormulaBuilderPage"))
const PlatformOperationalRuleComposerPage = lazy(() => import("../pages/platform/OperationalRuleComposerPage"))
const PlatformKnowledgeQualityAssurancePage = lazy(() => import("../pages/platform/KnowledgeQualityAssurancePage"))
const PlatformAirlineKnowledgePublishingPage = lazy(() => import("../pages/platform/AirlineKnowledgePublishingPage"))
const PlatformOperationalScenarioTestingPage = lazy(() => import("../pages/platform/OperationalScenarioTestingPage"))
const PlatformKnowledgePopulationToolkitPage = lazy(() => import("../pages/platform/KnowledgePopulationToolkitPage"))
const PlatformPilotReadinessPage = lazy(() => import("../pages/platform/PilotReadinessPage"))
const PlatformPilotOperationsReadinessPage = lazy(() => import("../pages/platform/PilotOperationsReadinessPage"))
const CommercialPilotReadinessPage = lazy(() => import("../pages/platform/CommercialPilotReadinessPage"))
const PilotFeedbackReviewPage = lazy(() => import("../pages/platform/PilotFeedbackReviewPage"))
const PlatformAirlineIntelligenceAgencyConsumptionPage = lazy(() => import("../pages/platform/AirlineIntelligenceAgencyConsumptionPage"))
const PlatformAirlineIntelligenceKnowledgeVersionsPage = lazy(() => import("../pages/platform/AirlineIntelligenceKnowledgeVersionsPage"))
const AirlineKnowledgeDetailPage = lazy(() => import("../pages/platform/AirlineKnowledgeDetailPage"))
const AirlinePolicyIngestionPage = lazy(() => import("../pages/platform/AirlinePolicyIngestionPage"))
const AirlinesPage = lazy(() => import("../pages/platform/AirlinesPage"))
const AirlineMasterProfilesPage = lazy(() => import("../pages/platform/AirlineMasterProfilesPage"))
const PlatformAirlineEvidencePage = lazy(() => import("../pages/platform/AirlineEvidencePage"))
const PlatformAirlineKnowledgeVersionsPage = lazy(() => import("../pages/platform/AirlineKnowledgeVersionsPage"))
const PlatformAirlineServiceCoveragePage = lazy(() => import("../pages/platform/AirlineServiceCoveragePage"))
const PlatformAirlineDistributionCapabilitiesPage = lazy(() => import("../pages/platform/AirlineDistributionCapabilitiesPage"))
const PlatformInterlineCodeshareIntelligencePage = lazy(() => import("../pages/platform/InterlineCodeshareIntelligencePage"))
const PlatformFareBrandIntelligencePage = lazy(() => import("../pages/platform/FareBrandIntelligencePage"))
const PlatformAirlineContactIntelligencePage = lazy(() => import("../pages/platform/AirlineContactIntelligencePage"))
const PlatformAirlineIntelligenceReadinessPage = lazy(() => import("../pages/platform/AirlineIntelligenceReadinessPage"))
const PlatformAgenciesPage = lazy(() => import("../pages/platform/PlatformAgenciesPage"))
const PlatformAncillaryPricingPage = lazy(() => import("../pages/platform/AncillaryPricingPage"))
const PlatformAgencyDetailPage = lazy(() => import("../pages/platform/PlatformAgencyDetailPage"))
const PlatformBlueprintPage = lazy(() => import("../pages/platform/PlatformBlueprintPage"))
const PlatformCapabilityCatalogPage = lazy(() => import("../pages/platform/CapabilityCatalogPage"))
const PlatformClientMasterPage = lazy(() => import("../pages/platform/ClientMasterPage"))
const PlatformDashboardPage = lazy(() => import("../pages/platform/PlatformDashboardPage"))
const PlatformDocumentWorkspacesPage = lazy(() => import("../pages/platform/DocumentWorkspacesPage"))
const PlatformDocumentTemplatesPage = lazy(() => import("../pages/platform/PlatformDocumentTemplatesPage"))
const PlatformFeatureBundleDependenciesPage = lazy(() => import("../pages/platform/FeatureBundleDependenciesPage"))
const PlatformFeatureBundleAssignmentsPage = lazy(() => import("../pages/platform/FeatureBundleAssignmentsPage"))
const PlatformFeatureBundleRolloutApprovalsPage = lazy(() => import("../pages/platform/FeatureBundleRolloutApprovalsPage"))
const PlatformFeatureBundleRolloutChangeRequestsPage = lazy(() => import("../pages/platform/FeatureBundleRolloutChangeRequestsPage"))
const PlatformFeatureBundleRolloutDecisionsPage = lazy(() => import("../pages/platform/FeatureBundleRolloutDecisionsPage"))
const PlatformFeatureBundleRolloutIssuesPage = lazy(() => import("../pages/platform/FeatureBundleRolloutIssuesPage"))
const PlatformFeatureBundleRolloutPlansPage = lazy(() => import("../pages/platform/FeatureBundleRolloutPlansPage"))
const PlatformFeatureBundleRolloutReadinessPage = lazy(() => import("../pages/platform/FeatureBundleRolloutReadinessPage"))
const PlatformFeatureBundleRolloutRisksPage = lazy(() => import("../pages/platform/FeatureBundleRolloutRisksPage"))
const PlatformFeatureBundleRolloutRollbackPlansPage = lazy(() => import("../pages/platform/FeatureBundleRolloutRollbackPlansPage"))
const PlatformFeatureBundleRolloutSchedulePage = lazy(() => import("../pages/platform/FeatureBundleRolloutSchedulePage"))
const PlatformFeatureBundleRolloutSummaryPacksPage = lazy(() => import("../pages/platform/FeatureBundleRolloutSummaryPacksPage"))
const PlatformFeatureBundleRolloutTimelinePage = lazy(() => import("../pages/platform/FeatureBundleRolloutTimelinePage"))
const PlatformFlightWorkspacesPage = lazy(() => import("../pages/platform/FlightWorkspacesPage"))
const PlatformBookingWorkspacesPage = lazy(() => import("../pages/platform/BookingWorkspacesPage"))
const PlatformOfferWorkspacesPage = lazy(() => import("../pages/platform/OfferWorkspacesPage"))
const PlatformPassengerMasterPage = lazy(() => import("../pages/platform/PassengerMasterPage"))
const PlatformOperationalTimelinesPage = lazy(() => import("../pages/platform/OperationalTimelinesPage"))
const PlatformOperationalTravelWorkspacesPage = lazy(() => import("../pages/platform/OperationalTravelWorkspacesPage"))
const PlatformPassengerServiceWorkflowsPage = lazy(() => import("../pages/platform/PassengerServiceWorkflowsPage"))
const PlatformPassengerWorkspacesPage = lazy(() => import("../pages/platform/PassengerWorkspacesPage"))
const PlatformSsrOsiWorkspacesPage = lazy(() => import("../pages/platform/SsrOsiWorkspacesPage"))
const PlatformTicketWorkspacesPage = lazy(() => import("../pages/platform/TicketWorkspacesPage"))
const PlatformEmdWorkspacesPage = lazy(() => import("../pages/platform/EmdWorkspacesPage"))
const PlatformTripWorkspacesPage = lazy(() => import("../pages/platform/TripWorkspacesPage"))
const PlatformJourneyEnginePage = lazy(() => import("../pages/platform/JourneyEnginePage"))
const PlatformJourneyAuthoringDiagnosticsPage = lazy(() => import("../pages/platform/JourneyAuthoringDiagnosticsPage"))
const PlatformJourneyOptionCompositionDiagnosticsPage = lazy(() => import("../pages/platform/JourneyOptionCompositionDiagnosticsPage"))
const PlatformJourneyComparisonPresentationDiagnosticsPage = lazy(() => import("../pages/platform/JourneyComparisonPresentationDiagnosticsPage"))
const PlatformOfferDeliveryDiagnosticsPage = lazy(() => import("../pages/platform/OfferDeliveryDiagnosticsPage"))
const PlatformTravelRequestWorkspacesPage = lazy(() => import("../pages/platform/TravelRequestWorkspacesPage"))
const PlatformRolloutDashboardPage = lazy(() => import("../pages/platform/RolloutDashboardPage"))
const PlatformFeatureFlagAuditPage = lazy(() => import("../pages/platform/FeatureFlagAuditPage"))
const PlatformFeatureFlagBundlesPage = lazy(() => import("../pages/platform/FeatureFlagBundlesPage"))
const PlatformFeatureFlagsPage = lazy(() => import("../pages/platform/FeatureFlagsPage"))
const PlatformGdsParserPage = lazy(() => import("../pages/platform/PlatformGdsParserPage"))
const PlatformOfferDecisionExportAuditReviewsPage = lazy(() => import("../pages/platform/OfferDecisionExportAuditReviewsPage"))
const PlatformOfferDecisionExportCompliancePage = lazy(() => import("../pages/platform/OfferDecisionExportCompliancePage"))
const PlatformOfferDecisionExportDeliveriesPage = lazy(() => import("../pages/platform/OfferDecisionExportDeliveriesPage"))
const PlatformOfferDecisionExportDeliveryOutcomesPage = lazy(() => import("../pages/platform/OfferDecisionExportDeliveryOutcomesPage"))
const PlatformOfferDecisionExportGovernancePage = lazy(() => import("../pages/platform/OfferDecisionExportGovernancePage"))
const PlatformOfferDecisionExportPreviewsPage = lazy(() => import("../pages/platform/OfferDecisionExportPreviewsPage"))
const PlatformOfferDecisionExportReleasesPage = lazy(() => import("../pages/platform/OfferDecisionExportReleasesPage"))
const PlatformOfferDecisionExportsPage = lazy(() => import("../pages/platform/OfferDecisionExportsPage"))
const PlatformOfferDecisionExplanationsPage = lazy(() => import("../pages/platform/OfferDecisionExplanationsPage"))
const PlatformOfferDecisionPacksPage = lazy(() => import("../pages/platform/OfferDecisionPacksPage"))
const PlatformIntelligentOfferBuilderPage = lazy(() => import("../pages/platform/IntelligentOfferBuilderPage"))
const PlatformOfferPolicyAdvisorPage = lazy(() => import("../pages/platform/OfferPolicyAdvisorPage"))
const PlatformPolicyComparisonPage = lazy(() => import("../pages/platform/PolicyComparisonPage"))
const PlatformReferenceDataPage = lazy(() => import("../pages/platform/PlatformReferenceDataPage"))
const PlatformRulesServicesPage = lazy(() => import("../pages/platform/PlatformRulesServicesPage"))
const PlatformSaaSSubscriptionsPage = lazy(() => import("../pages/platform/SaaSSubscriptionsPage"))
const PlatformServiceMechanicsPage = lazy(() => import("../pages/platform/ServiceMechanicsPage"))
const PlatformServiceTaxonomyPage = lazy(() => import("../pages/platform/ServiceTaxonomyPage"))
const PortalBookingDetailPage = lazy(() => import("../pages/portal/PortalBookingDetailPage"))
const PortalActionsPage = lazy(() => import("../pages/portal/PortalActionsPage"))
const PortalBookingsPage = lazy(() => import("../pages/portal/PortalBookingsPage"))
const PortalDashboardPage = lazy(() => import("../pages/portal/PortalDashboardPage"))
const PortalDocumentDetailPage = lazy(() => import("../pages/portal/PortalDocumentDetailPage"))
const PortalDocumentsPage = lazy(() => import("../pages/portal/PortalDocumentsPage"))
const PortalInvoiceDetailPage = lazy(() => import("../pages/portal/PortalInvoiceDetailPage"))
const PortalInvoicesPage = lazy(() => import("../pages/portal/PortalInvoicesPage"))
const PortalOfferDetailPage = lazy(() => import("../pages/portal/PortalOfferDetailPage"))
const PortalOfferDeliveriesPage = lazy(() => import("../pages/portal/PortalOfferDeliveriesPage"))
const PortalOfferDeliveryDetailPage = lazy(() => import("../pages/portal/PortalOfferDeliveryDetailPage"))
const PortalPassengerDetailPage = lazy(() => import("../pages/portal/PortalPassengerDetailPage"))
const PortalPassengersPage = lazy(() => import("../pages/portal/PortalPassengersPage"))
const PortalPaymentsPage = lazy(() => import("../pages/portal/PortalPaymentsPage"))
const PortalProfilePage = lazy(() => import("../pages/portal/PortalProfilePage"))
const PortalRequestDetailPage = lazy(() => import("../pages/portal/PortalRequestDetailPage"))
const PortalRequestCreatePage = lazy(() => import("../pages/portal/PortalRequestCreatePage"))
const PortalRequestsPage = lazy(() => import("../pages/portal/PortalRequestsPage"))
const PortalRefundExchangeCaseDetailPage = lazy(() => import("../pages/portal/PortalRefundExchangeCaseDetailPage"))
const PortalRefundExchangeCasesPage = lazy(() => import("../pages/portal/PortalRefundExchangeCasesPage"))
const PortalApprovalsPage = lazy(() => import("../pages/portal/PortalApprovalsPage"))
const PortalAssistancePage = lazy(() => import("../pages/portal/PortalAssistancePage"))
const PortalCommunicationDetailPage = lazy(() => import("../pages/portal/PortalCommunicationDetailPage"))
const PortalCommunicationsPage = lazy(() => import("../pages/portal/PortalCommunicationsPage"))
const PortalEmdDetailPage = lazy(() => import("../pages/portal/PortalEmdDetailPage"))
const PortalEmdsPage = lazy(() => import("../pages/portal/PortalEmdsPage"))
const PortalFinancePage = lazy(() => import("../pages/portal/PortalFinancePage"))
const PortalNotificationsPage = lazy(() => import("../pages/portal/PortalNotificationsPage"))
const PortalTicketDetailPage = lazy(() => import("../pages/portal/PortalTicketDetailPage"))
const PortalTicketsPage = lazy(() => import("../pages/portal/PortalTicketsPage"))
const PortalTimelinePage = lazy(() => import("../pages/portal/PortalTimelinePage"))
const PortalTripDetailPage = lazy(() => import("../pages/portal/PortalTripDetailPage"))
const PortalTripsPage = lazy(() => import("../pages/portal/PortalTripsPage"))
const HomePage = lazy(() => import("../pages/public/HomePage"))
const PublicAgencyWebsitePage = lazy(() => import("../pages/public/PublicAgencyWebsitePage"))
const CommunicationsPage = lazy(() => import("../pages/agency/CommunicationsPage"))
const ReportsPage = lazy(() => import("../pages/agency/ReportsPage"))
const PlatformUsersPage = lazy(() => import("../pages/platform/PlatformUsersPage"))
const PlatformAuditPage = lazy(() => import("../pages/platform/PlatformAuditPage"))
const PlatformSettingsPage = lazy(() => import("../pages/platform/PlatformSettingsPage"))

const routes = {
  "/": HomePage,
  "/invite/accept": InviteAcceptPage,
  "/login": LoginPage,
  "/platform": PlatformDashboardPage,
  "/platform/users": PlatformUsersPage,
  "/platform/monitoring": PlatformPilotOperationsReadinessPage,
  "/platform/audit": PlatformAuditPage,
  "/platform/settings": PlatformSettingsPage,
  "/platform/saas-subscriptions": PlatformSaaSSubscriptionsPage,
  "/platform/feature-flags": PlatformFeatureFlagsPage,
  "/platform/feature-flag-audit": PlatformFeatureFlagAuditPage,
  "/platform/feature-flag-bundles": PlatformFeatureFlagBundlesPage,
  "/platform/feature-bundle-assignments": PlatformFeatureBundleAssignmentsPage,
  "/platform/feature-bundle-dependencies": PlatformFeatureBundleDependenciesPage,
  "/platform/feature-bundle-rollout-readiness": PlatformFeatureBundleRolloutReadinessPage,
  "/platform/feature-bundle-rollout-plans": PlatformFeatureBundleRolloutPlansPage,
  "/platform/feature-bundle-rollout-approvals": PlatformFeatureBundleRolloutApprovalsPage,
  "/platform/feature-bundle-rollout-change-requests": PlatformFeatureBundleRolloutChangeRequestsPage,
  "/platform/feature-bundle-rollout-decisions": PlatformFeatureBundleRolloutDecisionsPage,
  "/platform/feature-bundle-rollout-issues": PlatformFeatureBundleRolloutIssuesPage,
  "/platform/feature-bundle-rollout-risks": PlatformFeatureBundleRolloutRisksPage,
  "/platform/feature-bundle-rollout-rollback-plans": PlatformFeatureBundleRolloutRollbackPlansPage,
  "/platform/feature-bundle-rollout-schedule": PlatformFeatureBundleRolloutSchedulePage,
  "/platform/feature-bundle-rollout-summary-packs": PlatformFeatureBundleRolloutSummaryPacksPage,
  "/platform/feature-bundle-rollout-timeline": PlatformFeatureBundleRolloutTimelinePage,
  "/platform/operational-travel-workspaces": PlatformOperationalTravelWorkspacesPage,
  "/platform/travel-request-workspaces": PlatformTravelRequestWorkspacesPage,
  "/platform/passenger-workspaces": PlatformPassengerWorkspacesPage,
  "/platform/flight-workspaces": PlatformFlightWorkspacesPage,
  "/platform/trip-workspaces": PlatformTripWorkspacesPage,
  "/platform/journey-engine": PlatformJourneyEnginePage,
  "/platform/journey-authoring": PlatformJourneyAuthoringDiagnosticsPage,
  "/platform/journey-option-compositions": PlatformJourneyOptionCompositionDiagnosticsPage,
  "/platform/journey-comparison-presentations": PlatformJourneyComparisonPresentationDiagnosticsPage,
  "/platform/offer-delivery-diagnostics": PlatformOfferDeliveryDiagnosticsPage,
  "/platform/offer-workspaces": PlatformOfferWorkspacesPage,
  "/platform/booking-workspaces": PlatformBookingWorkspacesPage,
  "/platform/ticket-workspaces": PlatformTicketWorkspacesPage,
  "/platform/emd-workspaces": PlatformEmdWorkspacesPage,
  "/platform/ssr-osi-workspaces": PlatformSsrOsiWorkspacesPage,
  "/platform/document-workspaces": PlatformDocumentWorkspacesPage,
  "/platform/operational-timelines": PlatformOperationalTimelinesPage,
  "/platform/operational-workflows": PlatformOperationalWorkflowsPage,
  "/platform/work-queues": PlatformWorkQueueGovernancePage,
  "/platform/sla-policies": PlatformSlaPoliciesPage,
  "/platform/task-automation": PlatformTaskAutomationPage,
  "/platform/request-trip-conversion": PlatformRequestTripConversionDiagnosticsPage,
  "/platform/booking-handoffs": PlatformBookingHandoffDiagnosticsPage,
  "/platform/after-sales": PlatformAfterSalesDiagnosticsPage,
  "/platform/operations-governance": PlatformOperationsGovernancePage,
  "/platform/workflow-maturity": PlatformWorkflowMaturityPage,
  "/platform/passenger-service-workflows": PlatformPassengerServiceWorkflowsPage,
  "/platform/rollout-dashboard": PlatformRolloutDashboardPage,
  "/platform/capabilities": PlatformCapabilityCatalogPage,
  "/platform/agencies": PlatformAgenciesPage,
  "/platform/blueprint": PlatformBlueprintPage,
  "/platform/airlines": AirlinesPage,
  "/platform/airline-master-profiles": AirlineMasterProfilesPage,
  "/platform/airline-evidence": PlatformAirlineEvidencePage,
  "/platform/knowledge-versions": PlatformAirlineKnowledgeVersionsPage,
  "/platform/airline-service-coverage": PlatformAirlineServiceCoveragePage,
  "/platform/airline-distribution-capabilities": PlatformAirlineDistributionCapabilitiesPage,
  "/platform/interline-codeshare-intelligence": PlatformInterlineCodeshareIntelligencePage,
  "/platform/fare-brand-intelligence": PlatformFareBrandIntelligencePage,
  "/platform/airline-contact-intelligence": PlatformAirlineContactIntelligencePage,
  "/platform/airline-intelligence-readiness": PlatformAirlineIntelligenceReadinessPage,
  "/platform/airline-intelligence-data-packs": AirlineIntelligenceDataPacksPage,
  "/platform/airline-intelligence-data-pack-reviews": AirlineIntelligenceDataPackReviewsPage,
  "/platform/airline-intelligence-knowledge-versions": PlatformAirlineIntelligenceKnowledgeVersionsPage,
  "/platform/airline-intelligence-agency-consumption": PlatformAirlineIntelligenceAgencyConsumptionPage,
  "/platform/airline-operational-intelligence": AirlineOperationalIntelligencePage,
  "/platform/airline-knowledge-acquisition": AirlineKnowledgeAcquisitionPage,
  "/platform/operational-constraints": PlatformOperationalConstraintsPage,
  "/platform/airline-knowledge-normalisation": AirlineKnowledgeNormalisationPage,
  "/platform/airline-knowledge-governance": AirlineKnowledgeGovernancePage,
  "/platform/airline-knowledge-releases": AirlineKnowledgeGovernancePage,
  "/platform/airline-capability-matrix": AirlineCapabilityMatrixPage,
  "/platform/operational-evaluations": PlatformOperationalEvaluationsPage,
  "/platform/passenger-service-feasibility": PlatformPassengerServiceFeasibilityPage,
  "/platform/airline-recommendations": PlatformAirlineRecommendationsPage,
  "/platform/operational-intelligence-cases": PlatformOperationalIntelligenceCasesPage,
  "/platform/reference-data-engine": PlatformReferenceDataEnginePage,
  "/platform/knowledge-import-templates": PlatformKnowledgeImportTemplatesPage,
  "/platform/visual-policy-editor": PlatformVisualPolicyEditorPage,
  "/platform/pricing-formula-builder": PlatformPricingFormulaBuilderPage,
  "/platform/operational-rule-composer": PlatformOperationalRuleComposerPage,
  "/platform/knowledge-quality-assurance": PlatformKnowledgeQualityAssurancePage,
  "/platform/knowledge-publishing": PlatformAirlineKnowledgePublishingPage,
  "/platform/operational-scenario-testing": PlatformOperationalScenarioTestingPage,
  "/platform/knowledge-population-toolkit": PlatformKnowledgePopulationToolkitPage,
  "/platform/pilot-readiness": PlatformPilotReadinessPage,
  "/platform/pilot-operations": PlatformPilotOperationsReadinessPage,
  "/platform/commercial-pilot-readiness": CommercialPilotReadinessPage,
  "/platform/pilot-feedback": PilotFeedbackReviewPage,
  "/platform/service-parameter-taxonomies": PlatformServiceParameterTaxonomiesPage,
  "/platform/request-segment-services": PlatformRequestSegmentServicesPage,
  "/platform/client-master": PlatformClientMasterPage,
  "/platform/passenger-master": PlatformPassengerMasterPage,
  "/platform/reference": PlatformReferenceDataPage,
  "/platform/rules-services": PlatformRulesServicesPage,
  "/platform/documents": PlatformDocumentTemplatesPage,
  "/platform/document-templates": PlatformDocumentTemplatesPage,
  "/platform/gds-parser": PlatformGdsParserPage,
  "/platform/airline-policy-ingestion": AirlinePolicyIngestionPage,
  "/platform/service-taxonomy": PlatformServiceTaxonomyPage,
  "/platform/service-mechanics": PlatformServiceMechanicsPage,
  "/platform/ancillary-pricing": PlatformAncillaryPricingPage,
  "/platform/policy-comparison": PlatformPolicyComparisonPage,
  "/platform/offer-policy-advisor": PlatformOfferPolicyAdvisorPage,
  "/platform/intelligent-offer-builder": PlatformIntelligentOfferBuilderPage,
  "/platform/offer-decision-packs": PlatformOfferDecisionPacksPage,
  "/platform/offer-decision-explanations": PlatformOfferDecisionExplanationsPage,
  "/platform/offer-decision-exports": PlatformOfferDecisionExportsPage,
  "/platform/offer-decision-export-previews": PlatformOfferDecisionExportPreviewsPage,
  "/platform/offer-decision-export-releases": PlatformOfferDecisionExportReleasesPage,
  "/platform/offer-decision-export-deliveries": PlatformOfferDecisionExportDeliveriesPage,
  "/platform/offer-decision-export-delivery-outcomes": PlatformOfferDecisionExportDeliveryOutcomesPage,
  "/platform/offer-decision-export-audit-reviews": PlatformOfferDecisionExportAuditReviewsPage,
  "/platform/offer-decision-export-governance": PlatformOfferDecisionExportGovernancePage,
  "/platform/offer-decision-export-compliance": PlatformOfferDecisionExportCompliancePage,
  "/agency": OperationsCommandCenterPage,
  "/agency/communications": CommunicationsPage,
  "/agency/reports": ReportsPage,
  "/agency/onboarding": AgencyOnboardingPage,
  "/agency/pilot-feedback": PilotFeedbackPage,
  "/agency/saas-subscription": SaaSSubscriptionPage,
  "/agency/feature-availability": FeatureAvailabilityPage,
  "/agency/feature-readiness": FeatureReadinessPage,
  "/agency/feature-bundles": FeatureBundlesPage,
  "/agency/assigned-bundles": AssignedBundlesPage,
  "/agency/bundle-dependencies": BundleDependenciesPage,
  "/agency/bundle-rollout-readiness": BundleRolloutReadinessPage,
  "/agency/rollout-plans": RolloutPlansPage,
  "/agency/rollout-approval": RolloutApprovalPage,
  "/agency/rollout-change-requests": RolloutChangeRequestsPage,
  "/agency/rollout-decisions": RolloutDecisionsPage,
  "/agency/rollout-issues": RolloutIssuesPage,
  "/agency/rollout-risks": RolloutRisksPage,
  "/agency/rollout-rollback-plans": RolloutRollbackPlansPage,
  "/agency/rollout-schedule": RolloutSchedulePage,
  "/agency/rollout-summary-packs": RolloutSummaryPacksPage,
  "/agency/rollout-timeline": RolloutTimelinePage,
  "/agency/travel-requests": TravelRequestsPage,
  "/agency/travel-workspaces": TravelWorkspacesPage,
  "/agency/passenger-workspaces": PassengerWorkspacesPage,
  "/agency/flight-workspaces": FlightWorkspacesPage,
  "/agency/trip-workspaces": TripWorkspacesPage,
  "/agency/journeys": JourneyWorkspacePage,
  "/agency/journey-authoring": JourneyAuthoringWorkspacePage,
  "/agency/journey-option-composition": JourneyOptionCompositionWorkspacePage,
  "/agency/journey-comparison-presentations": JourneyComparisonPresentationWorkspacePage,
  "/agency/offer-deliveries": OfferDeliveryContextPage,
  "/agency/offer-workspaces": OfferWorkspaceMetadataPage,
  "/agency/booking-workspaces": BookingWorkspaceMetadataPage,
  "/agency/ticket-workspaces": TicketWorkspaceMetadataPage,
  "/agency/emd-workspaces": EmdWorkspaceMetadataPage,
  "/agency/passenger-services": PassengerServicesPage,
  "/agency/document-workspaces": DocumentWorkspacesPage,
  "/agency/timeline": TimelinePage,
  "/agency/operational-workflows": AgencyOperationalWorkflowsPage,
  "/agency/work-queue": AgentWorkQueuePage,
  "/agency/deadlines": DeadlinesPage,
  "/agency/task-automation": AgencyTaskAutomationPage,
  "/agency/request-trip-conversion": RequestTripConversionPage,
  "/agency/booking-handoffs": BookingHandoffsPage,
  "/agency/after-sales": AfterSalesPage,
  "/agency/operations-command-center": OperationsCommandCenterPage,
  "/agency/workflow-maturity": AgencyWorkflowMaturityPage,
  "/agency/workflow-engine": WorkflowEnginePage,
  "/agency/rollout-dashboard": AgencyRolloutDashboardPage,
  "/agency/capabilities": CapabilitiesPage,
  "/agency/settings": AgencySettingsPage,
  "/agency/website": WebsiteBuilderPage,
  "/agency/website/media": WebsiteMediaLibraryPage,
  "/agency/reference": ReferenceDataPage,
  "/agency/settings/forms": FormProfilesPage,
  "/agency/airline-intelligence": AirlineIntelligencePage,
  "/agency/airline-profiles": AirlineProfilesPage,
  "/agency/airline-evidence": AgencyAirlineEvidencePage,
  "/agency/knowledge-updates": AgencyKnowledgeUpdatesPage,
  "/agency/airline-service-coverage": AgencyAirlineServiceCoveragePage,
  "/agency/distribution-capabilities": AgencyAirlineDistributionCapabilitiesPage,
  "/agency/interline-codeshare-advisor": AgencyInterlineCodeshareAdvisorPage,
  "/agency/fare-brand-library": AgencyFareBrandLibraryPage,
  "/agency/airline-contact-directory": AgencyAirlineContactDirectoryPage,
  "/agency/airline-intelligence-readiness": AgencyAirlineIntelligenceReadinessPage,
  "/agency/airline-intelligence-coverage": AirlineIntelligenceCoveragePage,
  "/agency/airline-intelligence-review-coverage": AirlineIntelligenceReviewCoveragePage,
  "/agency/airline-intelligence-knowledge-versions": AgencyAirlineIntelligenceKnowledgeVersionsPage,
  "/agency/airline-intelligence-consumption": AgencyAirlineIntelligenceConsumptionPage,
  "/agency/operational-intelligence": OperationalIntelligencePage,
  "/agency/knowledge-acquisition": KnowledgeAcquisitionPage,
  "/agency/operational-constraints": AgencyOperationalConstraintsPage,
  "/agency/knowledge-normalisation": KnowledgeNormalisationPage,
  "/agency/knowledge-governance": KnowledgeGovernancePage,
  "/agency/capability-matrix": CapabilityMatrixPage,
  "/agency/operational-evaluations": OperationalEvaluationsPage,
  "/agency/service-feasibility": ServiceFeasibilityPage,
  "/agency/recommendations": RecommendationsPage,
  "/agency/intelligence-cases": IntelligenceCasesPage,
  "/agency/reference-data-engine": AgencyReferenceDataEnginePage,
  "/agency/import-templates": ImportTemplatesPage,
  "/agency/policy-editor": PolicyEditorPage,
  "/agency/pricing-formula-builder": AgencyPricingFormulaBuilderPage,
  "/agency/rule-composer": RuleComposerPage,
  "/agency/knowledge-quality-assurance": AgencyKnowledgeQualityAssurancePage,
  "/agency/published-knowledge": AgencyPublishedKnowledgePage,
  "/agency/scenario-testing": AgencyScenarioTestingPage,
  "/agency/knowledge-population-toolkit": AgencyKnowledgePopulationToolkitPage,
  "/agency/pilot-readiness": AgencyPilotReadinessPage,
  "/agency/service-parameter-taxonomies": ServiceParameterTaxonomiesPage,
  "/agency/request-segment-services": RequestSegmentServicesPage,
  "/agency/clients": AgencyClientMasterPage,
  "/agency/passengers": AgencyPassengerMasterPage,
  "/agency/airline-policy-library": AirlinePolicyLibraryPage,
  "/agency/service-taxonomy": AgencyServiceTaxonomyPage,
  "/agency/service-mechanics": AgencyServiceMechanicsPage,
  "/agency/ancillary-pricing": AgencyAncillaryPricingPage,
  "/agency/policy-comparison": AgencyPolicyComparisonPage,
  "/agency/airline-service-advisor": AirlineServiceAdvisorPage,
  "/agency/offer-policy-advisor": AgencyOfferPolicyAdvisorPage,
  "/agency/offer-intelligence": OfferIntelligencePage,
  "/agency/offer-decision-packs": AgencyOfferDecisionPacksPage,
  "/agency/offer-decision-explanations": AgencyOfferDecisionExplanationsPage,
  "/agency/offer-decision-exports": AgencyOfferDecisionExportsPage,
  "/agency/offer-decision-export-previews": AgencyOfferDecisionExportPreviewsPage,
  "/agency/offer-decision-export-releases": AgencyOfferDecisionExportReleasesPage,
  "/agency/offer-decision-export-deliveries": AgencyOfferDecisionExportDeliveriesPage,
  "/agency/offer-decision-export-delivery-outcomes": AgencyOfferDecisionExportDeliveryOutcomesPage,
  "/agency/offer-decision-export-audit-reviews": AgencyOfferDecisionExportAuditReviewsPage,
  "/agency/offer-decision-export-governance": AgencyOfferDecisionExportGovernancePage,
  "/agency/offer-decision-export-compliance": AgencyOfferDecisionExportCompliancePage,
  "/agency/documents": DocumentsPage,
  "/agency/gds-parser": GdsParserPage,
  "/agency/document-storage": DocumentStoragePage,
  "/agency/document-templates": DocumentTemplatesPage,
  "/agency/portal-actions": AgencyPortalActionsPage,
  "/agency/request-intakes": RequestIntakesListPage,
  "/agency/trips": TripsPage,
  "/agency/trips/new": TripCreatePage,
  "/agency/refunds-exchanges": RefundExchangeCasesPage,
  "/agency/refunds-exchanges/new": RefundExchangeCaseCreatePage,
  "/portal": PortalDashboardPage,
  "/portal/actions": PortalActionsPage,
  "/portal/profile": PortalProfilePage,
  "/portal/passengers": PortalPassengersPage,
  "/portal/refunds-exchanges": PortalRefundExchangeCasesPage,
  "/portal/requests": PortalRequestsPage,
  "/portal/requests/new": PortalRequestCreatePage,
  "/portal/offers": PortalOfferDeliveriesPage,
  "/portal/travel-options": PortalOfferDeliveriesPage,
  "/portal/trips": PortalTripsPage,
  "/portal/bookings": PortalBookingsPage,
  "/portal/tickets": PortalTicketsPage,
  "/portal/emds": PortalEmdsPage,
  "/portal/documents": PortalDocumentsPage,
  "/portal/communications": PortalCommunicationsPage,
  "/portal/timeline": PortalTimelinePage,
  "/portal/notifications": PortalNotificationsPage,
  "/portal/approvals": PortalApprovalsPage,
  "/portal/assistance": PortalAssistancePage,
  "/portal/finance": PortalFinancePage,
  "/portal/invoices": PortalInvoicesPage,
  "/portal/payments": PortalPaymentsPage,
}

export default function RoutedApplication() {
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
    return <BookingWorkspacesPage />
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

  const requestSpecialServicesMatch = window.location.pathname.match(/^\/agency\/requests\/([^/]+)\/special-services$/)
  if (requestSpecialServicesMatch) {
    return <SpecialServicesPage requestId={requestSpecialServicesMatch[1]} />
  }

  const tripMatch = window.location.pathname.match(/^\/agency\/trips\/([^/]+)$/)
  if (tripMatch && tripMatch[1] !== "new") {
    return <TripDetailPage tripId={tripMatch[1]} />
  }

  const tripSpecialServicesMatch = window.location.pathname.match(/^\/agency\/trips\/([^/]+)\/special-services$/)
  if (tripSpecialServicesMatch) {
    return <SpecialServicesPage tripId={tripSpecialServicesMatch[1]} />
  }

  const requestIntakeMatch = window.location.pathname.match(/^\/agency\/request-intakes\/([^/]+)$/)
  if (requestIntakeMatch) {
    return <RequestIntakeDetailPage intakeId={requestIntakeMatch[1]} />
  }

  const offerBuilderMatch = window.location.pathname.match(/^\/agency\/offers\/([^/]+)\/builder$/)
  if (offerBuilderMatch) {
    return <OfferBuilderPage workspaceId={offerBuilderMatch[1]} />
  }

  const offerMatch = window.location.pathname.match(/^\/agency\/offers\/([^/]+)$/)
  if (offerMatch) {
    return <OfferWorkspaceDetailPage workspaceId={offerMatch[1]} />
  }

  const bookingWorkspaceMatch = window.location.pathname.match(/^\/agency\/booking-workspaces\/([^/]+)$/)
  if (bookingWorkspaceMatch) {
    return <BookingWorkspaceDetailPage bookingWorkspaceId={bookingWorkspaceMatch[1]} />
  }

  const ticketMatch = window.location.pathname.match(/^\/agency\/tickets\/([^/]+)$/)
  if (ticketMatch) {
    return <TicketDetailPage ticketRecordId={ticketMatch[1]} />
  }

  const emdMatch = window.location.pathname.match(/^\/agency\/emds\/([^/]+)$/)
  if (emdMatch) {
    return <EmdDetailPage emdRecordId={emdMatch[1]} />
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

  const portalOfferDeliveryMatch = window.location.pathname.match(/^\/portal\/travel-options\/([^/]+)$/)
  if (portalOfferDeliveryMatch) {
    return <PortalOfferDeliveryDetailPage deliveryId={portalOfferDeliveryMatch[1]} />
  }

  const portalBookingMatch = window.location.pathname.match(/^\/portal\/bookings\/([^/]+)$/)
  if (portalBookingMatch) {
    return <PortalBookingDetailPage bookingId={portalBookingMatch[1]} />
  }

  const portalTripMatch = window.location.pathname.match(/^\/portal\/trips\/([^/]+)$/)
  if (portalTripMatch) {
    return <PortalTripDetailPage tripId={portalTripMatch[1]} />
  }

  const portalTicketMatch = window.location.pathname.match(/^\/portal\/tickets\/([^/]+)$/)
  if (portalTicketMatch) {
    return <PortalTicketDetailPage ticketId={portalTicketMatch[1]} />
  }

  const portalEmdMatch = window.location.pathname.match(/^\/portal\/emds\/([^/]+)$/)
  if (portalEmdMatch) {
    return <PortalEmdDetailPage emdId={portalEmdMatch[1]} />
  }

  const portalCommunicationMatch = window.location.pathname.match(/^\/portal\/communications\/([^/]+)$/)
  if (portalCommunicationMatch) {
    return <PortalCommunicationDetailPage threadId={portalCommunicationMatch[1]} />
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
    return <AgencyClientMasterPage />
  }

  if (window.location.pathname === "/agency/passengers") {
    return <AgencyPassengerMasterPage />
  }

  if (window.location.pathname === "/agency/requests") {
    return <RequestsPage />
  }

  if (window.location.pathname === "/agency/trips") {
    return <TripsPage />
  }

  if (window.location.pathname === "/agency/offers") {
    return <OfferWorkspacesPage />
  }

  if (window.location.pathname === "/agency/bookings") {
    return <BookingsPage />
  }

  if (window.location.pathname === "/agency/booking-workspaces") {
    return <BookingWorkspacesPage />
  }

  if (window.location.pathname === "/agency/booking-imports") {
    return <BookingImportsPage />
  }

  if (window.location.pathname === "/agency/gds-parser") {
    return <GdsParserPage />
  }

  if (window.location.pathname === "/agency/service-taxonomy") {
    return <AgencyServiceTaxonomyPage />
  }

  if (window.location.pathname === "/agency/service-mechanics") {
    return <AgencyServiceMechanicsPage />
  }

  if (window.location.pathname === "/agency/policy-comparison") {
    return <AgencyPolicyComparisonPage />
  }

  if (window.location.pathname === "/agency/airline-service-advisor") {
    return <AirlineServiceAdvisorPage />
  }

  if (window.location.pathname === "/agency/offer-policy-advisor") {
    return <AgencyOfferPolicyAdvisorPage />
  }

  if (window.location.pathname === "/agency/tickets-emds") {
    return <TicketsEmdsPage />
  }

  if (window.location.pathname === "/agency/invoices") {
    return <InvoicesPage />
  }

  if (window.location.pathname === "/agency/finance") {
    return <FinanceDashboardPage />
  }

  if (window.location.pathname === "/agency/supplier-costs") {
    return <SupplierCostsPage />
  }

  if (window.location.pathname === "/agency/payments") {
    return <PaymentsPage />
  }

  const Page = routes[window.location.pathname] || NotFoundPage
  return <Page />
}
