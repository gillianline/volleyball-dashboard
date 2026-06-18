import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

st.markdown("""
    <style>
    /* Center table text and style metrics */
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
    </style>
    """, unsafe_allow_html=True)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")


# --- PASSWORD PROTECTION ---
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

if check_password():
    if "is_printing" not in st.session_state:
        st.session_state.is_printing = False

    # --- CSS: FORMATTING & PAGE BREAK CONTROLS ---
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; color: #1D1D1F; }
        hr { display: none !important; }
        .block-container { padding-top: 2rem !important; }
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
    
    def get_flipped_gradient(score):
        try:
            score = float(score)
            if pd.isna(score): return "#808080" 
        except (ValueError, TypeError):
            return "#808080" 
        return "#2D5A27" if score <= 40 else "#D4A017" if score <= 70 else "#A52A2A"

        
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

        # Load GPS Data
        df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
        match_df = pd.read_csv(st.secrets["MATCHES_SHEET_URL"])
        
        for frame in [df, match_df]:
            frame = heavy_sanitize(frame)
            frame['Sheet_Order'] = range(len(frame))
            frame['Date'] = pd.to_datetime(frame['Date'], errors='coerce')
            if 'Week' in frame.columns:
                frame['Week'] = pd.to_numeric(frame['Week'].astype(str).str.extract('(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
            frame['Session_Name'] = frame['Activity'].fillna(frame['Date'].dt.strftime('%m/%d/%Y'))
            frame['Position'] = frame.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
            frame['PhotoURL'] = frame.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
            frame['Session_Type'] = frame['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
            frame['Season'] = frame['Date'].apply(assign_season)

        # 1. Process CMJ Lower Body Sheet
        cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
        cmj_df.columns = cmj_df.columns.str.strip()
        cmj_df.rename(columns={'Athlete': 'Name'}, inplace=True)
        cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
        cmj_df['Season'] = cmj_df['Test Date'].apply(assign_season)

        # 2. Process ASH Upper Body Sheet
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

        # 3. Process External Rotation Range of Motion Sheet
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

        # Process Drill Phases
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

    LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

    try:
        df, match_df, cmj_df, phase_df, thresh_df, ash_df, er_df = load_all_data()

        # --- GLOBAL SEASON FILTER SIDEBAR CONFIG ---
        st.sidebar.markdown("### Season")
        selected_season = st.sidebar.radio("Select Season", ["Spring", "Summer"], index=1, key="global_season_toggle")
        
        df = df[df['Season'] == selected_season].copy()
        match_df = match_df[match_df['Season'] == selected_season].copy()
        cmj_df = cmj_df[cmj_df['Season'] == selected_season].copy()
        ash_df = ash_df[ash_df['Season'] == selected_season].copy()
        er_df = er_df[er_df['Season'] == selected_season].copy()
        phase_df = phase_df[phase_df['Season'] == selected_season].copy()
        
        st.sidebar.info(f"Currently displaying: {selected_season} Season Performance Data.")

        phase_map = {
            "Mini Games (Set 1)": "Mini Games", "Mini Games (Set 2)": "Mini Games", "Brizo (2)": "Brizo",
            "2 Ball (Set 1)": "2 Ball", "2 Ball (Set 2)": "2 Ball", "2 Ball (Set 3)": "2 Ball", "2 Ball (Set 4)": "2 Ball",
            "serving (2)": "Serving", "serving": "Serving", "Serving (2)": "Serving", "2/3 Hitters (2)": "2/3 Hitters",
            "5v5 (2)": "5v5", "Serve & Pass": "Serve and Pass"
        }
        
        all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
        st.markdown('<div class="main-logo-container" style="text-align: center; margin-top: 10px; margin-bottom: 15px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120"><div style="color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;">LADY VOLS VOLLEYBALL PERFORMANCE</div></div>', unsafe_allow_html=True)

        tabs = st.tabs(["Individual Profile", "Practice Scores", "Practice History", "Match v. Practice", "Match Summary", "Position Analysis", "Phase Analysis", "Practice Planner"])
        session_list = df[df['Session_Name'].notna()].sort_values('Date', ascending=False)['Session_Name'].unique().tolist()

        with tabs[0]: # Tab 0: Individual Profile
            target_date_str = "2026-04-04"
            tournament_label = "GT Spring Tournament 4-4-26"
            
            clean_session_list_prof = []
            tourney_added_prof = False
            for s in session_list:
                s_date = df[df['Session_Name'] == s]['Date'].dt.strftime('%Y-%m-%d').iloc[0]
                if s_date == target_date_str:
                    if not tourney_added_prof:
                        clean_session_list_prof.append(tournament_label)
                        tourney_added_prof = True
                else:
                    clean_session_list_prof.append(s)

            c_prof1, c_prof2 = st.columns(2)
            with c_prof1: selected_session_prof = st.selectbox("Session Selection", clean_session_list_prof, index=0, key="nav_sel_prof")
            with c_prof2: selected_athlete_prof = st.selectbox("Athlete Selection", sorted(df['Name'].unique()), key="nav_ath_prof")

            if selected_session_prof == tournament_label:
                curr_date_prof = pd.to_datetime(target_date_str)
                p_session_data = df[(df['Name'] == selected_athlete_prof) & (df['Date'] == curr_date_prof)].copy()
                p_row = p_session_data.groupby(['Name', 'Position', 'PhotoURL', 'Date']).sum(numeric_only=True).reset_index().iloc[0] if not p_session_data.empty else pd.Series()
                p_meta = p_session_data.iloc[0] if not p_session_data.empty else pd.Series()
            else:
                p_session_data = df[(df['Name'] == selected_athlete_prof) & (df['Session_Name'] == selected_session_prof)]
                p_row = p_session_data.iloc[0] if not p_session_data.empty else pd.Series()
                curr_date_prof = p_row['Date'] if not p_row.empty else None
                p_meta = p_row

            if not p_row.empty:
                p_full_prof = df[df['Name'] == selected_athlete_prof]
                daily_sums_prof = p_full_prof.groupby('Date')[all_metrics].sum().reset_index()
                lb_prof = daily_sums_prof[(daily_sums_prof['Date'] >= pd.to_datetime(curr_date_prof) - timedelta(days=30)) & (daily_sums_prof['Date'] <= pd.to_datetime(curr_date_prof))]

                filtered_metrics_prof = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]
                r_html_prof = ""; t_grade_prof = 0; c_metrics_prof = 0

                for k in filtered_metrics_prof:
                    val = p_row[k]
                    mx = lb_prof[k].max() if not lb_prof[k].empty else 1
                    avg = lb_prof[k].mean() if not lb_prof[k].empty else 1
                    g = math.ceil((val / mx) * 100) if mx > 0 else 0
                    t_grade_prof += g; c_metrics_prof += 1
                    diff = (val - avg) / avg if avg != 0 else 0
                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                    arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                    r_html_prof += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"

                sc_prof = math.ceil(t_grade_prof / c_metrics_prof) if c_metrics_prof > 0 else 0

                c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
                with c1: st.markdown(f'<div style="text-align:center;"><img src="{p_meta["PhotoURL"]}" class="player-photo-large"></div><h3 style="text-align:center;">{p_meta["Name"]}</h3>', unsafe_allow_html=True)
                with c2: st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today Total</th><th>30d Max Day</th><th>Grade</th></tr></thead><tbody>{r_html_prof}</tbody></table>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(sc_prof)};">{sc_prof}</div></div><p style="text-align:center; font-weight:bold; color:grey; margin-top:10px;">SESSION SCORE</p>', unsafe_allow_html=True)
                
                # =========================================================================
                # --- WEEKLY READINESS PROFILE MATRICES STACK ---
                # =========================================================================
                st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
                
                # --- BLOCK 1: LOWER BODY JUMP PROFILE (CMJ) ---
                st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">LOWER BODY: COUNTERMOVEMENT JUMP</h4>', unsafe_allow_html=True)
                jc1, jc2 = st.columns([1.5, 3.5])
                p_cmj_hist = cmj_df[(cmj_df['Name'] == selected_athlete_prof) & (cmj_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
                cmj_col = 'Jump Height (Imp-Mom) [cm]'
                rsi_col = 'RSI-modified [m/s]'

                with jc1:
                    if selected_season == 'Summer':
                        baseline_cmj = p_cmj_hist[p_cmj_hist['Season'] == 'Summer'].head(1)
                    else:
                        baseline_cmj = cmj_df[(cmj_df['Name'] == selected_athlete_prof) & (cmj_df['Week'] == 4)]
                    
                    if not baseline_cmj.empty and not p_cmj_hist.empty:
                        base_h = baseline_cmj.iloc[-1][cmj_col]
                        base_rsi = baseline_cmj.iloc[-1][rsi_col]
                        latest_cmj = p_cmj_hist.iloc[-1]
                        cur_h, cur_rsi = latest_cmj[cmj_col], latest_cmj[rsi_col]
                        p_diff = ((cur_h - base_h) / base_h) * 100 if base_h > 0 else 0
                        label, color = (" ", "#28a745") if cur_h >= base_h and cur_rsi >= base_rsi else (" ", "#dc3545") if cur_h < base_h and cur_rsi < base_rsi else (" ", "#ffc107")

                        st.markdown(f"""
                            <div style="text-align:center;">
                                <div class="score-box" style="background-color:{color}; line-height:1.2; padding-top:15px; height:80px; width:100%;">
                                    <span style="font-size:18px;">{p_diff:+.1f}%</span>
                                    <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">{label}</span>
                                </div>
                            </div>
                            <div class="info-box" style="text-align:center; margin-top:10px;">
                                <p style="margin:0; font-size:13px; color:#FF8200;"><b>CMJ:</b> {cur_h:.1f} cm (Base: {base_h:.1f})</p>
                            </div>
                        """, unsafe_allow_html=True)
                with jc2:
                    if not p_cmj_hist.empty:
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[cmj_col], name="Height", line=dict(color='#FF8200', width=3)), secondary_y=False)
                        fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[rsi_col], name="RSI", line=dict(color='#4895DB', dash='dot')), secondary_y=True)
                        fig.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, template="simple_white")
                        st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG, key="cmj_top_chart")

                # --- BLOCK 2: UPPER BODY ISOMETRIC PROFILE (ASH TEST) ---
                st.markdown('<hr style="display:block !important; margin:15px 0; border:0; border-top:1px solid #E5E5E7;" />', unsafe_allow_html=True)
                st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">UPPER BODY: ASH SHOULDER ISOMETRIC</h4>', unsafe_allow_html=True)
                
                p_ash_all = ash_df[(ash_df['Name'] == selected_athlete_prof) & (ash_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
                
                if not p_ash_all.empty:
                    ac1, ac2 = st.columns([1.5, 3.5])
                    with ac1:
                        latest_date_ash = p_ash_all['Test Date'].iloc[-1]
                        today_ash_rows = p_ash_all[p_ash_all['Test Date'] == latest_date_ash]
                        
                        row_i = today_ash_rows[today_ash_rows['Isometric Type'].str.contains('I', case=False, na=False)]
                        
                        li = row_i.iloc[-1]['Peak Vertical Force [N] (L)'] if not row_i.empty else 0.0
                        ri = row_i.iloc[-1]['Peak Vertical Force [N] (R)'] if not row_i.empty else 0.0
                        asym_i = row_i.iloc[-1]['Peak Vertical Force [N] (Asym)(%)'] if not row_i.empty else 0.0
                        
                        if selected_season == 'Summer':
                            baseline_ash = p_ash_all[(p_ash_all['Season'] == 'Summer') & (p_ash_all['Isometric Type'].str.contains('I', case=False, na=False))].head(1)
                        else:
                            baseline_ash = p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)].head(1)
                        
                        base_li = baseline_ash.iloc[-1]['Peak Vertical Force [N] (L)'] if not baseline_ash.empty else 0.0
                        base_ri = baseline_ash.iloc[-1]['Peak Vertical Force [N] (R)'] if not baseline_ash.empty else 0.0
                        
                        pct_l = ((li - base_li) / base_li * 100) if base_li > 0 else 0
                        pct_r = ((ri - base_ri) / base_ri * 100) if base_ri > 0 else 0
                        ash_avg_diff = (pct_l + pct_r) / 2
                        
                        label_ash, color_ash = (" ", "#28a745") if ash_avg_diff >= 0 and abs(asym_i) <= 10 else (" ", "#dc3545") if ash_avg_diff < -8 else (" ", "#ffc107")

                        st.markdown(f"""
                            <div style="text-align:center;">
                                <div class="score-box" style="background-color:{color_ash}; line-height:1.2; padding-top:15px; height:80px; width:100%;">
                                    <span style="font-size:18px;">{ash_avg_diff:+.1f}%</span>
                                    <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">{label_ash} (Asym: {asym_i:+.1f}%)</span>
                                </div>
                            </div>
                            <div class="info-box" style="text-align:center; margin-top:10px;">
                                <p style="margin:0; font-size:11px; color:grey;"><b>Base Force:</b> L: {base_li:.0f} N | R: {base_ri:.0f} N</p>
                                <p style="margin:0; font-size:13px; color:#FF8200;"><b>Today Force:</b> L: {li:.0f} N | R: {ri:.0f} N</p>
                            </div>
                        """, unsafe_allow_html=True)
                    with ac2:
                        p_ash_i_only = p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)]
                        if not p_ash_i_only.empty:
                            fig_ash = go.Figure()
                            fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (L)'], name="Left I Force", line=dict(color='#4895DB', width=2.5)))
                            fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (R)'], name="Right I Force", line=dict(color='#FF8200', width=2.5, dash='dash')))
                            fig_ash.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, template="simple_white")
                            st.plotly_chart(fig_ash, use_container_width=True, config=LOCKED_CONFIG, key="ash_profile_chart")
                else:
                    st.info("No explicit ASH shoulder test dataset records parsed for this athlete.")

                # --- BLOCK 3: ROTATOR CUFF EXTERNAL ROTATION ROM ---
                st.markdown('<hr style="display:block !important; margin:15px 0; border:0; border-top:1px solid #E5E5E7;" />', unsafe_allow_html=True)
                st.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">EXTERNAL ROTATION: ROM</h4>', unsafe_allow_html=True)
                
                p_er_hist = er_df[(er_df['Name'] == selected_athlete_prof) & (er_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
                
                if not p_er_hist.empty:
                    ec1, ec2 = st.columns([1.5, 3.5])
                    with ec1:
                        if selected_season == 'Summer':
                            baseline_er = p_er_hist[p_er_hist['Season'] == 'Summer'].head(1)
                        else:
                            baseline_er = p_er_hist.head(1)
                            
                        if not baseline_er.empty:
                            base_l_rom = baseline_er.iloc[-1]['L Max ROM (°)']
                            base_r_rom = baseline_er.iloc[-1]['R Max ROM (°)']
                            
                            latest_er = p_er_hist.iloc[-1]
                            cur_l_rom = latest_er['L Max ROM (°)']
                            cur_r_rom = latest_er['R Max ROM (°)']
                            cur_asym_rom = latest_er['ROM Asymmetry (%)']
                            
                            rom_pct_l = ((cur_l_rom - base_l_rom) / base_l_rom * 100) if base_l_rom > 0 else 0
                            rom_pct_r = ((cur_r_rom - base_r_rom) / base_r_rom * 100) if base_r_rom > 0 else 0
                            er_avg_diff = (rom_pct_l + rom_pct_r) / 2
                            
                            label_er, color_er = (" ", "#28a745") if er_avg_diff >= 0 and abs(cur_asym_rom) <= 10 else (" ", "#dc3545") if er_avg_diff < -6 else (" ", "#ffc107")
                            
                            st.markdown(f"""
                                <div style="text-align:center;">
                                    <div class="score-box" style="background-color:{color_er}; line-height:1.2; padding-top:15px; height:80px; width:100%;">
                                        <span style="font-size:18px;">{cur_asym_rom:+.1f}%</span>
                                        <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">{label_er} (Asym ROM)</span>
                                    </div>
                                </div>
                                <div class="info-box" style="text-align:center; margin-top:10px;">
                                    <p style="margin:0; font-size:11px; color:grey;"><b>Base ROM:</b> L: {base_l_rom:.1f}° | R: {base_r_rom:.1f}°</p>
                                    <p style="margin:0; font-size:13px; color:#FF8200;"><b>Today ROM:</b> L: {cur_l_rom:.1f}° | R: {cur_r_rom:.1f}°</p>
                                </div>
                            """, unsafe_allow_html=True)
                    with ec2:
                        fig_er = go.Figure()
                        fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['L Max ROM (°)'], name="Left ROM", line=dict(color='#4895DB', width=2.5)))
                        fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['R Max ROM (°)'], name="Right ROM", line=dict(color='#FF8200', width=2.5, dash='dash')))
                        fig_er.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, template="simple_white")
                        st.plotly_chart(fig_er, use_container_width=True, config=LOCKED_CONFIG, key="er_profile_chart")
                else:
                    st.info("External Rotation logs recorded for this athlete profile.")

                st.divider()

                # --- PRACTICE PHASE BREAKDOWN ---
                p_ph = phase_df[(phase_df['Name'] == selected_athlete_prof) & (phase_df['Date'] == curr_date_prof)].copy()
                if not p_ph.empty:
                    st.markdown('<div class="section-header">Practice Phase Analysis</div>', unsafe_allow_html=True)
                    fig_ph = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_ph.add_trace(go.Bar(x=p_ph['Phase'], y=p_ph['Player Load'], name="Player Load", marker_color='#4895DB'), secondary_y=False)
                    fig_ph.add_trace(go.Scatter(x=p_ph['Phase'], y=p_ph['Total Jumps'], name="Total Jumps", line=dict(color='#FF8200', width=4), mode='lines+markers'), secondary_y=True)
                    fig_ph.update_layout(height=350, showlegend=True, template="simple_white", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=0, r=0, t=30, b=0))
                    fig_ph.update_yaxes(title_text="Player Load", secondary_y=False)
                    fig_ph.update_yaxes(title_text="Total Jumps", secondary_y=True)
                    st.plotly_chart(fig_ph, use_container_width=True, config=LOCKED_CONFIG)
                    
        with tabs[1]: # Tab 1: Leaderboard Gallery
            c_gal1, c_gal2 = st.columns(2)
            with c_gal1: selected_session_gal = st.selectbox("Session Selection", clean_session_list_prof, index=0, key="nav_sel_gal")
            with c_gal2: pos_f_gal = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_gal")
            
            display_df = df[df['Session_Name'] == selected_session_gal].copy() if selected_session_gal != tournament_label else df[df['Date'] == pd.to_datetime(target_date_str)].groupby(['Name', 'Position', 'PhotoURL']).sum(numeric_only=True).reset_index()
            curr_date_gal = pd.to_datetime(target_date_str) if selected_session_gal == tournament_label else (display_df['Date'].iloc[0] if not display_df.empty else None)

            if not display_df.empty:
                if pos_f_gal != "All Positions": display_df = display_df[display_df['Position'] == pos_f_gal]
                athlete_names = sorted(display_df['Name'].unique())
                filtered_metrics_gal = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]

                for i in range(0, len(athlete_names), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(athlete_names):
                            name = athlete_names[i + j]
                            p_session_row = display_df[display_df['Name'] == name].iloc[0]
                            daily_sums_g = df[df['Name'] == name].groupby('Date')[all_metrics].sum().reset_index()
                            lb_sums = daily_sums_g[(daily_sums_g['Date'] >= curr_date_gal - timedelta(days=30)) & (daily_sums_g['Date'] <= curr_date_gal)]
                            
                            r_html = ""; t_grade = 0; c_metrics = 0
                            for k in filtered_metrics_gal:
                                val = p_session_row[k]
                                mx = lb_sums[k].max() if not lb_sums[k].empty else 1
                                avg = lb_sums[k].mean() if not lb_sums[k].empty else 1
                                g = math.ceil((val / mx) * 100) if mx > 0 else 0
                                t_grade += g; c_metrics += 1
                                diff = (val - avg) / avg if avg != 0 else 0
                                h_class = "class='bg-highlight-red'" if abs(diff) > 0.15 else ""
                                arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.15 else '↓'}</span>" if abs(diff) > 0.15 else ""
                                r_html += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"
                            
                            sc_g = math.ceil(t_grade / c_metrics) if c_metrics > 0 else 0
                            with cols[j]: 
                                st.markdown(f"""
                                    <div style="border:1px solid #E5E5E7; border-radius:15px; padding:15px; margin-bottom:20px; background-color:white;">
                                        <div style="display:flex; align-items:center; gap:10px;">
                                            <div style="flex:1.2; text-align:center;">
                                                <img src="{p_session_row["PhotoURL"]}" class="gallery-photo">
                                                <p style="font-weight:bold; font-size:15px; margin-top:8px; color:#333;">{name}</p>
                                            </div>
                                            <div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Total</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div>
                                            <div style="flex:1; text-align:center;"><div style="background-color:{get_flipped_gradient(sc_g)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{sc_g}</div></div>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)

        with tabs[2]: # Tab 2: Performance History Review
            st.markdown('<div class="section-header">Season History & Team Weekly Review</div>', unsafe_allow_html=True)
            sub_tabs = st.tabs(["Individual Review", "Team Weekly Review"])
            metrics_to_score = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]

            with sub_tabs[0]:
                sel_ath_hist = st.selectbox("Select Athlete", sorted(df['Name'].unique()), key="master_ath_sel")
                p_full = df[df['Name'] == sel_ath_hist].copy()
                daily_raw = p_full.groupby(['Date', 'Week']).agg({**{m: 'sum' for m in metrics_to_score}, 'Session_Name': lambda x: ' | '.join(x.astype(str)), 'Session_Type': lambda x: ' | '.join(x.astype(str))}).reset_index().sort_values('Date')
                
                scores_list = []
                for idx, row in daily_raw.iterrows():
                    row_grades = []
                    lb_sums = daily_raw[(daily_raw['Date'] >= row['Date'] - timedelta(days=30)) & (daily_raw['Date'] <= row['Date'])]
                    for m in metrics_to_score:
                        mx = lb_sums[m].max() if not lb_sums[m].empty else 1
                        row_grades.append(math.ceil((row[m] / mx) * 100) if mx > 0 else 0)
                    is_match = any(w in str(row['Session_Name']).upper() or w in str(row['Session_Type']).upper() for w in ['MATCH', 'GAME'])
                    scores_list.append({'Date': row['Date'], 'Display': row['Date'].strftime('%m/%d'), 'Score': math.ceil(sum(row_grades)/len(row_grades)), 'Type': 'Match' if is_match else 'Practice', 'Week': str(row['Week'])})
                
                master_df = pd.DataFrame(scores_list)
                if not master_df.empty:
                    fig_master = px.line(master_df, x='Display', y='Score', range_y=[0, 110])
                    prac_df = master_df[master_df['Type'] == 'Practice']
                    if not prac_df.empty: fig_master.add_trace(go.Scatter(x=prac_df['Display'], y=prac_df['Score'], mode='markers+text', text=prac_df['Score'], textposition="top center", name="Practice", marker=dict(size=8, color='#4895DB')))
                    match_df_line = master_df[master_df['Type'] == 'Match']
                    if not match_df_line.empty: fig_master.add_trace(go.Scatter(x=match_df_line['Display'], y=match_df_line['Score'], mode='markers+text', text=[f"<b>{s}</b>" for s in match_df_line['Score']], textposition="top center", name="Match Day", marker=dict(size=15, color='#FF8200')))
                    fig_master.update_layout(template="simple_white", height=380, legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"))
                    st.plotly_chart(fig_master, use_container_width=True)

                # --- MULTI-SHEET TIMELINE ALIGNMENT FOR HISTORICAL READINESS ---
                st.markdown("### Combined Lower & Upper Body Kinetics History")
                ath_cmj = cmj_df[cmj_df['Name'] == sel_ath_hist].sort_values('Test Date')
                ath_ash = ash_df[ash_df['Name'] == sel_ath_hist].sort_values('Test Date')
                ath_er = er_df[er_df['Name'] == sel_ath_hist].sort_values('Test Date')

                if selected_season == 'Summer':
                    baseline_cmj = ath_cmj[ath_cmj['Season'] == 'Summer'].head(1)
                else:
                    baseline_cmj = cmj_df[(cmj_df['Name'] == sel_ath_hist) & (cmj_df['Week'] == 4)]

                if not baseline_cmj.empty:
                    base_row = baseline_cmj.iloc[-1]
                    all_testing_dates = pd.Index(set(ath_cmj['Test Date'].dropna()) | set(ath_ash['Test Date'].dropna()) | set(ath_er['Test Date'].dropna())).sort_values()

                    comparison_list = []
                    for t_date in all_testing_dates:
                        cmj_day = ath_cmj[ath_cmj['Test Date'] == t_date]
                        ash_day = ath_ash[ash_df['Test Date'] == t_date]
                        er_day = ath_er[er_df['Test Date'] == t_date]

                        h_val = cmj_day.iloc[-1][cmj_col] if not cmj_day.empty else None
                        rsi_val = cmj_day.iloc[-1][rsi_col] if not cmj_day.empty else None
                        
                        ash_i_filter = ash_day[ash_day['Isometric Type'].str.contains('I', case=False, na=False)]
                        li_val = ash_i_filter.iloc[-1]['Peak Vertical Force [N] (L)'] if not ash_i_filter.empty else None
                        ri_val = ash_i_filter.iloc[-1]['Peak Vertical Force [N] (R)'] if not ash_i_filter.empty else None
                        asym_val = ash_i_filter.iloc[-1]['Peak Vertical Force [N] (Asym)(%)'] if not ash_i_filter.empty else None
                        
                        er_l_val = er_day.iloc[-1]['L Max ROM (°)'] if not er_day.empty else None
                        er_r_val = er_day.iloc[-1]['R Max ROM (°)'] if not er_day.empty else None
                        er_asym_val = er_day.iloc[-1]['ROM Asymmetry (%)'] if not er_day.empty else None

                        raw_diff = (h_val - base_row[cmj_col]) if h_val else 0.0
                        display_diff = f"{raw_diff:+.1f} cm" if h_val else "N/A"

                        comparison_list.append({
                            "Date": t_date.strftime('%m/%d/%Y'),
                            "Height": f"{h_val:.1f} cm" if h_val else "N/A",
                            "Raw Diff": raw_diff,
                            "Display Diff": display_diff,
                            "RSI": f"{rsi_val:.2f}" if rsi_val else "N/A",
                            "ASH_F": f"L: {li_val:.0f} / R: {ri_val:.0f}" if li_val and ri_val else "N/A",
                            "ASH_ASYM": f"{asym_val:+.1f}%" if asym_val else "N/A",
                            "ER_ROM": f"L: {er_l_val:.1f}° / R: {er_r_val:.1f}°" if er_l_val and er_r_val else "N/A",
                            "ER_ASYM": f"{er_asym_val:+.1f}%" if er_asym_val else "N/A"
                        })

                    cmj_table_html = """<table class="scout-table">
                                        <thead><tr style="background-color: #f0f2f6; font-weight: bold;">
                                            <th>Test Date</th><th>Jump Height</th><th>Vs. Baseline</th><th>RSI-mod</th>
                                            <th>ASH Forces (I)</th><th>ASH Asym %</th><th>ER Max ROM</th><th>ER Asym %</th>
                                        </tr></thead><tbody>"""
                    for item in comparison_list:
                        color = "#28a745" if item['Raw Diff'] >= 0 else "#dc3545"
                        if item['Height'] == "N/A": color = "#1D1D1F"
                        cmj_table_html += f"""<tr>
                            <td>{item['Date']}</td><td>{item['Height']}</td>
                            <td style="font-weight: bold; color: {color};">{item['Display Diff']}</td><td>{item['RSI']}</td>
                            <td style="font-weight:700;">{item['ASH_F']}</td><td style="font-weight:700;">{item['ASH_ASYM']}</td>
                            <td style="font-weight:700;">{item['ER_ROM']}</td><td style="font-weight:700;">{item['ER_ASYM']}</td>
                        </tr>"""
                    st.markdown(cmj_table_html + "</tbody></table>", unsafe_allow_html=True)

                    # Kinetics & ROM Joint Coordinated Plot
                    fig_cmj = make_subplots(specs=[[{"secondary_y": True}]])
                    if not ath_cmj.empty:
                        fig_cmj.add_trace(go.Scatter(x=ath_cmj['Test Date'], y=ath_cmj[cmj_col], name="Jump Height (cm)", mode='lines+markers', line=dict(color='#4895DB', width=3)), secondary_y=False)
                    if not ath_ash.empty:
                        ash_i_plot = ath_ash[ath_ash['Isometric Type'].str.contains('I', case=False, na=False)]
                        if not ash_i_plot.empty:
                            fig_cmj.add_trace(go.Scatter(x=ash_i_plot['Test Date'], y=ash_i_plot['Peak Vertical Force [N] (L)'], name="ASH Left Force (N)", mode='lines+markers', line=dict(color='#FF8200', width=2)), secondary_y=False)
                    if not ath_er.empty:
                        fig_cmj.add_trace(go.Scatter(x=ath_er['Test Date'], y=ath_er['L Max ROM (°)'], name="ER Left ROM (°)", mode='lines+markers', line=dict(color='#A52A2A', width=2)), secondary_y=True)
                    
                    fig_cmj.add_hline(y=base_row[cmj_col], line_dash="dash", line_color="red")
                    fig_cmj.update_layout(height=380, template="simple_white", legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"))
                    st.plotly_chart(fig_cmj, use_container_width=True)

            with sub_tabs[1]:
                avail_weeks = sorted(df['Week'].unique(), reverse=True)
                if avail_weeks:
                    sel_week = st.selectbox("Select Review Week", avail_weeks, key="team_week_sel")
                    week_df = df[df['Week'] == sel_week].copy()
                    ath_names = sorted(week_df['Name'].unique())
                    for i in range(0, len(ath_names), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(ath_names):
                                name = ath_names[i+j]
                                st.write(f"**{name}** Processed")

        with tabs[3]: # Tab 3: Match v Practice
            st.markdown('<div class="section-header">Season Preparation Intensity vs Match Density</div>', unsafe_allow_html=True)
            c_mode, c_sel = st.columns([1, 3])
            with c_mode: view_mode = st.radio("View Level Context", ["Team", "Position", "Individual"], horizontal=True, key="gp_view_mode_t3")
            
            if view_mode == "Individual":
                gp_p = st.selectbox("Select Athlete Profile", sorted(df['Name'].unique()), key="gp_p_vf_t3")
                main_filtered = df[df['Name'] == gp_p].copy()
                match_filtered = match_df[match_df['Name'] == gp_p].copy()
            elif view_mode == "Position":
                gp_pos = st.selectbox("Select Position Group Context", sorted(df['Position'].unique().tolist()), key="gp_pos_vf_t3")
                main_filtered = df[df['Position'] == gp_pos].copy()
                match_filtered = match_df[match_df['Position'] == gp_pos].copy()
            else:
                main_filtered = df.copy()
                match_filtered = match_df.copy()

            if not main_filtered.empty and not match_filtered.empty:
                s_prac_all = main_filtered[main_filtered['Session_Type'] == 'Practice']
                s_p_avg = s_prac_all[['Player Load', 'Jump Load', 'Total Jumps', 'Explosive Efforts', 'Duration']].mean()
                s_m_avg = match_filtered[['Player Load', 'Jump Load', 'Total Jumps', 'Explosive Efforts', 'Duration']].mean()
                
                tab3_html = """<table class="scout-table"><thead><tr><th>Metric (Rate/Min)</th><th>Practice Average Density</th><th>Match Load Density</th><th>Intensity Gap</th></tr></thead><tbody>"""
                for m in ['Player Load', 'Jump Load', 'Total Jumps', 'Explosive Efforts']:
                    p_rate = s_p_avg[m] / s_p_avg['Duration'] if s_p_avg['Duration'] > 0 else 0
                    m_rate = s_m_avg[m] / s_m_avg['Duration'] if s_m_avg['Duration'] > 0 else 0
                    gap = ((m_rate - p_rate) / p_rate * 100) if p_rate > 0 else 0
                    tab3_html += f"<tr><td><b>{m}</b></td><td>{p_rate:.2f}</td><td>{m_rate:.2f}</td><td style='font-weight:bold;'>{gap:+.1f}%</td></tr>"
                st.markdown(tab3_html + "</tbody></table>", unsafe_allow_html=True)

        with tabs[4]: # Tab 4: Match Summary Cards
            selected_matches = st.multiselect("Select Matches to Analyze", match_df.sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique().tolist(), key="matches_t4")
            if selected_matches:
                tourney_df = match_df[match_df['Session_Name'].isin(selected_matches)].sort_values(['Date', 'Sheet_Order'])
                for name in sorted(tourney_df['Name'].unique()):
                    ad = tourney_df[tourney_df['Name'] == name]
                    st.markdown(f"#### Match Summary Profile: {name}")
                    st.dataframe(ad[['Session_Name', 'Total Jumps', 'Player Load', 'Explosive Efforts']], use_container_width=True, hide_index=True)

        with tabs[5]: # Tab 5: Position Trends Matrix
            st.markdown('<div class="section-header">Positional Performance Tracking Over Time</div>', unsafe_allow_html=True)
            pos_filter_an = st.selectbox("Select Position Group to Monitor", sorted([p for p in df['Position'].unique() if p != "N/A"]), key="pos_an_filt_t5")
            tr_df = df[df['Position'] == pos_filter_an]
            if not tr_df.empty:
                pos_sums = tr_df.groupby(['Week', 'Name'])[['Player Load', 'Total Jumps']].sum().reset_index()
                st.dataframe(pos_sums, use_container_width=True, hide_index=True)

        with tabs[6]: # Tab 6: Phase Work Index Matrix
            st.markdown('<div class="section-header">Work Index Density Matrix by Training Drill</div>', unsafe_allow_html=True)
            if not phase_df.empty:
                phase_df['Phase'] = phase_df['Phase'].replace(phase_map)
                wi_df = phase_df.groupby('Phase')[['Player Load', 'Total Jumps', 'Duration']].mean().reset_index()
                wi_df['Load / Min'] = wi_df['Player Load'] / wi_df['Duration']
                wi_df['Jumps / Min'] = wi_df['Total Jumps'] / wi_df['Duration']
                st.dataframe(wi_df[['Phase', 'Duration', 'Load / Min', 'Jumps / Min']], use_container_width=True, hide_index=True)

        with tabs[7]: # Tab 7: Practice Planner Engine
            st.markdown('<div class="section-header">Neuromuscular Practice Planner Sequence</div>', unsafe_allow_html=True)
            if not phase_df.empty:
                phase_df['Phase'] = phase_df['Phase'].replace(phase_map)
                available_phases = sorted(phase_df['Phase'].unique())
                selected_build = st.multiselect("Select Training Phase Drill Sequence", available_phases, key="planner_t7")
                if selected_build:
                    st.info("Planned Drill Sequence Loaded.")

    except Exception as e:
        st.error(f"Dashboard Integration Sync Error: {e}")
