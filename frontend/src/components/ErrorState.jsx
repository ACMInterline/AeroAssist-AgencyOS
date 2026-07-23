import AlertCircle from "lucide-react/dist/esm/icons/alert-circle.js"
import RotateCcw from "lucide-react/dist/esm/icons/rotate-ccw.js"
import SecondaryButton from "./SecondaryButton"

export default function ErrorState({ message, onRetry, title = "We could not open this view" }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-red-900" role="alert">
      <div className="flex items-start gap-3">
        <AlertCircle aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0" />
        <div className="min-w-0">
          <h2 className="text-sm font-semibold">{title}</h2>
          <p className="mt-1 text-sm leading-6">{message || "Please try again. Your existing work has not been changed."}</p>
          {onRetry ? <SecondaryButton className="mt-3" icon={RotateCcw} onClick={onRetry}>Try again</SecondaryButton> : null}
        </div>
      </div>
    </div>
  )
}
