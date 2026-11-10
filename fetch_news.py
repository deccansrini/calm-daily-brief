#!/usr/bin/env python3
"""
Calm News Dashboard: feed fetcher (Python 3.8+, standard library only).

    python3 fetch_news.py          # fetch, filter, write data.js
    then open index.html in a browser

What it does
  1. Pulls RSS/Atom feeds per stream (Google News search feeds give many outlets,
     plus direct feeds from PIB, The Hindu, etc.).
  2. Drops clickbait / outrage / gossip headlines (see CLICKBAIT, SENSATIONAL).
  3. Merges the same story from different outlets into one card and shows
     how many outlets carried it (helps you get out of the echo chamber).
  4. Keeps 30 days of history and links stories across days into
     "follow-up" threads, so you can see how an incident developed day by day.
  5. Adds Wikipedia's "On this day" events.
"""
import concurrent.futures as cf
import datetime as dt
import email.utils
import html
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(HERE, "history.json")
OUTPUT_FILE = os.path.join(HERE, "data.js")
HISTORY_DAYS = 30
MAX_PER_FEED = 25
UA = "CalmNewsDashboard/1.0 (personal RSS reader)"

# ---------------------------------------------------------------- settings --
# >>> EASY SETTING <<<
# Ground-level news: put your state, district and city between the brackets.
# Keep the quotes and commas exactly like the example.
# Example: LOCAL_PLACES = ["Tamil Nadu", "Coimbatore"]
LOCAL_PLACES = []

def gnews(query):
    """Google News RSS search, India edition. One feed, many outlets."""
    q = urllib.parse.quote(query + " when:2d")
    return f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"

# Each stream: label, google-news queries, direct feeds, optional India level.
STREAMS = {
    "india_national": {"label": "India: National", "level": "national",
        "queries": ["India government policy", "Parliament India bill", "Supreme Court India ruling"],
        "feeds": ["https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
                  "https://www.thehindu.com/news/national/feeder/default.rss"]},
    "india_state": {"label": "India: States", "level": "state",
        "queries": ["state government India scheme", "state assembly India"]
                   + [f"{p} government" for p in LOCAL_PLACES],
        "feeds": []},
    "india_ground": {"label": "India: Ground level", "level": "ground",
        "queries": ["gram panchayat India", "district administration India farmers",
                    "rural India village water school"]
                   + [f"{p} district news" for p in LOCAL_PLACES],
        "feeds": ["https://www.downtoearth.org.in/rss/india"]},
    "politics": {"label": "Politics", "queries": ["Election Commission India", "Lok Sabha Rajya Sabha"], "feeds": []},
    "leaders": {"label": "National Leaders", "queries": ["Prime Minister India announces", "President of India", "Chief Minister announces scheme"], "feeds": []},
    "technology": {"label": "Technology", "queries": ["technology India launch", "artificial intelligence research", "ISRO"], "feeds": []},
    "finance": {"label": "Finance", "queries": ["RBI policy", "India GDP inflation data", "SEBI rule"], "feeds": []},
    "health": {"label": "Health", "queries": ["ICMR study", "WHO health report", "public health India"], "feeds": []},
    "fitness": {"label": "Fitness", "queries": ["exercise study research", "nutrition research study"], "feeds": []},
    "sport": {"label": "Sport", "queries": ["India cricket result", "India hockey football badminton result", "Olympics India athlete"], "feeds": []},
    "knowledge": {"label": "Science & Knowledge", "queries": ["scientists discover", "new study finds research journal"], "feeds": []},
    "history": {"label": "History", "queries": ["archaeologists India excavation", "ASI discovery history"], "feeds": []},
    "geography": {"label": "Geography & Environment", "queries": ["IMD monsoon forecast", "climate environment India report"], "feeds": []},
    "mathematics": {"label": "Mathematics", "queries": ["mathematicians prove theorem", "mathematics prize"], "feeds": []},
    "psychology": {"label": "Psychology", "queries": ["psychology study finds", "mental health research"], "feeds": []},
    "philosophy": {"label": "Philosophy & Ethics", "queries": ["philosophy ethics debate", "AI ethics policy"], "feeds": []},
    "softskills": {"label": "Careers & Soft Skills", "queries": ["workplace skills survey India", "jobs report India employment"], "feeds": []},
    "entertainment": {"label": "Entertainment", "queries": ["film festival India", "box office India film release"], "feeds": []},
    "music": {"label": "Music", "queries": ["Indian classical music concert", "music album release award"], "feeds": []},
    "celebrities": {"label": "Personalities", "queries": ["award honoured India Padma", "Indian personality achievement"], "feeds": []},
    "world": {"label": "World", "queries": ["United Nations", "world news diplomacy"], "feeds": []},
}

# ----------------------------------------------------------------- filters --
CLICKBAIT = re.compile(r"""(?ix)
  you\ won'?t\ believe | shocking | shocked | jaw[-\ ]?drop | mind[-\ ]?blow |
  goes\ viral | viral\ video | netizens | internet\ (is\ )?(reacts|breaks) |
  slams | lashes\ out | blasts | destroys | epic\ reply | befitting\ reply |
  here'?s\ why | here'?s\ what | this\ is\ why | what\ happened\ next |
  \bwatch\b | \bphotos?\b | in\ pics | video:\ | \bhot\b | bold\ look |
  oops | ugly\ spat | spat\ with | troll(ed|s)? | meme | breakup | dating\ rumou?rs |
  horoscope | astrology | zodiac | lucky\ number | top\ \d+\ (reasons|ways) |
  \bquiz\b | must[-\ ]see | unbelievable | stunning | outrage | furious | fumes
""")
# Graphic / distressing crime details are filtered unless you set SHOW_SENSITIVE.
SENSATIONAL = re.compile(r"""(?ix)
  gruesome | brutal(ly)? | chopped | beheaded | horrific | dismembered |
  caught\ on\ camera | cctv\ footage | leaked\ video | mms
""")
SHOW_SENSITIVE = False

STOP = set("""a an the of to in on for and or but is are was were be been with by at from as
that this it its into over after before about up down out new says said will would can could
has have had not no than then more most also amid how why what when who which while against
india indian s 2025 2026 year day week news report reports""".split())

# --------------------------------------------------------------- helpers ----
def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def clean(text):
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return re.sub(r"\s+", " ", text).strip()

def bite(text, limit=260):
    """First one or two sentences: a 'bite', not the whole article."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = ""
    for s in sentences[:2]:
        if len(out) + len(s) > limit:
            break
        out = (out + " " + s).strip()
    return out or text[:limit]

def parse_date(s):
    if not s:
        return None
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)

def tokens(title):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in STOP and len(w) > 2}

def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0

def local(tag):
    return tag.rsplit("}", 1)[-1]

def parse_feed(raw, default_source):
    root = ET.fromstring(raw)
    items = []
    for el in root.iter():
        if local(el.tag) not in ("item", "entry"):
            continue
        f = {}
        for c in el:
            name = local(c.tag)
            if name == "link":
                f["link"] = c.attrib.get("href") or (c.text or "")
            elif name == "source":
                f["source"] = (c.text or "").strip()
            else:
                f.setdefault(name, c.text or "")
        title = clean(f.get("title", ""))
        source = f.get("source") or default_source
        # Google News titles look like "Headline - Outlet"
        m = re.match(r"^(.*)\s+-\s+([^-]{2,60})$", title)
        if m and "news.google" in f.get("link", ""):
            title, source = m.group(1).strip(), m.group(2).strip()
        summary = clean(f.get("description") or f.get("summary") or f.get("content") or "")
        if summary.lower().startswith(title.lower()[:40]) or "news.google" in f.get("link", ""):
            summary = ""  # Google's description just repeats the headline
        date = parse_date(f.get("pubDate") or f.get("published") or f.get("updated") or f.get("date"))
        if title:
            items.append({"title": title, "source": source, "link": f.get("link", "").strip(),
                          "summary": bite(summary) if summary else "", "date": date})
        if len(items) >= MAX_PER_FEED:
            break
    return items

def source_name(url):
    host = urllib.parse.urlparse(url).netloc.replace("www.", "")
    return {"pib.gov.in": "PIB (Govt. of India)", "thehindu.com": "The Hindu",
            "downtoearth.org.in": "Down To Earth"}.get(host, host)

def fetch_stream(key, cfg):
    urls = [gnews(q) for q in cfg["queries"]] + cfg["feeds"]
    got, errors = [], []
    for u in urls:
        try:
            for it in parse_feed(fetch(u), source_name(u)):
                it["stream"] = key
                got.append(it)
        except Exception as e:  # one dead feed should not stop the rest
            errors.append(f"{key}: {u[:70]}... {type(e).__name__}")
    return got, errors

def keep(item):
    text = item["title"] + " " + item["summary"]
    if CLICKBAIT.search(text):
        return False
    if not SHOW_SENSITIVE and SENSATIONAL.search(text):
        return False
    if item["title"].isupper() or item["title"].count("!") > 0:
        return False
    return True

def merge_same_story(items):
    """Same event from several outlets -> one story with multiple sources."""
    stories = []
    for it in sorted(items, key=lambda x: x["date"] or dt.datetime.min.replace(tzinfo=dt.timezone.utc)):
        tk = tokens(it["title"])
        for s in stories:
            if s["stream"] == it["stream"] and jaccard(tk, s["_tk"]) >= 0.5:
                if it["source"] not in [x["name"] for x in s["sources"]]:
                    s["sources"].append({"name": it["source"], "link": it["link"]})
                if not s["summary"] and it["summary"]:
                    s["summary"] = it["summary"]
                break
        else:
            stories.append({"title": it["title"], "summary": it["summary"], "stream": it["stream"],
                            "date": it["date"], "_tk": tk,
                            "sources": [{"name": it["source"], "link": it["link"]}]})
    return stories

def wiki_on_this_day(today):
    url = (f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/selected/"
           f"{today.month:02d}/{today.day:02d}")
    try:
        data = json.loads(fetch(url))
        return [{"year": e.get("year"), "text": e.get("text")} for e in data.get("selected", [])][:12]
    except Exception:
        return []

def build_threads(history):
    """Link stories across different days into follow-up timelines."""
    entries = sorted(history, key=lambda s: s["date"])
    threads = []
    for s in entries:
        tk = set(s["tk"])
        best, best_score = None, 0.0
        for th in threads:
            score = jaccard(tk, th["_tk"])
            if score > best_score:
                best, best_score = th, score
        if best and best_score >= 0.3:
            best["updates"].append(s)
            best["_tk"] = best["_tk"] | tk
        else:
            threads.append({"_tk": set(tk), "updates": [s]})
    out = []
    for th in threads:
        days = sorted({u["date"][:10] for u in th["updates"]})
        if len(days) < 2:
            continue
        ups = th["updates"]
        # theme = the words most updates have in common
        counts = {}
        for u in ups:
            for w in set(u["tk"]):
                counts[w] = counts.get(w, 0) + 1
        theme = [w for w, c in sorted(counts.items(), key=lambda x: -x[1])[:4]]
        out.append({"title": ups[-1]["title"], "stream": ups[-1]["stream"], "theme": theme,
                    "days": len(days), "first": days[0], "last": days[-1],
                    "updates": [{"date": u["date"], "title": u["title"], "summary": u["summary"],
                                 "sources": u["sources"]} for u in ups]})
    out.sort(key=lambda t: (t["last"], t["days"]), reverse=True)
    return out[:40]

# ------------------------------------------------------------------ main ----
def main():
    now = dt.datetime.now(dt.timezone.utc)
    all_items, errors = [], []
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        for items, errs in pool.map(lambda kv: fetch_stream(*kv), STREAMS.items()):
            all_items += items
            errors += errs

    cutoff = now - dt.timedelta(days=3)
    fresh = [i for i in all_items if keep(i) and (i["date"] is None or i["date"] >= cutoff)]
    for i in fresh:
        i["date"] = i["date"] or now
    dropped = len(all_items) - len(fresh)
    stories = merge_same_story(fresh)

    # history for follow-ups
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as fh:
            history = json.load(fh)
    known = {(h["stream"], h["title"]) for h in history}
    for s in stories:
        if (s["stream"], s["title"]) not in known:
            history.append({"title": s["title"], "summary": s["summary"], "stream": s["stream"],
                            "date": s["date"].isoformat(), "tk": sorted(s["_tk"]),
                            "sources": s["sources"][:6]})
    hcut = (now - dt.timedelta(days=HISTORY_DAYS)).isoformat()
    history = [h for h in history if h["date"] >= hcut]
    with open(HISTORY_FILE, "w", encoding="utf-8") as fh:
        json.dump(history, fh, ensure_ascii=False)

    out_stories = [{"title": s["title"], "summary": s["summary"], "stream": s["stream"],
                    "date": s["date"].isoformat(), "sources": s["sources"][:8]}
                   for s in sorted(stories, key=lambda s: (len(s["sources"]), s["date"]), reverse=True)]

    data = {
        "generated": now.isoformat(),
        "streams": {k: {"label": v["label"], "level": v.get("level")} for k, v in STREAMS.items()},
        "stories": out_stories,
        "threads": build_threads(history),
        "onThisDay": wiki_on_this_day(dt.date.today()),
        "stats": {"fetched": len(all_items), "filtered_out": dropped, "stories": len(out_stories),
                  "errors": errors[:30]},
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        fh.write("window.DASH = " + json.dumps(data, ensure_ascii=False) + ";\n")
    print(f"Fetched {len(all_items)} headlines, filtered out {dropped} (clickbait/old), "
          f"{len(out_stories)} stories, {len(data['threads'])} follow-up threads.")
    if errors:
        print(f"{len(errors)} feeds failed (skipped). First few:")
        for e in errors[:5]:
            print("  -", e)
    print("Open index.html in your browser.")

if __name__ == "__main__":
    main()
