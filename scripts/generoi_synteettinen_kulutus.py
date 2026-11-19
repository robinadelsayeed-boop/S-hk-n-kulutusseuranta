"""Tuottaa synteettisen kulutus-CSV:n, jonka muoto jäljittelee Datahubin tiedostoa.

Data on keksittyä: sähkölämmitteisen omakotitalon karkea profiili (peruskulutus,
lämmitys, aamu- ja iltahuippu ja satunnaisvaihtelu). Siemenluku tekee tuloksesta
toistettavan. Kenenkään todellista kulutusta ei käytetä.

Esimerkki:
    python scripts/generoi_synteettinen_kulutus.py --alku 2026-10-01 --loppu 2026-11-01 \
        --resoluutio 15 --ulos data/esimerkki/kulutus_synteettinen_15min.csv
"""

from __future__ import annotations

import argparse
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SUOMI = ZoneInfo("Europe/Helsinki")
OTSIKKO = "MeteringPointGSRN;Product Type;Resolution;Unit Type;Reading Type;Start Time;Quantity;Quality"
KAYTTOPAIKKA = "643000000000000000"  # keksitty tunnus


def tuntiteho_kw(aika_suomi: datetime, rng: random.Random) -> float:
    kuukausi = aika_suomi.month
    # Lämmitystarve: suurin tammikuussa, pienin heinäkuussa.
    lammitys = 1.6 * (1 + math.cos((kuukausi - 1) / 12 * 2 * math.pi)) / 2
    tunti = aika_suomi.hour + aika_suomi.minute / 60
    aamu = 0.8 * math.exp(-((tunti - 7.5) ** 2) / 2)
    ilta = 1.2 * math.exp(-((tunti - 19) ** 2) / 4)
    yo_lammitys = 0.6 * lammitys if tunti < 6 or tunti >= 22 else 0.0
    teho = 0.35 + lammitys + aamu + ilta + yo_lammitys
    return max(0.05, teho * rng.uniform(0.8, 1.2))


def generoi(alku: datetime, loppu: datetime, resoluutio_min: int, siemen: int) -> list[str]:
    rng = random.Random(siemen)
    askel = timedelta(minutes=resoluutio_min)
    res = "PT15M" if resoluutio_min == 15 else "PT1H"
    rivit = [OTSIKKO]
    aika = alku.astimezone(timezone.utc)
    loppu_utc = loppu.astimezone(timezone.utc)
    while aika < loppu_utc:
        kwh = tuntiteho_kw(aika.astimezone(SUOMI), rng) * resoluutio_min / 60
        maara = f"{kwh:.3f}".replace(".", ",")
        rivit.append(
            f"{KAYTTOPAIKKA};8716867000030;{res};kWh;BN01;{aika:%Y-%m-%dT%H:%M:%S}Z;{maara};OK"
        )
        aika += askel
    return rivit


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--alku", required=True, help="Ensimmäinen päivä Suomen aikaa, VVVV-KK-PP")
    p.add_argument("--loppu", required=True, help="Päivä jakson jälkeen Suomen aikaa, VVVV-KK-PP")
    p.add_argument("--resoluutio", type=int, choices=[15, 60], default=15)
    p.add_argument("--siemen", type=int, default=2026)
    p.add_argument("--ulos", required=True)
    a = p.parse_args()
    alku = datetime.fromisoformat(a.alku).replace(tzinfo=SUOMI)
    loppu = datetime.fromisoformat(a.loppu).replace(tzinfo=SUOMI)
    rivit = generoi(alku, loppu, a.resoluutio, a.siemen)
    Path(a.ulos).parent.mkdir(parents=True, exist_ok=True)
    Path(a.ulos).write_text("\n".join(rivit) + "\n", encoding="utf-8")
    print(f"Kirjoitettu {len(rivit) - 1} riviä tiedostoon {a.ulos}")


if __name__ == "__main__":
    main()
