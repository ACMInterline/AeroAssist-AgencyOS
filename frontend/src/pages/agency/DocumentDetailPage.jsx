import { useEffect, useState } from "react"
import DocumentPreviewFrame from "../../components/DocumentPreviewFrame"
import OperationalCollaborationPanel from "../../components/OperationalCollaborationPanel"
import DocumentStatusBadge from "../../components/DocumentStatusBadge"
import DocumentTypeBadge from "../../components/DocumentTypeBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiDownload, apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function DocumentDetailPage({ documentId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [deliveryForm, setDeliveryForm] = useState({ recipient_email: "", recipient_name: "", subject: "", message_text: "", export_id: "", client_visible: false })
  const [settingsForm, setSettingsForm] = useState({ sender_name: "", sender_email: "", reply_to_email: "", mode: "disabled", smtp_host: "", smtp_port: "", smtp_username: "", smtp_password_secret_ref: "", smtp_use_tls: true })

  async function load() {
    const context = await loadCurrentAgency()
    const [detail, exportsData, deliveriesData, settingsData, capabilitiesData] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/documents/${documentId}`),
      apiGet(`/api/agencies/${context.agency.id}/documents/${documentId}/exports`),
      apiGet(`/api/agencies/${context.agency.id}/documents/${documentId}/deliveries`),
      apiGet(`/api/agencies/${context.agency.id}/email-settings`),
      apiGet(`/api/agencies/${context.agency.id}/document-export-capabilities`),
    ])
    const diagnosticsEntries = await Promise.all(
      deliveriesData.items.map((item) =>
        apiGet(`/api/agencies/${context.agency.id}/document-deliveries/${item.id}/diagnostics`)
          .then((result) => [item.id, result.diagnostics])
          .catch((err) => [item.id, { next_allowed_action: "unknown", last_error_message: err.message }])
      )
    )
    setState({ ...context, ...detail, exports: exportsData.items, deliveries: deliveriesData.items, deliveryDiagnostics: Object.fromEntries(diagnosticsEntries), emailSettings: settingsData.settings, exportCapabilities: capabilitiesData })
    setSettingsForm({
      sender_name: settingsData.settings.sender_name || "",
      sender_email: settingsData.settings.sender_email || "",
      reply_to_email: settingsData.settings.reply_to_email || "",
      mode: settingsData.settings.mode || "disabled",
      smtp_host: settingsData.settings.smtp_host || "",
      smtp_port: settingsData.settings.smtp_port || "",
      smtp_username: settingsData.settings.smtp_username || "",
      smtp_password_secret_ref: "",
      smtp_use_tls: settingsData.settings.smtp_use_tls !== false,
    })
    setDeliveryForm((current) => ({
      ...current,
      subject: current.subject || `Document: ${detail.document.title}`,
      message_text: current.message_text || "Please find the agency-generated document snapshot attached or available as a printable export.",
      export_id: current.export_id || exportsData.items.find((item) => item.status === "generated")?.id || "",
    }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [documentId])

  async function archive() {
    await apiPost(`/api/agencies/${state.agency.id}/documents/${documentId}/archive`)
    await load()
  }

  async function generateExport(exportType = "print_html") {
    setError("")
    setNotice("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/documents/${documentId}/exports`, { export_type: exportType, client_visible: true })
      setNotice(`${result.export.export_type.replaceAll("_", " ")} export generated.`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function downloadExport(exportId) {
    setError("")
    try {
      await apiDownload(`/api/agencies/${state.agency.id}/document-exports/${exportId}/download`)
    } catch (err) {
      setError(err.message)
    }
  }

  async function createDelivery(event) {
    event.preventDefault()
    setError("")
    setNotice("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/documents/${documentId}/deliveries`, {
        ...deliveryForm,
        export_id: deliveryForm.export_id || undefined,
        recipient_name: deliveryForm.recipient_name || undefined,
      })
      setNotice("Delivery draft created.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function sendDelivery(deliveryId) {
    setError("")
    setNotice("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/document-deliveries/${deliveryId}/send`)
      setNotice("Delivery sent.")
      await load()
    } catch (err) {
      setError(err.message)
      await load().catch(() => null)
    }
  }

  async function retryDelivery(deliveryId) {
    setError("")
    setNotice("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/document-deliveries/${deliveryId}/retry`)
      setNotice("Delivery retry recorded.")
      await load()
    } catch (err) {
      setError(err.message)
      await load().catch(() => null)
    }
  }

  async function cancelDelivery(deliveryId) {
    setError("")
    setNotice("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/document-deliveries/${deliveryId}/cancel`)
      setNotice("Delivery cancelled.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function validateEmailSettings() {
    setError("")
    setNotice("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/email-settings/validate`)
      setNotice(result.validation?.ok ? "Email settings validated." : result.validation?.error || "Email settings need attention.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function saveEmailSettings(event) {
    event.preventDefault()
    setError("")
    setNotice("")
    try {
      await apiPut(`/api/agencies/${state.agency.id}/email-settings`, {
        ...settingsForm,
        reply_to_email: settingsForm.reply_to_email || undefined,
        smtp_host: settingsForm.smtp_host || undefined,
        smtp_port: settingsForm.smtp_port ? Number(settingsForm.smtp_port) : undefined,
        smtp_username: settingsForm.smtp_username || undefined,
        smtp_password_secret_ref: settingsForm.smtp_password_secret_ref || undefined,
      })
      setNotice("Email settings updated.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const document = state?.document
  const sourceHref = document ? sourceLink(document) : "#"
  const emailMode = state?.emailSettings?.mode || "disabled"
  const emailSendingDisabled = emailMode === "disabled"
  const pdfCapability = state?.exportCapabilities?.pdf
  const pdfAvailable = Boolean(pdfCapability?.available)

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/documents">Back to documents</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">HTML document · Preview only</p>
              <h2 className="text-2xl font-semibold text-slate-950">{document.title}</h2>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <DocumentTypeBadge type={document.document_type} />
              <DocumentStatusBadge status={document.status} />
              <button className="rounded-md border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700" onClick={archive}>Archive</button>
            </div>
          </div>
          <section className="grid gap-4 lg:grid-cols-3">
            <Info title="Metadata" rows={[["Source", document.source_entity_type], ["Rendered", document.rendered_at ? new Date(document.rendered_at).toLocaleString() : "Not set"], ["Language", document.language], ["Client visible", document.client_visible ? "Yes" : "No"]]} />
            <Info title="Brand Snapshot" rows={[["Brand", document.brand_snapshot.brand_name], ["Primary", document.brand_snapshot.primary_color], ["Secondary", document.brand_snapshot.secondary_color], ["Font", document.brand_snapshot.font_family]]} />
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Source</h3>
              <a className="mt-4 inline-flex rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-blue-700" href={sourceHref}>Open source record</a>
              <p className="mt-3 text-sm text-slate-600">Snapshot captured at render time. Main UI does not expose raw JSON.</p>
            </section>
          </section>
          {error ? <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          {notice ? <p className="rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p> : null}
          <section className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-slate-950">Exports</h3>
                  <p className="mt-1 text-sm text-slate-600">Agency-generated document exports from the stored rendered snapshot.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="button" onClick={() => generateExport("print_html")}>Generate printable export</button>
                  <button className={pdfAvailable ? "rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-blue-700" : "rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-400"} type="button" disabled={!pdfAvailable} title={pdfCapability?.diagnostic || "PDF generation is not available."} onClick={() => generateExport("pdf")}>{pdfAvailable ? "Generate PDF" : "PDF unavailable"}</button>
                </div>
              </div>
              <p className="mt-3 text-xs text-slate-500">PDF renderer: {pdfCapability?.engine || "unknown"} · {pdfCapability?.diagnostic || "Capability not loaded."}</p>
              <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                {(state.exports || []).length ? state.exports.map((item) => (
                  <div className="flex flex-wrap items-center justify-between gap-3 p-3 text-sm" key={item.id}>
                    <div>
                      <p className="font-medium text-slate-900">{item.filename}</p>
                      <p className="text-slate-500">{item.export_type.replaceAll("_", " ")} · {item.status} · {item.content_type || "unknown"} · {item.client_visible ? "portal visible" : "staff only"}</p>
                      <p className="text-slate-500">Storage {item.storage_mode || "unknown"} · Retention {item.retention_policy || "not set"}</p>
                      {item.retention_expires_at ? <p className="text-slate-500">Expires {new Date(item.retention_expires_at).toLocaleDateString()}</p> : null}
                      {item.generated_at ? <p className="text-slate-500">Generated {new Date(item.generated_at).toLocaleString()}</p> : null}
                      {item.file_size_bytes ? <p className="text-slate-500">{item.file_size_bytes} bytes{item.checksum_sha256 ? ` · SHA-256 ${item.checksum_sha256.slice(0, 12)}...` : ""}</p> : null}
                      {item.error_message ? <p className="mt-1 text-rose-700">{item.error_message}</p> : null}
                    </div>
                    {item.status === "generated" ? <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-blue-700" type="button" onClick={() => downloadExport(item.id)}>Download</button> : null}
                  </div>
                )) : <p className="p-3 text-sm text-slate-500">No exports yet.</p>}
              </div>
            </div>

            <form className="rounded-lg border border-slate-200 bg-white p-5" onSubmit={createDelivery}>
              <h3 className="font-semibold text-slate-950">Manual staff-controlled delivery</h3>
              <p className="mt-1 text-sm text-slate-600">No automatic email is sent when documents are rendered.</p>
              <div className="mt-4 grid gap-3">
                <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Recipient email" value={deliveryForm.recipient_email} onChange={(event) => setDeliveryForm((current) => ({ ...current, recipient_email: event.target.value }))} />
                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Recipient name" value={deliveryForm.recipient_name} onChange={(event) => setDeliveryForm((current) => ({ ...current, recipient_name: event.target.value }))} />
                <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Subject" value={deliveryForm.subject} onChange={(event) => setDeliveryForm((current) => ({ ...current, subject: event.target.value }))} />
                <textarea required className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Message" value={deliveryForm.message_text} onChange={(event) => setDeliveryForm((current) => ({ ...current, message_text: event.target.value }))} />
                <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={deliveryForm.export_id} onChange={(event) => setDeliveryForm((current) => ({ ...current, export_id: event.target.value }))}>
                  <option value="">No export attachment</option>
                  {(state.exports || []).filter((item) => item.status === "generated").map((item) => <option key={item.id} value={item.id}>{item.filename}</option>)}
                </select>
                <label className="inline-flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" checked={deliveryForm.client_visible} onChange={(event) => setDeliveryForm((current) => ({ ...current, client_visible: event.target.checked }))} />
                  Client-visible delivery record
                </label>
                <button className="justify-self-start rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Create delivery draft</button>
              </div>
            </form>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Deliveries</h3>
              {emailSendingDisabled ? <p className="mt-1 text-sm text-slate-600">Email sending is disabled for this agency. Drafts can be prepared, but sending requires dev console or SMTP mode.</p> : null}
              <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                {(state.deliveries || []).length ? state.deliveries.map((item) => {
                  const diagnostics = state.deliveryDiagnostics?.[item.id] || {}
                  const sendDisabled = emailSendingDisabled || diagnostics.next_allowed_action !== "send"
                  const retryDisabled = emailSendingDisabled || diagnostics.next_allowed_action !== "retry"
                  return (
                  <div className="flex flex-wrap items-center justify-between gap-3 p-3 text-sm" key={item.id}>
                    <div>
                      <p className="font-medium text-slate-900">{item.subject}</p>
                      <p className="text-slate-500">{item.recipient_email} · {item.status} · {item.provider} · attempts {item.attempt_count || 0}/{item.max_attempts || 3}</p>
                      <p className="text-slate-500">Retry {item.retry_status || "none"}{item.last_attempt_at ? ` · last ${new Date(item.last_attempt_at).toLocaleString()}` : ""}</p>
                      <p className="text-slate-500">Processing {item.processing_state || "manual_only"}{item.queued_at ? ` · queued ${new Date(item.queued_at).toLocaleString()}` : ""}{item.scheduled_for ? ` · scheduled ${new Date(item.scheduled_for).toLocaleString()}` : ""}</p>
                      <p className="text-slate-500">Next action {diagnostics.next_allowed_action || "unknown"} · attachment {diagnostics.attachment?.valid === false ? "invalid" : "valid"}</p>
                      {item.locked_at ? <p className="text-slate-500">Locked {new Date(item.locked_at).toLocaleString()}</p> : null}
                      {(item.attempts || []).slice(0, 3).map((attempt) => <p className="text-xs text-slate-500" key={attempt.id}>Attempt {attempt.attempt_number}: {attempt.status} · {attempt.provider}{attempt.error_message ? ` · ${attempt.error_message}` : ""}</p>)}
                      {diagnostics.email?.validation_error ? <p className="mt-1 text-amber-700">{diagnostics.email.validation_error}</p> : null}
                      {diagnostics.last_error_message || item.last_error_message || item.error_message ? <p className="mt-1 text-rose-700">{diagnostics.last_error_message || item.last_error_message || item.error_message}</p> : null}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {["draft", "queued"].includes(item.status) ? <button className={sendDisabled ? "rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-400" : "rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-blue-700"} type="button" disabled={sendDisabled} title={sendDisabled ? "Delivery diagnostics must allow send." : ""} onClick={() => sendDelivery(item.id)}>Send</button> : null}
                      {item.retry_status === "retry_available" ? <button className={retryDisabled ? "rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-400" : "rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-blue-700"} type="button" disabled={retryDisabled} title={retryDisabled ? "Delivery diagnostics must allow retry." : ""} onClick={() => retryDelivery(item.id)}>Retry</button> : null}
                      {["draft", "queued", "failed"].includes(item.status) ? <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700" type="button" onClick={() => cancelDelivery(item.id)}>Cancel</button> : null}
                    </div>
                  </div>
                )}) : <p className="p-3 text-sm text-slate-500">No deliveries yet.</p>}
              </div>
            </div>

            <form className="rounded-lg border border-slate-200 bg-white p-5" onSubmit={saveEmailSettings}>
              <h3 className="font-semibold text-slate-950">Email Settings</h3>
              <p className="mt-1 text-sm text-slate-600">Use dev console for local testing. SMTP password is resolved from environment secret reference.</p>
              <p className="mt-2 text-sm text-slate-600">Manual staff-controlled delivery · No automatic sending · No public link</p>
              <p className="mt-2 text-sm text-slate-600">Mode {state.emailSettings?.mode || "disabled"} · Secret configured {state.emailSettings?.smtp_password_is_configured ? "yes" : "no"} · Secret resolved {state.emailSettings?.smtp_password_secret_resolved ? "yes" : "no"}</p>
              {state.emailSettings?.smtp_password_secret_ref_masked ? <p className="mt-1 text-sm text-slate-600">Secret reference {state.emailSettings.smtp_password_secret_ref_masked}</p> : null}
              {state.emailSettings?.last_validation_error ? <p className="mt-1 text-sm text-rose-700">{state.emailSettings.last_validation_error}</p> : null}
              <div className="mt-4 grid gap-3">
                <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={settingsForm.mode} onChange={(event) => setSettingsForm((current) => ({ ...current, mode: event.target.value }))}>
                  <option value="disabled">disabled</option>
                  <option value="dev_console">dev console</option>
                  <option value="smtp">smtp</option>
                </select>
                <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Sender name" value={settingsForm.sender_name} onChange={(event) => setSettingsForm((current) => ({ ...current, sender_name: event.target.value }))} />
                <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Sender email" value={settingsForm.sender_email} onChange={(event) => setSettingsForm((current) => ({ ...current, sender_email: event.target.value }))} />
                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Reply-to email" value={settingsForm.reply_to_email} onChange={(event) => setSettingsForm((current) => ({ ...current, reply_to_email: event.target.value }))} />
                <div className="grid gap-3 md:grid-cols-2">
                  <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="SMTP host" value={settingsForm.smtp_host} onChange={(event) => setSettingsForm((current) => ({ ...current, smtp_host: event.target.value }))} />
                  <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="SMTP port" value={settingsForm.smtp_port} onChange={(event) => setSettingsForm((current) => ({ ...current, smtp_port: event.target.value }))} />
                  <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="SMTP username" value={settingsForm.smtp_username} onChange={(event) => setSettingsForm((current) => ({ ...current, smtp_username: event.target.value }))} />
                  <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Password secret reference" value={settingsForm.smtp_password_secret_ref} onChange={(event) => setSettingsForm((current) => ({ ...current, smtp_password_secret_ref: event.target.value }))} />
                </div>
                <label className="inline-flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" checked={settingsForm.smtp_use_tls} onChange={(event) => setSettingsForm((current) => ({ ...current, smtp_use_tls: event.target.checked }))} />
                  Use TLS
                </label>
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Save email settings</button>
                  <button className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-blue-700" type="button" onClick={validateEmailSettings}>Validate settings</button>
                </div>
              </div>
            </form>
          </section>
          <DocumentPreviewFrame html={document.rendered_html} />
          <OperationalCollaborationPanel
            agencyId={state.agency.id}
            entityId={documentId}
            entityLabel={document.document_number || document.title || "Document"}
            entityType="document"
          />
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function sourceLink(document) {
  if (document.source_entity_type === "offer") return `/agency/offers/${document.source_entity_id}`
  if (document.source_entity_type === "booking") return `/agency/bookings/${document.source_entity_id}`
  if (document.source_entity_type === "invoice") return `/agency/invoices/${document.source_entity_id}`
  return "/agency/bookings"
}

function Info({ title, rows }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 break-words text-slate-600">{value || "Not set"}</dd></div>)}</dl></section>
}
