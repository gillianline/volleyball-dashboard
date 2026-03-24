import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# --- CSS: TENNESSEE STYLE ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    [data-testid="stVerticalBlock"] > div:empty { display: none !important; }
    .st-emotion-cache-16idsys p { margin-bottom: 0px; }
    .block-container { padding-top: 1.5rem !important; }

    /* Table Styles */
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #F5F5F7; padding: 6px; border-bottom: 2px solid #E5E5E7; font-weight: 700; font-size: 13px; }
    .scout-table td { padding: 5px; border-bottom: 1px solid #F5F5F7; font-size: 13px; }
    
    /* Photo & Card Styles */
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    .gallery-photo { border-radius: 50%; width: 90px; height: 90px; object-fit: cover; border: 4px solid #FF8200; }
    .score-box { padding: 15px 30px; border-radius: 12px; font-size: 36px; font-weight: 800; text-align: center; color: #1D1D1F; }
    .gallery-card { border: 1px solid #E5E5E7; padding: 12px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; min-height: 420px; }
    </style>
    """, unsafe_allow_html=True)

# --- SECURITY ---
if "password_correct" not in st.session_state:
    st.title("Access Restricted")
    pwd = st.text_input("Access Key:", type="password")
    if st.button("Unlock"):
        if pwd == st.secrets["COACH_PWD"]:
            st.session_state["password_correct"] = True
            st.rerun()
    st.stop()

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    
    rename_map = {
        'Total Jumps': 'Total Jumps',
        'IMA Jump Count Med Band': 'Moderate Jumps',
        'IMA Jump Count High Band': 'High Jumps',
        'BMP Jumping Load': 'Jump Load',
        'Total Player Load': 'Player Load',
        'Estimated Distance (y)': 'Estimated Distance',
        'Explosive Efforts': 'Explosive Efforts',
        'High Intensity Movement': 'High Intensity Movements'
    }
    df = df.rename(columns=rename_map)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Sort and fill Position/Photo
    df = df.sort_values(['Name', 'Date'])
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    
    metric_cols = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    df[metric_cols] = df[metric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    
    p_df = pd.read_csv(st.secrets["PHASE_SHEET_URL"])
    p_df.columns = p_df.columns.str.strip()
    p_df = p_df.rename(columns=rename_map)
    p_df['Date'] = pd.to_datetime(p_df['Date'])
    return df, p_df

try:
    df, phase_df = load_all_data()
    date_options = [d.strftime('%m/%d/%Y') for d in sorted(df['Date'].unique(), reverse=True)]

    # --- 1. HEADER SELECTION ---
    st.markdown("<h3 style='text-align: center; margin-bottom: 0px;'>Performance Lab</h3>", unsafe_allow_html=True)
    c_main, c_pos = st.columns([2, 2])
    with c_main:
        date_a_str = st.selectbox("Current Practice", date_options, index=0)
    with c_pos:
        pos_list = sorted([p for p in df['Position'].unique() if p != "N/A"])
        pos_filter = st.selectbox("Position Filter", ["All Positions"] + pos_list)

    date_a = pd.to_datetime(date_a_str)
    day_df = df[df['Date'] == date_a].copy()
    
    # Global position filtering logic
    if pos_filter != "All Positions":
        day_df = day_df[day_df['Position'] == pos_filter]

    # --- METRICS & GRADING ---
    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    overall_maxes = df.groupby('Name')[all_metrics].max()
    pos_avgs_today = day_df[all_metrics].mean()

    def get_gradient(score):
        score = max(0, min(100, float(score)))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        grades = [math.ceil((float(row[k]) / float(p_maxes[k])) * 100) if float(p_maxes[k]) > 0 else 0 for k in all_metrics]
        row['Practice Score'] = math.ceil(sum(grades) / len(grades))
        for k in all_metrics:
            row[f'{k}_Grade'] = math.ceil((float(row[k]) / float(p_maxes[k])) * 100) if float(p_maxes[k]) > 0 else 0
            row[f'{k}_Max'] = p_maxes[k]
        return row

    if not day_df.empty:
        day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    # --- TABS ---
    t_flow, t_player, t_gallery, t_comp = st.tabs(["Session Flow", "Individual Profile", "Team Gallery", "Team Comparison"])

    with t_flow:
        # Filter Session Flow based on position by cross-referencing names in day_df
        current_names = day_df['Name'].unique()
        day_phase_df = phase_df[(phase_df['Date'] == date_a) & (phase_df['Name'].isin(current_names))].copy()
        
        if not day_phase_df.empty:
            phase_stats = day_phase_df.groupby('Phase', sort=False).agg({'Player Load': 'mean', 'Explosive Efforts': 'mean', 'Total Jumps': 'mean'}).reset_index()
            st.plotly_chart(px.bar(phase_stats, x='Phase', y='Player Load', color='Explosive Efforts', color_continuous_scale='Oranges').update_layout(height=380, title=f"Drill Workload: {pos_filter}"), use_container_width=True)
            
            html = '<table class="scout-table"><thead><tr><th>Phase</th><th>Player Load</th><th>Explosive Efforts</th><th>Total Jumps</th></tr></thead><tbody>'
            for _, r in phase_stats.iterrows():
                html += f"<tr><td>{r['Phase']}</td><td>{int(r['Player Load'])}</td><td>{int(r['Explosive Efforts'])}</td><td>{int(r['Total Jumps'])}</td></tr>"
            st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
        else:
            st.warning(f"No drill data found for {pos_filter} on this date.")

    with t_player:
        if not day_df.empty:
            selected_player = st.selectbox("Select Athlete", day_df['Name'].unique())
            p_data = day_df[day_df['Name'] == selected_player].iloc[0]
            
            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1:
                st.markdown(f'<div style="text-align:center;"><img src="{p_data["PhotoURL"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
                st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]} ({p_data["Position"]})</h2>', unsafe_allow_html=True)
            with c2:
                html = '<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>Season Max</th><th>Grade</th></tr></thead><tbody>'
                for k in all_metrics:
                    html += f"<tr><td>{k}</td><td>{int(p_data[k])}</td><td>{int(p_data[f'{k}_Max'])}</td><td>{int(p_data[f'{k}_Grade'])}</td></tr>"
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div style="text-align:center; font-weight:bold; font-size:18px; margin-top:15px;">Practice Score</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="score-box" style="background-color:{get_gradient(p_data["Practice Score"])};">{int(p_data["Practice Score"])}</div>', unsafe_allow_html=True)

            # RESTORED CHARTS
            st.divider()
            st.markdown("### 📊 Performance Insights")
            g1, g2 = st.columns(2)
            with g1:
                radar_m = ['Total Jumps', 'Explosive Efforts', 'High Intensity Movements', 'Jump Load', 'Player Load']
                r_vals = [math.ceil((float(p_data[m]) / float(overall_maxes.loc[selected_player][m])) * 100) if float(overall_maxes.loc[selected_player][m]) > 0 else 0 for m in radar_m]
                t_vals = [math.ceil((float(pos_avgs_today[m]) / float(df[m].max())) * 100) if float(df[m].max()) > 0 else 0 for m in radar_m]
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=r_vals, theta=radar_m, fill='toself', name=selected_player, line_color='#FF8200'))
                fig_radar.add_trace(go.Scatterpolar(r=t_vals, theta=radar_m, fill='toself', name=f'{pos_filter} Avg', line_color='#1D1D1F', opacity=0.3))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(l=90, r=90, t=60, b=60), height=400, title="Physical Profile vs Team")
                st.plotly_chart(fig_radar, use_container_width=True)
            with g2:
                hist_m = st.selectbox("Season Trend", all_metrics, key="player_hist_sel")
                p_hist = df[df['Name'] == selected_player].sort_values('Date')
                fig_line = px.line(p_hist, x='Date', y=hist_m, markers=True, title=f"{hist_m} History")
                fig_line.update_traces(line_color='#FF8200')
                fig_line.update_layout(height=400)
                st.plotly_chart(fig_line, use_container_width=True)

    with t_gallery:
        if not day_df.empty:
            for i in range(0, len(day_df), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(day_df):
                        p_d = day_df.iloc[i + j]
                        with cols[j]:
                            rows_html = ""
                            for k in all_metrics:
                                rows_html += f"<tr><td>{k}</td><td>{int(p_d[k])}</td><td>{int(p_d[f'{k}_Grade'])}</td></tr>"
                            st.markdown(f"""
                            <div class="gallery-card">
                                <div style="display: flex; align-items: center;">
                                    <div style="flex: 1; text-align: center;">
                                        <img src="{p_d['PhotoURL']}" class="gallery-photo">
                                        <p style="font-weight:bold; font-size:14px; margin-top:5px;">{p_d['Name']}<br><small>{p_d['Position']}</small></p>
                                    </div>
                                    <div style="flex: 2.5;">
                                        <table class="scout-table">
                                            <thead><tr><th>Metric</th><th>Val</th><th>Grade</th></tr></thead>
                                            <tbody>{rows_html}</tbody>
                                        </table>
                                    </div>
                                    <div style="flex: 0.8; text-align: center;">
                                        <div style="background-color:{get_gradient(p_d['Practice Score'])}; border-radius:10px; padding:8px; font-size:20px; font-weight:800;">{int(p_d['Practice Score'])}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

    with t_comp:
        st.markdown("#### Team Session Comparison")
        date_b_str = st.selectbox("Select Comparison Date", [d for d in date_options if d != date_a_str])
        if date_b_str:
            avg_a = day_df[all_metrics].mean()
            # Comparison also respects position filter
            df_comp = df[df['Date'] == pd.to_datetime(date_b_str)]
            if pos_filter != "All Positions":
                df_comp = df_comp[df_comp['Position'] == pos_filter]
            
            avg_b = df_comp[all_metrics].mean()
            html = f'<table class="scout-table"><thead><tr><th>Metric</th><th>{date_a_str}</th><th>{date_b_str}</th><th>% Diff</th></tr></thead><tbody>'
            for k in all_metrics:
                diff = ((avg_a[k] - avg_b[k]) / avg_b[k] * 100) if avg_b[k] != 0 else 0
                html += f"<tr><td>{k}</td><td>{int(avg_a[k])}</td><td>{int(avg_b[k])}</td><td>{int(diff)}%</td></tr>"
            st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
