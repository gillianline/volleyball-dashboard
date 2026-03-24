import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# Sleek White Styling with Centered Tables and Card UI
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #007AFF; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #F5F5F7; border-radius: 10px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #007AFF; color: white; }
    
    /* Centering Table Text */
    [data-testid="stDataTable"] th { text-align: center !important; background-color: #F5F5F7 !important; }
    [data-testid="stDataTable"] td { text-align: center !important; }

    /* Custom Grade Card Styling */
    .grade-card {
        padding: 20px;
        border: 1px solid #E5E5E7;
        border-radius: 12px;
        background-color: #FBFBFD;
    }
    .practice-score-box {
        background-color: #F2994A;
        color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
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

    # --- 3. CALCULATE GRADES (ALL COLUMNS) ---
    # Identifying all numeric columns except Week, Day, and Year-related ones
    exclude_cols = ['Week', 'Day', 'Date', 'Name']
    numeric_cols = [c for c in day_df.columns if c not in exclude_cols and day_df[c].dtype in ['int64', 'float64']]
    
    grade_data = []
    for col in numeric_cols:
        max_val = day_df[col].max()
        day_df[f'{col} Max'] = max_val
        if max_val > 0:
            day_df[f'{col} Grade'] = (day_df[col] / max_val * 100).round(0)
        else:
            day_df[f'{col} Grade'] = 0

    grade_col_names = [f'{c} Grade' for c in numeric_cols]
    day_df['Practice Score'] = day_df[grade_col_names].mean(axis=1).round(0)

    st.title(f"Performance Analysis: {selected_date_str}")
    
    tab1, tab2, tab3 = st.tabs(["Session Flow", "Player Deep Dive", "Data Leaderboard"])

    with tab1:
        st.subheader("Practice Intensity by Phase")
        phase_cols = ['Phase', 'Total Jumps', 'Total Player Load', 'Explosive Efforts']
        phase_avg = day_phase_df[phase_cols].groupby('Phase', sort=False).mean().reset_index().round(0)
        
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
        st.subheader("Player Profile Grade Card")
        selected_player = st.selectbox("Select Player", day_df['Name'].unique())
        p_data = day_df[day_df['Name'] == selected_player].iloc[0]

        # Constructing the Grade Card Table like your screenshot
        card_rows = []
        for col in numeric_cols:
            card_rows.append({
                "Metric": col,
                "Current": p_data[col],
                "Max": p_data[f'{col} Max'],
                "Grade": int(p_data[f'{col} Grade'])
            })
        
        grade_card_df = pd.DataFrame(card_rows)

        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # Displaying the Card Table
            st.dataframe(grade_card_df, use_container_width=True, hide_index=True)
            
        with col_right:
            st.markdown(f"""
                <div style="text-align: center; padding-top: 50px;">
                    <p style="font-size: 20px; color: #1D1D1F; margin-bottom: 5px;">Practice Score</p>
                    <div class="practice-score-box">
                        {int(p_data['Practice Score'])}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.divider()
        # Drill Breakdown below the card
        p_phase_df = day_phase_df[day_phase_df['Name'] == selected_player]
        fig_p = px.bar(p_phase_df, x="Phase", y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
                       title=f"Jump Intensity Mix: {selected_player}",
                       barmode="group",
                       color_discrete_map={"IMA Jump Count High Band": "#FF3B30", "IMA Jump Count Med Band": "#FF9500", "IMA Jump Count Low Band": "#007AFF"},
                       template="plotly_white")
        fig_p.update_layout(xaxis={'categoryorder':'trace'}, xaxis_title=None, legend_title=None)
        st.plotly_chart(fig_p, use_container_width=True)

    with tab3:
        st.subheader("Leaderboard")
        display_cols = ['Name', 'Total Jumps', 'Total Player Load', 'Practice Score']
        st.dataframe(day_df[display_cols].astype(int, errors='ignore'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
