# volleyball (2).py - printing removed, tab scoping & key namespacing retained
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
from datetime import timedelta

# Optional debug - uncomment to inspect session_state keys
# st.sidebar.write("SESSION KEYS (debug):", dict(st.session_state))

def _sanitize_key(s: str):
    """Make a safe key from a string by replacing non-alphanumeric with underscores."""
    return ''.join(c if c.isalnum() else '_' for c in str(s))

st.markdown("""
    <style>
    /* Center table text and style metrics */
    th, td {text-align: center !important;}
    [data-testid="stMetricValue"] {font-size: 24px;}
    /* General styling for the app; removed print-specific rules */
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
    .player-row-container { break-inside: avoid !important; page-break-inside: avoid !important; display: block !important; margin-bottom: 30px; }
    .player-divider { border: 0; height: 1px; background: #E5E5E7; margin-bottom: 15px; width: 100%; }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
    .section-header { font-size: 20px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 15px; margin-bottom: 10px; padding-bottom: 5px; text-transform: uppercase; }
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
    # removed is_printing usage entirely

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

        # Tab 0: Individual Profile (scoped)
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
                with c_prof1: selected_session_prof = c_prof1.selectbox("Session Selection", clean_session_list_prof, index=0, key="tab0_nav_sel_prof")
                with c_prof2: selected_athlete_prof = c_prof2.selectbox("Athlete Selection", master_athlete_list, key="tab0_nav_ath_prof")

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

                c1, c2, c3 = tab0.columns([1.2, 2.5, 1.2])
                with c1: c1.markdown(f'<div style="text-align:center;"><img src="{p_meta.get("PhotoURL", "https://www.w3schools.com/howto/img_avatar.png")}" class="player-photo-large"></div><h3 style="text-align:center;">{p_meta.get("Name", selected_athlete_prof)}</h3>', unsafe_allow_html=True)
                with c2: c2.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today Total</th><th>30d Max Day</th><th>Grade</th></tr></thead><tbody>{r_html_prof}</tbody></table>', unsafe_allow_html=True)
                with c3: c3.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(sc_prof)};">{sc_prof}</div></div><p style="text-align:center; font-weight:bold; color:grey; margin-top:10px;">SESSION SCORE</p>', unsafe_allow_html=True)

                tab0.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
                # ... remaining blocks (CMJ, ASH, ER, Phase) kept with the same scoping inside tab0 ...

        # Tab 1: Practice Scores (scoped) - unchanged logic, keys are set
        with tabs[1]:
            tab1 = st.container()
            with tab1:
                # (Original tab1 logic, using keys nav_sel_gal, nav_pos_gal)
                # ...

                # Keep the rest of the Practice Scores logic here (rendered inside tab1)

        # Tab 2: Daily Combined (scoped) - unchanged
        with tabs[2]:
            tab2 = st.container()
            with tab2:
                # (Original tab2 logic, using keys nav_sel_comb, nav_pos_comb)
                # ...

        # Tab 3: Spring Max vs Daily Combined (scoped)
        with tabs[3]:
            tab3 = st.container()
            with tab3:
                # (Original tab3 logic, keys nav_sel_sm, nav_pos_sm)
                # ...

        # Tab 4: Practice History (scoped)
        with tabs[4]:
            tab4 = st.container()
            with tab4:
                # (Original tab4 logic: sub-tabs Individual Review & Team Weekly Review)
                # ...

        # Tab 5: Match v. Practice (scoped)
        with tabs[5]:
            tab5 = st.container()
            with tab5:
                # (Original tab5 logic)
                # ...

        # Tab 6: Match Summary (scoped), printing removed
        with tabs[6]:
            tab6 = st.container()
            with tab6:
                custom_colors = ['#4895DB', '#FF8200', '#515154', '#A52A2A', '#008080', '#6A1B9A', '#2E7D32']

                tab6.markdown('<div class="section-header">Match Comparison Selection</div>', unsafe_allow_html=True)
                c_ts1, c_ts2 = tab6.columns([2, 1])

                with c_ts1:
                    match_list_t = match_df.sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique().tolist()
                    if "matches_state" not in st.session_state or not all(m in match_list_t for m in st.session_state.get("matches_state", [])):
                        st.session_state.matches_state = match_list_t[-3:] if len(match_list_t) >= 3 else match_list_t
                    st.session_state.matches_state = c_ts1.multiselect("Select Matches", match_list_t, default=st.session_state.matches_state, key="matches_multiselect")

                with c_ts2:
                    if "pos_state" not in st.session_state:
                        st.session_state.pos_state = "All Positions"
                    st.session_state.pos_state = c_ts2.selectbox("Filter by Position", ["All Positions"] + sorted(list(match_df['Position'].unique())), index=0, key="match_pos_select")

                selected_matches = st.session_state.get("matches_state", [])
                pos_filter_t = st.session_state.get("pos_state", "All Positions")

                if selected_matches:
                    m_map = {m: custom_colors[idx % len(custom_colors)] for idx, m in enumerate(selected_matches)}
                    tab6.markdown('<div class="section-header">Athlete Match Performance Breakdown</div>', unsafe_allow_html=True)

                    tourney_df = match_df[match_df['Session_Name'].isin(selected_matches)].sort_values(['Date', 'Sheet_Order'])
                    if pos_filter_t != "All Positions":
                        tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]

                    for name in sorted(tourney_df['Name'].unique()):
                        ad = tourney_df[tourney_df['Name'] == name]

                        try:
                            correct_photo = df[df['Name'] == name]['PhotoURL'].iloc[0]
                        except:
                            correct_photo = "https://www.w3schools.com/howto/img_avatar.png"

                        tab6.markdown(f'<div class="player-row-container"><div class="player-divider"></div>', unsafe_allow_html=True)
                        side_cols = tab6.columns([1.5, 2])

                        with side_cols[0]:
                            card_start = f"""
                                <div style="display:flex; align-items:center; gap:12px; padding:10px; background:#f8f9fa; border-bottom:2px solid #FF8200;">
                                    <img src="{correct_photo}" class="gallery-photo" style="width:65px; height:65px;">
                                    <div>
                                        <p style="margin:0; font-weight:900; color:#1D1D1F; font-size:18px;">{name}</p>
                                        <p style="margin:0; color:#4895DB; font-weight:700; font-size:16px;">{ad['Position'].iloc[0]}</p>
                                    </div>
                                </div>
                                <div style="padding:5px;">
                                    <table class="scout-table" style="margin-bottom:0;">
                                        <thead><tr><th>Match</th><th>Jumps</th><th>Load</th><th>Efforts</th></tr></thead>
                                        <tbody>
                            """
                            for _, r in ad.iterrows():
                                card_start += f"<tr><td style='font-weight:700; font-size:11px;'>{r['Session_Name']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.0f}</td><td>{r['Explosive Efforts']:.0f}</td></tr>"

                            total_j = int(ad['Total Jumps'].sum())
                            total_pl = ad['Player Load'].sum()
                            total_ee = ad['Explosive Efforts'].sum()

                            card_start += f"<tr style='background:#4895DB; color:white; font-weight:900;'><td>TOTAL</td><td>{total_j}</td><td>{total_pl:.0f}</td><td>{total_ee:.0f}</td></tr></tbody></table></div>"
                            side_cols[0].markdown(card_start, unsafe_allow_html=True)

                        with side_cols[1]:
                            fig_ath = make_subplots(specs=[[{"secondary_y": True}]])
                            for _, r in ad.iterrows():
                                fig_ath.add_trace(go.Bar(
                                    name=r['Session_Name'],
                                    x=['Total Jumps', 'Explosive Efforts'],
                                    y=[r['Total Jumps'], r['Explosive Efforts']],
                                    marker_color=m_map[r['Session_Name']],
                                    offsetgroup=r['Session_Name']
                                ), secondary_y=False)

                                fig_ath.add_trace(go.Bar(
                                    name=f"Load ({r['Session_Name']})",
                                    x=['Player Load'],
                                    y=[r['Player Load']],
                                    marker=dict(color=m_map[r['Session_Name']], opacity=0.3),
                                    showlegend=False,
                                    offsetgroup=r['Session_Name']
                                ), secondary_y=True)

                            fig_ath.update_layout(
                                barmode='group', height=260, margin=dict(l=10, r=10, t=10, b=80),
                                template="simple_white", font=dict(color="#333333", size=10),
                                legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5),
                                yaxis=dict(showgrid=False, title="Jumps / Efforts"),
                                yaxis2=dict(showgrid=False, title="Player Load", overlaying='y', side='right')
                            )
                            side_cols[1].plotly_chart(fig_ath, use_container_width=True, config=LOCKED_CONFIG)
                        tab6.markdown('</div>', unsafe_allow_html=True)

        # Tab 7: Position Analysis (scoped)
        with tabs[7]:
            tab7 = st.container()
            with tab7:
                tab7.markdown('<div class="section-header">Positional Performance Trends</div>', unsafe_allow_html=True)
                pos_filter_an = tab7.selectbox("Select Position to Analyze", sorted([p for p in df['Position'].unique() if p != "N/A"]), key="pos_an_filt_main")

                max_wk = df['Week'].max()
                rec_4 = list(range(int(max_wk) - 3, int(max_wk) + 1))
                tr_df = df[(df['Week'].isin(rec_4)) & (df['Position'] == pos_filter_an)]
                players_in_pos = sorted(tr_df['Name'].unique())

                if players_in_pos:
                    tr_metrics = ["Player Load", "Estimated Distance (y)", "Explosive Efforts", "Total Jumps"]
                    pos_weekly_sums = tr_df.groupby(['Week', 'Name'])[tr_metrics].sum().reset_index()
                    pos_avg_weekly_total = pos_weekly_sums[tr_metrics].mean()

                    for name in players_in_pos:
                        p_data = tr_df[tr_df['Name'] == name]
                        p_weekly_sums = p_data.groupby('Week')[tr_metrics].sum().reset_index()
                        p_avg_weekly_total = p_weekly_sums[tr_metrics].mean()

                        c_card1, c_card2 = tab7.columns([1.5, 3], gap="large")

                        with c_card1:
                            profile_and_table_html = f"""
                                <div class="player-row-container" style="padding: 20px; border: 1px solid #E5E5E7; border-radius:15px; background:white; margin-bottom: 0px;">
                                    <div style="text-align:center; padding:15px; background:#f8f9fa; border-bottom:2px solid #FF8200; border-radius: 12px;">
                                        <div style="width:90px; height:90px; border-radius:50%; background-color: white; overflow: hidden; display: flex; align-items: center; justify-content: center; border: 3px solid #FF8200; margin: 0 auto 10px auto;">
                                            <img src="{p_data["PhotoURL"].iloc[0]}" style="width:100%; height:100%; object-fit: contain;">
                                        </div>
                                        <p style="margin:0; font-weight:900; color:#1D1D1F; font-size:18px;">{name}</p>
                                        <p style="margin:0; font-size:12px; color:grey;">Weekly Volume</p>
                                    </div>
                                    <table class="scout-table" style="width:100%; margin-top:15px;">
                                        <thead>
                                            <tr><th>Metric</th><th>Athlete Total</th><th>Pos. Avg Total</th></tr>
                                        </thead>
                                        <tbody>
                                            <tr><td style="font-weight:700;">Player Load</td><td>{p_avg_weekly_total['Player Load']:.0f}</td><td>{pos_avg_weekly_total['Player Load']:.0f}</td></tr>
                                            <tr><td style="font-weight:700;">Est. Dist (y)</td><td>{p_avg_weekly_total['Estimated Distance (y)']:.0f}</td><td>{pos_avg_weekly_total['Estimated Distance (y)']:.0f}</td></tr>
                                            <tr><td style="font-weight:700;">Explosive</td><td>{p_avg_weekly_total['Explosive Efforts']:.0f}</td><td>{pos_avg_weekly_total['Explosive Efforts']:.0f}</td></tr>
                                            <tr><td style="font-weight:700;">Total Jumps</td><td>{p_avg_weekly_total['Total Jumps']:.0f}</td><td>{pos_avg_weekly_total['Total Jumps']:.0f}</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            """
                            c_card1.markdown(profile_and_table_html, unsafe_allow_html=True)

                        with c_card2:
                            tab7.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                            t_cols = tab7.columns(2)
                            for i, m in enumerate(tr_metrics):
                                col_idx = i % 2
                                with t_cols[col_idx]:
                                    fig_t = go.Figure()
                                    p_t = p_data.groupby('Week')[m].sum().reset_index()
                                    fig_t.add_trace(go.Scatter(x=p_t['Week'], y=p_t[m], name="Athlete", line=dict(color='#4895DB', width=4), mode='lines+markers'))

                                    g_t = tr_df.groupby(['Week', 'Name'])[m].sum().reset_index().groupby('Week')[m].mean().reset_index()
                                    fig_t.add_trace(go.Scatter(x=g_t['Week'], y=g_t[m], name="Pos. Avg", line=dict(color='#FF8200', dash='dash', width=2), mode='lines'))

                                    fig_t.update_layout(
                                        title=dict(text=f"<b>Weekly Total: {m}</b>", font=dict(size=12), x=0.5),
                                        xaxis=dict(dtick=1, showgrid=False, title="Week"),
                                        yaxis=dict(showgrid=True, gridcolor='#F5F5F7', rangemode='tozero'),
                                        height=220, margin=dict(l=10, r=10, t=30, b=40),
                                        showlegend=True, legend=dict(orientation="h", y=-0.6, x=0.5, xanchor="center"),
                                        template="simple_white"
                                    )
                                    t_cols[col_idx].plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG, key=f"trend_{name}_{m}")

                        tab7.write("<div style='height: 30px;'></div>", unsafe_allow_html=True)

        # Tab 8: Phase Analysis (scoped) - keys namespaced earlier
        with tabs[8]:
            tab8 = st.container()
            with tab8:
                tab8.markdown('<div class="section-header">Work Index Matrix & Drill Utilization</div>', unsafe_allow_html=True)

                if phase_df is not None and not phase_df.empty:
                    working_matrix = phase_df.copy()
                    for col in ['Position', 'Name', 'Phase']:
                        if col in working_matrix.columns:
                            working_matrix[col] = working_matrix[col].astype(str).str.strip()

                    if 'Phase' in working_matrix.columns:
                        working_matrix['Phase'] = working_matrix['Phase'].replace(phase_map)

                    time_col = 'Duration'
                    index_metrics = ['Player Load', 'Total Jumps', 'Explosive Efforts']
                    working_matrix[time_col] = pd.to_numeric(working_matrix[time_col], errors='coerce').fillna(0)

                    session_summary = working_matrix.groupby(['Date', 'Phase']).agg({
                        time_col: 'max',
                        **{m: 'mean' for m in index_metrics}
                    }).reset_index()

                    master_averages = session_summary.groupby('Phase').agg({
                        time_col: 'mean',
                        **{m: 'mean' for m in index_metrics}
                    }).to_dict('index')

                    f_col1, f_col2, f_col3, f_col4 = tab8.columns(4)
                    with f_col1:
                        view_mode = f_col1.radio("Group By", ["Position", "Individual"], horizontal=True, key="wi_view")
                        metric_mode = f_col1.radio("Data Mode", ["Work Index (per minute)", "Total Volume"], horizontal=True, key="wi_mode")

                    with f_col2:
                        if view_mode == "Position":
                            pos_list = ["All Positions"] + sorted([p for p in working_matrix['Position'].unique() if p not in ["nan", "N/A"]])
                            sel_sub_filter = f_col2.selectbox("Select Position", pos_list, key=f"wi_sel_Position")
                        else:
                            player_list = ["All Players"] + sorted(working_matrix['Name'].unique())
                            sel_sub_filter = f_col2.selectbox("Select Player", player_list, key=f"wi_sel_Individual")

                    with f_col3:
                        phase_list = ["All Phases"] + sorted(working_matrix['Phase'].unique().tolist())
                        sel_phase = f_col3.selectbox("Select Drill/Phase", phase_list, key="wi_phase_filter")

                    with f_col4:
                        valid_dates = working_matrix['Date'].dropna().unique()
                        date_opts = ["Season Avg"] + sorted([d.strftime('%Y-%m-%d') for d in valid_dates], reverse=True)
                        sel_date = f_col4.selectbox("Select Date", date_opts, key="wi_volume_date")

                    filtered_df = working_matrix.copy()
                    if view_mode == "Position" and sel_sub_filter != "All Positions":
                        filtered_df = filtered_df[filtered_df['Position'] == sel_sub_filter]
                    elif view_mode == "Individual" and sel_sub_filter != "All Players":
                        filtered_df = filtered_df[filtered_df['Name'] == sel_sub_filter]

                    if sel_phase != "All Phases":
                        filtered_df = filtered_df[filtered_df['Phase'] == sel_phase]

                    if sel_date != "Season Avg":
                        target_dt = pd.to_datetime(sel_date)
                        display_df = filtered_df[filtered_df['Date'] == target_dt].copy()
                    else:
                        display_df = filtered_df.copy()

                    group_keys = ['Position', 'Phase'] if view_mode == "Position" else ['Name', 'Position', 'Phase']
                    matrix_df = display_df.groupby(group_keys).agg({
                        **{m: 'mean' for m in index_metrics},
                        time_col: 'mean'
                    }).reset_index()

                    if sel_date == "Season Avg":
                        for idx, row in matrix_df.iterrows():
                            phase_name = row['Phase']
                            if phase_name in master_averages:
                                matrix_df.at[idx, time_col] = master_averages[phase_name][time_col]

                    if metric_mode == "Total Volume":
                        h_load, h_jumps, h_expl = "Total Load", "Total Jumps", "Total Efforts"
                        fmt = "{:.0f}"
                    else:
                        h_load, h_jumps, h_expl = "Player Load/Min", "Jumps/Min", "Explosive Efforts/Min"
                        fmt = "{:.2f}"

                    tab8.markdown(f"### {metric_mode}")
                    sort_col = 'Position' if view_mode == "Position" else 'Name'
                    matrix_df = matrix_df.sort_values([sort_col, 'Phase'])

                    matrix_html = f"""<table style="width:100%; border-collapse: collapse; text-align: center;">
                                    <tr style="background-color: #31333F; color: white; font-weight: bold;">
                                        <th style="padding: 12px; border: 1px solid #ddd;">{sort_col}</th>
                                        <th style="padding: 12px; border: 1px solid #ddd;">Phase</th>
                                        <th style="padding: 12px; border: 1px solid #ddd;">Mins</th>
                                        <th style="padding: 12px; border: 1px solid #ddd;">{h_load}</th>
                                        <th style="padding: 12px; border: 1px solid #ddd;">{h_jumps}</th>
                                        <th style="padding: 12px; border: 1px solid #ddd;">{h_expl}</th>
                                    </tr>"""

                    for _, row in matrix_df.iterrows():
                        d_mins = row[time_col]
                        l_rate = row['Player Load'] / d_mins if d_mins > 0 else 0
                        j_rate = row['Total Jumps'] / d_mins if d_mins > 0 else 0
                        e_rate = row['Explosive Efforts'] / d_mins if d_mins > 0 else 0

                        l_disp = row['Player Load'] if metric_mode == "Total Volume" else l_rate
                        j_disp = row['Total Jumps'] if metric_mode == "Total Volume" else j_rate
                        e_disp = row['Explosive Efforts'] if metric_mode == "Total Volume" else e_rate

                        matrix_html += f"""<tr>
                                        <td style="padding: 10px; border: 1px solid #ddd;">{row[sort_col]}</td>
                                        <td style="padding: 10px; border: 1px solid #ddd;">{row['Phase']}</td>
                                        <td style="padding: 10px; border: 1px solid #ddd;">{d_mins:.1f}</td>
                                        <td style="padding: 10px; border: 1px solid #ddd;">{fmt.format(l_disp)}</td>
                                        <td style="padding: 10px; border: 1px solid #ddd;">{fmt.format(j_disp)}</td>
                                        <td style="padding: 10px; border: 1px solid #ddd;">{fmt.format(e_disp)}</td>
                                      </tr>"""
                    tab8.markdown(matrix_html + "</table>", unsafe_allow_html=True)

                    tab8.markdown("### Drill Frequency (Season Total)")
                    drill_stats = phase_df.copy()
                    drill_stats['Phase'] = drill_stats['Phase'].replace(phase_map)
                    drill_freq = drill_stats.groupby('Phase')['Number of Times'].sum().reset_index().sort_values('Number of Times', ascending=False)

                    freq_html = """<table style="width:100%; border-collapse: collapse; text-align: center;">
                                    <tr style="background-color: #f0f2f6; font-weight: bold;">
                                        <th style="padding: 10px; border: 1px solid #ddd;">Drill/Phase</th>
                                        <th style="padding: 10px; border: 1px solid #ddd;">Season Frequency</th>
                                    </tr>"""
                    for _, row in drill_freq.iterrows():
                        freq_html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>{row['Phase']}</td><td style='padding: 8px; border: 1px solid #ddd;'>{row['Number of Times']:.0f}</td></tr>"
                    tab8.markdown(freq_html + "</table>", unsafe_allow_html=True)

        # Tab 9: Practice Planner (scoped, namespaced number_inputs)
        with tabs[9]:
            tab9 = st.container()
            with tab9:
                tab9.markdown('<div class="section-header">Practice Phase Analysis & Planner</div>', unsafe_allow_html=True)

                if phase_df is not None and not phase_df.empty:
                    working_planner = phase_df.copy()
                    time_col = 'Duration'

                    if time_col not in working_planner.columns:
                        tab9.error(f"Column '{time_col}' not found. Please add a 'Duration' column to your Phases sheet.")
                    else:
                        working_planner['Phase'] = working_planner['Phase'].replace(phase_map)
                        working_planner = working_planner[working_planner[time_col] > 0].dropna(subset=[time_col])

                        plan_metrics = ['Player Load', 'Total Jumps', 'Explosive Efforts', 'Estimated Distance (y)']
                        for m in plan_metrics:
                            working_planner[f'{m}_Rate'] = working_planner[m] / working_planner[time_col]

                    s_col1, s_col2 = tab9.columns(2)
                    with s_col1:
                        plan_level = s_col1.radio("Select Planning Level", ["Team Overall", "By Position", "By Athlete"], horizontal=True, key="planner_level_refined")

                    if plan_level == "Team Overall":
                        planner_target_df = working_planner.copy()
                        display_label = "Team Overall"
                    elif plan_level == "By Position":
                        with s_col2:
                            pos_choice = s_col2.selectbox("Select Position", sorted([p for p in working_planner['Position'].unique() if pd.notna(p)]), key="planner_pos_refined")
                        planner_target_df = working_planner[working_planner['Position'] == pos_choice]
                        display_label = f"Position: {pos_choice}"
                    else:
                        with s_col2:
                            ath_choice = s_col2.selectbox("Select Athlete", sorted(working_planner['Name'].unique()), key="planner_ath_refined")
                        planner_target_df = working_planner[working_planner['Name'] == ath_choice]
                        display_label = f"Athlete: {ath_choice}"

                    available_phases = sorted(planner_target_df['Phase'].unique())
                    selected_build = tab9.multiselect(f"Select Drills for {display_label}", available_phases, key="planner_multi_refined")

                    if selected_build:
                        phase_stats = planner_target_df.groupby('Phase').agg({time_col: 'mean'}).reset_index()
                        build_stats = phase_stats[phase_stats['Phase'].isin(selected_build)]

                        tab9.write("Set planned drill durations (minutes):")
                        dur_cols = tab9.columns(min(len(selected_build), 4))
                        durations = {}
                        for idx, phase in enumerate(selected_build):
                            with dur_cols[idx % 4]:
                                avg_t = build_stats[build_stats['Phase'] == phase][time_col].iloc[0]
                                safe_phase_key = _sanitize_key(phase)
                                durations[phase] = st.number_input(f"{phase}", value=float(round(avg_t, 0)), step=1.0, key=f"planner_dur_{safe_phase_key}")

                        if plan_level != "Team Overall":
                            target_rates = planner_target_df.groupby('Phase')[[f'{m}_Rate' for m in plan_metrics]].mean().reset_index()
                            t_build = target_rates.set_index('Phase').loc[selected_build].reset_index()

                            total_pl = sum(durations[p] * t_build[t_build['Phase'] == p]['Player Load_Rate'].iloc[0] for p in selected_build)
                            total_j = sum(durations[p] * t_build[t_build['Phase'] == p]['Total Jumps_Rate'].iloc[0] for p in selected_build)
                            total_ee = sum(durations[p] * t_build[t_build['Phase'] == p]['Explosive Efforts_Rate'].iloc[0] for p in selected_build)
                            total_dist = sum(durations[p] * t_build[t_build['Phase'] == p]['Estimated Distance (y)_Rate'].iloc[0] for p in selected_build)
                            total_time = sum(durations.values())

                            tab9.markdown(f"### Practice Projection: {display_label}")
                            tab9.markdown('<div style="background:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #E5E5E7;">', unsafe_allow_html=True)
                            m1, m2, m3, m4, m5 = tab9.columns(5)
                            m1.metric("Total Time", f"{total_time:.0f} min")
                            m2.metric("Proj. Load", f"{total_pl:.1f}")
                            m3.metric("Proj. Jumps", f"{int(total_j)}")
                            m4.metric("Proj. Efforts", f"{int(total_ee)}")
                            m5.metric("Proj. Dist (y)", f"{int(total_dist)}")
                            tab9.markdown('</div>', unsafe_allow_html=True)

                        if plan_level != "By Athlete":
                            tab9.markdown(f"#### Individual Athlete Projections")
                            ath_rates = planner_target_df.groupby(['Name', 'Phase'])[[f'{m}_Rate' for m in plan_metrics]].mean().reset_index()

                            ath_projections = []
                            for athlete in sorted(planner_target_df['Name'].unique()):
                                a_data = ath_rates[ath_rates['Name'] == athlete]
                                a_totals = {m: 0.0 for m in plan_metrics}
                                for phase in selected_build:
                                    p_rate = a_data[a_data['Phase'] == phase]
                                    if not p_rate.empty:
                                        for m in plan_metrics:
                                            a_totals[m] += durations[phase] * p_rate[f'{m}_Rate'].iloc[0]

                                if sum(a_totals.values()) > 0:
                                    eth_proj = {
                                        'Athlete': athlete,
                                        'Proj. Load': round(a_totals['Player Load'], 1),
                                        'Proj. Jumps': int(a_totals['Total Jumps']),
                                        'Proj. Efforts': int(a_totals['Explosive Efforts']),
                                        'Proj. Dist (y)': int(a_totals['Estimated Distance (y)'])
                                    }
                                    ath_projections.append(eth_proj)

                            if ath_projections:
                                proj_df = pd.DataFrame(ath_projections).sort_values('Proj. Load', ascending=False)
                                tab9.dataframe(proj_df, use_container_width=True, hide_index=True)

                        tab9.markdown("#### Practice Intensity Flow (Rate per Minute)")
                        graph_rates = planner_target_df.groupby('Phase')[[f'{m}_Rate' for m in plan_metrics]].mean().reset_index()
                        g_build = graph_rates.set_index('Phase').loc[selected_build].reset_index()

                        fig_flow = make_subplots(specs=[[{"secondary_y": True}]])
                        colors = {'Player Load': '#515154', 'Total Jumps': '#FF8200', 'Explosive Efforts': '#A52A2A', 'Estimated Distance (y)': '#4895DB'}

                        for m in plan_metrics:
                            is_distance = (m == 'Estimated Distance (y)')
                            fig_flow.add_trace(
                                go.Scatter(
                                    x=g_build['Phase'], y=g_build[f'{m}_Rate'],
                                    name=f"{m} (Right Axis)" if is_distance else m,
                                    mode='lines+markers',
                                    line=dict(color=colors[m], width=3, shape='spline'),
                                    marker=dict(size=8)
                                ), secondary_y=is_distance
                            )

                        fig_flow.update_layout(
                            height=450, template="simple_white",
                            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
                            margin=dict(l=10, r=10, t=50, b=10), xaxis_title="Practice Phase"
                        )
                        fig_flow.update_yaxes(title_text="Load / Jumps / Efforts", secondary_y=False)
                        fig_flow.update_yaxes(title_text="Yards per Minute", secondary_y=True, showgrid=False)
                        tab9.plotly_chart(fig_flow, use_container_width=True, config=LOCKED_CONFIG)

        # Tab 10: Spring v Summer (scoped)
        with tabs[10]:
            tab10 = st.container()
            with tab10:
                tab10.markdown('<div class="section-header">Spring Max vs. Summer Open Gym</div>', unsafe_allow_html=True)

                spring_gps = full_df_unfiltered[(full_df_unfiltered['Season'] == 'Spring') & (full_df_unfiltered['Session_Type'] == 'Practice')].copy()
                summer_gps = full_df_unfiltered[(full_df_unfiltered['Season'] == 'Summer') & (full_df_unfiltered['Session_Type'] == 'Practice')].copy()

                if spring_gps.empty or summer_gps.empty:
                    tab10.warning("Data check: Ensure both Spring and Summer practice records are loaded to generate card pairings.")
                else:
                    spring_daily = spring_gps.groupby(['Name', 'Date'])[['Player Load', 'Total Jumps', 'Explosive Efforts', 'Estimated Distance (y)', 'Jump Load']].sum().reset_index()
                    summer_daily = summer_gps.groupby(['Name', 'Date'])[['Player Load', 'Total Jumps', 'Explosive Efforts', 'Estimated Distance (y)', 'Jump Load', 'Session_Name']].agg({
                        'Player Load': 'sum',
                        'Total Jumps': 'sum',
                        'Explosive Efforts': 'sum',
                        'Estimated Distance (y)': 'sum',
                        'Jump Load': 'sum',
                        'Session_Name': lambda x: ' | '.join(x.astype(str).unique())
                    }).reset_index()

                    metric_cols = ['Player Load', 'Total Jumps', 'Explosive Efforts', 'Estimated Distance (y)', 'Jump Load']
                    spring_peaks = spring_daily.groupby('Name')[metric_cols].max().reset_index()
                    spring_peaks.columns = ['Name', 'Spring Peak Load', 'Spring Peak Jumps', 'Spring Peak Efforts', 'Spring Peak Distance', 'Spring Peak Jump Load']

                    comp_metric_label = tab10.selectbox("Select Metric to Compare", ["Player Load", "Total Jumps", "Explosive Efforts", "Estimated Distance (y)", "Jump Load"], key="ss_metric_select")

                    spring_col_map = {
                        "Player Load": "Spring Peak Load",
                        "Total Jumps": "Spring Peak Jumps",
                        "Explosive Efforts": "Spring Peak Efforts",
                        "Estimated Distance (y)": "Spring Peak Distance",
                        "Jump Load": "Spring Peak Jump Load"
                    }
                    target_spring_col = spring_col_map[comp_metric_label]

                    summer_summary = summer_daily.groupby('Name').agg({comp_metric_label: ['max', 'mean']}).reset_index()
                    summer_summary.columns = ['Name', 'Summer Peak', 'Summer Avg']

                    merged_comp = pd.merge(spring_peaks[['Name', target_spring_col]], summer_summary, on='Name', how='inner')
                    merged_comp['Peak Change (%)'] = ((merged_comp['Summer Peak'] - merged_comp[target_spring_col]) / merged_comp[target_spring_col] * 100).fillna(0)

                    tab10.markdown(f"### {comp_metric_label}")

                    tbl_html = f"""<table class="scout-table">
                        <thead>
                            <tr>
                                <th>Athlete Name</th>
                                <th>Highest Spring Peak Day</th>
                                <th>Highest Summer Peak Day</th>
                                <th>Summer Practice Avg</th>
                                <th>Peak Volume Shift (%)</th>
                            </tr>
                        </thead>
                        <tbody>"""
                    for _, row in merged_comp.sort_values('Name').iterrows():
                        shft_val = row['Peak Change (%)']
                        shft_color = "color:#28a745; font-weight:bold;" if shft_val >= 0 else "color:#dc3545; font-weight:bold;"
                        tbl_html += f"""
                            <tr>
                                <td style="font-weight:700; text-align:left !important; padding-left:15px;">{row['Name']}</td>
                                <td>{row[target_spring_col]:.1f}</td>
                                <td>{row['Summer Peak']:.1f}</td>
                                <td>{row['Summer Avg']:.1f}</td>
                                <td style="{shft_color}">{shft_val:+.1f}%</td>
                            </tr>"""
                    tab10.markdown(tbl_html + "</tbody></table>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sync Error: {e}")
