import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta, datetime
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
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
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


# --- 2. PASSWORD VALIDATION ---
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
            return "#D97706", "#FEF3C7", "Under-training"
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
        m = date_val.month
        d = date_val.day
        y = date_val.year
    
        if y == 2026 and m == 7 and d >= 30: return 'Pre-Season'
        elif y == 2026 and m >= 8: return 'Pre-Season'
        elif 1 <= m <= 4: return 'Spring'
        elif m == 5 and d >= 26: return 'Summer'
        elif m >= 5 and m <= 7: return 'Summer'
        else: return 'Spring'

    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    match_df = pd.read_csv(st.secrets["MATCHES_SHEET_URL"])
    
    df = heavy_sanitize(df)
    df['Sheet_Order'] = range(len(df))
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    if 'Week' in df.columns:
        df['Week'] = pd.to_numeric(df['Week'].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    df['Session_Type'] = df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
    df['Season'] = df['Date'].apply(assign_season)

    match_df = heavy_sanitize(match_df)
    match_df['Sheet_Order'] = range(len(match_df))
    match_df['Date'] = pd.to_datetime(match_df['Date'], errors='coerce')
    if 'Week' in match_df.columns:
        match_df['Week'] = pd.to_numeric(match_df['Week'].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    match_df['Session_Name'] = match_df['Activity'].fillna(match_df['Date'].dt.strftime('%m/%d/%Y'))
    match_df['Position'] = match_df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    match_df['PhotoURL'] = match_df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    match_df['Session_Type'] = match_df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
    match_df['Season'] = match_df['Date'].apply(assign_season)

    cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
    cmj_df.columns = cmj_df.columns.str.strip()
    if 'Athlete' in cmj_df.columns:
        cmj_df.rename(columns={'Athlete': 'Name'}, inplace=True)
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
        ash_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
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
        er_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        er_df['Test Date'] = pd.to_datetime(er_df['Test Date'], errors='coerce')
        
        for col in ['L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)']:
            if col in er_df.columns:
                er_df[col] = pd.to_numeric(
                    er_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), 
                    errors='coerce'
                ).fillna(0.0)
                
        er_df['Season'] = er_df['Test Date'].apply(assign_season)
    except:
        er_df = pd.DataFrame(columns=['Name', 'Test Date', 'L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)', 'Season'])

    # Calf Sheet
    try:
        calf_df = pd.read_csv(st.secrets["CALF_SHEET_URL"])
        calf_df.columns = calf_df.columns.str.strip()
        calf_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        calf_df['Test Date'] = pd.to_datetime(calf_df['Test Date'], errors='coerce')
        calf_df['Season'] = calf_df['Test Date'].apply(assign_season)
    except:
        calf_df = pd.DataFrame(columns=['Name', 'Test Date', 'Season'])

    # Hip Sheet
    try:
        hip_df = pd.read_csv(st.secrets["HIP_SHEET_URL"])
        hip_df.columns = hip_df.columns.str.strip()
        hip_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        hip_df['Test Date'] = pd.to_datetime(hip_df['Test Date'], errors='coerce')
        hip_df['Season'] = hip_df['Test Date'].apply(assign_season)
    except:
        hip_df = pd.DataFrame(columns=['Name', 'Test Date', 'Season'])

    # Shoulder Sheet
    try:
        shoulder_df = pd.read_csv(st.secrets["SHOULDER_SHEET_URL"])
        shoulder_df.columns = shoulder_df.columns.str.strip()
        shoulder_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        shoulder_df['Test Date'] = pd.to_datetime(shoulder_df['Test Date'], errors='coerce')
        shoulder_df['Season'] = shoulder_df['Test Date'].apply(assign_season)
    except:
        shoulder_df = pd.DataFrame(columns=['Name', 'Test Date', 'Season'])

    phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
    phase_df = heavy_sanitize(phase_df)
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
def compute_athlete_ewma_calendar(df_player, metrics_list):
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
def create_wellness_gauge(score_val, height=210):
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
        line=dict(color='#111827', width=4)
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
        font=dict(size=13, color="white", weight="bold"),
        bgcolor="#1E293B",
        borderpad=4,
        bordercolor="#1E293B"
    )
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=5, b=5),
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
        st.sidebar.markdown("### View Selection")
        view_options = ["Spring", "Summer", "Pre-Season", "Testing", "Comparison", "ACWR"]
        if "global_season_toggle" not in st.session_state:
            st.session_state.global_season_toggle = "Pre-Season"
            
        selected_season = st.sidebar.radio(
            "Select View Mode", 
            view_options, 
            key="global_season_toggle"
        )
        
        if selected_season not in ["Testing", "Comparison", "Compliance", "ACWR"]:
            st.sidebar.info(f"Currently displaying: {selected_season} Season Performance Data.")
            df_master = raw_df[raw_df['Season'] == selected_season].copy()
            match_master = raw_match_df[raw_match_df['Season'] == selected_season].copy()
            cmj_master = raw_cmj_df[raw_cmj_df['Season'] == selected_season].copy()
            ash_master = raw_ash_df[raw_ash_df['Season'] == selected_season].copy()
            er_master = raw_er_df[raw_er_df['Season'] == selected_season].copy()
            calf_master = raw_calf_df[raw_calf_df['Season'] == selected_season].copy()
            hip_master = raw_hip_df[raw_hip_df['Season'] == selected_season].copy()
            shoulder_master = raw_shoulder_df[raw_shoulder_df['Season'] == selected_season].copy()
            phase_master = raw_phase_df[raw_phase_df['Season'] == selected_season].copy()
        else:
            df_master, match_master, cmj_master, ash_master, er_master, calf_master, hip_master, shoulder_master, phase_master = raw_df, raw_match_df, raw_cmj_df, raw_ash_df, raw_er_df, raw_calf_df, raw_hip_df, raw_shoulder_df, raw_phase_df

        session_list = df_master.sort_values('Date', ascending=False)['Session_Name'].dropna().unique().tolist() if not df_master.empty else []

        full_df_unfiltered = raw_df.copy()
        all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
        metrics_to_score = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]
        
        cmj_col = 'Jump Height (Imp-Mom) [in]' if 'Jump Height (Imp-Mom) [in]' in raw_cmj_df.columns else 'Jump Height (Imp-Mom) [cm]'
        rsi_col = 'RSI-modified [m/s]'

        master_athlete_list = sorted(list(
            set(raw_df['Name'].unique()) | 
            set(raw_cmj_df['Name'].unique()) | 
            set(raw_ash_df['Name'].unique()) | 
            set(raw_er_df['Name'].unique())
        ))

        st.markdown('<div class="main-logo-container" style="text-align: center; margin-top: 10px; margin-bottom: 15px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120"><div style="color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;">LADY VOLS VOLLEYBALL PERFORMANCE</div></div>', unsafe_allow_html=True)
        
        # ==========================================
        # --- TESTING TAB --------------------------
        # ==========================================
        if selected_season == "Testing":
            st.markdown('<div class="section-header">Testing Profile</div>', unsafe_allow_html=True)
            
            testing_tabs_list = [
                "CMJ Dashboard",
                "Spring Testing", 
                "Summer Testing", 
                "Pre-Season Testing", 
                "Intake Testing", 
                "Overall Testing Profile", 
                "Season Comparison"
            ]
            if "testing_active_subtab" not in st.session_state:
                st.session_state.testing_active_subtab = testing_tabs_list[0]
                
            selected_testing_tab = st.radio(
                "Testing Sub Navigation",
                testing_tabs_list,
                key="testing_active_subtab",
                horizontal=True,
                label_visibility="collapsed"
            )
            
            # --- TAB 0: CMJ DASHBOARD ---
            if selected_testing_tab == "CMJ Dashboard":
                cmj_view_modes = ["Individual Athlete", "Team CMJ Summary"]
                if "cmj_view_mode_subtab" not in st.session_state:
                    st.session_state.cmj_view_mode_subtab = cmj_view_modes[0]
                    
                sel_cmj_mode = st.radio(
                    "CMJ View Mode",
                    cmj_view_modes,
                    key="cmj_view_mode_subtab",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                # Exact References Sheet Formulas
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

                # --- SUB-TAB 1: INDIVIDUAL ATHLETE DEEP DIVE ---
                if sel_cmj_mode == "Individual Athlete":
                    c_cmj_ath, c_cmj_date, c_cmj_comp = st.columns([2, 1.5, 1.5])
                    with c_cmj_ath:
                        sel_cmj_ath = st.selectbox("Select Athlete", master_athlete_list, key="cmj_dash_ath_sel")
                    
                    ath_cmj_all = raw_cmj_df[raw_cmj_df['Name'] == sel_cmj_ath].sort_values('Test Date')
                    
                    if ath_cmj_all.empty:
                        st.info(f"No CMJ records found for {sel_cmj_ath}.")
                    else:
                        valid_dates = ath_cmj_all['Test Date'].dropna().dt.strftime('%m/%d/%y').tolist()
                        with c_cmj_date:
                            sel_test_date_str = st.selectbox("Test Date", valid_dates, index=len(valid_dates)-1, key="cmj_dash_date_sel")
                        with c_cmj_comp:
                            comp_factor = st.selectbox("Comparison Factor", ["Individual", "Team", "Position"], key="cmj_dash_comp_sel")

                        # Current Trial Row
                        cur_idx_list = ath_cmj_all[ath_cmj_all['Test Date'].dt.strftime('%m/%d/%y') == sel_test_date_str].index.tolist()
                        cur_test_row = ath_cmj_all.loc[cur_idx_list[-1]]
                        
                        # Active Season Determination from Current Test Date
                        curr_season = cur_test_row.get('Season', 'Pre-Season')
                        ath_season_data = ath_cmj_all[ath_cmj_all['Season'] == curr_season].sort_values('Test Date')
                        if ath_season_data.empty:
                            ath_season_data = ath_cmj_all

                        # Baseline = First recorded test of this active season
                        base_test_row = ath_season_data.iloc[0]
                        
                        # Previous Trial Row (Trial - 1 within this season)
                        season_indices = list(ath_season_data.index)
                        if cur_idx_list[-1] in season_indices:
                            cur_pos = season_indices.index(cur_idx_list[-1])
                            prev_test_row = ath_season_data.iloc[max(0, cur_pos - 1)]
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

                        # Calculate Final Excel Readiness/Wellness Score
                        raw_readiness_avg = compute_excel_readiness_score(cur_test_row, prev_test_row)
                        display_score = int(round(raw_readiness_avg))

                        top_col1, top_col2, top_col3 = st.columns([1.2, 2.2, 1.6])

                        # Athlete Card
                        with top_col1:
                            ath_card_html = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:18px; text-align:center; padding:8px 10px; border-radius:6px 6px 0 0;">{sel_cmj_ath}</div><div style="border:1px solid #E2E8F0; border-top:none; border-radius:0 0 6px 6px; padding:16px; background:white; display:flex; align-items:center; gap:16px;"><img src="{photo_val}" style="width:95px; height:95px; border-radius:8px; object-fit:contain; border:2px solid #FF8200;"><div style="font-size:14px; line-height:1.8; color:#1D1D1F;"><b>Position:</b> {pos_val}</div></div><div style="background:#4895DB; color:white; font-weight:800; font-size:13px; text-align:center; padding:6px; margin-top:10px; border-radius:4px;">Comparison: {comp_factor}</div>"""
                            st.markdown(ath_card_html, unsafe_allow_html=True)

                        # Data Table (Replicating Dashboard O5:Z14 using seasonal baseline)
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
                            
                            full_table_html = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:14px; text-align:center; padding:6px; border-radius:6px 6px 0 0;">Countermovement Jump Performance</div><table class="scout-table" style="width:100%; border:1px solid #E2E8F0; border-top:none; background:white; border-collapse:collapse; margin-bottom:0;"><thead><tr style="background:#F8FAFC; color:#64748B; font-size:11px;"><th style="text-align:left !important; padding:6px 12px;">Metric</th><th style="padding:6px;">Baseline ({curr_season})</th><th style="padding:6px; background:#EBF5FF; color:#1E40AF;">Current</th><th style="padding:6px;">% Change</th></tr></thead><tbody>{table_rows_str}</tbody></table>"""
                            st.markdown(full_table_html, unsafe_allow_html=True)

                        # Calibrated Wellness Score Gauge
                        with top_col3:
                            gauge_header = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:14px; text-align:center; padding:6px; border-radius:6px 6px 0 0;">Wellness Score<br><span style="font-size:11px; font-weight:600;">{sel_test_date_str}</span></div>"""
                            st.markdown(gauge_header, unsafe_allow_html=True)
                            fig_gauge = create_wellness_gauge(display_score, height=230)
                            st.plotly_chart(fig_gauge, use_container_width=True, config=LOCKED_CONFIG, key="cmj_wellness_gauge_ind")

                        st.markdown("<br>", unsafe_allow_html=True)

                        # T-Score Standards
                        st.markdown(f'<div class="section-header">Countermovement Jump Performance Standards ({comp_factor})</div>', unsafe_allow_html=True)
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
                                if ref_pool_df.empty:
                                    ref_pool_df = raw_cmj_df
                                title_prefix = "Position"
                            else: # Team
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
                                        if bm["invert"]:
                                            z_val = -1.0 * ((ath_v - m_mean) / m_std)
                                        else:
                                            z_val = (ath_v - m_mean) / m_std
                                        
                                        t_val = 50.0 + (z_val * 10.0)
                                        t_scores.append(round(min(100.0, max(0.0, t_val)), 1))
                                    else:
                                        t_scores.append(50.0)
                                else:
                                    t_scores.append(50.0)

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

                            for b in bands:
                                fig_bands.add_hrect(
                                    y0=b["y0"], y1=b["y1"], 
                                    fillcolor=b["color"], 
                                    line_width=0, 
                                    opacity=1.0,
                                    layer="below"
                                )

                            fig_bands.add_trace(go.Bar(
                                x=x_labels,
                                y=t_scores,
                                marker=dict(color='#3A3D40', line=dict(color='#1A1C1E', width=1.5)),
                                width=0.42,
                                text=[f"<b>{val:.1f}</b>" for val in t_scores],
                                textposition='inside',
                                insidetextanchor='middle',
                                textfont=dict(color='white', size=12),
                                cliponaxis=False
                            ))

                            category_boxes = [
                                {"x0": -0.45, "x1": 2.45, "text": "Speed", "bg": "#F8E2E2"},
                                {"x0": 2.55, "x1": 6.45, "text": "Strength", "bg": "#EBF3DF"},
                                {"x0": 6.55, "x1": 7.45, "text": "Power", "bg": "#D3E2F4"},
                                {"x0": 7.55, "x1": 9.45, "text": "Jump Strategy", "bg": "#E6E1F2"}
                            ]

                            for cb in category_boxes:
                                fig_bands.add_shape(
                                    type="rect",
                                    xref="x", yref="paper",
                                    x0=cb["x0"], x1=cb["x1"],
                                    y0=-0.16, y1=-0.08,
                                    fillcolor=cb["bg"],
                                    line=dict(width=0),
                                    layer="above"
                                )
                                fig_bands.add_annotation(
                                    xref="x", yref="paper",
                                    x=(cb["x0"] + cb["x1"]) / 2,
                                    y=-0.12,
                                    text=f"<b>{cb['text']}</b>",
                                    showarrow=False,
                                    font=dict(size=11, color="#111827"),
                                    align="center"
                                )

                            fig_bands.update_layout(
                                height=450,
                                margin=dict(l=30, r=10, t=15, b=65),
                                plot_bgcolor='white',
                                paper_bgcolor='white',
                                xaxis=dict(
                                    tickangle=0, 
                                    tickfont=dict(size=10.5, weight='bold', color='#111827'),
                                    showgrid=False,
                                    showline=True,
                                    linecolor='#6B7280'
                                ),
                                yaxis=dict(
                                    range=[0, 100], 
                                    dtick=10, 
                                    showgrid=False, 
                                    showline=True, 
                                    linecolor='#6B7280',
                                    title=dict(text=f"{title_prefix} T-Score Performance Rating", font=dict(size=12, weight='bold', color='#4B5563'))
                                ),
                                showlegend=False
                            )
                            st.plotly_chart(fig_bands, use_container_width=True, config=LOCKED_CONFIG, key=f"cmj_standards_chart_{comp_factor}")

                        with legend_col:
                            legend_table_html = """<div style="background:#4895DB; color:white; font-weight:800; font-size:12px; text-align:center; padding:6px; border-radius:4px 4px 0 0;">Performance Bands<br><span style="font-size:10px; font-weight:600;">T-Score Rating</span></div><table style="width:100%; border-collapse:collapse; font-size:11px; text-align:center; font-weight:700;"><tr style="background:#1C7426; color:white;"><td style="padding:4px;">Excellent</td><td>> 80</td></tr><tr style="background:#33A338; color:white;"><td style="padding:4px;">Very Good</td><td>70 - 80</td></tr><tr style="background:#81D350; color:#111827;"><td style="padding:4px;">Good</td><td>60 - 70</td></tr><tr style="background:#C3E8A8; color:#111827;"><td style="padding:4px;">Above Avg.</td><td>55 - 60</td></tr><tr style="background:#FFFFFF; color:#111827; border-top:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0;"><td style="padding:4px;">Average</td><td>45 - 55</td></tr><tr style="background:#F8A2A2; color:#111827;"><td style="padding:4px;">Below Avg.</td><td>40 - 45</td></tr><tr style="background:#F05656; color:white;"><td style="padding:4px;">Poor</td><td>30 - 40</td></tr><tr style="background:#E60000; color:white;"><td style="padding:4px;">Very Poor</td><td>20 - 30</td></tr><tr style="background:#A00000; color:white;"><td style="padding:4px;">Extremely Poor</td><td>< 20</td></tr></table>"""
                            st.markdown(legend_table_html, unsafe_allow_html=True)

                # --- SUB-TAB 2: TEAM CMJ SUMMARY (SIDE-BY-SIDE WELLNESS GAUGES) ---
                elif sel_cmj_mode == "Team CMJ Summary":
                    st.markdown("### Team Wellness Score Overview")
                    
                    team_cmj_dates = sorted(raw_cmj_df['Test Date'].dropna().dt.strftime('%m/%d/%y').unique().tolist(), reverse=True)
                    
                    c_sum_d1, c_sum_d2 = st.columns([1.5, 2])
                    with c_sum_d1:
                        sel_team_cmj_date = st.selectbox("Evaluation Test Date", team_cmj_dates, index=0, key="team_cmj_eval_date")
                    with c_sum_d2:
                        team_pos_f = st.selectbox("Filter by Position", ["All Positions"] + sorted([p for p in full_df_unfiltered['Position'].unique() if p != "N/A"]), key="team_cmj_pos_filter")

                    team_cmj_cards = []
                    
                    for ath_name in sorted(raw_cmj_df['Name'].unique()):
                        ath_sub_cmj = raw_cmj_df[raw_cmj_df['Name'] == ath_name].sort_values('Test Date')
                        if ath_sub_cmj.empty:
                            continue
                        
                        meta_row = full_df_unfiltered[full_df_unfiltered['Name'] == ath_name]
                        pos_str = meta_row['Position'].iloc[0] if not meta_row.empty else "N/A"
                        photo_url = meta_row['PhotoURL'].iloc[0] if not meta_row.empty else "https://www.w3schools.com/howto/img_avatar.png"
                        
                        if team_pos_f != "All Positions" and pos_str != team_pos_f:
                            continue
                            
                        ath_date_match = ath_sub_cmj[ath_sub_cmj['Test Date'].dt.strftime('%m/%d/%y') == sel_team_cmj_date]
                        if ath_date_match.empty:
                            continue
                            
                        target_row = ath_date_match.iloc[-1]
                        
                        # Active Season
                        ath_season = target_row.get('Season', 'Pre-Season')
                        ath_season_sub = ath_sub_cmj[ath_sub_cmj['Season'] == ath_season].sort_values('Test Date')
                        if ath_season_sub.empty:
                            ath_season_sub = ath_sub_cmj
                            
                        season_indices = list(ath_season_sub.index)
                        if target_row.name in season_indices:
                            cur_pos = season_indices.index(target_row.name)
                            prev_row = ath_season_sub.iloc[max(0, cur_pos - 1)]
                        else:
                            prev_row = target_row
                        
                        readiness_pct = int(round(compute_excel_readiness_score(target_row, prev_row)))
                        
                        team_cmj_cards.append({
                            "Athlete": ath_name,
                            "PhotoURL": photo_url,
                            "Position": pos_str,
                            "Readiness %": readiness_pct
                        })

                    if team_cmj_cards:
                        # Top Metrics Overview
                        c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
                        avg_team_readiness = sum(c['Readiness %'] for c in team_cmj_cards) / len(team_cmj_cards)
                        peak_count = sum(1 for r in team_cmj_cards if r['Readiness %'] >= 90)
                        fatigue_count = sum(1 for r in team_cmj_cards if r['Readiness %'] < 80)
                        
                        c_kpi1.metric("Athletes Evaluated", len(team_cmj_cards))
                        c_kpi2.metric("Team Mean Wellness", f"{avg_team_readiness:.1f}%")
                        c_kpi3.metric("Optimal (>=90%)", peak_count)
                        c_kpi4.metric("Fatigued (<80%)", fatigue_count)
                        st.markdown("<hr style='border:0; border-top:1px solid #E2E8F0; margin:15px 0;'>", unsafe_allow_html=True)

                        # Display Side-by-Side (2 Athletes Per Row)
                        for i in range(0, len(team_cmj_cards), 2):
                            row_cols = st.columns(2)
                            for j in range(2):
                                if i + j < len(team_cmj_cards):
                                    card_info = team_cmj_cards[i + j]
                                    with row_cols[j]:
                                        st.markdown(f"""
                                            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:15px; margin-bottom:15px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                                                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #FF8200; padding-bottom:8px; margin-bottom:10px;">
                                                    <div style="display:flex; align-items:center; gap:12px;">
                                                        <img src="{card_info['PhotoURL']}" style="width:48px; height:48px; border-radius:50%; object-fit:cover; border:2px solid #FF8200;">
                                                        <div>
                                                            <div style="font-size:16px; font-weight:900; color:#111827;">{card_info['Athlete']}</div>
                                                            <div style="font-size:12px; font-weight:600; color:#4895DB;">{card_info['Position']}</div>
                                                        </div>
                                                    </div>
                                                    <div style="text-align:right;">
                                                        <span style="background-color:#F1F5F9; color:#475569; font-size:11px; font-weight:700; padding:4px 10px; border-radius:12px;">{sel_team_cmj_date}</span>
                                                    </div>
                                                </div>
                                                <div style="font-size:12px; font-weight:800; color:#64748B; text-align:center; text-transform:uppercase; letter-spacing:0.5px; margin-top:5px;">Wellness Score</div>
                                            </div>
                                        """, unsafe_allow_html=True)
                                        
                                        # Render actual gauge inside card
                                        gauge_fig = create_wellness_gauge(card_info['Readiness %'], height=185)
                                        st.plotly_chart(gauge_fig, use_container_width=True, config=LOCKED_CONFIG, key=f"gauge_team_{card_info['Athlete']}_{sel_team_cmj_date}")
                    else:
                        st.info(f"No Countermovement Jump testing records logged on {sel_team_cmj_date}.")

            # --- SEASON SPECIFIC TESTING TABS ---
            elif selected_testing_tab in ["Spring Testing", "Summer Testing", "Pre-Season Testing"]:
                s_label = selected_testing_tab.replace(" Testing", "")
                c_t_ath, _ = st.columns([2, 2])
                with c_t_ath:
                    selected_athlete_test = st.selectbox(f"Select Athlete ({s_label})", master_athlete_list, key=f"nav_ath_test_{s_label}")
                
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
                        pct_r = ((ri - base_ri) / base_ri * 100) if base_ri > 0 else 0
                        color_ash_l = "#28a745" if li >= 100 else "#dc3545"
                        color_ash_r = "#28a745" if ri >= 100 else "#dc3545"

                        sc1, sc2 = st.columns(2)
                        with sc1: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_ash_l}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{li:.0f} N</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">LEFT</span></div></div>', unsafe_allow_html=True)
                        with sc2: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_ash_r}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{ri:.0f} N</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RIGHT</span></div></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>Asymmetry:</b> {asym_i:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> L: {pct_l:+.1f}% | R: {pct_r:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base Force:</b> L: {base_li:.0f} N | R: {base_ri:.0f} N</p></div>', unsafe_allow_html=True)
                    
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
                        st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>Asymmetry:</b> {cur_asym_rom:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> L: {rom_pct_l:+.1f}% | R: {pct_r:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base ROM:</b> L: {base_l_rom:.1f}° | R: {base_r_rom:.1f}°</p></div>', unsafe_allow_html=True)
                    with ec2:
                        fig_er_t = go.Figure()
                        fig_er_t.add_trace(go.Scatter(x=er_t_data['Test Date'], y=er_t_data['L Max ROM (°)'], name="Left Max ROM", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                        fig_er_t.add_trace(go.Scatter(x=er_t_data['Test Date'], y=er_t_data['R Max ROM (°)'], name="Right Max ROM", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                        fig_er_t.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                        st.plotly_chart(fig_er_t, use_container_width=True, config=LOCKED_CONFIG, key=f"er_chart_test_{s_label}")
                else:
                    st.info(f"No External Rotation testing records logged for {selected_athlete_test} in {s_label}.")

            elif selected_testing_tab == "Intake Testing":
                st.markdown("<h3 style='color:#1D1D1F; font-weight:900; text-transform:uppercase;'>Athlete Intake Assessment</h3>", unsafe_allow_html=True)
                c_int_ath, _ = st.columns([2, 2])
                with c_int_ath:
                    selected_intake_athlete = st.selectbox("Select Athlete for Intake Assessment", master_athlete_list, key="intake_ath_select")

                calf_ath = raw_calf_df[raw_calf_df['Name'] == selected_intake_athlete].sort_values('Test Date')
                hip_ath = raw_hip_df[raw_hip_df['Name'] == selected_intake_athlete].sort_values('Test Date')
                sh_ath = raw_shoulder_df[raw_shoulder_df['Name'] == selected_intake_athlete].sort_values('Test Date')
                isoy_ath = raw_ash_df[(raw_ash_df['Name'] == selected_intake_athlete) & (raw_ash_df['Isometric Type'].str.contains('ISO-Y|Y', case=False, na=False))].sort_values('Test Date')

                has_data = not (calf_ath.empty and hip_ath.empty and sh_ath.empty and isoy_ath.empty)

                if has_data:
                    def render_val_with_arrow(current, initial, fmt="{:.1f}", unit=""):
                        if initial == 0:
                            return f"{fmt.format(current)}{unit}"
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
                            sh_ir = sh_ath[sh_ath['Direction'].str.contains('Internal|IR', case=False, na=False)] if 'Direction' in sh_ath.columns else sh_ath
                            sh_er = sh_ath[sh_ath['Direction'].str.contains('External|ER', case=False, na=False)] if 'Direction' in sh_ath.columns else sh_ath
                            
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
                            hip_ad = hip_ath[hip_ath['Direction'].str.contains('AD', case=False, na=False)] if 'Direction' in hip_ath.columns else hip_ath
                            hip_ab = hip_ath[hip_ath['Direction'].str.contains('AB', case=False, na=False)] if 'Direction' in hip_ath.columns else hip_ath

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

                else:
                    st.info(f"No Intake Assessment records found for {selected_intake_athlete}.")

            elif selected_testing_tab == "Overall Testing Profile":
                st.markdown("<h3 style='color:#1D1D1F; font-weight:900; text-transform:uppercase;'>Overall Athletic Testing Profile</h3>", unsafe_allow_html=True)
                c_ov_ath, _ = st.columns([2, 2])
                with c_ov_ath:
                    selected_overall_athlete = st.selectbox("Select Athlete for Overall Profile", master_athlete_list, key="overall_ath_select")

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

                max_cmj_h = cmj_p[cmj_col].max() if not cmj_p.empty and cmj_col in cmj_p.columns else 0.0
                max_rsi_val = cmj_p[rsi_col].max() if not cmj_p.empty and rsi_col in cmj_p.columns else 0.0
                
                max_ash_l = ash_p['Peak Vertical Force [N] (L)'].max() if not ash_p.empty and 'Peak Vertical Force [N] (L)' in ash_p.columns else 0.0
                max_ash_r = ash_p['Peak Vertical Force [N] (R)'].max() if not ash_p.empty and 'Peak Vertical Force [N] (R)' in ash_p.columns else 0.0

                max_er_l = er_p['L Max ROM (°)'].max() if not er_p.empty and 'L Max ROM (°)' in er_p.columns else 0.0
                max_er_r = er_p['R Max ROM (°)'].max() if not er_p.empty and 'R Max ROM (°)' in er_p.columns else 0.0

                max_calf_l = calf_p['Peak Vertical Force [N] (L)'].max() if not calf_p.empty and 'Peak Vertical Force [N] (L)' in calf_p.columns else 0.0
                max_calf_r = calf_p['Peak Vertical Force [N] (R)'].max() if not calf_p.empty and 'Peak Vertical Force [N] (R)' in calf_p.columns else 0.0

                hip_ad_p = hip_p[hip_p['Direction'].str.contains('AD', case=False, na=False)] if not hip_p.empty and 'Direction' in hip_p.columns else pd.DataFrame()
                hip_ab_p = hip_p[hip_p['Direction'].str.contains('AB', case=False, na=False)] if not hip_p.empty and 'Direction' in hip_p.columns else pd.DataFrame()
                
                max_hip_ad = max(hip_ad_p['L Max Force (N)'].max() if 'L Max Force (N)' in hip_ad_p.columns else 0.0, hip_ad_p['R Max Force (N)'].max() if 'R Max Force (N)' in hip_ad_p.columns else 0.0) if not hip_ad_p.empty else 0.0
                max_hip_ab = max(hip_ab_p['L Max Force (N)'].max() if 'L Max Force (N)' in hip_ad_p.columns else 0.0, hip_ab_p['R Max Force (N)'].max() if 'R Max Force (N)' in hip_ad_p.columns else 0.0) if not hip_ad_p.empty else 0.0

                sh_ir_p = sh_p[sh_p['Direction'].str.contains('Internal|IR', case=False, na=False)] if not sh_p.empty and 'Direction' in sh_p.columns else pd.DataFrame()
                sh_er_p = sh_p[sh_p['Direction'].str.contains('External|ER', case=False, na=False)] if not sh_p.empty and 'Direction' in sh_p.columns else pd.DataFrame()

                max_sh_ir = max(sh_ir_p['L Max Force (N)'].max() if 'L Max Force (N)' in sh_ir_p.columns else 0.0, sh_ir_p['R Max Force (N)'].max() if 'R Max Force (N)' in sh_ir_p.columns else 0.0) if not sh_ir_p.empty else 0.0
                max_sh_er = max(sh_er_p['L Max Force (N)'].max() if 'L Max Force (N)' in sh_ir_p.columns else 0.0, sh_er_p['R Max Force (N)'].max() if 'R Max Force (N)' in sh_ir_p.columns else 0.0) if not sh_ir_p.empty else 0.0

                m_c1, m_c2, m_c3, m_c4, m_c5, m_c6 = st.columns(6)
                m_c1.metric("Peak CMJ", f"{max_cmj_h:.1f}")
                m_c2.metric("Peak RSI", f"{max_rsi_val:.2f}")
                m_c3.metric("Peak ASH (L/R)", f"{max_ash_l:.0f} / {max_ash_r:.0f} N")
                m_c4.metric("Peak ER ROM", f"{max(max_er_l, max_er_r):.1f}°")
                m_c5.metric("Peak Calf Raise", f"{max(max_calf_l, max_calf_r):.0f} N")
                m_c6.metric("Hip AD / AB", f"{max_hip_ad:.0f} / {max_hip_ab:.0f} N")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### Comprehensive Peak Performance Matrix")
                
                ov_summary_data = [
                    {"Test Domain": "Countermovement Jump", "Key Metric": "Max Height", "Peak Value": f"{max_cmj_h:.1f}"},
                    {"Test Domain": "Countermovement Jump", "Key Metric": "Max RSI-Mod", "Peak Value": f"{max_rsi_val:.2f}"},
                    {"Test Domain": "ASH Shoulder (Iso-I)", "Key Metric": "Peak Force (L / R)", "Peak Value": f"{max_ash_l:.0f} N / {max_ash_r:.0f} N"},
                    {"Test Domain": "External Rotation", "Key Metric": "Max ROM (L / R)", "Peak Value": f"{max_er_l:.1f}° / {max_er_r:.1f}°"},
                    {"Test Domain": "Single Leg Calf Raise", "Key Metric": "Peak Force (L / R)", "Peak Value": f"{max_calf_l:.0f} N / {max_calf_r:.0f} N"},
                    {"Test Domain": "Hip Strength", "Key Metric": "Adduction (AD)", "Peak Value": f"{max_hip_ad:.1f} N"},
                    {"Test Domain": "Hip Strength", "Key Metric": "Abduction (AB)", "Peak Value": f"{max_hip_ab:.1f} N"},
                    {"Test Domain": "Shoulder Strength", "Key Metric": "Internal Rotation (IR)", "Peak Value": f"{max_sh_ir:.1f} N"},
                    {"Test Domain": "Shoulder Strength", "Key Metric": "External Rotation (ER)", "Peak Value": f"{max_sh_er:.1f} N"},
                ]
                st.dataframe(pd.DataFrame(ov_summary_data), use_container_width=True, hide_index=True)
                    
            elif selected_testing_tab == "Season Comparison":
                st.markdown("### Multi-Season Testing Performance Comparison")
                c_comp_ath, _ = st.columns([2, 2])
                with c_comp_ath:
                    comp_athlete = st.selectbox("Select Athlete for Cross-Seasonal Comparison", master_athlete_list, key="comp_ath_testing_t4")

                cmj_comp = raw_cmj_df[raw_cmj_df['Name'] == comp_athlete].sort_values('Test Date')
                ash_comp = raw_ash_df[raw_ash_df['Name'] == comp_athlete].sort_values('Test Date')
                er_comp = raw_er_df[raw_er_df['Name'] == comp_athlete].sort_values('Test Date')

                if not cmj_comp.empty or not ash_comp.empty or not er_comp.empty:
                    st.markdown("#### Countermovement Jump Trend Across Seasons")
                    if not cmj_comp.empty:
                        season_order = ["Spring", "Summer", "Pre-Season"]
                        cmj_comp_ordered = cmj_comp.copy()
                        cmj_comp_ordered['Season'] = pd.Categorical(cmj_comp_ordered['Season'], categories=season_order, ordered=True)
            
                        cmj_avg_season = cmj_comp_ordered.groupby('Season', observed=False)[[cmj_col, rsi_col]].mean().reset_index()
                        cmj_avg_season = cmj_avg_season.sort_values('Season')

                        max_h = cmj_avg_season[cmj_col].max() if not cmj_avg_season.empty and not pd.isna(cmj_avg_season[cmj_col].max()) else 50.0
                        max_r = cmj_avg_season[rsi_col].max() if not cmj_avg_season.empty and not pd.isna(cmj_avg_season[rsi_col].max()) else 1.0

                        fig_comp_cmj = make_subplots(specs=[[{"secondary_y": True}]])
            
                        fig_comp_cmj.add_trace(
                            go.Bar(
                                x=cmj_avg_season['Season'], 
                                y=cmj_avg_season[cmj_col], 
                                name="Avg CMJ Height", 
                                marker_color='#FF8200', 
                                text=[f"<b>{val:.1f}</b>" if pd.notna(val) else "" for val in cmj_avg_season[cmj_col]], 
                                textposition="inside",
                                insidetextanchor="middle",
                                textfont=dict(color='white', size=13),
                                cliponaxis=False
                            ), 
                            secondary_y=False
                        )
            
                        fig_comp_cmj.add_trace(
                            go.Scatter(
                                x=cmj_avg_season['Season'], 
                                y=cmj_avg_season[rsi_col], 
                                name="Avg RSI-mod", 
                                mode='lines+markers+text', 
                                text=[f"<b>RSI: {val:.2f}</b>" if pd.notna(val) else "" for val in cmj_avg_season[rsi_col]], 
                                textposition="top center", 
                                textfont=dict(color='#1D1D1F', size=12),
                                line=dict(color='#4895DB', width=3), 
                                marker=dict(size=10, color='#4895DB'), 
                                cliponaxis=False
                            ), 
                            secondary_y=True
                        )
            
                        fig_comp_cmj.update_layout(
                            template="simple_white", 
                            height=420, 
                            margin=dict(l=20, r=20, t=70, b=20),
                            showlegend=True, 
                            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
                            xaxis=dict(
                                categoryorder="array",
                                categoryarray=season_order
                            )
                        )
                        fig_comp_cmj.update_yaxes(title_text="CMJ Height", range=[0, max_h * 1.30], secondary_y=False)
                        fig_comp_cmj.update_yaxes(title_text="RSI Modified", range=[0, max_r * 1.45], secondary_y=True, showgrid=False)
            
                        st.plotly_chart(fig_comp_cmj, use_container_width=True, config=LOCKED_CONFIG, key="cmj_cross_season_bar")
                    
                    st.markdown("#### Season-by-Season Best")
                    summary_rows = []
                    for season_period in ['Spring', 'Summer', 'Pre-Season']:
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
                else:
                    st.info(f"No multi-season testing records logged for {comp_athlete}.")

        # ==========================================
        # --- ACWR STANDALONE SIDEBAR TAB ----------
        # ==========================================
        elif selected_season == "ACWR":
            st.markdown('<div class="section-header">Acute:Chronic Workload Ratio (EWMA)</div>', unsafe_allow_html=True)
            
            acwr_tabs_list = ["Team Workload Summary", "Individual"]
            if "acwr_active_subtab" not in st.session_state:
                st.session_state.acwr_active_subtab = acwr_tabs_list[0]
                
            selected_acwr_tab = st.radio(
                "ACWR Sub Navigation",
                acwr_tabs_list,
                key="acwr_active_subtab",
                horizontal=True,
                label_visibility="collapsed"
            )
            
            # --- TAB 1: TEAM SUMMARY ---
            if selected_acwr_tab == "Team Workload Summary":
                valid_acwr_dates = sorted(raw_df['Date'].dropna().unique(), reverse=True)
                valid_acwr_dates_str = [d.strftime('%Y-%m-%d') for d in valid_acwr_dates] if valid_acwr_dates else []

                col_top1, col_top2, col_top3 = st.columns([1.5, 1.5, 1.5])
                with col_top1:
                    sel_team_date_str = st.selectbox(
                        "Evaluation Date", 
                        valid_acwr_dates_str, 
                        index=0, 
                        key="acwr_team_eval_date"
                    ) if valid_acwr_dates_str else None
                with col_top2:
                    team_pos_filter = st.selectbox(
                        "Position Filter", 
                        ["All Positions"] + sorted([p for p in raw_df['Position'].unique() if p != "N/A"]), 
                        key="acwr_team_pos_filt"
                    )
                with col_top3:
                    sel_view_metric_header = st.selectbox(
                        "Featured Table Metric", 
                        metrics_to_score, 
                        index=0, 
                        key="acwr_featured_metric_sel"
                    )

                hide_inactive_last_week = st.checkbox("Hide athletes inactive in the past 7 days", value=True, key="acwr_hide_inactive_chk")

                if sel_team_date_str:
                    eval_date_obj = pd.to_datetime(sel_team_date_str)
                    week_start_window = eval_date_obj - timedelta(days=6)
                    
                    team_summary_rows = []
                    
                    for ath in sorted(raw_df['Name'].unique()):
                        ath_all = raw_df[raw_df['Name'] == ath]
                        pos_str = ath_all['Position'].iloc[0] if not ath_all.empty else "N/A"
                        
                        if team_pos_filter != "All Positions" and pos_str != team_pos_filter:
                            continue
                            
                        if hide_inactive_last_week:
                            ath_recent_7d = ath_all[(ath_all['Date'] >= week_start_window) & (ath_all['Date'] <= eval_date_obj)]
                            if ath_recent_7d.empty or (ath_recent_7d[metrics_to_score].sum().sum() == 0):
                                continue
                            
                        ath_cal = compute_athlete_ewma_calendar(ath_all, metrics_to_score)
                        if ath_cal.empty:
                            continue
                            
                        cal_point = ath_cal[ath_cal['Date'] <= eval_date_obj]
                        if cal_point.empty:
                            continue
                            
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
                        sc3.metric("Under-training (<0.80)", under_count)
                        sc4.metric("High Spikes (>1.50)", spike_count)
                        
                        st.markdown(f"#### ACWR Grid on {eval_date_obj.strftime('%m/%d/%Y')} (Active 7-Day Window)")
                        
                        table_html = """<table class="scout-table"><thead><tr>
                            <th style="text-align:left !important; padding-left:10px;">Athlete</th>
                            <th>Position</th>
                            <th>Practice Score ACWR</th>
                            <th>Workload Zone</th>"""
                        for m in metrics_to_score:
                            table_html += f"<th>{m}</th>"
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

            # --- TAB 2: INDIVIDUAL DEEP-DIVE ---
            elif selected_acwr_tab == "Individual":
                c_ind1, c_ind2, c_ind3 = st.columns([1.5, 1.5, 1.5])
                
                valid_all_dates_str = [d.strftime('%Y-%m-%d') for d in sorted(raw_df['Date'].dropna().unique(), reverse=True)]
                with c_ind3:
                    sel_ind_date_str = st.selectbox("Select Snapshot Date", valid_all_dates_str, index=0, key="acwr_ind_date_sel")
                
                sel_ind_date = pd.to_datetime(sel_ind_date_str)
                week_start_ind = sel_ind_date - timedelta(days=6)
                
                active_athletes_for_date = []
                for ath_name in sorted(raw_df['Name'].unique()):
                    ath_sub = raw_df[(raw_df['Name'] == ath_name) & (raw_df['Date'] >= week_start_ind) & (raw_df['Date'] <= sel_ind_date)]
                    if not ath_sub.empty and ath_sub[metrics_to_score].sum().sum() > 0:
                        active_athletes_for_date.append(ath_name)
                
                if not active_athletes_for_date:
                    active_athletes_for_date = sorted(raw_df['Name'].unique())

                with c_ind1:
                    sel_ind_ath = st.selectbox("Select Active Athlete", active_athletes_for_date, key="acwr_ind_ath_sel")
                with c_ind2:
                    sel_ind_metric = st.selectbox("Select Practice Score Metric", metrics_to_score, index=0, key="acwr_ind_metric_sel")
                
                ath_all_ind = raw_df[raw_df['Name'] == sel_ind_ath].copy()
                meta_lookup = full_df_unfiltered[full_df_unfiltered['Name'] == sel_ind_ath]
                photo_url = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                pos_str = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"
                
                ath_cal_ind = compute_athlete_ewma_calendar(ath_all_ind, metrics_to_score)
                
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
                    
                    fig_acwr.add_hrect(
                        y0=0.80, y1=1.30, 
                        fillcolor="#28a745", opacity=0.10, 
                        line_width=0, secondary_y=False,
                        annotation_text="Optimal (0.80 - 1.30)", 
                        annotation_position="top left",
                        annotation_font_size=10,
                        annotation_font_color="#137333"
                    )

                    fig_acwr.add_hline(
                        y=1.50, line_dash="dash", line_color="#D93025", 
                        line_width=1.5, secondary_y=False,
                        annotation_text="Spike Threshold (1.50)", 
                        annotation_position="bottom right",
                        annotation_font_size=10,
                        annotation_font_color="#D93025"
                    )

                    fig_acwr.add_trace(
                        go.Scatter(
                            x=ath_cal_ind['Date'], 
                            y=ath_cal_ind[f'{sel_ind_metric}_ACWR'], 
                            name="ACWR Ratio (EWMA)", 
                            mode='lines+markers',
                            line=dict(color='#FF8200', width=3.5),
                            marker=dict(size=5, color='#FF8200')
                        ), 
                        secondary_y=False
                    )

                    fig_acwr.add_trace(
                        go.Scatter(
                            x=ath_cal_ind['Date'], 
                            y=ath_cal_ind[f'{sel_ind_metric}_Acute'], 
                            name="Acute Load (7d)", 
                            mode='lines',
                            line=dict(color='#4895DB', width=2, dash='dot')
                        ), 
                        secondary_y=True
                    )

                    fig_acwr.add_trace(
                        go.Scatter(
                            x=ath_cal_ind['Date'], 
                            y=ath_cal_ind[f'{sel_ind_metric}_Chronic'], 
                            name="Chronic Load (28d)", 
                            mode='lines',
                            line=dict(color='#515154', width=1.8, dash='dash')
                        ), 
                        secondary_y=True
                    )

                    fig_acwr.add_vline(x=sel_ind_date, line_dash="dash", line_color="#111827", opacity=0.4)

                    fig_acwr.update_layout(
                        height=440,
                        template="simple_white",
                        title=dict(text=f"<b>{sel_ind_ath} — {sel_ind_metric} ACWR Longitudinal Profile</b>", font=dict(size=14), x=0, y=0.97),
                        margin=dict(l=20, r=20, t=50, b=30),
                        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1),
                        xaxis=dict(title="Date", tickformat="%m/%d", showgrid=False)
                    )
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
                        
                        ind_metric_rows.append({
                            "Metric": m,
                            "Day Total": f"{target_row.get(m, 0.0):.1f}",
                            "Acute (7d EWMA)": f"{a_ewma:.1f}",
                            "Chronic (28d EWMA)": f"{c_ewma:.1f}",
                            "ACWR Ratio": f"{r_val:.2f}",
                            "Workload Zone": status_lbl
                        })

                    st.dataframe(pd.DataFrame(ind_metric_rows), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Sync Error: {e}")
