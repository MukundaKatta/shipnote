# shipnote 📝

Turn raw git commits into clean, grouped **release notes** with a suggested
**SemVer bump** — in one command, with no API key. `shipnote` understands
Conventional Commits, never drops a commit it doesn't recognize, and ships a
keyless deterministic backend so it runs anywhere. Plug in an LLM only when you
want prose highlights.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-blueviolet.svg)](tests/)

---

## Why

Writing release notes by hand is the chore everyone skips, so changelogs rot.
The information is already in your commit messages — `shipnote` just shapes it:

- **Groups** commits into Features / Fixes / Performance / Docs / … by type.
- **Flags breaking changes** from `!` or a `BREAKING CHANGE` note.
- **Suggests the SemVer bump**: breaking → major, a feature → minor, else patch.
- **Loses nothing.** Non-conventional commits land in an "Other" section instead
  of vanishing.
- **Runs offline.** The default backend is deterministic and keyless; the LLM
  backends are optional and only add a prose summary line.

## Quickstart (no API key)

```bash
pip install -e .
python examples/demo.py
```

```python
from shipnote import Shipnote

log = """\
a1b2c3d feat(api): add pagination
b2c3d4e fix(auth): reject expired tokens
c3d4e5f feat!: drop v1 config
"""

notes = Shipnote().generate(log, version="v2.0.0")
print(notes.version_bump)   # major  (because of the breaking change)
print(notes.markdown())
```

```markdown
## v2.0.0

1 breaking change, 2 features, 1 fix.

### ⚠ BREAKING CHANGES
- drop v1 config (c3d4e5f)

### Features
- **api:** add pagination (a1b2c3d)

### Fixes
- **auth:** reject expired tokens (b2c3d4e)
```

## Straight from a repo

```python
from shipnote import Shipnote
from shipnote.gitlog import read_commits

notes = Shipnote().generate(read_commits("v1.0.0..HEAD"))
print(notes.markdown())
```

`read_commits` shells out to `git log` (standard library only — no GitPython).

## LLM highlights (optional)

All optional and lazily imported — the core install pulls **zero** vendor deps.

| Backend            | Install        | Needs                 |
| ------------------ | -------------- | --------------------- |
| `StubBackend`      | (built in)     | nothing — runs offline|
| `GeminiBackend`    | `.[gemini]`    | `GEMINI_API_KEY`      |
| `AnthropicBackend` | `.[anthropic]` | `ANTHROPIC_API_KEY`   |
| `OllamaBackend`    | `.[ollama]`    | a local Ollama server |

```python
from shipnote import Shipnote, GeminiBackend

notes = Shipnote(backend=GeminiBackend()).generate(log, version="v2.0.0")
```

The grouping, breaking-change detection, and SemVer bump are always
deterministic; only the one-line highlights change when you plug in an LLM.

## Dashboard

```bash
pip install -e ".[dashboard]"
streamlit run app.py
```

Paste a commit log, get rendered release notes and a copy-ready markdown block.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Runs fully offline against the stub backend.

## License

MIT — see [LICENSE](LICENSE).
