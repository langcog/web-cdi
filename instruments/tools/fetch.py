"""Fetch an instrument's source files from Google Drive by file ID.

Sources are listed in the package manifest (instruments/packages/<name>/manifest.yaml)
under `sources:` with a Drive `id`. Files land in forms/new-instruments/<name>/
(gitignored: form PDFs are licensed and are never committed), and their sha256
is checked against / recorded in the manifest so later steps can prove which
bytes they were derived from.

Needs Application Default Credentials with the drive.readonly scope:
  gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive.readonly

Usage: python fetch.py PACKAGE [PACKAGE ...]
"""

import hashlib
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import google.auth
import google.auth.transport.requests
import yaml

REPO = Path(__file__).resolve().parents[2]
PACKAGES = REPO / "instruments" / "packages"
DEST = REPO / "forms" / "new-instruments"
QUOTA_PROJECT = "hs-hs-langcog-gemini"


def token():
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/drive.readonly"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def download(file_id, tok):
    q = urllib.parse.urlencode({"alt": "media", "supportsAllDrives": "true"})
    req = urllib.request.Request(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?{q}",
        headers={"Authorization": f"Bearer {tok}", "x-goog-user-project": QUOTA_PROJECT},
    )
    with urllib.request.urlopen(req) as r:
        return r.read()


def fetch(package, tok):
    mpath = PACKAGES / package / "manifest.yaml"
    manifest = yaml.safe_load(mpath.read_text())
    changed = False
    for src in manifest["sources"]:
        data = download(src["id"], tok)
        digest = hashlib.sha256(data).hexdigest()
        if src.get("sha256") and src["sha256"] != digest:
            sys.exit(f"{package}: {src['file']} changed on Drive (sha256 mismatch); "
                     "re-extract and update the manifest deliberately")
        if not src.get("sha256"):
            src["sha256"] = digest
            changed = True
        out = DEST / package / src["file"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print(f"{package}: {src['file']} ({len(data)} bytes) sha256 {digest[:12]}")
    if changed:
        mpath.write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    tok = token()
    for p in sys.argv[1:]:
        fetch(p, tok)
