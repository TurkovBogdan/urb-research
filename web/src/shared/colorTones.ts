// Contract between a named-colour palette and whatever paints with it.
//
// A palette (today: research group shelves, `features/research/constants/groupColors.ts`) stores
// three lightness steps per hue. Which step becomes the readable one depends on the theme, and a
// plain object cannot hold that condition — so the object carries the raw steps as CSS variables
// and the choice is made once, in `main.scss`, by the `.color-tones` class:
//
//     <span class="color-tones" :style="colorToneVars(steps)">   →  var(--gc-ink) / var(--gc-fill)
//
// The class also composes `--gc-swatch` (the flat fill identifying the colour) and `--gc-fill`
// (the ink at the `*-soft` alpha), so those formulas have one home too. Consumers name roles,
// never steps. The steps themselves are hex, per the single-source rule in
// `docs/frontend/rules.md`.

/** One hue frozen at three lightness steps (OKLCH L 0.80 / 0.62 / 0.47). */
export interface ColorSteps {
  /** Readable tone on a dark background. */
  light: string
  /** Flat fill of a swatch — the tone that stands for the colour in either theme. */
  mid: string
  /** Readable tone on a light background. */
  deep: string
}

/**
 * The three steps as CSS custom properties. The index signature is what lets the object go
 * straight into a `:style` binding — Vue's `CSSProperties` accepts custom properties only from a
 * type that declares one.
 */
export interface ColorToneVars {
  [property: `--${string}`]: string
}

/**
 * Steps of a colour, or — for `null` — the app accent, so an unset colour paints exactly as the
 * interface did before colours existed.
 */
export function colorToneVars(steps: ColorSteps | null): ColorToneVars {
  if (!steps) {
    return {
      '--gc-light': 'var(--accent)',
      '--gc-mid': 'var(--accent-mid)',
      '--gc-deep': 'var(--accent)',
    }
  }
  return {
    '--gc-light': steps.light,
    '--gc-mid': steps.mid,
    '--gc-deep': steps.deep,
  }
}
