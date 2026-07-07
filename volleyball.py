import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

# --- INITIALIZE SESSION STATE ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

# --- PASSWORD PROTECTION ---
def check_password():
    if st.session_state["password_correct"]:
        return True
        
    def password_entered():
        secret_pass = st.secrets.get("PASSWORD", "VolsVB2026")
        if st.session_state["password_input"] == secret_pass:
            st.session_state["password_correct"] = True
            st.session_state["password_error"] = False
        else:
            st.session_state["password_correct"] = False
            st.session_state["password_error"] = True

    st.markdown('<div style="max-width: 400px; margin: 80px auto;">', unsafe_allow_html=True)
    st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password_input")
    if st.session_state.get("password_error", False):
        st.error("❌ Incorrect Password. Please try again.")
    st.markdown('</div>', unsafe_allow_html=True)
    return False

if check_password():
    # --- WEB ONLY UI CSS (No Print Blocks to Prevent Bleeding) ---
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; color: #1D1D1F; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 3rem !important; }
        th, td { text-align: center !important; vertical-align: middle !important; }
        
        .scout-table { width: 100%; border-collapse: collapse; text-align: center; margin: 10px 0 20px 0; }
        .scout-table th { background-color: #4895DB; color: white; padding: 10px 8px; border-bottom: 3px solid #FF8200; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
        .scout-table td { padding: 10px 8px; border-bottom: 1px solid #E5E5E7; font-size: 13px; color: #1D1D1F; font-weight: 500; }
        .bg-highlight-red { background-color: #FFE6E6 !important; font-weight: 800; color: #B30000 !important; }
        .arrow-red { color: #B30000 !important; font-weight: 900; margin-left: 4px; }
        
        .player-photo-large { border-radius: 50%; width: 170px; height: 170px; object-fit: cover; border: 5px solid #FF8200; margin: 0 auto; display: block; box-shadow: 0px 4px 12px rgba(0,0,0,0.08); }
        .score-box { padding: 16px; border-radius: 12px; font-size: 30px; font-weight: 800; min-width: 90px; color: #FFFFFF; text-align: center; display: inline-block; line-height: 1; }
        .info-box { background-color: #F8F9FA; border-left: 5px solid #FF8200; padding: 12px; margin-top: 10px; font-size: 12px; color: #1D1D1F; font-weight: 600; line-height: 1.5; border-radius: 0 8px 8px 0; }
        .section-header { font-size: 18px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin: 30px 0 15px 0; padding-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        
        .flex-row-container { display: flex; flex-direction: column; width: 100%; margin-bottom: 25px; }
        </style>
        """, unsafe_allow_html=True)

    # --- PROTECTED DATA UTILS ---
    def get_flipped_gradient(score):
        try:
            score = float(score)
            if pd.isna(score): return "#808080" 
        except (ValueError, TypeError):
            return "#808080" 
        return "#2D5A27" if score <= 40 else "#D4A017" if score <= 70 else "#A52A2A"

    def safe_float(val, fallback=0.0):
        try:
            if pd.isna(val) or val == 'N/A' or val == '-' or val == 'nan': return fallback
            return float(val)
        except (ValueError, TypeError):
            return fallback

    # --- REBUILT INGESTION PIPELINE ---
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

        g_url = st.secrets.get("GOOGLE_SHEET_URL", "")
        m_url = st.secrets.get("MATCHES_SHEET_URL", "")
        c_url = st.secrets.get("CMJ_SHEET_URL", "")
        a_url = st.secrets.get("ASH_SHEET_URL", "")
        e_url = st.secrets.get("ER_SHEET_URL", "")
        p_url = st.secrets.get("PHASES_SHEET_URL", "")

        def read_or_mock(url, columns):
            try:
                if url: return pd.read_csv(url)
            except Exception:
                pass
            return pd.DataFrame(columns=columns)

        df = read_or_mock(g_url, ['Name', 'Date', 'Activity', 'Position', 'PhotoURL', 'Player Load', 'Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Estimated Distance (y)', 'Explosive Efforts', 'Duration', 'High Intensity Movement'])
        match_df = read_or_mock(m_url, ['Name', 'Date', 'Activity', 'Position', 'Player Load', 'Total Jumps', 'Duration'])
        cmj_df = read_or_mock(c_url, ['Athlete', 'Test Date', 'Jump Height (Imp-Mom) [cm]', 'RSI-modified [m/s]', 'Week'])
        ash_df = read_or_mock(a_url, ['Athlete', 'Date', 'Isometric Type', 'Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force [N] (Asym)(%)'])
        er_df = read_or_mock(e_url, ['Athlete', 'Date', 'L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)'])
        phase_df = read_or_mock(p_url, ['Date', 'Phases', 'Activity', 'Player Load', 'Total Jumps', 'Name', 'Duration'])

        df = heavy_sanitize(df)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
        df['Session_Type'] = df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
        df['Season'] = df['Date'].apply(assign_season)
        if not df.empty:
            df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
            df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")

        match_df = heavy_sanitize(match_df)
        match_df['Date'] = pd.to_datetime(match_df['Date'], errors='coerce')
        match_df['Season'] = match_df['Date'].apply(assign_season)
        match_df['Session_Name'] = match_df['Activity'].fillna(match_df['Date'].dt.strftime('%m/%d/%Y'))

        cmj_df.columns = cmj_df.columns.str.strip()
        cmj_df.rename(columns={'Athlete': 'Name'}, inplace=True)
        cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
        cmj_df['Season'] = cmj_df['Test Date'].apply(assign_season)

        ash_df.columns = ash_df.columns.str.strip()
        ash_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        ash_df['Test Date'] = pd.to_datetime(ash_df['Test Date'], errors='coerce')
        ash_df['Season'] = ash_df['Test Date'].apply(assign_season)

        er_df.columns = er_df.columns.str.strip()
        er_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
        er_df['Test Date'] = pd.to_datetime(er_df['Test Date'], errors='coerce')
        er_df['Season'] = er_df['Test Date'].apply(assign_season)

        phase_df = heavy_sanitize(phase_df)
        phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
        phase_df['Season'] = phase_df['Date'].apply(assign_season)
        if 'Phases' in phase_df.columns: phase_df.rename(columns={'Phases': 'Phase'}, inplace=True)

        return df.dropna(subset=['Date']), match_df.dropna(subset=['Date']), cmj_df, ash_df, er_df, phase_df

    LOCKED_CONFIG = {'staticPlot': False, 'displayModeBar': False}

    # --- UNPACK DATA ---
    df, match_df, cmj_df, ash_df, er_df, phase_df = load_all_data()

    # --- GLOBAL FILTER SIDEBAR ---
    st.sidebar.markdown("### 🎛️ Dashboard Filters")
    selected_season = st.sidebar.radio("Active Season", ["Spring", "Summer"], index=1, key="global_season_toggle")
    
    # Season-scoped data copies
    df_filtered = df[df['Season'] == selected_season].copy()
    match_filtered = match_df[match_df['Season'] == selected_season].copy()
    cmj_filtered = cmj_df[cmj_df['Season'] == selected_season].copy()
    ash_filtered = ash_df[ash_df['Season'] == selected_season].copy()
    er_filtered = er_df[er_df['Season'] == selected_season].copy()
    phase_filtered = phase_df[phase_df['Season'] == selected_season].copy()

    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
    master_athlete_list = sorted(list(set(df_filtered['Name'].unique()) | set(cmj_filtered['Name'].unique()) | set(ash_filtered['Name'].unique()) | set(er_filtered['Name'].unique())))
    if not master_athlete_list: master_athlete_list = ["No Data Registered"]
    
    session_list = df_filtered[df_filtered['Session_Name'].notna()].sort_values('Date', ascending=False)['Session_Name'].unique().tolist()
    practice_sessions = df_filtered[df_filtered['Session_Type'] == 'Practice']['Session_Name'].unique().tolist()

    # --- APPLICATION TABS ---
    tabs = st.tabs([
        "Individual Profile", "Practice Scores", "Daily Combined Scores", 
        "Spring Max vs Daily Combined", "Practice History", "Match v. Practice", 
        "Match Summary", "Position Analysis", "Phase Analysis", "Practice Planner", "Spring v. Summer"
    ])

    # ==========================================
    # --- TAB 0: INDIVIDUAL PROFILE ------------
    # ==========================================
    with tabs[0]:
        st.markdown('<div class="flex-row-container">', unsafe_allow_html=True)
        if not df_filtered.empty:
            target_date_str = "2026-04-04"
            tournament_label = "GT Spring Tournament 4-4-26"
            clean_session_list_prof = [tournament_label] + [s for s in session_list if s != tournament_label]
            
            deck_c1, deck_c2 = st.columns(2)
            with deck_c1:
                selected_session_prof = st.selectbox("Active Session Windows", clean_session_list_prof, index=0, key="nav_sel_prof")
            with deck_c2:
                selected_athlete_prof = st.selectbox("Active Athlete Profile", master_athlete_list, index=0, key="nav_ath_prof")
            
            if selected_session_prof == tournament_label:
                curr_date_prof = pd.to_datetime(target_date_str)
                p_session_data = df_filtered[(df_filtered['Name'] == selected_athlete_prof) & (df_filtered['Date'] == curr_date_prof)].copy()
                p_row = p_session_data.groupby(['Name', 'Position', 'PhotoURL', 'Date']).sum(numeric_only=True).reset_index().iloc[0] if not p_session_data.empty else pd.Series()
                p_meta = p_session_data.iloc[0] if not p_session_data.empty else pd.Series()
            else:
                p_session_data = df_filtered[(df_filtered['Name'] == selected_athlete_prof) & (df_filtered['Session_Name'] == selected_session_prof)]
                p_row = p_session_data.iloc[0] if not p_session_data.empty else pd.Series()
                curr_date_prof = p_row['Date'] if not p_row.empty else pd.to_datetime("2026-01-01")
                p_meta = p_row

            if p_row.empty:
                meta_lookup = df_filtered[df_filtered['Name'] == selected_athlete_prof]
                pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"
                photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                p_meta = pd.Series({'Name': selected_athlete_prof, 'Position': pos_val, 'PhotoURL': photo_val})
                p_row = pd.Series({m: 0.0 for m in all_metrics})
                p_row['Name'] = selected_athlete_prof

            p_full_prof = df_filtered[df_filtered['Name'] == selected_athlete_prof]
            daily_sums_prof = p_full_prof.groupby('Date')[all_metrics].sum().reset_index()
            lb_prof = daily_sums_prof[(daily_sums_prof['Date'] >= pd.to_datetime(curr_date_prof) - timedelta(days=30)) & (daily_sums_prof['Date'] <= pd.to_datetime(curr_date_prof))]

            filtered_metrics_prof = [m for m in all_metrics if m not in ['High Jumps', 'Moderate Jumps', 'High Intensity Movement']]
            r_html_prof = ""
            t_grade_prof = 0
            c_metrics_prof = 0

            for k in filtered_metrics_prof:
                val = safe_float(p_row.get(k, 0.0))
                mx = safe_float(lb_prof[k].max() if (not lb_prof.empty and k in lb_prof.columns) else 1.0)
                avg = safe_float(lb_prof[k].mean() if (not lb_prof.empty and k in lb_prof.columns) else 1.0)
                if mx <= 0: mx = 1.0
                g = math.ceil((val / mx) * 100)
                t_grade_prof += g
                c_metrics_prof += 1
                diff = (val - avg) / avg if avg != 0 else 0
                h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
                arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
                r_html_prof += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}%</td></tr>"

            sc_prof = math.ceil(t_grade_prof / c_metrics_prof) if c_metrics_prof > 0 else 0

            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1:
                st.markdown(f'<div style="text-align:center; padding-top:10px;"><img src="{p_meta.get("PhotoURL", "https://www.w3schools.com/howto/img_avatar.png")}" class="player-photo-large"></div><h4 style="text-align:center; margin-top:12px; margin-bottom: 2px;">{p_meta.get("Name", selected_athlete_prof)}</h4><p style="text-align:center; color:#7F8C8D; font-weight:700; font-size:13px;">{p_meta.get("Position","N/A")}</p>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<table class="scout-table"><thead><tr><th>Metric Target</th><th>Session Total</th><th>30d Rolling Max</th><th>Session Load %</th></tr></thead><tbody>{r_html_prof}</tbody></table>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; min-height:180px;"><div class="score-box" style="background-color:{get_flipped_gradient(sc_prof)};">{sc_prof}</div><p style="text-align:center; font-weight:bold; color:#7F8C8D; margin-top:10px; font-size:12px; letter-spacing:0.5px;">SESSION STRAIN INDEX</p></div>', unsafe_allow_html=True)
            
            st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
            
            # CMJ SUB-BLOCK
            st.markdown('<h5 style="color:#4895DB; font-weight:800; margin-bottom:12px;">LOWER BODY METRICS: COUNTERMOVEMENT JUMP (CMJ)</h5>', unsafe_allow_html=True)
            jc1, jc2 = st.columns([1.8, 3.2])
            p_cmj_hist = cmj_filtered[(cmj_filtered['Name'] == selected_athlete_prof) & (cmj_filtered['Test Date'] <= curr_date_prof)].sort_values('Test Date')
            cmj_col, rsi_col = 'Jump Height (Imp-Mom) [cm]', 'RSI-modified [m/s]'

            with jc1:
                baseline_cmj = p_cmj_hist.head(1) if selected_season == 'Summer' else cmj_filtered[(cmj_filtered['Name'] == selected_athlete_prof) & (cmj_filtered['Week'] == 4)]
                if not baseline_cmj.empty and not p_cmj_hist.empty:
                    base_h = safe_float(baseline_cmj.iloc[-1].get(cmj_col, 0.0))
                    base_rsi = safe_float(baseline_cmj.iloc[-1].get(rsi_col, 0.0))
                    latest_cmj = p_cmj_hist.iloc[-1]
                    cur_h = safe_float(latest_cmj.get(cmj_col, 0.0))
                    cur_rsi = safe_float(latest_cmj.get(rsi_col, 0.0))
                    
                    p_diff_h = ((cur_h - base_h) / base_h * 100) if base_h > 0 else 0
                    p_diff_rsi = ((cur_rsi - base_rsi) / base_rsi * 100) if base_rsi > 0 else 0
                    col_h = "#28a745" if cur_h >= base_h else "#dc3545"
                    col_rsi = "#28a745" if cur_rsi >= base_rsi else "#dc3545"

                    sub_c1, sub_c2 = st.columns(2)
                    with sub_c1:
                        st.markdown(f'<div class="score-box" style="background-color:{col_h}; width:100%; font-size:18px; padding:12px;">{cur_h:.1f} cm<span style="font-size:10px; display:block; font-weight:bold; margin-top:3px;">CMJ HEIGHT</span></div>', unsafe_allow_html=True)
                    with sub_c2:
                        st.markdown(f'<div class="score-box" style="background-color:{col_rsi}; width:100%; font-size:18px; padding:12px;">{cur_rsi:.2f}<span style="font-size:10px; display:block; font-weight:bold; margin-top:3px;">RSI MODIFIED</span></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="info-box"><b>% Variance vs Base:</b> CMJ Height: {p_diff_h:+.1f}% | RSI Mod: {p_diff_rsi:+.1f}%<br><b>Base Baselines:</b> CMJ: {base_h:.1f}cm | RSI: {base_rsi:.2f}</div>', unsafe_allow_html=True)
                else:
                    st.info("ℹ️ Baseline jump metrics unmapped for player selection.")

            with jc2:
                if not p_cmj_hist.empty and cmj_col in p_cmj_hist.columns:
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[cmj_col], name="Jump Height (cm)", mode='lines+markers', line=dict(color='#FF8200', width=3)), secondary_y=False)
                    fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[rsi_col], name="RSI Modified", mode='lines+markers', line=dict(color='#4895DB', dash='dot', width=2)), secondary_y=True)
                    fig.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0), template="simple_white")
                    st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG, key="cmj_profile_chart")

            # ASH SHOULDER SUB-BLOCK
            st.markdown('<h5 style="color:#4895DB; font-weight:800; margin-top:25px; margin-bottom:12px;">UPPER BODY CAPACITY: ASH SHOULDER TEST (ISO I)</h5>', unsafe_allow_html=True)
            p_ash_all = ash_filtered[(ash_filtered['Name'] == selected_athlete_prof) & (ash_filtered['Test Date'] <= curr_date_prof)].sort_values('Test Date')

            if not p_ash_all.empty:
                ac1, ac2 = st.columns([1.8, 3.2])
                with ac1:
                    latest_date_ash = p_ash_all['Test Date'].iloc[-1]
                    row_i = p_ash_all[(p_ash_all['Test Date'] == latest_date_ash) & (p_ash_all['Isometric Type'].str.contains('I', case=False, na=False))]
                    li = safe_float(row_i.iloc[-1].get('Peak Vertical Force [N] (L)', 0.0) if not row_i.empty else 0.0)
                    ri = safe_float(row_i.iloc[-1].get('Peak Vertical Force [N] (R)', 0.0) if not row_i.empty else 0.0)
                    asym_i = safe_float(row_i.iloc[-1].get('Peak Vertical Force [N] (Asym)(%)', 0.0) if not row_i.empty else 0.0)
                    
                    baseline_ash = p_ash_all[(p_ash_all['Isometric Type'].str.contains('I', case=False, na=False))].head(1)
                    base_li = safe_float(baseline_ash.iloc[-1].get('Peak Vertical Force [N] (L)', 1.0) if not baseline_ash.empty else 1.0)
                    base_ri = safe_float(baseline_ash.iloc[-1].get('Peak Vertical Force [N] (R)', 1.0) if not baseline_ash.empty else 1.0)
                    if base_li <= 0: base_li = 1.0
                    if base_ri <= 0: base_ri = 1.0
                    
                    pct_l = ((li - base_li) / base_li * 100)
                    pct_r = ((ri - base_ri) / base_ri * 100)
                    color_ash_l = "#28a745" if li >= 100 else "#dc3545"
                    color_ash_r = "#28a745" if ri >= 100 else "#dc3545"

                    sub_ac1, sub_ac2 = st.columns(2)
                    with sub_ac1:
                        st.markdown(f'<div class="score-box" style="background-color:{color_ash_l}; width:100%; font-size:18px; padding:12px;">{li:.0f} N<span style="font-size:10px; display:block; font-weight:bold; margin-top:3px;">LEFT FORCE</span></div>', unsafe_allow_html=True)
                    with sub_ac2:
                        st.markdown(f'<div class="score-box" style="background-color:{color_ash_r}; width:100%; font-size:18px; padding:12px;">{ri:.0f} N<span style="font-size:10px; display:block; font-weight:bold; margin-top:3px;">RIGHT FORCE</span></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="info-box"><b>Peak Force Asymmetry:</b> {asym_i:+.1f}%<br><b>Force Shift from Base:</b> Left: {pct_l:+.1f}% | Right: {pct_r:+.1f}%</div>', unsafe_allow_html=True)

                with ac2:
                    p_ash_i_only = p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)]
                    if not p_ash_i_only.empty:
                        fig_ash = go.Figure()
                        fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (L)'], name="Left ISO", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                        fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (R)'], name="Right ISO", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                        fig_ash.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0), template="simple_white")
                        st.plotly_chart(fig_ash, use_container_width=True, config=LOCKED_CONFIG, key="ash_profile_chart")
            else:
                st.info("ℹ️ No shoulder isometric testing sets logged.")

            # ROTATOR CUFF ROM SUB-BLOCK
            st.markdown('<h5 style="color:#4895DB; font-weight:800; margin-top:25px; margin-bottom:12px;">ROTATOR CUFF RECOVERY: EXTERNAL ROTATION ROM</h5>', unsafe_allow_html=True)
            p_er_hist = er_filtered[(er_filtered['Name'] == selected_athlete_prof) & (er_filtered['Test Date'] <= curr_date_prof)].sort_values('Test Date')

            if not p_er_hist.empty:
                ec1, ec2 = st.columns([1.8, 3.2])
                with ec1:
                    latest_er = p_er_hist.iloc[-1]
                    cur_l_rom = safe_float(latest_er.get('L Max ROM (°)', 0.0))
                    cur_r_rom = safe_float(latest_er.get('R Max ROM (°)', 0.0))
                    cur_asym_rom = safe_float(latest_er.get('ROM Asymmetry (%)', 0.0))
                    color_er_l = "#28a745" if cur_l_rom >= 110 else "#ffc107" if cur_l_rom >= 90 else "#dc3545"
                    color_er_r = "#28a745" if cur_r_rom >= 110 else "#ffc107" if cur_r_rom >= 90 else "#dc3545"

                    sub_ec1, sub_ec2 = st.columns(2)
                    with sub_ec1:
                        st.markdown(f'<div class="score-box" style="background-color:{color_er_l}; width:100%; font-size:18px; padding:12px;">{cur_l_rom:.1f}°<span style="font-size:10px; display:block; font-weight:bold; margin-top:3px;">LEFT ROM</span></div>', unsafe_allow_html=True)
                    with sub_ec2:
                        st.markdown(f'<div class="score-box" style="background-color:{color_er_r}; width:100%; font-size:18px; padding:12px;">{cur_r_rom:.1f}°<span style="font-size:10px; display:block; font-weight:bold; margin-top:3px;">RIGHT ROM</span></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="info-box"><b>ROM Asymmetry Index:</b> {cur_asym_rom:+.1f}%</div>', unsafe_allow_html=True)

                with ec2:
                    fig_er = go.Figure()
                    fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['L Max ROM (°)'], name="Left ROM", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                    fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['R Max ROM (°)'], name="Right ROM", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                    fig_er.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0), template="simple_white")
                    st.plotly_chart(fig_er, use_container_width=True, config=LOCKED_CONFIG, key="er_profile_chart")
            else:
                st.info("ℹ️ External rotation metrics unavailable.")
        else:
            st.warning("No metrics registered inside tracking databases.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # --- TAB 1: PRACTICE SCORES ---------------
    # ==========================================
    with tabs[1]:
        st.subheader("Practice Day Stress & Strain Metrics")
        if practice_sessions:
            sel_prac = st.selectbox("Select Target Practice Session", practice_sessions, key="sel_prac_tab1")
            prac_data = df_filtered[df_filtered['Session_Name'] == sel_prac]
            if not prac_data.empty:
                fig_prac = px.bar(prac_data, x="Name", y="Player Load", color="Position", title=f"Player Load Spread - {sel_prac}", color_discrete_sequence=px.colors.qualitative.Safe)
                fig_prac.update_layout(template="simple_white", height=300)
                st.plotly_chart(fig_prac, use_container_width=True, config=LOCKED_CONFIG)
                st.dataframe(prac_data[['Name', 'Position', 'Player Load', 'Total Jumps', 'Duration']], use_container_width=True, hide_index=True)
        else:
            st.info("No practice session items indexed inside chosen season parameters.")

    # ==========================================
    # --- TAB 2: DAILY COMBINED SCORES ---------
    # ==========================================
    with tabs[2]:
        st.subheader("Team Combined Structural Load Profiles")
        if not df_filtered.empty:
            team_daily = df_filtered.groupby(['Date', 'Session_Name'])[['Player Load', 'Total Jumps']].sum().reset_index().sort_values('Date', ascending=False)
            fig_comb = px.line(team_daily, x="Date", y="Player Load", markers=True, title="Total Squad Volumetric Load Trajectory", color_discrete_sequence=["#FF8200"])
            fig_comb.update_layout(template="simple_white", height=280)
            st.plotly_chart(fig_comb, use_container_width=True, config=LOCKED_CONFIG)
            st.dataframe(team_daily, use_container_width=True, hide_index=True)
        else:
            st.info("Awaiting structural dataset vectors.")

    # ==========================================
    # --- TAB 3: SPRING MAX VS DAILY COMBINED ---
    # ==========================================
    with tabs[3]:
        st.subheader("Current Daily Outputs Compared to Historical Season Maximums")
        if not df_filtered.empty:
            pos_maxes = df_filtered.groupby('Position')[['Player Load', 'Total Jumps']].max().rename(columns={'Player Load':'Max Load', 'Total Jumps':'Max Jumps'})
            st.markdown("### Position Peak References")
            st.dataframe(pos_maxes.reset_index(), use_container_width=True, hide_index=True)
            
            fig_max_comp = px.scatter(df_filtered, x="Total Jumps", y="Player Load", color="Position", size="Duration", hover_data=["Name", "Session_Name"], title="Daily Session Output Distribution relative to Max Volume Thresholds")
            fig_max_comp.update_layout(template="simple_white", height=320)
            st.plotly_chart(fig_max_comp, use_container_width=True, config=LOCKED_CONFIG)
        else:
            st.info("No timeline threshold indicators populated.")

    # ==========================================
    # --- TAB 4: PRACTICE HISTORY --------------
    # ==========================================
    with tabs[4]:
        st.subheader("Historical Training Trend Visualizations")
        if not df_filtered.empty:
            sel_ath_hist = st.selectbox("Select Athlete for Historical Inquiries", master_athlete_list, key="sel_ath_tab4")
            ath_hist = df_filtered[df_filtered['Name'] == sel_ath_hist].sort_values('Date')
            
            if not ath_hist.empty:
                fig_hist = make_subplots(specs=[[{"secondary_y": True}]])
                fig_hist.add_trace(go.Bar(x=ath_hist['Date'], y=ath_hist['Player Load'], name="Player Load", marker_color='#4895DB'), secondary_y=False)
                fig_hist.add_trace(go.Scatter(x=ath_hist['Date'], y=ath_hist['Total Jumps'], name="Total Jumps", mode='lines+markers', line=dict(color='#FF8200', width=2.5)), secondary_y=True)
                fig_hist.update_layout(title=f"Training Load Accumulation Curve: {sel_ath_hist}", template="simple_white", height=300, legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_hist, use_container_width=True, config=LOCKED_CONFIG)
            else:
                st.info("No recorded historical logs discovered for profile target.")
        else:
            st.info("Historical metrics framework requires active tracking rows.")

    # ==========================================
    # --- TAB 5: MATCH V. PRACTICE -------------
    # ==========================================
    with tabs[5]:
        st.subheader("Neuromuscular Output Profiling: Competitive vs. Practice Sessions")
        if not df_filtered.empty:
            fig_box_comp = px.box(df_filtered, x="Session_Type", y="Player Load", color="Position", points="all", title="Player Load Intensity Spreads by Structural Session Variant", color_discrete_sequence=px.colors.qualitative.Safe)
            fig_box_comp.update_layout(template="simple_white", height=320)
            st.plotly_chart(fig_box_comp, use_container_width=True, config=LOCKED_CONFIG)
            
            type_means = df_filtered.groupby(['Position', 'Session_Type'])[['Player Load', 'Total Jumps']].mean().reset_index()
            st.dataframe(type_means, use_container_width=True, hide_index=True)
        else:
            st.info("Awaiting workload structural entries.")

    # ==========================================
    # --- TAB 6: MATCH SUMMARY -----------------
    # ==========================================
    with tabs[6]:
        st.subheader("Competitive Match Engine Performance Synthetics")
        if not match_filtered.empty:
            match_sessions = match_filtered['Session_Name'].unique().tolist()
            sel_match = st.selectbox("Select Competitive Matrix Frame", match_sessions, key="sel_match_tab6")
            m_data = match_filtered[match_filtered['Session_Name'] == sel_match]
            
            fig_match = px.bar(m_data, x="Name", y="Player Load", color="Position", title=f"Competitive Match Breakdown: {sel_match}", color_discrete_sequence=["#FF8200", "#4895DB"])
            fig_match.update_layout(template="simple_white", height=300)
            st.plotly_chart(fig_match, use_container_width=True, config=LOCKED_CONFIG)
            st.dataframe(m_data[['Name', 'Position', 'Player Load', 'Total Jumps']], use_container_width=True, hide_index=True)
        else:
            st.info("No match tracking items indexed inside data parameters for this season.")

    # ==========================================
    # --- TAB 7: POSITION ANALYSIS -------------
    # ==========================================
    with tabs[7]:
        st.subheader("Positional Workload Benchmarking Matrix")
        if not df_filtered.empty:
            # Shift explicitly to Position Max values per business logic overrides
            pos_analytics = df_filtered.groupby('Position')[['Player Load', 'Total Jumps', 'Jump Load']].max().reset_index()
            st.markdown("### ⚡ Positional Benchmark References (Max Values)")
            st.dataframe(pos_analytics, use_container_width=True, hide_index=True)
            
            fig_pos_scatter = px.scatter(df_filtered, x="Player Load", y="Total Jumps", color="Position", marginal_x="box", marginal_y="box", title="Positional Scatter Densities (Max Scaling Context)")
            fig_pos_scatter.update_layout(template="simple_white", height=340)
            st.plotly_chart(fig_pos_scatter, use_container_width=True, config=LOCKED_CONFIG)
        else:
            st.info("Positional breakdown matrix requires streaming dataset rows.")

    # ==========================================
    # --- TAB 8: PHASE ANALYSIS ----------------
    # ==========================================
    with tabs[8]:
        st.subheader("Drill Phase Specific Load Intensity Frameworks")
        if 'Phase' in phase_filtered.columns and not phase_filtered.empty:
            phase_summary = phase_filtered.groupby('Phase')[['Player Load', 'Total Jumps', 'Duration']].mean().reset_index()
            st.dataframe(phase_summary, use_container_width=True, hide_index=True)
            
            fig_phase = px.bar(phase_summary, x="Phase", y="Player Load", text_auto='.1f', title="Average Player Load Yielded per Individual Tactical Phase Block", color_discrete_sequence=["#4895DB"])
            fig_phase.update_layout(template="simple_white", height=300)
            st.plotly_chart(fig_phase, use_container_width=True, config=LOCKED_CONFIG)
        else:
            st.info("Tactical Drill Phase logs absent or columns unmapped for current configuration arrays.")

    # ==========================================
    # --- TAB 9: PRACTICE PLANNER --------------
    # ==========================================
    with tabs[9]:
        st.subheader("Microcycle Tactical Practice Load Modeling Simulator")
        st.markdown("Calculate projected workout impacts using verified historical parameters.")
        
        plan_c1, plan_c2 = st.columns(2)
        with plan_c1:
            planned_duration = st.slider("Target Planned Practice Duration (Minutes)", 30, 180, 90, step=5)
            intensity_scalar = st.select_slider("Projected Training Intensity Target", options=["Low Recovery", "Moderate Development", "High Game Engine Simulation"], value="Moderate Development")
        
        scalar_map = {"Low Recovery": 3.8, "Moderate Development": 5.2, "High Game Engine Simulation": 7.1}
        modeled_rate = scalar_map[intensity_scalar]
        projected_load = planned_duration * modeled_rate
        
        with plan_c2:
            st.markdown("#### Projected Target Outcomes")
            st.metric("Modeled Target Player Load", f"{projected_load:.1f} Units")
            st.metric("Estimated Minute Density Accumulation Rate", f"{modeled_rate} Load/Min")
            
        st.info("💡 Note: This simulation models physical stress behaviors by matching baseline position averages to chronological session boundaries.")

    # ==========================================
    # --- TAB 10: SPRING V. SUMMER -------------
    # ==========================================
    with tabs[10]:
        st.subheader("Macrocycle Chronological Variance: Spring vs. Summer Structural Baselines")
        if not df.empty:
            macro_comp = df.groupby(['Season', 'Position'])[['Player Load', 'Total Jumps']].mean().reset_index()
            
            fig_macro = px.bar(macro_comp, x="Position", y="Player Load", color="Season", barmode="group", title="Volumetric Seasonal Baseline Deviations by Squad Unit Placement", color_discrete_map={'Spring': '#4895DB', 'Summer': '#FF8200'})
            fig_macro.update_layout(template="simple_white", height=320)
            st.plotly_chart(fig_macro, use_container_width=True, config=LOCKED_CONFIG)
            st.dataframe(macro_comp, use_container_width=True, hide_index=True)
        else:
            st.info("Upstream chronological metrics are empty.")
