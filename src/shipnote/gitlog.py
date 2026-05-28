"""Read commit lines straight from a local git repository.

Thin wrapper over `git log` so you can point shipnote at a real repo:

    from shipnote.gitlog import read_commits
    notes = Shipnote().generate(read_commits("v1.0.0..HEAD"))

Uses only the standard library; no GitPython dependency.
"""

from __future__ import annotations

import subprocess


def read_commits(rev_range: str = "HEAD~20..HEAD", *, cwd: str = ".") -> str:
    """Return `hash subject` lines for `rev_range`, newest first.

    Merge commits are skipped. Raises CalledProcessError if git fails (e.g. the
    range is invalid or `cwd` is not a repository).
    """
    result = subprocess.run(
        ["git", "-C", cwd, "log", "--no-merges", "--pretty=%h %s", rev_range],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout
