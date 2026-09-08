#!/usr/bin/env python3
"""
Permanently delete offline external-library assets (files removed from disk,
detected by a library rescan) that Immich's own "Empty Trash" button fails
to clear -- a known bug for external libraries (immich-app/immich#26601,
#13770, #24381): the bulk empty-trash action reports "0 assets" and leaves
them stuck.

Finds every isOffline asset via /search/metadata (paginated) and permanently
deletes them via DELETE /assets with force=true, in small batches -- doing
this in one huge batch is reported to silently fail at scale (thousands of
assets), same underlying issue as the broken bulk button.

Pass the target user as an argument (matches that user's ALBUM_KEY_* in the
docker compose, e.g. martha) -- only deletes assets that user's key can see.

  ./immich-purge-offline-assets.py martha
"""
import json
import os
import sys
import urllib.request

if len(sys.argv) != 2:
    sys.exit(f"usage: {sys.argv[0]} <user>  (e.g. juliette, hank, martha)")

USER = sys.argv[1].upper()
IMMICH_URL = os.environ.get("IMMICH_URL", "").rstrip("/")
API_KEY = os.environ.get(f"ALBUM_KEY_{USER}", "")
BATCH_SIZE = 200

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


def find_offline_asset_ids():
    ids = []
    page = 1
    while True:
        result = api("POST", "/search/metadata", {
            "isOffline": True,
            "withDeleted": True,
            "size": 1000,
            "page": page,
        })
        items = result["assets"]["items"]
        ids.extend(a["id"] for a in items)
        print(f"  fetched page {page}: {len(items)} assets (total so far: {len(ids)})")
        if not items:
            break
        page += 1
    return ids


def main():
    print("Finding offline assets...")
    ids = find_offline_asset_ids()
    print(f"\n{len(ids)} offline assets found. Deleting in batches of {BATCH_SIZE}...")

    for i in range(0, len(ids), BATCH_SIZE):
        batch = ids[i:i + BATCH_SIZE]
        api("DELETE", "/assets", {"ids": batch, "force": True})
        print(f"  deleted {i + len(batch)}/{len(ids)}")

    print("Done.")


main()
