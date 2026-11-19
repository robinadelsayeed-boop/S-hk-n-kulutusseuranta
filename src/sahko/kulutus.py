"""V1: Datahubin kulutus-CSV:n tuonti yhtenäiseksi 15 minuutin aikasarjaksi UTC-ajassa.

Tuonti
- tunnistaa erottimen (; , tai tabulaattori) ja desimaalierottimen (pilkku tai piste)
- etsii aikaleima- ja kulutussarakkeen otsikon perusteella (SARAKEALIAKSET)
- muuntaa aikaleiman UTC-aikaan: aikavyöhykkeellinen leima (Z tai +02:00) muunnetaan
  suoraan, aikavyöhyketön tulkitaan Suomen ajaksi (Europe/Helsinki)
- jakaa tuntiarvon tasan neljälle vartille
- raportoi virheelliset rivit rivinumerolla ja tuo muut rivit

Datahubin muoto tarkistettu oikeasta tiedostosta 19.11.2026:
MeteringPointGSRN;Product Type;Resolution;Unit Type;Reading Type;Start Time;Quantity;Quality
aikaleima UTC-muodossa 2025-08-31T21:00:00Z, desimaalipilkku, resoluutio PT1H.
Jos otsikot poikkeavat, lisää ne SARAKEALIAKSET-listoihin.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SUOMI = ZoneInfo("Europe/Helsinki")
VARTTI = timedelta(minutes=15)
TUNTI = timedelta(hours=1)

# Otsikot pienillä kirjaimilla. Ensimmäinen osuma voittaa.
SARAKEALIAKSET = {
    "aika": ["start time", "alkuaika", "aikaleima", "timestamp", "start", "aika", "time"],
    "kulutus": ["quantity", "määrä", "maara", "kulutus", "consumption", "kwh", "value", "arvo"],
    "resoluutio": ["resolution", "resoluutio", "aikatarkkuus"],
}


@dataclass
class Rivivirhe:
    rivi: int  # tiedoston rivinumero (otsikko on rivi 1)
    syy: str


@dataclass
class Tuontitulos:
    # UTC-aikaleima (vartin alku) -> kWh
    vartit: dict[datetime, float] = field(default_factory=dict)
    virheet: list[Rivivirhe] = field(default_factory=list)
    alkuperainen_summa_kwh: float = 0.0
    resoluutio: timedelta | None = None

    @property
    def summa_kwh(self) -> float:
        return sum(self.vartit.values())


def _etsi_sarake(otsikot: list[str], avain: str) -> int | None:
    pienet = [o.strip().lower() for o in otsikot]
    for alias in SARAKEALIAKSET[avain]:
        for i, o in enumerate(pienet):
            if o == alias:
                return i
    for alias in SARAKEALIAKSET[avain]:
        for i, o in enumerate(pienet):
            if alias in o:
                return i
    return None


def _parsi_luku(teksti: str) -> float:
    t = teksti.strip().replace(" ", "").replace(" ", "")
    if not t:
        raise ValueError("tyhjä kulutusarvo")
    if "," in t and "." in t:  # esim. 1.234,56
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    arvo = float(t)
    if arvo != arvo or arvo in (float("inf"), float("-inf")):
        raise ValueError("kulutusarvo ei ole luku")
    if arvo < 0:
        raise ValueError(f"negatiivinen kulutus {arvo}")
    return arvo


def _parsi_aika(teksti: str, edellinen_utc: datetime | None) -> datetime:
    """Palauttaa aikaleiman UTC-aikana."""
    t = teksti.strip()
    if not t:
        raise ValueError("tyhjä aikaleima")
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    aika = None
    try:
        aika = datetime.fromisoformat(t)
    except ValueError:
        for muoto in ("%d.%m.%Y %H:%M", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y klo %H.%M"):
            try:
                aika = datetime.strptime(t, muoto)
                break
            except ValueError:
                pass
    if aika is None:
        raise ValueError(f"tuntematon aikaleiman muoto '{teksti.strip()}'")

    if aika.tzinfo is not None:
        return aika.astimezone(timezone.utc)

    # Aikavyöhyketön = Suomen aika. Syksyn kaksinkertainen tunti (fold) ratkaistaan
    # järjestyksen perusteella: jos fold=0 olisi ajassa taaksepäin, käytetään fold=1.
    utc0 = aika.replace(tzinfo=SUOMI, fold=0).astimezone(timezone.utc)
    utc1 = aika.replace(tzinfo=SUOMI, fold=1).astimezone(timezone.utc)
    if utc0 != utc1 and edellinen_utc is not None and utc0 <= edellinen_utc:
        return utc1
    return utc0


def _parsi_resoluutio(teksti: str) -> timedelta | None:
    t = teksti.strip().upper()
    if t in ("PT15M", "15MIN", "15 MIN", "15"):
        return VARTTI
    if t in ("PT1H", "PT60M", "60MIN", "60 MIN", "1H", "60"):
        return TUNTI
    return None


def lue_kulutus_csv(polku: str | Path) -> Tuontitulos:
    teksti = Path(polku).read_text(encoding="utf-8-sig")
    return lue_kulutus_teksti(teksti)


def lue_kulutus_teksti(teksti: str) -> Tuontitulos:
    rivit = teksti.splitlines()
    if not rivit:
        raise ValueError("Tiedosto on tyhjä")
    # Datahubin tiedostossa erotin on puolipiste; Excelistä tallennettu tai kopioitu voi olla tabulaattori.
    erotin = max(";\t,", key=rivit[0].count)
    lukija = csv.reader(io.StringIO(teksti), delimiter=erotin)
    otsikot = next(lukija)

    i_aika = _etsi_sarake(otsikot, "aika")
    i_kulutus = _etsi_sarake(otsikot, "kulutus")
    i_res = _etsi_sarake(otsikot, "resoluutio")
    if i_aika is None or i_kulutus is None:
        raise ValueError(
            f"Aikaleima- tai kulutussaraketta ei löytynyt otsikoista {otsikot}. "
            "Lisää otsikot SARAKEALIAKSET-listaan."
        )

    tulos = Tuontitulos()
    luetut: list[tuple[int, datetime, float, timedelta | None]] = []
    edellinen: datetime | None = None
    for rivinro, rivi in enumerate(lukija, start=2):
        if not rivi or all(not s.strip() for s in rivi):
            continue
        try:
            if len(rivi) <= max(i_aika, i_kulutus):
                raise ValueError("rivillä on liian vähän sarakkeita")
            aika = _parsi_aika(rivi[i_aika], edellinen)
            kwh = _parsi_luku(rivi[i_kulutus])
            res = _parsi_resoluutio(rivi[i_res]) if i_res is not None and i_res < len(rivi) else None
        except ValueError as e:
            tulos.virheet.append(Rivivirhe(rivinro, str(e)))
            continue
        luetut.append((rivinro, aika, kwh, res))
        edellinen = aika

    if not luetut:
        return tulos

    # Resoluutio: sarakkeesta, tai muuten yleisin aikaväli peräkkäisten rivien välillä.
    oletus = next((r for *_, r in luetut if r is not None), None)
    if oletus is None:
        valit = [b[1] - a[1] for a, b in zip(luetut, luetut[1:]) if b[1] > a[1]]
        oletus = max(set(valit), key=valit.count) if valit else TUNTI
        if oletus not in (VARTTI, TUNTI):
            raise ValueError(f"Tuntematon mittausväli {oletus}; odotettiin 15 min tai 60 min")
    tulos.resoluutio = oletus

    for rivinro, aika, kwh, res in luetut:
        res = res or oletus
        if aika.minute % 15 or aika.second or (res == TUNTI and aika.minute):
            tulos.virheet.append(Rivivirhe(rivinro, f"aikaleima {aika:%Y-%m-%d %H:%M} UTC ei osu jakson alkuun"))
            continue
        osat = 4 if res == TUNTI else 1
        jaksot = [aika + k * VARTTI for k in range(osat)]
        if any(j in tulos.vartit for j in jaksot):
            tulos.virheet.append(Rivivirhe(rivinro, f"päällekkäinen aikaleima {aika:%Y-%m-%d %H:%M} UTC"))
            continue
        for j in jaksot:
            tulos.vartit[j] = kwh / osat
        tulos.alkuperainen_summa_kwh += kwh

    tulos.vartit = dict(sorted(tulos.vartit.items()))
    return tulos


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Käyttö: python -m sahko.kulutus <kulutus.csv>")
        sys.exit(1)
    t = lue_kulutus_csv(sys.argv[1])
    print(f"Varttijaksoja: {len(t.vartit)}")
    if t.vartit:
        eka, vika = min(t.vartit), max(t.vartit)
        print(f"Jakso (Suomen aika): {eka.astimezone(SUOMI):%d.%m.%Y %H:%M} – {(vika + VARTTI).astimezone(SUOMI):%d.%m.%Y %H:%M}")
    print(f"Kokonaiskulutus: {t.summa_kwh:.3f} kWh (tiedostossa {t.alkuperainen_summa_kwh:.3f} kWh)")
    for v in t.virheet:
        print(f"VIRHE rivi {v.rivi}: {v.syy}")
