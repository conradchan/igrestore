#!/usr/bin/env python3
"""Fetch Instagram profile data for all accounts in results.json.

Usage:
    python fetch_profiles.py --sessionid YOUR_SESSIONID

    To get your sessionid:
      1. Open Instagram in Chrome and log in
      2. Open DevTools (F12) > Application > Cookies > instagram.com
      3. Copy the value of 'sessionid'

    Pass --reset to re-fetch accounts that previously returned errors.
"""

import argparse
import json
import os
import random
import sys
import time

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_JSON = os.path.join(SCRIPT_DIR, "results.json")
PROFILES_JSON = os.path.join(SCRIPT_DIR, "profiles.json")

API_URL = "https://www.instagram.com/api/v1/users/web_profile_info/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/125.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-IG-App-ID": "936619743392459",
    "X-Requested-With": "XMLHttpRequest",
}


def load_existing():
    if os.path.exists(PROFILES_JSON):
        with open(PROFILES_JSON) as f:
            return json.load(f)
    return {}


def save_progress(data):
    with open(PROFILES_JSON, "w") as f:
        json.dump(data, f, indent=2)


def fetch_profile(username, session):
    try:
        resp = session.get(API_URL, params={"username": username}, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        return {"username": username, "status": "error", "error": str(e)}

    if resp.status_code == 404:
        return {"username": username, "status": "not_found"}
    if resp.status_code in (401, 403):
        return {"username": username, "status": "login_required", "http_status": resp.status_code}
    if resp.status_code != 200:
        return {"username": username, "status": "http_error", "http_status": resp.status_code}

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError):
        return {"username": username, "status": "error", "error": "invalid json"}

    user = data.get("data", {}).get("user")
    if user is None:
        return {"username": username, "status": "not_found"}

    return {
        "username": username,
        "status": "active",
        "full_name": user.get("full_name", ""),
        "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url", ""),
        "followers": user.get("edge_followed_by", {}).get("count"),
        "following": user.get("edge_follow", {}).get("count"),
        "posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
        "is_private": user.get("is_private", False),
        "is_verified": user.get("is_verified", False),
        "biography": user.get("biography", ""),
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch Instagram profile data")
    parser.add_argument("--sessionid", required=True, help="Your Instagram sessionid cookie")
    parser.add_argument("--reset", action="store_true", help="Re-fetch accounts that previously returned errors")
    args = parser.parse_args()

    if not os.path.exists(RESULTS_JSON):
        print("ERROR: results.json not found. Run find_unfollowers.py first.")
        sys.exit(1)

    with open(RESULTS_JSON) as f:
        results = json.load(f)

    # Collect all unique usernames across all categories
    all_usernames = set()
    for entry in results.get("not_following_back", []):
        all_usernames.add(entry["username"])
    for entry in results.get("pending_not_following_back", []):
        all_usernames.add(entry["username"])
    for entry in results.get("mutuals", []):
        all_usernames.add(entry["username"])
    for entry in results.get("fans", []):
        all_usernames.add(entry["username"])

    print(f"Total unique accounts: {len(all_usernames)}")

    profiles = load_existing()

    if args.reset:
        # Remove entries that had errors so they get re-fetched
        error_statuses = {"http_error", "error", "login_required"}
        removed = [u for u, p in profiles.items() if p.get("status") in error_statuses]
        for u in removed:
            del profiles[u]
        if removed:
            print(f"Reset {len(removed)} errored entries for re-fetch")
            save_progress(profiles)

    already_ok = {u for u, p in profiles.items() if p.get("status") in ("active", "not_found")}
    remaining = sorted(all_usernames - already_ok)
    print(f"Already fetched: {len(already_ok)}, remaining: {len(remaining)}")

    if not remaining:
        print("All done!")
        return

    session = requests.Session()
    session.cookies.set("sessionid", args.sessionid, domain=".instagram.com")
    consecutive_errors = 0

    for i, username in enumerate(remaining):
        print(f"[{len(already_ok) + i + 1}/{len(all_usernames)}] {username}...", end=" ", flush=True)

        result = fetch_profile(username, session)
        profiles[username] = result

        status = result.get("status", "unknown")
        extra = ""
        if status == "active":
            extra = f" ({result.get('followers', '?')} followers)"
        print(f"{status}{extra}")

        if status in ("error", "http_error", "login_required"):
            consecutive_errors += 1
            if consecutive_errors >= 5:
                print(f"\n{consecutive_errors} consecutive errors. Pausing 60s...")
                save_progress(profiles)
                time.sleep(60)
                consecutive_errors = 0
        else:
            consecutive_errors = 0

        if (i + 1) % 10 == 0:
            save_progress(profiles)

        time.sleep(random.uniform(2, 5))

    save_progress(profiles)
    print(f"\nDone! Saved {len(profiles)} profiles to {PROFILES_JSON}")

    statuses = {}
    for v in profiles.values():
        s = v.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1
    print("Status summary:", statuses)


if __name__ == "__main__":
    main()
