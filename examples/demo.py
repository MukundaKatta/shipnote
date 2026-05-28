"""shipnote demo — runs offline, no API key required.

    python examples/demo.py

Turns a raw commit log into grouped release notes with a SemVer bump. Then, if
this directory is a git repo, does the same on its real recent history.
"""

from __future__ import annotations

import subprocess

from shipnote import Shipnote
from shipnote.gitlog import read_commits

SAMPLE = """a1b2c3d feat(api): add pagination to list endpoints
b2c3d4e fix(auth): reject expired refresh tokens
c3d4e5f feat!: drop support for v1 config files
d4e5f6a perf(db): cache the schema lookup
e5f6a7b docs: rewrite the quickstart guide
f6a7b8c chore: bump dev dependencies
"""


def main() -> None:
    notes = Shipnote().generate(SAMPLE, version="v2.0.0")

    print("Suggested bump:", notes.version_bump, f"({notes.commit_count} commits)")
    print()
    print(notes.markdown())

    # Bonus: run on this repo's real history if available.
    try:
        log = read_commits("HEAD~10..HEAD")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return
    if log.strip():
        print("=" * 60)
        print("From this repo's last 10 commits:")
        print("=" * 60)
        print(Shipnote().generate(log).markdown())


if __name__ == "__main__":
    main()
