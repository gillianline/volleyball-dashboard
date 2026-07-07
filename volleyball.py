import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

# --- INITIALIZE SESSION STATE ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

# --- PASSWORD PROTECTION ---
def check_password():
    if st.session_state["password_correct"]:
        return True
        
    def password_entered():
        # Safeguard fallback if secrets aren't deployment-ready yet
        secret_pass = st.secrets.get("PASSWORD", "VolsVB2026")
        if st.session_state["password_input"] == secret_pass:
            st.session_state["password_correct"] = True
            st.session_state["password_error"] = False
        else:
            st.session_state["password_correct"] = False
            st.session_state["password_error"] = True

    st.markdown('<div style="max-width: 400px; margin: 50px auto;">', unsafe_allow_html=True)
    st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password_input")
    
    if st.session_state.get("password_error", False):
        st.error("❌ Incorrect Password. Please try again.")
    st.markdown('</div>', unsafe_allow_html=True)
    return False

if check_password():
    # --- CUSTOM DESIGN MATRIX CSS ---
    st.markdown("""
        <style>
        /* Global Brand Overrides */
        .stApp { background-color: #FFFFFF; color: #1D1D1F; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
        th, td { text-align: center !important; vertical-align: middle !important; }
        [data-testid="stMetricValue"] { font-size: 22px; font-weight: 700; color: #FF8200; }
        
        /* Scout Tables Styling */
        .scout-table { width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 15px; }
        .scout-table th { background-color: #4895DB; color: white; padding: 8px 6px; border-bottom: 3px solid #FF8200; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
        .scout-table td { padding: 8px 6px; border-bottom: 1px solid #E5E5E7; font-size: 12px; color: #1D1D1F; font-weight: 500; }
        .bg-highlight-red { background-color: #FFE6E6 !important; font-weight: 800; color: #B30000 !important; }
        .arrow-red { color: #B30000 !important; font-weight: 900; margin-left: 3px; font-size: 13px; }
        
        /* UI Components */
        .player-photo-large { border-radius: 50%; width: 160px; height: 160px; object-fit: cover; border: 5px solid #FF8200; margin: 0 auto; display: block; boxShadow: 0px 4px 10px rgba(0,0,0,0.1); }
        .score-box { padding: 14px; border-radius: 12px; font-size: 28px; font-weight: 800; min-width: 85px; color: #FFFFFF; text-align: center; line-height: 1.1; display: inline-block; }
        .info-box { background-color: #F8F9FA; border-left: 5px solid #FF8200; padding: 10px 12px; margin-top: 8px; font-size: 11px; color: #1D1D1F; font-weight: 600; line-height: 1.4; border-radius: 0 6px 6px 0; }
        .section-header { font-size: 16px; font-weight: 800; color: #4895DB; border-bottom: 2px solid #FF8200; margin-top: 25px; margin-bottom: 15px; padding-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* Responsive Fixes to avoid bleeding */
        div[data-testid="stHorizontalBlock"] { gap: 1.5rem !important; }
        </style>
        """, unsafe_allow_html=True)

    # --- GRADIENT UTILS ---
    def get_flipped_gradient(score):
        try:
            score = float(score)
            if pd.isna(score): return "#808080" 
        except (ValueError, TypeError):
            return "#808080" 
        # Low strain = green, Med strain = gold, Heavy strain = red
        return "#2D5A27" if score <= 40 else "#D4A017" if score <= 70 else "#A52A2A"

    # --- COMPREHENSIVE SANITIZATION & CACHING ---
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

        # Safely extract URLs from Streamlit Secrets
        g_url = st.secrets.get("GOOGLE_SHEET_URL", "")
        m_url = st.secrets.get("MATCHES_SHEET_URL", "")
        c_url = st.secrets.get("CMJ_SHEET_URL", "")
        a_url = st.secrets.get("ASH_SHEET_URL", "")
        e_url = st.secrets.get("ER_SHEET_URL", "")
        p_url = st.secrets.get("PHASES_SHEET_URL", "")

        # Safe Fallback Generator to guarantee execution with zero layout crashing
        def read_or_mock(url, columns):
            try:
                if url: return pd.read_csv(url)
            except Exception:
                pass
            return pd.DataFrame(columns=columns)

        df = read_or_mock(g_url, ['Name', 'Date', 'Activity', 'Position', 'PhotoURL', 'Player Load', 'Total Jumps', 'Estimated Distance (y)', 'Explosive Efforts', 'Duration'])
        match_df = read_or_mock(m_url, ['Name', 'Date', 'Activity', 'Position', 'Player Load', 'Total Jumps'])
        cmj_df = read_or_mock(c_url, ['Athlete', 'Test Date', 'Jump Height (Imp-Mom) [cm]', 'RSI-modified [m/s]', 'Week'])
        ash_df = read_or_mock(a_url, ['Athlete', 'Date', 'Isometric Type', 'Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force [N] (Asym)(%)'])
        er_df = read_or_mock(e_url, ['Athlete', 'Date', 'L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)'])
        phase_df = read_or_mock(p_url, ['Date', 'Phases', 'Activity'])

        # Data Frame Standardization Pipeline
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

        phase_df.columns = phase_df.columns.str.strip()
        phase_df.rename(columns={'Phases': 'Phase'}, errors='ignore', inplace=True)
        phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')

        return df.dropna(subset=['Date']), match_df, cmj_df, ash_df, er_df, phase_df

    LOCKED_CONFIG = {'staticPlot': False, 'displayModeBar': False}

    # --- PROCESS DATA ENVIRONMENT ---
    df, match_df, cmj_df, ash_df, er_df, phase_df = load_all_data()

    # --- SIDEBAR CONTROL PANEL ---
    st.sidebar.markdown("### 🎛️ Global Filters")
    selected_season = st.sidebar.radio("Active Season Dataset", ["Spring", "Summer"], index=1, key="global_season_toggle")
    
    # Filter datasets dynamically based on season selection
    df_filtered = df[df['Season'] == selected_season].copy()
    match_filtered = match_df[match_df['Season'] == selected_season].copy()
    cmj_filtered = cmj_df[cmj_df['Season'] == selected_season].copy()
    ash_filtered = ash_df[ash_df['Season'] == selected_season].copy()
    er_filtered = er_df[er_df['Season'] == selected_season].copy()

    st.sidebar.info(f"💡 Dashboard context bound strictly to the {selected_season} Season.")

    # Generate Safe Global Lookup Indexes
    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
    master_athlete_list = sorted(list(set(df_filtered['Name'].unique()) | set(cmj_filtered['Name'].unique()) | set(ash_filtered['Name'].unique()) | set(er_filtered['Name'].unique())))
    if not master_athlete_list: master_athlete_list = ["No Athletes Available"]
    
    session_list = df_filtered[df_filtered['Session_Name'].notna()].sort_values('Date', ascending=False)['Session_Name'].unique().tolist()

    # --- BRAND BANNER ---
    st.markdown('<div style="text-align: center; margin-top: 5px; margin-bottom: 20px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tennessee_Lady_Volunteers_logo.svg/1280px-Tennessee_Lady_Volunteers_logo.svg.png" width="90"><div style="color: #FF8200; font-size: 1.8rem; font-weight: 900; margin-top: 5px; letter-spacing: 0.5px;">LADY VOLS VOLLEYBALL PERFORMANCE</div></div>', unsafe_allow_html=True)

    # --- APPLICATION TABS MAP ---
    tabs = st.tabs([
        "Individual Profile", "Practice Scores", "Daily Combined Scores", 
        "Spring Max vs Daily Combined", "Practice History", "Match v. Practice", 
        "Match Summary", "Position Analysis", "Phase Analysis", "Practice Planner", "Spring v. Summer"
    ])

    # ==========================================
    # --- TAB 0: INDIVIDUAL PROFILE ------------
    # ==========================================
    with tabs[0]:
        if not df_filtered.empty or not cmj_filtered.empty:
            target_date_str = "2026-04-04"
            tournament_label = "GT Spring Tournament 4-4-26"
            
            clean_session_list_prof = [tournament_label] + [s for s in session_list if s != tournament_label]
            
            # Isolated Controls Layout Row (Prevents Component Bleeding)
            ctrl_c1, ctrl_c2 = st.columns(2)
            with ctrl_c1:
                selected_session_prof = st.selectbox("Session Window Selection", clean_session_list_prof, index=0, key="nav_sel_prof")
            with ctrl_c2:
                selected_athlete_prof = st.selectbox("Athlete Profile Target", master_athlete_list, index=0, key="nav_ath_prof")
            
            # Parse Active Context Elements
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

            # Fallback Matrix Architecture if Data Record is Missing
            if p_row.empty:
                meta_lookup = df_filtered[df_filtered['Name'] == selected_athlete_prof]
                pos_val = meta_lookup['Position'].iloc[0] if not meta_lookup.empty else "N/A"
                photo_val = meta_lookup['PhotoURL'].iloc[0] if not meta_lookup.empty else "https://www.w3schools.com/howto/img_avatar.png"
                p_meta = pd.Series({'Name': selected_athlete_prof, 'Position': pos_val, 'PhotoURL': photo_val})
                p_row = pd.Series({m: 0.0 for m in all_metrics})
                p_row['Name'] = selected_athlete_prof

            # Calculate Rolling 30-Day Baselines
            p_full_prof = df_filtered[df_filtered['Name'] == selected_athlete_prof]
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
                r_html_prof += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}%</td></tr>"

            sc_prof = math.ceil(t_grade_prof / c_metrics_prof) if c_metrics_prof > 0 else 0

            # --- PROFILE LAYOUT MATRIX ---
            c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
            with c1:
                st.markdown(f'<div style="text-align:center; padding-top:10px;"><img src="{p_meta.get("PhotoURL", "https://www.w3schools.com/howto/img_avatar.png")}" class="player-photo-large"></div><h4 style="text-align:center; margin-top:10px; margin-bottom: 2px;">{p_meta.get("Name", selected_athlete_prof)}</h4><p style="text-align:center; color:grey; font-weight:700; font-size:13px;">Position: {p_meta.get("Position","N/A")}</p>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<table class="scout-table"><thead><tr><th>Metric Target</th><th>Today Total</th><th>30d Max Day</th><th>Grade %</th></tr></thead><tbody>{r_html_prof}</tbody></table>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; min-height:200px;"><div class="score-box" style="background-color:{get_flipped_gradient(sc_prof)};">{sc_prof}</div><p style="text-align:center; font-weight:bold; color:#7F8C8D; margin-top:8px; font-size:11px; letter-spacing:0.5px;">STRAIN GRADE</p></div>', unsafe_allow_html=True)
            
            st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
            
            # --- SUB-BLOCK 1: CMJ PROFILE ---
            st.markdown('<h5 style="color:#4895DB; font-weight:800; margin-bottom:10px;">LOWER BODY CAPACITY: COUNTERMOVEMENT JUMP</h5>', unsafe_allow_html=True)
            jc1, jc2 = st.columns([1.8, 3.2])
            p_cmj_hist = cmj_filtered[(cmj_filtered['Name'] == selected_athlete_prof) & (cmj_filtered['Test Date'] <= curr_date_prof)].sort_values('Test Date')
            cmj_col, rsi_col = 'Jump Height (Imp-Mom) [cm]', 'RSI-modified [m/s]'

            with jc1:
                baseline_cmj = p_cmj_hist.head(1) if selected_season == 'Summer' else cmj_filtered[(cmj_filtered['Name'] == selected_athlete_prof) & (cmj_filtered['Week'] == 4)]
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
                        st.markdown(f'<div class="score-box" style="background-color:{col_h}; width:100%; font-size:18px; padding:10px;">{cur_h:.1f} cm<span style="font-size:9px; display:block; font-weight:bold; margin-top:2px;">CMJ HEIGHT</span></div>', unsafe_allow_html=True)
                    with sub_c2:
                        st.markdown(f'<div class="score-box" style="background-color:{col_rsi}; width:100%; font-size:18px; padding:10px;">{cur_rsi:.2f}<span style="font-size:9px; display:block; font-weight:bold; margin-top:2px;">RSI MODIFIED</span></div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="info-box"><b>% Delta from Base:</b> CMJ: {p_diff_h:+.1f}% | RSI: {p_diff_rsi:+.1f}%<br><b>Baseline Config:</b> Baseline CMJ: {base_h:.1f}cm | Baseline RSI: {base_rsi:.2f}</div>', unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Baseline metrics missing for active profile timeline.")

            with jc2:
                if not p_cmj_hist.empty and cmj_col in p_cmj_hist.columns:
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[cmj_col], name="Jump Height (cm)", mode='lines+markers', line=dict(color='#FF8200', width=3)), secondary_y=False)
                    fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[rsi_col], name="RSI Modified", mode='lines+markers', line=dict(color='#4895DB', dash='dot', width=2)), secondary_y=True)
                    fig.update_layout(height=150, margin=dict(l=5, r=5, t=10, b=5), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0), template="simple_white")
                    st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG, key="cmj_profile_chart")

            # --- SUB-BLOCK 2: ASH SHOULDER CAPACITY ---
            st.markdown('<h5 style="color:#4895DB; font-weight:800; margin-top:20px; margin-bottom:10px;">UPPER BODY CAPACITY: ASH SHOULDER TEST (ISO I)</h5>', unsafe_allow_html=True)
            p_ash_all = ash_filtered[(ash_filtered['Name'] == selected_athlete_prof) & (ash_filtered['Test Date'] <= curr_date_prof)].sort_values('Test Date')

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
                        st.markdown(f'<div class="score-box" style="background-color:{color_ash_l}; width:100%; font-size:18px; padding:10px;">{li:.0f} N<span style="font-size:9px; display:block; font-weight:bold; margin-top:2px;">LEFT PEAK FORCE</span></div>', unsafe_allow_html=True)
                    with sub_ac2:
                        st.markdown(f'<div class="score-box" style="background-color:{color_ash_r}; width:100%; font-size:18px; padding:10px;">{ri:.0f} N<span style="font-size:9px; display:block; font-weight:bold; margin-top:2px;">RIGHT PEAK FORCE</span></div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="info-box"><b>Peak Force Asymmetry:</b> {asym_i:+.1f}%<br><b>Force Shift from Base:</b> Left: {pct_l:+.1f}% | Right: {pct_r:+.1f}%</div>', unsafe_allow_html=True)

                with ac2:
                    p_ash_i_only = p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)]
                    if not p_ash_i_only.empty:
                        fig_ash = go.Figure()
                        fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (L)'], name="Left Peak Force", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                        fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (R)'], name="Right Peak Force", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                        fig_ash.update_layout(height=150, margin=dict(l=5, r=5, t=10, b=5), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0), template="simple_white")
                        st.plotly_chart(fig_ash, use_container_width=True, config=LOCKED_CONFIG, key="ash_profile_chart")
            else:
                st.info("ℹ️ No historical Isometric Shoulder Force metrics logged for player timeline.")

            # --- SUB-BLOCK 3: EXTERNAL ROTATION ROM ---
            st.markdown('<h5 style="color:#4895DB; font-weight:800; margin-top:20px; margin-bottom:10px;">ROTATOR CUFF INTEGRITY: ER RANGE OF MOTION</h5>', unsafe_allow_html=True)
            p_er_hist = er_filtered[(er_filtered['Name'] == selected_athlete_prof) & (er_filtered['Test Date'] <= curr_date_prof)].sort_values('Test Date')

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
                        st.markdown(f'<div class="score-box" style="background-color:{color_er_l}; width:100%; font-size:18px; padding:10px;">{cur_l_rom:.1f}°<span style="font-size:9px; display:block; font-weight:bold; margin-top:2px;">LEFT MAX ROM</span></div>', unsafe_allow_html=True)
                    with sub_ec2:
                        st.markdown(f'<div class="score-box" style="background-color:{color_er_r}; width:100%; font-size:18px; padding:10px;">{cur_r_rom:.1f}°<span style="font-size:9px; display:block; font-weight:bold; margin-top:2px;">RIGHT MAX ROM</span></div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="info-box"><b>ROM Structural Asymmetry:</b> {cur_asym_rom:+.1f}%</div>', unsafe_allow_html=True)

                with ec2:
                    fig_er = go.Figure()
                    fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['L Max ROM (°)'], name="Left Max ROM", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                    fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['R Max ROM (°)'], name="Right Max ROM", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                    fig_er.update_layout(height=150, margin=dict(l=5, r=5, t=10, b=5), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0), template="simple_white")
                    st.plotly_chart(fig_er, use_container_width=True, config=LOCKED_CONFIG, key="er_profile_chart")
            else:
                st.info("ℹ️ No historical Rotator Cuff ROM records found for selected athlete.")
        else:
            st.warning("⚠️ Active season metrics are empty. Connect valid structured live tables.")

    # ==========================================
    # --- TABS 1 TO 10: ISOLATED PLACEHOLDERS --
    # ==========================================
    remaining_tabs_map = [
        "Practice Scores", "Daily Combined Scores", "Spring Max vs Daily Combined", 
        "Practice History", "Match v. Practice", "Match Summary", 
        "Position Analysis", "Phase Analysis", "Practice Planner", "Spring v. Summer"
    ]

    for idx, tab_name in enumerate(remaining_tabs_map, start=1):
        with tabs[idx]:
            st.subheader(f"📊 {tab_name}")
            
            # Sub-Tab Header Block
            st.markdown(f"""
                <div class="info-box" style="margin-bottom: 20px;">
                    <b>Analysis Context Layer:</b> System engine currently routing <b>{selected_season} Season</b> matrix data. Adjust parameters in the sidebar to sync alternative performance blocks.
                </div>
                """, unsafe_allow_html=True)
            
            # Isolated Analytics Layout Row
            with st.container():
                sub_col1, sub_col2 = st.columns([3, 2])
                with sub_col1:
                    st.markdown(f"##### {tab_name} Group Summary Matrix")
                    # Safe Dynamic DataFrame Render Block
                    if not df_filtered.empty:
                        summary_view = df_filtered.groupby('Position')[['Player Load', 'Total Jumps', 'Duration']].mean().reset_index()
                        st.dataframe(summary_view, use_container_width=True, hide_index=True)
                    else:
                        st.info("Awaiting structural upstream CSV data to map analytics table framework.")
                        
                with sub_col2:
                    st.markdown("##### Season Load Spread")
                    if not df_filtered.empty:
                        fig_placeholder = px.box(df_filtered, x="Position", y="Player Load", color_discrete_sequence=["#FF8200"])
                        fig_placeholder.update_layout(height=180, margin=dict(l=5, r=5, t=5, b=5), template="simple_white")
                        st.plotly_chart(fig_placeholder, use_container_width=True, config=LOCKED_CONFIG, key=f"p_box_{idx}")
                    else:
                        st.info("Chart engine offline until dataframe records exist.")
