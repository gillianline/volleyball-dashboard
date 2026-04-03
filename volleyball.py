import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="", layout="wide")

# --- CSS: FIXED PADDING & LADY VOLS THEMING ---
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
    
    .highlight-red { color: #b30000 !important; font-weight: 900; font-size: 14px; }

    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    .score-box { padding: 12px 20px; border-radius: 12px; font-size: 28px; font-weight: 800; min-width: 100px; color: #FFFFFF; line-height: 1.2; text-align: center;}
    .gallery-card { border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; min-height: 380px; display: flex; flex-direction: column; justify-content: center; }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
    .section-header { font-size: 14px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    .info-box { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 12px; margin-top: 10px; font-size: 12px; color: #1D1D1F; font-weight: 600; line-height: 1.4; }
    
    .js-plotly-plot { pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    df['Session_Type'] = df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
    cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
    cmj_df.columns = cmj_df.columns.str.strip()
    cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
    phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
    phase_df.columns = phase_df.columns.str.strip()
    if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
    phase_df['Date'] = pd.to_datetime(phase_df['Date'])
    rename_map = {'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps', 'IMA Jump Count High Band': 'High Jumps', 'BMP Jumping Load': 'Jump Load', 'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance', 'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movements'}
    df = df.rename(columns=rename_map)
    df['Date'] = pd.to_datetime(df['Date'])
    metric_cols = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    df[metric_cols] = df[metric_cols].apply(pd.to_numeric, errors='coerce').fillna(0).round(1)
    df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'])
    return df, cmj_df, phase_df

LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

try:
    df, cmj_df, phase_df = load_all_data()
    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    
    def get_flipped_gradient(score):
        score = float(score)
        if score <= 40: return "#2D5A27"
        if score <= 70: return "#D4A017"
        return "#A52A2A"

    st.markdown("""
        <div style="text-align: center; margin-top: 10px; margin-bottom: 15px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="120">
            <div style='color: #FF8200; font-size: 2rem; font-weight: 900; margin-top: 10px;'>LADY VOLS VOLLEYBALL PERFORMANCE</div>
        </div>
    """, unsafe_allow_html=True)
    
    session_map = df[['Date', 'Session_Name']].drop_duplicates().sort_values('Date', ascending=False)
    col_f1, col_f2 = st.columns(2)
    with col_f1: selected_session = st.selectbox("Practice Selection", session_map['Session_Name'].tolist(), index=0)
    with col_f2: pos_f = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]))

    day_df = df[df['Session_Name'] == selected_session].copy()
    curr_date = day_df['Date'].iloc[0]
    if pos_f != "All Positions": day_df = day_df[day_df['Position'] == pos_f]

    tabs = st.tabs(["Individual Profile", "Team Practice Grade Profiles", "Game v. Practice"])

    # --- TAB 0: INDIVIDUAL PROFILE ---
    with tabs[0]:
        if not day_df.empty:
            sel_p = st.selectbox("Select Athlete", sorted(day_df['Name'].unique()))
            p = day_df[day_df['Name'] == sel_p].iloc[0]
            
            # CMJ Logic
            p_cmj_hist = cmj_df[(cmj_df['Athlete'] == sel_p) & (cmj_df['Test Date'] <= curr_date)].sort_values('Test Date')
            sync_cmj = p_cmj_hist[(p_cmj_hist['Test Date'] > curr_date - timedelta(days=7))]

            # Metrics with Deviation Arrows
            lb = df[(df['Name'] == sel_p) & (df['Date'] >= curr_date - timedelta(days=30)) & (df['Date'] <= curr_date)]
            rolling_maxes = lb[all_metrics].max().round(1)
            rolling_avgs = lb[all_metrics].mean()
            
            total_grade = 0
            m_rows = ""
            for k in all_metrics:
                val = p[k]; mx = rolling_maxes[k]; avg = rolling_avgs[k]
                grade = math.ceil((val / mx) * 100) if mx > 0 else 0
                total_grade += grade
                
                # Check for 10% deviation vs average
                diff = (val - avg) / avg if avg != 0 else 0
                arrow = ""
                if diff > 0.10: arrow = "<span class='highlight-red'>↑</span>"
                elif diff < -0.10: arrow = "<span class='highlight-red'>↓</span>"
                
                m_rows += f"<tr><td>{k}</td><td>{val} {arrow}</td><td>{mx}</td><td>{grade}</td></tr>"
            
            practice_score = math.ceil(total_grade / len(all_metrics))

            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1: st.markdown(f'<div style="text-align:center;"><img src="{p["PhotoURL"]}" class="player-photo-large"></div><h3 style="text-align:center;">{p["Name"]}</h3>', unsafe_allow_html=True)
            with c2: st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>{m_rows}</tbody></table>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div style="display:flex; justify-content:center;"><div class="score-box" style="background-color:{get_flipped_gradient(practice_score)};">{practice_score}</div></div>', unsafe_allow_html=True)
            
            # CMJ Profile
            st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
            jc1, jc2 = st.columns([1.5, 3.5])
            with jc1:
                if not sync_cmj.empty:
                    latest = sync_cmj.iloc[-1]; base_h = p_cmj_hist.tail(5).iloc[:-1]['Jump Height (in)'].mean(); base_rsi = p_cmj_hist.tail(5).iloc[:-1]['RSI-modified [m/s]'].mean()
                    cur_h, cur_rsi = latest['Jump Height (in)'], latest['RSI-modified [m/s]']; p_diff = ((cur_h - base_h) / base_h) * 100
                    if cur_h >= base_h and cur_rsi >= base_rsi: label, color, profile = "ELITE", "#28a745", "Jump Height and RSI are both High."
                    elif cur_h >= base_h and cur_rsi < base_rsi: label, color, profile = "GRINDER", "#ffc107", "Jump Height is High | RSI is Low."
                    elif cur_h < base_h and cur_rsi >= base_rsi: label, color, profile = "SPRINGY", "#ffc107", "Jump Height is Low | RSI is High."
                    else: label, color, profile = "FATIGUED", "#dc3545", "Jump Height and RSI are both Low."
                    prev_h, prev_rsi = "N/A", "N/A"
                    if len(p_cmj_hist) > 1: prev = p_cmj_hist.iloc[-2]; prev_h, prev_rsi = f"{prev['Jump Height (in)']:.1f}\"", f"{prev['RSI-modified [m/s]']:.2f}"
                    st.markdown(f'<div style="text-align:center;"><div class="score-box" style="background-color:{color};">{p_diff:+.1f}%<span style="font-size:10px; display:block;">{label}</span></div></div><div class="info-box"><b>Today:</b> {cur_h:.1f}" | {cur_rsi:.2f} RSI<br><b>Previous:</b> {prev_h} | {prev_rsi} RSI<br><b>Profile:</b> {profile}</div>', unsafe_allow_html=True)
            with jc2:
                if not p_cmj_hist.empty:
                    fig = make_subplots(specs=[[{"secondary_y": True}]]); fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist['Jump Height (in)'], name="Height", line=dict(color='#FF8200', width=3)), secondary_y=False); fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist['RSI-modified [m/s]'], name="RSI", line=dict(color='#4895DB', dash='dot')), secondary_y=True); fig.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), showlegend=False, hovermode=False); st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG)

            # Phase Breakdown
            p_phases = phase_df[(phase_df['Name'] == sel_p) & (phase_df['Date'] == curr_date)].copy()
            if not p_phases.empty:
                st.markdown('<div class="section-header">Practice Phase Breakdown</div>', unsafe_allow_html=True)
                fig_p = make_subplots(specs=[[{"secondary_y": True}]])
                fig_p.add_trace(go.Bar(x=p_phases['Phase'], y=p_phases['Total Jumps'], name="Jumps", marker_color='#FF8200'), secondary_y=False)
                fig_p.add_trace(go.Scatter(x=p_phases['Phase'], y=p_phases['Total Player Load'], name="Load", line=dict(color='#4895DB', width=4)), secondary_y=True)
                st.plotly_chart(fig_p.update_layout(height=350, showlegend=False, hovermode=False), use_container_width=True, config=LOCKED_CONFIG)

    # --- TAB 1: TEAM GALLERY ---
    with tabs[1]:
        if not day_df.empty:
            for i in range(0, len(day_df), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(day_df):
                        pd_row = day_df.iloc[i + j]
                        lb = df[(df['Name'] == pd_row['Name']) & (df['Date'] >= curr_date - timedelta(days=30)) & (df['Date'] <= curr_date)]
                        r_html = ""; total_grade = 0
                        for k in all_metrics:
                            val = pd_row[k]; mx = lb[k].max(); avg = lb[k].mean()
                            grade = math.ceil((val / mx) * 100) if mx > 0 else 0
                            total_grade += grade
                            diff = (val - avg) / avg if avg != 0 else 0
                            arrow = ""
                            if diff > 0.10: arrow = "<span class='highlight-red'>↑</span>"
                            elif diff < -0.10: arrow = "<span class='highlight-red'>↓</span>"
                            r_html += f"<tr><td>{k}</td><td>{val} {arrow}</td><td>{mx}</td><td>{grade}</td></tr>"
                        sc = math.ceil(total_grade / len(all_metrics))
                        with cols[j]: st.markdown(f'<div class="gallery-card"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{pd_row["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px;">{pd_row["Name"]}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Val</th><th>Max</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div><div style="flex:1; text-align:center;"><div style="background-color:{get_flipped_gradient(sc)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{sc}</div></div></div></div>', unsafe_allow_html=True)

    # --- TAB 2: GAME V PRACTICE ---
    with tabs[2]:
        st.markdown('<div class="section-header">Weekly Prep Intensity vs. Game Demands</div>', unsafe_allow_html=True)
        c_ga, c_gw, c_gg = st.columns(3)
        with c_ga: gp_p = st.selectbox("Athlete", sorted(df['Name'].unique()), key="gp_p_final")
        with c_gw:
            w_r = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index(); w_r['L'] = w_r.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1)
            gp_w = st.selectbox("Week", w_r['L'].tolist(), key="gp_w_final"); sel_w = w_r[w_r['L'] == gp_w]['Week'].values[0]
        with c_gg: gp_g = st.selectbox("Game", df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Game')]['Session_Name'].unique(), key="gp_g_final")
        
        crit = ['Total Jumps', 'Player Load', 'High Intensity Movements', 'Explosive Efforts']
        w_data = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Practice') & (df['Week'] == sel_w)]
        g_data_l = df[(df['Name'] == gp_p) & (df['Session_Name'] == gp_g)]
        if not w_data.empty and not g_data_l.empty:
            w_avg = w_data[crit].mean(); g_data = g_data_l.iloc[0]; cg1, cg2 = st.columns([1, 2])
            with cg1:
                for m in crit:
                    pct_diff = ((w_avg[m] - g_data[m]) / g_data[m] * 100) if g_data[m] > 0 else 0
                    st.metric(label=m, value=" ", delta=f"{pct_diff:+.1f}% vs Game Load")
            with cg2:
                plot = pd.DataFrame({'Metric': crit, 'Weekly Avg': w_avg.values, 'Game Demand': [g_data[m] for m in crit]}).melt(id_vars='Metric')
                fig_bar = px.bar(plot, x='Metric', y='value', color='variable', barmode='group', color_discrete_map={'Weekly Avg': '#FF8200', 'Game Demand': '#4895DB'})
                st.plotly_chart(fig_bar.update_layout(height=400, showlegend=False, hovermode=False), use_container_width=True, config=LOCKED_CONFIG)
            
            st.markdown(f'<div class="section-header">Average Weekly Load: {sel_w}</div>', unsafe_allow_html=True)
            week_team_trends = df[df['Week'] == sel_w].groupby(['Date', 'Session_Type']).agg({'Player Load': 'mean'}).reset_index().sort_values('Date')
            week_team_trends['Day_Label'] = week_team_trends['Date'].dt.strftime('%a %m/%d')
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=week_team_trends['Day_Label'], y=week_team_trends['Player Load'], mode='lines', line=dict(color='#4895DB', width=3), showlegend=False))
            for s_type, color in [('Practice', '#4895DB'), ('Game', '#FF8200')]:
                subset = week_team_trends[week_team_trends['Session_Type'] == s_type]
                fig_trend.add_trace(go.Scatter(x=subset['Day_Label'], y=subset['Player Load'], name=s_type, mode='markers', marker=dict(color=color, size=12, line=dict(width=2, color='white'))))
            st.plotly_chart(fig_trend.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0), yaxis_title="Average Player Load", hovermode=False), use_container_width=True, config=LOCKED_CONFIG)

except Exception as e:
    st.error(f"Sync Error: {e}")
