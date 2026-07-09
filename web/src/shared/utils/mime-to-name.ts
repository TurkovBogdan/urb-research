import { fileExt } from './file-icon'

// MIME → short display label ("application/pdf" → "PDF"). Covers the types core_storage
// admits; anything absent falls back to the subtype after the slash (see subtypeLabel).
// The generic binary types are absent on purpose — their subtype ("octet-stream") is
// already what the fallback yields.
const MIME_LABEL: Record<string, string> = {
  'application/pdf': 'PDF',
  'application/msword': 'DOC',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
  'application/vnd.oasis.opendocument.text': 'ODT',
  'application/rtf': 'RTF',
  'text/rtf': 'RTF (text)',
  'application/vnd.ms-excel': 'XLS',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX',
  'application/vnd.oasis.opendocument.spreadsheet': 'ODS',
  'application/vnd.ms-powerpoint': 'PPT',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPTX',
  'application/vnd.oasis.opendocument.presentation': 'ODP',
  'application/zip': 'ZIP',
  'application/x-zip-compressed': 'ZIP (Windows)',
  'application/x-rar-compressed': 'RAR',
  'application/vnd.rar': 'RAR5',
  'application/x-7z-compressed': '7Z',
  'application/gzip': 'GZIP',
  'application/x-tar': 'TAR',
  'application/json': 'JSON',
  'text/html': 'HTML',
  'text/calendar': 'ICS',
  'text/csv': 'CSV',
  'text/plain': 'TXT',
  'image/svg+xml': 'SVG',
  'application/pgp-keys': 'PGP',
  'application/pkcs7-signature': 'P7S',
  'application/vnd.ms-outlook': 'MSG',
  'application/ms-tnef': 'TNEF',
  'application/vnd.ms-fontobject': 'EOT',
  'video/mp4': 'MP4',
}

// The subtype after the slash, stripped of the x-/vnd. prefix and the +xml suffix and
// upper-cased ("application/x-foo" → "FOO", "image/jpeg" → "JPEG") — the label fallback
// when MIME_LABEL has no curated entry.
function subtypeLabel(type: string): string {
  const subtype = type.split('/')[1] ?? type
  return subtype.replace(/^(x-|vnd\.)/, '').replace(/\+.*$/, '').toUpperCase()
}

export function mimeToName(mime: string | null, filename: string | null = null): string {
  const type = (mime || '').toLowerCase().trim().split(';')[0]
  if (type) return MIME_LABEL[type] ?? subtypeLabel(type)
  return fileExt(filename).toUpperCase()
}
