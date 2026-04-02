import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols Performance Lab", layout="wide")

# --- CSS: FIXED PADDING & LADY VOLS THEMING ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    .block-container { padding-top: 5rem !important; }

    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #4895DB; color: white; padding: 6px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 11px; text-transform: uppercase; }
    .scout-table td { padding: 6px; border-bottom: 1px solid #F5F5F7; font-size: 11px; }
    
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    
    .score-wrapper { text-align: center; }
    .score-label { font-size: 10px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; color: #515154; }
    .score-box { padding: 12px 20px; border-radius: 12px; font-size: 28px; font-weight: 800; min-width: 100px; color: #FFFFFF; line-height: 1.2; }
    .status-subtext { font-size: 11px; font-weight: 900; display: block; margin-top: 2px; text-transform: uppercase; }
    
    .section-header { font-size: 14px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    
    .gallery-card { border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; min-height: 380px; display: flex; flex-direction: column; justify-content: center; }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
    .info-box { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 12px; margin-top: 10px; font-size: 12px; color: #1D1D1F; font-weight: 600; line-height: 1.4; }
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

try:
    df, cmj_df, phase_df = load_all_data()
    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    
    def get_flipped_gradient(score):
        score = float(score)
        if score <= 40: return "#2D5A27"
        if score <= 70: return "#D4A017"
        return "#A52A2A"

    st.markdown("<h2 style='text-align: center; color: #FF8200; font-weight: 900; margin-top: -40px;'>LADY VOLS PERFORMANCE LAB</h2>", unsafe_allow_html=True)
    
    session_map = df[['Date', 'Session_Name']].drop_duplicates().sort_values('Date', ascending=False)
    col_f1, col_f2 = st.columns(2)
    with col_f1: selected_session = st.selectbox("Global Session Selection", session_map['Session_Name'].tolist(), index=0)
    with col_f2: pos_f = st.selectbox("Global Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]))

    day_df = df[df['Session_Name'] == selected_session].copy()
    curr_date = day_df['Date'].iloc[0]
    if pos_f != "All Positions": day_df = day_df[day_df['Position'] == pos_f]

    tabs = st.tabs(["Individual Profile", "Team Gallery", "Comparison Lab", "Game v. Practice"])

    with tabs[0]:
        if not day_df.empty:
            sel_p = st.selectbox("Select Athlete", sorted(day_df['Name'].unique()))
            p = day_df[day_df['Name'] == sel_p].iloc[0]
            p_cmj_hist = cmj_df[(cmj_df['Athlete'] == sel_p) & (cmj_df['Test Date'] <= curr_date)].sort_values('Test Date')
            sync_cmj = p_cmj_hist[(p_cmj_hist['Test Date'] > curr_date - timedelta(days=7))]
            lookback = df[(df['Name'] == sel_p) & (df['Date'] >= curr_date - timedelta(days=30)) & (df['Date'] <= curr_date)]
            rolling_maxes = lookback[all_metrics].max().round(1)
            grades = [math.ceil((float(p[k]) / float(rolling_maxes[k])) * 100) if float(rolling_maxes[k]) > 0 else 0 for k in all_metrics]
            practice_score = math.ceil(sum(grades) / len(grades)) if grades else 0
            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1: st.markdown(f'<div style="text-align:center;"><img src="{p["PhotoURL"]}" class="player-photo-large"></div><h3 style="text-align:center;">{p["Name"]}</h3>', unsafe_allow_html=True)
            with c2:
                html = '<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>'
                for i, k in enumerate(all_metrics): html += f"<tr><td>{k}</td><td>{p[k]}</td><td>{rolling_maxes[k]}</td><td>{grades[i]}</td></tr>"
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="score-wrapper"><div class="score-label">Practice Score</div><div class="score-box" style="background-color:{get_flipped_gradient(practice_score)};">{practice_score}</div></div>', unsafe_allow_html=True)
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
                    st.markdown(f'<div class="score-wrapper"><div class="score-label">Readiness</div><div class="score-box" style="background-color:{color};">{p_diff:+.1f}%<span class="status-subtext">{label}</span></div></div><div class="info-box"><b>Today:</b> {cur_h:.1f}" | {cur_rsi:.2f} RSI<br><b>Previous:</b> {prev_h} | {prev_rsi} RSI<br><b>Profile:</b> {profile}</div>', unsafe_allow_html=True)
            with jc2:
                if not p_cmj_hist.empty:
                    fig = make_subplots(specs=[[{"secondary_y": True}]]); fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist['Jump Height (in)'], name="Height", line=dict(color='#FF8200', width=3)), secondary_y=False); fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist['RSI-modified [m/s]'], name="RSI", line=dict(color='#4895DB', dash='dot')), secondary_y=True); fig.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), showlegend=False); st.plotly_chart(fig, use_container_width=True)
            st.markdown('<div class="section-header">Practice Phase Breakdown</div>', unsafe_allow_html=True)
            p_phases = phase_df[(phase_df['Name'] == sel_p) & (phase_df['Date'] == curr_date)].copy()
            if not p_phases.empty:
                pc1, pc2 = st.columns([3, 2])
                with pc1:
                    fig_p = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_p.add_trace(go.Bar(x=p_phases['Phase'], y=p_phases['Total Jumps'], name="Jumps", marker_color='#FF8200'), secondary_y=False)
                    fig_p.add_trace(go.Scatter(x=p_phases['Phase'], y=p_phases['Total Player Load'], name="Load", line=dict(color='#4895DB', width=4)), secondary_y=True)
                    st.plotly_chart(fig_p.update_layout(height=350, showlegend=False), use_container_width=True)
                with pc2:
                    p_tbl = '<table class="scout-table"><thead><tr><th>Phase</th><th>Jumps</th><th>Load</th></tr></thead><tbody>'
                    for _, r in p_phases.iterrows(): p_tbl += f"<tr><td>{r['Phase']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Total Player Load']:.1f}</td></tr>"
                    st.markdown(p_tbl + '</tbody></table>', unsafe_allow_html=True)

    with tabs[1]:
        day_df_gal = df[df['Session_Name'] == selected_session].copy()
        if pos_f != "All Positions": day_df_gal = day_df_gal[day_df_gal['Position'] == pos_f]
        for i in range(0, len(day_df_gal), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(day_df_gal):
                    pd_row = day_df_gal.iloc[i + j]; lb = df[(df['Name'] == pd_row['Name']) & (df['Date'] >= curr_date - timedelta(days=30)) & (df['Date'] <= curr_date)]; rm = lb[all_metrics].max().round(1); gr = [math.ceil((float(pd_row[k]) / float(rm[k])) * 100) if float(rm[k]) > 0 else 0 for k in all_metrics]; sc = math.ceil(sum(gr) / len(gr)) if gr else 0; r_html = "".join([f"<tr><td>{k}</td><td>{pd_row[k]}</td><td>{rm[k]}</td><td>{gr[idx]}</td></tr>" for idx, k in enumerate(all_metrics)])
                    with cols[j]: st.markdown(f'<div class="gallery-card"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{pd_row["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px;">{pd_row["Name"]}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Val</th><th>Max</th><th>Grade</th></tr></thead><tbody>{r_html}</tbody></table></div><div style="flex:1; text-align:center;"><div style="background-color:{get_flipped_gradient(sc)}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{sc}</div></div></div></div>', unsafe_allow_html=True)

    with tabs[2]:
        if not day_df.empty:
            st.markdown('<div class="section-header">Athlete Efficiency Mapping</div>', unsafe_allow_html=True)
            cy, cx = st.columns(2)
            with cy: y_m = st.selectbox("Vertical Axis (Output)", ['Total Jumps', 'High Intensity Movements', 'Explosive Efforts'], index=0)
            with cx: x_m = st.selectbox("Horizontal Axis (Effort)", ['Player Load', 'Estimated Distance', 'Jump Load'], index=0)
            fig_s = px.scatter(day_df, x=x_m, y=y_m, text='Name', color_discrete_sequence=['#4895DB'])
            fig_s.add_vline(x=day_df[x_m].mean(), line_dash="dash", line_color="#515154", opacity=0.5)
            fig_s.add_hline(y=day_df[y_m].mean(), line_dash="dash", line_color="#515154", opacity=0.5)
            st.plotly_chart(fig_s.update_traces(marker=dict(size=12), textposition='top center').update_layout(height=500), use_container_width=True)

    with tabs[3]:
        st.markdown('<div class="section-header">Weekly Prep Intensity vs. Game Demands</div>', unsafe_allow_html=True)
        c_ga, c_gw, c_gg = st.columns(3)
        with c_ga: gp_p = st.selectbox("Athlete", sorted(df['Name'].unique()), key="gp_p_v3")
        with c_gw:
            w_r = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index(); w_r['L'] = w_r.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1)
            gp_w = st.selectbox("Week", w_r['L'].tolist(), key="gp_w_v3"); sel_w = w_r[w_r['L'] == gp_w]['Week'].values[0]
        with c_gg: gp_g = st.selectbox("Target Game", df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Game')]['Session_Name'].unique(), key="gp_g_v3")
        
        crit = ['Total Jumps', 'Player Load', 'High Intensity Movements', 'Explosive Efforts']
        w_data = df[(df['Name'] == gp_p) & (df['Session_Type'] == 'Practice') & (df['Week'] == sel_w)]
        g_data_l = df[(df['Name'] == gp_p) & (df['Session_Name'] == gp_g)]
        
        if not w_data.empty and not g_data_l.empty:
            w_avg = w_data[crit].mean(); g_data = g_data_l.iloc[0]; cg1, cg2 = st.columns([1, 2])
            with cg1:
                for m in crit:
                    pct = (w_avg[m] / g_data[m] * 100) if g_data[m] > 0 else 0
                    st.metric(label=f"{m} (% of Game Demand)", value=f"{pct:.1f}%", delta=f"{w_avg[m] - g_data[m]:+.1f} vs Game Load")
            with cg2:
                plot = pd.DataFrame({'Metric': crit, 'Weekly Avg': w_avg.values, 'Game Demand': [g_data[m] for m in crit]}).melt(id_vars='Metric')
                st.plotly_chart(px.bar(plot, x='Metric', y='value', color='variable', barmode='group', color_discrete_map={'Weekly Avg': '#FF8200', 'Game Demand': '#4895DB'}).update_layout(height=400, xaxis_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)), use_container_width=True)

            # TEAM LOAD GRAPH - INCLUDES GAME DATA
            st.markdown(f'<div class="section-header">Average Training Load Context (Inc. Game): {sel_w}</div>', unsafe_allow_html=True)
            # Include BOTH Practice and Game for this week
            week_team_trends = df[df['Week'] == sel_w].groupby(['Date', 'Session_Type']).agg({'Player Load': 'mean'}).reset_index().sort_values('Date')
            week_team_trends['Day_Label'] = week_team_trends['Date'].dt.strftime('%a %m/%d')
            
            fig_trend = go.Figure()
            # The line connecting all points
            fig_trend.add_trace(go.Scatter(x=week_team_trends['Day_Label'], y=week_team_trends['Player Load'], mode='lines', line=dict(color='#4895DB', width=3), showlegend=False))
            # Individual markers for Practice vs Game
            for s_type, color in [('Practice', '#4895DB'), ('Game', '#FF8200')]:
                subset = week_team_trends[week_team_trends['Session_Type'] == s_type]
                fig_trend.add_trace(go.Scatter(x=subset['Day_Label'], y=subset['Player Load'], name=s_type, mode='markers', marker=dict(color=color, size=12, line=dict(width=2, color='white'))))
            
            fig_trend.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig_trend.update_yaxes(title_text="Average Player Load")
            st.plotly_chart(fig_trend, use_container_width=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
