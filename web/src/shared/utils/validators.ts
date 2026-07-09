type Rule = (v: unknown) => true | string

/** Lowercase Latin letters, digits, hyphen and underscore. No spaces. */
export function isSlug(message = 'Только a-z, 0-9, дефис и подчёркивание'): Rule {
  return (v) => {
    const s = v == null ? '' : String(v)
    if (s === '') return true
    return /^[a-z0-9_-]+$/.test(s) || message
  }
}
