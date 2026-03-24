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
    # Put your transformed Google Sheet link in Secrets as 'GOOGLE_SHEET_URL'
    SHEET_URL = st.secrets["GOOGLE_SHEET_URL"]

    @st.cache_data(ttl=300) # Refreshes every 5 minutes
    def load_data():
        return pd.read_csv(SHEET_URL)

    try:
        df = load_data()
        
        st.title("🏐 Volleyball Performance Dashboard")
        st.sidebar.success("✅ Connected to Google Sheets")
        
        # --- 3. DASHBOARD UI ---
        # Date Selector
        all_dates = df['Date'].unique()
        selected_date = st.sidebar.selectbox("Select Session Date", all_dates)
        day_df = df[df['Date'] == selected_date]

        # Metric Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Jumps", int(day_df['Total Jumps'].sum()))
        m2.metric("Avg Player Load", round(day_df['Total Player Load'].mean(), 1))
        m3.metric("Explosive Efforts", int(day_df['Explosive Efforts'].sum()))
        m4.metric("High Intensity Mov.", int(day_df['High Intensity Movement'].sum()))

        st.divider()

        # Chart 1: Jump Intensity
        st.subheader("Jump Intensity Profile")
        fig_jumps = px.bar(
            day_df, x="Player", 
            y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
            barmode="stack",
            color_discrete_map={
                "IMA Jump Count High Band": "#e63946", 
                "IMA Jump Count Med Band": "#f4a261", 
                "IMA Jump Count Low Band": "#a8dadc"
            }
        )
        st.plotly_chart(fig_jumps, use_container_width=True)

        # Chart 2: Load vs Efficiency
        st.subheader("Workload Analysis")
        fig_scatter = px.scatter(
            day_df, x="Explosive Efforts", y="Total Player Load",
            size="Total Jumps", color="High Intensity Movement",
            hover_name="Player", text="Player", color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
