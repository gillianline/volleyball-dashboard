import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
import time
from datetime import timedelta

# --- PAGE CONFIG & CSS (NO CHANGES) ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

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
    .gallery-card { border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; min-height: 250px; display: flex; flex-direction: column; justify-content: center; }
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

# --- DATA LOADING (CACHING TTL=0 FOR LIVE UPDATES) ---
@st.cache_data(ttl=0)
def load_all_data():
    def get_fresh_url(url): return f"{url}&cachebust={int(time.time())}"
    df = pd.read_csv(get_fresh_url(st.secrets["GOOGLE_SHEET_URL"]))
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date']) 
    if 'Week' in df.columns:
        df['Week'] = pd.to_numeric(df['Week'].astype(str).str.extract('(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    rename_map = {
        'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps', 'IMA Jump Count High Band': 'High Jumps', 
        'BMP Jumping Load': 'Jump Load', 'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance (y)', 
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
    
    tabs = st.tabs(["Individual Profile", "Team Gallery", "Game v. Practice", "Position Analysis", "Tournament Summary"])
    session_list = df[['Date', 'Session_Name']].drop_duplicates().sort_values('Date', ascending=False)['Session_Name'].tolist()

    # [TAB 0, 1, 2, 3 LOGIC REMAINS UNCHANGED]
    # ... (Keeping your existing code here)

    # --- TAB 4: TOURNAMENT SUMMARY (MATCH COMPARISON & PLAYER CARDS) ---
    with tabs[4]:
        st.markdown('<div class="section-header">Weekend Tournament Overview</div>', unsafe_allow_html=True)
        game_list = sorted(df[df['Session_Type'] == 'Game']['Session_Name'].unique())
        selected_games = st.multiselect("Select Tournament Matches", game_list, default=game_list[-3:] if len(game_list) >=3 else game_list, key="tourney_multi")
        
        if selected_games:
            tourney_df = df[df['Session_Name'].isin(selected_games)].copy()
            comp_metrics = ['Total Jumps', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts']
            team_avg = tourney_df.groupby('Session_Name')[comp_metrics].mean().reset_index()
            
            # 1. Metric Grid (All metrics at once)
            m_cols = st.columns(4)
            for i, metric in enumerate(comp_metrics):
                with m_cols[i]:
                    fig = px.bar(team_avg, x='Session_Name', y=metric, color='Session_Name', 
                                 color_discrete_sequence=['#4895DB', '#FF8200', '#515154'])
                    fig.update_layout(showlegend=False, height=250, margin=dict(l=10, r=10, t=30, b=10), xaxis_title=None)
                    st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG)

            # 2. Athlete Tournament Cards
            st.markdown('<div class="section-header">Athlete Tournament Performance Cards</div>', unsafe_allow_html=True)
            
            # Filter by position in the tournament tab too
            pos_filter = st.selectbox("Filter Cards by Position", ["All"] + sorted(list(tourney_df['Position'].unique())), key="tourney_pos")
            display_df = tourney_df if pos_filter == "All" else tourney_df[tourney_df['Position'] == pos_filter]
            
            athletes = sorted(display_df['Name'].unique())
            
            # Grid of cards (3 per row)
            for i in range(0, len(athletes), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(athletes):
                        ath_name = athletes[i+j]
                        ath_data = display_df[display_df['Name'] == ath_name].sort_values('Date')
                        
                        # Calculate Tournament Totals/Maxes
                        t_jumps = ath_data['Total Jumps'].sum()
                        t_load = ath_data['Player Load'].sum()
                        t_dist = ath_data['Estimated Distance (y)'].sum()
                        
                        with cols[j]:
                            # Mini Sparkline for Load Trend
                            fig_spark = go.Figure()
                            fig_spark.add_trace(go.Scatter(x=ath_data['Session_Name'], y=ath_data['Player Load'], 
                                                         line=dict(color='#FF8200', width=3), fill='tozeroy'))
                            fig_spark.update_layout(height=80, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            
                            st.markdown(f"""
                            <div class="gallery-card">
                                <div style="display:flex; align-items:center; gap:15px; margin-bottom:10px;">
                                    <img src="{ath_data['PhotoURL'].iloc[0]}" class="gallery-photo">
                                    <div>
                                        <p style="margin:0; font-weight:900; color:#1D1D1F; font-size:16px;">{ath_name}</p>
                                        <p style="margin:0; color:#4895DB; font-weight:700; font-size:12px;">{ath_data['Position'].iloc[0]}</p>
                                    </div>
                                </div>
                                <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; text-align:center; gap:5px; background:#f8f9fa; border-radius:8px; padding:10px; margin-bottom:10px;">
                                    <div><p style="margin:0; font-size:10px; color:#515154;">TOTAL JUMPS</p><p style="margin:0; font-weight:800; color:#FF8200;">{int(t_jumps)}</p></div>
                                    <div><p style="margin:0; font-size:10px; color:#515154;">TOTAL LOAD</p><p style="margin:0; font-weight:800; color:#FF8200;">{int(t_load)}</p></div>
                                    <div><p style="margin:0; font-size:10px; color:#515154;">TOTAL DIST</p><p style="margin:0; font-weight:800; color:#FF8200;">{int(t_dist)}</p></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            st.plotly_chart(fig_spark, use_container_width=True, config=LOCKED_CONFIG)

except Exception as e:
    st.error(f"Sync Error: {e}")
