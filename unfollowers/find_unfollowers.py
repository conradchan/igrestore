#!/usr/bin/env python3
"""
Find Instagram accounts you follow (or requested to follow) that don't follow you back.

Usage:
    Place your Instagram data export folder in this directory, then run:
      python find_unfollowers.py

    The script auto-detects the export folder and parses:
      - connections/followers_and_following/followers_1.html (+ followers_2.html, etc.)
      - connections/followers_and_following/following.html
      - connections/followers_and_following/pending_follow_requests.html

    To get your data export from Instagram:
      Settings > Accounts Center > Your Information and Permissions >
      Download Your Information > Download or transfer information >
      select your account > Download to device > select HTML format
"""

import json
import glob
import os
import re
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def find_export_dir(base_dir):
    """Auto-detect the Instagram export folder."""
    for entry in os.listdir(base_dir):
        path = os.path.join(base_dir, entry)
        if os.path.isdir(path) and "instagram" in entry.lower():
            connections = os.path.join(path, "connections", "followers_and_following")
            if os.path.isdir(connections):
                return connections
    # Maybe they put files directly in the folder
    if os.path.exists(os.path.join(base_dir, "connections", "followers_and_following")):
        return os.path.join(base_dir, "connections", "followers_and_following")
    return None


def parse_html_entries(html_content):
    """Extract usernames and dates from Instagram export HTML.

    The HTML has entries like:
      <a target="_blank" href="https://www.instagram.com/username">username</a>
      <div>Feb 08, 2026 1:17 pm</div>

    Or for following.html:
      <h2 class="...">username</h2>
      <a target="_blank" href="https://www.instagram.com/_u/username">...</a>
      <div>Feb 08, 2026 1:17 pm</div>

    Returns dict of {username: {"date": "Feb 08, 2026 1:17 pm"}}
    """
    results = {}

    # Extract username from instagram.com links
    # Handles both /username and /_u/username formats
    link_pattern = re.compile(
        r'href="https://www\.instagram\.com/(?:_u/)?([^"/?]+)"'
    )
    # Date pattern: "Mon DD, YYYY H:MM am/pm" appearing in <div> after the link
    date_pattern = re.compile(
        r'</a></div><div>([A-Z][a-z]{2} \d{1,2}, \d{4} \d{1,2}:\d{2} [ap]m)</div>'
    )

    # Find all links with their positions
    links = list(link_pattern.finditer(html_content))
    dates = list(date_pattern.finditer(html_content))

    # Build a list of dates by position for matching
    date_by_pos = {}
    for m in dates:
        date_by_pos[m.start()] = m.group(1)

    for link_match in links:
        username = link_match.group(1).strip()
        if not username:
            continue

        # Find the closest date after this link
        link_end = link_match.end()
        best_date = ""
        for date_match in dates:
            if date_match.start() > link_end and date_match.start() - link_end < 200:
                best_date = date_match.group(1)
                break

        if username not in results:
            results[username] = {"date": best_date}

    return results


def load_followers(directory):
    """Load all followers_*.html files."""
    pattern = os.path.join(directory, "followers_*.html")
    files = sorted(glob.glob(pattern))
    if not files:
        print("ERROR: No followers_*.html files found in", directory)
        sys.exit(1)

    all_followers = {}
    for f in files:
        print(f"  Loading {os.path.basename(f)}...")
        with open(f, encoding="utf-8") as fh:
            all_followers.update(parse_html_entries(fh.read()))
    return all_followers


def load_following(directory):
    """Load following.html."""
    path = os.path.join(directory, "following.html")
    if not os.path.exists(path):
        print("ERROR: following.html not found in", directory)
        sys.exit(1)

    print("  Loading following.html...")
    with open(path, encoding="utf-8") as f:
        return parse_html_entries(f.read())


def load_pending_requests(directory):
    """Load pending_follow_requests.html (optional)."""
    path = os.path.join(directory, "pending_follow_requests.html")
    if not os.path.exists(path):
        return {}

    print("  Loading pending_follow_requests.html...")
    with open(path, encoding="utf-8") as f:
        return parse_html_entries(f.read())


def main():
    print("=" * 60)
    print("Instagram Unfollower Finder")
    print("=" * 60)
    print()

    export_dir = find_export_dir(SCRIPT_DIR)
    if not export_dir:
        print("ERROR: Could not find Instagram export folder.")
        print(f"  Place your unzipped Instagram export in: {SCRIPT_DIR}")
        print("  Expected structure: <export_folder>/connections/followers_and_following/")
        sys.exit(1)

    print(f"Found export at: {export_dir}")
    print()
    print("Loading data...")

    followers = load_followers(export_dir)
    following = load_following(export_dir)
    pending = load_pending_requests(export_dir)

    print()
    print(f"  Followers:         {len(followers)}")
    print(f"  Following:         {len(following)}")
    if pending:
        print(f"  Pending requests:  {len(pending)}")
    print()

    # People you follow who don't follow you back
    not_following_back = {
        username: info
        for username, info in following.items()
        if username not in followers
    }

    # Pending requests where they don't follow you
    pending_not_following = {
        username: info
        for username, info in pending.items()
        if username not in followers
    }

    # People who follow you but you don't follow back
    fans = {
        username: info
        for username, info in followers.items()
        if username not in following and username not in pending
    }

    # Mutual follows
    mutuals = {
        username: info
        for username, info in following.items()
        if username in followers
    }

    # --- Print results ---

    print("=" * 60)
    print(f"FOLLOWING BUT NOT FOLLOWED BACK: {len(not_following_back)}")
    print("=" * 60)
    for username in sorted(not_following_back):
        info = not_following_back[username]
        date = info["date"] or "unknown date"
        print(f"  @{username:<30} (followed {date})")

    if pending_not_following:
        print()
        print("=" * 60)
        print(f"PENDING REQUESTS (not following you): {len(pending_not_following)}")
        print("=" * 60)
        for username in sorted(pending_not_following):
            info = pending_not_following[username]
            date = info["date"] or "unknown date"
            print(f"  @{username:<30} (requested {date})")

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Mutual follows:              {len(mutuals)}")
    print(f"  You follow, they don't:      {len(not_following_back)}")
    if pending:
        print(f"  Pending requests:            {len(pending_not_following)}")
    print(f"  They follow, you don't:      {len(fans)}")
    print()

    # Save detailed results to JSON
    output = {
        "generated_at": datetime.now().isoformat(),
        "counts": {
            "followers": len(followers),
            "following": len(following),
            "pending_requests": len(pending),
            "mutual": len(mutuals),
            "not_following_back": len(not_following_back),
            "pending_not_following_back": len(pending_not_following),
            "fans": len(fans),
        },
        "not_following_back": [
            {"username": u, "followed_at": not_following_back[u]["date"]}
            for u in sorted(not_following_back)
        ],
        "pending_not_following_back": [
            {"username": u, "requested_at": pending_not_following[u]["date"]}
            for u in sorted(pending_not_following)
        ],
        "fans": [
            {"username": u, "followed_you_at": fans[u]["date"]}
            for u in sorted(fans)
        ],
        "mutuals": [
            {"username": u}
            for u in sorted(mutuals)
        ],
    }

    output_path = os.path.join(SCRIPT_DIR, "results.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Detailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
