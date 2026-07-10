"""Automated sales report — Team Squirtle.

app.py only orchestrates; the logic lives in pipeline/ and slides/.
Assembled together in the integration session (Wednesday ~16:00).
"""
import streamlit as st

st.set_page_config(
    page_title="Sales Report — Squirtle",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Automated Monthly Sales Report")
st.caption("Team Squirtle · Dataset: Online Retail II")
st.info("Skeleton — the P1-P5 sections get wired up here in the integration session.")
