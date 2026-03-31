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
    
    /* Global Elements */
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; margin-bottom: 15px; }
    .scout-table th { background-color: #F5F5F7; padding: 6px; border-bottom: 2px solid #E5E5E7; font-weight: 700; font-size: 11px; }
    .scout-table td { padding: 6px; border-bottom: 1px solid #F5F5F7; font-size: 11px; }
    .player-photo-large { border-radius: 50%; width: 180px; height: 180px; object-fit: cover; border: 6px solid #FF8200; }
    
    /* Section Headers */
    .section-header { font-size: 14px; font-weight: 800; color: #FF8200; border-bottom: 2px solid #FF8200; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    
    /* KPI Components */
    .kpi-label { font-size: 10px; font-weight: 800; text-transform: uppercase; color: #515154; text-align: center; margin-bottom: 4px; }
    .kpi-box { padding: 15px; border-radius: 12px; text-align: center; font-weight: 800; border: 1px solid #EEE; background-color: #FAFAFA; }
    .status-tag { font-size: 16px; font-weight: 900; margin-bottom: 5px; }
    .status-desc { font-size: 10px; font-weight: 400; color: #515154; line-height: 1.3; }
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
            
            # --- LAYOUT ZONE ---
            col_id, col_gps, col_jump = st.columns([1, 2.2, 1.8])
            
            # 1. IDENTITY ZONE
            with col_id:
                st.markdown(f'<div style="text-align:center;"><img src="{p["PhotoURL"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
                st.markdown(f'<h3 style="text-align:center; margin-top:10px;">{p["Name"]}</h3>', unsafe_allow_html=True)
                st.markdown(f'<p style="text-align:center; color:#FF8200; font-weight:700;">{p["Position"]}</p>', unsafe_allow_html=True)

            # 2. GPS ZONE (Catapult Data)
            with col_gps:
                st.markdown('<div class="section-header">Daily GPS Workload</div>', unsafe_allow_html=True)
                
                gps_c1, gps_c2 = st.columns([2.5, 1])
                with gps_c1:
                    html = '<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>Grade</th></tr></thead><tbody>'
                    for k in all_metrics:
                        html += f"<tr><td>{k}</td><td>{p[k]}</td><td>{int(p[f'{k}_Grade'])}</td></tr>"
                    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
                
                with gps_c2:
                    st.markdown(f'<p class="kpi-label">Session Grade</p>', unsafe_allow_html=True)
                    st.markdown(f'<div class="kpi-box" style="background-color:{get_gradient(p["Practice Score"])}; font-size:36px; height:120px; display:flex; align-items:center; justify-content:center;">{int(p["Practice Score"])}</div>', unsafe_allow_html=True)

            # 3. JUMP ZONE (VALD Data)
            with col_jump:
                st.markdown('<div class="section-header">Weekly Jump Readiness</div>', unsafe_allow_html=True)
                
                if not p_cmj_history.empty:
                    # Readiness Profile
                    if not sync_cmj.empty:
                        latest = sync_cmj.iloc[-1]
                        baseline = p_cmj_history.tail(4)['Jump Height (in)'].mean()
                        rsi_baseline = p_cmj_history.tail(4)['RSI-modified [m/s]'].mean()
                        
                        perc_diff = ((latest['Jump Height (in)'] - baseline) / baseline) * 100
                        
                        # Profiling Logic
                        if latest['Jump Height (in)'] >= baseline and latest['RSI-modified [m/s]'] >= rsi_baseline:
                            status, s_color, desc = "ELASTIC ⚡", "#00CC96", "System fresh and reactive."
                        elif latest['Jump Height (in)'] >= baseline and latest['RSI-modified [m/s]'] < rsi_baseline:
                            status, s_color, desc = "POWERED 🏋️", "#FF8200", "High output, slow speed (CNS Fatigue)."
                        elif latest['Jump Height (in)'] < baseline and latest['RSI-modified [m/s]'] >= rsi_baseline:
                            status, s_color, desc = "SPRINGY 📉", "#FF8200", "Fast but low height. Monitor load."
                        else:
                            status, s_color, desc = "FATIGUED 🚨", "#FF4B4B", "Height & Efficiency down."

                        st.markdown(f"""
                            <div class="kpi-box" style="background-color:{s_color}15; border-color:{s_color}; margin-bottom:15px;">
                                <div class="status-tag" style="color:{s_color};">{status}</div>
                                <div style="font-size:20px; font-weight:900;">{perc_diff:+.1f}% vs Avg</div>
                                <div class="status-desc">{desc}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    # Graph
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(go.Scatter(x=p_cmj_history['Test Date'], y=p_cmj_history['Jump Height (in)'], name="Height", line=dict(color='#FF8200', width=3)), secondary_y=False)
                    fig.add_trace(go.Scatter(x=p_cmj_history['Test Date'], y=p_cmj_history['RSI-modified [m/s]'], name="RSI", line=dict(color='#1D1D1F', dash='dot')), secondary_y=True)
                    fig.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_title=None)
                    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
