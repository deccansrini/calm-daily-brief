# Calm Daily Brief

A personal news dashboard: short, factual bites across 20+ streams, with day-by-day follow-ups, and without clickbait.

## Run it
1. Install Python 3.8 or newer. Nothing else is needed.
2. In this folder, run `python3 fetch_news.py`
3. Open `index.html` in your browser.

Run the fetcher once or twice a day. Follow-up timelines build up from a 30-day history kept in `history.json`.

**Automate it.** On Linux or Mac, add a cron entry (`crontab -e`): `0 7,19 * * * cd /path/to/news-dashboard && python3 fetch_news.py`.
On Windows, use Task Scheduler to run `python fetch_news.py` daily.

## Customise (top of fetch_news.py)
- `LOCAL_PLACES = ["Your State", "Your District"]` adds real ground-level news.
- `STREAMS` lets you add or remove streams and change their search queries or RSS feeds.
- `CLICKBAIT` / `SENSATIONAL` are the filter word lists. Add phrases that annoy you.
- `knowledge.js` holds the daily evergreen facts and the important dates. Add your own.

## How it avoids the limelight and the echo chamber
- Headlines with outrage, gossip or clickbait phrasing ("slams", "goes viral", "you won't believe") are dropped. So are graphic crime details.
- The same story from different outlets is merged, and each card shows how many outlets reported it. A single-outlet story is marked in amber. The "2+ outlets only" switch hides those.
- Google News search feeds draw on many different publishers rather than one. PIB adds the government's own primary statements.
- The follow-ups section shows how a story developed over days instead of only the latest twist. Use "Track" to follow any topic.
