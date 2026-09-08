#!/usr/bin/env python3
"""
Fix wrong capture dates on external-library albums, one album at a time.

For each album owned by the API key's user, shows the photo count and asks
for the correct date. Each asset gets staggered a minute apart (by filename)
so relative order survives, same trick as the exiftool version but done as a
plain Immich DB update through the API -- never touches the read-only files,
so no library rescan is needed and it's safe on any library size.

Needs an API key with album.read + asset.update. Operates on one user's
albums at a time -- pass the same name used for that user's ALBUM_KEY_* in
the docker compose (e.g. juliette, hank, martha).

  ./immich-redate-album.py martha
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta

if len(sys.argv) != 2:
    sys.exit(f"usage: {sys.argv[0]} <user>  (e.g. juliette, hank, martha)")

USER = sys.argv[1].upper()
IMMICH_URL = os.environ.get("IMMICH_URL", "").rstrip("/")
API_KEY = os.environ.get(f"ALBUM_KEY_{USER}", "")

if not IMMICH_URL or not API_KEY:
    sys.exit(f"set IMMICH_URL and ALBUM_KEY_{USER}")


def api(method, path, body=None):
    req = urllib.request.Request(
        IMMICH_URL + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json",
            "User-Agent": "curl/8.0.0",
            "Accept": "*/*",
        },
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
        return json.loads(data) if data else None


def main():
    albums = sorted(api("GET", "/albums"), key=lambda a: a["albumName"])

    for album in albums:
        detail = api("GET", f"/albums/{album['id']}")
        assets = sorted(detail["assets"], key=lambda a: a["originalFileName"])
        print(f"\n{album['albumName']} ({len(assets)} photos)")
        answer = input("Correct date (YYYY-MM-DD), or Enter to skip: ").strip()
        if not answer:
            continue
        base = datetime.strptime(answer, "%Y-%m-%d").replace(hour=12)
        for i, asset in enumerate(assets):
            when = (base + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            api("PUT", "/assets", {"ids": [asset["id"]], "dateTimeOriginal": when})
        print(f"  updated {len(assets)} photos")


main()
