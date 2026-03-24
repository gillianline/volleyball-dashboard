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
    .score-box { padding: 20px 40px; border-radius: 12px; font-size: 40px; font-weight: 800; text-align: center; }
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

# --- DATE SELECT ---
date_options = sorted(df['Date'].unique(), reverse=True)
date_a = st.selectbox("Select Practice", date_options)
day_df = df[df['Date'] == date_a].copy()

# auto previous practice
prev_dates = [d for d in date_options if d < date_a]
date_b = prev_dates[0] if prev_dates else None

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

# --- SESSION FLOW (RESTORED) ---
with t1:
    st.subheader("Drill Breakdown")
    day_phase_df = phase_df[phase_df['Date'] == date_a]
    if not day_phase_df.empty:
        phase_stats = day_phase_df.groupby('Phase')[list(grading_map.keys())].mean().reset_index()
        st.plotly_chart(px.bar(phase_stats, x="Phase", y="Total Player Load"), use_container_width=True)
        st.markdown(render_table(phase_stats, ['Phase', 'Total Player Load']), unsafe_allow_html=True)

# --- INDIVIDUAL ---
with t2:
    selected_player = st.selectbox("Select Athlete", day_df['Name'].unique())
    p_data = day_df[day_df['Name'] == selected_player].iloc[0]

    c1, c2, c3 = st.columns([1.2,2.5,1.2])

    with c1:
        st.markdown(f'<img src="{p_data["PhotoURL_Fixed"]}" class="player-photo-large">', unsafe_allow_html=True)
        st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]}</h2>', unsafe_allow_html=True)

    with c2:
        rows = []
        for k in grading_map.keys():
            rows.append({"Metric": grading_map[k], "Current": p_data[k], "Max": p_data[f'{k}_Max'], "Grade": f"{p_data[f'{k}_Grade']}%"})
        st.markdown(render_table(pd.DataFrame(rows), ["Metric","Current","Max","Grade"]), unsafe_allow_html=True)

    with c3:
        st.markdown(f'<div class="score-box" style="background-color:{get_excel_gradient(p_data["Practice Score"])};">{p_data["Practice Score"]}</div>', unsafe_allow_html=True)

    st.divider()

    # VS TYPICAL
    st.subheader("Vs Typical (Last 5)")
    hist = df[df['Name']==selected_player].sort_values('Date')
    avg = hist[list(grading_map.keys())].rolling(5).mean().iloc[-1]

    rows=[]
    for k in grading_map:
        diff=((p_data[k]-avg[k])/avg[k]*100) if avg[k]!=0 else 0
        rows.append({"Metric":grading_map[k],"Today":p_data[k],"Avg":round(avg[k],1),"% Diff":f"{'+' if diff>0 else ''}{int(diff)}%"})
    st.markdown(render_table(pd.DataFrame(rows),["Metric","Today","Avg","% Diff"]), unsafe_allow_html=True)

    # TREND
    st.subheader("Practice Score Trend")
    hist = hist.apply(process_player, axis=1)
    st.plotly_chart(px.line(hist,x="Date",y="Practice Score",markers=True), use_container_width=True)

    # STACKED LOAD
    st.subheader("Workload Breakdown")
    stack_df = pd.DataFrame({
        "Type":["Jump Load","High Intensity","Other"],
        "Value":[
            p_data["BMP Jumping Load"],
            p_data["High Intensity Movement"],
            p_data["Total Player Load"]-(p_data["BMP Jumping Load"]+p_data["High Intensity Movement"])
        ]
    })
    st.plotly_chart(px.bar(stack_df,x=["Total"]*3,y="Value",color="Type"), use_container_width=True)

    # JUMPS
    st.subheader("Jump Profile")
    jump_df=pd.DataFrame({
        "Band":["Moderate","High"],
        "Count":[p_data["IMA Jump Count Med Band"],p_data["IMA Jump Count High Band"]]
    })
    st.plotly_chart(px.bar(jump_df,x="Band",y="Count",color="Band"), use_container_width=True)

# --- TEAM GALLERY (RESTORED) ---
with t3:
    for _, r in day_df.iterrows():
        st.write(r["Name"], r["Practice Score"])

# --- TEAM COMPARISON (RESTORED AUTO) ---
with t4:
    if date_b:
        df_b = df[df['Date']==date_b]
        avg_a = day_df[list(grading_map.keys())].mean()
        avg_b = df_b[list(grading_map.keys())].mean()

        rows=[]
        for k in grading_map:
            diff=((avg_a[k]-avg_b[k])/avg_b[k]*100) if avg_b[k]!=0 else 0
            rows.append({"Metric":grading_map[k],"Today":avg_a[k],"Prev":avg_b[k],"% Diff":f"{'+' if diff>0 else ''}{int(diff)}%"})

        st.markdown(render_table(pd.DataFrame(rows),["Metric","Today","Prev","% Diff"]), unsafe_allow_html=True)
