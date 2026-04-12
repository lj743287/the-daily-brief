import json
import html
from pathlib import Path

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data"

SECTION_ORDER = [
    "World",
    "Markets & Economy",
    "Business",
    "UK",
    "Science & Technology",
    "Sport",
]


def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_homepage_page(updated_time, at_a_glance_items, lead_story, story_cards, feature, section_features):
    feature_html = ""
    if feature:
        feature_html = f"""
        <section class="feature-block">
          <div class="feature-label">Daily Long Read</div>
          <h2><a href="{feature['url']}">{html.escape(feature['title'])}</a></h2>
          <p class="feature-standfirst">{html.escape(feature['standfirst'])}</p>
        </section>
        """

    lead_html = ""
    if lead_story:
        thumb_html = ""
        if lead_story.get("thumbnail_url"):
            thumb_html = f'<img class="lead-image" src="{html.escape(lead_story["thumbnail_url"])}" alt="{html.escape(lead_story["title"])}">'
        published_html = ""
        if lead_story.get("published_at"):
            published_html = f'<div class="published-line">Published: {html.escape(lead_story["published_at"])}</div>'
        lead_html = f"""
        <section class="lead-story">
          {thumb_html}
          <div class="lead-meta">{html.escape(lead_story['section'])} | {html.escape(lead_story['story_type'])}</div>
          {published_html}
          <h2><a href="{lead_story['url']}">{html.escape(lead_story['title'])}</a></h2>
          <p>{html.escape(lead_story['summary'])}</p>
        </section>
        """

    grouped = {section: [] for section in SECTION_ORDER}
    for card in story_cards:
        grouped.setdefault(card["section"], []).append(card)

    world_html = ""
    world_cards = grouped.get("World", [])
    if world_cards:
        lead_card = world_cards[0]
        tail_cards = world_cards[1:]

        thumb_html = ""
        if lead_card.get("thumbnail_url"):
            thumb_html = f'<img class="section-lead-image" src="{html.escape(lead_card["thumbnail_url"])}" alt="{html.escape(lead_card["title"])}">'

        world_tail = "\n".join(
            f"""
            <article class="story-card">
              <div class="story-meta">{html.escape(card['story_type'])}</div>
              {'<div class="published-line">Published: ' + html.escape(card['published_at']) + '</div>' if card.get('published_at') else ''}
              <h4><a href="{card['url']}">{html.escape(card['title'])}</a></h4>
              <p>{html.escape(card['summary'])}</p>
            </article>
            """
            for card in tail_cards
        )

        world_html = f"""
        <section class="news-section">
          <h2>World News</h2>
          <article class="section-lead-card">
            {thumb_html}
            <div class="story-meta">{html.escape(lead_card['story_type'])}</div>
            {'<div class="published-line">Published: ' + html.escape(lead_card['published_at']) + '</div>' if lead_card.get('published_at') else ''}
            <h3><a href="{lead_card['url']}">{html.escape(lead_card['title'])}</a></h3>
            <p>{html.escape(lead_card['summary'])}</p>
          </article>
          {world_tail}
        </section>
        """

    features_html = ""
    if section_features:
        feature_cards_html = "\n".join(
            f"""
            <article class="mini-feature-card">
              <div class="mini-feature-label">{html.escape(item['label'])}</div>
              <h3><a href="{item['url']}">{html.escape(item['title'])}</a></h3>
              <p>{html.escape(item['standfirst'])}</p>
            </article>
            """
            for item in section_features
        )
        features_html = f"""
        <section class="mini-features">
          <h2>Features</h2>
          <div class="mini-features-grid">
            {feature_cards_html}
          </div>
        </section>
        """

    glance_html = "\n".join(f"<li>{html.escape(item)}</li>" for item in at_a_glance_items)

    remaining_sections_html_parts = []

    for section in SECTION_ORDER:
        if section == "World":
            continue

        cards = grouped.get(section, [])
        if not cards:
            continue

        lead_card = cards[0]
        tail_cards = cards[1:]

        section_lead_thumb = ""
        if lead_card.get("thumbnail_url"):
            section_lead_thumb = f'<img class="section-lead-image" src="{html.escape(lead_card["thumbnail_url"])}" alt="{html.escape(lead_card["title"])}">'

        section_lead_published = ""
        if lead_card.get("published_at"):
            section_lead_published = f'<div class="published-line">Published: {html.escape(lead_card["published_at"])}</div>'

        section_lead_html = f"""
        <article class="section-lead-card">
          {section_lead_thumb}
          <div class="story-meta">{html.escape(lead_card['story_type'])}</div>
          {section_lead_published}
          <h3><a href="{lead_card['url']}">{html.escape(lead_card['title'])}</a></h3>
          <p>{html.escape(lead_card['summary'])}</p>
        </article>
        """

        tail_html = "\n".join(
            f"""
            <article class="story-card">
              <div class="story-meta">{html.escape(card['story_type'])}</div>
              {'<div class="published-line">Published: ' + html.escape(card['published_at']) + '</div>' if card.get('published_at') else ''}
              <h4><a href="{card['url']}">{html.escape(card['title'])}</a></h4>
              <p>{html.escape(card['summary'])}</p>
            </article>
            """
            for card in tail_cards
        )

        remaining_sections_html_parts.append(
            f"""
            <section class="news-section">
              <h2>{html.escape(section)}</h2>
              {section_lead_html}
              {tail_html}
            </section>
            """
        )

    remaining_sections_html = "\n".join(remaining_sections_html_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Daily Brief</title>
  <style>
    body {{
      margin: 0;
      background: #f3efe7;
      color: #111;
      font-family: Georgia, "Times New Roman", serif;
    }}
    .page {{
      max-width: 1080px;
      margin: 0 auto;
      background: #fffdf8;
      min-height: 100vh;
      padding: 32px 22px 60px;
      box-shadow: 0 0 18px rgba(0,0,0,0.08);
    }}
    header {{
      border-bottom: 3px solid #111;
      margin-bottom: 28px;
      padding-bottom: 14px;
    }}
    h1 {{
      margin: 0;
      font-size: 3rem;
      line-height: 1.1;
    }}
    .updated, .published-line {{
      margin-top: 8px;
      color: #666;
      font-size: 0.92rem;
    }}
    .feature-block {{
      margin-top: 18px;
      margin-bottom: 30px;
      padding: 22px;
      background: #f8f3e8;
      border-left: 5px solid #111;
    }}
    .feature-label, .mini-feature-label {{
      font-size: 0.85rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #666;
      margin-bottom: 10px;
    }}
    .feature-block h2, .mini-features h2 {{
      margin: 0 0 12px 0;
      padding: 0;
      border: 0;
      font-size: 2rem;
      line-height: 1.2;
    }}
    .feature-block a, .mini-feature-card a {{
      color: #111;
      text-decoration: none;
    }}
    .feature-block a:hover, .mini-feature-card a:hover {{
      text-decoration: underline;
    }}
    .feature-standfirst {{
      margin: 0;
      font-size: 1.08rem;
      line-height: 1.8;
      color: #333;
    }}
    .mini-features {{
      margin-bottom: 34px;
    }}
    .mini-features-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 18px;
    }}
    .mini-feature-card {{
      border: 1px solid #e3ddd2;
      padding: 18px;
      background: #faf7f0;
    }}
    .mini-feature-card h3 {{
      margin: 0 0 10px 0;
      font-size: 1.35rem;
      line-height: 1.25;
    }}
    .mini-feature-card p {{
      margin: 0;
      font-size: 1rem;
      line-height: 1.7;
      color: #333;
    }}
    .lead-story {{
      margin-bottom: 34px;
      padding-bottom: 26px;
      border-bottom: 1px solid #ddd;
    }}
    .lead-image, .section-lead-image {{
      width: 100%;
      max-width: 360px;
      height: auto;
      display: block;
      margin-bottom: 14px;
      background: #e9e3d7;
    }}
    .lead-meta,
    .story-meta {{
      font-size: 0.82rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #666;
      margin-bottom: 8px;
    }}
    .lead-story h2 {{
      margin: 8px 0 14px 0;
      font-size: 2.4rem;
      line-height: 1.12;
    }}
    .lead-story a {{
      color: #111;
      text-decoration: none;
    }}
    .lead-story a:hover {{
      text-decoration: underline;
    }}
    .lead-story p {{
      margin: 0;
      font-size: 1.12rem;
      line-height: 1.85;
      color: #222;
    }}
    .glance-section h2,
    .news-section h2 {{
      margin-top: 34px;
      margin-bottom: 14px;
      padding-top: 14px;
      border-top: 1px solid #ddd;
      font-size: 1.7rem;
      line-height: 1.2;
    }}
    ul {{
      margin: 0 0 20px 0;
      padding-left: 22px;
    }}
    li {{
      font-size: 1.05rem;
      line-height: 1.7;
      margin-bottom: 10px;
    }}
    .section-lead-card {{
      padding: 0 0 20px 0;
      margin: 0 0 20px 0;
      border-bottom: 1px solid #dcdcdc;
    }}
    .section-lead-card h3 {{
      margin: 8px 0 10px 0;
      font-size: 1.55rem;
      line-height: 1.25;
    }}
    .section-lead-card a,
    .story-card a {{
      color: #111;
      text-decoration: none;
    }}
    .section-lead-card a:hover,
    .story-card a:hover {{
      text-decoration: underline;
    }}
    .section-lead-card p {{
      margin: 0;
      font-size: 1.05rem;
      line-height: 1.8;
      color: #222;
    }}
    .story-card {{
      padding: 0 0 18px 0;
      margin: 0 0 18px 0;
      border-bottom: 1px solid #e6e6e6;
    }}
    .story-card h4 {{
      margin: 8px 0 8px 0;
      font-size: 1.18rem;
      line-height: 1.3;
    }}
    .story-card p {{
      margin: 0;
      font-size: 1rem;
      line-height: 1.72;
      color: #333;
    }}
  </style>
</head>
<body>
  <div class="page">
    <header>
      <h1>The Daily Brief</h1>
      <div class="updated">Updated: {updated_time} UTC</div>
    </header>

    {feature_html}
    {lead_html}
    {world_html}
    {features_html}

    <section class="glance-section">
      <h2>At a Glance</h2>
      <ul>
        {glance_html}
      </ul>
    </section>

    {remaining_sections_html}
  </div>
</body>
</html>
"""


def main():
    news_data = load_json(DATA_DIR / "stories.json")
    feature_data = load_json(DATA_DIR / "feature.json")

    if not news_data:
        raise RuntimeError("data/stories.json does not exist, so the homepage cannot be rebuilt.")

    homepage = build_homepage_page(
        updated_time=news_data.get("last_updated", ""),
        at_a_glance_items=news_data.get("at_a_glance", []),
        lead_story=news_data.get("lead_story"),
        story_cards=news_data.get("stories", []),
        feature=feature_data,
        section_features=news_data.get("section_features", []),
    )

    with open(BASE_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(homepage)

    print("Homepage rebuilt")


if __name__ == "__main__":
    main()
