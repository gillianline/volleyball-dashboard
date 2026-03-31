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
    
    /* Table & Gallery Styles */
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; margin-bottom: 10px; }
    .scout-table th { background-color: #F5F5F7; padding: 4px; border-bottom: 2px solid #E5E5E7; font-weight: 700; font-size: 10px; text-transform: uppercase; }
    .scout-table td { padding: 4px; border-bottom: 1px solid #F5F5F7; font-size: 11px; }
    
    .gallery-card { 
        border: 1px solid #E5E5E7; 
        padding: 15px; 
        border-radius: 15px; 
        background-color: #FFFFFF; 
        margin-bottom: 20px;
    }
    .player-photo-small { border-radius: 50%; width: 80px; height: 80px; object-fit: cover; border: 3px solid #FF8200; }
    .player-photo-large { border-radius: 50%; width: 180px; height: 180px; object-fit: cover; border: 6px solid #FF8200; }
    
    /* Headers & KPIs */
    .section-header { font-size: 13px; font-weight: 800; color: #FF8200; border-bottom: 2px solid #FF8200; margin-top: 20px; margin-bottom: 10px; padding-bottom: 3px; text-transform: uppercase; }
    .kpi-box { padding: 10px; border-radius: 12px; text-align: center; font-weight: 800; border: 1px solid #EEE; background-color: #FAFAFA; }
    .status-tag { font-size: 14px; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

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
    c_sel, c_pos = st.columns(2)
    with c_sel: selected_session = st.selectbox("Select Session", session_options)
    with c_pos: pos_filter = st.selectbox("Filter Position", ["All Positions"] + sorted(list(df['Position'].unique())))

    day_df = df[df['Activity'] == selected_session].copy()
    if pos_filter != "All Positions": day_df = day_df[day_df['Position'] == pos_filter]

    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']

    def get_gradient(score):
        score = max(0, min(100, float(score)))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        lookback = df[(df['Name'] == p_name) & (df['Date'] >= row['Date'] - timedelta(days=30)) & (df['Date'] <= row['Date'])]
        rolling_maxes = lookback[all_metrics].max()
        grades = [math.ceil((row[k] / rolling_maxes[k]) * 100) if rolling_maxes[k] > 0 else 0 for k in all_metrics]
        row['Practice Score'] = math.ceil(sum(grades)/len(grades)) if grades else 0
        for i, k in enumerate(all_metrics): row[f'{k}_Grade'] = grades[i]
        return row

    if not day_df.empty:
        day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    tab1, tab2 = st.tabs(["Individual Profile", "Team Scorecard Gallery"])

    with tab1:
        if not day_df.empty:
            sel_p = st.selectbox("Athlete", day_df['Name'].unique())
            p = day_df[day_df['Name'] == sel_p].iloc[0]
            p_cmj = cmj_df[cmj_df['Athlete'] == sel_p].sort_values('Test Date')
            sync_cmj = p_cmj[(p_cmj['Test Date'] <= p['Date']) & (p_cmj['Test Date'] > p['Date'] - timedelta(days=7))]

            c_photo, c_data = st.columns([1, 4])
            with c_photo:
                st.markdown(f'<center><img src="{p["PhotoURL"]}" class="player-photo-large"><br><h3>{p["Name"]}</h3><p style="color:#FF8200;">{p["Position"]}</p></center>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi-box" style="background-color:{get_gradient(p["Practice Score"])}; font-size:36px; margin-top:20px;">{int(p["Practice Score"])}<br><small style="font-size:10px;">Practice Grade</small></div>', unsafe_allow_html=True)

            with c_data:
                # GPS SECTION
                st.markdown('<div class="section-header">Daily GPS Workload</div>', unsafe_allow_html=True)
                tbl = '<table class="scout-table"><tr><th>Metric</th>' + "".join([f"<th>{k}</th>" for k in all_metrics]) + '</tr><tr><td><b>Today</b></td>' + "".join([f"<td>{p[k]}</td>" for k in all_metrics]) + '</tr><tr><td><b>Grade</b></td>' + "".join([f"<td>{int(p[f'{k}_Grade'])}</td>" for k in all_metrics]) + '</tr></table>'
                st.markdown(tbl, unsafe_allow_html=True)

                # JUMP SECTION (BELOW)
                st.markdown('<div class="section-header">Neuromuscular Readiness & Jump History</div>', unsafe_allow_html=True)
                jc1, jc2 = st.columns([1, 2])
                with jc1:
                    if not sync_cmj.empty:
                        latest = sync_cmj.iloc[-1]
                        baseline = p_cmj.tail(4)['Jump Height (in)'].mean()
                        perc = ((latest['Jump Height (in)'] - baseline) / baseline) * 100
                        color = "#00CC96" if perc > -5 else ("#FF8200" if perc > -10 else "#FF4B4B")
                        st.markdown(f'<div class="kpi-box" style="border-color:{color}; color:{color};"><div class="status-tag">{perc:+.1f}% vs Avg</div><small style="color:gray;">{latest["Jump Height (in)"]:.1f}" Jump ({latest["Test Date"].strftime("%m/%d")})</small></div>', unsafe_allow_html=True)
                    else: st.info("No VALD test this week.")
                with jc2:
                    if not p_cmj.empty:
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        fig.add_trace(go.Scatter(x=p_cmj['Test Date'], y=p_cmj['Jump Height (in)'], name="Height", line=dict(color='#FF8200', width=3)), secondary_y=False)
                        fig.add_trace(go.Scatter(x=p_cmj['Test Date'], y=p_cmj['RSI-modified [m/s]'], name="RSI", line=dict(dash='dot', color='black')), secondary_y=True)
                        fig.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if not day_df.empty:
            for _, row in day_df.iterrows():
                # Get the full metric row for the gallery card
                metrics_row_html = "".join([f"<td>{row[k]}<br><small style='color:gray;'>{int(row[f'{k}_Grade'])}</small></td>" for k in all_metrics])
                st.markdown(f"""
                <div class="gallery-card">
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <img src="{row['PhotoURL']}" class="player-photo-small">
                        <div style="flex: 1;">
                            <h4 style="margin:0;">{row['Name']}</h4>
                            <p style="margin:0; color:#FF8200; font-size:12px; font-weight:700;">{row['Position']}</p>
                        </div>
                        <div style="flex: 4;">
                            <table class="scout-table" style="margin:0;">
                                <thead><tr>{"".join([f"<th>{k[:6]}..</th>" for k in all_metrics])}</tr></thead>
                                <tbody><tr>{metrics_row_html}</tr></tbody>
                            </table>
                        </div>
                        <div style="background-color:{get_gradient(row['Practice Score'])}; padding:15px; border-radius:12px; font-size:28px; font-weight:900; width:80px; text-align:center;">
                            {int(row['Practice Score'])}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
