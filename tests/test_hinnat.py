"""V2: hintojen jäsennyksen, tallennuksen ja puuttuvien hintojen testit (docs/01-projektikuvaus.md, V2).

Testit eivät ota yhteyttä ENTSO-E:hen. XML-esimerkit on kirjoitettu käsin ENTSO-E:n
A44-vastauksen rakenteen mukaan, ja odotetut arvot on laskettu käsin (€/MWh / 10 = snt/kWh).
"""

from datetime import datetime, timedelta, timezone

import pytest

from sahko import hinnat as h

NS = "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"


def xml(jaksot: str, juuri: str = "Publication_MarketDocument") -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><{juuri} xmlns="{NS}">{jaksot}</{juuri}>'


def sarja(alku: str, loppu: str, res: str, pisteet: list[tuple[int, float]]) -> str:
    p = "".join(f"<Point><position>{pos}</position><price.amount>{hinta}</price.amount></Point>" for pos, hinta in pisteet)
    return (
        "<TimeSeries><curveType>A03</curveType><Period>"
        f"<timeInterval><start>{alku}</start><end>{loppu}</end></timeInterval>"
        f"<resolution>{res}</resolution>{p}</Period></TimeSeries>"
    )


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def test_varttihinnat_muunnetaan_snt_kwh():
    # 4 varttia: 45,67 / 12,30 / -1,50 / 100,00 €/MWh
    teksti = xml(sarja("2026-10-01T21:00Z", "2026-10-01T22:00Z", "PT15M",
                       [(1, 45.67), (2, 12.30), (3, -1.50), (4, 100.00)]))
    t = h.parsi_entsoe_xml(teksti)
    assert t.hinnat == {
        utc(2026, 10, 1, 21, 0): pytest.approx(4.567),
        utc(2026, 10, 1, 21, 15): pytest.approx(1.23),
        utc(2026, 10, 1, 21, 30): pytest.approx(-0.15),   # negatiivinen hinta säilyy
        utc(2026, 10, 1, 21, 45): pytest.approx(10.0),
    }


def test_a03_puuttuva_positio_saa_edellisen_hinnan():
    # Positio 3 puuttuu: ENTSO-E jättää pois pisteen, jonka hinta on sama kuin edellisen.
    teksti = xml(sarja("2026-10-01T21:00Z", "2026-10-01T22:00Z", "PT15M",
                       [(1, 50.0), (2, 30.0), (4, 70.0)]))
    t = h.parsi_entsoe_xml(teksti)
    assert t.hinnat[utc(2026, 10, 1, 21, 30)] == pytest.approx(3.0)
    assert len(t.hinnat) == 4


def test_tuntihinta_ennen_lokakuuta_2025_kaytetaan_neljalle_vartille():
    teksti = xml(sarja("2025-09-29T21:00Z", "2025-09-29T23:00Z", "PT60M", [(1, 80.0), (2, 20.0)]))
    t = h.parsi_entsoe_xml(teksti)
    assert len(t.hinnat) == 8
    assert [t.hinnat[utc(2025, 9, 29, 21, m)] for m in (0, 15, 30, 45)] == [pytest.approx(8.0)] * 4
    assert [t.hinnat[utc(2025, 9, 29, 22, m)] for m in (0, 15, 30, 45)] == [pytest.approx(2.0)] * 4


def test_samat_vartit_kahdessa_sarjassa_raportoidaan_ristiriitana():
    a = sarja("2026-10-01T21:00Z", "2026-10-01T21:30Z", "PT15M", [(1, 10.0), (2, 20.0)])
    b = sarja("2026-10-01T21:00Z", "2026-10-01T21:30Z", "PT15M", [(1, 10.0), (2, 99.0)])
    t = h.parsi_entsoe_xml(xml(a + b))
    assert t.hinnat[utc(2026, 10, 1, 21, 15)] == pytest.approx(2.0)
    assert t.ristiriidat == [utc(2026, 10, 1, 21, 15)]


def test_acknowledgement_vastaus_on_virhe_eika_tyhja_hintalista():
    teksti = xml("<Reason><code>999</code><text>No matching data found</text></Reason>",
                 juuri="Acknowledgement_MarketDocument")
    with pytest.raises(h.HintahakuVirhe, match="No matching data found"):
        h.parsi_entsoe_xml(teksti)


def test_tallennus_ja_luku_sailyttavat_hinnat(tmp_path):
    alkuperaiset = {utc(2026, 10, 1, 21, 0): 4.567, utc(2026, 10, 1, 21, 15): -0.15}
    polku = tmp_path / "hinnat.csv"
    h.tallenna_hinnat(alkuperaiset, polku)
    assert polku.read_text(encoding="utf-8").splitlines() == [
        "aika_utc;hinta_snt_kwh",
        "2026-10-01T21:00Z;4.56700",
        "2026-10-01T21:15Z;-0.15000",
    ]
    assert h.lue_hinnat(polku) == alkuperaiset


def test_lue_hinnat_rajaa_jakson(tmp_path):
    polku = tmp_path / "hinnat.csv"
    h.tallenna_hinnat({utc(2026, 10, 1, 21, 15 * k): float(k) for k in range(4)}, polku)
    valittu = h.lue_hinnat(polku, utc(2026, 10, 1, 21, 15), utc(2026, 10, 1, 21, 45))
    assert sorted(valittu) == [utc(2026, 10, 1, 21, 15), utc(2026, 10, 1, 21, 30)]


def test_puuttuva_hinta_raportoidaan_eika_nolla():
    vartit = {utc(2026, 10, 1, 21, 15 * k): 0.3 for k in range(4)}
    hinnat = {utc(2026, 10, 1, 21, 0): 5.0, utc(2026, 10, 1, 21, 30): 0.0}  # 0,0 on oikea hinta
    assert h.puuttuvat_vartit(vartit, hinnat) == [utc(2026, 10, 1, 21, 15), utc(2026, 10, 1, 21, 45)]


def test_haku_jaetaan_paloihin_ja_rajataan_jaksoon(monkeypatch):
    kutsut = []

    def vale_haku(alku, loppu, avain):
        kutsut.append((alku, loppu))
        tunteja = int((loppu - alku) / timedelta(hours=1))
        return xml(sarja(f"{alku:%Y-%m-%dT%H:%M}Z", f"{loppu:%Y-%m-%dT%H:%M}Z", "PT60M",
                         [(i + 1, 10.0) for i in range(tunteja)]))

    monkeypatch.setattr(h, "_hae_pala", vale_haku)
    alku, loppu = utc(2026, 1, 1), utc(2026, 7, 1)  # 181 vrk -> 3 palaa (90 + 90 + 1)
    t = h.hae_entsoe(alku, loppu, avain="testi")
    assert len(kutsut) == 3
    assert kutsut[0][0] == alku and kutsut[-1][1] == loppu
    assert len(t.hinnat) == 181 * 24 * 4
    assert min(t.hinnat) == alku and max(t.hinnat) == loppu - timedelta(minutes=15)


def test_avain_luetaan_ymparistomuuttujasta(monkeypatch):
    monkeypatch.setenv("ENTSOE_API_KEY", "abc123")
    assert h.lue_avain() == "abc123"


def test_varttien_maara_huomioi_kellonsiirrot():
    # Löytyi Oskarin ajossa 23.11.2026: skripti ilmoitti lokakuulle 2976 varttia, vaikka niitä on 2980.
    from zoneinfo import ZoneInfo
    fi = ZoneInfo("Europe/Helsinki")
    assert h.varttien_maara(datetime(2026, 10, 1, tzinfo=fi), datetime(2026, 11, 1, tzinfo=fi)) == 31 * 96 + 4
    assert h.varttien_maara(datetime(2026, 3, 29, tzinfo=fi), datetime(2026, 3, 30, tzinfo=fi)) == 23 * 4
    assert h.varttien_maara(datetime(2026, 10, 25, tzinfo=fi), datetime(2026, 10, 26, tzinfo=fi)) == 25 * 4
