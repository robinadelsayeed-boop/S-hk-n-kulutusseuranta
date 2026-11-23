import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta

from sahko.kulutus import lue_kulutus_teksti


st.set_page_config(page_title="Sähkönkulutus", layout="wide")
st.title("Sähkönkulutuksen seuranta")

tiedosto = st.file_uploader("Lataa kulutuksen CSV-tiedosto", type=["csv"])

if tiedosto is not None:
    teksti = tiedosto.getvalue().decode("utf-8-sig")
    tulos = lue_kulutus_teksti(teksti)

    if tulos.virheet:
        st.warning(f"CSV-tiedostossa havaittiin {len(tulos.virheet)} virheellistä riviä.")

    if not tulos.vartit:
        st.error("Tiedostosta ei löytynyt käyttökelpoista kulutusdataa.")
        st.stop()

    df = pd.DataFrame({
        "aika": list(tulos.vartit.keys()),
        "kulutus": list(tulos.vartit.values())
    })

    df["aika"] = pd.to_datetime(df["aika"], utc=True).dt.tz_convert(
        "Europe/Helsinki"
    )
    df = df.sort_values("aika")

    df["paiva"] = df["aika"].dt.date
    df["viikon_alku"] = df["paiva"].apply(
        lambda paiva: paiva - timedelta(days=paiva.weekday())
    )
    df["kuukausi"] = df["aika"].dt.strftime("%Y-%m")

    yhteensa = df["kulutus"].sum()
    alku = df["aika"].min().strftime("%d.%m.%Y")
    loppu = df["aika"].max().strftime("%d.%m.%Y")

    col1, col2, col3 = st.columns(3)
    col1.metric("Kulutus yhteensä", f"{yhteensa:.2f} kWh")
    col2.metric("Alkupäivä", alku)
    col3.metric("Loppupäivä", loppu)

    st.divider()

    nakyma = st.segmented_control(
        "Kulutusnäkymä",
        options=["Kuukausi", "Viikko"],
        default="Kuukausi"
    )

    kuukaudet = sorted(df["kuukausi"].unique())
    valittu_kuukausi = st.selectbox("Kuukausi", kuukaudet)

    kuukauden_data = df[df["kuukausi"] == valittu_kuukausi]

    if nakyma == "Viikko":
        viikot = sorted(kuukauden_data["viikon_alku"].unique())

        def viikon_nimi(alku):
            loppu = alku + timedelta(days=6)
            return f"{alku.strftime('%d.%m.')} – {loppu.strftime('%d.%m.%Y')}"

        valittu_viikko = st.selectbox(
            "Viikko",
            viikot,
            format_func=viikon_nimi
        )

        nakyman_data = kuukauden_data[
            kuukauden_data["viikon_alku"] == valittu_viikko
        ]
    else:
        nakyman_data = kuukauden_data

    paivittainen = (
        nakyman_data.groupby("paiva")["kulutus"]
        .sum()
        .reset_index()
        .sort_values("paiva")
    )

    paivittainen["paivamaara"] = paivittainen["paiva"].apply(
        lambda p: p.strftime("%d.%m.")
    )

    paivat = paivittainen["paiva"].tolist()

    if (
        "valittu_paiva" not in st.session_state
        or st.session_state.valittu_paiva not in paivat
    ):
        st.session_state.valittu_paiva = paivat[0]

    vasen, oikea = st.columns([1.6, 1])

    with vasen:
        st.subheader("Päivittäinen kulutus")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=paivittainen["paivamaara"],
            y=paivittainen["kulutus"],
            customdata=paivittainen["paiva"].astype(str),
            hovertemplate="%{x}<br>Kulutus: %{y:.2f} kWh<extra></extra>"
        ))

        fig.update_layout(
            xaxis_title="Päivä",
            yaxis_title="Kulutus (kWh)",
            clickmode="event+select",
            margin=dict(l=10, r=10, t=20, b=10),
            height=400
        )

        tapahtuma = st.plotly_chart(
            fig,
            use_container_width=True,
            on_select="rerun",
            selection_mode="points"
        )

        pisteet = tapahtuma.selection.points

        if pisteet:
            indeksi = pisteet[-1].get("point_index")
            if indeksi is not None and 0 <= indeksi < len(paivat):
                st.session_state.valittu_paiva = paivat[indeksi]

    with oikea:
        valittu = st.session_state.valittu_paiva
        paivan_data = nakyman_data[
            nakyman_data["paiva"] == valittu
        ].copy()

        paivan_kulutus = paivan_data["kulutus"].sum()

        st.subheader(valittu.strftime("%d.%m.%Y"))
        st.metric("Päivän kulutus", f"{paivan_kulutus:.2f} kWh")

        paivan_data["kellonaika"] = paivan_data["aika"].dt.strftime("%H:%M")

        paiva_fig = go.Figure()
        paiva_fig.add_trace(go.Bar(
            x=paivan_data["kellonaika"],
            y=paivan_data["kulutus"],
            hovertemplate="%{x}<br>Kulutus: %{y:.3f} kWh<extra></extra>"
        ))

        paiva_fig.update_layout(
            xaxis_title="Kellonaika",
            yaxis_title="Kulutus (kWh)",
            margin=dict(l=10, r=10, t=20, b=10),
            height=400
        )

        st.plotly_chart(
            paiva_fig,
            use_container_width=True
        )

else:
    st.info("Lataa CSV-tiedosto nähdäksesi sähkönkulutuksen.")
