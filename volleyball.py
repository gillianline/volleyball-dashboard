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

# --- CSS: FORMATTING & PRINT OPTIMIZATION ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    .viewerBadge_link__1S137, .main_heading_anchor__m6v0K, a.header-anchor { display: none !important; }
    header a { display: none !important; }
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #4895DB; color: white; padding: 4px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 10px; text-transform: uppercase; }
    .scout-table td { padding: 4px; border-bottom: 1px solid #F5F5F7; font-size: 10px; }
    .bg-highlight-red { background-color: #ffcccc !important; font-weight: 900; }
    .arrow-red { color: #b30000 !important; font-weight: 900; margin-left: 4px; }
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    .score-box { padding: 12px 20px; border-radius: 12px; font-size: 28px; font-weight: 800; min-width: 100px; color: #FFFFFF; line-height: 1.2; text-align: center;}
    .gallery-card { border: 1px solid #E5E5E7; padding: 0; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 20px; overflow: hidden; }
    .gallery-photo { border-radius: 50%; width: 60px; height: 60px; object-fit: cover; border: 3px solid #FF8200; }
    .section-header { font-size: 14px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    .info-box { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 12px; margin-top: 10px; font-size: 12px; color: #1D1D1F; font-weight: 600; line-height: 1.4; }
    
    /* Print Logic */
    @media print {
        button[title="View fullscreen"] { display: none !important; }
        .no-print { display: none !important; }
        .stTabs { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stHeader"] { display: none !important; }
        .main .block-container { padding: 0 !important; }
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

try:
    df, cmj_df, phase_df = load_all_data()
    LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}
    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']

    # --- SIDEBAR CONTROLS ---
    st.sidebar.header("Dashboard Controls")
    print_mode = st.sidebar.toggle("Enable Clean Print Mode", help="Hides UI and formats for PDF")

    if not print_mode:
        st.markdown("""
            <div style="text-align: center; margin-top: 10px; margin-bottom: 15px;">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120">
                <div style='color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;'>LADY VOLS VOLLEYBALL PERFORMANCE</div>
            </div>
        """, unsafe_allow_html=True)
        tabs = st.tabs(["Individual Profile", "Team Gallery", "Match v. Practice", "Position Analysis", "Match Summary"])
    else:
        st.markdown("<h1 style='text-align:center; color:#FF8200;'>MATCH PERFORMANCE REPORT</h1>", unsafe_allow_html=True)
        # In print mode, we skip the tabs and go straight to the content of Tab 4

    session_list = df[['Date', 'Sheet_Order', 'Session_Name']].drop_duplicates(subset=['Session_Name']).sort_values(['Date', 'Sheet_Order'], ascending=[False, False])['Session_Name'].tolist()

    # --- TAB 0, 1, 2, 3 LOGIC (HIDDEN IF PRINT MODE) ---
    if not print_mode:
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
                m_rows = ""
                for k in ['Total Jumps', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts']:
                    val, mx, avg = p[k], lb[k].max(), lb[k].mean()
                    grade = math.ceil((val / mx) * 100) if mx > 0 else 0
                    diff = (val - avg) / avg if avg != 0 else 0
                    h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                    m_rows += f"<tr><td>{k}</td><td {h_class}>{val}</td><td>{mx}</td><td>{grade}</td></tr>"
                c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
                with c1: st.markdown(f'<div style="text-align:center;"><img src="{p["PhotoURL"]}" class="player-photo-large"></div><h3 style="text-align:center;">{p["Name"]}</h3>', unsafe_allow_html=True)
                with c2: st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>{m_rows}</tbody></table>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(math.ceil(p["Total Jumps"]/10))};">85</div></div>', unsafe_allow_html=True)

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
                            pd_row = gal_df.iloc[i + j]
                            with cols[j]: st.markdown(f'<div class="gallery-card"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{pd_row["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px;">{pd_row["Name"]}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Val</th><th>Max</th><th>Grade</th></tr></thead><tbody><tr><td>Jumps</td><td>{pd_row["Total Jumps"]}</td><td>100</td><td>90</td></tr></tbody></table></div></div></div>', unsafe_allow_html=True)

        with tabs[2]:
            st.markdown('<div class="section-header">Weekly Prep Intensity vs. Match Demands</div>', unsafe_allow_html=True)
            c_ga, c_gw, c_gg = st.columns(3)
            with c_ga: gp_p = st.selectbox("Athlete", sorted(df['Name'].unique()), key="gp_p_vf")
            with c_gw:
                w_r = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index(); gp_w = st.selectbox("Week", w_r.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1), key="gp_w_vf"); sel_w = int(gp_w.split(' ')[0])
            with c_gg: 
                match_opts = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Match') & (df['Week'] == sel_w)].sort_values('Sheet_Order')['Session_Name'].unique(); gp_g = st.selectbox("Select Match", match_opts, key="gp_g_vf")
            w_data = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Practice') & (df['Week'] == sel_w)]; g_data_l = df[(df['Name'] == gp_p) & (df['Session_Name'] == gp_g)]
            if not w_data.empty and not g_data_l.empty:
                cg1, cg2 = st.columns([1, 2]); w_avg = w_data[['Total Jumps', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts']].mean(); g_d = g_data_l.iloc[0]
                with cg1:
                    for m in ['Total Jumps', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts']: st.metric(label=m, value=f"{g_d[m]:.0f}", delta=f"{(w_avg[m]-g_d[m])/g_d[m]*100:+.1f}%")
                with cg2:
                    fig_v = make_subplots(specs=[[{"secondary_y": True}]]); fig_v.add_trace(go.Bar(x=['Total Jumps', 'Player Load', 'Explosive Efforts'], y=[w_avg[m] for m in ['Total Jumps', 'Player Load', 'Explosive Efforts']], name="Avg", marker_color='#4895DB'), secondary_y=False); fig_v.add_trace(go.Bar(x=['Total Jumps', 'Player Load', 'Explosive Efforts'], y=[g_d[m] for m in ['Total Jumps', 'Player Load', 'Explosive Efforts']], name="Match", marker_color='#FF8200'), secondary_y=False); st.plotly_chart(fig_v, use_container_width=True)

        with tabs[3]:
            st.markdown('<div class="section-header">Positional Performance Trends</div>', unsafe_allow_html=True)
            sel_p_pos = st.selectbox("Select Athlete for Comparative Trend", sorted(df['Name'].unique()), key="athlete_sel_pos")
            p_pos = df[df['Name'] == sel_p_pos].iloc[0]; pos_label = p_pos['Position']; max_wk = df['Week'].max(); rec_4 = list(range(int(max_wk)-3, int(max_wk)+1)); tr_df = df[df['Week'].isin(rec_4)]; t_col1, t_col2, t_col3 = st.columns(3)
            for i, m in enumerate(["Player Load", "Estimated Distance (y)", "Total Jumps"]):
                with [t_col1, t_col2, t_col3][i]:
                    fig_t = go.Figure(); fig_t.add_trace(go.Scatter(x=rec_4, y=tr_df[tr_df['Name']==sel_p_pos].groupby('Week')[m].sum(), name=sel_p_pos)); st.plotly_chart(fig_t, use_container_width=True)

    # --- TAB 4 / PRINT CONTENT: MATCH SUMMARY ---
    # We display this content if we're in print mode OR if the user clicked Tab 4
    if print_mode:
        container = st.container()
    else:
        container = tabs[4]

    with container:
        # Hide the selection widgets when printing to save space
        if not print_mode:
            st.markdown('<div class="section-header">Match Comparison Selection</div>', unsafe_allow_html=True)
            with st.container():
                c_ts1, c_ts2 = st.columns([2, 1])
                with c_ts1:
                    match_list_t = df[df['Session_Type'] == 'Match'].sort_values(['Date', 'Sheet_Order'])['Session_Name'].unique()
                    selected_matches = st.multiselect("Select Weekend Matches", match_list_t, default=match_list_t[-3:] if len(match_list_t) >=3 else match_list_t, key="tourney_multi")
                with c_ts2:
                    pos_filter_t = st.selectbox("Filter by Position", ["All Positions"] + sorted(list(df['Position'].unique())), key="tourney_pos_filter")
        else:
            # If printing, use the existing state from before turning on print mode or defaults
            selected_matches = st.session_state.get("tourney_multi", session_list[:3])
            pos_filter_t = st.session_state.get("tourney_pos_filter", "All Positions")

        if selected_matches:
            color_palette = ['#4895DB', '#FF8200', '#515154']
            match_color_map = {m: color_palette[i % len(color_palette)] for i, m in enumerate(selected_matches)}
            
            st.markdown('<div class="section-header">Athlete Match-by-Match Performance</div>', unsafe_allow_html=True)
            tourney_df = df[df['Session_Name'].isin(selected_matches)].sort_values(['Date', 'Sheet_Order'])
            if pos_filter_t != "All Positions":
                tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]
            athletes_t = sorted(tourney_df['Name'].unique())
            
            # Print Mode: Use 3 columns to fit more. Normal Mode: Use 2 columns.
            n_cols = 3 if print_mode else 2
            for i in range(0, len(athletes_t), n_cols):
                card_cols = st.columns(n_cols)
                for j in range(n_cols):
                    if i + j < len(athletes_t):
                        ath_name_t = athletes_t[i+j]
                        ath_data_t = tourney_df[tourney_df['Name'] == ath_name_t]
                        with card_cols[j]:
                            card_html = f"""
                            <div class="gallery-card">
                                <div style="display:flex; align-items:center; gap:10px; padding:10px; background:#f8f9fa; border-bottom:2px solid #FF8200;">
                                    <img src="{ath_data_t['PhotoURL'].iloc[0]}" class="gallery-photo">
                                    <div>
                                        <p style="margin:0; font-weight:900; font-size:14px;">{ath_name_t}</p>
                                        <p style="margin:0; color:#4895DB; font-weight:700; font-size:10px;">{ath_data_t['Position'].iloc[0]}</p>
                                    </div>
                                </div>
                                <div style="padding:5px;">
                                    <table class="scout-table" style="margin-bottom:0;">
                                        <thead><tr><th>Match</th><th>Jumps</th><th>Load</th><th>Dist</th><th>Effort</th></tr></thead>
                                        <tbody>
                            """
                            for _, r in ath_data_t.iterrows():
                                card_html += f"<tr><td style='font-weight:700;'>{r['Session_Name'][:10]}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.0f}</td><td>{r['Estimated Distance (y)']:.0f}</td><td>{r['Explosive Efforts']:.0f}</td></tr>"
                            card_html += f"</tbody></table></div>"
                            st.markdown(card_html, unsafe_allow_html=True)
                            
                            fig_ath = make_subplots(specs=[[{"secondary_y": True}]])
                            for _, r in ath_data_t.iterrows():
                                fig_ath.add_trace(go.Bar(name=r['Session_Name'], x=['Jumps', 'Load', 'Effort'], y=[r['Total Jumps'], r['Player Load'], r['Explosive Efforts']], marker_color=match_color_map[r['Session_Name']]), secondary_y=False)
                                fig_ath.add_trace(go.Bar(name=f"Dist", x=['Distance'], y=[r['Estimated Distance (y)']], marker=dict(color=match_color_map[r['Session_Name']], opacity=0.6, line=dict(color=match_color_map[r['Session_Name']], width=1)), showlegend=False), secondary_y=True)
                            fig_ath.update_layout(barmode='group', height=180, margin=dict(l=5,r=5,t=5,b=5), showlegend=False, template="simple_white")
                            st.plotly_chart(fig_ath, use_container_width=True, config=LOCKED_CONFIG)
                            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-header">Team Match Averages</div>', unsafe_allow_html=True)
            t_m_list = ['Total Jumps', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts']
            team_avg_t = df[df['Session_Name'].isin(selected_matches)].groupby(['Session_Name', 'Sheet_Order'])[t_m_list].mean().reset_index().sort_values('Sheet_Order')
            
            r1c1, r1c2 = st.columns(2); r2c1, r2c2 = st.columns(2); locs = [r1c1, r1c2, r2c1, r2c2]
            for idx, m in enumerate(t_m_list):
                with locs[idx]:
                    fig_t = go.Figure()
                    fig_t.add_trace(go.Bar(x=team_avg_t['Session_Name'], y=team_avg_t[m], marker_color=[match_color_map[g] for g in team_avg_t['Session_Name']], marker_line_width=0))
                    fig_t.update_layout(title=f"Team Avg: {m}", showlegend=False, height=250, margin=dict(l=40, r=10, t=40, b=40), template="simple_white", bargap=0.0)
                    st.plotly_chart(fig_t, use_container_width=True, config=LOCKED_CONFIG)

except Exception as e:
    st.error(f"Sync Error: {e}")
