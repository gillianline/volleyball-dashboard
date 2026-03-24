import streamlit as st
import pandas as pd
import plotly.express as px
import math 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# Styling: Big Photos, Orange Borders, Centered Tables, Custom Date Picker
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stDateInput"] { width: 300px !important; margin: 0 auto !important; display: block; }
    
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; }
    .scout-table th { background-color: #F5F5F7; padding: 10px; border-bottom: 2px solid #E5E5E7; font-weight: 700; }
    .scout-table td { padding: 8px; border-bottom: 1px solid #F5F5F7; }

    .player-photo-large { border-radius: 50%; width: 240px; height: 240px; object-fit: cover; border: 6px solid #FF8200; }
    .score-box { color: white; padding: 20px; border-radius: 12px; font-size: 40px; font-weight: 800; text-align: center; }
    .gallery-card { border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; margin-bottom: 15px; }
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
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    phase_df = pd.read_csv(st.secrets["PHASE_SHEET_URL"])
    phase_df.columns = phase_df.columns.str.strip()
    phase_df['Date'] = pd.to_datetime(phase_df['Date']).dt.date
    return df, phase_df

try:
    df, phase_df = load_all_data()
    
    # --- CENTERED DATE SELECTION & COMPARISON ---
    st.markdown("<h3 style='text-align: center;'>Session Selection</h3>", unsafe_allow_html=True)
    selected_dates = st.multiselect("Select Date(s) to View or Compare", sorted(df['Date'].unique(), reverse=True), default=[sorted(df['Date'].unique())[-1]])

    if not selected_dates:
        st.warning("Please select at least one date.")
        st.stop()

    # Filter data based on selection
    day_df = df[df['Date'].isin(selected_dates)].copy()
    day_phase_df = phase_df[phase_df['Date'].isin(selected_dates)].copy()

    # --- SCORING LOGIC ---
    grading_map = {'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps', 'IMA Jump Count High Band': 'High Jumps', 'BMP Jumping Load': 'Jump Load', 'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance', 'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movements'}
    overall_maxes = df.groupby('Name')[list(grading_map.keys())].max()
    photo_map = df.dropna(subset=['PhotoURL']).drop_duplicates('Name').set_index('Name')['PhotoURL'].to_dict()

    def get_excel_gradient(score):
        score = max(0, min(100, score))
        return f"rgb({int(255*(score/50)) if score < 50 else 255}, {255 if score < 50 else int(255*(1-(score-50)/50))}, 0)"

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        grades = [math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0 for k in grading_map.keys()]
        row['Practice Score'] = math.ceil(sum(grades) / len(grades))
        for k in grading_map.keys(): row[f'{k}_Max'] = p_maxes[k]; row[f'{k}_Grade'] = math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0
        row['PhotoURL_Fixed'] = photo_map.get(p_name, "https://www.w3schools.com/howto/img_avatar.png")
        return row

    day_df = day_df.apply(process_player, axis=1)

    tab1, tab2, tab3, tab4 = st.tabs(["Session Breakdown", "Player Detail", "Team Comparison", "Leaderboard"])

    with tab1:
        st.subheader("Team Intensity by Phase")
        # Aggregating all drills: Warm Up, Serving, Block D, etc.
        phase_stats = day_phase_df.groupby(['Date', 'Phase'], sort=False)[['Total Jumps', 'Total Player Load']].mean().reset_index()
        
        # Multidate Phase Comparison
        fig_phase = px.bar(phase_stats, x="Phase", y="Total Player Load", color="Date", barmode="group", 
                           title="Phase Workload Comparison", template="plotly_white", color_discrete_sequence=px.colors.qualitative.Bold)
        st.plotly_chart(fig_phase, use_container_width=True)
        
        # Detailed Phase Table (No Index)
        st.markdown("<h4 style='text-align: center;'>Phase Averages (Per Player)</h4>", unsafe_allow_html=True)
        st.dataframe(phase_stats.astype({'Total Jumps': int, 'Total Player Load': int}), hide_index=True, use_container_width=True)

    with tab2:
        selected_player = st.selectbox("Select Player", day_df['Name'].unique())
        p_data_list = day_df[day_df['Name'] == selected_player]
        
        for _, p_data in p_data_list.iterrows():
            st.markdown(f"### Profile: {p_data['Name']} ({p_data['Date']})")
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1: st.image(p_data["PhotoURL_Fixed"], width=200)
            with c2:
                rows = [{"Metric": grading_map[k], "Current": int(p_data[k]), "Max": int(p_data[f'{k}_Max']), "Grade": int(p_data[f'{k}_Grade'])} for k in grading_map.keys()]
                st.table(pd.DataFrame(rows))
            with c3:
                bg = get_excel_gradient(p_data['Practice Score'])
                st.markdown(f'<div class="score-box" style="background-color:{bg};">{int(p_data["Practice Score"])}</div>', unsafe_allow_html=True)
            
            # Individual Player Phase Breakdown
            st.markdown("#### Phase Intensity Breakdown")
            p_phases = day_phase_df[(day_phase_df['Name'] == selected_player) & (day_phase_df['Date'] == p_data['Date'])]
            fig_p_phase = px.line(p_phases, x="Phase", y="Total Player Load", markers=True, title=f"Intensity Flow: {p_data['Date']}", template="plotly_white")
            st.plotly_chart(fig_p_phase, use_container_width=True)

    with tab3:
        st.subheader("Head-to-Head Gallery")
        # Shows cards for all selected dates side-by-side or stacked
        for i in range(0, len(day_df), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(day_df):
                    p_d = day_df.iloc[i + j]
                    with cols[j]:
                        st.markdown(f'<div class="gallery-card"><b>{p_d["Name"]}</b> ({p_d["Date"]})<br>Score: {int(p_d["Practice Score"])}</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
