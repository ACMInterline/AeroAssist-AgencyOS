import { UserCircle } from "lucide-react"

export default function ClientPortalLayout({ children, user }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Client / Passenger Portal</p>
            <h1 className="text-lg font-semibold text-slate-950">Portal foundation</h1>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <UserCircle className="h-4 w-4" />
            {user?.full_name || "Demo user"}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  )
}
