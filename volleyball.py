import math
import re
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components

# --- 1. PAGE CONFIG & SYSTEM GLOBAL CSS ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

st.markdown("""
    <style>
    th, td {text-align: center !important;}
    [data-testid="stMetricValue"] {font-size: 24px;}
    
    @media print {
        [data-testid="stSidebar"], [data-testid="stHeader"] {
            display: none !important;
        }
        .main .block-container {
            padding: 1rem !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        body {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
    }
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    
    /* Global Container Padding */
    .block-container { 
        padding-top: 5rem !important; 
        padding-bottom: 3rem !important; 
    }
    
    .viewerBadge_link__1S137, .main_heading_anchor__m6v0K, a.header-anchor { display: none !important; }
    header a { display: none !important; }
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #4895DB; color: white; padding: 6px 4px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 11px; text-transform: uppercase; }
    .scout-table td { padding: 6px 4px; border-bottom: 1px solid #F5F5F7; font-size: 11px; color: #1D1D1F; }
    .bg-highlight-red { background-color: #ffcccc !important; font-weight: 900; }
    .arrow-red { color: #b30000 !important; font-weight: 900; margin-left: 4px; }
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: contain; border: 6px solid #FF8200; }
    .score-box { padding: 12px 20px; border-radius: 12px; font-size: 28px; font-weight: 800; min-width: 100px; color: #FFFFFF; line-height: 1.2; text-align: center;}
    .info-box { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 12px; margin-top: 10px; font-size: 12px; color: #1D1D1F; font-weight: 600; line-height: 1.4; }
    
    .player-row-container { 
        break-inside: avoid !important; 
        page-break-inside: avoid !important; 
        display: block !important; 
        margin-bottom: 30px; 
    }
    
    .player-divider { border: 0; height: 1px; background: #E5E5E7; margin-bottom: 15px; width: 100%; }
    .gallery-photo { 
        border-radius: 50%; 
        width: 110px; 
        height: 110px; 
        object-fit: contain; 
        border: 4px solid #FF8200; 
        padding: 4px; 
        box-sizing: border-box; 
        background-color: #FFFFFF; 
    }
    .section-header { font-size: 20px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 15px; margin-bottom: 10px; padding-bottom: 5px; text-transform: uppercase; }

    /* --- COMPLIANCE CARD UI CSS --- */
    .comp-athlete-header {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        background-color: #FFFFFF;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .comp-athlete-photo {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        border: 3px solid #FF8200;
        object-fit: cover;
    }
    .comp-card-outer {
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px;
        background-color: #FFFFFF;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .comp-card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .comp-card-title {
        font-size: 18px;
        font-weight: 800;
        color: #111827;
    }
    .comp-pill-badge {
        background-color: #FCE8E6;
        color: #D93025;
        font-size: 12px;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 16px;
    }
    .comp-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
    }
    .comp-tile {
        background-color: #F8FAFC;
        border: 1px solid #F1F5F9;
        border-radius: 10px;
        padding: 14px 10px;
        text-align: center;
    }
    .comp-label {
        font-size: 10px;
        font-weight: 800;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 6px;
    }
    .comp-metric-val {
        font-size: 22px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
    .comp-metric-orange {
        color: #FF8200 !important;
    }
    .comp-subtext {
        font-size: 11px;
        color: #94A3B8;
        margin-top: 6px;
        font-weight: 500;
    }

    @media print {
        .main-logo-container { display: block !important; margin-bottom: 0 !important; }
        .stTabs [role="tablist"], [data-testid="stSidebar"], header, footer, button, .stButton { display: none !important; }
        .main .block-container { padding: 0 !important; max-width: 100% !important; }
        .scout-table td, p, span, div { color: #000000 !important; }
    }
    </style>
    """, unsafe_allow_html=True)


# --- 2. PASSWORD & UTILITY FUNCTIONS ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("Incorrect Password")
        return False
    else:
        return True

def get_flipped_gradient(score):
    try:
        score = float(score)
        if pd.isna(score): return "#808080" 
    except (ValueError, TypeError):
        return "#808080" 
    return "#2D5A27" if score <= 40 else "#D4A017" if score <= 70 else "#A52A2A"

def get_acwr_badge(ratio):
    try:
        r = float(ratio)
        if pd.isna(r) or r == 0:
            return "#64748B", "#F1F5F9", "No Baseline"
        elif r < 0.80:
            return "#D97706", "#FEF3C7", "Under"
        elif 0.80 <= r <= 1.30:
            return "#137333", "#E6F4EA", "Optimal Spot"
        elif 1.30 < r <= 1.50:
            return "#D97706", "#FEF3C7", "Elevated Risk"
        else:
            return "#D93025", "#FCE8E6", "High Spike"
    except:
        return "#64748B", "#F1F5F9", "N/A"

def get_readiness_color(pct_score):
    if pct_score >= 95:
        return "#15803D"
    elif pct_score >= 90:
        return "#65A30D"
    elif pct_score >= 80:
        return "#D97706"
    elif pct_score >= 70:
        return "#EA580C"
    else:
        return "#B91C1C"

phase_map = {}

# --- 3. HARD DECOUPLED DATA FETCHING ENGINE ---
@st.cache_data(ttl=10)
def load_all_data():
    def heavy_sanitize(frame):
        frame.columns = frame.columns.str.strip()
        for col in frame.columns:
            c_low = col.lower()
            if 'player' in c_low and 'load' in c_low: frame.rename(columns={col: 'Player Load'}, inplace=True)
            if 'total' in c_low and 'jumps' in c_low: frame.rename(columns={col: 'Total Jumps'}, inplace=True)
            if 'estimated' in c_low and 'dist' in c_low: frame.rename(columns={col: 'Estimated Distance (y)'}, inplace=True)
            if 'explosive' in c_low: frame.rename(columns={col: 'Explosive Efforts'}, inplace=True)
            if 'duration' in c_low: frame.rename(columns={col: 'Duration'}, inplace=True)

        math_cols = ['Player Load', 'Total Jumps', 'Estimated Distance (y)', 'Explosive Efforts', 'Duration', 
                     'Moderate Jumps', 'High Jumps', 'Jump Load', 'High Intensity Movement']
        
        for col in math_cols:
            if col in frame.columns:
                frame[col] = pd.to_numeric(frame[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0).astype(float)
            else:
                frame[col] = 0.0
        return frame

    def assign_season(date_val):
        if pd.isna(date_val): return 'Spring'
        y = date_val.year
        m = date_val.month
        d = date_val.day
    
        # Isolate historical data (2025 and earlier)
        if y < 2026:
            return f"Historical {y}"
        
        # 2026 Active Season Boundaries
        if (m == 8 and d >= 24) or (m > 8 and m <= 12):
            return 'In-Season'
        elif (m == 7 and d >= 28) or (m == 8 and d < 24):
            return 'Pre-Season'
        elif 1 <= m <= 4:
            return 'Spring'
        elif (m == 5 and d >= 20) or (m >= 5 and m <= 7):
            return 'Summer'
        else:
            return 'Spring'

    def clean_name_col(df_in):
        if 'Athlete' in df_in.columns and 'Name' not in df_in.columns:
            df_in.rename(columns={'Athlete': 'Name'}, inplace=True)
        if 'Name' in df_in.columns:
            df_in['Name'] = df_in['Name'].astype(str).str.strip()
        return df_in

    # GPS Practice Data
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df = clean_name_col(heavy_sanitize(df))
    df['Sheet_Order'] = range(len(df))
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    if 'Week' in df.columns:
        df['Week'] = pd.to_numeric(df['Week'].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    df['Session_Type'] = df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
    df['Season'] = df['Date'].apply(assign_season)

    # GPS Matches Data
    match_df = pd.read_csv(st.secrets["MATCHES_SHEET_URL"])
    match_df = clean_name_col(heavy_sanitize(match_df))
    match_df['Sheet_Order'] = range(len(match_df))
    match_df['Date'] = pd.to_datetime(match_df['Date'], errors='coerce')
    if 'Week' in match_df.columns:
        match_df['Week'] = pd.to_numeric(match_df['Week'].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    match_df['Session_Name'] = match_df['Activity'].fillna(match_df['Date'].dt.strftime('%m/%d/%Y'))
    match_df['Position'] = match_df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    match_df['PhotoURL'] = match_df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    match_df['Session_Type'] = match_df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
    match_df['Season'] = match_df['Date'].apply(assign_season)

    # CMJ Testing Data
    cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
    cmj_df.columns = cmj_df.columns.str.strip()
    cmj_df = clean_name_col(cmj_df)
    if 'Test Date' not in cmj_df.columns and 'Date' in cmj_df.columns:
        cmj_df.rename(columns={'Date': 'Test Date'}, inplace=True)
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
    if 'Week' in cmj_df.columns:
        cmj_df['Week'] = pd.to_numeric(cmj_df['Week'].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    cmj_df['Season'] = cmj_df['Test Date'].apply(assign_season)

    # Standardized calculated columns
    if 'Countermovement Depth [cm]' in cmj_df.columns:
        cmj_df['Adjusted CMD'] = pd.to_numeric(cmj_df['Countermovement Depth [cm]'], errors='coerce').abs()
    else:
        cmj_df['Adjusted CMD'] = 0.0

    if 'Contraction Time [ms]' not in cmj_df.columns and 'Time to Takeoff [s]' in cmj_df.columns:
        cmj_df['Contraction Time [ms]'] = pd.to_numeric(cmj_df['Time to Takeoff [s]'], errors='coerce') * 1000.0

    if 'Eccentric Deceleration RFD [N/s]' not in cmj_df.columns and 'Eccentric RFD [N/s]' in cmj_df.columns:
        cmj_df['Eccentric Deceleration RFD [N/s]'] = cmj_df['Eccentric RFD [N/s]']

    if 'Relative Mean Con Force' not in cmj_df.columns and 'Concentric Mean Force [N]' in cmj_df.columns:
        cmj_df['Relative Mean Con Force'] = pd.to_numeric(cmj_df['Concentric Mean Force [N]'], errors='coerce')
    if 'Relative Force @ 0 Velo' not in cmj_df.columns and 'Force at Zero Velocity [N]' in cmj_df.columns:
        cmj_df['Relative Force @ 0 Velo'] = pd.to_numeric(cmj_df['Force at Zero Velocity [N]'], errors='coerce')

    # ASH Sheet
    try:
        ash_df = pd.read_csv(st.secrets["ASH_SHEET_URL"])
        ash_df.columns = ash_df.columns.str.strip()
        ash_df = clean_name_col(ash_df)
        if 'Test Date' not in ash_df.columns and 'Date' in ash_df.columns:
            ash_df.rename(columns={'Date': 'Test Date'}, inplace=True)
        ash_df['Test Date'] = pd.to_datetime(ash_df['Test Date'], errors='coerce')
        for col in ['Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force [N] (Asym)(%)']:
            if col in ash_df.columns:
                ash_df[col] = pd.to_numeric(ash_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
        ash_df['Season'] = ash_df['Test Date'].apply(assign_season)
    except:
        ash_df = pd.DataFrame(columns=['Name', 'Test Date', 'Isometric Type', 'Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Season'])

    # External Rotation Sheet
    try:
        er_df = pd.read_csv(st.secrets["ER_SHEET_URL"])
        er_df.columns = er_df.columns.str.strip()
        er_df = clean_name_col(er_df)
        if 'Test Date' not in er_df.columns and 'Date' in er_df.columns:
            er_df.rename(columns={'Date': 'Test Date'}, inplace=True)
        er_df['Test Date'] = pd.to_datetime(er_df['Test Date'], errors='coerce')
        for col in ['L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)']:
            if col in er_df.columns:
                er_df[col] = pd.to_numeric(er_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
        er_df['Season'] = er_df['Test Date'].apply(assign_season)
    except:
        er_df = pd.DataFrame(columns=['Name', 'Test Date', 'L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)', 'Season'])

    # Calf Sheet
    try:
        calf_df = pd.read_csv(st.secrets["CALF_SHEET_URL"])
        calf_df.columns = calf_df.columns.str.strip()
        calf_df = clean_name_col(calf_df)
        if 'Test Date' not in calf_df.columns and 'Date' in calf_df.columns:
            calf_df.rename(columns={'Date': 'Test Date'}, inplace=True)
        calf_df['Test Date'] = pd.to_datetime(calf_df['Test Date'], errors='coerce')
        for col in ['Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force / BM [N/kg] (L)']:
            if col in calf_df.columns:
                calf_df[col] = pd.to_numeric(calf_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
        calf_df['Season'] = calf_df['Test Date'].apply(assign_season)
    except:
        calf_df = pd.DataFrame(columns=['Name', 'Test Date', 'Season'])

    # Hip Sheet
    try:
        hip_df = pd.read_csv(st.secrets["HIP_SHEET_URL"])
        hip_df.columns = hip_df.columns.str.strip()
        hip_df = clean_name_col(hip_df)
        if 'Test Date' not in hip_df.columns and 'Date' in hip_df.columns:
            hip_df.rename(columns={'Date': 'Test Date'}, inplace=True)
        hip_df['Test Date'] = pd.to_datetime(hip_df['Test Date'], errors='coerce')
        for col in ['L Max Force (N)', 'R Max Force (N)']:
            if col in hip_df.columns:
                hip_df[col] = pd.to_numeric(hip_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
        hip_df['Season'] = hip_df['Test Date'].apply(assign_season)
    except:
        hip_df = pd.DataFrame(columns=['Name', 'Test Date', 'Season'])

    # Shoulder Sheet
    try:
        shoulder_df = pd.read_csv(st.secrets["SHOULDER_SHEET_URL"])
        shoulder_df.columns = shoulder_df.columns.str.strip()
        shoulder_df = clean_name_col(shoulder_df)
        if 'Test Date' not in shoulder_df.columns and 'Date' in shoulder_df.columns:
            shoulder_df.rename(columns={'Date': 'Test Date'}, inplace=True)
        shoulder_df['Test Date'] = pd.to_datetime(shoulder_df['Test Date'], errors='coerce')
        for col in ['L Max Force (N)', 'R Max Force (N)']:
            if col in shoulder_df.columns:
                shoulder_df[col] = pd.to_numeric(shoulder_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
        shoulder_df['Season'] = shoulder_df['Test Date'].apply(assign_season)
    except:
        shoulder_df = pd.DataFrame(columns=['Name', 'Test Date', 'Season'])

    # Phases Data
    phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
    phase_df = clean_name_col(heavy_sanitize(phase_df))
    if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
    phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')

    date_season_map = df.drop_duplicates('Date').set_index('Date')['Season'].to_dict()
    phase_df['Season'] = phase_df['Date'].map(date_season_map).fillna('Spring')
    
    try:
        thresh_df = pd.read_csv(st.secrets["THRESH_SHEET_URL"])
        thresh_df.columns = thresh_df.columns.str.strip()
    except:
        thresh_df = None
        
    return df.dropna(subset=['Date']), match_df.dropna(subset=['Date']), cmj_df, phase_df, thresh_df, ash_df, er_df, calf_df, hip_df, shoulder_df


# --- 4. EWMA ACWR COMPUTATION ENGINE ---
def compute_athlete_ewMA_calendar(df_player, metrics_list):
    if df_player.empty or df_player['Date'].dropna().empty:
        return pd.DataFrame()
    daily = df_player.groupby('Date')[metrics_list].sum().reset_index().sort_values('Date')
    min_date = daily['Date'].min()
    max_date = daily['Date'].max()
    full_idx = pd.date_range(start=min_date, end=max_date, freq='D')
    cal = daily.set_index('Date').reindex(full_idx).fillna(0.0).reset_index()
    cal.rename(columns={'index': 'Date'}, inplace=True)
    
    for m in metrics_list:
        cal[f'{m}_Acute'] = cal[m].ewm(span=7, adjust=False).mean()
        cal[f'{m}_Chronic'] = cal[m].ewm(span=28, adjust=False).mean()
        cal[f'{m}_ACWR'] = cal.apply(
            lambda r: (r[f'{m}_Acute'] / r[f'{m}_Chronic']) if r[f'{m}_Chronic'] > 0 else 0.0,
            axis=1
        )
    return cal

# --- REUSABLE GAUGE GENERATOR FUNCTION ---
def create_wellness_gauge(score_val, height=230):
    normalized = float(min(100, max(0, score_val)))
    gauge_colors = ['#B91C1C', '#EA580C', '#FACC15', '#65A30D', '#15803D', 'rgba(0,0,0,0)']
    values = [20, 20, 20, 20, 20, 100]

    center_x, center_y = 0.50, 0.50
    needle_length = 0.38
    
    angle_rad = math.pi * (1.0 - (normalized / 100.0))
    needle_x = center_x + needle_length * math.cos(angle_rad)
    needle_y = center_y + needle_length * math.sin(angle_rad)

    fig = go.Figure()
    fig.add_trace(go.Pie(
        values=values,
        rotation=270,
        direction='clockwise',
        hole=0.50,
        marker=dict(colors=gauge_colors, line=dict(color='white', width=2)),
        textinfo='none',
        hoverinfo='none',
        sort=False,
        domain=dict(x=[0, 1], y=[0, 1])
    ))

    fig.add_shape(
        type='line',
        x0=center_x, y0=center_y,
        x1=needle_x, y1=needle_y,
        line=dict(color='#111827', width=5)
    )
    fig.add_shape(
        type='circle',
        x0=center_x - 0.035, y0=center_y - 0.035,
        x1=center_x + 0.035, y1=center_y + 0.035,
        fillcolor='#111827',
        line_color='#111827'
    )
    fig.add_annotation(
        x=center_x, y=center_y - 0.02,
        text=f"<b>{int(score_val)}%</b>",
        showarrow=False,
        font=dict(size=14, color="white", weight="bold"),
        bgcolor="#1E293B",
        borderpad=4,
        bordercolor="#1E293B"
    )
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[0, 1]),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[0, 1]),
        paper_bgcolor="white"
    )
    return fig


# --- 5. EXECUTION BLOCK CONTEXT ---
if check_password():
    if "is_printing" not in st.session_state:
        st.session_state.is_printing = False

    LOCKED_CONFIG = {'staticPlot': False, 'displayModeBar': False}

    try:
        raw_df, raw_match_df, raw_cmj_df, raw_phase_df, thresh_df, raw_ash_df, raw_er_df, raw_calf_df, raw_hip_df, raw_shoulder_df = load_all_data()

        # --- GLOBAL SIDEBAR ---
        st.sidebar.markdown("### Active Season")
        view_seasons = ["In-Season", "Pre-Season", "Spring", "Summer"]
        if "global_season_toggle" not in st.session_state:
            st.session_state.global_season_toggle = "In-Season"
    
        selected_season = st.sidebar.selectbox(
            "Select Season", 
            view_seasons, 
            key="global_season_toggle"
        )
            
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Performance Hubs")
        
        workflow_hubs = [
            "Daily Monitoring & Wellness",
            "Match Performance",
            "Practice & Drill Planning",
            "Workload & ACWR",
            "Testing & Baselines"
        ]
        
        if "main_workflow_nav" not in st.session_state:
            st.session_state.main_workflow_nav = workflow_hubs[0]
            
        selected_hub = st.sidebar.radio(
            "Navigation", 
            workflow_hubs, 
            key="main_workflow_nav"
        )

        df_master = raw_df[raw_df['Season'] == selected_season].copy()
        match_master = raw_match_df[raw_match_df['Season'] == selected_season].copy()
        cmj_master = raw_cmj_df[raw_cmj_df['Season'] == selected_season].copy()
        ash_master = raw_ash_df[raw_ash_df['Season'] == selected_season].copy()
        er_master = raw_er_df[raw_er_df['Season'] == selected_season].copy()
        calf_master = raw_calf_df[raw_calf_df['Season'] == selected_season].copy()
        hip_master = raw_hip_df[raw_hip_df['Season'] == selected_season].copy()
        shoulder_master = raw_shoulder_df[raw_shoulder_df['Season'] == selected_season].copy()
        phase_master = raw_phase_df[raw_phase_df['Season'] == selected_season].copy()

        session_list = df_master.sort_values('Date', ascending=False)['Session_Name'].dropna().unique().tolist() if not df_master.empty else []

        full_df_unfiltered = raw_df.copy()
        all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
        metrics_to_score = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]
        
        cmj_col = 'Jump Height (Imp-Mom) [in]' if 'Jump Height (Imp-Mom) [in]' in raw_cmj_df.columns else 'Jump Height (Imp-Mom) [cm]'
        rsi_col = 'RSI-modified [m/s]'

        master_athlete_list = sorted(list(
            set(raw_df['Name'].dropna().unique()) | 
            set(raw_cmj_df['Name'].dropna().unique()) | 
            set(raw_ash_df['Name'].dropna().unique()) | 
            set(raw_er_df['Name'].dropna().unique()) | 
            set(raw_calf_df['Name'].dropna().unique()) | 
            set(raw_hip_df['Name'].dropna().unique()) | 
            set(raw_shoulder_df['Name'].dropna().unique())
        ))

        st.markdown('<div class="main-logo-container" style="text-align: center; margin-top: 10px; margin-bottom: 15px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120"><div style="color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;">LADY VOLS VOLLEYBALL PERFORMANCE</div></div>', unsafe_allow_html=True)

        readiness_metrics_ref = [
            {"label": "mRSI", "col": "RSI-modified [m/s]", "invert": False},
            {"label": "ECC RFD", "col": "Eccentric Deceleration RFD [N/s]", "alt_col": "Eccentric RFD [N/s]", "invert": False},
            {"label": "Force @ 0 Velo", "col": "Force at Zero Velocity [N]", "invert": False},
            {"label": "TTO", "col": "Contraction Time [ms]", "alt_col": "Time to Takeoff [s]", "invert": True},
            {"label": "ECC Peak Velo", "col": "Eccentric Peak Velocity [m/s]", "invert": False},
            {"label": "Ecc Peak Power", "col": "Eccentric Peak Power [W]", "invert": False},
            {"label": "P2:P1 Con Impulse", "col": "P2 Concentric Impulse:P1 Concentric Impulse", "invert": True}
        ]

        def compute_excel_readiness_score(curr_row, prev_row):
            sub_scores = []
            for rm in readiness_metrics_ref:
                c_name = rm["col"] if rm["col"] in curr_row else rm.get("alt_col", rm["col"])
                if c_name in curr_row and c_name in prev_row:
                    t_val = abs(float(curr_row.get(c_name, 0.0)))
                    s_val = abs(float(prev_row.get(c_name, 0.0)))
                    if s_val > 0 and t_val > 0:
                        if rm["invert"]:
                            pct_diff = ((t_val - s_val) / s_val) * 100.0
                            score = 100.0 - pct_diff
                        else:
                            pct_diff = ((t_val - s_val) / s_val) * 100.0
                            score = 100.0 + pct_diff
                        score = min(100.0, score)
                        sub_scores.append(max(0.0, score))
            if sub_scores:
                return sum(sub_scores) / len(sub_scores)
            return 100.0


        # =========================================================================
        # --- HUB 1: DAILY MONITORING & WELLNESS ----------------------------------
        # =========================================================================
        if selected_hub == "Daily Monitoring & Wellness":
            daily_subtabs = ["Individual Profile", "Practice Scores", "Daily Combined Scores", "Practice History", "CMJ Performance"]
            if selected_season == "Summer":
                daily_subtabs.append("Spring Max vs Daily Combined")

            if "daily_subtab_radio" not in st.session_state or st.session_state["daily_subtab_radio"] not in daily_subtabs:
                st.session_state["daily_subtab_radio"] = daily_subtabs[0]

            sel_daily_tab = st.radio("Daily Sub Navigation", daily_subtabs, key="daily_subtab_radio", horizontal=True, label_visibility="collapsed")

            if sel_daily_tab == "Individual Profile":
                df_t0 = df_master.copy()
                cmj_t0 = cmj_master.copy()
                ash_t0 = ash_master.copy()
                er_t0 = er_master.copy()
                phase_t0 = phase_master.copy()

                target_date_str = "2026-04-04"
                tournament_label = "GT Spring Tournament 4-4-26"
                
                clean_session_list_prof = []
                tourney_added_prof = False
                for s in session_list:
                    s_date_series = df_t0[df_t0['Session_Name'] == s]['Date']
                    if not s_date_series.empty:
                        s_date = pd.to_datetime(s_date_series.iloc[0]).strftime('%Y-%m-%d')
                        if selected_season == "Spring" and s_date == target_date_str:
                            if not tourney_added_prof:
                                clean_session_list_prof.append(tournament_label)
                                tourney_added_prof = True
                        else:
                            clean_session_list_prof.append(s)
                    else:
                        clean_session_list_prof.append(s)
                
                if not clean_session_list_prof:
                    clean_session_list_prof = [tournament_label] if selected_season == "Spring" else session_list

                c_prof1, c_prof2 = st.columns(2)
                with c_prof1: selected_session_prof = st.selectbox("Session Selection", clean_session_list_prof, index=0, key="nav_sel_prof_t0")
                with c_prof2: selected_athlete_prof = st.selectbox("Athlete Selection", master_athlete_list, key="nav_ath_prof_t0")

                if selected_season == "Spring" and selected_session_prof == tournament_label:
                    curr_date_prof = pd.to_datetime(target_date_str)
                    p_session_data = df_t0[(df_t0['Name'] == selected_athlete_prof) & (df_t0['Date'].dt.date == curr_date_prof.date())].copy()
                    p_row = p_session_data.groupby(['Name', 'Position', 'PhotoURL']).sum(numeric_only=True).reset_index().iloc[0] if not p_session_data.empty else pd.Series()
                    p_meta = p_session_data.iloc[0] if not p_session_data.empty else pd.Series()
                else:
                    p_session_data = df_t0[(df_t0['Name'] == selected_athlete_prof) & (df_t0['Session_Name'] == selected_session_prof)]
                    p_row = p_session_data.iloc[0] if not p_session_data.empty else pd.Series()
                    curr_date_prof = pd.to_datetime(p_row['Date']) if not p_row.empty else None
                    p_meta = p_row

                if p_row.empty or curr_date_prof is None or pd.isna(curr_date_prof):
                    curr_date_prof = pd.to_datetime(df_t0['Date'].max()) if not df_t0.empty and df_t0['Date'].notna().any() else pd.to_datetime("2026-08-06")
                    meta_lookup = full_df_unfiltered[full_df_unfiltered['Name'] == selected_athlete_prof]
                    pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"
                    photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                    p_meta = pd.Series({'Name': selected_athlete_prof, 'Position': pos_val, 'PhotoURL': photo_val})
                    p_row = pd.Series({m: 0.0 for m in all_metrics})
                    p_row['Name'] = selected_athlete_prof

                # ALWAYS calculate 30-day rolling max from full unfiltered historical data
                p_full_prof = full_df_unfiltered[full_df_unfiltered['Name'] == selected_athlete_prof]
                curr_order = p_row.get('Sheet_Order', float('inf'))

                lb_prof = p_full_prof[
                    (p_full_prof['Date'].dt.date >= curr_date_prof.date() - timedelta(days=30)) & 
                    (p_full_prof['Date'].dt.date <= curr_date_prof.date()) &
                    (p_full_prof['Sheet_Order'] <= curr_order)
                ]

                filtered_metrics_prof = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]
                r_html_prof = ""; t_grade_prof = 0; c_metrics_prof = 0

                for k in filtered_metrics_prof:
                    val = p_row.get(k, 0.0)
                    mx = lb_prof[k].max() if (not lb_prof.empty and k in lb_prof.columns and lb_prof[k].max() > 0) else 1.0
                    avg = lb_prof[k].mean() if (not lb_prof.empty and k in lb_prof.columns and lb_prof[k].mean() > 0) else 1.0
                    g = math.ceil((val / mx) * 100) if mx > 0 else 0
                    t_grade_prof += g; c_metrics_prof += 1
                    diff = (val - avg) / avg if avg != 0 else 0
                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                    arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                    r_html_prof += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"

                sc_prof = math.ceil(t_grade_prof / c_metrics_prof) if c_metrics_prof > 0 else 0

                c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
                with c1: st.markdown(f'<div style="text-align:center;"><img src="{p_meta.get("PhotoURL", "https://www.w3schools.com/howto/img_avatar.png")}" class="player-photo-large"></div><h3 style="text-align:center;">{p_meta.get("Name", selected_athlete_prof)}</h3>', unsafe_allow_html=True)
                with c2: st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today Total</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>{r_html_prof}</tbody></table>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(sc_prof)};">{sc_prof}</div></div><p style="text-align:center; font-weight:bold; color:grey; margin-top:10px;">SESSION SCORE</p>', unsafe_allow_html=True)
                
                st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
                st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">COUNTERMOVEMENT JUMP</h4>', unsafe_allow_html=True)
                
                jc1, jc2 = st.columns([1.5, 3.5])
                p_cmj_hist = cmj_t0[(cmj_t0['Name'] == selected_athlete_prof) & (cmj_t0['Test Date'] <= curr_date_prof)].sort_values('Test Date')

                with jc1:
                    baseline_cmj = cmj_t0[(cmj_t0['Name'] == selected_athlete_prof) & (cmj_t0['Season'] == selected_season)].head(1)
                    if not baseline_cmj.empty and not p_cmj_hist.empty:
                        base_h = baseline_cmj.iloc[-1][cmj_col]
                        base_rsi = baseline_cmj.iloc[-1][rsi_col]
                        latest_cmj = p_cmj_hist.iloc[-1]
                        cur_h, cur_rsi = latest_cmj[cmj_col], latest_cmj[rsi_col]
                        p_diff_h = ((cur_h - base_h) / base_h * 100) if base_h > 0 else 0
                        p_diff_rsi = ((cur_rsi - base_rsi) / base_rsi * 100) if base_rsi > 0 else 0
                        color_h = "#28a745" if cur_h >= base_h else "#dc3545"
                        color_rsi = "#28a745" if cur_rsi >= base_rsi else "#dc3545"

                        sc1, sc2 = st.columns(2)
                        with sc1: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_h}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_h:.1f}</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">CMJ HEIGHT</span></div></div>', unsafe_allow_html=True)
                        with sc2: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_rsi}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_rsi:.2f}</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RSI MOD</span></div></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> CMJ: {p_diff_h:+.1f}% | RSI: {p_diff_rsi:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base Values:</b> CMJ: {base_h:.1f} | RSI: {base_rsi:.2f}</p></div>', unsafe_allow_html=True)
                    else:
                        st.warning("No data recorded.")

                with jc2:
                    if not p_cmj_hist.empty:
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[cmj_col], name="Jump Height", mode='lines+markers', line=dict(color='#FF8200', width=3)), secondary_y=False)
                        fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[rsi_col], name="RSI Modified", mode='lines+markers', line=dict(color='#4895DB', dash='dot', width=2)), secondary_y=True)
                        fig.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                        st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG, key="cmj_top_chart_t0")
                    else:
                        st.info("No Countermovement Jump metrics recorded.")

                st.markdown('<hr style="display:block !important; margin:15px 0; border:0; border-top:1px solid #E5E5E7;" />', unsafe_allow_html=True)
                st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">ASH SHOULDER: ISO I</h4>', unsafe_allow_html=True)
                    
                p_ash_all = ash_t0[(ash_t0['Name'] == selected_athlete_prof) & (ash_t0['Test Date'] <= curr_date_prof)].sort_values('Test Date')
                if not p_ash_all.empty:
                    ac1, ac2 = st.columns([1.5, 3.5])
                    with ac1:
                        latest_date_ash = p_ash_all['Test Date'].iloc[-1]
                        today_ash_rows = p_ash_all[p_ash_all['Test Date'] == latest_date_ash]
                        row_i = today_ash_rows[today_ash_rows['Isometric Type'].str.contains('I', case=False, na=False)]
                        li = row_i.iloc[-1]['Peak Vertical Force [N] (L)'] if not row_i.empty else 0.0
                        ri = row_i.iloc[-1]['Peak Vertical Force [N] (R)'] if not row_i.empty else 0.0
                        asym_i = row_i.iloc[-1]['Peak Vertical Force [N] (Asym)(%)'] if not row_i.empty else 0.0
                        baseline_ash = p_ash_all[(p_ash_all['Season'] == selected_season) & (p_ash_all['Isometric Type'].str.contains('I', case=False, na=False))].head(1)
                        base_li = baseline_ash.iloc[-1]['Peak Vertical Force [N] (L)'] if not baseline_ash.empty else 0.0
                        base_ri = baseline_ash.iloc[-1]['Peak Vertical Force [N] (R)'] if not baseline_ash.empty else 0.0
                        pct_l = ((li - base_li) / base_li * 100) if base_li > 0 else 0
                        pct_r_ash = ((ri - base_ri) / base_ri * 100) if base_ri > 0 else 0
                        color_ash_l = "#28a745" if li >= 100 else "#dc3545"
                        color_ash_r = "#28a745" if ri >= 100 else "#dc3545"

                        sc1, sc2 = st.columns(2)
                        with sc1: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_ash_l}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{li:.0f} N</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">LEFT</span></div></div>', unsafe_allow_html=True)
                        with sc2: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_ash_r}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{ri:.0f} N</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RIGHT</span></div></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>Asymmetry:</b> {asym_i:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> L: {pct_l:+.1f}% | R: {pct_r_ash:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base Force:</b> L: {base_li:.0f} N | R: {base_ri:.0f} N</p></div>', unsafe_allow_html=True)
                    with ac2:
                        p_ash_i_only = p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)]
                        if not p_ash_i_only.empty:
                            fig_ash = go.Figure()
                            fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (L)'], name="Left Peak Force", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                            fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (R)'], name="Right Peak Force", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                            fig_ash.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                            st.plotly_chart(fig_ash, use_container_width=True, config=LOCKED_CONFIG, key="ash_profile_chart_t0")
                else:
                    st.info("No ASH shoulder test dataset recorded.")

                st.markdown('<hr style="display:block !important; margin:15px 0; border:0; border-top:1px solid #E5E5E7;" />', unsafe_allow_html=True)
                st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">EXTERNAL ROTATION: ROM</h4>', unsafe_allow_html=True)
                
                p_er_hist = er_t0[(er_t0['Name'] == selected_athlete_prof) & (er_t0['Test Date'] <= curr_date_prof)].sort_values('Test Date')
                if not p_er_hist.empty:
                    ec1, ec2 = st.columns([1.5, 3.5])
                    with ec1:
                        baseline_er = p_er_hist[p_er_hist['Season'] == selected_season].head(1)
                        if not baseline_er.empty:
                            base_l_rom = baseline_er.iloc[-1]['L Max ROM (°)']
                            base_r_rom = baseline_er.iloc[-1]['R Max ROM (°)']
                            latest_er = p_er_hist.iloc[-1]
                            cur_l_rom = latest_er['L Max ROM (°)']
                            cur_r_rom = latest_er['R Max ROM (°)']
                            cur_asym_rom = latest_er['ROM Asymmetry (%)']
                            rom_pct_l = ((cur_l_rom - base_l_rom) / base_l_rom * 100) if base_l_rom > 0 else 0
                            rom_pct_r = ((cur_r_rom - base_r_rom) / base_r_rom * 100) if base_r_rom > 0 else 0
                            color_er_l = "#28a745" if cur_l_rom >= 110 else "#ffc107" if 90 <= cur_l_rom <= 109 else "#dc3545"
                            color_er_r = "#28a745" if cur_r_rom >= 110 else "#ffc107" if 90 <= cur_r_rom <= 109 else "#dc3545"

                            sc1, sc2 = st.columns(2)
                            with sc1: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_er_l}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_l_rom:.1f}°</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">LEFT</span></div></div>', unsafe_allow_html=True)
                            with sc2: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_er_r}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_r_rom:.1f}°</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RIGHT</span></div></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>Asymmetry:</b> {cur_asym_rom:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> L: {rom_pct_l:+.1f}% | R: {rom_pct_r:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base ROM:</b> L: {base_l_rom:.1f}° | R: {base_r_rom:.1f}°</p></div>', unsafe_allow_html=True)
                    with ec2:
                        fig_er = go.Figure()
                        fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['L Max ROM (°)'], name="Left Max ROM", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                        fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['R Max ROM (°)'], name="Right Max ROM", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                        fig_er.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                        st.plotly_chart(fig_er, use_container_width=True, config=LOCKED_CONFIG, key="er_profile_chart_t0")
                else:
                    st.info("No External Rotation data recorded.")

                st.divider()
                target_activity = p_meta.get('Activity', p_meta.get('Session_Name', selected_session_prof))

                p_ph = phase_t0[
                    (phase_t0['Name'] == selected_athlete_prof) & 
                    (phase_t0['Date'].dt.date == curr_date_prof.date())
                ].copy()

                if 'Activity' in p_ph.columns and target_activity:
                    p_ph_act = p_ph[p_ph['Activity'].astype(str).str.strip().str.lower() == str(target_activity).strip().lower()]
                    if not p_ph_act.empty:
                        p_ph = p_ph_act

                if not p_ph.empty:
                    st.markdown('<div class="section-header">Practice Phase Analysis</div>', unsafe_allow_html=True)
                    fig_ph = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_ph.add_trace(go.Bar(x=p_ph['Phase'], y=p_ph['Player Load'], name="Player Load", marker_color='#4895DB'), secondary_y=False)
                    fig_ph.add_trace(go.Scatter(x=p_ph['Phase'], y=p_ph['Total Jumps'], name="Total Jumps", line=dict(color='#FF8200', width=4), mode='lines+markers'), secondary_y=True)
                    fig_ph.update_layout(height=350, showlegend=True, template="simple_white", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=0, r=0, t=30, b=0))
                    fig_ph.update_yaxes(title_text="Player Load", secondary_y=False)
                    fig_ph.update_yaxes(title_text="Total Jumps", secondary_y=True)
                    st.plotly_chart(fig_ph, use_container_width=True, config=LOCKED_CONFIG, key="phase_analysis_t0")

            elif sel_daily_tab == "Practice Scores":
                df_t1 = df_master.copy()
                target_date_str = "2026-04-04"
                tournament_label = "GT Spring Tournament 4-4-26"
                
                clean_session_list = []
                tourney_added = False
                for s in session_list:
                    s_date_series = df_t1[df_t1['Session_Name'] == s]['Date']
                    if not s_date_series.empty:
                        s_date = pd.to_datetime(s_date_series.iloc[0]).strftime('%Y-%m-%d')
                        if selected_season == "Spring" and s_date == target_date_str:
                            if not tourney_added:
                                clean_session_list.append(tournament_label)
                                tourney_added = True
                        else:
                            clean_session_list.append(s)
                    else:
                        clean_session_list.append(s)

                if not clean_session_list:
                    clean_session_list = [tournament_label] if selected_season == "Spring" else session_list

                c_gal1, c_gal2 = st.columns(2)
                with c_gal1: selected_session_gal = st.selectbox("Session Selection", clean_session_list, index=0, key="nav_sel_gal_t1")
                with c_gal2: pos_f_gal = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df_t1['Position'].unique() if p != "N/A"]), key="nav_pos_gal_t1")
                
                if selected_season == "Spring" and selected_session_gal == tournament_label:
                    curr_date_gal = pd.to_datetime(target_date_str)
                    display_df = df_t1[df_t1['Date'].dt.date == curr_date_gal.date()].groupby(['Name', 'Position', 'PhotoURL']).sum(numeric_only=True).reset_index()
                else:
                    display_df = df_t1[df_t1['Session_Name'] == selected_session_gal].copy()
                    if not display_df.empty: 
                        curr_date_gal = pd.to_datetime(display_df['Date'].iloc[0])

                if display_df is not None and not display_df.empty:
                    if pos_f_gal != "All Positions": display_df = display_df[display_df['Position'] == pos_f_gal]
                    athlete_names = sorted(display_df['Name'].unique())
                    filtered_metrics_gal = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]

                    for i in range(0, len(athlete_names), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(athlete_names):
                                name = athlete_names[i + j]
                                p_session_row = display_df[display_df['Name'] == name].iloc[0]
                                # Look up across full historical dataset
                                p_full_g = full_df_unfiltered[full_df_unfiltered['Name'] == name]
                                curr_order = p_session_row.get('Sheet_Order', float('inf'))

                                lb_sums = p_full_g[
                                    (p_full_g['Date'].dt.date >= curr_date_gal.date() - timedelta(days=30)) & 
                                    (p_full_g['Date'].dt.date <= curr_date_gal.date()) &
                                    (p_full_g['Sheet_Order'] <= curr_order)
                                ]
                                
                                r_html = ""; t_grade = 0; c_metrics = 0
                                for k in filtered_metrics_gal:
                                    val = p_session_row[k]
                                    mx = lb_sums[k].max() if (not lb_sums.empty and k in lb_sums.columns and lb_sums[k].max() > 0) else 1.0
                                    avg = lb_sums[k].mean() if (not lb_sums.empty and k in lb_sums.columns and lb_sums[k].mean() > 0) else 1.0
                                    g = math.ceil((val / mx) * 100) if mx > 0 else 0
                                    t_grade += g; c_metrics += 1
                                    diff = (val - avg) / avg if avg != 0 else 0
                                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                                    arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                                    r_html += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"
                                
                                sc_g = math.ceil(t_grade / c_metrics) if c_metrics > 0 else 0
                                with cols[j]: st.markdown(f'<div style="border:1px solid #E5E5E7; border-radius:15px; padding:15px; margin-bottom:20px; background-color:white;"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{p_session_row["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px; color:#333;">{name}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Total</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div><div style="flex:1; text-align:center;"><div style="background-color:{get_flipped_gradient(sc_g)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{sc_g}</div></div></div></div>', unsafe_allow_html=True)

            elif sel_daily_tab == "Daily Combined Scores":
                df_t2 = df_master.copy()
                valid_dates_sorted = df_t2[df_t2['Date'].notna()].sort_values('Date', ascending=False)['Date'].dt.strftime('%Y-%m-%d').unique().tolist()
                
                target_date_str = "2026-04-04"
                tournament_label = "GT Spring Tournament 4-4-26"
                clean_date_list = []
                tourney_added_comb = False
                for d_str in valid_dates_sorted:
                    if selected_season == "Spring" and d_str == target_date_str:
                        if not tourney_added_comb:
                            clean_date_list.append(tournament_label)
                            tourney_added_comb = True
                    else:
                        clean_date_list.append(d_str)

                if not clean_date_list: clean_date_list = valid_dates_sorted

                c_comb1, c_comb2 = st.columns(2)
                with c_comb1: selected_date_comb = st.selectbox("Date Selection", clean_date_list, index=0, key="nav_sel_comb_t2")
                with c_comb2: pos_f_comb = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df_t2['Position'].unique() if p != "N/A"]), key="nav_pos_comb_t2")
                
                target_date_obj_comb = pd.to_datetime(target_date_str) if (selected_season == "Spring" and selected_date_comb == tournament_label) else pd.to_datetime(selected_date_comb)
                display_df_comb = df_t2[df_t2['Date'] == target_date_obj_comb].groupby(['Name', 'Position', 'PhotoURL'])[all_metrics].sum().reset_index()

                if not display_df_comb.empty:
                    if pos_f_comb != "All Positions": display_df_comb = display_df_comb[display_df_comb['Position'] == pos_f_comb]
                    athlete_names_comb = sorted(display_df_comb['Name'].unique())
                    filtered_metrics_comb = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]

                    for i in range(0, len(athlete_names_comb), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(athlete_names_comb):
                                name = athlete_names_comb[i + j]
                                p_session_row = display_df_comb[display_df_comb['Name'] == name].iloc[0]
                                # Calculate 30-day daily sums across all seasons
                                p_full_g = full_df_unfiltered[full_df_unfiltered['Name'] == name]
                                daily_sums_g = p_full_g.groupby('Date')[all_metrics].sum().reset_index()
                                lb_sums = daily_sums_g[(daily_sums_g['Date'] >= target_date_obj_comb - timedelta(days=30)) & (daily_sums_g['Date'] <= target_date_obj_comb)]
                                
                                r_html = ""; t_grade = 0; c_metrics = 0
                                for k in filtered_metrics_comb:
                                    val = p_session_row[k]
                                    mx = lb_sums[k].max() if not lb_sums.empty else 1.0
                                    avg = lb_sums[k].mean() if not lb_sums.empty else 1.0
                                    g = math.ceil((val / mx) * 100) if mx > 0 else 0
                                    t_grade += g; c_metrics += 1
                                    diff = (val - avg) / avg if avg != 0 else 0
                                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.15 else ""
                                    arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.15 else '↓'}</span>" if abs(diff) > 0.15 else ""
                                    r_html += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"
                                
                                sc_g = math.ceil(t_grade / c_metrics) if c_metrics > 0 else 0
                                with cols[j]: st.markdown(f'<div style="border:1px solid #E5E5E7; border-radius:15px; padding:15px; margin-bottom:20px; background-color:white;"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{p_session_row["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px; color:#333;">{name}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Combined Total</th><th>30d Max Day</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div><div style="flex:1; text-align:center;"><div style="background-color:{get_flipped_gradient(sc_g)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{sc_g}</div></div></div></div>', unsafe_allow_html=True)

            elif sel_daily_tab == "Practice History":
                df_t4 = df_master.copy()
                st.markdown('<div class="section-header">Season History & Team Weekly Review</div>', unsafe_allow_html=True)
                
                sub_tabs_list = ["Individual Review", "Team Weekly Review"]
                if "ph_subtab_active" not in st.session_state:
                    st.session_state.ph_subtab_active = sub_tabs_list[0]
                    
                selected_ph_subtab = st.radio("Practice History Sub Navigation", sub_tabs_list, key="ph_subtab_active", horizontal=True, label_visibility="collapsed")

                if selected_ph_subtab == "Individual Review":
                    sel_ath_hist = st.selectbox("Select Athlete", sorted(df_t4['Name'].unique()), key="master_ath_sel_t4")
                    p_full = full_df_unfiltered[full_df_unfiltered['Name'] == sel_ath_hist].copy()
                    p_full['Date'] = pd.to_datetime(p_full['Date'])
                    p_sessions = df_t4[df_t4['Name'] == sel_ath_hist].sort_values(['Date', 'Sheet_Order']).reset_index(drop=True)

                    scores_list = []
                    for idx, row in p_sessions.iterrows():
                        row_grades = []
                        curr_order = row.get('Sheet_Order', float('inf'))
                        lb_sums = p_full[(p_full['Date'] >= row['Date'] - timedelta(days=30)) & (p_full['Date'] <= row['Date']) & (p_full['Sheet_Order'] <= curr_order)]
                        
                        for m in metrics_to_score:
                            val = row[m]
                            mx = lb_sums[m].max() if not lb_sums.empty else 1.0
                            row_grades.append(math.ceil((val / mx) * 100) if mx > 0 else 0)
                            
                        is_match = any(w in str(row['Session_Name']).upper() or w in str(row['Session_Type']).upper() for w in ['MATCH', 'GAME'])
                        scores_list.append({
                            'Date': row['Date'], 
                            'Sheet_Order': curr_order,
                            'Display': row['Date'].strftime('%m/%d'), 
                            'Session_Name': row['Session_Name'],
                            'Score': int(math.ceil(sum(row_grades) / len(row_grades))) if row_grades else 0, 
                            'Type': 'Match' if is_match else 'Practice', 
                            'Week': str(row['Week'])
                        })
                
                    master_df_history = pd.DataFrame(scores_list).reset_index(drop=True)
                    st.markdown(f"### Full Season Performance: {sel_ath_hist}")
                    
                    if not master_df_history.empty:
                        fig_master = go.Figure()
                        fig_master.add_trace(go.Scatter(x=master_df_history['Display'], y=master_df_history['Score'], mode='lines', line=dict(color='#4895DB', width=2), showlegend=False, hoverinfo='skip'))

                        prac_df = master_df_history[master_df_history['Type'] == 'Practice']
                        if not prac_df.empty: 
                            fig_master.add_trace(go.Scatter(x=prac_df['Display'], y=prac_df['Score'], mode='markers+text', text=prac_df['Score'], textposition="top center", name="Practice", hovertemplate="<b>%{customdata}</b><br>Date: %{x}<br>Score: %{y}<extra></extra>", customdata=prac_df['Session_Name'], marker=dict(size=9, color='#4895DB', line=dict(width=1, color='white'))))
                            
                        match_df_line = master_df_history[master_df_history['Type'] == 'Match']
                        if not match_df_line.empty: 
                            fig_master.add_trace(go.Scatter(x=match_df_line['Display'], y=match_df_line['Score'], mode='markers+text', text=[f"<b>{s}</b>" for s in match_df_line['Score']], textposition="top center", name="Match Day", hovertemplate="<b>%{customdata}</b><br>Date: %{x}<br>Score: %{y}<extra></extra>", customdata=match_df_line['Session_Name'], marker=dict(size=15, color='#FF8200', line=dict(width=3, color='#31333F')), textfont=dict(color='#31333F', size=13, weight='bold')))
                            
                        unique_dates_df = master_df_history.drop_duplicates(subset=['Display']).reset_index(drop=True)
                        for i in range(1, len(unique_dates_df)):
                            if unique_dates_df.iloc[i]['Week'] != unique_dates_df.iloc[i-1]['Week']:
                                fig_master.add_vline(x=i-0.5, line_dash="dash", line_color="#515154", opacity=0.3)
                                fig_master.add_annotation(x=i-0.5, y=0.98, yref="paper", text=f"Wk {unique_dates_df.iloc[i]['Week']}", showarrow=False, bgcolor="white", font=dict(size=10, color="#515154"), yanchor="top")
                                
                        fig_master.update_layout(template="simple_white", height=500, margin=dict(l=40, r=20, t=40, b=90), xaxis=dict(type='category', title=dict(text="Date", standoff=15)), yaxis=dict(range=[0, 120], automargin=True, tickvals=[0, 20, 40, 60, 80, 100]), legend=dict(orientation="h", yanchor="top", y=-0.28, x=0.5, xanchor="center"))
                        st.plotly_chart(fig_master, use_container_width=True, key=f"master_full_flow_{sel_ath_hist}_t4")

                elif selected_ph_subtab == "Team Weekly Review":
                    sel_week = st.selectbox("Select Review Week", sorted(df_t4['Week'].unique(), reverse=True), key="team_week_sel_t4")
                    week_df = df_t4[df_t4['Week'] == sel_week].copy()
                    ath_names = sorted(week_df['Name'].unique())
                    
                    for i in range(0, len(ath_names), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(ath_names):
                                name = ath_names[i+j]
                                p_all = full_df_unfiltered[full_df_unfiltered['Name'] == name].sort_values(['Date', 'Sheet_Order']).reset_index(drop=True)
                                w_daily = df_t4[(df_t4['Name'] == name) & (df_t4['Week'].astype(str) == str(sel_week))]
                                
                                if not w_daily.empty:
                                    card_scores = []
                                    for idx, r in w_daily.iterrows():
                                        r_grades = []
                                        curr_order = r.get('Sheet_Order', float('inf'))
                                        lb = p_all[(p_all['Date'] >= r['Date'] - timedelta(days=30)) & (p_all['Date'] <= r['Date']) & (p_all['Sheet_Order'] <= curr_order)]
                                        for m in metrics_to_score:
                                            mx = lb[m].max() if not lb.empty else 1.0
                                            r_grades.append(math.ceil((r[m] / mx) * 100) if mx > 0 else 0)
                                            
                                        card_scores.append({'Display': r['Date'].strftime('%m/%d'), 'Score': round(sum(r_grades)/len(r_grades), 0) if r_grades else 0})
                                    
                                    with cols[j]:
                                        st.markdown(f'<div style="border:1px solid #E5E5E7; border-top:4px solid #FF8200; border-radius:10px 10px 0 0; padding:10px; background:white;"><div style="display:flex; align-items:center; gap:12px;"><div style="width:60px; height:60px; border-radius:50%; background-color:white; overflow: hidden; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 1px 3px rgba(0,0,0,0.1);"><img src="{p_all.iloc[0]["PhotoURL"]}" style="width:100%; height:100%; object-fit:contain;"></div><p style="margin:0; font-weight:900; font-size:16px; color:#31333F;">{name}</p></div></div>', unsafe_allow_html=True)
                                        fig_p = px.line(pd.DataFrame(card_scores), x='Display', y='Score', markers=True, text='Score', range_y=[0, 140])
                                        fig_p.update_traces(textposition="top center", line=dict(color='#FF8200', width=3), marker=dict(size=8, color='#4895DB', line=dict(width=1, color='white')))
                                        fig_p.update_layout(height=200, margin=dict(l=15, r=15, t=30, b=10), template="simple_white", xaxis=dict(type='category', title=None), yaxis=dict(visible=False))
                                        st.plotly_chart(fig_p, use_container_width=True, key=f"team_card_{name}_{sel_week}_t4")

            elif sel_daily_tab == "CMJ Performance":
                cmj_view_modes = ["Individual Athlete", "Asymmetry & Favoring", "Team CMJ Summary"]
                
                if "cmj_view_mode_subtab" not in st.session_state or st.session_state.cmj_view_mode_subtab not in cmj_view_modes:
                    st.session_state.cmj_view_mode_subtab = cmj_view_modes[0]
                    
                sel_cmj_mode = st.radio("CMJ View Mode", cmj_view_modes, key="cmj_view_mode_subtab", horizontal=True, label_visibility="collapsed")

                # =========================================================================
                # --- ASYMMETRY HELPER FUNCTIONS ------------------------------------------
                # =========================================================================
                def parse_asym_val(raw_val):
                    if pd.isna(raw_val):
                        return 0.0, "Balanced"
                    s = str(raw_val).strip().upper()
                    num_part = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", s)
                    val = float(num_part[0]) if num_part else 0.0
                    if "L" in s:
                        return -abs(val), "Left"
                    elif "R" in s:
                        return abs(val), "Right"
                    else:
                        return val, "Right" if val > 0 else ("Left" if val < 0 else "Balanced")

                def resolve_col_val(row, primary_col, alt_cols=[]):
                    candidates = [primary_col] + alt_cols
                    for col in candidates:
                        if col in row and pd.notna(row[col]) and str(row[col]).strip() != "":
                            return row[col]
                    row_keys_norm = {re.sub(r'[^a-zA-Z0-9]', '', str(k)).lower(): k for k in row.index}
                    for col in candidates:
                        norm = re.sub(r'[^a-zA-Z0-9]', '', str(col)).lower()
                        if norm in row_keys_norm:
                            matched_key = row_keys_norm[norm]
                            if pd.notna(row[matched_key]) and str(row[matched_key]).strip() != "":
                                return row[matched_key]
                    return None

                # -------------------------------------------------------------------------
                # --- 1. INDIVIDUAL ATHLETE PROFILE --------------------------------------
                # -------------------------------------------------------------------------
                if sel_cmj_mode == "Individual Athlete":
                    c_cmj_ath, c_cmj_date = st.columns([2, 2])
                    with c_cmj_ath: sel_cmj_ath = st.selectbox("Select Athlete", master_athlete_list, key="cmj_dash_ath_sel")
                    ath_cmj_all = raw_cmj_df[raw_cmj_df['Name'] == sel_cmj_ath].sort_values('Test Date')
                    
                    if ath_cmj_all.empty:
                        st.info(f"No CMJ records found for {sel_cmj_ath}.")
                    else:
                        valid_dates = ath_cmj_all['Test Date'].dropna().drop_duplicates().sort_values(ascending=False).dt.strftime('%m/%d/%y').tolist()
                        with c_cmj_date: sel_test_date_str = st.selectbox("Test Date", valid_dates, index=0, key="cmj_dash_date_sel")

                        cur_idx_list = ath_cmj_all[ath_cmj_all['Test Date'].dt.strftime('%m/%d/%y') == sel_test_date_str].index.tolist()
                        cur_test_row = ath_cmj_all.loc[cur_idx_list[-1]]
                        
                        base_test_row = ath_cmj_all.iloc[0]
                        all_indices = list(ath_cmj_all.index)
                        if cur_idx_list[-1] in all_indices:
                            cur_pos = all_indices.index(cur_idx_list[-1])
                            prev_test_row = ath_cmj_all.iloc[max(0, cur_pos - 1)]
                        else:
                            prev_test_row = cur_test_row

                        meta_lookup = full_df_unfiltered[full_df_unfiltered['Name'] == sel_cmj_ath]
                        photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                        pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"

                        cmj_metric_defs = [
                            {"label": "Jump Height", "col": cmj_col, "fmt": "{:.1f}"},
                            {"label": "Jump Momentum", "col": "Jump Momentum", "alt_col": "Take-off Momentum [kg m/s]", "fmt": "{:.1f}"},
                            {"label": "Peak Velocity", "col": "Concentric Peak Velocity [m/s]", "fmt": "{:.2f}"},
                            {"label": "Mean Con Force", "col": "Concentric Mean Force [N]", "fmt": "{:.0f}"},
                            {"label": "Force @ 0 Velocity", "col": "Force at Zero Velocity [N]", "fmt": "{:.0f}"},
                            {"label": "Positive Impulse", "col": "Positive Impulse [N s]", "fmt": "{:.1f}"},
                            {"label": "P1 Con Impulse", "col": "P1 Concentric Impulse [N s]", "fmt": "{:.1f}"},
                            {"label": "P2 Con Impulse", "col": "P2 Concentric Impulse [N s]", "fmt": "{:.1f}"},
                            {"label": "P2:P1 Impulse Ratio", "col": "P2 Concentric Impulse:P1 Concentric Impulse", "fmt": "{:.2f}"}
                        ]

                        raw_readiness_avg = compute_excel_readiness_score(cur_test_row, prev_test_row)
                        display_score = int(round(raw_readiness_avg))

                        top_col1, top_col2, top_col3 = st.columns([1.2, 2.2, 1.6])
                        with top_col1:
                            ath_card_html = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:18px; text-align:center; padding:8px 10px; border-radius:6px 6px 0 0;">{sel_cmj_ath}</div><div style="border:1px solid #E2E8F0; border-top:none; border-radius:0 0 6px 6px; padding:16px; background:white; display:flex; align-items:center; gap:16px;"><img src="{photo_val}" style="width:95px; height:95px; border-radius:8px; object-fit:contain; border:2px solid #FF8200;"><div style="font-size:14px; line-height:1.8; color:#1D1D1F;"><b>Position:</b> {pos_val}</div></div>"""
                            st.markdown(ath_card_html, unsafe_allow_html=True)
                            comp_factor = st.selectbox("Comparison Factor", ["Individual", "Team", "Position"], key="cmj_dash_comp_sel")

                        with top_col2:
                            table_rows_str = ""
                            for m_info in cmj_metric_defs:
                                lbl = m_info["label"]
                                col_name = m_info["col"] if m_info["col"] in cur_test_row else m_info.get("alt_col", m_info["col"])
                                fmt = m_info["fmt"]
                                c_val = float(cur_test_row.get(col_name, 0.0)) if col_name in cur_test_row and pd.notna(cur_test_row.get(col_name)) else 0.0
                                b_val = float(base_test_row.get(col_name, 0.0)) if col_name in base_test_row and pd.notna(base_test_row.get(col_name)) else 0.0
                                diff = ((c_val - b_val) / b_val * 100) if b_val > 0 else 0.0
                                pct_color = "#137333" if diff >= 0 else "#D93025"
                                table_rows_str += f"""<tr><td style="text-align:left !important; padding-left:12px; font-weight:600;">{lbl}</td><td style="color:#64748B;">{fmt.format(b_val)}</td><td style="font-weight:800; background:#F0F7FF; border: 1px solid #3B82F6;">{fmt.format(c_val)}</td><td style="font-weight:800; color:{pct_color};">{diff:+.0f}%</td></tr>"""
                            
                            full_table_html = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:14px; text-align:center; padding:6px; border-radius:6px 6px 0 0;">Countermovement Jump Performance</div><table class="scout-table" style="width:100%; border:1px solid #E2E8F0; border-top:none; background:white; border-collapse:collapse; margin-bottom:0;"><thead><tr style="background:#F8FAFC; color:#64748B; font-size:11px;"><th style="text-align:left !important; padding:6px 12px;">Metric</th><th style="padding:6px;">Baseline (Overall)</th><th style="padding:6px; background:#EBF5FF; color:#1E40AF;">Current</th><th style="padding:6px;">% Change</th></tr></thead><tbody>{table_rows_str}</tbody></table>"""
                            st.markdown(full_table_html, unsafe_allow_html=True)

                        with top_col3:
                            gauge_header = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:14px; text-align:center; padding:6px; border-radius:6px 6px 0 0;">Wellness Score<br><span style="font-size:11px; font-weight:600;">{sel_test_date_str}</span></div>"""
                            st.markdown(gauge_header, unsafe_allow_html=True)
                            fig_gauge = create_wellness_gauge(display_score, height=230)
                            st.plotly_chart(fig_gauge, use_container_width=True, config=LOCKED_CONFIG, key="cmj_wellness_gauge_ind")

                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f'<div class="section-header">Countermovement Jump Performance Standards </div>', unsafe_allow_html=True)
                        chart_col, legend_col = st.columns([4.2, 1.1])

                        with chart_col:
                            bar_metrics_excel = [
                                {"name": "Jump Height", "col": cmj_col, "invert": False},
                                {"name": "Jump Momentum", "col": "Jump Momentum", "alt_col": "Take-off Momentum [kg m/s]", "invert": False},
                                {"name": "Peak Velocity", "col": "Concentric Peak Velocity [m/s]", "invert": False},
                                {"name": "Mean Con Force", "col": "Relative Mean Con Force", "alt_col": "Concentric Mean Force [N]", "invert": False},
                                {"name": "Force @ 0 Velocity", "col": "Relative Force @ 0 Velo", "alt_col": "Force at Zero Velocity [N]", "invert": False},
                                {"name": "Positive Impulse", "col": "Positive Impulse [N s]", "invert": False},
                                {"name": "P1 Con Impulse", "col": "P1 Concentric Impulse [N s]", "invert": False},
                                {"name": "P2 Con Impulse", "col": "P2 Concentric Impulse [N s]", "invert": False},
                                {"name": "CM Depth", "col": "Adjusted CMD", "alt_col": "Countermovement Depth [cm]", "invert": False},
                                {"name": "Time to Takeoff", "col": "Contraction Time [ms]", "alt_col": "Time to Takeoff [s]", "invert": True}
                            ]

                            if comp_factor == "Individual":
                                ref_pool_df = raw_cmj_df[raw_cmj_df['Name'] == sel_cmj_ath]
                                title_prefix = "Individual"
                            elif comp_factor == "Position":
                                pos_athletes = full_df_unfiltered[full_df_unfiltered['Position'] == pos_val]['Name'].unique()
                                ref_pool_df = raw_cmj_df[raw_cmj_df['Name'].isin(pos_athletes)]
                                if ref_pool_df.empty: ref_pool_df = raw_cmj_df
                                title_prefix = "Position"
                            else:
                                ref_pool_df = raw_cmj_df
                                title_prefix = "Team"

                            t_scores = []
                            x_labels = []
                            for bm in bar_metrics_excel:
                                x_labels.append(bm["name"])
                                cname = bm["col"] if bm["col"] in cur_test_row else bm.get("alt_col", bm["col"])
                                ath_v = abs(float(cur_test_row.get(cname, 0.0))) if cname in cur_test_row and pd.notna(cur_test_row.get(cname)) else 0.0
                                if cname in ref_pool_df.columns and len(ref_pool_df[cname].dropna()) > 1:
                                    valid_series = ref_pool_df[cname].dropna().abs()
                                    m_mean = valid_series.mean()
                                    m_std = valid_series.std(ddof=1)
                                    if m_std > 0:
                                        z_val = -1.0 * ((ath_v - m_mean) / m_std) if bm["invert"] else (ath_v - m_mean) / m_std
                                        t_val = 50.0 + (z_val * 10.0)
                                        t_scores.append(round(min(100.0, max(0.0, t_val)), 1))
                                    else: t_scores.append(50.0)
                                else: t_scores.append(50.0)

                            fig_bands = go.Figure()
                            bands = [
                                {"y0": 0, "y1": 20, "color": "#A00000"},
                                {"y0": 20, "y1": 30, "color": "#E60000"},
                                {"y0": 30, "y1": 40, "color": "#F05656"},
                                {"y0": 40, "y1": 45, "color": "#F8A2A2"},
                                {"y0": 45, "y1": 55, "color": "#FFFFFF"},
                                {"y0": 55, "y1": 60, "color": "#C3E8A8"},
                                {"y0": 60, "y1": 70, "color": "#81D350"},
                                {"y0": 70, "y1": 80, "color": "#33A338"},
                                {"y0": 80, "y1": 100, "color": "#1C7426"}
                            ]
                            for b in bands: fig_bands.add_hrect(y0=b["y0"], y1=b["y1"], fillcolor=b["color"], line_width=0, opacity=1.0, layer="below")
                            fig_bands.add_trace(go.Bar(x=x_labels, y=t_scores, marker=dict(color='#3A3D40', line=dict(color='#1A1C1E', width=1.5)), width=0.42, text=[f"<b>{val:.1f}</b>" for val in t_scores], textposition='inside', insidetextanchor='middle', textfont=dict(color='white', size=12), cliponaxis=False))

                            category_boxes = [
                                {"x0": 0.55, "x1": 2.45, "text": "Speed", "bg": "#F8E2E2"},
                                {"x0": 2.55, "x1": 6.45, "text": "Strength", "bg": "#EBF3DF"},
                                {"x0": 6.55, "x1": 7.45, "text": "Power", "bg": "#D3E2F4"},
                                {"x0": 7.55, "x1": 9.45, "text": "Jump Strategy", "bg": "#E6E1F2"}
                            ]
                            for cb in category_boxes:
                                fig_bands.add_shape(type="rect", xref="x", yref="paper", x0=cb["x0"], x1=cb["x1"], y0=-0.16, y1=-0.08, fillcolor=cb["bg"], line=dict(width=0), layer="above")
                                fig_bands.add_annotation(xref="x", yref="paper", x=(cb["x0"] + cb["x1"]) / 2, y=-0.12, text=f"<b>{cb['text']}</b>", showarrow=False, font=dict(size=11, color="#111827"), align="center")

                            fig_bands.update_layout(height=450, margin=dict(l=30, r=10, t=15, b=65), plot_bgcolor='white', paper_bgcolor='white', xaxis=dict(tickangle=0, tickfont=dict(size=10.5, weight='bold', color='#111827'), showgrid=False, showline=True, linecolor='#6B7280'), yaxis=dict(range=[0, 100], dtick=10, showgrid=False, showline=True, linecolor='#6B7280', title=dict(text=f"{title_prefix} T-Score Performance Rating", font=dict(size=12, weight='bold', color='#4B5563'))), showlegend=False)
                            st.plotly_chart(fig_bands, use_container_width=True, config=LOCKED_CONFIG, key=f"cmj_standards_chart_{comp_factor}")

                        with legend_col:
                            legend_table_html = """<div style="background:#4895DB; color:white; font-weight:800; font-size:12px; text-align:center; padding:6px; border-radius:4px 4px 0 0;">Performance Bands<br><span style="font-size:10px; font-weight:600;">T-Score Rating</span></div><table style="width:100%; border-collapse:collapse; font-size:11px; text-align:center; font-weight:700;"><tr style="background:#1C7426; color:white;"><td style="padding:4px;">Excellent</td><td>> 80</td></tr><tr style="background:#33A338; color:white;"><td style="padding:4px;">Very Good</td><td>70 - 80</td></tr><tr style="background:#81D350; color:#111827;"><td style="padding:4px;">Good</td><td>60 - 70</td></tr><tr style="background:#C3E8A8; color:#111827;"><td style="padding:4px;">Above Avg.</td><td>55 - 60</td></tr><tr style="background:#FFFFFF; color:#111827; border-top:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0;"><td style="padding:4px;">Average</td><td>45 - 55</td></tr><tr style="background:#F8A2A2; color:#111827;"><td style="padding:4px;">Below Avg.</td><td>40 - 45</td></tr><tr style="background:#F05656; color:white;"><td style="padding:4px;">Poor</td><td>30 - 40</td></tr><tr style="background:#E60000; color:white;"><td style="padding:4px;">Very Poor</td><td>20 - 30</td></tr><tr style="background:#A00000; color:white;"><td style="padding:4px;">Extremely Poor</td><td>< 20</td></tr></table>"""
                            st.markdown(legend_table_html, unsafe_allow_html=True)

                # -------------------------------------------------------------------------
                # --- 2. ASYMMETRY & FAVORING ANALYSIS ------------------------------------
                # -------------------------------------------------------------------------
                elif sel_cmj_mode == "Asymmetry & Favoring":
                    st.markdown('<div class="section-header">Bilateral CMJ Asymmetry & Performance Standards</div>', unsafe_allow_html=True)
                    
                    asym_c1, asym_c2, asym_c3 = st.columns([1.5, 1.5, 1.2])
                    with asym_c1:
                        sel_asym_ath = st.selectbox("Select Athlete", master_athlete_list, key="cmj_asym_ath_sel")
                    
                    ath_cmj_asym = raw_cmj_df[raw_cmj_df['Name'] == sel_asym_ath].sort_values('Test Date')
                    
                    if ath_cmj_asym.empty:
                        st.info(f"No CMJ test logs found for {sel_asym_ath}.")
                    else:
                        asym_valid_dates = ath_cmj_asym['Test Date'].dropna().drop_duplicates().sort_values(ascending=False).dt.strftime('%m/%d/%y').tolist()
                        with asym_c2:
                            sel_asym_date_str = st.selectbox("Select Test Date", asym_valid_dates, index=0, key="cmj_asym_date_sel")
                        with asym_c3:
                            known_injury_side = st.selectbox("Known Injured / Re-hab Side", ["None / Unknown", "Left", "Right"], key="cmj_asym_injured_side")

                        cur_asym_idx = ath_cmj_asym[ath_cmj_asym['Test Date'].dt.strftime('%m/%d/%y') == sel_asym_date_str].index[-1]
                        cur_asym_row = ath_cmj_asym.loc[cur_asym_idx]

                        bw_kg = float(cur_asym_row.get("BW [KG]", cur_asym_row.get("Body Weight [kg]", 80.0)))
                        bw_n = bw_kg * 9.81

                        asym_metric_list = [
                            {
                                "label": "Eccentric Braking RFD",
                                "raw_val_col": "Eccentric Braking RFD [N/s]",
                                "alt_raw": ["Eccentric Braking RFD", "Braking RFD [N/s]", "Braking RFD"],
                                "asym_col": "Eccentric Braking RFD % (Asym) (%)",
                                "alt_asym": ["Eccentric Braking RFD (Asym) (%)", "Eccentric Braking RFD Asymmetry (%)", "Braking RFD (Asym) (%)"],
                                "phase": "Eccentric Braking RFD",
                                "unit": "N/s",
                                "fmt": "{:.0f}",
                                "target_min": 4000.0,
                                "target_max": 8000.0,
                                "target_label": "4,000 - 8,000 N/s",
                                "desc": "Rate of force development as the athlete decelerates downward."
                            },
                            {
                                "label": "Eccentric Deceleration RFD",
                                "raw_val_col": "Eccentric Deceleration RFD [N/s]",
                                "alt_raw": ["Eccentric Deceleration RFD", "Eccentric RFD [N/s]", "Eccentric RFD"],
                                "asym_col": "Eccentric Deceleration RFD % (Asym) (%)",
                                "alt_asym": ["Eccentric Deceleration RFD (Asym) (%)", "Eccentric RFD % (Asym) (%)", "Eccentric RFD (Asym) (%)"],
                                "phase": "Eccentric Deceleration RFD",
                                "unit": "N/s",
                                "fmt": "{:.0f}",
                                "target_min": 4500.0,
                                "target_max": 8500.0,
                                "target_label": "4,500 - 8,500 N/s",
                                "desc": "Braking rate immediately prior to turnaround into upward drive."
                            },
                            {
                                "label": "Force at Zero Velocity",
                                "raw_val_col": "Force at Zero Velocity [N]",
                                "alt_raw": ["Force at Zero Velocity", "Force @ 0 Velo", "Relative Force @ 0 Velo"],
                                "asym_col": "Force at Zero Velocity % (Asym) (%)",
                                "alt_asym": ["Force at Zero Velocity (Asym) (%)", "Force at Zero Velocity Asymmetry (%)", "Force @ 0 Velo (Asym) (%)"],
                                "phase": "Force at Zero Velocity",
                                "unit": "N",
                                "fmt": "{:.0f}",
                                "target_min": round(bw_n * 2.2, 0),
                                "target_max": round(bw_n * 2.6, 0),
                                "target_label": f"{bw_n*2.2:.0f} - {bw_n*2.6:.0f} N (2.2-2.6x BW)",
                                "desc": "Vertical load absorbed at the absolute bottom of the dip (v = 0)."
                            },
                            {
                                "label": "Concentric Mean Force",
                                "raw_val_col": "Concentric Mean Force [N]",
                                "alt_raw": ["Concentric Mean Force", "Relative Mean Con Force", "Mean Concentric Force [N]"],
                                "asym_col": "Concentric Mean Force % (Asym) (%)",
                                "alt_asym": ["Concentric Mean Force (Asym) (%)", "Concentric Mean Force Asymmetry (%)"],
                                "phase": "Concentric Mean Force",
                                "unit": "N",
                                "fmt": "{:.0f}",
                                "target_min": round(bw_n * 1.6, 0),
                                "target_max": round(bw_n * 1.9, 0),
                                "target_label": f"{bw_n*1.6:.0f} - {bw_n*1.9:.0f} N (1.6-1.9x BW)",
                                "desc": "Average upward thrust produced across the propulsion phase."
                            },
                            {
                                "label": "Takeoff Peak Force",
                                "raw_val_col": "Takeoff Peak Force [N]",
                                "alt_raw": ["Takeoff Peak Force", "Take-off Peak Force [N]", "Take-off Peak Force", "Peak Takeoff Force [N]", "Peak Takeoff Force", "Takeoff Force [N]", "Takeoff Force", "Concentric Peak Force [N]", "Concentric Peak Force"],
                                "asym_col": "Takeoff Peak Force % (Asym) (%)",
                                "alt_asym": ["Takeoff Peak Force (Asym) (%)", "Takeoff Peak Force [N] (Asym) (%)", "Take-off Peak Force % (Asym) (%)", "Take-off Peak Force (Asym) (%)", "Peak Takeoff Force % (Asym) (%)", "Takeoff Peak Force Asymmetry (%)", "Concentric Peak Force % (Asym) (%)"],
                                "phase": "Takeoff Peak Force",
                                "unit": "N",
                                "fmt": "{:.0f}",
                                "target_min": round(bw_n * 2.0, 0),
                                "target_max": round(bw_n * 2.5, 0),
                                "target_label": f"{bw_n*2.0:.0f} - {bw_n*2.5:.0f} N (2.0-2.5x BW)",
                                "desc": "Maximum explosive force spike generated before leaving the plates."
                            }
                        ]

                        parsed_records = []
                        for item in asym_metric_list:
                            raw_val_found = resolve_col_val(cur_asym_row, item["raw_val_col"], item.get("alt_raw", []))
                            raw_num_val = None
                            if raw_val_found is not None:
                                try:
                                    cleaned_num = float(re.sub(r'[^0-9.]', '', str(raw_val_found)))
                                    if cleaned_num > 0:
                                        raw_num_val = cleaned_num
                                except:
                                    raw_num_val = None

                            if raw_num_val is not None and raw_num_val > 0:
                                if raw_num_val >= item["target_min"]:
                                    out_status = "Optimal" if raw_num_val <= item["target_max"] * 1.25 else "Elite"
                                    out_color = "#137333"
                                    out_bg = "#E6F4EA"
                                else:
                                    out_status = "Below Norm"
                                    out_color = "#D93025"
                                    out_bg = "#FCE8E6"
                            else:
                                out_status = "No Data"
                                out_color = "#64748B"
                                out_bg = "#F1F5F9"

                            raw_asym_found = resolve_col_val(cur_asym_row, item["asym_col"], item.get("alt_asym", []))
                            parsed_signed_val, side_favored = parse_asym_val(raw_asym_found)
                            
                            asym_status = "Symmetric (<10%)"
                            if abs(parsed_signed_val) >= 15.0:
                                asym_status = f"High Bias ({abs(parsed_signed_val):.1f}%)"
                            elif abs(parsed_signed_val) >= 10.0:
                                asym_status = f"Moderate Bias ({abs(parsed_signed_val):.1f}%)"
                            
                            parsed_records.append({
                                "Phase / Metric": item["label"],
                                "Phase": item["phase"],
                                "Description": item["desc"],
                                "Absolute_Val": raw_num_val,
                                "Formatted_Val": f"{item['fmt'].format(raw_num_val)} {item['unit']}" if raw_num_val is not None else "—",
                                "Target_Range": item["target_label"],
                                "Output_Status": out_status,
                                "Output_Color": out_color,
                                "Output_Bg": out_bg,
                                "Signed_Val": parsed_signed_val,
                                "Magnitude": abs(parsed_signed_val),
                                "Favored": side_favored,
                                "Raw_Asym": str(raw_asym_found) if pd.notna(raw_asym_found) and str(raw_asym_found).strip() != "" else "0.0",
                                "Asym_Status": asym_status
                            })

                        asym_table_df = pd.DataFrame(parsed_records)

                        kpi_a1, kpi_a2, kpi_a3, kpi_a4 = st.columns(4)
                        mean_mag = asym_table_df["Magnitude"].mean()
                        max_imbalance_row = asym_table_df.loc[asym_table_df["Magnitude"].idxmax()]
                        
                        r_count = sum(1 for r in parsed_records if r["Favored"] == "Right" and r["Magnitude"] >= 5.0)
                        l_count = sum(1 for r in parsed_records if r["Favored"] == "Left" and r["Magnitude"] >= 5.0)
                        
                        primary_favoring = "Balanced"
                        if r_count > l_count:
                            primary_favoring = "Right Leg (Unloading Left)"
                        elif l_count > r_count:
                            primary_favoring = "Left Leg (Unloading Right)"

                        meets_count = sum(1 for r in parsed_records if r["Output_Status"] in ["Optimal", "Elite"])

                        kpi_a1.metric("Recorded Body Weight", f"{bw_kg:.1f} kg", help="Used to normalize force thresholds (N/kg).")
                        kpi_a2.metric("Output Standards Met", f"{meets_count} / {len(parsed_records)}", help="Number of force/RFD metrics meeting or exceeding collegiate benchmarks.")
                        kpi_a3.metric("Dominant Favoring", primary_favoring, help="Limb consistently generating higher force across jump phases.")
                        kpi_a4.metric("Peak Phase Imbalance", f"{max_imbalance_row['Phase']} ({max_imbalance_row['Magnitude']:.1f}% {max_imbalance_row['Favored'][0]})")

                        if known_injury_side != "None / Unknown":
                            unloaded_side = "Left" if "Right" in primary_favoring else ("Right" if "Left" in primary_favoring else "None")
                            if unloaded_side == known_injury_side:
                                diag_color = "#D93025"
                                diag_bg = "#FCE8E6"
                                diag_text = f"<b>Compensatory Unloading Detected:</b> Athlete is meeting output standards overall but heavily offloading the injured <b>{known_injury_side}</b> side onto the healthy <b>{primary_favoring.split()[0]}</b> limb."
                            elif unloaded_side != "None":
                                diag_color = "#D97706"
                                diag_bg = "#FEF3C7"
                                diag_text = f"<b>Observation:</b> Athlete is favoring the injured side (<b>{known_injury_side}</b>). Verify test mechanics or limb dominance compensation."
                            else:
                                diag_color = "#137333"
                                diag_bg = "#E6F4EA"
                                diag_text = f"<b>Symmetric Strategy:</b> Jump mechanics show balanced loading across both limbs."
                            
                            st.markdown(f'<div style="background:{diag_bg}; border-left:5px solid {diag_color}; padding:10px 14px; border-radius:6px; margin: 15px 0; font-size:13px; color:#111827;">{diag_text}</div>', unsafe_allow_html=True)

                        fig_asym = go.Figure()
                        fig_asym.add_vrect(
                            x0=-10, x1=10, 
                            fillcolor="#E2E8F0", opacity=0.4, line_width=0, layer="below", 
                            annotation_text="Symmetric Zone (±10%)", annotation_position="top left", 
                            annotation_font_size=10, annotation_font_color="#64748B"
                        )
                        
                        bar_colors = ['#FF8200' if v > 0 else '#4895DB' for v in asym_table_df["Signed_Val"]]
                        
                        fig_asym.add_trace(go.Bar(
                            y=asym_table_df["Phase / Metric"],
                            x=asym_table_df["Signed_Val"],
                            orientation='h',
                            marker=dict(color=bar_colors, line=dict(color='#1E293B', width=1)),
                            text=[f"<b>{r['Magnitude']:.1f}% {r['Favored'][0]}</b>" if r['Magnitude'] > 0 else "0%" for _, r in asym_table_df.iterrows()],
                            textposition='outside',
                            cliponaxis=False
                        ))

                        max_range = max(30.0, asym_table_df["Magnitude"].max() * 1.35)
                        fig_asym.update_layout(
                            height=320,
                            template="simple_white",
                            title=dict(text="<b>Current Test: Limb Loading Bias (← Left Favored | Right Favored →)</b>", font=dict(size=13, color="#1D1D1F")),
                            margin=dict(l=20, r=40, t=40, b=20),
                            xaxis=dict(range=[-max_range, max_range], ticksuffix="%", zeroline=True, zerolinewidth=2, zerolinecolor="#111827"),
                            yaxis=dict(autorange="reversed")
                        )
                        st.plotly_chart(fig_asym, use_container_width=True, config=LOCKED_CONFIG, key="cmj_asym_horizontal_bar")

                        # =========================================================================
                        # --- OPTION 1: LONGITUDINAL LIMB FAVORING HEATMAP ------------------------
                        # =========================================================================
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f"#### Longitudinal Limb Favoring Heatmap: {sel_asym_ath}")
                        
                        trend_records = []
                        for _, test_row in ath_cmj_asym.iterrows():
                            t_date = test_row['Test Date']
                            t_date_str = pd.to_datetime(t_date).strftime('%m/%d/%y')
                            
                            for item in asym_metric_list:
                                raw_asym_val = resolve_col_val(test_row, item["asym_col"], item.get("alt_asym", []))
                                signed_v, fav_side = parse_asym_val(raw_asym_val)
                                trend_records.append({
                                    "Date": t_date,
                                    "Date_Str": t_date_str,
                                    "Metric": item["label"],
                                    "Signed_Asymmetry": signed_v,
                                    "Magnitude": abs(signed_v),
                                    "Favored": fav_side
                                })
                        
                        trend_df = pd.DataFrame(trend_records).sort_values("Date")
                        
                        if not trend_df.empty:
                            metric_order = [m["label"] for m in asym_metric_list]
                            pivot_asym = trend_df.pivot(index="Metric", columns="Date_Str", values="Signed_Asymmetry").reindex(metric_order).fillna(0.0)
                            
                            # Custom Diverging Color Scale: Tennessee Blue (Left) -> Slate (Balanced) -> Tennessee Orange (Right)
                            diverging_scale = [
                                [0.00, "#2563EB"],  # Deep Blue (Heavy Left)
                                [0.30, "#93C5FD"],  # Light Blue
                                [0.45, "#F1F5F9"],  # Balanced (<10%)
                                [0.55, "#F1F5F9"],  # Balanced (<10%)
                                [0.70, "#FDBA74"],  # Light Orange
                                [1.00, "#FF8200"]   # Tennessee Orange (Heavy Right)
                            ]
                            
                            text_annotations = []
                            for row_vals in pivot_asym.values:
                                row_text = []
                                for val in row_vals:
                                    if abs(val) >= 0.1:
                                        side_char = "R" if val > 0 else "L"
                                        row_text.append(f"{abs(val):.1f}% {side_char}")
                                    else:
                                        row_text.append("0%")
                                text_annotations.append(row_text)

                            fig_heat = go.Figure(data=go.Heatmap(
                                z=pivot_asym.values,
                                x=pivot_asym.columns,
                                y=pivot_asym.index,
                                colorscale=diverging_scale,
                                zmid=0,
                                zmin=-25,
                                zmax=25,
                                text=text_annotations,
                                texttemplate="<b>%{text}</b>",
                                textfont=dict(size=11, color="#0F172A"),
                                xgap=3,
                                ygap=3,
                                colorbar=dict(
                                    title=dict(text="Limb Bias", font=dict(size=11, color="#64748B")),
                                    tickvals=[-20, -10, 0, 10, 20],
                                    ticktext=["Left (20%+)", "Left (10%)", "Balanced", "Right (10%)", "Right (20%+)"],
                                    len=0.9
                                )
                            ))

                            fig_heat.update_layout(
                                height=270,
                                margin=dict(l=20, r=20, t=10, b=25),
                                xaxis=dict(title=None, showgrid=False, tickfont=dict(size=11, color="#1D1D1F")),
                                yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=11, weight="bold", color="#1D1D1F")),
                                plot_bgcolor="white",
                                paper_bgcolor="white"
                            )
                            st.plotly_chart(fig_heat, use_container_width=True, config=LOCKED_CONFIG, key=f"asym_heatmap_{sel_asym_ath}")

                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("#### Combined Metric Values, Standards & Limb Asymmetry")
                        unified_tbl_html = """<table class="scout-table" style="width:100%; border:1px solid #E2E8F0; background:white;">
                            <thead>
                                <tr style="background:#4895DB; color:white;">
                                    <th style="text-align:left !important; padding-left:14px; width:30%;">Phase Metric</th>
                                    <th style="width:14%;">Actual Total</th>
                                    <th style="width:18%;">D1 Standard Target</th>
                                    <th style="width:12%;">Output Standard</th>
                                    <th style="width:13%;">Favored Limb</th>
                                    <th style="width:13%;">Asymmetry %</th>
                                </tr>
                            </thead>
                            <tbody>"""
                        for _, row in asym_table_df.iterrows():
                            asym_badge_color = "#137333" if "Symmetric" in row["Asym_Status"] else ("#D97706" if "Moderate" in row["Asym_Status"] else "#D93025")
                            asym_badge_bg = "#E6F4EA" if "Symmetric" in row["Asym_Status"] else ("#FEF3C7" if "Moderate" in row["Asym_Status"] else "#FCE8E6")
                            favored_text_color = '#FF8200' if row['Favored'] == 'Right' else ('#4895DB' if row['Favored'] == 'Left' else '#64748B')
                            
                            unified_tbl_html += f"""<tr>
                                <td style="text-align:left !important; padding-left:14px; padding-top:8px; padding-bottom:8px;">
                                    <div style="font-weight:800; font-size:12px; color:#111827;">{row['Phase / Metric']}</div>
                                    <div style="font-size:10px; color:#64748B; line-height:1.2;">{row['Description']}</div>
                                </td>
                                <td style="font-weight:800; font-size:13px; color:#0F172A;">{row['Formatted_Val']}</td>
                                <td style="color:#64748B; font-weight:600; font-size:11px;">{row['Target_Range']}</td>
                                <td><span style="background:{row['Output_Bg']}; color:{row['Output_Color']}; padding:3px 8px; border-radius:10px; font-weight:700; font-size:11px;">{row['Output_Status']}</span></td>
                                <td style="font-weight:800; color:{favored_text_color};">{row['Favored']}</td>
                                <td><span style="background:{asym_badge_bg}; color:{asym_badge_color}; padding:3px 8px; border-radius:10px; font-weight:800; font-size:11px;">{row['Raw_Asym']}</span></td>
                            </tr>"""
                        unified_tbl_html += "</tbody></table>"
                        st.markdown(unified_tbl_html, unsafe_allow_html=True)

                # -------------------------------------------------------------------------
                # --- 3. TEAM CMJ SUMMARY ------------------------------------------------
                # -------------------------------------------------------------------------
                elif sel_cmj_mode == "Team CMJ Summary":
                    st.markdown("### Team Wellness Score Overview")
                    team_cmj_dates = raw_cmj_df['Test Date'].dropna().drop_duplicates().sort_values(ascending=False).dt.strftime('%m/%d/%y').tolist()
                    
                    c_sum_d1, c_sum_d2 = st.columns([1.5, 2])
                    with c_sum_d1: sel_team_cmj_date = st.selectbox("Evaluation Test Date", team_cmj_dates, index=0, key="team_cmj_eval_date")
                    with c_sum_d2: team_pos_f = st.selectbox("Filter by Position", ["All Positions"] + sorted([p for p in full_df_unfiltered['Position'].unique() if p != "N/A"]), key="team_cmj_pos_filter")

                    team_cmj_rows = []
                    for ath_name in sorted(raw_cmj_df['Name'].unique()):
                        ath_sub_cmj = raw_cmj_df[raw_cmj_df['Name'] == ath_name].sort_values('Test Date')
                        if ath_sub_cmj.empty: continue
                        
                        meta_row = full_df_unfiltered[full_df_unfiltered['Name'] == ath_name]
                        pos_str = meta_row['Position'].iloc[0] if not meta_row.empty else "N/A"
                        photo_url = meta_row['PhotoURL'].iloc[0] if not meta_row.empty else "https://www.w3schools.com/howto/img_avatar.png"
                        if team_pos_f != "All Positions" and pos_str != team_pos_f: continue
                            
                        ath_date_match = ath_sub_cmj[ath_sub_cmj['Test Date'].dt.strftime('%m/%d/%y') == sel_team_cmj_date]
                        if ath_date_match.empty: continue
                            
                        target_row = ath_date_match.iloc[-1]
                        
                        all_indices = list(ath_sub_cmj.index)
                        if target_row.name in all_indices:
                            cur_pos = all_indices.index(target_row.name)
                            prev_row = ath_sub_cmj.iloc[max(0, cur_pos - 1)]
                        else: 
                            prev_row = target_row
                        
                        readiness_pct = int(round(compute_excel_readiness_score(target_row, prev_row)))
                        z_color = get_readiness_color(readiness_pct)
                        team_cmj_rows.append({"Athlete": ath_name, "PhotoURL": photo_url, "Position": pos_str, "Readiness %": readiness_pct, "Status_Color": z_color})

                    if team_cmj_rows:
                        cmj_team_df = pd.DataFrame(team_cmj_rows).sort_values("Readiness %", ascending=False)
                        c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
                        avg_team_readiness = cmj_team_df['Readiness %'].mean()
                        peak_count = sum(1 for r in team_cmj_rows if r['Readiness %'] >= 90)
                        fatigue_count = sum(1 for r in team_cmj_rows if r['Readiness %'] < 80)
                        
                        c_kpi1.metric("Athletes Evaluated", len(team_cmj_rows))
                        c_kpi2.metric("Team Mean Wellness", f"{avg_team_readiness:.1f}%")
                        c_kpi3.metric("Optimal (>=90%)", peak_count)
                        c_kpi4.metric("Fatigued (<80%)", fatigue_count)

                        team_tbl_html = """<table class="scout-table" style="width:100%; border:1px solid #E2E8F0; background:white; margin-top:15px;"><thead><tr style="background:#4895DB; color:white;"><th style="width:60px;">Athlete</th><th style="text-align:left !important; padding-left:15px;">Name</th><th>Position</th><th>Wellness Score</th></tr></thead><tbody>"""
                        for _, row in cmj_team_df.iterrows():
                            team_tbl_html += f"""<tr>
                                <td style="padding:6px;"><img src="{row['PhotoURL']}" style="width:38px; height:38px; border-radius:50%; object-fit:contain; border:2px solid #FF8200;"></td>
                                <td style="text-align:left !important; font-weight:800; padding-left:15px; font-size:13px;">{row['Athlete']}</td>
                                <td style="font-weight:600; color:#4B5563;">{row['Position']}</td>
                                <td style="font-weight:900; font-size:15px; color:{row['Status_Color']};">{row['Readiness %']}%</td>
                            </tr>"""
                        team_tbl_html += "</tbody></table>"
                        st.markdown(team_tbl_html, unsafe_allow_html=True)
                    else:
                        st.info(f"No Countermovement Jump testing records logged on {sel_team_cmj_date}.")
                        
        # =========================================================================
        # --- HUB 2: MATCH PERFORMANCE --------------------------------------------
        # =========================================================================
        elif selected_hub == "Match Performance":
            match_subtabs = ["Match Summary", "Match v. Practice", "Match v. CMJ Recovery"]
            if "match_subtab_radio" not in st.session_state or st.session_state["match_subtab_radio"] not in match_subtabs:
                st.session_state["match_subtab_radio"] = match_subtabs[0]

            sel_match_tab = st.radio("Match Sub Navigation", match_subtabs, key="match_subtab_radio", horizontal=True, label_visibility="collapsed")

            if sel_match_tab == "Match Summary":
                match_t6 = match_master.copy()
                custom_colors = ['#4895DB', '#FF8200', '#515154', '#A52A2A', '#008080', '#6A1B9A', '#2E7D32']

                if st.session_state.is_printing:
                    if st.button("Back to Editor", key="back_editor_btn_t6"):
                        st.session_state.is_printing = False
                        st.rerun()
                else:
                    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                    if st.button("Prepare PDF for Printing", key="prep_print_btn_t6"):
                        st.session_state.is_printing = True
                        st.rerun()
                    
                    # Clean match session extraction sorted chronologically
                    match_list_t = match_t6.sort_values(['Date', 'Sheet_Order'])['Session_Name'].dropna().unique().tolist()
                    latest_matches = match_list_t[-3:] if len(match_list_t) >= 3 else match_list_t
                    
                    # Dynamically sync selections and auto-include new matches if not set
                    valid_defaults = [m for m in st.session_state.get("matches_state", []) if m in match_list_t]
                    if not valid_defaults:
                        valid_defaults = latest_matches

                    selected_matches = st.multiselect(
                        "Select Matches", 
                        options=match_list_t, 
                        default=valid_defaults, 
                        key="matches_summary_selector"
                    )
                    st.session_state.matches_state = selected_matches

                    pos_filter_t = st.selectbox(
                        "Filter by Position", 
                        ["All Positions"] + sorted(list(match_t6['Position'].dropna().unique())), 
                        key="pos_select_t6"
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

                if st.session_state.is_printing: 
                    st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

                selected_matches = st.session_state.get("matches_state", [])
                pos_filter_t = st.session_state.get("pos_select_t6", "All Positions")

                if selected_matches:
                    m_map = {m: custom_colors[idx % len(custom_colors)] for idx, m in enumerate(selected_matches)}
                    st.markdown('<div class="section-header">Athlete Match Performance Breakdown</div>', unsafe_allow_html=True)
                    tourney_df = match_t6[match_t6['Session_Name'].isin(selected_matches)].sort_values(['Date', 'Sheet_Order'])
                    if pos_filter_t != "All Positions": 
                        tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]

                    for name in sorted(tourney_df['Name'].unique()):
                        ad = tourney_df[tourney_df['Name'] == name]
                        try: 
                            correct_photo = df_master[df_master['Name'] == name]['PhotoURL'].iloc[0]
                        except: 
                            correct_photo = "https://www.w3schools.com/howto/img_avatar.png"
                        
                        st.markdown('<div class="player-row-container"><div class="player-divider"></div>', unsafe_allow_html=True)
                        side_cols = st.columns([1.5, 2])
                        with side_cols[0]:
                            card_start = f"""<div style="display:flex; align-items:center; gap:12px; padding:10px; background:#f8f9fa; border-bottom:2px solid #FF8200;"><img src="{correct_photo}" class="gallery-photo" style="width:65px; height:65px;"><div><p style="margin:0; font-weight:900; color:#1D1D1F; font-size:18px;">{name}</p><p style="margin:0; color:#4895DB; font-weight:700; font-size:16px;">{ad['Position'].iloc[0]}</p></div></div><div style="padding:5px;"><table class="scout-table" style="margin-bottom:0;"><thead><tr><th>Match</th><th>Jumps</th><th>Load</th><th>Efforts</th></tr></thead><tbody>"""
                            for _, r in ad.iterrows():
                                card_start += f"<tr><td style='font-weight:700; font-size:11px;'>{r['Session_Name']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.0f}</td><td>{r['Explosive Efforts']:.0f}</td></tr>"
                            card_start += f"<tr style='background:#4895DB; color:white; font-weight:900;'><td>TOTAL</td><td>{int(ad['Total Jumps'].sum())}</td><td>{ad['Player Load'].sum():.0f}</td><td>{ad['Explosive Efforts'].sum():.0f}</td></tr></tbody></table></div>"
                            st.markdown(card_start, unsafe_allow_html=True)
                        
                        with side_cols[1]:
                            fig_ath = make_subplots(specs=[[{"secondary_y": True}]])
                            for _, r in ad.iterrows():
                                fig_ath.add_trace(go.Bar(name=r['Session_Name'], x=['Total Jumps', 'Explosive Efforts'], y=[r['Total Jumps'], r['Explosive Efforts']], marker_color=m_map[r['Session_Name']], offsetgroup=r['Session_Name']), secondary_y=False)
                                fig_ath.add_trace(go.Bar(name=f"Load ({r['Session_Name']})", x=['Player Load'], y=[r['Player Load']], marker=dict(color=m_map[r['Session_Name']], opacity=0.3), showlegend=False, offsetgroup=r['Session_Name']), secondary_y=True)
                            fig_ath.update_layout(barmode='group', height=260, margin=dict(l=10, r=10, t=10, b=80), template="simple_white", font=dict(color="#333333", size=10), legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5), yaxis=dict(showgrid=False, title="Jumps / Efforts"), yaxis2=dict(showgrid=False, title="Player Load", overlaying='y', side='right'))
                            st.plotly_chart(fig_ath, use_container_width=True, config=LOCKED_CONFIG, key=f"match_breakdown_{name}")
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("Please select at least one match from the dropdown above.")

            elif sel_match_tab == "Match v. Practice":
                df_t5 = df_master.copy()
                match_t5 = match_master.copy()
                st.markdown('<div class="section-header">Season Preparation vs. Match Demands</div>', unsafe_allow_html=True)
                
                c_mode, c_sel = st.columns([1, 3])
                with c_mode: 
                    view_mode_t5 = st.radio("View Level", ["Team", "Position", "Individual"], horizontal=True, key="gp_view_mode_t5")
                
                with c_sel:
                    if view_mode_t5 == "Individual":
                        gp_p = st.selectbox("Select Athlete", sorted(df_t5['Name'].unique()), key="gp_p_vf_t5")
                        main_filtered = df_t5[df_t5['Name'] == gp_p].copy()
                        match_filtered = match_t5[match_t5['Name'] == gp_p].copy()
                    elif view_mode_t5 == "Position":
                        gp_pos = st.selectbox("Select Position Group", sorted(df_t5['Position'].unique().tolist()), key="gp_pos_vf_t5")
                        main_filtered = df_t5[df_t5['Position'] == gp_pos].copy()
                        match_filtered = match_t5[match_t5['Position'] == gp_pos].copy()
                    else:
                        main_filtered = df_t5.copy()
                        match_filtered = match_t5.copy()

                def clean_gp_data(target_df):
                    if target_df.empty: return target_df
                    target_df = target_df.rename(columns={'Total Player Load': 'Player Load', 'PlayerLoad': 'Player Load'})
                    cols_to_clean = ['Player Load', 'Explosive Efforts', 'Total Jumps', 'Jump Load', 'Duration']
                    for c in cols_to_clean:
                        if c in target_df.columns: 
                            target_df[c] = pd.to_numeric(target_df[c], errors='coerce').fillna(0)
                    if 'Duration' in target_df.columns: 
                        target_df['Duration'] = target_df['Duration'].apply(lambda x: x if x > 0 else 1)
                    return target_df

                main_filtered = clean_gp_data(main_filtered)
                match_filtered = clean_gp_data(match_filtered)
                calc_cols = ['Player Load', 'Jump Load', 'Total Jumps', 'Explosive Efforts']

                if not main_filtered.empty and not match_filtered.empty:
                    s_p_avg = main_filtered[main_filtered['Session_Type'] == 'Practice'][calc_cols + ['Duration']].mean()
                    s_m_avg = match_filtered[calc_cols + ['Duration']].mean()
                    
                    overall_html = """<table style="width:100%; border-collapse: collapse; text-align: center; margin-top: 10px;"><tr style="background-color: #31333F; color: white; font-weight: bold;"><th style="padding: 12px; border: 1px solid #ddd;">Metric (Rate/Min)</th><th style="padding: 12px; border: 1px solid #ddd;">Full Season Practice Avg</th><th style="padding: 12px; border: 1px solid #ddd;">Full Season Match Avg</th><th style="padding: 12px; border: 1px solid #ddd;">Intensity Gap (%)</th></tr>"""
                    for m in calc_cols:
                        p_rate = s_p_avg[m] / s_p_avg['Duration'] if s_p_avg['Duration'] > 0 else 0
                        m_rate = s_m_avg[m] / s_m_avg['Duration'] if s_m_avg['Duration'] > 0 else 0
                        overall_html += f"""<tr><td style="padding: 10px; border: 1px solid #ddd;"><b>{m}</b></td><td style="padding: 10px; border: 1px solid #ddd;">{p_rate:.2f}</td><td style="padding: 10px; border: 1px solid #ddd;">{m_rate:.2f}</td><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{(((m_rate - p_rate) / p_rate * 100) if p_rate > 0 else 0):+.1f}%</td></tr>"""
                    st.markdown(overall_html + "</table>", unsafe_allow_html=True)
                else:
                    st.info("Insufficient practice or match records available for comparison.")

            elif sel_match_tab == "Match v. CMJ Recovery":
                st.markdown('<div class="section-header">Match Volume Demands vs. CMJ Jump Recovery</div>', unsafe_allow_html=True)
                
                match_rec_df = match_master.copy()
                
                if not match_rec_df.empty:
                    c_m1, c_m2 = st.columns([1.5, 2])
                    with c_m1:
                        sel_match_session = st.selectbox("Select Match Session", sorted(match_rec_df['Session_Name'].unique()), key="m_v_cmj_session")
                    with c_m2:
                        sel_pos_m = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in match_rec_df['Position'].unique() if p != "N/A"]), key="m_v_cmj_pos")
                        
                    filtered_match = match_rec_df[match_rec_df['Session_Name'] == sel_match_session].copy()
                    if sel_pos_m != "All Positions":
                        filtered_match = filtered_match[filtered_match['Position'] == sel_pos_m]
                        
                    filtered_match = filtered_match.sort_values("Total Jumps", ascending=False)
                    
                    table_rows_html = ""
                    for _, row in filtered_match.iterrows():
                        ath_name = row['Name']
                        m_date = pd.to_datetime(row['Date'])
                        pos_str = row['Position']
                        
                        ath_all_cmj = raw_cmj_df[raw_cmj_df['Name'] == ath_name].sort_values('Test Date')
                        
                        # Pre-match baseline jump (latest test on or before match day)
                        pre_cmj = ath_all_cmj[ath_all_cmj['Test Date'] <= m_date]
                        pre_h = pre_cmj.iloc[-1][cmj_col] if (not pre_cmj.empty and cmj_col in pre_cmj.columns) else None
                        
                        # Post-match recovery jump (first test within 1-4 days after match day)
                        post_cmj = ath_all_cmj[(ath_all_cmj['Test Date'] > m_date) & (ath_all_cmj['Test Date'] <= m_date + timedelta(days=4))]
                        post_h = post_cmj.iloc[0][cmj_col] if (not post_cmj.empty and cmj_col in post_cmj.columns) else None
                        
                        # Delta and Badge formatting
                        if pre_h is not None and post_h is not None and pre_h > 0:
                            diff_h = ((post_h - pre_h) / pre_h) * 100
                            if diff_h >= 0:
                                delta_badge = f'<span style="background-color: #E6F4EA; color: #137333; padding: 4px 10px; border-radius: 12px; font-weight: 800; font-size: 11px;">↑ +{diff_h:.1f}%</span>'
                            else:
                                delta_badge = f'<span style="background-color: #FCE8E6; color: #D93025; padding: 4px 10px; border-radius: 12px; font-weight: 800; font-size: 11px;">↓ {diff_h:.1f}%</span>'
                        else:
                            delta_badge = '<span style="background-color: #F1F5F9; color: #64748B; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px;">No Post-Test</span>'
                            
                        pre_str = f"{pre_h:.1f} in" if pre_h is not None else "—"
                        post_str = f"{post_h:.1f} in" if post_h is not None else "—"
                        
                        table_rows_html += f"""
                        <tr>
                            <td style="font-weight: 800; text-align: left !important; padding-left: 14px;">{ath_name}</td>
                            <td style="font-weight: 600; color: #64748B;">{pos_str}</td>
                            <td style="font-weight: 800; color: #FF8200; font-size: 13px;">{int(row['Total Jumps'])}</td>
                            <td style="font-weight: 600;">{row['Player Load']:.0f}</td>
                            <td style="font-weight: 600;">{int(row['Explosive Efforts'])}</td>
                            <td style="color: #475569; font-weight: 700;">{pre_str}</td>
                            <td style="font-weight: 800; color: #0F172A;">{post_str}</td>
                            <td>{delta_badge}</td>
                        </tr>
                        """
                        
                    if table_rows_html:
                        full_table_html = f"""
                        <table class="scout-table" style="width: 100%; border: 1px solid #E2E8F0; background: white; margin-top: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                            <thead>
                                <tr style="background: #4895DB; color: white;">
                                    <th style="text-align: left !important; padding-left: 14px;">Athlete</th>
                                    <th>Position</th>
                                    <th>Match Jumps</th>
                                    <th>Match Load</th>
                                    <th>Efforts</th>
                                    <th>Pre-Match CMJ</th>
                                    <th>Post-Match CMJ</th>
                                    <th>Recovery Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_rows_html}
                            </tbody>
                        </table>
                        """
                        st.markdown(full_table_html, unsafe_allow_html=True)
                    else:
                        st.info("No athlete match records found.")
                else:
                    st.info("No match session records available in the selected season.")
                    
            


        # =========================================================================
        # --- HUB 3: PRACTICE & DRILL PLANNING ------------------------------------
        # =========================================================================
        elif selected_hub == "Practice & Drill Planning":
            plan_subtabs = ["Practice Planner", "Phase Analysis"]
            if "plan_subtab_radio" not in st.session_state or st.session_state["plan_subtab_radio"] not in plan_subtabs:
                st.session_state["plan_subtab_radio"] = plan_subtabs[0]

            sel_plan_tab = st.radio("Planning Sub Navigation", plan_subtabs, key="plan_subtab_radio", horizontal=True, label_visibility="collapsed")

            if sel_plan_tab == "Practice Planner":
                st.markdown('<div class="section-header">Practice Phase Analysis & Planner</div>', unsafe_allow_html=True)
                if phase_master is not None and not phase_master.empty:
                    working_planner = phase_master.copy()
                    time_col = 'Duration' 
                    
                    if time_col not in working_planner.columns:
                        st.error(f"Column '{time_col}' not found.")
                    else:
                        working_planner['Phase'] = working_planner['Phase'].replace(phase_map)
                        working_planner = working_planner[working_planner[time_col] > 0].dropna(subset=[time_col])
                        plan_metrics = ['Player Load', 'Total Jumps', 'Explosive Efforts', 'Estimated Distance (y)']
                        for m in plan_metrics: working_planner[f'{m}_Rate'] = working_planner[m] / working_planner[time_col]

                        s_col1, s_col2 = st.columns(2)
                        with s_col1: plan_level = st.radio("Select Planning Level", ["Team Overall", "By Position", "By Athlete"], horizontal=True, key="planner_level_refined_t9")
                        
                        if plan_level == "Team Overall":
                            planner_target_df = working_planner.copy()
                            display_label = "Team Overall"
                        elif plan_level == "By Position":
                            with s_col2: pos_choice = st.selectbox("Select Position", sorted([p for p in working_planner['Position'].unique() if pd.notna(p)]), key="planner_pos_refined_t9")
                            planner_target_df = working_planner[working_planner['Position'] == pos_choice]
                            display_label = f"Position: {pos_choice}"
                        else:
                            with s_col2: ath_choice = st.selectbox("Select Athlete", sorted(working_planner['Name'].unique()), key="planner_ath_refined_t9")
                            planner_target_df = working_planner[working_planner['Name'] == ath_choice]
                            display_label = f"Athlete: {ath_choice}"

                        selected_build = st.multiselect(f"Select Drills for {display_label}", sorted(planner_target_df['Phase'].unique()), key="planner_multi_refined_t9")
                        if selected_build:
                            build_stats = planner_target_df.groupby('Phase').agg({time_col: 'mean'}).reset_index()
                            st.write("Set planned drill durations (minutes):")
                            dur_cols = st.columns(min(len(selected_build), 4))
                            durations = {}
                            for idx, phase in enumerate(selected_build):
                                with dur_cols[idx % 4]:
                                    avg_t = build_stats[build_stats['Phase'] == phase][time_col].iloc[0]
                                    durations[phase] = st.number_input(f"{phase}", value=float(round(avg_t, 0)), step=1.0, key=f"dur_ref_{phase}_t9")

                            if plan_level != "Team Overall":
                                t_build = planner_target_df.groupby('Phase')[[f'{m}_Rate' for m in plan_metrics]].mean().reset_index().set_index('Phase').loc[selected_build].reset_index()
                                m1, m2, m3, m4, m5 = st.columns(5)
                                m1.metric("Total Time", f"{sum(durations.values()):.0f} min")
                                m2.metric("Proj. Load", f"{sum(durations[p] * t_build[t_build['Phase'] == p]['Player Load_Rate'].iloc[0] for p in selected_build):.1f}")
                                m3.metric("Proj. Jumps", f"{int(sum(durations[p] * t_build[t_build['Phase'] == p]['Total Jumps_Rate'].iloc[0] for p in selected_build))}")
                                m4.metric("Proj. Efforts", f"{int(sum(durations[p] * t_build[t_build['Phase'] == p]['Explosive Efforts_Rate'].iloc[0] for p in selected_build))}")
                                m5.metric("Proj. Dist (y)", f"{int(sum(durations[p] * t_build[t_build['Phase'] == p]['Estimated Distance (y)_Rate'].iloc[0] for p in selected_build))}")

                            if plan_level != "By Athlete":
                                st.markdown(f"#### Individual Athlete Projections")
                                ath_rates = planner_target_df.groupby(['Name', 'Phase'])[[f'{m}_Rate' for m in plan_metrics]].mean().reset_index()
                                ath_projections = []
                                for athlete in sorted(planner_target_df['Name'].unique()):
                                    a_data = ath_rates[ath_rates['Name'] == athlete]
                                    a_totals = {m: 0.0 for m in plan_metrics}
                                    for phase in selected_build:
                                        p_rate = a_data[a_data['Phase'] == phase]
                                        if not p_rate.empty:
                                            for m in plan_metrics: a_totals[m] += durations[phase] * p_rate[f'{m}_Rate'].iloc[0]
                                    if sum(a_totals.values()) > 0:
                                        ath_projections.append({'Athlete': athlete, 'Proj. Load': round(a_totals['Player Load'], 1), 'Proj. Jumps': int(a_totals['Total Jumps']), 'Proj. Efforts': int(a_totals['Explosive Efforts']), 'Proj. Dist (y)': int(a_totals['Estimated Distance (y)'])})
                                if ath_projections: st.dataframe(pd.DataFrame(ath_projections).sort_values('Proj. Load', ascending=False), use_container_width=True, hide_index=True)

                            st.markdown("#### Practice Intensity Flow (Rate per Minute)")
                            g_build = planner_target_df.groupby('Phase')[[f'{m}_Rate' for m in plan_metrics]].mean().reset_index().set_index('Phase').loc[selected_build].reset_index()
                            fig_flow = make_subplots(specs=[[{"secondary_y": True}]])
                            colors = {'Player Load': '#515154', 'Total Jumps': '#FF8200', 'Explosive Efforts': '#A52A2A', 'Estimated Distance (y)': '#4895DB'}
                            for m in plan_metrics:
                                is_distance = (m == 'Estimated Distance (y)')
                                fig_flow.add_trace(go.Scatter(x=g_build['Phase'], y=g_build[f'{m}_Rate'], name=f"{m} (Right Axis)" if is_distance else m, mode='lines+markers', line=dict(color={m: colors[m] for m in plan_metrics}[m], width=3, shape='spline'), marker=dict(size=8)), secondary_y=is_distance)
                            fig_flow.update_layout(height=450, template="simple_white", legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5), margin=dict(l=10, r=10, t=50, b=10), xaxis_title="Practice Phase")
                            fig_flow.update_yaxes(title_text="Load / Jumps / Efforts", secondary_y=False)
                            fig_flow.update_yaxes(title_text="Yards per Minute", secondary_y=True, showgrid=False)
                            st.plotly_chart(fig_flow, use_container_width=True, config=LOCKED_CONFIG, key="planner_flow_chart_t9")

            elif sel_plan_tab == "Phase Analysis":
                st.markdown('<div class="section-header">Work Index Matrix & Drill Utilization</div>', unsafe_allow_html=True)
                if phase_master is not None and not phase_master.empty:
                    working_matrix = phase_master.copy()
                    for col in ['Position', 'Name', 'Phase']:
                        if col in working_matrix.columns: working_matrix[col] = working_matrix[col].astype(str).str.strip()
                    if 'Phase' in working_matrix.columns: working_matrix['Phase'] = working_matrix['Phase'].replace(phase_map)

                    time_col = 'Duration'
                    index_metrics = ['Player Load', 'Total Jumps', 'Explosive Efforts']
                    working_matrix[time_col] = pd.to_numeric(working_matrix[time_col], errors='coerce').fillna(0)
                    session_summary = working_matrix.groupby(['Date', 'Phase']).agg({time_col: 'max', **{m: 'mean' for m in index_metrics}}).reset_index()
                    master_averages = session_summary.groupby('Phase').agg({time_col: 'mean', **{m: 'mean' for m in index_metrics}}).to_dict('index')

                    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                    with f_col1:
                        view_mode_t8 = st.radio("Group By", ["Position", "Individual"], horizontal=True, key="wi_view_t8")
                        metric_mode = st.radio("Data Mode", ["Work Index (per minute)", "Total Volume"], horizontal=True, key="wi_mode_t8")
                    with f_col2:
                        if view_mode_t8 == "Position":
                            sel_sub_filter = st.selectbox("Select Position", ["All Positions"] + sorted([p for p in working_matrix['Position'].unique() if p not in ["nan", "N/A"]]), key="wi_sub_pos_t8")
                        else:
                            sel_sub_filter = st.selectbox("Select Player", ["All Players"] + sorted(working_matrix['Name'].unique()), key="wi_sub_ath_t8")
                    with f_col3: sel_phase = st.selectbox("Select Drill/Phase", ["All Phases"] + sorted(working_matrix['Phase'].unique().tolist()), key="wi_phase_filter_t8")
                    with f_col4: sel_date = st.selectbox("Select Date", ["Season Avg"] + sorted([d.strftime('%Y-%m-%d') for d in working_matrix['Date'].dropna().unique()], reverse=True), key="wi_volume_date_t8")

                    filtered_df = working_matrix.copy()
                    if view_mode_t8 == "Position" and sel_sub_filter != "All Positions": filtered_df = filtered_df[filtered_df['Position'] == sel_sub_filter]
                    elif view_mode_t8 == "Individual" and sel_sub_filter != "All Players": filtered_df = filtered_df[filtered_df['Name'] == sel_sub_filter]
                    if sel_phase != "All Phases": filtered_df = filtered_df[filtered_df['Phase'] == sel_phase]
                    display_df = filtered_df[filtered_df['Date'] == pd.to_datetime(sel_date)].copy() if sel_date != "Season Avg" else filtered_df.copy()

                    group_keys = ['Position', 'Phase'] if view_mode_t8 == "Position" else ['Name', 'Position', 'Phase']
                    matrix_df = display_df.groupby(group_keys).agg({**{m: 'mean' for m in index_metrics}, time_col: 'mean'}).reset_index()

                    if sel_date == "Season Avg":
                        for idx, row in matrix_df.iterrows():
                            if row['Phase'] in master_averages: matrix_df.at[idx, time_col] = master_averages[row['Phase']][time_col]

                    h_load, h_jumps, h_expl = ("Total Load", "Total Jumps", "Total Efforts") if metric_mode == "Total Volume" else ("Player Load/Min", "Jumps/Min", "Explosive Efforts/Min")
                    fmt = "{:.0f}" if metric_mode == "Total Volume" else "{:.2f}"

                    st.markdown(f"### {metric_mode}")
                    sort_col = 'Position' if view_mode_t8 == "Position" else 'Name'
                    matrix_df = matrix_df.sort_values([sort_col, 'Phase'])

                    matrix_html = f"""<table class="scout-table"><tr style="background-color: #31333F; color: white; font-weight: bold;"><th style="padding: 12px; border: 1px solid #ddd;">{sort_col}</th><th style="padding: 12px; border: 1px solid #ddd;">Phase</th><th style="padding: 12px; border: 1px solid #ddd;">Mins</th><th style="padding: 12px; border: 1px solid #ddd;">{h_load}</th><th style="padding: 12px; border: 1px solid #ddd;">{h_jumps}</th><th style="padding: 12px; border: 1px solid #ddd;">{h_expl}</th></tr>"""
                    for _, row in matrix_df.iterrows():
                        d_mins = row[time_col]
                        matrix_html += f"""<tr><td style="padding: 10px; border: 1px solid #ddd;">{row[sort_col]}</td><td style="padding: 10px; border: 1px solid #ddd;">{row['Phase']}</td><td style="padding: 10px; border: 1px solid #ddd;">{d_mins:.1f}</td><td style="padding: 10px; border: 1px solid #ddd;">{fmt.format(row['Player Load'] if metric_mode == "Total Volume" else (row['Player Load'] / d_mins if d_mins > 0 else 0))}</td><td style="padding: 10px; border: 1px solid #ddd;">{fmt.format(row['Total Jumps'] if metric_mode == "Total Volume" else (row['Total Jumps'] / d_mins if d_mins > 0 else 0))}</td><td style="padding: 10px; border: 1px solid #ddd;">{fmt.format(row['Explosive Efforts'] if metric_mode == "Total Volume" else (row['Explosive Efforts'] / d_mins if d_mins > 0 else 0))}</td></tr>"""
                    st.markdown(matrix_html + "</table>", unsafe_allow_html=True)
                    
                    st.markdown("### Drill Frequency (Season Total)")
                    drill_stats = phase_master.copy()
                    drill_stats['Phase'] = drill_stats['Phase'].replace(phase_map)
                    freq_html = """<table class="scout-table"><tr style="background-color: #f0f2f6; font-weight: bold;"><th style="padding: 10px; border: 1px solid #ddd;">Drill/Phase</th><th style="padding: 10px; border: 1px solid #ddd;">Season Frequency</th></tr>"""
                    for _, row in drill_stats.groupby('Phase')['Number of Times'].sum().reset_index().sort_values('Number of Times', ascending=False).iterrows():
                        freq_html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>{row['Phase']}</td><td style='padding: 8px; border: 1px solid #ddd;'>{row['Number of Times']:.0f}</td></tr>"
                    st.markdown(freq_html + "</table>", unsafe_allow_html=True)


        # =========================================================================
        # --- HUB 4: WORKLOAD & ACWR ----------------------------------------------
        # =========================================================================
        elif selected_hub == "Workload & ACWR":
            st.markdown('<div class="section-header">Acute:Chronic Workload Ratio (EWMA)</div>', unsafe_allow_html=True)
            
            acwr_tabs_list = ["Team Workload Summary", "Individual"]
            if "acwr_active_subtab" not in st.session_state:
                st.session_state.acwr_active_subtab = acwr_tabs_list[0]
                
            selected_acwr_tab = st.radio("ACWR Sub Navigation", acwr_tabs_list, key="acwr_active_subtab", horizontal=True, label_visibility="collapsed")
            
            if selected_acwr_tab == "Team Workload Summary":
                valid_acwr_dates = sorted(raw_df['Date'].dropna().unique(), reverse=True)
                valid_acwr_dates_str = [d.strftime('%Y-%m-%d') for d in valid_acwr_dates] if valid_acwr_dates else []

                col_top1, col_top2, col_top3 = st.columns([1.5, 1.5, 1.5])
                with col_top1:
                    sel_team_date_str = st.selectbox("Evaluation Date", valid_acwr_dates_str, index=0, key="acwr_team_eval_date") if valid_acwr_dates_str else None
                with col_top2:
                    team_pos_filter = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in raw_df['Position'].unique() if p != "N/A"]), key="acwr_team_pos_filt")
                with col_top3:
                    sel_view_metric_header = st.selectbox("Featured Table Metric", metrics_to_score, index=0, key="acwr_featured_metric_sel")

                hide_inactive_last_week = st.checkbox("Hide athletes inactive in the past 7 days", value=True, key="acwr_hide_inactive_chk")

                if sel_team_date_str:
                    eval_date_obj = pd.to_datetime(sel_team_date_str)
                    week_start_window = eval_date_obj - timedelta(days=6)
                    team_summary_rows = []
                    
                    for ath in sorted(raw_df['Name'].unique()):
                        ath_all = raw_df[raw_df['Name'] == ath]
                        pos_str = ath_all['Position'].iloc[0] if not ath_all.empty else "N/A"
                        if team_pos_filter != "All Positions" and pos_str != team_pos_filter: continue
                            
                        if hide_inactive_last_week:
                            ath_recent_7d = ath_all[(ath_all['Date'] >= week_start_window) & (ath_all['Date'] <= eval_date_obj)]
                            if ath_recent_7d.empty or (ath_recent_7d[metrics_to_score].sum().sum() == 0): continue
                            
                        ath_cal = compute_athlete_ewMA_calendar(ath_all, metrics_to_score)
                        if ath_cal.empty: continue
                            
                        cal_point = ath_cal[ath_cal['Date'] <= eval_date_obj]
                        if cal_point.empty: continue
                            
                        target_row = cal_point.iloc[-1]
                        comp_acwr = sum([target_row.get(f'{m}_ACWR', 0.0) for m in metrics_to_score]) / len(metrics_to_score)
                        b_color, b_bg, b_status = get_acwr_badge(comp_acwr)
                        
                        row_dict = {
                            "Athlete": ath,
                            "Position": pos_str,
                            "Overall ACWR": comp_acwr,
                            "Status": b_status,
                            f"Featured ({sel_view_metric_header})": target_row.get(f'{sel_view_metric_header}_ACWR', 0.0)
                        }
                        for m in metrics_to_score:
                            row_dict[m] = target_row.get(f'{m}_ACWR', 0.0)
                        team_summary_rows.append(row_dict)
                        
                    if team_summary_rows:
                        team_summary_df = pd.DataFrame(team_summary_rows).sort_values("Overall ACWR", ascending=False)
                        sweet_count = sum(1 for r in team_summary_rows if 0.80 <= r['Overall ACWR'] <= 1.30)
                        spike_count = sum(1 for r in team_summary_rows if r['Overall ACWR'] > 1.50)
                        under_count = sum(1 for r in team_summary_rows if 0 < r['Overall ACWR'] < 0.80)
                        
                        sc1, sc2, sc3, sc4 = st.columns(4)
                        sc1.metric("Active Athletes Evaluated", len(team_summary_rows))
                        sc2.metric("Optimal (0.80-1.30)", sweet_count)
                        sc3.metric("Under (<0.80)", under_count)
                        sc4.metric("High Spikes (>1.50)", spike_count)
                        
                        st.markdown(f"#### ACWR Grid on {eval_date_obj.strftime('%m/%d/%Y')} (Active 7-Day Window)")
                        table_html = """<table class="scout-table"><thead><tr>
                            <th style="text-align:left !important; padding-left:10px;">Athlete</th>
                            <th>Position</th>
                            <th>Practice Score ACWR</th>
                            <th>Workload Zone</th>"""
                        for m in metrics_to_score: table_html += f"<th>{m}</th>"
                        table_html += "</tr></thead><tbody>"
                        
                        for _, r in team_summary_df.iterrows():
                            c_acwr = r['Overall ACWR']
                            c_color, c_bg, c_status = get_acwr_badge(c_acwr)
                            table_html += f"""<tr>
                                <td style="font-weight:800; text-align:left !important; padding-left:10px;">{r['Athlete']}</td>
                                <td>{r['Position']}</td>
                                <td style="font-weight:900; font-size:13px; color:{c_color};">{c_acwr:.2f}</td>
                                <td><span style="background-color:{c_bg}; color:{c_color}; padding:3px 8px; border-radius:10px; font-weight:700; font-size:11px;">{c_status}</span></td>"""
                            for m in metrics_to_score:
                                m_val = r[m]
                                m_col, _, _ = get_acwr_badge(m_val)
                                table_html += f"<td style='color:{m_col}; font-weight:700;'>{m_val:.2f}</td>"
                            table_html += "</tr>"
                            
                        table_html += "</tbody></table>"
                        st.markdown(table_html, unsafe_allow_html=True)
                    else:
                        st.info(f"No active athletes with recorded practice data found in the 7 days leading up to {eval_date_obj.strftime('%m/%d/%Y')}.")

            elif selected_acwr_tab == "Individual":
                c_ind1, c_ind2, c_ind3 = st.columns([1.5, 1.5, 1.5])
                valid_all_dates_str = [d.strftime('%Y-%m-%d') for d in sorted(raw_df['Date'].dropna().unique(), reverse=True)]
                with c_ind3: sel_ind_date_str = st.selectbox("Select Snapshot Date", valid_all_dates_str, index=0, key="acwr_ind_date_sel")
                
                sel_ind_date = pd.to_datetime(sel_ind_date_str)
                week_start_ind = sel_ind_date - timedelta(days=6)
                
                active_athletes_for_date = []
                for ath_name in sorted(raw_df['Name'].unique()):
                    ath_sub = raw_df[(raw_df['Name'] == ath_name) & (raw_df['Date'] >= week_start_ind) & (raw_df['Date'] <= sel_ind_date)]
                    if not ath_sub.empty and ath_sub[metrics_to_score].sum().sum() > 0: active_athletes_for_date.append(ath_name)
                if not active_athletes_for_date: active_athletes_for_date = sorted(raw_df['Name'].unique())

                with c_ind1: sel_ind_ath = st.selectbox("Select Active Athlete", active_athletes_for_date, key="acwr_ind_ath_sel")
                with c_ind2: sel_ind_metric = st.selectbox("Select Practice Score Metric", metrics_to_score, index=0, key="acwr_ind_metric_sel")
                
                ath_all_ind = raw_df[raw_df['Name'] == sel_ind_ath].copy()
                meta_lookup = full_df_unfiltered[full_df_unfiltered['Name'] == sel_ind_ath]
                photo_url = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                pos_str = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"
                
                ath_cal_ind = compute_athlete_ewMA_calendar(ath_all_ind, metrics_to_score)
                
                if ath_cal_ind.empty or ath_cal_ind[ath_cal_ind['Date'] == sel_ind_date].empty:
                    st.info(f"No training history found for {sel_ind_ath} around {sel_ind_date.strftime('%m/%d/%Y')}.")
                else:
                    target_row = ath_cal_ind[ath_cal_ind['Date'] == sel_ind_date].iloc[0]
                    cur_acute = target_row[f'{sel_ind_metric}_Acute']
                    cur_chronic = target_row[f'{sel_ind_metric}_Chronic']
                    cur_acwr = target_row[f'{sel_ind_metric}_ACWR']
                    badge_color, badge_bg, status_text = get_acwr_badge(cur_acwr)

                    st.markdown(f'''
                        <div class="comp-athlete-header" style="margin-top: 10px;">
                            <img src="{photo_url}" class="comp-athlete-photo">
                            <div>
                                <div style="font-size:22px; font-weight:900; color:#111827;">{sel_ind_ath}</div>
                                <div style="font-size:14px; font-weight:600; color:#64748B;">{pos_str} | Metric: {sel_ind_metric}</div>
                            </div>
                        </div>
                    ''', unsafe_allow_html=True)

                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Daily Raw Workload", f"{target_row[sel_ind_metric]:.1f}", help=f"Recorded on {sel_ind_date.strftime('%m/%d/%Y')}")
                    k2.metric("Acute Load (7d EWMA)", f"{cur_acute:.1f}")
                    k3.metric("Chronic Load (28d EWMA)", f"{cur_chronic:.1f}")
                    with k4:
                        st.markdown(f'''
                            <div style="background:{badge_bg}; border:1px solid #E2E8F0; border-radius:10px; padding:10px; text-align:center;">
                                <div style="font-size:10px; font-weight:800; color:{badge_color}; text-transform:uppercase;">ACWR RATIO</div>
                                <div style="font-size:24px; font-weight:900; color:{badge_color}; line-height:1.1;">{cur_acwr:.2f}</div>
                                <div style="font-size:11px; font-weight:700; color:{badge_color}; margin-top:3px;">{status_text}</div>
                            </div>
                        ''', unsafe_allow_html=True)

                    st.write("<br>", unsafe_allow_html=True)
                    fig_acwr = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_acwr.add_hrect(y0=0.80, y1=1.30, fillcolor="#28a745", opacity=0.10, line_width=0, secondary_y=False, annotation_text="Optimal (0.80 - 1.30)", annotation_position="top left", annotation_font_size=10, annotation_font_color="#137333")
                    fig_acwr.add_hline(y=1.50, line_dash="dash", line_color="#D93025", line_width=1.5, secondary_y=False, annotation_text="Spike Threshold (1.50)", annotation_position="bottom right", annotation_font_size=10, annotation_font_color="#D93025")
                    fig_acwr.add_trace(go.Scatter(x=ath_cal_ind['Date'], y=ath_cal_ind[f'{sel_ind_metric}_ACWR'], name="ACWR Ratio (EWMA)", mode='lines+markers', line=dict(color='#FF8200', width=3.5), marker=dict(size=5, color='#FF8200')), secondary_y=False)
                    fig_acwr.add_trace(go.Scatter(x=ath_cal_ind['Date'], y=ath_cal_ind[f'{sel_ind_metric}_Acute'], name="Acute Load (7d)", mode='lines', line=dict(color='#4895DB', width=2, dash='dot')), secondary_y=True)
                    fig_acwr.add_trace(go.Scatter(x=ath_cal_ind['Date'], y=ath_cal_ind[f'{sel_ind_metric}_Chronic'], name="Chronic Load (28d)", mode='lines', line=dict(color='#515154', width=1.8, dash='dash')), secondary_y=True)
                    fig_acwr.add_vline(x=sel_ind_date, line_dash="dash", line_color="#111827", opacity=0.4)
                    fig_acwr.update_layout(height=440, template="simple_white", title=dict(text=f"<b>{sel_ind_ath} — {sel_ind_metric} ACWR Longitudinal Profile</b>", font=dict(size=14), x=0, y=0.97), margin=dict(l=20, r=20, t=50, b=30), legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1), xaxis=dict(title="Date", tickformat="%m/%d", showgrid=False))
                    fig_acwr.update_yaxes(title_text="ACWR (Acute:Chronic)", secondary_y=False, rangemode='tozero', range=[0, max(2.0, ath_cal_ind[f'{sel_ind_metric}_ACWR'].max() * 1.15)])
                    fig_acwr.update_yaxes(title_text=f"Absolute {sel_ind_metric} Workload", secondary_y=True, showgrid=False)
                    st.plotly_chart(fig_acwr, use_container_width=True, config=LOCKED_CONFIG, key=f"acwr_chart_{sel_ind_ath}_{sel_ind_metric}")

                    st.markdown(f"#### Practice Score Metrics Breakdown on {sel_ind_date.strftime('%m/%d/%Y')}")
                    ind_metric_rows = []
                    for m in metrics_to_score:
                        a_ewma = target_row[f'{m}_Acute']
                        c_ewma = target_row[f'{m}_Chronic']
                        r_val = target_row[f'{m}_ACWR']
                        _, _, status_lbl = get_acwr_badge(r_val)
                        ind_metric_rows.append({"Metric": m, "Day Total": f"{target_row.get(m, 0.0):.1f}", "Acute (7d EWMA)": f"{a_ewma:.1f}", "Chronic (28d EWMA)": f"{c_ewma:.1f}", "ACWR Ratio": f"{r_val:.2f}", "Workload Zone": status_lbl})
                    st.dataframe(pd.DataFrame(ind_metric_rows), use_container_width=True, hide_index=True)


        # =========================================================================
        # --- HUB 5: TESTING & BASELINES ------------------------------------------
        # =========================================================================
        elif selected_hub == "Testing & Baselines":
            testing_subtabs = [
                "Intake Testing", 
                "Overall Testing Profile", 
                "Season Comparison",
                "In-Season Testing",
                "Pre-Season Testing",
                "Summer Testing", 
                "Spring Testing"
            ]
            if "test_subtab_radio" not in st.session_state or st.session_state["test_subtab_radio"] not in testing_subtabs:
                st.session_state["test_subtab_radio"] = testing_subtabs[0]

            sel_test_tab = st.radio("Testing Sub Navigation", testing_subtabs, key="test_subtab_radio", horizontal=True, label_visibility="collapsed")

            if sel_test_tab == "Intake Testing":
                st.markdown("<h3 style='color:#1D1D1F; font-weight:900; text-transform:uppercase;'>Athlete Intake Assessment</h3>", unsafe_allow_html=True)
                c_int_ath, _ = st.columns([2, 2])
                with c_int_ath: selected_intake_athlete = st.selectbox("Select Athlete for Intake Assessment", master_athlete_list, key="intake_ath_select")

                calf_ath = raw_calf_df[raw_calf_df['Name'] == selected_intake_athlete].sort_values('Test Date')
                hip_ath = raw_hip_df[raw_hip_df['Name'] == selected_intake_athlete].sort_values('Test Date')
                sh_ath = raw_shoulder_df[raw_shoulder_df['Name'] == selected_intake_athlete].sort_values('Test Date')
                isoy_ath = raw_ash_df[(raw_ash_df['Name'] == selected_intake_athlete) & (raw_ash_df['Isometric Type'].astype(str).str.contains('ISO-Y|Y', case=False, na=False))].sort_values('Test Date')

                has_data = not (calf_ath.empty and hip_ath.empty and sh_ath.empty and isoy_ath.empty)
                if has_data:
                    def render_val_with_arrow(current, initial, fmt="{:.1f}", unit=""):
                        if initial == 0: return f"{fmt.format(current)}{unit}"
                        diff = current - initial
                        pct = (diff / initial) * 100
                        arrow = "↑" if diff >= 0 else "↓"
                        color = "#28a745" if diff >= 0 else "#dc3545"
                        return f"{fmt.format(current)}{unit} <span style='color:{color}; font-size:11px; font-weight:bold;'>({arrow}{abs(pct):.1f}%)</span>"

                    hud_col1, hud_col2 = st.columns([1.2, 1.8])
                    with hud_col1:
                        hud_html = """
                        <!DOCTYPE html>
                        <html>
                        <head>
                        <style>
                            body { margin: 0; padding: 0; background-color: transparent; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
                            .hud-dashboard-card { background: #FFFFFF; border-radius: 16px; padding: 16px; border: 1px solid #E5E5E7; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
                            .hud-header-title { color: #1D1D1F; font-weight: 800; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; border-bottom: 2px solid #FF8200; padding-bottom: 6px; margin-bottom: 12px; }
                            .hud-body-viewport { position: relative; width: 100%; height: 380px; background: #FAFDFD; border-radius: 12px; border: 1px solid #D5E5E8; display: flex; align-items: center; justify-content: center; overflow: hidden; }
                            svg { width: 100%; height: 100%; }
                        </style>
                        </head>
                        <body>
                            <div class="hud-dashboard-card">
                                <div class="hud-header-title">Anatomy Location Map</div>
                                <div class="hud-body-viewport">
                                    <svg viewBox="0 0 140 220" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
                                        <defs>
                                            <linearGradient id="anatomicalBodyGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                                <stop offset="0%" stop-color="#C5CACC" />
                                                <stop offset="25%" stop-color="#E8ECEE" />
                                                <stop offset="50%" stop-color="#F2F5F7" />
                                                <stop offset="75%" stop-color="#D0D5D8" />
                                                <stop offset="100%" stop-color="#9AA0A6" />
                                            </linearGradient>
                                        </defs>
                                        <ellipse cx="68" cy="214" rx="20" ry="3.5" fill="#000000" opacity="0.12" />
                                        <g stroke="#2C3036" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                                            <ellipse cx="68" cy="17" rx="7" ry="9" fill="url(#anatomicalBodyGrad)" />
                                            <path d="M 65 25 L 63 33 M 71 25 L 73 33" stroke-width="1.2" />
                                            <path d="M 63 33 C 58 33, 48 36, 42 40 C 37 43, 36 50, 39 56 L 43 56 C 47 52, 49 46, 52 44 M 73 33 C 78 33, 88 36, 94 40 C 99 43, 100 50, 97 56 L 93 56 C 89 52, 87 46, 84 44" fill="url(#anatomicalBodyGrad)" />
                                            <path d="M 42 40 C 37 43, 35 52, 33 64 C 31 74, 29 82, 27 92 C 25 96, 23 100, 22 104 C 21 106, 23 107, 25 106 C 27 104, 28 98, 30 92 C 33 82, 36 74, 38 64 C 40 54, 42 48, 43 56 Z" fill="url(#anatomicalBodyGrad)" />
                                            <path d="M 22 104 C 20 106, 18 108, 17 110 M 23 105 C 21 108, 20 110, 19 112 M 24 105 C 23 108, 22 110, 21 112 M 25 104 C 25 107, 24 109, 23 111" fill="none" stroke-width="0.8" />
                                            <path d="M 94 40 C 99 43, 101 52, 103 64 C 105 74, 107 82, 109 92 C 111 96, 113 100, 114 104 C 115 106, 113 107, 111 106 C 109 104, 108 98, 106 92 C 103 82, 100 74, 98 64 C 96 54, 94 48, 93 56 Z" fill="url(#anatomicalBodyGrad)" />
                                            <path d="M 114 104 C 116 106, 118 108, 119 110 M 113 105 C 115 108, 116 110, 117 112 M 112 105 C 113 108, 114 110, 115 112 M 111 104 C 111 107, 112 109, 113 111" fill="none" stroke-width="0.8" />
                                            <path d="M 52 44 L 54 75 L 52 92 L 68 106 L 84 92 L 82 75 L 84 44 Z" fill="url(#anatomicalBodyGrad)" />
                                            <path d="M 52 92 C 50 105, 49 122, 53 138 C 55 144, 55 152, 54 162 C 52 175, 52 192, 54 205 L 48 210 L 58 210 L 59 203 C 60 190, 60 175, 60 162 C 60 152, 60 144, 62 138 C 66 122, 66 105, 68 106 Z" fill="url(#anatomicalBodyGrad)" />
                                            <path d="M 84 92 C 86 105, 87 122, 83 138 C 81 144, 81 152, 82 162 C 84 175, 84 192, 82 205 L 88 210 L 78 210 L 77 203 C 76 190, 76 175, 76 162 C 76 152, 76 144, 74 138 C 70 122, 70 105, 68 106 Z" fill="url(#anatomicalBodyGrad)" />
                                            <line x1="68" y1="8" x2="68" y2="211" stroke="#FF8200" stroke-width="1.3" />
                                            <line x1="51" y1="116" x2="85" y2="116" stroke="#D32F2F" stroke-width="1.1" />
                                            <line x1="55" y1="168" x2="81" y2="168" stroke="#D32F2F" stroke-width="1.1" />
                                            <g stroke="#3A3F46" stroke-width="0.9" fill="none">
                                                <path d="M 68 35 C 60 34, 52 37, 46 40 M 68 35 C 76 34, 84 37, 90 40" stroke-width="1" />
                                                <path d="M 52 44 C 60 43, 67 47, 68 54 C 60 56, 52 52, 52 44 Z" fill="#E2E7EC" opacity="0.6" />
                                                <path d="M 84 44 C 76 43, 69 47, 68 54 C 76 56, 84 52, 84 44 Z" fill="#E2E7EC" opacity="0.6" />
                                                <path d="M 58 58 C 64 57, 72 57, 78 58" />
                                                <path d="M 58 66 C 64 65, 72 65, 78 66" />
                                                <path d="M 59 74 C 64 73, 72 73, 77 74" />
                                                <path d="M 39 56 C 37 62, 35 70, 33 78" stroke-width="0.75" />
                                                <path d="M 97 56 C 99 62, 101 70, 103 78" stroke-width="0.75" />
                                                <path d="M 52 92 C 58 98, 64 103, 68 106 M 84 92 C 78 98, 72 103, 68 106" stroke-width="1" />
                                                <path d="M 52 96 C 49 108, 50 125, 57 138" />
                                                <path d="M 84 96 C 87 108, 86 125, 79 138" />
                                                <ellipse cx="57" cy="142" rx="3" ry="3.5" stroke-width="0.9" fill="#E8EDF2" />
                                                <ellipse cx="79" cy="142" rx="3" ry="3.5" stroke-width="0.9" fill="#E8EDF2" />
                                                <path d="M 54 150 C 51 160, 52 178, 56 195" />
                                                <path d="M 82 150 C 85 160, 84 178, 80 195" />
                                            </g>
                                        </g>
                                        <circle cx="91" cy="46" r="3.5" fill="#FF8200" stroke="#FFFFFF" stroke-width="1" />
                                        <line x1="91" y1="46" x2="118" y2="46" stroke="#FF8200" stroke-width="1.8" stroke-dasharray="2,2" />
                                        <rect x="112" y="39" width="14" height="14" rx="3" fill="#FF8200" />
                                        <text x="119" y="50" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">1</text>
                                        <circle cx="68" cy="54" r="3.5" fill="#FF8200" stroke="#FFFFFF" stroke-width="1" />
                                        <line x1="68" y1="54" x2="118" y2="68" stroke="#FF8200" stroke-width="1.8" stroke-dasharray="2,2" />
                                        <rect x="112" y="61" width="14" height="14" rx="3" fill="#FF8200" />
                                        <text x="119" y="72" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">2</text>
                                        <circle cx="74" cy="122" r="3.5" fill="#4895DB" stroke="#FFFFFF" stroke-width="1" />
                                        <line x1="74" y1="122" x2="118" y2="122" stroke="#4895DB" stroke-width="1.8" stroke-dasharray="2,2" />
                                        <rect x="112" y="115" width="14" height="14" rx="3" fill="#4895DB" />
                                        <text x="119" y="126" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">3</text>
                                        <circle cx="53" cy="116" r="3.5" fill="#4895DB" stroke="#FFFFFF" stroke-width="1" />
                                        <line x1="53" y1="116" x2="22" y2="116" stroke="#4895DB" stroke-width="1.8" stroke-dasharray="2,2" />
                                        <rect x="14" y="109" width="14" height="14" rx="3" fill="#4895DB" />
                                        <text x="21" y="120" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">4</text>
                                        <circle cx="77" cy="172" r="3.5" fill="#4895DB" stroke="#FFFFFF" stroke-width="1" />
                                        <line x1="77" y1="172" x2="118" y2="172" stroke="#4895DB" stroke-width="1.8" stroke-dasharray="2,2" />
                                        <rect x="112" y="165" width="14" height="14" rx="3" fill="#4895DB" />
                                        <text x="119" y="176" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">5</text>
                                    </svg>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        components.html(hud_html, height=450)

                    with hud_col2:
                        st.markdown("""
                            <style>
                            .hud-details-card { background: #FFFFFF; border-radius: 16px; padding: 20px; border: 1px solid #E5E5E7; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
                            .hud-header-title-light { color: #1D1D1F; font-weight: 800; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; border-bottom: 2px solid #FF8200; padding-bottom: 6px; margin-bottom: 16px; }
                            .hud-metric-row-light { background: #F8F9FA; border-left: 4px solid #FF8200; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; color: #1D1D1F; border-top: 1px solid #E5E5E7; border-right: 1px solid #E5E5E7; border-bottom: 1px solid #E5E5E7; }
                            .hud-metric-row-light-blue { background: #F8F9FA; border-left: 4px solid #4895DB; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; color: #1D1D1F; border-top: 1px solid #E5E5E7; border-right: 1px solid #E5E5E7; border-bottom: 1px solid #E5E5E7; }
                            .node-badge-orange { display: inline-block; width: 20px; height: 20px; background: #FF8200; color: #FFFFFF; font-weight: 900; font-size: 11px; border-radius: 4px; text-align: center; line-height: 20px; margin-right: 8px; }
                            .node-badge-blue { display: inline-block; width: 20px; height: 20px; background: #4895DB; color: #FFFFFF; font-weight: 900; font-size: 11px; border-radius: 4px; text-align: center; line-height: 20px; margin-right: 8px; }
                            </style>
                            <div class="hud-details-card">
                                <div class="hud-header-title-light">Anatomy Location Assessment Details</div>
                        """, unsafe_allow_html=True)

                        if not sh_ath.empty:
                            sh_ir = sh_ath[sh_ath['Direction'].astype(str).str.contains('Internal|IR', case=False, na=False)] if 'Direction' in sh_ath.columns else sh_ath
                            sh_er = sh_ath[sh_ath['Direction'].astype(str).str.contains('External|ER', case=False, na=False)] if 'Direction' in sh_ath.columns else sh_ath
                            
                            ir_base = sh_ir.iloc[0] if not sh_ir.empty else pd.Series()
                            ir_latest = sh_ir.iloc[-1] if not sh_ir.empty else pd.Series()
                            er_base = sh_er.iloc[0] if not sh_er.empty else pd.Series()
                            er_latest = sh_er.iloc[-1] if not sh_er.empty else pd.Series()

                            ir_bL, ir_bR = ir_base.get('L Max Force (N)', 0.0), ir_base.get('R Max Force (N)', 0.0)
                            ir_lL, ir_lR = ir_latest.get('L Max Force (N)', 0.0), ir_latest.get('R Max Force (N)', 0.0)
                            er_bL, er_bR = er_base.get('L Max Force (N)', 0.0), er_base.get('R Max Force (N)', 0.0)
                            er_lL, er_lR = er_latest.get('L Max Force (N)', 0.0), er_latest.get('R Max Force (N)', 0.0)

                            latest_date_str = ir_latest.get('Test Date', pd.Timestamp.now()).strftime('%m/%d/%Y') if not ir_latest.empty else "N/A"

                            st.markdown(f"""
                                <div class="hud-metric-row-light">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                        <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-orange">1</span>SHOULDER IR / ER</span>
                                        <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {latest_date_str}</span>
                                    </div>
                                    <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                        <b>Internal (IR):</b> Initial L {ir_bL:.1f}N | R {ir_bR:.1f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(ir_lL, ir_bL, '{:.1f}', 'N')} | R {render_val_with_arrow(ir_lR, ir_bR, '{:.1f}', 'N')}<br>
                                        <b>External (ER):</b> Initial L {er_bL:.1f}N | R {er_bR:.1f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(er_lL, er_bL, '{:.1f}', 'N')} | R {render_val_with_arrow(er_lR, er_bR, '{:.1f}', 'N')}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                        if not isoy_ath.empty:
                            b_y, l_y = isoy_ath.iloc[0], isoy_ath.iloc[-1]
                            byL, byR = b_y.get('Peak Vertical Force [N] (L)', 0.0), b_y.get('Peak Vertical Force [N] (R)', 0.0)
                            lyL, lyR = l_y.get('Peak Vertical Force [N] (L)', 0.0), l_y.get('Peak Vertical Force [N] (R)', 0.0)

                            st.markdown(f"""
                                <div class="hud-metric-row-light">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                        <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-orange">2</span>ISO-Y STRENGTH</span>
                                        <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {l_y['Test Date'].strftime('%m/%d/%Y')}</span>
                                    </div>
                                    <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                        <b>Initial Force:</b> L {byL:.0f}N | R {byR:.0f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(lyL, byL, '{:.0f}', 'N')} | R {render_val_with_arrow(lyR, byR, '{:.0f}', 'N')}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                        if not hip_ath.empty:
                            hip_ad = hip_ath[hip_ath['Direction'].astype(str).str.contains('AD', case=False, na=False)] if 'Direction' in hip_ath.columns else hip_ath
                            hip_ab = hip_ath[hip_ath['Direction'].astype(str).str.contains('AB', case=False, na=False)] if 'Direction' in hip_ath.columns else hip_ath

                            if not hip_ad.empty:
                                ad_b, ad_l = hip_ad.iloc[0], hip_ad.iloc[-1]
                                ad_bL, ad_bR = ad_b.get('L Max Force (N)', 0.0), ad_b.get('R Max Force (N)', 0.0)
                                ad_lL, ad_lR = ad_l.get('L Max Force (N)', 0.0), ad_l.get('R Max Force (N)', 0.0)

                                st.markdown(f"""
                                    <div class="hud-metric-row-light-blue">
                                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                            <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">3</span>HIP ADDUCTION (AD)</span>
                                            <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {ad_l['Test Date'].strftime('%m/%d/%Y')}</span>
                                        </div>
                                        <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                            <b>Initial Force:</b> L {ad_bL:.1f}N | R {ad_bR:.1f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(ad_lL, ad_bL, '{:.1f}', 'N')} | R {render_val_with_arrow(ad_lR, ad_bR, '{:.1f}', 'N')}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)

                            if not hip_ab.empty:
                                ab_b, ab_l = hip_ab.iloc[0], hip_ab.iloc[-1]
                                ab_bL, ab_bR = ab_b.get('L Max Force (N)', 0.0), ab_b.get('R Max Force (N)', 0.0)
                                ab_lL, ab_lR = ab_l.get('L Max Force (N)', 0.0), ab_l.get('R Max Force (N)', 0.0)

                                st.markdown(f"""
                                    <div class="hud-metric-row-light-blue">
                                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                            <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">4</span>HIP ABDUCTION (AB)</span>
                                            <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {ab_l['Test Date'].strftime('%m/%d/%Y')}</span>
                                        </div>
                                        <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                            <b>Initial Force:</b> L {ab_bL:.1f}N | R {ab_bR:.1f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(ab_lL, ab_bL, '{:.1f}', 'N')} | R {render_val_with_arrow(ab_lR, ab_bR, '{:.1f}', 'N')}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)

                        if not calf_ath.empty:
                            b_c, l_c = calf_ath.iloc[0], calf_ath.iloc[-1]
                            bcL, bcR = b_c.get('Peak Vertical Force [N] (L)', 0.0), b_c.get('Peak Vertical Force [N] (R)', 0.0)
                            lcL, lcR = l_c.get('Peak Vertical Force [N] (L)', 0.0), l_c.get('Peak Vertical Force [N] (R)', 0.0)
                            bcL_bm = b_c.get('Peak Vertical Force / BM [N/kg] (L)', 0.0)

                            st.markdown(f"""
                                <div class="hud-metric-row-light-blue">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                        <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">5</span>SINGLE LEG CALF RAISE</span>
                                        <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {l_c['Test Date'].strftime('%m/%d/%Y')}</span>
                                    </div>
                                    <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                        <b>Initial Force:</b> L {bcL:.0f}N ({bcL_bm:.2f} N/kg) | R {bcR:.0f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(lcL, bcL, '{:.0f}', 'N')} | R {render_val_with_arrow(lcR, bcR, '{:.0f}', 'N')}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                        st.markdown('</div>', unsafe_allow_html=True)

                    # --- EXPANDABLE RAW TEST LOGS AT THE BOTTOM ---
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='color:#1D1D1F; font-weight:900;'>Intake Assessment Raw Logs for {selected_intake_athlete}</h3>", unsafe_allow_html=True)

                    def format_intake_table(df_source, test_col='Direction', test_fallback='Test'):
                        if df_source.empty:
                            return pd.DataFrame()
                        
                        df_out = df_source.sort_values('Test Date', ascending=True).copy()
                        df_out['DATE'] = pd.to_datetime(df_out['Test Date']).dt.strftime('%Y-%m-%d')
                        
                        if test_col in df_out.columns:
                            df_out['TEST'] = df_out[test_col].astype(str)
                        elif 'Isometric Type' in df_out.columns:
                            df_out['TEST'] = df_out['Isometric Type'].astype(str)
                        else:
                            df_out['TEST'] = test_fallback
                            
                        l_col = 'L Max Force (N)' if 'L Max Force (N)' in df_out.columns else 'Peak Vertical Force [N] (L)'
                        r_col = 'R Max Force (N)' if 'R Max Force (N)' in df_out.columns else 'Peak Vertical Force [N] (R)'
                        
                        df_out['L_VAL'] = pd.to_numeric(df_out[l_col], errors='coerce').fillna(0.0) if l_col in df_out.columns else 0.0
                        df_out['R_VAL'] = pd.to_numeric(df_out[r_col], errors='coerce').fillna(0.0) if r_col in df_out.columns else 0.0
                        
                        def calc_imbalance(row):
                            lv, rv = row['L_VAL'], row['R_VAL']
                            high = max(lv, rv)
                            if high > 0:
                                return round((abs(lv - rv) / high) * 100.0, 2)
                            return 0.0

                        df_out['MAX IMBALANCE'] = df_out.apply(calc_imbalance, axis=1)
                        
                        df_out['L MAX FORCE (N)'] = df_out['L_VAL'].apply(lambda x: f"{x:.2f}")
                        df_out['R MAX FORCE (N)'] = df_out['R_VAL'].apply(lambda x: f"{x:.2f}")
                        df_out['MAX IMBALANCE'] = df_out['MAX IMBALANCE'].apply(lambda x: f"{x:.2f}")
                        
                        return df_out[['DATE', 'TEST', 'L MAX FORCE (N)', 'R MAX FORCE (N)', 'MAX IMBALANCE']]

                    with st.expander("Shoulder IR / ER Log", expanded=False):
                        sh_tbl = format_intake_table(sh_ath, test_col='Direction', test_fallback='Shoulder ISO')
                        if not sh_tbl.empty:
                            st.dataframe(sh_tbl, use_container_width=True, hide_index=True)
                        else:
                            st.info(f"No Shoulder IR / ER records found for {selected_intake_athlete}.")

                    with st.expander("ISO-Y Strength Log", expanded=False):
                        isoy_tbl = format_intake_table(isoy_ath, test_col='Isometric Type', test_fallback='ISO-Y')
                        if not isoy_tbl.empty:
                            st.dataframe(isoy_tbl, use_container_width=True, hide_index=True)
                        else:
                            st.info(f"No ISO-Y Strength records found for {selected_intake_athlete}.")

                    with st.expander("Hip Adduction / Abduction Log", expanded=False):
                        hip_tbl = format_intake_table(hip_ath, test_col='Direction', test_fallback='Hip ISO')
                        if not hip_tbl.empty:
                            st.dataframe(hip_tbl, use_container_width=True, hide_index=True)
                        else:
                            st.info(f"No Hip Adduction / Abduction records found for {selected_intake_athlete}.")

                    with st.expander("Single Leg Calf Raise Log", expanded=False):
                        calf_tbl = format_intake_table(calf_ath, test_col='Direction', test_fallback='Single Leg Calf Raise')
                        if not calf_tbl.empty:
                            st.dataframe(calf_tbl, use_container_width=True, hide_index=True)
                        else:
                            st.info(f"No Single Leg Calf Raise records found for {selected_intake_athlete}.")
                    

            elif sel_test_tab == "Overall Testing Profile":
                st.markdown("<h3 style='color:#1D1D1F; font-weight:900; text-transform:uppercase;'>Overall Athletic Testing Profile</h3>", unsafe_allow_html=True)
                c_ov_ath, _ = st.columns([2, 2])
                with c_ov_ath: selected_overall_athlete = st.selectbox("Select Athlete for Overall Profile", master_athlete_list, key="overall_ath_select")

                meta_lookup_ov = full_df_unfiltered[full_df_unfiltered['Name'] == selected_overall_athlete]
                photo_val_ov = meta_lookup_ov['PhotoURL'].iloc[0] if not meta_lookup_ov.empty else "https://www.w3schools.com/howto/img_avatar.png"
                pos_val_ov = meta_lookup_ov['Position'].iloc[0] if not meta_lookup_ov.empty else "N/A"

                st.markdown(f'<div style="display:flex; align-items:center; gap:20px; padding:15px; background:#f8f9fa; border-radius:15px; border-left:6px solid #FF8200; margin-bottom:20px;"><img src="{photo_val_ov}" class="gallery-photo" style="width:80px; height:80px;"><div><h2 style="margin:0; color:#1D1D1F;">{selected_overall_athlete}</h2><p style="margin:0; color:#4895DB; font-weight:700; font-size:16px;">{pos_val_ov} | Overall All-Time Max Testing Baseline</p></div></div>', unsafe_allow_html=True)

                cmj_p = raw_cmj_df[raw_cmj_df['Name'] == selected_overall_athlete]
                ash_p = raw_ash_df[raw_ash_df['Name'] == selected_overall_athlete]
                er_p = raw_er_df[raw_er_df['Name'] == selected_overall_athlete]
                calf_p = raw_calf_df[raw_calf_df['Name'] == selected_overall_athlete]
                hip_p = raw_hip_df[raw_hip_df['Name'] == selected_overall_athlete]
                sh_p = raw_shoulder_df[raw_shoulder_df['Name'] == selected_overall_athlete]

                # --- Metric Extractions & Associated Dates ---
                # CMJ Height
                if not cmj_p.empty and cmj_col in cmj_p.columns and cmj_p[cmj_col].notna().any():
                    cmj_h_row = cmj_p.loc[cmj_p[cmj_col].idxmax()]
                    max_cmj_h = cmj_h_row[cmj_col]
                    date_cmj_h = cmj_h_row['Test Date'].strftime('%Y-%m-%d') if pd.notna(cmj_h_row['Test Date']) else "N/A"
                else:
                    max_cmj_h, date_cmj_h = 0.0, "N/A"

                # CMJ RSI-mod
                if not cmj_p.empty and rsi_col in cmj_p.columns and cmj_p[rsi_col].notna().any():
                    cmj_rsi_row = cmj_p.loc[cmj_p[rsi_col].idxmax()]
                    max_rsi_val = cmj_rsi_row[rsi_col]
                    date_cmj_rsi = cmj_rsi_row['Test Date'].strftime('%Y-%m-%d') if pd.notna(cmj_rsi_row['Test Date']) else "N/A"
                else:
                    max_rsi_val, date_cmj_rsi = 0.0, "N/A"

                # ASH Shoulder (ISO-I)
                ash_i_p = ash_p[ash_p['Isometric Type'].astype(str).str.contains('I', case=False, na=False)] if not ash_p.empty and 'Isometric Type' in ash_p.columns else ash_p
                if not ash_i_p.empty and ('Peak Vertical Force [N] (L)' in ash_i_p.columns or 'Peak Vertical Force [N] (R)' in ash_i_p.columns):
                    ash_i_p_calc = ash_i_p.copy()
                    ash_i_p_calc['Combined_Peak'] = ash_i_p_calc[['Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)']].max(axis=1)
                    ash_row = ash_i_p_calc.loc[ash_i_p_calc['Combined_Peak'].idxmax()]
                    max_ash_l = ash_row.get('Peak Vertical Force [N] (L)', 0.0)
                    max_ash_r = ash_row.get('Peak Vertical Force [N] (R)', 0.0)
                    date_ash = ash_row['Test Date'].strftime('%Y-%m-%d') if pd.notna(ash_row['Test Date']) else "N/A"
                else:
                    max_ash_l, max_ash_r, date_ash = 0.0, 0.0, "N/A"

                # External Rotation ROM
                if not er_p.empty and ('L Max ROM (°)' in er_p.columns or 'R Max ROM (°)' in er_p.columns):
                    er_p_calc = er_p.copy()
                    er_p_calc['Combined_Peak'] = er_p_calc[['L Max ROM (°)', 'R Max ROM (°)']].max(axis=1)
                    er_row = er_p_calc.loc[er_p_calc['Combined_Peak'].idxmax()]
                    max_er_l = er_row.get('L Max ROM (°)', 0.0)
                    max_er_r = er_row.get('R Max ROM (°)', 0.0)
                    date_er = er_row['Test Date'].strftime('%Y-%m-%d') if pd.notna(er_row['Test Date']) else "N/A"
                else:
                    max_er_l, max_er_r, date_er = 0.0, 0.0, "N/A"

                # Calf Raise
                if not calf_p.empty and ('Peak Vertical Force [N] (L)' in calf_p.columns or 'Peak Vertical Force [N] (R)' in calf_p.columns):
                    calf_p_calc = calf_p.copy()
                    calf_p_calc['Combined_Peak'] = calf_p_calc[['Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)']].max(axis=1)
                    calf_row = calf_p_calc.loc[calf_p_calc['Combined_Peak'].idxmax()]
                    max_calf_l = calf_row.get('Peak Vertical Force [N] (L)', 0.0)
                    max_calf_r = calf_row.get('Peak Vertical Force [N] (R)', 0.0)
                    date_calf = calf_row['Test Date'].strftime('%Y-%m-%d') if pd.notna(calf_row['Test Date']) else "N/A"
                else:
                    max_calf_l, max_calf_r, date_calf = 0.0, 0.0, "N/A"

                # Hip Adduction
                hip_ad_p = hip_p[hip_p['Direction'].astype(str).str.contains('AD', case=False, na=False)] if not hip_p.empty and 'Direction' in hip_p.columns else pd.DataFrame()
                if not hip_ad_p.empty:
                    hip_ad_calc = hip_ad_p.copy()
                    hip_ad_calc['Combined_Peak'] = hip_ad_calc[['L Max Force (N)', 'R Max Force (N)']].max(axis=1)
                    ad_row = hip_ad_calc.loc[hip_ad_calc['Combined_Peak'].idxmax()]
                    max_hip_ad_l = ad_row.get('L Max Force (N)', 0.0)
                    max_hip_ad_r = ad_row.get('R Max Force (N)', 0.0)
                    date_hip_ad = ad_row['Test Date'].strftime('%Y-%m-%d') if pd.notna(ad_row['Test Date']) else "N/A"
                else:
                    max_hip_ad_l, max_hip_ad_r, date_hip_ad = 0.0, 0.0, "N/A"

                # Hip Abduction
                hip_ab_p = hip_p[hip_p['Direction'].astype(str).str.contains('AB', case=False, na=False)] if not hip_p.empty and 'Direction' in hip_p.columns else pd.DataFrame()
                if not hip_ab_p.empty:
                    hip_ab_calc = hip_ab_p.copy()
                    hip_ab_calc['Combined_Peak'] = hip_ab_calc[['L Max Force (N)', 'R Max Force (N)']].max(axis=1)
                    ab_row = hip_ab_calc.loc[hip_ab_calc['Combined_Peak'].idxmax()]
                    max_hip_ab_l = ab_row.get('L Max Force (N)', 0.0)
                    max_hip_ab_r = ab_row.get('R Max Force (N)', 0.0)
                    date_hip_ab = ab_row['Test Date'].strftime('%Y-%m-%d') if pd.notna(ab_row['Test Date']) else "N/A"
                else:
                    max_hip_ab_l, max_hip_ab_r, date_hip_ab = 0.0, 0.0, "N/A"

                # Shoulder IR
                sh_ir_p = sh_p[sh_p['Direction'].astype(str).str.contains('Internal|IR', case=False, na=False)] if not sh_p.empty and 'Direction' in sh_p.columns else pd.DataFrame()
                if not sh_ir_p.empty:
                    sh_ir_calc = sh_ir_p.copy()
                    sh_ir_calc['Combined_Peak'] = sh_ir_calc[['L Max Force (N)', 'R Max Force (N)']].max(axis=1)
                    ir_row = sh_ir_calc.loc[sh_ir_calc['Combined_Peak'].idxmax()]
                    max_sh_ir_l = ir_row.get('L Max Force (N)', 0.0)
                    max_sh_ir_r = ir_row.get('R Max Force (N)', 0.0)
                    date_sh_ir = ir_row['Test Date'].strftime('%Y-%m-%d') if pd.notna(ir_row['Test Date']) else "N/A"
                else:
                    max_sh_ir_l, max_sh_ir_r, date_sh_ir = 0.0, 0.0, "N/A"

                # Shoulder ER
                sh_er_p = sh_p[sh_p['Direction'].astype(str).str.contains('External|ER', case=False, na=False)] if not sh_p.empty and 'Direction' in sh_p.columns else pd.DataFrame()
                if not sh_er_p.empty:
                    sh_er_calc = sh_er_p.copy()
                    sh_er_calc['Combined_Peak'] = sh_er_calc[['L Max Force (N)', 'R Max Force (N)']].max(axis=1)
                    er_sh_row = sh_er_calc.loc[sh_er_calc['Combined_Peak'].idxmax()]
                    max_sh_er_l = er_sh_row.get('L Max Force (N)', 0.0)
                    max_sh_er_r = er_sh_row.get('R Max Force (N)', 0.0)
                    date_sh_er = er_sh_row['Test Date'].strftime('%Y-%m-%d') if pd.notna(er_sh_row['Test Date']) else "N/A"
                else:
                    max_sh_er_l, max_sh_er_r, date_sh_er = 0.0, 0.0, "N/A"

                # KPI Metrics Cards
                m_c1, m_c2, m_c3, m_c4, m_c5, m_c6 = st.columns(6)
                m_c1.metric("Peak CMJ", f"{max_cmj_h:.1f}")
                m_c2.metric("Peak RSI", f"{max_rsi_val:.2f}")
                m_c3.metric("Peak ASH (L/R)", f"{max_ash_l:.0f} / {max_ash_r:.0f} N")
                m_c4.metric("Peak ER ROM", f"{max(max_er_l, max_er_r):.1f}°")
                m_c5.metric("Peak Calf Raise", f"{max(max_calf_l, max_calf_r):.0f} N")
                m_c6.metric("Hip AD / AB", f"{max(max_hip_ad_l, max_hip_ad_r):.0f} / {max(max_hip_ab_l, max_hip_ab_r):.0f} N")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### Comprehensive Peak Performance Matrix")
                
                ov_summary_data = [
                    {"ASSESSMENT": "Countermovement Jump (Max Height)", "PEAK VALUE": f"{max_cmj_h:.1f}", "DATE": date_cmj_h},
                    {"ASSESSMENT": "Countermovement Jump (Max RSI-Mod)", "PEAK VALUE": f"{max_rsi_val:.2f}", "DATE": date_cmj_rsi},
                    {"ASSESSMENT": "ASH Shoulder (ISO-I) (L/R)", "PEAK VALUE": f"{max_ash_l:.1f} N / {max_ash_r:.1f} N", "DATE": date_ash},
                    {"ASSESSMENT": "External Rotation ROM (L/R)", "PEAK VALUE": f"{max_er_l:.1f}° / {max_er_r:.1f}°", "DATE": date_er},
                    {"ASSESSMENT": "Single Leg Calf Raise (L/R)", "PEAK VALUE": f"{max_calf_l:.1f} N / {max_calf_r:.1f} N", "DATE": date_calf},
                    {"ASSESSMENT": "Hip Adduction (L/R)", "PEAK VALUE": f"{max_hip_ad_l:.1f} N / {max_hip_ad_r:.1f} N", "DATE": date_hip_ad},
                    {"ASSESSMENT": "Hip Abduction (L/R)", "PEAK VALUE": f"{max_hip_ab_l:.1f} N / {max_hip_ab_r:.1f} N", "DATE": date_hip_ab},
                    {"ASSESSMENT": "Shoulder Internal Rotation (L/R)", "PEAK VALUE": f"{max_sh_ir_l:.1f} N / {max_sh_ir_r:.1f} N", "DATE": date_sh_ir},
                    {"ASSESSMENT": "Shoulder External Rotation (L/R)", "PEAK VALUE": f"{max_sh_er_l:.1f} N / {max_sh_er_r:.1f} N", "DATE": date_sh_er}
                ]
                st.dataframe(pd.DataFrame(ov_summary_data), use_container_width=True, hide_index=True)
                
            elif sel_test_tab == "Season Comparison":
                st.markdown("### Multi-Season Testing Performance Comparison")
                c_comp_ath, _ = st.columns([2, 2])
                with c_comp_ath: comp_athlete = st.selectbox("Select Athlete for Cross-Seasonal Comparison", master_athlete_list, key="comp_ath_testing_t4")

                cmj_comp = raw_cmj_df[raw_cmj_df['Name'] == comp_athlete].sort_values('Test Date')
                ash_comp = raw_ash_df[raw_ash_df['Name'] == comp_athlete].sort_values('Test Date')
                er_comp = raw_er_df[raw_er_df['Name'] == comp_athlete].sort_values('Test Date')

                if not cmj_comp.empty or not ash_comp.empty or not er_comp.empty:
                    st.markdown("#### Countermovement Jump Trend Across Seasons")
                    if not cmj_comp.empty:
                        season_order = ["Spring", "Summer", "Pre-Season", "In-Season"]
                        cmj_comp_ordered = cmj_comp.copy()
                        cmj_comp_ordered['Season'] = pd.Categorical(cmj_comp_ordered['Season'], categories=season_order, ordered=True)
            
                        cmj_avg_season = cmj_comp_ordered.groupby('Season', observed=False)[[cmj_col, rsi_col]].mean().reset_index()
                        cmj_avg_season = cmj_avg_season.sort_values('Season')

                        max_h = cmj_avg_season[cmj_col].max() if not cmj_avg_season.empty and not pd.isna(cmj_avg_season[cmj_col].max()) else 50.0
                        max_r = cmj_avg_season[rsi_col].max() if not cmj_avg_season.empty and not pd.isna(cmj_avg_season[rsi_col].max()) else 1.0

                        fig_comp_cmj = make_subplots(specs=[[{"secondary_y": True}]])
                        fig_comp_cmj.add_trace(go.Bar(x=cmj_avg_season['Season'], y=cmj_avg_season[cmj_col], name="Avg CMJ Height", marker_color='#FF8200', text=[f"<b>{val:.1f}</b>" if pd.notna(val) else "" for val in cmj_avg_season[cmj_col]], textposition="inside", insidetextanchor="middle", textfont=dict(color='white', size=13), cliponaxis=False), secondary_y=False)
                        fig_comp_cmj.add_trace(go.Scatter(x=cmj_avg_season['Season'], y=cmj_avg_season[rsi_col], name="Avg RSI-mod", mode='lines+markers+text', text=[f"<b>RSI: {val:.2f}</b>" if pd.notna(val) else "" for val in cmj_avg_season[rsi_col]], textposition="top center", textfont=dict(color='#1D1D1F', size=12), line=dict(color='#4895DB', width=3), marker=dict(size=10, color='#4895DB'), cliponaxis=False), secondary_y=True)
                        fig_comp_cmj.update_layout(template="simple_white", height=420, margin=dict(l=20, r=20, t=70, b=20), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1), xaxis=dict(categoryorder="array", categoryarray=season_order))
                        fig_comp_cmj.update_yaxes(title_text="CMJ Height", range=[0, max_h * 1.30], secondary_y=False)
                        fig_comp_cmj.update_yaxes(title_text="RSI Modified", range=[0, max_r * 1.45], secondary_y=True, showgrid=False)
                        st.plotly_chart(fig_comp_cmj, use_container_width=True, config=LOCKED_CONFIG, key="cmj_cross_season_bar")
                    
                    st.markdown("#### Season-by-Season Best")
                    summary_rows = []
                    for season_period in ['Spring', 'Summer', 'Pre-Season', 'In-Season']:
                        s_cmj = cmj_comp[cmj_comp['Season'] == season_period]
                        s_ash = ash_comp[ash_comp['Season'] == season_period]
                        s_er = er_comp[er_comp['Season'] == season_period]
                        
                        max_cmj = s_cmj[cmj_col].max() if not s_cmj.empty else 0.0
                        max_rsi = s_cmj[rsi_col].max() if not s_cmj.empty else 0.0
                        max_ash_l = s_ash['Peak Vertical Force [N] (L)'].max() if not s_ash.empty and 'Peak Vertical Force [N] (L)' in s_ash.columns else 0.0
                        max_ash_r = s_ash['Peak Vertical Force [N] (R)'].max() if not s_ash.empty and 'Peak Vertical Force [N] (R)' in s_ash.columns else 0.0
                        max_er_l = s_er['L Max ROM (°)'].max() if not s_er.empty and 'L Max ROM (°)' in s_er.columns else 0.0
                        max_er_r = s_er['R Max ROM (°)'].max() if not s_er.empty and 'R Max ROM (°)' in s_er.columns else 0.0
                        
                        summary_rows.append({
                            'Season': season_period,
                            'Max CMJ': round(max_cmj, 1),
                            'Max RSI': round(max_rsi, 2),
                            'Max ASH L (N)': round(max_ash_l, 0),
                            'Max ASH R (N)': round(max_ash_r, 0),
                            'Max ER ROM L (°)': round(max_er_l, 1),
                            'Max ER ROM R (°)': round(max_er_r, 1)
                        })
                    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            elif sel_test_tab in ["In-Season Testing", "Pre-Season Testing", "Summer Testing", "Spring Testing"]:
                s_label = sel_test_tab.replace(" Testing", "")
                c_t_ath, _ = st.columns([2, 2])
                with c_t_ath: selected_athlete_test = st.selectbox(f"Select Athlete ({s_label})", master_athlete_list, key=f"nav_ath_test_{s_label}")
                
                meta_lookup = full_df_unfiltered[full_df_unfiltered['Name'] == selected_athlete_test]
                photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"

                st.markdown(f'<div style="display:flex; align-items:center; gap:20px; padding:15px; background:#f8f9fa; border-radius:15px; border-left:6px solid #FF8200; margin-bottom:20px;"><img src="{photo_val}" class="gallery-photo" style="width:80px; height:80px;"><div><h2 style="margin:0; color:#1D1D1F;">{selected_athlete_test}</h2><p style="margin:0; color:#4895DB; font-weight:700; font-size:16px;">{pos_val} | {s_label} Testing Profile</p></div></div>', unsafe_allow_html=True)
                st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">COUNTERMOVEMENT JUMP</h4>', unsafe_allow_html=True)
                cmj_t_data = raw_cmj_df[(raw_cmj_df['Name'] == selected_athlete_test) & (raw_cmj_df['Season'] == s_label)].sort_values('Test Date')
                
                if not cmj_t_data.empty:
                    jc1, jc2 = st.columns([1.5, 3.5])
                    with jc1:
                        baseline_cmj = cmj_t_data.head(1)
                        base_h = baseline_cmj.iloc[-1][cmj_col] if not baseline_cmj.empty else 0.0
                        base_rsi = baseline_cmj.iloc[-1][rsi_col] if not baseline_cmj.empty else 0.0
                        latest_cmj = cmj_t_data.iloc[-1]
                        cur_h, cur_rsi = latest_cmj[cmj_col], latest_cmj[rsi_col]
                        p_diff_h = ((cur_h - base_h) / base_h * 100) if base_h > 0 else 0
                        p_diff_rsi = ((cur_rsi - base_rsi) / base_rsi * 100) if base_rsi > 0 else 0
                        color_h = "#28a745" if cur_h >= base_h else "#dc3545"
                        color_rsi = "#28a745" if cur_rsi >= base_rsi else "#dc3545"

                        sc1, sc2 = st.columns(2)
                        with sc1: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_h}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_h:.1f}</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">CMJ HEIGHT</span></div></div>', unsafe_allow_html=True)
                        with sc2: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_rsi}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_rsi:.2f}</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RSI MOD</span></div></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> CMJ: {p_diff_h:+.1f}% | RSI: {p_diff_rsi:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base Values:</b> CMJ: {base_h:.1f} | RSI: {base_rsi:.2f}</p></div>', unsafe_allow_html=True)

                    with jc2:
                        fig_cmj_t = make_subplots(specs=[[{"secondary_y": True}]])
                        fig_cmj_t.add_trace(go.Scatter(x=cmj_t_data['Test Date'], y=cmj_t_data[cmj_col], name="Jump Height", mode='lines+markers', line=dict(color='#FF8200', width=3)), secondary_y=False)
                        fig_cmj_t.add_trace(go.Scatter(x=cmj_t_data['Test Date'], y=cmj_t_data[rsi_col], name="RSI Modified", mode='lines+markers', line=dict(color='#4895DB', dash='dot', width=2)), secondary_y=True)
                        fig_cmj_t.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                        st.plotly_chart(fig_cmj_t, use_container_width=True, config=LOCKED_CONFIG, key=f"cmj_chart_test_{s_label}")
                else:
                    st.info(f"No Countermovement Jump testing records logged for {selected_athlete_test} in {s_label}.")

                st.markdown('<hr style="display:block !important; margin:15px 0; border:0; border-top:1px solid #E5E5E7;" />', unsafe_allow_html=True)
                st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">ASH SHOULDER: ISO I</h4>', unsafe_allow_html=True)
                ash_t_data = raw_ash_df[(raw_ash_df['Name'] == selected_athlete_test) & (raw_ash_df['Season'] == s_label)].sort_values('Test Date')
                
                if not ash_t_data.empty:
                    ac1, ac2 = st.columns([1.5, 3.5])
                    with ac1:
                        latest_date_ash = ash_t_data['Test Date'].iloc[-1]
                        today_ash_rows = ash_t_data[ash_t_data['Test Date'] == latest_date_ash]
                        row_i = today_ash_rows[today_ash_rows['Isometric Type'].str.contains('I', case=False, na=False)] if 'Isometric Type' in today_ash_rows.columns else today_ash_rows
                        li = row_i.iloc[-1]['Peak Vertical Force [N] (L)'] if not row_i.empty else 0.0
                        ri = row_i.iloc[-1]['Peak Vertical Force [N] (R)'] if not row_i.empty else 0.0
                        asym_i = row_i.iloc[-1]['Peak Vertical Force [N] (Asym)(%)'] if not row_i.empty else 0.0
                        baseline_ash = ash_t_data.head(1)
                        base_li = baseline_ash.iloc[-1]['Peak Vertical Force [N] (L)'] if not baseline_ash.empty else 0.0
                        base_ri = baseline_ash.iloc[-1]['Peak Vertical Force [N] (R)'] if not baseline_ash.empty else 0.0
                        pct_l = ((li - base_li) / base_li * 100) if base_li > 0 else 0
                        pct_r_ash = ((ri - base_ri) / base_ri * 100) if base_ri > 0 else 0
                        color_ash_l = "#28a745" if li >= 100 else "#dc3545"
                        color_ash_r = "#28a745" if ri >= 100 else "#dc3545"

                        sc1, sc2 = st.columns(2)
                        with sc1: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_ash_l}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{li:.0f} N</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">LEFT</span></div></div>', unsafe_allow_html=True)
                        with sc2: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_ash_r}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{ri:.0f} N</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RIGHT</span></div></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>Asymmetry:</b> {asym_i:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> L: {pct_l:+.1f}% | R: {pct_r_ash:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base Force:</b> L: {base_li:.0f} N | R: {base_ri:.0f} N</p></div>', unsafe_allow_html=True)
                    with ac2:
                        fig_ash_t = go.Figure()
                        fig_ash_t.add_trace(go.Scatter(x=ash_t_data['Test Date'], y=ash_t_data['Peak Vertical Force [N] (L)'], name="Left Peak Force", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                        fig_ash_t.add_trace(go.Scatter(x=ash_t_data['Test Date'], y=ash_t_data['Peak Vertical Force [N] (R)'], name="Right Peak Force", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                        fig_ash_t.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                        st.plotly_chart(fig_ash_t, use_container_width=True, config=LOCKED_CONFIG, key=f"ash_chart_test_{s_label}")
                else:
                    st.info(f"No ASH Shoulder testing records logged for {selected_athlete_test} in {s_label}.")

                st.markdown('<hr style="display:block !important; margin:15px 0; border:0; border-top:1px solid #E5E5E7;" />', unsafe_allow_html=True)
                st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">EXTERNAL ROTATION: ROM</h4>', unsafe_allow_html=True)
                er_t_data = raw_er_df[(raw_er_df['Name'] == selected_athlete_test) & (raw_er_df['Season'] == s_label)].sort_values('Test Date')
                if not er_t_data.empty:
                    ec1, ec2 = st.columns([1.5, 3.5])
                    with ec1:
                        baseline_er = er_t_data.head(1)
                        base_l_rom = float(baseline_er.iloc[-1].get('L Max ROM (°)', 0.0)) if not baseline_er.empty else 0.0
                        base_r_rom = float(baseline_er.iloc[-1].get('R Max ROM (°)', 0.0)) if not baseline_er.empty else 0.0
                        latest_er = er_t_data.iloc[-1]
                        cur_l_rom = float(latest_er.get('L Max ROM (°)', 0.0))
                        cur_r_rom = float(latest_er.get('R Max ROM (°)', 0.0))
                        cur_asym_rom = float(latest_er.get('ROM Asymmetry (%)', 0.0))
                        rom_pct_l = ((cur_l_rom - base_l_rom) / base_l_rom * 100) if base_l_rom > 0 else 0.0
                        rom_pct_r = ((cur_r_rom - base_r_rom) / base_r_rom * 100) if base_r_rom > 0 else 0.0
                        color_er_l = "#28a745" if cur_l_rom >= 110 else "#ffc107" if 90 <= cur_l_rom <= 109 else "#dc3545"
                        color_er_r = "#28a745" if cur_r_rom >= 110 else "#ffc107" if 90 <= cur_r_rom <= 109 else "#dc3545"

                        sc1, sc2 = st.columns(2)
                        with sc1: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_er_l}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_l_rom:.1f}°</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">LEFT</span></div></div>', unsafe_allow_html=True)
                        with sc2: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_er_r}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_r_rom:.1f}°</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RIGHT</span></div></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>Asymmetry:</b> {cur_asym_rom:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> L: {rom_pct_l:+.1f}% | R: {rom_pct_r:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base ROM:</b> L: {base_l_rom:.1f}° | R: {base_r_rom:.1f}°</p></div>', unsafe_allow_html=True)
                    with ec2:
                        fig_er_t = go.Figure()
                        fig_er_t.add_trace(go.Scatter(x=er_t_data['Test Date'], y=er_t_data['L Max ROM (°)'], name="Left Max ROM", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                        fig_er_t.add_trace(go.Scatter(x=er_t_data['Test Date'], y=er_t_data['R Max ROM (°)'], name="Right Max ROM", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                        fig_er_t.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                        st.plotly_chart(fig_er_t, use_container_width=True, config=LOCKED_CONFIG, key=f"er_chart_test_{s_label}")
                else:
                    st.info(f"No External Rotation testing records logged for {selected_athlete_test} in {s_label}.")

    except Exception as e:
        st.error(f"Sync Error: {e}")
