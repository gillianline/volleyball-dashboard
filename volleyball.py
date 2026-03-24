import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Volleyball Performance Lab", layout="wide")

# --- 1. SECURITY BARRIER ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🏐 Coach Login")
        pwd = st.text_input("Enter Access Key:", type="password")
        if st.button("Unlock Dashboard"):
            if pwd == st.secrets["COACH_PWD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return True

if check_password():
    # --- 2. DATA CONNECTION ---
    SHEET_URL = st.secrets["GOOGLE_SHEET_URL"]

    @st.cache_data(ttl=300) 
    def load_data():
        data = pd.read_csv(SHEET_URL)
        # Clean up any weird spaces in headers
        data.columns = data.columns.str.strip()
        return data

    try:
        df = load_data()
        
        st.title("🏐 Volleyball Performance Dashboard")
        
        # --- 3. DASHBOARD UI ---
        # Using 'Name' instead of 'Player' based on your error message
        all_dates = df['Date'].unique()
        selected_date = st.sidebar.selectbox("Select Session Date", all_dates)
        day_df = df[df['Date'] == selected_date]

        # Top Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Jumps", int(day_df['Total Jumps'].sum()))
        m2.metric("Avg Player Load", round(day_df['Total Player Load'].mean(), 1))
        m3.metric("Explosive Efforts", int(day_df['Explosive Efforts'].sum()))
        m4.metric("High Intensity Mov.", int(day_df['High Intensity Movement'].sum()))

        st.divider()

        # Tabs for different views
        tab1, tab2 = st.tabs(["Daily Session View", "Season Comparison"])

        with tab1:
            st.subheader(f"Intensity Profile for {selected_date}")
            # Updated x="Name" to match your Google Sheet
            fig_jumps = px.bar(
                day_df, x="Name", 
                y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
                barmode="stack",
                color_discrete_map={
                    "IMA Jump Count High Band": "#e63946", 
                    "IMA Jump Count Med Band": "#f4a261", 
                    "IMA Jump Count Low Band": "#a8dadc"
                }
            )
            # Remove the numbers next to names as you requested previously
            fig_jumps.update_layout(yaxis_title="Jump Count", xaxis_title="")
            st.plotly_chart(fig_jumps, use_container_width=True)

        with tab2:
            st.subheader("Season Trends")
            selected_player = st.selectbox("Select Player to Track", df['Name'].unique())
            player_df = df[df['Name'] == selected_player].sort_values('Date')
            
            fig_trend = px.line(player_df, x='Date', y='Total Player Load', 
                               title=f"Workload Trend: {selected_player}",
                               markers=True)
            st.plotly_chart(fig_trend, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
