"""Fetch Hacker News top stories, filter with OpenAI, and post to Discord."""

import datetime
from dotenv import load_dotenv

from src import discord_comm, storage, sources, ai_client, config

load_dotenv()
cfg = config.build_config()

discord_comm.configure(cfg)
storage.configure(cfg)
ai_client.configure(cfg)


def check_hacker_news() -> None:
    """Check Hacker News top stories and post interesting ones to Discord."""
    print(f"[{datetime.datetime.now()}] Fetching Hacker News...")

    top_story_ids = sources.fetch_hn_top_ids()
    if not top_story_ids:
        return
    for story_id in top_story_ids[:100]:
        story_key = str(story_id)
        if storage.is_processed(story_key):
            continue

        storage.mark_processed(story_key)

        story = sources.fetch_hn_item(story_id)
        if not story or story.get("type") != "story":
            continue

        title = story.get("title", "")
        url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
        text = story.get("text", "")

        is_match, accept_reason, reject_reason, summary = ai_client.analyze_story(
            title, url, text, source="hn"
        )

        if is_match:
            print(f"Found match: {title} — reason: {accept_reason}")
            discord_comm.send_embed(
                title=title,
                url=url,
                score=story.get("score", 0),
                story_id=story_id,
                source="Hacker News",
                accept_reason=accept_reason,
                summary=summary,
            )
        else:
            # Log why the story was rejected for debugging and tuning
            if reject_reason:
                if summary:
                    print(
                        f"Rejected: {title} — reason: {reject_reason} — summary: {summary}"
                    )
                else:
                    print(f"Rejected: {title} — reason: {reject_reason}")


def check_arxiv_ai_papers() -> None:
    """Check recent ArXiv AI papers and post worthwhile ones to Discord."""
    print(f"[{datetime.datetime.now()}] Fetching ArXiv papers...")

    papers = sources.fetch_arxiv_ai_papers(max_results=10)
    if not papers:
        return

    for paper in papers:
        paper_id = paper.get("id", "")
        if not paper_id:
            continue

        story_key = f"arxiv:{paper_id}"
        if storage.is_processed(story_key):
            continue

        storage.mark_processed(story_key)

        title = paper.get("title", "")
        url = paper.get("url", f"https://arxiv.org/abs/{paper_id}")
        abstract = paper.get("summary", "")

        authors = paper.get("authors", [])
        category = paper.get("category", "")
        paper_context = [f"Abstract: {abstract}"]
        if authors:
            paper_context.append(f"Authors: {', '.join(authors)}")
        if category:
            paper_context.append(f"Category: {category}")
        is_match, accept_reason, reject_reason, summary = ai_client.analyze_story(
            title,
            url,
            "\n\n".join(paper_context),
            source="arxiv",
        )

        if is_match:
            print(f"Found arXiv match: {title} — reason: {accept_reason}")
            discord_comm.send_embed(
                title=title,
                url=url,
                score=0,
                story_id=paper_id,
                source="ArXiv",
                accept_reason=accept_reason,
                summary=summary,
            )
        else:
            if reject_reason:
                if summary:
                    print(
                        f"Rejected arXiv: {title} — reason: {reject_reason} — summary: {summary}"
                    )
                else:
                    print(f"Rejected arXiv: {title} — reason: {reject_reason}")


def main():
    """Entry point: run Hacker News and ArXiv checks."""

    check_hacker_news()
    check_arxiv_ai_papers()


if __name__ == "__main__":
    main()
