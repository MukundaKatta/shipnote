"""Highlight backends. A backend turns grouped commits into a short "what
changed" blurb that leads the release notes.

`StubBackend` is deterministic and dependency-free: it writes a one-line count
summary, so the demo and tests run with no API key. The LLM backends
(`GeminiBackend`, `AnthropicBackend`, `OllamaBackend`) are thin and import their
SDK lazily, so installing shipnote core never pulls a vendor dependency.

Every backend implements one method:

    summarize(grouped, *, breaking) -> str
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .parse import Commit, TYPE_TITLES, count_label


@runtime_checkable
class Backend(Protocol):
    name: str

    def summarize(self, grouped: dict[str, list[Commit]], *, breaking: list[Commit]) -> str: ...


class StubBackend:
    """Deterministic highlight writer. No network, no key.

    Produces a factual one-liner like "3 features, 1 fix, 1 breaking change".
    Swap in an LLM backend for a prose summary.
    """

    name = "stub"

    def summarize(self, grouped: dict[str, list[Commit]], *, breaking: list[Commit]) -> str:
        parts: list[str] = []
        if breaking:
            n = len(breaking)
            parts.append(f"{n} breaking change{'s' if n != 1 else ''}")
        for section, commits in grouped.items():
            parts.append(count_label(section, len(commits)))
        if not parts:
            return "No changes."
        return ", ".join(parts).capitalize() + "."


def _build_prompt(grouped: dict[str, list[Commit]], breaking: list[Commit]) -> str:
    lines = ["Summarize this release in 2-3 short sentences for end users.",
             "Lead with the most important change. Plain language, no jargon.", ""]
    if breaking:
        lines.append("BREAKING CHANGES:")
        lines += [f"- {c.subject}" for c in breaking]
        lines.append("")
    for section, commits in grouped.items():
        lines.append(f"{TYPE_TITLES.get(section, section)}:")
        lines += [f"- {c.subject}" for c in commits]
        lines.append("")
    lines.append("Return only the summary.")
    return "\n".join(lines)


class GeminiBackend:
    """Google Gemini backend. Requires `google-genai` and GEMINI_API_KEY."""

    name = "gemini"

    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None):
        from google import genai  # lazy import

        import os

        self._client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY"])
        self._model = model

    def summarize(self, grouped: dict[str, list[Commit]], *, breaking: list[Commit]) -> str:
        prompt = _build_prompt(grouped, breaking)
        resp = self._client.models.generate_content(model=self._model, contents=prompt)
        return (resp.text or "").strip()


class AnthropicBackend:
    """Anthropic Claude backend. Requires `anthropic` and ANTHROPIC_API_KEY."""

    name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None):
        import anthropic  # lazy import

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def summarize(self, grouped: dict[str, list[Commit]], *, breaking: list[Commit]) -> str:
        prompt = _build_prompt(grouped, breaking)
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if block.type == "text").strip()


class OllamaBackend:
    """Local Ollama backend. Requires a running ollama server. No key."""

    name = "ollama"

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        self._model = model
        self._host = host.rstrip("/")

    def summarize(self, grouped: dict[str, list[Commit]], *, breaking: list[Commit]) -> str:
        import httpx  # lazy import

        prompt = _build_prompt(grouped, breaking)
        resp = httpx.post(
            f"{self._host}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
