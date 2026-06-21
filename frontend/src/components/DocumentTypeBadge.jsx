export default function DocumentTypeBadge({ type }) {
  return (
    <span className="inline-flex rounded-full bg-cyan-50 px-2 py-1 text-xs font-medium text-cyan-800 ring-1 ring-cyan-200">
      {String(type || "document").replaceAll("_", " ")}
    </span>
  )
}
