# Extraction Best Practices

Guidelines for capturing and analyzing design references effectively.

## Capture Quality Guidelines

### Screenshot Requirements
- High-resolution (minimum 1920px wide for desktop)
- Accurate color reproduction (disable browser extensions that alter colors)
- Actual viewport size, not full-page scrolls
- Device-specific resolutions (desktop 1920x1080, mobile 390x844)
- Multiple states: default, hover, active, responsive breakpoints

### Multiple Examples
- Analyze 3-5 screens minimum for pattern recognition
- Include different page types (home, product, about, contact)
- Single screenshots miss patterns
- Capture from same site to identify consistency

## Analysis Best Practices

### 0. Measure What You Can, Label What You Estimate
Claude reads colors and sizes by eye, so hex codes and px values are estimates. Measure with ImageMagick (`media-processing`) when accuracy matters:

```bash
# Dominant colors with pixel counts (8 clusters)
magick in.png -resize 400x -colors 8 -depth 8 -format %c histogram:info:-
# Exact color of one pixel (x=120, y=64), e.g. a button fill or background
magick in.png -depth 8 -format '#%[hex:p{120,64}]\n' info:
# Zoom into a region before reading small text
magick in.png -crop 400x200+0+0 +repage -resize 200% crop.png
```
Pick sample coordinates by looking at the image first. Photographs, gradients, and anti-aliased edges give approximate values; sample flat areas. When the design must match exactly, ask for the source file or Figma tokens, or read computed styles from the live site with the `chrome-devtools` skill.

### 1. Demand Specifics
❌ Accept: "Uses blue and gray colors"
✓ Demand: "Primary: #1E40AF, Secondary: #6B7280, Accent: #F59E0B"

❌ Accept: "Modern sans-serif font"
✓ Demand: "Inter, weight 600, 48px for h1, tracking -0.02em"

### 2. Document Rationale
Understand *why* design decisions work, not just *what* they are:
- Why does this color palette create trust?
- Why does this spacing scale improve readability?
- Why does this typography hierarchy guide user attention?

### 3. Create Actionable Guidelines
Output should be directly implementable in code:

```css
/* Immediately usable CSS from extraction */
:root {
  --font-display: 'Bebas Neue', sans-serif;
  --font-body: 'Inter', sans-serif;

  --color-primary-600: #1E40AF;
  --color-accent-500: #F59E0B;

  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;

  --radius-sm: 4px;
  --radius-md: 8px;

  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
}
```

### 4. Cross-Reference
- Font identification from an image is approximate: name the likely family plus 2-3 alternatives and validate against the Google Fonts library
- If the site is live, read the real font stack with the `chrome-devtools` skill (computed styles) instead of guessing; or use WhatFont
- Verify extracted colors with the ImageMagick samples above or an eyedropper

### 5. Iterate Analysis
First pass may miss subtleties:
- Do the initial comprehensive pass
- Review your notes, identify gaps
- Re-Read a cropped, zoomed region for each specific element (nav, buttons, footer, small text)

## Advanced Techniques

### Design System Mining
Extract a complete design system from a single brand (10+ screens): `Read` the screens one at a time, keep a running token table, then write the result. Target output:
- All color tokens (20+ colors)
- All typography specs (sizes, weights, line-heights)
- All spacing tokens
- All component variants
- All animation timings
Output as CSS variables ready for implementation (`docs/design-guidelines/brand-design-system.md`). More than ~10 images in one turn is heavy: batch by page type and merge.

### Trend Analysis
Analyze multiple top designs (`docs/inspiration/awwwards-*.png`) to identify current trends. `Read` each, then answer:
1. Dominant aesthetic movements
2. Common color strategies
3. Typography trends
4. Layout innovations
5. Animation patterns
A screenshot set shows what these sites look like, not what is "trending this year"; say so rather than claim a market trend. Save to `docs/design-guidelines/trend-analysis.md`.

### Historical Evolution
Track the design evolution of a single brand: `Read` `docs/inspiration/brand-2020.png` and `brand-2024.png`, then answer:
1. What changed and why
2. What remained consistent (brand identity)
3. How trends influenced changes
4. Lessons for our design evolution
Save to `docs/design-guidelines/evolution-analysis.md`.

## Common Pitfalls

### ❌ Surface-Level Analysis
"Uses blue colors and sans-serif fonts"
**Fix**: Demand specifics—hex codes, font names, size values (measured where possible, labelled as estimates otherwise)

### ❌ Missing Context
Extracting design without understanding target audience or purpose
**Fix**: Research brand context before analysis

### ❌ Blind Copying
Extracting and applying design 1:1 to your project
**Fix**: Extract principles, adapt to your unique context

### ❌ Single Source
Learning from one example only
**Fix**: Analyze 3-5 examples to identify patterns vs. anomalies
