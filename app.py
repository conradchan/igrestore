#!/usr/bin/env python3
"""Local web app to browse Instagram following list."""

import csv
import json
import os
import sqlite3

from flask import Flask, render_template, jsonify, send_from_directory, request

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_JSON = os.path.join(DATA_DIR, "profiles.json")
FOLLOWING_CSV = os.path.join(DATA_DIR, "following.csv")
PICS_DIR = os.path.join(DATA_DIR, "pics")
DB_PATH = os.path.join(DATA_DIR, "decisions.db")

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS decisions "
        "(username TEXT PRIMARY KEY, decision TEXT NOT NULL DEFAULT 'undecided', notes TEXT DEFAULT '')"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS manual_adds "
        "(username TEXT PRIMARY KEY, display_name TEXT DEFAULT '', notes TEXT DEFAULT '', "
        "decision TEXT NOT NULL DEFAULT 'will_follow', added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS people "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, notes TEXT DEFAULT '', "
        "added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    return conn


def get_all_decisions():
    conn = get_db()
    rows = conn.execute("SELECT username, decision, notes FROM decisions").fetchall()
    conn.close()
    return {r[0]: {"decision": r[1], "notes": r[2] or ""} for r in rows}


def load_data():
    csv_data = {}
    with open(FOLLOWING_CSV, "r") as f:
        for row in csv.DictReader(f):
            csv_data[row["username"]] = row

    profiles = {}
    if os.path.exists(PROFILES_JSON):
        with open(PROFILES_JSON, "r") as f:
            profiles = json.load(f)

    decisions = get_all_decisions()

    result = []
    for username, csv_row in csv_data.items():
        entry = {
            "username": username,
            "display_name": csv_row.get("display_name", ""),
            "profile_url": f"https://instagram.com/{username}",
            "status": "unknown",
            "followers": None,
            "following": None,
            "posts": None,
            "is_private": False,
            "is_verified": False,
            "biography": "",
            "has_pic": os.path.exists(os.path.join(PICS_DIR, f"{username}.jpg")),
            "decision": decisions.get(username, {}).get("decision", "undecided"),
            "notes": decisions.get(username, {}).get("notes", ""),
        }
        if username in profiles:
            p = profiles[username]
            entry["status"] = p.get("status", "unknown")
            entry["followers"] = p.get("followers")
            entry["following"] = p.get("following")
            entry["posts"] = p.get("posts")
            entry["is_private"] = p.get("is_private", False)
            entry["is_verified"] = p.get("is_verified", False)
            entry["biography"] = p.get("biography", "")
            if p.get("full_name"):
                entry["display_name"] = p["full_name"]
        result.append(entry)

    return result


@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", profiles=data, total=len(data))


@app.route("/api/profiles")
def api_profiles():
    return jsonify(load_data())


@app.route("/pics/<filename>")
def serve_pic(filename):
    return send_from_directory(PICS_DIR, filename)


@app.route("/api/decision", methods=["POST"])
def set_decision():
    data = request.get_json()
    username = data.get("username", "")
    decision = data.get("decision", "undecided")
    notes = data.get("notes")
    if not username:
        return jsonify({"error": "missing username"}), 400
    conn = get_db()
    conn.execute(
        "INSERT INTO decisions (username, decision, notes) VALUES (?, ?, ?) "
        "ON CONFLICT(username) DO UPDATE SET decision=excluded.decision, notes=excluded.notes",
        (username, decision, notes),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/people", methods=["GET"])
def get_people():
    conn = get_db()
    rows = conn.execute("SELECT id, name, notes FROM people ORDER BY added_at DESC").fetchall()
    conn.close()
    return jsonify([{"id": r[0], "name": r[1], "notes": r[2] or ""} for r in rows])


@app.route("/api/people", methods=["POST"])
def add_person():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "missing name"}), 400
    notes = data.get("notes", "")
    conn = get_db()
    cur = conn.execute("INSERT INTO people (name, notes) VALUES (?, ?)", (name, notes))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return jsonify({"ok": True, "id": pid})


@app.route("/api/people/<int:pid>", methods=["PUT"])
def update_person(pid):
    data = request.get_json()
    conn = get_db()
    conn.execute("UPDATE people SET notes = ? WHERE id = ?", (data.get("notes", ""), pid))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/people/<int:pid>", methods=["DELETE"])
def delete_person(pid):
    conn = get_db()
    conn.execute("DELETE FROM people WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
