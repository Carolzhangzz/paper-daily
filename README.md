# Paper Daily

A zero-maintenance daily digest of the latest HCI and AI research papers — auto-fetched, statically hosted, and always up to date.

**[Read today's papers →](https://carolzhangzz.github.io/paper-daily/)**

## What it does

Every morning, a GitHub Actions workflow pulls the latest papers from two sources and publishes them as a clean, browsable static site on GitHub Pages:

| Source | What it fetches |
|---|---|
| **arXiv API** | Recent submissions in `cs.HC` · `cs.AI` · `cs.CL` · `cs.LG` |
| **HuggingFace Daily Papers** | Community-upvoted trending papers |

No backend. No database. No server to maintain. Just a cron job, some JSON files, and a single HTML page.

## Features

- **Category filters** — switch between HCI, AI, NLP, ML, and Trending tabs
- **Search** — full-text search across titles and abstracts
- **Bookmarks** — star papers to save them (stored in browser localStorage)
- **Date navigation** — browse the past 30 days of papers
- **One-click access** — direct links to PDF and arXiv page for every paper
- **Mobile-friendly** — responsive layout, works on any device

## How it works

```
GitHub Actions (daily cron)
        │
        ▼
  fetch_papers.py
  ├── arXiv API  ──→  200 papers
  └── HuggingFace ──→  ~50 papers
        │
        ▼
  data/YYYY-MM-DD.json  ──→  git commit + push
        │
        ▼
  GitHub Pages serves index.html
  (reads JSON client-side, zero backend)
```

The workflow runs daily at **7:00 AM Pacific Time**. Papers are stored as flat JSON files under `data/`, with a rolling 30-day window.

## Project structure

```
paper-daily/
├── index.html                  # Static frontend (Tailwind CSS)
├── fetcher.py                  # arXiv + HuggingFace fetch logic
├── scripts/
│   └── fetch_papers.py         # Entry point for GitHub Actions
├── data/
│   ├── dates.json              # Index of available dates
│   └── YYYY-MM-DD.json         # Papers for each day
├── .github/workflows/
│   └── fetch.yml               # Daily cron workflow
└── requirements.txt
```

## Run it yourself

Fork this repo and enable GitHub Pages (Settings → Pages → Source: `main`, folder: `/`). The Actions workflow will run automatically on schedule. You can also trigger it manually from the Actions tab.

To customize the categories, edit the `CATEGORIES` list in `fetcher.py`:

```python
CATEGORIES = ["cs.HC", "cs.AI", "cs.CL", "cs.LG"]
```

## Local development

```bash
# Fetch papers locally
python3 scripts/fetch_papers.py

# Serve the site
python3 -m http.server 8000
# Open http://localhost:8000
```

## License

MIT
