import streamlit as st
import pandas as pd
import plotly.express as px
import math 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# Sleek White Styling + BIG PHOTOS + MANUAL TABLE CENTERING
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    
    /* Custom CSS for the HTML Table to ensure NO INDEX and CENTERED TEXT */
    .scout-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 16px;
        text-align: center;
    }
    .scout-table th {
        background-color: #F5F5F7;
        color: #1D1D1F;
        font-weight: 700;
        padding: 12px;
        border-bottom: 2px solid #E5E5E7;
    }
    .scout-table td {
        padding: 10px;
        border-bottom: 1px solid #F5F5F7;
        color: #1D1D1F;
    }

    .img-container { display: flex; justify-content: center; margin-bottom: 15px; }
    .player-photo-large {
        border-radius: 50%;
        width: 240px; /* Even bigger as requested */
        height: 240px;
        object-fit: cover;
        border: 5px solid #007AFF;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    }

    .score-box-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; }
    .score-label { font-size: 22px; font-weight: 700; margin-bottom: 8px; }
    .score-box {
        background-color: #F2994A;
        color: white;
        padding: 30px 60px;
        border-radius: 15px;
        font-size: 54px;
        font-weight: 800;
        text-align: center;
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
    sorted_dates = sorted(df['Date'].unique())
    date_options = [d.strftime('%m/%d/%Y') for d in sorted_dates]
    
    st.sidebar.header("Session Filter")
    selected_date_str = st.sidebar.selectbox("Select Date", date_options, index=len(date_options)-1)
    sel_date_dt = pd.to_datetime(selected_date_str)
    
    day_df = df[df['Date'] == sel_date_dt].copy()
    day_phase_df = phase_df[phase_df['Date'] == sel_date_dt].copy()

    # --- SCORING LOGIC (Season Max & Round Up) ---
    grading_map = {
        'Total Jumps': 'Total Jumps',
        'IMA Jump Count Med Band': 'Moderate Jumps',
        'IMA Jump Count High Band': 'High Jumps',
        'BMP Jumping Load': 'Jump Load',
        'Total Player Load': 'Player Load',
        'Estimated Distance (y)': 'Estimated Distance',
        'Explosive Efforts': 'Explosive Efforts',
        'High Intensity Movement': 'High Intensity Movements'
    }

    overall_maxes = df.groupby('Name')[list(grading_map.keys())].max()
    photo_map = df.dropna(subset=['PhotoURL']).drop_duplicates('Name').set_index('Name')['PhotoURL'].to_dict()

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        grades = []
        for internal in grading_map.keys():
            curr = row[internal]
            m_val = p_maxes[internal]
            grade = math.ceil((curr / m_val) * 100) if m_val > 0 else 0
            row[f'{internal}_Max'] = m_val
            row[f'{internal}_Grade'] = grade
            grades.append(grade)
        row['Practice Score'] = math.ceil(sum(grades) / len(grades))
        row['PhotoURL_Fixed'] = photo_map.get(p_name, "https://www.w3schools.com/howto/img_avatar.png")
        return row

    full_graded_df = df.apply(process_player, axis=1)
    day_df = full_graded_df[full_graded_df['Date'] == sel_date_dt].sort_values('Practice Score', ascending=False)

    # --- HELPER FUNCTION FOR TABLE ---
    def render_custom_table(dataframe, cols_to_show):
        html = '<table class="scout-table"><thead><tr>'
        for col in cols_to_show:
            html += f'<th>{col}</th>'
        html += '</tr></thead><tbody>'
        for _, row in dataframe.iterrows():
            html += '<tr>'
            for col in cols_to_show:
                val = row[col]
                html += f'<td>{int(round(val,0)) if isinstance(val, (int, float)) else val}</td>'
            html += '</tr>'
        html += '</tbody></table>'
        return html

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["Session Flow", "Player Profile", "Team Gallery", "Leaderboard"])

    with tab2:
        selected_player = st.selectbox("Select Player Profile", day_df['Name'].unique())
        p_data = day_df[day_df['Name'] == selected_player].iloc[0]
        
        col_img, col_card, col_score = st.columns([1, 2, 1])
        with col_img:
            st.markdown(f'<div class="img-container"><img src="{p_data["PhotoURL_Fixed"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
            st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]}</h2>', unsafe_allow_html=True)
        
        with col_card:
            card_rows = []
            for internal, display in grading_map.items():
                card_rows.append({
                    "Metric": display,
                    "Current": p_data[internal],
                    "Max": p_data[f'{internal}_Max'],
                    "Grade": p_data[f'{internal}_Grade']
                })
            # RENDER TABLE WITHOUT INDEX
            st.markdown(render_custom_table(pd.DataFrame(card_rows), ["Metric", "Current", "Max", "Grade"]), unsafe_allow_html=True)
        
        with col_score:
            st.markdown(f'<div class="score-box-container"><div class="score-label">Practice Score</div><div class="score-box">{int(p_data["Practice Score"])}</div></div>', unsafe_allow_html=True)

    with tab3:
        st.subheader("Full Roster Report Cards")
        for i in range(0, len(day_df), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(day_df):
                    p_data = day_df.iloc[i + j]
                    with cols[j]:
                        st.markdown(f'<div style="border:1px solid #E5E5E7; padding:20px; border-radius:15px; margin-bottom:20px;">', unsafe_allow_html=True)
                        c_img, c_table, c_scr = st.columns([1, 2, 1])
                        with c_img:
                            st.markdown(f'<div class="img-container"><img src="{p_data["PhotoURL_Fixed"]}" class="player-photo-large" style="width:100px; height:100px;"></div>', unsafe_allow_html=True)
                            st.markdown(f'<p style="text-align:center; font-weight:bold;">{p_data["Name"]}</p>', unsafe_allow_html=True)
                        with c_table:
                            card_rows = [{"Metric": grading_map[k], "Current": p_data[k], "Grade": p_data[f'{k}_Grade']} for k in grading_map.keys()]
                            st.markdown(render_custom_table(pd.DataFrame(card_rows), ["Metric", "Current", "Grade"]), unsafe_allow_html=True)
                        with c_scr:
                            st.markdown(f'<div class="score-box-container"><div class="score-box" style="font-size:24px; padding:15px 30px;">{int(p_data["Practice Score"])}</div></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.subheader("Leaderboard")
        st.dataframe(day_df[['Name', 'Total Jumps', 'Total Player Load', 'Practice Score']].astype(int, errors='ignore'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
