import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math 

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
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    .score-wrapper { text-align: center; }
    .score-label { font-size: 10px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; color: #515154; }
    .score-box { padding: 10px 20px; border-radius: 12px; font-size: 32px; font-weight: 800; min-width: 100px; color: #1D1D1F; }
    .gallery-card { border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; min-height: 320px; display: flex; flex-direction: column; justify-content: center; }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 5px solid #FF8200; }
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
    
    rename_map = {
        'Total Jumps': 'Total Jumps',
        'IMA Jump Count Med Band': 'Moderate Jumps',
        'IMA Jump Count High Band': 'High Jumps',
        'BMP Jumping Load': 'Jump Load',
        'Total Player Load': 'Player Load',
        'Estimated Distance (y)': 'Estimated Distance',
        'Explosive Efforts': 'Explosive Efforts',
        'High Intensity Movement': 'High Intensity Movements'
    }
    df = df.rename(columns=rename_map)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 1. CLEANING: Match Excel rounding (1 decimal place)
    metric_cols = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    df[metric_cols] = df[metric_cols].apply(pd.to_numeric, errors='coerce').fillna(0).round(1)
    
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'])
    
    return df, cmj_df

try:
    df, cmj_df = load_all_data()
    date_options = [d.strftime('%m/%d/%Y') for d in sorted(df['Date'].unique(), reverse=True)]

    st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>Performance Lab</h3>", unsafe_allow_html=True)
    c_main, c_pos = st.columns([2, 2])
    with c_main:
        date_a_str = st.selectbox("Current Practice", date_options, index=0)
    with c_pos:
        pos_list = sorted([p for p in df['Position'].unique() if p != "N/A"])
        pos_filter = st.selectbox("Position Filter", ["All Positions"] + pos_list)

    date_a = pd.to_datetime(date_a_str)
    day_df = df[df['Date'] == date_a].copy()
    if pos_filter != "All Positions":
        day_df = day_df[day_df['Position'] == pos_filter]

    # --- SCORE LOGIC ---
    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    overall_maxes = df.groupby('Name')[all_metrics].max().round(1)
    team_ath_maxes = cmj_df[['Jump Height (Imp-Mom) [cm]', 'Peak Power [W]', 'RSI-modified [m/s]']].max()

    def get_gradient(score):
        score = max(0, min(100, float(score)))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        
        grades = []
        for k in all_metrics:
            val = float(row[k])
            mx = float(p_maxes[k])
            # Grade = ROUNDUP(Current/Max*100, 0)
            grade = math.ceil((val / mx) * 100) if mx > 0 else 0
            row[f'{k}_Grade'] = grade
            row[f'{k}_Max'] = mx
            grades.append(grade)
        
        # Practice Score = ROUNDUP(AVERAGE(Grades), 0)
        row['Practice Score'] = math.ceil(sum(grades) / len(grades)) if grades else 0
        
        p_cmj = cmj_df[cmj_df['Athlete'] == p_name].sort_values('Test Date', ascending=False)
        if not p_cmj.empty:
            v = p_cmj.iloc[0]
            jh_s = (v['Jump Height (Imp-Mom) [cm]'] / team_ath_maxes['Jump Height (Imp-Mom) [cm]']) * 100
            pw_s = (v['Peak Power [W]'] / team_ath_maxes['Peak Power [W]']) * 100
            rs_s = (v['RSI-modified [m/s]'] / team_ath_maxes['RSI-modified [m/s]']) * 100
            row['Athletic Score'] = math.ceil((pw_s * 0.4) + (jh_s * 0.3) + (rs_s * 0.3))
        else:
            row['Athletic Score'] = 0
        return row

    if not day_df.empty:
        day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    t_player, t_gallery = st.tabs(["Individual Profile", "Team Gallery"])

    with t_player:
        if not day_df.empty:
            sel_p = st.selectbox("Select Athlete", day_df['Name'].unique())
            p = day_df[day_df['Name'] == sel_p].iloc[0]
            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1:
                st.markdown(f'<div style="text-align:center;"><img src="{p["PhotoURL"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
                st.markdown(f'<h2 style="text-align:center; margin-top:10px;">{p["Name"]}</h2>', unsafe_allow_html=True)
            with c2:
                html = '<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>Season Max</th><th>Grade</th></tr></thead><tbody>'
                for k in all_metrics:
                    html += f"<tr><td>{k}</td><td>{p[k]}</td><td>{p[f'{k}_Max']}</td><td>{int(p[f'{k}_Grade'])}</td></tr>"
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="score-wrapper">
                    <div class="score-label">Athletic Score</div>
                    <div class="score-box" style="background-color:{get_gradient(p['Athletic Score'])}; margin-bottom:20px;">{int(p['Athletic Score'])}</div>
                    <div class="score-label">Practice Score</div>
                    <div class="score-box" style="background-color:{get_gradient(p['Practice Score'])};">{int(p['Practice Score'])}</div>
                </div>
                """, unsafe_allow_html=True)

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
