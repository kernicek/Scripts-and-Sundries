#!/usr/bin/env python3
"""
Hide every not-yet-named person detected in one photo (named people are left
alone). Face clustering auto-creates a person with no name for each new face,
and there's no "hide all unnamed people in this photo" button in the UI --
this walks GET /faces?id=<assetId> and bulk-hides the unnamed ones via
PUT /people.

Pass the target user as an argument (matches that user's ALBUM_KEY_* in the
docker compose, e.g. jimmy), plus optionally a photo URL copied from the
browser (works for both the asset-detail view and a person's photo-detail
view, which has two UUIDs in the path) or a bare asset UUID. With no URL/ID
given, it prompts for one, runs once, and exits.

Add -l/--loop to keep prompting for one URL after another instead of
exiting after the first -- blank line (or Ctrl-D) quits the loop.

Add -u/--ultra to instead take a *person* URL/ID (any URL containing
/people/<id>) and sweep every photo that person appears in, hiding the
unnamed people in each one. Combine with -l/--loop to sweep one person
after another.

Needs an API key with asset.read (for the ultra sweep) + face.read +
person.update -- the ALBUM_KEY_* keys were scoped for the album-creator
only, so this may 403 until those scopes are added to the key.

  ./immich-hide-unnamed-faces.py jimmy [-l|--loop] [-u|--ultra] [url-or-id]
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

UUID_RE = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

_args = sys.argv[1:]
LOOP = any(a in ("-l", "--loop") for a in _args)
ULTRA = any(a in ("-u", "--ultra") for a in _args)
_args = [a for a in _args if a not in ("-l", "--loop", "-u", "--ultra")]

if len(_args) not in (1, 2):
    sys.exit(f"usage: {sys.argv[0]} <user> [-l|--loop] [-u|--ultra] [photo-or-person-url-or-id]  (e.g. jimmy, hank, martha)")

USER = _args[0].upper()
URL_ARG = _args[1] if len(_args) == 2 else None
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
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            return json.loads(data) if data else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {e.read().decode()}")


def find_asset_id(arg):
    m = re.search(rf"/photos/({UUID_RE})", arg)
    if m:
        return m.group(1)
    matches = re.findall(UUID_RE, arg)
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f"couldn't find a single asset ID in {arg!r} (found {matches})")


def find_person_id(arg):
    m = re.search(rf"/people/({UUID_RE})", arg)
    if m:
        return m.group(1)
    matches = re.findall(UUID_RE, arg)
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f"couldn't find a single person ID in {arg!r} (found {matches})")


def hide_unnamed_in_asset(asset_id):
    faces = api("GET", f"/faces?id={asset_id}")
    print(f"{len(faces)} face(s) detected on asset {asset_id}")

    targets = [
        f["person"] for f in faces
        if f["person"] and not f["person"]["name"] and not f["person"]["isHidden"]
    ]
    if not targets:
        print("nothing to hide (no unnamed, unhidden people found)")
        return

    result = api("PUT", "/people", {
        "people": [{"id": p["id"], "isHidden": True} for p in targets],
    })
    failed = [r for r in result if not r["success"]]
    print(f"hidden {len(result) - len(failed)}/{len(result)} unnamed person(s)")
    for r in failed:
        print(f"  failed {r['id']}: {r.get('error')}")


def hide_unnamed(arg):
    hide_unnamed_in_asset(find_asset_id(arg))


def find_person_assets(person_id):
    ids = []
    page = 1
    while True:
        result = api("POST", "/search/metadata", {
            "personIds": [person_id],
            "size": 1000,
            "page": page,
        })
        items = result["assets"]["items"]
        ids.extend(a["id"] for a in items)
        if not items:
            break
        page += 1
    return ids


def hide_unnamed_ultra(arg):
    person_id = find_person_id(arg)
    asset_ids = find_person_assets(person_id)
    print(f"person {person_id} appears in {len(asset_ids)} photo(s)")
    for i, asset_id in enumerate(asset_ids, 1):
        print(f"[{i}/{len(asset_ids)}] ", end="")
        hide_unnamed_in_asset(asset_id)


RUN = hide_unnamed_ultra if ULTRA else hide_unnamed
PROMPT = "Person URL or ID: " if ULTRA else "Photo URL or asset ID: "


def main():
    if not LOOP:
        arg = URL_ARG or input(PROMPT).strip()
        try:
            RUN(arg)
        except (ValueError, RuntimeError) as e:
            sys.exit(str(e))
        return

    if URL_ARG:
        try:
            RUN(URL_ARG)
        except (ValueError, RuntimeError) as e:
            print(f"  error: {e}")

    what = "person URL/ID" if ULTRA else "photo URL/asset ID"
    print(f"Paste one {what} after another, blank line (or Ctrl-D) to quit.")
    while True:
        try:
            arg = input(PROMPT).strip()
        except EOFError:
            print()
            break
        if not arg:
            break
        try:
            RUN(arg)
        except (ValueError, RuntimeError) as e:
            print(f"  error: {e}")


main()
