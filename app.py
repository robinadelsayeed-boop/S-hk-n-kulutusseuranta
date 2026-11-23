import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
from pathlib import Path

from sahko.kulutus import lue_kulutus_teksti
from sahko.hinnat import lue_hinnat
from sahko.laskenta import laske_kustannukset


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

    # Luetaan hintadata kulutuksen aikaväliltä
    alku_utc = min(tulos.vartit)
    loppu_utc = max(tulos.vartit) + timedelta(minutes=15)

    hintapolku = Path("data/esimerkki/hinnat_FI_2026-10.csv")

    if not hintapolku.exists():
        st.error("Esimerkkihintatiedostoa ei löytynyt.")
        st.stop()

    hinnat = lue_hinnat(hintapolku, alku_utc, loppu_utc)

    # Lasketaan kustannukset
    laskenta = laske_kustannukset(tulos.vartit, hinnat)

    # Yhdistetään laskennan tulokset käyttöliittymän DataFrameen
    df["aika_utc"] = pd.to_datetime(df["aika"], utc=True)
    df["hinta_snt_kwh"] = df["aika_utc"].map(hinnat)
    df["kustannus_eur"] = (
        df["kulutus"] * df["hinta_snt_kwh"] / 100
    )

    df["paiva"] = df["aika"].dt.date
    df["viikon_alku"] = df["paiva"].apply(
        lambda paiva: paiva - timedelta(days=paiva.weekday())
    )
    df["kuukausi"] = df["aika"].dt.strftime("%Y-%m")

    yhteensa = df["kulutus"].sum()
    alku = df["aika"].min().strftime("%d.%m.%Y")
    loppu = df["aika"].max().strftime("%d.%m.%Y")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Kulutus yhteensä", f"{yhteensa:.2f} kWh")
    col2.metric(
        "Kustannus yhteensä",
        f"{laskenta['kokonaiskustannus_eur']:.2f} €"
    )
    col3.metric(
        "Painotettu keskihinta",
        f"{laskenta['painotettu_keskihinta_snt_kwh']:.2f} snt/kWh"
        if laskenta["painotettu_keskihinta_snt_kwh"] is not None
        else "Ei saatavilla"
    )
    col4.metric("Alkupäivä", alku)
    col5.metric("Loppupäivä", loppu)

    if laskenta["puuttuvat_vartit"]:
        st.warning(
            f"{len(laskenta['puuttuvat_vartit'])} kulutusvartilta "
            "puuttuu hintatieto. Niitä ei ole laskettu kustannuksiin."
        )

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
        paivan_kustannus = paivan_data["kustannus_eur"].sum()

        paivan_keskihinta = (
            paivan_kustannus * 100 / paivan_kulutus
            if paivan_kulutus > 0
            else None
        )

        st.subheader(valittu.strftime("%d.%m.%Y"))

        st.metric("Päivän kulutus", f"{paivan_kulutus:.2f} kWh")
        st.metric("Päivän kustannus", f"{paivan_kustannus:.2f} €")

        st.metric(
            "Päivän keskihinta",
            f"{paivan_keskihinta:.2f} snt/kWh"
            if paivan_keskihinta is not None
            else "Ei saatavilla"
        )

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

    # --- Uudet tuntikohtaiset kuvaajat ---

    st.divider()
    st.header("Tuntikohtainen tarkastelu")

    # Ryhmitellään valitun päivän tiedot UTC-tunneittain.
    # Näin myös kesä- ja talviajan vaihtuminen käsitellään oikein.
    paivan_tunnit = paivan_data.copy()
    paivan_tunnit["tunti_utc"] = paivan_tunnit["aika_utc"].dt.floor("h")

    tuntidata = (
        paivan_tunnit.groupby("tunti_utc")
        .agg(
            kulutus_kwh=("kulutus", "sum"),
            kustannus_eur=(
                "kustannus_eur",
                lambda x: x.sum(min_count=1)
            )
        )
        .reset_index()
    )

    tuntidata["tunti"] = (
        tuntidata["tunti_utc"]
        .dt.tz_convert("Europe/Helsinki")
        .dt.strftime("%H:%M %z")
    )

    # 1. Tuntikohtainen kulutus
    st.subheader("Kulutus tunneittain")

    kulutus_fig = go.Figure()
    kulutus_fig.add_trace(go.Bar(
        x=tuntidata["tunti"],
        y=tuntidata["kulutus_kwh"],
        hovertemplate="%{x}<br>Kulutus: %{y:.3f} kWh<extra></extra>"
    ))

    kulutus_fig.update_layout(
        xaxis_title="Tunti",
        yaxis_title="Kulutus (kWh)",
        margin=dict(l=10, r=10, t=20, b=10),
        height=350
    )

    st.plotly_chart(kulutus_fig, use_container_width=True)

    # 2. Pörssisähkön hinta 15 minuutin tarkkuudella
    st.subheader("Pörssisähkön hinta päivän aikana")

    hinta_data = paivan_data.sort_values("aika_utc").copy()
    hinta_data["kellonaika"] = (
        hinta_data["aika"].dt.strftime("%H:%M")
    )

    hinta_fig = go.Figure()
    hinta_fig.add_trace(go.Scatter(
        x=hinta_data["kellonaika"],
        y=hinta_data["hinta_snt_kwh"],
        mode="lines+markers",
        connectgaps=False,
        hovertemplate=(
            "%{x}<br>Hinta: %{y:.3f} snt/kWh<extra></extra>"
        )
    ))

    hinta_fig.update_layout(
        xaxis_title="Kellonaika",
        yaxis_title="Hinta (snt/kWh)",
        margin=dict(l=10, r=10, t=20, b=10),
        height=350
    )

    st.plotly_chart(hinta_fig, use_container_width=True)

    # 3. Kalleimmat tunnit valitulla kuukausi-/viikkoaikavälillä
    st.subheader("Kalleimmat kulutustunnit")

    jakson_data = nakyman_data.copy()
    jakson_data["tunti_utc"] = jakson_data["aika_utc"].dt.floor("h")

    kustannus_tunnit = (
        jakson_data.groupby("tunti_utc")
        .agg(
            kustannus_eur=(
                "kustannus_eur",
                lambda x: x.sum(min_count=1)
            ),
            kulutus_kwh=("kulutus", "sum")
        )
        .reset_index()
        .dropna(subset=["kustannus_eur"])
        .sort_values("kustannus_eur", ascending=False)
        .head(10)
        .sort_values("kustannus_eur", ascending=True)
    )

    kustannus_tunnit["tunti"] = (
        kustannus_tunnit["tunti_utc"]
        .dt.tz_convert("Europe/Helsinki")
        .dt.strftime("%d.%m. %H:%M")
    )

    kustannus_fig = go.Figure()
    kustannus_fig.add_trace(go.Bar(
        x=kustannus_tunnit["kustannus_eur"],
        y=kustannus_tunnit["tunti"],
        orientation="h",
        customdata=kustannus_tunnit["kulutus_kwh"],
        hovertemplate=(
            "%{y}<br>"
            "Kustannus: %{x:.3f} €<br>"
            "Kulutus: %{customdata:.3f} kWh"
            "<extra></extra>"
        )
    ))

    kustannus_fig.update_layout(
        xaxis_title="Kustannus (€)",
        yaxis_title="Tunti",
        margin=dict(l=10, r=10, t=20, b=10),
        height=400
    )

    st.plotly_chart(kustannus_fig, use_container_width=True)


else:
    st.info("Lataa CSV-tiedosto nähdäksesi sähkönkulutuksen.")
