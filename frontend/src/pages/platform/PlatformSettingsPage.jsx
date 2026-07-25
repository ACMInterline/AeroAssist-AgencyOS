import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js"
import PageHeader from "../../components/PageHeader"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkspacePage from "../../components/WorkspacePage"
import { useAuthorization } from "../../context/AuthorizationContext"
import PlatformLayout from "../../layouts/PlatformLayout"

const settings = [
  { title: "Feature access", body: "Review feature visibility and reusable access bundles.", href: "/platform/feature-flags" },
  { title: "Subscriptions", body: "Review plans, agency assignments, and entitlement visibility.", href: "/platform/saas-subscriptions" },
  { title: "Document templates", body: "Maintain reusable layouts for manually prepared documents.", href: "/platform/document-templates" },
  { title: "Pilot operations", body: "Review release evidence, backups, and human approval status.", href: "/platform/pilot-operations" },
]

export default function PlatformSettingsPage() {
  const authorization = useAuthorization()
  const allowed = ["platform_owner", "platform_admin"].includes(authorization.user?.global_role)
  return (
    <PlatformLayout user={authorization.user}>
      <ProtectedRoute error={!allowed ? "Platform Owner or Platform Admin access is required." : ""} loading={false}>
        <WorkspacePage as="main" className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Platform", href: "/platform" }, { label: "Settings" }]}
            eyebrow="Platform configuration"
            title="Settings"
            description="Open the governed area that owns the setting you need to review."
          />
          <div className="grid gap-4 md:grid-cols-2">
            {settings.map((item) => (
              <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={item.href} key={item.href}>
                <div className="flex items-start justify-between gap-3">
                  <div><h2 className="font-semibold text-slate-950">{item.title}</h2><p className="mt-2 text-sm leading-6 text-slate-600">{item.body}</p></div>
                  <ArrowRight aria-hidden="true" className="mt-1 h-4 w-4 shrink-0 text-slate-400" />
                </div>
              </a>
            ))}
          </div>
          <p className="text-xs leading-5 text-slate-500">Specialist configuration, release registers, and support diagnostics remain under Advanced.</p>
        </WorkspacePage>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
