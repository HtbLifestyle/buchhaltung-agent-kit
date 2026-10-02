#!/usr/bin/env python3
"""Deterministische Belegextraktion.

Dieses Werkzeug macht den **mechanischen** Teil des Auslesens: Textebene gewinnen,
Sammeldateien zerlegen, Datum, Betrag, Vorzeichen, Währung, USt-IdNr. und Lieferant
bestimmen, Dubletten und Lieferantengruppen bilden.

Warum als Code und nicht als Anweisung an ein Modell: Jeder dieser Schritte ist eine
Zeichenkettenoperation mit genau einer richtigen Antwort, und die Fehler darin sind
**lautlos** — ein verschlucktes Minuszeichen, ein Betrag aus der Folgezeile, ein
Gruppierungsschlüssel, der fehlen kann. Sie erzeugen keine Fehlermeldung, sondern eine
plausible falsche Zahl. Deterministischer Code macht sie einmal falsch, lässt sich
testen und dann nie wieder falsch machen.

Was dieses Werkzeug **nicht** entscheidet, weil es Urteil braucht:
  - ob ein Dokument überhaupt ein Beleg ist (B-02)
  - welcher Steuersatz für eine Ware gilt, wenn der Beleg ihn nicht nennt (E-05)
  - ob ein Beleg dem Mandanten gehört (E-13)
  - wie ein Fremdwährungsbetrag umzurechnen ist (F-01)
Für all das setzt es eine Marke in `pruefen` und reicht weiter.

Das Ergebnis ist ein **Vorschlag**, keine Wahrheit. Das Plausibilitätsgate prüft es
unabhängig gegen die Dokumente.

Aufruf:
    python3 belege_lesen.py --zeitraum 2026-09 \
        --eingang <ordner> [--ausgang <ordner>] \
        [--context .claude/docs/COMPANY_CONTEXT.md] \
        [--eigene-ustid DE123456789] [--eigene-namen "Muster GmbH" "Muster UG"]

Ausgabe: eine JSON-Zeile je Beleg auf stdout, Zusammenfassung auf stderr.
"""
import argparse, collections, hashlib, json, os, pathlib, re, subprocess, sys

EU = {"AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","EL","HU","IE","IT","LV",
      "LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE","EU"}

MON = {"jan":1,"feb":2,"mar":3,"mär":3,"maer":3,"apr":4,"may":5,"mai":5,"jun":6,"jul":7,
       "aug":8,"sep":9,"oct":10,"okt":10,"nov":11,"dec":12,"dez":12}


# ───────────────────────────── Textebene ─────────────────────────────

def pdf_text(pfad):
    try:
        return subprocess.run(["pdftotext", "-layout", str(pfad), "-"],
                              capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return ""


def datei_hash(pfad):
    return hashlib.md5(pathlib.Path(pfad).read_bytes()).hexdigest()


# ───────────────────────── Datum (G-07, B-07) ─────────────────────────

LABEL = (r"(?:date of issue|invoice date|date of invoice|rechnungs-?\s*/?\s*lieferdatum|"
         r"rechnungsdatum|rechnung vom|belegdatum|issue date|\bdatum\b|\bdate\b)")
ORD = r"(?:st|nd|rd|th|\.)?"


def slash_konvention(t):
    """G-07: Die Konvention aus dem Dokument selbst ableiten.

    `09/01/2026` ist ohne Herkunft des Ausstellers nicht auflösbar. Findet sich im selben
    Dokument ein eindeutiger Fall (eine Zahl über 12), gilt dessen Konvention für alle.
    """
    dd_mm = mm_dd = False
    for a, b, _ in re.findall(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", t):
        if int(a) > 12: dd_mm = True
        if int(b) > 12: mm_dd = True
    if dd_mm and not mm_dd: return "dd/mm"
    if mm_dd and not dd_mm: return "mm/dd"
    return None


def _datum_aus(s, konv):
    """-> (jahr, monat, sicher) oder None. Reihenfolge = Verlässlichkeit."""
    if m := re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", s):          # ISO, auch 2026-6-29
        return int(m.group(1)), int(m.group(2)), True
    if m := re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b", s):        # 28.09.2026
        return int(m.group(3)), int(m.group(2)), True
    if m := re.search(r"([A-Za-zäöü]{3,})\s+(\d{1,2})" + ORD + r",?\s+(\d{4})", s):
        k = m.group(1)[:3].lower()                                     # September 28, 2026
        if k in MON: return int(m.group(3)), MON[k], True
    if m := re.search(r"(\d{1,2})" + ORD + r"\s+([A-Za-zäöü]{3,})\.?\s+(\d{4})", s):
        k = m.group(2)[:3].lower()                                     # 30. Sep 2026
        if k in MON: return int(m.group(3)), MON[k], True
    if m := re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", s):          # mehrdeutig
        a, b, j = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if b > 12: return j, a, True
        if a > 12: return j, b, True
        if konv == "mm/dd": return j, a, True
        if konv == "dd/mm": return j, b, True
        return j, b, False
    return None


def rechnungsdatum(t):
    """B-07: Label und Wert sind häufig getrennt — Spaltenkopf mit Wertzeile darunter
    oder Zeilenumbruch. Wer nur die Labelzeile liest, findet kein Datum und verwirft den
    Beleg stillschweigend."""
    konv = slash_konvention(t)
    zeilen = t.split("\n")
    kandidaten = []
    for i, z in enumerate(zeilen):
        m = re.search(LABEL + r"(.*)$", z, re.I)
        if not m: continue
        kandidaten.append(m.group(1))
        if not _datum_aus(m.group(1), konv):
            genommen = 0
            for j in range(i + 1, min(i + 5, len(zeilen))):
                if zeilen[j].strip():
                    kandidaten.append(zeilen[j]); genommen += 1
                    if genommen == 2: break
    for s in kandidaten:
        if r := _datum_aus(s, konv): return r
    # Kein Label getroffen oder keines trug ein Datum: ganzes Dokument, Ergebnis unsicher.
    if r := _datum_aus(t[:3000], konv):
        return r[0], r[1], False
    return None, None, False


# ───────────────────────── Betrag (G-08, G-10) ─────────────────────────

BETRAG_T1 = (r"(?:gesamtbetrag|zu zahlender betrag|rechnungssumme|rechnungsbetrag|"
             r"zahlbetrag|endbetrag|amount due|total amount|invoice total|total due|"
             r"grand total|betrag brutto)")
BETRAG_T2 = r"(?:^[ \t]*total\b|gesamtpreis|^[ \t]*summe\b)"
QUALIFIER = r"[^\d]*\b(netto|net|excl|ohne)\b"


def geld(s):
    """G-10: Beträge **mit Vorzeichen**. Das Minus gehört zum Wert — eine Gutschrift ohne
    Vorzeichen wird zur Ausgabe, und der Fehler verdoppelt sich."""
    v = []
    for x in re.findall(r"-?\d{1,3}(?:\.\d{3})+,\d{2}|-?\d+,\d{2}", s):
        v.append(float(x.replace(".", "").replace(",", ".")))
    for x in re.findall(r"-?\d{1,3}(?:,\d{3})+\.\d{2}|-?\d+\.\d{2}", s):
        v.append(float(x.replace(",", "")))
    return v


def groesster(v):
    """Betragsmäßig größter Wert mit erhaltenem Vorzeichen. Ein numerisches Maximum
    wählt bei einer Gutschriftzeile die Null."""
    return max(v, key=abs) if v else None


def gesamtbetrag(t):
    """G-08: am Label, zweistufig, letztes Vorkommen."""
    zeilen = t.split("\n")
    for label in (BETRAG_T1, BETRAG_T2):
        treffer = []
        for i, z in enumerate(zeilen):
            m = re.search(label + r"(.*)$", z, re.I)
            if not m: continue
            rest = m.group(1)
            if re.match(QUALIFIER, rest, re.I): continue   # "Gesamtbetrag netto"
            v = geld(m.group(0))
            # Wert in die Folgezeile umgebrochen — nur prüfen, wenn hinter dem Label
            # nichts mehr steht. Sonst zöge Fließtext fremde Zahlen an.
            if not v and not rest.strip():
                for j in range(i + 1, min(i + 4, len(zeilen))):
                    if zeilen[j].strip():
                        v = geld(zeilen[j]); break
            if v: treffer.append(groesster(v))
        if treffer: return treffer[-1]
    return None


# ───────────────────────── Währung (G-11) ─────────────────────────

def waehrung(t, betrag=None):
    """G-11: aus dem **Umfeld des Betrags**, nicht aus dem Dokumenttext. Ein
    Währungszeichen in einer Produktbezeichnung ist keine Währungsangabe."""
    if betrag is not None:
        muster = f"{abs(betrag):.2f}".replace(".", "[.,]")
        for m in re.finditer(r"[^\n]{0,30}" + muster + r"[^\n]{0,20}", t):
            u = m.group(0)
            if re.search(r"USD|\$", u): return "USD"
            if re.search(r"EUR|€", u):  return "EUR"
            if re.search(r"GBP|£", u):  return "GBP"
            if re.search(r"CHF", u):    return "CHF"
    if re.search(r"\bUSD\b", t):   return "USD"
    if re.search(r"\bEUR\b|€", t): return "EUR"
    return None


# ────────────────── Leistender (G-09, E-17, E-18) ──────────────────

def ustid_liste(t):
    """G-09: `DE123456789`, `BE 0123.456.789`, `EU123456789`, `EE VAT EE123456789`.
    Der Zahlenteil beginnt mit einer Ziffer — sonst verschluckt das Muster das
    dazwischenstehende Wort VAT/USt-IdNr."""
    out = []
    for m in re.finditer(r"\b([A-Z]{2})[\s\-.]?([0-9][0-9A-Z.\s\-]{5,13}[0-9A-Z])\b", t):
        land = m.group(1)
        rest = re.sub(r"[.\s\-]", "", m.group(2))
        if land in EU and 6 <= len(rest) <= 12:
            out.append((land, land + rest))
    return out


LAENDER = {
    "united states":"US","usa":"US","vereinigte staaten":"US",
    "united kingdom":"GB","great britain":"GB",
    "switzerland":"CH","schweiz":"CH","canada":"CA","kanada":"CA",
    "china":"CN","japan":"JP","australia":"AU","singapore":"SG","india":"IN",
    "ireland":"IE","irland":"IE","netherlands":"NL","niederlande":"NL",
    "belgium":"BE","belgien":"BE","denmark":"DK","daenemark":"DK",
    "estonia":"EE","estland":"EE","france":"FR","frankreich":"FR",
    "spain":"ES","spanien":"ES","italy":"IT","italien":"IT",
    "poland":"PL","polen":"PL","austria":"AT","oesterreich":"AT",
    "luxembourg":"LU","luxemburg":"LU","sweden":"SE","schweden":"SE",
    "norway":"NO","norwegen":"NO","czech":"CZ","tschechien":"CZ",
}


def land_aus_anschrift(t):
    """E-17: Anbieter außerhalb der EU führen oft gar keine USt-IdNr. Ihr Land steht im
    Adressblock. Mehrdeutig → None, nie raten."""
    tl = t.lower().replace("ö", "oe").replace("ä", "ae").replace("ü", "ue")
    gefunden = {c for n, c in LAENDER.items() if re.search(rf"\b{re.escape(n)}\b", tl)}
    gefunden.discard("DE")
    return gefunden.pop() if len(gefunden) == 1 else None


RECHTSFORM = (r"(?:GmbH(?:\s*&\s*Co\.?\s*KG)?|UG(?:\s*\(haftungsbeschr[^)]*\))?|AG|SE|KG|"
              r"OHG|e\.?K\.?|Inc\.?|LLC|Ltd\.?|PBC|Corp\.?|B\.?V\.?|N\.?V\.?|ApS|A/S|"
              r"O[ÜU]|AB|Oy|S\.?A\.?S?|S\.?R\.?L\.?|SARL|PLC|Pty)")
NICHT_NAME = re.compile(r"^(zahlungs|invoice|rechnungs|beleg|kunden|auftrags|bestell|"
                        r"total|summe|seite|page)", re.I)


def lieferant_name(t, eigene_namen=()):
    """Name des Leistenden über die Rechtsform.

    Die **eigenen** Firmierungen scheiden aus — die eigene Anschrift steht auf jedem
    Beleg und würde sonst als Leistender gelesen. Frühere Firmierungen gehören dazu
    (B-04).
    """
    eigen = re.compile("|".join(re.escape(n) for n in eigene_namen), re.I) if eigene_namen else None
    for z in t.split("\n")[:40]:
        z = z.strip()
        if not z or len(z) > 90: continue
        m = re.search(r"([A-ZÄÖÜ][\w\.\-&äöüß]*(?:\s+[A-ZÄÖÜa-zäöü0-9\.\-&]+){0,4}\s*,?\s*"
                      + RECHTSFORM + r")", z)
        if not m: continue
        name = re.sub(r"\s+", " ", m.group(1)).strip(" ,.")
        if eigen and eigen.search(name): continue
        if NICHT_NAME.match(name): continue
        return name
    return None


def verkaeufer(t, eigene_ustid):
    for land, voll in ustid_liste(t):
        if voll != eigene_ustid:
            return voll, land
    return None, land_aus_anschrift(t)


# ──────────────────── Steuermerkmale (E-01…E-15) ────────────────────

def marker(t):
    tl = t.lower()
    return dict(
        rc=bool(re.search(r"reverse charge|steuerschuldnerschaft des leistungsempf|"
                          r"article 196|artikel 196|autoliquidation|§\s*13b", tl)),
        ig=bool(re.search(r"artikel 138|article 138|innergemeinschaftliche lieferung|"
                          r"intra-?community supply", tl)),
        de=bool(re.search(r"(mehrwertsteuer|umsatzsteuer|mwst\.?|ust\.?)\s*\(?\s*"
                          r"(19|7)[,.]?0?\s*%", tl)),
    )


def saetze(t):
    """E-01/E-02: Nur ein Satz mit Steuerbetrag **ungleich null** ist wirksam.
    Rechnungsvorlagen führen regelmäßig eine ermäßigte Zeile mit `0,00` mit."""
    out = set()
    for m in re.finditer(r"\b(\d{1,2})(?:[.,]\d{1,2})?\s*%([^\n]*)", t):
        rest = geld(m.group(2))
        if rest and not any(rest): continue
        out.add(int(m.group(1)))
    return out


def klassifiziere(t, land, eigene_id_auf_beleg):
    """Entscheidungskette. Gibt (behandlung, regel) zurück."""
    mk = marker(t)
    s = saetze(t)
    wirksam = {x for x in s if x in (7, 19)}

    if mk["ig"]:
        # E-05: Der Beleg weist 0 % aus. Der deutsche Erwerbsteuersatz folgt aus der
        # Ware und ist aus dem Dokument nicht ableitbar — offen lassen, nie defaulten.
        if len(wirksam) == 1 and 0 not in s:
            return f"ig_erwerb_{wirksam.pop()}", "E-05"
        return "ig_erwerb_satz_offen", "E-05"

    if mk["rc"]:
        return ("§13b_eu", "E-03") if land in EU else ("§13b_drittland", "E-04")

    # E-15: Reverse Charge ohne ausdrücklichen Hinweis. Der fehlende Vermerk ist ein
    # formeller Mangel, kein anderer Sachverhalt.
    if eigene_id_auf_beleg and not wirksam and land != "DE":
        if land in EU: return "§13b_eu", "E-15"
        if land:       return "§13b_drittland", "E-15"
        return "§13b_verdacht", "E-15"

    if mk["de"] or land == "DE":
        if len(wirksam) > 1: return "inland_gemischt", "E-02"
        if wirksam:          return f"inland_{wirksam.pop()}", "E-01"
        # E-01: 0 % ausgewiesen → nichts abzuziehen. Kein Default auf den Regelsatz.
        return "inland_0", "E-01"

    return "kein_vorsteuerabzug", "E-10"


def ersetzt_nummer(t):
    m = re.search(r"ersetzt die stornierte (?:Teil)?[Rr]echnung\s+(\S+)", t)
    return m.group(1) if m else None


# ──────────────────── Sammeldateien (B-06) ────────────────────

NUMMER = (r"(?:Rechnungsnummer|Invoice number|Rechnungs-Nr\.?|Belegnummer)"
          r"\s*:?\s+([A-Z0-9][A-Z0-9\-/]{5,})")


def zerlege(t):
    """B-06: Eine Datei kann mehrere eigenständige Rechnungen enthalten.

    Wer sie als einen Beleg liest, erfasst willkürlich einen Vorgang und verliert die
    übrigen — ohne Fehlermeldung, weil ein Betrag ja gefunden wurde.
    """
    nrn = list(dict.fromkeys(re.findall(NUMMER, t)))
    if len(nrn) < 2:
        return [(nrn[0] if nrn else None, t)]
    teile = [s for s in re.split(r"(?=Rechnungsnummer|Invoice number)", t)
             if re.search(NUMMER, s)]
    if len(teile) < 2:
        return [(nrn[0], t)]
    return [(re.search(NUMMER, s).group(1), s) for s in teile]


# ──────────────────────────── Belegaufbau ────────────────────────────

def beleg_aus_text(t, zeitraum, *, name="", richtung="eingang", nummer=None,
                   anzahl=1, hash_=None, eigene_ustid="", eigene_namen=()):
    """Ein Beleg aus einem Textabschnitt. Gibt None zurück, wenn er nicht in den
    Zeitraum fällt."""
    j, mo, sicher = rechnungsdatum(t)
    if j is None:
        # B-07: Ohne bestimmbares Datum ist der Beleg nicht "außerhalb des Zeitraums",
        # sondern ungeprüft. Das muss sichtbar bleiben.
        return dict(datei=name, richtung=richtung, status="datum_unbestimmt",
                    pruefen=["datum_nicht_bestimmbar"])
    if (j, mo) != zeitraum:
        return None

    ustid, land = verkaeufer(t, eigene_ustid)
    eigene_id = bool(eigene_ustid) and eigene_ustid in re.sub(r"[.\s\-]", "", t)
    if richtung == "eingang":
        behandlung, regel = klassifiziere(t, land, eigene_id)
    else:
        behandlung, regel = "ausgang", "A-01"

    betrag = gesamtbetrag(t)
    w = waehrung(t, betrag)

    pruefen = []
    if w and w != "EUR":                 pruefen.append("umrechnung_fremdwaehrung")    # F-01
    if not sicher:                       pruefen.append("datum_mehrdeutig")            # G-07
    if behandlung == "ig_erwerb_satz_offen": pruefen.append("steuersatz_aus_ware")     # E-05
    if behandlung == "inland_gemischt":  pruefen.append("saetze_getrennt_erfassen")    # E-02
    if behandlung == "§13b_verdacht":    pruefen.append("leistender_land_unklar")      # E-15
    if regel == "E-15":                  pruefen.append("rc_hinweis_fehlt_auf_beleg")  # E-07
    if betrag is None:                   pruefen.append("betrag_nicht_gefunden")       # G-08
    if betrag is not None and betrag < 0:
        pruefen.append("gutschrift_mindert_bemessungsgrundlage")                       # A-03
    if anzahl > 1:                       pruefen.append("sammeldatei_zerlegt")         # B-06

    return dict(
        datei=name if anzahl == 1 else f"{name} [{nummer}]",
        hash=hash_, richtung=richtung,
        belegnummer=nummer, belege_in_datei=anzahl,
        datum=f"{j}-{mo:02d}", datum_sicher=sicher,
        lieferant=lieferant_name(t, eigene_namen), ustid=ustid, land=land,
        waehrung=w, betrag=betrag,
        belegart="gutschrift" if (betrag or 0) < 0 else "rechnung",
        behandlung=behandlung, regel=regel,
        ersetzt=ersetzt_nummer(t), pruefen=pruefen,
    )


def ordner_lesen(ordner, zeitraum, richtung, **kw):
    out = []
    for p in sorted(pathlib.Path(ordner).glob("*.pdf")):
        t = pdf_text(p)
        if not t.strip():
            # B-05: Ohne Textebene kein Datum — der Beleg ist ungelesen, nicht
            # außerhalb des Zeitraums. Der Agent muss ihn als Bild lesen.
            out.append(dict(datei=p.name, richtung=richtung, status="nicht_lesbar",
                            pruefen=["als_bild_lesen"]))
            continue
        teile = zerlege(t)
        h = datei_hash(p)
        for nr, teil in teile:
            b = beleg_aus_text(teil, zeitraum, name=p.name, richtung=richtung,
                               nummer=nr, anzahl=len(teile), hash_=h, **kw)
            if b: out.append(b)
    return out


# ──────────────────── Belegübergreifende Prüfungen ────────────────────

def schluessel(b):
    """E-16: Der Lieferantenname führt, die USt-IdNr. ist nur Rückfall.

    Umgekehrt trennt eine auf einem Beleg fehlende USt-IdNr. denselben Lieferanten
    wieder auf — und eine Gruppe mit einem Element ist nie uneinheitlich. Die Prüfung
    meldete dann null Befunde und sähe aus wie ein Erfolg.
    """
    return b.get("lieferant") or b.get("ustid")


def nachbearbeiten(belege):
    """Dubletten, Stornoketten, Lieferantenangleich und Konsistenzprüfung."""
    # Dubletten: Dateihash PLUS Belegnummer. Über den Hash allein gälten die Teile einer
    # zerlegten Sammeldatei als Dubletten voneinander (B-06).
    gesehen = {}
    for b in belege:
        if not b.get("hash"): continue
        k = (b["hash"], b.get("belegnummer"))
        if k in gesehen:
            b["dublette_von"] = gesehen[k]
            b.setdefault("pruefen", []).append("dublette")        # P-04
        else:
            gesehen[k] = b["datei"]

    # A-02: Stornierte und ersetzte Belege aussortieren. Die ersetzte Nummer muss nicht
    # die ganze Belegnummer sein — sie steckt oft im Dateinamen (`..._RE0001.pdf`).
    ersetzte = {b["ersetzt"] for b in belege if b.get("ersetzt")}
    for b in belege:
        felder = f"{b.get('belegnummer') or ''} {b.get('datei') or ''}"
        treffer = [e for e in ersetzte if e and e in felder]
        if treffer:
            b["behandlung"] = "aussortiert"; b["regel"] = "A-02"
            b["grund"] = f"storniert und ersetzt ({treffer[0]})"

    # E-18: USt-IdNr. und Ansässigkeit sind Eigenschaften des Lieferanten.
    bekannt = {}
    for b in belege:
        k = schluessel(b)
        if k and b.get("ustid"):
            bekannt.setdefault(k, (b["ustid"], b.get("land")))
    for b in belege:
        k = schluessel(b)
        if k in bekannt and not b.get("ustid") and b.get("richtung") == "eingang":
            ustid, land = bekannt[k]
            b["ustid"], b["land"], b["land_quelle"] = ustid, land, "lieferant_memory"
            b.setdefault("pruefen", []).append("ustid_vom_lieferanten_uebernommen")
            if b["behandlung"] in ("§13b_drittland", "§13b_verdacht", "kein_vorsteuerabzug"):
                b["behandlung"] = "§13b_eu" if land in EU else "§13b_drittland"
                b["regel"] = "E-18"

    # E-16: ein Lieferant, eine Behandlung — und ein Land.
    behandlungen = collections.defaultdict(set)
    laender = collections.defaultdict(set)
    for b in belege:
        k = schluessel(b)
        if k and b.get("richtung") == "eingang":
            behandlungen[k].add(b["behandlung"])
            laender[k].add(b.get("land"))
    for b in belege:
        k = schluessel(b)
        if not k: continue
        if len(behandlungen[k]) > 1:
            b.setdefault("pruefen", []).append("lieferant_uneinheitlich")
        if len({l for l in laender[k] if l}) > 1:
            b.setdefault("pruefen", []).append("lieferant_land_uneinheitlich")

    for b in belege:
        if "pruefen" in b:
            b["pruefen"] = list(dict.fromkeys(b["pruefen"]))
    return belege


def gruppen_kennzahlen(belege):
    """E-16-Selbstprüfung: Wie viele Lieferantengruppen haben nur einen Beleg?

    Auffällig viele Einzelgruppen bedeuten, dass der Gruppierungsschlüssel nicht trägt —
    dann ist ein Null-Befund kein Ergebnis, sondern ein Messfehler.
    """
    g = collections.Counter(schluessel(b) for b in belege
                            if b.get("richtung") == "eingang" and schluessel(b))
    ohne = sum(1 for b in belege
               if b.get("richtung") == "eingang" and not schluessel(b) and not b.get("status"))
    return dict(gruppen=len(g), einzelgruppen=sum(1 for v in g.values() if v == 1),
                ohne_schluessel=ohne)


# ──────────────────────────── Context / CLI ────────────────────────────

def aus_context(pfad):
    """Eigene USt-IdNr., Firmierungen und Belegordner aus COMPANY_CONTEXT.md."""
    t = pathlib.Path(pfad).read_text(encoding="utf-8", errors="replace")
    cfg = {}
    if m := re.search(r"^\s*ust[_\-]?id(?:nr)?\.?:\s*(\S+)", t, re.M | re.I):
        cfg["eigene_ustid"] = m.group(1).strip("\"'")
    namen = []
    if m := re.search(r"^\s*name:\s*(\S.*)$", t, re.M):
        namen.append(m.group(1).split("#")[0].strip().strip("\"'"))
    if m := re.search(r"^\s*frühere_firmierungen:\s*\[(.*?)\]", t, re.M | re.S):
        namen += [x.strip().strip("\"'") for x in m.group(1).split(",") if x.strip()]
    cfg["eigene_namen"] = [n for n in namen if n]
    for key, feld in (("eingangsrechnungen", "eingang"), ("ausgangsrechnungen", "ausgang")):
        if m := re.search(rf"^\s*{key}:\s*(\S.*)$", t, re.M):
            cfg[feld] = m.group(1).split("#")[0].strip().strip("\"'")
    return cfg


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zeitraum", required=True, help="JJJJ-MM")
    ap.add_argument("--eingang"), ap.add_argument("--ausgang")
    ap.add_argument("--context", help="Pfad zu COMPANY_CONTEXT.md")
    ap.add_argument("--eigene-ustid", default="")
    ap.add_argument("--eigene-namen", nargs="*", default=[])
    a = ap.parse_args(argv)

    cfg = aus_context(a.context) if a.context else {}
    eingang = a.eingang or cfg.get("eingang")
    ausgang = a.ausgang or cfg.get("ausgang")
    ustid = a.eigene_ustid or cfg.get("eigene_ustid", "")
    namen = a.eigene_namen or cfg.get("eigene_namen", [])
    if not eingang:
        ap.error("Kein Eingangsordner — weder --eingang noch im Context.")
    if not ustid:
        # Ohne eigene USt-IdNr. ist die eigene Nummer von der des Leistenden nicht zu
        # unterscheiden — sie steht auf jedem Beleg und würde als Lieferant gelesen.
        # Das wäre ein stiller Fehler über den ganzen Lauf, also lieber gar kein Lauf.
        ap.error("Keine eigene USt-IdNr. — ohne sie wird die eigene Nummer als die des "
                 "Leistenden gelesen. Setze `ust_id:` im Context oder --eigene-ustid.")
    if not namen:
        print("WARNUNG: keine eigenen Firmierungen bekannt — die eigene Gesellschaft kann "
              "als Lieferant erkannt werden (E-18). `unternehmen.name` im Context setzen.",
              file=sys.stderr)

    jahr, monat = (int(x) for x in a.zeitraum.split("-"))
    zeitraum = (jahr, monat)
    kw = dict(eigene_ustid=ustid, eigene_namen=namen)

    # <JJJJ> durch das Jahr ersetzen und `~` aufloesen — Context-Pfade sind oft relativ
    # zum Benutzerverzeichnis notiert, und glob() expandiert die Tilde nicht.
    def pfad(p):
        return os.path.expanduser(p.replace("<JJJJ>", str(jahr))) if p else p

    belege = ordner_lesen(pfad(eingang), zeitraum, "eingang", **kw)
    if ausgang:
        belege += ordner_lesen(pfad(ausgang), zeitraum, "ausgang", **kw)
    nachbearbeiten(belege)

    for b in belege:
        print(json.dumps(b, ensure_ascii=False))

    k = gruppen_kennzahlen(belege)
    offen = collections.Counter(p for b in belege for p in b.get("pruefen", []))
    print(f"{len(belege)} Belege · {k['gruppen']} Lieferanten "
          f"({k['einzelgruppen']} mit nur einem Beleg, {k['ohne_schluessel']} ohne "
          f"erkannten Lieferanten)", file=sys.stderr)
    for marke, n in offen.most_common():
        print(f"  {marke}: {n}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
