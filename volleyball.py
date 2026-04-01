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
    .score-wrapper { text-align: center; }
    .score-label { font-size: 10px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; color: #515154; }
    .score-box { padding: 10px 20px; border-radius: 12px; font-size: 32px; font-weight: 800; min-width: 100px; color: #1D1D1F; }
    .status-subtext { font-size: 12px; font-weight: 900; display: block; margin-top: -5px; }
    
    /* Section Headers */
    .section-header { font-size: 14px; font-weight: 800; color: #FF8200; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    
    /* Gallery Card */
    .gallery-card { 
        border: 1px solid #E5E5E7; padding: 15px; border-radius: 15px; background-color: #FFFFFF; margin-bottom: 12px; min-height: 380px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .gallery-photo { border-radius: 50%; width: 110px; height: 110px; object-fit: cover; border: 5px solid #FF8200; }
    
    /* Info Box */
    .info-box { background-color: #F8F9FA; border-left: 5px solid #FF8200; padding: 10px; margin-top: 10px; font-size: 11px; color: #515154; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
    df.columns = df.columns.str.strip()
    
    # Categorize Session Type
    if 'Session Type' not in df.columns:
        df['Session Type'] = df['Activity'].apply(lambda x: 'Game' if any(word in str(x).lower() for word in ['game', 'match', 'v.']) else 'Practice')
    
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

    tabs = st.tabs(["Individual Profile", "Team Gallery", "Comparison Lab", "Game v. Practice"])

    # --- TABS 1-3 (STAY THE SAME) ---
    with tabs[0]:
        if not day_df.empty:
            sel_p = st.selectbox("Select Athlete", day_df['Name'].unique())
            p = day_df[day_df['Name'] == sel_p].iloc[0]
            # ... (Existing Individual Logic: GPS Top Row, Jump Middle Row, Phases Bottom Row)

    with tabs[1]:
        if not day_df.empty:
            # ... (Existing Gallery Logic: Score Cards with Today, Max, Grade)

    with tabs[2]:
        # ... (Existing Comparison Logic: Athlete v Pos and Volume Trends)

    # --- NEW TAB: GAME V PRACTICE ---
    with tabs[3]:
        st.markdown('<div class="section-header">Intensity Benchmark: Game vs. Practice</div>', unsafe_allow_html=True)
        
        # Calculate Team-Wide Averages by Session Type
        gp_agg = df.groupby('Session Type')[all_metrics].mean().reset_index()
        
        c_gp1, c_gp2 = st.columns([1.5, 3])
        with c_gp1:
            gp_metric = st.selectbox("Select Benchmark Metric", all_metrics)
            
            game_val = gp_agg[gp_agg['Session Type'] == 'Game'][gp_metric].values[0] if not gp_agg[gp_agg['Session Type'] == 'Game'].empty else 0
            prac_val = gp_agg[gp_agg['Session Type'] == 'Practice'][gp_metric].values[0] if not gp_agg[gp_agg['Session Type'] == 'Practice'].empty else 0
            
            intensity_pct = (prac_val / game_val * 100) if game_val > 0 else 0
            
            st.metric(label=f"Avg Practice {gp_metric}", value=f"{prac_val:.1f}", delta=f"{intensity_pct:.1f}% of Game Avg")
            
            st.markdown(f"""
                <div class="info-box">
                <b>The Intensity Gap:</b><br>
                Your practice average for {gp_metric} is currently <b>{intensity_pct:.1f}%</b> of your game intensity. 
                Sports scientists usually aim for 70-90% to ensure players are conditioned but not over-stressed.
                </div>
            """, unsafe_allow_html=True)

        with c_gp2:
            fig_gp = px.bar(gp_agg, x='Session Type', y=gp_metric, 
                            color='Session Type', color_discrete_map={'Game': '#1D1D1F', 'Practice': '#FF8200'},
                            title=f"Team Averages: {gp_metric}")
            fig_gp.update_layout(showlegend=False, height=350, xaxis_title=None)
            st.plotly_chart(fig_gp, use_container_width=True)

        st.markdown('<div class="section-header">Positional Game Demands</div>', unsafe_allow_html=True)
        pos_gp = df.groupby(['Position', 'Session Type'])[gp_metric].mean().reset_index()
        fig_pos_gp = px.bar(pos_gp, x='Position', y=gp_metric, color='Session Type', 
                            barmode='group', color_discrete_map={'Game': '#1D1D1F', 'Practice': '#FF8200'})
        st.plotly_chart(fig_pos_gp, use_container_width=True)

except Exception as e:
    st.error(f"Sync Error: {e}")
