import os
import json
import datetime
import feedparser
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# RSS feeds
feeds = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml"
]

def get_headlines():
    headlines = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            headlines.append(entry.title)
    return headlines

# Get new headlines
new_headlines = get_headlines()

# Load previous headlines
try:
    with open("data/stories.json", "r") as f:
        old_data = json.load(f)
        old_headlines = old_data.get("headlines", [])
except:
    old_headlines = []

# Check if anything changed
if set(new_headlines) == set(old_headlines):
    print("No changes, skipping update")
    exit()

# Ask ChatGPT to write the newspaper
prompt = f"""
You are writing The Daily Brief.

Here are the latest headlines:
{new_headlines}

Write a professional news homepage with:
- At a Glance (5 bullets)
- Front Page (lead + 3 stories)
- Markets summary
- UK summary

Keep it structured and readable.
"""

response = client.responses.create(
    model="gpt-5",
    input=prompt
)

article = response.output_text

# Save headlines for next run
with open("data/stories.json", "w") as f:
    json.dump({
        "headlines": new_headlines,
        "last_updated": str(datetime.datetime.utcnow())
    }, f)

# Write homepage
html = f"""
<!DOCTYPE html>
<html>
<head>
  <title>The Daily Brief</title>
</head>
<body>
<h1>The Daily Brief</h1>
<p>Updated: {datetime.datetime.utcnow()}</p>
<pre>{article}</pre>
</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(html)

print("Site updated")
