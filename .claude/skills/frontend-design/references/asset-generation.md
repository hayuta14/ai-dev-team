# Asset Creation Workflow

Workflow for making design-aligned visual assets. Default: Claude writes SVG and CSS (no external service). Photos come from the user; anything else that needs a raster is a labelled placeholder.

## Workflow

### Step 1: Define Design Context

Before creating anything, extract from the design brief:
- **Aesthetic direction**: Minimalist? Maximalist? Brutalist? Organic?
- **Color palette**: Primary colors, accent colors, mood (as CSS variables)
- **Typography character**: Modern sans-serif? Elegant serif? Bold display?
- **Visual tone**: Professional? Playful? Luxury? Raw?
- **User context**: Who sees this? What problem does it solve?

### Step 2: Choose the Asset Path

| Need | Path |
|---|---|
| Illustration, icon, pattern, divider, abstract hero | SVG (Step 3a) |
| Gradient, mesh, glow, grain, texture | CSS / SVG filter (Step 3a) |
| Real photograph | User-supplied file, else labelled placeholder (Step 3b) |
| Painterly/photographic raster | Labelled placeholder (Step 3b) |

Write the brief for the asset in design terms, not generic ones:

**Generic (avoid)**: "Modern website hero image"
**Design-driven (use)**: "Brutalist concrete texture, stark black and white, hard shadows, geometric slabs, 1960s Bauhaus influence, 16:9, quiet zone on the left for the headline"

Components of a good brief: style/movement, visual elements (textures, shapes, composition), color direction, mood, technical specs (aspect ratio, focal point, text-safe area), references.

### Step 3a: Make It as SVG / CSS (default)

Use the page's CSS variables so the asset follows the palette. Keep files small (hand-written paths, few nodes).

```html
<!-- Grain overlay: SVG turbulence filter -->
<svg width="0" height="0" aria-hidden="true">
  <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>
</svg>
<div class="grain" aria-hidden="true"></div>
```
```css
.grain { position: fixed; inset: 0; pointer-events: none; opacity: .08; filter: url(#grain); mix-blend-mode: multiply; }
.hero-mesh {
  background:
    radial-gradient(60% 50% at 20% 30%, var(--color-accent-500) 0%, transparent 60%),
    radial-gradient(50% 60% at 80% 70%, var(--color-primary-600) 0%, transparent 65%),
    var(--color-bg);
}
```

**Pattern recipes** (design context, then how to make it):
- **Minimalist paper texture** (refined, white space): off-white `--color-bg`, grain overlay at 4-6% opacity.
- **Maximalist hero** (bold, energetic): layered radial gradients in 2-3 saturated hues, diagonal SVG shapes with `mix-blend-mode`, animated `background-position`.
- **Brutalist geometric pattern**: SVG `<pattern>` of overlapping rectangles, 2 colors, hard edges, grid-aligned.
- **Organic / wellness**: soft blob paths (`border-radius` 40-60% or SVG curves), sage/cream tones, low contrast, large quiet area for text.
- **Retro-futuristic**: SVG perspective grid (lines converging to a horizon), cyan/magenta gradient sun, scanline overlay.
- **Editorial**: high-contrast crop frames, thin rules, duotone via CSS `mix-blend-mode` on user-supplied photos.

### Step 3b: Placeholder

When no photo is available, ship a labelled placeholder so the layout is real and the swap is trivial:

```html
<figure class="ph" data-placeholder="hero-photo 1600x900: sunrise over terraced rice fields, warm light">
  <svg viewBox="0 0 1600 900" role="img" aria-label="Placeholder: sunrise over terraced rice fields"><rect width="1600" height="900" fill="var(--color-neutral-200)"/><text x="800" y="450" text-anchor="middle" fill="var(--color-neutral-600)">1600x900 hero photo</text></svg>
</figure>
```
List every placeholder in the final report (path, size, intended content).

### Step 4: Evaluate Against Design Standards

Render the asset (screenshot with `chrome-devtools`, or `magick -density 144 in.svg out.png`), `Read` it in the real layout, and answer (see `visual-analysis-overview.md`):
1. Visual coherence with the aesthetic direction
2. Color harmony and contrast (compute ratios, `technical-accessibility.md`)
3. Composition and balance
4. Suitability for overlaying text
5. Quality 1-10 with a one-line reason; specific weaknesses

### Step 5: Iterate or Integrate

**Score < 7/10**: name the specific issue (color, composition, mood, technical), edit the SVG/CSS, re-render, re-score.
**Meets standard**: optimize for web (`technical-optimization.md`), create responsive variants, document usage, integrate.

## Brief Best Practices

1. **Style**: ❌ "Modern design" ✓ "Bauhaus-inspired geometric abstraction with primary colors"
2. **Color**: ❌ "Colorful" ✓ "Sunset palette: coral (#FF6B6B), amber (#FFB84D), violet (#A66FF0)"
3. **Composition**: ❌ "Nice layout" ✓ "Rule of thirds, subject left, negative space right for text"
4. **References**: ❌ "Artistic" ✓ "Bauhaus geometric abstraction, Swiss International Style"
5. **Technical first**: aspect ratio, resolution, intended use
6. **Iterate**: broad exploration, then color and composition, then details

## Common Pitfalls

- **Generic stock aesthetics**: "professional business team" imagery. Make contextual, design-specific assets.
- **Overcomplex assets**: backgrounds that fight UI text and buttons. Keep them subtle enough for overlays.
- **Inconsistent visual language**: every asset reuses the palette variables, stroke widths, and corner radii.
- **Ignoring context**: check typography overlays, interactive elements, navigation, responsive behavior.
- **Hidden placeholders**: an unlabelled grey box shipped as final.

## Responsive Asset Strategy

- **SVG/CSS**: use `viewBox` + `preserveAspectRatio`, or `clamp()`/container sizes; check at 360, 768, 1280 px.
- **Raster**: desktop 16:9 and mobile 9:16 variants with the same focal point; serve with `<picture>` (see `technical-overview.md`).
- Test that the composition holds in both orientations.

## Next Steps

- **Verify quality**: `visual-analysis-overview.md`
- **Optimize assets**: `technical-overview.md`
- **Extract inspiration**: `design-extraction-overview.md`
