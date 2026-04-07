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

# --- CSS: FORMATTING & AGGRESSIVE PRINT HIDING ---
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

    @media print {
        /* Hide UI controls and stubborn labels */
        .stTabs [role="tablist"], 
        .no-print, 
        [data-testid="stSidebar"], 
        .print-hide,
        [data-testid="stHeader"],
        [data-baseweb="select"],
        [data-testid="stMultiSelect"],
        [data-testid="stWidgetLabel"],
        label,
        header, 
        button { 
            display: none !important; 
        }
        .main .block-container { padding: 0 !important; }
        .gallery-card { break-inside: avoid; border: 1px solid #EEE !important; }
    }
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
        'BMP Jumping Load': 'Jump Load', 'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance (y)', 
        'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movement'
    }
    df = df.rename(columns=rename_map)
    df['Session_Type'] = df['Activity'].apply(lambda x: 'Match' if any(w in str(x).lower() for w in ['game', 'match', 'v.', 'vs']) else 'Practice')
    avail = [v for v in rename_map.values() if v in df.columns]
    for col in avail: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).round(1)
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

LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

try:
    df, cmj_df, phase_df = load_all_data()
    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
    
    st.markdown('<h1 style="color:#FF8200; text-align:center; font-family:sans-serif; font-weight:900;">Lady Vol Volleyball Performance</h1>', unsafe_allow_html=True)
    st.markdown('<div style="height:4px; background-color:#FF8200; width:100%; margin-bottom:20px;"></div>', unsafe_allow_html=True)

    tabs = st.tabs(["Individual Profile", "Team Gallery", "Match v. Practice", "Position Analysis", "Match Summary"])
    session_list = df[['Date', 'Sheet_Order', 'Session_Name']].drop_duplicates(subset=['Session_Name']).sort_values(['Date', 'Sheet_Order'], ascending=[False, False])['Session_Name'].tolist()

    # --- TAB 0, 1, 2, 3 Logic ---
    with tabs[0]:
        c_f1, c_f2 = st.columns(2)
        with c_f1: selected_session = st.selectbox("Practice Selection", session_list, index=0, key="nav_sel_ind")
        with c_f2: pos_f = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_ind")
        day_df = df[df['Session_Name'] == selected_session].copy()
        if not day_df.empty:
            curr_date = day_df['Date'].iloc[0]
            if pos_f != "All Positions": day_df = day_df[day_df['Position'] == pos_f]
            sel_p = st.selectbox("Select Athlete", sorted(day_df['Name'].unique()))
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

    with tabs[1]:
        c_gal1, c_gal2 = st.columns(2)
        with c_gal1: selected_session_gal = st.selectbox("Practice Selection", session_list, index=0, key="nav_sel_gal")
        with c_gal2: pos_f_gal = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]), key="nav_pos_gal")
        gal_df = df[df['Session_Name'] == selected_session_gal].copy()
        if not gal_df.empty:
            for i in range(0, len(gal_df), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(gal_df):
                        pd_row = gal_df.iloc[i + j]; lb_g = df[(df['Name'] == pd_row['Name']) & (df['Date'] >= pd_row['Date'] - timedelta(days=30)) & (df['Date'] <= pd_row['Date'])]; r_html = ""
                        for k in ['Total Jumps', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts']:
                            v, m = pd_row[k], lb_g[k].max(); g = math.ceil((v / m) * 100) if m > 0 else 0; r_html += f"<tr><td>{k}</td><td>{v}</td><td>{g}</td></tr>"
                        with cols[j]: st.markdown(f'<div class="gallery-card"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{pd_row["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px;">{pd_row["Name"]}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Val</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div></div></div>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="section-header">Weekly Intensity Analysis</div>', unsafe_allow_html=True)
        c_ga, c_gw, c_gg = st.columns(3)
        with c_ga: gp_p = st.selectbox("Athlete", sorted(df['Name'].unique()), key="gp_p_vf")
        with c_gw:
            w_r = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index(); gp_w = st.selectbox("Week", w_r.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1), key="gp_w_vf"); sel_w = int(gp_w.split(' ')[0])
        with c_gg: match_opts = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Match') & (df['Week'] == sel_w)]['Session_Name'].unique(); gp_g = st.selectbox("Select Match", match_opts, key="gp_g_vf")
        w_data = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Practice') & (df['Week'] == sel_w)]; g_data_l = df[(df['Name'] == gp_p) & (df['Session_Name'] == gp_g)]
        if not w_data.empty and not g_data_l.empty:
            low_m = ['Total Jumps', 'Player Load', 'Explosive Efforts']; w_avg = w_data[low_m + ['Estimated Distance (y)']].mean(); g_d = g_data_l.iloc[0]; cg1, cg2 = st.columns([1, 2])
            with cg1:
                for m in low_m + ['Estimated Distance (y)']: st.metric(label=m, value=f"{g_d[m]:.0f}", delta=f"{(w_avg[m]-g_d[m])/g_d[m]*100:+.1f}%")
            with cg2:
                fig_dual = make_subplots(specs=[[{"secondary_y": True}]]); fig_dual.add_trace(go.Bar(x=low_m, y=[w_avg[m] for m in low_m], name="Weekly Avg", marker_color='#4895DB'), secondary_y=False); fig_dual.add_trace(go.Bar(x=low_m, y=[g_d[m] for m in low_m], name=f"Match Output", marker_color='#FF8200'), secondary_y=False); fig_dual.update_layout(height=400, barmode='group'); st.plotly_chart(fig_dual, use_container_width=True)
            wk_df = df[(df['Name'] == gp_p) & (df['Week'] == sel_w)].sort_values('Sheet_Order')
            fig_trend = px.line(wk_df, x='Session_Name', y='Player Load', markers=True); fig_trend.update_traces(line_color='#FF8200', marker_size=12); st.plotly_chart(fig_trend, use_container_width=True, config=LOCKED_CONFIG)

    with tabs[3]:
        st.markdown('<div class="section-header">Positional Performance Trends</div>', unsafe_allow_html=True)

    # --- TAB 4: MATCH SUMMARY ---
    with tabs[4]:
        st.markdown('<div class="no-print">', unsafe_allow_html=True)
        if st.button("🖨️ Prepare PDF Report"): st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        st.markdown('<div class="print-hide">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Match Comparison Selection</div>', unsafe_allow_html=True)
        c_ts1, c_ts2 = st.columns([2, 1])
        with c_ts1:
            match_list_t = df[df['Session_Type'] == 'Match'].sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique()
            selected_matches = st.multiselect("Select Weekend Matches", match_list_t, default=match_list_t[-3:] if len(match_list_t) >=3 else match_list_t)
        with c_ts2:
            pos_filter_t = st.selectbox("Filter by Position", ["All Positions"] + sorted(list(df['Position'].unique())), key="ms_pos_final")
        st.markdown('</div></div>', unsafe_allow_html=True)

        if selected_matches:
            color_palette = ['#4895DB', '#FF8200', '#515154']; match_color_map = {m: color_palette[i % 3] for i, m in enumerate(selected_matches)}
            st.markdown('<div class="section-header">Athlete Match Performance Breakdown</div>', unsafe_allow_html=True)
            tourney_df = df[df['Session_Name'].isin(selected_matches)].sort_values(['Date', 'Sheet_Order'])
            if pos_filter_t != "All Positions": tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]
            ath_t = sorted(tourney_df['Name'].unique())

            for i in range(0, len(ath_t), 2):
                card_cols = st.columns(2)
                for j in range(2):
                    if i + j < len(ath_t):
                        name = ath_t[i+j]; ad = tourney_df[tourney_df['Name'] == name]
                        with card_cols[j]:
                            card_html = f"""
                            <div class="gallery-card">
                                <div style="display:flex; align-items:center; gap:15px; padding:15px; background:#f8f9fa; border-bottom:2px solid #FF8200;">
                                    <img src="{ad['PhotoURL'].iloc[0]}" class="gallery-photo" style="width:70px; height:70px;">
                                    <div>
                                        <p style="margin:0; font-weight:900; color:#1D1D1F; font-size:18px;">{name}</p>
                                        <p style="margin:0; color:#4895DB; font-weight:700; font-size:12px;">{ad['Position'].iloc[0]}</p>
                                    </div>
                                </div>
                                <div style="padding:10px 15px;">
                                    <table class="scout-table" style="margin-bottom:0;">
                                        <thead><tr><th>Match</th><th>Total Jumps</th><th>Player Load</th><th>Est Dist (y)</th><th>Explosive Efforts</th></tr></thead>
                                        <tbody>
                            """
                            for _, r in ad.iterrows():
                                card_html += f"<tr><td>{r['Session_Name']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.0f}</td><td>{r['Estimated Distance (y)']:.0f}</td><td>{r['Explosive Efforts']:.0f}</td></tr>"
                            card_html += f"<tr style='background:#4895DB; color:white; font-weight:900;'><td>TOTAL</td><td>{int(ad['Total Jumps'].sum())}</td><td>{ad['Player Load'].sum():.0f}</td><td>{ad['Estimated Distance (y)'].sum():.0f}</td><td>{ad['Explosive Efforts'].sum():.0f}</td></tr></tbody></table></div>"
                            st.markdown(card_html, unsafe_allow_html=True)
                            
                            fig_ath = make_subplots(specs=[[{"secondary_y": True}]]);
                            for _, r in ad.iterrows():
                                fig_ath.add_trace(go.Bar(name=r['Session_Name'], x=['Jumps', 'Load', 'Effort'], y=[r['Total Jumps'], r['Player Load'], r['Explosive Efforts']], marker_color=match_color_map[r['Session_Name']]), secondary_y=False)
                                fig_ath.add_trace(go.Bar(name="Dist", x=['Distance'], y=[r['Estimated Distance (y)']], marker=dict(color=match_color_map[r['Session_Name']], opacity=0.6), showlegend=False), secondary_y=True)
                            fig_ath.update_layout(barmode='group', height=300, showlegend=False, template="simple_white"); st.plotly_chart(fig_ath, use_container_width=True, config=LOCKED_CONFIG); st.markdown("</div>", unsafe_allow_html=True)

            st.write("<br><br>", unsafe_allow_html=True); st.markdown('<div class="section-header">Team Match Averages</div>', unsafe_allow_html=True)
            team_avg_t = tourney_df.groupby(['Session_Name', 'Sheet_Order'])[['Total Jumps', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts']].mean().reset_index().sort_values('Sheet_Order')
            c1, c2 = st.columns(2); c3, c4 = st.columns(2); cols = [c1, c2, c3, c4]
            for idx, m in enumerate(['Total Jumps', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts']):
                with cols[idx]:
                    fig_t = go.Figure(); fig_t.add_trace(go.Bar(x=team_avg_t['Session_Name'], y=team_avg_t[m], marker_color=[match_color_map[g] for g in team_avg_t['Session_Name']], marker_line_width=0))
                    fig_t.update_layout(title=f"Team Avg: {m}", showlegend=False, height=400, template="simple_white", bargap=0.01); st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)

except Exception as e:
    st.error(f"Sync Error: {e}")
