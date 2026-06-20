import AgencyDashboardPage from "./pages/agency/AgencyDashboardPage"
import LoginPage from "./pages/auth/LoginPage"
import PlatformDashboardPage from "./pages/platform/PlatformDashboardPage"
import PortalDashboardPage from "./pages/portal/PortalDashboardPage"
import HomePage from "./pages/public/HomePage"

const routes = {
  "/": HomePage,
  "/login": LoginPage,
  "/platform": PlatformDashboardPage,
  "/agency": AgencyDashboardPage,
  "/portal": PortalDashboardPage,
}

export default function App() {
  const Page = routes[window.location.pathname] || HomePage
  return <Page />
}
