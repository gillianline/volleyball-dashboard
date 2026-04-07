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
    .gallery-card { border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; min-height: 380px; display: flex; flex-direction: column; justify-content: center; }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
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
    df = pd.read_csv(get_fresh_url(st.secrets["GOOGLE_SHEET_URL"]))
    df['Sheet_Order'] = range(len(df))
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date']) 
    if 'Week' in df.columns:
        df['Week'] = pd.to_numeric(df['Week'].astype(str).str.extract('(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
    
    rename_map = {
        'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps', 'IMA Jump Count High Band': 'High Jumps', 
        'BMP Jumping Load': 'Jump Load', 'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance', 
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
    
    cmj_df = pd.read_csv(get_fresh_url(st.secrets["CMJ_SHEET_URL"]))
    cmj_df.columns = cmj_df.columns.str.strip()
    cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
    
    phase_df = pd.read_csv(get_fresh_url(st.secrets["PHASES_SHEET_URL"]))
    phase_df.columns = phase_df.columns.str.strip()
    if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
    phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
    phase_df = phase_df.rename(columns=rename_map)
    return df, cmj_df, phase_df

try:
    df, cmj_df, phase_df = load_all_data()
    LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}
    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movement']

    st.markdown("""
        <div style="text-align: center; margin-top: 10px; margin-bottom: 15px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120">
            <div style='color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;'>LADY VOLS VOLLEYBALL PERFORMANCE</div>
        </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["Individual Profile", "Team Gallery", "Game v. Practice", "Position Analysis", "Tournament Summary"])
    session_list = df[['Date', 'Sheet_Order', 'Session_Name']].drop_duplicates(subset=['Session_Name']).sort_values(['Date', 'Sheet_Order'], ascending=[False, False])['Session_Name'].tolist()

    # --- TAB 0: INDIVIDUAL PROFILE (RESTORED) ---
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
            for k in ['Total Jumps', 'Player Load', 'Estimated Distance', 'Explosive Efforts']:
                val, mx, avg = p[k], lb[k].max(), lb[k].mean()
                grade = math.ceil((val / mx) * 100) if mx > 0 else 0
                total_grade += grade; count += 1
                diff = (val - avg) / avg if avg != 0 else 0
                h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                m_rows += f"<tr><td>{k}</td><td {h_class}>{val} {arr_val}</td><td>{mx}</td><td>{grade}</td></tr>"
            
            score = math.ceil(total_grade / count)
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
                    base_h, base_rsi = p_cmj_hist.tail(6).iloc[:-1]['Jump Height (in)'].mean(), p_cmj_hist.tail(6).iloc[:-1]['RSI-modified [m/s]'].mean()
                    p_diff = ((latest['Jump Height (in)'] - base_h) / base_h) * 100
                    color = "#28a745" if latest['Jump Height (in)'] >= base_h else "#dc3545"
                    st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color};">{p_diff:+.1f}%</div></div>', unsafe_allow_html=True)
            with jc2:
                if not p_cmj_hist.empty:
                    fig = make_subplots(specs=[[{"secondary_y": True}]]); fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist['Jump Height (in)'], name="Height", line=dict(color='#FF8200', width=3)), secondary_y=False); fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist['RSI-modified [m/s]'], name="RSI", line=dict(color='#4895DB', dash='dot')), secondary_y=True); fig.update_layout(height=280, showlegend=False); st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG)
            
            p_ph = phase_df[(phase_df['Name'] == sel_p) & (phase_df['Date'] == curr_date)].copy()
            if not p_ph.empty:
                st.markdown('<div class="section-header">Practice Phase Breakdown</div>', unsafe_allow_html=True)
                fig_ph = make_subplots(specs=[[{"secondary_y": True}]]); fig_ph.add_trace(go.Bar(x=p_ph['Phase'], y=p_ph['Total Jumps'], name="Jumps", marker_color='#FF8200'), secondary_y=False); fig_ph.add_trace(go.Scatter(x=p_ph['Phase'], y=p_ph['Player Load'], name="Load", line=dict(color='#4895DB', width=4)), secondary_y=False); fig_ph.update_layout(height=350, showlegend=True); st.plotly_chart(fig_ph, use_container_width=True, config=LOCKED_CONFIG)

    # --- TAB 1: TEAM GALLERY (RESTORED) ---
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
                        for k in ['Total Jumps', 'Player Load', 'Estimated Distance', 'Explosive Efforts']:
                            v, m = pd_row[k], lb_g[k].max()
                            g = math.ceil((v / m) * 100) if m > 0 else 0
                            t_grade += g; c_metrics += 1; r_html += f"<tr><td>{k}</td><td>{v}</td><td>{m}</td><td>{g}</td></tr>"
                        sc_g = math.ceil(t_grade / c_metrics)
                        with cols[j]: st.markdown(f'<div class="gallery-card"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{pd_row["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px;">{pd_row["Name"]}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Val</th><th>Max</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div><div style="flex:1; text-align:center;"><div style="background-color:{get_flipped_gradient(sc_g)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{sc_g}</div></div></div></div>', unsafe_allow_html=True)

    # --- TAB 2: GAME V PRACTICE (RESTORED TREND GRAPH) ---
    with tabs[2]:
        st.markdown('<div class="section-header">Weekly Prep Intensity vs. Game Demands</div>', unsafe_allow_html=True)
        c_ga, c_gw, c_gg = st.columns(3)
        with c_ga: gp_p = st.selectbox("Athlete", sorted(df['Name'].unique()), key="gp_p_vf")
        with c_gw:
            w_r = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index(); gp_w = st.selectbox("Week", w_r.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1), key="gp_w_vf"); sel_w = int(gp_w.split(' ')[0])
        with c_gg: 
            game_opts = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Game') & (df['Week'] == sel_w)].sort_values('Sheet_Order')['Session_Name'].unique(); gp_g = st.selectbox("Select Game", game_opts, key="gp_g_vf")
        w_data = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Practice') & (df['Week'] == sel_w)]; g_data_l = df[(df['Name'] == gp_p) & (df['Session_Name'] == gp_g)]
        if not w_data.empty and not g_data_l.empty:
            cg1, cg2 = st.columns([1, 2]); w_avg = w_data[['Total Jumps', 'Player Load', 'Estimated Distance', 'Explosive Efforts']].mean(); g_d = g_data_l.iloc[0]
            with cg1:
                for m in ['Total Jumps', 'Player Load', 'Estimated Distance', 'Explosive Efforts']: st.metric(label=m, value=f"{g_d[m]:.0f}", delta=f"{(w_avg[m]-g_d[m])/g_d[m]*100:+.1f}% vs Avg")
            with cg2:
                fig_v = make_subplots(specs=[[{"secondary_y": True}]]); fig_v.add_trace(go.Bar(x=['Total Jumps', 'Player Load', 'Explosive Efforts'], y=[w_avg[m] for m in ['Total Jumps', 'Player Load', 'Explosive Efforts']], name="Weekly Avg", marker_color='#4895DB'), secondary_y=False); fig_v.add_trace(go.Bar(x=['Total Jumps', 'Player Load', 'Explosive Efforts'], y=[g_d[m] for m in ['Total Jumps', 'Player Load', 'Explosive Efforts']], name="Game Output", marker_color='#FF8200'), secondary_y=False); fig_v.add_trace(go.Bar(x=['Estimated Distance'], y=[w_avg['Estimated Distance']], name="Weekly Dist", marker=dict(color='#4895DB', opacity=0.6, line=dict(color='#4895DB', width=2))), secondary_y=True); fig_v.add_trace(go.Bar(x=['Estimated Distance'], y=[g_d['Estimated Distance']], name="Game Dist", marker=dict(color='#FF8200', opacity=0.6, line=dict(color='#FF8200', width=2))), secondary_y=True); fig_v.update_layout(height=400, barmode='group'); st.plotly_chart(fig_v, use_container_width=True, config=LOCKED_CONFIG)
            
            st.markdown('<div class="section-header">Weekly Load Trend Leading to Game</div>', unsafe_allow_html=True)
            wk_df = df[(df['Name'] == gp_p) & (df['Week'] == sel_w)].sort_values('Date')
            fig_trend = px.line(wk_df, x='Date', y='Player Load', markers=True, title="Daily Player Load Context"); fig_trend.update_traces(line_color='#FF8200', marker_size=12); st.plotly_chart(fig_trend, use_container_width=True, config=LOCKED_CONFIG)

    # --- TAB 3: POSITION ANALYSIS ---
    with tabs[3]:
        sel_p_pos = st.selectbox("Select Athlete for Comparative Trend", sorted(df['Name'].unique()), key="athlete_sel_pos"); p_pos = df[df['Name'] == sel_p_pos].iloc[0]; pos_label = p_pos['Position']; max_wk = df['Week'].max(); rec_4 = list(range(int(max_wk)-3, int(max_wk)+1)); tr_df = df[df['Week'].isin(rec_4)]; t_col1, t_col2, t_col3 = st.columns(3)
        for i, m in enumerate(["Player Load", "Estimated Distance", "Total Jumps"]):
            with [t_col1, t_col2, t_col3][i]:
                fig_t = go.Figure(); fig_t.add_trace(go.Scatter(x=rec_4, y=tr_df[tr_df['Name']==sel_p_pos].groupby('Week')[m].sum(), name=sel_p_pos, line=dict(color='#0046ad', width=4))); fig_t.add_trace(go.Scatter(x=rec_4, y=tr_df[tr_df['Position']==pos_label].groupby(['Week', 'Name'])[m].sum().groupby('Week').mean(), name="Pos Avg", line=dict(color='#ff7f0e', dash='dash'))); st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)

    # --- TAB 4: TOURNAMENT SUMMARY ---
    with tabs[4]:
        st.markdown('<div class="section-header">Tournament Match Comparison</div>', unsafe_allow_html=True)
        game_list_t = df[df['Session_Type'] == 'Game'].sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique(); selected_games = st.multiselect("Select Weekend Matches", game_list_t, default=game_list_t[-3:] if len(game_list_t) >=3 else game_list_t, key="tourney_multi")
        if selected_games:
            game_color_map = {game: ['#4895DB', '#FF8200', '#515154'][i % 3] for i, game in enumerate(selected_games)}
            tourney_df = df[df['Session_Name'].isin(selected_games)].sort_values(['Date', 'Sheet_Order']); athletes_t = sorted(tourney_df['Name'].unique())
            for i in range(0, len(athletes_t), 2):
                card_cols = st.columns(2)
                for j in range(2):
                    if i + j < len(athletes_t):
                        ath_name_t = athletes_t[i+j]; ath_data_t = tourney_df[tourney_df['Name'] == ath_name_t]
                        with card_cols[j]:
                            card_html = f'<div class="gallery-card"><div style="display:flex; align-items:center; gap:15px; padding:15px; background:#f8f9fa; border-bottom:2px solid #FF8200;"><img src="{ath_data_t["PhotoURL"].iloc[0]}" class="gallery-photo"><div><p style="font-weight:900; font-size:18px;">{ath_name_t}</p><p style="color:#4895DB; font-weight:700;">{ath_data_t["Position"].iloc[0]}</p></div></div><div style="padding:10px 15px;"><table class="scout-table"><thead><tr><th>Match</th><th>Total Jumps</th><th>Player Load</th><th>Estimated Distance</th><th>Explosive Efforts</th></tr></thead><tbody>'
                            for _, r in ath_data_t.iterrows(): card_html += f"<tr><td style='font-weight:700;'>{r['Session_Name']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.0f}</td><td>{r['Estimated Distance']:.0f}</td><td>{r['Explosive Efforts']:.0f}</td></tr>"
                            card_html += f"<tr style='background:#4895DB; color:white; font-weight:900;'><td>TOTAL</td><td>{int(ath_data_t['Total Jumps'].sum())}</td><td>{ath_data_t['Player Load'].sum():.0f}</td><td>{ath_data_t['Estimated Distance'].sum():.0f}</td><td>{ath_data_t['Explosive Efforts'].sum():.0f}</td></tr></tbody></table></div>"
                            st.markdown(card_html, unsafe_allow_html=True)
                            fig_ath = make_subplots(specs=[[{"secondary_y": True}]]);
                            for _, r in ath_data_t.iterrows():
                                fig_ath.add_trace(go.Bar(name=r['Session_Name'], x=['Total Jumps', 'Player Load', 'Explosive Efforts'], y=[r['Total Jumps'], r['Player Load'], r['Explosive Efforts']], marker_color=game_color_map[r['Session_Name']]), secondary_y=False)
                                fig_ath.add_trace(go.Bar(name=f"Distance", x=['Estimated Distance'], y=[r['Estimated Distance']], marker=dict(color=game_color_map[r['Session_Name']], opacity=0.6, line=dict(color=game_color_map[r['Session_Name']], width=2)), showlegend=False), secondary_y=True)
                            fig_ath.update_layout(barmode='group', height=320, legend=dict(orientation="h", y=-0.2), template="simple_white"); st.plotly_chart(fig_ath, use_container_width=True, config=LOCKED_CONFIG); st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">Team Tournament Averages</div>', unsafe_allow_html=True)
            t_avg = df[df['Session_Name'].isin(selected_games)].groupby(['Session_Name', 'Sheet_Order'])[['Total Jumps', 'Player Load', 'Estimated Distance', 'Explosive Efforts']].mean().reset_index().sort_values('Sheet_Order')
            r1c1, r1c2 = st.columns(2); r2c1, r2c2 = st.columns(2)
            for idx, m in enumerate(['Total Jumps', 'Player Load', 'Estimated Distance', 'Explosive Efforts']):
                with [r1c1, r1c2, r2c1, r2c2][idx]:
                    fig_t = go.Figure(); fig_t.add_trace(go.Bar(x=t_avg['Session_Name'], y=t_avg[m], marker_color=[game_color_map[g] for g in t_avg['Session_Name']], marker_line_width=0))
                    fig_t.update_layout(title=f"Team Avg: {m}", height=400, template="simple_white", bargap=0.0); st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)
except Exception as e:
    st.error(f"Sync Error: {e}")
