import Briefcase from "lucide-react/dist/esm/icons/briefcase.js"
import ClipboardList from "lucide-react/dist/esm/icons/clipboard-list.js"
import FileCheck2 from "lucide-react/dist/esm/icons/file-check-2.js"
import FileText from "lucide-react/dist/esm/icons/file-text.js"
import Home from "lucide-react/dist/esm/icons/home.js"
import ReceiptText from "lucide-react/dist/esm/icons/receipt-text.js"
import Repeat2 from "lucide-react/dist/esm/icons/repeat-2.js"
import UserCircle from "lucide-react/dist/esm/icons/user-circle.js"
import Users from "lucide-react/dist/esm/icons/users.js"
import WalletCards from "lucide-react/dist/esm/icons/wallet-cards.js"
import ListChecks from "lucide-react/dist/esm/icons/list-checks.js"
import { apiDeleteSession } from "../lib/api"
import { clearAuthSession } from "../lib/auth"
import { useAuthorization } from "../context/AuthorizationContext"

async function logout() {
  await apiDeleteSession().catch(() => null)
  clearAuthSession()
  window.location.href = "/login"
}

export default function ClientPortalLayout({ children, user: providedUser, brand }) {
  const authorization = useAuthorization()
  const subjectType = authorization.portalAccess?.subject_type || "client"
  const user = providedUser || {
    full_name: authorization.portalAccess?.subject?.display_name,
  }
  const primary = brand?.primary_color || "#2563eb"
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: primary }}>{subjectType === "passenger" ? "Passenger Portal" : "Client Portal"}</p>
            <h1 className="text-lg font-semibold text-slate-950">{brand?.brand_name || "Portal foundation"}</h1>
          </div>
          <nav className="flex flex-wrap items-center gap-2 text-sm">
            <Nav href="/portal" icon={<Home className="h-4 w-4" />} label="Dashboard" />
            <Nav href="/portal/profile" icon={<UserCircle className="h-4 w-4" />} label="Profile" />
            <Nav href="/portal/passengers" icon={<Users className="h-4 w-4" />} label="Passengers" />
            {subjectType === "client" ? <Nav href="/portal/requests" icon={<ClipboardList className="h-4 w-4" />} label="Requests" /> : null}
            {subjectType === "client" ? <Nav href="/portal/offers" icon={<FileText className="h-4 w-4" />} label="Offers" /> : null}
            {subjectType === "client" ? <Nav href="/portal/travel-options" icon={<ListChecks className="h-4 w-4" />} label="Travel Options" /> : null}
            {subjectType === "client" ? <Nav href="/portal/bookings" icon={<Briefcase className="h-4 w-4" />} label="Bookings" /> : null}
            {subjectType === "client" ? <Nav href="/portal/documents" icon={<FileText className="h-4 w-4" />} label="Documents" /> : null}
            {subjectType === "client" ? <Nav href="/portal/invoices" icon={<ReceiptText className="h-4 w-4" />} label="Invoices" /> : null}
            {subjectType === "client" ? <Nav href="/portal/payments" icon={<WalletCards className="h-4 w-4" />} label="Payments" /> : null}
            {subjectType === "client" ? <Nav href="/portal/refunds-exchanges" icon={<Repeat2 className="h-4 w-4" />} label="Refunds / Exchanges" /> : null}
            {subjectType === "client" ? <Nav href="/portal/actions" icon={<FileCheck2 className="h-4 w-4" />} label="Actions" /> : null}
          </nav>
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <UserCircle className="h-4 w-4" />
            {user?.full_name || "Demo user"}
            <button className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700 hover:bg-slate-100" type="button" onClick={logout}>Logout</button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  )
}

function Nav({ href, icon, label }) {
  return <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href={href}>{icon}{label}</a>
}
