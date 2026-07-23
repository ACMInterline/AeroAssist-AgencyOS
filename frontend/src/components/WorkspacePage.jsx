const workspaceVariants = {
  standard: "aa-workspace-standard",
  wide: "aa-workspace-wide",
  focused: "aa-workspace-focused",
  reading: "aa-workspace-reading",
}

export function workspacePageClass(variant = "standard") {
  return workspaceVariants[variant] || workspaceVariants.standard
}

export default function WorkspacePage({
  as: Component = "div",
  children,
  className = "",
  variant = "standard",
  ...props
}) {
  return (
    <Component className={`${workspacePageClass(variant)} ${className}`.trim()} data-workspace-layout={variant} {...props}>
      {children}
    </Component>
  )
}
