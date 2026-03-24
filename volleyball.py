import streamlit as st
import pandas as pd
import plotly.express as px
import math 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# Sleek White Styling + FORCE CENTER + No Index
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    
    /* Center all table content and hide index */
    [data-testid="stTable"] th { text-align: center !important; background-color: #F5F5F7 !important; border-bottom: 2px solid #E5E5E7 !important; }
    [data-testid="stTable"] td { text-align: center !important; border-bottom: 1px solid #F5F5F7 !important; }
    
    .img-container { display: flex; justify-content: center; margin-bottom: 10px; }
    .player-photo {
        border-radius: 50%;
        width: 130px;
        height: 130px;
        object-fit: cover;
        border: 3px solid #007AFF;
    }

    /* Practice Score Box Styling */
    .score-box-container { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .score-label { font-size: 14px; font-weight: 700; margin-bottom: 4px; color: #1D1D1F; }
    .score-box {
        background-color: #F2994A;
        color: white;
        padding: 12px 25px;
        border-radius: 10px;
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        min-width: 80px;
    }

    /* Card Wrapper to keep two-column looks clean */
    .card-wrapper {
        border: 1px solid #E5E5E7;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #FBFBFD;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. SECURITY ---
if "password_correct" not in st.session_state:
    st.title("Access Restricted")
    pwd = st.text_input("Access Key:", type="password")
    if st.button("Unlock"):
        if pwd == st.secrets["COACH_PWD"]:
            st.session_state["password_correct"] = True
            st.rerun()
    st.stop()

# --- 2. DATA LOADING ---
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

    # --- 3. SCORING LOGIC (Season Max & Round Up) ---
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

    day_df = day_df.apply(process_player, axis=1).sort_values('Practice Score', ascending=False)

    # --- 4. TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["Session Flow", "Player Profile", "Team Gallery", "Leaderboard"])

    with tab1:
        st.subheader("Practice Intensity by Phase")
        phase_avg = day_phase_df.groupby('Phase', sort=False)[['Total Jumps', 'Total Player Load']].mean().reset_index()
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(phase_avg, x="Phase", y="Total Jumps", title="Avg Jumps per Player", color_discrete_sequence=["#007AFF"], template="plotly_white")
            fig1.update_layout(xaxis={'categoryorder':'trace'})
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.line(phase_avg, x="Phase", y="Total Player Load", title="Workload Trend", markers=True, color_discrete_sequence=["#FF9500"], template="plotly_white")
            fig2.update_layout(xaxis={'categoryorder':'trace'})
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        selected_player = st.selectbox("Select Player Profile", day_df['Name'].unique())
        p_data = day_df[day_df['Name'] == selected_player].iloc[0]
        
        col_img, col_card, col_score = st.columns([1, 2, 1])
        with col_img:
            st.markdown(f'<div class="img-container"><img src="{p_data["PhotoURL_Fixed"]}" class="player-photo"></div>', unsafe_allow_html=True)
            st.markdown(f'<h3 style="text-align:center;">{p_data["Name"]}</h3>', unsafe_allow_html=True)
        with col_card:
            rows = [{"Metric": display, "Current": int(round(p_data[internal], 0)), "Max": int(round(p_data[f'{internal}_Max'], 0)), "Grade": int(p_data[f'{internal}_Grade'])} for internal, display in grading_map.items()]
            st.table(pd.DataFrame(rows))
        with col_score:
            st.markdown(f'<div class="score-box-container"><div class="score-label">Practice Score</div><div class="score-box">{int(p_data["Practice Score"])}</div></div>', unsafe_allow_html=True)

    with tab3:
        st.subheader("Full Roster Report Cards")
        # Display 2 players per row
        for i in range(0, len(day_df), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(day_df):
                    p_data = day_df.iloc[i + j]
                    with cols[j]:
                        st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
                        c_img, c_table, c_scr = st.columns([1, 2, 1])
                        with c_img:
                            st.markdown(f'<div class="img-container"><img src="{p_data["PhotoURL_Fixed"]}" class="player-photo" style="width:80px; height:80px;"></div>', unsafe_allow_html=True)
                            st.markdown(f'<p style="text-align:center; font-weight:bold; font-size:14px;">{p_data["Name"]}</p>', unsafe_allow_html=True)
                        with c_table:
                            rows = [{"Metric": display, "Current": int(round(p_data[internal], 0)), "Grade": int(p_data[f'{internal}_Grade'])} for internal, display in grading_map.items()]
                            st.table(pd.DataFrame(rows))
                        with c_scr:
                            st.markdown(f'<div class="score-box-container"><div class="score-label" style="font-size:10px;">Score</div><div class="score-box" style="font-size:20px; padding:8px 15px;">{int(p_data["Practice Score"])}</div></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.subheader("Leaderboard")
        st.dataframe(day_df[['Name', 'Total Jumps', 'Total Player Load', 'Practice Score']].astype(int, errors='ignore').sort_values('Practice Score', ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
