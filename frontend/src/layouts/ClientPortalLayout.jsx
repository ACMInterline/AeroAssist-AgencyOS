import Bell from "lucide-react/dist/esm/icons/bell.js"
import BookOpenCheck from "lucide-react/dist/esm/icons/book-open-check.js"
import BriefcaseBusiness from "lucide-react/dist/esm/icons/briefcase-business.js"
import CircleDollarSign from "lucide-react/dist/esm/icons/circle-dollar-sign.js"
import ClipboardList from "lucide-react/dist/esm/icons/clipboard-list.js"
import FileText from "lucide-react/dist/esm/icons/file-text.js"
import Home from "lucide-react/dist/esm/icons/home.js"
import LogOut from "lucide-react/dist/esm/icons/log-out.js"
import MessageSquareText from "lucide-react/dist/esm/icons/message-square-text.js"
import PlaneTakeoff from "lucide-react/dist/esm/icons/plane-takeoff.js"
import ReceiptText from "lucide-react/dist/esm/icons/receipt-text.js"
import TicketCheck from "lucide-react/dist/esm/icons/ticket-check.js"
import UserCircle from "lucide-react/dist/esm/icons/user-circle.js"
import Users from "lucide-react/dist/esm/icons/users.js"
import { useAuthorization } from "../context/AuthorizationContext"
import { apiDeleteSession } from "../lib/api"
import { clearAuthSession } from "../lib/auth"

const clientLinks = [
  ["/portal", "Dashboard", Home],
  ["/portal/requests", "Requests", ClipboardList],
  ["/portal/travel-options", "Travel Options", BookOpenCheck],
  ["/portal/trips", "Trips", PlaneTakeoff],
  ["/portal/bookings", "Bookings", BriefcaseBusiness],
  ["/portal/tickets", "Tickets", TicketCheck],
  ["/portal/documents", "Documents", FileText],
  ["/portal/communications", "Messages", MessageSquareText],
  ["/portal/finance", "Finance", CircleDollarSign],
  ["/portal/notifications", "Actions", Bell],
  ["/portal/passengers", "Passengers", Users],
  ["/portal/profile", "Profile", UserCircle],
]

const passengerLinks = [
  ["/portal", "Dashboard", Home],
  ["/portal/trips", "My trips", PlaneTakeoff],
  ["/portal/tickets", "My tickets", TicketCheck],
  ["/portal/assistance", "My assistance", BookOpenCheck],
  ["/portal/documents", "My documents", FileText],
  ["/portal/communications", "Messages", MessageSquareText],
  ["/portal/timeline", "Timeline", ClipboardList],
  ["/portal/notifications", "Actions", Bell],
  ["/portal/profile", "Travel profile", UserCircle],
]

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
  const links = subjectType === "passenger" ? passengerLinks : clientLinks
  const primary = brand?.primary_color || "#2563eb"

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4">
          <a className="min-w-0" href="/portal">
            <p className="text-xs font-semibold uppercase" style={{ color: primary }}>
              {subjectType === "passenger" ? "Passenger Portal" : "Client Portal"}
            </p>
            <h1 className="truncate text-lg font-semibold text-slate-950">{brand?.brand_name || "AeroAssist"}</h1>
          </a>
          <div className="flex shrink-0 items-center gap-2 text-sm text-slate-600">
            <UserCircle aria-hidden="true" className="h-4 w-4" />
            <span className="hidden max-w-48 truncate sm:inline">{user?.full_name || "Portal user"}</span>
            <button aria-label="Sign out" className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 text-slate-700 hover:bg-slate-100" type="button" onClick={logout}>
              <LogOut aria-hidden="true" className="h-4 w-4" />
            </button>
          </div>
        </div>
        <nav aria-label="Portal navigation" className="mx-auto max-w-7xl overflow-x-auto px-4">
          <div className="flex min-w-max gap-1 pb-3">
            {links.map(([href, label, Icon]) => <Nav href={href} icon={Icon} label={label} key={href} />)}
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:py-8">{children}</main>
    </div>
  )
}

function Nav({ href, icon: Icon, label }) {
  const active = window.location.pathname === href || (href !== "/portal" && window.location.pathname.startsWith(`${href}/`))
  return (
    <a aria-current={active ? "page" : undefined} className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${active ? "bg-blue-50 text-blue-800" : "text-slate-700 hover:bg-slate-100"}`} href={href}>
      <Icon aria-hidden="true" className="h-4 w-4" />
      {label}
    </a>
  )
}
