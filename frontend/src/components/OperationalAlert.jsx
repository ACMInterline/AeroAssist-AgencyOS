import AlertCircle from "lucide-react/dist/esm/icons/alert-circle.js"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import Info from "lucide-react/dist/esm/icons/info.js"
import TriangleAlert from "lucide-react/dist/esm/icons/triangle-alert.js"

const tones = {
  info: ["border-blue-200 bg-blue-50 text-blue-900", Info],
  success: ["border-emerald-200 bg-emerald-50 text-emerald-900", CheckCircle2],
  warning: ["border-amber-200 bg-amber-50 text-amber-950", TriangleAlert],
  error: ["border-red-200 bg-red-50 text-red-900", AlertCircle],
}

export default function OperationalAlert({ actions, children, title, tone = "info" }) {
  const [classes, Icon] = tones[tone] || tones.info
  return (
    <div className={`rounded-lg border p-4 ${classes}`} role={tone === "error" ? "alert" : "status"}>
      <div className="flex items-start gap-3">
        <Icon aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0" />
        <div className="min-w-0 flex-1">
          {title ? <p className="text-sm font-semibold">{title}</p> : null}
          <div className={`${title ? "mt-1 " : ""}text-sm leading-6`}>{children}</div>
          {actions ? <div className="mt-3 flex flex-wrap gap-2">{actions}</div> : null}
        </div>
      </div>
    </div>
  )
}
