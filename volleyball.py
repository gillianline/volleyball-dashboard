import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# Sleek White Styling with centered tables and "Practice Score" box
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #007AFF; font-weight: 700; }
    
    /* Centering Table Text */
    [data-testid="stDataTable"] th { text-align: center !important; background-color: #F5F5F7 !important; border-bottom: 2px solid #E5E5E7 !important; }
    [data-testid="stDataTable"] td { text-align: center !important; border-bottom: 1px solid #F5F5F7 !important; }

    /* Practice Score Box Styling */
    .practice-score-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        padding-top: 40px;
    }
    .score-label { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .score-box {
        background-color: #F2994A;
        color: white;
        padding: 30px 60px;
        border-radius: 12px;
        font-size: 48px;
        font-weight: 800;
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

    # --- 3. THE SCORING LOGIC ---
    # These are the specific columns from your screenshot
    grading_metrics = [
        'Total Jumps', 'IMA Jump Count Med Band', 'IMA Jump Count High Band', 
        'BMP Jumping Load', 'Total Player Load', 'Estimated Distance (y)', 
        'Explosive Efforts', 'High Intensity Movement'
    ]
    
    # Map the internal names to the "Pretty Names" for the coach's card
    pretty_names = {
        'Total Jumps': 'Total Jumps',
        'IMA Jump Count Med Band': 'Moderate Jumps',
        'IMA Jump Count High Band': 'High Jumps',
        'BMP Jumping Load': 'Jump Load',
        'Total Player Load': 'Player Load',
        'Estimated Distance (y)': 'Estimated Distance',
        'Explosive Efforts': 'Explosive Efforts',
        'High Intensity Movement': 'High Intensity Movements'
    }

    # Calculate Maxes and Individual Grades
    grade_cols = []
    for metric in grading_metrics:
        if metric in day_df.columns:
            max_val = day_df[metric].max()
            day_df[f'{metric}_Max'] = max_val
            # Grade = Roundup(Current / Max * 100)
            if max_val > 0:
                day_df[f'{metric}_Grade'] = (day_df[metric] / max_val * 100).apply(lambda x: int(-(-x // 1)))
            else:
                day_df[f'{metric}_Grade'] = 0
            grade_cols.append(f'{metric}_Grade')

    # Practice Score = Average of all grades
    day_df['Practice Score'] = day_df[grade_cols].mean(axis=1).round(0).astype(int)

    # --- 4. TABS ---
    tab1, tab2, tab3 = st.tabs(["Session Flow", "Player Profile", "Leaderboard"])

    with tab1:
        st.subheader("Practice Intensity by Phase")
        # Ensure Phase order from Google Sheet is respected
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

        # Build the exact table from your screenshot
        card_data = []
        for m in grading_metrics:
            if m in day_df.columns:
                card_data.append({
                    " ": pretty_names[m],
                    "Current": int(p_data[m]) if 'Distance' not in m and 'Load' not in m else round(p_data[m], 1),
                    "Max": int(p_data[f'{m}_Max']) if 'Distance' not in m and 'Load' not in m else round(p_data[f'{m}_Max'], 1),
                    "Grade": int(p_data[f'{m}_Grade'])
                })
        
        card_df = pd.DataFrame(card_data)

        col_card, col_score = st.columns([2, 1])
        
        with col_card:
            st.dataframe(card_df, use_container_width=True, hide_index=True)
            
        with col_score:
            st.markdown(f"""
                <div class="practice-score-container">
                    <div class="score-label">Practice Score</div>
                    <div class="score-box">{p_data['Practice Score']}</div>
                </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.subheader("Phase Breakdown")
        p_phase = day_phase_df[day_phase_df['Name'] == selected_player]
        fig_p = px.bar(p_phase, x="Phase", y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
                       title=f"Jump Intensity Mix: {selected_player}", barmode="group",
                       color_discrete_map={"IMA Jump Count High Band": "#FF3B30", "IMA Jump Count Med Band": "#FF9500", "IMA Jump Count Low Band": "#007AFF"},
                       template="plotly_white")
        fig_p.update_layout(xaxis={'categoryorder':'trace'}, xaxis_title=None, legend_title=None)
        st.plotly_chart(fig_p, use_container_width=True)

    with tab3:
        st.subheader("Leaderboard")
        st.dataframe(day_df[['Name', 'Total Jumps', 'Total Player Load', 'Practice Score']].sort_values('Practice Score', ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
