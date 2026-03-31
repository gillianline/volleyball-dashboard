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
    
    /* Flags & Cards */
    .flag-box { padding: 12px; border-radius: 10px; text-align: center; font-weight: 800; margin-bottom: 10px; border: 2px solid #EEE; }
    .score-box { padding: 10px 20px; border-radius: 12px; font-size: 36px; font-weight: 900; color: #1D1D1F; text-align: center; border: 1px solid #E5E5E7; }
    .readiness-box { padding: 15px; border-radius: 12px; text-align: center; color: white; }
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
        lookback_df = df[(df['Name'] == p_name) & (df['Date'] >= current_date - timedelta(days=30)) & (df['Date'] <= current_date)]
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
                
                # JUMP FLAG LOGIC
                if not sync_cmj.empty:
                    v = sync_cmj.iloc[-1]
                    hist = p_cmj_history.tail(5)
                    h_avg, r_avg = hist['Jump Height (in)'].mean(), hist['RSI-modified [m/s]'].mean()
                    
                    # Flag Definitions
                    if v['Jump Height (in)'] >= h_avg and v['RSI-modified [m/s]'] >= r_avg:
                        flag, color, msg = "⚡ SUPERNOVA", "#00CC96", "Elite firing; ready for max load."
                    elif v['Jump Height (in)'] >= h_avg and v['RSI-modified [m/s]'] < r_avg:
                        flag, color, msg = "🐢 THE GRINDER", "#FF8200", "Hitting height but slow. CNS Fatigue."
                    elif v['Jump Height (in)'] < h_avg and v['RSI-modified [m/s]'] >= r_avg:
                        flag, color, msg = "📉 FADING", "#FF8200", "Springy but low output. Monitor recovery."
                    else:
                        flag, color, msg = "🚨 RED ALERT", "#FF4B4B", "Height & Pop down. High risk."
                    
                    st.markdown(f"""
                        <div class="flag-box" style="color:{color}; border-color:{color}; background-color:{color}10;">
                            <div style="font-size:16px;">{flag}</div>
                            <div style="font-size:10px; font-weight:400; color:#515154;">{msg}</div>
                        </div>
                    """, unsafe_allow_html=True)

            with c2:
                html = '<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>'
                for k in all_metrics: html += f"<tr><td>{k}</td><td>{p[k]}</td><td>{p[f'{k}_Max']}</td><td>{int(p[f'{k}_Grade'])}</td></tr>"
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

                if not p_cmj_history.empty:
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(go.Scatter(x=p_cmj_history['Test Date'], y=p_cmj_history['Jump Height (in)'], name="Height (in)", line=dict(color='#FF8200', width=3)), secondary_y=False)
                    fig.add_trace(go.Scatter(x=p_cmj_history['Test Date'], y=p_cmj_history['RSI-modified [m/s]'], name="RSI-Mod", line=dict(color='#1D1D1F', dash='dot')), secondary_y=True)
                    fig.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True)

            with c3:
                st.markdown(f'<div style="font-size:10px; font-weight:800; text-align:center;">PRACTICE SCORE</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="score-box" style="background-color:{get_gradient(p["Practice Score"])}; margin-bottom:20px;">{int(p["Practice Score"])}</div>', unsafe_allow_html=True)

                if not sync_cmj.empty:
                    latest = sync_cmj.iloc[-1]
                    baseline = p_cmj_history.tail(4)['Jump Height (in)'].mean()
                    perc_diff = ((latest['Jump Height (in)'] - baseline) / baseline) * 100
                    r_color = "#00CC96" if perc_diff > -5 else ("#FF8200" if perc_diff > -10 else "#FF4B4B")
                    st.markdown(f'<div style="font-size:10px; font-weight:800; text-align:center;">WEEKLY READINESS</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="readiness-box" style="background-color:{r_color};"><div class="readiness-val">{perc_diff:+.1f}%</div><div class="readiness-sub">vs. Recent Avg</div></div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
    
