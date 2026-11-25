"""HazardLens entrypoint: page config, navigation and sidebar engine settings."""
import streamlit as st

from hazardlens import state, views
from hazardlens.config import DEPTH, LANGUAGES, MODELS, VERSION
from hazardlens.ui import styles

st.set_page_config(page_title="HazardLens · Visual Risk Assessment", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
styles.inject()
state.init()

pages = [
    st.Page(views.dashboard, title="Dashboard", icon=":material/dashboard:", default=True),
    st.Page(views.inspection, title="New inspection", icon=":material/photo_camera:", url_path="inspection"),
    st.Page(views.register, title="Inspection register", icon=":material/fact_check:", url_path="register"),
    st.Page(views.methodology, title="Methodology", icon=":material/menu_book:", url_path="methodology"),
]
nav = st.navigation(pages)

# Always-visible top navigation (works even if the sidebar is collapsed)
_cols = st.columns(len(pages))
for _col, _pg in zip(_cols, pages):
    with _col:
        st.page_link(_pg)

with st.sidebar:
    st.divider()
    st.caption("ENGINE SETTINGS")
    st.selectbox("Vision engine", list(MODELS), key="engine")
    st.selectbox("Report language", list(LANGUAGES), key="lang")
    st.selectbox("Analysis depth", list(DEPTH), key="depth")
    st.markdown(
        f'<div class="side-note"><b>HazardLens v{VERSION}</b><br>Records stay in this browser session only. '
        f'Automatic model fallback is enabled.</div>', unsafe_allow_html=True)
    if st.session_state.records and st.button("Clear session records", key="clear_all"):
        st.session_state.records = []
        st.session_state.current_id = None
        st.rerun()

nav.run()
