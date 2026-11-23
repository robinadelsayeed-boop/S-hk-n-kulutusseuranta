"""Hakee Suomen day-ahead-hinnat ENTSO-E:stä ja tallentaa ne CSV-tiedostoon (V2).

Vaatii ENTSO-E-avaimen ympäristömuuttujassa ENTSOE_API_KEY tai repon juuren .env-tiedostossa.

Esimerkki (päivät Suomen aikaa, loppupäivä ei kuulu jaksoon):
    python scripts/hae_hinnat.py --alku 2026-10-01 --loppu 2026-11-01 \
        --ulos data/esimerkki/hinnat_FI_2026-10.csv
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sahko.hinnat import HintahakuVirhe, hae_entsoe, tallenna_hinnat, varttien_maara  # noqa: E402

SUOMI = ZoneInfo("Europe/Helsinki")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--alku", required=True, help="Ensimmäinen päivä Suomen aikaa, VVVV-KK-PP")
    p.add_argument("--loppu", required=True, help="Päivä jakson jälkeen Suomen aikaa, VVVV-KK-PP")
    p.add_argument("--ulos", required=True, help="Tallennettavan CSV:n polku")
    a = p.parse_args()

    alku = datetime.fromisoformat(a.alku).replace(tzinfo=SUOMI)
    loppu = datetime.fromisoformat(a.loppu).replace(tzinfo=SUOMI)
    try:
        tulos = hae_entsoe(alku, loppu)
    except HintahakuVirhe as e:
        print(f"Virhe: {e}", file=sys.stderr)
        return 1

    odotettu = varttien_maara(alku, loppu)
    tallenna_hinnat(tulos.hinnat, a.ulos)
    print(f"Tallennettu {len(tulos.hinnat)} varttihintaa tiedostoon {a.ulos} (jaksossa {odotettu} varttia)")
    if len(tulos.hinnat) < odotettu:
        print(f"HUOM: {odotettu - len(tulos.hinnat)} vartilta puuttuu hinta.")
    if tulos.ristiriidat:
        print(f"HUOM: {len(tulos.ristiriidat)} vartille tuli kaksi eri hintaa; ensimmäinen pidettiin.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
