import io
import urllib.request
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
import requests


def save_to_secret_sheet(athlete, metric, count_val):
    sheet_url = st.secrets.get("Live Track") or st.secrets.get("sheets", {}).get("live_track_url")
    
    if not sheet_url:
        print("Sync Error: No URL found in st.secrets")
        return

    payload = {
        "Week_Starting": str(week_starting),
        "Athlete": athlete,
        "Metric": metric,
        "Day": day_selected,
        "Count": int(count_val),
    }

    try:
        response = requests.post(sheet_url, json=payload, timeout=5)
        print(f"Sync Response: {response.status_code}")
    except Exception as e:
        print(f"Sync error: {e}")

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Lady Vols Basketball | Performance Console",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background-color: #F8FAFC; color: #0F172A; }
        section[data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
        
        .console-header {
            background: linear-gradient(90deg, #FF8200 0%, #D96B00 100%);
            padding: 12px 20px;
            border-radius: 8px;
            color: #FFFFFF;
            font-weight: 800;
            font-size: 1.4rem;
            letter-spacing: 0.5px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .athlete-card {
            background-color: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 12px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .athlete-avatar {
            width: 75px;
            height: 75px;
            border-radius: 50%;
            border: 3px solid #FF8200;
            object-fit: cover;
            background-color: #F1F5F9;
        }

        .vball-section-title {
            background-color: #38BDF8; color: #0F172A; font-weight: 700; font-size: 1.05rem;
            padding: 8px 16px; border-radius: 6px; text-align: center;
            margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px;
        }

        .vball-table {
            width: 100%; border-collapse: collapse; background-color: #FFFFFF;
            border-radius: 8px; overflow: hidden; border: 1px solid #E2E8F0;
            font-size: 0.88rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 12px;
        }
        .vball-table th {
            background-color: #F1F5F9; color: #475569; font-weight: 700; text-align: left;
            padding: 8px 12px; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; font-size: 0.72rem;
        }
        .vball-table td { padding: 8px 12px; border-bottom: 1px solid #F1F5F9; color: #0F172A; }
        .vball-table tr:last-child td { border-bottom: none; }
        .grade-badge { font-weight: 700; padding: 2px 8px; border-radius: 4px; display: inline-block; }

        .compliance-wrapper {
            background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 12px;
            padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }
        .compliance-subcard {
            background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
            padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); height: 100%;
        }
        .compliance-metric-card {
            background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;
            padding: 8px 6px; text-align: center;
        }
        .compliance-metric-label { font-size: 0.68rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 2px; }
        .compliance-metric-value { font-size: 1.05rem; font-weight: 800; color: #0F172A; }
        .compliance-metric-sub { font-size: 0.68rem; color: #94A3B8; margin-top: 2px; }
    </style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 2. PASSWORD PROTECTION
# -----------------------------------------------------------------------------
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown(
            '<div class="console-header">LADY VOLS PERFORMANCE CONSOLE - LOGIN</div>',
            unsafe_allow_html=True,
        )
        pwd = st.text_input("Enter Dashboard Password:", type="password")
        if st.button("Login"):
            target_password = st.secrets.get("dashboard_password", "ladyvols")
            if pwd == target_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        return False
    return True


if not check_password():
    st.stop()


# -----------------------------------------------------------------------------
# 3. DATA LOADING VIA SECRETS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_sheet_data():
    def fetch_csv(secret_key):
        if "sheets" not in st.secrets or secret_key not in st.secrets["sheets"]:
            return pd.DataFrame()
        url = st.secrets["sheets"][secret_key]
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8")
            return pd.read_csv(
                io.StringIO(content), on_bad_lines="skip", engine="python"
            )

    try:
        vol_df = fetch_csv("volume_url")
        int_df = fetch_csv("intensity_url")
        comp_df = fetch_csv("compliance_url")
        weekly_df = fetch_csv("weekly_url")
        cmj_df = fetch_csv("cmj_url")
        roster_df = fetch_csv("roster_url")
        
        nordic_df = fetch_csv("nordic_url")
        ankle_df = fetch_csv("ankle_url")
        knee_df = fetch_csv("knee_url")
        hip_df = fetch_csv("hip_url")

        for df in [vol_df, int_df, comp_df, weekly_df, cmj_df, nordic_df, ankle_df, knee_df, hip_df]:
            if df.empty:
                continue
            date_col = [c for c in df.columns if "date" in c.lower()]
            if date_col:
                df["Date"] = pd.to_datetime(df[date_col[0]], errors="coerce")
                df["Date_Str"] = df["Date"].dt.strftime("%Y-%m-%d")

        return (
            vol_df, int_df, comp_df, weekly_df, cmj_df, roster_df,
            nordic_df, ankle_df, knee_df, hip_df
        )
    except Exception as e:
        st.error(f"Error loading data from Google Sheets secrets: {e}")
        st.stop()


(
    vol_raw, int_raw, comp_raw, weekly_raw, cmj_raw, roster_raw,
    nordic_raw, ankle_raw, knee_raw, hip_raw
) = load_sheet_data()

        
# -----------------------------------------------------------------------------
# 4. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def get_vball_color(score):
    if score is None or pd.isna(score):
        return "#E2E8F0", "#475569"
    if score < 50:
        return "#BBF7D0", "#166534"  # Green
    elif score < 75:
        return "#FEF08A", "#854D0E"  # Yellow
    else:
        return "#FFD6D6", "#991B1B"  # Red


def render_vball_table(df):
    if df.empty:
        return "<p style='color:#64748B; font-style:italic;'>No data available.</p>"
    html = '<table class="vball-table"><thead><tr>'
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df.iterrows():
        html += "<tr>"
        for col in df.columns:
            val = row[col]
            if col == "Grade":
                bg_c, fg_c = get_vball_color(val)
                html += f'<td><span class="grade-badge" style="background-color:{bg_c}; color:{fg_c};">{val}</span></td>'
            elif isinstance(val, float):
                html += f"<td>{val:.2f}</td>"
            else:
                html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def create_clean_bar_chart(x_vals, y_vals, title_text, bar_color="#38BDF8"):
    fig = px.bar(x=x_vals, y=y_vals, title=title_text)
    fig.update_traces(marker_color=bar_color)
    fig.update_layout(
        title_font=dict(size=14, color="#0F172A"),
        height=240,
        margin=dict(l=0, r=0, t=35, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None,
        yaxis_title=None,
    )
    return fig


def compute_practice_tables(player_name, session_date_str):
    v_player = vol_raw[
        (vol_raw["Player"] == player_name)
        & (vol_raw["Date_Str"] == str(session_date_str))
    ]
    i_player = int_raw[
        (int_raw["Player"] == player_name)
        & (int_raw["Date_Str"] == str(session_date_str))
    ]

    v_all = vol_raw[vol_raw["Player"] == player_name].sort_values("Date")
    i_all = int_raw[int_raw["Player"] == player_name].sort_values("Date")
    
    if not v_all.empty and "Date" in v_all.columns and v_all["Date"].notna().any():
        start_date_v = v_all["Date"].min()
        v_base = v_all[v_all["Date"] <= start_date_v + pd.Timedelta(days=14)]
    else:
        v_base = v_all

    if not i_all.empty and "Date" in i_all.columns and i_all["Date"].notna().any():
        start_date_i = i_all["Date"].min()
        i_base = i_all[i_all["Date"] <= start_date_i + pd.Timedelta(days=14)]
    else:
        i_base = i_all

    vol_metrics = [
        "Distance (mi)",
        "Accumulated Acceleration Load",
        "Decels Load",
        "FCTs",
        "Physio Load",
        "Mechanical Load",
        "Jump Load (J)",
    ]
    int_metrics = [
        "Physio Intensity",
        "Acceleration Load (load | High AAL)",
        "Distance (speed | High Speed) (mi)",
        "Speed (max.) (mph)",
        "Sprints",
        "Exertions",
        "High Metabolic Power Distance (m)",
    ]

    vol_rows, int_rows = [], []

    for m in vol_metrics:
        curr = (
            v_player[m].values[0] if not v_player.empty and m in v_player else 0.0
        )
        mx = v_base[m].max() if not v_base.empty and m in v_base else curr
        grade = round((curr / mx * 100), 0) if mx > 0 else 0
        vol_rows.append({"Metric": m, "Current": curr, "Max": mx, "Grade": grade})

    for m in int_metrics:
        curr = (
            i_player[m].values[0] if not i_player.empty and m in i_player else 0.0
        )
        mx = i_base[m].max() if not i_base.empty and m in i_base else curr
        grade = round((curr / mx * 100), 0) if mx > 0 else 0
        int_rows.append({"Metric": m, "Current": curr, "Max": mx, "Grade": grade})

    vol_df_out = pd.DataFrame(vol_rows)
    int_df_out = pd.DataFrame(int_rows)

    vol_score = int(vol_df_out["Grade"].mean()) if not vol_df_out.empty else 0
    int_score = int(int_df_out["Grade"].mean()) if not int_df_out.empty else 0

    minutes = (
        v_player["Minutes"].values[0]
        if not v_player.empty and "Minutes" in v_player
        else "--"
    )
    week_num = (
        v_player["Week"].values[0]
        if not v_player.empty and "Week" in v_player
        else "--"
    )
    day_num = (
        v_player["Day"].values[0]
        if not v_player.empty and "Day" in v_player
        else "--"
    )

    return (
        vol_df_out,
        int_df_out,
        vol_score,
        int_score,
        minutes,
        week_num,
        day_num,
    )


def create_team_bar_athlete_line_chart(
    weeks, team_avg_vals, athlete_vals, title_text, athlete_name, bar_color="#38BDF8"
):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=weeks, y=team_avg_vals, name="Team Average", marker_color=bar_color
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=athlete_vals,
            name=f"{athlete_name} Output",
            mode="markers",
            marker=dict(
                symbol="line-ew", size=24, line=dict(width=3, color="black")
            ),
        )
    )
    fig.update_layout(
        title=title_text,
        title_font=dict(size=14, color="#0F172A"),
        height=250,
        margin=dict(l=0, r=0, t=35, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    return fig


def render_metric_subcard_html(p_comp, col_name, title_name, unit):
    if p_comp.empty or col_name not in p_comp.columns:
        return ""

    valid_df = p_comp.dropna(subset=[col_name])
    if valid_df.empty:
        return ""

    all_time_max = valid_df[col_name].max()
    max_row = valid_df[valid_df[col_name] == all_time_max].iloc[-1]
    max_date = max_row["Date_Str"]

    recent_row = valid_df.iloc[-1]
    recent_val = recent_row[col_name]
    recent_date = recent_row["Date_Str"]

    pct_max = (
        f"{(recent_val / all_time_max * 100):.1f}%"
        if all_time_max > 0
        else "-- %"
    )
    days_since = (
        pd.to_datetime("today") - pd.to_datetime(max_date)
    ).days

    badge_bg = "#BBF7D0" if days_since <= 7 else "#FFD6D6"
    badge_fg = "#166534" if days_since <= 7 else "#991B1B"

    val_str = f"{recent_val:.1f} {unit}" if isinstance(recent_val, (int, float)) else str(recent_val)
    max_str = f"{all_time_max:.1f} {unit}" if isinstance(all_time_max, (int, float)) else str(all_time_max)

    return f"""
    <div class="compliance-subcard">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
            <h5 style="margin:0; font-size:0.95rem; color:#0F172A; font-weight:700;">{title_name}</h5>
            <div style="background-color:{badge_bg}; color:{badge_fg}; font-weight:700; padding:2px 8px; border-radius:10px; font-size:0.7rem;">
                {days_since} Days
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px;">
            <div class="compliance-metric-card">
                <div class="compliance-metric-label">Recent</div>
                <div class="compliance-metric-value">{val_str}</div>
                <div class="compliance-metric-sub">{recent_date}</div>
            </div>
            <div class="compliance-metric-card">
                <div class="compliance-metric-label">All-Time Max</div>
                <div class="compliance-metric-value">{max_str}</div>
                <div class="compliance-metric-sub">{max_date}</div>
            </div>
            <div class="compliance-metric-card">
                <div class="compliance-metric-label">% Peak Output</div>
                <div class="compliance-metric-value" style="color:#FF8200;">{pct_max}</div>
                <div class="compliance-metric-sub">Recent vs. Peak</div>
            </div>
            <div class="compliance-metric-card">
                <div class="compliance-metric-label">Recency Status</div>
                <div class="compliance-metric-value">{days_since} Days</div>
                <div class="compliance-metric-sub">Elapsed Threshold</div>
            </div>
        </div>
    </div>
    """


# -----------------------------------------------------------------------------
# 5. SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.markdown("### LADY VOLS BASKETBALL")

main_tab = st.sidebar.radio(
    "Console View:",
    options=[
        "Individual Profile",
        "Practice Score",
        "Compliance",
        "Weekly Data",
        "Testing"
    ],
    index=0,
)

st.sidebar.divider()
st.sidebar.markdown("### DATA MANAGEMENT")

if st.sidebar.button("Refresh Google Sheets Data"):
    st.cache_data.clear()
    st.sidebar.success("Data reloaded!")
    st.rerun()

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()


# -----------------------------------------------------------------------------
# 6. VIEW CONTROLLERS
# -----------------------------------------------------------------------------

st.markdown(
    """
    <div class="console-header">
        <span>LADY VOLS BASKETBALL ANALYTICS</span>
        <span style="font-size: 0.9rem; font-weight: 600; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 4px;">SUMMER PHASE</span>
    </div>
""",
    unsafe_allow_html=True,
)

active_season = st.tabs(["Summer"])[0]

with active_season:
    st.markdown("<br>", unsafe_allow_html=True)
    roster_players = (
        roster_raw["Name"].tolist()
        if not roster_raw.empty
        else vol_raw["Player"].unique().tolist()
    )

    compliance_metrics = [
        ("Speed (MPH)", "Max Speed", "mph"),
        ("Distance (mi)", "Distance", "mi"),
        ("High Metabolic Power Distance (m)", "High Metabolic Power", "m"),
        ("Accumulated Acceleration Load", "AAL", "load"),
        ("Decels Load", "Decels Load", "load"),
        ("Sprints", "Sprints", "cnt"),
        ("MCTs", "MCTs", "cnt"),
        ("FCTs", "FCTs", "cnt"),
    ]

    # =========================================================================
    # TAB 1: INDIVIDUAL PROFILE
    # =========================================================================
    if main_tab == "Individual Profile":
        c_sel, _ = st.columns([1, 2])
        with c_sel:
            selected_player = st.selectbox("Select Athlete Profile:", roster_players)

        p_row = roster_raw[roster_raw["Name"] == selected_player]
        p_pos = (
            p_row["Position"].values[0]
            if not p_row.empty
            else "Guard / Forward | #00"
        )
        p_img = (
            p_row["Picture"].values[0]
            if not p_row.empty
            else "https://via.placeholder.com/80"
        )

        st.markdown(
            f"""
                <div class="athlete-card">
                    <img src="{p_img}" class="athlete-avatar">
                    <div class="athlete-info">
                        <h2 style="margin:0; font-size:1.4rem; font-weight:700; color:#0F172A;">{selected_player}</h2>
                        <p style="margin:2px 0 0 0; color:#64748B; font-size:0.88rem;">{p_pos}</p>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="vball-section-title">1. Workload Exposure & Compliance Grid</div>',
            unsafe_allow_html=True,
        )
        
        p_comp = comp_raw[comp_raw["Player"] == selected_player].sort_values("Date")

        for row_idx in range(0, len(compliance_metrics), 2):
            col1, col2 = st.columns(2)
            cols = [col1, col2]
            for j in range(2):
                metric_idx = row_idx + j
                if metric_idx < len(compliance_metrics):
                    col_name, display_title, unit = compliance_metrics[metric_idx]
                    subcard_html = render_metric_subcard_html(p_comp, col_name, display_title, unit)
                    with cols[j]:
                        st.markdown(subcard_html, unsafe_allow_html=True)

        st.divider()

        st.markdown(
            '<div class="vball-section-title">2. Practice Performance & Score Trends</div>',
            unsafe_allow_html=True,
        )
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("#### Practice Score History")
            v_p = vol_raw[vol_raw["Player"] == selected_player].sort_values("Date")

            if not v_p.empty:
                score_history = []
                for d_str in v_p["Date_Str"].unique():
                    _, _, v_sc, i_sc, _, _, _ = compute_practice_tables(
                        selected_player, d_str
                    )
                    score_history.append(
                        {"Date": d_str, "Volume Score": v_sc, "Intensity Score": i_sc}
                    )

                df_score_trend = pd.DataFrame(score_history)

                fig1 = px.line(
                    df_score_trend,
                    x="Date",
                    y=["Volume Score", "Intensity Score"],
                    markers=True,
                    color_discrete_sequence=["#FF8200", "#38BDF8"],
                )
                fig1.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=230,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        title=None,
                    ),
                )
                st.plotly_chart(fig1, use_container_width=True)

        latest_date_str = vol_raw[vol_raw["Player"] == selected_player][
            "Date_Str"
        ].max()

        if pd.notna(latest_date_str):
            vol_df, int_df, vol_score, int_score, mins, wk, dy = (
                compute_practice_tables(selected_player, latest_date_str)
            )

            wk_str = str(wk).replace("Week ", "")
            dy_str = str(dy).replace("Day ", "")

            with col_g2:
                st.markdown(f"#### Latest Practice Metrics ({latest_date_str})")
                st.markdown(
                    f"""
                        <div style="margin-bottom: 12px; display: flex; gap: 10px;">
                            <span style="background:#F1F5F9; border:1px solid #E2E8F0; color:#475569; padding:4px 10px; border-radius:6px; font-weight:600; font-size:0.8rem;">Minutes: {mins}</span>
                            <span style="background:#F1F5F9; border:1px solid #E2E8F0; color:#475569; padding:4px 10px; border-radius:6px; font-weight:600; font-size:0.8rem;">Week {wk_str}</span>
                            <span style="background:#F1F5F9; border:1px solid #E2E8F0; color:#475569; padding:4px 10px; border-radius:6px; font-weight:600; font-size:0.8rem;">Day {dy_str}</span>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_v_sc, col_i_sc = st.columns(2)
                v_bg, v_fg = get_vball_color(vol_score)
                i_bg, i_fg = get_vball_color(int_score)

                with col_v_sc:
                    st.markdown(
                        f"""
                            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:10px; text-align:center;">
                                <div style="font-weight: 700; color: #64748B; font-size: 0.85rem;">VOLUME SCORE</div>
                                <div style="font-size: 1.8rem; font-weight: 800; padding: 4px 0; border-radius: 6px; background-color: {v_bg}; color: {v_fg}; margin-top: 4px;">{vol_score}</div>
                            </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col_i_sc:
                    st.markdown(
                        f"""
                            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:10px; text-align:center;">
                                <div style="font-weight: 700; color: #64748B; font-size: 0.85rem;">INTENSITY SCORE</div>
                                <div style="font-size: 1.8rem; font-weight: 800; padding: 4px 0; border-radius: 6px; background-color: {i_bg}; color: {i_fg}; margin-top: 4px;">{int_score}</div>
                            </div>
                        """,
                        unsafe_allow_html=True,
                    )

            col_v_tbl, col_i_tbl = st.columns(2)
            with col_v_tbl:
                st.markdown(
                    '<div style="font-weight:700; font-size:0.9rem; margin: 10px 0 5px 0;">Volume Breakdown</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(render_vball_table(vol_df), unsafe_allow_html=True)
            with col_i_tbl:
                st.markdown(
                    '<div style="font-weight:700; font-size:0.9rem; margin: 10px 0 5px 0;">Intensity Breakdown</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(render_vball_table(int_df), unsafe_allow_html=True)

        st.divider()

        st.markdown(
            '<div class="vball-section-title">3. Jump Performance & RSI Tracking</div>',
            unsafe_allow_html=True,
        )

        p_cmj_ind = cmj_raw[cmj_raw["Name"] == selected_player].sort_values("Date").copy()
        jump_cols_ind = [c for c in p_cmj_ind.columns if "jump" in c.lower() or "height" in c.lower()]
        j_col_ind = jump_cols_ind[0] if jump_cols_ind else None
        rsi_cols_ind = [c for c in p_cmj_ind.columns if "rsi" in c.lower()]
        rsi_col_ind = rsi_cols_ind[0] if rsi_cols_ind else None

        if not p_cmj_ind.empty and j_col_ind:
            p_cmj_ind["Jump_Height_Clean"] = pd.to_numeric(
                p_cmj_ind[j_col_ind].astype(str).str.replace(r"[^0-9.]", "", regex=True),
                errors="coerce",
            )

            fig_jump_trend = go.Figure()
            fig_jump_trend.add_trace(
                go.Scatter(
                    x=p_cmj_ind["Date"],
                    y=p_cmj_ind["Jump_Height_Clean"],
                    name="Jump Height",
                    mode="lines+markers",
                    connectgaps=True,
                    yaxis="y",
                    line=dict(color="#FF8200", width=4),
                    marker=dict(size=8, color="#FF8200"),
                )
            )

            if rsi_col_ind:
                p_cmj_ind["RSI_Clean"] = pd.to_numeric(
                    p_cmj_ind[rsi_col_ind].astype(str).str.replace(r"[^0-9.]", "", regex=True),
                    errors="coerce",
                )
                fig_jump_trend.add_trace(
                    go.Scatter(
                        x=p_cmj_ind["Date"],
                        y=p_cmj_ind["RSI_Clean"],
                        name="RSI Modified",
                        mode="lines+markers",
                        connectgaps=True,
                        yaxis="y2",
                        line=dict(color="#38BDF8", width=3, dash="dot"),
                        marker=dict(size=8, color="#38BDF8"),
                    )
                )

            fig_jump_trend.update_layout(
                height=300,
                margin=dict(l=40, r=40, t=40, b=40),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.08,
                    xanchor="left",
                    x=0.01,
                    font=dict(size=13, color="#0F172A"),
                ),
                xaxis=dict(
                    title=None,
                    type="date",
                    tickformat="%b %d\n%Y",
                    showgrid=False,
                    showline=True,
                    linewidth=1.5,
                    linecolor="#0F172A",
                    tickfont=dict(color="#64748B", size=12),
                ),
                yaxis=dict(
                    showgrid=False,
                    showline=True,
                    linewidth=1.5,
                    linecolor="#0F172A",
                    tickfont=dict(color="#64748B", size=12),
                    side="left",
                ),
                yaxis2=dict(
                    showgrid=False,
                    showline=True,
                    linewidth=1.5,
                    linecolor="#0F172A",
                    tickfont=dict(color="#64748B", size=12),
                    overlaying="y",
                    side="right",
                    anchor="x",
                ),
            )
            st.plotly_chart(fig_jump_trend, use_container_width=True)

            with st.expander(f"View Raw CMJ Data Log for {selected_player}"):
                display_cols_ind = [c for c in p_cmj_ind.columns if c not in ["Name", "Date_Str", "Jump_Height_Clean", "RSI_Clean"]]
                st.markdown(render_vball_table(p_cmj_ind[display_cols_ind]), unsafe_allow_html=True)

        st.divider()

        st.markdown(
            '<div class="vball-section-title">4. Weekly Output vs. Team Averages</div>',
            unsafe_allow_html=True,
        )

        p_weekly = weekly_raw[weekly_raw["Player"] == selected_player]
        t_weekly_avg = (
            weekly_raw.groupby("Week")
            .agg({
                "Distance (mi)": "mean",
                "Distance (speed | High Speed) (mi)": "mean",
                "Accumulated Acceleration Load": "mean",
                "Decels Load": "mean",
            })
            .reset_index()
        )

        all_weeks = t_weekly_avg["Week"].tolist()

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            fig_ind_td = create_team_bar_athlete_line_chart(
                all_weeks,
                t_weekly_avg["Distance (mi)"],
                p_weekly["Distance (mi)"],
                f"Total Distance (mi) — {selected_player}",
                selected_player,
                "#FF8200",
            )
            st.plotly_chart(fig_ind_td, use_container_width=True)

            fig_ind_aal = create_team_bar_athlete_line_chart(
                all_weeks,
                t_weekly_avg["Accumulated Acceleration Load"],
                p_weekly["Accumulated Acceleration Load"],
                f"AAL — {selected_player}",
                selected_player,
                "#38BDF8",
            )
            st.plotly_chart(fig_ind_aal, use_container_width=True)

        with col_p2:
            fig_ind_hsd = create_team_bar_athlete_line_chart(
                all_weeks,
                t_weekly_avg["Distance (speed | High Speed) (mi)"],
                p_weekly["Distance (speed | High Speed) (mi)"],
                f"High Speed Distance (mi) — {selected_player}",
                selected_player,
                "#FF8200",
            )
            st.plotly_chart(fig_ind_hsd, use_container_width=True)

            fig_ind_dl = create_team_bar_athlete_line_chart(
                all_weeks,
                t_weekly_avg["Decels Load"],
                p_weekly["Decels Load"],
                f"Deceleration Load — {selected_player}",
                selected_player,
                "#38BDF8",
            )
            st.plotly_chart(fig_ind_dl, use_container_width=True)

    # =========================================================================
    # TAB 2: PRACTICE SCORE (TEAM/SESSION VIEW)
    # =========================================================================
    elif main_tab == "Practice Score":
        c_d, _ = st.columns([1, 3])
        with c_d:
            available_dates = (
                vol_raw["Date_Str"].sort_values(ascending=False).unique()
            )
            session_date = st.selectbox("Select Session Date:", available_dates)

        st.markdown("<br>", unsafe_allow_html=True)

        for player_name in roster_players:
            p_row = roster_raw[roster_raw["Name"] == player_name]
            p_pos = (
                p_row["Position"].values[0] if not p_row.empty else "Guard / Forward"
            )
            p_img = (
                p_row["Picture"].values[0]
                if not p_row.empty
                else "https://via.placeholder.com/70"
            )

            vol_df, int_df, vol_score, int_score, mins, wk, dy = (
                compute_practice_tables(player_name, str(session_date))
            )

            vol_html_table = render_vball_table(vol_df)
            int_html_table = render_vball_table(int_df)

            v_bg, v_fg = get_vball_color(vol_score)
            i_bg, i_fg = get_vball_color(int_score)

            wk_str = str(wk).replace("Week ", "")
            dy_str = str(dy).replace("Day ", "")

            single_box_card_html = f"""
            <div style="background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 12px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; border-bottom: 1px solid #E2E8F0; padding-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <img src="{p_img}" style="width:60px; height:60px; border-radius:50%; border:3px solid #FF8200; object-fit:cover;">
                        <div>
                            <h3 style="margin:0; font-size:1.3rem; color:#0F172A; font-weight:700;">{player_name}</h3>
                            <span style="color:#64748B; font-size:0.85rem;">{p_pos}</span>
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <span style="background:#F1F5F9; border:1px solid #E2E8F0; color:#475569; padding:4px 10px; border-radius:6px; font-weight:600; font-size:0.8rem;">Minutes: {mins}</span>
                        <span style="background:#F1F5F9; border:1px solid #E2E8F0; color:#475569; padding:4px 10px; border-radius:6px; font-weight:600; font-size:0.8rem;">Week {wk_str}</span>
                        <span style="background:#F1F5F9; border:1px solid #E2E8F0; color:#475569; padding:4px 10px; border-radius:6px; font-weight:600; font-size:0.8rem;">Day {dy_str}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 20px; width: 100%;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="background-color:#38BDF8; color:#0F172A; font-weight:700; font-size:0.95rem; padding:6px 12px; border-radius:6px; text-align:center; margin-bottom:12px; text-transform:uppercase;">Volume Metrics</div>
                        {vol_html_table}
                        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:10px; text-align:center; margin-top:10px;">
                            <div style="font-weight:700; color:#64748B; font-size:0.85rem;">VOLUME SCORE</div>
                            <div style="font-size:2rem; font-weight:800; padding:6px 0; border-radius:6px; background-color:{v_bg}; color:{v_fg}; margin-top:4px;">{vol_score}</div>
                        </div>
                    </div>
                    <div style="flex: 1; min-width: 0;">
                        <div style="background-color:#38BDF8; color:#0F172A; font-weight:700; font-size:0.95rem; padding:6px 12px; border-radius:6px; text-align:center; margin-bottom:12px; text-transform:uppercase;">Intensity Metrics</div>
                        {int_html_table}
                        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:10px; text-align:center; margin-top:10px;">
                            <div style="font-weight:700; color:#64748B; font-size:0.85rem;">INTENSITY SCORE</div>
                            <div style="font-size:2rem; font-weight:800; padding:6px 0; border-radius:6px; background-color:{i_bg}; color:{i_fg}; margin-top:4px;">{int_score}</div>
                        </div>
                    </div>
                </div>
            </div>
            """

            st.markdown(single_box_card_html, unsafe_allow_html=True)

    # =========================================================================
    # TAB 3: COMPLIANCE (TEAM GRID VIEW)
    # =========================================================================
    elif main_tab == "Compliance":
        st.markdown(
            '<div class="vball-section-title">Team Performance Compliance Matrix</div>',
            unsafe_allow_html=True,
        )

        selected_player_comp = st.selectbox("Select Athlete Compliance Overview:", roster_players)

        p_row = roster_raw[roster_raw["Name"] == selected_player_comp]
        p_pos = p_row["Position"].values[0] if not p_row.empty else "Guard / Forward | #00"
        p_img = p_row["Picture"].values[0] if not p_row.empty else "https://via.placeholder.com/60"

        p_comp = comp_raw[comp_raw["Player"] == selected_player_comp].sort_values("Date")

        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 15px; background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 12px 16px; margin-bottom: 20px;">
                <img src="{p_img}" class="athlete-avatar" style="width:50px; height:50px;">
                <div>
                    <h3 style="margin:0; font-size:1.2rem; color:#0F172A; font-weight:700;">{selected_player_comp}</h3>
                    <span style="color:#64748B; font-size:0.85rem;">{p_pos}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for row_idx in range(0, len(compliance_metrics), 2):
            col1, col2 = st.columns(2)
            cols = [col1, col2]
            for j in range(2):
                metric_idx = row_idx + j
                if metric_idx < len(compliance_metrics):
                    col_name, display_title, unit = compliance_metrics[metric_idx]
                    subcard_html = render_metric_subcard_html(p_comp, col_name, display_title, unit)
                    with cols[j]:
                        st.markdown(subcard_html, unsafe_allow_html=True)

    # =========================================================================
    # TAB 4: WEEKLY DATA
    # =========================================================================
    elif main_tab == "Weekly Data":
        st.markdown(
            '<div class="vball-section-title">1. Team Weekly Accumulation Overview</div>',
            unsafe_allow_html=True,
        )

        weekly_agg = (
            weekly_raw.groupby("Week")
            .agg({
                "Distance (mi)": "sum",
                "Distance (speed | High Speed) (mi)": "sum",
                "Accumulated Acceleration Load": "sum",
                "Decels Load": "sum",
            })
            .reset_index()
        )

        weeks = weekly_agg["Week"].tolist()

        w1, w2 = st.columns(2)
        with w1:
            fig_td = create_clean_bar_chart(
                weeks, weekly_agg["Distance (mi)"], "Total Distance (mi)", "#38BDF8"
            )
            st.plotly_chart(fig_td, use_container_width=True)

            fig_aal = create_clean_bar_chart(
                weeks,
                weekly_agg["Accumulated Acceleration Load"],
                "Accumulated Acceleration Load (AAL)",
                "#FF8200",
            )
            st.plotly_chart(fig_aal, use_container_width=True)

        with w2:
            fig_hsd = create_clean_bar_chart(
                weeks,
                weekly_agg["Distance (speed | High Speed) (mi)"],
                "High Speed Distance (mi)",
                "#38BDF8",
            )
            st.plotly_chart(fig_hsd, use_container_width=True)

            fig_dl = create_clean_bar_chart(
                weeks, weekly_agg["Decels Load"], "Deceleration Load", "#FF8200"
            )
            st.plotly_chart(fig_dl, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            '<div class="vball-section-title">2. Individual Player Breakdown vs. Team Average</div>',
            unsafe_allow_html=True,
        )
        selected_player_w = st.selectbox("Select Athlete:", roster_players)

        p_weekly = weekly_raw[weekly_raw["Player"] == selected_player_w]
        t_weekly_avg = (
            weekly_raw.groupby("Week")
            .agg({
                "Distance (mi)": "mean",
                "Distance (speed | High Speed) (mi)": "mean",
                "Accumulated Acceleration Load": "mean",
                "Decels Load": "mean",
            })
            .reset_index()
        )

        all_weeks = t_weekly_avg["Week"].tolist()

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            fig_ind_td = create_team_bar_athlete_line_chart(
                all_weeks,
                t_weekly_avg["Distance (mi)"],
                p_weekly["Distance (mi)"],
                f"Total Distance (mi) — {selected_player_w}",
                selected_player_w,
                "#FF8200",
            )
            st.plotly_chart(fig_ind_td, use_container_width=True)

            fig_ind_aal = create_team_bar_athlete_line_chart(
                all_weeks,
                t_weekly_avg["Accumulated Acceleration Load"],
                p_weekly["Accumulated Acceleration Load"],
                f"AAL — {selected_player_w}",
                selected_player_w,
                "#38BDF8",
            )
            st.plotly_chart(fig_ind_aal, use_container_width=True)

        with col_p2:
            fig_ind_hsd = create_team_bar_athlete_line_chart(
                all_weeks,
                t_weekly_avg["Distance (speed | High Speed) (mi)"],
                p_weekly["Distance (speed | High Speed) (mi)"],
                f"High Speed Distance (mi) — {selected_player_w}",
                selected_player_w,
                "#FF8200",
            )
            st.plotly_chart(fig_ind_hsd, use_container_width=True)

            fig_ind_dl = create_team_bar_athlete_line_chart(
                all_weeks,
                t_weekly_avg["Decels Load"],
                p_weekly["Decels Load"],
                f"Deceleration Load — {selected_player_w}",
                selected_player_w,
                "#38BDF8",
            )
            st.plotly_chart(fig_ind_dl, use_container_width=True)

    # =========================================================================
    # TAB 5: TESTING (SUB-TABS FOR CMJ HISTORY & INTAKE TESTING)
    # =========================================================================
    elif main_tab == "Testing":
        testing_tab_cmj, testing_tab_intake = st.tabs(["CMJ History", "Intake Assessment"])

        # SUB-TAB 1: CMJ HISTORY
        with testing_tab_cmj:
            st.markdown(
                '<div class="vball-section-title">CMJ History</div>',
                unsafe_allow_html=True,
            )

            c_filter, _ = st.columns([1, 2])
            with c_filter:
                selected_player_t = st.selectbox("Select Athlete:", roster_players, key="cmj_player_select")

            p_cmj = cmj_raw[cmj_raw["Name"] == selected_player_t].sort_values("Date").copy()

            jump_cols = [c for c in p_cmj.columns if "jump" in c.lower() or "height" in c.lower()]
            j_col = jump_cols[0] if jump_cols else None

            rsi_cols = [c for c in p_cmj.columns if "rsi" in c.lower()]
            rsi_col = rsi_cols[0] if rsi_cols else None

            display_cols = [c for c in p_cmj.columns if c not in ["Name", "Date_Str"]]
            st.markdown(f"### Jump History for {selected_player_t}")
            st.markdown(render_vball_table(p_cmj[display_cols]), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if not p_cmj.empty and j_col:
                p_cmj["Jump_Height_Clean"] = pd.to_numeric(
                    p_cmj[j_col].astype(str).str.replace(r"[^0-9.]", "", regex=True),
                    errors="coerce",
                )

                fig_jump_trend = go.Figure()

                fig_jump_trend.add_trace(
                    go.Scatter(
                        x=p_cmj["Date"],
                        y=p_cmj["Jump_Height_Clean"],
                        name="Jump Height",
                        mode="lines+markers",
                        connectgaps=True,
                        yaxis="y",
                        line=dict(color="#FF8200", width=4),
                        marker=dict(size=8, color="#FF8200"),
                    )
                )

                if rsi_col:
                    p_cmj["RSI_Clean"] = pd.to_numeric(
                        p_cmj[rsi_col].astype(str).str.replace(r"[^0-9.]", "", regex=True),
                        errors="coerce",
                    )
                    fig_jump_trend.add_trace(
                        go.Scatter(
                            x=p_cmj["Date"],
                            y=p_cmj["RSI_Clean"],
                            name="RSI Modified",
                            mode="lines+markers",
                            connectgaps=True,
                            yaxis="y2",
                            line=dict(color="#38BDF8", width=3, dash="dot"),
                            marker=dict(size=8, color="#38BDF8"),
                        )
                    )

                fig_jump_trend.update_layout(
                    height=320,
                    margin=dict(l=40, r=40, t=50, b=40),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.08,
                        xanchor="left",
                        x=0.01,
                        font=dict(size=13, color="#0F172A"),
                    ),
                    xaxis=dict(
                        title=None,
                        type="date",
                        tickformat="%b %d\n%Y",
                        showgrid=False,
                        showline=True,
                        linewidth=1.5,
                        linecolor="#0F172A",
                        tickfont=dict(color="#64748B", size=12),
                    ),
                    yaxis=dict(
                        showgrid=False,
                        showline=True,
                        linewidth=1.5,
                        linecolor="#0F172A",
                        tickfont=dict(color="#64748B", size=12),
                        side="left",
                    ),
                    yaxis2=dict(
                        showgrid=False,
                        showline=True,
                        linewidth=1.5,
                        linecolor="#0F172A",
                        tickfont=dict(color="#64748B", size=12),
                        overlaying="y",
                        side="right",
                        anchor="x",
                    ),
                )

                st.plotly_chart(fig_jump_trend, use_container_width=True)

        # SUB-TAB 2: INTAKE ASSESSMENT (ANATOMY MAP + ASSESSMENT DETAILS)
        with testing_tab_intake:
            st.markdown("<h3 style='color:#1D1D1F; font-weight:900; text-transform:uppercase;'>Athlete Intake Assessment</h3>", unsafe_allow_html=True)
            c_int_ath, _ = st.columns([2, 2])
            with c_int_ath:
                selected_intake_athlete = st.selectbox("Select Athlete for Intake Assessment", roster_players, key="intake_ath_select")

            calf_ath = ankle_raw[ankle_raw['Name'] == selected_intake_athlete].sort_values('Date') if not ankle_raw.empty else pd.DataFrame()
            hip_ath = hip_raw[hip_raw['Name'] == selected_intake_athlete].sort_values('Date') if not hip_raw.empty else pd.DataFrame()
            sh_ath = knee_raw[knee_raw['Name'] == selected_intake_athlete].sort_values('Date') if not knee_raw.empty else pd.DataFrame()
            isoy_ath = nordic_raw[nordic_raw['Name'] == selected_intake_athlete].sort_values('Date') if not nordic_raw.empty else pd.DataFrame()

            has_data = not (calf_ath.empty and hip_ath.empty and sh_ath.empty and isoy_ath.empty)

            if has_data:
                def render_val_with_arrow(current, initial, fmt="{:.1f}", unit=""):
                    if initial == 0:
                        return f"{fmt.format(current)}{unit}"
                    diff = current - initial
                    pct = (diff / initial) * 100
                    arrow = "↑" if diff >= 0 else "↓"
                    color = "#28a745" if diff >= 0 else "#dc3545"
                    return f"{fmt.format(current)}{unit} <span style='color:{color}; font-size:11px; font-weight:bold;'>({arrow}{abs(pct):.1f}%)</span>"

                hud_col1, hud_col2 = st.columns([1.2, 1.8])

                # --- LEFT PANEL: REALISTIC PROPORTIONAL ATHLETIC ANATOMY MAP ---
                with hud_col1:
                    hud_svg_html = """
                    <div style="background:#FFFFFF; border-radius:16px; padding:16px; border:1px solid #E5E5E7; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
                        <div style="color:#1D1D1F; font-weight:800; font-size:13px; letter-spacing:1px; text-transform:uppercase; border-bottom:2px solid #FF8200; padding-bottom:6px; margin-bottom:12px;">Anatomy Location Map</div>
                        <div style="position:relative; width:100%; height:380px; background:#FAFDFD; border-radius:12px; border:1px solid #D5E5E8; display:flex; align-items:center; justify-content:center; overflow:hidden;">
                            <svg viewBox="0 0 140 220" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:100%;">
                                <defs>
                                    <linearGradient id="anatomicalBodyGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" stop-color="#C5CACC" />
                                        <stop offset="25%" stop-color="#E8ECEE" />
                                        <stop offset="50%" stop-color="#F2F5F7" />
                                        <stop offset="75%" stop-color="#D0D5D8" />
                                        <stop offset="100%" stop-color="#9AA0A6" />
                                    </linearGradient>
                                </defs>

                                <!-- DROP SHADOW AT BASE -->
                                <ellipse cx="68" cy="214" rx="20" ry="3.5" fill="#000000" opacity="0.12" />

                                <!-- REALISTIC PROPORTIONAL HUMAN MANNEQUIN (FULL VOLUME ARMS) -->
                                <g stroke="#2C3036" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                                    
                                    <!-- Head & Neck -->
                                    <ellipse cx="68" cy="17" rx="7" ry="9" fill="url(#anatomicalBodyGrad)" />
                                    <path d="M 65 25 L 63 33 M 71 25 L 73 33" stroke-width="1.2" />

                                    <!-- Shoulders (Symmetrical Deltoid Caps) -->
                                    <path d="M 63 33 C 58 33, 48 36, 42 40 C 37 43, 36 50, 39 56 L 43 56 C 47 52, 49 46, 52 44 M 73 33 C 78 33, 88 36, 94 40 C 99 43, 100 50, 97 56 L 93 56 C 89 52, 87 46, 84 44" fill="url(#anatomicalBodyGrad)" />

                                    <!-- Left Arm (Full Volume Bicep, Forearm, Hand & Fingers) -->
                                    <path d="M 42 40 C 37 43, 35 52, 33 64 C 31 74, 29 82, 27 92 C 25 96, 23 100, 22 104 C 21 106, 23 107, 25 106 C 27 104, 28 98, 30 92 C 33 82, 36 74, 38 64 C 40 54, 42 48, 43 56 Z" fill="url(#anatomicalBodyGrad)" />
                                    <path d="M 22 104 C 20 106, 18 108, 17 110 M 23 105 C 21 108, 20 110, 19 112 M 24 105 C 23 108, 22 110, 21 112 M 25 104 C 25 107, 24 109, 23 111" fill="none" stroke-width="0.8" />
                                    
                                    <!-- Right Arm (Full Volume Bicep, Forearm, Hand & Fingers) -->
                                    <path d="M 94 40 C 99 43, 101 52, 103 64 C 105 74, 107 82, 109 92 C 111 96, 113 100, 114 104 C 115 106, 113 107, 111 106 C 109 104, 108 98, 106 92 C 103 82, 100 74, 98 64 C 96 54, 94 48, 93 56 Z" fill="url(#anatomicalBodyGrad)" />
                                    <path d="M 114 104 C 116 106, 118 108, 119 110 M 113 105 C 115 108, 116 110, 117 112 M 112 105 C 113 108, 114 110, 115 112 M 111 104 C 111 107, 112 109, 113 111" fill="none" stroke-width="0.8" />

                                    <!-- Torso & Waist -->
                                    <path d="M 52 44 L 54 75 L 52 92 L 68 106 L 84 92 L 82 75 L 84 44 Z" fill="url(#anatomicalBodyGrad)" />

                                    <!-- Lower Body (Thighs, Knees, Calves, Feet) -->
                                    <!-- Left Leg -->
                                    <path d="M 52 92 C 50 105, 49 122, 53 138 C 55 144, 55 152, 54 162 C 52 175, 52 192, 54 205 L 48 210 L 58 210 L 59 203 C 60 190, 60 175, 60 162 C 60 152, 60 144, 62 138 C 66 122, 66 105, 68 106 Z" fill="url(#anatomicalBodyGrad)" />
                                    <!-- Right Leg -->
                                    <path d="M 84 92 C 86 105, 87 122, 83 138 C 81 144, 81 152, 82 162 C 84 175, 84 192, 82 205 L 88 210 L 78 210 L 77 203 C 76 190, 76 175, 76 162 C 76 152, 76 144, 74 138 C 70 122, 70 105, 68 106 Z" fill="url(#anatomicalBodyGrad)" />

                                    <!-- ORANGE PLUMB LINE -->
                                    <line x1="68" y1="8" x2="68" y2="211" stroke="#FF8200" stroke-width="1.3" />

                                    <!-- RED HORIZONTAL GUIDELINES -->
                                    <line x1="51" y1="116" x2="85" y2="116" stroke="#D32F2F" stroke-width="1.1" />
                                    <line x1="55" y1="168" x2="81" y2="168" stroke="#D32F2F" stroke-width="1.1" />

                                    <!-- ANATOMICAL DEFINITION LINES -->
                                    <g stroke="#3A3F46" stroke-width="0.9" fill="none">
                                        <!-- Collarbone -->
                                        <path d="M 68 35 C 60 34, 52 37, 46 40 M 68 35 C 76 34, 84 37, 90 40" stroke-width="1" />
                                        <!-- Chest / Pectorals -->
                                        <path d="M 52 44 C 60 43, 67 47, 68 54 C 60 56, 52 52, 52 44 Z" fill="#E2E7EC" opacity="0.6" />
                                        <path d="M 84 44 C 76 43, 69 47, 68 54 C 76 56, 84 52, 84 44 Z" fill="#E2E7EC" opacity="0.6" />
                                        <!-- Abs (6-Pack Grid) -->
                                        <path d="M 58 58 C 64 57, 72 57, 78 58" />
                                        <path d="M 58 66 C 64 65, 72 65, 78 66" />
                                        <path d="M 59 74 C 64 73, 72 73, 77 74" />
                                        <!-- Arm Muscle Separation Creases -->
                                        <path d="M 39 56 C 37 62, 35 70, 33 78" stroke-width="0.75" />
                                        <path d="M 97 56 C 99 62, 101 70, 103 78" stroke-width="0.75" />
                                        <!-- Inguinal Crease -->
                                        <path d="M 52 92 C 58 98, 64 103, 68 106 M 84 92 C 78 98, 72 103, 68 106" stroke-width="1" />
                                        <!-- Quads Definition -->
                                        <path d="M 52 96 C 49 108, 50 125, 57 138" />
                                        <path d="M 84 96 C 87 108, 86 125, 79 138" />
                                        <!-- Knees -->
                                        <ellipse cx="57" cy="142" rx="3" ry="3.5" stroke-width="0.9" fill="#E8EDF2" />
                                        <ellipse cx="79" cy="142" rx="3" ry="3.5" stroke-width="0.9" fill="#E8EDF2" />
                                        <!-- Calves Definition -->
                                        <path d="M 54 150 C 51 160, 52 178, 56 195" />
                                        <path d="M 82 150 C 85 160, 84 178, 80 195" />
                                    </g>
                                </g>

                                <!-- NODES & CALLOUT LINES / BADGES -->
                                <!-- Node 1: Left Shoulder IR/ER (Orange) -->
                                <circle cx="91" cy="46" r="3.5" fill="#FF8200" stroke="#FFFFFF" stroke-width="1" />
                                <line x1="91" y1="46" x2="118" y2="46" stroke="#FF8200" stroke-width="1.8" stroke-dasharray="2,2" />
                                <rect x="112" y="39" width="14" height="14" rx="3" fill="#FF8200" />
                                <text x="119" y="50" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">1</text>

                                <!-- Node 2: ISO-Y Spine/Thoracic (Orange) -->
                                <circle cx="68" cy="54" r="3.5" fill="#FF8200" stroke="#FFFFFF" stroke-width="1" />
                                <line x1="68" y1="54" x2="118" y2="68" stroke="#FF8200" stroke-width="1.8" stroke-dasharray="2,2" />
                                <rect x="112" y="61" width="14" height="14" rx="3" fill="#FF8200" />
                                <text x="119" y="72" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">2</text>

                                <!-- Node 3: Hip Adduction (Blue) -->
                                <circle cx="74" cy="122" r="3.5" fill="#4895DB" stroke="#FFFFFF" stroke-width="1" />
                                <line x1="74" y1="122" x2="118" y2="122" stroke="#4895DB" stroke-width="1.8" stroke-dasharray="2,2" />
                                <rect x="112" y="115" width="14" height="14" rx="3" fill="#4895DB" />
                                <text x="119" y="126" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">3</text>

                                <!-- Node 4: Hip Abduction (Blue) -->
                                <circle cx="53" cy="116" r="3.5" fill="#4895DB" stroke="#FFFFFF" stroke-width="1" />
                                <line x1="53" y1="116" x2="22" y2="116" stroke="#4895DB" stroke-width="1.8" stroke-dasharray="2,2" />
                                <rect x="14" y="109" width="14" height="14" rx="3" fill="#4895DB" />
                                <text x="21" y="120" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">4</text>

                                <!-- Node 5: Single Leg Calf Raise (Blue) -->
                                <circle cx="77" cy="172" r="3.5" fill="#4895DB" stroke="#FFFFFF" stroke-width="1" />
                                <line x1="77" y1="172" x2="118" y2="172" stroke="#4895DB" stroke-width="1.8" stroke-dasharray="2,2" />
                                <rect x="112" y="165" width="14" height="14" rx="3" fill="#4895DB" />
                                <text x="119" y="176" font-size="9" font-weight="900" fill="#FFFFFF" text-anchor="middle">5</text>
                            </svg>
                        </div>
                    </div>
                    """
                    components.html(hud_svg_html, height=450)

                # --- RIGHT PANEL: LIGHT DETAILS CARDS ---
                with hud_col2:
                    st.markdown(
                        """
                        <style>
                        .hud-details-card {
                            background: #FFFFFF;
                            border-radius: 16px;
                            padding: 20px;
                            border: 1px solid #E5E5E7;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
                        }
                        .hud-header-title-light {
                            color: #1D1D1F;
                            font-weight: 800;
                            font-size: 13px;
                            letter-spacing: 1px;
                            text-transform: uppercase;
                            border-bottom: 2px solid #FF8200;
                            padding-bottom: 6px;
                            margin-bottom: 16px;
                        }
                        .hud-metric-row-light {
                            background: #F8F9FA;
                            border-left: 4px solid #FF8200;
                            border-radius: 8px;
                            padding: 10px 14px;
                            margin-bottom: 10px;
                            color: #1D1D1F;
                            border-top: 1px solid #E5E5E7;
                            border-right: 1px solid #E5E5E7;
                            border-bottom: 1px solid #E5E5E7;
                        }
                        .hud-metric-row-light-blue {
                            background: #F8F9FA;
                            border-left: 4px solid #4895DB;
                            border-radius: 8px;
                            padding: 10px 14px;
                            margin-bottom: 10px;
                            color: #1D1D1F;
                            border-top: 1px solid #E5E5E7;
                            border-right: 1px solid #E5E5E7;
                            border-bottom: 1px solid #E5E5E7;
                        }
                        .node-badge-orange {
                            display: inline-block;
                            width: 20px;
                            height: 20px;
                            background: #FF8200;
                            color: #FFFFFF;
                            font-weight: 900;
                            font-size: 11px;
                            border-radius: 4px;
                            text-align: center;
                            line-height: 20px;
                            margin-right: 8px;
                        }
                        .node-badge-blue {
                            display: inline-block;
                            width: 20px;
                            height: 20px;
                            background: #4895DB;
                            color: #FFFFFF;
                            font-weight: 900;
                            font-size: 11px;
                            border-radius: 4px;
                            text-align: center;
                            line-height: 20px;
                            margin-right: 8px;
                        }
                        </style>
                        <div class="hud-details-card">
                            <div class="hud-header-title-light">Anatomy Location Assessment Details</div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # NODE 1: KNEE EXTENSION & FLEXION
                    if not sh_ath.empty:
                        knee_ext = sh_ath[sh_ath['TestDirection'].str.contains('Extension', case=False, na=False)] if 'TestDirection' in sh_ath.columns else sh_ath
                        knee_flx = sh_ath[sh_ath['TestDirection'].str.contains('Flexion', case=False, na=False)] if 'TestDirection' in sh_ath.columns else sh_ath

                        ke_b = knee_ext.iloc[0] if not knee_ext.empty else pd.Series()
                        ke_l = knee_ext.iloc[-1] if not knee_ext.empty else pd.Series()
                        kf_b = knee_flx.iloc[0] if not knee_flx.empty else pd.Series()
                        kf_l = knee_flx.iloc[-1] if not knee_flx.empty else pd.Series()

                        ke_bL, ke_bR = ke_b.get('L Max Force (N)', 0.0), ke_b.get('R Max Force (N)', 0.0)
                        ke_lL, ke_lR = ke_l.get('L Max Force (N)', 0.0), ke_l.get('R Max Force (N)', 0.0)
                        kf_bL, kf_bR = kf_b.get('L Max Force (N)', 0.0), kf_b.get('R Max Force (N)', 0.0)
                        kf_lL, kf_lR = kf_l.get('L Max Force (N)', 0.0), kf_l.get('R Max Force (N)', 0.0)

                        latest_date_str = ke_l.get('Date', pd.Timestamp.now()).strftime('%m/%d/%Y') if pd.notna(ke_l.get('Date')) else "N/A"

                        st.markdown(f"""
                            <div class="hud-metric-row-light">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                    <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-orange">1</span>KNEE EXTENSION & FLEXION</span>
                                    <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {latest_date_str}</span>
                                </div>
                                <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                    <b>Extension:</b> Initial L {ke_bL:.1f}N | R {ke_bR:.1f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(ke_lL, ke_bL, '{:.1f}', 'N')} | R {render_val_with_arrow(ke_lR, ke_bR, '{:.1f}', 'N')}<br>
                                    <b>Flexion:</b> Initial L {kf_bL:.1f}N | R {kf_bR:.1f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(kf_lL, kf_bL, '{:.1f}', 'N')} | R {render_val_with_arrow(kf_lR, kf_bR, '{:.1f}', 'N')}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    # NODE 2: NORDIC HAMSTRING
                    if not isoy_ath.empty:
                        b_n, l_n = isoy_ath.iloc[0], isoy_ath.iloc[-1]
                        bnL, bnR = b_n.get('L Max Force (N)', 0.0), b_n.get('R Max Force (N)', 0.0)
                        lnL, lnR = l_n.get('L Max Force (N)', 0.0), l_n.get('R Max Force (N)', 0.0)
                        date_str = l_n['Date'].strftime('%m/%d/%Y') if pd.notna(l_n.get('Date')) else "N/A"

                        st.markdown(f"""
                            <div class="hud-metric-row-light">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                    <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-orange">2</span>NORDIC HAMSTRING STRENGTH</span>
                                    <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                                </div>
                                <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                    <b>Initial Force:</b> L {bnL:.1f}N | R {bnR:.1f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(lnL, bnL, '{:.1f}', 'N')} | R {render_val_with_arrow(lnR, bnR, '{:.1f}', 'N')}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    # NODE 3 & 4: HIP AD/AB
                    if not hip_ath.empty:
                        hip_ad = hip_ath[hip_ath['TestDirection'].str.contains('AD|Adduction', case=False, na=False)] if 'TestDirection' in hip_ath.columns else hip_ath
                        hip_ab = hip_ath[hip_ath['TestDirection'].str.contains('AB|Abduction', case=False, na=False)] if 'TestDirection' in hip_ath.columns else hip_ath

                        if not hip_ad.empty:
                            ad_b, ad_l = hip_ad.iloc[0], hip_ad.iloc[-1]
                            ad_bL, ad_bR = ad_b.get('L Max Force (N)', 0.0), ad_b.get('R Max Force (N)', 0.0)
                            ad_lL, ad_lR = ad_l.get('L Max Force (N)', 0.0), ad_l.get('R Max Force (N)', 0.0)
                            date_str = ad_l['Date'].strftime('%m/%d/%Y') if pd.notna(ad_l.get('Date')) else "N/A"

                            st.markdown(f"""
                                <div class="hud-metric-row-light-blue">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                        <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">3</span>HIP ADDUCTION (AD)</span>
                                        <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                                    </div>
                                    <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                        <b>Initial Force:</b> L {ad_bL:.1f}N | R {ad_bR:.1f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(ad_lL, ad_bL, '{:.1f}', 'N')} | R {render_val_with_arrow(ad_lR, ad_bR, '{:.1f}', 'N')}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                        if not hip_ab.empty:
                            ab_b, ab_l = hip_ab.iloc[0], hip_ab.iloc[-1]
                            ab_bL, ab_bR = ab_b.get('L Max Force (N)', 0.0), ab_b.get('R Max Force (N)', 0.0)
                            ab_lL, ab_lR = ab_l.get('L Max Force (N)', 0.0), ab_l.get('R Max Force (N)', 0.0)
                            date_str = ab_l['Date'].strftime('%m/%d/%Y') if pd.notna(ab_l.get('Date')) else "N/A"

                            st.markdown(f"""
                                <div class="hud-metric-row-light-blue">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                        <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">4</span>HIP ABDUCTION (AB)</span>
                                        <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                                    </div>
                                    <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                        <b>Initial Force:</b> L {ab_bL:.1f}N | R {ab_bR:.1f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(ab_lL, ab_bL, '{:.1f}', 'N')} | R {render_val_with_arrow(ab_lR, ab_bR, '{:.1f}', 'N')}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                    # NODE 5: ANKLE PLANTAR FLEXION
                    if not calf_ath.empty:
                        b_a, l_a = calf_ath.iloc[0], calf_ath.iloc[-1]
                        baL, baR = b_a.get('L Max Force (N)', 0.0), b_a.get('R Max Force (N)', 0.0)
                        laL, laR = l_a.get('L Max Force (N)', 0.0), l_a.get('R Max Force (N)', 0.0)
                        date_str = l_a['Date'].strftime('%m/%d/%Y') if pd.notna(l_a.get('Date')) else "N/A"

                        st.markdown(f"""
                            <div class="hud-metric-row-light-blue">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                    <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">5</span>ANKLE PLANTAR FLEXION</span>
                                    <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                                </div>
                                <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                    <b>Initial Force:</b> L {baL:.1f}N | R {baR:.1f}N &nbsp;→&nbsp; <b>Latest:</b> L {render_val_with_arrow(laL, baL, '{:.1f}', 'N')} | R {render_val_with_arrow(laR, baR, '{:.1f}', 'N')}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.info(f"No Intake Assessment records found for {selected_intake_athlete}.")
