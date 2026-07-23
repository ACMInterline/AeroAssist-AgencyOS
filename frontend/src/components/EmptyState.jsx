import Inbox from "lucide-react/dist/esm/icons/inbox.js"

export default function EmptyState({ title, body, children, icon: Icon = Inbox }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6" role="status">
      <Icon aria-hidden="true" className="h-5 w-5 text-slate-400" />
      <h3 className="mt-3 text-sm font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">{body}</p>
      {children ? <div className="mt-4">{children}</div> : null}
    </div>
  )
}
