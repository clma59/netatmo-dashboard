import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sqlalchemy import create_engine

# ======================================
# CONFIG PAGE
# ======================================

st.set_page_config(
    page_title="Météo Cambrin",
    layout="wide"
)

# ======================================
# SUPABASE
# ======================================

DATABASE_URL = "postgresql://postgres.dqzlpzlylcpinfldzjja:netatmo2026@aws-1-eu-central-1.pooler.supabase.com:6543/postgres"

engine = create_engine(DATABASE_URL)

# ======================================
# CHARGEMENT DONNÉES
# ======================================

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

# ======================================
# PRÉPARATION
# ======================================

df["year"] = df["timestamp"].dt.year

last_row = df.iloc[-1]

today = pd.Timestamp.now().date()

today_df = df[
    df["timestamp"].dt.date == today
]

if today_df.empty:

    today_df = df[
        df["timestamp"].dt.date == df["timestamp"].max().date()
    ]

# ======================================
# TITRE
# ======================================

st.title("🌤 Météo Cambrin")

st.caption("Station météo personnelle")

# ======================================
# KPIs
# ======================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🌡 Température actuelle",
        f"{last_row['temperature']:.1f} °C"
    )

with col2:
    st.metric(
        "💧 Humidité actuelle",
        f"{last_row['humidity']:.0f} %"
    )

with col3:
    st.metric(
        "🔵 Minimum du jour",
        f"{today_df['temperature'].min():.1f} °C"
    )

with col4:
    st.metric(
        "🔴 Maximum du jour",
        f"{today_df['temperature'].max():.1f} °C"
    )

# ======================================
# STATS JOUR
# ======================================

st.subheader("📊 Statistiques du jour")

col5, col6 = st.columns(2)

with col5:
    st.metric(
        "Moyenne du jour",
        f"{today_df['temperature'].mean():.1f} °C"
    )

with col6:
    st.metric(
        "Amplitude thermique",
        f"{today_df['temperature'].max() - today_df['temperature'].min():.1f} °C"
    )

# ======================================
# FILTRE
# ======================================

st.subheader("📈 Évolution des températures")

periode = st.selectbox(
    "Période",
    [
        "24 heures",
        "7 jours",
        "30 jours",
        "12 mois",
        "Tout l'historique"
    ]
)

if periode == "24 heures":

    filtered_df = df[
        df["timestamp"] >= (
            df["timestamp"].max() - pd.Timedelta(hours=24)
        )
    ]

elif periode == "7 jours":

    filtered_df = df[
        df["timestamp"] >= (
            df["timestamp"].max() - pd.Timedelta(days=7)
        )
    ]

elif periode == "30 jours":

    filtered_df = df[
        df["timestamp"] >= (
            df["timestamp"].max() - pd.Timedelta(days=30)
        )
    ]

elif periode == "12 mois":

    filtered_df = df[
        df["timestamp"] >= (
            df["timestamp"].max() - pd.Timedelta(days=365)
        )
    ]

else:

    filtered_df = df

# ======================================
# GRAPHIQUE
# ======================================

fig = go.Figure()

if periode == "24 heures":

    fig.add_trace(
        go.Scatter(
            x=filtered_df["timestamp"],
            y=filtered_df["temperature"],
            mode="lines",
            name="Température",
            line=dict(
                color="orange",
                shape="spline",
                smoothing=1.2,
                width=3
            ),
            hovertemplate=
            "<b>%{x|%d/%m/%Y %H:%M}</b><br>" +
            "Température : %{y:.1f}°C" +
            "<extra></extra>"
        )
    )

else:

    daily_df = (
        filtered_df
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

    # COURBE MIN

    fig.add_trace(
        go.Scatter(
            x=daily_df["timestamp"],
            y=daily_df["temp_min"],
            mode="lines",
            name="Min",
            line=dict(
                color="royalblue",
                shape="spline",
                smoothing=1.2,
                width=3
            ),
            hovertemplate=
            "<b>%{x|%d/%m/%Y}</b><br>" +
            "Min : %{y:.1f}°C" +
            "<extra></extra>"
        )
    )

    # COURBE MAX

    fig.add_trace(
        go.Scatter(
            x=daily_df["timestamp"],
            y=daily_df["temp_max"],
            mode="lines",
            name="Max",
            line=dict(
                color="red",
                shape="spline",
                smoothing=1.2,
                width=3
            ),
            hovertemplate=
            "<b>%{x|%d/%m/%Y}</b><br>" +
            "Max : %{y:.1f}°C" +
            "<extra></extra>"
        )
    )

# ======================================
# LAYOUT MOBILE
# ======================================

fig.update_layout(

    title="Évolution des températures",

    xaxis_title="",
    yaxis_title="°C",

    hovermode="x unified",

    dragmode="pan",

    height=420,

    margin=dict(
        l=10,
        r=10,
        t=40,
        b=10
    ),

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
        font=dict(size=11)
    )
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displayModeBar": False,
        "scrollZoom": False
    }
)

# ======================================
# STATS ANNUELLES
# ======================================

st.subheader("📚 Statistiques annuelles")

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
    "Température min",
    "Température max",
    "Température moyenne"
]

annual_stats = annual_stats.round(1)

st.dataframe(
    annual_stats,
    use_container_width=True
)