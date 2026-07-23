import { useEffect, useState } from "react"
import { apiGet, apiPost } from "../../lib/api"
import { clearAuthSession, setAuthSession, setDemoEmail, setDemoPortalEmail } from "../../lib/auth"

export default function InviteAcceptPage() {
  const token = new URLSearchParams(window.location.search).get("token") || ""
  const [invite, setInvite] = useState(null)
  const [form, setForm] = useState({ display_name: "", password: "" })
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    if (!token) {
      setError("Invitation token is missing.")
      return
    }
    apiGet(`/api/auth/invitations/validate?token=${encodeURIComponent(token)}`)
      .then((result) => {
        setInvite(result)
        setForm((current) => ({ ...current, display_name: result.invitation?.invited_name || "" }))
      })
      .catch((err) => setError(err.message))
  }, [token])

  async function acceptInvitation(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const result = await apiPost("/api/auth/invitations/accept", {
        token,
        email: invite?.invitation?.invited_email,
        password: form.password,
        display_name: form.display_name || undefined,
      })
      setAuthSession(result.session, result.auth)
      if (result.auth?.user?.email) {
        setDemoEmail(result.auth.user.email)
      }
      if (["client_portal", "passenger_portal"].includes(result.auth?.identity?.identity_type)) {
        setDemoPortalEmail(result.auth.identity.email)
      }
      const type = result.auth?.identity?.identity_type
      window.location.href = ["client_portal", "passenger_portal"].includes(type) ? "/portal" : "/agency"
    } catch (err) {
      clearAuthSession()
      setError(err.message)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <section className="w-full max-w-xl rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Staff Invitation</p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-950">Accept invitation</h1>
        {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
        {message ? <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
        {invite ? (
          <div className="mt-5 space-y-5">
            <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
              <p><span className="font-semibold text-slate-900">Agency:</span> {invite.agency?.name || "Agency workspace"}</p>
              <p className="mt-1"><span className="font-semibold text-slate-900">Workspace:</span> {invite.workspace?.name || "Agency-wide access"}</p>
              <p className="mt-1"><span className="font-semibold text-slate-900">Email:</span> {invite.invitation?.invited_email}</p>
              <p className="mt-1"><span className="font-semibold text-slate-900">Role:</span> {invite.invitation?.target_role?.replaceAll("_", " ")}</p>
            </div>
            <form className="grid gap-4" onSubmit={acceptInvitation}>
              <label className="block text-sm font-medium text-slate-700">
                Display name
                <input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.display_name} onChange={(event) => setForm((current) => ({ ...current, display_name: event.target.value }))} />
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Password
                <input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" required minLength={10} type="password" value={form.password} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} />
              </label>
              <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Activate account</button>
            </form>
          </div>
        ) : !error ? (
          <p className="mt-4 text-sm text-slate-600">Checking invitation...</p>
        ) : null}
      </section>
    </main>
  )
}
