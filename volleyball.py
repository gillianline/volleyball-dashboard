import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Vball Performance Portal", layout="wide")

# --- 1. SECURITY BARRIER ---
# This checks if the coach has entered the correct password stored in your Secrets.
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🏐 Coach Login")
        st.info("Please enter your access key to view player data.")
        pwd = st.text_input("Access Key:", type="password")
        
        if st.button("Unlock Dashboard"):
            # 'COACH_PWD' must be defined in your Streamlit Secrets
            if pwd == st.secrets["COACH_PWD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("🚫 Incorrect password. Access denied.")
        return False
    return True

if check_password():
    # --- 2. DATA CONNECTION ---
    # 'MY_ONEDRIVE_LINK' must be defined in your Streamlit Secrets
    EXCEL_URL = st.secrets["MY_ONEDRIVE_LINK"]

    @st.cache_data(ttl=600) # Auto-refresh data every 10 minutes
    def load_data():
        # Loading from Excel (.xlsx) - ensure the link ends with download=1
        return pd.read_excel(EXCEL_URL)

    try:
        df = load_data()
        
        # --- 3. DASHBOARD UI ---
        st.title("🏐 Volleyball Performance Dashboard")
        st.markdown(f"**Last Sync:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Filters
        all_dates = df['Date'].unique()
        selected_date = st.sidebar.selectbox("Select Session Date", all_dates)
        day_df = df[df['Date'] == selected_date]

        # Top Level Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Jumps", int(day_df['Total Jumps'].sum()))
        m2.metric("Avg Player Load", round(day_df['Total Player Load'].mean(), 1))
        m3.metric("Explosive Efforts", int(day_df['Explosive Efforts'].sum()))
        m4.metric("High Intensity Mov.", int(day_df['High Intensity Movement'].sum()))

        st.divider()

        # Jump Intensity Stacked Bar
        st.subheader("Jump Intensity Profile by Player")
        fig_jumps = px.bar(
            day_df, 
            x="Player", 
            y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
            labels={"value": "Jump Count", "variable": "Intensity"},
            barmode="stack",
            color_discrete_map={
                "IMA Jump Count High Band": "#e63946", # Red
                "IMA Jump Count Med Band": "#f4a261", # Orange
                "IMA Jump Count Low Band": "#a8dadc"  # Light Blue
            }
        )
        st.plotly_chart(fig_jumps, use_container_width=True)

        # Workload Comparison Scatter
        st.subheader("Load vs. Explosiveness")
        st.caption("Larger bubbles = More total jumps. Use this to find players working hard but not jumping.")
        fig_scatter = px.scatter(
            day_df, 
            x="Explosive Efforts", 
            y="Total Player Load",
            size="Total Jumps", 
            color="High Intensity Movement",
            hover_name="Player",
            text="Player",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    except Exception as e:
        st.error("Could not connect to the data source. Check your OneDrive link in Secrets.")
        st.exception(e)
