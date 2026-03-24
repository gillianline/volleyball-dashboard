import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# Sleek White Styling
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 2rem; color: #007AFF; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #F5F5F7; border-radius: 10px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #007AFF; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. SECURITY ---
if "password_correct" not in st.session_state:
    st.title("🔒 Access Restricted")
    pwd = st.text_input("Enter Access Key:", type="password")
    if st.button("Unlock Dashboard"):
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
    
    day_df = df[df['Date'] == sel_date_dt].sort_values('Total Jumps', ascending=False)
    day_phase_df = phase_df[phase_df['Date'] == sel_date_dt]

    st.title(f"Performance Analysis: {selected_date_str}")
    
    # --- 3. THE TABBED NAVIGATION ---
    tab1, tab2, tab3 = st.tabs(["🕒 Session Flow", "👤 Player Deep Dive", "📋 Data Leaderboard"])

    with tab1:
        st.subheader("Practice Intensity by Phase")
        # Average per player per phase
        phase_avg = day_phase_df.groupby('Phase')[['Total Jumps', 'Explosive Efforts', 'Total Player Load']].mean().reset_index()
        
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(phase_avg, x="Phase", y="Total Jumps", title="Avg Jumps per Player", color_discrete_sequence=["#007AFF"], template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.line(phase_avg, x="Phase", y="Total Player Load", title="Workload Trend", markers=True, color_discrete_sequence=["#FF9500"], template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)
            
        st.info("💡 High Ball and Block D typically show the highest jumping load. Use this to verify your practice plan.")

    with tab2:
        st.subheader("Individual Phase Breakdown")
        selected_player = st.selectbox("Select Player", day_df['Name'].unique())
        p_df = day_phase_df[day_phase_df['Name'] == selected_player]
        
        # Player Stats Bar
        m1, m2, m3 = st.columns(3)
        m1.metric("Session Jumps", int(p_df['Total Jumps'].sum()))
        m2.metric("Total Load", int(p_df['Total Player Load'].sum()))
        m3.metric("Explosive Efforts", int(p_df['Explosive Efforts'].sum()))

        st.divider()
        
        # Detailed Breakdown for the specific player
        fig_p = px.bar(p_df, x="Phase", y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
                       title=f"Jump Intensity mix across Phases: {selected_player}",
                       barmode="group", # Changed to group for better visual separation
                       color_discrete_map={"IMA Jump Count High Band": "#FF3B30", "IMA Jump Count Med Band": "#FF9500", "IMA Jump Count Low Band": "#007AFF"},
                       template="plotly_white")
        fig_p.update_layout(xaxis_title=None, legend_title=None)
        st.plotly_chart(fig_p, use_container_width=True)

    with tab3:
        st.subheader("Session Statistics Leaderboard")
        # Cleaned up table with the core metrics
        cols = ['Name', 'Total Jumps', 'IMA Jump Count High Band', 'Total Player Load', 'Explosive Efforts', 'High Intensity Movement']
        st.dataframe(day_df[cols], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error Syncing Data: {e}")
