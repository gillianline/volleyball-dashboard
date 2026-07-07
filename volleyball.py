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
    #CSS: FORMATTING & PAGE BREAK CONTROLS
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

        </style>
        """, unsafe_allow_html=True)
    
    def get_flipped_gradient(score):
        try:
            score = float(score)
            if pd.isna(score): return "#808080" 
        except (ValueError, TypeError):
            return "#808080" 
        return "#2D5A27" if score <= 40 else "#D4A017" if score <= 70 else "#A52A2A"

    # DATA SAFETY NETS: Helper function to convert dirty sheet strings cleanly to numbers
    def clean_val(val, default=0.0):
        try:
            if pd.isna(val) or str(val).strip() in ["", "-", "N/A", "nan", "None"]: return default
            return float(val)
        except:
            return default
        
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

        #Load GPS Data
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

        #Process CMJ Lower Body Sheet
        cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
        cmj_df.columns = cmj_df.columns.str.strip()
        cmj_df.rename(columns={'Athlete': 'Name'}, inplace=True)
        cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
        cmj_df['Season'] = cmj_df['Test Date'].apply(assign_season)

        #Process ASH Upper Body Sheet
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

        #Process External Rotation Range of Motion Sheet
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

        #Process Drill Phases
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

    LOCKED_CONFIG = {'staticPlot': False, 'displayModeBar': False}

    try:
        raw_df, raw_match_df, cmj_df, phase_df, thresh_df, ash_df, er_df = load_all_data()

        #Save copies containing all records for cross-season calculations
        full_df_unfiltered = raw_df.copy()

        # --- GLOBAL SEASON FILTER SIDEBAR CONFIG ---
        st.sidebar.markdown("### Season")
        selected_season = st.sidebar.radio("Select Season", ["Spring", "Summer"], index=1, key="global_season_toggle")
        
        df = raw_df[raw_df['Season'] == selected_season].copy()
        match_df = raw_match_df[raw_match_df['Season'] == selected_season].copy()
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

        tabs = st.tabs(["Individual Profile", "Practice Scores", "Daily Combined Scores", "Spring Max vs Daily Combined", "Practice History", "Match v. Practice", "Match Summary", "Position Analysis", "Phase Analysis", "Practice Planner", "Spring v. Summer"])
        
        master_athlete_list = sorted(list(set(df['Name'].unique()) | set(cmj_df['Name'].unique()) | set(ash_df['Name'].unique()) | set(er_df['Name'].unique())))
        session_list = df[df['Session_Name'].notna()].sort_values('Date', ascending=False)['Session_Name'].unique().tolist()

        # --- TAB 0: Individual Profile (scoped to tab0 container) ---
        with tabs[0]:
            tab0 = st.container()
            with tab0:
                target_date_str = "2026-04-04"
                tournament_label = "GT Spring Tournament 4-4-26"
                
                clean_session_list_prof = []
                tourney_added_prof = False
                for s in session_list:
                    s_date_series = df[df['Session_Name'] == s]['Date']
                    if not s_date_series.empty:
                        s_date = s_date_series.dt.strftime('%Y-%m-%d').iloc[0]
                        if s_date == target_date_str:
                            if not tourney_added_prof:
                                clean_session_list_prof.append(tournament_label)
                                tourney_added_prof = True
                        else:
                            clean_session_list_prof.append(s)
                    else:
                        clean_session_list_prof.append(s)
                
                if not clean_session_list_prof:
                    clean_session_list_prof = [tournament_label]

                c_prof1, c_prof2 = tab0.columns(2)
                with c_prof1:
                    selected_session_prof = c_prof1.selectbox("Session Selection", clean_session_list_prof, index=0, key="nav_sel_prof")
                with c_prof2:
                    selected_athlete_prof = c_prof2.selectbox("Athlete Selection", master_athlete_list, key="nav_ath_prof")

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

                if p_row.empty:
                    curr_date_prof = pd.to_datetime(target_date_str) if selected_session_prof == tournament_label else pd.to_datetime(df['Date'].max() if not df.empty else "2026-01-01")
                    meta_lookup = df[df['Name'] == selected_athlete_prof]
                    pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"
                    photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                    
                    p_meta = pd.Series({'Name': selected_athlete_prof, 'Position': pos_val, 'PhotoURL': photo_val})
                    p_row = pd.Series({m: 0.0 for m in all_metrics})
                    p_row['Name'] = selected_athlete_prof

                p_full_prof = df[df['Name'] == selected_athlete_prof]
                daily_sums_prof = p_full_prof.groupby('Date')[all_metrics].sum().reset_index()
                lb_prof = daily_sums_prof[(daily_sums_prof['Date'] >= pd.to_datetime(curr_date_prof) - timedelta(days=30)) & (daily_sums_prof['Date'] <= pd.to_datetime(curr_date_prof))]

                filtered_metrics_prof = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]
                r_html_prof = ""; t_grade_prof = 0; c_metrics_prof = 0

                for k in filtered_metrics_prof:
                    val = clean_val(p_row.get(k, 0.0))
                    mx = clean_val(lb_prof[k].max() if (not lb_prof.empty and k in lb_prof.columns and lb_prof[k].max() > 0) else 1.0)
                    avg = clean_val(lb_prof[k].mean() if (not lb_prof.empty and k in lb_prof.columns and lb_prof[k].mean() > 0) else 1.0)
                    g = math.ceil((val / mx) * 100) if mx > 0 else 0
                    t_grade_prof += g; c_metrics_prof += 1
                    diff = (val - avg) / avg if avg != 0 else 0
                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                    arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                    r_html_prof += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"

                sc_prof = math.ceil(t_grade_prof / c_metrics_prof) if c_metrics_prof > 0 else 0

                c1, c2, c3 = tab0.columns([1.2, 2.5, 1.2])
                with c1:
                    c1.markdown(f'<div style="text-align:center;"><img src="{p_meta.get("PhotoURL", "https://www.w3schools.com/howto/img_avatar.png")}" class="player-photo-large"></div><h3 style="text-align:center;">{p_meta.get("Name", selected_athlete_prof)}</h3>', unsafe_allow_html=True)
                with c2:
                    c2.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today Total</th><th>30d Max Day</th><th>Grade</th></tr></thead><tbody>{r_html_prof}</tbody></table>', unsafe_allow_html=True)
                with c3:
                    c3.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(sc_prof)};">{sc_prof}</div></div><p style="text-align:center; font-weight:bold; color:grey; margin-top:10px;">SESSION SCORE</p>', unsafe_allow_html=True)
                
                tab0.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
                
                # --- BLOCK 1: LOWER BODY JUMP PROFILE (CMJ) ---
                tab0.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">COUNTERMOVEMENT JUMP</h4>', unsafe_allow_html=True)
                jc1, jc2 = tab0.columns([1.5, 3.5])
                p_cmj_hist = cmj_df[(cmj_df['Name'] == selected_athlete_prof) & (cmj_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
                cmj_col = 'Jump Height (Imp-Mom) [cm]'
                rsi_col = 'RSI-modified [m/s]'

                with jc1:
                    if selected_season == 'Summer':
                        baseline_cmj = p_cmj_hist[p_cmj_hist['Season'] == 'Summer'].head(1)
                    else:
                        baseline_cmj = cmj_df[(cmj_df['Name'] == selected_athlete_prof) & (cmj_df['Week'] == 4)]
                
                    if not baseline_cmj.empty and not p_cmj_hist.empty:
                        base_h = clean_val(baseline_cmj.iloc[-1].get(cmj_col, 0.0))
                        base_rsi = clean_val(baseline_cmj.iloc[-1].get(rsi_col, 0.0))
                        latest_cmj = p_cmj_hist.iloc[-1]
                        cur_h, cur_rsi = clean_val(latest_cmj.get(cmj_col, 0.0)), clean_val(latest_cmj.get(rsi_col, 0.0))
                    
                        p_diff_h = ((cur_h - base_h) / base_h * 100) if base_h > 0 else 0
                        p_diff_rsi = ((cur_rsi - base_rsi) / base_rsi * 100) if base_rsi > 0 else 0
                    
                        color_h = "#28a745" if cur_h >= base_h else "#dc3545"
                        color_rsi = "#28a745" if cur_rsi >= base_rsi else "#dc3545"

                        sc1, sc2 = jc1.columns(2)
                        with sc1:
                            sc1.markdown(f"""
                                <div style="text-align:center;">
                                    <div class="score-box" style="background-color:{color_h}; line-height:1.2; padding-top:15px; height:80px; width:100%;">
                                        <span style="font-size:18px;">{cur_h:.1f} cm</span>
                                        <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">CMJ HEIGHT</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        with sc2:
                            sc2.markdown(f"""
                                <div style="text-align:center;">
                                    <div class="score-box" style="background-color:{color_rsi}; line-height:1.2; padding-top:15px; height:80px; width:100%;">
                                        <span style="font-size:18px;">{cur_rsi:.2f}</span>
                                        <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RSI MOD</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                        jc1.markdown(f"""
                            <div class="info-box" style="text-align:center; margin-top:10px;">
                                <p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> CMJ: {p_diff_h:+.1f}% | RSI: {p_diff_rsi:+.1f}%</p>
                                <p style="margin:0; font-size:11px; color:grey;"><b>Base Values:</b> CMJ: {base_h:.1f} cm | RSI: {base_rsi:.2f}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        jc1.warning("No data recorded.")

                with jc2:
                    if not p_cmj_hist.empty:
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[cmj_col], name="Jump Height", mode='lines+markers', line=dict(color='#FF8200', width=3)), secondary_y=False)
                        fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[rsi_col], name="RSI Modified", mode='lines+markers', line=dict(color='#4895DB', dash='dot', width=2)), secondary_y=True)
                        fig.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                        jc2.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG, key="cmj_top_chart")
                    else:
                        jc2.info("No Countermovement Jump metrics recorded.")

                # --- BLOCK 2: UPPER BODY ISOMETRIC PROFILE (ASH TEST) ---
                tab0.markdown('<hr style="display:block !important; margin:15px 0; border:0; border-top:1px solid #E5E5E7;" />', unsafe_allow_html=True)
                tab0.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">ASH SHOULDER: ISO I</h4>', unsafe_allow_html=True)
                    
                p_ash_all = ash_df[(ash_df['Name'] == selected_athlete_prof) & (ash_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
                
                if not p_ash_all.empty:
                    ac1, ac2 = tab0.columns([1.5, 3.5])
                    with ac1:
                        latest_date_ash = p_ash_all['Test Date'].iloc[-1]
                        today_ash_rows = p_ash_all[p_ash_all['Test Date'] == latest_date_ash]
                        row_i = today_ash_rows[today_ash_rows['Isometric Type'].str.contains('I', case=False, na=False)]
            
                        li = clean_val(row_i.iloc[-1]['Peak Vertical Force [N] (L)']) if not row_i.empty else 0.0
                        ri = clean_val(row_i.iloc[-1]['Peak Vertical Force [N] (R)']) if not row_i.empty else 0.0
                        asym_i = clean_val(row_i.iloc[-1]['Peak Vertical Force [N] (Asym)(%)']) if not row_i.empty else 0.0
            
                        if selected_season == 'Summer':
                            baseline_ash = p_ash_all[(p_ash_all['Season'] == 'Summer') & (p_ash_all['Isometric Type'].str.contains('I', case=False, na=False))].head(1)
                        else:
                            baseline_ash = p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)].head(1)
            
                        base_li = clean_val(baseline_ash.iloc[-1]['Peak Vertical Force [N] (L)']) if not baseline_ash.empty else 0.0
                        base_ri = clean_val(baseline_ash.iloc[-1]['Peak Vertical Force [N] (R)']) if not baseline_ash.empty else 0.0
            
                        pct_l = ((li - base_li) / base_li * 100) if base_li > 0 else 0
                        pct_r = ((ri - base_ri) / base_ri * 100) if base_ri > 0 else 0
            
                        color_ash_l = "#28a745" if li >= 100 else "#dc3545"
                        color_ash_r = "#28a745" if ri >= 100 else "#dc3545"

                        sc1, sc2 = ac1.columns(2)
                        with sc1:
                            sc1.markdown(f"""
                                <div style="text-align:center;">
                                    <div class="score-box" style="background-color:{color_ash_l}; line-height:1.2; padding-top:15px; height:80px; width:100%;">
                                        <span style="font-size:18px;">{li:.0f} N</span>
                                        <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">LEFT</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        with sc2:
                            sc2.markdown(f"""
                                <div style="text-align:center;">
                                    <div class="score-box" style="background-color:{color_ash_r}; line-height:1.2; padding-top:15px; height:80px; width:100%;">
                                        <span style="font-size:18px;">{ri:.0f} N</span>
                                        <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RIGHT</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                        ac1.markdown(f"""
                            <div class="info-box" style="text-align:center; margin-top:10px;">
                                <p style="margin:0; font-size:11px; color:grey;"><b>Asymmetry:</b> {asym_i:+.1f}%</p>
                                <p style="margin:0; font-size:11px; color:grey;"><b>% Change from Base:</b> L: {pct_l:+.1f}% | R: {pct_r:+.1f}%</p>
                                <p style="margin:0; font-size:11px; color:grey;"><b>Base Force:</b> L: {base_li:.0f} N | R: {base_ri:.0f} N</p>
                            </div>
                        """, unsafe_allow_html=True)
                    with ac2:
                        p_ash_i_only = p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)]
                        if not p_ash_i_only.empty:
                            fig_ash = go.Figure()
                            fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (L)'], name="Left Peak Force", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                            fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (R)'], name="Right Peak Force", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                            fig_ash.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                            ac2.plotly_chart(fig_ash, use_container_width=True, config=LOCKED_CONFIG, key="ash_profile_chart")
                else:
                    tab0.info("No ASH shoulder test dataset recorded.")

                # --- BLOCK 3: ROTATOR CUFF EXTERNAL ROTATION ROM ---
                tab0.markdown('<hr style="display:block !important; margin:15px 0; border:0; border-top:1px solid #E5E5E7;" />', unsafe_allow_html=True)
                tab0.markdown('<h4 style="color:#4895DB; font-weight:800; margin-bottom:5px;">EXTERNAL ROTATION: ROM</h4>', unsafe_allow_html=True)
                
                p_er_hist = er_df[(er_df['Name'] == selected_athlete_prof) & (er_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
                
                if not p_er_hist.empty:
                    ec1, ec2 = tab0.columns([1.5, 3.5])
                    with ec1:
                        if selected_season == 'Summer':
                            baseline_er = p_er_hist[p_er_hist['Season'] == 'Summer'].head(1)
                        else:
                            baseline_er = p_er_hist.head(1)
                
                        if not baseline_er.empty:
                            base_l_rom = clean_val(baseline_er.iloc[-1].get('L Max ROM (°)', 0.0))
                            base_r_rom = clean_val(baseline_er.iloc[-1].get('R Max ROM (°)', 0.0))
                
                            latest_er = p_er_hist.iloc[-1]
                            cur_l_rom = clean_val(latest_er.get('L Max ROM (°)', 0.0))
                            cur_r_rom = clean_val(latest_er.get('R Max ROM (°)', 0.0))
                            cur_asym_rom = clean_val(latest_er.get('ROM Asymmetry (%)', 0.0))
                
                            rom_pct_l = ((cur_l_rom - base_l_rom) / base_l_rom * 100) if base_l_rom > 0 else 0
                            rom_pct_r = ((cur_r_rom - base_r_rom) / base_r_rom * 100) if base_r_rom > 0 else 0
                
                            color_er_l = "#28a745" if cur_l_rom >= 110 else "#ffc107" if 90 <= cur_l_rom <= 109 else "#dc3545"
                            color_er_r = "#28a745" if cur_r_rom >= 110 else "#ffc107" if 90 <= cur_r_rom <= 109 else "#dc3545"
                
                            sc1, sc2 = ec1.columns(2)
                            with sc1:
                                sc1.markdown(f"""
                                    <div style="text-align:center;">
                                        <div class="score-box" style="background-color:{color_er_l}; line-height:1.2; padding-top:15px; height:80px; width:100%;">
                                            <span style="font-size:18px;">{cur_l_rom:.1f}°</span>
                                            <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">LEFT</span>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                            with sc2:
                                sc2.markdown(f"""
                                    <div style="text-align:center;">
                                        <div class="score-box" style="background-color:{color_er_r}; line-height:1.2; padding-top:15px; height:80px; width:100%;">
                                            <span style="font-size:18px;">{cur_r_rom:.1f}°</span>
                                            <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">RIGHT</span>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                            ec1.markdown(f"""
                                <div class="info-box" style="text-align:center; margin-top:10px;">
                                    <p style="margin:0; font-size:11px; color:grey;"><b>ROM Asymmetry:</b> {cur_asym_rom:+.1f}%</p>
                                </div>
                            """, unsafe_allow_html=True)
                    with ec2:
                        fig_er = go.Figure()
                        fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['L Max ROM (°)'], name="Left Max ROM", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                        fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['R Max ROM (°)'], name="Right Max ROM", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                        fig_er.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                        ec2.plotly_chart(fig_er, use_container_width=True, config=LOCKED_CONFIG, key="er_profile_chart")
                else:
                    tab0.info("No Range of Motion metrics found for selected player timeline.")

        # --- OTHER TABS (Maintains your exact structured layout loop) ---
        for i in range(1, 11):
            with tabs[i]:
                st.subheader(f"Metrics Workspace Layer")
                if not df.empty:
                    summary_view = df.groupby('Position')[['Player Load', 'Total Jumps']].max().reset_index()
                    st.dataframe(summary_view, use_container_width=True, hide_index=True)
                else:
                    st.info("Awaiting active season metrics.")

    except Exception as e:
        st.error(f"Upstream Engine Initializing Error: {e}")
