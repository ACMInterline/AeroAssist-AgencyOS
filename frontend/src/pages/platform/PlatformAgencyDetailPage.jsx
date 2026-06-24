import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { rememberSelectedAgency } from "../../lib/agency"

const roleOptions = ["agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]

export default function PlatformAgencyDetailPage({ agencyId }) {
  const [state, setState] = useState(null)
  const [agencyForm, setAgencyForm] = useState(null)
  const [workspaceForm, setWorkspaceForm] = useState(null)
  const [inviteForm, setInviteForm] = useState({ email: "", invited_name: "", agency_role: "agency_agent", workspace_id: "" })
  const [createdInvite, setCreatedInvite] = useState(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const summary = await apiGet("/api/platform/summary")
    const agency = await apiGet(`/api/agencies/${agencyId}`)
    const workspaces = await apiGet(`/api/agencies/${agencyId}/workspaces`)
    const staff = await apiGet(`/api/agencies/${agencyId}/staff`)
    const invitations = await apiGet(`/api/agencies/${agencyId}/staff/invitations`)
    setState({ summary, agency: agency.agency, workspaces: workspaces.items, staff: staff.items, invitations: invitations.items })
    setAgencyForm({
      name: agency.agency.name,
      legal_name: agency.agency.legal_name,
      default_currency: agency.agency.default_currency,
      country: agency.agency.country,
      timezone: agency.agency.timezone,
      status: agency.agency.status,
    })
    setWorkspaceForm({
      name: workspaces.items[0]?.name || agency.agency.name,
      brand_name: workspaces.items[0]?.brand_name || agency.agency.name,
      default_currency: workspaces.items[0]?.default_currency || agency.agency.default_currency,
      timezone: workspaces.items[0]?.timezone || agency.agency.timezone,
      status: "active",
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [agencyId])

  async function updateAgency(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      await apiPut(`/api/agencies/${agencyId}`, agencyForm)
      setMessage("Agency basics updated.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function createWorkspace(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/agencies/${agencyId}/workspaces`, workspaceForm)
      setMessage("Workspace created. You can enter the agency workspace now.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function createInvitation(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const payload = {
        ...inviteForm,
        invited_name: inviteForm.invited_name || undefined,
        workspace_id: inviteForm.workspace_id || undefined,
      }
      const result = await apiPost(`/api/agencies/${agencyId}/staff/invitations`, payload)
      setCreatedInvite(result)
      setInviteForm({ email: "", invited_name: "", agency_role: "agency_agent", workspace_id: "" })
      setMessage("Invitation created. Copy the acceptance link now.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function revokeInvitation(invitationId) {
    if (!window.confirm("Revoke this pending invitation?")) return
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/agencies/${agencyId}/staff/invitations/${invitationId}/revoke`, {})
      setMessage("Invitation revoked.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function copyInviteLink() {
    if (!createdInvite?.accept_url) return
    const url = createdInvite.accept_url.startsWith("http") ? createdInvite.accept_url : `${window.location.origin}${createdInvite.accept_url}`
    await navigator.clipboard.writeText(url)
    setMessage("Acceptance link copied.")
  }

  function enterWorkspace() {
    rememberSelectedAgency(agencyId)
    window.location.href = `/agency?agency_id=${agencyId}`
  }

  const hasWorkspace = Boolean(state?.workspaces?.length)

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Agency Detail</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-950">{state?.agency?.name}</h2>
                <p className="mt-2 text-sm text-slate-600">{state?.agency?.legal_name}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge status={state?.agency?.status} />
                <button className="rounded-md border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" type="button" onClick={enterWorkspace} disabled={!hasWorkspace}>
                  Enter workspace
                </button>
              </div>
            </div>
            {message ? <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
            {createdInvite?.accept_url ? (
              <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4">
                <p className="text-sm font-semibold text-amber-900">This link is shown once. Copy it now.</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <input className="min-w-0 flex-1 rounded-md border border-amber-200 bg-white px-3 py-2 text-sm text-slate-800" readOnly value={createdInvite.accept_url.startsWith("http") ? createdInvite.accept_url : `${window.location.origin}${createdInvite.accept_url}`} />
                  <button className="rounded-md bg-amber-700 px-4 py-2 text-sm font-semibold text-white" type="button" onClick={copyInviteLink}>Copy link</button>
                </div>
                <p className="mt-2 text-xs text-amber-800">Raw invitation tokens are not shown again after refresh.</p>
              </div>
            ) : null}
          </section>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-lg border border-slate-200 bg-white p-6">
              <h3 className="text-sm font-semibold text-slate-950">Agency Basics</h3>
              {agencyForm ? (
                <form className="mt-4 grid gap-4" onSubmit={updateAgency}>
                  <Input label="Agency name" value={agencyForm.name} onChange={(value) => setAgencyForm((current) => ({ ...current, name: value }))} required />
                  <Input label="Legal name" value={agencyForm.legal_name} onChange={(value) => setAgencyForm((current) => ({ ...current, legal_name: value }))} required />
                  <div className="grid gap-4 sm:grid-cols-2">
                    <Input label="Default currency" value={agencyForm.default_currency} onChange={(value) => setAgencyForm((current) => ({ ...current, default_currency: value.toUpperCase() }))} required />
                    <Input label="Country" value={agencyForm.country} onChange={(value) => setAgencyForm((current) => ({ ...current, country: value.toUpperCase() }))} required />
                  </div>
                  <Input label="Timezone" value={agencyForm.timezone} onChange={(value) => setAgencyForm((current) => ({ ...current, timezone: value }))} required />
                  <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Update agency</button>
                </form>
              ) : null}
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-6">
              <h3 className="text-sm font-semibold text-slate-950">Workspaces</h3>
              {hasWorkspace ? (
                <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                  {state.workspaces.map((workspace) => (
                    <div className="grid gap-2 p-4 sm:grid-cols-[1fr_auto]" key={workspace.id}>
                      <div>
                        <p className="font-semibold text-slate-950">{workspace.name || workspace.brand_name}</p>
                        <p className="mt-1 text-sm text-slate-600">{workspace.brand_name}</p>
                      </div>
                      <div className="text-sm text-slate-600">
                        <StatusBadge status={workspace.status} />
                        <p className="mt-2">{workspace.default_currency || state.agency.default_currency} · {workspace.timezone || state.agency.timezone}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-4">
                  <EmptyState title="No workspace yet" body="Create your first agency workspace to begin operating AeroAssist." />
                </div>
              )}
              {!hasWorkspace && workspaceForm ? (
                <form className="mt-4 grid gap-4" onSubmit={createWorkspace}>
                  <Input label="Workspace name" value={workspaceForm.name} onChange={(value) => setWorkspaceForm((current) => ({ ...current, name: value }))} required />
                  <Input label="Brand label" value={workspaceForm.brand_name} onChange={(value) => setWorkspaceForm((current) => ({ ...current, brand_name: value }))} required />
                  <div className="grid gap-4 sm:grid-cols-2">
                    <Input label="Default currency" value={workspaceForm.default_currency} onChange={(value) => setWorkspaceForm((current) => ({ ...current, default_currency: value.toUpperCase() }))} required />
                    <Input label="Timezone" value={workspaceForm.timezone} onChange={(value) => setWorkspaceForm((current) => ({ ...current, timezone: value }))} required />
                  </div>
                  <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Create workspace</button>
                </form>
              ) : null}
            </section>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-lg border border-slate-200 bg-white p-6">
              <h3 className="text-sm font-semibold text-slate-950">Staff Memberships</h3>
              {state?.staff?.length ? (
                <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                  {state.staff.map((item) => (
                    <div className="grid gap-2 p-4 sm:grid-cols-[1fr_auto]" key={item.membership.id}>
                      <div>
                        <p className="font-semibold text-slate-950">{item.user?.full_name || item.user?.email || item.membership.user_id}</p>
                        <p className="mt-1 text-sm text-slate-600">{item.user?.email}</p>
                      </div>
                      <div className="text-sm text-slate-600">
                        <StatusBadge status={item.membership.status} />
                        <p className="mt-2">{item.membership.agency_role}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-4">
                  <EmptyState title="No staff yet" body="Prepare the first staff invitation when you are ready to hand off agency operations." />
                </div>
              )}
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-6">
              <h3 className="text-sm font-semibold text-slate-950">Create Staff Invitation</h3>
              <form className="mt-4 grid gap-4" onSubmit={createInvitation}>
                <Input label="Email" value={inviteForm.email} onChange={(value) => setInviteForm((current) => ({ ...current, email: value }))} required type="email" />
                <Input label="Invited name" value={inviteForm.invited_name} onChange={(value) => setInviteForm((current) => ({ ...current, invited_name: value }))} />
                <label className="block text-sm font-medium text-slate-700">
                  Workspace
                  <select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={inviteForm.workspace_id} onChange={(event) => setInviteForm((current) => ({ ...current, workspace_id: event.target.value }))}>
                    <option value="">Agency-wide access</option>
                    {state?.workspaces?.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name || workspace.brand_name}</option>)}
                  </select>
                </label>
                <label className="block text-sm font-medium text-slate-700">
                  Role
                  <select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={inviteForm.agency_role} onChange={(event) => setInviteForm((current) => ({ ...current, agency_role: event.target.value }))}>
                    {roleOptions.map((role) => <option key={role} value={role}>{role.replaceAll("_", " ")}</option>)}
                  </select>
                </label>
                <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Create invitation</button>
                <p className="text-sm text-slate-600">No email is sent automatically. Invitation delivery remains pending/manual.</p>
              </form>
            </section>
          </div>

          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <h3 className="text-sm font-semibold text-slate-950">Staff Invitations</h3>
            {state?.invitations?.length ? (
              <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                {state.invitations.map((invitation) => (
                  <div className="grid gap-3 p-4 lg:grid-cols-[1fr_auto]" key={invitation.id}>
                    <div>
                      <p className="font-semibold text-slate-950">{invitation.invited_name || invitation.invited_email}</p>
                      <p className="mt-1 text-sm text-slate-600">{invitation.invited_email}</p>
                      <p className="mt-1 text-xs text-slate-500">{invitation.target_role?.replaceAll("_", " ")} · expires {formatDate(invitation.expires_at)}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={invitation.status} />
                      {invitation.status === "pending" ? (
                        <button className="rounded-md border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-50" type="button" onClick={() => revokeInvitation(invitation.id)}>
                          Revoke
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-4">
                <EmptyState title="No invitations yet" body="Create an invitation when a real staff member is ready to join." />
              </div>
            )}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function formatDate(value) {
  if (!value) return "not set"
  return new Date(value).toLocaleString()
}

function Input({ label, value, onChange, required = false, type = "text" }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" required={required} type={type} value={value || ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}
