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
    "--aa-text": mode === "dark" || (mode === "system" && prefersDark) ? "#f8fafc" : "#0f172a",
    "--aa-shell": mode === "dark" || (mode === "system" && prefersDark) ? activeColors.surface : "#ffffff",
    "--aa-shadow": mode === "dark" || (mode === "system" && prefersDark) ? "0 20px 60px rgba(0,0,0,0.28)" : "0 20px 60px rgba(15,23,42,0.08)",
    "--aa-radius": computed.corner_radius || "12px",
    "--aa-font": computed.font_stack || "Inter, ui-sans-serif, system-ui, sans-serif",
    background: "var(--aa-bg)",
    color: "var(--aa-muted-text)",
    fontFamily: "var(--aa-font)",
  }
}
