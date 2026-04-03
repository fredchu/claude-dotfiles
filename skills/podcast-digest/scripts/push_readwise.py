#!/usr/bin/env python3
"""Push a podcast digest to Readwise Reader.

Usage:
    python3 push_readwise.py transcript.md --metadata metadata.json --summary "..."

As module:
    from push_readwise import push_to_readwise
    result = push_to_readwise(md_path, metadata, summary, tags)

Handles:
- Markdown → semantic HTML via md2html.py
- Cover image URL from metadata.json (pre-verified)
- Summary (required, ≤200 chars)
- image_url + summary must be in the FIRST POST (Readwise won't update them later)
"""

import argparse
import json
import os
import sys

# Import sibling module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md2html import md_to_html


def push_to_readwise(
    md_path: str,
    slug: str,
    title: str,
    summary: str,
    cover_url: str = "",
    tags: list[str] | None = None,
) -> dict:
    """Push markdown file to Readwise Reader as HTML article.

    Returns dict with 'id' and 'url' from Readwise API.
    Raises on HTTP error.
    """
    token_path = os.path.expanduser("~/.readwise-cli.json")
    with open(token_path) as f:
        token = json.load(f)["access_token"]

    with open(md_path) as f:
        html = md_to_html(f.read())

    payload = {
        "url": f"https://podscribe.local/{slug}",
        "title": title,
        "html": html,
        "category": "article",
        "tags": tags or ["podscribe", "podcast"],
    }
    if cover_url:
        payload["image_url"] = cover_url
    if summary:
        payload["summary"] = summary

    import requests
    resp = requests.post(
        "https://readwise.io/api/v3/save/",
        headers={"Authorization": f"Token {token}"},
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Push podcast digest to Readwise Reader")
    parser.add_argument("md_path", help="Path to markdown transcript")
    parser.add_argument("--slug", required=True, help="URL slug")
    parser.add_argument("--title", required=True, help="Article title")
    parser.add_argument("--summary", required=True, help="2-3 sentence summary (≤200 chars)")
    parser.add_argument("--metadata", help="Path to metadata.json (for cover_url)")
    parser.add_argument("--tags", nargs="*", default=["podscribe", "podcast"], help="Tags")
    args = parser.parse_args()

    cover_url = ""
    if args.metadata:
        with open(args.metadata) as f:
            meta = json.load(f)
            cover_url = meta.get("cover_url", "")

    result = push_to_readwise(
        md_path=args.md_path,
        slug=args.slug,
        title=args.title,
        summary=args.summary,
        cover_url=cover_url,
        tags=args.tags,
    )
    print(f"ID: {result.get('id')}")
    print(f"URL: {result.get('url')}")
