import { useEffect, useRef } from "react"
import DestructiveButton from "./DestructiveButton"
import SecondaryButton from "./SecondaryButton"

export default function ConfirmationDialog({
  cancelLabel = "Keep current",
  confirmLabel = "Confirm",
  destructive = false,
  message,
  onCancel,
  onConfirm,
  open,
  title,
}) {
  const confirmRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const previousFocus = document.activeElement
    confirmRef.current?.focus()
    const onKeyDown = (event) => {
      if (event.key === "Escape") onCancel()
    }
    document.addEventListener("keydown", onKeyDown)
    return () => {
      document.removeEventListener("keydown", onKeyDown)
      previousFocus?.focus?.()
    }
  }, [onCancel, open])

  if (!open) return null

  const ConfirmButton = destructive ? DestructiveButton : SecondaryButton
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4" onMouseDown={(event) => { if (event.target === event.currentTarget) onCancel() }}>
      <section
        aria-describedby="confirmation-dialog-message"
        aria-labelledby="confirmation-dialog-title"
        aria-modal="true"
        className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-5 shadow-xl"
        role="alertdialog"
      >
        <h2 className="text-lg font-semibold text-slate-950" id="confirmation-dialog-title">{title}</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600" id="confirmation-dialog-message">{message}</p>
        <div className="mt-5 flex flex-wrap justify-end gap-2">
          <SecondaryButton onClick={onCancel}>{cancelLabel}</SecondaryButton>
          <ConfirmButton onClick={onConfirm} ref={confirmRef}>{confirmLabel}</ConfirmButton>
        </div>
      </section>
    </div>
  )
}
