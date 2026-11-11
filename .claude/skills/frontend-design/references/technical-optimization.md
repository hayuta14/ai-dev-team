# Effort & Performance Optimization

Strategy for choosing the cheapest asset path that meets the design bar, and keeping delivered assets light.

## Asset Path Strategy

1. **SVG / CSS first**: no external service, no key, no network; edits are instant and follow the CSS variables. Covers illustrations, patterns, gradients, textures, grain.
2. **User-supplied photos**: ask once, early, for the photos the brief needs.
3. **Labelled placeholder**: when a photo is unavoidable and none exists; exact size, content, alt text.

## Analysis Strategy

- Claude reads the image itself (`Read`); no per-analysis API cost.
- Large images cost context tokens: downscale references to ~1600px on the long edge (`magick in.png -resize '1600x1600>' small.png`) unless fine detail is needed; crop and zoom only the regions you need.
- Batch comparisons: Read the variants in one turn and rank them together.

## Delivery Performance Budgets

- Hero image: aim < 200 KB WebP at 1920 px; mobile variant < 100 KB
- Inline SVG: keep each under ~10 KB; larger ones go to files and are cached
- Grain/noise: SVG filter or a tiny tiled PNG, not a full-screen bitmap
- Lazy-load below-the-fold images (`loading="lazy"`), set `width`/`height` to avoid layout shift

## Optimization Tips

1. **Reuse tokens**: assets reference CSS variables, so a palette change needs no re-export
2. **Reuse successful recipes/briefs** with variations
3. **Create responsive variants only for assets that need them**
4. **Skip the high-effort option unless critical**: standard quality is enough for most assets
