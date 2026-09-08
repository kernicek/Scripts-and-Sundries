#!/usr/bin/env python3
"""
Find sibling directories whose names look identical but differ in raw
bytes -- usually Unicode normalization (NFC vs NFD) or an invisible stray
character -- which fools file managers and tools that compare names by
exact string equality (e.g. immich-folder-album-creator) into treating
them as two different things.

Walks the given root and, within each parent directory, groups subfolders
by a normalized name (Unicode NFC + collapsed whitespace). Any group with
more than one raw name is a suspect duplicate pair. Read-only, does not
touch anything.

Synology's @eaDir thumbnail-cache directories (auto-generated, one per
media file) are pruned from both the walk and the file counts, so they
don't skew comparisons between a copy that was ever touched by a Synology
NAS and one that wasn't.

  ./find-duplicate-folders.py /mnt/tank/pictures/SomeFolder
"""
import os
import sys
import unicodedata

IGNORE_DIRS = {"@eaDir"}


def normalize(name):
    return " ".join(unicodedata.normalize("NFC", name).split())


def count_files(path):
    total = 0
    for _, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        total += len(filenames)
    return total


def main():
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <root-path>")
    root = sys.argv[1]

    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        groups = {}
        for name in dirnames:
            groups.setdefault(normalize(name), []).append(name)
        for norm_name, raw_names in groups.items():
            if len(raw_names) > 1:
                print(f"\n{dirpath}/{norm_name!r}")
                for raw in raw_names:
                    full = os.path.join(dirpath, raw)
                    file_count = count_files(full)
                    print(f"  {raw!r}  ({file_count} files)  bytes={raw.encode('utf-8', 'surrogateescape')}")


main()
