# qlrisk Brand Kit

## Tagline

> **Every risk. One engine.**

Supporting line (hero / sub-headline):

> Market risk, counterparty credit risk and XVA — priced, shocked and measured on one QuantLib-powered core.

Short descriptor (package metadata, social cards):

> Unified market risk & counterparty credit risk analytics on QuantLib.

## The mark

A skewed loss distribution with its **tail highlighted** and a **quantile cut line**.

The same picture describes both halves of the platform:

| Reading | Cut line means | Tail means |
|---------|---------------|------------|
| Market risk | VaR quantile | Expected Shortfall region |
| Counterparty risk | PFE quantile | Exposure beyond the PFE level |

One distribution, one tail, every risk — the visual form of the tagline.

## Files

| File | Use |
|------|-----|
| `hero.svg` / `hero.png` | README / landing page banner (1280×340, dark — works on light and dark themes) |
| `logo-light.svg` / `.png` | Horizontal logo on light backgrounds |
| `logo-dark.svg` / `.png` | Horizontal logo on dark backgrounds |
| `logo-mark.svg`, `logo-mark-512.png` | App icon / avatar / social image |
| `favicon.svg` | Modern browsers (simplified mark tuned for 16–32 px) |
| `favicon.ico` | Legacy browsers (16, 32, 48 px) |
| `favicon-16.png`, `favicon-32.png` | PNG favicons |
| `apple-touch-icon.png` | iOS home screen (180 px) |
| `android-chrome-192.png` | Android / PWA manifest |
| `src/` | Editable sources with live `<text>` — the exported SVGs have text converted to paths so they render without the font installed |

HTML head snippet:

```html
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
```

## Palette

| Role | Hex |
|------|-----|
| Navy (primary / background) | `#0B1F3A` |
| Navy light (gradient top) | `#13315C` |
| Tail amber (accent — risk, the tail) | `#F5A524` |
| Sky blue (market-risk accent) | `#4FB3FF` |
| Wordmark "ql" — light bg | `#2D6CDF` |
| Wordmark "ql" — dark bg | `#7FB6FF` |
| Muted text — light bg / dark bg | `#4F6B8F` / `#A9BCD6` |

In the hero, blue pills denote market-risk capabilities and amber pills counterparty-risk/XVA capabilities.

## Typography

Inter (fallbacks: Segoe UI, Helvetica, Arial). Wordmark: "ql" Medium 500, "risk" ExtraBold 800, tracking −1.
The wordmark is always lowercase: **qlrisk**. In prose, "QLRisk" is acceptable.

## Regenerating exports

```bash
cd assets/branding
for f in logo-light logo-dark hero; do
  inkscape src/$f.svg --export-text-to-path --export-plain-svg -o $f.svg
done
inkscape src/favicon.svg -w 180 -o apple-touch-icon.png
```
