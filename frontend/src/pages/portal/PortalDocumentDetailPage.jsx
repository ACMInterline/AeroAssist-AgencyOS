import { useEffect, useState } from "react"
import Download from "lucide-react/dist/esm/icons/download.js"
import Upload from "lucide-react/dist/esm/icons/upload.js"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalFacts, PortalPageHeader, PortalRecordList, PortalSection, PortalTimeline, formatDate, formatDateTime, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiDownload, apiGet, apiPost } from "../../lib/api"

export default function PortalDocumentDetailPage({ documentId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [uploading, setUploading] = useState(false)

  async function load() {
    const [me, detail] = await Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/document-center/${documentId}`)])
    setState({ me, ...detail })
  }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [documentId])

  async function uploadFile(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setError("")
    setNotice("")
    setUploading(true)
    try {
      const contentBase64 = await fileBase64(file)
      await apiPost(`/api/portal/document-center/${documentId}/upload`, {
        file_name: file.name,
        content_type: file.type,
        content_base64: contentBase64,
      })
      setNotice("Document uploaded for agency review.")
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
      event.target.value = ""
    }
  }

  async function download(versionId) {
    setError("")
    try {
      await apiDownload(`/api/portal/document-center/${documentId}/download${versionId ? `?version_id=${encodeURIComponent(versionId)}` : ""}`)
    } catch (err) {
      setError(err.message)
    }
  }

  const document = state?.document || {}
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-8">
          <PortalPageHeader eyebrow={document.document_reference || titleCase(document.type)} title={document.title || "Document"} description={document.description} status={document.status} backHref="/portal/documents" backLabel="Back to documents" actions={state?.download_available ? <button className="secondary-button" type="button" onClick={() => download()}><Download aria-hidden="true" className="h-4 w-4" />Download latest</button> : null} />
          {notice ? <p className="border-y border-emerald-200 bg-emerald-50 px-3 py-3 text-sm text-emerald-800" role="status">{notice}</p> : null}
          {error ? <p className="border-y border-rose-200 bg-rose-50 px-3 py-3 text-sm text-rose-800" role="alert">{error}</p> : null}
          <PortalSection title="Document details"><PortalFacts columns={3} rows={[["Type", titleCase(document.type)], ["Category", titleCase(document.category)], ["Passenger", document.passenger_name], ["Required for travel", document.required_for_travel], ["Deadline", formatDate(document.deadline)], ["Received", titleCase(document.received_status)], ["Verification", titleCase(document.verification_status)], ["Valid from", formatDate(document.valid_from)], ["Valid until", formatDate(document.valid_until)]]} /></PortalSection>
          {state?.upload_allowed ? (
            <PortalSection title="Upload requested document" description="PDF, JPEG, or PNG. Maximum file size 5 MB. Each upload creates an immutable version.">
              <label className="secondary-button w-fit cursor-pointer">
                <Upload aria-hidden="true" className="h-4 w-4" />
                {uploading ? "Uploading..." : "Choose file"}
                <input accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png" className="sr-only" disabled={uploading} type="file" onChange={uploadFile} />
              </label>
            </PortalSection>
          ) : null}
          <PortalSection title="Version history">
            <PortalRecordList items={state?.versions} emptyTitle="No stored file versions" emptyBody="A downloadable file has not been attached yet.">
              {(item) => <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold text-slate-950">Version {item.version} · {item.file_name || "Document"}</p><p className="mt-1 text-sm text-slate-600">{formatDateTime(item.uploaded_at)} · {item.size_bytes ? `${item.size_bytes.toLocaleString()} bytes` : "Size not recorded"}</p></div><button aria-label={`Download version ${item.version}`} className="secondary-button" type="button" onClick={() => download(item.id)}><Download aria-hidden="true" className="h-4 w-4" />Download</button></div>}
            </PortalRecordList>
          </PortalSection>
          <PortalSection title="Document timeline"><PortalTimeline items={state?.timeline} /></PortalSection>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function fileBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error("The file could not be read."))
    reader.onload = () => resolve(String(reader.result || "").split(",", 2)[1] || "")
    reader.readAsDataURL(file)
  })
}
