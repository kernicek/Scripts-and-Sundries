#!/usr/bin/env python3
"""
Find albums that look identical but the folder-album-creator sees as
different names, so it created a duplicate instead of reusing the existing
album.

Matching in the tool is a strict string == on the album name, so this
usually happens with accented folder names (e.g. Czech diacritics) stored in
different Unicode forms -- precomposed (NFC) vs decomposed (NFD) -- which
render identically but aren't the same bytes. Stray leading/trailing/double
spaces from old renames cause the same symptom.

Groups every album owned by one user by a normalized name (Unicode NFC +
collapsed whitespace); any group with more than one album is a duplicate
pair to merge by hand. Pass the same name used for that user's ALBUM_KEY_*
in the docker compose (e.g. juliette, hank, martha).

  ./immich-find-duplicate-albums.py martha
"""
import json
import os
import sys
import unicodedata
import urllib.request

if len(sys.argv) != 2:
    sys.exit(f"usage: {sys.argv[0]} <user>  (e.g. juliette, hank, martha)")

USER = sys.argv[1].upper()
IMMICH_URL = os.environ.get("IMMICH_URL", "").rstrip("/")
API_KEY = os.environ.get(f"ALBUM_KEY_{USER}", "")

if not IMMICH_URL or not API_KEY:
    sys.exit(f"set IMMICH_URL and ALBUM_KEY_{USER}")


def api(method, path):
    req = urllib.request.Request(
        IMMICH_URL + path,
        headers={"x-api-key": API_KEY, "User-Agent": "curl/8.0.0", "Accept": "*/*"},
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def normalize(name):
    return " ".join(unicodedata.normalize("NFC", name).split())


def main():
    albums = api("GET", "/albums")

    groups = {}
    for a in albums:
        groups.setdefault(normalize(a["albumName"]), []).append(a)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    if not duplicates:
        print("no duplicates found")
        return

    for key, group in duplicates.items():
        print(f"\n{key!r} -- {len(group)} albums:")
        for a in group:
            print(f"  id={a['id']}  raw={a['albumName']!r}  assets={a['assetCount']}")


main()
