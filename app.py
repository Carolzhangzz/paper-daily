"""Paper Daily - Local daily HCI & AI paper reader."""

import json
import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from fetcher import fetch_arxiv_papers, fetch_hf_daily_papers

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "papers.db")

app = Flask(__name__)


# ── Database ──────────────────────────────────────────────────────────────────


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS papers (
                arxiv_id    TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                authors     TEXT DEFAULT '[]',
                abstract    TEXT DEFAULT '',
                categories  TEXT DEFAULT '[]',
                url         TEXT DEFAULT '',
                pdf_url     TEXT DEFAULT '',
                published   TEXT DEFAULT '',
                source      TEXT DEFAULT 'arxiv',
                fetched_date TEXT NOT NULL,
                starred     INTEGER DEFAULT 0
            )"""
        )


# ── Fetch logic ───────────────────────────────────────────────────────────────


def do_fetch(date=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    print(f"[INFO] Fetching papers for {date} ...")
    papers = []
    try:
        papers.extend(fetch_arxiv_papers())
        print(f"[INFO] arXiv: {len(papers)} papers")
    except Exception as e:
        print(f"[WARN] arXiv fetch failed: {e}")

    try:
        hf = fetch_hf_daily_papers()
        papers.extend(hf)
        print(f"[INFO] HuggingFace: {len(hf)} papers")
    except Exception as e:
        print(f"[WARN] HF fetch failed: {e}")

    count = 0
    with get_db() as conn:
        for p in papers:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO papers
                       (arxiv_id,title,authors,abstract,categories,url,pdf_url,published,source,fetched_date)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    [
                        p["arxiv_id"],
                        p["title"],
                        json.dumps(p["authors"]),
                        p["abstract"],
                        json.dumps(p["categories"]),
                        p["url"],
                        p["pdf_url"],
                        p["published"],
                        p["source"],
                        date,
                    ],
                )
                count += 1
            except Exception:
                pass
    print(f"[INFO] Stored {count} new papers")
    return count


def auto_fetch_if_needed():
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM papers WHERE fetched_date = ?", [today]
        ).fetchone()[0]
    if n == 0:
        do_fetch(today)
    else:
        print(f"[INFO] Already have {n} papers for today")


# ── Routes ────────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/papers")
def api_papers():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    category = request.args.get("category", "all")
    search = request.args.get("q", "")

    with get_db() as conn:
        if category == "starred":
            query = "SELECT * FROM papers WHERE starred = 1"
            params = []
        else:
            query = "SELECT * FROM papers WHERE fetched_date = ?"
            params = [date]
            if category != "all":
                query += ' AND categories LIKE ?'
                params.append(f'%"{category}"%')

        if search:
            query += " AND (title LIKE ? OR abstract LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY source DESC, published DESC"
        papers = [dict(r) for r in conn.execute(query, params).fetchall()]

    for p in papers:
        p["authors"] = json.loads(p["authors"])
        p["categories"] = json.loads(p["categories"])

    return jsonify(papers)


@app.route("/api/dates")
def api_dates():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT fetched_date FROM papers ORDER BY fetched_date DESC LIMIT 30"
        ).fetchall()
    return jsonify([r["fetched_date"] for r in rows])


@app.route("/api/stats")
def api_stats():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM papers WHERE fetched_date = ?", [date]
        ).fetchone()[0]
        cats = {}
        for key in ["cs.HC", "cs.AI", "cs.CL", "cs.LG", "trending"]:
            cats[key] = conn.execute(
                'SELECT COUNT(*) FROM papers WHERE fetched_date = ? AND categories LIKE ?',
                [date, f'%"{key}"%'],
            ).fetchone()[0]
        starred = conn.execute(
            "SELECT COUNT(*) FROM papers WHERE starred = 1"
        ).fetchone()[0]
    return jsonify({"total": total, "categories": cats, "starred": starred})


@app.route("/api/star/<path:paper_id>", methods=["POST"])
def toggle_star(paper_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT starred FROM papers WHERE arxiv_id = ?", [paper_id]
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE papers SET starred = ? WHERE arxiv_id = ?",
                [0 if row["starred"] else 1, paper_id],
            )
    return jsonify({"ok": True})


@app.route("/api/fetch", methods=["POST"])
def trigger_fetch():
    count = do_fetch()
    return jsonify({"ok": True, "count": count})


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    auto_fetch_if_needed()
    print("=" * 50)
    print("  Paper Daily running at http://127.0.0.1:5188")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5188, debug=False)
