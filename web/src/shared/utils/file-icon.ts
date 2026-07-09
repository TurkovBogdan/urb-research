import type { FunctionalComponent } from 'vue'
import {
  IconFile,
  IconFileTypePdf,
  IconFileTypeDoc,
  IconFileTypeXls,
  IconFileTypePpt,
  IconFileTypeZip,
  IconFileTypeCsv,
  IconFileTypeTxt,
  IconFileCode,
  IconFileMusic,
  IconMarkdown,
  IconMovie,
  IconPhoto,
  IconCalendarEvent,
} from '@tabler/icons-vue'

// Single source of truth for "file → glyph" used by FileCards and any table cell that
// renders a file. The kind is resolved from the MIME type first (authoritative when the
// store recorded it), then the filename extension as a fallback; the glyph from the kind.

export type FileKind =
  | 'pdf' | 'doc' | 'sheet' | 'slides' | 'image' | 'audio' | 'video'
  | 'archive' | 'calendar' | 'code' | 'markdown' | 'csv' | 'text' | 'other'

const EXT_KIND: Record<string, FileKind> = {
  pdf: 'pdf',
  doc: 'doc', docx: 'doc', odt: 'doc', rtf: 'doc',
  xls: 'sheet', xlsx: 'sheet', ods: 'sheet',
  ppt: 'slides', pptx: 'slides', odp: 'slides',
  png: 'image', jpg: 'image', jpeg: 'image', gif: 'image', webp: 'image', bmp: 'image', svg: 'image', avif: 'image', tif: 'image', tiff: 'image', ico: 'image', heic: 'image',
  mp3: 'audio', wav: 'audio', ogg: 'audio', oga: 'audio', flac: 'audio', m4a: 'audio', aac: 'audio', opus: 'audio', wma: 'audio',
  mp4: 'video', m4v: 'video', mov: 'video', avi: 'video', mkv: 'video', webm: 'video', wmv: 'video', flv: 'video', mpeg: 'video', mpg: 'video',
  zip: 'archive', rar: 'archive', '7z': 'archive', gz: 'archive', tar: 'archive', bz2: 'archive', xz: 'archive',
  ics: 'calendar',
  csv: 'csv',
  md: 'markdown', markdown: 'markdown', mdx: 'markdown',
  js: 'code', mjs: 'code', cjs: 'code', ts: 'code', jsx: 'code', tsx: 'code', vue: 'code',
  py: 'code', rb: 'code', go: 'code', rs: 'code', java: 'code', kt: 'code', php: 'code', swift: 'code',
  c: 'code', h: 'code', cpp: 'code', cc: 'code', hpp: 'code', cs: 'code',
  sh: 'code', bash: 'code', zsh: 'code', sql: 'code',
  css: 'code', scss: 'code', sass: 'code', less: 'code',
  html: 'code', htm: 'code', xml: 'code', json: 'code', yaml: 'code', yml: 'code', toml: 'code', ini: 'code',
  txt: 'text', log: 'text',
}

// Exact MIME → kind. The generic binary types (application/octet-stream, …) are absent on
// purpose: they carry no signal, so resolution falls through to the extension. The image/,
// audio/ and video/ families are matched by prefix in mimeKind, not listed here.
const MIME_KIND: Record<string, FileKind> = {
  'application/pdf': 'pdf',
  'application/msword': 'doc',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'doc',
  'application/vnd.oasis.opendocument.text': 'doc',
  'application/rtf': 'doc',
  'text/rtf': 'doc',
  'application/vnd.ms-excel': 'sheet',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'sheet',
  'application/vnd.oasis.opendocument.spreadsheet': 'sheet',
  'application/vnd.ms-powerpoint': 'slides',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'slides',
  'application/vnd.oasis.opendocument.presentation': 'slides',
  'application/zip': 'archive',
  'application/x-zip-compressed': 'archive',
  'application/x-rar-compressed': 'archive',
  'application/vnd.rar': 'archive',
  'application/x-7z-compressed': 'archive',
  'application/gzip': 'archive',
  'application/x-tar': 'archive',
  'application/x-bzip2': 'archive',
  'text/calendar': 'calendar',
  'text/csv': 'csv',
  'text/markdown': 'markdown',
  'application/json': 'code',
  'application/xml': 'code',
  'text/xml': 'code',
  'text/html': 'code',
  'text/javascript': 'code',
  'application/javascript': 'code',
  'application/x-sh': 'code',
  'application/x-yaml': 'code',
  'text/yaml': 'code',
  'text/plain': 'text',
}

const KIND_ICON: Record<FileKind, FunctionalComponent> = {
  pdf: IconFileTypePdf,
  doc: IconFileTypeDoc,
  sheet: IconFileTypeXls,
  slides: IconFileTypePpt,
  image: IconPhoto,
  audio: IconFileMusic,
  video: IconMovie,
  archive: IconFileTypeZip,
  calendar: IconCalendarEvent,
  code: IconFileCode,
  markdown: IconMarkdown,
  csv: IconFileTypeCsv,
  text: IconFileTypeTxt,
  other: IconFile,
}

export function fileExt(filename: string | null): string {
  const name = (filename || '').toLowerCase().trim()
  const dot = name.lastIndexOf('.')
  return dot > 0 ? name.slice(dot + 1) : ''
}

function mimeKind(mime: string | null): FileKind | undefined {
  const type = (mime || '').toLowerCase().trim().split(';')[0]
  if (!type) return undefined
  if (type.startsWith('image/')) return 'image'
  if (type.startsWith('audio/')) return 'audio'
  if (type.startsWith('video/')) return 'video'
  return MIME_KIND[type]
}

export function fileKind(filename: string | null, mime: string | null = null): FileKind {
  return mimeKind(mime) ?? EXT_KIND[fileExt(filename)] ?? 'other'
}

export function fileIcon(filename: string | null, mime: string | null = null): FunctionalComponent {
  return KIND_ICON[fileKind(filename, mime)]
}

export function humanSize(bytes: number | null): string {
  if (bytes == null) return ''
  let value = bytes
  for (const unit of ['B', 'KB', 'MB', 'GB']) {
    if (value < 1024 || unit === 'GB') {
      return unit === 'B' ? `${value} ${unit}` : `${value.toFixed(1)} ${unit}`
    }
    value /= 1024
  }
  return ''
}
