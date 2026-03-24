import streamlit as st
import pandas as pd
import plotly.express as px
import math 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# --- CSS: TENNESSEE STYLE ---
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

    # --- TOP SELECTION ---
    st.markdown("<h3 style='text-align: center;'>Practice Selection</h3>", unsafe_allow_html=True)
    c_main, c_toggle, c_compare = st.columns([2, 1, 2])
    with c_main:
        date_a_str = st.selectbox("Current Practice", date_options, index=0)
    with c_toggle:
        compare_on = st.toggle("Compare Session")
    with c_compare:
        date_b_str = st.selectbox("Comparison Practice", ["None"] + date_options, index=0) if compare_on else "None"

    date_a = pd.to_datetime(date_a_str)
    day_df = df[df['Date'] == date_a].copy()

    # --- COLUMN MAPPING (Technical Sheet Header -> Display Name) ---
    metrics_map = {
        'Total Jumps': 'Total Jumps',
        'IMA Jump Count Med Band': 'Moderate Jumps',
        'IMA Jump Count High Band': 'High Jumps',
        'BMP Jumping Load': 'Jump Load',
        'Total Player Load': 'Player Load',
        'Estimated Distance (y)': 'Estimated Distance',
        'Explosive Efforts': 'Explosive Efforts',
        'High Intensity Movement': 'High Intensity Movements'
    }
    
    # Extra BMP metrics for Flow/Comparison tabs
    bmp_extras = ['BMP Running Load', 'BMP Active Load', 'BMP Dynamic Load', 'BMP Total Basketball Load']
    
    technical_cols = list(metrics_map.keys())
    all_metrics = technical_cols + bmp_extras
    
    overall_maxes = df.groupby('Name')[all_metrics].max()
    photo_map = df.dropna(subset=['PhotoURL']).drop_duplicates('Name').set_index('Name')['PhotoURL'].to_dict()

    def get_excel_gradient(score):
        score = max(0, min(100, score))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        grades = [math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0 for k in all_metrics]
        row['Practice Score'] = math.ceil(sum(grades) / len(grades))
        for k in all_metrics:
            row[f'{k}_Max'] = p_maxes[k]
            row[f'{k}_Grade'] = math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0
        row['PhotoURL_Fixed'] = photo_map.get(p_name, "https://www.w3schools.com/howto/img_avatar.png")
        return row

    def render_table(dataframe, cols, rename_dict=None):
        html = '<table class="scout-table"><thead><tr>'
        for c in cols:
            display_name = rename_dict.get(c, c) if rename_dict else c
            html += f'<th>{display_name}</th>'
        html += '</tr></thead><tbody>'
        for _, r in dataframe.iterrows():
            html += '<tr>'
            for c in cols:
                val = r[c]
                html += f'<td>{int(round(val,0)) if isinstance(val, (int, float)) else val}</td>'
            html += '</tr>'
        return html + '</tbody></table>'

    day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["Session Flow", "Individual Profile", "Team Gallery", "Team Comparison"])

    with t1:
        st.subheader(f"Drill Breakdown: {date_a_str}")
        day_p = phase_df[phase_df['Date'] == date_a].copy()
        if not day_p.empty:
            p_stats = day_p.groupby('Phase', sort=False)[all_metrics].mean().fillna(0).reset_index()
            # Table 1: Screenshot Metrics (Mapped)
            st.markdown(render_table(p_stats, ['Phase'] + technical_cols[:4], metrics_map), unsafe_allow_html=True)
            st.divider()
            # Table 2: BMP Extras
            st.markdown(render_table(p_stats, ['Phase'] + bmp_extras), unsafe_allow_html=True)
        else: st.warning("No drill data available.")

    with t2:
        sel_p = st.selectbox("Select Athlete", day_df['Name'].unique())
        p_d = day_df[day_df['Name'] == sel_p].iloc[0]
        c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
        with c1:
            st.markdown(f'<div style="text-align:center;"><img src="{p_d["PhotoURL_Fixed"]}" class="player-photo-large"></div><h2 style="text-align:center;">{p_d["Name"]}</h2>', unsafe_allow_html=True)
        with c2:
            p_rows = []
            for k, disp in metrics_map.items():
                p_rows.append({"Metric": disp, "Current": p_d[k], "Max": p_d[f'{k}_Max'], "Grade": p_d[f'{k}_Grade']})
            st.markdown(render_table(pd.DataFrame(p_rows), ["Metric", "Current", "Max", "Grade"]), unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="text-align:center; font-weight:bold; font-size:18px; margin-top:20px;">Practice Score</div><div class="score-box" style="background-color:{get_excel_gradient(p_d["Practice Score"])};">{int(p_d["Practice Score"])}</div>', unsafe_allow_html=True)

    with t3:
        for i in range(0, len(day_df), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(day_df):
                    p_i = day_df.iloc[i + j]
                    with cols[j]:
                        st.markdown('<div class="gallery-card">', unsafe_allow_html=True)
                        ci, ct, cs = st.columns([1, 2.5, 0.8])
                        with ci:
                            st.markdown(f'<div style="text-align:center;"><img src="{p_i["PhotoURL_Fixed"]}" class="gallery-photo"></div><p style="text-align:center; font-weight:bold;">{p_i["Name"]}</p>', unsafe_allow_html=True)
                        with ct:
                            g_rows = []
                            for k in technical_cols[:4]:
                                g_rows.append({"Metric": metrics_map[k], "Current": p_i[k], "Max": p_i[f'{k}_Max'], "
