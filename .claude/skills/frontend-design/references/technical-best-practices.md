# Best Practices Checklists

Quality gates and checklists for asset workflows (SVG/CSS, supplied photos, placeholders).

## Asset Creation Workflow

### Before Creating Assets
- [ ] Defined clear aesthetic direction from design brief
- [ ] Extracted color palette and typography character
- [ ] Identified asset purpose and integration context
- [ ] Considered accessibility and text overlay needs

### During Creation
- [ ] Wrote a design-driven, contextual brief (not generic)
- [ ] Chose the asset path: SVG/CSS, user photo, or labelled placeholder
- [ ] Specified correct aspect ratio for use case
- [ ] Made multiple variations if exploring

### After Creation
- [ ] Rendered, Read, and scored the asset in context (≥ 7/10)
- [ ] Extracted exact color palette with hex codes
- [ ] Compared multiple variations and selected best
- [ ] Tested with overlaid text/UI elements
- [ ] Optimized file size for web performance
- [ ] Created responsive variants if needed
- [ ] Documented asset usage and guidelines

## Design Guideline Extraction Workflow

### When Analyzing Existing Designs
- [ ] Captured high-quality reference screenshots
- [ ] Read the references and answered the structured extraction checklist
- [ ] Extracted specific values (hex codes, px sizes, ms timings), labelled as estimates unless measured
- [ ] Analyzed multiple screens for pattern consistency
- [ ] Validated font guesses against Google Fonts (identification from images is approximate)
- [ ] Documented findings in actionable format
- [ ] Created CSS variable specifications
- [ ] Saved extracted guidelines in project docs/

## Quality Gates

### Never Proceed to Integration Without
- [ ] Visual analysis score ≥ 7/10
- [ ] Extracted color palette documented
- [ ] Accessibility contrast ratios computed and passed
- [ ] Responsive variants created
- [ ] File optimization completed
- [ ] Asset usage guidelines documented

## Final Checklist

Before considering any asset "done":
- [ ] Made from a design-driven brief (not generic)
- [ ] Looked at and scored ≥ 7/10
- [ ] Extracted color palette for CSS implementation
- [ ] Tested with UI overlays for readability
- [ ] Optimized for web (WebP/JPEG)
- [ ] Created responsive variants
- [ ] Documented usage guidelines
- [ ] Placeholders labelled and listed in the report
- [ ] Accessibility checks passed (contrast, alt text)
- [ ] Integrated into frontend with proper optimization

## Common Issues & Solutions

### Issue 1: Asset Too Generic
**Symptoms**: Looks like stock imagery or a default gradient, lacks design character
**Solution**:
- Anchor in a specific aesthetic movement and the subject's own world (materials, instruments, artifacts)
- Use more distinctive color directions and shape language
- Add contextual details that make it unique

### Issue 2: Inconsistent Design Language
**Symptoms**: Each asset feels unrelated
**Solution**:
- Drive every asset from the same CSS variables, stroke widths, and corner radii
- Document the design system from the first successful asset and reuse it
- Keep one aesthetic direction across the page

### Issue 3: Low Scores
**Symptoms**: Consistently scoring < 7/10
**Solutions**:
- Review the criteria: are they realistic?
- Study high-scoring references with the extraction workflow
- Fix the top 3 named weaknesses, then re-render and re-score

### Issue 4: Slow Iteration
**Symptoms**: Waiting too long for results
**Solutions**:
- Explore with SVG/CSS edits; they are instant and follow the CSS variables
- Render all variants at once and compare them in one pass

**Remember**: Design first, assets second. Context is king. Iterate. Look at the result. Demand specifics, not generalities.
