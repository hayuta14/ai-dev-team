# Visual Assets for Frontend Design

Entry point for making and analyzing visual assets that align with frontend design thinking and aesthetic guidelines. Claude does the work itself: it writes SVG/CSS assets and reads images with the `Read` tool (vision). There is no AI image generation.

## When to Use

**Asset Creation**:
- Hero visuals, background assets, decorative elements
- Placeholder images with specific aesthetic qualities
- Icon sets, illustrations, graphic elements
- Texture overlays, gradient meshes, background patterns

**Visual Analysis**:
- Check assets against design standards (Read the image, answer a checklist)
- Compare variations with written scores
- Pull color palettes (estimated by eye, measured with ImageMagick)
- Test assets with UI overlays for readability and contrast

**Design Extraction**:
- Extract design guidelines from screenshots and reference images
- Analyze competitor designs, reverse-engineer design systems from inspiration
- Establish a consistent aesthetic direction from references

## Core Principles

### 1. Design-Driven Creation
Avoid generic imagery. Every asset should align with:
- The chosen aesthetic direction (brutalism, maximalism, retro-futurism, etc.)
- Typography system and visual hierarchy
- Color palette and theme consistency
- Overall design story and purpose

### 2. Contextual Asset Creation
Assets aren't standalone, they are part of a cohesive interface. Consider:
- **Purpose**: Hero vs. background texture vs. decorative element
- **Integration**: How it interacts with overlaid text, buttons, forms
- **Technical constraints**: File size, aspect ratio, responsive behavior
- **Accessibility**: Color contrast, text readability, decorative vs. informative

### 3. Analysis Before Integration
Never integrate assets without looking at them:
- Render and Read the asset in the real layout, not in isolation
- Score quality (1-10, minimum 7/10) with a one-line reason
- Use specific values: hex codes, not "blue"; px sizes, not "large"
- Compare variations before deciding

### 4. Learn from Excellence
Extract design systems systematically from high-quality references:
- Analyze 3-5 screens to identify patterns
- Document actionably with CSS variables and exact values
- Treat fonts and colors read from images as estimates; validate them
- Adapt principles contextually, don't copy blindly

### 5. Be Honest About Placeholders
If an asset is a placeholder (no photo available), label it in the code (`data-placeholder`, comment) with exact size, aspect ratio, and intended content, and say so in your report.

## Which Asset Path

| Need | Path |
|---|---|
| Illustration, icon, logo shape, pattern, divider | Claude writes SVG |
| Gradient, mesh, glow, noise/grain, texture | CSS (`linear-gradient`, `radial-gradient`, SVG `feTurbulence`) |
| Real photo | User-supplied file |
| Photo or painterly raster not available | Labelled placeholder (size + content + alt) |
| Background removal, resize, format conversion | `media-processing` skill |

## Workflow Quick Reference

### For Asset Creation
**See**: `asset-generation.md`

1. Define design context (aesthetic, colors, typography, tone)
2. Pick the asset path from the table above
3. Write the SVG/CSS (or placeholder); keep it parametrized with the CSS variables
4. Render, Read, and score it (≥ 7/10)
5. Iterate or integrate

### For Visual Analysis
**See**: `visual-analysis-overview.md`

1. Define evaluation criteria (context-specific)
2. Read the image, answer the checklist
3. Compare variations
4. Extract color palettes (estimate, then measure)
5. Test integration with UI elements

### For Design Extraction
**See**: `design-extraction-overview.md`

1. Capture high-quality reference screenshots
2. Read them, extract design elements systematically
3. Analyze multiple screens for consistent patterns
4. Document with CSS-ready specifications

## Integration with Other Skills

- `ui-ux-pro-max`: styles, palettes, font pairings, design decisions. Use it first, then this skill for assets.
- `chrome-devtools`: capture reference screenshots (`screenshot.js`, fixed 1920x1080 viewport) and screenshots of your implementation for side-by-side comparison; read computed styles from a live site.
- `ui-styling`: implement with shadcn/ui + Tailwind using colors/styles that complement the assets.
- `media-processing`: post-process assets (resize, compress, crop, background removal, ffmpeg frames from video).

## Navigation

**Detailed Workflows**:
- `asset-generation.md` - Asset creation workflow (SVG/CSS first, optional raster)
- `visual-analysis-overview.md` - Analysis and verification workflow
- `design-extraction-overview.md` - Extract guidelines from existing designs

**Additional Resources**:
- `technical-overview.md` - File optimization, examples, checklists, common pitfalls
- `animejs.md` - Animation implementation for frontend

## Remember

1. **Design First, Create Second**: Start with design thinking, not tooling
2. **Context is King**: Every asset serves the interface, not itself
3. **Iterate**: The first version is rarely final; render, look, refine
4. **Verify**: Never integrate without looking at the asset in context (≥ 7/10)
5. **Demand Specifics**: Hex codes not "blue", px not "large", ms not "fast"; label estimates as estimates
6. **Adapt, Don't Copy**: Understand principles, apply them to your own design
