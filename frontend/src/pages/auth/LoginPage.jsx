import { useState } from "react"
import PublicLayout from "../../layouts/PublicLayout"
import { apiPost } from "../../lib/api"
import { clearAuthSession, setAuthSession, setDemoEmail, setDemoPortalEmail } from "../../lib/auth"

const demoAccounts = [
  ["Platform owner", "owner@aeroassist.dev"],
  ["Agency owner", "agency.owner@aeroassist.dev"],
  ["Agency agent", "agency.agent@aeroassist.dev"],
  ["Portal client", "anna.client@example.com"],
  ["Portal company", "travel@orbitex.example.com"],
]

const isProduction = import.meta.env.PROD || import.meta.env.VITE_APP_ENV === "production"

export default function LoginPage() {
  const invite = new URLSearchParams(window.location.search).get("invite")
  const [email, setEmail] = useState(isProduction ? "" : "owner@aeroassist.dev")
  const [password, setPassword] = useState(isProduction ? "" : "DemoPass123!")
  const [displayName, setDisplayName] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    setSubmitting(true)
    try {
      const result = invite
        ? await apiPost("/api/auth/invitations/accept", { token: invite, password, display_name: displayName || undefined })
        : await apiPost("/api/auth/login", { email, password })
      setAuthSession(result.session, result.auth)
      if (!isProduction) {
        setDemoEmail(result.auth?.user?.email || email)
        if (["client_portal", "passenger_portal"].includes(result.auth?.identity?.identity_type)) {
          setDemoPortalEmail(result.auth.identity.email)
        }
      }
      setMessage("Signed in.")
      const type = result.auth?.identity?.identity_type
      window.location.href = ["client_portal", "passenger_portal"].includes(type) ? "/portal" : type === "platform_user" ? "/platform" : "/agency"
    } catch (err) {
      clearAuthSession()
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  function useDemo(accountEmail) {
    setEmail(accountEmail)
    setPassword("DemoPass123!")
    if (accountEmail.includes("example.com")) {
      setDemoPortalEmail(accountEmail)
    } else {
      setDemoEmail(accountEmail)
    }
  }

  return (
    <PublicLayout>
      <div className={`mx-auto grid max-w-4xl gap-6 ${isProduction ? "" : "md:grid-cols-[1fr_280px]"}`}>
        <section className="rounded-lg border border-slate-200 bg-white p-6">
          <h1 className="text-xl font-semibold text-slate-950">{invite ? "Accept invitation" : "Sign in"}</h1>
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            {!invite ? (
              <label className="block text-sm font-medium text-slate-700">
                Email
                <input
                  autoComplete="email"
                  className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  name="email"
                  required
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </label>
            ) : null}
            {invite ? (
              <label className="block text-sm font-medium text-slate-700">
                Display name
                <input
                  autoComplete="name"
                  className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  name="display_name"
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                />
              </label>
            ) : null}
            <label className="block text-sm font-medium text-slate-700">
              Password
              <input
                autoComplete={invite ? "new-password" : "current-password"}
                className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                name="password"
                required
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <button className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-wait disabled:opacity-70" disabled={submitting} type="submit">
              {submitting ? "Signing in..." : invite ? "Accept and sign in" : "Sign in"}
            </button>
          </form>
          {message ? <p aria-live="polite" className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{message}</p> : null}
          {error ? <p aria-live="assertive" className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-800" role="alert">{error}</p> : null}
        </section>
        {!isProduction ? (
          <aside className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="text-sm font-semibold text-slate-950">Demo accounts</h2>
            <div className="mt-4 space-y-2">
              {demoAccounts.map(([label, accountEmail]) => (
                <button className="w-full rounded-md border border-slate-200 px-3 py-2 text-left text-sm hover:bg-slate-50" key={accountEmail} type="button" onClick={() => useDemo(accountEmail)}>
                  <span className="block font-medium text-slate-900">{label}</span>
                  <span className="text-xs text-slate-500">{accountEmail}</span>
                </button>
              ))}
            </div>
          </aside>
        ) : null}
      </div>
    </PublicLayout>
  )
}
