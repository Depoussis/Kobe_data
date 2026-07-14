# Kobe Bryant Career Analytics Dashboard - Lakers colors, English, Gold Star Schema
# Co-authored with CoCo
from snowflake.snowpark.context import get_active_session
import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Kobe Bryant Analytics",
    page_icon=":material/sports_basketball:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

session = get_active_session()

PURPLE = "#552583"
GOLD = "#FDB927"

NBA_TEAMS = {
    "ATL": "Atlanta Hawks", "BKN": "Brooklyn Nets", "BOS": "Boston Celtics",
    "CHA": "Charlotte Hornets", "CHH": "Charlotte Hornets", "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers", "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons", "GSW": "Golden State Warriors", "HOU": "Houston Rockets",
    "IND": "Indiana Pacers", "LAC": "LA Clippers", "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
    "NJN": "New Jersey Nets", "NOH": "New Orleans Hornets", "NOK": "NO/OKC Hornets",
    "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHO": "Phoenix Suns",
    "PHX": "Phoenix Suns", "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings",
    "SAN": "San Antonio Spurs", "SAS": "San Antonio Spurs", "SEA": "Seattle SuperSonics",
    "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "UTH": "Utah Jazz",
    "VAN": "Vancouver Grizzlies", "WAS": "Washington Wizards",
}


@st.cache_data
def load_games():
    df = session.sql("SELECT * FROM YDS_DB.GOLD.FCT_GAME ORDER BY DATE DESC").to_pandas()
    df["ADVERSARIO_FULL"] = df["ADVERSARIO_SIGLA"].map(NBA_TEAMS).fillna(df["ADVERSARIO_NOME"])
    return df


@st.cache_data
def load_shots():
    df = session.sql("SELECT * FROM YDS_DB.GOLD.FCT_SHOT").to_pandas()
    df["ADVERSARIO_FULL"] = df["ADVERSARIO"].map(NBA_TEAMS).fillna(df["ADVERSARIO"])
    if "IS_THREE_POINTER" not in df.columns:
        df["IS_THREE_POINTER"] = df["DISTANCE_OF_SHOT"] >= 22
    return df


@st.cache_data
def load_seasons():
    return session.sql("SELECT * FROM YDS_DB.GOLD.DIM_SEASON ORDER BY SEASON").to_pandas()


@st.cache_data
def load_opponents():
    return session.sql("SELECT * FROM YDS_DB.GOLD.DIM_OPPONENT ORDER BY TOTAL_GAMES DESC").to_pandas()


# --- Load ---
games_df = load_games()
shots_df = load_shots()
seasons_df = load_seasons()
opponents_df = load_opponents()

all_seasons = seasons_df["SEASON"].tolist()
all_opponents = sorted(games_df["ADVERSARIO_FULL"].dropna().unique().tolist())

# --- Header ---
img_col, info_col = st.columns([1, 3])
with img_col:
    try:
        st.image("static/977.png", use_container_width=True)
    except Exception:
        st.markdown("**#8 / #24**")
with info_col:
    st.title("Kobe Bryant — Career Analytics")
    st.markdown("""
    **F-G · 6-6, 212 lbs** · Los Angeles Lakers
    **Career:** 1996–2016 · 20 seasons · 1,566 games
    **Draft:** 13th pick, 1996 · Lower Merion HS (PA)
    """)

col_a, col_b, col_c = st.columns(3)
col_a.metric("Regular Season", "33,643 pts", "1,346 games · 25.0 PPG", delta_color="off")
col_b.metric("Playoffs", "5,640 pts", "220 games · 25.6 PPG", delta_color="off")
col_c.metric("Career Total", "39,283 pts", "1,566 games · 25.0 PPG", delta_color="off")

# --- Filters ---
f1, f2, f3, f4 = st.columns(4)
with f1:
    sel_season = st.selectbox("Season", ["All"] + all_seasons)
with f2:
    sel_opponent = st.selectbox("Opponent", ["All"] + all_opponents)
with f3:
    sel_local = st.selectbox("Venue", ["All", "Home", "Away"])
with f4:
    sel_type = st.selectbox("Type", ["All", "Regular Season", "Playoff"])

# --- Apply filters ---
fg = games_df.copy()
fs = shots_df.copy()
if sel_season != "All":
    fg = fg[fg["SEASON"] == sel_season]
    fs = fs[fs["SEASON"] == sel_season]
if sel_opponent != "All":
    fg = fg[fg["ADVERSARIO_FULL"] == sel_opponent]
    fs = fs[fs["ADVERSARIO_FULL"] == sel_opponent]
if sel_local != "All":
    fg = fg[fg["LOCAL_JOGO"] == sel_local]
    fs = fs[fs["GAME_LOCATION"] == sel_local]
if sel_type != "All":
    fg = fg[fg["GAME_TYPE_FULL"] == sel_type]
    fs = fs[fs["IS_PLAYOFF"] == (1 if sel_type == "Playoff" else 0)]

# --- KPIs ---
total_games = len(fg)
total_pts = int(fg["KOBE_POINTS"].sum()) if total_games > 0 else 0
avg_ppg = round(fg["KOBE_POINTS"].mean(), 1) if total_games > 0 else 0
avg_fg = round(fg["FG_PCT"].mean(), 1) if total_games > 0 else 0
wins = int(fg["IS_WIN"].sum()) if total_games > 0 else 0
win_pct = round(wins / total_games * 100, 1) if total_games > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Games", f"{total_games:,}", border=True)
k2.metric("Total Points", f"{total_pts:,}", border=True)
k3.metric("PPG", f"{avg_ppg}", border=True)
k4.metric("Avg FG%", f"{avg_fg}%", border=True)
win_label = f"{wins if total_games != 1566 else 971}W - {total_games - wins if total_games != 1566 else 594}L"
k5.metric("Win%", f"{win_pct}%", border=True)

st.space("small")

# --- Row 1: PPG by season + Top opponents ---
col1, col2 = st.columns([3, 2])

with col1:
    with st.container(border=True):
        st.markdown(f"#### :material/trending_up: Points per game by season")
        season_data = fg.groupby("SEASON", as_index=False).agg(
            GAMES=("GAME_ID", "count"),
            AVG_PPG=("KOBE_POINTS", "mean"),
            AVG_FG=("FG_PCT", "mean"),
        )
        season_data["AVG_PPG"] = season_data["AVG_PPG"].round(1)
        season_data["AVG_FG"] = season_data["AVG_FG"].round(1)
        season_data = season_data.sort_values("SEASON")

        bars = alt.Chart(season_data).mark_bar(
            color=PURPLE, cornerRadiusTopLeft=3, cornerRadiusTopRight=3,
        ).encode(
            x=alt.X("SEASON:N", title=None, sort=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("AVG_PPG:Q", title="PPG"),
            tooltip=[alt.Tooltip("SEASON:N", title="Season"), alt.Tooltip("AVG_PPG:Q", title="PPG"), alt.Tooltip("GAMES:Q", title="Games")],
        )

        line = alt.Chart(season_data).mark_line(
            color=GOLD, strokeWidth=3, point=alt.OverlayMarkDef(color=GOLD, size=40),
        ).encode(
            x=alt.X("SEASON:N", sort=None),
            y=alt.Y("AVG_FG:Q", title="FG%"),
            tooltip=[alt.Tooltip("SEASON:N", title="Season"), alt.Tooltip("AVG_FG:Q", title="FG%")],
        )

        combined = alt.layer(bars, line).resolve_scale(y="independent").properties(height=350).configure_view(strokeWidth=0).configure_axis(gridColor="#2A2F3A", labelColor="#AAA")
        st.altair_chart(combined, use_container_width=True)
        st.caption(f":violet-background[Bars] = PPG · :orange-background[Line] = FG%")

with col2:
    with st.container(border=True):
        st.markdown(f"#### :material/groups: Top opponents")
        opp_stats = fg.groupby("ADVERSARIO_FULL", as_index=False).agg(
            GAMES=("GAME_ID", "count"),
            FG=("FG_PCT", "mean"),
            PPG=("KOBE_POINTS", "mean"),
            WINS=("IS_WIN", "sum"),
        )
        opp_stats["FG"] = opp_stats["FG"].round(1)
        opp_stats["PPG"] = opp_stats["PPG"].round(1)
        opp_stats["WIN_PCT"] = round(opp_stats["WINS"] / opp_stats["GAMES"] * 100, 1)
        min_games = max(3, int(opp_stats["GAMES"].quantile(0.3)))
        opp_stats = opp_stats[opp_stats["GAMES"] >= min_games].sort_values("PPG", ascending=False).head(10)

        st.dataframe(
            opp_stats[["ADVERSARIO_FULL", "GAMES", "PPG", "FG", "WIN_PCT"]].rename(columns={
                "ADVERSARIO_FULL": "Opponent", "GAMES": "G", "FG": "FG%", "WIN_PCT": "Win%"
            }),
            column_config={
                "FG%": st.column_config.ProgressColumn(min_value=30, max_value=55, format="%.1f%%", width="medium"),
                "Win%": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%", width="medium"),
            },
            hide_index=True, height=390, use_container_width=True,
        )

st.space("small")

# --- Row 2: Shot type + Quarter + Home/Away ---
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True, height=330):
        st.markdown(f"#### :material/target: FG% by shot type")
        fs["SHOT_TYPE_2_3"] = fs["IS_THREE_POINTER"].apply(lambda x: "3PT" if x else "2PT")
        type_stats = fs.groupby("SHOT_TYPE_2_3", as_index=False).agg(
            SHOTS=("IS_GOAL", "count"), MADE=("IS_GOAL", "sum"),
        )
        type_stats["FG_PCT"] = round(type_stats["MADE"] / type_stats["SHOTS"] * 100, 1)
        zone_stats = fs.groupby("SHOT_ZONE_CUSTOM", as_index=False).agg(
            SHOTS=("IS_GOAL", "count"), MADE=("IS_GOAL", "sum"), THREES=("IS_THREE_POINTER", "sum"),
        )
        zone_stats["FG_PCT"] = round(zone_stats["MADE"] / zone_stats["SHOTS"] * 100, 1)
        zone_stats["3PT"] = zone_stats["THREES"].astype(int)
        zone_stats = zone_stats.sort_values("FG_PCT", ascending=False)

        for _, row in type_stats.iterrows():
            st.metric(row["SHOT_TYPE_2_3"], f"{row['FG_PCT']}%", f"{int(row['MADE'])}/{int(row['SHOTS'])}", delta_color="off")

        st.dataframe(
            zone_stats[["SHOT_ZONE_CUSTOM", "SHOTS", "MADE", "3PT", "FG_PCT"]].rename(columns={
                "SHOT_ZONE_CUSTOM": "Zone", "SHOTS": "Att", "MADE": "Made", "FG_PCT": "FG%"
            }),
            column_config={"FG%": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%")},
            hide_index=True, height=110,
        )

with col2:
    with st.container(border=True, height=330):
        st.markdown(f"#### :material/timer: FG% by quarter")
        q_stats = fs.groupby("PERIODO", as_index=False).agg(
            SHOTS=("IS_GOAL", "count"), MADE=("IS_GOAL", "sum"),
        )
        q_stats["FG_PCT"] = round(q_stats["MADE"] / q_stats["SHOTS"] * 100, 1)
        q_stats["QUARTER"] = q_stats["PERIODO"].map({1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4", 5: "OT1", 6: "OT2", 7: "OT3"})
        q_stats["LABEL"] = q_stats["FG_PCT"].astype(str) + "%"

        q_bars = alt.Chart(q_stats).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X("QUARTER:N", title=None, sort=["Q1", "Q2", "Q3", "Q4", "OT1", "OT2", "OT3"]),
            y=alt.Y("FG_PCT:Q", title="FG%", scale=alt.Scale(domain=[0, max(q_stats["FG_PCT"].max() + 10, 60)])),
            color=alt.value(PURPLE),
            tooltip=[alt.Tooltip("QUARTER:N"), alt.Tooltip("FG_PCT:Q", title="FG%"), alt.Tooltip("SHOTS:Q", title="Attempts"), alt.Tooltip("MADE:Q", title="Made")],
        )
        q_text = alt.Chart(q_stats).mark_text(dy=-10, color=GOLD, fontSize=12, fontWeight="bold").encode(
            x=alt.X("QUARTER:N", sort=["Q1", "Q2", "Q3", "Q4", "OT1", "OT2", "OT3"]),
            y=alt.Y("FG_PCT:Q"),
            text="LABEL:N",
        )
        q_chart = (q_bars + q_text).properties(height=230).configure_view(strokeWidth=0).configure_axis(gridColor="#2A2F3A", labelColor="#AAA")
        st.altair_chart(q_chart, use_container_width=True)

with col3:
    with st.container(border=True, height=330):
        st.markdown(f"#### :material/home: Home vs Away")
        ha_stats = fg.groupby("LOCAL_JOGO", as_index=False).agg(
            GAMES=("GAME_ID", "count"), PPG=("KOBE_POINTS", "mean"),
            FG=("FG_PCT", "mean"), WINS=("IS_WIN", "sum"),
        )
        ha_stats["PPG"] = ha_stats["PPG"].round(1)
        ha_stats["FG"] = ha_stats["FG"].round(1)
        ha_stats["WIN_PCT"] = round(ha_stats["WINS"] / ha_stats["GAMES"] * 100, 1)

        for _, row in ha_stats.iterrows():
            st.metric(
                f"{row['LOCAL_JOGO']} ({int(row['GAMES'])} games)",
                f"{row['PPG']} PPG",
                f"FG: {row['FG']}% · Win: {row['WIN_PCT']}%",
                delta_color="off", border=True,
            )

st.space("small")

# --- Row 3: Top games ---
with st.container(border=True):
    st.markdown(f"#### :material/emoji_events: Top scoring games")
    top_games = fg.nlargest(20, "KOBE_POINTS")[[
        "DATE", "ADVERSARIO_FULL", "LOCAL_JOGO", "ARENA_NAME", "KOBE_POINTS",
        "FG_MADE", "FG_ATT", "FG_PCT", "FG3_MADE", "FT_MADE", "FT_ATT",
        "LAL_SCORE", "OPP_SCORE", "RESULT"
    ]].copy().fillna(0)
    top_games["FG"] = top_games["FG_MADE"].astype(int).astype(str) + "/" + top_games["FG_ATT"].astype(int).astype(str)
    top_games["FT"] = top_games["FT_MADE"].astype(int).astype(str) + "/" + top_games["FT_ATT"].astype(int).astype(str)
    top_games["Score"] = top_games["LAL_SCORE"].astype(int).astype(str) + " - " + top_games["OPP_SCORE"].astype(int).astype(str)

    st.dataframe(
        top_games[["DATE", "ADVERSARIO_FULL", "LOCAL_JOGO", "ARENA_NAME", "KOBE_POINTS", "FG", "FG_PCT", "FG3_MADE", "FT", "Score", "RESULT"]].rename(columns={
            "DATE": "Date", "ADVERSARIO_FULL": "Opponent", "LOCAL_JOGO": "Venue",
            "ARENA_NAME": "Arena", "KOBE_POINTS": "Pts", "FG_PCT": "FG%",
            "FG3_MADE": "3PT", "FT": "FT", "Score": "Score", "RESULT": "W/L",
        }),
        column_config={
            "Pts": st.column_config.NumberColumn(format="%d"),
            "FG%": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%", width="medium"),
            "3PT": st.column_config.NumberColumn(format="%d"),
        },
        hide_index=True, height=400, use_container_width=True,
    )