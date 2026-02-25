#!/usr/bin/env python3
"""Fetch papers and save as JSON for GitHub Pages deployment."""

import json
import os
import sys
from datetime import datetime

# Allow importing fetcher from parent dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fetcher import fetch_arxiv_papers, fetch_hf_daily_papers

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    papers = []
    try:
        arxiv = fetch_arxiv_papers()
        papers.extend(arxiv)
        print(f"[INFO] arXiv: {len(arxiv)} papers")
    except Exception as e:
        print(f"[WARN] arXiv fetch failed: {e}")

    try:
        hf = fetch_hf_daily_papers()
        papers.extend(hf)
        print(f"[INFO] HuggingFace: {len(hf)} papers")
    except Exception as e:
        print(f"[WARN] HF fetch failed: {e}")

    # Save today's papers
    filepath = os.path.join(DATA_DIR, f"{today}.json")
    with open(filepath, "w") as f:
        json.dump(papers, f, ensure_ascii=False)
    print(f"[INFO] Saved {len(papers)} papers to {filepath}")

    # Update dates index
    dates = sorted(
        [
            f.replace(".json", "")
            for f in os.listdir(DATA_DIR)
            if f.endswith(".json") and f != "dates.json"
        ],
        reverse=True,
    )

    # Keep only last 30 days
    for old in dates[30:]:
        os.remove(os.path.join(DATA_DIR, f"{old}.json"))
    dates = dates[:30]

    with open(os.path.join(DATA_DIR, "dates.json"), "w") as f:
        json.dump(dates, f)
    print(f"[INFO] Dates index updated: {len(dates)} days")


if __name__ == "__main__":
    main()
