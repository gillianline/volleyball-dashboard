import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

# --- CSS STYLES ---
st.markdown("""
    <style>
    th, td {text-align: center !important;}
    .scout-table { width: 100%; border-collapse: collapse; }
    .section-header { font-size: 20px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 15px; margin-bottom: 10px; }
    .score-box { padding: 10px; border-radius: 8px; font-size: 20px; font-weight: 800; color: #FFFFFF; text-align: center; }
    @media print {
        [data-testid="stSidebar"], [data-testid="stHeader"] { display: none !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- PASSWORD GATE ---
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        pwd = st.text_input("Enter Password", type="password")
        if pwd == st.secrets.get("PASSWORD"):
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if check_password():
    @st.cache_data(ttl=60)
    def load_all_data():
        def heavy_sanitize(df):
            # Clean columns and force types
            df.columns = df.columns.str.strip()
            return df

        df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
        match_df = pd.read_csv(st.secrets["MATCHES_SHEET_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
        phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
        ash_df = pd.read_csv(st.secrets["ASH_SHEET_URL"])
        er_df = pd.read_csv(st.secrets["ER_SHEET_URL"])

        # Fix date parsing warnings by using format='mixed'
        for f in [df, match_df, cmj_df, phase_df, ash_df, er_df]:
            if 'Date' in f.columns: f['Date'] = pd.to_datetime(f['Date'], errors='coerce', format='mixed')
            if 'Test Date' in f.columns: f['Test Date'] = pd.to_datetime(f['Test Date'], errors='coerce', format='mixed')
            
        return df, match_df, cmj_df, phase_df, ash_df, er_df

    raw_df, match_df, cmj_df, phase_df, ash_df, er_df = load_all_data()

    # Define tabs once
    tab_list = ["Profile", "Scores", "Combined", "Spring/Daily", "History", "Match/Prac", "Summary", "Positions", "Phases", "Planner", "Spring v Summer"]
    tabs = st.tabs(tab_list)

    # EXAMPLE: Tab 0 (Individual Profile)
    with tabs[0]:
        with st.container():
            st.markdown('<div class="section-header">Individual Profile</div>', unsafe_allow_html=True)
            # All content for tab 0 goes here
            # REMEMBER: Replace use_container_width=True with width='stretch' in plots

    # EXAMPLE: Tab 6 (Match Summary - Your potential spillover point)
    with tabs[6]:
        with st.container():
            st.markdown('<div class="section-header">Match Summary</div>', unsafe_allow_html=True)
            # Use columns and containers instead of raw HTML divs
            c1, c2 = st.columns(2)
            with c1: st.write("Data")

