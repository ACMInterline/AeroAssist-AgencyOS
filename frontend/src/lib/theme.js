const defaultPalette = {
  primary: "#2563eb",
  primary_contrast: "#ffffff",
  accent: "#38bdf8",
  background: "#f8fafc",
  surface: "#ffffff",
  border: "#dbe3ef",
  muted_background: "#eff6ff",
  muted_text: "#475569",
  success: "#16a34a",
  warning: "#d97706",
  danger: "#dc2626",
}

export function agencyThemeStyle(branding) {
  const computed = branding?.computed_theme || {}
  const mode = computed.theme_mode || branding?.theme_mode || "light"
  const prefersDark = typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)")?.matches
  const palette = computed.palette || {}
  const colors = mode === "dark" || (mode === "system" && prefersDark) ? palette.dark : palette.light
  const activeColors = colors || defaultPalette
  return {
    "--aa-primary": activeColors.primary,
    "--aa-primary-contrast": activeColors.primary_contrast,
    "--aa-accent": activeColors.accent,
    "--aa-bg": activeColors.background,
    "--aa-surface": activeColors.surface,
    "--aa-border": activeColors.border,
    "--aa-muted-bg": activeColors.muted_background,
    "--aa-muted-text": activeColors.muted_text,
    "--aa-success": activeColors.success,
    "--aa-warning": activeColors.warning,
    "--aa-danger": activeColors.danger,
    "--aa-radius": computed.corner_radius || "12px",
    "--aa-font": computed.font_stack || "Inter, ui-sans-serif, system-ui, sans-serif",
    background: "var(--aa-bg)",
    color: "var(--aa-muted-text)",
    fontFamily: "var(--aa-font)",
  }
}
