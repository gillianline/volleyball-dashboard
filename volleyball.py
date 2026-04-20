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
        cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
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

        
        tabs = st.tabs(["Individual Profile", "Team Gallery", "Match v. Practice", "Position Analysis", "Match Summary", "Phase Analysis", "Practice Planner", "Practice Red Flags-TESTING"])
        session_list = df[['Date', 'Session_Name']].drop_duplicates().sort_values('Date', ascending=False)['Session_Name'].tolist()

        with tabs[0]: # Tab 0: Individual Profile
            c_f1, c_f2 = st.columns(2)
            with c_f1: selected_session = st.selectbox("Practice Selection", session_list, index=0, key="nav_sel_ind")
            with c_f2: pos_f = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_ind")
            
            day_df = df[df['Session_Name'] == selected_session].copy()
            if not day_df.empty:
                curr_date = day_df['Date'].iloc[0]
                dropdown_df = day_df.copy()
                if pos_f != "All Positions": dropdown_df = dropdown_df[dropdown_df['Position'] == pos_f]
                sel_p = st.selectbox("Select Athlete", sorted(dropdown_df['Name'].unique()))
                
                # --- DATA GATHERING ---
                p_full = df[df['Name'] == sel_p]
                # Filter specific session row for the Photo/Position metadata
                p_meta = day_df[day_df['Name'] == sel_p].iloc[0]
                
                # --- SUM LOGIC FOR TABLE ---
                daily_sums = p_full.groupby('Date')[all_metrics].sum().reset_index()
                lb = daily_sums[(daily_sums['Date'] >= curr_date - timedelta(days=30)) & (daily_sums['Date'] <= curr_date)]
                p_today_total = daily_sums[daily_sums['Date'] == curr_date].iloc[0]

                m_rows = ""; total_grade = 0; count = 0
                for k in all_metrics:
                    val, mx, avg = p_today_total[k], lb[k].max(), lb[k].mean()
                    grade = math.ceil((val / mx) * 100) if mx > 0 else 0
                    total_grade += grade; count += 1; diff = (val - avg) / avg if avg != 0 else 0
                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                    arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                    m_rows += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{grade}</td></tr>"
                
                score = math.ceil(total_grade / count) if count > 0 else 0
                
                # --- UI DISPLAY ---
                c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
                with c1: 
                    st.markdown(f'<div style="text-align:center;"><img src="{p_meta["PhotoURL"]}" class="player-photo-large"></div><h3 style="text-align:center;">{p_meta["Name"]}</h3>', unsafe_allow_html=True)
                with c2: 
                    st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today Total</th><th>30d Max Day</th><th>Grade</th></tr></thead><tbody>{m_rows}</tbody></table>', unsafe_allow_html=True)
                with c3: 
                    st.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(score)};">{score}</div></div>', unsafe_allow_html=True)

                # --- READINESS PROFILE (CMJ) ---
                st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
                jc1, jc2 = st.columns([1.5, 3.5])
                p_cmj_hist = cmj_df[(cmj_df['Athlete'] == sel_p) & (cmj_df['Test Date'] <= curr_date)].sort_values('Test Date')
                
                with jc1:
                    sync_cmj = p_cmj_hist[(p_cmj_hist['Test Date'] > curr_date - timedelta(days=7))]
                    
                    # We need at least 2 tests in history to show a "change"
                    if len(p_cmj_hist) >= 2:
                        latest = p_cmj_hist.iloc[-1]   # The most recent test
                        previous = p_cmj_hist.iloc[-2] # The test immediately before it
                        
                        cur_h, cur_rsi = latest['Jump Height (in)'], latest['RSI-modified [m/s]']
                        prev_h, prev_rsi = previous['Jump Height (in)'], previous['RSI-modified [m/s]']
                        
                        # Calculate % change from the previous jump
                        p_diff = ((cur_h - prev_h) / prev_h) * 100 if prev_h > 0 else 0
                        
                        # Status Logic: Compared to the jump right before
                        label, color = ("ELITE", "#28a745") if cur_h >= prev_h and cur_rsi >= prev_rsi else \
                                       ("FATIGUED", "#dc3545") if cur_h < prev_h and cur_rsi < prev_rsi else \
                                       ("GRINDER", "#ffc107")
                        
                        # UI Display
                        st.markdown(f"""
                            <div style="text-align:center;">
                                <div class="score-box" style="background-color:{color}; line-height:1.2; padding-top:15px; height:80px; width:390px;">
                                    <span style="font-size:18px;">{p_diff:+.1f}%</span>
                                    <span style="font-size:10px; display:block; font-weight:bold; margin-top:2px;">{label}</span>
                                </div>
                            </div>
                            <div class="info-box" style="text-align:center; margin-top:10px;">
                                <p style="margin:0; font-size:12px;"><b>Vs. Prev:</b> {prev_h:.1f}" | {prev_rsi:.2f}</p>
                                <p style="margin:0; font-size:13px; color:#4895DB;"><b>Today:</b> {cur_h:.1f}" | {cur_rsi:.2f}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    elif not p_cmj_hist.empty:
                        # Fallback if they only have 1 test ever
                        latest = p_cmj_hist.iloc[-1]
                        st.info(f"First test recorded: {latest['Jump Height (in)']:.1f}\"")
                        
                with jc2:
                    if not p_cmj_hist.empty:
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist['Jump Height (in)'], name="Height", line=dict(color='#FF8200', width=3)), secondary_y=False)
                        fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist['RSI-modified [m/s]'], name="RSI", line=dict(color='#4895DB', dash='dot')), secondary_y=True)
                        fig.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), showlegend=False, template="simple_white")
                        st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG)
                
                # --- PRACTICE PHASE BREAKDOWN ---
                p_ph = phase_df[(phase_df['Name'] == sel_p) & (phase_df['Date'] == curr_date)].copy()
                if not p_ph.empty:
                    st.markdown('<div class="section-header">Practice Phase Breakdown</div>', unsafe_allow_html=True)
                    fig_ph = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_ph.add_trace(go.Bar(x=p_ph['Phase'], y=p_ph['Total Jumps'], name="Jumps", marker_color='#FF8200'), secondary_y=False)
                    fig_ph.add_trace(go.Scatter(x=p_ph['Phase'], y=p_ph['Player Load'], name="Load", line=dict(color='#4895DB', width=4)), secondary_y=False)
                    fig_ph.update_layout(height=350, showlegend=True, template="simple_white", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_ph, use_container_width=True, config=LOCKED_CONFIG)
        with tabs[1]: # Tab 1: Gallery
            c_gal1, c_gal2 = st.columns(2)
            with c_gal1: selected_session_gal = st.selectbox("Practice Selection", session_list, index=0, key="nav_sel_gal")
            with c_gal2: pos_f_gal = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_gal")
            gal_df = df[df['Session_Name'] == selected_session_gal].copy()
            if not gal_df.empty:
                curr_date_gal = gal_df['Date'].iloc[0]
                if pos_f_gal != "All Positions": gal_df = gal_df[gal_df['Position'] == pos_f_gal]
                athlete_names = sorted(gal_df['Name'].unique())
                for i in range(0, len(athlete_names), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(athlete_names):
                            name = athlete_names[i + j]
                            p_full_g = df[df['Name'] == name]
                            daily_sums_g = p_full_g.groupby('Date')[all_metrics].sum().reset_index()
                            lb_g = daily_sums_g[(daily_sums_g['Date'] >= curr_date_gal - timedelta(days=30)) & (daily_sums_g['Date'] <= curr_date_gal)]
                            p_today_g = daily_sums_g[daily_sums_g['Date'] == curr_date_gal].iloc[0]
                            
                            r_html = ""; t_grade = 0; c_metrics = 0
                            for k in all_metrics:
                                v, mx, avg = p_today_g[k], lb_g[k].max(), lb_g[k].mean()
                                g = math.ceil((v / mx) * 100) if mx > 0 else 0
                                t_grade += g; c_metrics += 1; diff = (v - avg) / avg if avg != 0 else 0
                                h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                                arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                                r_html += f"<tr><td>{k}</td><td {h_class}>{v:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"
                            
                            sc_g = math.ceil(t_grade / c_metrics) if c_metrics > 0 else 0
                            p_info = gal_df[gal_df['Name'] == name].iloc[0]
                            with cols[j]: st.markdown(f'<div style="border:1px solid #E5E5E7; border-radius:15px; padding:15px; margin-bottom:20px;"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{p_info["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px;">{name}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Total</th><th>Max Day</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div><div style="flex:1; text-align:center;"><div style="background-color:{get_flipped_gradient(sc_g)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{sc_g}</div></div></div></div>', unsafe_allow_html=True)

        with tabs[2]: # Game v Practice
            st.markdown('<div class="section-header">Weekly Prep Intensity vs. Match Demands</div>', unsafe_allow_html=True)
            c_ga, c_gw, c_gg = st.columns(3)
            with c_ga: gp_p = st.selectbox("Athlete", sorted(df['Name'].unique()), key="gp_p_vf")
            with c_gw:
                w_r = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index(); w_r['L'] = w_r.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1); gp_w = st.selectbox("Week", w_r['L'].tolist(), key="gp_w_vf"); sel_w = w_r[w_r['L'] == gp_w]['Week'].values[0]
            with c_gg: 
                # Games now pull from match_df
                game_opts = match_df[(match_df['Name'] == gp_p) & (match_df['Week'] == sel_w)]['Session_Name'].unique(); gp_g = st.selectbox("Select Specific Match", game_opts, key="gp_g_vf")
            
            w_data = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Practice') & (df['Week'] == sel_w)]; g_data_l = match_df[(match_df['Name'] == gp_p) & (match_df['Session_Name'] == gp_g)]
            
            if not w_data.empty and not g_data_l.empty:
                low_m = ['Total Jumps', 'Player Load', 'Explosive Efforts']; w_avg = w_data[low_m + ['Estimated Distance (y)']].mean(); g_d = g_data_l.iloc[0]; cg1, cg2 = st.columns([1, 2])
                with cg1:
                    for m in low_m + ['Estimated Distance (y)']: st.metric(label=m, value=f"{g_d[m]:.0f}", delta=f"{(w_avg[m]-g_d[m])/g_d[m]*100:+.1f}%")
                with cg2:
                    fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # Primary Metrics (Left Axis)
                    fig_dual.add_trace(go.Bar(x=low_m, y=[w_avg[m] for m in low_m], name="Weekly Avg", marker_color='#4895DB', offsetgroup=1), secondary_y=False)
                    fig_dual.add_trace(go.Bar(x=low_m, y=[g_d[m] for m in low_m], name=f"Match Output", marker_color='#FF8200', offsetgroup=2), secondary_y=False)
                    
                    # Distance Ghost Bars (Right Axis)
                    fig_dual.add_trace(go.Bar(x=['Estimated Distance (y)'], y=[w_avg['Estimated Distance (y)']], name="Wkly Dist", marker=dict(color='#4895DB', opacity=0.3), offsetgroup=1), secondary_y=True)
                    fig_dual.add_trace(go.Bar(x=['Estimated Distance (y)'], y=[g_d['Estimated Distance (y)']], name="Match Dist", marker=dict(color='#FF8200', opacity=0.3), offsetgroup=2), secondary_y=True)
                    
                    fig_dual.update_layout(barmode='group', height=350, margin=dict(l=0, r=0, t=20, b=0), template="simple_white")
                    st.plotly_chart(fig_dual, use_container_width=True, config=LOCKED_CONFIG)
                
                # Trends pull from combined sources to show the full week
                combined_wk = pd.concat([w_data, g_data_l])
                wk_trends = combined_wk.groupby(['Date', 'Session_Name', 'Session_Type']).agg({'Player Load': 'mean'}).reset_index().sort_values('Date'); wk_trends['Day_Label'] = wk_trends['Date'].dt.strftime('%a %m/%d'); fig_tr = go.Figure(); fig_tr.add_trace(go.Scatter(x=wk_trends['Day_Label'], y=wk_trends['Player Load'], mode='lines', line=dict(color='#4895DB', width=3), showlegend=False))
                for s_t, clr in [('Practice', '#4895DB'), ('Match', '#FF8200')]:
                    sub = wk_trends[wk_trends['Session_Type'] == s_t]
                    for _, r in sub.iterrows(): is_sel = (r['Session_Name'] == gp_g); fig_tr.add_trace(go.Scatter(x=[r['Day_Label']], y=[r['Player Load']], name=r['Session_Name'] if s_t == 'Game' else s_t, mode='markers', marker=dict(color=clr, size=16 if is_sel else 10, line=dict(width=3 if is_sel else 1, color='black' if is_sel else 'white')), showlegend=True if s_t == 'Game' else (True if _ == sub.index[0] else False)))
                fig_tr.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0), yaxis_title="Avg Player Load"); st.plotly_chart(fig_tr, use_container_width=True, config=LOCKED_CONFIG)
                
        with tabs[3]: # Position Analysis
            st.markdown('<div class="section-header">Positional Performance Trends</div>', unsafe_allow_html=True)
            
            # --- PRIMARY FILTER ---
            pos_filter_an = st.selectbox("Select Position to Analyze", sorted([p for p in df['Position'].unique() if p != "N/A"]), key="pos_an_filt_main")
            
            max_wk = df['Week'].max()
            rec_4 = list(range(int(max_wk) - 3, int(max_wk) + 1))
            tr_df = df[(df['Week'].isin(rec_4)) & (df['Position'] == pos_filter_an)]
            
            players_in_pos = sorted(tr_df['Name'].unique())
            
            if players_in_pos:
                tr_metrics = ["Player Load", "Estimated Distance (y)", "Total Jumps"]
                pos_4wk_avg = tr_df[tr_metrics].mean()

                for name in players_in_pos:
                    p_data = tr_df[tr_df['Name'] == name]
                    
                    try:
                        correct_photo = df[df['Name'] == name]['PhotoURL'].iloc[0]
                    except:
                        correct_photo = p_data['PhotoURL'].iloc[0]

                    st.markdown(f'<div class="player-row-container" style="padding: 20px; margin-bottom: 30px;">', unsafe_allow_html=True)
                    # Adjusted ratio to give the photo and table more breathing room
                    c_card1, c_card2 = st.columns([1.5, 3], gap="large")
                    
                    with c_card1:
                        # Inline styles to ensure NO cropping/zooming on this specific tab
                        st.markdown(f"""
                            <div style="text-align:center; padding:15px; background:#f8f9fa; border-bottom:2px solid #FF8200; border-radius: 12px;">
                                <img src="{correct_photo}" style="
                                    border-radius: 50%; 
                                    width: 90px; 
                                    height: 90px; 
                                    object-fit: contain; 
                                    background-color: white; 
                                    border: 3px solid #FF8200;
                                    display: block;
                                    margin: 0 auto 10px auto;
                                ">
                                <p style="margin:0; font-weight:900; color:#1D1D1F; font-size:18px;">{name}</p>
                                <p style="margin:0; color:#4895DB; font-weight:700; font-size:13px;">{pos_filter_an}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        p_4wk_avg = p_data[tr_metrics].mean()
                        table_html = f"""
                            <table class="scout-table" style="width:100%; margin-top:15px;">
                                <thead>
                                    <tr><th>Metric</th><th>{name}.</th><th>Position</th></tr>
                                </thead>
                                <tbody>
                                    <tr><td style="font-weight:700;">Player Load</td><td>{p_4wk_avg['Player Load']:.0f}</td><td>{pos_4wk_avg['Player Load']:.0f}</td></tr>
                                    <tr><td style="font-weight:700;">Distance</td><td>{p_4wk_avg['Estimated Distance (y)']:.0f}</td><td>{pos_4wk_avg['Estimated Distance (y)']:.0f}</td></tr>
                                    <tr><td style="font-weight:700;">Total Jumps</td><td>{p_4wk_avg['Total Jumps']:.0f}</td><td>{pos_4wk_avg['Total Jumps']:.0f}</td></tr>
                                </tbody>
                            </table>
                        """
                        st.markdown(table_html, unsafe_allow_html=True)

                    with c_card2:
                        # Aligning the graphs vertically to match the table height
                        st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                        t_cols = st.columns(3)
                        for i, m in enumerate(tr_metrics):
                            with t_cols[i]:
                                fig_t = go.Figure()
                                p_t = p_data.groupby('Week')[m].mean().reset_index()
                                fig_t.add_trace(go.Scatter(x=p_t['Week'], y=p_t[m], name=name, line=dict(color='#4895DB', width=4), mode='lines+markers'))
                                g_t = tr_df.groupby('Week')[m].mean().reset_index()
                                fig_t.add_trace(go.Scatter(x=g_t['Week'], y=g_t[m], name="Avg", line=dict(color='#FF8200', dash='dash', width=2), mode='lines'))
                                
                                fig_t.update_layout(
                                    title=dict(text=f"<b>{m}</b>", font=dict(size=13, color='#4895DB'), x=0.5, xanchor='center'),
                                    xaxis=dict(dtick=1, showgrid=False, title="Week"), 
                                    yaxis=dict(showgrid=True, gridcolor='#F5F5F7'),
                                    height=250, 
                                    margin=dict(l=10, r=10, t=40, b=10), showlegend=False, template="simple_white"
                                )
                                st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                        
        with tabs[4]: # Match Summary
            custom_colors = ['#4895DB', '#FF8200', '#515154', '#A52A2A', '#008080', '#6A1B9A', '#2E7D32']
    
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
                    
                    # --- AUTO-DETECT THE LOAD COLUMN ---
                    # This finds the column even if it has an extra space at the end
                    load_col_matches = next((c for c in ad.columns if "Player Load" in c), None)
                    load_col_phases = next((c for c in phase_df.columns if "Player Load" in c), None)

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
                            val_load = r[load_col_matches] if load_col_matches else 0
                            card_start += f"<tr><td style='font-weight:700; font-size:11px;'>{r['Activity']}</td><td>{int(r['Total Jumps'])}</td><td>{val_load:.0f}</td><td>{r['Explosive Efforts']:.0f}</td></tr>"
                
                        total_j = int(ad['Total Jumps'].sum())
                        total_pl = ad[load_col_matches].sum() if load_col_matches else 0
                        total_ee = ad['Explosive Efforts'].sum()
                
                        card_start += f"<tr style='background:#4895DB; color:white; font-weight:900;'><td>TOTAL</td><td>{total_j}</td><td>{total_pl:.0f}</td><td>{total_ee:.0f}</td></tr></tbody></table></div>"
                        st.markdown(card_start, unsafe_allow_html=True)
            
                    with side_cols[1]:
                        fig_ath = make_subplots(specs=[[{"secondary_y": True}]])
                        for _, r in ad.iterrows():
                            act_color = m_map.get(r['Activity'], '#A52A2A')
                            val_load = r[load_col_matches] if load_col_matches else 0
                            
                            fig_ath.add_trace(go.Bar(
                                name=r['Activity'], x=['Total Jumps', 'Explosive Efforts'], 
                                y=[r['Total Jumps'], r['Explosive Efforts']], 
                                marker_color=act_color, offsetgroup=r['Activity']
                            ), secondary_y=False)
                    
                            fig_ath.add_trace(go.Bar(
                                name=f"Load ({r['Activity']})", x=['Load'], 
                                y=[val_load], 
                                marker=dict(color=act_color, opacity=0.3), 
                                showlegend=False, offsetgroup=r['Activity']
                            ), secondary_y=True)
                
                        fig_ath.update_layout(barmode='group', height=240, margin=dict(l=10, r=10, t=10, b=40), template="simple_white")
                        st.plotly_chart(fig_ath, use_container_width=True, config=LOCKED_CONFIG)

                    # --- THE ACTIVITY-STRICT FILTER ---
                    if 'Activity' in phase_df.columns and load_col_phases:
                        # 1. Narrow down to the specific athlete first
                        p_name = str(name).strip()
                        p_data = phase_df[phase_df['Name'].astype(str).str.strip() == p_name].copy()

                        # 2. We loop through the matches shown in this card (ad)
                        for _, m_row in ad.iterrows():
                            # This is exactly "Match v. EKU 4-18-26"
                            m_id = str(m_row['Activity']).strip()
                            
                            # 3. FILTER: Must have "Set" in Phase AND Activity must match m_id EXACTLY
                            spec_match_sets = p_data[
                                (p_data['Phase'].astype(str).str.contains('Set', case=False, na=False)) & 
                                (p_data['Activity'].astype(str).str.strip() == m_id)
                            ].sort_values('Phase')

                            # 4. Only display if it found sets for THIS SPECIFIC Match ID
                            if not spec_match_sets.empty:
                                with st.expander(f"View Set Breakdown: {m_id}"):
                                    fig_s = px.bar(
                                        spec_match_sets, 
                                        x='Phase', 
                                        y=load_col_phases, 
                                        color='Total Jumps',
                                        title=f"Set-by-Set: {m_id}",
                                        labels={load_col_phases: 'Load', 'Phase': 'Set'},
                                        color_continuous_scale='Reds', 
                                        text='Total Jumps'
                                    )
                                    fig_s.update_traces(textposition='outside')
                                    st.plotly_chart(fig_s, use_container_width=True, config=LOCKED_CONFIG)
                                    
        with tabs[5]: # Tab 5: Work Index Matrix
            st.markdown('<div class="section-header">Practice Phase Volume & Avg Duration</div>', unsafe_allow_html=True)
            
            if phase_df is not None and not phase_df.empty:
                # --- 1. DATA PREPARATION ---
                working_matrix = phase_df.copy()
                time_col = 'Duration'
                
                # Cleaning: Remove hidden spaces
                for col in ['Position', 'Name', 'Phase']:
                    if col in working_matrix.columns:
                        working_matrix[col] = working_matrix[col].astype(str).str.strip()

                # Group Mini Games and other phases
                if 'Phase' in working_matrix.columns:
                    working_matrix['Phase'] = working_matrix['Phase'].replace(phase_map)
                
                # Force Duration to be numeric
                working_matrix[time_col] = pd.to_numeric(working_matrix[time_col], errors='coerce').fillna(0)
                
                # --- 2. CALCULATION LOGIC ---
                # We calculate the "Rate" first, then we will use the Avg Duration to show Total Volume
                index_metrics = ['Player Load', 'Total Jumps', 'Explosive Efforts']
                for m in index_metrics:
                    if m in working_matrix.columns:
                        working_matrix[f'{m}_Rate'] = working_matrix.apply(
                            lambda x: x[m] / x[time_col] if x[time_col] > 0 else 0, axis=1
                        )

                # --- 3. UI FILTERS ---
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    view_mode = st.radio("Table View", ["By Position", "By Individual Player"], horizontal=True, key="wi_volume_view")
                with f_col2:
                    valid_dates = working_matrix['Date'].dropna().unique()
                    date_opts = ["Season Average"] + sorted([d.strftime('%Y-%m-%d') for d in valid_dates], reverse=True)
                    sel_date = st.selectbox("Select Date Scope", date_opts, key="wi_volume_date")

                if sel_date != "Season Average":
                    working_matrix = working_matrix[working_matrix['Date'] == pd.to_datetime(sel_date)]

                # --- 4. AGGREGATION ---
                # We average the Rates and the Duration separately
                rate_cols = [f'{m}_Rate' for m in index_metrics]
                agg_cols = rate_cols + [time_col]
                
                if view_mode == "By Position":
                    mask = (working_matrix['Position'] != 'nan') & (working_matrix['Position'] != '') & (working_matrix['Position'] != 'N/A')
                    matrix_df = working_matrix[mask].groupby(['Position', 'Phase'])[agg_cols].mean().reset_index()
                    sort_col = 'Position'
                else:
                    matrix_df = working_matrix.groupby(['Name', 'Position', 'Phase'])[agg_cols].mean().reset_index()
                    sort_col = 'Name'

                # --- 5. CONVERT RATES BACK TO VOLUME ---
                # This makes the numbers "Total Load" for that duration
                for m in index_metrics:
                    matrix_df[m] = matrix_df[f'{m}_Rate'] * matrix_df[time_col]

                # --- 6. FORMATTING & DISPLAY ---
                display_df = matrix_df[[sort_col, 'Phase', time_col] + index_metrics].rename(columns={
                    'Duration': 'Avg Mins',
                    'Player Load': 'Total Load',
                    'Total Jumps': 'Total Jumps',
                    'Explosive Efforts': 'Total Efforts'
                })

                display_df = display_df.sort_values([sort_col, 'Phase'])

                def style_table(styler):
                    # Show as whole numbers (integers)
                    styler.format({
                        'Avg Mins': '{:.0f}',
                        'Total Load': '{:.0f}', 
                        'Total Jumps': '{:.0f}', 
                        'Total Efforts': '{:.0f}'
                    })
                    return styler

                st.dataframe(
                    display_df.style.pipe(style_table),
                    use_container_width=True,
                    hide_index=True,
                    height=600
                )

            else:
                st.warning("No data found in the Phases sheet.")
                
        with tabs[6]: # Practice Planner
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
                    
                    # Focus metrics (Removed Distance from logic)
                    plan_metrics = ['Player Load', 'Total Jumps', 'Explosive Efforts']
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
                    # Only show the Total Projection Box if we are NOT in Team Overall mode
                    if plan_level != "Team Overall":
                        target_rates = planner_target_df.groupby('Phase')[[f'{m}_Rate' for m in plan_metrics]].mean().reset_index()
                        t_build = target_rates.set_index('Phase').loc[selected_build].reset_index()
                        
                        total_pl = sum(durations[p] * t_build[t_build['Phase'] == p]['Player Load_Rate'].iloc[0] for p in selected_build)
                        total_j = sum(durations[p] * t_build[t_build['Phase'] == p]['Total Jumps_Rate'].iloc[0] for p in selected_build)
                        total_ee = sum(durations[p] * t_build[t_build['Phase'] == p]['Explosive Efforts_Rate'].iloc[0] for p in selected_build)
                        total_time = sum(durations.values())

                        st.markdown(f"### Practice Projection: {display_label}")
                        st.markdown('<div style="background:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #E5E5E7;">', unsafe_allow_html=True)
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Total Time", f"{total_time:.0f} min")
                        m2.metric("Proj. Load", f"{total_pl:.1f}")
                        m3.metric("Proj. Jumps", f"{int(total_j)}")
                        m4.metric("Proj. Efforts", f"{int(total_ee)}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    # --- 5. INDIVIDUAL BREAKDOWN (Crucial for Team View) ---
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
                                    'Proj. Efforts': int(a_totals['Explosive Efforts'])
                                })
                        
                        if ath_projections:
                            proj_df = pd.DataFrame(ath_projections).sort_values('Proj. Load', ascending=False)
                            st.dataframe(proj_df, use_container_width=True, hide_index=True)

                    # --- 6. INTENSITY FLOW GRAPH (Removed Distance) ---
                    st.markdown("#### Practice Intensity Flow (Rate per Minute)")
                    # Re-calculating rates for the graph target
                    graph_rates = planner_target_df.groupby('Phase')[[f'{m}_Rate' for m in plan_metrics]].mean().reset_index()
                    g_build = graph_rates.set_index('Phase').loc[selected_build].reset_index()

                    fig_flow = go.Figure()
                    colors = {'Player Load': '#515154', 'Total Jumps': '#FF8200', 'Explosive Efforts': '#A52A2A'}

                    for m in plan_metrics:
                        fig_flow.add_trace(go.Scatter(
                            x=g_build['Phase'], y=g_build[f'{m}_Rate'], 
                            name=m, mode='lines+markers',
                            line=dict(color=colors[m], width=3, shape='spline'),
                            marker=dict(size=8)
                        ))
                    
                    fig_flow.update_layout(
                        height=400, template="simple_white",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(l=10, r=10, t=30, b=10),
                        yaxis_title="Intensity per Minute"
                    )
                    st.plotly_chart(fig_flow, use_container_width=True, config=LOCKED_CONFIG)
                else:
                    st.info(f"Select drills to visualize the intensity flow for {display_label}.")
            else:
                st.warning("No phase data detected.")
                
        with tabs[7]: # Risk Monitor
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
                
    except Exception as e:
        st.error(f"Sync Error: {e}")
