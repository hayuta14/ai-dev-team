# Extract Design Guidelines from Existing Assets

Reverse-engineer design principles from images (and video frames) to establish design guidelines. Claude does this itself: `Read` the image, answer the checklist, write the result to `docs/design-guidelines/`. No external API.

## Purpose

- Analyze competitor designs to understand their approach
- Extract design systems from inspiration screenshots
- Learn from high-quality design examples
- Create documented guidelines based on visual analysis
- Establish consistent aesthetic direction from references

## Use Cases

- Analyzing competitor websites or apps
- Learning from inspiration galleries (Dribbble, Awwwards, Mobbin)
- Extracting design systems from brand materials
- Reverse-engineering successful interfaces
- Creating design documentation from visual references

## What Claude Vision Can and Cannot Do

- **Good at**: layout structure, hierarchy, component patterns, spacing rhythm (relative), aesthetic direction, mood, copy, icon style, likely font category.
- **Estimates only**: hex colors read by eye, px sizes, font family names, line-heights. Label them as estimates in the output. Measure instead of guess when it matters: dominant colors and single-pixel samples via ImageMagick (see `extraction-best-practices.md`).
- **Tiny text / dense UI**: crop and zoom the region (`magick in.png -crop WxH+X+Y +repage -resize 200% crop.png`), then `Read` the crop.
- **Exact values**: ask the user for the source file, Figma tokens, or the live URL (then read computed styles with the `chrome-devtools` skill) when the design must match 1:1.
- **Video / motion**: Claude cannot watch video. Extract frames with `media-processing` (`ffmpeg -i demo.mp4 -vf fps=10 frames/f-%03d.png`), `Read` the frames, and derive timing from frame numbers (frame index / fps). Timings are approximate.

## Quick Workflows

### Single Image Analysis
1. `Read` `docs/inspiration/reference-design.png`.
2. Answer the comprehensive checklist in `extraction-prompts.md`.
3. Write the result to `docs/design-guidelines/extracted-design.md` using `extraction-output-templates.md`.

### Multi-Screen System Extraction
1. `Read` each screen (`home.png`, `about.png`, ...), one by one.
2. Answer the multi-screen checklist in `extraction-prompts.md`: shared tokens first, then variations.
3. Write `docs/design-guidelines/complete-design-system.md`.

### Motion Analysis (from a recording)
1. Extract frames with `ffmpeg` (see above), then `Read` the key frames in order.
2. Answer the motion checklist in `extraction-prompts.md`; mark timings as approximate.
3. Write `docs/design-guidelines/motion-system.md`.

### Competitive Analysis
1. `Read` each competitor screenshot.
2. Answer the competitive checklist in `extraction-prompts.md`.
3. Write `docs/design-guidelines/competitive-analysis.md`.

## Detailed References

- `extraction-prompts.md` - Checklists Claude answers after reading the image
- `extraction-best-practices.md` - Capture quality, measuring colors, analysis tips
- `extraction-output-templates.md` - Documentation formats

## Integration

After extraction, use the guidelines with `asset-generation.md` to make design-aligned visual assets.
