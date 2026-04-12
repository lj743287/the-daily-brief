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

SOURCE_FEEDS = [
    {
        "source": "BBC",
        "section": "World",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    },
    {
        "source": "BBC",
        "section": "Business",
        "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
    },
    {
        "source": "BBC",
        "section": "UK",
        "url": "https://feeds.bbci.co.uk/news/uk/rss.xml",
    },
    {
        "source": "BBC",
        "section": "Wales",
        "url": "https://feeds.bbci.co.uk/news/wales/rss.xml",
    },
    {
        "source": "BBC",
        "section": "Science & Technology",
        "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    },
    {
        "source": "BBC",
        "section": "Sport",
        "url": "https://feeds.bbci.co.uk/sport/rss.xml",
    },
    {
        "source": "The Guardian",
        "section": "World",
        "url": "https://www.theguardian.com/world/rss",
    },
    {
        "source": "The Guardian",
        "section": "Business",
        "url": "https://www.theguardian.com/business/rss",
    },
    {
        "source": "The Guardian",
        "section": "Science & Technology",
        "url": "https://www.theguardian.com/uk/technology/rss",
    },
    {
        "source": "The Guardian",
        "section": "Sport",
        "url": "https://www.theguardian.com/uk/sport/rss",
    },
    {
        "source": "AP",
        "section": "World",
        "url": "https://apnews.com/hub/apf-topnews?output=rss",
    },
]

SECTION_ORDER = [
    "World",
    "Markets & Economy",
    "Business",
    "UK",
    "Wales",
    "Science & Technology",
    "Sport",
]

STORY_TYPE_ORDER = [
    "News",
    "Analysis",
    "Explainer",
    "Profile",
    "Feature",
]

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\\s-]", "", text)
    text = re.sub(r"\\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-") or "story"

def clean_html(raw_text):
    if not raw_text:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_text)
    text = html.unescape(text)
    text = re.sub(r"\\s+", " ", text)
    return text.strip()

def normalise_title(title):
    text = title.lower().strip()
    text = re.sub(r"[^a-z0-9\\s]", "", text)
    text = re.sub(r"\\s+", " ", text)
    return text

def get_source_signals():
    signals = []
    seen_titles = set()

    for feed_info in SOURCE_FEEDS:
        parsed = feedparser.parse(feed_info["url"])

        for entry in parsed.entries[:8]:
            title = clean_html(entry.get("title", ""))
            summary = clean_html(entry.get("summary", ""))
            link = entry.get("link", "").strip()

            if not title:
                continue

            normalised = normalise_title(title)
            if normalised in seen_titles:
                continue

            seen_titles.add(normalised)

            signals.append({
                "source": feed_info["source"],
                "section": feed_info["section"],
                "title": title,
                "summary": summary,
                "link": link,
            })

    return signals[:50]

def load_feature():
    feature_file = DATA_DIR / "feature.json"
    if not feature_file.exists():
        return None
    with open(feature_file, "r", encoding="utf-8") as f:
        return json.load(f)

def build_story_page(title, section, story_type, summary, body_html, updated_time):
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
      max-width: 960px;
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
    .meta {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 12px;
      font-size: 0.85rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #666;
    }}
    .meta span {{
      display: inline-block;
    }}
    h2 {{
      margin-top: 0;
      margin-bottom: 16px;
      font-size: 2.5rem;
      line-height: 1.12;
    }}
    .standfirst {{
      font-size: 1.18rem;
      line-height: 1.8;
      color: #333;
      margin-bottom: 28px;
      font-style: italic;
    }}
    p {{
      font-size: 1.1rem;
      line-height: 1.95;
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
      <div class="meta">
        <span>{html.escape(section)}</span>
        <span>{html.escape(story_type)}</span>
      </div>
      <h2>{html.escape(title)}</h2>
      <div class="standfirst">{html.escape(summary)}</div>
      {body_html}
    </article>
  </div>
</body>
</html>
"""

def build_homepage_page(updated_time, at_a_glance_items, lead_story, story_cards, feature):
    feature_html = ""
    if feature:
        feature_html = f"""
        <section class="feature-block">
          <div class="feature-label">Daily Long Read</div>
          <h2><a href="{feature['url']}">{html.escape(feature['title'])}</a></h2>
          <p class="feature-standfirst">{html.escape(feature['standfirst'])}</p>
        </section>
        """

    glance_html = "\\n".join(f"<li>{html.escape(item)}</li>" for item in at_a_glance_items)

    lead_html = ""
    if lead_story:
        lead_html = f"""
        <section class="lead-story">
          <div class="lead-meta">{html.escape(lead_story['section'])} | {html.escape(lead_story['story_type'])}</div>
          <h2><a href="{lead_story['url']}">{html.escape(lead_story['title'])}</a></h2>
          <p>{html.escape(lead_story['summary'])}</p>
        </section>
        """

    grouped = {section: [] for section in SECTION_ORDER}
    for card in story_cards:
        grouped.setdefault(card["section"], []).append(card)

    sections_html_parts = []
    for section in SECTION_ORDER:
        cards = grouped.get(section, [])
        if not cards:
            continue

        cards_html = "\\n".join(
            f"""
            <article class="story-card">
              <div class="story-meta">{html.escape(card['story_type'])}</div>
              <h3><a href="{card['url']}">{html.escape(card['title'])}</a></h3>
              <p>{html.escape(card['summary'])}</p>
            </article>
            """
            for card in cards
        )

        sections_html_parts.append(
            f"""
            <section class="news-section">
              <h2>{html.escape(section)}</h2>
              {cards_html}
            </section>
            """
        )

    sections_html = "\\n".join(sections_html_parts)

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
      max-width: 1040px;
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
    .lead-story {{
      margin-bottom: 34px;
      padding-bottom: 26px;
      border-bottom: 1px solid #ddd;
    }}
    .lead-meta,
    .story-meta {{
      font-size: 0.82rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #666;
      margin-bottom: 10px;
    }}
    .lead-story h2 {{
      margin: 0 0 14px 0;
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
    .story-card {{
      padding: 0 0 20px 0;
      margin: 0 0 20px 0;
      border-bottom: 1px solid #e2e2e2;
    }}
    .story-card h3 {{
      margin: 0 0 10px 0;
      font-size: 1.45rem;
      line-height: 1.28;
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
      font-size: 1.04rem;
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

    {lead_html}

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

def coerce_story_type(story_type):
    if story_type in STORY_TYPE_ORDER:
        return story_type
    return "News"

def coerce_section(section):
    if section in SECTION_ORDER:
        return section
    return "World"

signals = get_source_signals()

prompt = f"""
You are the editor of The Daily Brief, a serious premium digital newspaper.

Your job is not to echo one national news agenda.
Your job is to select and rank the most important stories in the world, using the signals below.

SOURCE SIGNALS:
{json.dumps(signals, ensure_ascii=False, indent=2)}

EDITORIAL RULES:
- British English.
- World-first, not UK-first.
- Do not overweight the UK or the US just because they are familiar.
- Rank stories by consequence, strategic importance, market importance, democratic importance, public-interest significance, and international relevance.
- Avoid celebrity, gossip, fluff, influencer stories, clickbait, trivial culture-war noise, and low-consequence domestic chatter.
- Use calm, restrained, serious newspaper language.
- Present contested issues fairly.
- Show both sides where relevant, but do not create false balance.
- Distinguish evidence from claims.
- Use context, stakes, trade-offs, history, and likely next steps.
- Make the paper feel closer in spirit to BBC World Service than to a domestic news site.
- The front page lead must be the most important global story, not the most familiar Anglophone story.
- UK belongs in the paper, but not as the default centre of gravity.
- Wales must have its own dedicated section.
- Markets & Economy should be treated as a serious pillar of the paper.
- Do not invent direct quotes.
- Do not make up precise statistics that are not clearly supported by the source signals.
- It is acceptable to synthesise and explain significance.
- Story types allowed: News, Analysis, Explainer, Profile, Feature.

RETURN VALID JSON ONLY IN EXACTLY THIS STRUCTURE:

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
  "lead_story": {{
    "section": "World",
    "story_type": "Analysis",
    "title": "Lead headline",
    "summary": "A serious standfirst in 4 to 5 sentences.",
    "body": [
      "Paragraph 1",
      "Paragraph 2",
      "Paragraph 3",
      "Paragraph 4",
      "Paragraph 5",
      "Paragraph 6",
      "Paragraph 7",
      "Paragraph 8",
      "Paragraph 9",
      "Paragraph 10"
    ]
  }},
  "stories": [
    {{
      "section": "World",
      "story_type": "News",
      "title": "Story title",
      "summary": "A strong standfirst in 3 to 4 sentences.",
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
      "section": "Markets & Economy",
      "story_type": "Analysis",
      "title": "Story title",
      "summary": "A strong standfirst in 3 to 4 sentences.",
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
      "story_type": "News",
      "title": "Story title",
      "summary": "A strong standfirst in 3 to 4 sentences.",
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
      "story_type": "News",
      "title": "Story title",
      "summary": "A strong standfirst in 3 to 4 sentences.",
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
      "section": "Wales",
      "story_type": "News",
      "title": "Story title",
      "summary": "A strong standfirst in 3 to 4 sentences.",
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
      "story_type": "Explainer",
      "title": "Story title",
      "summary": "A strong standfirst in 3 to 4 sentences.",
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
      "story_type": "News",
      "title": "Story title",
      "summary": "A strong standfirst in 3 to 4 sentences.",
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

ADDITIONAL INSTRUCTIONS:
- Produce exactly 7 secondary stories.
- Use each of these sections exactly once in the secondary stories:
  World, Markets & Economy, Business, UK, Wales, Science & Technology, Sport.
- The lead story must not duplicate any secondary story.
- The lead story should be the most important item in the world agenda.
- The Markets & Economy piece should explain the biggest macro or market-moving theme visible in the signals.
- The Sport story should prioritise significance over celebrity.
- The Wales story should focus on material consequence, not trivial political theatre.
- The prose should feel like a real newspaper, not an AI digest.
- Avoid generic filler such as 'in today's fast-moving world' or 'this highlights the importance of'.
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

lead_story = data["lead_story"]
lead_title = lead_story["title"].strip()
lead_section = coerce_section(lead_story["section"].strip())
lead_type = coerce_story_type(lead_story["story_type"].strip())
lead_summary = lead_story["summary"].strip()
lead_body = [p.strip() for p in lead_story["body"] if p.strip()]

lead_slug = slugify(lead_title)
lead_filename = f"{lead_slug}.html"
lead_url = f"stories/{lead_filename}"

lead_body_html = "\\n".join(f"<p>{html.escape(p)}</p>" for p in lead_body)
lead_page = build_story_page(
    title=lead_title,
    section=lead_section,
    story_type=lead_type,
    summary=lead_summary,
    body_html=lead_body_html,
    updated_time=now
)

with open(STORIES_DIR / lead_filename, "w", encoding="utf-8") as f:
    f.write(lead_page)

story_cards = []
saved_stories = []

for story in data["stories"]:
    title = story["title"].strip()
    section = coerce_section(story["section"].strip())
    story_type = coerce_story_type(story["story_type"].strip())
    summary = story["summary"].strip()
    body = [p.strip() for p in story["body"] if p.strip()]

    slug = slugify(title)
    filename = f"{slug}.html"
    story_url = f"stories/{filename}"

    body_html = "\\n".join(f"<p>{html.escape(p)}</p>" for p in body)
    story_page = build_story_page(
        title=title,
        section=section,
        story_type=story_type,
        summary=summary,
        body_html=body_html,
        updated_time=now
    )

    with open(STORIES_DIR / filename, "w", encoding="utf-8") as f:
        f.write(story_page)

    story_cards.append({
        "section": section,
        "story_type": story_type,
        "title": title,
        "summary": summary,
        "url": story_url,
    })

    saved_stories.append({
        "section": section,
        "story_type": story_type,
        "title": title,
        "summary": summary,
        "url": story_url,
        "body": body,
    })

feature = load_feature()

homepage = build_homepage_page(
    updated_time=now,
    at_a_glance_items=data["at_a_glance"],
    lead_story={
        "section": lead_section,
        "story_type": lead_type,
        "title": lead_title,
        "summary": lead_summary,
        "url": lead_url,
    },
    story_cards=story_cards,
    feature=feature,
)

with open(BASE_DIR / "index.html", "w", encoding="utf-8") as f:
    f.write(homepage)

with open(DATA_DIR / "stories.json", "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": now,
        "source_signals": signals,
        "at_a_glance": data["at_a_glance"],
        "lead_story": {
            "section": lead_section,
            "story_type": lead_type,
            "title": lead_title,
            "summary": lead_summary,
            "url": lead_url,
            "body": lead_body,
        },
        "stories": saved_stories,
    }, f, indent=2)

print("Homepage and story pages updated")
