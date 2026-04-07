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
    # --- CSS: FORMATTING, PRINT CONTROLS, & GAP REMOVAL ---
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; color: #1D1D1F; }
        hr { display: none !important; }
        .block-container { padding-top: 1rem !important; }
        .viewerBadge_link__1S137, .main_heading_anchor__m6v0K, a.header-anchor { display: none !important; }
        header a { display: none !important; }
        .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
        .scout-table th { background-color: #4895DB; color: white; padding: 4px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 10px; text-transform: uppercase; }
        .scout-table td { padding: 4px; border-bottom: 1px solid #F5F5F7; font-size: 10px; color: #1D1D1F; }
        .bg-highlight-red { background-color: #ffcccc !important; font-weight: 900; }
        .arrow-red { color: #b30000 !important; font-weight: 900; margin-left: 4px; }
        .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
        .score-box { padding: 12px 20px; border-radius: 12px; font-size: 28px; font-weight: 800; min-width: 100px; color: #FFFFFF; line-height: 1.2; text-align: center;}
        .info-box { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 12px; margin-top: 10px; font-size: 12px; color: #1D1D1F; font-weight: 600; line-height: 1.4; }
        
        .player-row-container {
            break-inside: avoid !important;
            page-break-inside: avoid !important;
            display: block;
            margin-bottom: 30px;
        }
        
        .player-divider { border: 0; height: 1px; background: #E5E5E7; margin-bottom: 15px; width: 100%; }
        .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
        .section-header { font-size: 14px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 15px; margin-bottom: 10px; padding-bottom: 5px; text-transform: uppercase; }

        @media print {
            .main-logo-container { display: block !important; margin-bottom: 0 !important; }
            .stTabs [role="tablist"], [data-testid="stSidebar"], header, footer, [data-testid="stHeader"], .print-hide, button, #print-hide-header { 
                display: none !important; 
            }
            /* Removes the empty space where the hidden filters were */
            [data-testid="stVerticalBlock"] > div:has(div.print-hide) {
                display: none !important;
                height: 0 !important;
                margin: 0 !important;
            }
            [data-testid="stMultiSelect"], [data-testid="stSelectbox"], [data-baseweb="select"] {
                display: none !important;
            }
            .main .block-container { padding: 0 !important; max-width: 100% !important; }
            .scout-table td, p, span, div { color: #000000 !important; }
        }
        </style>
        """, unsafe_allow_html=True)

    @st.cache_data(ttl=300)
    def load_all_data():
        df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
        df.columns = df.columns.str.strip()
        df['Sheet_Order'] = range(len(df))
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']) 
        if 'Week' in df.columns:
            df['Week'] = pd.to_numeric(df['Week'].astype(str).str.extract('(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
        rename_map = {
            'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps', 'IMA Jump Count High Band': 'High Jumps', 
            'BMP Jumping Load': 'Jump Load', 'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance (y)', 
            'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movement'
        }
        df = df.rename(columns=rename_map)
        df['Session_Type'] = df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
        avail = [v for v in rename_map.values() if v in df.columns]
        for col in avail: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).round(1)
        df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
        df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
        df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
        cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
        cmj_df.columns = cmj_df.columns.str.strip()
        cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
        cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
        phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
        phase_df.columns = phase_df.columns.str.strip()
        if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
        phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
        phase_df = phase_df.rename(columns=rename_map)
        return df, cmj_df, phase_df

    LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

    try:
        df, cmj_df, phase_df = load_all_data()
        all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
        def get_flipped_gradient(score):
            score = float(score); return "#2D5A27" if score <= 40 else "#D4A017" if score <= 70 else "#A52A2A"

        st.markdown('<div class="main-logo-container" style="text-align: center; margin-top: 10px; margin-bottom: 15px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120"><div style="color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;">LADY VOLS VOLLEYBALL PERFORMANCE</div></div>', unsafe_allow_html=True)
        
        tabs = st.tabs(["Individual Profile", "Team Gallery", "Game v. Practice", "Position Analysis", "Match Summary"])
        session_list = df[['Date', 'Session_Name']].drop_duplicates().sort_values('Date', ascending=False)['Session_Name'].tolist()

        # --- TAB 0: INDIVIDUAL PROFILE ---
        with tabs[0]:
            cf1, cf2 = st.columns(2)
            with cf1: selected_session = st.selectbox("Practice Selection", session_list, index=0, key="shared_sess")
            with cf2: pos_f = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="shared_pos")
            day_df = df[df['Session_Name'] == selected_session].copy()
            if pos_f != "All Positions": day_df = day_df[day_df['Position'] == pos_f]
            if not day_df.empty:
                sel_p = st.selectbox("Select Athlete", sorted(day_df['Name'].unique()))
                p = day_df[day_df['Name'] == sel_p].iloc[0]; curr_date = p['Date']
                lb = df[(df['Name'] == sel_p) & (df['Date'] >= curr_date - timedelta(days=30)) & (df['Date'] <= curr_date)]
                m_rows = ""; total_grade = 0; count = 0
                for k in all_metrics:
                    if k in p:
                        val, mx, avg = p[k], lb[k].max(), lb[k].mean(); grade = math.ceil((val / mx) * 100) if mx > 0 else 0
                        total_grade += grade; count += 1; diff = (val - avg) / avg if avg != 0 else 0
                        h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                        arr = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                        m_rows += f"<tr><td>{k}</td><td {h_class}>{val} {arr}</td><td>{mx}</td><td>{grade}</td></tr>"
                score = math.ceil(total_grade / count) if count > 0 else 0
                c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
                with c1: st.markdown(f'<div style="text-align:center;"><img src="{p["PhotoURL"]}" class="player-photo-large"></div><h3 style="text-align:center;">{p["Name"]}</h3>', unsafe_allow_html=True)
                with c2: st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>{m_rows}</tbody></table>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(score)};">{score}</div></div>', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
                jc1, jc2 = st.columns([1.5, 3.5])
                with jc1:
                    p_cmj = cmj_df[(cmj_df['Athlete'] == sel_p) & (cmj_df['Test Date'] <= curr_date)].sort_values('Test Date'); sync_cmj = p_cmj[(p_cmj['Test Date'] > curr_date - timedelta(days=7))]
                    if not sync_cmj.empty:
                        latest = sync_cmj.iloc[-1]; base_h = p_cmj.tail(5).iloc[:-1]['Jump Height (in)'].mean(); base_rsi = p_cmj.tail(5).iloc[:-1]['RSI-modified [m/s]'].mean(); cur_h, cur_rsi = latest['Jump Height (in)'], latest['RSI-modified [m/s]']; p_diff = ((cur_h - base_h) / base_h) * 100
                        label, color = (("ELITE", "#28a745") if cur_h >= base_h and cur_rsi >= base_rsi else ("FATIGUED", "#dc3545") if cur_h < base_h and cur_rsi < base_rsi else ("GRINDER", "#ffc107"))
                        st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color};">{p_diff:+.1f}%<span style="font-size:10px; display:block;">{label}</span></div></div><div class="info-box"><b>Today:</b> {cur_h:.1f}" | {cur_rsi:.2f} RSI</div>', unsafe_allow_html=True)
                with jc2:
                    if not p_cmj.empty:
                        fig = make_subplots(specs=[[{"secondary_y": True}]]); fig.add_trace(go.Scatter(x=p_cmj['Test Date'], y=p_cmj['Jump Height (in)'], name="Height", line=dict(color='#FF8200', width=3)), secondary_y=False); fig.add_trace(go.Scatter(x=p_cmj['Test Date'], y=p_cmj['RSI-modified [m/s]'], name="RSI", line=dict(color='#4895DB', dash='dot')), secondary_y=True); fig.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), showlegend=False); st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG)
                p_ph = phase_df[(phase_df['Name'] == sel_p) & (phase_df['Date'] == curr_date)].copy()
                if not p_ph.empty:
                    st.markdown('<div class="section-header">Practice Phase Breakdown</div>', unsafe_allow_html=True)
                    fig_ph = make_subplots(specs=[[{"secondary_y": True}]]); fig_ph.add_trace(go.Bar(x=p_ph['Phase'], y=p_ph['Total Jumps'], name="Jumps", marker_color='#FF8200'), secondary_y=False); fig_ph.add_trace(go.Scatter(x=p_ph['Phase'], y=p_ph['Player Load'], name="Load", line=dict(color='#4895DB', width=4)), secondary_y=False)
                    if 'Estimated Distance (y)' in p_ph.columns: fig_ph.add_trace(go.Scatter(x=p_ph['Phase'], y=p_ph['Estimated Distance (y)'], name="Distance (y)", line=dict(color='#515154', width=2, dash='dash')), secondary_y=True)
                    fig_ph.update_layout(height=350, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode=False); st.plotly_chart(fig_ph, use_container_width=True, config=LOCKED_CONFIG)
                    dist_th = "<th>Distance (y)</th>" if "Estimated Distance (y)" in p_ph.columns else ""; p_tbl = f'<table class="scout-table"><thead><tr><th>Phase</th><th>Jumps</th><th>Load</th>{dist_th}</tr></thead><tbody>'
                    for _, r in p_ph.iterrows(): p_tbl += f"<tr><td>{r['Phase']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.1f}</td>{f'<td>{r['Estimated Distance (y)']:.1f}</td>' if 'Estimated Distance (y)' in p_ph.columns else ''}</tr>"
                    st.markdown(p_tbl + '</tbody></table>', unsafe_allow_html=True)

        # --- TAB 1: TEAM GALLERY ---
        with tabs[1]:
            gal_df = df[df['Session_Name'] == selected_session].copy()
            if pos_f != "All Positions": gal_df = gal_df[gal_df['Position'] == pos_f]
            for i in range(0, len(gal_df), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(gal_df):
                        pr = gal_df.iloc[i + j]; plb = df[(df['Name'] == pr['Name']) & (df['Date'] >= pr['Date'] - timedelta(days=30)) & (df['Date'] <= pr['Date'])]
                        r_html = ""; tg = 0; cm = 0
                        for k in all_metrics:
                            if k in pr:
                                v, mx, avg = pr[k], plb[k].max(), plb[k].mean(); g = math.ceil((v / mx) * 100) if mx > 0 else 0
                                tg += g; cm += 1; diff = (v - avg) / avg if avg != 0 else 0; h = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""; arr = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                                r_html += f"<tr><td>{k}</td><td {h}>{v} {arr}</td><td>{g}</td></tr>"
                        sc = math.ceil(tg / cm) if cm > 0 else 0
                        with cols[j]: st.markdown(f'<div style="border:1px solid #E5E5E7; border-radius:15px; padding:15px; margin-bottom:20px;"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{pr["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold;">{pr["Name"]}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Val</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div><div style="flex:1; text-align:center;"><div class="score-box" style="background-color:{get_flipped_gradient(sc)};">{sc}</div></div></div></div>', unsafe_allow_html=True)

        # --- TAB 2: GAME V PRACTICE ---
        with tabs[2]:
            st.markdown('<div class="section-header">Weekly Prep Intensity vs. Game Demands</div>', unsafe_allow_html=True)
            cga, cgw, cgg = st.columns(3)
            with cga: gpp = st.selectbox("Athlete", sorted(df['Name'].unique()), key="gp_a")
            with cgw:
                wr = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index(); wr['L'] = wr.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1)
                gpw = st.selectbox("Week", wr['L'].tolist(), key="gp_w"); sel_w = wr[wr['L'] == gpw]['Week'].values[0]
            with cgg:
                go_opts = df[(df['Name'] == gpp) & (df['Session_Type'] == 'Game') & (df['Week'] == sel_w)]['Session_Name'].unique()
                gpg = st.selectbox("Select Specific Game", go_opts, key="gp_g")
            wd = df[(df['Name'] == gpp) & (df['Session_Type'] == 'Practice') & (df['Week'] == sel_w)]; gd = df[(df['Name'] == gpp) & (df['Session_Name'] == gpg)]
            if not wd.empty and not gd.empty:
                lm = ['Total Jumps', 'Player Load', 'Explosive Efforts']; wavg = wd[lm + ['Estimated Distance (y)']].mean(); g_d = gd.iloc[0]; cg1, cg2 = st.columns([1, 2])
                with cg1:
                    for m in lm + ['Estimated Distance (y)']: st.metric(label=m, value=f"{g_d[m]:.0f}", delta=f"{(wavg[m]-g_d[m])/g_d[m]*100:+.1f}%")
                with cg2:
                    fig_d = make_subplots(specs=[[{"secondary_y": True}]]); fig_d.add_trace(go.Bar(x=lm, y=[wavg[m] for m in lm], name="Weekly Avg", marker_color='#4895DB'), secondary_y=False); fig_d.add_trace(go.Bar(x=lm, y=[g_d[m] for m in lm], name=f"Game Output", marker_color='#FF8200'), secondary_y=False); st.plotly_chart(fig_d, use_container_width=True, config=LOCKED_CONFIG)
                wk_trends = df[df['Week'] == sel_w].groupby(['Date', 'Session_Name', 'Session_Type']).agg({'Player Load': 'mean'}).reset_index().sort_values('Date'); wk_trends['Day_Label'] = wk_trends['Date'].dt.strftime('%a %m/%d'); fig_tr = go.Figure(); fig_tr.add_trace(go.Scatter(x=wk_trends['Day_Label'], y=wk_trends['Player Load'], mode='lines', line=dict(color='#4895DB', width=3), showlegend=False))
                for s_t, clr in [('Practice', '#4895DB'), ('Game', '#FF8200')]:
                    sub = wk_trends[wk_trends['Session_Type'] == s_t]
                    for _, r in sub.iterrows(): is_sel = (r['Session_Name'] == gpg); fig_tr.add_trace(go.Scatter(x=[r['Day_Label']], y=[r['Player Load']], name=r['Session_Name'] if s_t == 'Game' else s_t, mode='markers', marker=dict(color=clr, size=16 if is_sel else 10, line=dict(width=3 if is_sel else 1, color='black' if is_sel else 'white')), showlegend=True if s_t == 'Game' else (True if _ == sub.index[0] else False)))
                fig_tr.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0), yaxis_title="Avg Player Load"); st.plotly_chart(fig_tr, use_container_width=True, config=LOCKED_CONFIG)

        # --- TAB 4: MATCH SUMMARY ---
        with tabs[4]:
            st.markdown('<div class="print-hide">', unsafe_allow_html=True)
            if st.button("🖨️ Prepare PDF for Printing"): st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
            st.markdown('<div id="print-hide-header"><div class="section-header">Match Comparison Selection</div></div>', unsafe_allow_html=True)
            c_ts1, c_ts2 = st.columns([2, 1])
            with c_ts1:
                match_list_t = df[df['Session_Type'].isin(['Game', 'Match'])].sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique()
                selected_matches = st.multiselect("Select Weekend Matches", match_list_t, default=match_list_t[-3:] if len(match_list_t) >=3 else match_list_t)
            with c_ts2: pos_filter_t = st.selectbox("Filter by Position", ["All Positions"] + sorted(list(df['Position'].unique())), key="ms_pos_surgical")
            st.markdown('</div>', unsafe_allow_html=True)

            if selected_matches:
                c_pal = ['#4895DB', '#FF8200', '#515154']; m_map = {m: c_pal[idx % 3] for idx, m in enumerate(selected_matches)}
                st.markdown('<div class="section-header">Athlete Match Performance Breakdown</div>', unsafe_allow_html=True)
                tourney_df = df[df['Session_Name'].isin(selected_matches)].sort_values(['Date', 'Sheet_Order'])
                if pos_filter_t != "All Positions": tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]
                ath_t = sorted(tourney_df['Name'].unique())
                
                for name in ath_t:
                    ad = tourney_df[tourney_df['Name'] == name]
                    st.markdown(f'<div class="player-row-container"><div class="player-divider"></div>', unsafe_allow_html=True)
                    side_cols = st.columns([1.5, 2])
                    with side_cols[0]:
                        card_start = f"""
                            <div style="display:flex; align-items:center; gap:12px; padding:10px; background:#f8f9fa; border-bottom:2px solid #FF8200;">
                                <img src="{ad['PhotoURL'].iloc[0]}" class="gallery-photo" style="width:55px; height:55px;">
                                <div><p style="margin:0; font-weight:900; color:#1D1D1F; font-size:15px;">{name}</p><p style="margin:0; color:#4895DB; font-weight:700; font-size:10px;">{ad['Position'].iloc[0]}</p></div>
                            </div>
                            <div style="padding:5px;">
                                <table class="scout-table" style="margin-bottom:0;">
                                    <thead><tr><th>Match</th><th>Jumps</th><th>Load</th><th>Effort</th><th>Dist</th></tr></thead>
                                    <tbody>
                        """
                        for _, r in ad.iterrows():
                            card_start += f"<tr><td style='font-weight:700; font-size:9px;'>{r['Session_Name']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.0f}</td><td>{r['Explosive Efforts']:.0f}</td><td>{r['Estimated Distance (y)']:.0f}</td></tr>"
                        card_start += f"<tr style='background:#4895DB; color:white; font-weight:900;'><td>TOTAL</td><td>{int(ad['Total Jumps'].sum())}</td><td>{ad['Player Load'].sum():.0f}</td><td>{ad['Explosive Efforts'].sum():.0f}</td><td>{ad['Estimated Distance (y)'].sum():.0f}</td></tr></tbody></table></div>"
                        st.markdown(card_start, unsafe_allow_html=True)
                    with side_cols[1]:
                        fig_ath = make_subplots(specs=[[{"secondary_y": True}]]);
                        for _, r in ad.iterrows():
                            fig_ath.add_trace(go.Bar(name=r['Session_Name'], x=['Jumps', 'Load', 'Effort'], y=[r['Total Jumps'], r['Player Load'], r['Explosive Efforts']], marker_color=m_map[r['Session_Name']]), secondary_y=False)
                            fig_ath.add_trace(go.Bar(name="Dist", x=['Distance'], y=[r['Estimated Distance (y)']], marker=dict(color=m_map[r['Session_Name']], opacity=0.4), showlegend=False), secondary_y=True)
                        fig_ath.update_layout(barmode='group', height=260, margin=dict(l=10, r=10, t=10, b=80), template="simple_white", font=dict(color="#333333", size=10), legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5))
                        st.plotly_chart(fig_ath, use_container_width=True, config=LOCKED_CONFIG)
                    st.markdown('</div>', unsafe_allow_html=True)

                st.write("<br><br>", unsafe_allow_html=True); st.markdown('<div class="section-header">Team Match Averages</div>', unsafe_allow_html=True)
                team_avg_t = tourney_df.groupby('Session_Name')[['Total Jumps', 'Player Load', 'Explosive Efforts', 'Estimated Distance (y)']].mean().reset_index()
                c1, c2 = st.columns(2); c3, c4 = st.columns(2); t_cols = [c1, c2, c3, c4]
                for idx, m in enumerate(['Total Jumps', 'Player Load', 'Explosive Efforts', 'Estimated Distance (y)']):
                    with t_cols[idx]:
                        fig_t = go.Figure(); fig_t.add_trace(go.Bar(x=team_avg_t['Session_Name'], y=team_avg_t[m], marker_color=[m_map[g] for g in team_avg_t['Session_Name']], marker_line_width=0))
                        fig_t.update_layout(title=f"Team Avg: {m}", font=dict(color="#333333"), showlegend=False, height=400, template="simple_white", bargap=0.01); st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)

    except Exception as e:
        st.error(f"Sync Error: {e}")
