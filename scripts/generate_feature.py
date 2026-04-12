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
FEATURES_DIR = BASE_DIR / "features"

feeds = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.bbci.co.uk/news/uk/rss.xml"
]

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-") or "feature"

def get_headlines():
    headlines = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:8]:
            title = entry.get("title", "").strip()
            if title and title not in headlines:
                headlines.append(title)
    return headlines[:20]

def build_feature_page(title, standfirst, body_paragraphs, updated_time):
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

headlines = get_headlines()

prompt = f"""
You are writing the daily long-read feature for The Daily Brief, a premium newspaper.

Use these latest headlines as the live news signal:
{headlines}

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
    "Paragraph 10",
    "Paragraph 11",
    "Paragraph 12"
  ]
}}

Rules:
- British English
- Professional, elegant, serious newspaper prose
- This is a substantial feature, not a summary
- Aim for a proper long read with depth, context, both sides where relevant, evidence and implications
- No markdown
- No code fences
- No extra text outside the JSON
"""

response = client.responses.create(
    model="gpt-5",
    input=prompt
)

raw = response.output_text.strip()
data = json.loads(raw)

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
        "title": data["title"],
        "standfirst": data["standfirst"],
        "url": f"features/{filename}"
    }, f, indent=2)

print("Daily feature created")
