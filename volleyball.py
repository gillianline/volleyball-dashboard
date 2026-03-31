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

    /* Table Styles */
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; table-layout: auto; }
    .scout-table th { background-color: #F5F5F7; padding: 4px; border-bottom: 2px solid #E5E5E7; font-weight: 700; font-size: 11px; }
    .scout-table td { padding: 4px; border-bottom: 1px solid #F5F5F7; font-size: 11px; }
    
    /* Profile Photo */
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    .score-box { padding: 15px 30px; border-radius: 12px; font-size: 36px; font-weight: 800; text-align: center; color: #1D1D1F; }
    
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
    .gallery-score-box { 
        padding: 10px; 
        border-radius: 12px; 
        text-align: center; 
        height: 100px; 
        width: 100px;
        display: flex; 
        align-items: center; 
        justify-content: center;
        margin: auto; 
    }
    .gallery-score { font-size: 38px; font-weight: 900; color: #1D1D1F; }
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
    # Primary Catapult Sheet
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    
    # VALD / CMJ Sheet (Add this URL to secrets)
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
    
    df = df.sort_values(['Name', 'Date'])
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    
    metric_cols = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    df[metric_cols] = df[metric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # Phase Sheet (Sheet 2)
    p_df = pd.read_csv(st.secrets["PHASE_SHEET_URL"])
    p_df.columns = p_df.columns.str.strip()
    p_df = p_df.rename(columns=rename_map)
    p_df['Date'] = pd.to_datetime(p_df['Date'])
    
    # CMJ Date Formatting
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'])
    
    return df, p_df, cmj_df

try:
    df, phase_df, cmj_df = load_all_data()
    date_options = [d.strftime('%m/%d/%Y') for d in sorted(df['Date'].unique(), reverse=True)]

    # --- HEADER ---
    st.markdown("<h3 style='text-align: center; margin-bottom: 0px;'>Performance Lab</h3>", unsafe_allow_html=True)
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

    # --- LOGIC ---
    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance', 'Explosive Efforts', 'High Intensity Movements']
    overall_maxes = df.groupby('Name')[all_metrics].max()

    def get_gradient(score):
        score = max(0, min(100, float(score)))
        r, g = (int(255*(score/50)), 255) if score < 50 else (255, int(255*(1-(score-50)/50)))
        return f"rgb({r}, {g}, 0)"

    def process_player(row):
        p_name = row['Name']
        p_maxes = overall_maxes.loc[p_name]
        grades = [math.ceil((float(row[k]) / float(p_maxes[k])) * 100) if float(p_maxes[k]) > 0 else 0 for k in all_metrics]
        row['Practice Score'] = math.ceil(sum(grades) / len(grades))
        for k in all_metrics:
            row[f'{k}_Grade'] = math.ceil((float(row[k]) / float(p_maxes[k])) * 100) if float(p_maxes[k]) > 0 else 0
            row[f'{k}_Max'] = p_maxes[k]
        return row

    if not day_df.empty:
        day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    t_flow, t_player, t_gallery = st.tabs(["Session Flow", "Individual Profile", "Team Gallery"])

    with t_flow:
        current_names = day_df['Name'].unique()
        day_phase_df = phase_df[(phase_df['Date'] == date_a) & (phase_df['Name'].isin(current_names))].copy()
        if not day_phase_df.empty:
            phase_stats = day_phase_df.groupby('Phase', sort=False).agg({'Player Load': 'mean', 'Explosive Efforts': 'mean', 'Total Jumps': 'mean'}).reset_index()
            st.plotly_chart(px.bar(phase_stats, x='Phase', y='Player Load', color='Explosive Efforts', color_continuous_scale='Oranges').update_layout(height=380), use_container_width=True)
            html = '<table class="scout-table"><thead><tr><th>Phase</th><th>Player Load</th><th>Explosive Efforts</th><th>Total Jumps</th></tr></thead><tbody>'
            for _, r in phase_stats.iterrows():
                html += f"<tr><td>{r['Phase']}</td><td>{int(r['Player Load'])}</td><td>{int(r['Explosive Efforts'])}</td><td>{int(r['Total Jumps'])}</td></tr>"
            st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

    with t_player:
        if not day_df.empty:
            selected_player = st.selectbox("Select Athlete", day_df['Name'].unique())
            p_data = day_df[day_df['Name'] == selected_player].iloc[0]
            
            # CMJ Data Lookup for Reference
            p_cmj = cmj_df[cmj_df['Athlete'] == selected_player].sort_values('Test Date', ascending=False)
            
            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1:
                st.markdown(f'<div style="text-align:center;"><img src="{p_data["PhotoURL"]}" class="player-photo-large"></div>', unsafe_allow_html=True)
                st.markdown(f'<h2 style="text-align:center;">{p_data["Name"]} ({p_data["Position"]})</h2>', unsafe_allow_html=True)
                
                if not p_cmj.empty:
                    v = p_cmj.iloc[0]
                    st.info(f"**Morning Readiness (VALD)**\n\nJump: {v['Jump Height (Imp-Mom) [cm]']:.1f}cm\n\nRSI: {v['RSI-modified [m/s]']:.2f}")

            with c2:
                html = '<table class="scout-table"><thead><tr><th>Metric</th><th>Today</th><th>Season Max</th><th>Grade</th></tr></thead><tbody>'
                for k in all_metrics:
                    html += f"<tr><td>{k}</td><td>{int(p_data[k])}</td><td>{int(p_data[f'{k}_Max'])}</td><td>{int(p_data[f'{k}_Grade'])}</td></tr>"
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div style="text-align:center; font-weight:bold; font-size:18px; margin-top:15px;">Practice Score</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="score-box" style="background-color:{get_gradient(p_data["Practice Score"])};">{int(p_data["Practice Score"])}</div>', unsafe_allow_html=True)

    with t_gallery:
        if not day_df.empty:
            for i in range(0, len(day_df), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(day_df):
                        p_d = day_df.iloc[i + j]
                        rows_html = "".join([f"<tr><td>{k}</td><td>{int(p_d[k])}</td><td>{int(p_d[f'{k}_Grade'])}</td></tr>" for k in all_metrics])
                        with cols[j]:
                            st.markdown(f"""
                            <div class="gallery-card">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <div style="flex: 1.2; text-align: center;">
                                        <img src="{p_d['PhotoURL']}" class="gallery-photo">
                                        <p style="font-weight:bold; font-size:15px; margin-top:8px;">{p_d['Name']}<br><small style="color:#FF8200;">{p_d['Position']}</small></p>
                                    </div>
                                    <div style="flex: 2.5;"><table class="scout-table"><thead><tr><th>Metric</th><th>Val</th><th>Grade</th></tr></thead><tbody>{rows_html}</tbody></table></div>
                                    <div style="flex: 1; text-align: center;"><div class="gallery-score-box" style="background-color:{get_gradient(p_d['Practice Score'])};"><div class="gallery-score">{int(p_d['Practice Score'])}</div></div></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
