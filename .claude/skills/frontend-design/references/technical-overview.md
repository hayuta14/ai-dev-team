# Technical Guide Overview

Technical considerations and best practices for visual assets in frontend design.

## Quick Reference

### File Optimization (`media-processing` skill / ImageMagick)
```bash
# PNG/JPEG -> WebP at quality 85, max width 1920, strip metadata
magick docs/assets/hero-image.png -resize '1920x>' -strip -quality 85 docs/assets/hero-optimized.webp
# SVG: keep hand-written, remove editor cruft; check size
wc -c docs/assets/*.svg
```

### Format Selection
- **SVG**: illustrations, icons, patterns; resolution-independent, tiny, styleable with CSS variables
- **WebP**: Best for web photos/rasters, 25-35% smaller than PNG, wide browser support
- **AVIF**: Cutting edge, ~50% smaller than WebP, limited support
- **PNG**: Lossless, large file size, use for transparency
- **JPEG**: Lossy, smaller than PNG, photos without transparency

### Responsive Variants
- Desktop hero 16:9, mobile hero 9:16 or 3:4, square cards 1:1
- Crop per breakpoint (e.g. `magick in.png -gravity center -crop 9:16 +repage out.png`) and art-direct with `<picture>`

## Detailed References

- `technical-accessibility.md` - WCAG compliance, computing contrast ratios, alt text
- `technical-workflows.md` - Complete pipeline examples
- `technical-best-practices.md` - Checklists, quality gates
- `technical-optimization.md` - Effort/cost strategy, performance budgets

## Quick Commands

```bash
# Verify the implementation visually (viewport fixed at 1920x1080)
node <WS>/.claude/skills/chrome-devtools/scripts/screenshot.js --url http://localhost:3000 --output docs/screenshots/page.png
# Other viewports + horizontal-overflow check
node <WS>/.claude/skills/chrome-devtools/scripts/screenshot-at-viewport-with-overflow-check.mjs http://localhost:3000 docs/screenshots/page-360.png 360 800
# Dominant colors of an image (counts per cluster)
magick docs/assets/image.png -resize 400x -colors 8 -depth 8 -format %c histogram:info:-
# Render an SVG to PNG so it can be Read
magick -density 144 docs/assets/hero.svg docs/assets/hero.png
# Remove a background / resize: see the media-processing skill
```
Then `Read` the PNG and follow `visual-analysis-overview.md`.

## Responsive Image Strategies

**Art Direction (different crops)**:
```html
<picture>
  <source media="(min-width: 768px)" srcset="hero-desktop.webp">
  <source media="(max-width: 767px)" srcset="hero-mobile.webp">
  <img src="hero-desktop.jpg" alt="Hero image">
</picture>
```

**Resolution Switching (same crop, different sizes)**:
```html
<img
  srcset="hero-400w.webp 400w, hero-800w.webp 800w, hero-1200w.webp 1200w"
  sizes="(max-width: 600px) 400px, (max-width: 1000px) 800px, 1200px"
  src="hero-800w.jpg"
  alt="Hero image"
/>
```
