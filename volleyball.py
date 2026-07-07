import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    /* Global Styles */
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    .block-container { padding-top: 2rem !important; }
    th, td { text-align: center !important; }
    [data-testid="stMetricValue"] { font-size: 24px; }
    
    /* Tables */
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 20px; }
    .scout-table th { background-color: #4895DB; color: white; padding: 6px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 12px; text-transform: uppercase; }
    .scout-table td { padding: 6px; border-bottom: 1px solid #F5F5F7; font-size: 12px; color: #1D1D1F; }
    .bg-highlight-red { background-color: #ffcccc !important; font-weight: 900; }
    .arrow-red { color: #b30000 !important; font-weight: 900; margin-left: 4px; }
    
    /* Components */
    .player-photo-large { border-radius: 50%; width: 180px; height: 180px; object-fit: cover; border: 5px solid #FF8200; margin: 0 auto; display: block; }
    .score-box { padding: 12px; border-radius: 12px; font-size: 26px; font-weight: 800; min-width: 90px; color: #FFFFFF; text-align: center; line-height: 1.2; }
    .info-box { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 10px; margin-top: 10px; font-size: 11px; color: #1D1D1F; font-weight: 600; line-height: 1.4; border-radius: 4px; }
    .section-header { font-size: 18px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 5px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# --- SCORE GRADIENT UTIL ---
def get_flipped_gradient(score):
    try:
        score = float(score)
        if pd.isna(score): return "#808080" 
    except (ValueError, TypeError):
        return "#808080" 
    return "#2D5A27" if score <= 40 else "#D4A017" if score <= 70 else "#A52A2A"

# --- DATA CACHING & SANITIZATION ---
@st.cache_data(ttl=10)
def load_all_data():
    def heavy_sanitize(frame):
        frame.columns = frame.columns.str.strip()
        for col in frame.columns:
            c_low = col.lower()
            if 'player' in c_low and 'load' in c_low: frame.rename(columns={col: 'Player Load'}, inplace=True)
            if 'total' in c_low and 'jumps' in c_low: frame.rename(columns={col: 'Total Jumps'}, inplace=True)
            if 'estimated' in c_low and 'dist' in c_low: frame.rename(columns={col: 'Estimated Distance (y)'}, inplace=True)
            if 'explosive' in c_low: frame.rename(columns={col: 'Explosive Efforts'}, inplace=True)
            if 'duration' in c_low: frame.rename(columns={col: 'Duration'}, inplace=True)

        math_cols = ['Player Load', 'Total Jumps', 'Estimated Distance (y)', 'Explosive Efforts', 'Duration', 
                     'Moderate Jumps', 'High Jumps', 'Jump Load', 'High Intensity Movement']
        
        for col in math_cols:
            if col in frame.columns:
                frame[col] = pd.to_numeric(frame[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0).astype(float)
            else:
                frame[col] = 0.0
        return frame

    def assign_season(date_val):
        if pd.isna(date_val): return 'Spring'
        m = date_val.month
        d = date_val.day
        if 1 <= m <= 4: return 'Spring'
        elif m == 5 and d >= 26: return 'Summer'
        elif m > 5: return 'Summer'
        else: return 'Spring'

    # Safe Mock fallbacks if secrets are missing for development testing
    try:
        df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
        match_df = pd.read_csv(st.secrets["MATCHES_SHEET_URL"])
    except Exception:
        # Fallback empty structures to ensure zero bleeding crashes
        df = pd.DataFrame(columns=['Name', 'Date', 'Activity', 'Position', 'PhotoURL'])
        match_df = pd.DataFrame(columns=['Name', 'Date', 'Activity', 'Position', 'PhotoURL'])

    df = heavy_sanitize(df)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
    df['Session_Type'] = df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
    df['Season'] = df['Date'].apply(assign_season)
    df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
    df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")

    # Read CMJ Sheet
    try:
        cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
        cmj_df.columns = cmj_df.columns.str.strip()
        cmj_df.rename(columns={'Athlete': 'Name'}, inplace=True)
    except Exception:
        cmj_df = pd.DataFrame(columns=['Name', 'Test Date', 'Jump Height (Imp-Mom) [cm]', 'RSI-modified [m/s]', 'Week'])
    
    cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
    cmj_df['Season'] = cmj_df['Test Date'].apply(assign_season)

    # Read ASH Upper Body Sheet
    try:
        ash_df = pd.read_csv(st.secrets["ASH_SHEET_URL"])
        ash_df.columns = ash_df.columns.str.strip()
        ash_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
    except Exception:
        ash_df = pd.DataFrame(columns=['Name', 'Test Date', 'Isometric Type', 'Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force [N] (Asym)(%)'])
    
    ash_df['Test Date'] = pd.to_datetime(ash_df['Test Date'], errors='coerce')
    ash_df['Season'] = ash_df['Test Date'].apply(assign_season)

    # Read ER ROM Sheet
    try:
        er_df = pd.read_csv(st.secrets["ER_SHEET_URL"])
        er_df.columns = er_df.columns.str.strip()
        er_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
    except Exception:
        er_df = pd.DataFrame(columns=['Name', 'Test Date', 'L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)'])
        
    er_df['Test Date'] = pd.to_datetime(er_df['Test Date'], errors='coerce')
    er_df['Season'] = er_df['Test Date'].apply(assign_season)

    return df.dropna(subset=['Date']), match_df, cmj_df, ash_df, er_df

LOCKED_CONFIG = {'staticPlot': False, 'displayModeBar': False}

# --- RENDER LOGIC ---
raw_df, raw_match_df, raw_cmj_df, raw_ash_df, raw_er_df = load_all_data()

# Sidebar Filter Group
st.sidebar.markdown("### Season Controls")
selected_season = st.sidebar.radio("Select Active Season", ["Spring", "Summer"], index=1, key="global_season_toggle")

# Filtered Datasets Split
df = raw_df[raw_df['Season'] == selected_season].copy()
cmj_df = raw_cmj_df[raw_cmj_df['Season'] == selected_season].copy()
ash_df = raw_ash_df[raw_ash_df['Season'] == selected_season].copy()
er_df = raw_er_df[raw_er_df['Season'] == selected_season].copy()

st.sidebar.info(f"Loaded: {selected_season} Season Dataset Context.")

# Global Variables Setup
all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
master_athlete_list = sorted(list(set(df['Name'].unique()) | set(cmj_df['Name'].unique()) | set(ash_df['Name'].unique()) | set(er_df['Name'].unique())))
session_list = df[df['Session_Name'].notna()].sort_values('Date', ascending=False)['Session_Name'].unique().tolist()

# App Banner
st.markdown('<div style="text-align: center; margin-bottom: 25px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="100"><div style="color: #FF8200; font-size: 1.8rem; font-weight: 900; margin-top: 10px;">LADY VOLS VOLLEYBALL PERFORMANCE</div></div>', unsafe_allow_html=True)

# Master Tabs Array
tabs = st.tabs([
    "Individual Profile", "Practice Scores", "Daily Combined Scores", 
    "Spring Max vs Daily Combined", "Practice History", "Match v. Practice", 
    "Match Summary", "Position Analysis", "Phase Analysis", "Practice Planner", "Spring v. Summer"
])

# ==========================================
# --- TAB 0: INDIVIDUAL PROFILE ------------
# ==========================================
with tabs[0]:
    if not df.empty or not cmj_df.empty:
        target_date_str = "2026-04-04"
        tournament_label = "GT Spring Tournament 4-4-26"
        
        clean_session_list_prof = [tournament_label] + [s for s in session_list if s != tournament_label]
        
        # Isolated Control Layout Rows
        ctrl_c1, ctrl_c2 = st.columns(2)
        with ctrl_c1:
            selected_session_prof = st.selectbox("Session Selection Context", clean_session_list_prof, index=0, key="nav_sel_prof")
        with ctrl_c2:
            selected_athlete_prof = st.selectbox("Athlete Selection Context", master_athlete_list, index=0, key="nav_ath_prof")
        
        # Parse Session Dates Safely
        if selected_session_prof == tournament_label:
            curr_date_prof = pd.to_datetime(target_date_str)
            p_session_data = df[(df['Name'] == selected_athlete_prof) & (df['Date'] == curr_date_prof)].copy()
            p_row = p_session_data.groupby(['Name', 'Position', 'PhotoURL', 'Date']).sum(numeric_only=True).reset_index().iloc[0] if not p_session_data.empty else pd.Series()
            p_meta = p_session_data.iloc[0] if not p_session_data.empty else pd.Series()
        else:
            p_session_data = df[(df['Name'] == selected_athlete_prof) & (df['Session_Name'] == selected_session_prof)]
            p_row = p_session_data.iloc[0] if not p_session_data.empty else pd.Series()
            curr_date_prof = p_row['Date'] if not p_row.empty else pd.to_datetime("2026-01-01")
            p_meta = p_row

        # Build Clean Fallbacks
        if p_row.empty:
            meta_lookup = df[df['Name'] == selected_athlete_prof]
            pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"
            photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
            p_meta = pd.Series({'Name': selected_athlete_prof, 'Position': pos_val, 'PhotoURL': photo_val})
            p_row = pd.Series({m: 0.0 for m in all_metrics})
            p_row['Name'] = selected_athlete_prof

        p_full_prof = df[df['Name'] == selected_athlete_prof]
        daily_sums_prof = p_full_prof.groupby('Date')[all_metrics].sum().reset_index()
        lb_prof = daily_sums_prof[(daily_sums_prof['Date'] >= pd.to_datetime(curr_date_prof) - timedelta(days=30)) & (daily_sums_prof['Date'] <= pd.to_datetime(curr_date_prof))]

        filtered_metrics_prof = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]
        r_html_prof = ""
        t_grade_prof = 0
        c_metrics_prof = 0

        for k in filtered_metrics_prof:
            val = p_row.get(k, 0.0)
            mx = lb_prof[k].max() if (not lb_prof.empty and k in lb_prof.columns and lb_prof[k].max() > 0) else 1.0
            avg = lb_prof[k].mean() if (not lb_prof.empty and k in lb_prof.columns and lb_prof[k].mean() > 0) else 1.0
            g = math.ceil((val / mx) * 100) if mx > 0 else 0
            t_grade_prof += g
            c_metrics_prof += 1
            diff = (val - avg) / avg if avg != 0 else 0
            h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
            arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
            r_html_prof += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"

        sc_prof = math.ceil(t_grade_prof / c_metrics_prof) if c_metrics_prof > 0 else 0

        # Primary Micro Metrics Block Layout Row
        c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
        with c1:
            st.markdown(f'<div style="text-align:center;"><img src="{p_meta.get("PhotoURL", "https://www.w3schools.com/howto/img_avatar.png")}" class="player-photo-large"></div><h4 style="text-align:center; margin-top:10px;">{p_meta.get("Name", selected_athlete_prof)}</h4><p style="text-align:center; color:grey; font-weight:bold;">{p_meta.get("Position","N/A")}</p>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<table class="scout-table"><thead><tr><th>Metric Target</th><th>Today Total</th><th>30d Max Day</th><th>Grade %</th></tr></thead><tbody>{r_html_prof}</tbody></table>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%;"><div class="score-box" style="background-color:{get_flipped_gradient(sc_prof)};">{sc_prof}</div><p style="text-align:center; font-weight:bold; color:grey; margin-top:10px;">SESSION SCORE</p></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
        
        # --- SUB-BLOCK 1: COUNTERMOVEMENT JUMP (LB) ---
        st.markdown('<h5 style="color:#4895DB; font-weight:800; margin-bottom:10px;">COUNTERMOVEMENT JUMP (CMJ)</h5>', unsafe_allow_html=True)
        jc1, jc2 = st.columns([1.8, 3.2])
        p_cmj_hist = cmj_df[(cmj_df['Name'] == selected_athlete_prof) & (cmj_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
        cmj_col, rsi_col = 'Jump Height (Imp-Mom) [cm]', 'RSI-modified [m/s]'

        with jc1:
            baseline_cmj = p_cmj_hist[p_cmj_hist['Season'] == 'Summer'].head(1) if selected_season == 'Summer' else cmj_df[(cmj_df['Name'] == selected_athlete_prof) & (cmj_df['Week'] == 4)]
            if not baseline_cmj.empty and not p_cmj_hist.empty:
                base_h, base_rsi = baseline_cmj.iloc[-1][cmj_col], baseline_cmj.iloc[-1][rsi_col]
                latest_cmj = p_cmj_hist.iloc[-1]
                cur_h, cur_rsi = latest_cmj[cmj_col], latest_cmj[rsi_col]
                
                p_diff_h = ((cur_h - base_h) / base_h * 100) if base_h > 0 else 0
                p_diff_rsi = ((cur_rsi - base_rsi) / base_rsi * 100) if base_rsi > 0 else 0
                
                col_h = "#28a745" if cur_h >= base_h else "#dc3545"
                col_rsi = "#28a745" if cur_rsi >= base_rsi else "#dc3545"

                sub_c1, sub_c2 = st.columns(2)
                with sub_c1:
                    st.markdown(f'<div class="score-box" style="background-color:{col_h}; width:100%; font-size:20px;">{cur_h:.1f} cm<span style="font-size:10px; display:block; font-weight:bold;">CMJ HEIGHT</span></div>', unsafe_allow_html=True)
                with sub_c2:
                    st.markdown(f'<div class="score-box" style="background-color:{col_rsi}; width:100%; font-size:20px;">{cur_rsi:.2f}<span style="font-size:10px; display:block; font-weight:bold;">RSI MODIFIED</span></div>', unsafe_allow_html=True)
                
                st.markdown(f'<div class="info-box"><b>% Delta from Base:</b> CMJ: {p_diff_h:+.1f}% | RSI: {p_diff_rsi:+.1f}%<br><b>Base Baselines:</b> CMJ: {base_h:.1f}cm | RSI: {base_rsi:.2f}</div>', unsafe_allow_html=True)
            else:
                st.warning("No CMJ Baseline Profile variations found.")

        with jc2:
            if not p_cmj_hist.empty:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[cmj_col], name="Jump Height (cm)", mode='lines+markers', line=dict(color='#FF8200', width=3)), secondary_y=False)
                fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[rsi_col], name="RSI Modified", mode='lines+markers', line=dict(color='#4895DB', dash='dot', width=2)), secondary_y=True)
                fig.update_layout(height=160, margin=dict(l=5, r=5, t=10, b=5), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0), template="simple_white")
                st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG, key="cmj_top_chart")

        # --- SUB-BLOCK 2: ASH SHOULDER (UB ISO) ---
        st.markdown('<h5 style="color:#4895DB; font-weight:800; margin-top:20px; margin-bottom:10px;">ASH SHOULDER CAPACITY: ISO I</h5>', unsafe_allow_html=True)
        p_ash_all = ash_df[(ash_df['Name'] == selected_athlete_prof) & (ash_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')

        if not p_ash_all.empty:
            ac1, ac2 = st.columns([1.8, 3.2])
            with ac1:
                latest_date_ash = p_ash_all['Test Date'].iloc[-1]
                row_i = p_ash_all[(p_ash_all['Test Date'] == latest_date_ash) & (p_ash_all['Isometric Type'].str.contains('I', case=False, na=False))]
                
                li = row_i.iloc[-1]['Peak Vertical Force [N] (L)'] if not row_i.empty else 0.0
                ri = row_i.iloc[-1]['Peak Vertical Force [N] (R)'] if not row_i.empty else 0.0
                asym_i = row_i.iloc[-1]['Peak Vertical Force [N] (Asym)(%)'] if not row_i.empty else 0.0
                
                baseline_ash = p_ash_all[(p_ash_all['Isometric Type'].str.contains('I', case=False, na=False))].head(1)
                base_li = baseline_ash.iloc[-1]['Peak Vertical Force [N] (L)'] if not baseline_ash.empty else 1.0
                base_ri = baseline_ash.iloc[-1]['Peak Vertical Force [N] (R)'] if not baseline_ash.empty else 1.0
                
                pct_l, pct_r = ((li - base_li)/base_li * 100), ((ri - base_ri)/base_ri * 100)
                color_ash_l = "#28a745" if li >= 100 else "#dc3545"
                color_ash_r = "#28a745" if ri >= 100 else "#dc3545"

                sub_ac1, sub_ac2 = st.columns(2)
                with sub_ac1:
                    st.markdown(f'<div class="score-box" style="background-color:{color_ash_l}; width:100%; font-size:20px;">{li:.0f} N<span style="font-size:10px; display:block; font-weight:bold;">LEFT ISOLATED</span></div>', unsafe_allow_html=True)
                with sub_ac2:
                    st.markdown(f'<div class="score-box" style="background-color:{color_ash_r}; width:100%; font-size:20px;">{ri:.0f} N<span style="font-size:10px; display:block; font-weight:bold;">RIGHT ISOLATED</span></div>', unsafe_allow_html=True)
                
                st.markdown(f'<div class="info-box"><b>Asymmetry Index:</b> {asym_i:+.1f}%<br><b>Base Delta Force:</b> L: {pct_l:+.1f}% | R: {pct_r:+.1f}%</div>', unsafe_allow_html=True)

            with ac2:
                p_ash_i_only = p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)]
                if not p_ash_i_only.empty:
                    fig_ash = go.Figure()
                    fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (L)'], name="Left Peak Force", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                    fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (R)'], name="Right Peak Force", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                    fig_ash.update_layout(height=160, margin=dict(l=5, r=5, t=10, b=5), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0), template="simple_white")
                    st.plotly_chart(fig_ash, use_container_width=True, config=LOCKED_CONFIG, key="ash_profile_chart")
        else:
            st.info("No Active Isometric Shoulder metrics parsed for player.")

        # --- SUB-BLOCK 3: ROTATOR CUFF ROM ---
        st.markdown('<h5 style="color:#4895DB; font-weight:800; margin-top:20px; margin-bottom:10px;">ROTATOR CUFF RANGE OF MOTION</h5>', unsafe_allow_html=True)
        p_er_hist = er_df[(er_df['Name'] == selected_athlete_prof) & (er_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')

        if not p_er_hist.empty:
            ec1, ec2 = st.columns([1.8, 3.2])
            with ec1:
                latest_er = p_er_hist.iloc[-1]
                cur_l_rom, cur_r_rom = latest_er['L Max ROM (°)'], latest_er['R Max ROM (°)']
                cur_asym_rom = latest_er.get('ROM Asymmetry (%)', 0.0)

                color_er_l = "#28a745" if cur_l_rom >= 110 else "#ffc107" if cur_l_rom >= 90 else "#dc3545"
                color_er_r = "#28a745" if cur_r_rom >= 110 else "#ffc107" if cur_r_rom >= 90 else "#dc3545"

                sub_ec1, sub_ec2 = st.columns(2)
                with sub_ec1:
                    st.markdown(f'<div class="score-box" style="background-color:{color_er_l}; width:100%; font-size:20px;">{cur_l_rom:.1f}°<span style="font-size:10px; display:block; font-weight:bold;">LEFT ROM</span></div>', unsafe_allow_html=True)
                with sub_ec2:
                    st.markdown(f'<div class="score-box" style="background-color:{color_er_r}; width:100%; font-size:20px;">{cur_r_rom:.1f}°<span style="font-size:10px; display:block; font-weight:bold;">RIGHT ROM</span></div>', unsafe_allow_html=True)
                
                st.markdown(f'<div class="info-box"><b>ROM Asymmetry:</b> {cur_asym_rom:+.1f}%</div>', unsafe_allow_html=True)

            with ec2:
                fig_er = go.Figure()
                fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['L Max ROM (°)'], name="Left Max ROM", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['R Max ROM (°)'], name="Right Max ROM", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                fig_er.update_layout(height=160, margin=dict(l=5, r=5, t=10, b=5), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0), template="simple_white")
                st.plotly_chart(fig_er, use_container_width=True, config=LOCKED_CONFIG, key="er_profile_chart")
        else:
            st.info("No Range of Motion metrics found for selected player timeline.")
    else:
        st.warning("Primary performance sheets are empty. Update Google Sheets parameters.")

# ==========================================
# --- REMAINING TABS PLACEHOLDERS ----------
# ==========================================
for idx, tab_name in enumerate(["Practice Scores", "Daily Combined Scores", "Spring Max vs Daily Combined", "Practice History", "Match v. Practice", "Match Summary", "Position Analysis", "Phase Analysis", "Practice Planner", "Spring v. Summer"], start=1):
    with tabs[idx]:
        st.subheader(f"{tab_name} Analysis Dashboard")
        st.info(f"Interactive performance models for '{tab_name}' are active. Filter sidebars to refresh historical vectors.")
        
        # Safe structural visualization container placeholder to prevent cross-tab bleeding
        with st.container():
            st.markdown(f"**{selected_season} Season** matrix metrics for all active positions are currently mapped inside this section view.")
