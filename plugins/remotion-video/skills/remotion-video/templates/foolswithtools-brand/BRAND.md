# Brand notes — `foolswithtools-brand` profile

This is the **master brand** profile for the foolswithtools project — the published visual identity, not a genre-skinned promo treatment.

Source of truth:

- Live site: <https://foolswith.tools/>
- Source: <https://github.com/foolswithtools/website>

Tokens in `style-guide.ts` come straight from the site's `src/app.css` and `tailwind.config.js`. Don't add new colors. Don't change the wordmark casing rule.

## The vibe

Pop-art / punk-zine / maker-blog. Cream paper canvas, charcoal text, acid green as the workhorse signature. Anti-guru, **"no hype, no gurus"** voice — the brand laughs at itself.

Tagline: **"A fool with a tool is still a fool... just empowered."**

It's the opposite of a slick SaaS keynote. It's also the opposite of restrained corporate identity. It looks like a confident hand-stapled zine that ships software.

## Foundations

**Cream paper canvas.** `palette.bg` (`#FAFAF8`) — off-white paper. `palette.bgElevated` (`#F9FAFB`) for slightly lifted surfaces. `palette.surface` (`#F4F4F0`) for subtle separators. No dark canvases — this profile is light-mode native.

**Charcoal text.** `palette.text` (`#1A1A1A`) for primary copy. `textMuted` (`#3F3F3F`) for secondary, `textDim` (alpha 0.45) for de-emphasized.

**Acid green is the workhorse.** `palette.accentAcid` (`#CCFF00`) carries the identity — used aggressively for halftones, terminal chips, gummy buttons. It gets the most screen time of any color besides the canvas + text.

**Pop accents cycle.** Beat 0 → acid green, beat 1 → hot orange (`#F5471D`), beat 2 → banana yellow (`#FFE55C`), repeating. Use `accentForBeat(i)`. Orange and banana provide pop variety; the acid is the recurring anchor.

**Cool accents (cyan, magenta, lilac, mint, mocha)** are available for variety in larger compositions but aren't part of the cycle. Reach for them sparingly.

**Terminal motif.** The site uses a black + acid-green CRT chip (`palette.terminalBg` + `palette.terminalText`) for shell snippets and status indicators. Keep it.

**Chunky 2px borders, everywhere.** Default `layout.borderWidth` is `2`. Cards, chips, buttons — they all get the same chunky charcoal outline by default. It's part of the maker-blog feel.

## Wordmark rules

- Always uppercase **"FOOLS WITH TOOLS"** — three words with spaces.
- Never collapse to "foolswithtools" except as a URL slug.
- `preserveCase` prop on `WordmarkHero` exists **only** for actual CLI strings (e.g. `npx foolswithtools/some-tool`). Don't reach for it just because lowercase looks softer.

## Typography

All from Google Fonts (free):

- **Display:** Archivo Black (Helvetica Neue / system-ui fallback). Weight 900. **Default ALL-CAPS, tight tracking `-0.02em`, tight leading `0.95`.**
- **Display alt:** Archivo (regular weights for non-bold display variants).
- **Body:** Inter.
- **Secondary body:** Space Grotesk — used for taglines, button labels, excerpts.
- **Mono:** JetBrains Mono.

Sizes: `hero: 192`, `title: 104`, `subtitle: 56`, `body: 36`, `caption: 24`, `micro: 18`. The wordmark dominates — even bigger than `anthropic-brand`'s 144 hero.

## Voice samples

- Headlines: short, declarative, slightly self-deprecating. "We make tools. We use them on ourselves."
- Body: plain English, no jargon. Practical not aspirational.
- Anti-patterns: "unleash", "supercharge", "AI-powered" without context, growth-hacker speak.

## Motion philosophy

- **Energetic but not frantic.** Punchy with a tiny overshoot — this is `springs.pop` (damping 10, stiffness 200). Never the slam of a promo reel.
- **Pop, don't slam.** `appear` (damping 14) for normal elements; `pop` for chips, buttons, hero lines; `settle` (damping 22) for slow hero breathes.
- **The scribble underline is signature.** When you want to call attention to a phrase, use `ScribbleUnderline` rather than highlight chrome. It's the brand's gesture.
- **Halftones drift subtly.** ~8px slow drift over a scene — they're decoration, not dominant.
- **Mid-tempo.** `intro: 75`, `beat: 80`, `outro: 80`, `transition: 10`. Fast hard cuts mostly, with rare 10-frame fades. Slower than promo, faster than anthropic.
- **Easings:** `pop` for overshoot, `swiftOut` for normal, `softInOut` for slow, `expoOut` for whips, `scribble` (less smooth) for marker reveals.

## Composition primitives

The seven components shipped with this profile:

- **`WordmarkHero.tsx`** — full-bleed massive uppercase wordmark on cream canvas. Single line or stacked-words layout, optional Space-Grotesk tagline. Staggered pop-in per line.
- **`BentoTile.tsx`** — bordered rounded-card primitive (2px charcoal or beat-accent border, 24/32 radius, lifted shadow). For grouping content with the chunky-border maker-blog look.
- **`TerminalChip.tsx`** — black + acid-green mono pill. Inline command-line snippets, file names, status indicators. Optional blinking cursor.
- **`ScribbleUnderline.tsx`** — hand-drawn-feeling SVG underline that draws on under text. Caller passes `width` prop. Signature gesture for emphasis.
- **`HalftoneOverlay.tsx`** — radial-gradient dot pattern. Decorative tile background or corner accent in any palette color. Drifts slowly.
- **`GummyButton.tsx`** — pill button with `acidToBanana` gradient and fat glow shadow. Primary CTA. Ghost variant for secondary.
- **`StickerAvatar.tsx`** — rotated circular avatar with cream cut-out border + drop-shadow. Gentle live sway via sine on `currentFrame`. For author/persona references.

## When you promote a new component

After Phase 6 of the `remotion-video` workflow, if a new one-off fits this profile (cream canvas, charcoal text, acid-green-led accent cycle, chunky 2px borders, mid-tempo pop motion), move it into `src/brand/profiles/foolswithtools-brand/components/<Name>.tsx` and add a one-liner to the **Promotion log** below.

If a one-off needed a color outside the documented palette to work, don't promote it. Pick a palette-compliant alternative next time.

## Promotion log

- _(empty)_
