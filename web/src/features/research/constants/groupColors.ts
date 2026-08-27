// Registry of the colours a research group may be painted with: name -> three steps of one hue.
//
// The names are the contract with the backend (a stored value is a name, never a hex), the same
// way `groupIcons.ts` holds the icon half. Keeping the hexes here rather than in `main.scss` is
// deliberate: these are *data* — a set the user picks from, indexed by a name that travels to the
// database — while `main.scss` holds the app's own tokens, which are referenced by role and never
// enumerated. A name outside the registry is not an error: the value is not validated on the way
// in, so an unknown name falls back to the app accent rather than painting nothing.
//
// THE STEPS. Nine hues 40° apart around the wheel — so no two names have to be told apart by a
// shade — plus a neutral. Every hue is frozen at three lightness levels (OKLCH L 0.80 / 0.62 /
// 0.47, chroma asked for 0.20 and fitted down to the sRGB gamut per hue and level, with the
// utility in `docs/frontend/rules.md`). Lightness is what stays equal across the set — the
// swatches read as one family, and the two readable steps keep the contrast measured below
// whichever hue is picked; chroma is whatever each hue can still hold there. `light` is the
// readable tone on dark, `deep` the readable tone on light, `mid` the flat fill of a swatch. Both
// readable tones were measured against the plate they land on — the surface plus a 14% tint of
// the tone itself — and the worst pair in the set is 5.16:1, above the 4.5 AA asks for.
//
// How a step becomes a paintable role is not decided here: the vars go onto an element carrying
// the `.color-tones` class and `main.scss` resolves them for the active theme
// (see `shared/colorTones.ts`).

import { colorToneVars, type ColorSteps, type ColorToneVars } from '@/shared/colorTones'

const GROUP_COLORS: Record<string, ColorSteps> = {
  red:     { light: '#FFA098', mid: '#E64343', deep: '#AC011A' },
  orange:  { light: '#FFA746', mid: '#BE7204', deep: '#824C00' },
  yellow:  { light: '#CFC20C', mid: '#928A07', deep: '#645D00' },
  green:   { light: '#59DE65', mid: '#04A22C', deep: '#006F1A' },
  teal:    { light: '#0BDAC9', mid: '#099B8F', deep: '#036961' },
  sky:     { light: '#42CFFE', mid: '#0994BA', deep: '#046480' },
  blue:    { light: '#9EBDFF', mid: '#497CFD', deep: '#214BC9' },
  violet:  { light: '#D1A9FF', mid: '#A35DE4', deep: '#762BB2' },
  rose:    { light: '#FF96D3', mid: '#D446A1', deep: '#A00074' },
  slate:   { light: '#B1C0D0', mid: '#7A8897', deep: '#4F5C6A' },
}

/** Steps for a stored colour name; unknown or empty -> `null` (the accent). */
export function groupColor(name: string | null | undefined): ColorSteps | null {
  if (!name) return null
  return GROUP_COLORS[name] ?? null
}

/** Every name the picker may offer, in the order the backend lists them. */
export function groupColorNames(): string[] {
  return Object.keys(GROUP_COLORS)
}

/** Vars for a stored colour name — bind to `:style` on an element classed `color-tones`. */
export function groupColorVars(name: string | null | undefined): ColorToneVars {
  return colorToneVars(groupColor(name))
}
