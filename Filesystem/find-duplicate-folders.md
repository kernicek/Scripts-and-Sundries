# find-duplicate-folders

Finds sibling directories whose names look identical but differ in raw bytes.

## Why this happens

Usually Unicode normalization (NFC vs NFD) or an invisible stray character, which fools
file managers and tools that compare names by exact string equality (e.g.
immich-folder-album-creator) into treating them as two different things.

## What it does

Walks the given root and, within each parent directory, groups subfolders by a
normalized name (Unicode NFC + collapsed whitespace). Any group with more than one raw
name is a suspect duplicate pair. Read-only, does not touch anything.

Synology's `@eaDir` thumbnail-cache directories (auto-generated, one per media file) are
pruned from both the walk and the file counts, so they don't skew comparisons between a
copy that was ever touched by a Synology NAS and one that wasn't.

## Usage

```
./find-duplicate-folders.py /mnt/tank/pictures/SomeFolder
```

See also [verify-duplicate-folders](verify-duplicate-folders.md) to get a definitive
identical/differs verdict on the pairs this turns up.
