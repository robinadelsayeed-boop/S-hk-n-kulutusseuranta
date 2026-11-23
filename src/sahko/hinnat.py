"""V2: Suomen hinta-alueen day-ahead-hinnat ENTSO-E:stä ja paikallisesta hintatiedostosta.

Kulku
1. `hae_entsoe(alku_utc, loppu_utc, avain)` hakee hinnat ENTSO-E Transparency Platformin
   rajapinnasta (documentType A44, Suomi 10YFI-1--------U) ja palauttaa ne
   varttikohtaisesti yksikössä snt/kWh ilman ALV:ta.
2. `tallenna_hinnat(hinnat, polku)` tallentaa ne CSV-tiedostoon.
3. `lue_hinnat(polku, alku_utc, loppu_utc)` lukee tallennetut hinnat. Käyttöliittymä ja
   laskenta käyttävät vain tätä, joten ne toimivat ilman API-avainta (L1).
4. `puuttuvat_vartit(vartit, hinnat)` kertoo, mille kulutusvarteille ei ole hintaa.
   Puuttuvaa hintaa ei koskaan käsitellä nollana.

Yksiköt: ENTSO-E antaa hinnat €/MWh. 1 €/MWh = 0,1 snt/kWh, joten snt/kWh = €/MWh / 10.
Ennen 1.10.2025 hinnat ovat tunneittain (PT60M); tunnin hinta käytetään sen neljälle
vartille. Sen jälkeen hinnat ovat varteittain (PT15M).
"""

from __future__ import annotations

import csv
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

ENTSOE_URL = "https://web-api.tp.entsoe.eu/api"
SUOMI_EIC = "10YFI-1--------U"
VARTTI = timedelta(minutes=15)
RESOLUUTIOT = {"PT15M": timedelta(minutes=15), "PT30M": timedelta(minutes=30), "PT60M": timedelta(hours=1)}
MAKSIMIJAKSO = timedelta(days=90)  # ENTSO-E sallii enintään vuoden per pyyntö; pienemmät palat ovat varmempia
CSV_OTSIKKO = ["aika_utc", "hinta_snt_kwh"]


@dataclass
class Hintavastaus:
    # UTC-vartin alku -> snt/kWh (ilman ALV:ta)
    hinnat: dict[datetime, float] = field(default_factory=dict)
    # Samalle vartille tuli kaksi eri hintaa; ensimmäinen pidettiin
    ristiriidat: list[datetime] = field(default_factory=list)


class HintahakuVirhe(RuntimeError):
    pass


def _paikallinen_nimi(elementti: ET.Element) -> str:
    return elementti.tag.rsplit("}", 1)[-1]


def _lapset(elementti: ET.Element, nimi: str) -> list[ET.Element]:
    return [e for e in elementti if _paikallinen_nimi(e) == nimi]


def _lapsi(elementti: ET.Element, nimi: str) -> ET.Element | None:
    loydetyt = _lapset(elementti, nimi)
    return loydetyt[0] if loydetyt else None


def _teksti(elementti: ET.Element, polku: list[str]) -> str:
    e = elementti
    for nimi in polku:
        e = _lapsi(e, nimi)
        if e is None:
            raise HintahakuVirhe(f"XML:stä puuttuu {'/'.join(polku)}")
    return (e.text or "").strip()


def _parsi_utc(teksti: str) -> datetime:
    # ENTSO-E käyttää muotoa 2026-10-01T22:00Z
    return datetime.fromisoformat(teksti.replace("Z", "+00:00")).astimezone(timezone.utc)


def parsi_entsoe_xml(xml_teksti: str | bytes) -> Hintavastaus:
    """Muuntaa ENTSO-E:n A44-vastauksen varttihinnoiksi (snt/kWh)."""
    juuri = ET.fromstring(xml_teksti)
    if _paikallinen_nimi(juuri) == "Acknowledgement_MarketDocument":
        syy = " ".join(
            (e.text or "").strip() for e in juuri.iter() if _paikallinen_nimi(e) == "text"
        )
        raise HintahakuVirhe(f"ENTSO-E ei palauttanut hintoja: {syy or 'ei syytä'}")

    tulos = Hintavastaus()
    for sarja in _lapset(juuri, "TimeSeries"):
        for jakso in _lapset(sarja, "Period"):
            alku = _parsi_utc(_teksti(jakso, ["timeInterval", "start"]))
            loppu = _parsi_utc(_teksti(jakso, ["timeInterval", "end"]))
            res_teksti = _teksti(jakso, ["resolution"])
            if res_teksti not in RESOLUUTIOT:
                raise HintahakuVirhe(f"Tuntematon resoluutio {res_teksti}")
            res = RESOLUUTIOT[res_teksti]
            pisteita = int((loppu - alku) / res)

            arvot: dict[int, float] = {}
            for piste in _lapset(jakso, "Point"):
                pos = int(_teksti(piste, ["position"]))
                eur_mwh = float(_teksti(piste, ["price.amount"]))
                arvot[pos] = eur_mwh / 10

            if not arvot:
                continue
            # Käyrätyyppi A03: jos hinta pysyy samana, ENTSO-E jättää pisteen pois.
            # Puuttuva positio saa siis edellisen position hinnan saman jakson sisällä.
            edellinen = None
            for pos in range(1, pisteita + 1):
                if pos in arvot:
                    edellinen = arvot[pos]
                if edellinen is None:
                    continue  # jakson alussa ei hintaa: jätetään puuttuvaksi, ei nollaksi
                jakson_alku = alku + (pos - 1) * res
                for k in range(int(res / VARTTI)):
                    vartti = jakson_alku + k * VARTTI
                    if vartti in tulos.hinnat:
                        if abs(tulos.hinnat[vartti] - edellinen) > 1e-9:
                            tulos.ristiriidat.append(vartti)
                        continue
                    tulos.hinnat[vartti] = edellinen

    tulos.hinnat = dict(sorted(tulos.hinnat.items()))
    return tulos


def lue_avain() -> str:
    """Lukee avaimen ympäristömuuttujasta ENTSOE_API_KEY tai repon juuren .env-tiedostosta."""
    avain = os.environ.get("ENTSOE_API_KEY", "").strip()
    if not avain:
        env = Path(__file__).resolve().parents[2] / ".env"
        if env.exists():
            for rivi in env.read_text(encoding="utf-8").splitlines():
                if rivi.strip().startswith("ENTSOE_API_KEY="):
                    avain = rivi.split("=", 1)[1].strip().strip('"').strip("'")
    if not avain:
        raise HintahakuVirhe(
            "ENTSO-E-avainta ei löytynyt. Aseta ympäristömuuttuja ENTSOE_API_KEY tai lisää se .env-tiedostoon."
        )
    return avain


def _hae_pala(alku: datetime, loppu: datetime, avain: str) -> bytes:
    parametrit = {
        "securityToken": avain,
        "documentType": "A44",
        "in_Domain": SUOMI_EIC,
        "out_Domain": SUOMI_EIC,
        "periodStart": f"{alku:%Y%m%d%H%M}",
        "periodEnd": f"{loppu:%Y%m%d%H%M}",
    }
    url = f"{ENTSOE_URL}?{urllib.parse.urlencode(parametrit)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as vastaus:
            return vastaus.read()
    except urllib.error.HTTPError as e:
        sisalto = e.read()
        try:
            parsi_entsoe_xml(sisalto)  # nostaa virheen ENTSO-E:n omalla syyllä
        except HintahakuVirhe:
            raise
        except ET.ParseError:
            pass
        # Älä tulosta URL:ia, koska siinä on avain.
        raise HintahakuVirhe(f"ENTSO-E vastasi HTTP {e.code}") from None
    except urllib.error.URLError as e:
        raise HintahakuVirhe(f"Yhteys ENTSO-E:hen epäonnistui: {e.reason}") from None


def hae_entsoe(alku_utc: datetime, loppu_utc: datetime, avain: str | None = None) -> Hintavastaus:
    """Hakee hinnat väliltä [alku_utc, loppu_utc) ja palauttaa vain sille välille osuvat vartit."""
    avain = avain or lue_avain()
    alku_utc = alku_utc.astimezone(timezone.utc)
    loppu_utc = loppu_utc.astimezone(timezone.utc)
    yhteensa = Hintavastaus()
    pala_alku = alku_utc
    while pala_alku < loppu_utc:
        pala_loppu = min(pala_alku + MAKSIMIJAKSO, loppu_utc)
        osa = parsi_entsoe_xml(_hae_pala(pala_alku, pala_loppu, avain))
        for aika, hinta in osa.hinnat.items():
            if alku_utc <= aika < loppu_utc and aika not in yhteensa.hinnat:
                yhteensa.hinnat[aika] = hinta
        yhteensa.ristiriidat.extend(osa.ristiriidat)
        pala_alku = pala_loppu
    yhteensa.hinnat = dict(sorted(yhteensa.hinnat.items()))
    return yhteensa


def tallenna_hinnat(hinnat: dict[datetime, float], polku: str | Path) -> None:
    polku = Path(polku)
    polku.parent.mkdir(parents=True, exist_ok=True)
    with polku.open("w", encoding="utf-8", newline="") as f:
        kirjoittaja = csv.writer(f, delimiter=";")
        kirjoittaja.writerow(CSV_OTSIKKO)
        for aika, hinta in sorted(hinnat.items()):
            kirjoittaja.writerow([f"{aika:%Y-%m-%dT%H:%M}Z", f"{hinta:.5f}"])


def lue_hinnat(
    polku: str | Path, alku_utc: datetime | None = None, loppu_utc: datetime | None = None
) -> dict[datetime, float]:
    """Vartin alkuhetki (UTC) -> pörssihinta snt/kWh ilman ALV:ta.

    Puuttuva vartti puuttuu palautetusta dictistä (ei 0). Jos alku tai loppu annetaan,
    palautetaan vain väliin [alku, loppu) osuvat vartit.
    """
    hinnat: dict[datetime, float] = {}
    with Path(polku).open(encoding="utf-8", newline="") as f:
        lukija = csv.reader(f, delimiter=";")
        otsikko = next(lukija)
        if [o.strip() for o in otsikko] != CSV_OTSIKKO:
            raise ValueError(f"Hintatiedoston otsikko pitää olla {';'.join(CSV_OTSIKKO)}, oli {otsikko}")
        for rivinro, rivi in enumerate(lukija, start=2):
            if not rivi:
                continue
            try:
                aika = _parsi_utc(rivi[0])
                hinta = float(rivi[1])
            except (ValueError, IndexError) as e:
                raise ValueError(f"Hintatiedoston rivi {rivinro} on virheellinen: {e}") from None
            if alku_utc and aika < alku_utc.astimezone(timezone.utc):
                continue
            if loppu_utc and aika >= loppu_utc.astimezone(timezone.utc):
                continue
            hinnat[aika] = hinta
    return hinnat


def varttien_maara(alku: datetime, loppu: datetime) -> int:
    """Varttien määrä välillä [alku, loppu). Lasketaan UTC-aikana, jotta kellonsiirrot
    (23 h ja 25 h vuorokaudet) tulevat oikein: saman aikavyöhykkeen aikaleimojen
    erotuksen Python laskee seinäkelloajassa."""
    return int((loppu.astimezone(timezone.utc) - alku.astimezone(timezone.utc)) / VARTTI)


def puuttuvat_vartit(vartit, hinnat: dict[datetime, float]) -> list[datetime]:
    """Kulutusvartit, joille ei ole hintaa. `vartit` voi olla dict tai mikä tahansa iteroitava."""
    return sorted(v for v in vartit if v not in hinnat)
