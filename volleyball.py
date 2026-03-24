import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# Sleek White Styling with Centered Tables
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 2rem; color: #007AFF; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #F5F5F7; border-radius: 10px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #007AFF; color: white; }
    
    /* Centering Table Text and Headers */
    [data-testid="stDataTable"] th { text-align: center !important; background-color: #F5F5F7 !important; }
    [data-testid="stDataTable"] td { text-align: center !important; }
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
    # Load Main Totals
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Load Phase Breakdown
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
    
    # Filter and copy to avoid column conflicts
    day_df = df[df['Date'] == sel_date_dt].copy()
    day_phase_df = phase_df[phase_df['Date'] == sel_date_dt].copy()

    # --- 3. CALCULATE GRADES (Current / Max * 100) ---
    metrics = ['Total Jumps', 'Total Player Load', 'Explosive Efforts', 'High Intensity Movement']
    for m in metrics:
        max_val = day_df[m].max()
        if max_val > 0:
            day_df[f'{m} Grade'] = (day_df[m] / max_val * 100).round(0)
        else:
            day_df[f'{m} Grade'] = 0
    
    grade_cols = [f'{m} Grade' for m in metrics]
    day_df['Practice Score'] = day_df[grade_cols].mean(axis=1).round(0)

    st.title(f"Performance Analysis: {selected_date_str}")
    
    tab1, tab2, tab3 = st.tabs(["Session Flow", "Player Deep Dive", "Data Leaderboard"])

    with tab1:
        st.subheader("Practice Intensity by Phase")
        
        # Explicitly select only phase columns to avoid "Total Player Load 2 times" error
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
        st.subheader("Individual Phase Breakdown")
        selected_player = st.selectbox("Select Player", day_df['Name'].unique())
        p_day_stats = day_df[day_df['Name'] == selected_player].iloc[0]
        p_phase_df = day_phase_df[day_phase_df['Name'] == selected_player]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Session Jumps", int(p_day_stats['Total Jumps']))
        m2.metric("Total Load", int(p_day_stats['Total Player Load']))
        # Practice Score box matches your screenshot logic
        m3.metric("Practice Score", f"{int(p_day_stats['Practice Score'])}%")

        st.divider()
        
        fig_p = px.bar(p_phase_df, x="Phase", y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
                       title=f"Jump Intensity Mix: {selected_player}",
                       barmode="group",
                       color_discrete_map={"IMA Jump Count High Band": "#FF3B30", "IMA Jump Count Med Band": "#FF9500", "IMA Jump Count Low Band": "#007AFF"},
                       template="plotly_white")
        fig_p.update_layout(xaxis={'categoryorder':'trace'}, xaxis_title=None, legend_title=None)
        st.plotly_chart(fig_p, use_container_width=True)

    with tab3:
        st.subheader("Leaderboard and Practice Grades")
        display_cols = ['Name', 'Total Jumps', 'Total Player Load', 'Explosive Efforts', 'Practice Score']
        # Convert to int for clean table display
        st.dataframe(day_df[display_cols].astype(int, errors='ignore'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
