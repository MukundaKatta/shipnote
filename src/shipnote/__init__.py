"""shipnote — turn raw git commits into grouped, human-readable release notes
with a suggested SemVer bump. Runs offline with a keyless deterministic backend;
plug in an LLM for prose highlights."""

from __future__ import annotations

from .backends import (
    AnthropicBackend,
    Backend,
    GeminiBackend,
    OllamaBackend,
    StubBackend,
)
from .core import ReleaseNotes, Shipnote
from .parse import (
    Commit,
    group_commits,
    parse_commit,
    parse_commits,
    suggest_bump,
)

__version__ = "0.1.0"

__all__ = [
    "Shipnote",
    "ReleaseNotes",
    "Commit",
    "parse_commit",
    "parse_commits",
    "group_commits",
    "suggest_bump",
    "Backend",
    "StubBackend",
    "GeminiBackend",
    "AnthropicBackend",
    "OllamaBackend",
    "__version__",
]
