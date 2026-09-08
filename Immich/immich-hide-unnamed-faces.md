# immich-hide-unnamed-faces

Hides every not-yet-named person detected in one Immich photo (named people are left
alone).

## Why this is needed

Face clustering auto-creates a person with no name for each new face, and there's no
"hide all unnamed people in this photo" button in the UI. This walks
`GET /faces?id=<assetId>` and bulk-hides the unnamed ones via `PUT /people`.

## Usage

Set `IMMICH_URL` and an `ALBUM_KEY_<USER>` env var, then:

```
./immich-hide-unnamed-faces.py <user> [-l|--loop] [-u|--ultra] [url-or-id]
```

e.g. `./immich-hide-unnamed-faces.py jimmy`. Pass a photo URL copied from the browser
(works for both the asset-detail view and a person's photo-detail view, which has two
UUIDs in the path) or a bare asset UUID. With no URL/ID given, it prompts for one, runs
once, and exits.

- `-l`/`--loop` — keep prompting for one URL after another; blank line (or Ctrl-D) quits.
- `-u`/`--ultra` — take a *person* URL/ID instead (any URL containing `/people/<id>`) and
  sweep every photo that person appears in, hiding the unnamed people in each one.
  Combine with `-l`/`--loop` to sweep one person after another.

## Caveats

Needs an API key with `asset.read` (for the ultra sweep) + `face.read` + `person.update`
— a key scoped only for album creation will 403 until those scopes are added.
