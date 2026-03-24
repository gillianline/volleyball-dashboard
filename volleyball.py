import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# Sleek White Styling with Centered Table Headers/Cells
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 2rem; color: #007AFF; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #F5F5F7; border-radius: 10px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #007AFF; color: white; }
    
    /* Centering Table Text */
    [data-testid="stDataTable"] th { text-align: center !important; }
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
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'])
    
    phase_df = pd.read_csv(st.secrets["PHASE_SHEET_URL"])
    phase_df.columns = phase_df.columns.str.strip()
    phase_df['Date'] = pd.to_datetime(phase_df['Date'])
    
    # Remove decimals across all numeric columns
    df = df.round(0)
    phase_df = phase_df.round(0)
    
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
    
    tab1, tab2, tab3 = st.tabs(["Session Flow", "Player Deep Dive", "Data Leaderboard"])

    with tab1:
        st.subheader("Practice Intensity by Phase")
        phase_avg = day_phase_df.groupby('Phase')[['Total Jumps', 'Explosive Efforts', 'Total Player Load']].mean().reset_index().round(0)
        
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(phase_avg, x="Phase", y="Total Jumps", title="Avg Jumps per Player", color_discrete_sequence=["#007AFF"], template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.line(phase_avg, x="Phase", y="Total Player Load", title="Workload Trend", markers=True, color_discrete_sequence=["#FF9500"], template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)
            
        st.info("Performance Insight: Compare the 'Workload Trend' line against your planned practice intensity to ensure tapering or peaking is on track.")

    with tab2:
        st.subheader("Individual Phase Breakdown")
        selected_player = st.selectbox("Select Player", day_df['Name'].unique())
        p_df = day_phase_df[day_phase_df['Name'] == selected_player]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Session Jumps", int(p_df['Total Jumps'].sum()))
        m2.metric("Total Load", int(p_df['Total Player Load'].sum()))
        m3.metric("Explosive Efforts", int(p_df['Explosive Efforts'].sum()))

        st.divider()
        
        fig_p = px.bar(p_df, x="Phase", y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
                       title=f"Jump Intensity Mix: {selected_player}",
                       barmode="group",
                       color_discrete_map={"IMA Jump Count High Band": "#FF3B30", "IMA Jump Count Med Band": "#FF9500", "IMA Jump Count Low Band": "#007AFF"},
                       template="plotly_white")
        fig_p.update_layout(xaxis_title=None, legend_title=None)
        st.plotly_chart(fig_p, use_container_width=True)

    with tab3:
        # NEW: Performance Outliers Section
        st.subheader("Session Outliers")
        avg_jumps = day_df['Total Jumps'].mean()
        high_volume = day_df[day_df['Total Jumps'] > (avg_jumps * 1.2)]
        
        if not high_volume.empty:
            st.warning(f"High Volume Alert: {', '.join(high_volume['Name'].tolist())} exceeded 120% of team average jumps.")
        
        st.subheader("Full Session Statistics")
        cols = ['Name', 'Total Jumps', 'IMA Jump Count High Band', 'Total Player Load', 'Explosive Efforts', 'High Intensity Movement']
        # Displaying centered table without index
        st.dataframe(day_df[cols].astype(int, errors='ignore'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
