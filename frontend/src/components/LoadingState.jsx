import LoaderCircle from "lucide-react/dist/esm/icons/loader-circle.js"

export default function LoadingState({ label = "Opening workspace" }) {
  return (
    <div aria-live="polite" className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-700" role="status">
      <LoaderCircle aria-hidden="true" className="h-5 w-5 animate-spin text-blue-700" />
      <span>{label}</span>
    </div>
  )
}
