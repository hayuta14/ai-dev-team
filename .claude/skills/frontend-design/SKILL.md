---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces from scratch or from a visual reference. Use this skill especially when the user provides screenshots/images/designs to replicate or draw inspiration from — Claude reads the reference image itself (Read tool, vision) and extracts design guidelines first, then implements code following those guidelines, avoiding generic AI aesthetics. For picking styles/palettes/fonts and design decisions use `ui-ux-pro-max`; for plain shadcn/Tailwind component implementation use `ui-styling`. Triggers (VI): "thiết kế giao diện", "làm UI".
license: Complete terms in LICENSE.txt
---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Input Types & Workflows

### When User Provides Screenshot/Image/Design Reference

**Workflow for screenshot/image/design inputs** (Claude reads the images itself, no external API; extract first, then code):

1. **Extract Design Guidelines** using `./references/design-extraction-overview.md`:
   - `Read` the image(s) (PNG/JPG/WebP; PDFs via `pages`). For tiny text or fine detail, crop and zoom first (`magick in.png -crop WxH+X+Y +repage -resize 200% crop.png`) and Read the crop.
   - Extract: colors (hex), typography (likely family/category, sizes, weights), spacing scale, layout grid, visual hierarchy, components. Hex values read by eye are **estimates**; for numbers computed from pixels use ImageMagick (see `./references/extraction-best-practices.md`), and ask the user for the source file or Figma tokens when exact values matter. Font identification is approximate: say so and offer 2-3 close alternatives.
   - Write findings to project `docs/design-guidelines/extracted-design.md` using `./references/extraction-output-templates.md`
   - Use the checklists in `./references/extraction-prompts.md`

2. **Implement Code** following extracted guidelines:
   - Use the extracted colors (hex); round to a clean token only when you say so
   - Match typography specifications (fonts, sizes, weights, line-heights)
   - Replicate layout structure and spacing system
   - Maintain visual hierarchy and component patterns
   - Preserve aesthetic direction and mood

3. **Verify Quality** using `./references/visual-analysis-overview.md`:
   - Render the implementation and take a screenshot with the `chrome-devtools` skill (`node <WS>/.claude/skills/chrome-devtools/scripts/screenshot.js --url <url> --output docs/screenshots/impl.png`; viewport is fixed 1920x1080, use `screenshot-at-viewport-with-overflow-check.mjs <url> <out.png> <w> <h>` for other sizes)
   - `Read` the original and the screenshot, compare side by side with the checklist: color accuracy, spacing consistency, typography matching, all elements preserved
   - Fix the differences, re-screenshot, re-compare

Record the extracted values before writing code; do not skip straight to implementation.

### When Building from Scratch (No Screenshot Provided)

Follow "Design Thinking" process below to create original design.

## Ground in the Subject

If the brief does not pin down what the product or subject is, pin it yourself before designing: name one concrete subject, its audience, and the page's single job, and state your choice. The subject's own world — its materials, instruments, artifacts, and vernacular — is where distinctive choices come from. Build with the brief's real content and subject matter throughout; generic briefs do not excuse generic design.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use the project's existing animation library; otherwise Motion for React, otherwise `anime.js` (`./references/animejs.md`). Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.
- **Visual Assets**: Default is assets Claude makes itself: SVG illustrations/icons/patterns, CSS gradients/noise/textures, user-supplied photos, or a clearly labelled placeholder. `media-processing` for resizing and background removal of supplied images.

## Working with Visual Assets

**Quick Start**: `./references/visual-assets-overview.md`

### Creating Visual Assets
Default path, no external service: Claude writes the asset.
- **SVG** for illustrations, icons, logos-as-shapes, geometric patterns, dividers (inline or `docs/assets/*.svg`)
- **CSS** for gradients, gradient meshes, noise/grain (SVG `feTurbulence`), layered transparencies, textures
- **User-supplied photos** when the brief or the user provides them
- **Labelled placeholder** when a photo or raster is truly needed: exact size/aspect ratio, intended content, and alt text, so it can be swapped later. State in your report which assets are placeholders.

There is no AI image generation: photographic or painterly rasters come from the user or stay labelled placeholders. Use `media-processing` for background removal, resizing, and format conversion.

### Analyzing Provided Screenshots/Images/Designs
When user provides screenshots, photos, or design references to analyze or replicate, `Read` them and use `./references/design-extraction-overview.md` to extract design guidelines BEFORE implementation. This is required for screenshot inputs (see "Input Types & Workflows" above).

**Workflows**:
- `./references/asset-generation.md` - Make design-aligned visual assets (SVG/CSS, supplied photos, placeholders)
- `./references/visual-analysis-overview.md` - Analyze and verify assets and implementations (modular)
- `./references/design-extraction-overview.md` - Extract guidelines from inspiration (modular)
- `./references/technical-overview.md` - Optimization and best practices (modular)

Each overview references detailed sub-modules for progressive disclosure.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

## Process: Brainstorm → Critique → Build

Work in two passes. First, brainstorm a compact design plan (color tokens, type roles, layout concept, signature element). Then **critique it before writing a single line of code**:

- Does any part read like the generic default you would produce for any similar page? If yes, revise that part and say what you changed and why.
- Does the palette, type choice, or layout concept appear regardless of subject matter? That's a default, not a choice.
- Only after confirming relative uniqueness of the plan should you start writing code — then follow the revised plan exactly.

**AI-slop defaults to actively avoid** (legitimate for some briefs, but defaults rather than choices — never spend creative freedom on these unless the brief explicitly calls for them):
1. Warm cream background (~#F4F1EA) + high-contrast serif display + terracotta accent
2. Near-black background + single bright acid-green or vermilion accent
3. Broadsheet layout with hairline rules, zero border-radius, dense newspaper-like columns
4. Italic serif accent words dropped into a sans headline
5. Numbered `01 / 02 / 03` section labels
6. Small uppercase monospace labels and eyebrows
7. Pill-shaped buttons and badges everywhere

Where the brief pins down a visual direction, follow it exactly — the brief's words always win, including when it asks for one of these looks. Where an axis is free, don't default to any of the above.

## Writing as Design Material

Words in a design exist for one reason: to make the experience easier to understand and use. See `./references/writing-as-design-material-copy-as-design-intent.md` for principles on active voice, specificity, failure states, and register.