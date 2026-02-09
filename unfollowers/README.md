# Instagram Unfollower Finder

Find accounts you follow (or sent follow requests to) that don't follow you back, using your Instagram data export.

## Setup

```
pip install flask requests
```

## Usage

### 1. Download your Instagram data

1. Open Instagram app or website
2. Go to **Settings > Accounts Center > Your Information and Permissions > Download Your Information**
3. Select **Download or transfer information** > your account > **Download to device**
4. Choose **HTML** format
5. Unzip the download and place the folder in this directory

### 2. Parse the export

```
python find_unfollowers.py
```

This auto-detects the export folder and outputs:
- Terminal summary of mutual follows, non-followers, pending requests, and fans
- `results.json` with full details

### 3. Browse results in the web app

```
python app.py
```

Open http://localhost:5001. Features:
- Tabs: Not Following Back, Pending Requests, Mutuals, Fans
- Search by username
- Sort by A-Z, date, or follower count
- Filter by public/private

### 4. (Optional) Fetch profile pics and metadata

Requires your Instagram session cookie to avoid rate limits.

```
python fetch_profiles.py --sessionid YOUR_SESSIONID
python fetch_pics.py
```

To get your `sessionid`: open Instagram in Chrome > DevTools (F12) > Application > Cookies > `instagram.com` > copy `sessionid` value.

Pass `--reset` to `fetch_profiles.py` to re-fetch previously failed accounts.

## Files

| File | Purpose |
|------|---------|
| `find_unfollowers.py` | Parse IG data export, generate `results.json` |
| `app.py` | Flask web app to browse results |
| `templates/index.html` | Web UI |
| `fetch_profiles.py` | Fetch profile metadata from Instagram API |
| `fetch_pics.py` | Download profile pictures |
