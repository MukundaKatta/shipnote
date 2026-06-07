"""shipnote test suite.

Runs fully offline against the keyless ``StubBackend`` and uses only the
standard library (``unittest``), so it works with::

    python -m unittest discover -s tests

and equally under ``pytest`` if you have it installed.
"""

from __future__ import annotations

import unittest

from shipnote import (
    Shipnote,
    StubBackend,
    group_commits,
    parse_commit,
    parse_commits,
    suggest_bump,
)
from shipnote.parse import count_label

SAMPLE = """a1b2c3d feat(api): add pagination to list endpoints
b2c3d4e fix(auth): reject expired refresh tokens
c3d4e5f feat!: drop support for v1 config
d4e5f6a docs: rewrite the quickstart
e5f6a7b chore: bump deps
f6a7b8c just a plain message with no type
"""


class ParseTests(unittest.TestCase):
    def test_parse_conventional_commit(self):
        c = parse_commit("feat(api): add pagination")
        self.assertEqual(c.type, "feat")
        self.assertEqual(c.scope, "api")
        self.assertFalse(c.breaking)
        self.assertEqual(c.subject, "add pagination")

    def test_parse_bang_marks_breaking(self):
        c = parse_commit("feat!: drop v1 config")
        self.assertEqual(c.type, "feat")
        self.assertTrue(c.breaking)

    def test_parse_breaking_change_note(self):
        c = parse_commit("refactor: rework store BREAKING CHANGE: new layout")
        self.assertTrue(c.breaking)

    def test_parse_hash_prefix_is_extracted(self):
        c = parse_commit("a1b2c3d fix(auth): reject expired tokens")
        self.assertEqual(c.hash, "a1b2c3d")
        self.assertEqual(c.type, "fix")
        self.assertEqual(c.scope, "auth")

    def test_parse_hash_is_lowercased(self):
        c = parse_commit("A1B2C3D feat: shout")
        self.assertEqual(c.hash, "a1b2c3d")

    def test_non_conventional_is_kept_as_other(self):
        c = parse_commit("just a plain message")
        self.assertEqual(c.type, "other")
        self.assertEqual(c.subject, "just a plain message")

    def test_type_is_lowercased(self):
        c = parse_commit("FEAT: shout")
        self.assertEqual(c.type, "feat")

    def test_parse_commits_skips_blank_lines(self):
        commits = parse_commits("feat: a\n\n   \nfix: b\n")
        self.assertEqual(len(commits), 2)


class GroupingTests(unittest.TestCase):
    def test_group_buckets_by_type(self):
        grouped = group_commits(parse_commits(SAMPLE))
        self.assertEqual(len(grouped["feat"]), 2)
        self.assertEqual(len(grouped["fix"]), 1)
        self.assertEqual(len(grouped["other"]), 1)

    def test_group_follows_section_order(self):
        grouped = group_commits(parse_commits("fix: b\nfeat: a"))
        # feat must come before fix regardless of input order
        self.assertEqual(list(grouped.keys()), ["feat", "fix"])

    def test_unknown_type_keeps_every_commit(self):
        # Regression: an unrecognized-but-typed commit (e.g. "wip") used to keep
        # only the first occurrence, silently dropping the rest. The library's
        # promise is that it never drops history, so every "wip" must survive.
        grouped = group_commits(parse_commits("wip: a\nwip: b\nfeat: c"))
        self.assertEqual(len(grouped["wip"]), 2)
        self.assertEqual([c.subject for c in grouped["wip"]], ["a", "b"])

    def test_grouping_loses_no_commits(self):
        commits = parse_commits("wip: a\nwip: b\nfeat: c\nplain line\nxyz: q")
        grouped = group_commits(commits)
        total = sum(len(v) for v in grouped.values())
        self.assertEqual(total, len(commits))


class BumpTests(unittest.TestCase):
    def test_bump_major_on_breaking(self):
        self.assertEqual(suggest_bump(parse_commits(SAMPLE)), "major")

    def test_bump_minor_on_feat_without_breaking(self):
        commits = parse_commits("feat: add thing\nfix: a bug")
        self.assertEqual(suggest_bump(commits), "minor")

    def test_bump_patch_on_fixes_only(self):
        commits = parse_commits("fix: a\nfix: b\ndocs: c")
        self.assertEqual(suggest_bump(commits), "patch")

    def test_bump_patch_on_empty(self):
        self.assertEqual(suggest_bump([]), "patch")


class CountLabelTests(unittest.TestCase):
    def test_singular(self):
        self.assertEqual(count_label("fix", 1), "1 fix")

    def test_irregular_plural(self):
        # The reason an explicit map exists: "fixes", not "fixs"/"fixe".
        self.assertEqual(count_label("fix", 3), "3 fixes")

    def test_feature_plural(self):
        self.assertEqual(count_label("feat", 2), "2 features")

    def test_unknown_section_falls_back_to_naive_plural(self):
        self.assertEqual(count_label("widget", 2), "2 widgets")


class ReleaseNotesTests(unittest.TestCase):
    def test_generate_populates_release_notes(self):
        notes = Shipnote().generate(SAMPLE, version="v2.0.0")
        self.assertEqual(notes.version, "v2.0.0")
        self.assertEqual(notes.version_bump, "major")
        self.assertEqual(notes.commit_count, 6)
        self.assertEqual(len(notes.breaking), 1)
        self.assertEqual(notes.backend, "stub")

    def test_markdown_has_sections_and_breaking(self):
        md = Shipnote().generate(SAMPLE, version="v2.0.0").markdown()
        self.assertIn("## v2.0.0", md)
        self.assertIn("### ⚠ BREAKING CHANGES", md)
        self.assertIn("### Features", md)
        self.assertIn("### Fixes", md)
        self.assertIn("add pagination", md)

    def test_default_version_reflects_bump(self):
        notes = Shipnote().generate("fix: a tiny bug")
        self.assertEqual(notes.version_bump, "patch")
        self.assertIn("patch", notes.version)

    def test_stub_highlights_count_changes(self):
        notes = Shipnote().generate(SAMPLE)
        self.assertIn("breaking change", notes.highlights.lower())
        self.assertIn("feature", notes.highlights.lower())

    def test_empty_log_reports_no_changes(self):
        notes = Shipnote().generate("")
        self.assertEqual(notes.commit_count, 0)
        self.assertEqual(notes.highlights, "No changes.")

    def test_generate_is_deterministic(self):
        a = Shipnote().generate(SAMPLE, version="v2.0.0").markdown()
        b = Shipnote().generate(SAMPLE, version="v2.0.0").markdown()
        self.assertEqual(a, b)

    def test_markdown_ends_with_single_newline(self):
        md = Shipnote().generate(SAMPLE, version="v2.0.0").markdown()
        self.assertTrue(md.endswith("\n"))
        self.assertFalse(md.endswith("\n\n"))

    def test_to_dict_keys(self):
        d = Shipnote().generate(SAMPLE, version="v2.0.0").to_dict()
        for key in (
            "version",
            "version_bump",
            "commit_count",
            "breaking",
            "sections",
            "backend",
        ):
            self.assertIn(key, d)


class StubBackendTests(unittest.TestCase):
    def test_is_a_backend(self):
        from shipnote import Backend

        self.assertIsInstance(StubBackend(), Backend)

    def test_summarize_empty_is_no_changes(self):
        self.assertEqual(StubBackend().summarize({}, breaking=[]), "No changes.")

    def test_summarize_ends_with_period(self):
        grouped = group_commits(parse_commits("feat: a\nfeat: b"))
        out = StubBackend().summarize(grouped, breaking=[])
        self.assertEqual(out, "2 features.")
        self.assertTrue(out.endswith("."))

    def test_summarize_leads_with_breaking_count(self):
        breaking = parse_commits("feat!: drop v1")
        out = StubBackend().summarize({}, breaking=breaking)
        self.assertEqual(out, "1 breaking change.")


if __name__ == "__main__":
    unittest.main()
