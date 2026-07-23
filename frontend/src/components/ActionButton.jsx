import { forwardRef } from "react"

const variants = {
  primary: "primary-button",
  secondary: "secondary-button",
  destructive: "destructive-button",
}

const ActionButton = forwardRef(function ActionButton({
  children,
  className = "",
  disabled = false,
  href,
  icon: Icon,
  busy = false,
  busyLabel = "Working...",
  type = "button",
  variant = "primary",
  ...props
}, ref) {
  const classes = `${variants[variant] || variants.secondary} ${className}`.trim()
  const content = (
    <>
      {Icon ? <Icon aria-hidden="true" className="h-4 w-4 shrink-0" /> : null}
      <span>{busy ? busyLabel : children}</span>
    </>
  )

  if (href && !disabled && !busy) {
    return <a className={classes} href={href} ref={ref} {...props}>{content}</a>
  }

  return (
    <button
      className={classes}
      disabled={disabled || busy}
      ref={ref}
      type={type}
      {...props}
    >
      {content}
    </button>
  )
})

export default ActionButton
