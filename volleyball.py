import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# --- CSS: TENNESSEE STYLE ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    .block-container { padding-top: 1.5rem !important; }
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #F5F5F7; padding: 4px; border-bottom: 2px solid #E5E5E7; font-weight: 700; font-size: 11px; }
    .scout-table td { padding: 4px; border-bottom: 1px solid #F5F5F7; font-size: 11px; }
    .player-photo-large { border-radius: 50%; width: 200px; height: 200px; object-fit: cover; border: 6px solid #FF8200; }
    .score-label { font-size: 10px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; color: #515154; text-align: center; }
    .score-box { padding: 10px 20px; border-radius: 12px; font-size: 32px; font-weight: 800; min-width: 100px; color: #1D1D1F; text-align: center; }
    
    .readiness-box { padding: 15px; border-radius: 12px; text-align: center; color: white; margin-bottom: 10px; }
    .readiness-val { font-size: 28px; font-weight: 900; }
    .readiness-sub { font-size: 10px; font-weight: 700; opacity: 0.9; }
    
    .jump-info-box { border: 1px solid #EEE; padding: 10px; border-radius: 8px; background-color: #FAFAFA; }
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

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
    cmj_df.columns = cmj_df.columns.str.strip()
    
    # Conversion: cm to in
    cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
    
    rename_map = {
        'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps',
        'IMA Jump Count High Band': 'High Jumps', 'BMP Jumping Load': 'Jump Load',
        'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance',
        'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movements'
    }
    df = df.rename(columns=rename_map)
    df['Date'] = pd.to_datetime(df['Date'])
    
    metric_cols = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    df[metric_cols] = df[metric_cols].apply(pd.to_numeric, errors='coerce').fillna(0).round(1)
    
    if 'Activity' not in df.columns:
        df['Activity'] = df['Date'].dt.strftime('%m/%d/%Y')
    else:
        df['Activity'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))

    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'])
    
    return df, cmj_df

try:
    df, cmj_df = load_all_data()
    session_map = df[['Date', 'Activity']].drop_duplicates().sort_values('Date', ascending=False)
    session_options = session_map['Activity'].tolist()

    st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>Performance Lab</h3>", unsafe_allow_html=True)
    c_main, c_pos = st.columns([2, 2])
    with c_main:
        selected_session = st.selectbox("Select Session", session_options, index=0)
    with c_pos:
        pos_list = sorted([p for p in df['Position'].unique() if p != "N/A"])
        pos_filter = st.selectbox("Position Filter", ["All Positions"] + pos_list)

    day_df = df[df['Activity'] == selected_session].copy()
    current_practice_date = day_df['Date'].iloc[0]
    
    if pos_filter != "All Positions":
        day_df = day_df[day_df['Position'] == pos_filter]

    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    overall_maxes = df.groupby('Name')[all_metrics].max().round(1)

    def get_gradient(score):
        score = max(0, min(100, float(score)))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        current_date = row['Date']
        start_date = current_date - timedelta(days=30)
        lookback_df = df[(df['Name'] == p_name) & (df['Date'] >= start_date) & (df['Date'] <= current_date)]
        rolling_maxes = lookback_df[all_metrics].max().round(1)
        grades = [math.ceil((float(row[k]) / float(rolling_maxes[k])) * 100) if float(rolling_maxes[k]) > 0 else 0 for k in all_metrics]
        row['Practice Score'] = math.ceil(sum(grades) / len(grades)) if grades else 0
        for i, k in enumerate(all_metrics): row[f'{k}_Max'] = rolling_maxes[k]; row[f'{k}_Grade'] = grades[i]
        return row

    if not day_df.empty:
        day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    t_player, t_gallery = st.tabs(["Individual Profile", "Team Gallery"])

    with t_player:
        if not day_df.empty:
            sel_p = st.selectbox("Select Athlete", day_df['Name'].unique())
            p = day_df[day_df['Name'] == sel_p].iloc[0]
            p_cmj_history = cmj_df[cmj_df['Athlete'] == sel_p].sort_values('Test Date', ascending=True)
            sync_cmj = p_cmj_history[(p_cmj_history['Test Date'] <= current_practice_date) & 
                                     (p_cmj_history['Test Date'] > current_practice_date - timedelta(days=7))]
            
            c1, c2, c3 = st.columns([1, 2.5, 1])
            with c1:
                st.markdown(f'<div style="text-align:center;"><img src="{p["PhotoURL"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
                st.markdown(f'<h3 style="text-align:center; margin-top:10px;">{p["Name"]}</h3>', unsafe_allow_html=True)
                st.markdown(f'<p style="text-align:center; color:#FF8200; font-weight:700;">{p["Position"]}</p>', unsafe_allow_html=True)

            with c2:
                # 1. CATAPULT DATA TABLE
                html = '<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>'
                for k in all_metrics:
                    html += f"<tr><td>{k}</td><td>{p[k]}</td><td>{p[f'{k}_Max']}</td><td>{int(p[f'{k}_Grade'])}</td></tr>"
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

                # 2. DUAL AXIS GRAPH: Height and RSI-Mod
                if not p_cmj_history.empty:
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(go.Scatter(x=p_cmj_history['Test Date'], y=p_cmj_history['Jump Height (in)'], 
                                             name="Height (in)", line=dict(color='#FF8200', width=3), marker=dict(size=8)), secondary_y=False)
                    fig.add_trace(go.Scatter(x=p_cmj_history['Test Date'], y=p_cmj_history['RSI-modified [m/s]'], 
                                             name="RSI-Mod", line=dict(color='#1D1D1F', dash='dot'), marker=dict(size=8)), secondary_y=True)
                    
                    fig.update_layout(title="Neuromuscular Profile (Season History)", height=280, margin=dict(l=0, r=0, t=50, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    fig.update_yaxes(title_text="Height (in)", secondary_y=False)
                    fig.update_yaxes(title_text="RSI-Modified", secondary_y=True)
                    st.plotly_chart(fig, use_container_width=True)

            with c3:
                # 3. PRACTICE SCORE (Now at Top Right)
                st.markdown(f'<p class="score-label">PRACTICE SCORE</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="score-box" style="background-color:{get_gradient(p["Practice Score"])}; margin-bottom:40px;">{int(p["Practice Score"])}</div>', unsafe_allow_html=True)

                # 4. WEEKLY READINESS (Now Below Score)
                if not sync_cmj.empty:
                    latest = sync_cmj.iloc[-1]
                    past_tests = p_cmj_history[p_cmj_history['Test Date'] <= latest['Test Date']]
                    baseline = past_tests.tail(min(len(past_tests), 4))['Jump Height (in)'].mean()
                    perc_diff = ((latest['Jump Height (in)'] - baseline) / baseline) * 100
                    color = "#00CC96" if perc_diff > -5 else ("#FF8200" if perc_diff > -10 else "#FF4B4B")
                    
                    st.markdown(f'<p class="score-label">WEEKLY READINESS</p>', unsafe_allow_html=True)
                    st.markdown(f'<div class="readiness-box" style="background-color:{color};"><div class="readiness-val">{perc_diff:+.1f}%</div><div class="readiness-sub">vs. Recent Avg</div></div>', unsafe_allow_html=True)
                    
                    # Small Diagnostic Stats
                    st.markdown(f"""
                        <div class="jump-info-box">
                            <p style="margin:0; font-size:12px;"><b>Jump:</b> {latest['Jump Height (in)']:.1f}"</p>
                            <p style="margin:0; font-size:12px;"><b>RSI:</b> {latest['RSI-modified [m/s]']:.2f}</p>
                            <p style="margin:0; font-size:12px;"><b>Power:</b> {latest['Peak Power [W]']:.0f}W</p>
                            <p style="margin:0; font-size:9px; color:gray; margin-top:4px;">Tested: {latest['Test Date'].strftime('%m/%d')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No VALD test found for this week.")

except Exception as e:
    st.error(f"Sync Error: {e}")
