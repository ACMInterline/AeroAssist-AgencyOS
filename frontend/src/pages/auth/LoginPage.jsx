import { useState } from "react"
import PublicLayout from "../../layouts/PublicLayout"
import { apiPost } from "../../lib/api"
import { getDemoEmail, setDemoEmail } from "../../lib/auth"

export default function LoginPage() {
  const [email, setEmail] = useState(getDemoEmail())
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  async function handleSubmit(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const result = await apiPost("/api/auth/demo-login", { email })
      setDemoEmail(email)
      setMessage(result.message)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <PublicLayout>
      <div className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-6">
        <h1 className="text-xl font-semibold text-slate-950">Demo login</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Phase 1 uses an isolated development header instead of production authentication.
        </p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-slate-700">
            Demo email
            <input
              className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <button className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">
            Use demo session
          </button>
        </form>
        {message ? <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
        {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
      </div>
    </PublicLayout>
  )
}
