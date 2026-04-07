import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
import time
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

# --- CSS: EXACT RESTORATION OF ORIGINAL THEME ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; }
    .scout-table th { background-color: #4895DB; color: white; padding: 8px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 12px; text-transform: uppercase; }
    .scout-table td { padding: 10px; border-bottom: 1px solid #F5F5F7; font-size: 13px; font-weight: 500; }
    .growth-pos { color: #28a745; font-weight: 900; }
    .growth-neg { color: #dc3545; font-weight: 900; }
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; margin-bottom: 10px; }
    .section-header { font-size: 16px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    .score-box { padding: 15px; border-radius: 12px; font-size: 32px; font-weight: 900; color: #FFFFFF; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=0)
def load_all_data():
    def get_fresh_url(url): return f"{url}&cachebust={int(time.time())}"
    # Main Velocity Data
    df = pd.read_csv(get_fresh_url(st.secrets["GOOGLE_SHEET_URL"]))
    df['Sheet_Order'] = range(len(df))
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # CMJ Readiness
    cmj_df = pd.read_csv(get_fresh_url(st.secrets["CMJ_SHEET_URL"]))
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
    
    # Phases
    phase_df = pd.read_csv(get_fresh_url(st.secrets["PHASES_SHEET_URL"]))
    phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
    
    return df, cmj_df, phase_df

try:
    df, cmj_df, phase_df = load_all_data()
    LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

    tabs = st.tabs(["Individual Profile", "Team Gallery", "Game v. Practice", "Position Analysis", "Tournament Summary"])
    session_list = df.sort_values(['Date', 'Sheet_Order'], ascending=[False, False])['Activity'].unique().tolist()

    # --- TAB 0: INDIVIDUAL PROFILE (RESTORED VELOCITY LOGIC) ---
    with tabs[0]:
        c1, c2 = st.columns([1.5, 3.5])
        with c1:
            sel_p = st.selectbox("Select Athlete", sorted(df['Name'].unique()), key="ind_p")
            p_data = df[df['Name'] == sel_p].sort_values('Date')
            st.markdown(f'<center><img src="{p_data["PhotoURL"].iloc[0]}" class="player-photo-large"></center>', unsafe_allow_html=True)
            
            # Growth Logic
            initial = p_data['MaxSpeed'].iloc[0]
            top = p_data['MaxSpeed'].max()
            growth = top - initial
            st.markdown(f"""
                <div class="score-box" style="background-color:#FF8200;">
                    {top:.1f} <span style="font-size:14px;">MPH (MAX)</span>
                    <div style="font-size:16px;">Total Growth: {growth:+.2f}</div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="section-header">Velocity History & Growth</div>', unsafe_allow_html=True)
            fig_p = px.line(p_data, x='Date', y='MaxSpeed', markers=True)
            fig_p.update_traces(line_color='#FF8200', marker_size=10)
            st.plotly_chart(fig_p, use_container_width=True, config=LOCKED_CONFIG)
            
            # Phase Breakdown Table
            p_ph = phase_df[phase_df['Name'] == sel_p].sort_values('Date', ascending=False).head(5)
            st.markdown('<div class="section-header">Recent Practice Phase Breakdown</div>', unsafe_allow_html=True)
            st.table(p_ph[['Date', 'Phase', 'Total Jumps', 'Player Load']])

    # --- TAB 1: TEAM GALLERY (RESTORED SCOUT CARDS) ---
    with tabs[1]:
        st.markdown('<div class="section-header">Team Speed Gallery</div>', unsafe_allow_html=True)
        latest_date = df['Date'].max()
        gal_df = df[df['Date'] == latest_date]
        for i in range(0, len(gal_df), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(gal_df):
                    row = gal_df.iloc[i+j]
                    with cols[j]:
                        st.markdown(f"""
                        <div class="gallery-card" style="border: 1px solid #EEE; padding: 15px; border-radius: 15px; display: flex; align-items: center; gap: 20px;">
                            <img src="{row['PhotoURL']}" style="width:100px; border-radius:50%;">
                            <div>
                                <h4 style="margin:0;">{row['Name']}</h4>
                                <p style="color:#FF8200; font-weight:700;">{row['MaxSpeed']} MPH</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    # --- TAB 2: GAME V PRACTICE (RESTORED DUAL AXIS) ---
    with tabs[2]:
        st.markdown('<div class="section-header">Game vs Practice Intensity</div>', unsafe_allow_html=True)
        # Restore the original logic with Distance on Secondary Axis (Ghost/Print-Safe)
        c_p, c_g = st.columns(2)
        with c_p: sel_p_gv = st.selectbox("Athlete", sorted(df['Name'].unique()), key="gv_p")
        
        ath_gv = df[df['Name'] == sel_p_gv].sort_values('Date')
        fig_gv = make_subplots(specs=[[{"secondary_y": True}]])
        fig_gv.add_trace(go.Bar(x=ath_gv['Date'], y=ath_gv['Player Load'], name="Load", marker_color='#4895DB'), secondary_y=False)
        fig_gv.add_trace(go.Bar(x=ath_gv['Date'], y=ath_gv['Estimated Distance'], name="Distance", marker=dict(color='#FF8200', opacity=0.6, line=dict(color='#FF8200', width=1))), secondary_y=True)
        st.plotly_chart(fig_gv, use_container_width=True)

    # --- TAB 3: POSITION ANALYSIS (RESTORED TRENDS) ---
    with tabs[3]:
        st.markdown('<div class="section-header">Position Performance Trends</div>', unsafe_allow_html=True)
        pos_avg = df.groupby(['Date', 'Position'])['MaxSpeed'].mean().reset_index()
        fig_pos = px.line(pos_avg, x='Date', y='MaxSpeed', color='Position', color_discrete_sequence=['#FF8200', '#4895DB', '#515154'])
        st.plotly_chart(fig_pos, use_container_width=True)

    # --- TAB 4: TOURNAMENT SUMMARY (NEW 5TH TAB) ---
    with tabs[4]:
        st.markdown('<div class="section-header">Weekend Tournament Summary</div>', unsafe_allow_html=True)
        game_list = df[df['Session_Type'] == 'Game'].sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique()
        sel_games = st.multiselect("Select Games", game_list, default=game_list[-3:] if len(game_list) >= 3 else game_list)
        
        if sel_games:
            t_df = df[df['Session_Name'].isin(sel_games)].sort_values(['Date', 'Sheet_Order'])
            # Team Graphs in 2x2
            r1c1, r1c2 = st.columns(2); r2c1, r2c2 = st.columns(2)
            metrics = ['Total Jumps', 'Player Load', 'Estimated Distance', 'Explosive Efforts']
            for idx, m in enumerate(metrics):
                avg = t_df.groupby('Session_Name')[m].mean().reset_index()
                fig = px.bar(avg, x='Session_Name', y=m, color_discrete_sequence=['#FF8200'])
                fig.update_layout(bargap=0, height=300, margin=dict(l=50, r=20, t=30, b=50))
                [r1c1, r1c2, r2c1, r2c2][idx].plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
