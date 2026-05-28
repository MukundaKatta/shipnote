"""shipnote dashboard — paste a commit log, get release notes.

    pip install -e ".[dashboard]"
    streamlit run app.py

Runs offline against the keyless stub backend by default.
"""

from __future__ import annotations

import streamlit as st

from shipnote import Shipnote

SAMPLE = """a1b2c3d feat(api): add pagination to list endpoints
b2c3d4e fix(auth): reject expired refresh tokens
c3d4e5f feat!: drop support for v1 config files
d4e5f6a perf(db): cache the schema lookup
e5f6a7b docs: rewrite the quickstart guide
f6a7b8c chore: bump dev dependencies"""

_BUMP_EMOJI = {"major": "🔴 major", "minor": "🟡 minor", "patch": "🟢 patch"}

st.set_page_config(page_title="shipnote", page_icon="📝", layout="wide")

st.title("📝 shipnote")
st.caption(
    "Turn raw git commits into grouped, human-readable release notes with a "
    "suggested SemVer bump. Understands Conventional Commits. No key, runs offline."
)

col_in, col_out = st.columns(2)

with col_in:
    version = st.text_input("Version label (optional)", value="v2.0.0")
    log = st.text_area(
        "Commit log (one `hash subject` line per commit)",
        value=SAMPLE,
        height=320,
        help="Tip: paste the output of `git log --pretty='%h %s'`.",
    )
    go = st.button("Generate release notes", type="primary")

with col_out:
    if go:
        if not log.strip():
            st.warning("Paste a commit log first.")
            st.stop()

        notes = Shipnote().generate(log, version=version or None)

        c1, c2, c3 = st.columns(3)
        c1.metric("Commits", notes.commit_count)
        c2.metric("Bump", _BUMP_EMOJI.get(notes.version_bump, notes.version_bump))
        c3.metric("Breaking", len(notes.breaking))

        st.markdown(notes.markdown())

        with st.expander("Copy raw markdown"):
            st.code(notes.markdown(), language="markdown")
