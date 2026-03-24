import streamlit as st
import pandas as pd
import plotly.express as px

# 1. SECURITY BARRIER
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🏐 Coach Login")
        pwd = st.text_input("Enter Access Key:", type="password")
        if st.button("Unlock Dashboard"):
            if pwd == "Vball2026!": # SET YOUR PASSWORD HERE
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return True

if check_password():
    # 2. DATA CONNECTION
    # Replace the link below with your OneDrive Direct Download link from Phase 1
    EXCEL_URL = "https://liveutk-my.sharepoint.com/:x:/r/personal/asmit330_utk_edu/Documents/Volleyball/25-26%20Season/Catapult%20Dashboards/Catapult%20Dashboards.xlsx?download=1"

    @st.cache_data(ttl=600) # Refresh data every 10 mins
    def load_data():
        return pd.read_excel(EXCEL_URL)

    try:
        df = load_data()
        
        # 3. DASHBOARD LAYOUT
        st.title("🏐 Performance Dashboard")
        
        # Slicers
        date = st.selectbox("Select Date", df['Date'].unique())
        day_df = df[df['Date'] == date]

        # Metric Row
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Jumps", int(day_df['Total Jumps'].sum()))
        c2.metric("Avg Player Load", round(day_df['Total Player Load'].mean(), 1))
        c3.metric("High Intensity Effs", day_df['High Intensity Movement'].sum())

        # Jump Intensity Chart
        st.subheader("Jump Intensity by Player")
        fig = px.bar(day_df, x="Player", 
                     y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
                     title="Jump Distribution", barmode="stack",
                     color_discrete_map={"IMA Jump Count High Band": "red", "IMA Jump Count Med Band": "orange", "IMA Jump Count Low Band": "lightblue"})
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")
