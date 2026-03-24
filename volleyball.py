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
    .scout-table th { background-color: #F5F5F7; padding: 4px; border-bottom: 2px solid #E5E5E7; font-weight: 700; font-size: 12px; }
    .scout-table td { padding: 4px; border-bottom: 1px solid #F5F5F7; font-size: 12px; }
    
    /* Photo & Card Styles */
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    .gallery-photo { border-radius: 50%; width: 90px; height: 90px; object-fit: cover; border: 4px solid #FF8200; }
    .score-box { padding: 15px 30px; border-radius: 12px; font-size: 36px; font-weight: 800; text-align: center; color: #1D1D1F; }
    .gallery-card { border: 1px solid #E5E5E7; padding: 12px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; position: relative; min-height: 250px; overflow: hidden; }
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
    
    # Sort & Fill Positioning/Photos
    df = df.sort_values(['Name', 'Date'])
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    
    # Fill Numeric Metrics
    metric_cols = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    df[metric_cols] = df[metric_cols].fillna(0)
    
    p_df = pd.read_csv(st.secrets["PHASE_SHEET_URL"])
    p_df.columns = p_df.columns.str.strip()
    p_df = p_df.rename(columns=rename_map)
    p_df['Date'] = pd.to_datetime(p_df['Date'])
    p_df[metric_cols] = p_df[metric_cols].fillna(0)
    
    return df, p_df

try:
    df, phase_df = load_all_data()
    date_options = [d.strftime('%m/%d/%Y') for d in sorted(df['Date'].unique(), reverse=True)]

    # --- 1. SELECTION BAR ---
    st.markdown("<h3 style='text-align: center; margin-bottom: 0px;'>Performance Lab</h3>", unsafe_allow_html=True)
    c_main, c_pos, c_toggle, c_comp = st.columns([2, 1.5, 1, 2])
    
    with c_main:
        date_a_str = st.selectbox("Current Practice", date_options, index=0, key="date_a_final")
    with c_pos:
        pos_list = sorted([p for p in df['Position'].unique() if p != "N/A"])
        pos_filter = st.selectbox("Position Filter", ["All Positions"] + pos_list, key="pos_filter_final")
    with c_toggle:
        compare_on = st.checkbox("Compare", value=False, key="do_compare_final")
    
    date_b_str = "None"
    if compare_on:
        with c_comp:
            date_b_str = st.selectbox("Compare Date", [d for d in date_options if d != date_a_str], index=0, key="date_b_final")

    date_a = pd.to_datetime(date_a_str)
    day_df = df[df['Date'] == date_a].copy()
    
    if pos_filter != "All Positions":
        day_df = day_df[day_df['Position'] == pos_filter]

    # --- METRICS & LOGIC ---
    grading_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    overall_maxes = df.groupby('Name')[grading_metrics].max()
    overall_avgs = df.groupby('Name')[grading_metrics].mean()
    pos_avgs_today = day_df[grading_metrics].mean()

    def get_excel_gradient(score):
        score = max(0, min(100, float(score)))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        grades = [math.ceil((float(row[k]) / float(p_maxes[k])) * 100) if float(p_maxes[k]) > 0 else 0 for k in grading_metrics]
        row['Practice Score'] = math.ceil(sum(grades) / len(grades))
        for k in grading_metrics:
            row[f'{k}_Grade'] = math.ceil((float(row[k]) / float(p_maxes[k])) * 100) if float(p_maxes[k]) > 0 else 0
            row[f'{k}_Max'] = p_maxes[k]
        try:
            curr_eff = float(row['Explosive Efforts']) / float(row['Player Load']) if float(row['Player Load']) > 0 else 0
            s_avg_eff = float(overall_avgs.loc[p_name]['Explosive Efforts']) / float(overall_avgs.loc[p_name]['Player Load']) if float(overall_avgs.loc[p_name]['Player Load']) > 0 else 0
            row['Is_Fatigued'] = bool(curr_eff < (s_avg_eff * 0.85)) and curr_eff > 0
        except:
            row['Is_Fatigued'] = False
        return row

    def render_table(dataframe, cols):
        html = '<table class="scout-table"><thead><tr>'
        for c in cols: html += f'<th>{c}</th>'
        html += '</tr></thead><tbody>'
        for _, r in dataframe.iterrows():
            html += '<tr>'
            for c in cols:
                val = r.get(c, 0)
                d_val = f"{int(round(float(val),0))}" if not isinstance(val, str) else str(val)
                html += f'<td>{d_val}</td>'
            html += '</tr>'
        return html + '</tbody></table>'

    if not day_df.empty:
        day_df = day_df.apply(process_player, axis=1).sort_values('Practice Score', ascending=False)
        top_score = day_df['Practice Score'].max()
    else:
        top_score = 0

    # --- TABS ---
    t_flow, t_player, t_gallery, t_comp = st.tabs(["Session Flow", "Individual Profile", "Team Gallery", "Team Comparison"])

    with t_flow:
        st.subheader(f"Intensity Breakdown: {date_a_str}")
        day_phase_df = phase_df[phase_df['Date'] == date_a].copy()
        if not day_phase_df.empty:
            phase_stats = day_phase_df.groupby('Phase', sort=False).agg({'Player Load': 'mean', 'Explosive Efforts': 'mean', 'Total Jumps': 'mean'}).reset_index()
            st.plotly_chart(px.bar(phase_stats, x='Phase', y='Player Load', color='Explosive Efforts', color_continuous_scale='Oranges').update_layout(height=380), use_container_width=True)
            st.markdown(render_table(phase_stats, ['Phase', 'Player Load', 'Explosive Efforts', 'Total Jumps']), unsafe_allow_html=True)
        else:
            st.warning("No drill data found.")

    with t_player:
        if day_df.empty:
            st.info("No data for current filters.")
        else:
            selected_player = st.selectbox("Select Athlete", day_df['Name'].unique(), key="player_p_sel")
            p_data = day_df[day_df['Name'] == selected_player].iloc[0]
            
            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1:
                st.markdown(f'<div style="text-align:center;"><img src="{p_data["PhotoURL"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
                st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]} ({p_data["Position"]})</h2>', unsafe_allow_html=True)
            with c2:
                p_rows = []
                if compare_on and date_b_str != "None":
                    p_b_df = df[(df['Name'] == selected_player) & (df['Date'] == pd.to_datetime(date_b_str))]
                    if not p_b_df.empty:
                        p_b = p_b_df.iloc[0]
                        for k in grading_metrics:
                            p_rows.append({"Metric": k, date_a_str: p_data[k], date_b_str: p_b[k], "Grade": p_data[f'{k}_Grade']})
                        st.markdown(render_table(pd.DataFrame(p_rows), ["Metric", date_a_str, date_b_str, "Grade"]), unsafe_allow_html=True)
                else:
                    for k in grading_metrics:
                        p_rows.append({"Metric": k, "Today": p_data[k], "Max": p_data[f'{k}_Max'], "Grade": p_data[f'{k}_Grade']})
                    st.markdown(render_table(pd.DataFrame(p_rows), ["Metric", "Today", "Max", "Grade"]), unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div style="text-align:center; font-weight:bold; font-size:18px; margin-top:15px;">Practice Score</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="score-box" style="background-color:{get_excel_gradient(p_data["Practice Score"])};">{int(p_data["Practice Score"])}</div>', unsafe_allow_html=True)

    with t_gallery:
        if not day_df.empty:
            # FIXED: TWO-COLUMN GALLERY LOOP WITH FULL TAG CLOSURES
            for i in range(0, len(day_df), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(day_df):
                        p_d = day_df.iloc[i + j]
                        is_top = (p_d['Practice Score'] == top_score and top_score > 0)
                        
                        # Generate the metric table rows
                        rows_html = ""
                        for k in grading_metrics[:4]:
                            rows_html += f"<tr><td>{k}</td><td>{int(p_d[k])}</td><td>{int(p_d[f'{k}_Grade'])}</td></tr>"

                        with cols[j]:
                            st.markdown(f"""
                            <div class="gallery-card">
                                <div style='position: absolute; top: 10px; right: 10px; display: flex; gap: 5px;'>
                                    {"<div title='Top Performer' style='color:#FFD700; font-size:20px;'>⭐</div>" if is_top else ""}
                                    {"<div title='Fatigue Detected' style='font-size:20px;'>⚠️</div>" if p_d['Is_Fatigued'] else ""}
                                </div>
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
                                        <div style="background-color:{get_excel_gradient(p_d['Practice Score'])}; border-radius:10px; padding:8px; font-size:20px; font-weight:800;">{int(p_d['Practice Score'])}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.warning("No athletes found.")

    with t_comp:
        if compare_on and date_b_str != "None":
            avg_a, avg_b = day_df[grading_metrics].mean().fillna(0), df[df['Date'] == pd.to_datetime(date_b_str)][grading_metrics].mean().fillna(0)
            comp_rows = [{"Metric": k, date_a_str: avg_a[k], date_b_str: avg_b[k], "% Diff": f"{int(((avg_a[k]-avg_b[k])/avg_b[k])*100)}%"} if avg_b[k] != 0 else {"Metric": k, date_a_str: avg_a[k], date_b_str: avg_b[k], "% Diff": "0%"} for k in grading_metrics]
            st.markdown(render_table(pd.DataFrame(comp_rows), ["Metric", date_a_str, date_b_str, "% Diff"]), unsafe_allow_html=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
