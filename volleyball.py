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
    
    /* Lowers password input and adds global top breathing room */
    .block-container { 
        padding-top: 5rem !important; 
        padding-bottom: 3rem !important; 
    }
    
    .viewerBadge_link__1S137, .main_heading_anchor__m6v0K, a.header-anchor { display: none !important; }
    header a { display: none !important; }
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #4895DB; color: white; padding: 4px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 11px; text-transform: uppercase; }
    .scout-table td { padding: 4px; border-bottom: 1px solid #F5F5F7; font-size: 11px; color: #1D1D1F; }
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

    /* Intake Cards Container Styling */
    .intake-card {
        border: 1px solid #E5E5E7;
        border-radius: 12px;
        padding: 15px;
        background-color: #FFFFFF;
        margin-bottom: 15px;
    }
    .intake-card-header {
        font-weight: 800;
        font-size: 15px;
        color: #4895DB;
        border-bottom: 2px solid #FF8200;
        padding-bottom: 4px;
        margin-bottom: 12px;
    }
    .intake-col-title {
        font-weight: 800;
        font-size: 13px;
        color: #1D1D1F;
        margin-bottom: 8px;
        text-transform: uppercase;
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
    
        # Pre-Season starts July 30th onward
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

    # ASH Sheet (Contains ASH Shoulder + ISO-Y)
    try:
        ash_df = pd.read_csv(st.secrets["ASH_SHEET_URL"])
        ash_df.columns = ash_df.columns.str.strip()
        ash_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        ash_df['Test Date'] = pd.to_datetime(ash_df['Test Date'], errors='coerce')
        for col in ['Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force [N] (Asym)(%)', 'Peak Vertical Force / BM [N/kg] (L)', 'Peak Vertical Force / BM [N/kg] (R)']:
            if col in ash_df.columns:
                ash_df[col] = pd.to_numeric(ash_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
        ash_df['Season'] = ash_df['Test Date'].apply(assign_season)
    except:
        ash_df = pd.DataFrame(columns=['Name', 'Test Date', 'Isometric Type', 'Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force [N] (Asym)(%)', 'Season'])

    # External Rotation (ROM) Sheet
    try:
        er_df = pd.read_csv(st.secrets["ER_SHEET_URL"])
        er_df.columns = er_df.columns.str.strip()
        er_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        er_df['Test Date'] = pd.to_datetime(er_df['Test Date'], errors='coerce')
        for col in ['L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)']:
            if col in er_df.columns:
                er_df[col] = pd.to_numeric(er_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
        er_df['Season'] = er_df['Test Date'].apply(assign_season)
    except:
        er_df = pd.DataFrame(columns=['Name', 'Test Date', 'Movement', 'L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)', 'Season'])

    # Single Leg Calf Raise Sheet
    try:
        calf_df = pd.read_csv(st.secrets["CALF_SHEET_URL"])
        calf_df.columns = calf_df.columns.str.strip()
        calf_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        calf_df['Test Date'] = pd.to_datetime(calf_df['Test Date'], errors='coerce')
        for col in ['Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force / BM [N/kg] (L)', 'Peak Vertical Force / BM [N/kg] (R)']:
            if col in calf_df.columns:
                calf_df[col] = pd.to_numeric(calf_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
        calf_df['Season'] = calf_df['Test Date'].apply(assign_season)
    except:
        calf_df = pd.DataFrame(columns=['Name', 'Test Date', 'Season'])

    # Hip AD/AB Sheet
    try:
        hip_df = pd.read_csv(st.secrets["HIP_SHEET_URL"])
        hip_df.columns = hip_df.columns.str.strip()
        hip_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        hip_df['Test Date'] = pd.to_datetime(hip_df['Test Date'], errors='coerce')
        if 'Direction' in hip_df.columns:
            hip_df['Direction'] = hip_df['Direction'].astype(str).str.strip()
        for col in ['L Max Force (N)', 'R Max Force (N)', 'Max Imbalance', 'L Max Ratio', 'R Max Ratio']:
            if col in hip_df.columns:
                hip_df[col] = pd.to_numeric(hip_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
        hip_df['Season'] = hip_df['Test Date'].apply(assign_season)
    except:
        hip_df = pd.DataFrame(columns=['Name', 'Test Date', 'Direction', 'Season'])

    # Dedicated Shoulder IR/ER Sheet
    try:
        shoulder_df = pd.read_csv(st.secrets["SHOULDER_SHEET_URL"])
        shoulder_df.columns = shoulder_df.columns.str.strip()
        shoulder_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        shoulder_df['Test Date'] = pd.to_datetime(shoulder_df['Test Date'], errors='coerce')
        if 'Direction' in shoulder_df.columns:
            shoulder_df['Direction'] = shoulder_df['Direction'].astype(str).str.strip()
        for col in ['L Max Force (N)', 'R Max Force (N)', 'Max Imbalance', 'L Max Ratio', 'R Max Ratio']:
            if col in shoulder_df.columns:
                shoulder_df[col] = pd.to_numeric(shoulder_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
        shoulder_df['Season'] = shoulder_df['Test Date'].apply(assign_season)
    except:
        shoulder_df = pd.DataFrame(columns=['Name', 'Test Date', 'Direction', 'Season'])

    phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
    phase_df = heavy_sanitize(phase_df)
    if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
    phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
    date_season_map = df.drop_duplicates('Date').set_index('Date')['Season'].to_dict()
    phase_df['Season'] = phase_df['Date'].map(date_season_map).fillna('Spring')
    
    try:
        thresh_df = pd.read_csv(st.secrets["THRESH_SHEET_URL"])
        thresh_df.columns = thresh_df.columns.str.strip()
        for col in ['Load_Limit', 'Jump_Limit']:
            if col in thresh_df.columns:
                thresh_df[col] = pd.to_numeric(thresh_df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0).astype(float)
    except:
        thresh_df = None
        
    return df.dropna(subset=['Date']), match_df.dropna(subset=['Date']), cmj_df, phase_df, thresh_df, ash_df, er_df, calf_df, hip_df, shoulder_df


# --- 5. EXECUTION BLOCK CONTEXT ---
if check_password():
    if "is_printing" not in st.session_state:
        st.session_state.is_printing = False

    LOCKED_CONFIG = {'staticPlot': False, 'displayModeBar': False}

    try:
        raw_df, raw_match_df, raw_cmj_df, raw_phase_df, thresh_df, raw_ash_df, raw_er_df, raw_calf_df, raw_hip_df, raw_shoulder_df = load_all_data()

        # --- GLOBAL SIDEBAR ---
        st.sidebar.markdown("### Season")
        selected_season = st.sidebar.radio("Select Season", ["Spring", "Summer", "Pre-Season", "Testing"], index=2, key="global_season_toggle")
        
        if selected_season != "Testing":
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
            st.sidebar.info("Currently displaying: Testing")
            df_master, match_master, cmj_master, ash_master, er_master, calf_master, hip_master, shoulder_master, phase_master = raw_df, raw_match_df, raw_cmj_df, raw_ash_df, raw_er_df, raw_calf_df, raw_hip_df, raw_shoulder_df, raw_phase_df
            
        full_df_unfiltered = raw_df.copy()

        phase_map = {
            "Mini Games (Set 1)": "Mini Games", "Mini Games (Set 2)": "Mini Games", "Brizo (2)": "Brizo",
            "2 Ball (Set 1)": "2 Ball", "2 Ball (Set 2)": "2 Ball", "2 Ball (Set 3)": "2 Ball", "2 Ball (Set 4)": "2 Ball",
            "serving (2)": "Serving", "serving": "Serving", "Serving (2)": "Serving", "2/3 Hitters (2)": "2/3 Hitters",
            "5v5 (2)": "5v5", "Serve & Pass": "Serve and Pass"
        }
        all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
        metrics_to_score = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]
        cmj_col = 'Jump Height (Imp-Mom) [cm]'
        rsi_col = 'RSI-modified [m/s]'

        master_athlete_list = sorted(list(
            set(raw_df['Name'].unique()) | 
            set(raw_cmj_df['Name'].unique()) | 
            set(raw_ash_df['Name'].unique()) | 
            set(raw_er_df['Name'].unique()) |
            set(raw_calf_df['Name'].unique()) |
            set(raw_hip_df['Name'].unique()) |
            set(raw_shoulder_df['Name'].unique())
        ))
        session_list = df_master[df_master['Session_Name'].notna()].sort_values('Date', ascending=False)['Session_Name'].unique().tolist()

        st.markdown('<div class="main-logo-container" style="text-align: center; margin-top: 10px; margin-bottom: 15px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120"><div style="color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;">LADY VOLS VOLLEYBALL PERFORMANCE</div></div>', unsafe_allow_html=True)

        if selected_season == "Testing":
            st.markdown('<div class="section-header">Testing Profile</div>', unsafe_allow_html=True)
            testing_season_tabs = st.tabs(["Spring Testing", "Summer Testing", "Pre-Season Testing", "Intake Testing", "Season Comparison"])
            
            # --- TAB 1, 2, 3: INDIVIDUAL SEASONAL TESTING ---
            for tab_idx, s_label in enumerate(["Spring", "Summer", "Pre-Season"]):
                with testing_season_tabs[tab_idx]:
                    c_t_ath, _ = st.columns([2, 2])
                    with c_t_ath:
                        selected_athlete_test = st.selectbox(f"Select Athlete ({s_label})", master_athlete_list, key=f"nav_ath_test_{s_label}")
                    
                    meta_lookup = full_df_unfiltered[full_df_unfiltered['Name'] == selected_athlete_test]
                    photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                    pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"

                    # Top Header Card
                    st.markdown(f'<div style="display:flex; align-items:center; gap:20px; padding:15px; background:#f8f9fa; border-radius:15px; border-left:6px solid #FF8200; margin-bottom:20px;"><img src="{photo_val}" class="gallery-photo" style="width:80px; height:80px;"><div><h2 style="margin:0; color:#1D1D1F;">{selected_athlete_test}</h2><p style="margin:0; color:#4895DB; font-weight:700; font-size:16px;">{pos_val} | {s_label} Testing Profile</p></div></div>', unsafe_allow_html=True)

                    # --- SECTION 1: COUNTERMOVEMENT JUMP ---
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

                    # --- SECTION 2: ASH SHOULDER: ISO I ---
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

                    # --- SECTION 3: EXTERNAL ROTATION: ROM ---
                    st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">EXTERNAL ROTATION: ROM</h4>', unsafe_allow_html=True)
                    er_t_data = raw_er_df[(raw_er_df['Name'] == selected_athlete_test) & (raw_er_df['Season'] == s_label)].sort_values('Test Date')
                    
                    if not er_t_data.empty:
                        ec1, ec2 = st.columns([1.5, 3.5])
                        with ec1:
                            baseline_er = er_t_data.head(1)
                            base_l_rom = baseline_er.iloc[-1]['L Max ROM (°)'] if not baseline_er.empty else 0.0
                            base_r_rom = baseline_er.iloc[-1]['R Max ROM (°)'] if not baseline_er.empty else 0.0
                            latest_er = er_t_data.iloc[-1]
                            cur_l_rom = latest_er['L Max ROM (°)']
                            cur_r_rom = latest_er['R Max ROM (°)']
                            cur_asym_rom = latest_er['ROM Asymmetry (%)'] if 'ROM Asymmetry (%)' in latest_er else 0.0
                            
                            rom_pct_l = ((cur_l_rom - base_l_rom) / base_l_rom * 100) if base_l_rom > 0 else 0
                            rom_pct_r = ((cur_r_rom - base_r_rom) / base_r_rom * 100) if base_r_rom > 0 else 0
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
                        st.info(f"No External Rotation ROM testing records logged for {selected_athlete_test} in {s_label}.")

          # --- TAB 4: INTAKE TESTING TAB ---
            with testing_season_tabs[3]:
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

                    # --- LEFT PANEL: HIGHLY DEFINED ANATOMICAL MUSCLE MAP ---
                    with hud_col1:
                        hud_html = """
                        <!DOCTYPE html>
                        <html>
                        <head>
                        <style>
                            body {
                                margin: 0;
                                padding: 0;
                                background-color: transparent;
                                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            }
                            .hud-dashboard-card {
                                background: #FFFFFF;
                                border-radius: 16px;
                                padding: 16px;
                                border: 1px solid #E5E5E7;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.03);
                            }
                            .hud-header-title {
                                color: #1D1D1F;
                                font-weight: 800;
                                font-size: 13px;
                                letter-spacing: 1px;
                                text-transform: uppercase;
                                border-bottom: 2px solid #FF8200;
                                padding-bottom: 6px;
                                margin-bottom: 12px;
                            }
                            .hud-body-viewport {
                                position: relative;
                                width: 100%;
                                height: 380px;
                                background: #FAFDFD;
                                border-radius: 12px;
                                border: 1px solid #D5E5E8;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                overflow: hidden;
                            }
                            svg {
                                width: 100%;
                                height: 100%;
                            }
                        </style>
                        </head>
                        <body>
                            <div class="hud-dashboard-card">
                                <div class="hud-header-title">Anatomy Location Map</div>
                                <div class="hud-body-viewport">
                                    <svg viewBox="0 0 140 220" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
                                        <defs>
                                            <linearGradient id="bodySkinGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                                <stop offset="0%" stop-color="#CFD3D6" />
                                                <stop offset="35%" stop-color="#F2F4F7" />
                                                <stop offset="65%" stop-color="#E4E8EC" />
                                                <stop offset="100%" stop-color="#B6BAC0" />
                                            </linearGradient>
                                        </defs>

                                        <!-- DROP SHADOW AT BASE -->
                                        <ellipse cx="68" cy="214" rx="20" ry="3.5" fill="#000000" opacity="0.12" />

                                        <!-- BASE BODY SILHOUETTE WITH SMOOTH CURVES -->
                                        <g stroke="#2C3036" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                                            
                                            <path d="M 68 8 
                                                     C 73 8, 77 11, 77 17 
                                                     C 77 23, 73 27, 71 28
                                                     C 72 30, 74 32, 77 33
                                                     C 83 35, 93 39, 98 46
                                                     C 102 52, 106 66, 107 76
                                                     C 108 86, 108 96, 107 106
                                                     C 107 110, 104 112, 102 110
                                                     C 100 102, 98 92, 95 82
                                                     C 92 72, 89 66, 86 66
                                                     C 86 76, 85 88, 84 98
                                                     C 83 108, 84 118, 83 130
                                                     C 81 144, 79 158, 80 172
                                                     C 81 184, 82 195, 83 203
                                                     C 83 208, 78 211, 75 211
                                                     C 73 211, 71 207, 71 200
                                                     C 71 186, 71 170, 71 155
                                                     C 71 140, 71 126, 71 114
                                                     C 70 126, 68 140, 68 155
                                                     C 68 170, 66 186, 66 200
                                                     C 66 207, 63 211, 60 211
                                                     C 56 211, 53 208, 54 203
                                                     C 56 195, 57 184, 57 172
                                                     C 57 158, 55 144, 53 130
                                                     C 51 118, 51 108, 50 98
                                                     C 49 88, 47 76, 47 66
                                                     C 45 66, 42 72, 39 82
                                                     C 36 92, 33 102, 31 110
                                                     C 29 112, 26 110, 26 106
                                                     C 26 96, 26 86, 27 76
                                                     C 28 66, 32 52, 36 46
                                                     C 41 39, 51 35, 57 33
                                                     C 60 32, 62 30, 63 28
                                                     C 61 27, 57 23, 57 17
                                                     C 57 11, 61 8, 68 8 Z" 
                                                  fill="url(#bodySkinGradient)" />

                                            <!-- ORANGE PLUMB LINE (ANATOMICAL AXIS) -->
                                            <line x1="68" y1="8" x2="68" y2="211" stroke="#FF8200" stroke-width="1.3" />

                                            <!-- RED HORIZONTAL GUIDELINES -->
                                            <line x1="53" y1="116" x2="83" y2="116" stroke="#D32F2F" stroke-width="1.1" />
                                            <line x1="57" y1="165" x2="79" y2="165" stroke="#D32F2F" stroke-width="1.1" />

                                            <!-- HIGHLY DEFINED MUSCULATURE OUTLINES (Chest, Abs, Quads, Calves) -->
                                            <g stroke="#3A3F46" stroke-width="1" fill="none">
                                                <!-- Neck Muscles (Sternocleidomastoid) -->
                                                <path d="M 64 28 C 65 33, 67 36, 68 37" />
                                                <path d="M 72 28 C 71 33, 69 36, 68 37" />
                                                
                                                <!-- Clavicle / Collarbone -->
                                                <path d="M 68 37 C 60 35, 52 38, 48 40 M 68 37 C 76 35, 84 38, 88 40" stroke-width="1.1" />
                                                
                                                <!-- Shoulder Caps (Deltoids) -->
                                                <path d="M 47 40 C 42 45, 41 55, 47 62 C 50 56, 50 46, 47 40 Z" fill="#DDE2E6" opacity="0.6" />
                                                <path d="M 89 40 C 94 45, 95 55, 89 62 C 86 56, 86 46, 89 40 Z" fill="#DDE2E6" opacity="0.6" />
                                                
                                                <!-- Pectorals (Chest Definition) -->
                                                <path d="M 52 42 C 60 41, 67 45, 68 53 C 60 55, 52 51, 52 42 Z" fill="#E2E7EC" opacity="0.7" />
                                                <path d="M 84 42 C 76 41, 69 45, 68 53 C 76 55, 84 51, 84 42 Z" fill="#E2E7EC" opacity="0.7" />
                                                
                                                <!-- Six-Pack Abdominal Muscles (Distinct Defined Segments) -->
                                                <g stroke="#2C3036" stroke-width="0.95" fill="#E5EAEE">
                                                    <path d="M 59 56 C 63 55, 67 55, 67 61 C 63 62, 59 61, 59 56 Z" />
                                                    <path d="M 77 56 C 73 55, 69 55, 69 61 C 73 62, 77 61, 77 56 Z" />
                                                    <path d="M 58 64 C 63 63, 67 63, 67 69 C 63 70, 58 69, 58 64 Z" />
                                                    <path d="M 78 64 C 73 63, 69 63, 69 69 C 73 70, 78 69, 78 64 Z" />
                                                    <path d="M 59 72 C 63 71, 67 71, 67 77 C 63 78, 59 77, 59 72 Z" />
                                                    <path d="M 77 72 C 73 71, 69 71, 69 77 C 73 78, 77 77, 77 72 Z" />
                                                </g>
                                                
                                                <!-- Serratus / Obliques -->
                                                <path d="M 48 60 C 52 61, 55 64, 57 66" />
                                                <path d="M 88 60 C 84 61, 81 64, 79 66" />
                                                <path d="M 49 68 C 53 69, 55 72, 57 74" />
                                                <path d="M 87 68 C 83 69, 81 72, 79 74" />

                                                <!-- Hip / Inguinal Crease -->
                                                <path d="M 52 92 C 58 98, 64 105, 68 108" stroke-width="1.1" />
                                                <path d="M 84 92 C 78 98, 72 105, 68 108" stroke-width="1.1" />

                                                <!-- Quadriceps (Vastus Medialis / Lateralis Definition) -->
                                                <path d="M 53 98 C 50 108, 51 125, 57 138 C 61 125, 60 108, 53 98 Z" fill="#DDE3E8" opacity="0.6" />
                                                <path d="M 83 98 C 86 108, 85 125, 79 138 C 75 125, 76 108, 83 98 Z" fill="#DDE3E8" opacity="0.6" />
                                                <path d="M 62 104 C 58 115, 58 132, 62 142 C 65 132, 64 115, 62 104 Z" fill="#D5DCF1" opacity="0.6" />
                                                <path d="M 74 104 C 78 115, 78 132, 74 142 C 71 132, 72 115, 74 104 Z" fill="#D5DCF1" opacity="0.6" />

                                                <!-- Knees (Kneecaps / Patella) -->
                                                <ellipse cx="60" cy="147" rx="3" ry="3.8" stroke-width="1" fill="#E8EDF2" />
                                                <ellipse cx="76" cy="147" rx="3" ry="3.8" stroke-width="1" fill="#E8EDF2" />

                                                <!-- Calves (Gastrocnemius & Shin Bone Lines) -->
                                                <path d="M 55 152 C 52 160, 52 175, 57 188 C 58 175, 58 160, 55 152 Z" fill="#D5DCF1" opacity="0.65" />
                                                <path d="M 81 152 C 84 160, 84 175, 79 188 C 78 175, 78 160, 81 152 Z" fill="#D5DCF1" opacity="0.65" />
                                                <path d="M 60 152 L 58 198" stroke-width="1" />
                                                <path d="M 76 152 L 78 198" stroke-width="1" />
                                            </g>
                                        </g>

                                        <!-- NODES & CALLOUT LINES / BADGES -->
                                        <!-- Node 1: Left Shoulder IR/ER (Orange) -->
                                        <circle cx="91" cy="46" r="3.5" fill="#FF8200" stroke="#FFFFFF" stroke-width="1" />
                                        <line x1="91" y1="46" x2="118" y2="46" stroke="#FF8200" stroke-width="1.8" stroke-dasharray="2,2" />
                                        <rect x="112" y="39" width="14" height="14" rx="3" fill="#FF8200" />
                                        <text x="119" y="50" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">1</text>

                                        <!-- Node 2: ISO-Y Spine/Thoracic (Orange) -->
                                        <circle cx="68" cy="53" r="3.5" fill="#FF8200" stroke="#FFFFFF" stroke-width="1" />
                                        <line x1="68" y1="53" x2="118" y2="67" stroke="#FF8200" stroke-width="1.8" stroke-dasharray="2,2" />
                                        <rect x="112" y="60" width="14" height="14" rx="3" fill="#FF8200" />
                                        <text x="119" y="71" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">2</text>

                                        <!-- Node 3: Hip Adduction (Blue) -->
                                        <circle cx="74" cy="122" r="3.5" fill="#4895DB" stroke="#FFFFFF" stroke-width="1" />
                                        <line x1="74" y1="122" x2="118" y2="122" stroke="#4895DB" stroke-width="1.8" stroke-dasharray="2,2" />
                                        <rect x="112" y="115" width="14" height="14" rx="3" fill="#4895DB" />
                                        <text x="119" y="126" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">3</text>

                                        <!-- Node 4: Hip Abduction (Blue) -->
                                        <circle cx="53" cy="116" r="3.5" fill="#4895DB" stroke="#FFFFFF" stroke-width="1" />
                                        <line x1="53" y1="116" x2="22" y2="116" stroke="#4895DB" stroke-width="1.8" stroke-dasharray="2,2" />
                                        <rect x="14" y="109" width="14" height="14" rx="3" fill="#4895DB" />
                                        <text x="21" y="120" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">4</text>

                                        <!-- Node 5: Single Leg Calf Raise (Blue) -->
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
                        import streamlit.components.v1 as components
                        components.html(hud_html, height=450)

                    # --- RIGHT PANEL: LIGHT DETAILS CARDS ---
                    with hud_col2:
                        st.markdown("""
                            <style>
                            .hud-details-card {
                                background: #FFFFFF;
                                border-radius: 16px;
                                padding: 20px;
                                border: 1px solid #E5E5E7;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.03);
                            }
                            .hud-header-title-light {
                                color: #1D1D1F;
                                font-weight: 800;
                                font-size: 13px;
                                letter-spacing: 1px;
                                text-transform: uppercase;
                                border-bottom: 2px solid #FF8200;
                                padding-bottom: 6px;
                                margin-bottom: 16px;
                            }
                            .hud-metric-row-light {
                                background: #F8F9FA;
                                border-left: 4px solid #FF8200;
                                border-radius: 8px;
                                padding: 10px 14px;
                                margin-bottom: 10px;
                                color: #1D1D1F;
                                border-top: 1px solid #E5E5E7;
                                border-right: 1px solid #E5E5E7;
                                border-bottom: 1px solid #E5E5E7;
                            }
                            .hud-metric-row-light-blue {
                                background: #F8F9FA;
                                border-left: 4px solid #4895DB;
                                border-radius: 8px;
                                padding: 10px 14px;
                                margin-bottom: 10px;
                                color: #1D1D1F;
                                border-top: 1px solid #E5E5E7;
                                border-right: 1px solid #E5E5E7;
                                border-bottom: 1px solid #E5E5E7;
                            }
                            .node-badge-orange {
                                display: inline-block;
                                width: 20px;
                                height: 20px;
                                background: #FF8200;
                                color: #FFFFFF;
                                font-weight: 900;
                                font-size: 11px;
                                border-radius: 4px;
                                text-align: center;
                                line-height: 20px;
                                margin-right: 8px;
                            }
                            .node-badge-blue {
                                display: inline-block;
                                width: 20px;
                                height: 20px;
                                background: #4895DB;
                                color: #FFFFFF;
                                font-weight: 900;
                                font-size: 11px;
                                border-radius: 4px;
                                text-align: center;
                                line-height: 20px;
                                margin-right: 8px;
                            }
                            </style>
                            <div class="hud-details-card">
                                <div class="hud-header-title-light">Anatomy Location Assessment Details</div>
                        """, unsafe_allow_html=True)

                        # NODE 1: SHOULDER IR/ER
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

                        # NODE 2: ISO-Y STRENGTH
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

                        # NODE 3 & 4: HIP AD/AB
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

                        # NODE 5: SINGLE LEG CALF RAISE
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
                    
                    
                    
            # --- TAB 5: CROSS-SEASON TESTING COMPARISON ---
            with testing_season_tabs[4]:
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
                        cmj_avg_season = cmj_comp.groupby('Season')[[cmj_col, rsi_col]].mean().reset_index()
                        
                        max_h = cmj_avg_season[cmj_col].max() if not cmj_avg_season.empty else 50.0
                        max_r = cmj_avg_season[rsi_col].max() if not cmj_avg_season.empty else 1.0

                        fig_comp_cmj = make_subplots(specs=[[{"secondary_y": True}]])
                        
                        fig_comp_cmj.add_trace(
                            go.Bar(
                                x=cmj_avg_season['Season'], 
                                y=cmj_avg_season[cmj_col], 
                                name="Avg CMJ Height (cm)", 
                                marker_color='#FF8200', 
                                text=[f"<b>{val:.1f} cm</b>" for val in cmj_avg_season[cmj_col]], 
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
                                text=[f"<b>RSI: {val:.2f}</b>" for val in cmj_avg_season[rsi_col]], 
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
                            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
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

            if "active_tab_state" not in st.session_state or st.session_state.active_tab_state not in tab_titles:
                st.session_state.active_tab_state = tab_titles[0]

            selected_tab_label = st.radio("Navigation View Menu Selection Control", tab_titles, label_visibility="collapsed", horizontal=True, key="master_app_structural_gate_radio")
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

                if p_row.empty:
                    curr_date_prof = pd.to_datetime(target_date_str) if (selected_season == "Spring" and selected_session_prof == tournament_label) else pd.to_datetime(df_t0['Date'].max() if not df_t0.empty else "2026-08-06")
                    meta_lookup = df_t0[df_t0['Name'] == selected_athlete_prof]
                    pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"
                    photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                    p_meta = pd.Series({'Name': selected_athlete_prof, 'Position': pos_val, 'PhotoURL': photo_val})
                    p_row = pd.Series({m: 0.0 for m in all_metrics})
                    p_row['Name'] = selected_athlete_prof

                # Updated: Look at individual practice records in the 30-day lookback window instead of daily combined sums
                # Updated: Look at practice sessions up to the current row index/Sheet_Order within the 30-day window
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
                p_ph = phase_t0[(phase_t0['Name'] == selected_athlete_prof) & (phase_t0['Date'].dt.date == curr_date_prof.date())].copy()
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
                                
                                # Updated: Derive 30-day max benchmarks directly from session-level entries
                                # Updated: Ensure practice 1 only looks at historical sessions + itself, not future sessions on the same day
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
                    
                    # Sort sessions chronologically by Date and Sheet Order
                    p_sessions = p_full.sort_values(['Date', 'Sheet_Order']).reset_index(drop=True)

                    scores_list = []
                    for idx, row in p_sessions.iterrows():
                        row_grades = []
                        curr_order = row.get('Sheet_Order', float('inf'))
                        
                        # Lookback: individual sessions up to the current session (ignoring future sessions on the same day)
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
                        
                        # Keep display solely as Date string so multiple practices share the exact same vertical line on X-axis
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
                        
                        # Add connect-the-dots line across all ordered sessions
                        fig_master.add_trace(go.Scatter(
                            x=master_df_history['Display'],
                            y=master_df_history['Score'],
                            mode='lines',
                            line=dict(color='#4895DB', width=2),
                            showlegend=False,
                            hoverinfo='skip'
                        ))

                        # Practice points (plotted on exact same date string line)
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
                            
                        # Match points
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
                            
                        # Unique week vertical dividers
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
                                except: prev_match_name = "N/A"
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
                            st.plotly_chart(fig_cmj, use_container_width=True, key=f"integrated_cmj_final_{sel_ath_hist}_t4")

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
            # --- TAB CLAUSE 5: MATCH SUMMARY ----------
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
            # --- TAB CLAUSE 6: POSITION ANALYSIS ------
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
            # --- TAB CLAUSE 7: PHASE ANALYSIS ---------
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
            # --- TAB CLAUSE 8: PRACTICE PLANNER -------
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
            # --- TAB CLAUSE 9: SPRING V. SUMMER -------
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
