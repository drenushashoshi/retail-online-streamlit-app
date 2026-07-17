"""Shared look & feel — CSS + the slide accent colors.

Owner: P1 (Drenusha)

The three slide accents are the first three slots of a CVD-validated
categorical palette (worst adjacent DeltaE 24.2) — the same hues the slide
charts should use, so the whole app reads as one system:
  Business Pulse  -> blue   #2a78d6  (trend)
  Revenue Engines -> aqua   #1baf7a  (growth)
  Leaks           -> yellow #eda100  (caution)
"""
from __future__ import annotations

import streamlit as st

ACCENTS = {
    "pulse": "#2a78d6",
    "engines": "#1baf7a",
    "leaks": "#eda100",
}

_CSS = """
<style>
/* --- hero ------------------------------------------------------------- */
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1.12;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #2a78d6 0%, #4a3aa7 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.25rem;
}
.hero-sub {
    color: rgba(128, 128, 140, 0.95);
    font-size: 1.05rem;
    margin-bottom: 1.3rem;
    max-width: 44rem;
}

/* --- decision cards ----------------------------------------------------- */
.dec-card {
    border: 1px solid rgba(128, 128, 140, 0.22);
    border-top: 4px solid var(--accent, #2a78d6);
    border-radius: 14px;
    padding: 1.05rem 1.15rem 1.15rem;
    background: rgba(128, 128, 140, 0.04);
    height: 100%;
    min-height: 18rem;
}
.dec-emoji { font-size: 1.7rem; display: block; margin-bottom: 0.3rem; }
.dec-q     { font-weight: 700; font-size: 1.02rem; margin-bottom: 0.3rem; }
.dec-see   { font-size: 0.88rem; color: rgba(128, 128, 140, 0.95); margin-bottom: 0.65rem; }
.dec-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent, #2a78d6);
    margin-bottom: 0.1rem;
}
.dec-text  { font-size: 0.88rem; }

/* --- sidebar ------------------------------------------------------------ */
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    max-height: 100vh;
    overflow-x: hidden;
    overflow-y: auto;
    overscroll-behavior: contain;
    padding-bottom: 1.5rem;
}

/* Selectbox menus are rendered in a popover outside the sidebar, so they
   need their own scroll container when the country list is long. */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [data-baseweb="menu"] {
    max-height: min(60vh, 26rem) !important;
    overflow-y: auto !important;
    overscroll-behavior: contain;
}

.sb-brand {
    font-size: 1.3rem;
    font-weight: 800;
    letter-spacing: -0.01em;
    margin-bottom: 0.1rem;
}
.sb-file {
    font-size: 0.82rem;
    border: 1px solid rgba(42, 120, 214, 0.35);
    border-radius: 10px;
    padding: 0.55rem 0.7rem;
    background: rgba(42, 120, 214, 0.08);
    word-break: break-all;
}

/* --- slide pages ---------------------------------------------------------- */
.decision-chip {
    display: inline-block;
    padding: 0.28rem 0.8rem;
    border-radius: 999px;
    border: 1px solid var(--accent, #2a78d6);
    color: var(--accent, #2a78d6);
    font-size: 0.85rem;
    font-weight: 600;
    margin: 0.15rem 0 0.9rem;
}
.ph-card {
    border: 1.5px dashed rgba(128, 128, 140, 0.35);
    border-radius: 16px;
    padding: 2.6rem 2rem;
    text-align: center;
    margin-top: 0.6rem;
}
.ph-emoji { font-size: 2.5rem; }
.ph-title { font-weight: 700; font-size: 1.15rem; margin: 0.5rem 0 0.35rem; }
.ph-text  { color: rgba(128, 128, 140, 0.95); max-width: 36rem; margin: 0 auto; }
.owner-chip {
    display: inline-block;
    margin-top: 0.9rem;
    padding: 0.18rem 0.7rem;
    border-radius: 999px;
    background: rgba(128, 128, 140, 0.12);
    color: rgba(128, 128, 140, 1);
    font-size: 0.8rem;
    font-weight: 600;
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
