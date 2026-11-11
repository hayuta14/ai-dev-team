# Accessibility Checks

WCAG compliance and accessibility guidelines for generated assets.

## Text Overlay Readability

### Color Contrast Ratios
- **WCAG AA**: 4.5:1 for normal text, 3:1 for large text
- **WCAG AAA**: 7:1 for normal text, 4.5:1 for large text

### Compute Contrast, Don't Eyeball It
Take the foreground/background hex values (for text over an image, sample the busiest/lightest area behind the text with ImageMagick: `magick in.png -depth 8 -format '#%[hex:p{X,Y}]' info:`) and compute the WCAG 2.x ratio:

```bash
python3 - <<'PY' '#1E40AF' '#FFFFFF'
import sys
def lum(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
a, b = sorted((lum(sys.argv[1]), lum(sys.argv[2])), reverse=True)
print('contrast %.2f:1' % ((a + 0.05) / (b + 0.05)))
PY
```
Compare against the thresholds above (AA 4.5:1 normal / 3:1 large; AAA 7:1 / 4.5:1). Hex values taken from an image are estimates; for borderline results (within ~0.3 of a threshold) re-sample or use the real design tokens.

### Testing Requirements
- Test across image variations
- Consider adding gradient overlays in code
- Add text shadows for increased legibility

### Alt Text Guidelines
- Describe the asset's purpose and mood
- Don't repeat visible text
- Keep concise (150 characters max)

## CSS Techniques for Accessibility

### Gradient Overlay for Text Readability
```css
.hero {
  position: relative;
  background-image: url('hero.webp');
}
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(0,0,0,0.3) 0%,
    rgba(0,0,0,0.6) 100%
  );
}
```

### Text Shadow for Contrast
```css
.hero-text {
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}
```

### Ensure Minimum Contrast
```css
.hero-cta {
  background: var(--color-primary-600);
  color: white; /* Ensure 4.5:1 contrast */
}
```

## Integration Testing Analysis

Check how the asset works with UI elements: screenshot the page with the text overlay (`chrome-devtools` skill), `Read` the screenshot, and answer:

1. Text Readability: Can all text be read clearly?
2. Contrast Issues: Compute the ratio for each text/background pair (script above); list WCAG violations
3. Visual Hierarchy: Do buttons and CTAs stand out?
4. Spacing Problems: Any crowding or poor breathing room?
5. Responsive Concerns: Does it work on mobile at 9:16? (screenshot at 360x800 with `screenshot-at-viewport-with-overflow-check.mjs`)

Give specific recommendations for adjustments.

## Next.js Integration Example

```tsx
// app/components/Hero.tsx
import Image from 'next/image'

export function Hero() {
  return (
    <section className="relative h-screen">
      {/* Background image with optimization */}
      <Image
        src="/assets/hero-desktop.webp"
        alt="Minimalist desert landscape"
        fill
        priority
        quality={85}
        className="object-cover"
        sizes="100vw"
      />

      {/* Gradient overlay for text readability */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/30 to-black/60" />

      {/* Content */}
      <div className="relative z-10 flex h-full items-center justify-center">
        <h1 className="text-6xl font-bold text-white drop-shadow-lg">
          Your Headline
        </h1>
      </div>
    </section>
  )
}
```

## Common Issues

### Issue: Poor Text Overlay Readability
**Symptoms**: Text hard to read over generated background
**Solutions**:
- Add CSS gradient overlay (see above)
- Rework the asset with a clean composition for text overlay (calmer area behind the text)
- Use darker/lighter areas strategically
- Add text shadows or backdrop-blur
