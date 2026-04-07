import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
import time
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

# --- GLOBAL VARIABLES ---
all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']

# --- CSS: FORMATTING & HIGHLIGHTING ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    .viewerBadge_link__1S137, .main_heading_anchor__m6v0K, a.header-anchor { display: none !important; }
    header a { display: none !important; }
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #4895DB; color: white; padding: 6px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 11px; text-transform: uppercase; }
    .scout-table td { padding: 6px; border-bottom: 1px solid #F5F5F7; font-size: 11px; }
    .bg-highlight-red { background-color: #ffcccc !important; font-weight: 900; }
    .arrow-red { color: #b30000 !important; font-weight: 900; margin-left: 4px; }
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    .score-box { padding: 12px 20px; border-radius: 12px; font-size: 28px; font-weight: 800; min-width: 100px; color: #FFFFFF; line-height: 1.2; text-align: center;}
    .gallery-card { border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 25px; min-height: 450px; }
    .gallery-photo { border-radius: 50%; width: 80px; height: 80px; object-fit: cover; border: 3px solid #FF8200; }
    .section-header { font-size: 14px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    .info-box { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 12px; margin-top: 10px; font-size: 12px; color: #1D1D1F; font-weight: 600; line-height: 1.4; }
    .js-plotly-plot { pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_flipped_gradient(score):
    score = float(score)
    if score <= 40: return "#2D5A27"
    if score <= 70: return "#D4A017"
    return "#A52A2A"

# --- DATA LOADING ---
@st.cache_data(ttl=0)
def load_all_data():
    def get_fresh_url(url): return f"{url}&cachebust={int(time.time())}"
    
    # 1. Main Sheet
    df = pd.read_csv(get_fresh_url(st.secrets["GOOGLE_SHEET_URL"]))
    # CRITICAL: Store original row order to handle same-day games correctly
    df['Sheet_Order'] = range(len(df))
    df.columns = df.columns.str.strip()
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
    for col in avail:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).round(1)

    df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    
    # 2. CMJ Sheet
    cmj_df = pd.read_csv(get_fresh_url(st.secrets["CMJ_SHEET_URL"]))
    cmj_df.columns = cmj_df.columns.str.strip()
    cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
    
    # 3. Phases Sheet
    phase_df = pd.read_csv(get_fresh_url(st.secrets["PHASES_SHEET_URL"]))
    phase_df.columns = phase_df.columns.str.strip()
    if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
    phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
    phase_df = phase_df.rename(columns=rename_map)
    
    return df, cmj_df, phase_df

LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

try:
    df, cmj_df, phase_df = load_all_data()
    
    st.markdown("""
        <div style="text-align: center; margin-top: 10px; margin-bottom: 15px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120">
            <div style='color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;'>LADY VOLS VOLLEYBALL PERFORMANCE</div>
        </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["Individual Profile", "Team Gallery", "Game v. Practice", "Position Analysis", "Tournament Summary"])
    
    # Session lists sorted by original sheet order (descending)
    session_list = df[['Date', 'Sheet_Order', 'Session_Name']].drop_duplicates(subset=['Session_Name']).sort_values(['Date', 'Sheet_Order'], ascending=[False, False])['Session_Name'].tolist()

    # --- TAB 0: INDIVIDUAL PROFILE ---
    with tabs[0]:
        c_f1, c_f2 = st.columns(2)
        with c_f1: selected_session = st.selectbox("Practice Selection", session_list, index=0, key="nav_sel_ind")
        with c_f2: pos_f = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_ind")
        day_df = df[df['Session_Name'] == selected_session].copy()
        if not day_df.empty:
            curr_date = day_df['Date'].iloc[0]
            if pos_f != "All Positions": day_df = day_df[day_df['Position'] == pos_f]
            sel_p = st.selectbox("Select Athlete", sorted(day_df['Name'].unique()), key="athlete_sel_ind")
            p = day_df[day_df['Name'] == sel_p].iloc[0]
            lb = df[(df['Name'] == sel_p) & (df['Date'] >= curr_date - timedelta(days=30)) & (df['Date'] <= curr_date)]
            
            m_rows = ""; total_grade = 0; count = 0
            for k in all_metrics:
                if k in p:
                    val, mx, avg = p[k], lb[k].max(), lb[k].mean()
                    grade = math.ceil((val / mx) * 100) if mx > 0 else 0
                    total_grade += grade; count += 1
                    diff = (val - avg) / avg if avg != 0 else 0
                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                    arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                    m_rows += f"<tr><td>{k}</td><td {h_class}>{val} {arr_val}</td><td>{mx}</td><td>{grade}</td></tr>"
            score = math.ceil(total_grade / count) if count > 0 else 0
            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1: st.markdown(f'<div style="text-align:center;"><img src="{p["PhotoURL"]}" class="player-photo-large"></div><h3 style="text-align:center;">{p["Name"]}</h3>', unsafe_allow_html=True)
            with c2: st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>{m_rows}</tbody></table>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(score)};">{score}</div></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
            jc1, jc2 = st.columns([1.5, 3.5])
            with jc1:
                p_cmj_hist = cmj_df[cmj_df['Athlete'] == sel_p].sort_values('Test Date')
                if not p_cmj_hist.empty:
                    latest = p_cmj_hist.iloc[-1]
                    base_h = p_cmj_hist.tail(6).iloc[:-1]['Jump Height (in)'].mean()
                    base_rsi = p_cmj_hist.tail(6).iloc[:-1]['RSI-modified [m/s]'].mean()
                    cur_h, cur_rsi = latest['Jump Height (in)'], latest['RSI-modified [m/s]']
                    p_diff = ((cur_h - base_h) / base_h) * 100
                    label, color, profile = ("ELITE", "#28a745", "Jump Height and RSI are both High.") if cur_h >= base_h and cur_rsi >= base_rsi else \
                                           ("GRINDER", "#ffc107", "Jump Height is High | RSI is Low.") if cur_h >= base_h and cur_rsi < base_rsi else \
                                           ("SPRINGY", "#ffc107", "Jump Height is Low | RSI is High.") if cur_h < base_h and cur_rsi >= base_rsi else \
                                           ("FATIGUED", "#dc3545", "Jump Height and RSI are both Low.")
                    st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color};">{p_diff:+.1f}%<span style="font-size:10px; display:block;">{label}</span></div></div><div class="info-box"><b>Latest Test ({latest["Test Date"].strftime("%m/%d")}):</b> {cur_h:.1f}" | {cur_rsi:.2f} RSI<br><b>Profile:</b> {profile}</div>', unsafe_allow_html=True)
            with jc2:
                if not p_cmj_hist.empty:
                    fig = make_subplots(specs=[[{"secondary_y": True}]]); fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist['Jump Height (in)'], name="Height", line=dict(color='#FF8200', width=3)), secondary_y=False); fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist['RSI-modified [m/s]'], name="RSI", line=dict(color='#4895DB', dash='dot')), secondary_y=True); fig.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), showlegend=False, hovermode=False); st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG)

            p_ph = phase_df[(phase_df['Name'] == sel_p) & (phase_df['Date'] == curr_date)].copy()
            if not p_ph.empty:
                st.markdown('<div class="section-header">Practice Phase Breakdown</div>', unsafe_allow_html=True)
                fig_ph = make_subplots(specs=[[{"secondary_y": True}]])
                fig_ph.add_trace(go.Bar(x=p_ph['Phase'], y=p_ph['Total Jumps'], name="Jumps", marker_color='#FF8200'), secondary_y=False)
                fig_ph.add_trace(go.Scatter(x=p_ph['Phase'], y=p_ph['Player Load'], name="Load", line=dict(color='#4895DB', width=4)), secondary_y=False)
                fig_ph.update_layout(height=350, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode=False)
                st.plotly_chart(fig_ph, use_container_width=True, config=LOCKED_CONFIG)
                p_tbl = f'<table class="scout-table"><thead><tr><th>Phase</th><th>Jumps</th><th>Load</th></tr></thead><tbody>'
                for _, r in p_ph.iterrows(): p_tbl += f"<tr><td>{r['Phase']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.1f}</td></tr>"
                st.markdown(p_tbl + '</tbody></table>', unsafe_allow_html=True)

    # --- TAB 1: TEAM GALLERY ---
    with tabs[1]:
        c_gal1, c_gal2 = st.columns(2)
        with c_gal1: selected_session_gal = st.selectbox("Practice Selection", session_list, index=0, key="nav_sel_gal")
        with c_gal2: pos_f_gal = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_gal")
        gal_df = df[df['Session_Name'] == selected_session_gal].copy()
        if pos_f_gal != "All Positions": gal_df = gal_df[gal_df['Position'] == pos_f_gal]
        if not gal_df.empty:
            for i in range(0, len(gal_df), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(gal_df):
                        pd_row = gal_df.iloc[i + j]
                        lb_g = df[(df['Name'] == pd_row['Name']) & (df['Date'] >= pd_row['Date'] - timedelta(days=30)) & (df['Date'] <= pd_row['Date'])]
                        r_html = ""; t_grade = 0; c_metrics = 0
                        for k in all_metrics:
                            if k in pd_row:
                                v, m, a = pd_row[k], lb_g[k].max(), lb_g[k].mean()
                                g = math.ceil((v / m) * 100) if m > 0 else 0
                                t_grade += g; c_metrics += 1
                                r_html += f"<tr><td>{k}</td><td>{v}</td><td>{m}</td><td>{g}</td></tr>"
                        sc_g = math.ceil(t_grade / c_metrics) if c_metrics > 0 else 0
                        with cols[j]: st.markdown(f'<div class="gallery-card"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{pd_row["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px;">{pd_row["Name"]}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Val</th><th>Max</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div><div style="flex:1; text-align:center;"><div style="background-color:{get_flipped_gradient(sc_g)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{sc_g}</div></div></div></div>', unsafe_allow_html=True)

    # --- TAB 2: GAME V PRACTICE ---
    with tabs[2]:
        st.markdown('<div class="section-header">Weekly Prep Intensity vs. Game Demands</div>', unsafe_allow_html=True)
        c_ga, c_gw, c_gg = st.columns(3)
        with c_ga: gp_p = st.selectbox("Athlete", sorted(df['Name'].unique()), key="gp_p_vf")
        with c_gw:
            w_r = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index()
            w_r['L'] = w_r.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1)
            gp_w = st.selectbox("Week", w_r['L'].tolist(), key="gp_w_vf")
            sel_w = w_r[w_r['L'] == gp_w]['Week'].values[0]
        with c_gg: 
            game_opts = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Game') & (df['Week'] == sel_w)].sort_values('Sheet_Order')['Session_Name'].unique()
            gp_g = st.selectbox("Select Specific Game", game_opts, key="gp_g_vf")
        
        w_data = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Practice') & (df['Week'] == sel_w)]
        g_data_l = df[(df['Name'] == gp_p) & (df['Session_Name'] == gp_g)]
        if not w_data.empty and not g_data_l.empty:
            low_m = [m for m in ['Total Jumps', 'Player Load', 'Explosive Efforts'] if m in df.columns]
            w_avg = w_data[low_m].mean(); g_d = g_data_l.iloc[0]
            cg1, cg2 = st.columns([1, 2])
            with cg1:
                for m in low_m:
                    pdif = ((w_avg[m] - g_d[m]) / g_d[m] * 100) if g_d[m] > 0 else 0
                    st.metric(label=m, value=f"{g_d[m]:.0f}", delta=f"{pdif:+.1f}% vs Weekly Avg")
            with cg2:
                fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
                fig_dual.add_trace(go.Bar(x=low_m, y=[w_avg[m] for m in low_m], name="Weekly Avg", marker_color='#4895DB'), secondary_y=False)
                fig_dual.add_trace(go.Bar(x=low_m, y=[g_d[m] for m in low_m], name=f"Game: {gp_g}", marker_color='#FF8200'), secondary_y=False)
                fig_dual.update_layout(height=400, barmode='group', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_dual, use_container_width=True, config=LOCKED_CONFIG)

    # --- TAB 3: POSITION ANALYSIS ---
    with tabs[3]:
        st.markdown('<div class="section-header">Positional Performance & 4-Week Trends</div>', unsafe_allow_html=True)
        sel_p_pos = st.selectbox("Select Athlete for Comparative Trend", sorted(df['Name'].unique()), key="athlete_sel_pos")
        p_pos = df[df['Name'] == sel_p_pos].iloc[0]
        pos_label = p_pos['Position']
        max_wk = df['Week'].max()
        rec_4 = list(range(int(max_wk) - 3, int(max_wk) + 1))
        tr_df = df[df['Week'].isin(rec_4)]
        t_col1, t_col2, t_col3 = st.columns(3)
        tr_metrics = ["Player Load", "Estimated Distance (y)", "Total Jumps"]
        cols = [t_col1, t_col2, t_col3]
        for i, m in enumerate(tr_metrics):
            if m in df.columns:
                with cols[i]:
                    fig_t = go.Figure()
                    p_t = tr_df[tr_df['Name'] == sel_p_pos].groupby('Week')[m].sum().reset_index()
                    fig_t.add_trace(go.Scatter(x=p_t['Week'], y=p_t[m], name=sel_p_pos, line=dict(color='#0046ad', width=4), mode='lines+markers'))
                    pos_t = tr_df[tr_df['Position'] == pos_label].groupby(['Week', 'Name'])[m].sum().reset_index().groupby('Week')[m].mean().reset_index()
                    fig_t.add_trace(go.Scatter(x=pos_t['Week'], y=pos_t[m], name=f"{pos_label} Avg", line=dict(color='#ff7f0e', dash='dash')))
                    fig_t.update_layout(title=f"Weekly Total {m}", xaxis=dict(dtick=1), height=300, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)

    # --- TAB 4: TOURNAMENT SUMMARY ---
    with tabs[4]:
        st.markdown('<div class="section-header">Tournament Match Comparison</div>', unsafe_allow_html=True)
        
        with st.container():
            c_ts1, c_ts2 = st.columns([2, 1])
            with c_ts1:
                # Sorted specifically by original entry order
                game_list_t = df[df['Session_Type'] == 'Game'].sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique()
                selected_games = st.multiselect("Select Tournament Matches", game_list_t, default=game_list_t[-3:] if len(game_list_t) >=3 else game_list_t, key="tourney_multi")
            with c_ts2:
                pos_filter_t = st.selectbox("Filter by Position", ["All Positions"] + sorted(list(df['Position'].unique())), key="tourney_pos_filter")

        if selected_games:
            st.markdown('<div class="section-header">Athlete Match-by-Match Breakdown</div>', unsafe_allow_html=True)
            # Re-sort display df by Sheet_Order to keep double-headers aligned
            tourney_df = df[df['Session_Name'].isin(selected_games)].sort_values(['Date', 'Sheet_Order'])
            
            if pos_filter_t != "All Positions":
                tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]
                
            athletes_t = sorted(tourney_df['Name'].unique())
            t_metrics = ['Total Jumps', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts']

            for i in range(0, len(athletes_t), 2):
                card_cols = st.columns(2)
                for j in range(2):
                    if i + j < len(athletes_t):
                        ath_name_t = athletes_t[i+j]
                        ath_data_t = tourney_df[tourney_df['Name'] == ath_name_t]
                        with card_cols[j]:
                            card_html = f"""
                            <div class="gallery-card">
                                <div style="display:flex; align-items:center; gap:15px; padding:15px; background:#f8f9fa; border-radius:15px 15px 0 0; border-bottom:2px solid #FF8200;">
                                    <img src="{ath_data_t['PhotoURL'].iloc[0]}" class="gallery-photo">
                                    <div>
                                        <p style="margin:0; font-weight:900; color:#1D1D1F; font-size:18px;">{ath_name_t}</p>
                                        <p style="margin:0; color:#4895DB; font-weight:700; font-size:12px;">{ath_data_t['Position'].iloc[0]}</p>
                                    </div>
                                </div>
                                <div style="padding:10px;">
                                    <table class="scout-table">
                                        <thead><tr><th>Match</th><th>Jumps</th><th>Load</th><th>Dist</th><th>Effort</th></tr></thead>
                                        <tbody>
                            """
                            for _, r in ath_data_t.iterrows():
                                card_html += f"<tr><td style='font-weight:700;'>{r['Session_Name']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.0f}</td><td>{r['Estimated Distance (y)']:.0f}</td><td>{r['Explosive Efforts']:.0f}</td></tr>"
                            card_html += f"<tr style='background:#4895DB; color:white; font-weight:900;'><td>TOTAL</td><td>{int(ath_data_t['Total Jumps'].sum())}</td><td>{ath_data_t['Player Load'].sum():.0f}</td><td>{ath_data_t['Estimated Distance (y)'].sum():.0f}</td><td>{ath_data_t['Explosive Efforts'].sum():.0f}</td></tr></tbody></table>"
                            st.markdown(card_html + "</div>", unsafe_allow_html=True)
                            
                            fig_radar = go.Figure()
                            for _, r in ath_data_t.iterrows():
                                fig_radar.add_trace(go.Scatterpolar(r=[r[m] for m in t_metrics], theta=t_metrics, fill='toself', name=r['Session_Name']))
                            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False)), height=220, margin=dict(l=40, r=40, t=10, b=10), legend=dict(orientation="h", y=-0.3))
                            st.plotly_chart(fig_radar, use_container_width=True, config=LOCKED_CONFIG)
                            st.markdown("</div>", unsafe_allow_html=True)

            st.write("---")
            st.markdown('<div class="section-header">Team Tournament Averages</div>', unsafe_allow_html=True)
            # Use original order for x-axis categories
            team_avg_t = df[df['Session_Name'].isin(selected_games)].groupby(['Session_Name', 'Sheet_Order'])[t_metrics].mean().reset_index().sort_values('Sheet_Order')
            
            g_cols_t = st.columns(4)
            for idx, m in enumerate(t_metrics):
                with g_cols_t[idx]:
                    fig_t = px.bar(team_avg_t, x='Session_Name', y=m, color='Session_Name', color_discrete_sequence=['#4895DB', '#FF8200', '#515154'])
                    fig_t.update_layout(showlegend=False, height=300, margin=dict(l=50, r=10, t=60, b=80), xaxis_title=None, template="simple_white")
                    st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)

except Exception as e:
    st.error(f"Sync Error: {e}")
