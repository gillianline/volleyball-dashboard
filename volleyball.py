import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

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
    # Initialize print state
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
        score = float(score)
        return "#2D5A27" if score <= 40 else "#D4A017" if score <= 70 else "#A52A2A"    

    @st.cache_data(ttl=10)
    def load_all_data():
        # Load Primary Sheet
        df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
        df.columns = df.columns.str.strip()
        df['Sheet_Order'] = range(len(df))
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']) 

        # Load New Matches Sheet
        match_df = pd.read_csv(st.secrets["MATCHES_SHEET_URL"])
        match_df.columns = match_df.columns.str.strip()
        match_df['Sheet_Order'] = range(len(match_df))
        match_df['Date'] = pd.to_datetime(match_df['Date'], errors='coerce')
        match_df = match_df.dropna(subset=['Date'])

        rename_map = {
            'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps', 'IMA Jump Count High Band': 'High Jumps', 
            'BMP Jumping Load': 'Jump Load', 'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance (y)', 
            'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movement'
        }

        # Process both sheets
        for frame in [df, match_df]:
            frame.rename(columns=rename_map, inplace=True)
            if 'Week' in frame.columns:
                frame['Week'] = pd.to_numeric(frame['Week'].astype(str).str.extract('(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
            avail = [v for v in rename_map.values() if v in frame.columns]
            for col in avail: frame[col] = pd.to_numeric(frame[col], errors='coerce').fillna(0).round(1)
            frame['Session_Name'] = frame['Activity'].fillna(frame['Date'].dt.strftime('%m/%d/%Y'))
            frame['Position'] = frame.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
            frame['PhotoURL'] = frame.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
            frame['Session_Type'] = frame['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')

        cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
        cmj_df.columns = cmj_df.columns.str.strip()
        cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
        
        phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
        phase_df.columns = phase_df.columns.str.strip()
        if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
        phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
        phase_df = phase_df.rename(columns=rename_map)
        
        try:
            thresh_df = pd.read_csv(st.secrets["THRESH_SHEET_URL"])
            thresh_df.columns = thresh_df.columns.str.strip()
        except:
            thresh_df = None
        
        # UPDATE THE RETURN TO INCLUDE thresh_df
        return df, match_df, cmj_df, phase_df, thresh_df

    LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

    try:
        # UPDATE THIS LINE TO INCLUDE thresh_df
        df, match_df, cmj_df, phase_df, thresh_df = load_all_data()

        phase_map = {
                "Mini Games (Set 1)": "Mini Games", 
                "Mini Games (Set 2)": "Mini Games",
                "Brizo (2)": "Brizo",
                "2 Ball (Set 1)": "2 Ball", "2 Ball (Set 2)": "2 Ball", 
                "2 Ball (Set 3)": "2 Ball", "2 Ball (Set 4)": "2 Ball",
                "serving (2)": "Serving", "serving": "Serving", "Serving (2)": "Serving",
                "2/3 Hitters (2)": "2/3 Hitters", "5v5 (2)": "5v5",
                "Serve & Pass": "Serve and Pass"
            }
        
        all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
        
        st.markdown('<div class="main-logo-container" style="text-align: center; margin-top: 10px; margin-bottom: 15px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120"><div style="color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;">LADY VOLS VOLLEYBALL PERFORMANCE</div></div>', unsafe_allow_html=True)

        
        tabs = st.tabs(["Individual Profile", "Practice Scores", "Practice Score History", "Counter Movement Jumps", "Match v. Practice", "Match Summary", "Position Analysis", "Phase Analysis", "Practice Planner", "Practice Red Flags-TESTING"])
        raw_sessions = df[df['Session_Name'].notna()]
        session_list = raw_sessions.sort_values('Date', ascending=False)['Session_Name'].unique().tolist()

        with tabs[0]: # Tab 0: Individual Profile
            c_prof1, c_prof2 = st.columns(2)
            with c_prof1:
                selected_session_prof = st.selectbox("Session Selection", session_list, index=0, key="nav_sel_prof")
            with c_prof2:
                all_athletes = sorted(df['Name'].unique())
                selected_athlete_prof = st.selectbox("Athlete Selection", all_athletes, key="nav_ath_prof")

            p_session_data = df[(df['Name'] == selected_athlete_prof) & (df['Session_Name'] == selected_session_prof)]

            if not p_session_data.empty:
                p_row = p_session_data.iloc[0]
                curr_date_prof = p_row['Date']
                p_meta = p_row 

                # --- BASELINE LOGIC FOR THE GRAPH ---
                p_full_prof = df[df['Name'] == selected_athlete_prof]
                week_4_data = p_full_prof[p_full_prof['Week'] == 4]
                baseline_jump_val = week_4_data['Total Jumps'].max() if not week_4_data.empty else 0

                # 30-Day History for Score Card (Back to Original)
                daily_sums_prof = p_full_prof.groupby('Date')[all_metrics].sum().reset_index()
                lb_prof = daily_sums_prof[(daily_sums_prof['Date'] >= pd.to_datetime(curr_date_prof) - timedelta(days=30)) & 
                                          (daily_sums_prof['Date'] <= pd.to_datetime(curr_date_prof))]

                metrics_to_exclude = ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']
                filtered_metrics_prof = [m for m in all_metrics if m not in metrics_to_exclude]

                r_html_prof = ""; t_grade_prof = 0; c_metrics_prof = 0
                for k in filtered_metrics_prof:
                    val, mx, avg = p_row[k], lb_prof[k].max(), lb_prof[k].mean()
                    g = math.ceil((val / mx) * 100) if mx > 0 else 0
                    t_grade_prof += g
                    c_metrics_prof += 1
                    diff = (val - avg) / avg if avg != 0 else 0
                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                    arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                    r_html_prof += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"

                sc_prof = math.ceil(t_grade_prof / c_metrics_prof) if c_metrics_prof > 0 else 0
                
                # --- UI DISPLAY: TOP CARD (REVERTED) ---
                c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
                with c1: 
                    st.markdown(f'<div style="text-align:center;"><img src="{p_meta["PhotoURL"]}" class="player-photo-large"></div><h3 style="text-align:center;">{p_meta["Name"]}</h3>', unsafe_allow_html=True)
                with c2: 
                    st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today Total</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>{r_html_prof}</tbody></table>', unsafe_allow_html=True)
                with c3: 
                    st.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(sc_prof)};">{sc_prof}</div></div><p style="text-align:center; font-weight:bold; color:grey; margin-top:10px;">SESSION SCORE</p>', unsafe_allow_html=True)

                # --- READINESS PROFILE (BASELINE COMPARISON) ---
                st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
                jc1, jc2 = st.columns([1.5, 3.5])
                
                p_cmj_hist = cmj_df[(cmj_df['Athlete'] == selected_athlete_prof) & (cmj_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
                cmj_col = 'Jump Height (Imp-Mom) [cm]'
                week_4_cmj = cmj_df[(cmj_df['Athlete'] == selected_athlete_prof) & (cmj_df['Week'] == 4)]
                
                with jc1:
                    if not week_4_cmj.empty and not p_cmj_hist.empty:
                        baseline_row = week_4_cmj.iloc[-1]
                        base_h, base_rsi = baseline_row[cmj_col], baseline_row['RSI-modified [m/s]']
                        
                        latest = p_cmj_hist.iloc[-1]
                        cur_h, cur_rsi = latest[cmj_col], latest['RSI-modified [m/s]']
                        
                        p_diff_base = ((cur_h - base_h) / base_h) * 100 if base_h > 0 else 0
                        
                        # --- Readiness Logic ---
                        if cur_h >= base_h and cur_rsi >= base_rsi:
                            label, color = "ELITE", "#28a745"
                            desc = "Performing above baseline in both height and efficiency."
                        elif cur_h < base_h and cur_rsi < base_rsi:
                            label, color = "FATIGUED", "#dc3545"
                            desc = "Performing below baseline both height and efficiency."
                        else:
                            label, color = "GRINDER", "#ffc107"
                            desc = "ixed performance. Athlete is working hard but efficiency is inconsistent."
                        
                        st.markdown(f"""
                            <div style="text-align:center;">
                                <div class="score-box" style="background-color:{color}; line-height:1.2; padding-top:15px; height:80px; width:100%;">
                                    <span style="font-size:18px;">{p_diff_base:+.1f}%</span>
                                    <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">Vs. Baseline</span>
                                    <span style="font-size:12px; display:block; font-weight:900;">{label}</span>
                                </div>
                            </div>
                            <div style="margin-top:15px; padding:10px; background:#f8f9fa; border-radius:8px; border-left:4px solid {color};">
                                <p style="margin:0; font-size:11px; color:#555; line-height:1.4;"><b>{label}:</b> {desc}</p>
                            </div>
                            <div class="info-box" style="text-align:center; margin-top:10px; border: 1px solid #E5E5E7; border-radius:10px; padding:5px;">
                                <p style="margin:0; font-size:12px; color:grey;"><b>Baseline:</b> {base_h:.1f} cm | {base_rsi:.2f}</p>
                                <p style="margin:0; font-size:13px; color:#FF8200;"><b>Today:</b> {cur_h:.1f} cm | {cur_rsi:.2f}</p>
                            </div>
                        """, unsafe_allow_html=True)

                with jc2:
                    if not p_cmj_hist.empty:
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        
                        # 1. Current Jumps Path
                        fig.add_trace(go.Scatter(
                            x=p_cmj_hist['Test Date'], y=p_cmj_hist[cmj_col], 
                            name="Current Height", 
                            line=dict(color='#FF8200', width=3)
                        ), secondary_y=False)
                        
                        # 2. RSI Path
                        fig.add_trace(go.Scatter(
                            x=p_cmj_hist['Test Date'], y=p_cmj_hist['RSI-modified [m/s]'], 
                            name="RSI (m/s)", 
                            line=dict(color='#4895DB', dash='dot')
                        ), secondary_y=True)

                        fig.update_layout(
                            height=320, 
                            margin=dict(l=0, r=0, t=20, b=0), 
                            showlegend=True,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
                            template="simple_white"
                        )
                        st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG, key=f"readiness_final_clean_{selected_athlete_prof}")
                        
        with tabs[1]: # Tab 1: Gallery
            c_gal1, c_gal2 = st.columns(2)
            with c_gal1: 
                selected_session_gal = st.selectbox("Practice Selection", session_list, index=0, key="nav_sel_gal")
            with c_gal2: 
                pos_f_gal = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_gal")
            
            # Filter main data to the specific session selected in the dropdown
            gal_df = df[df['Session_Name'] == selected_session_gal].copy()
            
            if not gal_df.empty:
                curr_date_gal = gal_df['Date'].iloc[0]
                
                # Apply Position Filter
                display_df = gal_df.copy()
                if pos_f_gal != "All Positions": 
                    display_df = display_df[display_df['Position'] == pos_f_gal]
                
                athlete_names = sorted(display_df['Name'].unique())
                
                # Metric filtering setup
                metrics_to_exclude = ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']
                filtered_metrics_gal = [m for m in all_metrics if m not in metrics_to_exclude]

                for i in range(0, len(athlete_names), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(athlete_names):
                            name = athlete_names[i + j]
                            
                            # 1. Get the RAW row for THIS specific athlete in THIS specific session
                            # This prevents multiple matches on the same day from being summed together
                            p_session_row = display_df[display_df['Name'] == name].iloc[0]
                            
                            # 2. Get the athlete's full history for baseline calculations
                            p_full_g = df[df['Name'] == name]
                            
                            # We calculate the "Max Day" using daily sums (the athlete's peak 1-day output)
                            daily_sums_g = p_full_g.groupby('Date')[all_metrics].sum().reset_index()
                            lb_sums = daily_sums_g[(daily_sums_g['Date'] >= curr_date_gal - timedelta(days=30)) & 
                                                   (daily_sums_g['Date'] <= curr_date_gal)]
                            
                            r_html = ""; t_grade = 0; c_metrics = 0
                            
                            # 3. Loop through metrics to build the table
                            for k in filtered_metrics_gal:
                                val = p_session_row[k] # Specific session value
                                mx = lb_sums[k].max()  # 30-day peak day value
                                avg = lb_sums[k].mean() # 30-day average day
                                
                                # Grade relative to their 30-day max
                                g = math.ceil((val / mx) * 100) if mx > 0 else 0
                                t_grade += g
                                c_metrics += 1
                                
                                # Comparison logic for red highlight/arrows
                                diff = (val - avg) / avg if avg != 0 else 0
                                h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                                arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                                
                                r_html += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"
                            
                            # Final Grade for the card
                            sc_g = math.ceil(t_grade / c_metrics) if c_metrics > 0 else 0
                            
                            # 4. Display the Card
                            with cols[j]: 
                                st.markdown(f"""
                                    <div style="border:1px solid #E5E5E7; border-radius:15px; padding:15px; margin-bottom:20px; background-color:white;">
                                        <div style="display:flex; align-items:center; gap:10px;">
                                            <div style="flex:1.2; text-align:center;">
                                                <img src="{p_session_row["PhotoURL"]}" class="gallery-photo">
                                                <p style="font-weight:bold; font-size:15px; margin-top:8px; color:#333;">{name}</p>
                                            </div>
                                            <div style="flex:3;">
                                                <table class="scout-table">
                                                    <thead>
                                                        <tr>
                                                            <th>Metric</th>
                                                            <th>Today Total</th>
                                                            <th>30d Max</th>
                                                            <th>Grade</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {r_html}
                                                    </tbody>
                                                </table>
                                            </div>
                                            <div style="flex:1; text-align:center;">
                                                <div style="background-color:{get_flipped_gradient(sc_g)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">
                                                    {sc_g}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
            else:
                st.info("No data found for the selected session.")
                
        with tabs[4]: # Tab 4: Game v Practice
            st.markdown('<div class="section-header">Preparation Intensity vs. Match Demands</div>', unsafe_allow_html=True)
            
            # --- 1. DYNAMIC FILTERS ---
            c_mode, c_sel, c_week, c_match = st.columns(4)
            with c_mode:
                view_mode = st.radio("View Level", ["Team", "Position", "Individual"], horizontal=True, key="gp_view_mode")
            
            with c_sel:
                if view_mode == "Individual":
                    gp_p = st.selectbox("Select Athlete", sorted(df['Name'].unique()), key="gp_p_vf")
                    main_filtered = df[df['Name'] == gp_p].copy()
                    match_filtered = match_df[match_df['Name'] == gp_p].copy()
                elif view_mode == "Position":
                    gp_pos = st.selectbox("Select Position Group", sorted(df['Position'].unique()), key="gp_pos_vf")
                    main_filtered = df[df['Position'] == gp_pos].copy()
                    match_filtered = match_df[match_df['Position'] == gp_pos].copy()
                else:
                    main_filtered = df.copy()
                    match_filtered = match_df.copy()

            # --- 2. DATA STANDARDIZATION ---
            def clean_gp_data(target_df):
                if target_df.empty: return target_df
                rename_map = {'Player Load': 'Total Player Load', 'PlayerLoad': 'Total Player Load'}
                target_df = target_df.rename(columns=rename_map)
                cols = ['Total Player Load', 'Explosive Efforts', 'Total Jumps', 'Duration', 'Estimated Distance (y)']
                for c in cols:
                    if c in target_df.columns:
                        target_df[c] = pd.to_numeric(target_df[c], errors='coerce').fillna(0)
                return target_df

            main_filtered = clean_gp_data(main_filtered)
            match_filtered = clean_gp_data(match_filtered)

            # --- 3. SEASON OVERALL STANDARDS ---
            st.markdown("### Season Standards: Overall Intensity")
            if not main_filtered.empty and not match_filtered.empty:
                s_metrics = {'Total Player Load': 'Load', 'Explosive Efforts': 'Expl.', 'Total Jumps': 'Jumps', 'Estimated Distance (y)': 'Dist'}
                s_calc = list(s_metrics.keys())
                s_prac = main_filtered[main_filtered['Session_Type'] == 'Practice']
                s_p_avg = s_prac[s_calc + ['Duration']].mean()
                s_m_avg = match_filtered[s_calc + ['Duration']].mean()
                
                overall_html = """<table style="width:100%; border-collapse: collapse; text-align: center; margin-bottom: 20px;">
                                <tr style="background-color: #31333F; color: white; font-weight: bold;">
                                    <th style="padding: 12px; border: 1px solid #ddd;">Metric (Rate/Min)</th>
                                    <th style="padding: 12px; border: 1px solid #ddd;">Season Practice Avg</th>
                                    <th style="padding: 12px; border: 1px solid #ddd;">Season Match Avg</th>
                                    <th style="padding: 12px; border: 1px solid #ddd;">% Match Intensity</th>
                                </tr>"""
                for m, label in s_metrics.items():
                    p_rate = s_p_avg[m] / (s_p_avg['Duration'] if s_p_avg['Duration'] > 0 else 1)
                    m_rate = s_m_avg[m] / (s_m_avg['Duration'] if s_m_avg['Duration'] > 0 else 1)
                    perc = (p_rate / m_rate * 100) if m_rate > 0 else 0
                    color = "#28a745" if perc >= 85 else "#dc3545"
                    overall_html += f"<tr><td><b>{label}</b></td><td>{p_rate:.2f}</td><td>{m_rate:.2f}</td><td style='color:{color}; font-weight:bold;'>{perc:.1f}%</td></tr>"
                st.markdown(overall_html + "</table>", unsafe_allow_html=True)

                with st.expander("ℹ️ How is Match Intensity Calculated? (Coaches' Guide)"):
                    st.markdown("#### 1. The Core Formula: 'The Work Index'\nIntensity is calculated as a **Rate per Minute**. `[Total Volume] / [Duration] = Rate/Min`.")

            st.divider()

            # --- 4. NEW MULTI-MATCH AGGREGATION LOGIC ---
            with c_week:
                w_r = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index()
                w_r['L'] = w_r.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1)
                gp_w = st.selectbox("Select Week", w_r['L'].tolist(), key="gp_w_vf")
                sel_w = w_r[w_r['L'] == gp_w]['Week'].values[0]

            with c_match:
                # Group match_filtered by DATE to catch multiple sessions in one day
                if not match_filtered.empty:
                    daily_matches = match_filtered[match_filtered['Week'] == sel_w].groupby('Date').agg({
                        'Session_Name': lambda x: " + ".join(x.unique())
                    }).reset_index()
                    daily_matches['Display'] = daily_matches.apply(lambda x: f"{x['Date'].strftime('%m/%d')}: {x['Session_Name']}", axis=1)
                    sel_match_display = st.selectbox("Select Match Date", daily_matches['Display'].tolist(), key="gp_g_vf")
                    sel_match_date = daily_matches[daily_matches['Display'] == sel_match_display]['Date'].values[0]
                else:
                    sel_match_date = None

            w_data = main_filtered[(main_filtered['Session_Type'] == 'Practice') & (main_filtered['Week'] == sel_w)].copy()
            g_data_raw = match_filtered[match_filtered['Date'] == sel_match_date].copy()

            if not w_data.empty and not g_data_raw.empty:
                metrics_dict = {'Total Player Load': 'Player Load', 'Explosive Efforts': 'Expl. Efforts', 'Total Jumps': 'Total Jumps', 'Estimated Distance (y)': 'Distance (y)'}
                calc_cols = list(metrics_dict.keys())
                
                # Combine multiple matches into one "Daily Game Load"
                g_combined = g_data_raw.groupby('Date').agg({col: 'sum' for col in calc_cols + ['Duration']}).iloc[0]
                g_name_label = " + ".join(g_data_raw['Session_Name'].unique())
                
                w_avg = w_data[calc_cols + ['Duration']].mean()

                # --- 5. REDESIGNED VOLUME CARDS ---
                st.markdown(f"### Combined Match Volume: {g_name_label}")
                m_cols = st.columns(4)
                for i, (raw_col, label) in enumerate(metrics_dict.items()):
                    with m_cols[i]:
                        match_val, prac_avg = g_combined[raw_col], w_avg[raw_col]
                        delta = match_val - prac_avg
                        st.markdown(f"""<div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid #FF8200; text-align: center;">
                            <p style="margin: 0; font-size: 14px; color: #555;">{label}</p>
                            <h2 style="margin: 5px 0;">{match_val:.0f}</h2>
                            <p style="margin: 0; font-weight: bold; color: {'#dc3545' if delta > 0 else '#28a745'};">{'+' if delta > 0 else ''}{delta:.0f} vs Practice</p>
                        </div>""", unsafe_allow_html=True)

                # --- 6. INTENSITY TABLE ---
                st.markdown("#### Intensity Density (Work Rate)")
                week_html = """<table style="width:100%; border-collapse: collapse; text-align: center;">
                                <tr style="background-color: #f0f2f6; font-weight: bold;">
                                    <th style="padding: 10px; border: 1px solid #ddd;">Metric (Rate/Min)</th>
                                    <th style="padding: 10px; border: 1px solid #ddd;">Match Rate</th>
                                    <th style="padding: 10px; border: 1px solid #ddd;">Practice Rate</th>
                                    <th style="padding: 10px; border: 1px solid #ddd;">% Intensity</th>
                                </tr>"""
                for m in calc_cols:
                    m_r = g_combined[m] / (g_combined['Duration'] if g_combined['Duration'] > 0 else 1)
                    p_r = w_avg[m] / (w_avg['Duration'] if w_avg['Duration'] > 0 else 1)
                    perc = (p_r / m_r * 100) if m_r > 0 else 0
                    color = "#28a745" if perc >= 90 else ("#FF8200" if perc >= 75 else "#dc3545")
                    week_html += f"<tr><td><b>{metrics_dict[m]}</b></td><td>{m_r:.2f}</td><td>{p_r:.2f}</td><td style='color:{color}; font-weight:bold;'>{perc:.1f}%</td></tr>"
                st.markdown(week_html + "</table><br>", unsafe_allow_html=True)

                # --- 7. TRENDS ---
                combined_wk = pd.concat([w_data, g_data_raw])
                wk_trends = combined_wk.groupby(['Date']).agg({m: 'sum' for m in calc_cols}).reset_index().sort_values('Date')
                wk_trends['Day'] = wk_trends['Date'].dt.strftime('%a %m/%d')
                
                fig_tr = go.Figure()
                fig_tr.add_trace(go.Scatter(x=wk_trends['Day'], y=wk_trends['Total Player Load'], mode='lines+markers', name="Player Load", line=dict(color='#4895DB', width=3)))
                fig_tr.add_trace(go.Scatter(x=wk_trends['Day'], y=wk_trends['Total Jumps'], mode='lines+markers', name="Total Jumps", line=dict(color='#FF8200', width=2, dash='dot')))
                fig_tr.update_layout(height=350, template="simple_white", legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"))
                st.plotly_chart(fig_tr, use_container_width=True)
            else:
                st.info("Missing data for the current selection.")
                

                # --- 6. VISUAL BARS (Now full width for better scaling) ---
                fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
                bar_m = ['Total Player Load', 'Explosive Efforts', 'Total Jumps']
                
                # Weekly Practice Bars
                fig_dual.add_trace(go.Bar(
                    x=[metrics_dict[m] for m in bar_m], 
                    y=[w_avg[m] for m in bar_m], 
                    name="Practice Average", 
                    marker_color='#4895DB', 
                    offsetgroup=1
                ), secondary_y=False)
                
                # Match Output Bars
                fig_dual.add_trace(go.Bar(
                    x=[metrics_dict[m] for m in bar_m], 
                    y=[g_avg[m] for m in bar_m], 
                    name="Match Output", 
                    marker_color='#FF8200', 
                    offsetgroup=2
                ), secondary_y=False)
                
                # Distance Overlay
                fig_dual.add_trace(go.Bar(
                    x=['Distance (y)'], 
                    y=[w_avg['Estimated Distance (y)']], 
                    name="Prac. Distance", 
                    marker=dict(color='#4895DB', opacity=0.3), 
                    offsetgroup=1
                ), secondary_y=True)
                
                fig_dual.add_trace(go.Bar(
                    x=['Distance (y)'], 
                    y=[g_avg['Estimated Distance (y)']], 
                    name="Match Distance", 
                    marker=dict(color='#FF8200', opacity=0.3), 
                    offsetgroup=2
                ), secondary_y=True)

                fig_dual.update_layout(
                    barmode='group', 
                    height=400, 
                    template="simple_white", 
                    legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_dual, use_container_width=True)
                

                # 7. MULTI-LINE TREND WITH LEGEND
                st.markdown("#### Load Progression (Practice to Match)")
                combined_wk = pd.concat([w_data, g_data_l])
                wk_trends = combined_wk.groupby(['Date', 'Session_Name']).agg({'Total Player Load': 'mean', 'Total Jumps': 'mean', 'Explosive Efforts': 'mean'}).reset_index().sort_values('Date')
                wk_trends['Day'] = wk_trends['Date'].dt.strftime('%a %m/%d')
                
                fig_tr = go.Figure()
                fig_tr.add_trace(go.Scatter(x=wk_trends['Day'], y=wk_trends['Total Player Load'], mode='lines+markers', name="Player Load", line=dict(color='#4895DB', width=3)))
                fig_tr.add_trace(go.Scatter(x=wk_trends['Day'], y=wk_trends['Total Jumps'], mode='lines+markers', name="Total Jumps", line=dict(color='#FF8200', width=2, dash='dot')))
                fig_tr.add_trace(go.Scatter(x=wk_trends['Day'], y=wk_trends['Explosive Efforts'], mode='lines+markers', name="Explosive Efforts", line=dict(color='#28a745', width=2, dash='dash')))
                fig_tr.update_layout(height=400, template="simple_white", legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"))
                st.plotly_chart(fig_tr, use_container_width=True)
            else:
                st.info("Missing practice or match data for the current selection.")
                  
                
        with tabs[6]: # Position Analysis
            st.markdown('<div class="section-header">Positional Performance Trends</div>', unsafe_allow_html=True)
            
            pos_filter_an = st.selectbox("Select Position to Analyze", sorted([p for p in df['Position'].unique() if p != "N/A"]), key="pos_an_filt_main")
            
            max_wk = df['Week'].max()
            rec_4 = list(range(int(max_wk) - 3, int(max_wk) + 1))
            tr_df = df[(df['Week'].isin(rec_4)) & (df['Position'] == pos_filter_an)]
            
            players_in_pos = sorted(tr_df['Name'].unique())
            
            if players_in_pos:
                tr_metrics = ["Player Load", "Estimated Distance (y)", "Explosive Efforts", "Total Jumps"]
                pos_4wk_avg = tr_df[tr_metrics].mean()

                for name in players_in_pos:
                    p_data = tr_df[tr_df['Name'] == name]
                    p_4wk_avg = p_data[tr_metrics].mean()

                    # --- FIXED: TABLE IS NOW INSIDE THE SAME MARKDOWN BLOCK AS THE PHOTO/DIV ---
                    # This prevents Streamlit from injecting a "bar" (gutter) between the elements.
                    c_card1, c_card2 = st.columns([1.5, 3], gap="large")
                    
                    with c_card1:
                        # Combine everything (Div Start + Photo + Name + Table) into one single call
                        profile_and_table_html = f"""
                            <div class="player-row-container" style="padding: 20px; border: 1px solid #E5E5E7; border-radius:15px; background:white; margin-bottom: 0px;">
                                <div style="text-align:center; padding:15px; background:#f8f9fa; border-bottom:2px solid #FF8200; border-radius: 12px;">
                                    <img src="{p_data["PhotoURL"].iloc[0]}" style="border-radius: 50%; width: 90px; height: 90px; object-fit: contain; background-color: white; border: 3px solid #FF8200; display: block; margin: 0 auto 10px auto;">
                                    <p style="margin:0; font-weight:900; color:#1D1D1F; font-size:18px;">{name}</p>
                                </div>
                                <table class="scout-table" style="width:100%; margin-top:15px;">
                                    <thead>
                                        <tr><th>Metric</th><th>{name[:20]}</th><th>Pos. Avg</th></tr>
                                    </thead>
                                    <tbody>
                                        <tr><td style="font-weight:700;">Player Load</td><td>{p_4wk_avg['Player Load']:.0f}</td><td>{pos_4wk_avg['Player Load']:.0f}</td></tr>
                                        <tr><td style="font-weight:700;">Est. Dist (y)</td><td>{p_4wk_avg['Estimated Distance (y)']:.0f}</td><td>{pos_4wk_avg['Estimated Distance (y)']:.0f}</td></tr>
                                        <tr><td style="font-weight:700;">Explosive</td><td>{p_4wk_avg['Explosive Efforts']:.0f}</td><td>{pos_4wk_avg['Explosive Efforts']:.0f}</td></tr>
                                        <tr><td style="font-weight:700;">Total Jumps</td><td>{p_4wk_avg['Total Jumps']:.0f}</td><td>{pos_4wk_avg['Total Jumps']:.0f}</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        """
                        st.markdown(profile_and_table_html, unsafe_allow_html=True)

                    with c_card2:
                        # Keep your graphs exactly as they were
                        st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                        t_cols = st.columns(2) 
                        for i, m in enumerate(tr_metrics):
                            col_idx = i % 2
                            with t_cols[col_idx]:
                                fig_t = go.Figure()
                                p_t = p_data.groupby('Week')[m].mean().reset_index()
                                fig_t.add_trace(go.Scatter(x=p_t['Week'], y=p_t[m], name="Athlete", line=dict(color='#4895DB', width=4), mode='lines+markers'))
                                g_t = tr_df.groupby('Week')[m].mean().reset_index()
                                fig_t.add_trace(go.Scatter(x=g_t['Week'], y=g_t[m], name="Pos. Avg", line=dict(color='#FF8200', dash='dash', width=2), mode='lines'))
                                
                                fig_t.update_layout(
                                    title=dict(text=f"<b>{m}</b>", font=dict(size=12), x=0.5),
                                    xaxis=dict(dtick=1, showgrid=False, title="Week"), 
                                    yaxis=dict(showgrid=True, gridcolor='#F5F5F7'),
                                    height=220, margin=dict(l=10, r=10, t=30, b=40),
                                    showlegend=True, legend=dict(orientation="h", y=-0.6, x=0.5, xanchor="center"),
                                    template="simple_white"
                                )
                                st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG, key=f"trend_{name}_{m}")
                    
                    # Add a small vertical space between athletes, but not inside the card
                    st.write("<div style='height: 30px;'></div>", unsafe_allow_html=True)
                    
        with tabs[5]: # Match Summary
            custom_colors = [
                '#4895DB', # Blue
                '#FF8200', # Orange
                '#515154', # Grey
                '#A52A2A', # Brown/Red
                '#008080', # Teal
                '#6A1B9A', # Purple
                '#2E7D32'  # Green
            ]
    
            if st.session_state.is_printing:
                if st.button("Back to Editor (Show Filters)"):
                    st.session_state.is_printing = False
                    st.rerun()
            else:
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                if st.button("Prepare PDF for Printing"):
                    st.session_state.is_printing = True
                    st.rerun()
                st.markdown('<div class="section-header">Match Comparison Selection</div>', unsafe_allow_html=True)
                c_ts1, c_ts2 = st.columns([2, 1])
                with c_ts1:
                    match_list_t = match_df.sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique()
                    if "matches_state" not in st.session_state: 
                        st.session_state.matches_state = match_list_t[-3:] if len(match_list_t) >=3 else match_list_t
                    st.session_state.matches_state = st.multiselect("Select Matches", match_list_t, default=st.session_state.matches_state)
                with c_ts2:
                    if "pos_state" not in st.session_state: st.session_state.pos_state = "All Positions"
                    st.session_state.pos_state = st.selectbox("Filter by Position", ["All Positions"] + sorted(list(match_df['Position'].unique())), index=0)
                st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.is_printing:
                st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

            selected_matches = st.session_state.get("matches_state", [])
            pos_filter_t = st.session_state.get("pos_state", "All Positions")

            if selected_matches:
                m_map = {m: custom_colors[idx % len(custom_colors)] for idx, m in enumerate(selected_matches)}
                st.markdown('<div class="section-header">Athlete Match Performance Breakdown</div>', unsafe_allow_html=True)
        
                tourney_df = match_df[match_df['Session_Name'].isin(selected_matches)].sort_values(['Date', 'Sheet_Order'])
                if pos_filter_t != "All Positions": 
                    tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]

                for name in sorted(tourney_df['Name'].unique()):
                    ad = tourney_df[tourney_df['Name'] == name]
            
                    try:
                        correct_photo = df[df['Name'] == name]['PhotoURL'].iloc[0]
                    except:
                        correct_photo = "https://www.w3schools.com/howto/img_avatar.png"
            
                    st.markdown(f'<div class="player-row-container"><div class="player-divider"></div>', unsafe_allow_html=True)
                    side_cols = st.columns([1.5, 2])
                    
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
                        st.markdown(card_start, unsafe_allow_html=True)
            
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
                        st.plotly_chart(fig_ath, use_container_width=True, config=LOCKED_CONFIG)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    
        with tabs[7]: # Tab 5: Work Index Matrix
            st.markdown('<div class="section-header">Work Index Matrix & Drill Utilization</div>', unsafe_allow_html=True)
            
            if phase_df is not None and not phase_df.empty:
                # --- 1. DATA PREPARATION ---
                working_matrix = phase_df.copy()
                for col in ['Position', 'Name', 'Phase']:
                    if col in working_matrix.columns:
                        working_matrix[col] = working_matrix[col].astype(str).str.strip()
                if 'Phase' in working_matrix.columns:
                    working_matrix['Phase'] = working_matrix['Phase'].replace(phase_map)

                # --- 2. DRILL FREQUENCY TABLE ---
                st.markdown("### Drill Frequency")
                drill_stats = working_matrix.groupby('Phase')['Number of Times'].sum().reset_index()
                drill_stats = drill_stats.sort_values('Number of Times', ascending=False)
                
                freq_html = """<table style="width:100%; border-collapse: collapse; text-align: center;">
                                <tr style="background-color: #f0f2f6; font-weight: bold;">
                                    <th style="padding: 8px; border: 1px solid #ddd;">Drill/Phase</th>
                                    <th style="padding: 8px; border: 1px solid #ddd;">Frequency</th>
                                </tr>"""
                for _, row in drill_stats.iterrows():
                    freq_html += f"""<tr>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{row['Phase']}</td>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{row['Number of Times']:.0f}</td>
                                  </tr>"""
                freq_html += "</table>"
                st.markdown(freq_html, unsafe_allow_html=True)

                # --- 3. CALCULATION LOGIC ---
                time_col, index_metrics = 'Duration', ['Player Load', 'Total Jumps', 'Explosive Efforts']
                working_matrix[time_col] = pd.to_numeric(working_matrix[time_col], errors='coerce').fillna(0)
                
                for m in index_metrics:
                    working_matrix[f'{m}_Rate'] = working_matrix.apply(
                        lambda x: x[m] / x[time_col] if x[time_col] > 0 else 0, axis=1
                    )

                # --- 4. UI FILTERS ---
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1:
                    view_mode = st.radio("Group By", ["Position", "Individual"], horizontal=True, key="wi_view")
                    metric_mode = st.radio("Data Mode", ["Work Index (per minute)", "Total Volume"], horizontal=True, key="wi_mode")
                with f_col2:
                    if view_mode == "Position":
                        pos_list = ["All Positions"] + sorted([p for p in working_matrix['Position'].unique() if p not in ["nan", "N/A"]])
                        sel_sub_filter = st.selectbox("Select Position", pos_list)
                        if sel_sub_filter != "All Positions":
                            working_matrix = working_matrix[working_matrix['Position'] == sel_sub_filter]
                    else:
                        player_list = ["All Players"] + sorted(working_matrix['Name'].unique())
                        sel_sub_filter = st.selectbox("Select Player", player_list)
                        if sel_sub_filter != "All Players":
                            working_matrix = working_matrix[working_matrix['Name'] == sel_sub_filter]
                with f_col3:
                    valid_dates = working_matrix['Date'].dropna().unique()
                    date_opts = ["Season Avg"] + sorted([d.strftime('%Y-%m-%d') for d in valid_dates], reverse=True)
                    sel_date = st.selectbox("Select Date", date_opts, key="wi_volume_date")

                if sel_date != "Season Avg":
                    working_matrix = working_matrix[working_matrix['Date'] == pd.to_datetime(sel_date)]

                # --- 5. AGGREGATION & HEADER LOGIC ---
                rate_cols = [f'{m}_Rate' for m in index_metrics]
                group_keys = ['Position', 'Phase'] if view_mode == "Position" else ['Name', 'Position', 'Phase']
                matrix_df = working_matrix.groupby(group_keys)[rate_cols + [time_col]].mean().reset_index()

                # --- NEW HEADER LOGIC ---
                if metric_mode == "Total Volume":
                    h_load, h_jumps, h_expl = "Total Load", "Total Jumps", "Total Efforts"
                    fmt = "{:.0f}"
                else:
                    h_load, h_jumps, h_expl = "Player Load/Min", "Jumps/Min", "Explosive Efforts/Min"
                    fmt = "{:.2f}"

                # --- 6. MANUAL HTML TABLE ---
                st.markdown(f"### {metric_mode}")
                sort_col = 'Position' if view_mode == "Position" else 'Name'
                matrix_df = matrix_df.sort_values([sort_col, 'Phase'])

                matrix_html = f"""<table style="width:100%; border-collapse: collapse; text-align: center;">
                                <tr style="background-color: #f0f2f6; font-weight: bold;">
                                    <th style="padding: 8px; border: 1px solid #ddd;">{sort_col}</th>
                                    <th style="padding: 8px; border: 1px solid #ddd;">Phase</th>
                                    <th style="padding: 8px; border: 1px solid #ddd;">Mins</th>
                                    <th style="padding: 8px; border: 1px solid #ddd;">{h_load}</th>
                                    <th style="padding: 8px; border: 1px solid #ddd;">{h_jumps}</th>
                                    <th style="padding: 8px; border: 1px solid #ddd;">{h_expl}</th>
                                </tr>"""

                for _, row in matrix_df.iterrows():
                    # Math check
                    load_val = (row['Player Load_Rate'] * row[time_col]) if metric_mode == "Total Volume" else row['Player Load_Rate']
                    jump_val = (row['Total Jumps_Rate'] * row[time_col]) if metric_mode == "Total Volume" else row['Total Jumps_Rate']
                    expl_val = (row['Explosive Efforts_Rate'] * row[time_col]) if metric_mode == "Total Volume" else row['Explosive Efforts_Rate']

                    matrix_html += f"""<tr>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{row[sort_col]}</td>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{row['Phase']}</td>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{row[time_col]:.1f}</td>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{fmt.format(load_val)}</td>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{fmt.format(jump_val)}</td>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{fmt.format(expl_val)}</td>
                                  </tr>"""
                matrix_html += "</table>"
                st.markdown(matrix_html, unsafe_allow_html=True)
                
                
        with tabs[8]: # Practice Planner
            st.markdown('<div class="section-header">Practice Phase Analysis & Planner</div>', unsafe_allow_html=True)
            
            if phase_df is not None and not phase_df.empty:
                # --- 1. DATA PREPARATION ---
                working_planner = phase_df.copy()
                time_col = 'Duration' 
                
                if time_col not in working_planner.columns:
                    st.error(f"Column '{time_col}' not found. Please add a 'Duration' column to your Phases sheet.")
                else:
                    working_planner['Phase'] = working_planner['Phase'].replace(phase_map)
                    working_planner = working_planner[working_planner[time_col] > 0].dropna(subset=[time_col])
                    
                    # --- ADDED: Estimated Distance (y) to metrics ---
                    plan_metrics = ['Player Load', 'Total Jumps', 'Explosive Efforts', 'Estimated Distance (y)']
                    for m in plan_metrics:
                        working_planner[f'{m}_Rate'] = working_planner[m] / working_planner[time_col]

                # --- 2. HIERARCHICAL SELECTORS ---
                s_col1, s_col2 = st.columns(2)
                with s_col1:
                    plan_level = st.radio("Select Planning Level", ["Team Overall", "By Position", "By Athlete"], horizontal=True, key="planner_level_refined")
                
                if plan_level == "Team Overall":
                    planner_target_df = working_planner.copy()
                    display_label = "Team Overall"
                elif plan_level == "By Position":
                    with s_col2:
                        pos_choice = st.selectbox("Select Position", sorted([p for p in working_planner['Position'].unique() if pd.notna(p)]), key="planner_pos_refined")
                    planner_target_df = working_planner[working_planner['Position'] == pos_choice]
                    display_label = f"Position: {pos_choice}"
                else:
                    with s_col2:
                        ath_choice = st.selectbox("Select Athlete", sorted(working_planner['Name'].unique()), key="planner_ath_refined")
                    planner_target_df = working_planner[working_planner['Name'] == ath_choice]
                    display_label = f"Athlete: {ath_choice}"

                # --- 3. DRILL SELECTION ---
                available_phases = sorted(planner_target_df['Phase'].unique())
                selected_build = st.multiselect(f"Select Drills for {display_label}", available_phases, key="planner_multi_refined")

                if selected_build:
                    # Duration Inputs
                    phase_stats = planner_target_df.groupby('Phase').agg({time_col: 'mean'}).reset_index()
                    build_stats = phase_stats[phase_stats['Phase'].isin(selected_build)]
                    
                    st.write("Set planned drill durations (minutes):")
                    dur_cols = st.columns(min(len(selected_build), 4))
                    durations = {}
                    for idx, phase in enumerate(selected_build):
                        with dur_cols[idx % 4]:
                            avg_t = build_stats[build_stats['Phase'] == phase][time_col].iloc[0]
                            durations[phase] = st.number_input(f"{phase}", value=float(round(avg_t, 0)), step=1.0, key=f"dur_ref_{phase}")

                    # --- 4. DISPLAY RESULTS ---
                    if plan_level != "Team Overall":
                        target_rates = planner_target_df.groupby('Phase')[[f'{m}_Rate' for m in plan_metrics]].mean().reset_index()
                        t_build = target_rates.set_index('Phase').loc[selected_build].reset_index()
                        
                        total_pl = sum(durations[p] * t_build[t_build['Phase'] == p]['Player Load_Rate'].iloc[0] for p in selected_build)
                        total_j = sum(durations[p] * t_build[t_build['Phase'] == p]['Total Jumps_Rate'].iloc[0] for p in selected_build)
                        total_ee = sum(durations[p] * t_build[t_build['Phase'] == p]['Explosive Efforts_Rate'].iloc[0] for p in selected_build)
                        # Added Distance Projection
                        total_dist = sum(durations[p] * t_build[t_build['Phase'] == p]['Estimated Distance (y)_Rate'].iloc[0] for p in selected_build)
                        total_time = sum(durations.values())

                        st.markdown(f"### Practice Projection: {display_label}")
                        st.markdown('<div style="background:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #E5E5E7;">', unsafe_allow_html=True)
                        m1, m2, m3, m4, m5 = st.columns(5) # Expanded to 5 columns
                        m1.metric("Total Time", f"{total_time:.0f} min")
                        m2.metric("Proj. Load", f"{total_pl:.1f}")
                        m3.metric("Proj. Jumps", f"{int(total_j)}")
                        m4.metric("Proj. Efforts", f"{int(total_ee)}")
                        m5.metric("Proj. Dist (y)", f"{int(total_dist)}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    # --- 5. INDIVIDUAL BREAKDOWN ---
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
                                    for m in plan_metrics:
                                        a_totals[m] += durations[phase] * p_rate[f'{m}_Rate'].iloc[0]
                            
                            if sum(a_totals.values()) > 0:
                                ath_projections.append({
                                    'Athlete': athlete,
                                    'Proj. Load': round(a_totals['Player Load'], 1),
                                    'Proj. Jumps': int(a_totals['Total Jumps']),
                                    'Proj. Efforts': int(a_totals['Explosive Efforts']),
                                    'Proj. Dist (y)': int(a_totals['Estimated Distance (y)'])
                                })
                        
                        if ath_projections:
                            proj_df = pd.DataFrame(ath_projections).sort_values('Proj. Load', ascending=False)
                            st.dataframe(proj_df, use_container_width=True, hide_index=True)

                    # --- 6. INTENSITY FLOW GRAPH (Dual Axis for Distance) ---
                    st.markdown("#### Practice Intensity Flow (Rate per Minute)")
                    graph_rates = planner_target_df.groupby('Phase')[[f'{m}_Rate' for m in plan_metrics]].mean().reset_index()
                    g_build = graph_rates.set_index('Phase').loc[selected_build].reset_index()

                    # Create figure with secondary y-axis
                    fig_flow = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    colors = {
                        'Player Load': '#515154', 
                        'Total Jumps': '#FF8200', 
                        'Explosive Efforts': '#A52A2A',
                        'Estimated Distance (y)': '#4895DB' 
                    }

                    for m in plan_metrics:
                        # Distance goes on the secondary axis
                        is_distance = (m == 'Estimated Distance (y)')
                        
                        fig_flow.add_trace(
                            go.Scatter(
                                x=g_build['Phase'], 
                                y=g_build[f'{m}_Rate'], 
                                name=f"{m} (Right Axis)" if is_distance else m, 
                                mode='lines+markers',
                                line=dict(color=colors[m], width=3, shape='spline'),
                                marker=dict(size=8)
                            ),
                            secondary_y=is_distance
                        )
                    
                    fig_flow.update_layout(
                        height=450, 
                        template="simple_white",
                        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
                        margin=dict(l=10, r=10, t=50, b=10),
                        xaxis_title="Practice Phase"
                    )

                    # Label the axes appropriately
                    fig_flow.update_yaxes(title_text="Load / Jumps / Efforts", secondary_y=False)
                    fig_flow.update_yaxes(title_text="Yards per Minute", secondary_y=True, showgrid=False)
                    
                    st.plotly_chart(fig_flow, use_container_width=True, config=LOCKED_CONFIG)
                    
                
        with tabs[9]: # Risk Monitor
            st.markdown('<div class="section-header">Practice Risk Monitor</div>', unsafe_allow_html=True)
            
            if phase_df is not None and thresh_df is not None:
                # --- 1. SETUP THRESHOLDS ---
                c1, c2 = st.columns(2)
                
                working_risk = phase_df.copy()
                working_risk['Position'] = working_risk['Position'].str.strip()
                t_lookup = thresh_df.copy()
                t_lookup['Position'] = t_lookup['Position'].str.strip()

                with c1:
                    sel_day = st.selectbox("Select Training Day", t_lookup['Day'].unique(), key="risk_day_v4")
                
                day_thresh = t_lookup[t_lookup['Day'] == sel_day]
                
                with c2:
                    sel_pos = st.selectbox("Select Position Group", day_thresh['Position'].unique(), key="risk_pos_v4")

                active_limits = day_thresh[day_thresh['Position'] == sel_pos].iloc[0]
                L_LIM, J_LIM = active_limits['Load_Limit'], active_limits['Jump_Limit']

                st.info(f"Targeting {sel_day} Limits -- Max Load: {int(L_LIM)} | Max Jumps: {int(J_LIM)}")

                # --- 2. DATA PREP ---
                time_col = 'Duration'
                if time_col not in working_risk.columns:
                    st.error(f"Missing '{time_col}' column in Phases sheet.")
                else:
                    working_risk['Phase'] = working_risk['Phase'].replace(phase_map)
                    working_risk = working_risk[working_risk[time_col] > 0].dropna(subset=[time_col])
                    
                    risk_metrics = ['Player Load', 'Total Jumps', 'Explosive Efforts']
                    for m in risk_metrics:
                        working_risk[f'{m}_Rate'] = working_risk[m] / working_risk[time_col]

                    # --- 3. DRILL SELECTION ---
                    all_phases = sorted(working_risk['Phase'].unique())
                    selected_drills = st.multiselect("Select Drills for the Session", all_phases, key="risk_drills_v4")

                    if selected_drills:
                        st.write("Set Minutes per Drill:")
                        d_cols = st.columns(min(len(selected_drills), 5))
                        durations = {}
                        avg_durs = working_risk.groupby('Phase')[time_col].mean()

                        for idx, phase in enumerate(selected_drills):
                            with d_cols[idx % 5]:
                                def_t = float(round(avg_durs.get(phase, 10.0), 0))
                                durations[phase] = st.number_input(f"{phase}", value=def_t, step=1.0, key=f"risk_dur_v4_{phase}")

                        # --- 4. CALCULATE PROJECTIONS ---
                        if sel_pos == "Team Overall":
                            target_risk_df = working_risk.copy()
                        else:
                            target_risk_df = working_risk[working_risk['Position'] == sel_pos]

                        if target_risk_df.empty:
                            st.warning(f"No athletes found with the position name '{sel_pos}'.")
                        else:
                            ath_rates = target_risk_df.groupby(['Name', 'Phase'])[[f'{m}_Rate' for m in risk_metrics]].mean().reset_index()
                            
                            ath_projections = []
                            for athlete in sorted(target_risk_df['Name'].unique()):
                                a_data = ath_rates[ath_rates['Name'] == athlete]
                                a_totals = {m: 0.0 for m in risk_metrics}
                                
                                for phase in selected_drills:
                                    p_rate = a_data[a_data['Phase'] == phase]
                                    if not p_rate.empty:
                                        for m in risk_metrics:
                                            a_totals[m] += durations[phase] * p_rate[f'{m}_Rate'].iloc[0]
                                
                                if sum(a_totals.values()) > 0:
                                    status = "CLEAR"
                                    # Use int() here for clean comparison logic
                                    if int(a_totals['Player Load']) >= L_LIM or int(a_totals['Total Jumps']) >= J_LIM:
                                        status = "WATCH"

                                    ath_projections.append({
                                        'Athlete': athlete,
                                        'Status': status,
                                        # Convert all to integers for the list
                                        'Proj. Load': int(round(a_totals['Player Load'], 0)),
                                        'Proj. Jumps': int(round(a_totals['Total Jumps'], 0)),
                                        'Proj. Efforts': int(round(a_totals['Explosive Efforts'], 0))
                                    })

                            # --- 5. RENDER THE TABLE ---
                            if ath_projections:
                                proj_df = pd.DataFrame(ath_projections).sort_values('Proj. Load', ascending=False)
                                
                                def apply_risk_styles(row):
                                    styles = [''] * len(row)
                                    if row['Status'] == "WATCH":
                                        styles[proj_df.columns.get_loc('Athlete')] = 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
                                        styles[proj_df.columns.get_loc('Status')] = 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
                                    
                                    if row['Proj. Load'] >= L_LIM:
                                        styles[proj_df.columns.get_loc('Proj. Load')] = 'color: #cc0000; font-weight: 900; border: 1px solid red;'
                                    if row['Proj. Jumps'] >= J_LIM:
                                        styles[proj_df.columns.get_loc('Proj. Jumps')] = 'color: #cc0000; font-weight: 900; border: 1px solid red;'
                                    return styles

                                # Display with no decimal points
                                st.dataframe(
                                    proj_df.style.apply(apply_risk_styles, axis=1).format({
                                        'Proj. Load': '{:d}', 
                                        'Proj. Jumps': '{:d}', 
                                        'Proj. Efforts': '{:d}'
                                    }), 
                                    use_container_width=True, 
                                    hide_index=True
                                )
                                
                                watch_list = proj_df[proj_df['Status'] == "WATCH"]['Athlete'].tolist()
                                if watch_list:
                                    st.error(f"Action Needed: {', '.join(watch_list)} are projected to exceed limits for {sel_day}.")
                            else:
                                st.info("Drills selected, but no historical data matches this position for these specific drills.")
            else:
                st.warning("Please ensure 'Phases' and 'Thresholds' sheets are properly loaded.")

                
        with tabs[2]: # Performance History
            st.markdown('<div class="section-header">Season History & Team Weekly Review</div>', unsafe_allow_html=True)
            
            sub_tabs = st.tabs(["Individual Weekly Review", "Team Weekly Review"])
            metrics_to_score = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]

            # ---------------------------------------------------------
            # SUB-TAB 1: INDIVIDUAL SEASON PATH
            # ---------------------------------------------------------
            with sub_tabs[0]:
                all_athletes = sorted(df['Name'].unique())
                sel_ath_hist = st.selectbox("Select Athlete", all_athletes, key="master_ath_sel")
                
                # Data Preparation (Daily Totals)
                p_full = df[df['Name'] == sel_ath_hist].copy()
                p_full['Date'] = pd.to_datetime(p_full['Date'])
                
                # Group raw data to handle multiple matches per day
                daily_raw = p_full.groupby(['Date', 'Week'])[metrics_to_score].sum().reset_index()
                
                # Dynamic Naming (Match Name or "Match Day")
                display_names = []
                for idx, row in daily_raw.iterrows():
                    orig = p_full[p_full['Date'] == row['Date']]
                    if len(orig) > 1:
                        display_names.append(f"Match Day {row['Date'].strftime('%m/%d')}")
                    else:
                        display_names.append(orig['Session_Name'].iloc[0])
                daily_raw['Display'] = display_names
                
                # Calculate Scores
                scores_list = []
                for idx, row in daily_raw.iterrows():
                    row_grades = []
                    lb = daily_raw[(daily_raw['Date'] >= row['Date'] - timedelta(days=30)) & (daily_raw['Date'] <= row['Date'])]
                    for m in metrics_to_score:
                        mx = lb[m].max()
                        row_grades.append(math.ceil((row[m] / mx) * 100) if mx > 0 else 0)
                    scores_list.append({
                        'Date': row['Date'], 'Display': row['Display'], 
                        'Score': round(sum(row_grades)/len(row_grades), 1), 
                        'Week': str(row['Week']) # String for categorical comparison
                    })
                
                master_df = pd.DataFrame(scores_list).sort_values('Date')

                # A. Master Timeline (The Long Graph)
                st.markdown("### Full Season")
                fig_master = px.line(master_df, x='Display', y='Score', markers=True, text='Score', range_y=[0, 145])

                # --- VERTICAL LINES LOGIC ---
                # We loop through the master_df indices to find where the Week changes
                for i in range(1, len(master_df)):
                    if master_df.iloc[i]['Week'] != master_df.iloc[i-1]['Week']:
                        # Add the dashed line at the half-way point between sessions
                        fig_master.add_vline(
                            x=i-0.5, 
                            line_dash="dash", 
                            line_color="#515154", 
                            opacity=0.4,
                            line_width=1
                        )
                        # Add the "Week X" label at the top
                        fig_master.add_annotation(
                            x=i-0.5, 
                            y=135, 
                            text=f"Week {master_df.iloc[i]['Week']}", 
                            showarrow=False, 
                            font=dict(color="#515154", size=10),
                            bgcolor="white",
                            bordercolor="#E5E5E7",
                            borderwidth=1
                        )

                fig_master.update_traces(
                    line=dict(color='#FF8200', width=3), 
                    marker=dict(size=10, color='#4895DB', line=dict(width=2, color='white')),
                    textposition='top center'
                )
                
                fig_master.update_layout(
                    template="simple_white", 
                    height=480, 
                    xaxis=dict(type='category', title="Session / Match Day", tickangle=-45),
                    yaxis=dict(title="Daily Practice Score", showgrid=True, gridcolor="#f5f5f5"),
                    margin=dict(l=10, r=10, t=50, b=100)
                )
                
                # Chart with unique key
                st.plotly_chart(fig_master, use_container_width=True, config=LOCKED_CONFIG, key=f"master_full_{sel_ath_hist}")
                
                st.markdown("---")
                st.markdown("### Weekly Progressions")
                unique_weeks = sorted(master_df['Week'].unique(), key=int, reverse=True)
                for w_val in unique_weeks:
                    w_data = master_df[master_df['Week'] == w_val]
                    st.subheader(f"Week {w_val}")
                    fig_w = px.line(w_data, x='Display', y='Score', markers=True, text='Score', range_y=[0, 115])
                    fig_w.update_traces(line=dict(color='#FF8200', width=4), marker=dict(size=12, color='#4895DB'), textposition='top center')
                    fig_w.update_layout(height=350, template="simple_white", xaxis=dict(type='category'))
                    
                    # ADDED DYNAMIC KEY HERE
                    st.plotly_chart(fig_w, use_container_width=True, key=f"week_chart_{sel_ath_hist}_{w_val}")

            # ---------------------------------------------------------
            # SUB-TAB 2: TEAM WEEKLY REVIEW
            # ---------------------------------------------------------
            with sub_tabs[1]:
                avail_weeks = sorted(df['Week'].unique(), reverse=True)
                sel_week = st.selectbox("Select Week", avail_weeks, key="team_week_sel")
                
                week_df = df[df['Week'] == sel_week].copy()
                week_df['Date'] = pd.to_datetime(week_df['Date'])
                ath_names = sorted(week_df['Name'].unique())
                
                for i in range(0, len(ath_names), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(ath_names):
                            name = ath_names[i+j]
                            p_all = df[df['Name'] == name].copy()
                            p_all['Date'] = pd.to_datetime(p_all['Date'])
                            
                            p_daily = p_all.groupby(['Date', 'Week'])[metrics_to_score].sum().reset_index()
                            w_daily = p_daily[p_daily['Week'].astype(str) == str(sel_week)].sort_values('Date')
                            
                            card_scores = []
                            for _, r in w_daily.iterrows():
                                r_grades = []
                                lb = p_daily[(p_daily['Date'] >= r['Date'] - timedelta(days=30)) & (p_daily['Date'] <= r['Date'])]
                                for m in metrics_to_score:
                                    mx = lb[m].max()
                                    r_grades.append(math.ceil((r[m] / mx) * 100) if mx > 0 else 0)
                                
                                orig_day = p_all[p_all['Date'] == r['Date']]
                                label = f"Match Day {r['Date'].strftime('%m/%d')}" if len(orig_day) > 1 else orig_day['Session_Name'].iloc[0]
                                card_scores.append({'Display': label, 'Score': round(sum(r_grades)/len(r_grades), 0)})
                            
                            p_meta = p_all.iloc[0]
                            with cols[j]:
                                st.markdown(f"""
                                <div style="border:1px solid #E5E5E7; border-top:4px solid #FF8200; border-radius:10px 10px 0 0; padding:10px; background:white;">
                                    <div style="display:flex; align-items:center; gap:12px;">
                                        <img src="{p_meta["PhotoURL"]}" style="width:45px; height:45px; border-radius:50%;">
                                        <p style="margin:0; font-weight:900; font-size:16px;">{name}</p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                fig_p = px.line(pd.DataFrame(card_scores), x='Display', y='Score', markers=True, text='Score', range_y=[0, 115])
                                fig_p.update_traces(line=dict(color='#FF8200', width=3), marker=dict(size=8, color='#4895DB'), textposition='top center')
                                fig_p.update_layout(height=220, margin=dict(l=20, r=20, t=30, b=20), template="simple_white", xaxis=dict(type='category', title=None))
                                
                                # ADDED DYNAMIC KEY HERE
                                st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False}, key=f"team_card_{name}_{sel_week}")


        with tabs[3]: # Tab 7: CMJ Comparison
            st.markdown('<div class="section-header">CMJ Baseline vs. Post-Match Recovery</div>', unsafe_allow_html=True)
            
            if cmj_df is not None and not cmj_df.empty:
                # --- 1. SELECTION FILTERS ---
                all_ath_cmj = sorted(cmj_df['Athlete'].unique())
                sel_ath_cmj = st.selectbox("Select Athlete", all_ath_cmj, key="cmj_tab_ath")
                
                ath_cmj_data = cmj_df[cmj_df['Athlete'] == sel_ath_cmj].sort_values('Test Date')
                baseline_cmj = ath_cmj_data[ath_cmj_data['Week'] == 4]
                
                # Filter for jumps occurring after the Week 4 baseline
                post_match_cmj = ath_cmj_data[ath_cmj_data['Week'] > 4] 

                if not baseline_cmj.empty:
                    base_row = baseline_cmj.iloc[-1]
                    cmj_col = 'Jump Height (Imp-Mom) [cm]'
                    rsi_col = 'RSI-modified [m/s]'
                    
                    # --- 2. SUMMARY METRICS ---
                    st.markdown("### Performance vs. Week 4 Baseline")
                    latest_post = post_match_cmj.iloc[-1] if not post_match_cmj.empty else None
                    
                    if latest_post is not None:
                        h_diff = ((latest_post[cmj_col] - base_row[cmj_col]) / base_row[cmj_col]) * 100
                        rsi_diff = ((latest_post[rsi_col] - base_row[rsi_col]) / base_row[rsi_col]) * 100
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Wk 4 Baseline", f"{base_row[cmj_col]:.1f} cm")
                        m2.metric("Latest Jump", f"{latest_post[cmj_col]:.1f} cm", f"{h_diff:+.1f}%")
                        m3.metric("RSI Recovery", f"{latest_post[rsi_col]:.2f}", f"{rsi_diff:+.1f}%")

                    # --- 3. COMPARISON TABLE ---
                    st.markdown("#### Jump History & Match Context")
                    comparison_list = []
                    for _, row in post_match_cmj.iterrows():
                        jump_date = pd.to_datetime(row['Test Date'])
                        try:
                            prev_matches = df[(df['Name'] == sel_ath_cmj) & 
                                              (df['Date'] < jump_date) & 
                                              (df['Session_Name'].str.contains('Match|Game', case=False, na=False))]
                            prev_match_name = prev_matches.sort_values('Date', ascending=False).iloc[0]['Session_Name']
                        except:
                            prev_match_name = "N/A"

                        diff_val = row[cmj_col] - base_row[cmj_col]
                        comparison_list.append({
                            "Date": jump_date.strftime('%m/%d/%Y'),
                            "Prev Match": prev_match_name,
                            "Jump Height": f"{row[cmj_col]:.1f} cm",
                            "Vs. Baseline": f"{diff_val:+.1f} cm",
                            "RSI": f"{row[rsi_col]:.2f}"
                        })
                    
                    # Manual Centered Table
                    cmj_table_html = """<table style="width:100%; border-collapse: collapse; text-align: center;">
                                        <tr style="background-color: #f0f2f6; font-weight: bold;">
                                            <th style="padding: 10px; border: 1px solid #ddd;">Jump Date</th>
                                            <th style="padding: 10px; border: 1px solid #ddd;">Previous Match</th>
                                            <th style="padding: 10px; border: 1px solid #ddd;">Jump Height</th>
                                            <th style="padding: 10px; border: 1px solid #ddd;">Vs. Baseline</th>
                                            <th style="padding: 10px; border: 1px solid #ddd;">RSI</th>
                                        </tr>"""
                    for item in comparison_list:
                        val_float = float(item['Vs. Baseline'].replace(' cm', ''))
                        color = "#28a745" if val_float >= 0 else "#dc3545"
                        cmj_table_html += f"""<tr>
                            <td style="padding: 10px; border: 1px solid #ddd;">{item['Date']}</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{item['Prev Match']}</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{item['Jump Height']}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: {color};">{item['Vs. Baseline']}</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{item['RSI']}</td>
                        </tr>"""
                    st.markdown(cmj_table_html + "</table>", unsafe_allow_html=True)

                    # --- 4. DUAL-AXIS RECOVERY TRENDLINE ---
                    st.markdown("#### Recovery Trends (Height vs. RSI)")
                    from plotly.subplots import make_subplots
                    
                    # Create subplots with a secondary y-axis
                    fig_cmj = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # Jump Height Trace (Primary Y-Axis)
                    fig_cmj.add_trace(go.Scatter(
                        x=ath_cmj_data['Test Date'], 
                        y=ath_cmj_data[cmj_col], 
                        name="Jump Height (cm)", 
                        line=dict(color='#4895DB', width=3),
                        mode='lines+markers'
                    ), secondary_y=False)
                    
                    # RSI Trace (Secondary Y-Axis)
                    fig_cmj.add_trace(go.Scatter(
                        x=ath_cmj_data['Test Date'], 
                        y=ath_cmj_data[rsi_col], 
                        name="RSI-mod", 
                        line=dict(color='#FF8200', width=2, dash='dot'),
                        mode='lines+markers'
                    ), secondary_y=True)
                    
                    # Baseline Line
                    fig_cmj.add_hline(y=base_row[cmj_col], line_dash="dash", line_color="red")
                    
                    fig_cmj.update_layout(
                        height=400, 
                        template="simple_white", 
                        margin=dict(l=10, r=10, t=30, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                        xaxis=dict(title="Date", tickformat="%m/%d/%Y")
                    )

                    # Labels for both axes
                    fig_cmj.update_yaxes(title_text="<b>Height (cm)</b>", color="#4895DB", secondary_y=False)
                    fig_cmj.update_yaxes(title_text="<b>RSI-mod</b>", color="#FF8200", secondary_y=True)
                    
                    st.plotly_chart(fig_cmj, use_container_width=True, key="cmj_dual_trend")
                else:
                    st.warning(f"No Week 4 Baseline data found for {sel_ath_cmj}.")
                
    except Exception as e:
        st.error(f"Sync Error: {e}")
