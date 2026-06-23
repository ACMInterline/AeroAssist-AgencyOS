import { Plane } from "lucide-react"

const isProduction = import.meta.env.PROD || import.meta.env.VITE_APP_ENV === "production"

export default function PublicLayout({ children }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <a href="/" className="flex items-center gap-2 font-semibold text-slate-950">
            <Plane className="h-5 w-5 text-ocean" />
            AeroAssist AgencyOS
          </a>
          <nav className="flex items-center gap-4 text-sm text-slate-600">
            <a href="/login">{isProduction ? "Sign in" : "Demo login"}</a>
            <a href="/platform">Platform</a>
            <a href="/agency">Agency</a>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  )
}
