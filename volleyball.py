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
    .player-photo-large { border-radius: 50%; width: 220px; height: 220px; object-fit: cover; border: 6px solid #FF8200; }
    .score-wrapper { text-align: center; }
    .score-label { font-size: 10px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; color: #515154; }
    .score-box { padding: 10px 20px; border-radius: 12px; font-size: 32px; font-weight: 800; min-width: 100px; color: #1D1D1F; }
    .section-header { font-size: 14px; font-weight: 800; color: #FF8200; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    .gallery-card { border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; min-height: 380px; display: flex; flex-direction: column; justify-content: center; }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 5px solid #FF8200; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    
    # Assume 'Session Type' column exists to distinguish 'Game' vs 'Practice'
    if 'Session Type' not in df.columns:
        df['Session Type'] = df['Activity'].apply(lambda x: 'Game' if 'Game' in str(x) or 'Match' in str(x) else 'Practice')
    
    cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
    cmj_df.columns = cmj_df.columns.str.strip()
    cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
    
    phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
    phase_df.columns = phase_df.columns.str.strip()
    if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
    phase_df['Date'] = pd.to_datetime(phase_df['Date'])
    
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
    
    df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'])
    return df, cmj_df, phase_df

try:
    df, cmj_df, phase_df = load_all_data()
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
        for i, k in enumerate(all_metrics): 
            row[f'{k}_Grade'] = grades[i]
            row[f'{k}_Max'] = rolling_maxes[k]
        return row

    if not day_df.empty:
        day_df = day_df.apply(process_player, axis=1).sort_values('Name')

    tab_ind, tab_gal, tab_comp = st.tabs(["Individual Profile", "Team Gallery", "Comparison Lab"])

    # [Previous Tab 1 and Tab 2 code remains the same]

    with tab_comp:
        st.markdown('<div class="section-header">Game vs. Practice Intensity Gap</div>', unsafe_allow_html=True)
        
        comp_metric = st.selectbox("Metric to Compare", all_metrics, key="gp_metric")
        
        # Calculate averages for Game vs Practice
        gp_summary = df.groupby('Session Type')[comp_metric].mean().reset_index()
        
        c_gp1, c_gp2 = st.columns([1, 2])
        with c_gp1:
            game_avg = gp_summary[gp_summary['Session Type'] == 'Game'][comp_metric].values[0] if not gp_summary[gp_summary['Session Type'] == 'Game'].empty else 0
            prac_avg = gp_summary[gp_summary['Session Type'] == 'Practice'][comp_metric].values[0] if not gp_summary[gp_summary['Session Type'] == 'Practice'].empty else 0
            
            intensity_pct = (prac_avg / game_avg * 100) if game_avg > 0 else 0
            
            st.metric(label="Practice Intensity (% of Game)", value=f"{intensity_pct:.1f}%")
            st.write(f"Typical Game Average: **{game_avg:.1f}**")
            st.write(f"Typical Practice Average: **{prac_avg:.1f}**")

        with c_gp2:
            fig_gp = px.bar(gp_summary, x='Session Type', y=comp_metric, 
                            color='Session Type', color_discrete_map={'Game': '#1D1D1F', 'Practice': '#FF8200'},
                            title=f"Avg {comp_metric}: Games vs. Practices")
            fig_gp.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig_gp, use_container_width=True)

        st.markdown('<div class="section-header">Athlete Comparison (Head-to-Head)</div>', unsafe_allow_html=True)
        c_h1, c_h2 = st.columns(2)
        with c_h1: p1 = st.selectbox("Player 1", day_df['Name'].unique(), index=0)
        with c_h2: p2 = st.selectbox("Player 2", day_df['Name'].unique(), index=1)
        
        comp_data = day_df[day_df['Name'].isin([p1, p2])]
        fig_h2h = px.bar(comp_data, x='Name', y=comp_metric, color='Name', 
                         color_discrete_map={p1: '#FF8200', p2: '#515154'},
                         barmode='group', title=f"{comp_metric} Comparison")
        st.plotly_chart(fig_h2h, use_container_width=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
