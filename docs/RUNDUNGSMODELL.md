# Rundungsmodell

Grundlage für den Abgleich (Gate D). Ohne dieses Modell schlägt der Abgleich an **korrekten**
Werten fehl, weil Buchhaltungssysteme Bemessungsgrundlage und Steuer je Kennziffer
unterschiedlich runden.

> Alle Zahlen hier sind **konstruierte Beispielwerte**. Sie zeigen das Muster, nicht die
> Daten eines bestimmten Unternehmens.

## Das Muster

Beobachtet: Die angezeigte Bemessungsgrundlage wird auf volle Einheiten abgerundet. Für die
Steuer gilt das aber **nicht einheitlich** — je nach Kennziffer wird sie auf der exakten oder
auf der gerundeten Basis berechnet.

| Kennziffer (Beispiel) | Basis exakt | angezeigt | ausgewiesene Steuer | berechnet auf |
|---|---|---|---|---|
| § 13b sonstige Leistungen EU | 1.250,40 | 1.250 | 237,58 | **exakte** Basis (1.250,40 × 19 % = 237,576) |
| ig. Erwerb Regelsatz | 48,30 | 48 | 9,12 | **gerundete** Basis (48 × 19 %) |
| ig. Erwerb ermäßigt | 52,70 | 52 | 3,64 | **gerundete** Basis (52 × 7 %) |

Eine Prüfung „Steuer == angezeigte Basis × Satz" scheitert damit an der ersten Zeile, eine
Prüfung „Steuer == exakte Basis × Satz" an der zweiten und dritten.

## Folgefehler: gegengleiche Positionen gehen auseinander

Erwerbsteuer und die darauf entfallende Vorsteuer müssen sich fachlich aufheben. Werden sie
auf unterschiedlichen Basen berechnet, tun sie das nicht:

```
Erwerbsteuer laut Einzelkennziffern : 9,12 + 3,64 = 12,76   (gerundete Basen)
Vorsteuer aus ig. Erwerb            : 12,87              (exakte Basen: 9,18 + 3,69)
Differenz                           :  0,11
```

Die Differenz fließt in die Zahllast ein.

**Konsequenz für den Agenten:** Die Abweichung wird **gemeldet, nicht korrigiert** und
blockiert den Lauf nicht. Ob es sich um ein Rundungsartefakt des Systems oder um eine
fehlerhafte Erfassung handelt, entscheidet der Mensch bzw. die Steuerkanzlei — vor der
Übermittlung.

## Prüfregeln für Gate D

```
1. Bemessungsgrundlage je Kennziffer
   angezeigte Basis == abgerundete Summe der zugeordneten Nettobeträge
   Toleranz 0,00 — Abrundung ist deterministisch

2. Steuerbetrag je Kennziffer
   Prüfe beide Varianten:
     a) exakte Basis    × Satz
     b) gerundete Basis × Satz
   Trifft eine zu  -> ok, Variante protokollieren
   Trifft keine zu -> blockieren

3. Gegengleichheit
   Steuer aus Reverse Charge == Vorsteuer aus Reverse Charge
   Erwerbsteuer              == Vorsteuer aus ig. Erwerb
   Verletzung -> MELDEN mit Centbetrag und beiden Quellwerten, nicht blockieren

4. Summen
   Umsatzsteuer gesamt == Summe der Steuerpositionen
   Vorsteuer gesamt    == Summe der Vorsteuerpositionen
   Zahllast            == Umsatzsteuer − Vorsteuer         Toleranz 0,00

5. Vollständigkeit
   Inlandsvorsteuer gesamt == Summe der als Inlandsumsatz klassifizierten Vorsteuerbeträge
   Jede Kennziffer mit Wert hat mindestens einen zugeordneten Beleg
```

Variante 2a/2b wird je Kennziffer **gelernt** und im Laufprotokoll des Mandanten festgehalten.
Weicht ein späterer Lauf vom gelernten Verhalten ab, ist das ein Hinweis auf eine
Systemänderung und wird gemeldet.

## Warum keine pauschale Toleranz

Eine Toleranz von einem Cent würde genau die Fehler verdecken, die das Gate finden soll.
Stattdessen: deterministische Varianten prüfen, Unerklärtes melden.
