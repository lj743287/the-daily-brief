import json
import html
from pathlib import Path

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data"

SECTION_ORDER = [
    "World",
    "Markets & Economy",
    "Business",
    "UK",
    "Science & Technology",
    "Sport",
]


def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
        "paragraph_count": 6,
    })

for story in planned_stories:
    key = normalise_title(story["source_signal_title"] or story["title"])
    previous_story = previous_index.get(key, {})
    story["previous"] = previous_story
    body = previous_story.get("body", []) if previous_story else []
    if not body:
        stories_to_generate.append({
            "title": story["title"],
            "section": story["section"],
            "story_type": story["story_type"],
            "summary": story["summary"],
            "source_signal_title": story["source_signal_title"],
            "paragraph_count": 4 if story["is_section_lead"] else 3,
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
        paragraph_count = 4 if story["is_section_lead"] else 3
        body = [summary] * paragraph_count

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
