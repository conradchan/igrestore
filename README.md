# igrestore

Tools to rebuild an Instagram following list from a deleted account. Parses a saved HTML export of your "Following" page, fetches live profile data, downloads profile pictures, and serves a local web app to review and triage each account.

## Files

| File | Description |
|---|---|
| `data.xml` | Raw HTML of the Instagram "Following" page (saved before deletion) |
| `ig export- ppl i was following before delete.rtf` | Same HTML wrapped in RTF |
| `following.csv` | Extracted list: username, display name, profile URL, profile pic URL |
| `profiles.json` | Enriched profile data fetched from Instagram (followers, following, posts, bio, status) |
| `decisions.db` | SQLite database storing your follow/don't follow decisions and notes per account |
| `pics/` | Downloaded profile pictures (one `.jpg` per username) |
| `fetch_profiles.py` | Script to fetch live profile metadata from Instagram's web API |
| `fetch_pics.py` | Script to download profile pictures from URLs in `profiles.json` |
| `app.py` | Flask web app to browse and triage accounts |
| `templates/index.html` | Web app frontend |
| `requirements.txt` | Python dependencies |

## Setup

```bash
pip install -r requirements.txt
```

Requires Python 3.

## Usage

### 1. Fetch profile data

Fetches live metadata (followers, following, posts, bio, active/deleted status) for all 595 accounts via Instagram's public web API. Saves progress every 10 accounts to `profiles.json` — safe to interrupt and resume.

```bash
python3 fetch_profiles.py
```

### 2. Download profile pictures

Reads `profiles.json` and downloads profile pictures into `pics/`. Skips any already downloaded.

```bash
python3 fetch_pics.py
```

### 3. Run the web app

```bash
python3 app.py
```

Open http://localhost:5000

### Web app features

- Card grid showing profile picture, username, display name, follower/following/post counts
- Tabs: **No Decision Yet**, All, Will Follow, Maybe Follow, Don't Follow
- Dropdown per account to set follow decision (persisted to SQLite)
- Notes field per account (persisted to SQLite)
- Search by username or display name
- Filter by account status (active, deleted, error)
- Sort by username, display name, or follower count
- Accounts with downloaded profile pics sort to the top
