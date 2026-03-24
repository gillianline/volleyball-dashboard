import streamlit as st
import pandas as pd
import plotly.express as px
import math 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# --- CSS: TENNESSEE STYLE + CENTERED TABLES + NO INDEX ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    
    /* Remove all default dividers/bars */
    hr { display: none !important; }
    [data-testid="column"] { padding: 0px 10px !important; }

    /* Centered HTML Tables (No Index) */
    .scout-table {
        width: 100%;
        border-collapse: collapse;
        text-align: center;
        margin-top: 5px;
    }
    .scout-table th {
        background-color: #F5F5F7;
        padding: 10px;
        border-bottom: 2px solid #E5E5E7;
        font-weight: 700;
        color: #1D1D1F;
    }
    .scout-table td {
        padding: 8px;
        border-bottom: 1px solid #F5F5F7;
        color: #1D1D1F;
    }

    /* Photos & Borders */
    .player-photo-large {
        border-radius: 50%;
        width: 240px;
        height: 240px;
        object-fit: cover;
        border: 6px solid #FF8200;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    }
    .gallery-photo {
        border-radius: 50%;
        width: 110px;
        height: 110px;
        object-fit: cover;
        border: 4px solid #FF8200;
    }

    /* Score Box Gradient Style */
    .score-box {
        padding: 20px 40px;
        border-radius: 12px;
        font-size: 44px;
        font-weight: 800;
        text-align: center;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }

    /* Card Wrapper */
    .gallery-card {
        border: 1px solid #E5E5E7;
        padding: 20px;
        border-radius: 15px;
        background-color: #FFFFFF;
        margin-bottom: 10px;
    }
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
    phase_df = pd.read_csv(st.secrets["PHASE_SHEET_URL"])
    phase_df.columns = phase_df.columns.str.strip()
    phase_df['Date'] = pd.to_datetime(phase_df['Date'])
    return df, phase_df

try:
    df, phase_df = load_all_data()
    date_options = [d.strftime('%m/%d/%Y') for d in sorted(df['Date'].unique())]
    
    st.markdown("<h3 style='text-align: center;'>Practice Session</h3>", unsafe_allow_html=True)
    selected_date_str = st.selectbox("", date_options, index=len(date_options)-1, label_visibility="collapsed")
    sel_date_dt = pd.to_datetime(selected_date_str)
    
    day_df = df[df['Date'] == sel_date_dt].copy()
    day_phase_df = phase_df[phase_df['Date'] == sel_date_dt].copy()

    # --- LOGIC: EXCEL GRADIENT & SCORING ---
    def get_excel_gradient(score):
        score = max(0, min(100, score))
        r = int(255 * (score / 50)) if score < 50 else 255
        g = 255 if score < 50 else int(255 * (1 - (score - 50) / 50))
        return f"rgb({r}, {g}, 0)"

    grading_map = {
        'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps', 
        'IMA Jump Count High Band': 'High Jumps', 'BMP Jumping Load': 'Jump Load', 
        'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance', 
        'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movements'
    }

    overall_maxes = df.groupby('Name')[list(grading_map.keys())].max()
    photo_map = df.dropna(subset=['PhotoURL']).drop_duplicates('Name').set_index('Name')['PhotoURL'].to_dict()

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        grades = []
        for k in grading_map.keys():
            m_val = p_maxes[k]
            grade = math.ceil((row[k] / m_val) * 100) if m_val > 0 else 0
            row[f'{k}_Max'] = m_val
            row[f'{k}_Grade'] = grade
            grades.append(grade)
        row['Practice Score'] = math.ceil(sum(grades) / len(grades))
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
                html += f'<td>{int(round(val,0)) if isinstance(val, (int, float)) else val}</td>'
            html += '</tr>'
        return html + '</tbody></table>'

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["Session Flow", "Individual Profile", "Team Gallery", "Leaderboard"])

    with t1:
        st.subheader("Phase Intensity Breakdown")
        phase_stats = day_phase_df.groupby('Phase', sort=False)[['Total Jumps', 'Total Player Load']].mean().reset_index()
        fig_p = px.bar(phase_stats, x="Phase", y="Total Player Load", title="Team Workload per Drill", template="plotly_white", color_discrete_sequence=["#FF8200"])
        st.plotly_chart(fig_p, use_container_width=True)

    with t2:
        selected_player = st.selectbox("Select Athlete", day_df['Name'].unique())
        p_data = day_df[day_df['Name'] == selected_player].iloc[0]
        score_bg = get_excel_gradient(p_data['Practice Score'])
        
        c1, c2, c3 = st.columns([1.2, 2, 1])
        with c1:
            st.markdown(f'<div style="text-align:center;"><img src="{p_data["PhotoURL_Fixed"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
            st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]}</h2>', unsafe_allow_html=True)
        with c2:
            rows = [{"Metric": grading_map[k], "Current": p_data[k], "Max": p_data[f'{k}_Max'], "Grade": p_data[f'{k}_Grade']} for k in grading_map.keys()]
            st.markdown(render_table(pd.DataFrame(rows), ["Metric", "Current", "Max", "Grade"]), unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="text-align:center; font-weight:bold; font-size:20px; margin-top:20px;">Practice Score</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="score-box" style="background-color:{score_bg}; color:#1D1D1F;">{int(p_data["Practice Score"])}</div>', unsafe_allow_html=True)

    with t3:
        for i in range(0, len(day_df), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(day_df):
                    p_d = day_df.iloc[i + j]
                    p_score_bg = get_excel_gradient(p_d['Practice Score'])
                    with cols[j]:
                        st.markdown('<div class="gallery-card">', unsafe_allow_html=True)
                        ci, ct, cs = st.columns([1, 2.5, 0.8])
                        with ci:
                            st.markdown(f'<div style="text-align:center;"><img src="{p_d["PhotoURL_Fixed"]}" class="gallery-photo"></div>', unsafe_allow_html=True)
                            st.markdown(f'<p style="text-align:center; font-weight:bold;">{p_d["Name"]}</p>', unsafe_allow_html=True)
                        with ct:
                            rows = [{"Metric": grading_map[k], "Current": p_d[k], "Max": p_d[f'{k}_Max'], "Grade": p_d[f'{k}_Grade']} for k in grading_map.keys()]
                            st.markdown(render_table(pd.DataFrame(rows), ["Metric", "Current", "Max", "Grade"]), unsafe_allow_html=True)
                        with cs:
                            st.markdown(f'<div style="background-color:{p_score_bg}; color:#1D1D1F; border-radius:10px; text-align:center; padding:15px; font-size:24px; font-weight:800; margin-top:45px;">{int(p_d["Practice Score"])}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

    with t4:
        st.subheader("Leaderboard")
        st.dataframe(day_df[['Name', 'Total Jumps', 'Total Player Load', 'Practice Score']].astype(int, errors='ignore').sort_values('Practice Score', ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
