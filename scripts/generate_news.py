import os
import json
import datetime
import html
import feedparser
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

feeds = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.bbci.co.uk/news/uk/rss.xml"
]

def get_headlines():
    headlines = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:6]:
            title = entry.get("title", "").strip()
            if title and title not in headlines:
                headlines.append(title)
    return headlines[:15]

def build_content_html(article_text):
    safe = html.escape(article_text)
    lines = [line.strip() for line in safe.splitlines() if line.strip()]

    result = []
    in_list = False

    section_titles = {
        "at a glance",
        "front page",
        "world",
        "markets & economy",
        "business",
        "uk",
        "wales",
        "science & technology",
        "sport",
        "also in the news"
    }

    for line in lines:
        lower = line.lower()

        if lower == "the daily brief":
            continue

        if lower in section_titles:
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(f"<h2>{line}</h2>")
            continue

        if line.startswith("Lead:"):
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(f"<h3>{line}</h3>")
            continue

        if line.startswith("- "):
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(f"<li>{line[2:]}</li>")
            continue

        if in_list:
            result.append("</ul>")
            in_list = False

        result.append(f"<p>{line}</p>")

    if in_list:
        result.append("</ul>")

    return "\n".join(result)

def build_page(article_text, updated_time):
    content_html = build_content_html(article_text)

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
    h2 {{
      margin-top: 34px;
      margin-bottom: 14px;
      padding-top: 14px;
      border-top: 1px solid #ddd;
      font-size: 1.7rem;
      line-height: 1.2;
    }}
    h3 {{
      margin-top: 24px;
      margin-bottom: 10px;
      font-size: 1.25rem;
      line-height: 1.35;
    }}
    p {{
      font-size: 1.08rem;
      line-height: 1.8;
      margin: 0 0 14px 0;
    }}
    ul {{
      margin: 0 0 18px 0;
      padding-left: 22px;
    }}
    li {{
      font-size: 1.05rem;
      line-height: 1.7;
      margin-bottom: 8px;
    }}
  </style>
</head>
<body>
  <div class="page">
    <header>
      <h1>The Daily Brief</h1>
      <div class="updated">Updated: {updated_time} UTC</div>
    </header>
    {content_html}
  </div>
</body>
</html>
"""

headlines = get_headlines()

prompt = f"""
You are writing the homepage for The Daily Brief, a premium newspaper.

Use these latest headlines as source signals:
{headlines}

Write a polished homepage in British English using exactly this structure:

At a Glance
Front Page
Markets & Economy
UK
Also in the News

Rules:
- Professional tone
- Clear sections
- Plain text only
- No markdown
- No asterisks
- Use short paragraphs
- Use lines starting with '- ' for bullet points in At a Glance and Also in the News
- Start the lead story with 'Lead:'
- Do not include code fences
"""

response = client.responses.create(
    model="gpt-5",
    input=prompt
)

article = response.output_text.strip()
now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

with open("data/stories.json", "w", encoding="utf-8") as f:
    json.dump({
        "headlines": headlines,
        "last_updated": now,
        "article": article
    }, f, indent=2)

page_html = build_page(article, now)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(page_html)

print("Site updated")
