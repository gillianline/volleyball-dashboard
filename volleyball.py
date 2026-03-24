import streamlit as st
import pandas as pd
import plotly.express as px
import math # Added for precise rounding

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# Sleek White Styling
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stDataTable"] th { text-align: center !important; background-color: #F5F5F7 !important; }
    [data-testid="stDataTable"] td { text-align: center !important; }

    .img-container { display: flex; justify-content: center; margin-bottom: 20px; }
    .player-photo {
        border-radius: 50%;
        width: 180px;
        height: 180px;
        object-fit: cover;
        border: 4px solid #007AFF;
    }

    .score-box {
        background-color: #F2994A;
        color: white;
        padding: 25px 55px;
        border-radius: 12px;
        font-size: 48px;
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

    # --- UPDATED SCORING & PHOTO LOGIC ---
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

    # 1. Get Season Maxes
    overall_maxes = df.groupby('Name')[list(grading_map.keys())].max()
    
    # 2. Get the FIRST available PhotoURL for each person (ignores empty rows)
    photo_map = df.dropna(subset=['PhotoURL']).drop_duplicates('Name').set_index('Name')['PhotoURL'].to_dict()

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        grades = []
        for internal in grading_map.keys():
            curr = row[internal]
            m_val = p_maxes[internal]
            
            # ROUNDUP logic using math.ceil
            if m_val > 0:
                grade = math.ceil((curr / m_val) * 100)
            else:
                grade = 0
                
            row[f'{internal}_Max'] = m_val
            row[f'{internal}_Grade'] = grade
            grades.append(grade)
        
        # Final Practice Score is Average of Grades
        row['Practice Score'] = math.ceil(sum(grades) / len(grades))
        # Attach Photo from the map
        row['PhotoURL_Fixed'] = photo_map.get(p_name, "https://www.w3schools.com/howto/img_avatar.png")
        return row

    day_df = day_df.apply(process_player, axis=1)

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["Session Flow", "Player Profile", "Leaderboard"])

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
        selected_player = st.selectbox("Select Player", day_df['Name'].unique())
        p_data = day_df[day_df['Name'] == selected_player].iloc[0]

        col_img, col_card, col_score = st.columns([1, 2, 1])
        
        with col_img:
            st.markdown(f'<div class="img-container"><img src="{p_data["PhotoURL_Fixed"]}" class="player-photo"></div>', unsafe_allow_html=True)
            st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]}</h2>', unsafe_allow_html=True)

        with col_card:
            card_rows = []
            for internal, display in grading_map.items():
                is_dec = 'Distance' in display or 'Load' in display
                card_rows.append({
                    "Metric": display,
                    "Current": round(p_data[internal], 1) if is_dec else int(p_data[internal]),
                    "Max": round(p_data[f'{internal}_Max'], 1) if is_dec else int(p_data[f'{internal}_Max']),
                    "Grade": int(p_data[f'{internal}_Grade'])
                })
            st.dataframe(pd.DataFrame(card_rows), use_container_width=True, hide_index=True)
            
        with col_score:
            st.markdown(f'<div style="text-align:center; font-weight:bold; margin-top:20px;">Practice Score</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="score-box">{int(p_data["Practice Score"])}</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("Drill Intensity Breakdown")
        p_phase = day_phase_df[day_phase_df['Name'] == selected_player]
        fig_p = px.bar(p_phase, x="Phase", y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
                       barmode="group", color_discrete_map={"IMA Jump Count High Band": "#FF3B30", "IMA Jump Count Med Band": "#FF9500", "IMA Jump Count Low Band": "#007AFF"},
                       template="plotly_white")
        fig_p.update_layout(xaxis={'categoryorder':'trace'}, xaxis_title=None, legend_title=None)
        st.plotly_chart(fig_p, use_container_width=True)

    with tab3:
        st.subheader("Leaderboard")
        st.dataframe(day_df[['Name', 'Total Jumps', 'Total Player Load', 'Practice Score']].sort_values('Practice Score', ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
