"""Fetch latest papers from arXiv and HuggingFace."""

import json
import urllib.request
import xml.etree.ElementTree as ET

ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}
CATEGORIES = ["cs.HC", "cs.AI", "cs.CL", "cs.LG"]


def fetch_arxiv_papers(max_results=200):
    cat_query = "+OR+".join(f"cat:{c}" for c in CATEGORIES)
    url = (
        f"{ARXIV_API}?search_query={cat_query}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={max_results}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "PaperDaily/1.0"})
    resp = urllib.request.urlopen(req, timeout=30)
    root = ET.fromstring(resp.read())

    papers = []
    for entry in root.findall("atom:entry", ARXIV_NS):
        paper = _parse_arxiv_entry(entry)
        if paper:
            papers.append(paper)
    return papers


def _parse_arxiv_entry(entry):
    ns = ARXIV_NS
    id_text = entry.find("atom:id", ns).text
    arxiv_id = id_text.split("/abs/")[-1]

    title = " ".join(entry.find("atom:title", ns).text.split())
    abstract = " ".join(entry.find("atom:summary", ns).text.split())
    authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
    categories = [
        c.get("term")
        for c in entry.findall("atom:category", ns)
        if c.get("term", "").startswith("cs.")
    ]

    pdf_url = ""
    for link in entry.findall("atom:link", ns):
        if link.get("title") == "pdf":
            pdf_url = link.get("href", "")
            break

    published = entry.find("atom:published", ns).text[:10]

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "categories": categories,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": pdf_url or f"https://arxiv.org/pdf/{arxiv_id}",
        "published": published,
        "source": "arxiv",
    }


def fetch_hf_daily_papers():
    """Fetch trending papers from HuggingFace Daily Papers, then enrich with arXiv categories."""
    try:
        url = "https://huggingface.co/api/daily_papers"
        req = urllib.request.Request(url, headers={"User-Agent": "PaperDaily/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())

        papers = []
        for item in data:
            p = item.get("paper", {})
            aid = p.get("id", "")
            if not aid:
                continue
            papers.append(
                {
                    "arxiv_id": aid,
                    "title": p.get("title", ""),
                    "authors": [
                        a.get("name", "") for a in p.get("authors", [])
                    ],
                    "abstract": p.get("summary", ""),
                    "categories": ["trending"],
                    "url": f"https://arxiv.org/abs/{aid}",
                    "pdf_url": f"https://arxiv.org/pdf/{aid}",
                    "published": (p.get("publishedAt", "") or "")[:10],
                    "source": "huggingface",
                }
            )

        # Enrich with real arXiv categories via batch lookup
        if papers:
            papers = _enrich_hf_categories(papers)

        return papers
    except Exception as e:
        print(f"[WARN] HuggingFace fetch failed: {e}")
        return []


def _enrich_hf_categories(papers):
    """Batch-query arXiv to get real categories for HuggingFace papers."""
    id_list = ",".join(p["arxiv_id"] for p in papers)
    url = f"{ARXIV_API}?id_list={id_list}&max_results={len(papers)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperDaily/1.0"})
        resp = urllib.request.urlopen(req, timeout=30)
        root = ET.fromstring(resp.read())

        # Build a map: arxiv_id -> [categories]
        cat_map = {}
        for entry in root.findall("atom:entry", ARXIV_NS):
            id_text = entry.find("atom:id", ARXIV_NS).text
            aid = id_text.split("/abs/")[-1].split("v")[0]  # strip version suffix
            cats = [
                c.get("term")
                for c in entry.findall("atom:category", ARXIV_NS)
                if c.get("term", "").startswith("cs.")
            ]
            cat_map[aid] = cats

        # Merge: keep "trending" tag + add real arXiv categories
        for p in papers:
            real_cats = cat_map.get(p["arxiv_id"], [])
            p["categories"] = list(dict.fromkeys(["trending"] + real_cats))

        enriched = sum(1 for p in papers if len(p["categories"]) > 1)
        print(f"[INFO] Enriched {enriched}/{len(papers)} HF papers with arXiv categories")
    except Exception as e:
        print(f"[WARN] arXiv category enrichment failed: {e}")

    return papers
