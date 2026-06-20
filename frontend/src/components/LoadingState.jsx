export default function LoadingState({ label = "Loading" }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600">
      {label}
    </div>
  )
}
