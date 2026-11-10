# Your step-by-step guide (no coding needed)

Everything happens in your web browser on github.com. You never need to install anything.

---

## Part 1: Turn on your dashboard website (one time, about 5 minutes)

**Step 1. Allow the robot to save news**
1. Open your repo page: `https://github.com/deccansrini/calm-daily-brief`
2. Click **Settings** (the gear tab at the top right of the repo).
3. In the left menu, click **Actions**, then **General**.
4. Scroll to **Workflow permissions**, choose **Read and write permissions**, and click **Save**.

**Step 2. Turn on the website**
1. Still in **Settings**, click **Pages** in the left menu.
2. Under **Build and deployment**, find **Source** and choose **GitHub Actions**.

**Step 3. Fetch the news for the first time**
1. Click the **Actions** tab at the top of the repo.
2. If you see a green button saying *"I understand my workflows, go ahead and enable them"*, click it.
3. On the left, click **Update news**.
4. On the right, click **Run workflow**, then the green **Run workflow** button.
5. Wait 1–2 minutes until the yellow dot turns into a green tick ✅.

**Step 4. Open your dashboard**
Your dashboard is now at **https://deccansrini.github.io/calm-daily-brief/**

Bookmark it. On your phone, open it in Chrome, tap **⋮**, then **Add to Home screen**, and it works like an app.

From now on the news updates by itself at 6 AM, 12 PM and 6 PM India time. Just open the link.

---

## Part 2: Using the dashboard

| What you see | What it does |
|---|---|
| Chips at the top (Technology, Sport…) | Show only that stream. **All streams** shows everything. |
| **India: ground level to national** | Local, state and national news, side by side. |
| **Follow-ups: day by day** | Stories that continued over several days, shown as a timeline. Click a story to open it. |
| **Track** box | Type any topic (e.g. `monsoon`, `repo rate`, `ISRO`) to follow it every day. |
| **＋ Follow** on a card | Starts tracking that story. |
| **2 outlets: A, B** | How many different news outlets reported it. More outlets usually means more reliable. |
| Amber **1 outlet** | Only one outlet has reported it so far. Read it with care. |
| **2+ outlets only** | Hides the single-outlet stories. |
| **Mark read / Hide read** | Keeps your page tidy. |
| ◐ button | Switches between light and dark mode. |
| Right column | A daily fact for each subject, upcoming important dates, and "On this day in history". |

Your tracked topics and read marks are saved in your browser on that device.

---

## Part 3: Making your own changes (creative part)

### Method A: Edit directly on GitHub (simple changes)
1. Open the repo and click the file you want to change.
2. Click the ✏️ **pencil icon** at the top right of the file.
3. Make your change.
4. Click the green **Commit changes…** button, then **Commit changes** again.
5. Wait about 2 minutes and refresh your dashboard. It republishes automatically.

**Easy things to change:**

**1. Get news from your own state and district.** File: `fetch_news.py`. Find this line near the top:
```
LOCAL_PLACES = []
```
Change it to, for example:
```
LOCAL_PLACES = ["Tamil Nadu", "Coimbatore"]
```
Keep the quotes `" "`, the commas and the square brackets exactly as shown.

**2. Add your own daily facts.** File: `knowledge.js`. Inside any subject, add a new line in the same style:
```
    "Your new fact goes here, inside double quotes.",
```
Each fact needs double quotes and a comma at the end. Inside a fact, use 'single quotes' instead of "double quotes".

**3. Add an important date** (birthdays, festivals, exams). File: `knowledge.js`, near the bottom:
```
  [12,25,"Christmas"],
```
The format is `[month, day, "description"],`.

**4. Block words you find annoying.** File: `fetch_news.py`, find `CLICKBAIT = re.compile(`. Add words separated by ` | `, for example `| rumour | gossip`.

**5. Change the title.** File: `index.html`. Search (Ctrl+F) for `Calm Daily Brief` and replace it with your own name for the dashboard.

### Method B: Ask Claude (bigger or creative changes)
For changes like *"make the cards bigger"*, *"add a Tamil news stream"*, *"use orange colours"* or *"add a quote of the day"*:
1. Go to **claude.ai/code** and start a new session with the **calm-daily-brief** repository selected.
2. Describe what you want in plain English, then add: *"Commit and push to main."*
3. Refresh your dashboard about 2 minutes after Claude finishes.

### If something breaks
- Open the **Actions** tab. A red ❌ means the last change had a mistake. Click it to see the error.
- To undo a change, open the file, click **History**, open the previous version, and copy it back. Or ask Claude: *"My last change broke the dashboard, please fix it."*
- If a few news sources stop working, that's normal. The rest keep working.
