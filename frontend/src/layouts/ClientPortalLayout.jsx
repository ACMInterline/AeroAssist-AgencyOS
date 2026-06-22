import { Briefcase, ClipboardList, FileCheck2, FileText, Home, ReceiptText, Repeat2, UserCircle, Users, WalletCards } from "lucide-react"
import { apiDeleteSession } from "../lib/api"
import { clearAuthSession } from "../lib/auth"

async function logout() {
  await apiDeleteSession().catch(() => null)
  clearAuthSession()
  window.location.href = "/login"
}

export default function ClientPortalLayout({ children, user, brand }) {
  const primary = brand?.primary_color || "#2563eb"
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: primary }}>Client Portal</p>
            <h1 className="text-lg font-semibold text-slate-950">{brand?.brand_name || "Portal foundation"}</h1>
          </div>
          <nav className="flex flex-wrap items-center gap-2 text-sm">
            <Nav href="/portal" icon={<Home className="h-4 w-4" />} label="Dashboard" />
            <Nav href="/portal/profile" icon={<UserCircle className="h-4 w-4" />} label="Profile" />
            <Nav href="/portal/passengers" icon={<Users className="h-4 w-4" />} label="Passengers" />
            <Nav href="/portal/requests" icon={<ClipboardList className="h-4 w-4" />} label="Requests" />
            <Nav href="/portal/offers" icon={<FileText className="h-4 w-4" />} label="Offers" />
            <Nav href="/portal/bookings" icon={<Briefcase className="h-4 w-4" />} label="Bookings" />
            <Nav href="/portal/documents" icon={<FileText className="h-4 w-4" />} label="Documents" />
            <Nav href="/portal/invoices" icon={<ReceiptText className="h-4 w-4" />} label="Invoices" />
            <Nav href="/portal/payments" icon={<WalletCards className="h-4 w-4" />} label="Payments" />
            <Nav href="/portal/refunds-exchanges" icon={<Repeat2 className="h-4 w-4" />} label="Refunds / Exchanges" />
            <Nav href="/portal/actions" icon={<FileCheck2 className="h-4 w-4" />} label="Actions" />
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
