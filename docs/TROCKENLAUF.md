# Trockenlauf

Ein Trockenlauf wertet einen Zeitraum aus, der **bereits gebucht und geprüft** ist, und
vergleicht das Ergebnis mit dem bekannten Stand. Nichts wird geschrieben, nichts übermittelt.

Das ist die einzige Prüfung, die Extraktionsfehler findet, bevor sie Geld kosten — ein Lauf
gegen einen offenen Monat hat keinen Maßstab, gegen den er falsch sein könnte.

## Wann

- vor dem ersten echten Monatslauf eines neuen Mandanten
- nach jeder Änderung am Regelwerk oder an den Agenten
- wenn ein Lauf ein Ergebnis liefert, das zu glatt aussieht

## Maßstab

Nimm Größen, die der Lauf **nicht erraten** kann und die anderswo belegt sind:

| Größe | Gegenprobe |
|---|---|
| Anzahl Eingangsbelege | gebuchte Belege des Zeitraums |
| Anzahl gültiger Ausgangsrechnungen | Rechnungsausgangsbuch |
| Summe Ausgangsumsätze | offene Posten bzw. Umsatzkonto |
| Summe je Behandlung | Kennziffern der abgegebenen Voranmeldung |
| erkannte Dubletten | bekannt aus dem Lauf |
| aussortierte Stornos | Stornokette im System |
| nicht lesbare Belege | Abgleich Ordner gegen ausgewertete Dateien |

Summen je Behandlung sind der schärfste Test: Betrag **und** Zuordnung müssen gleichzeitig
stimmen, damit sie aufgehen.

## Auswertung

Eine Gesamtsumme, die stimmt, beweist die Aufteilung nicht. Prüfe die Kennziffern **einzeln**.

Im Erstlauf dieses Kits ging die Gesamtsumme des innergemeinschaftlichen Erwerbs auf den Cent
auf, während die Aufteilung zwischen Regelsatz und ermäßigtem Satz vollständig falsch war —
die Zahllast war trotzdem korrekt, weil Erwerbsteuer und Vorsteuer gegengleich laufen. Nur der
Einzelvergleich hat es gezeigt (E-05).

Gleiches gilt für Belege, die gar nicht erst auftauchten: ohne Abgleich der Dateianzahl bleibt
ein nicht lesbarer Scan unsichtbar, weil er keine Fehlermeldung erzeugt, sondern nur
Abwesenheit (B-05).

## Umgang mit Befunden

Jeder Befund wird zu einer Regel mit ID, nicht zu einem Einzelfix im Skript. Danach läuft der
Trockenlauf erneut — eine Regel, die den gefundenen Fall nicht schließt, ist nicht fertig.

Ein Trockenlauf ohne Befunde bei erstmaligem Einsatz ist kein gutes Zeichen, sondern ein
Grund, den Maßstab zu schärfen.

## Ergebnis

Der Lauf ist grün, wenn jede Einzelgröße trifft **und** jeder offen gelassene Punkt benannt
ist. Offene Punkte sind kein Mangel: ein Steuersatz, der nicht auf dem Beleg steht, muss offen
bleiben. Ein stiller Default wäre der Fehler.
