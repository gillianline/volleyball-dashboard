import streamlit as st
import pandas as pd
import plotly.express as px

# --- SECURITY CHECK ---
def check_password():
    """Returns True if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.text_input("Enter Coach Access Key", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == "VballCoach2026"}), key="password")
        return False
    return st.session_state["password_correct"]

if not check_password():
    st.stop()  # Stop execution if password isn't correct

# --- DATA LOADING ---
# Tip: Use a 'Share with specific people' link if possible, or a password-protected OneDrive folder.
# For high sensitivity, use the 'msal' library for official Microsoft Login (OAuth).
DATA_URL = "https://liveutk-my.sharepoint.com/:x:/r/personal/asmit330_utk_edu/Documents/Volleyball/25-26%20Season/Catapult%20Dashboards/Catapult%20Dashboards.xlsx?download=1"

@st.cache_data(ttl=3600) # Refresh data every hour
def get_data():
    return pd.read_csv(DATA_URL, sep='\t')

df = get_data()

# --- THE DASHBOARD ---
st.title("🛡️ Secure Performance Portal")
player = st.selectbox("Select Player to Review", df['Player'].unique())

# Filter for the specific player's profile
p_data = df[df['Player'] == player]

# Metric Row
c1, c2, c3 = st.columns(3)
c1.metric("Total Jumps", p_data['Total Jumps'].values[0])
c2.metric("Total Load", round(p_data['Total Player Load'].values[0], 1))
c3.metric("Explosive Efforts", p_data['Explosive Efforts'].values[0])

# Intensity Breakdown
fig = px.pie(
    names=['High', 'Med', 'Low'],
    values=[p_data['IMA Jump Count High Band'].values[0], 
            p_data['IMA Jump Count Med Band'].values[0], 
            p_data['IMA Jump Count Low Band'].values[0]],
    title=f"Jump Intensity Mix: {player}",
    color_discrete_sequence=['#ef233c', '#ffb703', '#8ecae6']
)
st.plotly_chart(fig)
