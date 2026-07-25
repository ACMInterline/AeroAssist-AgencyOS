import { useEffect, useRef } from "react"

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",")

export default function useDialogFocus({ dialogRef, initialFocusRef, onEscape, open }) {
  const escapeHandlerRef = useRef(onEscape)

  useEffect(() => {
    escapeHandlerRef.current = onEscape
  }, [onEscape])

  useEffect(() => {
    if (!open) return undefined
    const previousFocus = document.activeElement
    const dialog = dialogRef.current
    const initial = initialFocusRef?.current || dialog?.querySelector(FOCUSABLE_SELECTOR) || dialog
    initial?.focus?.()

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        event.preventDefault()
        escapeHandlerRef.current?.()
        return
      }
      if (event.key !== "Tab" || !dialog) return
      const focusable = [...dialog.querySelectorAll(FOCUSABLE_SELECTOR)].filter(
        (element) => !element.hasAttribute("hidden") && element.getAttribute("aria-hidden") !== "true",
      )
      if (!focusable.length) {
        event.preventDefault()
        dialog.focus()
        return
      }
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => {
      document.removeEventListener("keydown", handleKeyDown)
      previousFocus?.focus?.()
    }
  }, [dialogRef, initialFocusRef, open])
}
