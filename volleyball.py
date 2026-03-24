import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="VB Performance Lab", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for a "Pro" Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #00d4ff; }
    label[data-testid="stMetricLabel"] { font-size: 1rem; }
    </style>
    """, unsafe_allow_state_set=True)

# --- 1. SECURITY ---
if "password_correct" not in st.session_state:
    st.title("Coach Secure Access")
    pwd = st.text_input("Access Key:", type="password")
    if st.button("Unlock"):
        if pwd == st.secrets["COACH_PWD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Denied")
    st.stop()

# --- 2. DATA ---
@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    return df

df = load_data()
all_dates = df['Date'].unique()
selected_date = st.sidebar.selectbox("Practice Date", all_dates)
day_df = df[df['Date'] == selected_date].sort_values('Total Jumps', ascending=False)

# --- 3. THE "PRACTICE AT A GLANCE" SECTION ---
st.title(f"Practice Report: {selected_date}")

# Instead of team totals, let's show the "High Load" outliers
col1, col2, col3 = st.columns(3)

with col1:
    top_jumper = day_df.iloc[0]
    st.metric("Highest Jump Volume", top_jumper['Name'], f"{int(top_jumper['Total Jumps'])} Jumps")

with col2:
    top_load = day_df.sort_values('Total Player Load', ascending=False).iloc[0]
    st.metric("Highest Workload", top_load['Name'], f"{int(top_load['Total Player Load'])} Load")

with col3:
    # Identify someone who did a lot of high-intensity movement
    top_intensity = day_df.sort_values('High Intensity Movement', ascending=False).iloc[0]
    st.metric("Intensity Leader", top_intensity['Name'], f"{int(top_intensity['High Intensity Movement'])} Efforts")

st.divider()

# --- 4. THE VISUALS ---
left_chart, right_chart = st.columns([2, 1])

with left_chart:
    st.subheader("Jump Distribution (Intensity Bands)")
    # Stacked bar but cleaner
    fig_jumps = px.bar(
        day_df, x="Name", 
        y=["IMA Jump Count Low Band", "IMA Jump Count Med Band", "IMA Jump Count High Band"],
        barmode="stack",
        color_discrete_map={
            "IMA Jump Count High Band": "#FF4B4B", # Danger/High
            "IMA Jump Count Med Band": "#FFAA00",  # Warning/Med
            "IMA Jump Count Low Band": "#00D4FF"   # Safe/Low
        },
        template="plotly_dark"
    )
    fig_jumps.update_layout(
        showlegend=True, 
        legend_title="",
        xaxis_title=None,
        yaxis_title="Total Jumps",
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_jumps, use_container_width=True)

with right_chart:
    st.subheader("Workload Balance")
    # A Radar or Scatter showing who is working hardest vs jumping most
    fig_balance = px.scatter(
        day_df, x="Total Jumps", y="Total Player Load",
        color="Explosive Efforts",
        size="High Intensity Movement",
        hover_name="Name",
        text="Name",
        template="plotly_dark"
    )
    fig_balance.update_traces(textposition='top center')
    st.plotly_chart(fig_balance, use_container_width=True)

st.divider()

# --- 5. THE DATA TABLE ---
st.subheader("Individual Practice Breakdown")
# Create a cleaner table for the coach to scroll through
display_columns = ['Name', 'Total Jumps', 'IMA Jump Count High Band', 'Total Player Load', 'Explosive Efforts', 'BMP Total Basketball Load']
st.dataframe(
    day_df[display_columns].style.background_gradient(subset=['Total Player Load', 'IMA Jump Count High Band'], cmap='Reds'),
    use_container_width=True,
    hide_index=True
)
