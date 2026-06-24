import { BookOpenCheck, Building2, ClipboardList, CreditCard, FileCheck2, FileText, Files, Inbox, ReceiptText, Settings, TicketsPlane, UserRound, Users, Repeat2 } from "lucide-react"
import { apiDeleteSession } from "../lib/api"
import { clearAuthSession } from "../lib/auth"
import { agencyThemeStyle } from "../lib/theme"

async function logout() {
  await apiDeleteSession().catch(() => null)
  clearAuthSession()
  window.location.href = "/login"
}

export default function AgencyLayout({ children, user, agency }) {
  const themeStyle = agencyThemeStyle(agency)
  const brandName = agency?.branding?.brand_name || agency?.name || "Agency foundation"

  return (
    <div className="aa-themed min-h-screen" style={themeStyle}>
      <style>{`
        .aa-themed header, .aa-themed section, .aa-themed article, .aa-themed aside { border-color: var(--aa-border); }
        .aa-themed input, .aa-themed select, .aa-themed textarea {
          border-color: var(--aa-border) !important;
          border-radius: var(--aa-radius) !important;
          background: var(--aa-surface) !important;
          color: #0f172a;
          font-family: var(--aa-font);
        }
        .aa-themed input[type="date"], .aa-themed input[type="time"], .aa-themed input[type="datetime-local"] {
          color-scheme: light;
          box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--aa-primary), transparent 82%);
        }
        .aa-themed button, .aa-themed .aa-primary-action {
          border-radius: var(--aa-radius) !important;
          border-color: var(--aa-primary) !important;
          font-family: var(--aa-font);
        }
        .aa-themed button[type="submit"], .aa-themed .aa-primary-action {
          background: var(--aa-primary) !important;
          color: var(--aa-primary-contrast) !important;
        }
        .aa-themed .rounded-lg, .aa-themed .rounded-md {
          border-radius: var(--aa-radius) !important;
        }
        .aa-themed .text-blue-700, .aa-themed .text-blue-600 {
          color: var(--aa-primary) !important;
        }
        .aa-themed .bg-blue-600 {
          background: var(--aa-primary) !important;
        }
      `}</style>
      <header className="border-b" style={{ background: "var(--aa-surface)", borderColor: "var(--aa-border)" }}>
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <div className="flex items-center gap-3">
            {agency?.branding?.logo_url ? (
              <img className="h-11 w-11 rounded-md border object-contain p-1" src={agency.branding.logo_url} alt={`${brandName} logo`} style={{ borderColor: "var(--aa-border)", background: "var(--aa-muted-bg)" }} />
            ) : (
              <div className="flex h-11 w-11 items-center justify-center rounded-md text-sm font-bold" style={{ background: "var(--aa-muted-bg)", color: "var(--aa-primary)" }}>
                {brandName.slice(0, 2).toUpperCase()}
              </div>
            )}
            <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Agency Workspace</p>
            <h1 className="text-lg font-semibold text-slate-950">{brandName}</h1>
            </div>
          </div>
          <nav className="flex items-center gap-2 text-sm">
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency">
              <Building2 className="h-4 w-4" />
              Dashboard
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/clients">
              <Users className="h-4 w-4" />
              Clients
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/passengers">
              <UserRound className="h-4 w-4" />
              Passengers
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/requests">
              <ClipboardList className="h-4 w-4" />
              Requests
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/request-intakes">
              <Inbox className="h-4 w-4" />
              Intakes
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/offers">
              <FileText className="h-4 w-4" />
              Offers
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/bookings">
              <TicketsPlane className="h-4 w-4" />
              Bookings
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/invoices">
              <ReceiptText className="h-4 w-4" />
              Invoices
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/payments">
              <CreditCard className="h-4 w-4" />
              Payments
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/refunds-exchanges">
              <Repeat2 className="h-4 w-4" />
              Refunds / Exchanges
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/airline-intelligence">
              <BookOpenCheck className="h-4 w-4" />
              Airline Intelligence
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/documents">
              <Files className="h-4 w-4" />
              Documents
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/document-storage">
              <FileCheck2 className="h-4 w-4" />
              Storage
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/portal-actions">
              <FileCheck2 className="h-4 w-4" />
              Portal Actions
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/settings">
              <Settings className="h-4 w-4" />
              Settings
            </a>
          </nav>
          <div className="flex items-center gap-3">
            {user ? <p className="text-sm text-slate-500">{user.full_name}</p> : null}
            <button className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700 hover:bg-slate-100" type="button" onClick={logout}>Logout</button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  )
}
