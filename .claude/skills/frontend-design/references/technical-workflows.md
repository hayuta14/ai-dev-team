# Complete Workflow Examples

End-to-end pipelines for visual assets and analysis. Claude writes the SVG/CSS and reads the images itself; there is no AI image generation.

## Example 1: Hero Section (Complete Pipeline)

1. **Design context**: minimalist travel brand, desert, warm beige/tan/cream/soft ochre, serene and spacious, clean area for white headline text.
2. **Make the hero** (default path): write `docs/assets/hero-desert.svg`: layered dune silhouettes (3-4 smooth `<path>` curves), a soft sun `radialGradient`, grain overlay from `asset-generation.md`. Use the page's CSS variables for the colors.
3. **Render and look**:
   ```bash
   magick -density 144 docs/assets/hero-desert.svg docs/assets/hero-desert.png
   ```
   `Read` the PNG, then score 1-10 for visual appeal, color harmony, suitability for overlaying white text, professional quality; list improvements.
4. **Check contrast** of the headline over the lightest area behind it (`technical-accessibility.md`); add a gradient overlay if below 4.5:1 (3:1 for large text).
5. **Mobile variant**: adjust `viewBox`/`preserveAspectRatio` or write a 9:16 variant with the same focal point; screenshot at 360x800 (`screenshot-at-viewport-with-overflow-check.mjs`) and `Read` it.
6. **Optimize**: keep the SVG small; for raster fallbacks `magick in.png -resize '1920x>' -strip -quality 85 out.webp`.

## Example 2: Extract, Make, Compare Loop

1. **Extract** guidelines from the inspiration: `Read` `docs/inspiration/competitor-hero.png`, answer the checklist in `extraction-prompts.md`, write `docs/design-guidelines/competitor-analysis.md`.
2. **Make** our asset from the extracted aesthetic and palette (SVG/CSS), in our own direction, not a copy.
3. **Compare**: `Read` both images; rate differentiation 1-10 (too similar or distinct?), and list what makes ours different.
4. **Colors for CSS**: estimate from the asset, then confirm with `magick our-hero.png -resize 400x -colors 8 -depth 8 -format %c histogram:info:-`.

## Example 3: A/B Design Directions

1. Make two directions (A minimalist, B bold) as SVG/CSS variants.
2. Render both, `Read` both, run the A/B checklist in `analysis-prompts.md` for the target audience (attention, brand alignment, conversion potential).
3. Recommend which to test with real users; this is a design critique, not experiment data.
4. Polish the chosen direction.

## Example 4: Batch Variations for Rapid Iteration

1. Write 3 variants (change one axis each: palette, composition, density).
2. Render all three to PNG, `Read` them in one turn, rank 1-3 with scores, name the winner.
3. Iterate on the winner until ≥ 7/10.
