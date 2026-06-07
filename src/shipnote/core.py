"""shipnote core: turn raw git commits into grouped, human-readable release
notes with a suggested SemVer bump.

    from shipnote import Shipnote

    notes = Shipnote().generate(commit_log)
    print(notes.markdown())
    print("suggested bump:", notes.version_bump)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .backends import Backend, StubBackend
from .parse import (
    Commit,
    TYPE_TITLES,
    group_commits,
    parse_commits,
    suggest_bump,
)


@dataclass
class ReleaseNotes:
    version: str
    version_bump: str
    sections: dict[str, list[Commit]]
    breaking: list[Commit]
    highlights: str
    commit_count: int
    backend: str

    def markdown(self) -> str:
        out: list[str] = [f"## {self.version}", ""]
        if self.highlights:
            out += [self.highlights, ""]
        if self.breaking:
            out.append("### ⚠ BREAKING CHANGES")
            out += [f"- {_line(c)}" for c in self.breaking]
            out.append("")
        for section, commits in self.sections.items():
            out.append(f"### {TYPE_TITLES.get(section, section.title())}")
            out += [f"- {_line(c)}" for c in commits]
            out.append("")
        return "\n".join(out).rstrip() + "\n"

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "version_bump": self.version_bump,
            "commit_count": self.commit_count,
            "breaking": len(self.breaking),
            "sections": {k: len(v) for k, v in self.sections.items()},
            "backend": self.backend,
        }


def _line(commit: Commit) -> str:
    scope = f"**{commit.scope}:** " if commit.scope else ""
    short = f" ({commit.hash[:7]})" if commit.hash else ""
    return f"{scope}{commit.subject}{short}"


@dataclass
class Shipnote:
    """Configure once, reuse. Defaults to the keyless StubBackend so the whole
    pipeline runs offline."""

    backend: Backend = field(default_factory=StubBackend)

    def generate(
        self, commits_text: str, *, version: str | None = None
    ) -> ReleaseNotes:
        commits = parse_commits(commits_text)
        sections = group_commits(commits)
        breaking = [c for c in commits if c.breaking]
        bump = suggest_bump(commits)
        highlights = self.backend.summarize(sections, breaking=breaking)

        return ReleaseNotes(
            version=version or f"({bump} release)",
            version_bump=bump,
            sections=sections,
            breaking=breaking,
            highlights=highlights,
            commit_count=len(commits),
            backend=getattr(self.backend, "name", type(self.backend).__name__),
        )
