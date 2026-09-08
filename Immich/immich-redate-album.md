# immich-redate-album

Fixes wrong capture dates on external-library albums in Immich, one album at a time.

## What it does

For each album owned by the API key's user, shows the photo count and asks for the
correct date. Each asset gets staggered a minute apart (by filename) so relative order
survives. Goes through the Immich API rather than exiftool on the files, so it never
touches the read-only external-library files and no library rescan is needed — safe on
any library size.

## Usage

Needs an API key with `album.read` + `asset.update`. Set `IMMICH_URL` and an
`ALBUM_KEY_<USER>` env var, then:

```
./immich-redate-album.py <user>
```

e.g. `./immich-redate-album.py martha`. Walks that user's albums, prompts for a date
(`YYYY-MM-DD`) per album, Enter to skip.
