import os
import json
import datetime
import html
import re
from pathlib import Path

import feedparser
from openai import OpenAI

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data"
FEATURES_DIR = BASE_DIR / "features"

FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.bbci.co.uk/news/uk/rss.xml",
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://feeds.bbci.co.uk/sport/rss.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.theguardian.com/business/rss",
    "https://www.theguardian.com/uk-news/rss",
    "https://www.theguardian.com/uk/technology/rss",
    "https://www.theguardian.com/uk/sport/rss",
    "https://apnews.com/hub/apf-topnews?output=rss",
]

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-") or "feature"

def clean_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def get_headline_signals() -> list[dict]:
    signals = []
    seen_titles = set()

    for url in FEEDS:
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:
            print(f"Warning: failed to parse {url}: {exc}")
            continue

        for entry in parsed.entries[:8]:
            title = clean_text(entry.get("title", ""))
            summary = clean_text(entry.get("summary", ""))
            link = entry.get("link", "").strip()

            if not title:
                continue

            normalised = re.sub(r"\s+", " ", title.lower()).strip()
            if normalised in seen_titles:
                continue

            seen_titles.add(normalised)
            signals.append({
                "title": title,
                "summary": summary,
                "link": link,
            })

    return signals[:40]

def build_feature_page(title: str, standfirst: str, body_paragraphs: list[str], updated_time: str) -> str:
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
      <div class="label">Long Read</div>
      <h2>{html.escape(title)}</h2>
      <div class="standfirst">{html.escape(standfirst)}</div>
      {body_html}
    </article>
  </div>
</body>
</html>
"""

signals = get_headline_signals()

prompt = f"""
You are writing the daily long-read feature for The Daily Brief, a serious premium digital newspaper.

SOURCE SIGNALS:
{json.dumps(signals, ensure_ascii=False, indent=2)}

EDITORIAL RULES:
- British English.
- Professional, elegant, serious newspaper prose.
- This is a substantial feature, not a summary.
- Global-first rather than UK-first.
- Use context, structure, history where relevant, and likely future developments.
- Distinguish fact from claim.
- Show both sides where relevant, but do not create false balance.
- Do not invent direct quotes.
- Do not make up unsupported precise figures.
- Avoid generic filler.

Return valid JSON only in exactly this structure:

{{
  "title": "A strong feature headline",
  "standfirst": "A compelling standfirst of 2 to 3 sentences.",
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

response = client.responses.create(
    model=MODEL_NAME,
    input=prompt
)

data = json.loads(response.output_text.strip())

now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
slug = slugify(data["title"])
filename = f"{today}-{slug}.html"

FEATURES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

feature_page = build_feature_page(
    title=data["title"],
    standfirst=data["standfirst"],
    body_paragraphs=data["body"],
    updated_time=now
)

with open(FEATURES_DIR / filename, "w", encoding="utf-8") as f:
    f.write(feature_page)

with open(DATA_DIR / "feature.json", "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": now,
        "model_used": MODEL_NAME,
        "title": data["title"],
        "standfirst": data["standfirst"],
        "url": f"features/{filename}"
    }, f, indent=2)

print("Daily feature created")
