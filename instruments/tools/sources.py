"""Locate and checksum an instrument package's source files.

Sources are licensed and never committed. They live under forms/ (gitignored),
unpacked from the team's Drive folder ("Web-CDI Updates 2026", downloaded as a
zip). Each package manifest lists its sources by path relative to forms/, with
the Drive file id for provenance and a sha256 that pins the exact bytes the
package was extracted from.

Usage: python sources.py PACKAGE [PACKAGE ...]   # verify, recording missing hashes
"""

import hashlib
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
PACKAGES = REPO / "instruments" / "packages"
FORMS = REPO / "forms"


def path(src):
    return FORMS / src["path"]


def verify(package):
    mpath = PACKAGES / package / "manifest.yaml"
    manifest = yaml.safe_load(mpath.read_text())
    changed = False
    for src in manifest["sources"]:
        p = path(src)
        if not p.exists():
            sys.exit(f"{package}: missing source {p} — unpack the Drive folder into forms/")
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if src.get("sha256") and src["sha256"] != digest:
            sys.exit(f"{package}: {src['path']} differs from the version this package was "
                     "extracted from (sha256 mismatch); re-extract deliberately")
        if not src.get("sha256"):
            src["sha256"] = digest
            changed = True
        print(f"{package}: {src['path']} ok ({digest[:12]})")
    if changed:
        mpath.write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        verify(p)
