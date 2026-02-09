#!/usr/bin/env python3
"""Simple web app to browse Instagram unfollower results."""

import json
import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PICS_DIR = os.path.join(SCRIPT_DIR, "pics")


@app.route("/")
def index():
    results_path = os.path.join(SCRIPT_DIR, "results.json")
    profiles_path = os.path.join(SCRIPT_DIR, "profiles.json")

    if not os.path.exists(results_path):
        return "No results.json found. Run find_unfollowers.py first.", 404

    with open(results_path) as f:
        results = json.load(f)

    profiles = {}
    if os.path.exists(profiles_path):
        with open(profiles_path) as f:
            profiles = json.load(f)

    # Check which pics exist locally
    pic_set = set()
    if os.path.isdir(PICS_DIR):
        for fname in os.listdir(PICS_DIR):
            if fname.endswith(".jpg"):
                pic_set.add(fname[:-4])

    return render_template("index.html", results=results, profiles=profiles, pic_set=list(pic_set))


@app.route("/pics/<filename>")
def serve_pic(filename):
    return send_from_directory(PICS_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
