"""shipnote test suite. Runs fully offline against the StubBackend."""

from __future__ import annotations

from shipnote import (
    Shipnote,
    group_commits,
    parse_commit,
    parse_commits,
    suggest_bump,
)

SAMPLE = """a1b2c3d feat(api): add pagination to list endpoints
b2c3d4e fix(auth): reject expired refresh tokens
c3d4e5f feat!: drop support for v1 config
d4e5f6a docs: rewrite the quickstart
e5f6a7b chore: bump deps
f6a7b8c just a plain message with no type
"""


# ---- parsing ---------------------------------------------------------------


def test_parse_conventional_commit():
    c = parse_commit("feat(api): add pagination")
    assert c.type == "feat"
    assert c.scope == "api"
    assert c.breaking is False
    assert c.subject == "add pagination"


def test_parse_bang_marks_breaking():
    c = parse_commit("feat!: drop v1 config")
    assert c.type == "feat"
    assert c.breaking is True


def test_parse_breaking_change_note():
    c = parse_commit("refactor: rework store BREAKING CHANGE: new layout")
    assert c.breaking is True


def test_parse_hash_prefix_is_extracted():
    c = parse_commit("a1b2c3d fix(auth): reject expired tokens")
    assert c.hash == "a1b2c3d"
    assert c.type == "fix"
    assert c.scope == "auth"


def test_non_conventional_is_kept_as_other():
    c = parse_commit("just a plain message")
    assert c.type == "other"
    assert c.subject == "just a plain message"


# ---- grouping + bump -------------------------------------------------------


def test_group_buckets_by_type():
    grouped = group_commits(parse_commits(SAMPLE))
    assert len(grouped["feat"]) == 2
    assert len(grouped["fix"]) == 1
    assert len(grouped["other"]) == 1


def test_bump_major_on_breaking():
    assert suggest_bump(parse_commits(SAMPLE)) == "major"


def test_bump_minor_on_feat_without_breaking():
    commits = parse_commits("feat: add thing\nfix: a bug")
    assert suggest_bump(commits) == "minor"


def test_bump_patch_on_fixes_only():
    commits = parse_commits("fix: a\nfix: b\ndocs: c")
    assert suggest_bump(commits) == "patch"


# ---- release notes ---------------------------------------------------------


def test_generate_populates_release_notes():
    notes = Shipnote().generate(SAMPLE, version="v2.0.0")
    assert notes.version == "v2.0.0"
    assert notes.version_bump == "major"
    assert notes.commit_count == 6
    assert len(notes.breaking) == 1
    assert notes.backend == "stub"


def test_markdown_has_sections_and_breaking():
    md = Shipnote().generate(SAMPLE, version="v2.0.0").markdown()
    assert "## v2.0.0" in md
    assert "### ⚠ BREAKING CHANGES" in md
    assert "### Features" in md
    assert "### Fixes" in md
    assert "add pagination" in md


def test_default_version_reflects_bump():
    notes = Shipnote().generate("fix: a tiny bug")
    assert notes.version_bump == "patch"
    assert "patch" in notes.version


def test_stub_highlights_count_changes():
    notes = Shipnote().generate(SAMPLE)
    assert "breaking change" in notes.highlights.lower()
    assert "feature" in notes.highlights.lower()


def test_generate_is_deterministic():
    a = Shipnote().generate(SAMPLE, version="v2.0.0").markdown()
    b = Shipnote().generate(SAMPLE, version="v2.0.0").markdown()
    assert a == b


def test_to_dict_keys():
    d = Shipnote().generate(SAMPLE, version="v2.0.0").to_dict()
    for key in ("version", "version_bump", "commit_count", "breaking", "sections", "backend"):
        assert key in d
