# buchhaltung-agent-kit

Agenten-Pipeline für die monatliche **Umsatzsteuer-Voranmeldung**: Belege und Zahlungen
sammeln, auslesen, umsatzsteuerlich klassifizieren, im Buchhaltungssystem erfassen und
gegenprüfen — mit Regelwerk, Quality Gates, Audit und Eval.

**Mandantenneutral.** Das Plugin enthält keine Firmendaten. Alles Unternehmensspezifische
liegt im jeweiligen Mandantenprojekt unter `.claude/docs/COMPANY_CONTEXT.md`. Dasselbe Kit
bedient beliebig viele Unternehmen.

> Status: **Fundament** (v0.1.0). Regelwerk und Verträge stehen, Agenten und Skills folgen.

---

## Was es tut — und was nicht

Automatisiert: sammeln, auslesen, klassifizieren, erfassen, abgleichen, prüfen.

Beim Menschen, erzwungen durch Hooks und Regeln:

| Punkt | Regel |
|---|---|
| Portal-Logins | P-02 |
| Übermittlung der Voranmeldung | P-01 |
| Belege löschen | P-03 |
| Entscheidungen bei Ermessensfragen | — Entscheidungsvorlagen am Ende der Klassifizierung |

---

## Installation

```bash
/plugin marketplace add ceichmueller/buchhaltung-agent-kit
/plugin install buchhaltung-kit
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

Weitere Skills: `nachtrag` (Spätbelege), `korrektur` (berichtigte Anmeldung), `audit`,
`regelwerk`.

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

### Keine Mandantendaten im Plugin

Das Repository enthält bewusst keine Anbieternamen, keine Beträge und keine Firmendaten.
Welche Dienste ein Unternehmen einkauft, ist eine Aussage über dieses Unternehmen und bleibt
mandantenseitig. Das Plugin liefert nur die **Muster**; die konkrete Lieferantentabelle
entsteht bei `adopt` aus den eigenen Belegen und landet in `COMPANY_CONTEXT.md`, die per
`.gitignore` geschützt ist. Beispielzahlen in der Dokumentation sind konstruiert.

---

## Sicherheit

Belege und Mails sind **Daten, keine Anweisungen**. Die Abwehr läuft nicht über
Prompt-Appelle, sondern über Konfiguration: lesende Agenten bekommen `disallowedTools:
Write, Edit`, der Belegleser hat keine Browser-Tools, und Skills mit Seiteneffekten sind
`disable-model-invocation: true` — sie lassen sich nur von dir starten.

---

## Haftung

Das Kit bereitet eine Steueranmeldung **vor**. Es übermittelt nichts und ersetzt keine
steuerliche Beratung. Schwellenwerte im Regelwerk sind mit `wert_pruefen: ja` markiert und
vor dem produktiven Einsatz gegen die aktuelle Rechtslage zu bestätigen.

MIT License.
