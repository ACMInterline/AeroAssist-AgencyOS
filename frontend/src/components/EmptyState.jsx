export default function EmptyState({ title, body, children }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
      {children ? <div className="mt-4">{children}</div> : null}
    </div>
  )
}
