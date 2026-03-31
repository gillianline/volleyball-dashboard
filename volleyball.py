import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Performance Lab", layout="wide")

# --- CSS: ORIGINAL TENNESSEE STYLE ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    hr { display: none !important; }
    .block-container { padding-top: 1.5rem !important; }

    /* Table Styles */
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #F5F5F7; padding: 4px; border-bottom: 2px solid #E5E5E7; font-weight: 700; font-size: 11px; }
    .scout-table td { padding: 4px; border-bottom: 1px solid #F5F5F7; font-size: 11px; }
    
    /* Profile Photo */
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    
    /* Score Boxes */
    .score-container { display: flex; justify-content: center; gap: 15px; margin-top: 10px; }
    .score-wrapper { text-align: center; }
    .score-label { font-size: 10px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; color: #515154; }
    .score-box { padding: 10px 20px; border-radius: 12px; font-size: 32px; font-weight: 800; min-width: 100px; color: #1D1D1F; }
    
    /* Gallery Card */
    .gallery-card { 
        border: 1px solid #E5E5E7; 
        padding: 15px; 
        border-radius: 15px; 
        background-color: #FFFFFF; 
        margin-bottom: 12px; 
        min-height: 320px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 5px solid #FF8200; }
    
    /* Section Headers */
    .section-header { font-size: 14px; font-weight: 800; color: #FF8200; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
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
    
    if 'Activity' in df.columns:
        df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
    else:
        df['Session_Name'] = df['Date'].dt.strftime('%m/%d/%Y')

    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'])
    
    return df, cmj_df

try:
    df, cmj_df = load_all_data()
    session_map = df[['Date', 'Session_Name']].drop_duplicates().sort_values('Date', ascending=False)
    session_options = session_map['Session_Name'].tolist()

    st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>Performance Lab</h3>", unsafe_allow_html=True)
    c_main, c_pos = st.columns([2, 2])
    with c_main:
        selected_session = st.selectbox("Select Session", session_options, index=0)
    with c_pos:
        pos_list = sorted([p for p in df['Position'].unique() if p != "N/A"])
        pos_filter = st.selectbox("Position Filter", ["All Positions"] + pos_list)

    day_df = df[df['Session_Name'] == selected_session].copy()
    current_practice_date = day_df['Date'].iloc[0]
    if pos_filter != "All Positions": day_df = day_df[day_df['Position'] == pos_filter]

    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']

    def get_gradient(score):
        score = max(0, min(100, float(score)))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        lookback_df = df[(df['Name'] == p_name) & (df['Date'] >= row['Date'] - timedelta(days=30)) & (df['Date'] <= row['Date'])]
        rolling_maxes = lookback_df[all_metrics].max().round(1)
        grades = [math.ceil((float(row[k]) / float(rolling_maxes[k])) * 100) if float(rolling_maxes[k]) > 0 else 0 for k in all_metrics]
        row['Practice Score'] = math.ceil(sum(grades) / len(grades)) if grades else 0
        for i, k in enumerate(all_metrics): row[f'{k}_Grade'] = grades[i]; row[f'{k}_Max'] = rolling_maxes[k]
        return row

    if not day_df.empty:
        day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    t_player, t_gallery = st.tabs(["Individual Profile", "Team Gallery"])

    with t_player:
        if not day_df.empty:
            sel_p = st.selectbox("Select Athlete", day_df['Name'].unique())
            p = day_df[day_df['Name'] == sel_p].iloc[0]
            p_cmj_history = cmj_df[cmj_df['Athlete'] == sel_p].sort_values('Test Date')
            sync_cmj = p_cmj_history[(p_cmj_history['Test Date'] <= current_practice_date) & (p_cmj_history['Test Date'] > current_practice_date - timedelta(days=7))]

            # TOP ROW: ORIGINAL GPS LAYOUT
            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1:
                st.markdown(f'<div style="text-align:center;"><img src="{p["PhotoURL"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
                st.markdown(f'<h2 style="text-align:center; margin-top:10px;">{p["Name"]}</h2>', unsafe_allow_html=True)
            with c2:
                html = '<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>30d Max</th><th>Grade</th></tr></thead><tbody>'
                for k in all_metrics:
                    html += f"<tr><td>{k}</td><td>{p[k]}</td><td>{p[f'{k}_Max']}</td><td>{int(p[f'{k}_Grade'])}</td></tr>"
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="score-wrapper">
                    <div class="score-label">Practice Score</div>
                    <div class="score-box" style="background-color:{get_gradient(p['Practice Score'])};">{int(p['Practice Score'])}</div>
                </div>
                """, unsafe_allow_html=True)

            # BOTTOM ROW: JUMP DATA (MOVED BELOW)
            st.markdown('<div class="section-header">Weekly Jump Readiness & History</div>', unsafe_allow_html=True)
            jc1, jc2 = st.columns([1.5, 3.5])
            with jc1:
                if not sync_cmj.empty:
                    latest = sync_cmj.iloc[-1]
                    baseline = p_cmj_history.tail(4)['Jump Height (in)'].mean()
                    perc_diff = ((latest['Jump Height (in)'] - baseline) / baseline) * 100
                    color = "#00CC96" if perc_diff > -5 else ("#FF8200" if perc_diff > -10 else "#FF4B4B")
                    st.markdown(f"""
                        <div class="score-wrapper">
                            <div class="score-label">Weekly Readiness</div>
                            <div class="score-box" style="background-color:{color}; color:white;">{perc_diff:+.1f}%</div>
                            <p style="font-size:11px; margin-top:10px;">Height: <b>{latest['Jump Height (in)']:.1f}"</b> | RSI: <b>{latest['RSI-modified [m/s]']:.2f}</b></p>
                        </div>
                    """, unsafe_allow_html=True)
            with jc2:
                if not p_cmj_history.empty:
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(go.Scatter(x=p_cmj_history['Test Date'], y=p_cmj_history['Jump Height (in)'], name="Height", line=dict(color='#FF8200', width=3)), secondary_y=False)
                    fig.add_trace(go.Scatter(x=p_cmj_history['Test Date'], y=p_cmj_history['RSI-modified [m/s]'], name="RSI", line=dict(color='#1D1D1F', dash='dot')), secondary_y=True)
                    fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True)

    with t_gallery:
        if not day_df.empty:
            for i in range(0, len(day_df), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(day_df):
                        p_d = day_df.iloc[i + j]
                        rows_html = "".join([f"<tr><td>{k}</td><td>{p_d[k]}</td><td>{int(p_d[f'{k}_Grade'])}</td></tr>" for k in all_metrics])
                        with cols[j]:
                            st.markdown(f"""
                            <div class="gallery-card">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <div style="flex: 1.2; text-align: center;">
                                        <img src="{p_d['PhotoURL']}" class="gallery-photo">
                                        <p style="font-weight:bold; font-size:15px; margin-top:8px;">{p_d['Name']}</p>
                                    </div>
                                    <div style="flex: 2.5;"><table class="scout-table"><thead><tr><th>Metric</th><th>Val</th><th>Grade</th></tr></thead><tbody>{rows_html}</tbody></table></div>
                                    <div style="flex: 1; text-align: center;">
                                        <div class="score-label" style="font-size:9px;">Practice</div>
                                        <div style="background-color:{get_gradient(p_d['Practice Score'])}; padding:10px; border-radius:12px; font-size:32px; font-weight:900;">{int(p_d['Practice Score'])}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Sync Error: {e}")
