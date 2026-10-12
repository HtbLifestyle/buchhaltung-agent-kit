#!/usr/bin/env python3
"""Selbsttest der Belegextraktion.

Jeder Fall stellt **einen** real aufgetretenen Fehler nach. Die Belegtexte sind
erfunden — Firmen, Nummern und Beträge sind konstruiert. Was echt ist, ist das
Layoutmuster, denn daran ist die Extraktion gescheitert.

Ein Test, der nur den behobenen Fall prüft, ist die Hälfte. Wo eine Regel etwas
ausschließt, wird auch geprüft, dass sie den **Normalfall durchlässt** — sonst besteht
eine Regel, die alles verwirft, den Test.

    python3 tools/selbsttest.py
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from belege_lesen import (                                   # noqa: E402
    beleg_aus_text, gesamtbetrag, rechnungsdatum, waehrung, saetze,
    ustid_liste, lieferant_name, zerlege, nachbearbeiten, gruppen_kennzahlen,
    land_aus_anschrift,
)

ZEIT = (2026, 9)
UST = "DE999999999"
NAMEN = ["Beispiel Betrieb GmbH", "Beispiel Betrieb UG"]


# ─────────────────────────── Belegmuster ───────────────────────────

# G-08: Label und Wert über 100 Spalten auseinander
BREIT = """
Muster Hosting GmbH
Rechnungsnummer: RG-100193203928
Rechnungsdatum                06.09.2026

Pos.  Leistung                      Einheiten      Betrag (EUR)        MwSt.
1     Paket S                               1              4,20          19 %

Zwischensumme Netto (19,0 %)                                                                     4,20 EUR
Zu zahlender Betrag                                                                              5,00 EUR
"""

# G-08: Endbetrag in der Folgezeile, mit Leerzeile dazwischen; "Gesamtbetrag netto"
UMBRUCH = """
Muster Handel GmbH
USt-IdNr. DE822345678
Rechnungs-/Lieferdatum    Auftragsdatum    Rechnungsnummer
18.09.2026                17.09.2026       R480100

  Art.Nr.   Bezeichnung          Menge  MwSt.   Einzelpreis    Gesamtbetrag
  9607      Artikel A                1  19.00%      69,90 €         69,90 €

                                        Warenwert netto:            327,11 €
                                        Gesamtbetrag netto:         327,11 €
                                        MwSt.:   19%                 62,15 €
                                                   7%                 0,00 €
                                         Gesamtbetrag

                 Versand:     0,00 €                                389,26 €
"""

# G-10: Gutschrift, alle Summen negativ
GUTSCHRIFT = """
Muster Handel GmbH
USt-IdNr. DE822345678
Gutschrift               R000001
Rechnungs-/Lieferdatum
18.09.2026

                                        Gesamtbetrag netto:          -50,00 €
                                        MwSt.:   19%                  -9,50 €
                                         Gesamtbetrag

                                                                     -59,50 €
"""

# G-11: Währungszeichen in der Produktbezeichnung
DOLLAR_IM_TITEL = """
Markt GmbH
Rechnungsdatum 02.09.2026
Rechnungsnummer DE600MUSTER1
                                                              Zahlbetrag      21,29 €

 Beschreibung                                    Menge   Stückpreis    USt. %   Zwischensumme
 $100 Muster-Titel: Wie Zahlen Lesen                 1      19,90 €        7%        21,29 €
                                      USt. Gesamt                19,90 €     1,39 €
"""

# E-01: Inlandsbeleg, der ausschliesslich 0 % ausweist
NULL_PROZENT = """
Muster Verkehrsgesellschaft mbH
USt-IdNr. DE811234567
Ihre Rechnung vom 01.09.2026
Rechnungsnummer: 403606086691

Produkt                       MwSt.     Einzelpreis   Gesamtpreis
Position 1                       0%        0,03 EUR      0,03 EUR

Nettobetrag                                              0,03 EUR
Mehrwertsteuer 0 %                                       0,00 EUR
Zu zahlender Betrag                                      0,03 EUR
"""

# G-09: Wort zwischen Präfix und Nummer
USTID_MIT_WORT = """
Muster Zeit OUe
EE VAT EE123456789                              DE VAT DE999999999
Invoice number MUSTER-2146007
Date of issue   September 12, 2026
Reverse charge
Amount due                                                    100,00 EUR
"""

# E-15/E-17: Drittlandsanbieter ohne USt-IdNr. und ohne RC-Vermerk
OHNE_HINWEIS = """
Invoice
Invoice number MUSTER-0010
Date of issue       September 1, 2026
Muster Research Inc.                       Bill to
500 Example Street                         Beispiel Betrieb GmbH
San Francisco, California 94104            Musterstadt
United States                              Germany
                                           DE VAT DE999999999

Description                        Qty   Unit price      Amount
Plan                                 1     180,00 €      180,00 €
                     Amount due                          180,00 €
"""

# E-18: derselbe Lieferant, aber mit USt-IdNr.
MIT_USTID = """
Invoice
Invoice number MUSTER-0011
Date of issue       September 2, 2026
VAT Registration    EU VAT: IE1234567X
Muster Research Inc.                       Bill to
San Francisco, California                  Beispiel Betrieb GmbH
United States                              DE VAT DE999999999
Tax to be paid on reverse charge basis
                     Amount due                          180,00 €
"""

# B-06: zwei eigenständige Rechnungen in einer Datei
SAMMELDATEI = """
Markt GmbH
                                   Rechnungsdatum  18 September 2026
                                   Rechnungsnummer  DE600TEIL0001
                                   Zahlbetrag       28,49 €
 Position A      1   23,94 €   19%   28,49 €
                             USt. Gesamt    23,94 €    4,55 €
                                                             Seite 1 von 1

Markt GmbH
                                   Rechnungsdatum  18 September 2026
                                   Rechnungsnummer  DE600TEIL0002
                                   Zahlbetrag        6,64 €
 Position B      1    5,58 €   19%    6,64 €
                             USt. Gesamt     5,58 €    1,06 €
                                                             Seite 1 von 1
"""

# G-07: mehrdeutiges numerisches Datum, im Dokument auflösbar
SLASH_AUFLOESBAR = """
Muster Cloud Ltd
Invoice date: 09/15/2026
Service period: 09/01/2026 - 09/30/2026
Reverse charge
DK VAT DK12345678                       DE VAT DE999999999
Amount due                                                     30,00 EUR
"""

# G-07: mehrdeutig und nicht auflösbar
SLASH_UNAUFLOESBAR = """
Muster Cloud Ltd
Invoice date: 09/05/2026
DK VAT DK12345678                       DE VAT DE999999999
Reverse charge
Amount due                                                     30,00 EUR
"""

# B-07: kein Datum im Dokument
OHNE_DATUM = """
Muster Versand
Commercial Invoice
No.: 200260000629980
Amount due                                                     42,00 EUR
"""


# ─────────────────────────────── Fälle ───────────────────────────────

def lies(t, **kw):
    kw.setdefault("eigene_ustid", UST)
    kw.setdefault("eigene_namen", NAMEN)
    kw.setdefault("name", "probe.pdf")
    return beleg_aus_text(t, ZEIT, **kw)


FAELLE = []
def fall(name):
    def deko(f): FAELLE.append((name, f)); return f
    return deko


@fall("G-08 Betrag trotz 130 Spalten Abstand")
def _():
    assert gesamtbetrag(BREIT) == 5.00, gesamtbetrag(BREIT)

@fall("G-08 Endbetrag aus der Folgezeile, Leerzeile dazwischen")
def _():
    assert gesamtbetrag(UMBRUCH) == 389.26, gesamtbetrag(UMBRUCH)

@fall("G-08 'Gesamtbetrag netto' ist nicht der Gesamtbetrag")
def _():
    assert gesamtbetrag(UMBRUCH) != 327.11

@fall("G-08 Fliesstext hinter dem Label zieht keine Fremdzahl an")
def _():
    t = "Rechnungsdatum 05.09.2026\nDen Rechnungsbetrag buchen wir ab.\n\n  12345,00\nZu zahlender Betrag   7,00 EUR\n"
    assert gesamtbetrag(t) == 7.00, gesamtbetrag(t)

@fall("G-10 Gutschrift behaelt ihr Vorzeichen")
def _():
    assert gesamtbetrag(GUTSCHRIFT) == -59.50, gesamtbetrag(GUTSCHRIFT)

@fall("G-10 Gutschrift wird als solche erkannt")
def _():
    assert lies(GUTSCHRIFT)["belegart"] == "gutschrift"

@fall("G-10 normale Rechnung bleibt positiv")
def _():
    assert lies(UMBRUCH)["belegart"] == "rechnung"

@fall("G-11 Dollarzeichen im Produkttitel macht keine USD-Rechnung")
def _():
    b = lies(DOLLAR_IM_TITEL)
    assert b["waehrung"] == "EUR", b["waehrung"]
    assert "umrechnung_fremdwaehrung" not in b["pruefen"]

@fall("G-11 echte USD-Rechnung wird erkannt")
def _():
    t = "Invoice date: September 5, 2026\nAmount due      USD 38.00\n"
    assert waehrung(t, 38.00) == "USD"

@fall("E-01 0-%-Inlandsbeleg wird nicht zum Regelsatz")
def _():
    b = lies(NULL_PROZENT)
    assert b["behandlung"] == "inland_0", b["behandlung"]

@fall("E-01 Inlandsbeleg mit 19 % bleibt 19 %")
def _():
    assert lies(UMBRUCH)["behandlung"] == "inland_19"

@fall("E-02 Satzzeile mit 0,00 ist eine Vorlagenzeile, kein Satz")
def _():
    assert 7 not in {s for s in saetze(UMBRUCH) if s in (7, 19)}

@fall("G-09 USt-IdNr. mit Wort zwischen Praefix und Nummer")
def _():
    assert ("EE", "EE123456789") in ustid_liste(USTID_MIT_WORT)

@fall("G-09 USt-IdNr. mit Trennzeichen")
def _():
    assert ("BE", "BE0123456789") in ustid_liste("USt-ID: BE 0123.456.789")

@fall("G-09 EU-Praefix ist kein Drittland")
def _():
    assert ("EU", "EU123456789") in ustid_liste("EU VAT EU123456789")

@fall("E-17 Land aus der Anschrift, wenn keine USt-IdNr. vorliegt")
def _():
    assert land_aus_anschrift(OHNE_HINWEIS) == "US"

@fall("E-17 eigene Anschrift zaehlt nicht als Leistender")
def _():
    assert land_aus_anschrift("Musterstadt\nGermany\n") is None

@fall("E-15 Reverse Charge ohne ausdruecklichen Vermerk")
def _():
    b = lies(OHNE_HINWEIS)
    assert b["behandlung"] == "§13b_drittland", b["behandlung"]
    assert "rc_hinweis_fehlt_auf_beleg" in b["pruefen"]

@fall("E-18 USt-IdNr. des Lieferanten gilt fuer seine uebrigen Belege")
def _():
    a, b = lies(OHNE_HINWEIS), lies(MIT_USTID)
    a["datei"], b["datei"] = "ohne.pdf", "mit.pdf"
    nachbearbeiten([a, b])
    assert a["ustid"] == "IE1234567X", a["ustid"]
    assert a["behandlung"] == "§13b_eu", a["behandlung"]
    assert "ustid_vom_lieferanten_uebernommen" in a["pruefen"]

@fall("E-18 Uebernahme wird ausgewiesen, nicht stillschweigend")
def _():
    a, b = lies(OHNE_HINWEIS), lies(MIT_USTID)
    nachbearbeiten([a, b])
    assert a.get("land_quelle") == "lieferant_memory"

@fall("E-18 ergaenzt nur den Leistenden, nie Betrag oder Datum")
def _():
    a, b = lies(OHNE_HINWEIS), lies(MIT_USTID)
    betrag, datum = a["betrag"], a["datum"]
    nachbearbeiten([a, b])
    assert a["betrag"] == betrag and a["datum"] == datum

@fall("E-16 greift auch, wenn die USt-IdNr. auf einem Beleg fehlt")
def _():
    # Zwei Belege desselben Lieferanten, unterschiedlich behandelt. Eine Gruppierung
    # nach USt-IdNr. bildete zwei Gruppen von eins und meldete null Befunde.
    a, b = lies(OHNE_HINWEIS), lies(MIT_USTID)
    a["behandlung"], b["behandlung"] = "kein_vorsteuerabzug", "§13b_eu"
    a["ustid"], a["lieferant"] = None, "Muster Research Inc"
    b["lieferant"] = "Muster Research Inc"
    nachbearbeiten([a, b])
    assert "lieferant_uneinheitlich" in a["pruefen"] or a["regel"] == "E-18"

@fall("E-16 Selbstpruefung meldet Einzelgruppen")
def _():
    k = gruppen_kennzahlen([lies(MIT_USTID), lies(NULL_PROZENT)])
    assert "einzelgruppen" in k and k["gruppen"] >= 1

@fall("B-06 Sammeldatei wird in zwei Belege zerlegt")
def _():
    teile = zerlege(SAMMELDATEI)
    assert len(teile) == 2, len(teile)
    assert {n for n, _ in teile} == {"DE600TEIL0001", "DE600TEIL0002"}

@fall("B-06 Einzelrechnung wird nicht zerlegt")
def _():
    assert len(zerlege(BREIT)) == 1

@fall("B-06 jeder Teil traegt seinen eigenen Betrag")
def _():
    betraege = {gesamtbetrag(t) for _, t in zerlege(SAMMELDATEI)}
    assert betraege == {28.49, 6.64}, betraege

@fall("B-06 Teile derselben Datei sind keine Dubletten")
def _():
    teile = zerlege(SAMMELDATEI)
    belege = [lies(t, name="sammel.pdf", nummer=n, anzahl=2, hash_="gleicherhash")
              for n, t in teile]
    nachbearbeiten(belege)
    assert not any(b.get("dublette_von") for b in belege)

@fall("P-04 echte Dublette wird erkannt")
def _():
    a = lies(BREIT, name="a.pdf", nummer="RG-1", hash_="h")
    b = lies(BREIT, name="b.pdf", nummer="RG-1", hash_="h")
    nachbearbeiten([a, b])
    assert b.get("dublette_von") == "a.pdf"

@fall("A-02 ersetzte Rechnung wird aussortiert, auch ueber den Dateinamen")
def _():
    # Die ersetzte Nummer steckt im Dateinamen, nicht in der Belegnummer.
    alt = lies(BREIT, name="Rechnung_kunde_RE0001.pdf", richtung="ausgang")
    neu = lies(BREIT + "\nersetzt die stornierte Rechnung RE0001\n",
               name="Rechnung_kunde_RE0002.pdf", richtung="ausgang")
    nachbearbeiten([alt, neu])
    assert alt["behandlung"] == "aussortiert", alt["behandlung"]
    assert neu["behandlung"] == "ausgang", neu["behandlung"]

@fall("A-02 ohne Stornohinweis wird nichts aussortiert")
def _():
    a = lies(BREIT, name="Rechnung_kunde_RE0001.pdf", richtung="ausgang")
    nachbearbeiten([a])
    assert a["behandlung"] == "ausgang"

@fall("G-07 mehrdeutiges Datum, im Dokument aufloesbar")
def _():
    j, mo, sicher = rechnungsdatum(SLASH_AUFLOESBAR)
    assert (j, mo, sicher) == (2026, 9, True), (j, mo, sicher)

@fall("G-07 unaufloesbares Datum wird als unsicher markiert")
def _():
    *_, sicher = rechnungsdatum(SLASH_UNAUFLOESBAR)
    assert sicher is False

@fall("B-07 Datum aus der Zeile unter dem Spaltenkopf")
def _():
    j, mo, _ = rechnungsdatum(UMBRUCH)
    assert (j, mo) == (2026, 9), (j, mo)

@fall("B-07 Ordinalzahl im Datum")
def _():
    j, mo, _ = rechnungsdatum("Date    Sep 11th 2026\n")
    assert (j, mo) == (2026, 9)

@fall("B-07 ISO mit einstelligem Monat")
def _():
    j, mo, _ = rechnungsdatum("Date of Exportation: 2026-9-29\n")
    assert (j, mo) == (2026, 9)

@fall("B-07 ohne Datum: gemeldet, nicht stillschweigend verworfen")
def _():
    b = lies(OHNE_DATUM)
    assert b is not None and b["status"] == "datum_unbestimmt"

@fall("Zeitraumfilter: Beleg aus einem anderen Monat faellt heraus")
def _():
    assert lies(BREIT.replace("06.09.2026", "06.08.2026")) is None

@fall("E-18 eigene Firmierung wird nicht als Lieferant gelesen")
def _():
    assert lieferant_name(OHNE_HINWEIS, NAMEN) == "Muster Research Inc"

@fall("E-18 Labelwort ist kein Lieferantenname")
def _():
    assert lieferant_name("Invoice number ABC Inc\n", NAMEN) != "Invoice number ABC Inc"


def main():
    breite = max(len(n) for n, _ in FAELLE)
    fehler = 0
    for name, f in FAELLE:
        try:
            f(); print(f"  [OK  ] {name}")
        except AssertionError as e:
            fehler += 1; print(f"  [FEHL] {name:{breite}}  {e}")
        except Exception as e:
            fehler += 1; print(f"  [KAPUTT] {name:{breite}}  {type(e).__name__}: {e}")
    print(f"\n{len(FAELLE)} Fälle, "
          + ("alle grün" if not fehler else f"{fehler} fehlgeschlagen"))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
