export default function KnowledgeCategoryBadge({ category }) {
  return (
    <span className="inline-flex rounded-full bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700 ring-1 ring-indigo-200">
      {String(category || "other").replaceAll("_", " ")}
    </span>
  )
}
