import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

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
        if 1 <= m <= 4: return 'Spring'
        elif m == 5 and d >= 26: return 'Summer'
        elif m > 5: return 'Summer'
        else: return 'Spring'

    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    match_df = pd.read_csv(st.secrets["MATCHES_SHEET_URL"])
    
    df = heavy_sanitize(df)
    df['Sheet_Order'] = range(len(df))
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    if 'Week' in df.columns:
        df['Week'] = pd.to_numeric(df['Week'].astype(str).str.extract('(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    df['Session_Type'] = df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
    df['Season'] = df['Date'].apply(assign_season)

    match_df = heavy_sanitize(match_df)
    match_df['Sheet_Order'] = range(len(match_df))
    match_df['Date'] = pd.to_datetime(match_df['Date'], errors='coerce')
    if 'Week' in match_df.columns:
        match_df['Week'] = pd.to_numeric(match_df['Week'].astype(str).str.extract('(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
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
        cmj_df['Week'] = pd.to_numeric(cmj_df['Week'].astype(str).str.extract('(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    cmj_df['Season'] = cmj_df['Test Date'].apply(assign_season)

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
        ash_df = pd.DataFrame(columns=['Name', 'Test Date', 'Isometric Type', 'Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force [N] (Asym)(%)', 'Season'])

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
        
    return df.dropna(subset=['Date']), match_df.dropna(subset=['Date']), cmj_df, phase_df, thresh_df, ash_df, er_df


# --- 5. EXECUTION BLOCK CONTEXT ---
if check_password():
    if "is_printing" not in st.session_state:
        st.session_state.is_printing = False

    LOCKED_CONFIG = {'staticPlot': False, 'displayModeBar': False}

    try:
        raw_df, raw_match_df, raw_cmj_df, raw_phase_df, thresh_df, raw_ash_df, raw_er_df = load_all_data()

        # --- GLOBAL HIERARCHICAL SIDEBAR NAVIGATION ---
        st.sidebar.markdown("### Season Navigation")
        selected_season = st.sidebar.radio("Select Season", ["Summer", "Spring"], index=0, key="global_season_toggle")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {selected_season} Views")

        # Define Sub-tabs per Season according to your layout layout specifications
        if selected_season == "Summer":
            sub_tab_options = [
                "Individual Profile", 
                "Practice Scores", 
                "Daily Combined Scores", 
                "Spring Max v. Daily Combined", 
                "Practice History", 
                "Position Analysis", 
                "Spring v. Summer"
            ]
        else: # Spring
            sub_tab_options = [
                "Individual Profile", 
                "Practice Scores", 
                "Daily Combined Scores", 
                "Practice History", 
                "Position Analysis", 
                "Match v. Practice", 
                "Match Summary", 
                "Practice Planner"
            ]

        selected_tab_label = st.sidebar.radio("Select View", sub_tab_options, key="sub_tab_navigation_radio")
        st.sidebar.info(f"Active: **{selected_season}** ➔ *{selected_tab_label}*")
        
        df_master = raw_df[raw_df['Season'] == selected_season].copy()
        match_master = raw_match_df[raw_match_df['Season'] == selected_season].copy()
        cmj_master = raw_cmj_df[raw_cmj_df['Season'] == selected_season].copy()
        ash_master = raw_ash_df[raw_ash_df['Season'] == selected_season].copy()
        er_master = raw_er_df[raw_er_df['Season'] == selected_season].copy()
        phase_master = raw_phase_df[raw_phase_df['Season'] == selected_season].copy()
        full_df_unfiltered = raw_df.copy()

        phase_map = {
            "Mini Games (Set 1)": "Mini Games", "Mini Games (Set 2)": "Mini Games", "Brizo (2)": "Brizo",
            "2 Ball (Set 1)": "2 Ball", "2 Ball (Set 2)": "2 Ball", "2 Ball (Set 3)": "2 Ball", "2 Ball (Set 4)": "2 Ball",
            "serving (2)": "Serving", "serving": "Serving", "Serving (2)": "Serving", "2/3 Hitters (2)": "2/3 Hitters",
            "5v5 (2)": "5v5", "Serve & Pass": "Serve and Pass"
        }
        all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
        cmj_col = 'Jump Height (Imp-Mom) [cm]'
        rsi_col = 'RSI-modified [m/s]'

        master_athlete_list = sorted(list(set(df_master['Name'].unique()) | set(cmj_master['Name'].unique()) | set(ash_master['Name'].unique()) | set(er_master['Name'].unique())))
        session_list = df_master[df_master['Session_Name'].notna()].sort_values('Date', ascending=False)['Session_Name'].unique().tolist()

        st.markdown('<div class="main-logo-container" style="text-align: center; margin-top: 10px; margin-bottom: 15px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120"><div style="color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;">LADY VOLS VOLLEYBALL PERFORMANCE</div></div>', unsafe_allow_html=True)

        # ==========================================
        # --- TAB CLAUSE 0: INDIVIDUAL PROFILE -----
        # ==========================================
        if selected_tab_label == "Individual Profile":
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
                    if s_date == target_date_str:
                        if not tourney_added_prof:
                            clean_session_list_prof.append(tournament_label)
                            tourney_added_prof = True
                    else:
                        clean_session_list_prof.append(s)
                else:
                    clean_session_list_prof.append(s)
            
            if not clean_session_list_prof: clean_session_list_prof = [tournament_label]

            c_prof1, c_prof2 = st.columns(2)
            with c_prof1: selected_session_prof = st.selectbox("Session Selection", clean_session_list_prof, index=0, key="nav_sel_prof_t0")
            with c_prof2: selected_athlete_prof = st.selectbox("Athlete Selection", master_athlete_list, key="nav_ath_prof_t0")

            if selected_session_prof == tournament_label:
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
                curr_date_prof = pd.to_datetime(target_date_str) if selected_session_prof == tournament_label else pd.to_datetime(df_t0['Date'].max() if not df_t0.empty else "2026-01-01")
                meta_lookup = df_t0[df_t0['Name'] == selected_athlete_prof]
                pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"
                photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                p_meta = pd.Series({'Name': selected_athlete_prof, 'Position': pos_val, 'PhotoURL': photo_val})
                p_row = pd.Series({m: 0.0 for m in all_metrics})
                p_row['Name'] = selected_athlete_prof

            p_full_prof = df_t0[df_t0['Name'] == selected_athlete_prof]
            daily_sums_prof = p_full_prof.groupby('Date')[all_metrics].sum().reset_index()
            lb_prof = daily_sums_prof[(daily_sums_prof['Date'].dt.date >= curr_date_prof.date() - timedelta(days=30)) & (daily_sums_prof['Date'].dt.date <= curr_date_prof.date())]

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
            with c2: st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today Total</th><th>30d Max Day</th><th>Grade</th></tr></thead><tbody>{r_html_prof}</tbody></table>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(sc_prof)};">{sc_prof}</div></div><p style="text-align:center; font-weight:bold; color:grey; margin-top:10px;">SESSION SCORE</p>', unsafe_allow_html=True)
            
            st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
            st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">COUNTERMOVEMENT JUMP</h4>', unsafe_allow_html=True)
            
            jc1, jc2 = st.columns([1.5, 3.5])
            p_cmj_hist = cmj_t0[(cmj_t0['Name'] == selected_athlete_prof) & (cmj_t0['Test Date'] <= curr_date_prof)].sort_values('Test Date')

            with jc1:
                baseline_cmj = cmj_t0[(cmj_t0['Name'] == selected_athlete_prof) & (cmj_t0['Season'] == 'Summer')].head(1) if selected_season == 'Summer' else cmj_t0[(cmj_t0['Name'] == selected_athlete_prof) & (cmj_t0['Week'] == 4)]
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
                    baseline_ash = p_ash_all[(p_ash_all['Season'] == 'Summer') & (p_ash_all['Isometric Type'].str.contains('I', case=False, na=False))].head(1) if selected_season == 'Summer' else p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)].head(1)
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
                    baseline_er = p_er_hist[p_er_hist['Season'] == 'Summer'].head(1) if selected_season == 'Summer' else p_er_hist.head(1)
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
        elif selected_tab_label == "Practice Scores":
            df_t1 = df_master.copy()
            target_date_str = "2026-04-04"
            tournament_label = "GT Spring Tournament 4-4-26"
            
            clean_session_list = []
            tourney_added = False
            for s in session_list:
                s_date_series = df_t1[df_t1['Session_Name'] == s]['Date']
                if not s_date_series.empty:
                    s_date = pd.to_datetime(s_date_series.iloc[0]).strftime('%Y-%m-%d')
                    if s_date == target_date_str:
                        if not tourney_added:
                            clean_session_list.append(tournament_label)
                            tourney_added = True
                    else:
                        clean_session_list.append(s)
                else:
                    clean_session_list.append(s)

            c_gal1, c_gal2 = st.columns(2)
            with c_gal1: selected_session_gal = st.selectbox("Session Selection", clean_session_list, index=0, key="nav_sel_gal_t1")
            with c_gal2: pos_f_gal = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df_t1['Position'].unique() if p != "N/A"]), key="nav_pos_gal_t1")
            
            if selected_session_gal == tournament_label:
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
                            
                            daily_sums_g = p_full_g.groupby('Date')[all_metrics].sum().reset_index()
                            lb_sums = daily_sums_g[(daily_sums_g['Date'].dt.date >= curr_date_gal.date() - timedelta(days=30)) & (daily_sums_g['Date'].dt.date <= curr_date_gal.date())]
                            
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
        elif selected_tab_label == "Daily Combined Scores":
            df_t2 = df_master.copy()
            valid_dates_sorted = df_t2[df_t2['Date'].notna()].sort_values('Date', ascending=False)['Date'].dt.strftime('%Y-%m-%d').unique().tolist()
            
            target_date_str = "2026-04-04"
            tournament_label = "GT Spring Tournament 4-4-26"
            
            clean_date_list = []
            tourney_added_comb = False
            for d_str in valid_dates_sorted:
                if d_str == target_date_str:
                    if not tourney_added_comb:
                        clean_date_list.append(tournament_label)
                        tourney_added_comb = True
                else:
                    clean_date_list.append(d_str)

            c_comb1, c_comb2 = st.columns(2)
            with c_comb1: selected_date_comb = st.selectbox("Date Selection", clean_date_list, index=0, key="nav_sel_comb_t2")
            with c_comb2: pos_f_comb = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df_t2['Position'].unique() if p != "N/A"]), key="nav_pos_comb_t2")
            
            target_date_obj_comb = pd.to_datetime(target_date_str) if selected_date_comb == tournament_label else pd.to_datetime(selected_date_comb)
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
        # --- TAB CLAUSE 3: SPRING MAX VS COMBINED -
        # ==========================================
        elif selected_tab_label == "Spring Max v. Daily Combined":
            df_t3 = df_master.copy()
            valid_dates_sorted_sm = df_t3[df_t3['Date'].notna()].sort_values('Date', ascending=False)['Date'].dt.strftime('%Y-%m-%d').unique().tolist()
            
            target_date_str = "2026-04-04"
            tournament_label = "GT Spring Tournament 4-4-26"
            
            clean_date_list_sm = []
            tourney_added_sm = False
            for d_str in valid_dates_sorted_sm:
                if d_str == target_date_str:
                    if not tourney_added_sm:
                        clean_date_list_sm.append(tournament_label)
                        tourney_added_sm = True
                else:
                    clean_date_list_sm.append(d_str)

            if not clean_date_list_sm:
                st.warning("No recorded dates found for the currently active season.")
            else:
                c_sm1, c_sm2 = st.columns(2)
                with c_sm1: selected_date_sm = st.selectbox("Date Selection", clean_date_list_sm, index=0, key="nav_sel_sm_t3")
                with c_sm2: pos_f_sm = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df_t3['Position'].unique() if p != "N/A"]), key="nav_pos_sm_t3")
                
                target_date_obj_sm = pd.to_datetime(target_date_str) if selected_date_sm == tournament_label else pd.to_datetime(selected_date_sm)
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
        elif selected_tab_label == "Practice History":
            df_t4 = df_master.copy()
            st.markdown('<div class="section-header">Season History & Team Weekly Review</div>', unsafe_allow_html=True)
            sub_tabs = st.tabs(["Individual Review", "Team Weekly Review"])
            metrics_to_score = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]

            with sub_tabs[0]:
                sel_ath_hist = st.selectbox("Select Athlete", sorted(df_t4['Name'].unique()), key="master_ath_sel_t4")
                p_full = df_t4[df_t4['Name'] == sel_ath_hist].copy()
                p_full['Date'] = pd.to_datetime(p_full['Date'])
                daily_raw = p_full.groupby(['Date', 'Week']).agg({**{m: 'sum' for m in metrics_to_score}, 'Session_Name': lambda x: ' | '.join(x.astype(str)), 'Session_Type': lambda x: ' | '.join(x.astype(str))}).reset_index().sort_values('Date')
            
                scores_list = []
                for idx, row in daily_raw.iterrows():
                    row_grades = []
                    lb_sums = daily_raw[(daily_raw['Date'] >= row['Date'] - timedelta(days=30)) & (daily_raw['Date'] <= row['Date'])]
                    for m in metrics_to_score:
                        val = row[m]
                        mx = lb_sums[m].max()
                        row_grades.append(math.ceil((val / mx) * 100) if mx > 0 else 0)
                    is_match = any(w in str(row['Session_Name']).upper() or w in str(row['Session_Type']).upper() for w in ['MATCH', 'GAME'])
                    scores_list.append({'Date': row['Date'], 'Display': row['Date'].strftime('%m/%d'), 'Score': int(math.ceil(sum(row_grades) / len(row_grades))), 'Type': 'Match' if is_match else 'Practice', 'Week': str(row['Week'])})
            
                master_df_history = pd.DataFrame(scores_list).reset_index(drop=True)
                st.markdown(f"### Full Season Performance: {sel_ath_hist}")
                if not master_df_history.empty:
                    fig_master = px.line(master_df_history, x='Display', y='Score', range_y=[0, 110])
                    prac_df = master_df_history[master_df_history['Type'] == 'Practice']
                    if not prac_df.empty: fig_master.add_trace(go.Scatter(x=prac_df['Display'], y=prac_df['Score'], mode='markers+text', text=prac_df['Score'], textposition="top center", name="Practice", marker=dict(size=8, color='#4895DB', line=dict(width=1, color='white'))))
                    match_df_line = master_df_history[master_df_history['Type'] == 'Match']
                    if not match_df_line.empty: fig_master.add_trace(go.Scatter(x=match_df_line['Display'], y=match_df_line['Score'], mode='markers+text', text=[f"<b>{s}</b>" for s in match_df_line['Score']], textposition="top center", name="Match Day", marker=dict(size=15, color='#FF8200', line=dict(width=3, color='#31333F')), textfont=dict(color='#31333F', size=13, weight='bold')))
                    for i in range(1, len(master_df_history)):
                        if master_df_history.iloc[i]['Week'] != master_df_history.iloc[i-1]['Week']:
                            fig_master.add_vline(x=i-0.5, line_dash="dash", line_color="#515154", opacity=0.3)
                            fig_master.add_annotation(x=i-0.5, y=0.98, yref="paper", text=f"Wk {master_df_history.iloc[i]['Week']}", showarrow=False, bgcolor="white", font=dict(size=10, color="#515154"), yanchor="top")
                    fig_master.update_layout(template="simple_white", height=480, xaxis=dict(type='category', title="Date"), yaxis=dict(range=[0, 120], automargin=True, tickvals=[0, 20, 40, 60, 80, 100]), legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center"))
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
                st.info("Team Weekly Review view initialized.")

        # ==========================================
        # --- POSITION ANALYSIS / PLACEHOLDERS ----
        # ==========================================
        elif selected_tab_label == "Position Analysis":
            st.markdown('<div class="section-header">Position Analysis</div>', unsafe_allow_html=True)
            st.info("Position analysis dashboard section context placeholder.")

        elif selected_tab_label == "Spring v. Summer":
            st.markdown('<div class="section-header">Spring v. Summer Comparison Dashboard</div>', unsafe_allow_html=True)
            st.info("Cross-seasonal comparison engine context placeholder.")

        elif selected_tab_label == "Match v. Practice":
            st.markdown('<div class="section-header">Match v. Practice Comparison</div>', unsafe_allow_html=True)
            st.info("Match vs. Practice analytics context placeholder.")

        elif selected_tab_label == "Match Summary":
            st.markdown('<div class="section-header">Match Summary Dashboard</div>', unsafe_allow_html=True)
            st.info("Match summary analytics context placeholder.")

        elif selected_tab_label == "Practice Planner":
            st.markdown('<div class="section-header">Practice Planner Tool</div>', unsafe_allow_html=True)
            st.info("Practice planner matrix view context placeholder.")

    except Exception as e:
        st.error(f"Application Execution Error: {e}")
