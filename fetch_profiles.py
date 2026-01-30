#!/usr/bin/env python3
"""Fetch public Instagram profile data for accounts listed in following.csv."""

import csv
import json
import os
import random
import sys
import time

import requests

INPUT_CSV = os.path.join(os.path.dirname(__file__), "following.csv")
OUTPUT_JSON = os.path.join(os.path.dirname(__file__), "profiles.json")

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
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, "r") as f:
            return json.load(f)
    return {}


def save_progress(data):
    with open(OUTPUT_JSON, "w") as f:
        json.dump(data, f, indent=2)


def fetch_profile(username, session):
    try:
        resp = session.get(
            API_URL,
            params={"username": username},
            headers=HEADERS,
            timeout=15,
        )
    except requests.RequestException as e:
        return {"username": username, "status": "error", "error": str(e)}

    if resp.status_code == 404:
        return {"username": username, "status": "not_found"}

    if resp.status_code == 401 or resp.status_code == 403:
        return {"username": username, "status": "login_required", "http_status": resp.status_code}

    if resp.status_code != 200:
        return {
            "username": username,
            "status": "http_error",
            "http_status": resp.status_code,
        }

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
    # Load CSV
    with open(INPUT_CSV, "r") as f:
        reader = csv.DictReader(f)
        accounts = list(reader)

    print(f"Loaded {len(accounts)} accounts from CSV")

    # Load existing progress
    data = load_existing()
    already = set(data.keys())
    remaining = [a for a in accounts if a["username"] not in already]
    print(f"Already fetched: {len(already)}, remaining: {len(remaining)}")

    if not remaining:
        print("All done!")
        return

    session = requests.Session()
    consecutive_errors = 0

    for i, account in enumerate(remaining):
        username = account["username"]
        display_name = account.get("display_name", "")

        print(f"[{len(already) + i + 1}/{len(accounts)}] {username}...", end=" ", flush=True)

        result = fetch_profile(username, session)
        result["display_name"] = display_name
        result["profile_url"] = f"https://instagram.com/{username}"

        data[username] = result
        status = result.get("status", "unknown")
        extra = ""
        if status == "active":
            extra = f" ({result.get('followers', '?')} followers)"
        print(f"{status}{extra}")

        # Track consecutive errors for backoff
        if status in ("error", "http_error", "login_required"):
            consecutive_errors += 1
            if consecutive_errors >= 5:
                print(f"\n⚠ {consecutive_errors} consecutive errors. Pausing 60s...")
                save_progress(data)
                time.sleep(60)
                consecutive_errors = 0
        else:
            consecutive_errors = 0

        # Save every 10 accounts
        if (i + 1) % 10 == 0:
            save_progress(data)

        # Random delay
        delay = random.uniform(2, 5)
        time.sleep(delay)

    save_progress(data)
    print(f"\nDone! Saved {len(data)} profiles to {OUTPUT_JSON}")

    # Summary
    statuses = {}
    for v in data.values():
        s = v.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1
    print("Status summary:", statuses)


if __name__ == "__main__":
    main()
