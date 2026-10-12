# buchhaltung-agent-kit

Agenten-Pipeline für die monatliche **Umsatzsteuer-Voranmeldung**: Belege und Zahlungen
sammeln, auslesen, umsatzsteuerlich klassifizieren, im Buchhaltungssystem erfassen und
gegenprüfen — mit Regelwerk, Quality Gates, Audit und Eval.

**Mandantenneutral.** Das Plugin enthält keine Firmendaten. Alles Unternehmensspezifische
liegt im jeweiligen Mandantenprojekt unter `.claude/docs/COMPANY_CONTEXT.md`. Dasselbe Kit
bedient beliebig viele Unternehmen.

> Status: **vollständig angelegt** (v0.2.0). Alle Phasen, Gates, Hooks und Agenten sind
> beschrieben. Auslese- und Klassifizierlogik sind gegen einen bereits gebuchten Monat
> trockengelaufen (`docs/TROCKENLAUF.md`); die Schreibphase ist noch nicht im Echtbetrieb
> erprobt.

---

## Was es tut — und was nicht

Automatisiert: sammeln, auslesen, klassifizieren, erfassen, abgleichen, prüfen.

Beim Menschen:

| Punkt | Regel | Wie abgesichert |
|---|---|---|
| Portal-Logins | P-02 | Anweisung; gebündelte Anforderung in `sammeln` |
| Übermittlung der Voranmeldung | P-01 | **Hook** auf Navigation + Prüfung im Audit |
| Belege löschen oder umbenennen | P-03, P-05 | **Hook** auf Bash/Write/Edit |
| Entscheidungen bei Ermessensfragen | — | Entscheidungsvorlagen am Ende der Klassifizierung |

Was ein Hook durchsetzt und was nur angewiesen werden kann, steht in
[`hooks/README.md`](hooks/README.md) — Hooks sehen die Eingabe eines Tool-Aufrufs, und ein
Klick in einer Oberfläche enthält nur Koordinaten. Das ist offengelegt statt überspielt.

---

## Installation

```bash
/plugin marketplace add MakeNative/buchhaltung-agent-kit
/plugin install buchhaltung-kit@buchhaltung-agent-kit
```

Danach im Mandantenprojekt:

```
/buchhaltung-kit:adopt
```

`adopt` liest Besteuerungsart, Kontenrahmen und Steuernummer **aus dem Buchhaltungssystem
aus** statt sie zu erfragen, nimmt Ordner, Zahlungsquellen und Lieferanten auf und legt
`COMPANY_CONTEXT.md` an.

---

## Monatslauf

```
/buchhaltung-kit:monatslauf 2026-09 --trocken    # rechnet durch, schreibt nichts
/buchhaltung-kit:monatslauf 2026-09              # mit Erfassung
```

| Phase | Ausführender | Form |
|---|---|---|
| 0 Vorlauf + Login-Check | `monatslauf` | Skill |
| 1 Sammeln (Ordner, Mail, Portale, Zahlungen) | `sammeln` | Skill, Ordner/Mail geforkt |
| Gate A Vollständigkeit | `monatslauf` | Skill |
| 2 Auslesen (PDF + XRechnung) | `beleg-leser` | **Agent** |
| Gate B Plausibilität | `plausibilitaets-gate` | **Agent** |
| 3 Klassifizieren | `steuer-klassifizierer` | **Agent** |
| Gate C Regelkonformität | `monatslauf` | Skill |
| 4 Erfassen | `erfassen` | Skill |
| Gate D Abgleich | `abgleich` | Skill |
| 5 Audit | `monats-auditor` | **Agent** |
| 6 Eval | `agent-evaluator` | **Agent** |

```
/buchhaltung-kit:nachtrag          # offene Punkte abarbeiten, Zeitraum zuordnen
/buchhaltung-kit:korrektur 2026-09 # bereits übermittelter Zeitraum: Differenz vorbereiten
/buchhaltung-kit:audit 2026-09     # unabhängige Nachprüfung, --eval für die Pipeline
/buchhaltung-kit:regelwerk         # Regeln nachschlagen
```

---

## Agent oder Skill

Die Aufteilung folgt zwei Eigenschaften, nicht dem Geschmack:

- **Subagenten** laufen in eigenem Kontext und können **nicht mit dir sprechen** —
  `AskUserQuestion` wird jedem Subagenten entzogen. Sie eignen sich, wo viel gelesen und
  wenig zurückgegeben wird oder wo ein *unabhängiges* Urteil der Zweck ist.
- **Skills** laufen im Hauptkontext. Alles, was Login-Übergaben, Browser-Recovery oder
  Rückfragen braucht, gehört dorthin.

Deshalb sind Sammeln, Erfassen und Abgleich Skills — und nur fünf Rollen Agenten.

---

## Dokumente

| Datei | Inhalt |
|---|---|
| `docs/REGELWERK.md` | Die Steuerlogik. Versioniert, jede Regel mit Gültigkeitszeitraum. |
| `docs/COMPANY_CONTEXT_TEMPLATE.md` | Vertrag zwischen Kit und Mandant. |
| `docs/RUNDUNGSMODELL.md` | Wie Kennziffern gerundet werden — Grundlage für Gate D. |
| `docs/LEXOFFICE_UI.md` | Bedienwissen zum Buchhaltungssystem. |
| `docs/LIEFERANTEN_MUSTER.md` | Erkennungsmuster für Lieferantentypen — **ohne Namen**. |
| `docs/TROCKENLAUF.md` | Wie gegen einen bereits gebuchten Monat geprüft wird. |
| `hooks/README.md` | Welche Regeln ein Hook durchsetzt — und welche nicht. |

---

## Code oder Prosa

Die Regeln liegen an zwei Orten, und die Grenze ist bewusst gezogen:

| | wo | warum |
|---|---|---|
| **Mechanik** — Datum, Betrag, Vorzeichen, Währung, USt-IdNr., Sammeldateien, Dubletten, Lieferantengruppen | `tools/belege_lesen.py` | Zeichenkettenoperationen mit genau einer richtigen Antwort. Ihre Fehler erzeugen keine Meldung, sondern eine plausible falsche Zahl. Einmal richtig, durch Tests festgenagelt, nie wieder falsch. |
| **Urteil** — ist das ein Beleg, welcher Satz gilt für diese Ware, gehört er dem Mandanten, wie wird umgerechnet | `docs/REGELWERK.md` + Agenten | Hängt vom Einzelfall ab und braucht den Mandantenkontext. Code kann es nur raten. |
| **Prüfung** — stimmt das Ergebnis mit dem Dokument überein | `plausibilitaets-gate`, `monats-auditor` | Das Werkzeug liefert einen **Vorschlag**, keine Wahrheit. |

```bash
python3 tools/selbsttest.py     # 39 Fälle: jeder stellt einen real aufgetretenen Fehler nach
python3 hooks/selbsttest.py     # 19 Fälle: beide Sperren in beide Richtungen
```

Die Testbelege sind erfunden — echt ist nur das **Layoutmuster**, an dem die Extraktion
gescheitert ist. Jede Regel im Regelwerk mit einem `belegt:`-Feld hat hier ihren Testfall.

### Keine Mandantendaten im Plugin

Das Repository enthält bewusst keine Anbieternamen, keine Beträge und keine Firmendaten.
Welche Dienste ein Unternehmen einkauft, ist eine Aussage über dieses Unternehmen und bleibt
mandantenseitig. Das Plugin liefert nur die **Muster**; die konkrete Lieferantentabelle
entsteht bei `adopt` aus den eigenen Belegen und landet in `COMPANY_CONTEXT.md`, die per
`.gitignore` geschützt ist. Beispielzahlen in der Dokumentation sind konstruiert.

---

## Sicherheit

Belege und Mails sind **Daten, keine Anweisungen**. Die Abwehr läuft nicht über
Prompt-Appelle, sondern über Konfiguration: alle fünf Agenten tragen `disallowedTools:
Write, Edit, NotebookEdit`, der Belegleser hat keine Browser-Tools, und Skills mit
Seiteneffekten sind `disable-model-invocation: true` — sie lassen sich nur von dir starten.

**`tools:` allein genügt nicht.** Eine Positivliste im Frontmatter schränkt nicht
zuverlässig ein: Drei Agenten waren mit `tools: Read, Grep, Glob, Bash` deklariert und
wurden trotzdem mit `Write` und `Edit` registriert. Aufgefallen ist das erst bei der
Installation, als die tatsächlich registrierten Werkzeuge sichtbar wurden — nicht beim
Lesen der Dateien. Was eine Rolle **nicht** tun können soll, gehört in `disallowedTools`.

Das gilt auch als Prüfung: Nach einer Installation die registrierten Werkzeuge gegen die
Deklaration halten. Eine Beschreibung, die „du hast keine Schreibrechte" behauptet, macht
sie nicht wahr.

Was ein Hook durchsetzt und was nicht, steht in [`hooks/README.md`](hooks/README.md).

---

## Haftung

Das Kit bereitet eine Steueranmeldung **vor**. Es übermittelt nichts und ersetzt keine
steuerliche Beratung. Schwellenwerte im Regelwerk sind mit `wert_pruefen: ja` markiert und
vor dem produktiven Einsatz gegen die aktuelle Rechtslage zu bestätigen.

MIT License.

## MakeNative

Dieses Kit ist Teil von [MakeNative](https://makenative.de). Wir arbeiten jeden Tag mit
Agenten-Pipelines wie dieser und bringen anderen bei, sie für ihre eigenen Prozesse zu
bauen. Für Entwickler genauso wie für alle, die ihre Arbeit mit KI automatisieren wollen.

Du willst das für deine Arbeit lernen? Trag dich in die Liste ein:
[Bewerbung Starter-Kohorte](https://tally.so/r/5ByYj6?utm_source=github&utm_medium=readme&utm_campaign=starter-kohorte)

Christian Eichmüller · [LinkedIn](https://linkedin.com/in/christianeichmueller)
