import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols Performance Lab", layout="wide")

# --- CSS: SUMMITT BLUE & TENNESSEE ORANGE ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    .block-container { padding-top: 1.5rem !important; }

    /* Table Styles */
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #4895DB; color: white; padding: 6px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 11px; text-transform: uppercase; }
    .scout-table td { padding: 6px; border-bottom: 1px solid #F5F5F7; font-size: 11px; }
    
    /* Profile Photo */
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
    
    /* Score Boxes */
    .score-wrapper { text-align: center; }
    .score-label { font-size: 10px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; color: #515154; }
    .score-box { padding: 10px 20px; border-radius: 12px; font-size: 32px; font-weight: 800; min-width: 100px; color: #FFFFFF; }
    .status-subtext { font-size: 12px; font-weight: 900; display: block; margin-top: -5px; color: rgba(255,255,255,0.9); }
    
    /* Section Headers */
    .section-header { font-size: 14px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    
    /* Gallery Card */
    .gallery-card { 
        border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; min-height: 380px;
        display: flex; flex-direction: column; justify-content: center; transition: 0.3s;
    }
    .gallery-card:hover { border-color: #4895DB; box-shadow: 0px 4px 15px rgba(72, 149, 219, 0.2); }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
    
    /* Info Box */
    .info-box { background-color: #f0f7ff; border-left: 5px solid #4895DB; padding: 10px; margin-top: 10px; font-size: 11px; color: #515154; }
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
    
    rename_map = {
        'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps',
        'IMA Jump Count High Band': 'High Jumps', 'BMP Jumping Load': 'Jump Load',
        'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance',
        'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movements'
    }
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
    session_map = df[['Date', 'Session_Name']].drop_duplicates().sort_values('Date', ascending=False)
    session_options = session_map['Session_Name'].tolist()

    st.markdown("<h2 style='text-align: center; color: #FF8200; font-weight: 900; letter-spacing: -1px;'>LADY VOLS PERFORMANCE</h2>", unsafe_allow_html=True)
    c_main, c_pos = st.columns([2, 2])
    with c_main: selected_session = st.selectbox("Select Session", session_options, index=0)
    with c_pos: pos_filter = st.selectbox("Position Filter", ["All Positions"] + sorted([p for p in df['Position'].unique() if p != "N/A"]))

    day_df = df[df['Session_Name'] == selected_session].copy()
    current_practice_date = day_df['Date'].iloc[0]
    if pos_filter != "All Positions": day_df = day_df[day_df['Position'] == pos_filter]

    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']

    def get_gradient(score):
        # Using a Summitt Blue to Gray scale or keeping standard Green/Red? Let's stay with Green/Red for safety but themed labels
        score = max(0, min(100, float(score)))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        lookback_df = df[(df['Name'] == p_name) & (df['Date'] >= row['Date'] - timedelta(days=30)) & (df['Date'] <= row['Date'])]
        rolling_maxes = lookback_df[all_metrics].max().round(1)
        grades = [math.ceil((float(row[k]) / float(rolling_maxes[k])) * 100) if float(rolling_maxes[k]) > 0 else 0 for k in all_metrics]
        row['Practice Score'] = math.ceil(sum(grades) / len(grades)) if grades else 0
        for i, k in enumerate(all_metrics): row[f'{k}_Grade'] = grades[i]; row[f'{k}_Max'] = rolling_maxes[k]
        return row

    if not day_df.empty: day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    tab_ind, tab_gal, tab_comp, tab_gp = st.tabs(["Individual Profile", "Team Gallery", "Comparison Lab", "Game v. Practice"])

    with tab_ind:
        if not day_df.empty:
            sel_p = st.selectbox("Select Athlete", day_df['Name'].unique())
            p = day_df[day_df['Name'] == sel_p].iloc[0]
            p_cmj_history = cmj_df[cmj_df['Athlete'] == sel_p].sort_values('Test Date')
            sync_cmj = p_cmj_history[(p_cmj_history['Test Date'] <= current_practice_date) & (p_cmj_history['Test Date'] > current_practice_date - timedelta(days=7))]

            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1:
                st.markdown(f'<div style="text-align:center;"><img src="{p["PhotoURL"]}" class="player-photo-large"></div><h3 style="text-align:center; color:#515154;">{p["Name"]}</h3>', unsafe_allow_html=True)
            with c2:
                html = '<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>'
                for k in all_metrics: html += f"<tr><td>{k}</td><td>{p[k]}</td><td>{p[f'{k}_Max']}</td><td>{int(p[f'{k}_Grade'])}</td></tr>"
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="score-wrapper"><div class="score-label">Session Score</div><div class="score-box" style="background-color:{get_gradient(p["Practice Score"])};">{int(p["Practice Score"])}</div></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
            jc1, jc2 = st.columns([1.5, 3.5])
            with jc1:
                if not sync_cmj.empty:
                    latest = sync_cmj.iloc[-1]; baseline = p_cmj_history.tail(4)['Jump Height (in)'].mean(); rsi_baseline = p_cmj_history.tail(4)['RSI-modified [m/s]'].mean()
                    perc_diff = ((latest['Jump Height (in)'] - baseline) / baseline) * 100
                    status = "ELITE" if latest['Jump Height (in)'] >= baseline and latest['RSI-modified [m/s]'] >= rsi_baseline else "FATIGUED"
                    st.markdown(f'<div class="score-wrapper"><div class="score-label">Weekly Readiness</div><div class="score-box" style="background-color:#4895DB; color:white;">{perc_diff:+.1f}%<span class="status-subtext">{status}</span></div></div><div class="info-box"><b>Neuromuscular Status:</b> Based on Jump Height and RSI-Modified trends.</div>', unsafe_allow_html=True)
            with jc2:
                if not p_cmj_history.empty:
                    fig = make_subplots(specs=[[{"secondary_y": True}]]); fig.add_trace(go.Scatter(x=p_cmj_history['Test Date'], y=p_cmj_history['Jump Height (in)'], name="Height", line=dict(color='#FF8200', width=4)), secondary_y=False); fig.add_trace(go.Scatter(x=p_cmj_history['Test Date'], y=p_cmj_history['RSI-modified [m/s]'], name="RSI", line=dict(color='#4895DB', dash='dot', width=3)), secondary_y=True); fig.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig, use_container_width=True)

            st.markdown('<div class="section-header">Practice Phase Breakdown</div>', unsafe_allow_html=True)
            p_phases = phase_df[(phase_df['Name'] == sel_p) & (phase_df['Date'] == current_practice_date)].copy()
            if not p_phases.empty:
                pc1, pc2 = st.columns([3, 2])
                with pc1: st.plotly_chart(px.bar(p_phases, x='Phase', y='Total Jumps', color_discrete_sequence=['#FF8200'], height=300).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
                with pc2:
                    p_tbl = '<table class="scout-table"><thead><tr><th>Phase</th><th>Jumps</th><th>Load</th></tr></thead><tbody>'
                    for _, r in p_phases.iterrows(): p_tbl += f"<tr><td>{r['Phase']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Total Player Load']:.1f}</td></tr>"
                    st.markdown(p_tbl + '</tbody></table>', unsafe_allow_html=True)

    with tab_gal:
        if not day_df.empty:
            for i in range(0, len(day_df), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(day_df):
                        pd_row = day_df.iloc[i + j]; rows_html = "".join([f"<tr><td>{k}</td><td>{pd_row[k]}</td><td>{pd_row[f'{k}_Max']}</td><td>{int(pd_row[f'{k}_Grade'])}</td></tr>" for k in all_metrics])
                        with cols[j]: st.markdown(f'<div class="gallery-card"><div style="display:flex; align-items:center; gap:10px;"><div style="flex:1.2; text-align:center;"><img src="{pd_row["PhotoURL"]}" class="gallery-photo"><p style="font-weight:bold; font-size:15px; margin-top:8px; color:#515154;">{pd_row["Name"]}</p></div><div style="flex:3;"><table class="scout-table"><thead><tr><th>Metric</th><th>Val</th><th>Max</th><th>Grade</th></tr></thead><tbody>{rows_html}</tbody></table></div><div style="flex:1; text-align:center;"><div class="score-label" style="font-size:9px;">Grade</div><div style="background-color:{get_gradient(pd_row["Practice Score"])}; color:white; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{int(pd_row["Practice Score"])}</div></div></div></div>', unsafe_allow_html=True)

    with tab_comp:
        st.markdown('<div class="section-header">Positional Benchmarking</div>', unsafe_allow_html=True)
        c_comp1, c_comp2 = st.columns([1, 2])
        with c_comp1:
            comp_athlete = st.selectbox("Compare Athlete", day_df['Name'].unique(), key="comp_sel"); comp_metric = st.selectbox("Select Metric", all_metrics, key="comp_met"); p_val = day_df[day_df['Name'] == comp_athlete][comp_metric].values[0]; pos_val = day_df[day_df['Position'] == day_df[day_df['Name'] == comp_athlete]['Position'].values[0]][comp_metric].mean(); diff = ((p_val - pos_val) / pos_val * 100) if pos_val > 0 else 0; st.metric(label=f"{comp_athlete} vs Pos Avg", value=f"{p_val}", delta=f"{diff:+.1f}%")
        with c_comp2:
            pos_avg_df = day_df.groupby('Position')[comp_metric].mean().reset_index(); fig_pos = px.bar(pos_avg_df, x='Position', y=comp_metric, color_discrete_sequence=['#4895DB']); fig_pos.add_trace(go.Bar(x=[day_df[day_df['Name'] == comp_athlete]['Position'].values[0]], y=[p_val], name=comp_athlete, marker_color='#FF8200')); fig_pos.update_layout(showlegend=False, height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig_pos, use_container_width=True)

    with tab_gp:
        st.markdown('<div class="section-header">Weekly Prep vs. Game Demands</div>', unsafe_allow_html=True)
        c_gp_ath, c_gp_week, c_gp_game = st.columns(3)
        with c_gp_ath: gp_ath_sel = st.selectbox("Athlete", df['Name'].unique(), key="gp_ath_v4")
        with c_gp_week:
            if 'Week' in df.columns:
                week_ranges = df.groupby('Week')['Date'].agg(['min', 'max']).reset_index()
                week_ranges['Label'] = week_ranges.apply(lambda x: f"{x['Week']} ({x['min'].strftime('%m/%d')} - {x['max'].strftime('%m/%d')})", axis=1)
                week_options = dict(zip(week_ranges['Label'], week_ranges['Week']))
                gp_label_sel = st.selectbox("Practice Week", list(week_options.keys()), key="gp_week_v4"); gp_week_id = week_options[gp_label_sel]
        with c_gp_game: ath_games = df[(df['Name'] == gp_ath_sel) & (df['Session_Type'] == 'Game')]['Session_Name'].unique(); gp_game_target = st.selectbox("Target Game", ath_games, key="gp_game_v4")

        if 'Week' in df.columns:
            crit_mets = ['Total Jumps', 'Player Load', 'High Intensity Movements', 'Explosive Efforts']
            week_data = df[(df['Name'] == gp_ath_sel) & (df['Session_Type'] == 'Practice') & (df['Week'] == gp_week_id)]
            game_data = df[(df['Name'] == gp_ath_sel) & (df['Session_Name'] == gp_game_target)].iloc[0]
            if not week_data.empty:
                week_avg = week_data[crit_mets].mean()
                cg1, cg2 = st.columns([1, 2])
                with cg1:
                    st.write(f"**{gp_week_id} vs {gp_game_target}**")
                    for m in crit_mets:
                        g_val = game_data[m]; w_val = week_avg[m]; pct = (w_val / g_val * 100) if g_val > 0 else 0
                        st.metric(label=m, value=f"{w_val:.1f}", delta=f"{pct:.1f}% of Game")
                with cg2:
                    plot_df = pd.DataFrame({'Metric': crit_mets, 'Weekly Practice Avg': week_avg.values, 'Game Demand': [game_data[m] for m in crit_mets]}).melt(id_vars='Metric', var_name='Type', value_name='Value')
                    st.plotly_chart(px.bar(plot_df, x='Metric', y='Value', color='Type', barmode='group', color_discrete_map={'Weekly Practice Avg': '#FF8200', 'Game Demand': '#4895DB'}).update_layout(height=400, xaxis_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
