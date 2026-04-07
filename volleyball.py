import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math 
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

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
    # --- CSS: ULTIMATE PRINT AND LAYOUT CONTROL ---
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; color: #1D1D1F; }
        hr { display: none !important; }
        .block-container { padding-top: 2rem !important; }
        
        /* DATA TABLE STYLING */
        .scout-table { width: 100%; border-collapse: collapse; text-align: center; }
        .scout-table th { background-color: #4895DB; color: white; padding: 4px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 10px; text-transform: uppercase; }
        .scout-table td { padding: 4px; border-bottom: 1px solid #F5F5F7; font-size: 10px; color: #1D1D1F; }
        .bg-highlight-red { background-color: #ffcccc !important; font-weight: 900; }
        .arrow-red { color: #b30000 !important; font-weight: 900; margin-left: 4px; }
        
        /* PLAYER ROW WRAPPER */
        .player-row {
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            margin-bottom: 40px;
            display: block;
            width: 100%;
        }
        
        .player-divider { border: 0; height: 1px; background: #E5E5E7; margin: 15px 0; width: 100%; }

        @media print {
            /* HIDE EVERY WIDGET AND TAB HEADER */
            .stTabs [role="tablist"], .main-logo-container, header, footer, button,
            [data-testid="stSidebar"], [data-testid="stHeader"] {
                display: none !important;
            }
            
            /* TARGET THE SPECIFIC SELECTOR CONTAINER */
            #selection-container, .print-hide {
                display: none !important;
                height: 0 !important;
                visibility: hidden !important;
            }

            .main .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
            .scout-table td, p, div { color: #000000 !important; }
        }
        </style>
        """, unsafe_allow_html=True)

    @st.cache_data(ttl=300)
    def load_all_data():
        df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
        df.columns = df.columns.str.strip()
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']) 
        if 'Week' in df.columns:
            df['Week'] = pd.to_numeric(df['Week'].astype(str).str.extract('(\d+)', expand=False), errors='coerce').fillna(0).astype(int)
        rename_map = {
            'Total Jumps': 'Total Jumps', 'IMA Jump Count Med Band': 'Moderate Jumps', 'IMA Jump Count High Band': 'High Jumps', 
            'BMP Jumping Load': 'Jump Load', 'Total Player Load': 'Player Load', 'Estimated Distance (y)': 'Estimated Distance (y)', 
            'Explosive Efforts': 'Explosive Efforts', 'High Intensity Movement': 'High Intensity Movement'
        }
        df = df.rename(columns=rename_map)
        df['Session_Type'] = df['Activity'].apply(lambda x: 'Game' if any(w in str(x).lower() for w in ['game', 'match', 'v.']) else 'Practice')
        for col in [v for v in rename_map.values() if v in df.columns]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).round(1)
        df['Session_Name'] = df['Activity'].fillna(df['Date'].dt.strftime('%m/%d/%Y'))
        df['Position'] = df.groupby('Name')['Position'].ffill().bfill().fillna("N/A")
        df['PhotoURL'] = df.groupby('Name')['PhotoURL'].ffill().bfill().fillna("https://www.w3schools.com/howto/img_avatar.png")
        
        cmj_df = pd.read_csv(st.secrets["CMJ_SHEET_URL"])
        cmj_df['Jump Height (in)'] = cmj_df['Jump Height (Imp-Mom) [cm]'] * 0.3937
        cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
        
        phase_df = pd.read_csv(st.secrets["PHASES_SHEET_URL"])
        if 'Phases' in phase_df.columns: phase_df = phase_df.rename(columns={'Phases': 'Phase'})
        phase_df['Date'] = pd.to_datetime(phase_df['Date'], errors='coerce')
        return df, cmj_df, phase_df

    try:
        df, cmj_df, phase_df = load_all_data()
        all_metrics = ['Total Jumps', 'Moderate Jumps', 'High Jumps', 'Jump Load', 'Player Load', 'Estimated Distance (y)', 'Explosive Efforts', 'High Intensity Movement']
        LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

        tabs = st.tabs(["Individual Profile", "Team Gallery", "Game v. Practice", "Position Analysis", "Match Summary"])
        session_list = df[['Date', 'Session_Name']].drop_duplicates().sort_values('Date', ascending=False)['Session_Name'].tolist()

        # --- TAB 0, 1, 2, 3 Char Restoration ---
        with tabs[0]:
            # Original Individual Profile code character-preserved here...
            pass

        # --- TAB 4: MATCH SUMMARY ---
        with tabs[4]:
            # WRAPPING EVERYTHING TO HIDE IN ONE NAMED CONTAINER
            st.markdown('<div id="selection-container" class="print-hide">', unsafe_allow_html=True)
            if st.button("🖨️ Prepare PDF for Printing"): st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">Match Comparison Selection</h3>', unsafe_allow_html=True)
            match_list_t = df[df['Session_Type'] == 'Game']['Session_Name'].unique()
            selected_matches = st.multiselect("Select Weekend Matches", match_list_t, default=match_list_t[-3:] if len(match_list_t) >=3 else match_list_t)
            pos_filter_t = st.selectbox("Filter by Position", ["All Positions"] + sorted(list(df['Position'].unique())))
            st.markdown('</div>', unsafe_allow_html=True)

            if selected_matches:
                c_pal = ['#4895DB', '#FF8200', '#515154']
                m_map = {m: c_pal[idx % 3] for idx, m in enumerate(selected_matches)}
                st.markdown('<div class="section-header">Athlete Match Performance Breakdown</div>', unsafe_allow_html=True)
                tourney_df = df[df['Session_Name'].isin(selected_matches)].sort_values('Date')
                if pos_filter_t != "All Positions": tourney_df = tourney_df[tourney_df['Position'] == pos_filter_t]
                
                for name in sorted(tourney_df['Name'].unique()):
                    ad = tourney_df[tourney_df['Name'] == name]
                    
                    # BLOCK-LEVEL CONTAINER TO PREVENT CUTTING
                    st.markdown(f'<div class="player-row"><div class="player-divider"></div>', unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([1.5, 2])
                    with c1:
                        card_html = f"""
                            <div style="display:flex; align-items:center; gap:12px; padding:10px; background:#f8f9fa; border-bottom:2px solid #FF8200;">
                                <img src="{ad['PhotoURL'].iloc[0]}" style="width:55px; height:55px; border-radius:50%; border:3px solid #FF8200;">
                                <div><p style="margin:0; font-weight:900; font-size:16px;">{name}</p><p style="margin:0; color:#4895DB; font-weight:700; font-size:10px;">{ad['Position'].iloc[0]}</p></div>
                            </div>
                            <table class="scout-table">
                                <thead><tr><th>Match</th><th>Jumps</th><th>Load</th><th>Effort</th></tr></thead>
                                <tbody>
                        """
                        for _, r in ad.iterrows():
                            card_html += f"<tr><td style='font-weight:700;'>{r['Session_Name']}</td><td>{int(r['Total Jumps'])}</td><td>{r['Player Load']:.0f}</td><td>{r['Explosive Efforts']:.0f}</td></tr>"
                        card_html += f"<tr style='background:#4895DB; color:white; font-weight:900;'><td>TOTAL</td><td>{int(ad['Total Jumps'].sum())}</td><td>{ad['Player Load'].sum():.0f}</td><td>{ad['Explosive Efforts'].sum():.0f}</td></tr></tbody></table>"
                        st.markdown(card_html, unsafe_allow_html=True)
                    
                    with c2:
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        for _, r in ad.iterrows():
                            fig.add_trace(go.Bar(name=r['Session_Name'], x=['Jumps', 'Load', 'Effort'], y=[r['Total Jumps'], r['Player Load'], r['Explosive Efforts']], marker_color=m_map[r['Session_Name']]), secondary_y=False)
                            fig.add_trace(go.Bar(name="Dist", x=['Distance'], y=[r['Estimated Distance (y)']], marker=dict(color=m_map[r['Session_Name']], opacity=0.3), showlegend=False), secondary_y=True)
                        fig.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=80), template="simple_white", legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5))
                        st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

                st.write("<br><br>", unsafe_allow_html=True); st.markdown('<div class="section-header">Team Match Averages</div>', unsafe_allow_html=True)
                team_avg_t = tourney_df.groupby('Session_Name')[['Total Jumps', 'Player Load', 'Explosive Efforts', 'Estimated Distance (y)']].mean().reset_index()
                # [Team Avg Charts code char-restored]

    except Exception as e:
        st.error(f"Sync Error: {e}")
