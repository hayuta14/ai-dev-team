# Visual Analysis Overview

Claude analyzes assets and implementations itself: `Read` the image, answer the checklist, record the verdict. No external API.

## Purpose

- Verify generated assets align with aesthetic direction
- Ensure professional quality before integration
- Identify specific improvements needed for iteration
- Make objective design decisions based on analysis
- Extract actionable data (hex codes, composition insights)

## Quick Start

### Comprehensive Analysis
1. `Read` `docs/assets/generated-hero.png` (SVG: render it to PNG first, e.g. `magick -density 144 in.svg out.png`, or screenshot the page).
2. Answer the comprehensive checklist in `analysis-prompts.md`.
3. Save the verdict to `docs/assets/analysis-report.md`.

### Compare Multiple Variations
`Read` `option-1.png`, `option-2.png`, `option-3.png`, then answer the comparison checklist in `analysis-prompts.md` and rank them.

### Verify an Implementation Against a Reference
Screenshot the page with the `chrome-devtools` skill (`screenshot.js --url ... --output docs/screenshots/impl.png`), `Read` it next to the reference image, and compare: color accuracy, spacing, typography, element completeness. List each difference with the CSS fix.

### Extract Color Palette
Estimate 5-8 dominant colors by eye, then confirm with ImageMagick:
```bash
magick docs/assets/final-asset.png -resize 400x -colors 8 -depth 8 -format %c histogram:info:-
```
Classify as primary/accent/neutral and suggest CSS variable names.

### Limits
Scores (1-10) are Claude's judgment, not a measurement; give a one-line justification. Colors are estimates unless measured. Contrast ratios must be computed from hex values (`technical-accessibility.md`), not eyeballed.

## Decision Framework

### Score ≥ 8/10: Proceed to Integration
**Actions**:
- Optimize for web delivery
- Create responsive variants
- Document implementation guidelines
- Extract color palette for CSS variables

### Score 6-7/10: Minor Refinements Needed
**Actions**:
- Use `media-processing` skill for adjustments (brightness/contrast/saturation)
- Rework only the problem areas of the SVG/CSS
- May proceed with caution if time-constrained

### Score < 6/10: Major Iteration Required
**Actions**:
- Analyze specific failure points from report
- Rewrite the brief and the SVG/CSS substantially
- Re-render and re-score
- Consider alternative aesthetic approach

## Detailed References

- `analysis-prompts.md` - All analysis prompt templates
- `analysis-techniques.md` - Advanced analysis strategies
- `analysis-best-practices.md` - Quality guidelines and pitfalls

## Example Color Extraction Output

```css
/* Extracted Color Palette */
:root {
  /* Primary Colors */
  --color-primary-600: #2C5F7D;  /* Dark teal - headers, CTAs */
  --color-primary-400: #4A90B8;  /* Medium teal - links, accents */

  /* Accent Colors */
  --color-accent-500: #E8B44F;   /* Warm gold - highlights */

  /* Neutral Colors */
  --color-neutral-900: #1A1A1A;  /* Near black - body text */
  --color-neutral-100: #F5F5F5;  /* Light gray - backgrounds */

  /* Semantic Usage */
  --color-text-primary: var(--color-neutral-900);
  --color-text-on-primary: #FFFFFF;
  --color-background: var(--color-neutral-100);
  --color-cta: var(--color-primary-600);
}
```
