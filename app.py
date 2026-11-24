import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
from pathlib import Path

from sahko.kulutus import lue_kulutus_teksti
from sahko.hinnat import lue_hinnat, hae_entsoe, lue_avain, HintahakuVirhe
from sahko.laskenta import laske_kustannukset, vertaile_sopimukset


st.set_page_config(page_title="Sähkönkulutus", layout="wide")
st.title("Sähkönkulutuksen seuranta")


@st.cache_data(ttl=3600, show_spinner=False)
def hae_oikeat_hinnat(alku_utc, loppu_utc, api_avain):
    """Hakee ENTSO-E-hinnat ja välimuistittaa tuloksen tunniksi."""
    tulos = hae_entsoe(alku_utc, loppu_utc, api_avain)
    return tulos.hinnat, len(tulos.ristiriidat)


hintalahde = st.radio(
    "Hintadatan lähde",
    ["Synteettinen esimerkkidata", "Oikea ENTSO-E-data"],
    horizontal=True,
    help="Valitse käytetäänkö projektin mukana tulevaa esimerkkihintadataa vai haetaanko hinnat ENTSO-E:stä.",
)

if hintalahde == "Synteettinen esimerkkidata":
    st.info(
        "Käytössä on projektin mukana tuleva synteettinen esimerkkihintadata. "
        "API-avainta ei tarvita."
    )
else:
    st.warning(
        "**Oikean ENTSO-E-datan käyttö vaatii API-avaimen sovelluksen backendissä.** "
        "Aseta avain backendin ympäristömuuttujaan `ENTSOE_API_KEY` tai projektin "
        "juuren `.env`-tiedostoon. Avainta ei pidä syöttää tähän käyttöliittymään "
        "eikä tallentaa GitHub-repositorioon."
    )

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

    if hintalahde == "Synteettinen esimerkkidata":
        hintapolku = Path("data/esimerkki/hinnat_FI_2026-10.csv")

        if not hintapolku.exists():
            st.error("Esimerkkihintatiedostoa ei löytynyt.")
            st.stop()

        hinnat = lue_hinnat(hintapolku, alku_utc, loppu_utc)

    else:
        try:
            api_avain = lue_avain()
            with st.spinner("Haetaan pörssihintoja ENTSO-E:stä..."):
                hinnat, ristiriitoja = hae_oikeat_hinnat(
                    alku_utc,
                    loppu_utc,
                    api_avain,
                )

            if not hinnat:
                st.error(
                    "ENTSO-E ei palauttanut hintatietoja valitulle aikavälille. "
                    "Tarkista aikaväli ja API-avaimen toimivuus."
                )
                st.stop()

            if ristiriitoja:
                st.warning(
                    f"ENTSO-E palautti {ristiriitoja} ristiriitaista hintahavaintoa. "
                    "Ensimmäinen havainto säilytettiin."
                )

            st.success(
                f"Haettiin {len(hinnat)} varttihintaa suoraan ENTSO-E:stä."
            )

        except HintahakuVirhe as virhe:
            st.error(f"ENTSO-E-hintahaku epäonnistui: {virhe}")
            st.info(
                "Varmista, että ENTSOE_API_KEY on asetettu sovelluksen backendissä "
                "tai että projektin juuressa on .env-tiedosto, jossa avain on."
            )
            st.stop()

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
        "Spot-kustannus",
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
    st.caption(
        "Yllä näkyvä spot-kustannus ja kuvaajien kustannukset perustuvat pelkkään "
        "pörssihintaan. Marginaali, perusmaksut ja ALV huomioidaan erikseen "
        "sopimusvertailussa."
    )


    # --- Kulutusnäkymä ---

    st.divider()
    st.header("Kulutuksen analyysi")

    nakyma = st.segmented_control(
        "Kulutusnäkymä",
        options=["Kuukausi", "Viikko"],
        default="Kuukausi",
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
            format_func=viikon_nimi,
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

    st.subheader("Päivittäinen kulutus")
    st.caption("Valitse pylväs nähdäksesi kyseisen päivän tarkemman kulutuksen.")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=paivittainen["paivamaara"],
        y=paivittainen["kulutus"],
        customdata=paivittainen["paiva"].astype(str),
        hovertemplate="%{x}<br>Kulutus: %{y:.2f} kWh<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title="Päivä",
        yaxis_title="Kulutus (kWh)",
        clickmode="event+select",
        margin=dict(l=10, r=10, t=20, b=10),
        height=320,
    )

    tapahtuma = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
    )

    pisteet = tapahtuma.selection.points
    if pisteet:
        indeksi = pisteet[-1].get("point_index")
        if indeksi is not None and 0 <= indeksi < len(paivat):
            st.session_state.valittu_paiva = paivat[indeksi]

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

    st.subheader(f"Päivän tarkastelu: {valittu.strftime('%d.%m.%Y')}")

    mittari1, mittari2, mittari3 = st.columns(3)
    mittari1.metric("Päivän kulutus", f"{paivan_kulutus:.2f} kWh")
    mittari2.metric("Päivän kustannus", f"{paivan_kustannus:.2f} €")
    mittari3.metric(
        "Päivän keskihinta",
        f"{paivan_keskihinta:.2f} snt/kWh"
        if paivan_keskihinta is not None
        else "Ei saatavilla",
    )

    paivan_data["kellonaika"] = paivan_data["aika"].dt.strftime("%H:%M")

    # --- Tuntikohtaiset kuvaajat ---

    st.divider()
    st.header("Päivän ja tuntien tarkempi tarkastelu")

    paivan_tunnit = paivan_data.copy()
    paivan_tunnit["tunti_utc"] = paivan_tunnit["aika_utc"].dt.floor("h")

    tuntidata = (
        paivan_tunnit.groupby("tunti_utc")
        .agg(
            kulutus_kwh=("kulutus", "sum"),
            kustannus_eur=(
                "kustannus_eur",
                lambda x: x.sum(min_count=1),
            ),
        )
        .reset_index()
    )

    tuntidata["tunti"] = (
        tuntidata["tunti_utc"]
        .dt.tz_convert("Europe/Helsinki")
        .dt.strftime("%H:%M %z")
    )

    vasen, oikea = st.columns(2)

    with vasen:
        st.subheader("Kulutus 15 minuutin tarkkuudella")

        paiva_fig = go.Figure()
        paiva_fig.add_trace(go.Bar(
            x=paivan_data["kellonaika"],
            y=paivan_data["kulutus"],
            hovertemplate="%{x}<br>Kulutus: %{y:.3f} kWh<extra></extra>",
        ))

        paiva_fig.update_layout(
            xaxis_title="Kellonaika",
            yaxis_title="Kulutus (kWh)",
            margin=dict(l=10, r=10, t=20, b=10),
            height=320,
        )

        st.plotly_chart(paiva_fig, use_container_width=True)

    with oikea:
        st.subheader("Kulutuksen kustannus 15 minuutin jaksoissa")

        kustannus_vartti_fig = go.Figure()
        kustannus_vartti_fig.add_trace(go.Bar(
            x=paivan_data["kellonaika"],
            y=paivan_data["kustannus_eur"],
            hovertemplate=(
                "%{x}<br>"
                "Kulutus × spot-hinta: %{y:.4f} €"
                "<extra></extra>"
            ),
        ))

        kustannus_vartti_fig.update_layout(
            xaxis_title="Kellonaika",
            yaxis_title="Kustannus (€ / 15 min)",
            margin=dict(l=10, r=10, t=20, b=10),
            height=320,
        )

        st.plotly_chart(
            kustannus_vartti_fig,
            use_container_width=True,
        )

    vasen, oikea = st.columns(2)

    with vasen:
        st.subheader("Pörssisähkön hinta päivän aikana")

        hinta_data = paivan_data.sort_values("aika_utc").copy()

        hinta_fig = go.Figure()
        hinta_fig.add_trace(go.Scatter(
            x=hinta_data["kellonaika"],
            y=hinta_data["hinta_snt_kwh"],
            mode="lines+markers",
            connectgaps=False,
            hovertemplate=(
                "%{x}<br>Hinta: %{y:.3f} snt/kWh<extra></extra>"
            ),
        ))

        hinta_fig.update_layout(
            xaxis_title="Kellonaika",
            yaxis_title="Hinta (snt/kWh)",
            margin=dict(l=10, r=10, t=20, b=10),
            height=320,
        )

        st.plotly_chart(hinta_fig, use_container_width=True)

    with oikea:
        st.subheader("Kalleimmat kulutustunnit")

        jakson_data = nakyman_data.copy()
        jakson_data["tunti_utc"] = jakson_data["aika_utc"].dt.floor("h")

        kustannus_tunnit = (
            jakson_data.groupby("tunti_utc")
            .agg(
                kustannus_eur=(
                    "kustannus_eur",
                    lambda x: x.sum(min_count=1),
                ),
                kulutus_kwh=("kulutus", "sum"),
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
            ),
        ))

        kustannus_fig.update_layout(
            xaxis_title="Kustannus (€)",
            yaxis_title="Tunti",
            margin=dict(l=10, r=10, t=20, b=10),
            height=320,
        )

        st.plotly_chart(kustannus_fig, use_container_width=True)

    # --- Sopimusvertailu ---
    st.divider()
    st.header("Kiinteän sähkösopimuksen vertailu")

    # Sopimusvertailu käyttää samaa koko ladattua kulutusjaksoa kuin ennen.

    st.caption(
        "Vertailu tehdään koko ladatulle kulutusjaksolle. Syötä molempien "
        "energiahinnat ilman ALV:tä ja kuukausimaksut laskulla näkyvinä "
        "ALV:n sisältävinä summina. Projektin laskentakaavan mukaan ALV "
        "lisätään energiaosuuteen ja perusmaksu sen jälkeen. Kuukausimaksut "
        "jaksotetaan kulutusjakson pituuden mukaan Suomen kalenterikuukausissa."
    )

    if laskenta["puuttuvat_vartit"]:
        st.warning(
            f"Sopimusvertailua ei voida tehdä, koska "
            f"{len(laskenta['puuttuvat_vartit'])} kulutusvartilta puuttuu spot-hinta. "
            "Puuttuvia hintoja ei arvioida nollaksi."
        )
    else:
        with st.form("v4_sopimusvertailu"):
            spot_sarake, kiintea_sarake, alv_sarake = st.columns(3)

            with spot_sarake:
                st.markdown("**Pörssisähkösopimus**")
                spot_marginaali = st.number_input(
                    "Myyjän marginaali (snt/kWh)",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.3f",
                    key="v4_spot_marginaali",
                )
                spot_perusmaksu = st.number_input(
                    "Perusmaksu (€/kk, ALV mukana)",
                    min_value=0.0,
                    value=0.0,
                    step=0.50,
                    format="%.2f",
                    key="v4_spot_perusmaksu",
                )

            with kiintea_sarake:
                st.markdown("**Kiinteähintainen sopimus**")
                kiintea_hinta = st.number_input(
                    "Energiahinta (snt/kWh)",
                    min_value=0.0,
                    value=0.0,
                    step=0.10,
                    format="%.4f",
                    help="Anna sopimustarjouksen energiahinta ilman ALV:tä.",
                    key="v4_kiintea_hinta",
                )
                kiintea_perusmaksu = st.number_input(
                    "Perusmaksu (€/kk, ALV mukana)",
                    min_value=0.0,
                    value=0.0,
                    step=0.50,
                    format="%.2f",
                    key="v4_kiintea_perusmaksu",
                )

            with alv_sarake:
                st.markdown("**Verotus**")
                alv_prosentti = st.number_input(
                    "ALV (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=25.5,
                    step=0.1,
                    format="%.1f",
                    key="v4_alv_prosentti",
                )
                st.caption("Sama ALV-kanta molemmille sopimuksille.")

            laske_vertailu = st.form_submit_button("Laske sopimusvertailu")
    
        if laske_vertailu:
            try:
                vertailu = vertaile_sopimukset(
                    vartit=tulos.vartit,
                    hinnat=hinnat,
                    spot_marginaali_snt=spot_marginaali,
                    spot_perusmaksu_eur=spot_perusmaksu,
                    kiintea_hinta_snt=kiintea_hinta,
                    kiintea_perusmaksu_eur=kiintea_perusmaksu,
                    alv_prosentti=alv_prosentti,
                )
            except ValueError as e:
                st.error(str(e))
            else:
                spot_kortti, kiintea_kortti, erotus_kortti = st.columns(3)
                spot_kortti.metric(
                    "Pörssisähkön kokonaiskustannus",
                    f"{vertailu['spot_yhteensa_eur']:.2f} €",
                )
                kiintea_kortti.metric(
                    "Kiinteän sopimuksen kokonaiskustannus",
                    f"{vertailu['kiintea_yhteensa_eur']:.2f} €",
                )
                erotus_kortti.metric(
                    "Erotus (kiinteä − pörssi)",
                    f"{vertailu['erotus_eur']:+.2f} €",
                )

                if vertailu["erotus_eur"] > 0.005:
                    st.info(
                        f"Pörssisähkö olisi ollut {vertailu['erotus_eur']:.2f} € edullisempi "
                        "tällä kulutusjaksolla."
                    )
                elif vertailu["erotus_eur"] < -0.005:
                    st.info(
                        f"Kiinteä sopimus olisi ollut {-vertailu['erotus_eur']:.2f} € edullisempi "
                        "tällä kulutusjaksolla."
                    )
                else:
                    st.info("Sopimusten kustannukset olivat käytännössä yhtä suuret.")

                st.metric(
                    "Tasapainohinta",
                    f"{vertailu['tasapainohinta_snt_kwh']:.6f} snt/kWh",
                    help=(
                        "Kiinteä energiahinta ilman ALV:tä, jolla sopimusten "
                        "kokonaiskustannukset ovat samat. Molempien sopimusten "
                        "perusmaksut ja pörssisähkön marginaali on huomioitu."
                    ),
                )

                erittely = pd.DataFrame({
                    "Kustannuserä": [
                        "Spot-energia",
                        "Myyjän marginaali",
                        "Perusmaksu",
                        "ALV energiaosuudesta",
                        "Yhteensä",
                    ],
                    "Pörssisähkö (€)": [
                        vertailu["spot_energia_ilman_alv_eur"],
                        vertailu["spot_marginaali_ilman_alv_eur"],
                        vertailu["spot_perusmaksu_eur"],
                        vertailu["spot_alv_eur"],
                        vertailu["spot_yhteensa_eur"],
                    ],
                    "Kiinteä sopimus (€)": [
                        vertailu["kiintea_energia_ilman_alv_eur"],
                        None,
                        vertailu["kiintea_perusmaksu_eur"],
                        vertailu["kiintea_alv_eur"],
                        vertailu["kiintea_yhteensa_eur"],
                    ],
                })
                st.dataframe(
                    erittely,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Pörssisähkö (€)": st.column_config.NumberColumn(format="%.2f €"),
                        "Kiinteä sopimus (€)": st.column_config.NumberColumn(format="%.2f €"),
                    },
                )

                jakson_alku = pd.Timestamp(vertailu["jakson_alku_utc"]).tz_convert("Europe/Helsinki")
                jakson_loppu = pd.Timestamp(vertailu["jakson_loppu_utc"]).tz_convert("Europe/Helsinki")
                st.caption(
                    f"Vertailujakso: {jakson_alku:%d.%m.%Y %H:%M}–"
                    f"{jakson_loppu:%d.%m.%Y %H:%M} Suomen aikaa. "
                    f"Kulutus yhteensä: {vertailu['kokonaiskulutus_kwh']:.2f} kWh. "
                    "Kuukausimaksut on suhteutettu valittuun aikaväliin. "
                    "Siirtomaksut ja sähkövero eivät sisälly vertailuun."
                )

else:
    st.info("Lataa CSV-tiedosto nähdäksesi sähkönkulutuksen.")
