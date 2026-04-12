import os
import json
import datetime
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import feedparser
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data"
STORIES_DIR = BASE_DIR / "stories"

SECTION_ORDER = [
    "World",
    "Markets & Economy",
    "Business",
    "UK",
    "Science & Technology",
    "Sport",
]

SECTION_STORY_COUNTS = {
    "World": 10,
    "Markets & Economy": 10,
    "Business": 5,
    "UK": 5,
    "Science & Technology": 5,
    "Sport": 5,
}

STORY_TYPE_ORDER = ["News", "Analysis", "Explainer", "Profile", "Feature"]

SOURCE_CONFIG = [
    {
        "kind": "rss",
        "source": "BBC",
        "region": "UK",
        "viewpoint_group": "uk_public_broadcaster",
        "section": "World",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    },
    {
        "kind": "rss",
        "source": "BBC",
        "region": "UK",
        "viewpoint_group": "uk_public_broadcaster",
        "section": "Business",
        "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
    },
    {
        "kind": "rss",
        "source": "BBC",
        "region": "UK",
        "viewpoint_group": "uk_public_broadcaster",
        "section": "UK",
        "url": "https://feeds.bbci.co.uk/news/uk/rss.xml",
    },
    {
        "kind": "rss",
        "source": "BBC",
        "region": "UK",
        "viewpoint_group": "uk_public_broadcaster",
        "section": "Science & Technology",
        "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    },
    {
        "kind": "rss",
        "source": "BBC Sport",
        "region": "UK",
        "viewpoint_group": "uk_public_broadcaster",
        "section": "Sport",
        "url": "https://feeds.bbci.co.uk/sport/rss.xml",
    },
    {
        "kind": "rss",
        "source": "The Guardian",
        "region": "UK",
        "viewpoint_group": "uk_liberal_broadsheet",
        "section": "World",
        "url": "https://www.theguardian.com/world/rss",
    },
    {
        "kind": "rss",
        "source": "The Guardian",
        "region": "UK",
        "viewpoint_group": "uk_liberal_broadsheet",
        "section": "Business",
        "url": "https://www.theguardian.com/business/rss",
    },
    {
        "kind": "rss",
        "source": "The Guardian",
        "region": "UK",
        "viewpoint_group": "uk_liberal_broadsheet",
        "section": "UK",
        "url": "https://www.theguardian.com/uk-news/rss",
    },
    {
        "kind": "rss",
        "source": "The Guardian",
        "region": "UK",
        "viewpoint_group": "uk_liberal_broadsheet",
        "section": "Science & Technology",
        "url": "https://www.theguardian.com/uk/technology/rss",
    },
    {
        "kind": "rss",
        "source": "The Guardian",
        "region": "UK",
        "viewpoint_group": "uk_liberal_broadsheet",
        "section": "Sport",
        "url": "https://www.theguardian.com/uk/sport/rss",
    },
    {
        "kind": "rss",
        "source": "AP",
        "region": "United States",
        "viewpoint_group": "us_wire",
        "section": "World",
        "url": "https://apnews.com/hub/apf-topnews?output=rss",
    },
    {
        "kind": "rss",
        "source": "China Daily",
        "region": "China",
        "viewpoint_group": "china_state_english",
        "section": "World",
        "url": "http://www.chinadaily.com.cn/rss/world_rss.xml",
    },
    {
        "kind": "rss",
        "source": "China Daily",
        "region": "China",
        "viewpoint_group": "china_state_english",
        "section": "Business",
        "url": "http://www.chinadaily.com.cn/rss/bizchina_rss.xml",
    },
    {
        "kind": "rss",
        "source": "China Daily",
        "region": "China",
        "viewpoint_group": "china_state_english",
        "section": "World",
        "url": "http://www.chinadaily.com.cn/rss/china_rss.xml",
    },
    {
        "kind": "rss",
        "source": "Africanews",
        "region": "Africa",
        "viewpoint_group": "africa_panregional",
        "section": "World",
        "url": "https://www.africanews.com/feed/rss?themes=news",
    },
    {
        "kind": "rss",
        "source": "Africanews",
        "region": "Africa",
        "viewpoint_group": "africa_panregional",
        "section": "Business",
        "url": "https://www.africanews.com/feed/rss?themes=business",
    },
    {
        "kind": "rss",
        "source": "Africanews",
        "region": "Africa",
        "viewpoint_group": "africa_panregional",
        "section": "Sport",
        "url": "https://www.africanews.com/feed/rss?themes=sport",
    },
    {
        "kind": "rss",
        "source": "SABC News",
        "region": "Africa",
        "viewpoint_group": "south_africa_public",
        "section": "World",
        "url": "https://www.sabcnews.com/sabcnews/feed/",
    },
    {
        "kind": "sitemap",
        "source": "Al Jazeera English",
        "region": "Middle East",
        "viewpoint_group": "middle_east_broadcaster",
        "section": "World",
        "url": "https://www.aljazeera.com/news-sitemap.xml",
    },
]


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-") or "story"


def clean_text(raw_text):
    if not raw_text:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalise_title(title):
    text = title.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def ensure_unique_slug(base_slug, used_slugs):
    slug = base_slug
    counter = 2
    while slug in used_slugs:
        suffix = f"-{counter}"
        slug = f"{base_slug[: max(1, 80 - len(suffix))]}{suffix}"
        counter += 1
    used_slugs.add(slug)
    return slug


def coerce_story_type(story_type):
    if story_type in STORY_TYPE_ORDER:
        return story_type
    return "News"


def coerce_section(section):
    if section in SECTION_ORDER:
        return section
    return "World"


def load_feature():
    feature_file = DATA_DIR / "feature.json"
    if not feature_file.exists():
        return None
    with open(feature_file, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_url(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; TheDailyBrief/1.0)"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def extract_image_from_entry(entry):
    media_content = entry.get("media_content", [])
    if media_content:
        for item in media_content:
            url = item.get("url", "").strip()
            if url:
                return url

    media_thumbnail = entry.get("media_thumbnail", [])
    if media_thumbnail:
        for item in media_thumbnail:
            url = item.get("url", "").strip()
            if url:
                return url

    enclosures = entry.get("enclosures", [])
    for item in enclosures:
        href = item.get("href", "").strip()
        item_type = item.get("type", "").strip().lower()
        if href and item_type.startswith("image/"):
            return href

    for key in ["image", "imagehref", "image_url"]:
        value = entry.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()

    summary = entry.get("summary", "") or ""
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return ""


def extract_published_at(entry):
    struct_time_value = entry.get("published_parsed") or entry.get("updated_parsed")
    if struct_time_value:
        try:
            dt = datetime.datetime(*struct_time_value[:6], tzinfo=datetime.timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            pass

    for key in ["published", "updated"]:
        value = entry.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def parse_rss_source(config, max_items=20):
    parsed = feedparser.parse(config["url"])
    signals = []

    for entry in parsed.entries[:max_items]:
        title = clean_text(entry.get("title", ""))
        summary = clean_text(entry.get("summary", ""))
        link = entry.get("link", "").strip()
        image_url = extract_image_from_entry(entry)
        published_at = extract_published_at(entry)

        if not title:
            continue

        signals.append({
            "source": config["source"],
            "region": config["region"],
            "viewpoint_group": config["viewpoint_group"],
            "section": config["section"],
            "title": title,
            "summary": summary,
            "link": link,
            "image_url": image_url,
            "published_at": published_at,
        })

    return signals


def parse_aljazeera_sitemap(config, max_items=20):
    signals = []
    raw = fetch_url(config["url"])
    root = ET.fromstring(raw)

    ns = {
        "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
        "news": "http://www.google.com/schemas/sitemap-news/0.9",
    }

    for url_node in root.findall("sm:url", ns)[:max_items]:
        loc = url_node.findtext("sm:loc", default="", namespaces=ns).strip()
        news_node = url_node.find("news:news", ns)

        title = ""
        published_at = ""

        if news_node is not None:
            title = news_node.findtext("news:title", default="", namespaces=ns).strip()
            published_at = news_node.findtext("news:publication_date", default="", namespaces=ns).strip()

        if not title and loc:
            slug = loc.rstrip("/").split("/")[-1]
            title = slug.replace("-", " ").strip().title()

        if not title:
            continue

        signals.append({
            "source": config["source"],
            "region": config["region"],
            "viewpoint_group": config["viewpoint_group"],
            "section": config["section"],
            "title": clean_text(title),
            "summary": "",
            "link": loc,
            "image_url": "",
            "published_at": published_at,
        })

    return signals


def get_source_signals():
    signals = []
    seen_titles = set()

    for config in SOURCE_CONFIG:
        try:
            if config["kind"] == "rss":
                source_signals = parse_rss_source(config)
            elif config["kind"] == "sitemap":
                source_signals = parse_aljazeera_sitemap(config)
            else:
                source_signals = []
        except Exception as exc:
            print(f"Warning: failed to parse {config['source']} {config['url']}: {exc}")
            source_signals = []

        for signal in source_signals:
            normalised = normalise_title(signal["title"])
            if not normalised or normalised in seen_titles:
                continue
            seen_titles.add(normalised)
            signals.append(signal)

    return signals[:180]


def build_story_page(title, section, story_type, summary, body_html, updated_time, published_at=""):
    published_html = ""
    if published_at:
        published_html = f'<div class="published">Published: {html.escape(published_at)}</div>'

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
    .updated, .published {{
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
      {published_html}
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

    glance_html = "\n".join(f"<li>{html.escape(item)}</li>" for item in at_a_glance_items)

    lead_html = ""
    if lead_story:
        image_html = ""
        if lead_story.get("image_url"):
            image_html = f'<img class="lead-image" src="{html.escape(lead_story["image_url"])}" alt="{html.escape(lead_story["title"])}">'
        published_html = ""
        if lead_story.get("published_at"):
            published_html = f'<div class="published-line">Published: {html.escape(lead_story["published_at"])}</div>'
        lead_html = f"""
        <section class="lead-story">
          {image_html}
          <div class="lead-meta">{html.escape(lead_story['section'])} | {html.escape(lead_story['story_type'])}</div>
          {published_html}
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

        lead_card = cards[0]
        tail_cards = cards[1:]

        section_lead_image = ""
        if lead_card.get("image_url"):
            section_lead_image = f'<img class="section-lead-image" src="{html.escape(lead_card["image_url"])}" alt="{html.escape(lead_card["title"])}">'

        section_lead_published = ""
        if lead_card.get("published_at"):
            section_lead_published = f'<div class="published-line">Published: {html.escape(lead_card["published_at"])}</div>'

        section_lead_html = f"""
        <article class="section-lead-card">
          {section_lead_image}
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

        sections_html_parts.append(
            f"""
            <section class="news-section">
              <h2>{html.escape(section)}</h2>
              {section_lead_html}
              {tail_html}
            </section>
            """
        )

    sections_html = "\n".join(sections_html_parts)

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
    .lead-image, .section-lead-image {{
      width: 100%;
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


def build_outline_prompt(signals):
    story_counts_json = json.dumps(SECTION_STORY_COUNTS, indent=2)

    return f"""
You are the editor of The Daily Brief, a serious premium digital newspaper.

You are building the homepage package and newsroom plan for the edition.

SOURCE SIGNALS:
{json.dumps(signals, ensure_ascii=False, indent=2)}

EDITORIAL RULES:
- British English.
- Global-first, not UK-first.
- Do not overweight the UK or the US merely because they are familiar.
- Rank stories by consequence, strategic importance, market importance, democratic importance, public-interest significance, and international relevance.
- Avoid celebrity, gossip, fluff, influencer stories, clickbait, trivial culture-war noise, and low-consequence domestic chatter.
- Use calm, restrained, serious newspaper language.
- Present contested issues fairly.
- Show both sides where relevant, but do not create false balance.
- Distinguish evidence from claims.
- Use context, stakes, trade-offs, history, historical background, precedent, and likely next steps.
- The lead story must be the most important global story.
- Markets & Economy should be treated as a serious pillar of the paper.
- Science & Technology should focus on important developments, not gadget fluff.
- Sport must be tightly focused on:
  Cardiff City, Tampa Bay Buccaneers, NFL, football transfer developments or gossip, and cycling.
- If the live sport signals are thin for one of those priorities, you may create a careful state-of-play or watchlist story rather than drifting into random sport.
- In sport, separate confirmed developments from credible reports and rumours where relevant.
- Use timestamps and recency intelligently.
- Do not invent direct quotes.
- Do not make up precise statistics not clearly supported by the source signals.
- Treat source metadata seriously.
- Different regions and viewpoint groups may frame the same story differently.
- Prioritise consensus facts first.
- Mention framing differences only when meaningful.
- Do not automatically treat all viewpoints as equally well supported.
- Story types allowed: News, Analysis, Explainer, Profile, Feature.

SECTION STORY COUNTS:
{story_counts_json}

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
  "lead_story": {{
    "section": "World",
    "story_type": "Analysis",
    "title": "Lead headline",
    "summary": "A serious standfirst in 4 to 5 sentences."
  }},
  "sections": {{
    "World": [
      {{
        "story_type": "News",
        "title": "Story title",
        "summary": "A strong standfirst in 2 to 4 sentences."
      }}
    ],
    "Markets & Economy": [
      {{
        "story_type": "Analysis",
        "title": "Story title",
        "summary": "A strong standfirst in 2 to 4 sentences."
      }}
    ],
    "Business": [
      {{
        "story_type": "News",
        "title": "Story title",
        "summary": "A strong standfirst in 2 to 4 sentences."
      }}
    ],
    "UK": [
      {{
        "story_type": "News",
        "title": "Story title",
        "summary": "A strong standfirst in 2 to 4 sentences."
      }}
    ],
    "Science & Technology": [
      {{
        "story_type": "Explainer",
        "title": "Story title",
        "summary": "A strong standfirst in 2 to 4 sentences."
      }}
    ],
    "Sport": [
      {{
        "story_type": "News",
        "title": "Story title",
        "summary": "A strong standfirst in 2 to 4 sentences."
      }}
    ]
  }}
}}

ADDITIONAL RULES:
- Produce exactly the number of stories required for each section.
- Do not include a Wales section.
- Do not duplicate the lead story inside any section.
- The Markets & Economy section should cover macro, rates, inflation, currencies, bonds, commodities, major equity moves, policy shifts, and market consequences where visible.
- The paper should feel like a real newspaper, not an AI digest.
- Avoid generic filler.
"""


def build_lead_body_prompt(title, section, story_type, summary, signals):
    return f"""
You are writing the lead article for The Daily Brief.

ARTICLE DETAILS:
- Section: {section}
- Story type: {story_type}
- Headline: {title}
- Standfirst: {summary}

SOURCE SIGNALS:
{json.dumps(signals[:60], ensure_ascii=False, indent=2)}

EDITORIAL RULES:
- British English.
- Serious, calm, restrained newspaper prose.
- Global-first outlook.
- Explain what happened, why it matters, who is affected, what is uncertain, and what may happen next.
- Use the source metadata intelligently.
- If different regions frame the same story differently, explain that carefully.
- Prioritise consensus facts first.
- Distinguish claims from supported facts.
- Bring in historical context and background where it genuinely helps the reader understand the present moment.
- For major geopolitical tensions, explain what earlier phases, flashpoints or negotiations form the backdrop.
- Do not invent direct quotes.
- Do not make up unsupported precise figures.
- Avoid robotic phrasing.

Return valid JSON only in exactly this structure:

{{
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
}}
"""


def build_section_body_prompt(section, stories, signals):
    section_signals = [s for s in signals if s["section"] == section]

    if section == "Markets & Economy":
        section_signals = [
            s for s in signals
            if s["section"] in ["Business", "World", "UK"]
        ]

    if section == "Sport":
        sport_priority_terms = [
            "cardiff city",
            "cardiff",
            "tampa bay buccaneers",
            "buccaneers",
            "nfl",
            "transfer",
            "cycling",
            "tour",
            "championship",
            "premier league",
            "draft",
            "window",
        ]
        prioritised = []
        others = []
        for s in section_signals:
            title_blob = f"{s['title']} {s['summary']}".lower()
            if any(term in title_blob for term in sport_priority_terms):
                prioritised.append(s)
            else:
                others.append(s)
        section_signals = prioritised + others

    if len(section_signals) < 20:
        section_signals = signals[:70]

    return f"""
You are writing a full section package for The Daily Brief.

SECTION:
{section}

STORIES TO WRITE:
{json.dumps(stories, ensure_ascii=False, indent=2)}

SOURCE SIGNALS:
{json.dumps(section_signals[:70], ensure_ascii=False, indent=2)}

EDITORIAL RULES:
- British English.
- Serious, calm, restrained newspaper prose.
- Global-first where relevant.
- Use the region and viewpoint metadata intelligently.
- Prioritise consensus facts first.
- Where regional framings differ, mention that only if it genuinely helps the reader.
- Do not force artificial balance.
- Distinguish evidence from claims.
- Bring in historical context and background where it genuinely improves understanding.
- Each story should help the reader see not just what happened, but what led to it and what may come next.
- No invented quotes.
- No unsupported precise figures.
- Avoid generic filler.
- Every paragraph must add something new.
- For Sport, stay tightly focused on Cardiff City, Tampa Bay Buccaneers, NFL, football transfer developments or gossip, and cycling.
- Do not drift into generic sport simply to fill space.
- If a requested sport priority has little fresh reporting in the signals, write a careful watch, state-of-play, or context piece rather than pretending there is breaking news.
- For football transfer items, clearly imply the difference between confirmed developments, credible reports and rumours where relevant.

Return valid JSON only in exactly this structure:

{{
  "stories": [
    {{
      "title": "Story 1 title exactly as provided",
      "body": [
        "Paragraph 1",
        "Paragraph 2",
        "Paragraph 3",
        "Paragraph 4",
        "Paragraph 5",
        "Paragraph 6"
      ]
    }}
  ]
}}

ADDITIONAL RULES:
- Return one body for every story provided.
- Match titles exactly.
- Return exactly 6 paragraphs per story.
"""


signals = get_source_signals()

outline_response = client.responses.create(
    model="gpt-5",
    input=build_outline_prompt(signals),
)

outline_data = json.loads(outline_response.output_text.strip())

now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

STORIES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

used_slugs = set()

signal_map = {}
for signal in signals:
    norm = normalise_title(signal["title"])
    if not norm:
        continue
    if norm not in signal_map:
        signal_map[norm] = {
            "image_url": signal.get("image_url", ""),
            "published_at": signal.get("published_at", ""),
        }

lead_story = outline_data["lead_story"]
lead_title = lead_story["title"].strip()
lead_section = coerce_section(lead_story["section"].strip())
lead_type = coerce_story_type(lead_story["story_type"].strip())
lead_summary = lead_story["summary"].strip()
lead_meta = signal_map.get(normalise_title(lead_title), {})
lead_image_url = lead_meta.get("image_url", "")
lead_published_at = lead_meta.get("published_at", "")

lead_body_response = client.responses.create(
    model="gpt-5",
    input=build_lead_body_prompt(
        title=lead_title,
        section=lead_section,
        story_type=lead_type,
        summary=lead_summary,
        signals=signals,
    ),
)

lead_body_data = json.loads(lead_body_response.output_text.strip())
lead_body = [p.strip() for p in lead_body_data["body"] if p.strip()]

lead_slug = ensure_unique_slug(slugify(lead_title), used_slugs)
lead_filename = f"{lead_slug}.html"
lead_url = f"stories/{lead_filename}"

lead_body_html = "\n".join(f"<p>{html.escape(p)}</p>" for p in lead_body)
lead_page = build_story_page(
    title=lead_title,
    section=lead_section,
    story_type=lead_type,
    summary=lead_summary,
    body_html=lead_body_html,
    updated_time=now,
    published_at=lead_published_at,
)

with open(STORIES_DIR / lead_filename, "w", encoding="utf-8") as f:
    f.write(lead_page)

story_cards = []
saved_stories = []

sections = outline_data.get("sections", {})

for section_name in SECTION_ORDER:
    required_count = SECTION_STORY_COUNTS[section_name]
    raw_stories = sections.get(section_name, [])
    raw_stories = raw_stories[:required_count]

    while len(raw_stories) < required_count:
        fallback_title = f"{section_name} watch {len(raw_stories) + 1}" if section_name == "Sport" else f"{section_name} update {len(raw_stories) + 1}"
        fallback_summary = (
            f"A current watch item in {section_name.lower()} with broader context and next-step implications."
            if section_name == "Sport"
            else f"A significant development in {section_name.lower()} with wider consequences under review."
        )
        raw_stories.append({
            "story_type": "Analysis" if section_name == "Sport" else "News",
            "title": fallback_title,
            "summary": fallback_summary,
        })

    normalised_section_stories = []
    for raw_story in raw_stories:
        normalised_section_stories.append({
            "story_type": coerce_story_type(raw_story["story_type"].strip()),
            "title": raw_story["title"].strip(),
            "summary": raw_story["summary"].strip(),
        })

    section_body_response = client.responses.create(
        model="gpt-5",
        input=build_section_body_prompt(
            section=section_name,
            stories=normalised_section_stories,
            signals=signals,
        ),
    )

    section_body_data = json.loads(section_body_response.output_text.strip())
    bodies_by_title = {
        item["title"].strip(): [p.strip() for p in item.get("body", []) if p.strip()]
        for item in section_body_data.get("stories", [])
    }

    for story in normalised_section_stories:
        title = story["title"]
        story_type = story["story_type"]
        summary = story["summary"]
        body = bodies_by_title.get(title, [])
        meta = signal_map.get(normalise_title(title), {})
        image_url = meta.get("image_url", "")
        published_at = meta.get("published_at", "")

        if not body:
            body = [
                f"{title} is on the Daily Brief agenda because it appears to carry wider significance than a routine headline alone would suggest.",
                f"In {section_name.lower()}, the immediate facts are only one part of the picture, and the broader background helps explain why this matters now.",
                "Different outlets may emphasise different causes, risks, or consequences, but the key task is to separate agreed facts from interpretation.",
                "That means readers should pay attention not just to the latest development, but to the history and incentives that have shaped the current position.",
                "It also makes this a story worth following beyond the first burst of headlines, especially if the practical or strategic consequences widen.",
                "The next phase will depend on whether the present signals harden into a lasting shift, fade into a short-lived episode, or trigger further responses."
            ]

        base_slug = slugify(title)
        unique_slug = ensure_unique_slug(base_slug, used_slugs)
        filename = f"{unique_slug}.html"
        story_url = f"stories/{filename}"

        body_html = "\n".join(f"<p>{html.escape(p)}</p>" for p in body)
        story_page = build_story_page(
            title=title,
            section=section_name,
            story_type=story_type,
            summary=summary,
            body_html=body_html,
            updated_time=now,
            published_at=published_at,
        )

        with open(STORIES_DIR / filename, "w", encoding="utf-8") as f:
            f.write(story_page)

        story_cards.append({
            "section": section_name,
            "story_type": story_type,
            "title": title,
            "summary": summary,
            "url": story_url,
            "image_url": image_url,
            "published_at": published_at,
        })

        saved_stories.append({
            "section": section_name,
            "story_type": story_type,
            "title": title,
            "summary": summary,
            "url": story_url,
            "image_url": image_url,
            "published_at": published_at,
            "body": body,
        })

feature = load_feature()

homepage = build_homepage_page(
    updated_time=now,
    at_a_glance_items=outline_data["at_a_glance"],
    lead_story={
        "section": lead_section,
        "story_type": lead_type,
        "title": lead_title,
        "summary": lead_summary,
        "url": lead_url,
        "image_url": lead_image_url,
        "published_at": lead_published_at,
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
        "at_a_glance": outline_data["at_a_glance"],
        "lead_story": {
            "section": lead_section,
            "story_type": lead_type,
            "title": lead_title,
            "summary": lead_summary,
            "url": lead_url,
            "image_url": lead_image_url,
            "published_at": lead_published_at,
            "body": lead_body,
        },
        "section_story_counts": SECTION_STORY_COUNTS,
        "stories": saved_stories,
    }, f, indent=2)

print("Homepage and story pages updated")
