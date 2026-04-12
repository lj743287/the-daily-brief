import json
import datetime

# Simple placeholder headlines (we will replace this with real feeds later)
headlines = [
    "Global markets rise on easing tensions",
    "UK economy shows mixed signals",
    "AI investment continues to surge"
]

# Load previous data
try:
    with open("data/stories.json", "r") as f:
        data = json.load(f)
except:
    data = {"stories": []}

old_headlines = [s["headline"] for s in data.get("stories", [])]

# Check if anything changed
if headlines == old_headlines:
    print("No changes, skipping update")
    exit()

# Build new stories
stories = []
for h in headlines:
    stories.append({
        "headline": h,
        "summary": "This is a placeholder summary that will be replaced later."
    })

# Update JSON
new_data = {
    "last_updated": str(datetime.datetime.utcnow()),
    "stories": stories
}

with open("data/stories.json", "w") as f:
    json.dump(new_data, f, indent=2)

# Generate HTML
html = f"""
<!DOCTYPE html>
<html>
<head>
  <title>The Daily Brief</title>
</head>
<body>
<h1>The Daily Brief</h1>
<p>Updated: {new_data["last_updated"]}</p>
"""

for s in stories:
    html += f"<h2>{s['headline']}</h2><p>{s['summary']}</p>"

html += "</body></html>"

with open("index.html", "w") as f:
    f.write(html)

print("Updated site")
