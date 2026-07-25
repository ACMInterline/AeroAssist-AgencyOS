import BookOpen from "lucide-react/dist/esm/icons/book-open.js"
import BriefcaseBusiness from "lucide-react/dist/esm/icons/briefcase-business.js"
import ChevronDown from "lucide-react/dist/esm/icons/chevron-down.js"
import ClipboardPlus from "lucide-react/dist/esm/icons/clipboard-plus.js"
import FileText from "lucide-react/dist/esm/icons/file-text.js"
import MessageSquareText from "lucide-react/dist/esm/icons/message-square-text.js"
import NotebookPen from "lucide-react/dist/esm/icons/notebook-pen.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"

const actions = [
  { label: "Create request", href: "/agency/requests/new", permission: "edit_requests", icon: ClipboardPlus },
  { label: "Create offer", href: "/agency/offers/new", permission: "edit_offers", icon: Plus },
  { label: "Convert request", href: "/agency/request-trip-conversion", permission: "edit_trips", icon: RefreshCw },
  { label: "Open trips", href: "/agency/trips", permission: "view_trips", icon: Plane },
  { label: "Open bookings", href: "/agency/bookings", permission: "view_bookings", icon: BriefcaseBusiness },
  { label: "Prepare document", href: "/agency/document-workspaces", permission: "edit_documents", icon: FileText },
  { label: "Message client", href: "/agency/communications", permission: "edit_tasks", icon: MessageSquareText },
  { label: "Add internal note", href: "/agency/communications", permission: "edit_tasks", icon: NotebookPen },
]

export default function WorkflowQuickActions({ hasPermission }) {
  const permitted = actions.filter((action) => hasPermission(action.permission))
  if (!permitted.length) return null

  return (
    <details className="relative">
      <summary className="aa-primary-action inline-flex cursor-pointer list-none items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold">
        <BookOpen aria-hidden="true" className="h-4 w-4" />
        <span className="hidden sm:inline">Quick actions</span>
        <span className="sm:hidden">Actions</span>
        <ChevronDown aria-hidden="true" className="h-4 w-4" />
      </summary>
      <div className="absolute right-0 z-40 mt-2 w-64 overflow-hidden rounded-lg border border-slate-200 bg-white p-2 shadow-xl">
        {permitted.map(({ href, icon: Icon, label }) => (
          <a className="flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50" href={href} key={label}>
            <Icon aria-hidden="true" className="h-4 w-4 text-slate-500" />
            {label}
          </a>
        ))}
        <p className="border-t border-slate-100 px-3 pb-1 pt-2 text-[11px] leading-4 text-slate-500">
          These shortcuts open agency records. External actions still require authorised operational handling.
        </p>
      </div>
    </details>
  )
}
