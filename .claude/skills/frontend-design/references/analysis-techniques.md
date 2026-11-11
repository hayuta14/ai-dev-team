# Advanced Analysis Techniques

Advanced strategies for visual analysis and testing.

## Batch Analysis for Rapid Iteration

Compare several variations in one pass:

1. Produce 3 variations of the asset (for SVG/CSS assets, write 3 variants; cheap and fast).
2. Render each to PNG (`magick -density 144 var-1.svg var-1.png`, or screenshot the page with `chrome-devtools`).
3. `Read` all variations, rank them 1-3 with scores, and name the winner with a reason.
4. Record the ranking in `docs/assets/batch-analysis.md`.

## Contextual Testing

Test assets in actual UI context:

1. **Mock up UI overlay** (design tool or code)
2. **Capture screenshot** of the asset with real UI elements (`chrome-devtools` skill)
3. **`Read` the screenshot** and evaluate the integrated version:
   - Headline readability over the image
   - CTA button visibility and contrast
   - Navigation bar integration
   - Overall visual hierarchy effectiveness
4. Compute WCAG contrast ratios for the text/background pairs (`technical-accessibility.md`); do not estimate them by eye.

## A/B Testing Analysis

Compare design directions objectively: `Read` `design-a.png` and `design-b.png`, then use the A/B checklist in `analysis-prompts.md`. This is a design critique, not experiment data; it picks what to test, it does not replace testing.

## Iteration Strategy

When score < 6/10:

1. **Identify top 3 weaknesses** from the analysis
2. **Address each in the revised asset** (SVG/CSS edit)
3. **Cheapest variant first** (edit SVG/CSS)
4. **Re-analyze before committing** to the final version
5. **Iterate until score ≥ 7/10**

Example: first attempt scores 5/10 ("colors too muted, composition unbalanced"). Raise saturation of the palette tokens and recompose on a diagonal, re-render, `Read` again with the same criteria, compare scores.

## Documentation Strategy

Save analysis reports for design system documentation:

```
docs/
  assets/
    hero-image.png
    hero-analysis.md       # Analysis report
    hero-color-palette.md  # Extracted colors
  design-guidelines/
    asset-usage.md         # Guidelines derived from analysis
```
