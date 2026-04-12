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

def to_html(article_text, updated_time):
    safe = html.escape(article_text)

    lines = [line.strip() for line in safe.splitlines()]
    html_parts = []

    for line in lines:
        if not line:
            continue

        lower = line.lower()

        if line == "The Daily Brief":
            continue
        elif lower in [
            "at a glance",
            "front page",
            "world",
            "markets & economy",
            "business",
            "uk",
            "wales",
            "science & technology",
            "sport",
            "markets summary",
            "uk summary",
            "also in the news"
        ]:
            html_parts.append(f"<h2>{line}</h2>")
        elif line.startswith("Lead:"):
            html_parts.append(f"<h3>{line}</h3>")
        elif line.startswith("- "):
            html_parts.append(f"<li>{line[2:]}</li>")
        else:
            html_parts.append(f"<p>{line}</p>")

    content = "\n".join(html_parts)

    if "<li>" in content:
        rebuilt = []
        in_list = False
        for part in html_parts:
            if part.startswith("<li>") and not in_list:
                rebuilt.append("<ul>")
                in_list = True
            if not part.startswith("<li>") and in_list:
                rebuilt.append("</ul>")
                in_list = False
            rebuilt.append(part)
        if in_list:
            rebuilt.append("</ul>")
        content = "\n".join(rebuilt)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Daily Brief</title>
  <style>
    body {{
      margin: 0;
      background: #f4f1ea;
      color: #111;
      font-family: Georgia, "Times New Roman", serif;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
      padding: 32px 20px 60px 20px;
      background: #fffdf8;
      min-height: 100vh;
      box-shadow: 0 0 20px rgba(0,0,0,0.06);
    }}
    header {{
      border-bottom: 3px solid #111;
      margin-bottom: 24px;
      padding-bottom: 16px;
    }}
    h1 {{
      font-size: 3rem;
      margin: 0 0 8px 0;
      line-height: 1.1;
    }}
    .updated {{
      color: #555;
      font-size: 0.95rem;
    }}
    h2 {{
      font-size: 1.6rem;
      margin-top: 32px;
      border-top: 1px solid #ddd;
      padding-top: 18px;
    }}
    h3 {{
      font-size: 1.2rem;
      margin-top: 24px;
      margin-bottom: 8px;
    }}
    p, li {{
      font-size: 1.05rem;
      line-height: 1.75;
      margin: 0 0 14px 0;
    }}
    ul {{
      padding-left: 22px;
      margin-top: 8px;
      margin-bottom: 18px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>The Daily Brief</h1>
      <div class="updated">Updated: {updated_time} UTC</div>
    </header>
    {content}
  </div>
</body>
</html>
"""
    return page

new_headlines = get_headlines()

try:
    with open("data/stories.json", "r") as f:
        old_data = json.load(f)
        old_headlines = old_data.get("headlines", [])
except:
    old_headlines = []

if set(new_headlines) == set(old_headlines):
    print("No changes, skipping update")
    raise SystemExit(0)

prompt = f"""
You are writing the homepage for The Daily Brief, a premium newspaper.

Use these latest headlines as source signals:
{new_headlines}

Write a polished homepage in British English with this structure:

At a Glance
Front Page
Markets & Economy
UK
Also in the News

Rules:
- Professional tone
- Clear sections
- No markdown
- Plain text only
- Use short paragraphs
- Use lines starting with '- ' for bullet points in At a Glance and Also in the News
- Start the lead story line with 'Lead:'
- Do not use asterisks
- Do not include code fences
- Keep it readable and well structured
"""

response = client.responses.create(
    model="gpt-5",
    input=prompt
)

article = response.output_text.strip()
now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

with open("data/stories.json", "w") as f:
    json.dump({
        "headlines": new_headlines,
        "last_updated": now
    }, f, indent=2)

page_html = to_html(article, now)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(page_html)

print("Site updated")
