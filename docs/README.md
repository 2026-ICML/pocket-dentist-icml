# Pocket-Dentist — Project Page

Static project page for **Pocket-Dentist: On-Device Dental Image Understanding via Efficient
Multimodal Large Language Models** (ICML 2026 EMM-QA Workshop).

The page content is generated from the current paper (`reference/arXiv/main.tex`) and styled after
the Academic Project Page Template (Nerfies).

## Structure

```
docs/
├── index.html              # the page
├── .nojekyll               # tells GitHub Pages to serve files as-is
└── static/
    ├── css/                # bulma.min.css, index.css
    ├── js/                 # fontawesome (SVG), bulma-carousel/slider, index.js
    └── images/             # pipeline.png, deployment.png, favicons
```

Icons render as inline SVG via `fontawesome.all.min.js`, so no icon webfonts are bundled.

## Deploy on GitHub Pages

1. Push this repository to GitHub.
2. **Settings → Pages → Build and deployment**: set *Source* = **Deploy from a branch**,
   *Branch* = `main`, *Folder* = `/docs`.
3. The page will be served at `https://<user>.github.io/pocket-dentist-icml/`
   (for this repo: https://kyle17888.github.io/pocket-dentist-icml/).

## Local preview

```bash
cd docs
python3 -m http.server 8123
# open http://localhost:8123/index.html
```

## Updating figures

- **Pipeline figure** comes from `reference/arXiv/assets/pipeline-v2.3.pdf`. To regenerate:
  ```bash
  pdftoppm -png -r 300 reference/arXiv/assets/pipeline-v2.3.pdf docs/static/images/pipeline
  sips --resampleWidth 2600 docs/static/images/pipeline-1.png --out docs/static/images/pipeline.png
  ```
- **Deployment screenshot** is `reference/arXiv/assets/deployment.png`.

## TODO before publishing

- Add the **Paper** PDF/arXiv link in the hero (currently `#`).
- Confirm the **Dataset** link (Hugging Face).
