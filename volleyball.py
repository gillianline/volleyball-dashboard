import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
from datetime import timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Vols VB Performance", layout="wide")

# --- PASSWORD ---
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

    # --- CSS ---
    st.markdown("""
    <style>

    .gallery-card {
        border: 1px solid #E5E5E7;
        border-radius: 12px;
        background-color: #FFFFFF;
        margin-bottom: 6px;
        overflow: hidden;
        break-inside: avoid;
        page-break-inside: avoid;
    }

    .gallery-photo {
        border-radius: 50%;
        width: 110px;
        height: 110px;
        object-fit: cover;
        border: 4px solid #FF8200;
    }

    .scout-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
        text-align: center;
    }

    .scout-table th {
        background-color: #4895DB;
        color: white;
        padding: 5px;
    }

    .scout-table td {
        padding: 4px;
    }

    .section-header {
        font-size: 14px;
        font-weight: 800;
        color: #4895DB;
        border-bottom: 2px solid #FF8200;
        margin-top: 15px;
        margin-bottom: 10px;
    }

    @media print {

        body * {
            visibility: hidden;
        }

        #print-area, #print-area * {
            visibility: visible;
        }

        #print-area {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
        }

        .gallery-card {
            break-inside: avoid !important;
            page-break-inside: avoid !important;
        }

        .js-plotly-plot {
            break-inside: avoid !important;
            page-break-inside: avoid !important;
        }

        .stTabs, header, footer, button, .print-hide {
            display: none !important;
        }
    }

    </style>
    """, unsafe_allow_html=True)

    # --- DATA ---
    @st.cache_data
    def load_data():
        df = pd.read_csv(st.secrets["GOOGLE_SHEET_URL"])
        df['Date'] = pd.to_datetime(df['Date'])
        return df

    df = load_data()

    LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}

    tabs = st.tabs(["Match Summary"])

    # =========================
    # MATCH SUMMARY TAB
    # =========================
    with tabs[0]:

        st.markdown('<div class="print-hide">', unsafe_allow_html=True)

        if st.button("🖨️ Export to PDF"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

        match_list = df['Session_Name'].unique()

        selected_matches = st.multiselect(
            "Select Matches",
            match_list,
            default=match_list[-3:]
        )

        st.markdown('</div>', unsafe_allow_html=True)

        if selected_matches:

            st.markdown('<div id="print-area">', unsafe_allow_html=True)

            tourney_df = df[df['Session_Name'].isin(selected_matches)]

            athletes = sorted(tourney_df['Name'].unique())

            st.markdown('<div class="section-header">Athlete Breakdown</div>', unsafe_allow_html=True)

            for name in athletes:
                ad = tourney_df[tourney_df['Name'] == name]

                st.markdown('<div class="gallery-card">', unsafe_allow_html=True)

                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:10px; padding:10px;">
                    <img src="{ad['PhotoURL'].iloc[0]}" class="gallery-photo" style="width:55px;height:55px;">
                    <div>
                        <div style="font-weight:900;">{name}</div>
                        <div style="color:#4895DB;">{ad['Position'].iloc[0]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                table = "<table class='scout-table'><tr><th>Match</th><th>Jumps</th><th>Load</th><th>Effort</th><th>Distance</th></tr>"

                for _, r in ad.iterrows():
                    table += f"""
                    <tr>
                        <td>{r['Session_Name']}</td>
                        <td>{int(r['Total Jumps'])}</td>
                        <td>{r['Player Load']:.0f}</td>
                        <td>{r['Explosive Efforts']:.0f}</td>
                        <td>{r['Estimated Distance (y)']:.0f}</td>
                    </tr>
                    """

                table += "</table>"

                st.markdown(table, unsafe_allow_html=True)

                fig = go.Figure()

                for _, r in ad.iterrows():
                    fig.add_trace(go.Bar(
                        x=['Jumps','Load','Effort'],
                        y=[r['Total Jumps'], r['Player Load'], r['Explosive Efforts']],
                        name=r['Session_Name']
                    ))

                fig.update_layout(height=250, barmode='group')

                st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG)

                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">Team Averages</div>', unsafe_allow_html=True)

            team_avg = tourney_df.groupby('Session_Name')[[
                'Total Jumps',
                'Player Load',
                'Explosive Efforts',
                'Estimated Distance (y)'
            ]].mean().reset_index()

            for metric in ['Total Jumps','Player Load','Explosive Efforts','Estimated Distance (y)']:

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=team_avg['Session_Name'],
                    y=team_avg[metric]
                ))

                fig.update_layout(title=metric, height=300)

                st.plotly_chart(fig, use_container_width=True, config=LOCKED_CONFIG)

            st.markdown('</div>', unsafe_allow_html=True)
