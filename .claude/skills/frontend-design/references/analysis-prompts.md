# Analysis Checklists

Checklists for visual analysis and verification. Procedure: `Read` the image(s), then answer each item yourself in a short written report. Scores are judgment calls with a one-line reason; colors are estimates (measure with ImageMagick when it matters, see `extraction-best-practices.md`); contrast ratios are computed (`technical-accessibility.md`).

## Comprehensive Analysis Checklist

```
Read the asset, then analyze it comprehensively:

## Design Alignment
- Aesthetic Direction: [e.g., brutalist/minimalist/maximalist]
- Expected Style: [describe target aesthetic]
- Color Palette Target: [list expected colors]

## Evaluation Criteria
1. Visual Coherence: Does it match the intended aesthetic direction?
2. Color Analysis: List dominant colors (hex, estimated). Evaluate harmony and mood.
3. Composition: Analyze balance, focal points, negative space, visual flow.
4. Typography Compatibility: Rate suitability for overlaying text (consider contrast, busy areas).
5. Professional Quality: Rate 1-10 with justification.
6. Technical Assessment: Resolution quality, compression artifacts, aspect ratio correctness.

## Specific Feedback
- What works well?
- What specific elements need improvement?
- What would elevate this to 9/10 quality?

## Overall Rating: X/10
Provide final score with clear reasoning.
```

## Comparison Analysis Checklist

```
Read all 3 design variations, then compare them:

For each image, evaluate:
1. Aesthetic alignment with [design direction]
2. Color effectiveness
3. Composition strength
4. Text overlay suitability
5. Professional quality rating (1-10)

Then provide:
- Ranking: Best to worst with justification
- Recommendation: Which to use and why
- Hybrid suggestion: Best elements from each to combine
```

## Color Extraction Checklist

```
Extract the complete color palette from this image:

1. Identify 5-8 dominant colors with hex codes (estimated; confirm with ImageMagick histogram)
2. Classify each: primary, accent, neutral, or background
3. Suggest CSS variable names (e.g., --color-primary-500)
4. Evaluate color accessibility (compute WCAG contrast ratios from the hex values, don't eyeball)
5. Recommend which colors work for text, backgrounds, accents

Provide as structured data for easy CSS implementation.
```

## Integration Testing Checklist

```
Read the screenshot of the asset with UI elements overlaid:

1. Text Readability: Can all text be read clearly?
2. Contrast Issues: Identify any WCAG violations (compute ratios for the suspicious pairs)
3. Visual Hierarchy: Do buttons and CTAs stand out?
4. Spacing Problems: Any crowding or poor breathing room?
5. Responsive Concerns: Will this work on mobile at 9:16?

Provide specific recommendations for adjustments.
```

## A/B Testing Checklist

```
A/B test analysis (a design critique, not real user data; real A/B results need real traffic):

Design A: [minimalist approach]
Design B: [maximalist approach]

Compare for:
1. User attention capture (first 3 seconds)
2. Information hierarchy clarity
3. Emotional impact and brand perception
4. Conversion optimization potential
5. Target audience alignment ([describe audience])

Recommend which to A/B test in production and why.
```

## Quick Quality Check Template

```
Rate this asset 1-10 for:
1. Aesthetic quality
2. Color harmony
3. Composition balance
4. Professional polish

Overall: X/10. Brief justification.
```

## Comprehensive Evaluation Template

```
Comprehensive design asset evaluation:

## Aesthetic Alignment
- Target style: [describe]
- Actual style: [analyze]
- Match quality: [1-10]

## Technical Quality
- Resolution: [assess]
- Compression: [check artifacts]
- Aspect ratio: [verify]

## Color Analysis
- Dominant colors: [list hex codes]
- Harmony: [evaluate]
- Mood: [describe]

## Composition
- Balance: [analyze]
- Focal points: [identify]
- Negative space: [evaluate]

## Integration Readiness
- Text overlay: [rate 1-10]
- UI compatibility: [assess]
- Responsive suitability: [evaluate]

Overall Score: X/10
Key Strengths: [list]
Improvements Needed: [list]
```
