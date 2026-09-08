# verify-duplicate-folders

For every pair of sibling directories whose names collide under Unicode NFC
normalization (see [find-duplicate-folders](find-duplicate-folders.md)), hashes every
file in both copies and gives a definitive verdict instead of trusting a file-count
match.

- `IDENTICAL` — every relative path exists in both copies with the same content, safe
  to delete either one.
- `DIFFERS` — lists files that exist only in one copy, or exist in both but with
  different content. Needs manual review before anything gets deleted.

## Usage

```
./verify-duplicate-folders.py /mnt/tank/pictures/SomeFolder
```

Hashes every file in both copies (recursively, skipping Synology `@eaDir`). Read-only —
does not touch, move, or delete anything. Hashing a large archive takes a while, run it
under tmux.
