# dsh-academic-figure-ops

Figure rules for academic papers and reports, packaged as a DeepSeek Harness bundle. It answers one question that bites almost every paper: **will this text still be readable after the figure is squeezed into the page?**

Installing the bundle registers the `academic-figure-ops` skill, so the agent loads these rules whenever you ask it to draw, resize or check a figure.

## What it does

- **Font size is computed, not guessed.** The printed size follows `printed_pt = set_pt × text_width_cm ÷ exported_width_cm`. Set your page's text width once, then every figure is checked against it.
- **Three checks per export**: printed font size, effective resolution after scaling, and the actual pixel width of the file. A figure can pass one and fail the others; that gap is where "it looked fine on screen" comes from.
- **Chart type matches the message**, with an anti-pattern list for the usual mistakes (two y-axes, truncated axes, rainbow colormaps, decoration as data).
- **CFD post-processing conventions** for contour panels, colour bars and multi-case comparisons.
- **19 reproducible recipes** (`assets/case-gallery/`): every case ships a script, a case card explaining what it is good for, and a preview. All recipes use synthetic data with a fixed seed, so they run anywhere.

## What is inside

```
skills/academic-figure-ops/
├── SKILL.md                     the rules the agent reads
├── references/                  chart selection, hard parameters, anti-patterns,
│                                resolution & format, CFD patterns, schematics, QA
├── scripts/
│   ├── figstyle.py              the single implementation of the house style
│   ├── check_figure.py          read-only verifier for an exported figure
│   └── overlap_audit.py         finds overlapping labels/tick text
└── assets/case-gallery/         19 recipes + case cards + previews
```

## Install

**As a bundle (recommended)** — install `dsh-academic-figure-ops` from npm through Plugins → Add plugin, or from the plugin market once the listing is live. The bundle registers the skill for you.

**As a plain skill** — copy the directory and skip the bundle entirely:

```bash
cp -r skills/academic-figure-ops ~/.dsh/skills/
```

Either way the agent discovers `SKILL.md` and loads it on demand.

## Use

1. Open the skill, read `references/hard-params.md` for the defaults.
2. Measure the text width of your page (for A4 with 3.17 cm side margins it is 14.65 cm) and set it:
   - in code: `TEXT_WIDTH_CM = 14.65` or `set_style(text_width_cm=14.65)`
   - when verifying: `python check_figure.py --text-width-cm 14.65 figures/fig1.png`
3. Draw with `figstyle.py` so widths, fonts and colours stay consistent.
4. Before delivery run `check_figure.py`; it reports the printed size and the effective resolution and tells you which one fails.

Requirements: Python 3.10+, `matplotlib` (tested with 3.11) and `numpy` (tested with 2.4). Pillow is only needed by the verifier. Nothing else, no network access.

## Honest limits

- It checks whether a figure is **readable and correctly drawn**, not whether the science behind the numbers is right.
- The CFD section describes one common Fluent/CFD-Post workflow; other tools need their own steps for contour styling and colour-bar placement.
- The recipes use synthetic data to demonstrate layout. They are not datasets.
- No vendor software, no third-party image libraries and no copyrighted figure files are bundled or required.

## License and assets

Code, text and `icon.png` are MIT (see `LICENSE`). The 19 case previews are rendered by the bundled recipes from synthetic data and are covered by the same MIT license. No third-party figures are redistributed: the case cards describe a layout and the preview shows what this package's own code produces from it.

Product and company names mentioned (Fluent, ANSYS, matplotlib, DeepSeek Harness) are trademarks of their respective owners. This package is not affiliated with or endorsed by any of them.