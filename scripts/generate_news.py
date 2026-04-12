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

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data"
STORIES_DIR = BASE_DIR / "stories"
FEATURES_DIR = BASE_DIR / "features"

SECTION_ORDER = [
    "World",
    "Markets & Economy",
    "Business",
    "UK",
    "Science & Technology",
    "Sport",
]

SECTION_STORY_COUNTS = {
    "World": 6,
    "Markets & Economy": 6,
    "Business": 4,
    "UK": 4,
    "Science & Technology": 4,
    "Sport": 4,
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

SPORT_PRIORITY_TERMS = [
    "cardiff city",
    "cardiff",
    "bluebirds",
    "tampa bay buccaneers",
    "buccaneers",
    "bucs",
    "nfl",
    "football transfer",
    "transfer",
    "window",
    "cycling",
    "tour de france",
    "giro",
    "vuelta",
    "tour of britain",
]

OUTLINE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "at_a_glance": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 8,
            "maxItems": 8,
        },
        "lead_story": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "section": {"type": "string"},
                "story_type": {"type": "string"},
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "source_signal_title": {"type": "string"},
            },
            "required": ["section", "story_type", "title", "summary", "source_signal_title"],
        },
        "section_features": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "label": {"type": "string"},
                    "section": {"type": "string"},
                    "title": {"type": "string"},
                    "standfirst": {"type": "string"},
                },
                "required": ["label", "section", "title", "standfirst"],
            },
        },
        "sections": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "World": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "story_type": {"type": "string"},
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "source_signal_title": {"type": "string"},
                        },
                        "required": ["story_type", "title", "summary", "source_signal_title"],
                    },
                },
                "Markets & Economy": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "story_type": {"type": "string"},
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "source_signal_title": {"type": "string"},
                        },
                        "required": ["story_type", "title", "summary", "source_signal_title"],
                    },
                },
                "Business": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "story_type": {"type": "string"},
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "source_signal_title": {"type": "string"},
                        },
                        "required": ["story_type", "title", "summary", "source_signal_title"],
                    },
                },
                "UK": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "story_type": {"type": "string"},
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "source_signal_title": {"type": "string"},
                        },
                        "required": ["story_type", "title", "summary", "source_signal_title"],
                    },
                },
                "Science & Technology": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "story_type": {"type": "string"},
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "source_signal_title": {"type": "string"},
                        },
                        "required": ["story_type", "title", "summary", "source_signal_title"],
                    },
                },
                "Sport": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "story_type": {"type": "string"},
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "source_signal_title": {"type": "string"},
                        },
                        "required": ["story_type", "title", "summary", "source_signal_title"],
                    },
                },
            },
            "required": ["World", "Markets & Economy", "Business", "UK", "Science & Technology", "Sport"],
        },
    },
    "required": ["at_a_glance", "lead_story", "section_features", "sections"],
}

BODY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "stories": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "body": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 3,
                        "maxItems": 6,
                    },
                },
                "required": ["title", "body"],
            },
        }
    },
    "required": ["stories"],
}


def response_json_schema(name: str, schema: dict) -> dict:
    return {
        "type": "json_schema",
        "name": name,
        "strict": True,
        "schema": schema,
    }


def parse_response_json(response) -> dict:
    return json.loads(response.output_text)


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


def load_previous_news():
    stories_file = DATA_DIR / "stories.json"
    if not stories_file.exists():
        return {}

    with open(stories_file, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def index_previous_items(previous_data):
    index = {}

    lead = previous_data.get("lead_story")
    if isinstance(lead, dict):
        key = normalise_title(lead.get("source_signal_title") or lead.get("title", ""))
        if key:
            index[key] = lead

    for item in previous_data.get("stories", []):
        key = normalise_title(item.get("source_signal_title") or item.get("title", ""))
        if key and key not in index:
            index[key] = item

    return index


def fetch_url(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; TheDailyBrief/1.0)"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def extract_thumbnail_from_entry(entry):
    media_thumbnail = entry.get("media_thumbnail", [])
    if media_thumbnail:
        for item in media_thumbnail:
            url = item.get("url", "").strip()
            if url:
                return url

    media_content = entry.get("media_content", [])
    if media_content:
        for item in media_content:
            url = item.get("url", "").strip()
            if url:
                return url

    enclosures = entry.get("enclosures", [])
    for item in enclosures:
        href = item.get("href", "").strip()
        item_type = item.get("type", "").strip().lower()
        if href and item_type.startswith("image/"):
            return href

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
        thumbnail_url = extract_thumbnail_from_entry(entry)
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
            "thumbnail_url": thumbnail_url,
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
            "thumbnail_url": "",
            "published_at": published_at,
        })

    return signals


def score_sport_signal(signal):
    blob = f"{signal.get('title', '')} {signal.get('summary', '')}".lower()
    score = 0
    if "cardiff city" in blob or "bluebirds" in blob:
        score += 100
    if "tampa bay buccaneers" in blob or "buccaneers" in blob or "bucs" in blob:
        score += 90
    if "nfl" in blob:
        score += 80
    if "transfer" in blob or "window" in blob:
        score += 70
    if "cycling" in blob or "tour de france" in blob or "giro" in blob or "vuelta" in blob:
        score += 60
    if "cardiff" in blob:
        score += 40
    return score


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

        if config["section"] == "Sport":
            source_signals = sorted(source_signals, key=score_sport_signal, reverse=True)

        for signal in source_signals:
            normalised = normalise_title(signal["title"])
            if not normalised or normalised in seen_titles:
                continue
            seen_titles.add(normalised)
            signals.append(signal)

    return signals[:180]


def build_story_page(
    title,
    section,
    story_type,
    summary,
    body_html,
    updated_time,
    published_at="",
    source_name="",
    source_link="",
):
    published_html = ""
    if published_at:
        published_html = f'<div class="published">Published: {html.escape(published_at)}</div>'

    source_html = ""
    if source_name and source_link:
        source_html = f'<div class="source-line">Source signal: <a href="{html.escape(source_link)}">{html.escape(source_name)}</a></div>'
    elif source_name:
        source_html = f'<div class="source-line">Source signal: {html.escape(source_name)}</div>'

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
    .updated, .published, .source-line {{
      margin-top: 10px;
      color: #666;
      font-size: 0.95rem;
    }}
    .source-line a {{
      color: #444;
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
      {source_html}
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


def build_feature_page(title, label, standfirst, body_paragraphs, updated_time):
    body_html = "\n".join(f"<p>{html.escape(p)}</p>" for p in body_paragraphs)

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
    .label {{
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #666;
      margin-bottom: 10px;
    }}
    h2 {{
      margin: 0 0 14px 0;
      font-size: 2.5rem;
      line-height: 1.15;
    }}
    .standfirst {{
      font-size: 1.2rem;
      line-height: 1.7;
      color: #333;
      margin-bottom: 28px;
      font-style: italic;
    }}
    p {{
      font-size: 1.12rem;
      line-height: 1.95;
      margin: 0 0 18px 0;
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
      <div class="label">{html.escape(label)}</div>
      <h2>{html.escape(title)}</h2>
      <div class="standfirst">{html.escape(standfirst)}</div>
      {body_html}
    </article>
  </div>
</body>
</html>
"""


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


def build_outline_prompt(signals):
    story_counts_json = json.dumps(SECTION_STORY_COUNTS, indent=2)
    sport_signals = [s for s in signals if s["section"] == "Sport"]
    sport_signals = sorted(sport_signals, key=score_sport_signal, reverse=True)

    return f"""
You are the editor of The Daily Brief, a serious premium digital newspaper.

You are building the homepage package and newsroom plan for the edition.

SOURCE SIGNALS:
{json.dumps(signals, ensure_ascii=False, indent=2)}

SPORT PRIORITY SIGNALS:
{json.dumps(sport_signals[:20], ensure_ascii=False, indent=2)}

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
- The homepage order must be:
  1. Daily Long Read
  2. Main lead story
  3. World News
  4. Features
  5. The remaining sections
- Create exactly three feature cards:
  one world, one markets, one technology.
- Markets & Economy should be treated as a serious pillar of the paper.
- Science & Technology should focus on important developments, not gadget fluff.
- Sport must be tightly focused on:
  Cardiff City, Tampa Bay Buccaneers, NFL, football transfer developments or gossip, and cycling.
- Do not drift into generic sport.
- If there is not enough hard news on those priorities, create state-of-play stories on those same priorities.
- In sport, separate confirmed developments from credible reports and rumours where relevant.
- Use timestamps and recency intelligently.
- Reuse source titles closely. Do not write theatrical or overly rewritten headlines.
- Every story must include a source_signal_title that exactly matches one source signal title from the list, except sport state-of-play items may use the closest relevant matching source title.
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

Return JSON matching the schema exactly.
"""


def build_body_prompt(stories_to_write, signals):
    return f"""
You are writing article bodies for The Daily Brief.

STORIES TO WRITE:
{json.dumps(stories_to_write, ensure_ascii=False, indent=2)}

SOURCE SIGNALS:
{json.dumps(signals[:110], ensure_ascii=False, indent=2)}

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
- For Sport, stay tightly focused on Cardiff City, Tampa Bay Buccaneers, NFL, football transfer developments or gossip, and cycling.
- Do not drift into generic sport.
- No invented quotes.
- No unsupported precise figures.
- Avoid robotic phrasing.
- Keep the prose tight but useful.
- Every paragraph must add substance.
- Do not mention internal process, workflow, briefs, source signals, or how the paper is being generated.

Return JSON matching the schema exactly.
"""


def get_signal_maps(signals):
    signal_by_key = {}
    signal_by_title = {}

    for signal in signals:
        key = normalise_title(signal["title"])
        if key and key not in signal_by_key:
            signal_by_key[key] = signal
        if signal["title"] not in signal_by_title:
            signal_by_title[signal["title"]] = signal

    return signal_by_key, signal_by_title


def get_tier_for_story(is_main_lead, is_section_lead):
    if is_main_lead:
        return "lead"
    if is_section_lead:
        return "section_lead"
    return "standard"


def get_paragraph_count_for_tier(tier):
    if tier == "lead":
        return 6
    if tier == "section_lead":
        return 4
    return 3


signals = get_source_signals()
signal_by_key, signal_by_title = get_signal_maps(signals)

previous_data = load_previous_news()
previous_index = index_previous_items(previous_data)

outline_response = client.responses.create(
    model=MODEL_NAME,
    input=build_outline_prompt(signals),
    text={"format": response_json_schema("daily_brief_outline", OUTLINE_SCHEMA)},
)

outline_data = parse_response_json(outline_response)

now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

STORIES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

used_slugs = set()

lead_story = outline_data["lead_story"]
lead_title = lead_story["title"].strip()
lead_section = coerce_section(lead_story["section"].strip())
lead_type = coerce_story_type(lead_story["story_type"].strip())
lead_summary = lead_story["summary"].strip()
lead_source_signal_title = lead_story["source_signal_title"].strip()
lead_signal = signal_by_title.get(lead_source_signal_title) or signal_by_key.get(normalise_title(lead_source_signal_title), {})
lead_key = normalise_title(lead_source_signal_title or lead_title)

planned_stories = []
for section_name in SECTION_ORDER:
    required_count = SECTION_STORY_COUNTS[section_name]
    raw_stories = outline_data.get("sections", {}).get(section_name, [])[:required_count]

    while len(raw_stories) < required_count:
        if section_name == "Sport":
            sport_signals = sorted([s for s in signals if s["section"] == "Sport"], key=score_sport_signal, reverse=True)
            fallback_signal_title = sport_signals[0]["title"] if sport_signals else (signals[0]["title"] if signals else "Sport")
            fallback_title = [
                "Cardiff City state of play",
                "Tampa Bay Buccaneers state of play",
                "NFL state of play",
                "Transfer watch",
                "Cycling watch",
            ][min(len(raw_stories), 4)]
            fallback_summary = "A current state-of-play piece focused on one of the core sport priorities, explaining where matters stand and what to watch next."
            fallback_type = "Analysis"
        else:
            fallback_signal_title = next(
                (s["title"] for s in signals if s["section"] == section_name),
                signals[0]["title"] if signals else section_name,
            )
            fallback_title = f"{section_name} update {len(raw_stories) + 1}"
            fallback_summary = f"A significant development in {section_name.lower()} with wider consequences under review."
            fallback_type = "News"

        raw_stories.append({
            "story_type": fallback_type,
            "title": fallback_title,
            "summary": fallback_summary,
            "source_signal_title": fallback_signal_title,
        })

    for i, raw_story in enumerate(raw_stories):
        planned_stories.append({
            "section": section_name,
            "story_type": coerce_story_type(raw_story["story_type"].strip()),
            "title": raw_story["title"].strip(),
            "summary": raw_story["summary"].strip(),
            "source_signal_title": raw_story["source_signal_title"].strip(),
            "is_section_lead": i == 0,
        })

previous_lead = previous_index.get(lead_key, {})
lead_body = previous_lead.get("body", []) if previous_lead else []

stories_to_generate = []
if not lead_body:
    stories_to_generate.append({
        "title": lead_title,
        "section": lead_section,
        "story_type": lead_type,
        "summary": lead_summary,
        "source_signal_title": lead_source_signal_title,
        "paragraph_count": get_paragraph_count_for_tier("lead"),
    })

for story in planned_stories:
    key = normalise_title(story["source_signal_title"] or story["title"])
    previous_story = previous_index.get(key, {})
    story["previous"] = previous_story
    body = previous_story.get("body", []) if previous_story else []
    if not body:
        tier = get_tier_for_story(False, story["is_section_lead"])
        stories_to_generate.append({
            "title": story["title"],
            "section": story["section"],
            "story_type": story["story_type"],
            "summary": story["summary"],
            "source_signal_title": story["source_signal_title"],
            "paragraph_count": get_paragraph_count_for_tier(tier),
        })

generated_bodies = {}
if stories_to_generate:
    body_response = client.responses.create(
        model=MODEL_NAME,
        input=build_body_prompt(stories_to_generate, signals),
        text={"format": response_json_schema("daily_brief_story_bodies", BODY_SCHEMA)},
    )
    body_data = parse_response_json(body_response)
    generated_bodies = {
        item["title"].strip(): [p.strip() for p in item.get("body", []) if p.strip()]
        for item in body_data.get("stories", [])
    }

lead_body = lead_body or generated_bodies.get(lead_title, [])
if not lead_body:
    lead_body = [
        lead_summary,
        "The central question is not merely what happened, but why this moment matters in the wider international picture.",
        "That requires looking at the immediate facts, the strategic background, and the practical consequences that may follow.",
        "The Daily Brief is treating this as the clearest lead item on the current global agenda.",
        "The next meaningful test will be whether the present development holds, escalates, or gives way to a fresh round of positioning.",
        "For readers, the real value lies in understanding both the event itself and the structure beneath it."
    ]

lead_thumbnail_url = lead_signal.get("thumbnail_url", "")
lead_published_at = lead_signal.get("published_at", "")
lead_source_name = lead_signal.get("source", "")
lead_source_link = lead_signal.get("link", "")

if previous_lead and previous_lead.get("url"):
    lead_url = previous_lead["url"]
    lead_filename = Path(lead_url).name
    used_slugs.add(Path(lead_filename).stem)
else:
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
    source_name=lead_source_name,
    source_link=lead_source_link,
)

with open(STORIES_DIR / lead_filename, "w", encoding="utf-8") as f:
    f.write(lead_page)

story_cards = []
saved_stories = []

for story in planned_stories:
    key = normalise_title(story["source_signal_title"] or story["title"])
    previous_story = story["previous"]
    signal = signal_by_title.get(story["source_signal_title"]) or signal_by_key.get(key, {})

    title = story["title"]
    section = story["section"]
    story_type = story["story_type"]
    summary = story["summary"]

    if previous_story and previous_story.get("url"):
        story_url = previous_story["url"]
        filename = Path(story_url).name
        used_slugs.add(Path(filename).stem)
    else:
        unique_slug = ensure_unique_slug(slugify(title), used_slugs)
        filename = f"{unique_slug}.html"
        story_url = f"stories/{filename}"

    body = previous_story.get("body", []) if previous_story else []
    body = body or generated_bodies.get(title, [])

    if not body:
        tier = get_tier_for_story(False, story["is_section_lead"])
        paragraphs = get_paragraph_count_for_tier(tier)
        body = [summary] * paragraphs

    body_html = "\n".join(f"<p>{html.escape(p)}</p>" for p in body)
    story_page = build_story_page(
        title=title,
        section=section,
        story_type=story_type,
        summary=summary,
        body_html=body_html,
        updated_time=now,
        published_at=signal.get("published_at", ""),
        source_name=signal.get("source", ""),
        source_link=signal.get("link", ""),
    )

    with open(STORIES_DIR / filename, "w", encoding="utf-8") as f:
        f.write(story_page)

    story_cards.append({
        "section": section,
        "story_type": story_type,
        "title": title,
        "summary": summary,
        "url": story_url,
        "thumbnail_url": signal.get("thumbnail_url", ""),
        "published_at": signal.get("published_at", ""),
    })

    saved_stories.append({
        "section": section,
        "story_type": story_type,
        "title": title,
        "summary": summary,
        "url": story_url,
        "thumbnail_url": signal.get("thumbnail_url", ""),
        "published_at": signal.get("published_at", ""),
        "source_signal_title": story["source_signal_title"],
        "source_name": signal.get("source", ""),
        "source_link": signal.get("link", ""),
        "body": body,
    })

saved_section_features = []
for item in outline_data.get("section_features", []):
    label = item["label"].strip()
    section = item["section"].strip()
    title = item["title"].strip()
    standfirst = item["standfirst"].strip()

    feature_filename = f"{today}-{slugify(label + '-' + title)}.html"
    feature_url = f"features/{feature_filename}"

    feature_body = [
        standfirst,
        f"This feature is being highlighted from the {section.lower()} agenda because it appears to reward slower, more analytical reading.",
        "The card is intended to surface a worthwhile deeper-reading theme from the current edition rather than simply repeat a routine news summary."
    ]

    feature_page = build_feature_page(
        title=title,
        label=label,
        standfirst=standfirst,
        body_paragraphs=feature_body,
        updated_time=now,
    )

    with open(FEATURES_DIR / feature_filename, "w", encoding="utf-8") as f:
        f.write(feature_page)

    saved_section_features.append({
        "label": label,
        "section": section,
        "title": title,
        "standfirst": standfirst,
        "url": feature_url,
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
        "thumbnail_url": lead_thumbnail_url,
        "published_at": lead_published_at,
    },
    story_cards=story_cards,
    feature=feature,
    section_features=saved_section_features,
)

with open(BASE_DIR / "index.html", "w", encoding="utf-8") as f:
    f.write(homepage)

with open(DATA_DIR / "stories.json", "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": now,
        "model_used": MODEL_NAME,
        "source_signals": signals,
        "at_a_glance": outline_data["at_a_glance"],
        "lead_story": {
            "section": lead_section,
            "story_type": lead_type,
            "title": lead_title,
            "summary": lead_summary,
            "url": lead_url,
            "thumbnail_url": lead_thumbnail_url,
            "published_at": lead_published_at,
            "source_signal_title": lead_source_signal_title,
            "source_name": lead_source_name,
            "source_link": lead_source_link,
            "body": lead_body,
        },
        "section_features": saved_section_features,
        "section_story_counts": SECTION_STORY_COUNTS,
        "stories": saved_stories,
    }, f, indent=2)

print("Homepage and story pages updated")
