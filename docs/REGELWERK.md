# Regelwerk — Umsatzsteuer-Voranmeldung

```
REGELWERK_VERSION: 1
STAND: 2026-10
GELTUNG: Deutschland, Regelbesteuerung
```

Dieses Dokument ist die Entscheidungsgrundlage des `steuer-klassifizierer`. Es ist
**mandantenneutral** — keine Firmennamen, keine Kontonummern, keine Ordnerpfade. Alles
Mandantenspezifische steht in `COMPANY_CONTEXT.md` des jeweiligen Projekts.

> **Kein Steuerrat.** Das Regelwerk bildet die Praxis ab, die ein Buchhaltungsagent
> anwenden soll. Schwellenwerte und Pflichten ändern sich. Jede Regel mit
> `wert_pruefen: ja` muss gegen die aktuelle Rechtslage bestätigt werden, bevor sie
> produktiv greift. Im Zweifel entscheidet die Steuerkanzlei, nicht der Agent.

## Aufbau einer Regel

```
ID          Kurztitel
regel:      Was gilt.
gilt_ab:    JJJJ-MM-TT        gilt_bis: offen | JJJJ-MM-TT
pruefung:   Woran der Agent es erkennt.
folge:      Welche Kennziffer / welche Kategorie / welche Konsequenz.
wert_pruefen: ja|nein         # Schwellenwert gegen aktuelle Rechtslage bestätigen
```

Regeln werden nie gelöscht, nur mit `gilt_bis` geschlossen. Ein Lauf für einen
zurückliegenden Zeitraum verwendet die Regeln, die **damals** galten.

---

## G — Grundlagen

### G-01 Besteuerungsart wird ausgelesen, nie angenommen
- **regel:** Ob Soll- oder Ist-Versteuerung gilt, wird aus den Einstellungen des
  Buchhaltungssystems gelesen und in `COMPANY_CONTEXT.md` festgeschrieben.
- **pruefung:** Einstellungsseite des Systems. Fehlt die Angabe → Lauf stoppt.
- **folge:** Steuert G-02 und A-01. Eine falsche Annahme verschiebt die gesamte
  Umsatzseite eines Monats.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### G-02 Steuerentstehung
- **regel:** Bei **Soll**-Versteuerung entsteht die Umsatzsteuer mit Ablauf des Zeitraums,
  in dem die Leistung ausgeführt wurde. Bei **Ist**-Versteuerung mit Ablauf des Zeitraums,
  in dem das Entgelt **vereinnahmt** wurde.
- **pruefung:** Bei Ist: Zahlungseingang belegen, nicht das Rechnungsdatum verwenden.
- **folge:** Bei Ist gehören unbezahlte Ausgangsrechnungen **nicht** in den Zeitraum.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### G-03 Vorsteuerabzug ist nicht zahlungsabhängig
- **regel:** Der Vorsteuerabzug setzt eine ordnungsgemäße Rechnung und die ausgeführte
  Leistung voraus — auch beim Ist-Versteuerer, der seine Ausgangsumsätze nach Zahlung
  versteuert.
- **folge:** Eingangsrechnungen gehören in den Zeitraum des Rechnungseingangs, nicht der
  Zahlung.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### G-04 Maßgebliches Datum
- **regel:** Für die Zuordnung zählt das Rechnungs- bzw. Leistungsdatum auf dem Beleg.
  Bestelldatum, Lieferdatum der Ware und Zahlungsdatum sind **nicht** maßgeblich.
- **pruefung:** Datum aus dem Belegtext, nicht aus Dateiname, Bestellübersicht oder
  Kontoauszug.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### G-07 Numerische Datumsangaben sind mehrdeutig
- **regel:** Ein Datum der Form `09/01/2026` ist **nicht** auflösbar, ohne die Herkunft des
  Ausstellers zu kennen. Dasselbe Schriftbild bedeutet je nach Anbieter Tag/Monat oder
  Monat/Tag.
- **pruefung:** Belegt an zwei Rechnungen desselben Zeitraums: ein deutscher Anbieter
  schrieb `09/01/2026` für den 9. Januar, ein ausländischer `09/15/2026` für den 15. September.
  Eine Zahl über 12 an zweiter Stelle beweist Monat/Tag — darunter beweist nichts.
- **folge:** Bevorzuge in dieser Reihenfolge: ausgeschriebener Monat („September 28, 2026"),
  ISO (`2026-09-08`), deutsches Format mit Punkten (`28.09.2026`). Bleibt nur ein
  mehrdeutiges numerisches Datum, wird die Herkunft des Ausstellers herangezogen und das
  Ergebnis als `unsicher` markiert. Lässt sich die Mehrdeutigkeit nicht auflösen →
  `entscheidung_noetig`, nie raten.
- **zusatz:** Ein Beleg, dessen ermitteltes Datum außerhalb des Laufzeitraums liegt, aber
  dessen Dateiname oder Ablageort auf den Zeitraum deutet — und umgekehrt — ist immer ein
  Prüffall.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### G-05 Voranmeldungszeitraum und Frist
- **regel:** Monat oder Quartal gemäß Context. Abgabefrist ist der 10. Tag nach Ablauf des
  Zeitraums; mit Dauerfristverlängerung einen Monat später.
- **folge:** Bei Quartalsmeldung laufen alle Phasen über drei Monate; Zahlungszuordnung und
  Abgleich rechnen über den gesamten Zeitraum.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### G-06 Dauerfristverlängerung und Sondervorauszahlung
- **regel:** Bei Dauerfristverlängerung verschiebt sich die Frist um einen Monat. Die
  Sondervorauszahlung ist jährlich anzumelden und im letzten Voranmeldungszeitraum des
  Jahres anzurechnen.
- **pruefung:** `dauerfristverlängerung` im Context.
- gilt_ab: 2020-01-01 · wert_pruefen: ja

---

## E — Eingangsseite

### E-01 Inlandsleistung mit offenem Steuerausweis
- **regel:** Deutscher Lieferant mit deutscher USt-IdNr./Steuernummer und ausgewiesener
  Steuer → Vorsteuerabzug im Regelsatz oder ermäßigten Satz.
- **folge:** Vorsteuer in die Kennziffer für abziehbare Vorsteuer.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-02 Ermäßigter Satz erkennen
- **regel:** Bücher, Zeitschriften und Personenbeförderung unterliegen dem ermäßigten Satz.
  Buchhaltungssysteme schlagen häufig den Regelsatz vor.
- **pruefung:** Steuersatz **vom Beleg** übernehmen, nicht den Vorschlag bestätigen.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-03 Reverse Charge bei Leistungen aus dem EU-Ausland
- **regel:** Sonstige Leistung eines im EU-Ausland ansässigen Unternehmers an einen
  inländischen Unternehmer → Steuerschuldnerschaft des Leistungsempfängers.
- **pruefung:** Lieferant mit EU-USt-IdNr., 0 % ausgewiesen, Hinweis auf Reverse Charge
  bzw. Art. 196 MwStSystRL.
- **folge:** Bemessungsgrundlage und Steuer in die § 13b-Kennziffern, Vorsteuer in gleicher
  Höhe gegen — **zahllastneutral**.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-04 Reverse Charge bei Drittlandsbezug
- **regel:** Wie E-03, aber Lieferant im Drittland → eigene Kategorie/Konto, getrennt von
  EU-Bezügen.
- **pruefung:** Sitz des Lieferanten, nicht die Währung der Rechnung.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-05 Innergemeinschaftlicher Erwerb
- **regel:** Warenlieferung aus einem anderen EU-Mitgliedstaat an einen inländischen
  Unternehmer mit USt-IdNr. → innergemeinschaftlicher Erwerb. Eigene Kategorie, **nicht**
  § 13b und **nicht** Inlandsvorsteuer.
- **pruefung:** Vermerk „steuerfreie innergemeinschaftliche Lieferung" bzw. Art. 138
  MwStSystRL, Versendungsland im EU-Ausland, 0 % ausgewiesen.
- **folge:** Erwerb mit dem für die Ware geltenden Satz versteuern (Regelsatz oder
  ermäßigt), Vorsteuer daraus in gleicher Höhe gegen — zahllastneutral.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-06 Marktplatzbelege einzeln lesen
- **regel:** Bei Plattformen mit Drittanbietern bestimmt der **jeweilige Verkäufer** das
  Steuerregime, nicht die Plattform. Jede Rechnung wird einzeln ausgewertet.
- **pruefung:** Verkäufer, dessen USt-IdNr., Versendungsland und Steuervermerk je Beleg.
- **folge:** Innerhalb einer Plattform können Inlandsumsatz, ig. Erwerb und Drittlandsbezug
  nebeneinander auftreten.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-07 Formelle Rechnungsanforderungen
- **regel:** Der Vorsteuerabzug setzt eine Rechnung mit den gesetzlichen Pflichtangaben
  voraus.
- **pruefung:** Vollständiger Name und Anschrift beider Parteien, Steuernummer oder
  USt-IdNr. des Leistenden, Ausstellungsdatum, fortlaufende Rechnungsnummer, Menge und
  Bezeichnung der Leistung, Entgelt, Steuersatz und Steuerbetrag bzw. Hinweis auf
  Steuerbefreiung.
- **folge:** Fehlt eine Pflichtangabe → `vorsteuerfaehig: nein` mit Benennung der fehlenden
  Angabe. Kein stillschweigender Abzug.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-08 Kleinbetragsrechnung
- **regel:** Unterhalb eines Gesamtbetrags-Schwellenwerts genügen erleichterte Angaben
  (Name und Anschrift des Leistenden, Ausstellungsdatum, Leistungsbeschreibung, Entgelt und
  Steuerbetrag in einer Summe, Steuersatz).
- **folge:** E-07 greift unterhalb der Schwelle nur eingeschränkt.
- **schwellenwert:** 250 EUR brutto
- gilt_ab: 2017-01-01 · wert_pruefen: ja

### E-09 Kein Vorsteuerabzug bei nicht abziehbaren Betriebsausgaben
- **regel:** Für Aufwendungen, die ertragsteuerlich nicht abziehbar sind, entfällt der
  Vorsteuerabzug. Bei Bewirtungsaufwendungen gilt die Einschränkung ertragsteuerlich nur
  anteilig, der Vorsteuerabzug bleibt bei ordnungsgemäßem Beleg dagegen in voller Höhe
  erhalten.
- **pruefung:** Geschenke oberhalb der Freigrenze, Repräsentation, private Mitveranlassung.
- **folge:** `vorsteuerfaehig: nein` bzw. anteilig, mit Begründung.
- **schwellenwert Geschenke:** je Empfänger und Jahr — Betrag gegen aktuelle Rechtslage
  prüfen
- gilt_ab: 2020-01-01 · wert_pruefen: ja

### E-10 Belege ohne Steuerausweis und ohne Reverse-Charge-Hinweis
- **regel:** Fehlen sowohl ein Steuerausweis als auch ein Reverse-Charge-Hinweis und die
  USt-IdNr. des Empfängers, ist weder Vorsteuerabzug noch § 13b begründbar.
- **folge:** Als Betriebsausgabe ohne Steuer erfassen, Begründung dokumentieren, Lieferant
  zur Korrektur der Rechnungsdaten vormerken.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-11 Guthabenaufladungen sind keine Belege
- **regel:** Vorauszahlungen auf ein Guthabenkonto (Werbekonten, Prepaid-Dienste) sind
  keine Leistungsabrechnung. Maßgeblich ist die periodische Rechnung des Anbieters.
- **folge:** Zahlung nicht als Beleg führen; die zugehörige Rechnung in der Soll-Liste
  erwarten.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-12 Verspätet ausstellende Anbieter
- **regel:** Anbieter, die erst im Folgemonat abrechnen, erzeugen im Zeitraum eine Lücke,
  die kein Fehler ist.
- **folge:** Status `noch_nicht_ausgestellt` statt `fehlt`; Eintrag ins Offene-Punkte-Register.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-13 Belege fremder Gesellschaften
- **regel:** Rechnungen, die auf eine andere Gesellschaft lauten oder deren Leistung einer
  anderen Gesellschaft zuzurechnen ist, werden nicht erfasst — auch wenn die
  Zahlungsbestätigung im eigenen Postfach landet.
- **pruefung:** Rechnungsadressat und, bei Portalen, die Organisation im Anbieterkonto.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### E-14 Rechnungen auf eine natürliche Person
- **regel:** Belege, die auf eine Privatperson statt auf das Unternehmen lauten, werden
  markiert und nicht stillschweigend gebucht.
- **folge:** Entscheidungsvorlage; parallel Hinweis, die Rechnungsdaten beim Anbieter zu
  korrigieren.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

---

## A — Ausgangsseite

### A-01 Umsatz bei Ist-Versteuerung
- **regel:** Der Ausgangsumsatz zählt im Zeitraum des Zahlungseingangs. Unbezahlte
  Rechnungen bleiben außen vor.
- **pruefung:** Offene-Posten-Liste des Buchhaltungssystems gegen die Ausgangsrechnungen
  des Zeitraums abgleichen.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### A-02 Stornoketten auflösen
- **regel:** Wird eine Rechnung storniert und ersetzt, darf nur die wirksame Rechnung in die
  Bemessungsgrundlage eingehen.
- **pruefung:** Ersatzrechnungen verweisen im Fließtext auf die stornierte Nummer. Der
  Nummernkreis wird zusätzlich auf Lücken geprüft.
- **folge:** Liegt die stornierte Rechnung in einem bereits gemeldeten Zeitraum, ist die
  Berichtigung im Zeitraum der Änderung vorzunehmen.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### A-03 Änderung der Bemessungsgrundlage
- **regel:** Skonto, Teilzahlung, Gutschrift, Rückabwicklung und uneinbringliche Forderungen
  ändern die Bemessungsgrundlage im Zeitraum der Änderung, nicht rückwirkend.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### A-04 Anzahlungen und Teilrechnungen
- **regel:** Teil- und Schlussrechnungen werden getrennt betrachtet. Bei Ist-Versteuerung
  ist jede vereinnahmte Teilzahlung ein eigener Entstehungszeitpunkt.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### A-05 Zusammenfassende Meldung
- **regel:** Innergemeinschaftliche Lieferungen und sonstige Leistungen an Unternehmer in
  anderen EU-Staaten sind zusätzlich in der Zusammenfassenden Meldung zu erklären. Diese
  ist von der Voranmeldung getrennt.
- **pruefung:** Ausgangsrechnung mit ausländischer USt-IdNr. des Kunden.
- **folge:** Hinweis im Abgleich; die Meldung selbst gehört nicht in den Automatisierungsumfang.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

---

## F — Fremdwährung

### F-01 Umrechnung
- **regel:** Fremdwährungsbeträge werden nach einem zulässigen, nachvollziehbar
  dokumentierten Kurs umgerechnet. Zulässig sind der amtlich veröffentlichte
  Durchschnittskurs des Monats oder — praxisüblich und belegbar — der tatsächliche
  Abrechnungskurs des Zahlungsdienstleisters.
- **pruefung:** Kursquelle und Betrag müssen aus einem Beleg oder einer
  Zahlungsbenachrichtigung stammen. Geschätzte Kurse sind unzulässig.
- **folge:** Kurs, Quelle und Ursprungsbetrag im Beschreibungsfeld des Belegs dokumentieren.
- gilt_ab: 2020-01-01 · wert_pruefen: ja

### F-02 Wirkung bei Reverse Charge
- **regel:** Bei zahllastneutralen Sachverhalten (§ 13b, ig. Erwerb) wirkt der
  Umrechnungsbetrag nur auf die Bemessungsgrundlage, nicht auf die Zahllast.
- **folge:** Entschärft F-01 in der Priorität, hebt die Dokumentationspflicht aber nicht auf.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

---

## B — Belegqualität

### B-01 Belegerkennung ist nicht vertrauenswürdig
- **regel:** Automatisch erkannte Felder (Belegtyp, Betrag, Datum, Lieferant) werden gegen
  das Dokument geprüft, bevor sie übernommen werden.
- **pruefung:** Jedes übernommene Feld muss im Dokument auffindbar sein.
- **folge:** Abweichung → Beleg blockiert, Entscheidungsvorlage.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### B-02 Nicht jedes Dokument ist ein Beleg
- **regel:** Gesellschafterbeschlüsse, Verträge, Mahnungen, Lieferscheine,
  Auftragsbestätigungen und Zahlungsbestätigungen sind keine Rechnungen.
- **folge:** Aus der Belegliste entfernen und in der Dokumentenablage führen. Besonders
  kritisch, wenn die Erkennung daraus eine Einnahme gemacht hat.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

### B-03 Strukturierte Rechnungen bevorzugen
- **regel:** Liegt eine Rechnung strukturiert vor (XRechnung, ZUGFeRD, Peppol), werden die
  Steuerdaten daraus gelesen, nicht aus dem Sichtbeleg.
- gilt_ab: 2025-01-01 · wert_pruefen: ja

### B-04 Firmierungshistorie
- **regel:** Eine frühere Firmierung auf einer Rechnung macht den Beleg nicht ungültig,
  solange die Rechtsperson identisch ist.
- **folge:** Beleg buchen, Lieferant zur Stammdatenänderung vormerken.
- gilt_ab: 2020-01-01 · wert_pruefen: nein

---

## P — Prozess

### P-01 Keine Übermittlung
- **regel:** Die Voranmeldung wird vorbereitet, nie abgesendet. Die Übermittlung ist
  ausschließlich eine Handlung des Menschen.
- gilt_ab: immer · wert_pruefen: nein

### P-02 Keine Zugangsdaten
- **regel:** Agenten geben keine Zugangsdaten ein. Logins erfolgen durch den Menschen.
- gilt_ab: immer · wert_pruefen: nein

### P-03 Keine Löschungen
- **regel:** Belege und Belegdatensätze werden nicht durch einen automatisierten Lauf
  gelöscht. Löschen ist ein eigener, manuell angestoßener und einzeln freigegebener Vorgang.
- gilt_ab: immer · wert_pruefen: nein

### P-04 Keine Doppelbuchung
- **regel:** Vor dem Anlegen eines Belegs wird gegen den Bestand geprüft. Dedup-Schlüssel:
  Lieferant, Belegnummer, Belegdatum, Bruttobetrag.
- **folge:** Treffer → überspringen und als `bereits_vorhanden` protokollieren.
- gilt_ab: immer · wert_pruefen: nein

### P-05 Originalbelege bleiben unverändert
- **regel:** Aufbewahrungspflichtige Belege werden nicht verändert oder umbenannt. Sprechende
  Namen entstehen über eine Zuordnungsdatei, jede Bewegung wird protokolliert.
- gilt_ab: immer · wert_pruefen: nein

### P-06 Vollständigkeit über Zahlungen, nicht über den Ordner
- **regel:** Die Erwartungsliste eines Zeitraums speist sich aus den Zahlungsvorgängen und
  den bekannten wiederkehrenden Lieferanten — nicht aus dem, was zufällig im Ordner liegt.
- gilt_ab: immer · wert_pruefen: nein

### P-07 Jede Klassifikation nennt ihre Regel
- **regel:** Jeder klassifizierte Beleg trägt die ID der angewandten Regel. Ohne Regelbezug
  keine Erfassung.
- **folge:** Ermöglicht Audit, Eval und die Begründung gegenüber der Steuerkanzlei.
- gilt_ab: immer · wert_pruefen: nein

---

## Kennziffern-Zuordnung

Die konkreten Kennziffern der Voranmeldung und die Kategoriebezeichnungen des
Buchhaltungssystems stehen in `COMPANY_CONTEXT.md` bzw. in der Systemdokumentation
(`LEXOFFICE_UI.md` für lexoffice), weil sie system- und formularabhängig sind.

Fachliche Zuordnung:

| Sachverhalt | Regel | Wirkung auf die Zahllast |
|---|---|---|
| Inlandsumsatz | A-01 | erhöht |
| Inlandsvorsteuer | E-01, E-02 | mindert |
| § 13b EU / Drittland | E-03, E-04 | neutral (Steuer und Vorsteuer gegengleich) |
| Innergemeinschaftlicher Erwerb | E-05 | neutral |
| Ohne Vorsteuerabzug | E-09, E-10 | keine |

---

## Änderungshistorie

| Version | Datum | Änderung |
|---|---|---|
| 1 | 2026-10 | Erstfassung, abgeleitet aus einem realen Monatslauf |
