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

    /* --- EXACT COMPLIANCE CARD UI CSS --- */
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
    cmj_df.rename(columns={'Athlete': 'Name'}, inplace=True)
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
    if 'Week' in cmj_df.columns:
        cmj_df['Week'] = pd.to_numeric(cmj_df['Week'].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    cmj_df['Season'] = cmj_df['Test Date'].apply(assign_season)

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


# --- 5. EXECUTION BLOCK CONTEXT ---
if check_password():
    if "is_printing" not in st.session_state:
        st.session_state.is_printing = False

    if "active_tab_state" not in st.session_state:
        st.session_state.active_tab_state = "Individual Profile"

    LOCKED_CONFIG = {'staticPlot': False, 'displayModeBar': False}

    try:
        raw_df, raw_match_df, raw_cmj_df, raw_phase_df, thresh_df, raw_ash_df, raw_er_df, raw_calf_df, raw_hip_df, raw_shoulder_df = load_all_data()

        # --- GLOBAL SIDEBAR ---
        st.sidebar.markdown("### View Selection")
        selected_season = st.sidebar.radio(
            "Select View Mode", 
            ["Spring", "Summer", "Pre-Season", "Testing", "Comparison", "ACWR"], 
            index=2, 
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
        cmj_col = 'Jump Height (Imp-Mom) [cm]'
        rsi_col = 'RSI-modified [m/s]'

        master_athlete_list = sorted(list(
            set(raw_df['Name'].unique()) | 
            set(raw_cmj_df['Name'].unique()) | 
            set(raw_ash_df['Name'].unique()) | 
            set(raw_er_df['Name'].unique())
        ))

        st.markdown('<div class="main-logo-container" style="text-align: center; margin-top: 10px; margin-bottom: 15px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120"><div style="color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;">LADY VOLS VOLLEYBALL PERFORMANCE</div></div>', unsafe_allow_html=True)
        
        # ==========================================
        # --- ACWR STANDALONE SIDEBAR TAB ----------
        # ==========================================
        if selected_season == "ACWR":
            st.markdown('<div class="section-header">Acute:Chronic Workload Ratio (EWMA)</div>', unsafe_allow_html=True)
            
            acwr_mode_tabs = st.tabs(["Team Workload Summary", "Individual"])
            
            # --- TAB 1: TEAM SUMMARY ---
            with acwr_mode_tabs[0]:
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
            with acwr_mode_tabs[1]:
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

        # ==========================================
        # --- COMPARISON TAB ------------------------
        # ==========================================
        elif selected_season == "Comparison":
            st.markdown('<div class="section-header">Athlete Practice Peak Volume Baseline</div>', unsafe_allow_html=True)
            
            c_pos_filter = st.selectbox(
                "Position Filter", 
                ["All Positions"] + sorted([p for p in full_df_unfiltered['Position'].unique() if p != "N/A"]), 
                key="comp_pos_filter_global"
            )
            
            comp_tabs = st.tabs(["Spring", "Summer", "Pre-Season", "All-Time Max"])
            
            practice_raw = full_df_unfiltered[full_df_unfiltered['Session_Type'] == 'Practice'].copy()
            all_time_maxes = practice_raw.groupby('Name')[metrics_to_score].max().reset_index()
            
            for idx, season_name in enumerate(["Spring", "Summer", "Pre-Season", "All-Time Max"]):
                with comp_tabs[idx]:
                    if season_name in ["Spring", "Summer", "Pre-Season"]:
                        season_practices = practice_raw[practice_raw['Season'] == season_name]
                        season_maxes = season_practices.groupby('Name')[metrics_to_score].max().reset_index()
                    else:
                        season_maxes = all_time_maxes.copy()
                        
                    ath_list = sorted(full_df_unfiltered['Name'].unique())
                    if c_pos_filter != "All Positions":
                        pos_athletes = full_df_unfiltered[full_df_unfiltered['Position'] == c_pos_filter]['Name'].unique()
                        ath_list = [a for a in ath_list if a in pos_athletes]
                        
                    for i in range(0, len(ath_list), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(ath_list):
                                ath_name = ath_list[i + j]
                                meta_r = full_df_unfiltered[full_df_unfiltered['Name'] == ath_name].iloc[0]
                                photo_url = meta_r.get('PhotoURL', "https://www.w3schools.com/howto/img_avatar.png")
                                pos_str = meta_r.get('Position', "N/A")
                                
                                o_row = all_time_maxes[all_time_maxes['Name'] == ath_name]
                                s_row = season_maxes[season_maxes['Name'] == ath_name]
                                
                                r_html = ""
                                for m in metrics_to_score:
                                    o_val = o_row[m].iloc[0] if not o_row.empty else 0.0
                                    s_val = s_row[m].iloc[0] if not s_row.empty else 0.0
                                    
                                    is_peak = (s_val >= o_val) and (s_val > 0)
                                    highlight_style = 'style="color: #28a745; font-weight: 800; background-color: #e8f5e9;"' if is_peak else ''
                                    
                                    if season_name == "All-Time Max":
                                        r_html += f"<tr><td>{m}</td><td style='font-weight:700;'>{o_val:.1f}</td></tr>"
                                    else:
                                        r_html += f"<tr><td>{m}</td><td>{o_val:.1f}</td><td {highlight_style}>{s_val:.1f}</td></tr>"
                                        
                                table_header = "<thead><tr><th>Metric</th><th>Highest Practice</th></tr></thead>" if season_name == "All-Time Max" else f"<thead><tr><th>Metric</th><th>Overall Max</th><th>{season_name} Max</th></tr></thead>"
                                
                                with cols[j]:
                                    st.markdown(f'''
                                         <div style="border:1px solid #E5E5E7; border-radius:15px; padding:15px; margin-bottom:20px; background-color:white;">
                                             <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px; padding-bottom:8px; border-bottom:2px solid #FF8200;">
                                                <img src="{photo_url}" class="gallery-photo" style="width:55px; height:55px;">
                                                <div>
                                                    <p style="margin:0; font-weight:900; color:#1D1D1F; font-size:16px;">{ath_name}</p>
                                                    <p style="margin:0; color:#4895DB; font-weight:700; font-size:12px;">{pos_str} | {season_name} Max</p>
                                                </div>
                                             </div>
                                             <table class="scout-table">
                                                 {table_header}
                                                 <tbody>
                                                     {r_html}
                                                 </tbody>
                                             </table>
                                         </div>
                                    ''', unsafe_allow_html=True)

        # ==========================================
        # --- COMPLIANCE TAB -----------------------
        # ==========================================
        elif selected_season == "Compliance":
            st.markdown('<div class="section-header">Athlete Test Compliance Dashboard</div>', unsafe_allow_html=True)
            
            selected_comp_ath = st.selectbox("Select Athlete", master_athlete_list, key="comp_ath_select_card")
            
            meta_lookup = full_df_unfiltered[full_df_unfiltered['Name'] == selected_comp_ath]
            photo_url = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
            pos_str = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"

            st.markdown(f'''
                <div class="comp-athlete-header">
                    <img src="{photo_url}" class="comp-athlete-photo">
                    <div>
                        <div style="font-size:22px; font-weight:900; color:#111827;">{selected_comp_ath}</div>
                        <div style="font-size:14px; font-weight:600; color:#64748B;">{pos_str}</div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

            ref_date = datetime.now()

            def get_card_stats(df, col_name):
                ath_df = df[df['Name'] == selected_comp_ath].sort_values('Test Date')
                if ath_df.empty or col_name not in ath_df.columns:
                    return 0.0, "N/A", 0.0, "N/A", 0.0, 999
                
                recent_row = ath_df.iloc[-1]
                recent_val = float(recent_row[col_name])
                recent_date = recent_row['Test Date'].strftime('%Y-%m-%d')
                
                max_row = ath_df.loc[ath_df[col_name].idxmax()]
                max_val = float(max_row[col_name])
                max_date = max_row['Test Date'].strftime('%Y-%m-%d')
                
                pct_peak = (recent_val / max_val * 100) if max_val > 0 else 0.0
                days_since_max = int((ref_date - max_row['Test Date']).days)
                return recent_val, recent_date, max_val, max_date, pct_peak, days_since_max

            def render_compliance_card(title, recent_val, recent_date, max_val, max_date, pct_peak, max_days_num, threshold_days=7, unit="", decimals=1):
                try:
                    max_days_num = int(max_days_num)
                except (ValueError, TypeError):
                    max_days_num = 999

                if max_days_num <= threshold_days:
                    badge_bg = "#E6F4EA"
                    badge_color = "#137333"
                    badge_text = f"{max_days_num} Day" if max_days_num == 1 else f"{max_days_num} Days"
                else:
                    badge_bg = "#FCE8E6"
                    badge_color = "#D93025"
                    badge_text = "N/A" if max_days_num == 999 else f"{max_days_num} Days"

                fmt_str = f"{{:.{decimals}f}}"

                st.markdown(f'''
                <div class="comp-card-outer">
                    <div class="comp-card-top">
                        <span class="comp-card-title">{title}</span>
                        <span class="comp-pill-badge" style="background-color: {badge_bg}; color: {badge_color};">{badge_text}</span>
                    </div>
                    <div class="comp-grid">
                        <div class="comp-tile">
                            <div class="comp-label">RECENT</div>
                            <div class="comp-metric-val">{fmt_str.format(recent_val)}{unit}</div>
                            <div class="comp-subtext">{recent_date}</div>
                        </div>
                        <div class="comp-tile">
                            <div class="comp-label">ALL-TIME MAX</div>
                            <div class="comp-metric-val">{fmt_str.format(max_val)}{unit}</div>
                            <div class="comp-subtext">{max_date}</div>
                        </div>
                        <div class="comp-tile">
                            <div class="comp-label">% PEAK OUTPUT</div>
                            <div class="comp-metric-val comp-metric-orange">{pct_peak:.1f}%</div>
                            <div class="comp-subtext">Recent vs. Peak</div>
                        </div>
                        <div class="comp-tile">
                            <div class="comp-label">RECENCY STATUS</div>
                            <div class="comp-metric-val" style="color: {badge_color};">{badge_text}</div>
                            <div class="comp-subtext">Elapsed Threshold</div>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

            col_left, col_right = st.columns(2)

            with col_left:
                rv, rd, mv, md, pct, dn = get_card_stats(raw_cmj_df, cmj_col)
                render_compliance_card("CMJ Height", rv, rd, mv, md, pct, dn, threshold_days=7, unit=" cm", decimals=1)

                rv, rd, mv, md, pct, dn = get_card_stats(raw_ash_df, 'Peak Vertical Force [N] (L)')
                render_compliance_card("ASH Shoulder Force (Left)", rv, rd, mv, md, pct, dn, threshold_days=7, unit=" N", decimals=1)

                rv, rd, mv, md, pct, dn = get_card_stats(raw_er_df, 'L Max ROM (°)')
                render_compliance_card("External Rotation ROM (Left)", rv, rd, mv, md, pct, dn, threshold_days=7, unit="°", decimals=1)

            with col_right:
                rv, rd, mv, md, pct, dn = get_card_stats(raw_cmj_df, rsi_col)
                render_compliance_card("RSI Modified", rv, rd, mv, md, pct, dn, threshold_days=7, unit="", decimals=2)

                rv, rd, mv, md, pct, dn = get_card_stats(raw_ash_df, 'Peak Vertical Force [N] (R)')
                render_compliance_card("ASH Shoulder Force (Right)", rv, rd, mv, md, pct, dn, threshold_days=7, unit=" N", decimals=1)

                rv, rd, mv, md, pct, dn = get_card_stats(raw_er_df, 'R Max ROM (°)')
                render_compliance_card("External Rotation ROM (Right)", rv, rd, mv, md, pct, dn, threshold_days=7, unit="°", decimals=1)
                
        # ==========================================
        # --- TESTING TAB --------------------------
        # ==========================================
        elif selected_season == "Testing":
            st.markdown('<div class="section-header">Testing Profile</div>', unsafe_allow_html=True)
            testing_season_tabs = st.tabs([
                "CMJ Dashboard",
                "Spring Testing", 
                "Summer Testing", 
                "Pre-Season Testing", 
                "Intake Testing", 
                "Overall Testing Profile", 
                "Season Comparison"
            ])
            
            # --- TAB 0: CMJ DASHBOARD ---
            with testing_season_tabs[0]:
                cmj_view_modes = st.tabs(["Individual Athlete", "Team CMJ Summary"])
                
                # --- SUB-TAB 1: INDIVIDUAL ATHLETE DEEP DIVE ---
                with cmj_view_modes[0]:
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
                            comp_factor = st.selectbox("Comparison Factor", ["Individual (vs. Baseline)", "Team Benchmark (T-Score)", "Position Benchmark (T-Score)"], key="cmj_dash_comp_sel")

                        cur_test_row = ath_cmj_all[ath_cmj_all['Test Date'].dt.strftime('%m/%d/%y') == sel_test_date_str].iloc[-1]
                        base_test_row = ath_cmj_all.iloc[0]

                        meta_lookup = full_df_unfiltered[full_df_unfiltered['Name'] == sel_cmj_ath]
                        photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                        pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"

                        cmj_metric_defs = [
                            {"label": "Jump Height", "col": "Jump Height (Imp-Mom) [cm]", "unit": "cm", "fmt": "{:.1f}"},
                            {"label": "Jump Momentum", "col": "Take-off Momentum [kg m/s]", "unit": "kg·m/s", "fmt": "{:.1f}"},
                            {"label": "Peak Velocity", "col": "Concentric Peak Velocity [m/s]", "unit": "m/s", "fmt": "{:.2f}"},
                            {"label": "Mean Con Force", "col": "Concentric Mean Force [N]", "unit": "N", "fmt": "{:.0f}"},
                            {"label": "Force @ 0 Velocity", "col": "Force at Zero Velocity [N]", "unit": "N", "fmt": "{:.0f}"},
                            {"label": "Positive Impulse", "col": "Positive Impulse [N s]", "unit": "N·s", "fmt": "{:.1f}"},
                            {"label": "P1 Con Impulse", "col": "P1 Concentric Impulse [N s]", "unit": "N·s", "fmt": "{:.1f}"},
                            {"label": "P2 Con Impulse", "col": "P2 Concentric Impulse [N s]", "unit": "N·s", "fmt": "{:.1f}"},
                            {"label": "P2:P1 Impulse Ratio", "col": "P2 Concentric Impulse:P1 Concentric Impulse", "unit": "", "fmt": "{:.2f}"}
                        ]

                        top_col1, top_col2, top_col3 = st.columns([1.2, 2.2, 1.6])

                        # Athlete Card
                        with top_col1:
                            ath_card_html = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:18px; text-align:center; padding:8px 10px; border-radius:6px 6px 0 0;">{sel_cmj_ath}</div><div style="border:1px solid #E2E8F0; border-top:none; border-radius:0 0 6px 6px; padding:16px; background:white; display:flex; align-items:center; gap:16px;"><img src="{photo_val}" style="width:95px; height:95px; border-radius:8px; object-fit:contain; border:2px solid #FF8200;"><div style="font-size:14px; line-height:1.8; color:#1D1D1F;"><b>Position:</b> {pos_val}</div></div><div style="background:#4895DB; color:white; font-weight:800; font-size:13px; text-align:center; padding:6px; margin-top:10px; border-radius:4px;">Comparison: {comp_factor}</div>"""
                            st.markdown(ath_card_html, unsafe_allow_html=True)

                        # Data Table (Fixed % Change)
                        with top_col2:
                            table_rows_str = ""
                            for m_info in cmj_metric_defs:
                                lbl = m_info["label"]
                                col_name = m_info["col"]
                                fmt = m_info["fmt"]
                                
                                c_val = float(cur_test_row.get(col_name, 0.0)) if col_name in cur_test_row and pd.notna(cur_test_row.get(col_name)) else 0.0
                                b_val = float(base_test_row.get(col_name, 0.0)) if col_name in base_test_row and pd.notna(base_test_row.get(col_name)) else 0.0
                                
                                diff = ((c_val - b_val) / b_val * 100) if b_val > 0 else 0.0
                                pct_color = "#137333" if diff >= 0 else "#D93025"
                                
                                table_rows_str += f"""<tr><td style="text-align:left !important; padding-left:12px; font-weight:600;">{lbl}</td><td style="color:#64748B;">{fmt.format(b_val)}</td><td style="font-weight:800; background:#F0F7FF; border: 1px solid #3B82F6;">{fmt.format(c_val)}</td><td style="font-weight:800; color:{pct_color};">{diff:+.0f}%</td></tr>"""
                            
                            full_table_html = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:14px; text-align:center; padding:6px; border-radius:6px 6px 0 0;">Countermovement Jump Performance</div><table class="scout-table" style="width:100%; border:1px solid #E2E8F0; border-top:none; background:white; border-collapse:collapse; margin-bottom:0;"><thead><tr style="background:#F8FAFC; color:#64748B; font-size:11px;"><th style="text-align:left !important; padding:6px 12px;">Metric</th><th style="padding:6px;">Baseline</th><th style="padding:6px; background:#EBF5FF; color:#1E40AF;">Current</th><th style="padding:6px;">% Change</th></tr></thead><tbody>{table_rows_str}</tbody></table>"""
                            st.markdown(full_table_html, unsafe_allow_html=True)

                        # Calibrated Gauge
                        with top_col3:
                            gauge_header = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:14px; text-align:center; padding:6px; border-radius:6px 6px 0 0;">Performance Readiness Score<br><span style="font-size:11px; font-weight:600;">{sel_test_date_str}</span></div>"""
                            st.markdown(gauge_header, unsafe_allow_html=True)
                            
                            peak_h = ath_cmj_all[cmj_col].max() if cmj_col in ath_cmj_all else 1.0
                            cur_h_val = float(cur_test_row.get(cmj_col, 0.0))
                            gauge_score = min(100, max(0, int((cur_h_val / peak_h) * 100))) if peak_h > 0 else 94

                            gauge_colors = ['#B91C1C', '#EA580C', '#FACC15', '#65A30D', '#15803D', 'rgba(0,0,0,0)']
                            values = [20, 20, 20, 20, 20, 100]

                            center_x, center_y = 0.50, 0.50
                            needle_length = 0.38
                            
                            angle_rad = math.pi * (1.0 - (gauge_score / 100.0))
                            needle_x = center_x + needle_length * math.cos(angle_rad)
                            needle_y = center_y + needle_length * math.sin(angle_rad)

                            fig_gauge = go.Figure()

                            fig_gauge.add_trace(go.Pie(
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

                            fig_gauge.add_shape(
                                type='line',
                                x0=center_x, y0=center_y,
                                x1=needle_x, y1=needle_y,
                                line=dict(color='#111827', width=5)
                            )

                            fig_gauge.add_shape(
                                type='circle',
                                x0=center_x - 0.035, y0=center_y - 0.035,
                                x1=center_x + 0.035, y1=center_y + 0.035,
                                fillcolor='#111827',
                                line_color='#111827'
                            )

                            fig_gauge.add_annotation(
                                x=center_x, y=center_y - 0.02,
                                text=f"<b>{gauge_score}%</b>",
                                showarrow=False,
                                font=dict(size=14, color="white", weight="bold"),
                                bgcolor="#1E293B",
                                borderpad=4,
                                bordercolor="#1E293B"
                            )

                            fig_gauge.update_layout(
                                height=230,
                                margin=dict(l=10, r=10, t=10, b=10),
                                showlegend=False,
                                xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[0, 1]),
                                yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[0, 1]),
                                paper_bgcolor="white"
                            )
                            st.plotly_chart(fig_gauge, use_container_width=True, config=LOCKED_CONFIG, key="cmj_readiness_gauge")

                        st.markdown("<br>", unsafe_allow_html=True)

                        # Performance Standards Graph (Dynamically toggles Individual / Team / Position)
                        st.markdown(f'<div class="section-header">Countermovement Jump Performance Standards ({comp_factor})</div>', unsafe_allow_html=True)
                        
                        chart_col, legend_col = st.columns([4.2, 1.1])

                        with chart_col:
                            bar_metrics = [
                                {"name": "Jump Height", "col": "Jump Height (Imp-Mom) [cm]"},
                                {"name": "Jump Momentum", "col": "Take-off Momentum [kg m/s]"},
                                {"name": "Peak Velocity", "col": "Concentric Peak Velocity [m/s]"},
                                {"name": "Mean Con Force", "col": "Concentric Mean Force [N]"},
                                {"name": "Force @ 0 Velocity", "col": "Force at Zero Velocity [N]"},
                                {"name": "Positive Impulse", "col": "Positive Impulse [N s]"},
                                {"name": "P1 Con Impulse", "col": "P1 Concentric Impulse [N s]"},
                                {"name": "P2 Con Impulse", "col": "P2 Concentric Impulse [N s]"},
                                {"name": "CM Depth", "col": "Countermovement Depth [cm]"},
                                {"name": "Time to Takeoff", "col": "Time to Takeoff [s]"}
                            ]

                            # Determine comparison population pool
                            if "Position" in comp_factor:
                                pos_athletes = full_df_unfiltered[full_df_unfiltered['Position'] == pos_val]['Name'].unique()
                                ref_pool_df = raw_cmj_df[raw_cmj_df['Name'].isin(pos_athletes)]
                                if ref_pool_df.empty:
                                    ref_pool_df = raw_cmj_df
                            else:
                                ref_pool_df = raw_cmj_df

                            plot_scores = []
                            x_labels = []

                            for bm in bar_metrics:
                                x_labels.append(bm["name"])
                                cname = bm["col"]
                                ath_v = float(cur_test_row.get(cname, 0.0)) if cname in cur_test_row and pd.notna(cur_test_row.get(cname)) else 0.0

                                if "Individual" in comp_factor:
                                    base_v = float(base_test_row.get(cname, 0.0)) if cname in base_test_row and pd.notna(base_test_row.get(cname)) else 0.0
                                    if "time" in cname.lower():
                                        # For time to takeoff, faster/lower is better
                                        score_val = (base_v / ath_v * 100.0) if ath_v > 0 else 100.0
                                    else:
                                        score_val = (ath_v / base_v * 100.0) if base_v > 0 else 100.0
                                    plot_scores.append(round(min(140.0, max(0.0, score_val)), 1))
                                else:
                                    # Team or Position T-Score calculation
                                    if cname in ref_pool_df.columns and ref_pool_df[cname].dropna().std() > 0:
                                        m_mean = ref_pool_df[cname].mean()
                                        m_std = ref_pool_df[cname].std()
                                        if "time" in cname.lower():
                                            t_val = 50.0 - (10.0 * (ath_v - m_mean) / m_std)
                                        else:
                                            t_val = 50.0 + (10.0 * (ath_v - m_mean) / m_std)
                                        plot_scores.append(round(min(100.0, max(0.0, t_val)), 1))
                                    else:
                                        plot_scores.append(50.0)

                            fig_bands = go.Figure()

                            if "Individual" in comp_factor:
                                y_range = [50, 150]
                                y_axis_title = "% of Baseline Performance"
                                bands = [
                                    {"y0": 0, "y1": 70, "color": "#A00000"},
                                    {"y0": 70, "y1": 80, "color": "#E60000"},
                                    {"y0": 80, "y1": 90, "color": "#F05656"},
                                    {"y0": 90, "y1": 95, "color": "#F8A2A2"},
                                    {"y0": 95, "y1": 105, "color": "#FFFFFF"},
                                    {"y0": 105, "y1": 110, "color": "#C3E8A8"},
                                    {"y0": 110, "y1": 120, "color": "#81D350"},
                                    {"y0": 120, "y1": 130, "color": "#33A338"},
                                    {"y0": 130, "y1": 160, "color": "#1C7426"}
                                ]
                                val_labels = [f"<b>{val:.0f}%</b>" for val in plot_scores]
                            else:
                                y_range = [0, 100]
                                y_axis_title = f"{'Position' if 'Position' in comp_factor else 'Team'} T-Score Rating"
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
                                val_labels = [f"<b>{val:.1f}</b>" for val in plot_scores]

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
                                y=plot_scores,
                                marker=dict(
                                    color='#3A3D40',
                                    line=dict(color='#1A1C1E', width=1.5)
                                ),
                                width=0.42,
                                text=val_labels,
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
                                    range=y_range, 
                                    showgrid=False, 
                                    showline=True, 
                                    linecolor='#6B7280',
                                    title=dict(text=y_axis_title, font=dict(size=12, weight='bold', color='#4B5563'))
                                ),
                                showlegend=False
                            )
                            st.plotly_chart(fig_bands, use_container_width=True, config=LOCKED_CONFIG, key=f"cmj_standards_chart_{comp_factor}")

                        with legend_col:
                            if "Individual" in comp_factor:
                                legend_table_html = """<div style="background:#4895DB; color:white; font-weight:800; font-size:12px; text-align:center; padding:6px; border-radius:4px 4px 0 0;">Performance Bands<br><span style="font-size:10px; font-weight:600;">% of Baseline</span></div><table style="width:100%; border-collapse:collapse; font-size:11px; text-align:center; font-weight:700;"><tr style="background:#1C7426; color:white;"><td style="padding:4px;">Peak</td><td>> 130%</td></tr><tr style="background:#33A338; color:white;"><td style="padding:4px;">Optimal</td><td>120 - 130%</td></tr><tr style="background:#81D350; color:#111827;"><td style="padding:4px;">Elevated</td><td>110 - 120%</td></tr><tr style="background:#C3E8A8; color:#111827;"><td style="padding:4px;">Above Base</td><td>105 - 110%</td></tr><tr style="background:#FFFFFF; color:#111827; border-top:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0;"><td style="padding:4px;">Baseline</td><td>95 - 105%</td></tr><tr style="background:#F8A2A2; color:#111827;"><td style="padding:4px;">Below Base</td><td>90 - 95%</td></tr><tr style="background:#F05656; color:white;"><td style="padding:4px;">Fatigued</td><td>80 - 90%</td></tr><tr style="background:#E60000; color:white;"><td style="padding:4px;">High Fatigue</td><td>70 - 80%</td></tr><tr style="background:#A00000; color:white;"><td style="padding:4px;">Critical</td><td>< 70%</td></tr></table>"""
                            else:
                                legend_table_html = """<div style="background:#4895DB; color:white; font-weight:800; font-size:12px; text-align:center; padding:6px; border-radius:4px 4px 0 0;">Performance Bands<br><span style="font-size:10px; font-weight:600;">T-Score Rating</span></div><table style="width:100%; border-collapse:collapse; font-size:11px; text-align:center; font-weight:700;"><tr style="background:#1C7426; color:white;"><td style="padding:4px;">Excellent</td><td>> 80</td></tr><tr style="background:#33A338; color:white;"><td style="padding:4px;">Very Good</td><td>70 - 80</td></tr><tr style="background:#81D350; color:#111827;"><td style="padding:4px;">Good</td><td>60 - 70</td></tr><tr style="background:#C3E8A8; color:#111827;"><td style="padding:4px;">Above Avg.</td><td>55 - 60</td></tr><tr style="background:#FFFFFF; color:#111827; border-top:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0;"><td style="padding:4px;">Average</td><td>45 - 55</td></tr><tr style="background:#F8A2A2; color:#111827;"><td style="padding:4px;">Below Avg.</td><td>40 - 45</td></tr><tr style="background:#F05656; color:white;"><td style="padding:4px;">Poor</td><td>30 - 40</td></tr><tr style="background:#E60000; color:white;"><td style="padding:4px;">Very Poor</td><td>20 - 30</td></tr><tr style="background:#A00000; color:white;"><td style="padding:4px;">Extremely Poor</td><td>< 20</td></tr></table>"""
                            st.markdown(legend_table_html, unsafe_allow_html=True)
                            
                            

                # --- SUB-TAB 2: TEAM CMJ SUMMARY & READINESS DASHBOARD ---
                with cmj_view_modes[1]:
                    st.markdown("### Team Countermovement Jump Readiness Overview")
                    
                    team_cmj_dates = sorted(raw_cmj_df['Test Date'].dropna().dt.strftime('%m/%d/%y').unique().tolist(), reverse=True)
                    
                    c_sum_d1, c_sum_d2 = st.columns([1.5, 2])
                    with c_sum_d1:
                        sel_team_cmj_date = st.selectbox("Evaluation Test Date", team_cmj_dates, index=0, key="team_cmj_eval_date")
                    with c_sum_d2:
                        team_pos_f = st.selectbox("Filter by Position", ["All Positions"] + sorted([p for p in full_df_unfiltered['Position'].unique() if p != "N/A"]), key="team_cmj_pos_filter")

                    team_cmj_rows = []
                    
                    for ath_name in sorted(raw_cmj_df['Name'].unique()):
                        ath_sub_cmj = raw_cmj_df[raw_cmj_df['Name'] == ath_name].sort_values('Test Date')
                        if ath_sub_cmj.empty:
                            continue
                        
                        meta_row = full_df_unfiltered[full_df_unfiltered['Name'] == ath_name]
                        pos_str = meta_row['Position'].iloc[0] if not meta_row.empty else "N/A"
                        photo_url = meta_row['PhotoURL'].iloc[0] if not meta_row.empty else "https://www.w3schools.com/howto/img_avatar.png"
                        
                        if team_pos_f != "All Positions" and pos_str != team_pos_f:
                            continue
                            
                        ath_date_point = ath_sub_cmj[ath_sub_cmj['Test Date'].dt.strftime('%m/%d/%y') == sel_team_cmj_date]
                        if ath_date_point.empty:
                            continue
                            
                        target_row = ath_date_point.iloc[-1]
                        peak_h = ath_sub_cmj[cmj_col].max() if cmj_col in ath_sub_cmj else 1.0
                        cur_h = float(target_row.get(cmj_col, 0.0))
                        
                        readiness_pct = min(120, max(0, int((cur_h / peak_h) * 100))) if peak_h > 0 else 0
                        z_color = get_readiness_color(readiness_pct)
                        
                        team_cmj_rows.append({
                            "Athlete": ath_name,
                            "PhotoURL": photo_url,
                            "Position": pos_str,
                            "Readiness %": readiness_pct,
                            "Status_Color": z_color
                        })

                    if team_cmj_rows:
                        cmj_team_df = pd.DataFrame(team_cmj_rows).sort_values("Readiness %", ascending=False)
                        
                        c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
                        avg_team_readiness = cmj_team_df['Readiness %'].mean()
                        peak_count = sum(1 for r in team_cmj_rows if r['Readiness %'] >= 90)
                        fatigue_count = sum(1 for r in team_cmj_rows if r['Readiness %'] < 80)
                        
                        c_kpi1.metric("Athletes Evaluated", len(team_cmj_rows))
                        c_kpi2.metric("Team Mean Readiness", f"{avg_team_readiness:.1f}%")
                        c_kpi3.metric("Optimal (>=90%)", peak_count)
                        c_kpi4.metric("Fatigued (<80%)", fatigue_count)

                        team_tbl_html = """<table class="scout-table" style="width:100%; border:1px solid #E2E8F0; background:white; margin-top:15px;"><thead><tr style="background:#4895DB; color:white;"><th style="width:60px;">Athlete</th><th style="text-align:left !important; padding-left:15px;">Name</th><th>Position</th><th>Readiness Score</th></tr></thead><tbody>"""
                        
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

            # --- SEASON SPECIFIC TESTING TABS ---
            for tab_idx, s_label in enumerate(["Spring", "Summer", "Pre-Season"]):
                with testing_season_tabs[tab_idx + 1]:
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
                            with sc1: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_h}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_h:.1f} cm</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">CMJ HEIGHT</span></div></div>', unsafe_allow_html=True)
                            with sc2: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_rsi}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_rsi:.2f}</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RSI MOD</span></div></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> CMJ: {p_diff_h:+.1f}% | RSI: {p_diff_rsi:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base Values:</b> CMJ: {base_h:.1f} cm | RSI: {base_rsi:.2f}</p></div>', unsafe_allow_html=True)

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

            # --- TAB 4: INTAKE TESTING TAB ---
            with testing_season_tabs[4]:
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

            # --- TAB 5: OVERALL TESTING PROFILE ---
            with testing_season_tabs[5]:
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
                max_hip_ab = max(hip_ab_p['L Max Force (N)'].max() if 'L Max Force (N)' in hip_ab_p.columns else 0.0, hip_ab_p['R Max Force (N)'].max() if 'R Max Force (N)' in hip_ab_p.columns else 0.0) if not hip_ab_p.empty else 0.0

                sh_ir_p = sh_p[sh_p['Direction'].str.contains('Internal|IR', case=False, na=False)] if not sh_p.empty and 'Direction' in sh_p.columns else pd.DataFrame()
                sh_er_p = sh_p[sh_p['Direction'].str.contains('External|ER', case=False, na=False)] if not sh_p.empty and 'Direction' in sh_p.columns else pd.DataFrame()

                max_sh_ir = max(sh_ir_p['L Max Force (N)'].max() if 'L Max Force (N)' in sh_ir_p.columns else 0.0, sh_ir_p['R Max Force (N)'].max() if 'R Max Force (N)' in sh_ir_p.columns else 0.0) if not sh_ir_p.empty else 0.0
                max_sh_er = max(sh_er_p['L Max Force (N)'].max() if 'L Max Force (N)' in sh_ir_p.columns else 0.0, sh_er_p['R Max Force (N)'].max() if 'R Max Force (N)' in sh_ir_p.columns else 0.0) if not sh_ir_p.empty else 0.0

                m_c1, m_c2, m_c3, m_c4, m_c5, m_c6 = st.columns(6)
                m_c1.metric("Peak CMJ", f"{max_cmj_h:.1f} cm")
                m_c2.metric("Peak RSI", f"{max_rsi_val:.2f}")
                m_c3.metric("Peak ASH (L/R)", f"{max_ash_l:.0f} / {max_ash_r:.0f} N")
                m_c4.metric("Peak ER ROM", f"{max(max_er_l, max_er_r):.1f}°")
                m_c5.metric("Peak Calf Raise", f"{max(max_calf_l, max_calf_r):.0f} N")
                m_c6.metric("Hip AD / AB", f"{max_hip_ad:.0f} / {max_hip_ab:.0f} N")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### Comprehensive Peak Performance Matrix")
                
                ov_summary_data = [
                    {"Test Domain": "Countermovement Jump", "Key Metric": "Max Height", "Peak Value": f"{max_cmj_h:.1f} cm"},
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
                    
            # --- TAB 6: CROSS-SEASON TESTING COMPARISON ---
            with testing_season_tabs[6]:
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
                                name="Avg CMJ Height (cm)", 
                                marker_color='#FF8200', 
                                text=[f"<b>{val:.1f} cm</b>" if pd.notna(val) else "" for val in cmj_avg_season[cmj_col]], 
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
                        fig_comp_cmj.update_yaxes(title_text="CMJ Height (cm)", range=[0, max_h * 1.30], secondary_y=False)
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
                            'Max CMJ (cm)': round(max_cmj, 1),
                            'Max RSI': round(max_rsi, 2),
                            'Max ASH L (N)': round(max_ash_l, 0),
                            'Max ASH R (N)': round(max_ash_r, 0),
                            'Max ER ROM L (°)': round(max_er_l, 1),
                            'Max ER ROM R (°)': round(max_er_r, 1)
                        })
                    
                    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
                else:
                    st.info(f"No multi-season testing records logged for {comp_athlete}.")
        else:
            # --- DYNAMIC SEASONAL TAB NAVIGATION SETUP ---
            if selected_season == "Summer":
                tab_titles = [
                    "Individual Profile", 
                    "Practice Scores", 
                    "Daily Combined Scores", 
                    "Spring Max vs Daily Combined", 
                    "Practice History", 
                    "Position Analysis", 
                    "Spring v. Summer"
                ]
            elif selected_season == "Pre-Season":
                tab_titles = [
                    "Individual Profile", 
                    "Practice Scores", 
                    "Daily Combined Scores", 
                    "Practice History", 
                    "Match v. Practice", 
                    "Match Summary", 
                    "Position Analysis", 
                    "Phase Analysis", 
                    "Practice Planner"
                ]
            else: # Spring
                tab_titles = [
                    "Individual Profile", 
                    "Practice Scores", 
                    "Daily Combined Scores", 
                    "Practice History", 
                    "Match v. Practice", 
                    "Match Summary", 
                    "Position Analysis", 
                    "Phase Analysis", 
                    "Practice Planner"
                ]

            if st.session_state.active_tab_state not in tab_titles:
                st.session_state.active_tab_state = tab_titles[0]

            selected_tab_label = st.radio(
                "Navigation View Menu Selection Control", 
                tab_titles, 
                index=tab_titles.index(st.session_state.active_tab_state),
                label_visibility="collapsed", 
                horizontal=True, 
                key=f"master_radio_{selected_season}"
            )
            st.session_state.active_tab_state = selected_tab_label

            # ==========================================
            # --- TAB CLAUSE 0: INDIVIDUAL PROFILE -----
            # ==========================================
            if st.session_state.active_tab_state == "Individual Profile":
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
                    meta_lookup = df_t0[df_t0['Name'] == selected_athlete_prof]
                    pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"
                    photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                    p_meta = pd.Series({'Name': selected_athlete_prof, 'Position': pos_val, 'PhotoURL': photo_val})
                    p_row = pd.Series({m: 0.0 for m in all_metrics})
                    p_row['Name'] = selected_athlete_prof

                p_full_prof = df_t0[df_t0['Name'] == selected_athlete_prof]
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
                        with sc1: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_h}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_h:.1f} cm</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">CMJ HEIGHT</span></div></div>', unsafe_allow_html=True)
                        with sc2: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_rsi}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{cur_rsi:.2f}</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RSI MOD</span></div></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> CMJ: {p_diff_h:+.1f}% | RSI: {p_diff_rsi:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base Values:</b> CMJ: {base_h:.1f} cm | RSI: {base_rsi:.2f}</p></div>', unsafe_allow_html=True)
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
                        pct_r = ((ri - base_ri) / base_ri * 100) if base_ri > 0 else 0
                        color_ash_l = "#28a745" if li >= 100 else "#dc3545"
                        color_ash_r = "#28a745" if ri >= 100 else "#dc3545"

                        sc1, sc2 = st.columns(2)
                        with sc1: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_ash_l}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{li:.0f} N</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">LEFT</span></div></div>', unsafe_allow_html=True)
                        with sc2: st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color_ash_r}; line-height:1.2; padding-top:15px; height:80px; width:100%;"><span style="font-size:18px;">{ri:.0f} N</span><span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RIGHT</span></div></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>Asymmetry:</b> {asym_i:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> L: {pct_l:+.1f}% | R: {pct_r:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base Force:</b> L: {base_li:.0f} N | R: {base_ri:.0f} N</p></div>', unsafe_allow_html=True)
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
                            st.markdown(f'<div class="info-box" style="text-align:center; margin-top:10px;"><p style="margin:0; font-size:11px; color:grey;"><b>Asymmetry:</b> {cur_asym_rom:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> L: {rom_pct_l:+.1f}% | R: {pct_r:+.1f}%</p><p style="margin:0; font-size:11px; color:grey;"><b>Base ROM:</b> L: {base_l_rom:.1f}° | R: {base_r_rom:.1f}°</p></div>', unsafe_allow_html=True)
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

            # ==========================================
            # --- TAB CLAUSE 1: PRACTICE SCORES --------
            # ==========================================
            elif st.session_state.active_tab_state == "Practice Scores":
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
                                p_full_g = df_t1[df_t1['Name'] == name]
                                
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
                                    
            # ==========================================
            # --- TAB CLAUSE 2: DAILY COMBINED SCORES ---
            # ==========================================
            elif st.session_state.active_tab_state == "Daily Combined Scores":
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
                                p_full_g = df_t2[df_t2['Name'] == name]
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
                else:
                    st.warning("No data recorded on this specific day.")

            # ==========================================
            # --- TAB CLAUSE 3: SPRING PEAK VS COMBINED -
            # ==========================================
            elif st.session_state.active_tab_state in ["Spring Max vs Daily Combined", "Spring Max v. Daily Combined"]:
                df_t3 = df_master.copy()
                valid_dates_sorted_sm = df_t3[df_t3['Date'].notna()].sort_values('Date', ascending=False)['Date'].dt.strftime('%Y-%m-%d').unique().tolist()
                
                target_date_str = "2026-04-04"
                tournament_label = "GT Spring Tournament 4-4-26"
                
                clean_date_list_sm = []
                tourney_added_sm = False
                for d_str in valid_dates_sorted_sm:
                    if selected_season == "Spring" and d_str == target_date_str:
                        if not tourney_added_sm:
                            clean_date_list_sm.append(tournament_label)
                            tourney_added_sm = True
                    else:
                        clean_date_list_sm.append(d_str)

                if not clean_date_list_sm: clean_date_list_sm = valid_dates_sorted_sm

                if not clean_date_list_sm:
                    st.warning("No recorded dates found for the currently active season.")
                else:
                    c_sm1, c_sm2 = st.columns(2)
                    with c_sm1: selected_date_sm = st.selectbox("Date Selection", clean_date_list_sm, index=0, key="nav_sel_sm_t3")
                    with c_sm2: pos_f_sm = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df_t3['Position'].unique() if p != "N/A"]), key="nav_pos_sm_t3")
                    
                    target_date_obj_sm = pd.to_datetime(target_date_str) if (selected_season == "Spring" and selected_date_sm == tournament_label) else pd.to_datetime(selected_date_sm)
                    display_df_sm = df_t3[df_t3['Date'] == target_date_obj_sm].groupby(['Name', 'Position', 'PhotoURL'])[all_metrics].sum().reset_index()
                    spring_gps_raw = full_df_unfiltered[(full_df_unfiltered['Season'] == 'Spring') & (full_df_unfiltered['Session_Type'] == 'Practice')].copy()
                    
                    if spring_gps_raw.empty:
                        st.warning("No historical Spring dataset found to generate maximum baseline metrics.")
                    elif not display_df_sm.empty:
                        spring_daily_totals = spring_gps_raw.groupby(['Name', 'Date'])[all_metrics].sum().reset_index()
                        spring_daily_maxes = spring_daily_totals.groupby('Name')[all_metrics].max().reset_index()
                        if pos_f_sm != "All Positions": display_df_sm = display_df_sm[display_df_sm['Position'] == pos_f_sm]
                        
                        athlete_names_sm = sorted(display_df_sm['Name'].unique())
                        filtered_metrics_sm = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]

                        for i in range(0, len(athlete_names_sm), 2):
                            cols = st.columns(2)
                            for j in range(2):
                                if i + j < len(athlete_names_sm):
                                    name = athlete_names_sm[i + j]
                                    ath_spring_peaks = spring_daily_maxes[spring_daily_maxes['Name'] == name]
                                    if ath_spring_peaks.empty: continue
                                        
                                    p_session_row = display_df_sm[display_df_sm['Name'] == name].iloc[0]
                                    r_html = ""; t_grade = 0; c_metrics = 0
                                    
                                    for k in filtered_metrics_sm:
                                        val = p_session_row[k]
                                        mx = ath_spring_peaks[k].iloc[0]
                                        if pd.isna(mx) or mx <= 0: mx = 1.0
                                        g = math.ceil((val / mx) * 100)
                                        t_grade += g; c_metrics += 1
                                        r_html += f"<tr><td>{k}</td><td>{val:.1f}</td><td>{mx:.1f}</td><td>{g}</td></tr>"
                                    
                                    sc_g = math.ceil(t_grade / c_metrics) if c_metrics > 0 else 0
                                    with cols[j]: st.markdown(f'<div style="border:1px solid #E5E5E7; border-radius:15px; padding:15px; margin-bottom:20px; background-color:white;"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{p_session_row["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px; color:#333;">{name}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Combined Total</th><th>Spring Max Day</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div><div style="flex:1; text-align:center;"><div style="background-color:{get_flipped_gradient(sc_g)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{sc_g}</div></div></div></div>', unsafe_allow_html=True)
                    else:
                        st.warning("No performance footprint logged for selected parameters on this date.")

            # ==========================================
            # --- TAB CLAUSE 4: PRACTICE HISTORY -------
            # ==========================================
            elif st.session_state.active_tab_state == "Practice History":
                df_t4 = df_master.copy()
                st.markdown('<div class="section-header">Season History & Team Weekly Review</div>', unsafe_allow_html=True)
                sub_tabs = st.tabs(["Individual Review", "Team Weekly Review"])

                with sub_tabs[0]:
                    sel_ath_hist = st.selectbox("Select Athlete", sorted(df_t4['Name'].unique()), key="master_ath_sel_t4")
                    p_full = df_t4[df_t4['Name'] == sel_ath_hist].copy()
                    p_full['Date'] = pd.to_datetime(p_full['Date'])
                    
                    p_sessions = p_full.sort_values(['Date', 'Sheet_Order']).reset_index(drop=True)

                    scores_list = []
                    for idx, row in p_sessions.iterrows():
                        row_grades = []
                        curr_order = row.get('Sheet_Order', float('inf'))
                        
                        lb_sums = p_full[
                            (p_full['Date'] >= row['Date'] - timedelta(days=30)) & 
                            (p_full['Date'] <= row['Date']) &
                            (p_full['Sheet_Order'] <= curr_order)
                        ]
                        
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
                        
                        fig_master.add_trace(go.Scatter(
                            x=master_df_history['Display'],
                            y=master_df_history['Score'],
                            mode='lines',
                            line=dict(color='#4895DB', width=2),
                            showlegend=False,
                            hoverinfo='skip'
                        ))

                        prac_df = master_df_history[master_df_history['Type'] == 'Practice']
                        if not prac_df.empty: 
                            fig_master.add_trace(go.Scatter(
                                x=prac_df['Display'], 
                                y=prac_df['Score'], 
                                mode='markers+text', 
                                text=prac_df['Score'], 
                                textposition="top center", 
                                name="Practice", 
                                hovertemplate="<b>%{customdata}</b><br>Date: %{x}<br>Score: %{y}<extra></extra>",
                                customdata=prac_df['Session_Name'],
                                marker=dict(size=9, color='#4895DB', line=dict(width=1, color='white'))
                            ))
                            
                        match_df_line = master_df_history[master_df_history['Type'] == 'Match']
                        if not match_df_line.empty: 
                            fig_master.add_trace(go.Scatter(
                                x=match_df_line['Display'], 
                                y=match_df_line['Score'], 
                                mode='markers+text', 
                                text=[f"<b>{s}</b>" for s in match_df_line['Score']], 
                                textposition="top center", 
                                name="Match Day", 
                                hovertemplate="<b>%{customdata}</b><br>Date: %{x}<br>Score: %{y}<extra></extra>",
                                customdata=match_df_line['Session_Name'],
                                marker=dict(size=15, color='#FF8200', line=dict(width=3, color='#31333F')), 
                                textfont=dict(color='#31333F', size=13, weight='bold')
                            ))
                            
                        unique_dates_df = master_df_history.drop_duplicates(subset=['Display']).reset_index(drop=True)
                        for i in range(1, len(unique_dates_df)):
                            if unique_dates_df.iloc[i]['Week'] != unique_dates_df.iloc[i-1]['Week']:
                                fig_master.add_vline(x=i-0.5, line_dash="dash", line_color="#515154", opacity=0.3)
                                fig_master.add_annotation(
                                    x=i-0.5, y=0.98, yref="paper", 
                                    text=f"Wk {unique_dates_df.iloc[i]['Week']}", 
                                    showarrow=False, bgcolor="white", 
                                    font=dict(size=10, color="#515154"), yanchor="top"
                                )
                                
                        fig_master.update_layout(
                            template="simple_white", 
                            height=500, 
                            margin=dict(l=40, r=20, t=40, b=90),
                            xaxis=dict(
                                type='category', 
                                title=dict(text="Date", standoff=15)
                            ), 
                            yaxis=dict(
                                range=[0, 120], 
                                automargin=True, 
                                tickvals=[0, 20, 40, 60, 80, 100]
                            ), 
                            legend=dict(
                                orientation="h", 
                                yanchor="top", 
                                y=-0.28, 
                                x=0.5, 
                                xanchor="center"
                            )
                        )
                        st.plotly_chart(fig_master, use_container_width=True, key=f"master_full_flow_{sel_ath_hist}_t4")

                    st.markdown("### CMJ Baseline vs. Post-Match Recovery")
                    if raw_cmj_df is not None and not raw_cmj_df.empty:
                        c_sync = raw_cmj_df.rename(columns={'Athlete': 'Name'}) if 'Athlete' in raw_cmj_df.columns else raw_cmj_df.copy()
                        ath_cmj_data = c_sync[c_sync['Name'] == sel_ath_hist].sort_values('Test Date')
                        baseline_cmj = ath_cmj_data[ath_cmj_data['Week'] == 4]
                        post_match_cmj = ath_cmj_data[ath_cmj_data['Week'] > 4] 
                        if not baseline_cmj.empty:
                            base_row = baseline_cmj.iloc[-1]
                            latest_post = post_match_cmj.iloc[-1] if not post_match_cmj.empty else None
                            if latest_post is not None:
                                m1, m2, m3 = st.columns(3)
                                m1.metric("Baseline", f"{base_row[cmj_col]:.1f} cm")
                                m2.metric("Latest Jump", f"{latest_post[cmj_col]:.1f} cm", f"{((latest_post[cmj_col] - base_row[cmj_col]) / base_row[cmj_col]) * 100:+.1f}%")
                                m3.metric("RSI", f"{latest_post[rsi_col]:.2f}", f"{((latest_post[rsi_col] - base_row[rsi_col]) / base_row[rsi_col]) * 100:+.1f}%")
                            
                            st.markdown("#### Jump History & Match Context")
                            comparison_list = []
                            for _, row in post_match_cmj.iterrows():
                                jump_date = pd.to_datetime(row['Test Date'])
                                try:
                                    prev_matches = df_t4[(df_t4['Name'] == sel_ath_hist) & (df_t4['Date'] < jump_date) & ((df_t4['Session_Name'].str.contains('Match|Game', case=False, na=False)) | (df_t4['Session_Type'].str.contains('Match|Game', case=False, na=False)))]
                                    prev_match_name = prev_matches.sort_values('Date', ascending=False).iloc[0]['Session_Name']
                                except:
                                    prev_match_name = "N/A"
                                raw_diff = float(row[cmj_col]) - float(base_row[cmj_col])
                                comparison_list.append({"Date": jump_date.strftime('%m/%d/%Y'), "Prev Match": prev_match_name, "Jump Height": f"{row[cmj_col]:.1f} cm", "Raw Diff": raw_diff, "Display Diff": f"{raw_diff:+.1f} cm", "RSI": f"{row[rsi_col]:.2f}"})
                            
                            cmj_table_html = """<table class="scout-table" style="width:100%; border-collapse: collapse; text-align: center;"><thead><tr style="background-color: #f0f2f6; font-weight: bold;"><th style="padding: 10px; border: 1px solid #ddd;">Jump Date</th><th style="padding: 10px; border: 1px solid #ddd;">Previous Match</th><th style="padding: 10px; border: 1px solid #ddd;">Jump Height</th><th style="padding: 10px; border: 1px solid #ddd;">Vs. Baseline</th><th style="padding: 10px; border: 1px solid #ddd;">RSI</th></tr></thead><tbody>"""
                            for item in comparison_list:
                                cmj_table_html += f"""<tr><td style="padding: 10px; border: 1px solid #ddd;">{item['Date']}</td><td style="padding: 10px; border: 1px solid #ddd;">{item['Prev Match']}</td><td style="padding: 10px; border: 1px solid #ddd;">{item['Jump Height']}</td><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: {'#28a745' if item['Raw Diff'] >= 0 else '#dc3545'};">{item['Display Diff']}</td><td style="padding: 10px; border: 1px solid #ddd;">{item['RSI']}</td></tr>"""
                            st.markdown(cmj_table_html + "</tbody></table>", unsafe_allow_html=True)
                            
                            fig_cmj = make_subplots(specs=[[{"secondary_y": True}]])
                            fig_cmj.add_trace(go.Scatter(x=ath_cmj_data['Test Date'], y=ath_cmj_data[cmj_col], name="Jump Height (cm)", mode='lines+markers', line=dict(color='#4895DB', width=3)), secondary_y=False)
                            fig_cmj.add_trace(go.Scatter(x=ath_cmj_data['Test Date'], y=ath_cmj_data[rsi_col], name="RSI-mod", mode='lines+markers', line=dict(color='#FF8200', width=2, dash='dot')), secondary_y=True)
                            fig_cmj.add_hline(y=base_row[cmj_col], line_dash="dash", line_color="red")
                            fig_cmj.update_layout(height=400, template="simple_white", margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=-0.3, x=0.5, xanchor="center"), xaxis=dict(title="Date", tickformat="%m/%d"))
                            st.plotly_chart(fig_cmj, use_container_width=True, config=LOCKED_CONFIG, key=f"integrated_cmj_final_{sel_ath_hist}_t4")

                with sub_tabs[1]:
                    sel_week = st.selectbox("Select Review Week", sorted(df_t4['Week'].unique(), reverse=True), key="team_week_sel_t4")
                    week_df = df_t4[df_t4['Week'] == sel_week].copy()
                    ath_names = sorted(week_df['Name'].unique())
                    
                    for i in range(0, len(ath_names), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(ath_names):
                                name = ath_names[i+j]
                                p_all = df_t4[df_t4['Name'] == name].sort_values(['Date', 'Sheet_Order']).reset_index(drop=True)
                                w_daily = p_all[p_all['Week'].astype(str) == str(sel_week)]
                                
                                if not w_daily.empty:
                                    card_scores = []
                                    for idx, r in w_daily.iterrows():
                                        r_grades = []
                                        curr_order = r.get('Sheet_Order', float('inf'))
                                        lb = p_all[
                                            (p_all['Date'] >= r['Date'] - timedelta(days=30)) & 
                                            (p_all['Date'] <= r['Date']) &
                                            (p_all['Sheet_Order'] <= curr_order)
                                        ]
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
                                        
            # ==========================================
            # --- TAB CLAUSE 5: MATCH V. PRACTICE ------
            # ==========================================
            elif st.session_state.active_tab_state == "Match v. Practice":
                df_t5 = df_master.copy()
                match_t5 = match_master.copy()
                st.markdown('<div class="section-header">Season Preparation vs. Match Demands</div>', unsafe_allow_html=True)
                
                c_mode, c_sel = st.columns([1, 3])
                with c_mode: view_mode_t5 = st.radio("View Level", ["Team", "Position", "Individual"], horizontal=True, key="gp_view_mode_t5")
                
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
                        if c in target_df.columns: target_df[c] = pd.to_numeric(target_df[c], errors='coerce').fillna(0)
                    if 'Duration' in target_df.columns: target_df['Duration'] = target_df['Duration'].apply(lambda x: x if x > 0 else 1)
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

            # ==========================================
            # --- TAB CLAUSE 6: MATCH SUMMARY ----------
            # ==========================================
            elif st.session_state.active_tab_state == "Match Summary":
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
                    match_list_t = match_t6.sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique().tolist()
                    if "matches_state" not in st.session_state: st.session_state.matches_state = match_list_t[-3:] if len(match_list_t) >= 3 else match_list_t
                    st.session_state.matches_state = st.multiselect("Select Matches", match_list_t, default=st.session_state.matches_state, key="ms_select_t6")
                    st.session_state.pos_state = st.selectbox("Filter by Position", ["All Positions"] + sorted(list(match_t6['Position'].unique())), key="pos_select_t6")
                    st.markdown('</div>', unsafe_allow_html=True)

                if st.session_state.is_printing: st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
                selected_matches = st.session_state.get("matches_state", [])
                pos_filter_t = st.session_state.get("pos_state", "All Positions")

                if selected_matches:
                    m_map = {m: custom_colors[idx % len(custom_colors)] for idx, m in enumerate(selected_matches)}
                    st.markdown('<div class="section-header">Athlete Match Performance Breakdown</div>', unsafe_allow_html=True)
                    tourney_df = match_t6[match_t6['Session_Name'].isin(selected_matches)].sort_values(['Date', 'Sheet_Order'])
                    if pos_filter_t != "All Positions": tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]

                    for name in sorted(tourney_df['Name'].unique()):
                        ad = tourney_df[tourney_df['Name'] == name]
                        try: correct_photo = df_master[df_master['Name'] == name]['PhotoURL'].iloc[0]
                        except: correct_photo = "https://www.w3schools.com/howto/img_avatar.png"
                        
                        st.markdown(f'<div class="player-row-container"><div class="player-divider"></div>', unsafe_allow_html=True)
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

            # ==========================================
            # --- TAB CLAUSE 7: POSITION ANALYSIS ------
            # ==========================================
            elif st.session_state.active_tab_state == "Position Analysis":
                df_t7 = df_master.copy()
                st.markdown('<div class="section-header">Positional Performance Trends</div>', unsafe_allow_html=True)
                pos_filter_an = st.selectbox("Select Position to Analyze", sorted([p for p in df_t7['Position'].unique() if p != "N/A"]), key="pos_an_filt_main_t7")
                
                max_wk = df_t7['Week'].max()
                rec_4 = list(range(max(0, int(max_wk) - 3), int(max_wk) + 1))
                tr_df = df_t7[(df_t7['Week'].isin(rec_4)) & (df_t7['Position'] == pos_filter_an)]
                players_in_pos = sorted(tr_df['Name'].unique())
                
                if players_in_pos:
                    tr_metrics = ["Player Load", "Estimated Distance (y)", "Explosive Efforts", "Total Jumps"]
                    pos_weekly_sums = tr_df.groupby(['Week', 'Name'])[tr_metrics].sum().reset_index()
                    pos_avg_weekly_total = pos_weekly_sums[tr_metrics].max()

                    for name in players_in_pos:
                        p_data = tr_df[tr_df['Name'] == name]
                        p_weekly_sums = p_data.groupby('Week')[tr_metrics].sum().reset_index()
                        p_avg_weekly_total = p_weekly_sums[tr_metrics].max()

                        c_card1, c_card2 = st.columns([1.5, 3], gap="large")
                        with c_card1:
                            st.markdown(f"""<div class="player-row-container" style="padding: 20px; border: 1px solid #E5E5E7; border-radius:15px; background:white; margin-bottom: 0px;"><div style="text-align:center; padding:15px; background:#f8f9fa; border-bottom:2px solid #FF8200; border-radius: 12px;"><div style="width:90px; height:90px; border-radius:50%; background-color: white; overflow: hidden; display: flex; align-items: center; justify-content: center; border: 3px solid #FF8200; margin: 0 auto 10px auto;"><img src="{p_data["PhotoURL"].iloc[0]}" style="width:100%; height:100%; object-fit: contain;"></div><p style="margin:0; font-weight:900; color:#1D1D1F; font-size:18px;">{name}</p><p style="margin:0; font-size:12px; color:grey;">Weekly Max Volume</p></div><table class="scout-table" style="width:100%; margin-top:15px;"><thead><tr><th>Metric</th><th>Athlete Max</th><th>Pos. Max Total</th></tr></thead><tbody><tr><td style="font-weight:700;">Player Load</td><td>{p_avg_weekly_total['Player Load']:.0f}</td><td>{pos_avg_weekly_total['Player Load']:.0f}</td></tr><tr><td style="font-weight:700;">Est. Dist (y)</td><td>{p_avg_weekly_total['Estimated Distance (y)']:.0f}</td><td>{pos_avg_weekly_total['Estimated Distance (y)']:.0f}</td></tr><tr><td style="font-weight:700;">Explosive</td><td>{p_avg_weekly_total['Explosive Efforts']:.0f}</td><td>{pos_avg_weekly_total['Explosive Efforts']:.0f}</td></tr><tr><td style="font-weight:700;">Total Jumps</td><td>{p_avg_weekly_total['Total Jumps']:.0f}</td><td>{pos_avg_weekly_total['Total Jumps']:.0f}</td></tr></tbody></table></div>""", unsafe_allow_html=True)

                        with c_card2:
                            st.write("<div style='height: 25px;'></div>", unsafe_allow_html=True)
                            t_cols = st.columns(2) 
                            for i, m in enumerate(tr_metrics):
                                with t_cols[i % 2]:
                                    fig_t = go.Figure()
                                    p_t = p_data.groupby('Week')[m].sum().reset_index()
                                    fig_t.add_trace(go.Scatter(x=p_t['Week'], y=p_t[m], name="Athlete", line=dict(color='#4895DB', width=4), mode='lines+markers'))
                                    g_t = tr_df.groupby(['Week', 'Name'])[m].sum().reset_index().groupby('Week')[m].max().reset_index()
                                    fig_t.add_trace(go.Scatter(x=g_t['Week'], y=g_t[m], name="Pos. Max", line=dict(color='#FF8200', dash='dash', width=2), mode='lines'))
                                    
                                    fig_t.update_layout(
                                        title=dict(text=f"<b>Weekly Trend: {m.split(' (')[0]}</b>", font=dict(size=12), x=0.5, y=0.95), 
                                        xaxis=dict(dtick=1, showgrid=False, title="Week"), 
                                        yaxis=dict(showgrid=True, gridcolor='#F5F5F7', rangemode='tozero', title=m), 
                                        height=270, 
                                        margin=dict(l=20, r=20, t=50, b=65), 
                                        showlegend=True, 
                                        legend=dict(orientation="h", y=-0.4, x=0.5, xanchor="center"), 
                                        template="simple_white"
                                    )
                                    st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG, key=f"trend_{name}_{m}_t7")
                        st.write("<div style='height: 30px;'></div>", unsafe_allow_html=True)

            # ==========================================
            # --- TAB CLAUSE 8: PHASE ANALYSIS ---------
            # ==========================================
            elif st.session_state.active_tab_state == "Phase Analysis":
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

            # ==========================================
            # --- TAB CLAUSE 9: PRACTICE PLANNER -------
            # ==========================================
            elif st.session_state.active_tab_state == "Practice Planner":
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

            # ==========================================
            # --- TAB CLAUSE 10: SPRING V. SUMMER ------
            # ==========================================
            elif st.session_state.active_tab_state == "Spring v. Summer":
                st.markdown('<div class="section-header">Spring Max vs. Summer Open Gym</div>', unsafe_allow_html=True)
                spring_gps = full_df_unfiltered[(full_df_unfiltered['Season'] == 'Spring') & (full_df_unfiltered['Session_Type'] == 'Practice')].copy()
                summer_gps = full_df_unfiltered[(full_df_unfiltered['Season'] == 'Summer') & (full_df_unfiltered['Session_Type'] == 'Practice')].copy()
                
                if spring_gps.empty or summer_gps.empty:
                    st.warning("Data check: Ensure both Spring and Summer practice records are loaded to generate card pairings.")
                else:
                    spring_daily = spring_gps.groupby(['Name', 'Date'])[['Player Load', 'Total Jumps', 'Explosive Efforts', 'Estimated Distance (y)', 'Jump Load']].sum().reset_index()
                    summer_daily = summer_gps.groupby(['Name', 'Date'])[['Player Load', 'Total Jumps', 'Explosive Efforts', 'Estimated Distance (y)', 'Jump Load', 'Session_Name']].agg({
                        'Player Load': 'sum', 'Total Jumps': 'sum', 'Explosive Efforts': 'sum', 'Estimated Distance (y)': 'sum', 'Jump Load': 'sum', 'Session_Name': lambda x: ' | '.join(x.astype(str).unique())
                    }).reset_index()
                    
                    metric_cols = ['Player Load', 'Total Jumps', 'Explosive Efforts', 'Estimated Distance (y)', 'Jump Load']
                    spring_peaks = spring_daily.groupby('Name')[metric_cols].max().reset_index()
                    spring_peaks.columns = ['Name', 'Spring Peak Load', 'Spring Peak Jumps', 'Spring Peak Efforts', 'Spring Peak Distance', 'Spring Peak Jump Load']
                    
                    comp_metric_label = st.selectbox("Select Metric to Compare", ["Player Load", "Total Jumps", "Explosive Efforts", "Estimated Distance (y)", "Jump Load"], key="ss_metric_select_t10")
                    spring_col_map = {"Player Load": "Spring Peak Load", "Total Jumps": "Spring Peak Jumps", "Explosive Efforts": "Spring Peak Efforts", "Estimated Distance (y)": "Spring Peak Distance", "Jump Load": "Spring Peak Jump Load"}
                    target_spring_col = spring_col_map[comp_metric_label]
                    
                    summer_summary = summer_daily.groupby('Name').agg({comp_metric_label: ['max', 'mean']}).reset_index()
                    summer_summary.columns = ['Name', 'Summer Peak', 'Summer Avg']
                    
                    merged_comp = pd.merge(spring_peaks[['Name', target_spring_col]], summer_summary, on='Name', how='inner')
                    merged_comp['Peak Change (%)'] = ((merged_comp['Summer Peak'] - merged_comp[target_spring_col]) / merged_comp[target_spring_col] * 100).fillna(0)
                    
                    st.markdown(f"### {comp_metric_label}")
                    tbl_html = f"""<table class="scout-table"><thead><tr><th>Athlete Name</th><th>Highest Spring Peak Day</th><th>Highest Summer Peak Day</th><th>Summer Practice Avg</th><th>Peak Volume Shift (%)</th></tr></thead><tbody>"""
                    for _, row in merged_comp.sort_values('Name').iterrows():
                        shft_val = row['Peak Change (%)']
                        tbl_html += f"""<tr><td style="font-weight:700; text-align:left !important; padding-left:15px;">{row['Name']}</td><td>{row[target_spring_col]:.1f}</td><td>{row['Summer Peak']:.1f}</td><td>{row['Summer Avg']:.1f}</td><td style="{"color:#28a745; font-weight:bold;" if shft_val >= 0 else "color:#dc3545; font-weight:bold;"}">{shft_val:+.1f}%</td></tr>"""
                    st.markdown(tbl_html + "</tbody></table>", unsafe_allow_html=True)
                    
                    st.write("<br>", unsafe_allow_html=True)
                    st.divider()
                    st.markdown("### Summer Session Scores")
                    target_ath_comp = st.selectbox("Select Athlete", sorted(merged_comp['Name'].unique()), key="ss_ath_select_t10")
                    
                    meta_rows = full_df_unfiltered[full_df_unfiltered['Name'] == target_ath_comp]
                    correct_photo = meta_rows.iloc[0].get('PhotoURL', "https://www.w3schools.com/howto/img_avatar.png") if not meta_rows.empty else "https://www.w3schools.com/howto/img_avatar.png"
                    pos_label = meta_rows.iloc[0].get('Position', "N/A") if not meta_rows.empty else "N/A"

                    ath_benchmarks = spring_peaks[spring_peaks['Name'] == target_ath_comp]
                    ath_summer_days = summer_daily[summer_daily['Name'] == target_ath_comp].sort_values('Date', ascending=False)
                    
                    if ath_benchmarks.empty or ath_summer_days.empty:
                        st.info(f"Insufficient historical data pairings found to build benchmarks for {target_ath_comp}.")
                    else:
                        b_load = ath_benchmarks.iloc[0]['Spring Peak Load']
                        b_jumps = ath_benchmarks.iloc[0]['Spring Peak Jumps']
                        b_efforts = ath_benchmarks.iloc[0]['Spring Peak Efforts']
                        b_dist = ath_benchmarks.iloc[0]['Spring Peak Distance']
                        b_jload = ath_benchmarks.iloc[0]['Spring Peak Jump Load']
                        
                        ath_days_list = ath_summer_days.to_dict('records')
                        for s_idx in range(0, len(ath_days_list), 2):
                            card_cols = st.columns(2)
                            for col_offset in range(2):
                                if s_idx + col_offset < len(ath_days_list):
                                    row_day = ath_days_list[s_idx + col_offset]
                                    g_load = math.ceil((row_day['Player Load'] / b_load) * 100) if b_load > 0 else 0
                                    g_jumps = math.ceil((row_day['Total Jumps'] / b_jumps) * 100) if b_jumps > 0 else 0
                                    g_efforts = math.ceil((row_day['Explosive Efforts'] / b_efforts) * 100) if b_efforts > 0 else 0
                                    g_dist = math.ceil((row_day['Estimated Distance (y)'] / b_dist) * 100) if b_dist > 0 else 0
                                    g_jload = math.ceil((row_day['Jump Load'] / b_jload) * 100) if b_jload > 0 else 0
                                    total_session_score = math.ceil((g_load + g_jumps + g_efforts + g_dist + g_jload) / 5)
                                    
                                    with card_cols[col_offset]: st.markdown(f"""<div style="border:1px solid #E5E5E7; border-radius:15px; padding:15px; margin-bottom:20px; background-color:white;"><div style="display:flex; align-items:center; gap:12px; margin-bottom:10px; padding-bottom:8px; border-bottom:2px solid #FF8200;"><img src="{correct_photo}" class="gallery-photo" style="width:55px; height:55px;"><div><p style="margin:0; font-weight:900; color:#1D1D1F; font-size:15px;">{row_day['Session_Name']}</p><p style="margin:0; color:#4895DB; font-weight:700; font-size:12px;">{row_day['Date'].strftime('%m/%d/%Y')} | {pos_label}</p></div></div><div style="display:flex; align-items:center; gap:10px;"><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Summer</th><th>Spring Max</th></tr></thead><tbody><tr><td>Player Load</td><td>{row_day['Player Load']:.1f}</td><td>{b_load:.1f}</td></tr><tr><td>Total Jumps</td><td>{int(row_day['Total Jumps'])}</td><td>{int(b_jumps)}</td></tr><tr><td>Explosive Efforts</td><td>{int(row_day['Explosive Efforts'])}</td><td>{int(b_efforts)}</td></tr><tr><td>Jump Load</td><td>{row_day['Jump Load']:.1f}</td><td>{b_jload:.1f}</td></tr><tr><td>Est. Distance (y)</td><td>{row_day['Estimated Distance (y)']:.1f}</td><td>{b_dist:.1f}</td></tr></tbody></table></div><div style="flex:1; text-align:center;"><div class="score-box" style="background-color:{get_flipped_gradient(total_session_score)}; font-size:26px; padding:10px 5px; min-width:70px; margin:0 auto;">{total_session_score}</div></div></div></div>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sync Error: {e}")
