import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="VB Performance Lab", layout="wide")

# Custom CSS for a "Pro Sports" Dark Theme
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { font-size: 2rem; color: #00d4ff; font-weight: bold; }
    .stTable { background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. SECURITY ---
if "password_correct" not in st.session_state:
    st.title("🏐 Coach Secure Access")
    pwd = st.text_input("Access Key:", type="password")
    if st.button("Unlock"):
        if pwd == st.secrets["COACH_PWD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Denied")
    st.stop()

# --- 2. DATA LOADING ---
@st.cache_data(ttl=300)
def load_data():
    # Pulling from the Google Sheet URL in your Secrets
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data()
    all_dates = df['Date'].unique()
    
    # Sidebar Filters
    st.sidebar.header("Controls")
    selected_date = st.sidebar.selectbox("Select Practice Date", all_dates)
    
    # Filter data for that day
    day_df = df[df['Date'] == selected_date].sort_values('Total Jumps', ascending=False)

    # --- 3. THE "PRACTICE LEADERS" (Instead of Team Totals) ---
    st.title(f"📊 Practice Report: {selected_date}")
    
    col1, col2, col3 = st.columns(3)
    
    # Get top performers for the day
    top_jumper = day_df.iloc[0]
    top_load = day_df.sort_values('Total Player Load', ascending=False).iloc[0]
    top_intensity = day_df.sort_values('High Intensity Movement', ascending=False).iloc[0]

    with col1:
        st.metric("Top Jump Volume", top_jumper['Name'], f"{int(top_jumper['Total Jumps'])} Jumps")
    with col2:
        st.metric("Highest Workload", top_load['Name'], f"{int(top_load['Total Player Load'])} Load")
    with col3:
        st.metric("Intensity Leader", top_intensity['Name'], f"{int(top_intensity['High Intensity Movement'])} Efforts")

    st.divider()

    # --- 4. INDIVIDUAL PERFORMANCE CARDS ---
    st.subheader("Player Jump Profiles")
    # Stacked bar with clean colors
    fig_jumps = px.bar(
        day_df, x="Name", 
        y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
        barmode="stack",
        color_discrete_map={
            "IMA Jump Count High Band": "#FF4B4B", # Red
            "IMA Jump Count Med Band": "#FFAA00",  # Orange
            "IMA Jump Count Low Band": "#00D4FF"   # Blue
        },
        template="plotly_dark"
    )
    # Clean up the chart axes
    fig_jumps.update_layout(
        xaxis_title=None, 
        yaxis_title="Count", 
        legend_title="Intensity",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_jumps, use_container_width=True)

    st.divider()

    # --- 5. DETAILED STATS TABLE ---
    st.subheader("Individual Breakdown")
    # Select specific columns the coach cares about
    stats_to_show = ['Name', 'Total Jumps', 'IMA Jump Count High Band', 'Total Player Load', 'Explosive Efforts']
    
    # Highlight the high-load players in red in the table
    st.dataframe(
        day_df[stats_to_show].style.background_gradient(subset=['Total Player Load'], cmap='Reds'),
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error(f"Waiting for data... or Error: {e}")
