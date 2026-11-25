"""Session-scoped state. Records live only in the visitor's own session (no shared storage)."""
import streamlit as st

from . import risk
from .config import PRESETS


def init():
    ss = st.session_state
    ss.setdefault("records", [])
    ss.setdefault("current_id", None)
    ss.setdefault("seq", 0)
    ss.setdefault("query", PRESETS[1])


def next_id() -> str:
    st.session_state.seq += 1
    return risk.make_id(st.session_state.seq)


def add(rec: dict):
    st.session_state.records.append(rec)
    st.session_state.current_id = rec["id"]


def get(rec_id):
    return next((r for r in st.session_state.records if r["id"] == rec_id), None)


def current():
    return get(st.session_state.current_id)
