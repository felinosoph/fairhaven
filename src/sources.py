"""News source fetchers (Hacker News and ArXiv)."""

from urllib.parse import quote
from xml.etree import ElementTree as ET
import requests
from typing import Any, Optional


def fetch_json(url: str) -> Optional[Any]:
    """Fetch JSON from a URL using `requests` and return the decoded object, or None on error."""
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"JSON fetch error from {url}: {e}")
        return None


def fetch_hn_top_ids() -> Optional[list[int]]:
    """Return top story IDs from Hacker News, or None on error."""
    return fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")


def fetch_hn_item(story_id: int) -> Optional[dict[str, Any]]:
    """Fetch a Hacker News item by id and return its JSON dict, or None."""
    return fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")


def fetch_arxiv_ai_papers(max_results: int = 100) -> Optional[list[dict[str, Any]]]:
    """Fetch recent AI-related ArXiv papers.

    Returns a list of dictionaries with keys like `id`, `title`, `summary`, `url`,
    `published`, `updated`, `authors`, and `category`.
    """
    import time

    query = "(cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:stat.ML OR cat:cs.RO)"
    url = (
        "https://export.arxiv.org/api/query?"
        f"search_query={quote(query)}&"
        f"start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    )
    try:
        # ArXiv requires a descriptive User-Agent and respects rate limits
        headers = {
            "User-Agent": "ArXivBot/1.0 (compatible with requests; +http://example.com/bot)"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        time.sleep(1)  # Respect ArXiv's rate limit (3 requests per second max)
    except Exception as e:
        print(f"ArXiv fetch error: {e}")
        return None

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    papers: list[dict[str, Any]] = []

    # Debug: count total entries in response
    all_entries = root.findall("atom:entry", ns)
    print(
        f"[ArXiv] Found {len(all_entries)} entries in API response (requested max: {max_results})"
    )

    for entry in all_entries:
        try:
            paper_id = entry.findtext("atom:id", default="", namespaces=ns)
            title = (
                entry.findtext("atom:title", default="", namespaces=ns) or ""
            ).strip()
            summary = (
                entry.findtext("atom:summary", default="", namespaces=ns) or ""
            ).strip()
            published = entry.findtext("atom:published", default="", namespaces=ns)
            updated = entry.findtext("atom:updated", default="", namespaces=ns)
            authors = [
                author.findtext("atom:name", default="", namespaces=ns)
                for author in entry.findall("atom:author", ns)
            ]
            primary_category = entry.find("arxiv:primary_category", ns)
            category = (
                primary_category.attrib.get("term", "")
                if primary_category is not None
                else ""
            )
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("title") == "pdf":
                    pdf_url = link.attrib.get("href", "")
                    break
            if not pdf_url and paper_id:
                paper_id_tail = paper_id.rsplit("/", 1)[-1]
                pdf_url = f"https://arxiv.org/pdf/{paper_id_tail}.pdf"

            papers.append(
                {
                    "id": paper_id.rsplit("/", 1)[-1] if paper_id else "",
                    "title": title,
                    "summary": summary,
                    "url": pdf_url or paper_id,
                    "published": published,
                    "updated": updated,
                    "authors": authors,
                    "category": category,
                }
            )
        except Exception as e:
            print(f"[ArXiv] Error parsing entry: {e}")
            continue

    print(f"[ArXiv] Successfully parsed {len(papers)} papers")
    return papers


if __name__ == "__main__":
    # Quick test
    print("Testing ArXiv fetcher...")
    papers = fetch_arxiv_ai_papers(max_results=100)
    if papers:
        print(f"\nRetrieved {len(papers)} papers:")
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['title'][:60]}...")
            print(f"   ID: {paper['id']}, Category: {paper['category']}")
    else:
        print("Failed to fetch papers")
