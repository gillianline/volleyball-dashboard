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

# --- GLOBAL VARIABLES ---
all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']

# --- CSS: FORMATTING & HIGHLIGHTING ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    .viewerBadge_link__1S137, .main_heading_anchor__m6v0K, a.header-anchor { display: none !important; }
    header a { display: none !important; }
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #4895DB; color: white; padding: 6px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 11px; text-transform: uppercase; }
    .scout-table td { padding: 6px; border-bottom: 1px solid #F5F5F7; font-size: 11px; }
    .bg-highlight-red { background-color: #ffcccc !important; font-weight: 900; }
    .arrow-red { color: #b30000 !important; font-weight: 900; margin-left: 4px; }
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    .score-box { padding: 12px 20px; border-radius: 12px; font-size: 28px; font-weight: 800; min-width: 100px; color: #FFFFFF; line-height: 1.2; text-align: center;}
    .gallery-card { border: 1px solid #E5E5E7; padding: 0; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 30px; overflow: hidden; }
    .gallery-photo { border-radius: 50%; width: 80px; height: 80px; object-fit: cover; border: 3px solid #FF8200; }
    .section-header { font-size: 14px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    .info-box { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 12px; margin-top: 10px; font-size: 12px; color: #1D1D1F; font-weight: 600; line-height: 1.4; }
    .js-plotly-plot { pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_flipped_gradient(score):
    score = float(score)
    if score <= 40: return "#2D5A27"
    if score <= 70: return "#D4A017"
    return "#A52A2A"

# --- DATA LOADING ---
@st.cache_data(ttl=0)
def load_all_data():
    def get_fresh_url(url): return f"{url}&cachebust={int(time.time())}"
    df = pd.read_csv(get_fresh_url(st.secrets["GOOGLE_SHEET_URL"]))
    df['Sheet_Order'] = range(len(df))
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date']) 
    if 'Week' in df.columns:
        df['Week'] = pd.to_numeric(df['Week'].astype(str).str.extract('(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    rename_map = {
        'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps', 'IMA Jump Count High Band': 'High Jumps', 
        'BMP Jumping Load': 'Jump Load', 'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance', 
        'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movement'
    }
    df = df.rename(columns=rename_map)
    df['Session_Type'] = df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
    avail = [v for v in rename_map.values() if v in df.columns]
    for col in avail: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).round(1)
    df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    cmj_df = pd.read_csv(get_fresh_url(st.secrets["CMJ_SHEET_URL"]))
    cmj_df.columns = cmj_df.columns.str.strip()
    cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
    phase_df = pd.read_csv(get_fresh_url(st.secrets["PHASES_SHEET_URL"]))
    phase_df.columns = phase_df.columns.str.strip()
    if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
    phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
    phase_df = phase_df.rename(columns=rename_map)
    return df, cmj_df, phase_df

try:
    df, cmj_df, phase_df = load_all_data()
    LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}
    
    st.markdown("""
        <div style="text-align: center; margin-top: 10px; margin-bottom: 15px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120">
            <div style='color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;'>LADY VOLS VOLLEYBALL PERFORMANCE</div>
        </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["Individual Profile", "Team Gallery", "Game v. Practice", "Position Analysis", "Tournament Summary"])
    session_list = df[['Date', 'Sheet_Order', 'Session_Name']].drop_duplicates(subset=['Session_Name']).sort_values(['Date', 'Sheet_Order'], ascending=[False, False])['Session_Name'].tolist()

    # --- TAB 0, 1, 2, 3 ---
    # Logic remains as previously established...

    # --- TAB 4: TOURNAMENT SUMMARY ---
    with tabs[4]:
        st.markdown('<div class="section-header">Weekend Tournament Overview</div>', unsafe_allow_html=True)
        
        with st.container():
            c_ts1, c_ts2 = st.columns([2, 1])
            with c_ts1:
                game_list_t = df[df['Session_Type'] == 'Game'].sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique()
                selected_games = st.multiselect("Select Tournament Matches", game_list_t, default=game_list_t[-3:] if len(game_list_t) >=3 else game_list_t, key="tourney_multi")
            with c_ts2:
                pos_filter_t = st.selectbox("Filter by Position", ["All Positions"] + sorted(list(df['Position'].unique())), key="tourney_pos_filter")

        if selected_games:
            st.markdown('<div class="section-header">Athlete Match-by-Match Performance</div>', unsafe_allow_html=True)
            tourney_df = df[df['Session_Name'].isin(selected_games)].sort_values(['Date', 'Sheet_Order'])
            if pos_filter_t != "All Positions":
                tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]
                
            athletes_t = sorted(tourney_df['Name'].unique())
            t_metrics = ['Total Jumps', 'Player Load', 'Estimated Distance', 'Explosive Efforts']

            for i in range(0, len(athletes_t), 2):
                card_cols = st.columns(2)
                for j in range(2):
                    if i + j < len(athletes_t):
                        ath_name_t = athletes_t[i+j]
                        ath_data_t = tourney_df[tourney_df['Name'] == ath_name_t]
                        with card_cols[j]:
                            # 1. Header and Table Area
                            card_html = f"""
                            <div class="gallery-card">
                                <div style="display:flex; align-items:center; gap:15px; padding:15px; background:#f8f9fa; border-bottom:2px solid #FF8200;">
                                    <img src="{ath_data_t['PhotoURL'].iloc[0]}" class="gallery-photo">
                                    <div>
                                        <p style="margin:0; font-weight:900; color:#1D1D1F; font-size:18px;">{ath_name_t}</p>
                                        <p style="margin:0; color:#4895DB; font-weight:700; font-size:12px;">{ath_data_t['Position'].iloc[0]}</p>
                                    </div>
                                </div>
                                <div style="padding:10px 15px 0 15px;">
                                    <table class="scout-table" style="margin-bottom:0;">
                                        <thead><tr><th>Match</th><th>Total Jumps</th><th>Player Load</th><th>Estimated Distance</th><th>Explosive Efforts</th></tr></thead>
                                        <tbody>
                            """
                            for _, r in ath_data_t.iterrows():
                                card_html += f"<tr><td style='font-weight:700;'>{r['Session_Name']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.0f}</td><td>{r['Estimated Distance']:.0f}</td><td>{r['Explosive Efforts']:.0f}</td></tr>"
                            card_html += f"<tr style='background:#4895DB; color:white; font-weight:900;'><td>TOTAL</td><td>{int(ath_data_t['Total Jumps'].sum())}</td><td>{ath_data_t['Player Load'].sum():.0f}</td><td>{ath_data_t['Estimated Distance'].sum():.0f}</td><td>{ath_data_t['Explosive Efforts'].sum():.0f}</td></tr></tbody></table></div>"
                            st.markdown(card_html, unsafe_allow_html=True)
                            
                            # 2. Visual Area (Immediately following table)
                            fig_ath_bars = go.Figure()
                            for idx, r in ath_data_t.iterrows():
                                # Lady Vol Orange and Neutral Grey
                                colors = ['#FF8200', '#515154', '#4895DB']
                                fig_ath_bars.add_trace(go.Bar(
                                    name=r['Session_Name'], 
                                    x=t_metrics, 
                                    y=[r[m] for m in t_metrics],
                                    marker_color=colors[idx % len(colors)]
                                ))
                            
                            fig_ath_bars.update_layout(
                                barmode='group', 
                                height=280, 
                                margin=dict(l=40,r=40,t=10,b=20), 
                                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5), 
                                template="simple_white",
                                yaxis=dict(gridcolor='#F5F5F7')
                            )
                            st.plotly_chart(fig_ath_bars, use_container_width=True, config=LOCKED_CONFIG)
                            st.markdown("</div>", unsafe_allow_html=True)

            st.write("<br><br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">Team Tournament Averages</div>', unsafe_allow_html=True)
            team_avg_t = df[df['Session_Name'].isin(selected_games)].groupby(['Session_Name', 'Sheet_Order'])[t_metrics].mean().reset_index().sort_values('Sheet_Order')
            
            row1_c1, row1_c2 = st.columns(2)
            row2_c1, row2_c2 = st.columns(2)
            grid_locs = [row1_c1, row1_c2, row2_c1, row2_c2]
            
            for idx, m in enumerate(t_metrics):
                with grid_locs[idx]:
                    fig_t = px.bar(team_avg_t, x='Session_Name', y=m, color='Session_Name', 
                                 title=f"Team Average: {m}", color_discrete_sequence=['#FF8200', '#4895DB', '#515154'])
                    fig_t.update_layout(
                        showlegend=False, 
                        height=400, 
                        margin=dict(l=60, r=40, t=60, b=100), 
                        xaxis_title=None, 
                        template="simple_white",
                        yaxis=dict(title=m)
                    )
                    st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)

except Exception as e:
    st.error(f"Sync Error: {e}")
