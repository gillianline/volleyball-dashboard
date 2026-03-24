import streamlit as st
import pandas as pd
import plotly.express as px
import math 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; margin-top: 5px; }
    .scout-table th { background-color: #F5F5F7; padding: 10px; border-bottom: 2px solid #E5E5E7; font-weight: 700; }
    .scout-table td { padding: 8px; border-bottom: 1px solid #F5F5F7; }

    .player-photo-large { border-radius: 50%; width: 240px; height: 240px; object-fit: cover; border: 6px solid #FF8200; }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 4px solid #FF8200; }
    .score-box { padding: 20px 40px; border-radius: 12px; font-size: 40px; font-weight: 800; text-align: center; color: #1D1D1F; }
    .gallery-card { border: 1px solid #E5E5E7; padding: 20px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 10px; }
    
    .trend-up { color: #28a745; font-weight: bold; }
    .trend-down { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SECURITY ---
if "password_correct" not in st.session_state:
    st.title("Access Restricted")
    pwd = st.text_input("Access Key:", type="password")
    if st.button("Unlock"):
        if pwd == st.secrets["COACH_PWD"]:
            st.session_state["password_correct"] = True
            st.rerun()
    st.stop()

# --- DATA ---
@st.cache_data(ttl=300)
def load_all_data():
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'])
    
    p_df = pd.read_csv(st.secrets["PHASE_SHEET_URL"])
    p_df.columns = p_df.columns.str.strip()
    p_df['Date'] = pd.to_datetime(p_df['Date'])
    return df, p_df

df, phase_df = load_all_data()

date_options = [d.strftime('%m/%d/%Y') for d in sorted(df['Date'].unique(), reverse=True)]

# --- DATE SELECT ---
st.markdown("<h3 style='text-align: center;'>Practice Selection</h3>", unsafe_allow_html=True)
c_d1, c_d2 = st.columns(2)
with c_d1: date_a_str = st.selectbox("Current Practice", date_options, index=0)
with c_d2: date_b_str = st.selectbox("Comparison Practice (Optional)", ["None"] + date_options, index=0)

date_a = pd.to_datetime(date_a_str)
day_df = df[df['Date'] == date_a].copy()

# --- LOGIC ---
grading_map = {
    'Total Jumps': 'Total Jumps', 
    'IMA Jump Count Med Band': 'Moderate Jumps', 
    'IMA Jump Count High Band': 'High Jumps', 
    'BMP Jumping Load': 'Jump Load', 
    'Total Player Load': 'Player Load', 
    'Estimated Distance (y)': 'Estimated Distance', 
    'Explosive Efforts': 'Explosive Efforts', 
    'High Intensity Movement': 'High Intensity Movement'
}

overall_maxes = df.groupby('Name')[list(grading_map.keys())].max()
photo_map = df.dropna(subset=['PhotoURL']).drop_duplicates('Name').set_index('Name')['PhotoURL'].to_dict()

def get_excel_gradient(score):
    score = max(0, min(100, score))
    r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
    return f"rgb({r}, {g}, 0)"

def process_player(row):
    p_name = row['Name']
    p_maxes = overall_maxes.loc[p_name]
    grades = [math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0 for k in grading_map.keys()]
    row['Practice Score'] = math.ceil(sum(grades) / len(grades))
    for k in grading_map.keys():
        row[f'{k}_Max'] = p_maxes[k]
        row[f'{k}_Grade'] = math.ceil((row[k] / p_maxes[k]) * 100) if p_maxes[k] > 0 else 0
    row['PhotoURL_Fixed'] = photo_map.get(p_name, "https://www.w3schools.com/howto/img_avatar.png")
    return row

day_df = day_df.apply(process_player, axis=1)

def render_table(dataframe, cols):
    html = '<table class="scout-table"><thead><tr>'
    for c in cols: html += f'<th>{c}</th>'
    html += '</tr></thead><tbody>'
    for _, r in dataframe.iterrows():
        html += '<tr>'
        for c in cols:
            val = r[c]
            style = ""
            if c == "% Diff" and isinstance(val, str):
                num = int(val.replace('%',''))
                if num > 10:
                    style = 'class="trend-up"'
                elif num < -10:
                    style = 'class="trend-down"'
            html += f'<td {style}>{val}</td>'
        html += '</tr>'
    return html + '</tbody></table>'

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["Session Flow", "Individual Profile", "Team Gallery", "Team Comparison"])

# --- INDIVIDUAL PROFILE ---
with t2:
    selected_player = st.selectbox("Select Athlete", day_df['Name'].unique())
    p_data = day_df[day_df['Name'] == selected_player].iloc[0]

    c1, c2, c3 = st.columns([1.2, 2.5, 1.2])

    with c1:
        st.markdown(f'<img src="{p_data["PhotoURL_Fixed"]}" class="player-photo-large">', unsafe_allow_html=True)
        st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]}</h2>', unsafe_allow_html=True)

    with c2:
        rows = []
        for k in grading_map.keys():
            rows.append({
                "Metric": grading_map[k],
                "Current": p_data[k],
                "Max": p_data[f'{k}_Max'],
                "Grade": f"{p_data[f'{k}_Grade']}%"
            })
        st.markdown(render_table(pd.DataFrame(rows), ["Metric", "Current", "Max", "Grade"]), unsafe_allow_html=True)

    with c3:
        st.markdown(f'<div class="score-box" style="background-color:{get_excel_gradient(p_data["Practice Score"])};">{p_data["Practice Score"]}</div>', unsafe_allow_html=True)

    st.divider()

    # --- NEW: VS TYPICAL ---
    st.subheader("Vs Typical Load (Last 5)")
    player_history = df[df['Name'] == selected_player].sort_values('Date')

    rolling = player_history[list(grading_map.keys())].rolling(5).mean()
    latest_avg = rolling.iloc[-1]

    trend_rows = []
    for k in grading_map.keys():
        current = p_data[k]
        avg = latest_avg[k] if not pd.isna(latest_avg[k]) else current
        diff = ((current - avg) / avg * 100) if avg != 0 else 0

        trend_rows.append({
            "Metric": grading_map[k],
            "Today": current,
            "5-Day Avg": round(avg, 1),
            "% Diff": f"{'+' if diff > 0 else ''}{int(round(diff,0))}%"
        })

    st.markdown(render_table(pd.DataFrame(trend_rows), ["Metric", "Today", "5-Day Avg", "% Diff"]), unsafe_allow_html=True)

    # --- NEW: SCORE TREND ---
    st.subheader("Practice Score Trend")
    player_history = player_history.apply(process_player, axis=1)

    fig = px.line(player_history, x="Date", y="Practice Score", markers=True, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # --- NEW: LOAD DISTRIBUTION ---
    st.subheader("Load Distribution")

    workload_df = pd.DataFrame({
        "Metric": ["Jump Load", "Player Load", "High Intensity Movement"],
        "Value": [
            p_data["BMP Jumping Load"],
            p_data["Total Player Load"],
            p_data["High Intensity Movement"]
        ]
    })

    st.plotly_chart(px.pie(workload_df, names="Metric", values="Value", hole=0.4), use_container_width=True)
