import { useEffect, useState } from "react"
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js"
import PageHeader from "../../components/PageHeader"
import ProductTable from "../../components/ProductTable"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkspacePage from "../../components/WorkspacePage"
import { useAuthorization } from "../../context/AuthorizationContext"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

export default function PlatformUsersPage() {
  const authorization = useAuthorization()
  const allowed = ["platform_owner", "platform_admin"].includes(authorization.user?.global_role)
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!allowed) return
    Promise.all([apiGet("/api/platform/summary"), apiGet("/api/agencies")])
      .then(([summary, agencies]) => setState({ summary, agencies: agencies.items || [] }))
      .catch((err) => setError(err.message))
  }, [allowed])

  return (
    <PlatformLayout user={state?.summary?.current_user || authorization.user}>
      <ProtectedRoute error={!allowed ? "Platform Owner or Platform Admin access is required." : error} loading={allowed && !state && !error}>
        <WorkspacePage as="main" className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Platform", href: "/platform" }, { label: "Users" }]}
            eyebrow="Access overview"
            title="Users"
            description="Review where staff access exists, then open the owning agency to manage invitations and memberships."
          />
          <section className="grid gap-3 sm:grid-cols-3">
            <Metric label="Agency staff memberships" value={state?.summary?.counts?.staff_memberships || 0} />
            <Metric label="Pending staff invitations" value={state?.summary?.production_onboarding?.staff_invitations || 0} />
            <Metric label="Agencies" value={state?.agencies?.length || 0} />
          </section>
          <ProductTable
            caption="Agency access overview"
            columns={[
              { key: "agency", label: "Agency", render: (item) => item.name, sortValue: (item) => item.name || "" },
              { key: "status", label: "Status", render: (item) => formatLabel(item.status), sortValue: (item) => item.status || "" },
              { key: "staff", label: "Staff", render: (item) => item.staff_membership_count || 0, sortValue: (item) => Number(item.staff_membership_count || 0) },
              { key: "action", label: "Next action", render: () => <span className="inline-flex items-center gap-1 font-semibold text-blue-700">Review access <ArrowRight aria-hidden="true" className="h-4 w-4" /></span> },
            ]}
            defaultSort={{ key: "agency", direction: "asc" }}
            emptyBody="Create an agency before adding staff access."
            emptyTitle="No agency users yet"
            getRowHref={(item) => `/platform/agencies/${item.id}`}
            rows={state?.agencies || []}
          />
          <p className="text-xs leading-5 text-slate-500">Agency membership remains the authorization boundary. Platform roles do not silently grant access to Agency workspaces.</p>
        </WorkspacePage>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function formatLabel(value) {
  return String(value || "unknown").replaceAll("_", " ")
}
