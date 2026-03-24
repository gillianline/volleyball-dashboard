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
    .stTable { border-radius: 10px; }
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
        else:
            st.error("Invalid Key")
    st.stop()

# --- 2. DATA LOADING & SORTING ---
@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    # Ensure Date is actually a datetime object for sorting
    df['Date'] = pd.to_datetime(df['Date'])
    return df

try:
    df = load_data()
    
    # Sort dates so the sidebar is always in order
    sorted_dates = sorted(df['Date'].unique())
    # Convert back to string for the selector display
    date_options = [d.strftime('%m/%d/%Y') for d in sorted_dates]
    
    st.sidebar.header("Session Filter")
    selected_date_str = st.sidebar.selectbox("Select Date", date_options, index=len(date_options)-1)
    
    # Filter data for the selected day
    day_df = df[df['Date'] == pd.to_datetime(selected_date_str)].sort_values('Total Jumps', ascending=False)

    # --- 3. CLEAN DASHBOARD UI ---
    st.title(f"Volleyball Session Report")
    st.caption(f"Analysis for {selected_date_str}")

    # Top Performer Row (Clean metrics)
    m1, m2, m3 = st.columns(3)
    m1.metric("Jump Leader", day_df.iloc[0]['Name'], f"{int(day_df.iloc[0]['Total Jumps'])}")
    
    highest_load = day_df.sort_values('Total Player Load', ascending=False).iloc[0]
    m2.metric("Workload Leader", highest_load['Name'], f"{int(highest_load['Total Player Load'])}")
    
    highest_int = day_df.sort_values('High Intensity Movement', ascending=False).iloc[0]
    m3.metric("Intensity Leader", highest_int['Name'], f"{int(highest_int['High Intensity Movement'])}")

    st.divider()

    # --- 4. THE JUMP GRAPH ---
    st.subheader("Jump Intensity Breakdown")
    fig_jumps = px.bar(
        day_df, x="Name", 
        y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
        barmode="stack",
        color_discrete_map={
            "IMA Jump Count High Band": "#FF3B30", # Clean Apple Red
            "IMA Jump Count Med Band": "#FF9500", # Clean Apple Orange
            "IMA Jump Count Low Band": "#007AFF"  # Clean Apple Blue
        },
        template="plotly_white"
    )
    fig_jumps.update_layout(
        xaxis_title=None, 
        yaxis_title="Jumps",
        legend_title=None,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig_jumps, use_container_width=True)

    # --- 5. SIMPLE DATA TABLE ---
    st.subheader("Individual Performance Data")
    # Using a simple dataframe to avoid the matplotlib gradient error
    cols = ['Name', 'Total Jumps', 'IMA Jump Count High Band', 'Total Player Load', 'Explosive Efforts']
    st.dataframe(day_df[cols], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Issue connecting to data: {e}")
