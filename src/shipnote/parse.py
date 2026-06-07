"""Parse commit messages into structured, grouped data.

Understands Conventional Commits (`feat(scope): subject`, with `!` or a
`BREAKING CHANGE` note marking a break). Anything that does not match is kept
as an "other" commit rather than dropped, so no history is lost.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_CONVENTIONAL = re.compile(
    r"^(?P<type>[a-zA-Z]+)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<bang>!)?:\s*"
    r"(?P<subject>.+)$"
)
_HASH_PREFIX = re.compile(r"^(?P<hash>[0-9a-f]{7,40})\s+(?P<rest>.+)$", re.IGNORECASE)

# type -> human section title
TYPE_TITLES: dict[str, str] = {
    "feat": "Features",
    "fix": "Fixes",
    "perf": "Performance",
    "refactor": "Refactors",
    "docs": "Documentation",
    "build": "Build",
    "ci": "CI",
    "test": "Tests",
    "style": "Styles",
    "chore": "Chores",
    "revert": "Reverts",
    "other": "Other",
}

# Order sections appear in the changelog.
SECTION_ORDER: tuple[str, ...] = (
    "feat",
    "fix",
    "perf",
    "refactor",
    "docs",
    "build",
    "ci",
    "test",
    "style",
    "chore",
    "revert",
    "other",
)

# (singular, plural) noun for count summaries — English plurals are irregular,
# so spell them out rather than chopping an "s".
COUNT_LABELS: dict[str, tuple[str, str]] = {
    "feat": ("feature", "features"),
    "fix": ("fix", "fixes"),
    "perf": ("performance improvement", "performance improvements"),
    "refactor": ("refactor", "refactors"),
    "docs": ("docs update", "docs updates"),
    "build": ("build change", "build changes"),
    "ci": ("CI change", "CI changes"),
    "test": ("test", "tests"),
    "style": ("style change", "style changes"),
    "chore": ("chore", "chores"),
    "revert": ("revert", "reverts"),
    "other": ("other change", "other changes"),
}


def count_label(section: str, n: int) -> str:
    """`<n> <noun>` with the noun pluralized to match `n`."""
    singular, plural = COUNT_LABELS.get(section, (section, f"{section}s"))
    return f"{n} {singular if n == 1 else plural}"


@dataclass
class Commit:
    type: str
    scope: str | None
    breaking: bool
    subject: str
    raw: str
    hash: str | None = None


def parse_commit(line: str) -> Commit:
    """Parse one commit line (optionally prefixed with a git hash)."""
    text = line.strip()
    commit_hash: str | None = None

    m = _HASH_PREFIX.match(text)
    if m:
        commit_hash = m.group("hash").lower()
        text = m.group("rest")

    breaking = "BREAKING CHANGE" in text
    cc = _CONVENTIONAL.match(text)
    if cc:
        return Commit(
            type=cc.group("type").lower(),
            scope=cc.group("scope"),
            breaking=breaking or bool(cc.group("bang")),
            subject=cc.group("subject").strip(),
            raw=line.strip(),
            hash=commit_hash,
        )
    return Commit(
        type="other",
        scope=None,
        breaking=breaking,
        subject=text,
        raw=line.strip(),
        hash=commit_hash,
    )


def parse_commits(text: str) -> list[Commit]:
    """Parse a block of commit lines, one per line."""
    return [parse_commit(line) for line in text.splitlines() if line.strip()]


def group_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    """Bucket commits by type, in SECTION_ORDER, omitting empty buckets."""
    grouped: dict[str, list[Commit]] = {}
    for section in SECTION_ORDER:
        bucket = [c for c in commits if c.type == section]
        if bucket:
            grouped[section] = bucket
    # types outside the known order still get a bucket under their own name
    for c in commits:
        if c.type not in SECTION_ORDER:
            grouped.setdefault(c.type, []).append(c)
    return grouped


def suggest_bump(commits: list[Commit]) -> str:
    """SemVer bump implied by the commits: major / minor / patch."""
    if any(c.breaking for c in commits):
        return "major"
    if any(c.type == "feat" for c in commits):
        return "minor"
    return "patch"
