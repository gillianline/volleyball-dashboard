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
    .gallery-card { border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; min-height: 380px; display: flex; flex-direction: column; justify-content: center; }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
    .section-header { font-size: 14px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    .info-box { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 12px; margin-top: 10px; font-size: 12px; color: #1D1D1F; font-weight: 600; line-height: 1.4; }
    .js-plotly-plot { pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=0) 
def load_all_data():
    def get_fresh_url(url):
        return f"{url}&cachebust={int(time.time())}"

    main_url = get_fresh_url(st.secrets["GOOGLE_SHEET_URL"])
    df = pd.read_csv(main_url)
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
    for col in avail:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).round(1)

    df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    
    cmj_url = get_fresh_url(st.secrets["CMJ_SHEET_URL"])
    cmj_df = pd.read_csv(cmj_url)
    cmj_df.columns = cmj_df.columns.str.strip()
    cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
    
    phase_url = get_fresh_url(st.secrets["PHASES_SHEET_URL"])
    phase_df = pd.read_csv(phase_url)
    phase_df.columns = phase_df.columns.str.strip()
    if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
    phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
    phase_df = phase_df.rename(columns=rename_map)
    
    return df, cmj_df, phase_df

LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

try:
    df, cmj_df, phase_df = load_all_data()
    
    if st.sidebar.button("🔄 Sync Live Data"):
        st.cache_data.clear()
        st.rerun()

    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
    
    tabs = st.tabs(["Individual Profile", "Team Gallery", "Game v. Practice", "Position Analysis"])
    session_list = df[['Date', 'Session_Name']].drop_duplicates().sort_values('Date', ascending=False)['Session_Name'].tolist()

    # --- TAB 0: INDIVIDUAL PROFILE ---
    with tabs[0]:
        c_f1, c_f2 = st.columns(2)
        with c_f1: selected_session = st.selectbox("Practice Selection", session_list, index=0, key="nav_sel_ind")
        with c_f2: pos_f = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_ind")
        day_df = df[df['Session_Name'] == selected_session].copy()
        if not day_df.empty:
            curr_date = day_df['Date'].iloc[0]
            if pos_f != "All Positions": day_df = day_df[day_df['Position'] == pos_f]
            sel_p = st.selectbox("Select Athlete", sorted(day_df['Name'].unique()))
            p = day_df[day_df['Name'] == sel_p].iloc[0]
            lb = df[(df['Name'] == sel_p) & (df['Date'] >= curr_date - timedelta(days=30)) & (df['Date'] <= curr_date)]
            
            # (Table and Gauge Score Logic)
            m_rows = ""; total_grade = 0; count = 0
            for k in all_metrics:
                if k in p:
                    val, mx, avg = p[k], lb[k].max(), lb[k].mean()
                    grade = math.ceil((val / mx) * 100) if mx > 0 else 0
                    total_grade += grade; count += 1
                    diff = (val - avg) / avg if avg != 0 else 0
                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                    arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                    m_rows += f"<tr><td>{k}</td><td {h_class}>{val} {arr_val}</td><td>{mx}</td><td>{grade}</td></tr>"
            
            # (Individual Profile UI)
            st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>{m_rows}</tbody></table>', unsafe_allow_html=True)

            # Readiness
            st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
            # (CMJ Logic)
            
            # Phase Breakdown
            p_phases = phase_df[(phase_df['Name'] == sel_p) & (phase_df['Date'] == curr_date)].copy()
            if not p_phases.empty:
                st.markdown('<div class="section-header">Practice Phase Breakdown</div>', unsafe_allow_html=True)
                fig_ph = make_subplots(specs=[[{"secondary_y": True}]])
                fig_ph.add_trace(go.Bar(x=p_phases['Phase'], y=p_phases['Total Jumps'], name="Jumps", marker_color='#FF8200'), secondary_y=False)
                fig_ph.add_trace(go.Scatter(x=p_phases['Phase'], y=p_phases['Player Load'], name="Load", line=dict(color='#4895DB', width=4)), secondary_y=False)
                st.plotly_chart(fig_ph, use_container_width=True, config=LOCKED_CONFIG)

    # --- TAB 1: TEAM GALLERY ---
    with tabs[1]:
        # (Team Gallery Logic)
        pass

    # --- TAB 2: GAME V PRACTICE ---
    with tabs[2]:
        # (Game v Practice Logic)
        pass

    # --- TAB 3: POSITION ANALYSIS (CUMULATIVE LOAD) ---
    with tabs[3]:
        st.markdown('<div class="section-header">Cumulative Seasonal Workload & Trends</div>', unsafe_allow_html=True)
        sel_p_pos = st.selectbox("Select Athlete for Volume Trend", sorted(df['Name'].unique()))
        p_pos = df[df['Name'] == sel_p_pos].iloc[0]
        pos_label = p_pos['Position']
        
        # Sort data by date to ensure the "running total" works correctly
        trend_df = df.sort_values(['Name', 'Date'])
        
        t_col1, t_col2, t_col3 = st.columns(3)
        # Use metrics that make sense to "Grow"
        volume_metrics = ["Total Jumps", "Player Load", "Estimated Distance (y)"]
        cols = [t_col1, t_col2, t_col3]
        
        for i, m in enumerate(volume_metrics):
            if m in df.columns:
                with cols[i]:
                    fig_v = go.Figure()
                    
                    # 1. INDIVIDUAL CUMULATIVE (Grows with every entry)
                    p_v = trend_df[trend_df['Name'] == sel_p_pos].copy()
                    p_v[f'Cum_{m}'] = p_v[m].cumsum()
                    
                    fig_v.add_trace(go.Scatter(
                        x=p_v['Date'], 
                        y=p_v[f'Cum_{m}'], 
                        name=f"{sel_p_pos} Total", 
                        line=dict(color='#0046ad', width=4), 
                        fill='tozeroy' # This creates the "continually growing" area look
                    ))
                    
                    # 2. POSITIONAL AVG CUMULATIVE (Context baseline)
                    pos_v = trend_df[trend_df['Position'] == pos_label].groupby('Date')[m].mean().reset_index()
                    pos_v[f'Cum_{m}'] = pos_v[m].cumsum()
                    
                    fig_v.add_trace(go.Scatter(
                        x=pos_v['Date'], 
                        y=pos_v[f'Cum_{m}'], 
                        name=f"{pos_label} Avg", 
                        line=dict(color='#ff7f0e', dash='dash')
                    ))
                    
                    fig_v.update_layout(
                        title=f"Seasonal {m} Volume", 
                        height=350, 
                        margin=dict(l=10, r=10, t=40, b=10), 
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_v, use_container_width=True, config=LOCKED_CONFIG)

except Exception as e:
    st.error(f"Sync Error: {e}")
