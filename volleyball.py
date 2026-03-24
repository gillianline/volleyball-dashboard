import streamlit as st
import pandas as pd
import plotly.express as px
import math 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# --- CSS: TENNESSEE STYLE + NO INDEX + TREND COLORS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    
    /* Center all table content */
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; margin-top: 5px; }
    .scout-table th { background-color: #F5F5F7; padding: 10px; border-bottom: 2px solid #E5E5E7; font-weight: 700; }
    .scout-table td { padding: 8px; border-bottom: 1px solid #F5F5F7; }

    .player-photo-large { border-radius: 50%; width: 240px; height: 240px; object-fit: cover; border: 6px solid #FF8200; }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
    .score-box { padding: 20px 40px; border-radius: 12px; font-size: 40px; font-weight: 800; text-align: center; color: #1D1D1F; }
    .gallery-card { border: 1px solid #E5E5E7; padding: 20px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 10px; }
    
    .trend-up { color: #28a745; font-weight: bold; }
    .trend-down { color: #dc3545; font-weight: bold; }
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
    
    # --- CENTERED DATE SELECTION (LOCKED AT TOP) ---
    st.markdown("<h3 style='text-align: center;'>Practice Selection</h3>", unsafe_allow_html=True)
    c_d1, c_d2 = st.columns(2)
    with c_d1: date_a_str = st.selectbox("Current Practice", date_options, index=0)
    with c_d2: date_b_str = st.selectbox("Comparison Practice (Optional)", ["None"] + date_options, index=0)

    date_a = pd.to_datetime(date_a_str)
    day_df = df[df['Date'] == date_a].copy()

    # --- LOGIC ---
    grading_map = {
        'Total Jumps': 'Total Jumps', 
        'IMA Jump Count Med Band': 'Moderate Jumps', 
        'IMA Jump Count High Band': 'High Jumps', 
        'BMP Jumping Load': 'Jump Load', 
        'Total Player Load': 'Player Load', 
        'Estimated Distance (y)': 'Estimated Distance', 
        'Explosive Efforts': 'Explosive Efforts', 
        'High Intensity Movement': 'High Intensity Movement'
    }
    
    overall_maxes = df.groupby('Name')[list(grading_map.keys())].max()
    photo_map = df.dropna(subset=['PhotoURL']).drop_duplicates('Name').set_index('Name')['PhotoURL'].to_dict()

    def get_excel_gradient(score):
        score = max(0, min(100, score))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        grades = [math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0 for k in grading_map.keys()]
        row['Practice Score'] = math.ceil(sum(grades) / len(grades))
        for k in grading_map.keys():
            row[f'{k}_Max'] = p_maxes[k]
            row[f'{k}_Grade'] = math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0
        row['PhotoURL_Fixed'] = photo_map.get(p_name, "https://www.w3schools.com/howto/img_avatar.png")
        return row

    day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    def render_table(dataframe, cols):
        html = '<table class="scout-table"><thead><tr>'
        for c in cols: html += f'<th>{c}</th>'
        html += '</tr></thead><tbody>'
        for _, r in dataframe.iterrows():
            html += '<tr>'
            for c in cols:
                val = r[c]
                style = ""
                if c == "% Diff" and isinstance(val, str):
                    style = 'class="trend-up"' if "+" in val else 'class="trend-down"' if "-" in val else ""
                    val = f"▲ {val}" if "+" in val else f"▼ {val}" if "-" in val else val
                html += f'<td {style}>{int(round(val,0)) if isinstance(val, (int, float)) else val}</td>'
            html += '</tr>'
        return html + '</tbody></table>'

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["Session Flow", "Individual Profile", "Team Gallery", "Team Comparison"])

    with t1:
        st.subheader(f"Drill Breakdown: {date_a_str}")
        day_phase_df = phase_df[phase_df['Date'] == date_a].copy()
        if not day_phase_df.empty:
            p_metrics = ['Total Jumps', 'IMA Jump Count High Band', 'Total Player Load', 'High Intensity Movement']
            phase_stats = day_phase_df.groupby('Phase', sort=False)[p_metrics].mean().fillna(0).reset_index()
            st.plotly_chart(px.bar(phase_stats, x="Phase", y="Total Player Load", template="plotly_white", color_discrete_sequence=["#FF8200"]), use_container_width=True)
            st.markdown(render_table(phase_stats, ['Phase', 'Total Jumps', 'IMA Jump Count High Band', 'Total Player Load', 'High Intensity Movement']), unsafe_allow_html=True)
        else:
            st.info("No drill data available for this date.")

    with t2:
        selected_player = st.selectbox("Select Athlete", day_df['Name'].unique())
        p_data = day_df[day_df['Name'] == selected_player].iloc[0]
        
        c_p1, c_p2, c_p3 = st.columns([1.2, 2.5, 1.2])
        with c_p1:
            st.markdown(f'<div style="text-align:center;"><img src="{p_data["PhotoURL_Fixed"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
            st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]}</h2>', unsafe_allow_html=True)
        
        with c_p2:
            p_rows = []
            if date_b_str != "None":
                date_b = pd.to_datetime(date_b_str)
                p_b = df[(df['Name'] == selected_player) & (df['Date'] == date_b)]
                if not p_b.empty:
                    p_b = process_player(p_b.iloc[0])
                    for k in grading_map.keys():
                        p_rows.append({"Metric": grading_map[k], f"{date_a_str}": p_data[k], f"{date_b_str}": p_b[k], "Grade (Now)": p_data[f'{k}_Grade']})
                    st.markdown(render_table(pd.DataFrame(p_rows), ["Metric", date_a_str, date_b_str, "Grade (Now)"]), unsafe_allow_html=True)
                else: st.warning(f"No comparison data for {selected_player} on {date_b_str}")
            else:
                for k in grading_map.keys():
                    p_rows.append({"Metric": grading_map[k], "Current": p_data[k], "Max": p_data[f'{k}_Max'], "Grade": p_data[f'{k}_Grade']})
                st.markdown(render_table(pd.DataFrame(p_rows), ["Metric", "Current", "Max", "Grade"]), unsafe_allow_html=True)

        with c_p3:
            st.markdown(f'<div style="text-align:center; font-weight:bold; font-size:20px; margin-top:20px;">Practice Score</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="score-box" style="background-color:{get_excel_gradient(p_data["Practice Score"])};">{int(p_data["Practice Score"])}</div>', unsafe_allow_html=True)

        st.divider()
        # Individual drill breakdown
        st.subheader("Intensity per Drill")
        p_phases = phase_df[(phase_df['Name'] == selected_player) & (phase_df['Date'] == date_a)]
        if not p_phases.empty:
            st.plotly_chart(px.bar(p_phases, x="Phase", y="Total Player Load", template="plotly_white", color_discrete_sequence=["#FF8200"]), use_container_width=True)

    with t3:
        for i in range(0, len(day_df), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(day_df):
                    p_d = day_df.iloc[i + j]
                    with cols[j]:
                        st.markdown('<div class="gallery-card">', unsafe_allow_html=True)
                        ci, ct, cs = st.columns([1, 2.5, 0.8])
                        with ci:
                            st.markdown(f'<div style="text-align:center;"><img src="{p_d["PhotoURL_Fixed"]}" class="gallery-photo"></div><p style="text-align:center; font-weight:bold;">{p_d["Name"]}</p>', unsafe_allow_html=True)
                        with ct:
                            rows = [{"Metric": grading_map[k], "Current": p_d[k], "Max": p_d[f'{k}_Max'], "Grade": p_d[f'{k}_Grade']} for k in grading_map.keys()]
                            st.markdown(render_table(pd.DataFrame(rows), ["Metric", "Current", "Max", "Grade"]), unsafe_allow_html=True)
                        with cs:
                            st.markdown(f'<div style="background-color:{get_excel_gradient(p_d["Practice Score"])}; border-radius:10px; text-align:center; padding:15px; font-size:24px; font-weight:800; margin-top:45px;">{int(p_d["Practice Score"])}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

    with t4:
        if date_b_str != "None":
            date_b = pd.to_datetime(date_b_str)
            df_b = df[df['Date'] == date_b].copy()
            avg_a, avg_b = day_df[list(grading_map.keys())].mean(), df_b[list(grading_map.keys())].mean()
            comp_rows = []
            for k, display in grading_map.items():
                perc_diff = ((avg_a[k] - avg_b[k]) / avg_b[k] * 100) if avg_b[k] != 0 else 0
                comp_rows.append({"Metric": display, date_a_str: avg_a[k], date_b_str: avg_b[k], "% Diff": f"{'+' if perc_diff > 0 else ''}{int(round(perc_diff, 0))}%"})
            st.markdown(render_table(pd.DataFrame(comp_rows), ["Metric", date_a_str, date_b_str, "% Diff"]), unsafe_allow_html=True)
            # Graph excluding Estimated Distance
            g_rows = [r for r in comp_rows if "Distance" not in r["Metric"]]
            st.plotly_chart(px.bar(pd.DataFrame(g_rows).melt(id_vars="Metric", value_vars=[date_a_str, date_b_str]), x="Metric", y="value", color="variable", barmode="group", template="plotly_white", color_discrete_sequence=["#FF8200", "#545454"]), use_container_width=True)
        else:
            st.info("Select a comparison practice at the top to view team trends.")

except Exception as e:
    st.error(f"Sync Error: {e}")
