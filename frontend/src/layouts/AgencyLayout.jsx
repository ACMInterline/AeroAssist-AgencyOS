import { BookOpenCheck, Building2, ClipboardList, CreditCard, FileText, Files, ReceiptText, TicketsPlane, UserRound, Users } from "lucide-react"

export default function AgencyLayout({ children, user, agency }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Agency Workspace</p>
            <h1 className="text-lg font-semibold text-slate-950">{agency?.name || "Agency foundation"}</h1>
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
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/airline-intelligence">
              <BookOpenCheck className="h-4 w-4" />
              Airline Intelligence
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency/documents">
              <Files className="h-4 w-4" />
              Documents
            </a>
          </nav>
          {user ? <p className="text-sm text-slate-500">{user.full_name}</p> : null}
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  )
}
