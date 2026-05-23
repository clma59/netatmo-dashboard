import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sqlalchemy import create_engine

st.set_page_config(
    page_title="Météo Cambrin",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header {visibility: hidden;}
footer {visibility: hidden;}
.block-container {
    padding-top: 0.4rem;
    padding-left: 0.6rem;
    padding-right: 0.6rem;
}
h1 {
    font-size: 1.6rem !important;
    margin-bottom: 0rem !important;
}
h3 {
    margin-top: 0.5rem !important;
}
[data-testid="stMetric"] {
    padding: 0.2rem;
}
</style>
""", unsafe_allow_html=True)

DATABASE_URL = st.secrets["DATABASE_URL"]

engine = create_engine(DATABASE_URL)

@st.cache_data(ttl=300)
def load_data():
    query = """
    SELECT *
    FROM temperatures
    ORDER BY timestamp
    """

    df = pd.read_sql(query, engine)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        format="ISO8601"
    )

    return df

with st.spinner("Chargement des données météo..."):
    df = load_data()

df["date"] = df["timestamp"].dt.date
df["year"] = df["timestamp"].dt.year

last_row = df.iloc[-1]

today = pd.Timestamp.now().date()

today_df = df[df["timestamp"].dt.date == today]

if today_df.empty:
    today_df = df[df["timestamp"].dt.date == df["timestamp"].max().date()]

st.title("🌤 Météo Cambrin")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Température",
        f"{last_row['temperature']:.1f} °C"
    )

with col2:
    st.metric(
        "Humidité",
        f"{last_row['humidity']:.0f} %"
    )

col3, col4 = st.columns(2)

with col3:
    st.metric(
        "Min du jour",
        f"{today_df['temperature'].min():.1f} °C"
    )

with col4:
    st.metric(
        "Max du jour",
        f"{today_df['temperature'].max():.1f} °C"
    )

daily_df = (
    df
    .set_index("timestamp")
    .resample("D")
    .agg({
        "temperature": ["min", "max"]
    })
)

daily_df.columns = [
    "temp_min",
    "temp_max"
]

daily_df = daily_df.reset_index()

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=daily_df["timestamp"],
        y=daily_df["temp_min"],
        mode="lines+markers",
        name="Min",
        line=dict(
            color="royalblue",
            shape="spline",
            smoothing=1.2,
            width=3
        ),
        marker=dict(size=5),
        hovertemplate=
        "<b>%{x|%d/%m/%Y}</b><br>" +
        "Min : %{y:.1f} °C" +
        "<extra></extra>"
    )
)

fig.add_trace(
    go.Scatter(
        x=daily_df["timestamp"],
        y=daily_df["temp_max"],
        mode="lines+markers",
        name="Max",
        line=dict(
            color="red",
            shape="spline",
            smoothing=1.2,
            width=3
        ),
        marker=dict(size=5),
        hovertemplate=
        "<b>%{x|%d/%m/%Y}</b><br>" +
        "Max : %{y:.1f} °C" +
        "<extra></extra>"
    )
)

fig.update_layout(
    title="Évolution des températures",
    height=330,
    margin=dict(
        l=8,
        r=8,
        t=35,
        b=8
    ),
    xaxis=dict(
        title="",
        tickformat="%d/%m",
        rangeslider=dict(visible=True, thickness=0.08),
        rangeselector=dict(
            buttons=[
                dict(count=7, label="7 j", step="day", stepmode="backward"),
                dict(count=1, label="1 mois", step="month", stepmode="backward"),
                dict(count=6, label="6 mois", step="month", stepmode="backward"),
                dict(step="all", label="Tout")
            ],
            font=dict(size=10)
        )
    ),
    yaxis=dict(
        title="°C",
        fixedrange=True
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
        font=dict(size=11)
    ),
    hovermode="x unified",
    dragmode="pan"
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displayModeBar": False,
        "scrollZoom": False,
        "locale": "fr"
    }
)

annual_stats = (
    df
    .groupby("year")
    .agg({
        "temperature": [
            "min",
            "max",
            "mean"
        ]
    })
)

annual_stats.columns = [
    "Min",
    "Max",
    "Moyenne"
]

annual_stats = annual_stats.round(1)

with st.expander("Statistiques annuelles"):
    st.dataframe(
        annual_stats,
        use_container_width=True
    )