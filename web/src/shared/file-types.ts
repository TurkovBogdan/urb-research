// Global FileType catalog — mirrors the backend core_storage `FileType` enum. The
// single frontend source for the category list, their UI priority order, and the i18n
// label key. Labels are translated in the global `common.file_type.*` namespace, so
// every feature renders the same names from one place.

export type FileType =
  | 'document'
  | 'table'
  | 'presentation'
  | 'video'
  | 'archive'
  | 'image'
  | 'text'
  | 'email'
  | 'key'
  | 'font'
  | 'other'

// UI priority: the categories a user reaches for first (documents, spreadsheets,
// presentations, video, archives) on top; the technical rest below. Unlisted types
// sort last.
export const FILE_TYPE_ORDER: FileType[] = [
  'document',
  'table',
  'presentation',
  'video',
  'archive',
  'image',
  'text',
  'email',
  'key',
  'font',
  'other',
]

function fileTypeRank(fileType: string): number {
  const i = FILE_TYPE_ORDER.indexOf(fileType as FileType)
  return i === -1 ? FILE_TYPE_ORDER.length : i
}

// The i18n key for a file type's translated label (global `common` namespace).
export function fileTypeLabelKey(fileType: string): string {
  return `common.file_type.${fileType}`
}

// File types ordered by UI priority — for a filter dropdown built from a backend dict.
export function sortFileTypes(fileTypes: string[]): string[] {
  return [...fileTypes].sort((a, b) => fileTypeRank(a) - fileTypeRank(b))
}
