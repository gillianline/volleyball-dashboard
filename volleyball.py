import streamlit as st
import pandas as pd
import plotly.express as px
import math 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# --- CSS: TENNESSEE STYLE + NO INDEX ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    
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

    # --- 1. PRACTICE SELECTION (TOP) ---
    st.markdown("<h3 style='text-align: center;'>Practice Selection</h3>", unsafe_allow_html=True)
    c_date1, c_date2 = st.columns(2)
    with c_date1: date_a_str = st.selectbox("Current Practice", date_options, index=0)
    with c_date2: date_b_str = st.selectbox("Comparison Practice (Optional)", ["None"] + date_options, index=0)

    date_a = pd.to_datetime(date_a_str)
    day_df = df[df['Date'] == date_a].copy()

    # --- JUMP-WEIGHTED LOGIC ---
    # Metrics grouped by type
    jump_metrics = ['Total Jumps', 'IMA Jump Count Med Band', 'IMA Jump Count High Band', 'BMP Jumping Load']
    load_metrics = ['Total Player Load', 'Explosive Efforts', 'High Intensity Movement']
    
    overall_maxes = df.groupby('Name')[jump_metrics + load_metrics].max()
    photo_map = df.dropna(subset=['PhotoURL']).drop_duplicates('Name').set_index('Name')['PhotoURL'].to_dict()

    def get_excel_gradient(score):
        score = max(0, min(100, score))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        
        # Weighted Score: 70% Jumps, 30% Player Load
        j_grades = [math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0 for k in jump_metrics]
        l_grades = [math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0 for k in load_metrics]
        
        j_avg = sum(j_grades) / len(j_grades)
        l_avg = sum(l_grades) / len(l_grades)
        
        row['Practice Score'] = math.ceil((j_avg * 0.7) + (l_avg * 0.3))
        
        for k in (jump_metrics + load_metrics):
            row[f'{k}_Max'] = p_maxes[k]
            row[f'{k}_Grade'] = math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0
        
        row['PhotoURL_Fixed'] = photo_map.get(p_name, "https://www.w3schools.com/howto/img_avatar.png")
        return row

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
                html += f'<td {style}>{int(round(val,0)) if isinstance(val, (int, float)) else val}</td>'
            html += '</tr>'
        return html + '</tbody></table>'

    day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    # --- 2. TABS ---
    t_flow, t_player, t_gallery, t_comp = st.tabs(["Session Flow", "Individual Profile", "Team Gallery", "Team Comparison"])

    with t_flow:
        st.subheader(f"Jump Breakdown by Drill: {date_a_str}")
        day_phase_df = phase_df[phase_df['Date'] == date_a].copy()
        if not day_phase_df.empty:
            # Chart switched to lead with Jumps
            phase_stats = day_phase_df.groupby('Phase', sort=False)[['Total Jumps', 'Total Player Load']].mean().fillna(0).reset_index()
            st.plotly_chart(px.bar(phase_stats, x="Phase", y="Total Jumps", template="plotly_white", color_discrete_sequence=["#FF8200"]), use_container_width=True)
            st.markdown(render_table(phase_stats, ['Phase', 'Total Jumps', 'Total Player Load']), unsafe_allow_html=True)
        else:
            st.warning("No drill-specific data found in Phase Sheet for this date.")

    with t_player:
        selected_player = st.selectbox("Select Athlete", day_df['Name'].unique())
        p_data = day_df[day_df['Name'] == selected_player].iloc[0]
        
        c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
        with c1:
            st.markdown(f'<div style="text-align:center;"><img src="{p_data["PhotoURL_Fixed"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
            st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]}</h2>', unsafe_allow_html=True)
        with c2:
            # Table showing Jumps then Load
            display_cols = jump_metrics + load_metrics
            rows = [{"Metric": k, "Current": p_data[k], "Max": p_data[f'{k}_Max'], "Grade": p_data[f'{k}_Grade']} for k in display_cols]
            st.markdown(render_table(pd.DataFrame(rows), ["Metric", "Current", "Max", "Grade"]), unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="text-align:center; font-weight:bold; font-size:20px; margin-top:20px;">Jump-Weighted Score</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="score-box" style="background-color:{get_excel_gradient(p_data["Practice Score"])};">{int(p_data["Practice Score"])}</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("Intensity Distribution")
        low_j = p_data['Total Jumps'] - (p_data['IMA Jump Count Med Band'] + p_data['IMA Jump Count High Band'])
        j_df = pd.DataFrame({'Band': ['Low', 'Med', 'High'], 'Count': [max(0, low_j), p_data['IMA Jump Count Med Band'], p_data['IMA Jump Count High Band']]})
        st.plotly_chart(px.bar(j_df, x="Count", y="Band", orientation='h', color="Band", color_discrete_map={"Low":"#28a745", "Med":"#FFC107", "High":"#dc3545"}, template="plotly_white"), use_container_width=True)

    with t_gallery:
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
                            rows = [{"Metric": k, "Current": p_d[k], "Grade": p_d[f'{k}_Grade']} for k in (jump_metrics[:3] + [load_metrics[0]])]
                            st.markdown(render_table(pd.DataFrame(rows), ["Metric", "Current", "Grade"]), unsafe_allow_html=True)
                        with cs:
                            st.markdown(f'<div style="background-color:{get_excel_gradient(p_d["Practice Score"])}; border-radius:10px; text-align:center; padding:15px; font-size:24px; font-weight:800; margin-top:45px;">{int(p_d["Practice Score"])}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

    with t_comp:
        if date_b_str == "None":
            st.info("Select a 'Comparison Practice' at the top.")
        else:
            date_b = pd.to_datetime(date_b_str)
            df_b = df[df['Date'] == date_b].copy()
            avg_a, avg_b = day_df[jump_metrics + load_metrics].mean(), df_b[jump_metrics + load_metrics].mean()
            comp_rows = []
            for k in (jump_metrics + load_metrics):
                diff = ((avg_a[k] - avg_b[k]) / avg_b[k] * 100) if avg_b[k] != 0 else 0
                comp_rows.append({"Metric": k, date_a_str: avg_a[k], date_b_str: avg_b[k], "% Diff": f"{'+' if diff > 0 else ''}{int(round(diff, 0))}%"})
            st.markdown(render_table(pd.DataFrame(comp_rows), ["Metric", date_a_str, date_b_str, "% Diff"]), unsafe_allow_html=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
