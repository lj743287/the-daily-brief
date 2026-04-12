import os
import json
import datetime
import html
import re
from pathlib import Path

import feedparser
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data"
STORIES_DIR = BASE_DIR / "stories"

FEEDS = {
    "World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "UK": "https://feeds.bbci.co.uk/news/uk/rss.xml",
    "Science & Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "Sport": "https://feeds.bbci.co.uk/sport/rss.xml"
}

SECTION_ORDER = [
    "World",
    "Business",
    "UK",
    "Markets",
    "Science & Technology",
    "Sport"
]

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-") or "story"

def get_headline_signals():
    signals = []
    seen_titles = set()

    for section_name, url in FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:8]:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", "").strip()
            link = entry.get("link", "").strip()

            if not title:
                continue
            if title in seen_titles:
                continue

            seen_titles.add(title)
            signals.append({
                "section": section_name,
                "title": title,
                "summary": re.sub(r"<[^>]+>", "", summary).strip(),
                "link": link
            })

    return signals[:30]

def load_feature():
    feature_file = DATA_DIR / "feature.json"
    if not feature_file.exists():
        return None
    with open(feature_file, "r", encoding="utf-8") as f:
        return json.load(f)

def build_story_page(title, section, summary, body_html, updated_time):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} | The Daily Brief</title>
  <style>
    body {{
      margin: 0;
      background: #f3efe7;
      color: #111;
      font-family: Georgia, "Times New Roman", serif;
    }}
    .page {{
      max-width: 920px;
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
    .brand {{
      text-decoration: none;
      color: #111;
    }}
    h1 {{
      margin: 0;
      font-size: 3rem;
      line-height: 1.1;
    }}
    .updated {{
      margin-top: 10px;
      color: #666;
      font-size: 0.95rem;
    }}
    .back {{
      display: inline-block;
      margin-bottom: 22px;
      color: #333;
      text-decoration: none;
      font-size: 0.95rem;
    }}
    .back:hover {{
      text-decoration: underline;
    }}
    .section-label {{
      font-size: 0.85rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #666;
      margin-bottom: 10px;
    }}
    h2 {{
      margin-top: 0;
      margin-bottom: 16px;
      font-size: 2.4rem;
      line-height: 1.15;
    }}
    .standfirst {{
      font-size: 1.18rem;
      line-height: 1.75;
      color: #333;
      margin-bottom: 28px;
      font-style: italic;
    }}
    p {{
      font-size: 1.08rem;
      line-height: 1.9;
      margin: 0 0 18px 0;
    }}
  </style>
</head>
<body>
  <div class="page">
    <header>
      <a class="brand" href="../index.html"><h1>The Daily Brief</h1></a>
      <div class="updated">Updated: {updated_time} UTC</div>
    </header>
    <a class="back" href="../index.html">← Back to front page</a>
    <article>
      <div class="section-label">{html.escape(section)}</div>
      <h2>{html.escape(title)}</h2>
      <div class="standfirst">{html.escape(summary)}</div>
      {body_html}
    </article>
  </div>
</body>
</html>
"""

def build_homepage_page(updated_time, at_a_glance_items, story_cards, feature):
    glance_html = "\n".join(f"<li>{html.escape(item)}</li>" for item in at_a_glance_items)

    grouped = {section: [] for section in SECTION_ORDER}
    for card in story_cards:
        grouped.setdefault(card["section"], []).append(card)

    sections_html_parts = []
    for section in SECTION_ORDER:
        cards = grouped.get(section, [])
        if not cards:
            continue

        cards_html = "\n".join(
            f"""
            <article class="story-card">
              <h3><a href="{card['url']}">{html.escape(card['title'])}</a></h3>
              <p>{html.escape(card['summary'])}</p>
            </article>
            """
            for card in cards
        )

        section_html = f"""
        <section class="news-section">
          <h2>{html.escape(section)}</h2>
          {cards_html}
        </section>
        """
        sections_html_parts.append(section_html)

    sections_html = "\n".join(sections_html_parts)

    feature_html = ""
    if feature:
        feature_html = f"""
        <section class="feature-block">
          <div class="feature-label">Daily Long Read</div>
          <h2><a href="{feature['url']}">{html.escape(feature['title'])}</a></h2>
          <p class="feature-standfirst">{html.escape(feature['standfirst'])}</p>
        </section>
        """

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
      max-width: 980px;
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
    .updated {{
      margin-top: 10px;
      color: #666;
      font-size: 0.95rem;
    }}
    .feature-block {{
      margin-top: 18px;
      margin-bottom: 34px;
      padding: 22px;
      background: #f8f3e8;
      border-left: 5px solid #111;
    }}
    .feature-label {{
      font-size: 0.85rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #666;
      margin-bottom: 10px;
    }}
    .feature-block h2 {{
      margin: 0 0 12px 0;
      padding: 0;
      border: 0;
      font-size: 2rem;
      line-height: 1.2;
    }}
    .feature-block a {{
      color: #111;
      text-decoration: none;
    }}
    .feature-block a:hover {{
      text-decoration: underline;
    }}
    .feature-standfirst {{
      margin: 0;
      font-size: 1.08rem;
      line-height: 1.8;
      color: #333;
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
    .story-card {{
      padding: 0 0 20px 0;
      margin: 0 0 20px 0;
      border-bottom: 1px solid #e2e2e2;
    }}
    .story-card h3 {{
      margin: 0 0 10px 0;
      font-size: 1.5rem;
      line-height: 1.3;
    }}
    .story-card a {{
      color: #111;
      text-decoration: none;
    }}
    .story-card a:hover {{
      text-decoration: underline;
    }}
    .story-card p {{
      margin: 0;
      font-size: 1.05rem;
      line-height: 1.8;
      color: #222;
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

    <section class="glance-section">
      <h2>At a Glance</h2>
      <ul>
        {glance_html}
      </ul>
    </section>

    {sections_html}
  </div>
</body>
</html>
"""

signals = get_headline_signals()

prompt = f"""
You are writing The Daily Brief homepage package for a premium newspaper.

Use these latest source signals:
{json.dumps(signals, ensure_ascii=False, indent=2)}

Return valid JSON only in exactly this structure:

{{
  "at_a_glance": [
    "bullet 1",
    "bullet 2",
    "bullet 3",
    "bullet 4",
    "bullet 5",
    "bullet 6",
    "bullet 7",
    "bullet 8"
  ],
  "stories": [
    {{
      "section": "World",
      "title": "Story title",
      "summary": "A strong homepage standfirst in 3 to 4 sentences.",
      "body": [
        "Paragraph 1",
        "Paragraph 2",
        "Paragraph 3",
        "Paragraph 4",
        "Paragraph 5",
        "Paragraph 6",
        "Paragraph 7",
        "Paragraph 8"
      ]
    }},
    {{
      "section": "Business",
      "title": "Story title",
      "summary": "A strong homepage standfirst in 3 to 4 sentences.",
      "body": [
        "Paragraph 1",
        "Paragraph 2",
        "Paragraph 3",
        "Paragraph 4",
        "Paragraph 5",
        "Paragraph 6",
        "Paragraph 7",
        "Paragraph 8"
      ]
    }},
    {{
      "section": "UK",
      "title": "Story title",
      "summary": "A strong homepage standfirst in 3 to 4 sentences.",
      "body": [
        "Paragraph 1",
        "Paragraph 2",
        "Paragraph 3",
        "Paragraph 4",
        "Paragraph 5",
        "Paragraph 6",
        "Paragraph 7",
        "Paragraph 8"
      ]
    }},
    {{
      "section": "Markets",
      "title": "Story title",
      "summary": "A strong homepage standfirst in 3 to 4 sentences.",
      "body": [
        "Paragraph 1",
        "Paragraph 2",
        "Paragraph 3",
        "Paragraph 4",
        "Paragraph 5",
        "Paragraph 6",
        "Paragraph 7",
        "Paragraph 8"
      ]
    }},
    {{
      "section": "Science & Technology",
      "title": "Story title",
      "summary": "A strong homepage standfirst in 3 to 4 sentences.",
      "body": [
        "Paragraph 1",
        "Paragraph 2",
        "Paragraph 3",
        "Paragraph 4",
        "Paragraph 5",
        "Paragraph 6",
        "Paragraph 7",
        "Paragraph 8"
      ]
    }},
    {{
      "section": "Sport",
      "title": "Story title",
      "summary": "A strong homepage standfirst in 3 to 4 sentences.",
      "body": [
        "Paragraph 1",
        "Paragraph 2",
        "Paragraph 3",
        "Paragraph 4",
        "Paragraph 5",
        "Paragraph 6",
        "Paragraph 7",
        "Paragraph 8"
      ]
    }}
  ]
}}

Rules:
- British English
- Professional, serious newspaper tone
- No markdown
- No code fences
- No text outside the JSON
- Produce exactly 6 stories
- Use one story for each of these sections: World, Business, UK, Markets, Science & Technology, Sport
- The homepage summaries must feel weighty and informative, not breezy
- The body paragraphs should feel like proper reported copy with context, stakes, nuance and consequences
- Do not invent direct quotes
- If source signals are thin for Markets, infer the biggest market-moving theme from the wider business and world signals
"""

response = client.responses.create(
    model="gpt-5",
    input=prompt
)

raw = response.output_text.strip()
data = json.loads(raw)

now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

STORIES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

story_cards = []
saved_stories = []

for story in data["stories"]:
    title = story["title"].strip()
    section = story["section"].strip()
    summary = story["summary"].strip()
    body = [p.strip() for p in story["body"] if p.strip()]

    slug = slugify(title)
    filename = f"{slug}.html"
    story_url = f"stories/{filename}"

    body_html = "\n".join(f"<p>{html.escape(p)}</p>" for p in body)
    story_page = build_story_page(title, section, summary, body_html, now)

    with open(STORIES_DIR / filename, "w", encoding="utf-8") as f:
        f.write(story_page)

    story_cards.append({
        "section": section,
        "title": title,
        "summary": summary,
        "url": story_url
    })

    saved_stories.append({
        "section": section,
        "title": title,
        "summary": summary,
        "url": story_url,
        "body": body
    })

feature = load_feature()

homepage = build_homepage_page(
    updated_time=now,
    at_a_glance_items=data["at_a_glance"],
    story_cards=story_cards,
    feature=feature
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(homepage)

with open(DATA_DIR / "stories.json", "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": now,
        "source_signals": signals,
        "at_a_glance": data["at_a_glance"],
        "stories": saved_stories
    }, f, indent=2)

print("Homepage and story pages updated")
