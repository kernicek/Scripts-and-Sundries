# immich-find-duplicate-albums

Finds Immich albums that look identical but the folder-album-creator sees as different
names, so it created a duplicate instead of reusing the existing album.

## Why this happens

The folder-album-creator matches by strict string equality on the album name. This
usually happens with accented folder names (e.g. Czech diacritics) stored in different
Unicode forms — precomposed (NFC) vs decomposed (NFD) — which render identically but
aren't the same bytes. Stray leading/trailing/double spaces from old renames cause the
same symptom.

## Usage

Set `IMMICH_URL` and an `ALBUM_KEY_<USER>` env var (matching the API key used for that
user in the folder-album-creator's docker compose), then:

```
./immich-find-duplicate-albums.py <user>
```

e.g. `./immich-find-duplicate-albums.py martha`. Groups every album owned by that user
by a normalized name (Unicode NFC + collapsed whitespace); any group with more than one
album is a duplicate pair to merge by hand. Read-only — it only lists candidates.
