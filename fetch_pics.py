#!/usr/bin/env python3
"""Download profile pictures from profiles.json into a local folder."""

import json
import os
import random
import time

import requests

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_JSON = os.path.join(DATA_DIR, "profiles.json")
PICS_DIR = os.path.join(DATA_DIR, "pics")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/125.0.0.0 Safari/537.36",
}


def main():
    with open(PROFILES_JSON, "r") as f:
        profiles = json.load(f)

    os.makedirs(PICS_DIR, exist_ok=True)

    to_fetch = []
    for username, p in profiles.items():
        url = p.get("profile_pic_url", "")
        if not url:
            continue
        # Skip if already downloaded
        dest = os.path.join(PICS_DIR, f"{username}.jpg")
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            continue
        to_fetch.append((username, url))

    print(f"Total profiles: {len(profiles)}, already downloaded: {len(profiles) - len(to_fetch)}, to fetch: {len(to_fetch)}")

    if not to_fetch:
        print("All done!")
        return

    session = requests.Session()
    success = 0
    failed = 0

    for i, (username, url) in enumerate(to_fetch):
        print(f"[{i + 1}/{len(to_fetch)}] {username}...", end=" ", flush=True)
        dest = os.path.join(PICS_DIR, f"{username}.jpg")
        try:
            resp = session.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 100:
                with open(dest, "wb") as f:
                    f.write(resp.content)
                print(f"ok ({len(resp.content)} bytes)")
                success += 1
            else:
                print(f"failed (status {resp.status_code})")
                failed += 1
        except Exception as e:
            print(f"error ({e})")
            failed += 1

        time.sleep(random.uniform(0.3, 1.0))

    print(f"\nDone! {success} downloaded, {failed} failed")


if __name__ == "__main__":
    main()
