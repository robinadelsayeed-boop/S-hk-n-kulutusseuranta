from datetime import datetime, timezone

import pandas as pd

from sahko.hinnat import puuttuvat_vartit


def laske_kustannukset(vartit: dict, hinnat: dict) -> dict:
    """Yhdistää kulutuksen ja hinnat sekä laskee kustannukset."""

    puuttuvat = puuttuvat_vartit(vartit, hinnat)

    rivit = []

    for aika, kulutus_kwh in vartit.items():
        if aika not in hinnat:
            continue

        hinta_snt = hinnat[aika]
        kustannus_eur = kulutus_kwh * hinta_snt / 100

        rivit.append({
            "aika_utc": aika,
            "kulutus_kwh": kulutus_kwh,
            "hinta_snt_kwh": hinta_snt,
            "kustannus_eur": kustannus_eur,
        })

    df = pd.DataFrame(rivit)

    if df.empty:
        return {
            "data": df,
            "puuttuvat_vartit": puuttuvat,
            "kokonaiskulutus_kwh": 0.0,
            "kokonaiskustannus_eur": 0.0,
            "painotettu_keskihinta_snt_kwh": None,
        }

    kokonaiskulutus = df["kulutus_kwh"].sum()
    kokonaiskustannus = df["kustannus_eur"].sum()

    keskihinta = (
        kokonaiskustannus * 100 / kokonaiskulutus
        if kokonaiskulutus > 0 else None
    )

    return {
        "data": df,
        "puuttuvat_vartit": puuttuvat,
        "kokonaiskulutus_kwh": kokonaiskulutus,
        "kokonaiskustannus_eur": kokonaiskustannus,
        "painotettu_keskihinta_snt_kwh": keskihinta,
    }