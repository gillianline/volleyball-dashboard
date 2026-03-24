import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# --- CSS: CLEAN UI & GAP REMOVAL ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    [data-testid="stVerticalBlock"] > div:empty { display: none !important; }
    .block-container { padding-top: 1.5rem !important; }

    /* Table Styles */
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #F5F5F7; padding: 6px; border-bottom: 2px solid #E5E5E7; font-weight: 700; font-size: 13px; }
    .scout-table td { padding: 5px; border-bottom: 1px solid #F5F5F7; font-size: 13px; }
    
    /* Photo & Card Styles */
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    .gallery-photo { border-radius: 50%; width: 90px; height: 90px; object-fit: cover; border: 4px solid #FF8200; }
    .score-box { padding: 15px 30px; border-radius: 12px; font-size: 36px; font-weight: 800; text-align: center; color: #1D1D1F; }
    .gallery-card { border: 1px solid #E5E5E7; padding: 12px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 8px; position: relative; }
    .fatigue-warning { position: absolute; top: 10px; right: 10px; font-size: 24px; cursor: help; }
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
    df['Date'] = pd.to_datetime(df['Date'])
    p_df = pd.read_csv(st.secrets["PHASE_SHEET_URL"])
    p_df.columns = p_df.columns.str.strip()
    p_df['Date'] = pd.to_datetime(p_df['Date'])
    return df, p_df

try:
    df, phase_df = load_all_data()
    date_options = [d.strftime('%m/%d/%Y') for d in sorted(df['Date'].unique(), reverse=True)]

    # --- 1. DATE & POSITION SELECTION ---
    st.markdown("<h3 style='text-align: center; margin-bottom: 0px;'>Practice Session</h3>", unsafe_allow_html=True)
    c_main, c_pos, c_toggle, c_comp = st.columns([2, 1.5, 1, 2])
    
    with c_main:
        date_a_str = st.selectbox("Current Practice", date_options, index=0, key="date_sel")
    with c_pos:
        pos_filter = st.selectbox("Filter Position", ["All Positions"] + sorted(df['Position'].unique().tolist()), key="pos_filter")
    with c_toggle:
        compare_on = st.checkbox("Compare", value=False, key="compare_on")
    
    date_b_str = "None"
    if compare_on:
        with c_comp:
            date_b_str = st.selectbox("Compare Date", [d for d in date_options if d != date_a_str], index=0, key="date_b_sel")

    date_a = pd.to_datetime(date_a_str)
    day_df = df[df['Date'] == date_a].copy()
    
    # Apply Position Filter to the local day dataframe
    if pos_filter != "All Positions":
        day_df = day_df[day_df['Position'] == pos_filter]

    # --- METRICS & GRADING ---
    grading_metrics = ['Total Jumps', 'IMA Jump Count High Band', 'BMP Jumping Load', 'Total Player Load', 'Explosive Efforts', 'High Intensity Movement', 'Estimated Distance (y)']
    overall_maxes = df.groupby('Name')[grading_metrics].max()
    overall_avgs = df.groupby('Name')[grading_metrics].mean()
    pos_avgs_today = day_df[grading_metrics].mean() # This is now position-specific if filtered
    
    photo_map = df.dropna(subset=['PhotoURL']).drop_duplicates('Name').set_index('Name')['PhotoURL'].to_dict()

    def get_excel_gradient(score):
        score = max(0, min(100, score))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        grades = [math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0 for k in grading_metrics]
        row['Practice Score'] = math.ceil(sum(grades) / len(grades))
        for k in grading_metrics:
            row[f'{k}_Grade'] = math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0
        
        # FATIGUE LOGIC: Check if efficiency (Explosive/Load) is 15% below season avg
        current_eff = row['Explosive Efforts'] / row['Total Player Load'] if row['Total Player Load'] > 0 else 0
        avg_eff = overall_avgs.loc[p_name]['Explosive Efforts'] / overall_avgs.loc[p_name]['Total Player Load'] if overall_avgs.loc[p_name]['Total Player Load'] > 0 else 0
        row['Is_Fatigued'] = current_eff < (avg_eff * 0.85)
        
        row['PhotoURL_Fixed'] = photo_map.get(p_name, "https://www.w3schools.com/howto/img_avatar.png")
        return row

    def render_table(dataframe, cols):
        html = '<table class="scout-table"><thead><tr>'
        for c in cols: html += f'<th>{c}</th>'
        html += '</tr></thead><tbody>'
        for _, r in dataframe.iterrows():
            html += '<tr>'
            for c in cols:
                val = r.get(c, 0)
                display_val = f"{int(round(val,0))}" if isinstance(val, (int, float)) else str(val)
                html += f'<td>{display_val}</td>'
            html += '</tr>'
        return html + '</tbody></table>'

    day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    # --- 2. TABS ---
    t_flow, t_player, t_gallery, t_comp = st.tabs(["Session Flow", "Individual Profile", "Team Gallery", "Team Comparison"])

    with t_flow:
        day_phase_df = phase_df[phase_df['Date'] == date_a].copy()
        if not day_phase_df.empty:
            phase_stats = day_phase_df.groupby('Phase', sort=False).agg({'Total Player Load': 'mean', 'Explosive Efforts': 'mean', 'Total Jumps': 'mean'}).reset_index()
            fig_flow = px.bar(phase_stats, x='Phase', y='Total Player Load', color='Explosive Efforts', color_continuous_scale='Oranges')
            fig_flow.update_layout(height=350, margin=dict(l=40, r=40, t=20, b=20))
            st.plotly_chart(fig_flow, use_container_width=True)
            st.markdown(render_table(phase_stats, ['Phase', 'Total Player Load', 'Explosive Efforts', 'Total Jumps']), unsafe_allow_html=True)
        else:
            st.warning("No drill data found.")

    with t_player:
        selected_player = st.selectbox("Select Athlete", day_df['Name'].unique())
        p_data = day_df[day_df['Name'] == selected_player].iloc[0]
        
        c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
        with c1:
            st.markdown(f'<div style="text-align:center;"><img src="{p_data["PhotoURL_Fixed"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
            st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]} ({p_data["Position"]})</h2>', unsafe_allow_html=True)
        with c2:
            p_rows = []
            if compare_on and date_b_str != "None":
                p_b = df[(df['Name'] == selected_player) & (df['Date'] == pd.to_datetime(date_b_str))].iloc[0]
                for k in grading_metrics:
                    p_rows.append({"Metric": k, date_a_str: p_data[k], date_b_str: p_b[k], "Grade": p_data[f'{k}_Grade']})
                st.markdown(render_table(pd.DataFrame(p_rows), ["Metric", date_a_str, date_b_str, "Grade"]), unsafe_allow_html=True)
            else:
                for k in grading_metrics:
                    p_rows.append({"Metric": k, "Today": p_data[k], "Season Avg": int(overall_avgs.loc[selected_player][k]), "Grade": p_data[f'{k}_Grade']})
                st.markdown(render_table(pd.DataFrame(p_rows), ["Metric", "Today", "Season Avg", "Grade"]), unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="text-align:center; font-weight:bold; font-size:18px; margin-top:15px;">Practice Score</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="score-box" style="background-color:{get_excel_gradient(p_data["Practice Score"])};">{int(p_data["Practice Score"])}</div>', unsafe_allow_html=True)

        g1, g2 = st.columns(2)
        with g1:
            radar_m = ['Total Jumps', 'Explosive Efforts', 'High Intensity Movement', 'BMP Jumping Load', 'Total Player Load']
            r_vals = [math.ceil((p_data[m] / overall_maxes.loc[selected_player][m]) * 100) for m in radar_m]
            t_vals = [math.ceil((pos_avgs_today[m] / df[m].max()) * 100) for m in radar_m]
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=r_vals, theta=radar_m, fill='toself', name=selected_player, line_color='#FF8200'))
            fig_radar.add_trace(go.Scatterpolar(r=t_vals, theta=radar_m, fill='toself', name=f'{pos_filter} Avg', line_color='#1D1D1F', opacity=0.3))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(l=90, r=90, t=40, b=40), height=380)
            st.plotly_chart(fig_radar, use_container_width=True)
        with g2:
            hist_m = st.selectbox("Progress Tracker", grading_metrics)
            p_hist = df[df['Name'] == selected_player].sort_values('Date')
            st.plotly_chart(px.line(p_hist, x='Date', y=hist_m, markers=True).update_traces(line_color='#FF8200').update_layout(height=380), use_container_width=True)

    with t_gallery:
        for i in range(0, len(day_df), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(day_df):
                    p_d = day_df.iloc[i + j]
                    with cols[j]:
                        st.markdown(f"""
                        <div class="gallery-card">
                            {"<div class='fatigue-warning' title='Fatigue Detected: Low Explosive Efficiency'>⚠️</div>" if p_d['Is_Fatigued'] else ""}
                            <div style="display: flex; align-items: center;">
                                <div style="flex: 1; text-align: center;">
                                    <img src="{p_d['PhotoURL_Fixed']}" class="gallery-photo">
                                    <p style="font-weight:bold; font-size:14px; margin-top:5px;">{p_d['Name']}<br><small>{p_d['Position']}</small></p>
                                </div>
                                <div style="flex: 2.5;">
                                    {render_table(pd.DataFrame([{"Metric": k, "Val": p_d[k], "Grade": p_d[f'{k}_Grade']} for k in grading_metrics[:5]]), ["Metric", "Val", "Grade"])}
                                </div>
                                <div style="flex: 0.8; text-align: center;">
                                    <div style="background-color:{get_excel_gradient(p_d['Practice Score'])}; border-radius:10px; padding:8px; font-size:20px; font-weight:800;">{int(p_d['Practice Score'])}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    with t_comp:
        if not compare_on or date_b_str == "None":
            st.info("Select a Comparison Date above.")
        else:
            df_b = df[df['Date'] == pd.to_datetime(date_b_str)]
            avg_a, avg_b = day_df[grading_metrics].mean(), df_b[grading_metrics].mean()
            comp_rows = [{"Metric": k, date_a_str: avg_a[k], date_b_str: avg_b[k], "% Diff": f"{int(((avg_a[k]-avg_b[k])/avg_b[k])*100)}%"} for k in grading_metrics]
            st.markdown(render_table(pd.DataFrame(comp_rows), ["Metric", date_a_str, date_b_str, "% Diff"]), unsafe_allow_html=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
