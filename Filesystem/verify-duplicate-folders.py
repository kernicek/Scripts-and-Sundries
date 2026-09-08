#!/usr/bin/env python3
"""
For every pair of sibling directories whose names collide under Unicode
NFC normalization (see find-duplicate-folders.py), hash every file in
both copies (recursively, skipping Synology @eaDir) and give a definitive
verdict instead of trusting a file-count match:

  IDENTICAL         every relative path exists in both copies with the
                     same content -- safe to delete either one.
  DIFFERS           lists files that exist only in one copy, or exist in
                     both but with different content. Needs manual review
                     before anything gets deleted.

Read-only. Does not touch, move, or delete anything. Hashing a large
archive takes a while -- run it under tmux.

  ./verify-duplicate-folders.py /mnt/tank/pictures/SomeFolder
"""
import hashlib
import os
import sys
import unicodedata

IGNORE_DIRS = {"@eaDir"}


def normalize(name):
    return " ".join(unicodedata.normalize("NFC", name).split())


def hash_tree(root):
    hashes = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            h = hashlib.sha256()
            with open(full, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            hashes[rel] = h.hexdigest()
    return hashes


def find_pairs(root):
    pairs = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        groups = {}
        for name in dirnames:
            groups.setdefault(normalize(name), []).append(name)
        for raw_names in groups.values():
            if len(raw_names) > 1:
                pairs.append([os.path.join(dirpath, raw) for raw in raw_names])
    return pairs


def main():
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <root-path>")
    root = sys.argv[1]

    for pair in find_pairs(root):
        if len(pair) != 2:
            print(f"\n{pair!r}\n  SKIPPED: more than 2 copies, needs manual review")
            continue
        a, b = pair
        hashes_a = hash_tree(a)
        hashes_b = hash_tree(b)

        only_a = sorted(set(hashes_a) - set(hashes_b))
        only_b = sorted(set(hashes_b) - set(hashes_a))
        differing = sorted(p for p in set(hashes_a) & set(hashes_b) if hashes_a[p] != hashes_b[p])

        print(f"\n{a}\n{b}")
        if not only_a and not only_b and not differing:
            print("  IDENTICAL")
        else:
            print("  DIFFERS")
            for p in only_a:
                print(f"    only in copy 1: {p}")
            for p in only_b:
                print(f"    only in copy 2: {p}")
            for p in differing:
                print(f"    different content: {p}")


main()
