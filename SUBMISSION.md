# shipnote — submission copy

**Repo:** https://github.com/MukundaKatta/shipnote

**Target events:** MPC Hacks, HackPrix Season 3, Band Hackathon

**Tagline:** Turn raw git commits into clean release notes and a SemVer bump, in one command.

## Short description

Reads your commit log, understands Conventional Commits, groups changes into
Features / Fixes / Performance, flags breaking changes, and suggests whether the
next release is major, minor, or patch. Runs fully offline with no API key.

## Inspiration

Writing release notes by hand is the chore everyone skips, so changelogs rot.
But the information is already sitting in your commit messages.

## What it does

Reads your commit log, groups changes by Conventional-Commit type, flags
breaking changes, and suggests the SemVer bump. Anything it doesn't recognize
lands in an Other section instead of vanishing. Runs fully offline with no key.
Optional LLM backends add a one-line prose highlight.

## How we built it

A regex Conventional-Commits parser, deterministic grouping and bump logic, a
label helper for correct plurals, a keyless stub backend plus lazy
Gemini/Anthropic/Ollama, a Streamlit dashboard, and a stdlib-only git-log
reader.

## Challenges we ran into

Irregular English plurals broke a naive singularizer, so "fixes" came out as
"fixe". We replaced it with an explicit singular/plural map. The other rule was
keeping the bump and grouping fully deterministic so they never depend on a
model.

## Accomplishments we're proud of

Zero core dependencies, a test suite that runs completely offline, and it never
drops a commit.

## What we learned

Keep the deterministic spine separate from the optional LLM flourish. The useful
part should work with no key.

## What's next

Read git tags to auto-pick the next version, a GitHub Action wrapper, and
grouped multi-release changelogs.

## Tech tags

python, git, conventional-commits, semver, changelog, release-notes, cli,
streamlit, gemini, anthropic, ollama, mit
