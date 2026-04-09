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
        .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
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

    I have updated the code to handle multiple sessions per day by grouping by date and athlete name, then summing the metrics. This ensures that if an athlete has a lift and a practice on the same day, they are combined into one "Daily Total" for both today's values and the 30-day Max calculation.

I have also ensured that the Max is pulled from the full 30-day window (ignoring position filters) to keep your grades accurate to your Excel sheet.

Python
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
    # --- CSS: FORMATTING & PAGE BREAK CONTROLS ---
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; color: #1D1D1F; }
        hr { display: none !important; }
        .block-container { padding-top: 2rem !important; }
        .viewerBadge_link__1S137, .main_heading_anchor__m6v0K, a.header-anchor { display: none !important; }
        header a { display: none !important; }
        .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
        .scout-table th { background-color: #4895DB; color: white; padding: 6px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 14px; text-transform: uppercase; }
        .scout-table td { padding: 6px; border-bottom: 1px solid #F5F5F7; font-size: 14px; color: #1D1D1F; }
        .bg-highlight-red { background-color: #ffcccc !important; font-weight: 900; }
        .arrow-red { color: #b30000 !important; font-weight: 900; margin-left: 4px; }
        .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
        .score-box { padding: 12px 20px; border-radius: 12px; font-size: 28px; font-weight: 800; min-width: 100px; color: #FFFFFF; line-height: 1.2; text-align: center;}
        .info-box { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 12px; margin-top: 10px; font-size: 12px; color: #1D1D1F; font-weight: 600; line-height: 1.4; }
        .section-header { font-size: 24px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 20px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
        .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
        </style>
        """, unsafe_allow_html=True)

    def get_flipped_gradient(score):
        score = float(score); return "#2D5A27" if score <= 40 else "#D4A017" if score <= 70 else "#A52A2A"

    @st.cache_data(ttl=300)
    def load_all_data():
        df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
        df.columns = df.columns.str.strip()
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']) 
        rename_map = {
            'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps', 'IMA Jump Count High Band': 'High Jumps', 
            'BMP Jumping Load': 'Jump Load', 'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance (y)', 
            'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movement'
        }
        df = df.rename(columns=rename_map)
        all_metrics = list(rename_map.values())
        for col in [c for c in all_metrics if c in df.columns]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
        df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
        df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
        
        cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
        cmj_df.columns = cmj_df.columns.str.strip()
        cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
        cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
        
        phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
        phase_df.columns = phase_df.columns.str.strip()
        phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
        phase_df = phase_df.rename(columns=rename_map)
        return df, cmj_df, phase_df

    try:
        df, cmj_df, phase_df = load_all_data()
        all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
        LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

        tabs = st.tabs(["Individual Profile", "Team Gallery", "Game v. Practice", "Position Analysis", "Match Summary"])
        session_list = df[['Date', 'Session_Name']].drop_duplicates().sort_values('Date', ascending=False)['Session_Name'].tolist()

        # --- TAB 0: INDIVIDUAL PROFILE ---
        with tabs[0]:
            c_f1, c_f2 = st.columns(2)
            with c_f1: selected_session = st.selectbox("Practice Selection", session_list, index=0, key="nav_sel_ind")
            with c_f2: pos_f = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_ind")
            
            day_df = df[df['Session_Name'] == selected_session].copy()
            if not day_df.empty:
                curr_date = day_df['Date'].iloc[0]
                dropdown_df = day_df.copy()
                if pos_f != "All Positions": dropdown_df = dropdown_df[dropdown_df['Position'] == pos_f]
                sel_p = st.selectbox("Select Athlete", sorted(dropdown_df['Name'].unique()))
                
                # Handling Daily Totals (Summing multiple practices/lifts)
                p_full_hist = df[df['Name'] == sel_p]
                daily_sums = p_full_hist.groupby('Date')[all_metrics].sum().reset_index()
                lb = daily_sums[(daily_sums['Date'] >= curr_date - timedelta(days=30)) & (daily_sums['Date'] <= curr_date)]
                
                today_vals = daily_sums[daily_sums['Date'] == curr_date].iloc[0]
                avg_30 = lb[all_metrics].mean()
                
                m_rows = ""; total_grade = 0; count = 0
                for k in all_metrics:
                    val, mx, avg = today_vals[k], lb[k].max(), avg_30[k]
                    grade = math.ceil((val / mx) * 100) if mx > 0 else 0
                    total_grade += grade; count += 1; diff = (val - avg) / avg if avg != 0 else 0
                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                    arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                    m_rows += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{grade}</td></tr>"
                
                score = math.ceil(total_grade / count) if count > 0 else 0
                p_meta = day_df[day_df['Name'] == sel_p].iloc[0]
                c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
                with c1: st.markdown(f'<div style="text-align:center;"><img src="{p_meta["PhotoURL"]}" class="player-photo-large"></div><h3 style="text-align:center;">{p_meta["Name"]}</h3>', unsafe_allow_html=True)
                with c2: st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Daily Total</th><th>30d Max Day</th><th>Grade</th></tr></thead><tbody>{m_rows}</tbody></table>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(score)};">{score}</div></div>', unsafe_allow_html=True)

        # --- TAB 1: TEAM GALLERY ---
        with tabs[1]:
            c_gal1, c_gal2 = st.columns(2)
            with c_gal1: selected_session_gal = st.selectbox("Practice Selection", session_list, index=0, key="nav_sel_gal")
            with c_gal2: pos_f_gal = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_gal")
            
            gal_day_df = df[df['Session_Name'] == selected_session_gal].copy()
            curr_date_gal = gal_day_df['Date'].iloc[0] if not gal_day_df.empty else None
            
            if pos_f_gal != "All Positions": gal_day_df = gal_day_df[gal_day_df['Position'] == pos_f_gal]
            
            # Group by Name because an athlete might have multiple rows (practices) in the same day
            display_names = sorted(gal_day_df['Name'].unique())
            
            for i in range(0, len(display_names), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(display_names):
                        name = display_names[i + j]
                        p_full_g = df[df['Name'] == name]
                        daily_sums_g = p_full_g.groupby('Date')[all_metrics].sum().reset_index()
                        lb_g = daily_sums_g[(daily_sums_g['Date'] >= curr_date_gal - timedelta(days=30)) & (daily_sums_g['Date'] <= curr_date_gal)]
                        
                        today_g = daily_sums_g[daily_sums_g['Date'] == curr_date_gal].iloc[0]
                        avg_g = lb_g[all_metrics].mean()
                        
                        r_html = ""; t_grade_g = 0; c_metrics_g = 0
                        for k in all_metrics:
                            v, mx, av = today_g[k], lb_g[k].max(), avg_g[k]
                            gr = math.ceil((v / mx) * 100) if mx > 0 else 0
                            t_grade_g += gr; c_metrics_g += 1; diff_g = (v - av) / av if av != 0 else 0
                            h_c = "class='bg-highlight-red'" if abs(diff_g) > 0.10 else ""
                            arr = f"<span class='arrow-red'>{'↑' if diff_g > 0.10 else '↓'}</span>" if abs(diff_g) > 0.10 else ""
                            r_html += f"<tr><td>{k}</td><td {h_c}>{v:.1f} {arr}</td><td>{mx:.1f}</td><td>{gr}</td></tr>"
                        
                        sc_total = math.ceil(t_grade_g / c_metrics_g) if c_metrics_g > 0 else 0
                        photo = p_full_g['PhotoURL'].iloc[0]
                        with cols[j]: st.markdown(f'<div style="border:1px solid #E5E5E7; border-radius:15px; padding:15px; margin-bottom:20px;"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{photo}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px;">{name}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Total</th><th>Max Day</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div><div style="flex:1; text-align:center;"><div style="background-color:{get_flipped_gradient(sc_total)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{sc_total}</div></div></div></div>', unsafe_allow_html=True)

        with tabs[2]: # Game v Practice
            st.markdown('<div class="section-header">Weekly Prep Intensity vs. Game Demands</div>', unsafe_allow_html=True)
            c_ga, c_gw, c_gg = st.columns(3)
            with c_ga: gp_p = st.selectbox("Athlete", sorted(df['Name'].unique()), key="gp_p_vf")
            with c_gw:
                w_r = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index(); w_r['L'] = w_r.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1); gp_w = st.selectbox("Week", w_r['L'].tolist(), key="gp_w_vf"); sel_w = w_r[w_r['L'] == gp_w]['Week'].values[0]
            with c_gg: game_opts = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Game') & (df['Week'] == sel_w)]['Session_Name'].unique(); gp_g = st.selectbox("Select Specific Game", game_opts, key="gp_g_vf")
            w_data = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Practice') & (df['Week'] == sel_w)]; g_data_l = df[(df['Name'] == gp_p) & (df['Session_Name'] == gp_g)]
            if not w_data.empty and not g_data_l.empty:
                low_m = ['Total Jumps', 'Player Load', 'Explosive Efforts']; w_avg = w_data[low_m + ['Estimated Distance (y)']].mean(); g_d = g_data_l.iloc[0]; cg1, cg2 = st.columns([1, 2])
                with cg1:
                    for m in low_m + ['Estimated Distance (y)']: st.metric(label=m, value=f"{g_d[m]:.0f}", delta=f"{(w_avg[m]-g_d[m])/g_d[m]*100:+.1f}%")
                with cg2:
                    fig_dual = make_subplots(specs=[[{"secondary_y": True}]]); fig_dual.add_trace(go.Bar(x=low_m, y=[w_avg[m] for m in low_m], name="Weekly Avg", marker_color='#4895DB'), secondary_y=False); fig_dual.add_trace(go.Bar(x=low_m, y=[g_d[m] for m in low_m], name=f"Game Output", marker_color='#FF8200'), secondary_y=False); st.plotly_chart(fig_dual, use_container_width=True, config=LOCKED_CONFIG)
                wk_trends = df[df['Week'] == sel_w].groupby(['Date', 'Session_Name', 'Session_Type']).agg({'Player Load': 'mean'}).reset_index().sort_values('Date'); wk_trends['Day_Label'] = wk_trends['Date'].dt.strftime('%a %m/%d'); fig_tr = go.Figure(); fig_tr.add_trace(go.Scatter(x=wk_trends['Day_Label'], y=wk_trends['Player Load'], mode='lines', line=dict(color='#4895DB', width=3), showlegend=False))
                for s_t, clr in [('Practice', '#4895DB'), ('Game', '#FF8200')]:
                    sub = wk_trends[wk_trends['Session_Type'] == s_t]
                    for _, r in sub.iterrows(): is_sel = (r['Session_Name'] == gp_g); fig_tr.add_trace(go.Scatter(x=[r['Day_Label']], y=[r['Player Load']], name=r['Session_Name'] if s_t == 'Game' else s_t, mode='markers', marker=dict(color=clr, size=16 if is_sel else 10, line=dict(width=3 if is_sel else 1, color='black' if is_sel else 'white')), showlegend=True if s_t == 'Game' else (True if _ == sub.index[0] else False)))
                fig_tr.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0), yaxis_title="Avg Player Load"); st.plotly_chart(fig_tr, use_container_width=True, config=LOCKED_CONFIG)

        with tabs[3]: # Position Analysis
            st.markdown('<div class="section-header">Positional Performance Trends</div>', unsafe_allow_html=True)
            sel_p_pos = st.selectbox("Select Athlete for Comparative Trend", sorted(df['Name'].unique())); p_pos = df[df['Name'] == sel_p_pos].iloc[0]; pos_label = p_pos['Position']; max_wk = df['Week'].max(); rec_4 = list(range(int(max_wk) - 3, int(max_wk) + 1)); tr_df = df[df['Week'].isin(rec_4)]; t_col1, t_col2, t_col3 = st.columns(3); tr_metrics = ["Player Load", "Estimated Distance", "Total Jumps"]; cols = [t_col1, t_col2, t_col3]
            for i, m in enumerate(tr_metrics):
                if m in df.columns:
                    with cols[i]:
                        fig_t = go.Figure(); p_t = tr_df[tr_df['Name'] == sel_p_pos].groupby('Week')[m].mean().reset_index(); fig_t.add_trace(go.Scatter(x=p_t['Week'], y=p_t[m], name=sel_p_pos, line=dict(color='#0046ad', width=4), mode='lines+markers')); pos_t = tr_df[tr_df['Position'] == pos_label].groupby('Week')[m].mean().reset_index(); fig_t.add_trace(go.Scatter(x=pos_t['Week'], y=pos_t[m], name=f"{pos_label} Avg", line=dict(color='#ff7f0e', dash='dash'))); fig_t.update_layout(title=f"4-Week {m}", xaxis=dict(dtick=1), height=300, margin=dict(l=10, r=10, t=40, b=10), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)); st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)

        with tabs[4]: # Match Summary
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
                    match_list_t = df[df['Session_Type'].isin(['Game', 'Match'])].sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique()
                    if "matches_state" not in st.session_state: st.session_state.matches_state = match_list_t[-3:] if len(match_list_t) >=3 else match_list_t
                    st.session_state.matches_state = st.multiselect("Select Matches", match_list_t, default=st.session_state.matches_state)
                with c_ts2:
                    if "pos_state" not in st.session_state: st.session_state.pos_state = "All Positions"
                    st.session_state.pos_state = st.selectbox("Filter by Position", ["All Positions"] + sorted(list(df['Position'].unique())), index=0)
                st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.is_printing:
                st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

            selected_matches = st.session_state.get("matches_state", [])
            pos_filter_t = st.session_state.get("pos_state", "All Positions")

            if selected_matches:
                c_pal = ['#4895DB', '#FF8200', '#515154']; m_map = {m: c_pal[idx % 3] for idx, m in enumerate(selected_matches)}
                st.markdown('<div class="section-header">Athlete Match Performance Breakdown</div>', unsafe_allow_html=True)
                tourney_df = df[df['Session_Name'].isin(selected_matches)].sort_values(['Date', 'Sheet_Order'])
                if pos_filter_t != "All Positions": tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]
                
                # --- CALC GLOBAL MAX FOR UNIFIED AXIS ---
                global_max_primary = tourney_df[['Total Jumps', 'Player Load', 'Explosive Efforts']].max().max() * 1.1
                global_max_dist = tourney_df['Estimated Distance (y)'].max() * 1.1

                ath_t = sorted(tourney_df['Name'].unique())
                for name in ath_t:
                    ad = tourney_df[tourney_df['Name'] == name]
                    st.markdown(f'<div class="player-row-container"><div class="player-divider"></div>', unsafe_allow_html=True)
                    side_cols = st.columns([1.5, 2])
                    with side_cols[0]:
                        card_start = f"""
                            <div style="display:flex; align-items:center; gap:12px; padding:10px; background:#f8f9fa; border-bottom:2px solid #FF8200;">
                                <img src="{ad['PhotoURL'].iloc[0]}" class="gallery-photo" style="width:65px; height:65px;">
                                <div><p style="margin:0; font-weight:900; color:#1D1D1F; font-size:18px;">{name}</p><p style="margin:0; color:#4895DB; font-weight:700; font-size:16px;">{ad['Position'].iloc[0]}</p></div>
                            </div>
                            <div style="padding:5px;">
                                <table class="scout-table" style="margin-bottom:0;">
                                    <thead><tr><th>Match</th><th>Total Jumps</th><th>Player Load</th><th>Explosive Efforts</th><th>Estimated Distance</th></tr></thead>
                                    <tbody>
                        """
                        for _, r in ad.iterrows():
                            card_start += f"<tr><td style='font-weight:700; font-size:11px;'>{r['Session_Name']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.0f}</td><td>{r['Explosive Efforts']:.0f}</td><td>{r['Estimated Distance (y)']:.0f}</td></tr>"
                        card_start += f"<tr style='background:#4895DB; color:white; font-weight:900;'><td>TOTAL</td><td>{int(ad['Total Jumps'].sum())}</td><td>{ad['Player Load'].sum():.0f}</td><td>{ad['Explosive Efforts'].sum():.0f}</td><td>{ad['Estimated Distance (y)'].sum():.0f}</td></tr></tbody></table></div>"
                        st.markdown(card_start, unsafe_allow_html=True)
                    with side_cols[1]:
                        fig_ath = make_subplots(specs=[[{"secondary_y": True}]]);
                        for _, r in ad.iterrows():
                            fig_ath.add_trace(go.Bar(name=r['Session_Name'], x=['Total Jumps', 'Player Load', 'Explosive Efforts'], y=[r['Total Jumps'], r['Player Load'], r['Explosive Efforts']], marker_color=m_map[r['Session_Name']]), secondary_y=False)
                            fig_ath.add_trace(go.Bar(name="Dist", x=['Estimated Distance'], y=[r['Estimated Distance (y)']], marker=dict(color=m_map[r['Session_Name']], opacity=0.4), showlegend=False), secondary_y=True)
                        
                        # Apply Fixed Axis Values
                        fig_ath.update_layout(
                            barmode='group', height=260, margin=dict(l=10, r=10, t=10, b=80), 
                            template="simple_white", font=dict(color="#333333", size=10),
                            legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5),
                            yaxis=dict(range=[0, global_max_primary]),
                            yaxis2=dict(range=[0, global_max_dist])
                        )
                        st.plotly_chart(fig_ath, use_container_width=True, config=LOCKED_CONFIG)
                    st.markdown('</div>', unsafe_allow_html=True)

                st.write("<br><br>", unsafe_allow_html=True)
                st.markdown('<div class="section-header">Team Match Averages</div>', unsafe_allow_html=True)
                team_avg_t = tourney_df.groupby('Session_Name')[['Total Jumps', 'Player Load', 'Explosive Efforts', 'Estimated Distance (y)']].mean().reset_index()
                
                metrics_to_plot = ['Total Jumps', 'Player Load', 'Explosive Efforts', 'Estimated Distance (y)']
                rows = [st.columns(2), st.columns(2)]
                for idx, m in enumerate(metrics_to_plot):
                    with rows[idx // 2][idx % 2]:
                        fig_t = go.Figure()
                        fig_t.add_trace(go.Bar(x=team_avg_t['Session_Name'], y=team_avg_t[m], marker_color=[m_map[g] for g in team_avg_t['Session_Name']]))
                        fig_t.update_layout(title=f"Avg {m}", height=300, template="simple_white", margin=dict(l=10, r=10, t=40, b=10))
                        st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)

    except Exception as e:
        st.error(f"Sync Error: {e}")
