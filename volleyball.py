import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

# --- SAFE, CONTANCE-ONLY CSS (No App Background Overrides) ---
st.markdown("""
    <style>
    th, td { text-align: center !important; }
    [data-testid="stMetricValue"] { font-size: 24px; }
    
    /* Clean, non-breaking custom table styling */
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; }
    .scout-table th { background-color: #4895DB; color: white; padding: 6px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 11px; text-transform: uppercase; }
    .scout-table td { padding: 6px; border-bottom: 1px solid #F5F5F7; font-size: 11px; }
    .bg-highlight-red { background-color: #ffcccc !important; font-weight: 900; }
    .arrow-red { color: #b30000 !important; font-weight: 900; margin-left: 4px; }
    
    /* Percent-scaled components to ensure zero layout bleeding */
    .score-box-native { padding: 12px; border-radius: 8px; font-size: 24px; font-weight: 800; color: #FFFFFF; text-align: center; width: 100%; max-width: 120px; margin: 0 auto; }
    .info-box-native { background-color: #f8f9fa; border-left: 5px solid #FF8200; padding: 10px; margin-top: 5px; font-size: 11px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORD PROTECTION ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("Incorrect Password")
        return False
    else:
        return True

if check_password():
    
    def get_flipped_gradient(score):
        try:
            score = float(score)
            if pd.isna(score): return "#808080" 
        except (ValueError, TypeError):
            return "#808080" 
        return "#2D5A27" if score <= 40 else "#D4A017" if score <= 70 else "#A52A2A"

    def clean_val(val, default=0.0):
        try:
            if pd.isna(val) or str(val).strip() in ["", "-", "N/A", "nan", "None"]: return default
            return float(val)
        except:
            return default
        
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

        df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
        match_df = pd.read_csv(st.secrets["MATCHES_SHEET_URL"])
        
        for frame in [df, match_df]:
            frame = heavy_sanitize(frame)
            frame['Date'] = pd.to_datetime(frame['Date'], errors='coerce')
            frame['Session_Name'] = frame['Activity'].fillna(frame['Date'].dt.strftime('%m/%d/%Y'))
            frame['Position'] = frame.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
            frame['PhotoURL'] = frame.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
            frame['Season'] = frame['Date'].apply(assign_season)

        cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
        cmj_df.columns = cmj_df.columns.str.strip()
        cmj_df.rename(columns={'Athlete': 'Name'}, inplace=True)
        cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
        cmj_df['Season'] = cmj_df['Test Date'].apply(assign_season)

        try:
            ash_df = pd.read_csv(st.secrets["ASH_SHEET_URL"])
            ash_df.columns = ash_df.columns.str.strip()
            ash_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
            ash_df['Test Date'] = pd.to_datetime(ash_df['Test Date'], errors='coerce')
            for col in ['Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force [N] (Asym)(%)']:
                if col in ash_df.columns:
                    ash_df[col] = pd.to_numeric(ash_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
            ash_df['Season'] = ash_df['Test Date'].apply(assign_season)
        except:
            ash_df = pd.DataFrame(columns=['Name', 'Test Date', 'Isometric Type', 'Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)', 'Peak Vertical Force [N] (Asym)(%)', 'Season'])

        try:
            er_df = pd.read_csv(st.secrets["ER_SHEET_URL"])
            er_df.columns = er_df.columns.str.strip()
            er_df.rename(columns={'Athlete': 'Name', 'Date': 'Test Date'}, inplace=True)
            er_df['Test Date'] = pd.to_datetime(er_df['Test Date'], errors='coerce')
            for col in ['L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)']:
                if col in er_df.columns:
                    er_df[col] = pd.to_numeric(er_df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0.0)
            er_df['Season'] = er_df['Test Date'].apply(assign_season)
        except:
            er_df = pd.DataFrame(columns=['Name', 'Test Date', 'Movement', 'L Max ROM (°)', 'R Max ROM (°)', 'ROM Asymmetry (%)', 'Season'])

        phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
        phase_df = heavy_sanitize(phase_df)
        phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
        date_season_map = df.drop_duplicates('Date').set_index('Date')['Season'].to_dict()
        phase_df['Season'] = phase_df['Date'].map(date_season_map).fillna('Spring')
        
        return df.dropna(subset=['Date']), match_df.dropna(subset=['Date']), cmj_df, phase_df, ash_df, er_df

    LOCKED_CONFIG = {'staticPlot': False, 'displayModeBar': False}

    raw_df, raw_match_df, cmj_df, phase_df, ash_df, er_df = load_all_data()

    st.sidebar.markdown("### Season Panel")
    selected_season = st.sidebar.radio("Select Season", ["Spring", "Summer"], index=1, key="global_season_toggle")
    
    df = raw_df[raw_df['Season'] == selected_season].copy()
    match_df = raw_match_df[raw_match_df['Season'] == selected_season].copy()
    cmj_df = cmj_df[cmj_df['Season'] == selected_season].copy()
    ash_df = ash_df[ash_df['Season'] == selected_season].copy()
    er_df = er_df[er_df['Season'] == selected_season].copy()
    phase_df = phase_df[phase_df['Season'] == selected_season].copy()
    
    all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
    
    st.title("LADY VOLS VOLLEYBALL PERFORMANCE")

    tabs = st.tabs(["Individual Profile", "Practice Scores", "Daily Combined Scores", "Spring Max vs Daily Combined", "Practice History", "Match v. Practice", "Match Summary", "Position Analysis", "Phase Analysis", "Practice Planner", "Spring v. Summer"])
    
    master_athlete_list = sorted(list(set(df['Name'].unique()) | set(cmj_df['Name'].unique()) | set(ash_df['Name'].unique()) | set(er_df['Name'].unique())))
    session_list = df[df['Session_Name'].notna()].sort_values('Date', ascending=False)['Session_Name'].unique().tolist()

    # ==========================================
    # --- TAB 0: INDIVIDUAL PROFILE ------------
    # ==========================================
    with tabs[0]:
        target_date_str = "2026-04-04"
        tournament_label = "GT Spring Tournament 4-4-26"
        
        clean_session_list_prof = []
        tourney_added_prof = False
        for s in session_list:
            s_date_series = df[df['Session_Name'] == s]['Date']
            if not s_date_series.empty:
                s_date = s_date_series.dt.strftime('%Y-%m-%d').iloc[0]
                if s_date == target_date_str:
                    if not tourney_added_prof:
                        clean_session_list_prof.append(tournament_label)
                        tourney_added_prof = True
                else:
                    clean_session_list_prof.append(s)
            else:
                clean_session_list_prof.append(s)
        if not clean_session_list_prof:
            clean_session_list_prof = [tournament_label]

        c_prof1, c_prof2 = st.columns(2)
        with c_prof1:
            selected_session_prof = st.selectbox("Session Selection", clean_session_list_prof, index=0, key="nav_sel_prof")
        with c_prof2:
            selected_athlete_prof = st.selectbox("Athlete Selection", master_athlete_list, key="nav_ath_prof")

        if selected_session_prof == tournament_label:
            curr_date_prof = pd.to_datetime(target_date_str)
            p_session_data = df[(df['Name'] == selected_athlete_prof) & (df['Date'] == curr_date_prof)].copy()
            p_row = p_session_data.groupby(['Name', 'Position', 'PhotoURL', 'Date']).sum(numeric_only=True).reset_index().iloc[0] if not p_session_data.empty else pd.Series()
            p_meta = p_session_data.iloc[0] if not p_session_data.empty else pd.Series()
        else:
            p_session_data = df[(df['Name'] == selected_athlete_prof) & (df['Session_Name'] == selected_session_prof)]
            p_row = p_session_data.iloc[0] if not p_session_data.empty else pd.Series()
            curr_date_prof = p_row['Date'] if not p_row.empty else None
            p_meta = p_row

        if p_row.empty:
            curr_date_prof = pd.to_datetime(target_date_str) if selected_session_prof == tournament_label else pd.to_datetime(df['Date'].max() if not df.empty else "2026-01-01")
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
        r_html_prof = ""; t_grade_prof = 0; c_metrics_prof = 0

        for k in filtered_metrics_prof:
            val = clean_val(p_row.get(k, 0.0))
            mx = clean_val(lb_prof[k].max() if (not lb_prof.empty and k in lb_prof.columns and lb_prof[k].max() > 0) else 1.0)
            avg = clean_val(lb_prof[k].mean() if (not lb_prof.empty and k in lb_prof.columns and lb_prof[k].mean() > 0) else 1.0)
            g = math.ceil((val / mx) * 100) if mx > 0 else 0
            t_grade_prof += g; c_metrics_prof += 1
            diff = (val - avg) / avg if avg != 0 else 0
            h_class = "class='bg-highlight-red'" if abs(diff) > 0.10 else ""
            arr_val = f"<span class='arrow-red'>{'↑' if diff > 0.10 else '↓'}</span>" if abs(diff) > 0.10 else ""
            r_html_prof += f"<tr><td>{k}</td><td {h_class}>{val:.1f} {arr_val}</td><td>{mx:.1f}</td><td>{g}</td></tr>"

        sc_prof = math.ceil(t_grade_prof / c_metrics_prof) if c_metrics_prof > 0 else 0

        # Primary Block (Responsive Percentages Used)
        c1, c2, c3 = st.columns([1.5, 2.5, 1.0])
        with c1:
            st.image(p_meta.get("PhotoURL", "https://www.w3schools.com/howto/img_avatar.png"), use_container_width=True)
            st.markdown(f"<h3 style='text-align:center; margin:0;'>{p_meta.get('Name', selected_athlete_prof)}</h3>", unsafe_allow_html=True)
        with c2:
            st.markdown(f'<table class="scout-table"><thead><tr><th>Metric</th><th>Today Total</th><th>30d Max Day</th><th>Grade</th></tr></thead><tbody>{r_html_prof}</tbody></table>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="score-box-native" style="background-color:{get_flipped_gradient(sc_prof)};">{sc_prof}</div><p style="text-align:center; font-weight:bold; color:grey; margin-top:5px; font-size:12px;">SESSION SCORE</p>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Weekly Readiness Profile</div>', unsafe_allow_html=True)
        
        # --- BLOCK 1: LOWER BODY JUMP PROFILE (CMJ) ---
        st.markdown('<h4 style="color:#4895DB; font-weight:800; margin: 10px 0 5px 0;">COUNTERMOVEMENT JUMP</h4>', unsafe_allow_html=True)
        jc1, jc2 = st.columns([1.8, 3.2])
        p_cmj_hist = cmj_df[(cmj_df['Name'] == selected_athlete_prof) & (cmj_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
        cmj_col = 'Jump Height (Imp-Mom) [cm]'
        rsi_col = 'RSI-modified [m/s]'

        with jc1:
            baseline_cmj = p_cmj_hist[p_cmj_hist['Season'] == 'Summer'].head(1) if selected_season == 'Summer' else cmj_df[(cmj_df['Name'] == selected_athlete_prof) & (cmj_df['Week'] == 4)]
        
            if not baseline_cmj.empty and not p_cmj_hist.empty:
                base_h = clean_val(baseline_cmj.iloc[-1].get(cmj_col, 0.0))
                base_rsi = clean_val(baseline_cmj.iloc[-1].get(rsi_col, 0.0))
                latest_cmj = p_cmj_hist.iloc[-1]
                cur_h, cur_rsi = clean_val(latest_cmj.get(cmj_col, 0.0)), clean_val(latest_cmj.get(rsi_col, 0.0))
            
                p_diff_h = ((cur_h - base_h) / base_h * 100) if base_h > 0 else 0
                p_diff_rsi = ((cur_rsi - base_rsi) / base_rsi * 100) if base_rsi > 0 else 0
            
                color_h = "#28a745" if cur_h >= base_h else "#dc3545"
                color_rsi = "#28a745" if cur_rsi >= base_rsi else "#dc3545"

                sc1, sc2 = st.columns(2)
                with sc1:
                    st.markdown(f'<div class="score-box-native" style="background-color:{color_h}; font-size:16px;">{cur_h:.1f} cm<br><span style="font-size:9px; font-weight:bold;">CMJ HEIGHT</span></div>', unsafe_allow_html=True)
                with sc2:
                    st.markdown(f'<div class="score-box-native" style="background-color:{color_rsi}; font-size:16px;">{cur_rsi:.2f}<br><span style="font-size:9px; font-weight:bold;">RSI MOD</span></div>', unsafe_allow_html=True)

                st.markdown(f'<div class="info-box-native" style="text-align:center;"><p style="margin:0;"><b>% Change from Base:</b> CMJ: {p_diff_h:+.1f}% | RSI: {p_diff_rsi:+.1f}%</p><p style="margin:0; color:grey;">Base: CMJ: {base_h:.1f} cm | RSI: {base_rsi:.2f}</p></div>', unsafe_allow_html=True)
            else:
                st.warning("No data recorded.")

        with jc2:
            if not p_cmj_hist.empty:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[cmj_col], name="Jump Height", mode='lines+markers', line=dict(color='#FF8200', width=3)), secondary_y=False)
                fig.add_trace(go.Scatter(x=p_cmj_hist['Test Date'], y=p_cmj_hist[rsi_col], name="RSI Modified", mode='lines+markers', line=dict(color='#4895DB', dash='dot', width=2)), secondary_y=True)
                fig.update_layout(height=150, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG, key="cmj_top_chart")

        # --- BLOCK 2: UPPER BODY ISOMETRIC PROFILE (ASH TEST) ---
        st.markdown('<h4 style="color:#4895DB; font-weight:800; margin: 15px 0 5px 0;">ASH SHOULDER: ISO I</h4>', unsafe_allow_html=True)
        p_ash_all = ash_df[(ash_df['Name'] == selected_athlete_prof) & (ash_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
        
        if not p_ash_all.empty:
            ac1, ac2 = st.columns([1.8, 3.2])
            with ac1:
                latest_date_ash = p_ash_all['Test Date'].iloc[-1]
                row_i = p_ash_all[(p_ash_all['Test Date'] == latest_date_ash) & (p_ash_all['Isometric Type'].str.contains('I', case=False, na=False))]
    
                li = clean_val(row_i.iloc[-1]['Peak Vertical Force [N] (L)']) if not row_i.empty else 0.0
                ri = clean_val(row_i.iloc[-1]['Peak Vertical Force [N] (R)']) if not row_i.empty else 0.0
                asym_i = clean_val(row_i.iloc[-1]['Peak Vertical Force [N] (Asym)(%)']) if not row_i.empty else 0.0
    
                baseline_ash = p_ash_all[(p_ash_all['Season'] == 'Summer') & (p_ash_all['Isometric Type'].str.contains('I', case=False, na=False))].head(1) if selected_season == 'Summer' else p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)].head(1)
                base_li = clean_val(baseline_ash.iloc[-1]['Peak Vertical Force [N] (L)']) if not baseline_ash.empty else 0.0
                base_ri = clean_val(baseline_ash.iloc[-1]['Peak Vertical Force [N] (R)']) if not baseline_ash.empty else 0.0
    
                pct_l = ((li - base_li) / base_li * 100) if base_li > 0 else 0
                pct_r = ((ri - base_ri) / base_ri * 100) if base_ri > 0 else 0
    
                color_ash_l = "#28a745" if li >= 100 else "#dc3545"
                color_ash_r = "#28a745" if ri >= 100 else "#dc3545"

                asc1, asc2 = st.columns(2)
                with asc1:
                    st.markdown(f'<div class="score-box-native" style="background-color:{color_ash_l}; font-size:16px;">{li:.0f} N<br><span style="font-size:9px; font-weight:bold;">LEFT</span></div>', unsafe_allow_html=True)
                with asc2:
                    st.markdown(f'<div class="score-box-native" style="background-color:{color_ash_r}; font-size:16px;">{ri:.0f} N<br><span style="font-size:9px; font-weight:bold;">RIGHT</span></div>', unsafe_allow_html=True)

                st.markdown(f'<div class="info-box-native" style="text-align:center;"><p style="margin:0;"><b>Asymmetry:</b> {asym_i:+.1f}% | <b>Base Shift:</b> L: {pct_l:+.1f}% / R: {pct_r:+.1f}%</p></div>', unsafe_allow_html=True)
            with ac2:
                p_ash_i_only = p_ash_all[p_ash_all['Isometric Type'].str.contains('I', case=False, na=False)]
                if not p_ash_i_only.empty:
                    fig_ash = go.Figure()
                    fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (L)'], name="Left Peak Force", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                    fig_ash.add_trace(go.Scatter(x=p_ash_i_only['Test Date'], y=p_ash_i_only['Peak Vertical Force [N] (R)'], name="Right Peak Force", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                    fig_ash.update_layout(height=150, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                    st.plotly_chart(fig_ash, use_container_width=True, config=LOCKED_CONFIG, key="ash_profile_chart")
        else:
            st.info("No ASH shoulder test dataset recorded.")

        # --- BLOCK 3: ROTATOR CUFF EXTERNAL ROTATION ROM ---
        st.markdown('<h4 style="color:#4895DB; font-weight:800; margin: 15px 0 5px 0;">EXTERNAL ROTATION: ROM</h4>', unsafe_allow_html=True)
        p_er_hist = er_df[(er_df['Name'] == selected_athlete_prof) & (er_df['Test Date'] <= curr_date_prof)].sort_values('Test Date')
        
        if not p_er_hist.empty:
            ec1, ec2 = st.columns([1.8, 3.2])
            with ec1:
                baseline_er = p_er_hist[p_er_hist['Season'] == 'Summer'].head(1) if selected_season == 'Summer' else p_er_hist.head(1)
        
                if not baseline_er.empty:
                    latest_er = p_er_hist.iloc[-1]
                    cur_l_rom = clean_val(latest_er.get('L Max ROM (°)', 0.0))
                    cur_r_rom = clean_val(latest_er.get('R Max ROM (°)', 0.0))
                    cur_asym_rom = clean_val(latest_er.get('ROM Asymmetry (%)', 0.0))
        
                    color_er_l = "#28a745" if cur_l_rom >= 110 else "#ffc107" if 90 <= cur_l_rom <= 109 else "#dc3545"
                    color_er_r = "#28a745" if cur_r_rom >= 110 else "#ffc107" if 90 <= cur_r_rom <= 109 else "#dc3545"
        
                    romsc1, romsc2 = st.columns(2)
                    with romsc1:
                        st.markdown(f'<div class="score-box-native" style="background-color:{color_er_l}; font-size:16px;">{cur_l_rom:.1f}°<br><span style="font-size:9px; font-weight:bold;">LEFT</span></div>', unsafe_allow_html=True)
                    with romsc2:
                        st.markdown(f'<div class="score-box-native" style="background-color:{color_er_r}; font-size:16px;">{cur_r_rom:.1f}°<br><span style="font-size:9px; font-weight:bold;">RIGHT</span></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="info-box-native" style="text-align:center;"><p style="margin:0;"><b>ROM Asymmetry:</b> {cur_asym_rom:+.1f}%</p></div>', unsafe_allow_html=True)
            with ec2:
                fig_er = go.Figure()
                fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['L Max ROM (°)'], name="Left Max ROM", mode='lines+markers', line=dict(color='#4895DB', width=2.5)))
                fig_er.add_trace(go.Scatter(x=p_er_hist['Test Date'], y=p_er_hist['R Max ROM (°)'], name="Right Max ROM", mode='lines+markers', line=dict(color='#FF8200', width=2.5, dash='dash')))
                fig_er.update_layout(height=150, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), template="simple_white")
                st.plotly_chart(fig_er, use_container_width=True, config=LOCKED_CONFIG, key="er_profile_chart")
        else:
            st.info("No Range of Motion metrics found for selected player timeline.")

    # ==========================================
    # --- WORKSPACE TAB AUTOMATION (1-10) ------
    # ==========================================
    remaining_tabs = ["Practice Scores", "Daily Combined Scores", "Spring Max vs Daily Combined", "Practice History", "Match v. Practice", "Match Summary", "Position Analysis", "Phase Analysis", "Practice Planner", "Spring v. Summer"]

    for idx, tab_name in enumerate(remaining_tabs, start=1):
        with tabs[idx]:
            st.subheader(f"{tab_name} Analysis Layer")
            if not df.empty:
                # Utilizing position Maximum values over averages for high-performance visual target logic
                summary_view = df.groupby('Position')[['Player Load', 'Total Jumps']].max().reset_index()
                st.dataframe(summary_view, use_container_width=True, hide_index=True, key=f"tab_view_auto_{idx}")
            else:
                st.info("Upstream metric sheets initializing.")
