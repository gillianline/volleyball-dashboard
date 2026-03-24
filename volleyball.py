import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# Sleek White Styling
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #007AFF; font-weight: 600; }
    .stHeader { color: #1D1D1F; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. SECURITY ---
if "password_correct" not in st.session_state:
    st.title("🔒 Coach Secure Access")
    pwd = st.text_input("Enter Access Key:", type="password")
    if st.button("Unlock Dashboard"):
        if pwd == st.secrets["COACH_PWD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Invalid Key")
    st.stop()

# --- 2. DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    # Load Main Totals (Sheet 1)
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip() 
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Load Phase Breakdown (Sheet 2)
    phase_df = pd.read_csv(st.secrets["PHASE_SHEET_URL"])
    phase_df.columns = phase_df.columns.str.strip()
    phase_df['Date'] = pd.to_datetime(phase_df['Date'])
    
    return df, phase_df

try:
    df, phase_df = load_all_data()
    
    # Sort dates chronologically for the sidebar
    sorted_dates = sorted(df['Date'].unique())
    date_options = [d.strftime('%m/%d/%Y') for d in sorted_dates]
    
    st.sidebar.header("Session Filter")
    selected_date_str = st.sidebar.selectbox("Select Practice Date", date_options, index=len(date_options)-1)
    sel_date_dt = pd.to_datetime(selected_date_str)
    
    # Filter both datasets for the selected day
    day_df = df[df['Date'] == sel_date_dt].sort_values('Total Jumps', ascending=False)
    day_phase_df = phase_df[phase_df['Date'] == sel_date_dt]

    st.title(f"Volleyball Practice Analysis")
    st.caption(f"Session data for {selected_date_str}")

    # --- 3. DRILL / PHASE OVERVIEW (AVERAGES) ---
    st.subheader("Phase Intensity (Average per Player)")
    
    # Grouping by 'Phase' and calculating MEAN
    phase_summary = day_phase_df.groupby('Phase')[['Total Jumps', 'Explosive Efforts']].mean().reset_index().round(1)
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        fig_phase_j = px.bar(
            phase_summary, x="Phase", y="Total Jumps",
            title="Avg Jumps per Player by Drill",
            color_discrete_sequence=["#007AFF"],
            template="plotly_white"
        )
        fig_phase_j.update_layout(xaxis_title=None, yaxis_title="Avg Jumps")
        st.plotly_chart(fig_phase_j, use_container_width=True)
        
    with col_right:
        fig_phase_e = px.bar(
            phase_summary, x="Phase", y="Explosive Efforts",
            title="Avg Explosive Efforts per Player by Drill",
            color_discrete_sequence=["#5856D6"],
            template="plotly_white"
        )
        fig_phase_e.update_layout(xaxis_title=None, yaxis_title="Avg Efforts")
        st.plotly_chart(fig_phase_e, use_container_width=True)

    st.divider()

    # --- 4. PLAYER-SPECIFIC DRILL MIX ---
    st.subheader("Individual Drill Breakdown")
    player_list = day_df['Name'].unique()
    selected_player = st.selectbox("Select a Player to analyze their drill mix", player_list)
    
    player_phase = day_phase_df[day_phase_df['Name'] == selected_player]
    
    fig_player_mix = px.bar(
        player_phase, x="Phase", 
        y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
        title=f"Jump Intensity Mix by Drill: {selected_player}",
        barmode="stack",
        color_discrete_map={
            "IMA Jump Count High Band": "#FF3B30", 
            "IMA Jump Count Med Band": "#FF9500", 
            "IMA Jump Count Low Band": "#007AFF"
        },
        template="plotly_white"
    )
    fig_player_mix.update_layout(xaxis_title=None, yaxis_title="Intensity Count", legend_title=None)
    st.plotly_chart(fig_player_mix, use_container_width=True)

    st.divider()

    # --- 5. DATA TABLE ---
    st.subheader("Daily Session Totals")
    cols = ['Name', 'Total Jumps', 'IMA Jump Count High Band', 'Total Player Load', 'Explosive Efforts']
    st.dataframe(day_df[cols], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Ensure Sheet 2 has a column named 'Phase' and Sheet 1/2 have a column named 'Name'.")
