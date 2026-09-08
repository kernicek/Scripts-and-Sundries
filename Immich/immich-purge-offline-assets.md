# immich-purge-offline-assets

Permanently deletes offline external-library assets in Immich that the built-in "Empty
Trash" button fails to clear.

## Why this is needed

Files removed from disk get flagged `isOffline` by a library rescan, but the bulk
empty-trash action reports "0 assets" and leaves them stuck — a known bug for external
libraries (immich-app/immich#26601, #13770, #24381).

## What it does

Finds every offline asset via `/search/metadata` (paginated) and permanently deletes
them via `DELETE /assets` with `force=true`, in small batches — doing this in one huge
batch is reported to silently fail at scale (thousands of assets), same underlying
issue as the broken bulk button.

## Usage

Set `IMMICH_URL` and an `ALBUM_KEY_<USER>` env var, then:

```
./immich-purge-offline-assets.py <user>
```

e.g. `./immich-purge-offline-assets.py martha`. Only deletes assets that user's API key
can see.

## Caveats

Destructive — permanently deletes assets, no confirmation prompt.
