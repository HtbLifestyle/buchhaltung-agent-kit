---
name: sammeln
description: "Stellt für einen Zeitraum zusammen, welche Belege es geben müsste und welche davon vorliegen — aus Belegordner, Postfächern, Anbieterportalen und Zahlungsmeldungen. Erzeugt die Soll-Liste und fordert nötige Logins gebündelt an. Triggers on: /buchhaltung-kit:sammeln <YYYY-MM>"
disable-model-invocation: true
---

Du stellst die **Soll-Liste** eines Zeitraums auf: was es geben müsste, was vorliegt, was
fehlt und warum.

Diese Skill läuft im Hauptkontext, weil Portale Logins brauchen und ein Subagent dich nicht
fragen kann. Die datenintensiven Teile — Ordner durchsehen, Postfächer durchsuchen — lagerst
du aus, indem du den `beleg-leser` einsetzt oder Suchen bündelst.

## Grundsatz

Die Erwartung speist sich aus **Zahlungen und bekannten Lieferanten**, nicht aus dem
Ordnerinhalt (Regel P-06). Ein Ordner zeigt nur, was zufällig abgelegt wurde.

## Schritt 1 — Erwartung aufbauen

Drei Quellen:

1. **Zahlungsmeldungen** des Zeitraums aus den Postfächern laut Context (Bank, Karte,
   Zahlungsdienste). Je Zahlung: Datum, Empfänger, Betrag, Währung.
2. **Wiederkehrende Lieferanten** aus `COMPANY_CONTEXT.md`, auch ohne Zahlungsmeldung —
   manche rechnen per Sammellastschrift oder Guthaben ab (Muster M-09).
3. **Ausgangsrechnungen** aus dem Ausgangsordner und dem Buchhaltungssystem.

Beachte dabei:
- Guthabenaufladungen sind **keine** Belege (E-11) — sie erzeugen keine Erwartung auf einen
  Beleg in gleicher Höhe, sondern den Hinweis auf eine spätere periodische Rechnung.
- Lieferanten mit Muster M-08 rechnen verspätet ab → Status `noch_nicht_ausgestellt` (E-12).
- Ausschlussliste anwenden (E-13): Fremdbelege erzeugen keine Erwartung.

## Schritt 2 — Login-Check **vor** dem Sammeln

Öffne alle Portale, die für die Lieferanten dieses Zeitraums gebraucht werden, und
klassifiziere jedes:

| Status | Erkennung |
|---|---|
| `session_ok` | Zielseite lädt mit Inhalt |
| `login_noetig` | Weiterleitung auf eine Anmeldemaske |
| `domain_gesperrt` | Navigation wird von der Browser-Erweiterung abgelehnt |

Die dritte Lage ist **kein** Login-Problem — sie braucht eine Freigabe in den
Erweiterungseinstellungen. Verwechsle das nicht, sonst schickst du den Nutzer auf die falsche
Fährte.

Schreibe `05-login-bedarf.md` und lege **alle betroffenen Tabs gleichzeitig offen**. Dann
eine einzige Anforderung an den Nutzer, nicht fünf nacheinander:

```
Portal      Status            Betrifft                 Tab
<name>      login_noetig      <n> Rechnungen, ~<x> €   offen
<name>      domain_gesperrt   <n> Rechnungen           Freigabe nötig
```

**Begleiteter Lauf:** warte, prüfe nach der Rückmeldung erneut, mach weiter.
**Unbeaufsichtigter Lauf:** warte nicht. Hol alles Erreichbare, markiere den Rest als
`portal_login_noetig` und trage ihn ins Offene-Punkte-Register ein.

Gib niemals Zugangsdaten ein (P-02).

## Schritt 3 — Belege zusammentragen

In dieser Reihenfolge, weil jede Stufe billiger ist als die nächste:

1. **Belegordner** — was schon da ist
2. **Postfächer** — Anhänge und Links in Rechnungsmails
3. **Portale** — nur für das, was noch fehlt

Neue Dateien legst du nach dem Namensschema aus dem Context im Belegordner ab. Originale
werden nicht verändert (P-05): Wenn ein Anbieter einen kryptischen Dateinamen liefert, lege
eine Kopie mit sprechendem Namen an oder vermerke die Zuordnung — benenne das Original nicht
um, wenn der Context `originale_unveraendert: true` setzt.

Bei Portalen, die PDFs nur im Browser-Viewer anzeigen: Hinweis auf die Browsereinstellung
geben, statt zu versuchen, den Viewer zu bedienen — dessen Bedienleiste ist nicht erreichbar.

## Schritt 4 — Soll-Liste schreiben

`.claude/buchhaltung-log/<zeitraum>/10-soll-liste.md`:

```
quelle        zahlung | lieferantenliste | ausgangsordner
lieferant
erwartet_am   Datum oder Zeitraum
betrag        falls bekannt, mit Währung
status        vorhanden | fehlt | portal_login_noetig | domain_gesperrt
              | noch_nicht_ausgestellt | kein_beleg_erwartet | ausgeschlossen
datei         Pfad, falls vorhanden
begruendung   bei allem außer "vorhanden"
```

## Schritt 5 — Offene Punkte fortschreiben

Lies `.claude/buchhaltung-offene-punkte.md`, hake Erledigtes ab und trage Neues ein. Ohne
dieses Register wird eine Rechnung, die erst im Folgemonat erscheint, nie wieder gesucht.

## Rückgabe

```
Zeitraum <x>: <n> Belege erwartet, <v> vorhanden, <f> offen
Offen:
  <lieferant> — <status> — <begruendung>
Zahlungen ohne Belegerwartung: <Liste mit Grund, z. B. Guthabenaufladung>
Ausgeschlossen: <Liste>
```
