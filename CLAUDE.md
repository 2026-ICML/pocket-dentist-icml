# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is the **static project page** (academic "Nerfies"-style website) for the paper
*Pocket-Dentist: On-Device Dental Image Understanding via Efficient Multimodal Large Language Models*
(ICML 2026 EMM-QA Workshop). The only deployable code lives in `docs/`. There is **no application,
build step, package manager, or test suite** — it is hand-written HTML/CSS/JS plus vendored libraries.

The research artifacts the paper describes (curated QA pairs, prompts, parsers, deployment scripts)
are **not in this repo yet** — `src/` is empty and the top-level `README.md` notes they are undergoing
anonymization/compliance review. Do not fabricate them.

## Local preview

```bash
cd docs && python3 -m http.server 8123
# open http://localhost:8123/index.html
```

## Deploy

GitHub Pages, **Deploy from a branch**: branch `main`, folder `/docs`. `docs/.nojekyll` makes Pages
serve files as-is. Live URL: https://kyle17888.github.io/pocket-dentist-icml/. Just push to `main`.

## Architecture & where things live

- `docs/index.html` — the entire page (~1030 lines, single file). Sections alternate
  `hero is-small` (heading band) / `section hero is-light` (content): hero/abstract, datasets
  (`id="datasets"`), pipeline, results, deployment, and `id="BibTeX"`. Edit content here.
- `docs/static/css/index.css` — the only hand-written stylesheet. `bulma.min.css` is vendored — don't edit it.
- `docs/static/js/index.js` — the only hand-written script. Defines `toggleMoreWorks()` (header
  dropdown), `copyBibTeX()` (clipboard), `scrollToTop()`, and `IntersectionObserver`-based carousel
  video autoplay; on `$(document).ready` it attaches `bulmaCarousel` and `bulmaSlider`. jQuery and the
  `bulma-carousel`/`bulma-slider`/`fontawesome.all.min.js` files are vendored — don't edit them.
- FontAwesome icons render as **inline SVG** via `fontawesome.all.min.js` (no icon webfonts bundled).

## Content source of truth

Page copy, author list, numbers, and figures are derived from the paper LaTeX at
`reference/arXiv/main.tex` and the BibTeX block inside `index.html`. **`reference/` and `src/` are
gitignored** (see `.gitignore` line 1) so they won't appear in `git ls-files`, but `reference/` exists
locally and is the authoritative reference when updating claims, stats, author names, or the citation.
When changing factual content on the page, reconcile it against `reference/arXiv/main.tex`.

## Updating figures (from the paper's PDF assets)

```bash
# Pipeline figure
pdftoppm -png -r 300 reference/arXiv/assets/pipeline-v2.3.pdf docs/static/images/pipeline
sips --resampleWidth 2600 docs/static/images/pipeline-1.png --out docs/static/images/pipeline.png
# Deployment screenshot is reference/arXiv/assets/deployment.png
```

## Analytics — keep intact when editing links

The page uses GA4 (`gtag.js`, id `G-R7WYW79LNN`). A delegated click listener at the bottom of
`index.html` fires `click_resource` for links carrying a `data-track="..."` attribute (Paper / Code /
Datasets buttons) and `click_outbound` for any other external link. When adding or changing resource
buttons, preserve the `data-track` attribute so tracking continues to work.

## Reference material (gitignored, local-only)

- `reference/arXiv/` — full ICML 2026 LaTeX source, `refs.bib`, sty/bst files, and the camera-ready PDF.
- `reference/Pocket-Dentist-Bench/` — a **separate nested git repo**: the sibling benchmark project
  page. Useful as a styling/structure reference; not part of this repo's deploy.
