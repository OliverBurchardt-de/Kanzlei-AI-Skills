#!/usr/bin/env python3
"""slop_scan.py — Diagnose maschinell wirkender Sprache.

Das Skript misst Oberflaechenmerkmale, die bei KI-Text auffaellig oft
gleichfoermig ausfallen: Satzrhythmus, Absatzrhythmus, Fuellformeln,
Gedankenstriche, Dreierketten, Negativparallelen.

Es bewertet keine Qualitaet. Ein Text kann jede Kennzahl reissen und
trotzdem gut sein, und er kann alle Kennzahlen treffen und trotzdem leer
klingen. Die Ausgabe ist eine Liste von Stellen zum Nachsehen, keine
Mangelliste zum Abarbeiten. Wer nach Kennzahl umschreibt, erzeugt genau
die Gleichfoermigkeit, die hier gesucht wird.

Aufruf:
    python3 slop_scan.py DATEI [DATEI ...] [--profil PROFIL] [--json]
    cat text.md | python3 slop_scan.py - --profil fachtext

Profile (references/MESSWERTE.md erklaert die Herkunft der Werte):
    fachtext         deutsche Fachbeitraege und Mandantentexte
    fiktion-knapp    englische Belletristik, knapper Dialogton
    fiktion-kaskade  englische Belletristik, langer Erzaehlbogen
    auto             nach Sprache raten (Standard)
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# --------------------------------------------------------------------------
# Referenzwerte
#
# Gemessen am 26.09.2026 ueber die Fachtexte in korpus/fachtext/ und die
# Belletristik-Ausschnitte in korpus/fiktion/. Es sind Beobachtungswerte
# aus einem kleinen Korpus, keine Normen. Siehe references/MESSWERTE.md.
# --------------------------------------------------------------------------

REFERENZ = {
    # Fachtext deutsch: gemessen an den drei Beitraegen in korpus/fachtext/
    # (Ø 14.5–19.1 Woerter, Streuung 8.9–9.2, 14–27 % kurze Saetze,
    #  0–2.7 Gedankenstriche je 1000 Woerter, keine Fuellformeln).
    # Die Schwellen liegen knapp unter dem schwaechsten Kanonwert, damit
    # ein echter Text nicht beim ersten Ausreisser anschlaegt.
    "fachtext": {
        "sprache": "de",
        "satz_mittel": (13.0, 22.0),
        "satz_streuung_min": 7.5,       # Standardabweichung der Satzlaengen
        "anteil_kurz_min": 0.12,        # Saetze <= 8 Woerter
        "fueller_pro_1k_max": 1.0,
        "gedankenstrich_pro_1k_max": 5.0,
    },
    # Belletristik, knapper Dialogton: Tonprobe Three Weeks in a Bikini
    # (Ø 11.5, Streuung 5.7, 34 % kurze Saetze, keine Gedankenstriche).
    "fiktion-knapp": {
        "sprache": "en",
        "satz_mittel": (9.0, 17.0),
        "satz_streuung_min": 5.0,
        "anteil_kurz_min": 0.26,
        "fueller_pro_1k_max": 1.0,
        "gedankenstrich_pro_1k_max": 4.0,
    },
    # Belletristik, kaskadierender Erzaehlton: A Life Between Names, Kap. 35
    # (Ø 22.4, Streuung 17.2, 25 % kurze Saetze, 12.7 Gedankenstriche/1000).
    # Ein eigener Massstab, weil derselbe Autor hier bewusst anders schreibt.
    # Die Streuung trennt hier am schaerfsten: Kapitel 35 liegt bei 17.2,
    # das deutlich schwaechere Kapitel 1 desselben Buches bei 11.0.
    "fiktion-kaskade": {
        "sprache": "en",
        "satz_mittel": (17.0, 32.0),
        "satz_streuung_min": 14.0,
        "anteil_kurz_min": 0.15,
        "fueller_pro_1k_max": 1.0,
        "gedankenstrich_pro_1k_max": 16.0,
    },
}

STANDARDPROFIL = {"de": "fachtext", "en": "fiktion-knapp"}

FUELLER_DE = [
    "in der heutigen zeit", "in der heutigen", "von entscheidender bedeutung",
    "es ist wichtig zu beachten", "es ist wichtig", "lassen sie uns",
    "unerlässlich", "unerlaesslich", "maßgeschneidert", "massgeschneidert",
    "ganzheitlich", "passgenau", "zögern sie nicht", "zoegern sie nicht",
    "im folgenden betrachten", "im folgenden", "nicht zu unterschätzen",
    "gilt es zu beachten", "vorteile ausschöpfen", "spielt eine zentrale rolle",
    "spielt eine wichtige rolle", "wegweisend", "bahnbrechend",
    "umfassende beratung", "individuelle beratung", "kompetente beratung",
    "sorgfältig prüfen", "sorgfaeltig pruefen", "frühzeitig planen",
    "in der schnelllebigen", "ein wichtiger baustein", "das a und o",
    "es bleibt abzuwarten", "wie bereits erwähnt", "zusammenfassend lässt sich sagen",
    "abschließend lässt sich festhalten", "ein entscheidender faktor",
    "weit mehr als nur", "nicht nur ein", "revolutioniert", "meistern",
    "navigieren sie", "tauchen sie ein", "in der welt der",
]

FUELLER_EN = [
    "in today's world", "in today's fast-paced", "it is important to note",
    "it's important to note", "it is worth noting", "delve into", "dive into",
    "navigate the", "a testament to", "plays a crucial role",
    "plays a vital role", "plays a pivotal role", "at the end of the day",
    "when it comes to", "in conclusion", "furthermore", "moreover",
    "landscape of", "realm of", "tapestry", "unlock the", "unleash",
    "game-changer", "cutting-edge", "seamless", "robust solution",
    "ever-evolving", "underscores the", "highlights the importance",
    "not only", "meticulous", "embark on", "foster a", "leverage the",
    "it's worth mentioning", "needless to say", "last but not least",
]

# Bedeutungsaufblaehung: Adjektive/Adverbien, die Wirkung behaupten,
# statt sie zu zeigen.
AUFBLAEHUNG_DE = [
    "erheblich", "maßgeblich", "massgeblich", "enorm", "gravierend",
    "essentiell", "essenziell", "fundamental", "immens", "signifikant",
    "beträchtlich", "betraechtlich", "zentral", "elementar", "eminent",
]
AUFBLAEHUNG_EN = [
    "profound", "remarkable", "significant", "crucial", "vital", "pivotal",
    "immense", "stark", "compelling", "striking", "undeniable", "palpable",
]

# Kopula-Vermeidung: aufwendige Fuegungen anstelle von "ist" / "hat".
# Aus Wikipedia:Signs of AI writing, Abschnitt "copula avoidance", auf das
# Deutsche uebertragen — dort besonders haeufig, weil Nominalstil in
# Fachtexten ohnehin als seriös gilt.
KOPULA_DE = [
    "stellt dar", "stellt einen dar", "stellt eine dar", "fungiert als",
    "dient als", "bildet einen", "bildet eine", "verfügt über",
    "zeichnet sich durch", "zeichnet sich dadurch aus", "weist auf",
    "findet sich", "erweist sich als", "gestaltet sich", "nimmt eine ein",
    "kommt zum tragen", "bietet die möglichkeit",
]
KOPULA_EN = [
    "serves as", "stands as", "acts as", "functions as", "represents a",
    "marks a", "boasts a", "boasts an", "features a", "offers a",
    "constitutes a", "emerges as", "positions itself as",
]

# Uebertriebenes Absichern. Im Deutschen ist die Haeufung von "kann",
# "könnte" und "unter Umständen" das verlaesslichste Zeichen.
HEDGING_DE = [
    "könnte möglicherweise", "möglicherweise könnte", "unter umständen",
    "in der regel eher", "tendenziell eher", "durchaus denkbar",
    "nicht ausgeschlossen", "es ist denkbar", "könnte man argumentieren",
    "es lässt sich argumentieren", "in gewissem maße", "gewissermaßen",
]
HEDGING_EN = [
    "could potentially", "it could be argued", "may possibly",
    "it is worth considering", "to some extent", "in some cases",
    "arguably", "somewhat", "relatively speaking",
]

# Autoritaetsgestus: kuendigt eine tiefere Wahrheit an, liefert aber den
# gewoehnlichen Punkt mit Zeremonie.
AUTORITAET_DE = [
    "die eigentliche frage", "die eigentliche gefahr", "im kern",
    "in wahrheit", "der entscheidende punkt", "worauf es wirklich ankommt",
    "das eigentliche problem", "letztlich geht es um",
    "der springende punkt",
]
AUTORITAET_EN = [
    "the real question is", "at its core", "in reality", "what really matters",
    "fundamentally", "the deeper issue", "the heart of the matter",
]

# Chatbot-Rueckstaende und Wissensstand-Vorbehalte, die im Text
# stehenbleiben.
ARTEFAKTE_DE = [
    "ich hoffe, das hilft", "gerne!", "selbstverständlich!",
    "da hast du recht", "lass mich wissen", "möchtest du, dass ich",
    "hier ist ein", "nach den mir vorliegenden informationen",
    "soweit verfügbar", "stand meines wissens", "konkrete angaben liegen",
    "zusammenfassend lässt sich festhalten", "insgesamt lässt sich festhalten",
]
ARTEFAKTE_EN = [
    "i hope this helps", "of course!", "certainly!",
    "you're absolutely right", "let me know if", "would you like me to",
    "as of my last", "up to my last training", "based on available information",
    "while specific details are limited",
]

ABKUERZUNGEN = {
    "de": ["z.b", "bzw", "ggf", "u.a", "d.h", "evtl", "inkl", "abs", "nr",
           "rz", "vgl", "ca", "bspw", "s.o", "s.u", "str", "estg", "ao",
           "erbstg", "ustg", "kstg", "gewstg", "bgb", "hgb", "estr", "estdv"],
    "en": ["mr", "mrs", "ms", "dr", "prof", "st", "e.g", "i.e", "vs", "etc",
           "jr", "sr", "inc", "ltd", "no", "fig"],
}


@dataclass
class Befund:
    """Eine Auffaelligkeit mit Ort und Vorschlag."""
    art: str
    schwere: str          # "hinsehen" oder "notieren"
    text: str
    stelle: str = ""

    def zeile(self) -> str:
        marke = "!!" if self.schwere == "hinsehen" else " ."
        ort = f" [{self.stelle}]" if self.stelle else ""
        return f"  {marke} {self.art}{ort}: {self.text}"


@dataclass
class Bericht:
    datei: str
    sprache: str
    profil: str = ""
    woerter: int = 0
    saetze: int = 0
    satz_mittel: float = 0.0
    satz_streuung: float = 0.0
    satz_median: float = 0.0
    anteil_kurz: float = 0.0
    anteil_lang: float = 0.0
    absatz_mittel: float = 0.0
    absatz_streuung: float = 0.0
    fueller_pro_1k: float = 0.0
    aufblaehung_pro_1k: float = 0.0
    gedankenstrich_pro_1k: float = 0.0
    dreierketten: int = 0
    negativparallelen: int = 0
    kopula_pro_1k: float = 0.0
    hedging_pro_1k: float = 0.0
    falsche_spannen: int = 0
    fettlisten: int = 0
    emojis: int = 0
    ueberschriften: int = 0
    dialogschwaenze: int = 0
    adverbtags: int = 0
    filterverben: int = 0
    befunde: list = field(default_factory=list)


def sprache_raten(text: str) -> str:
    de = len(re.findall(r"\b(der|die|das|und|nicht|ist|eine|werden|sich)\b",
                        text, re.I))
    en = len(re.findall(r"\b(the|and|of|to|is|that|with|was|it)\b",
                        text, re.I))
    return "de" if de >= en else "en"


def saetze_teilen(text: str, sprache: str) -> list[str]:
    """Satzgrenzen finden und gaengige Abkuerzungen nicht als Satzende zaehlen."""
    geschuetzt = text
    for abk in ABKUERZUNGEN.get(sprache, []):
        geschuetzt = re.sub(
            rf"(?<![\w]){re.escape(abk)}\.", f"{abk}\u0001", geschuetzt, flags=re.I
        )
    # Ordnungszahlen und Paragraphenziffern: "§ 7 Abs. 4 S. 1" u. a.
    geschuetzt = re.sub(r"(\d)\.(?=\s|\d|$)", "\\1\u0001", geschuetzt)

    # Typografische Anfuehrungszeichen muessen als Satzanfang gelten, sonst
    # verschmilzt in Belletristik jede Replik mit dem Satz davor.
    roh = re.split(
        r"(?<=[.!?:])[\s ]+(?=[A-ZÄÖÜ\"“‘‚„«»'])", geschuetzt)
    ergebnis = []
    for s in roh:
        s = s.replace("\u0001", ".").strip()
        if s:
            ergebnis.append(s)
    return ergebnis


def woerter_zaehlen(s: str) -> int:
    return len([w for w in re.split(r"[\s ]+", s.strip()) if re.search(r"\w", w)])


def text_saeubern(roh: str) -> tuple[str, list[str]]:
    """Markdown-Geruest entfernen. Gibt Fliesstext und Absaetze zurueck."""
    t = roh
    # YAML-Kopf zuerst, sonst zaehlen quelle/stufe/herkunft als Fliesstext mit
    # und verschieben Satzlaenge und Absatzrhythmus.
    t = re.sub(r"\A---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)", "", t, flags=re.S)
    t = re.sub(r"```.*?```", " ", t, flags=re.S)          # Codebloecke
    t = re.sub(r"^\s*(\||[-*+]\s|\d+\.\s|>).*$", "", t, flags=re.M)  # Tabellen, Listen, Zitate
    t = re.sub(r"^#{1,6}\s.*$", "", t, flags=re.M)        # Ueberschriften
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)      # Links, Bilder
    t = re.sub(r"<[^>]+>", " ", t)                        # HTML
    t = re.sub(r"[*_`]{1,3}", "", t)                      # Auszeichnung
    t = re.sub(r"^\s*---+\s*$", "", t, flags=re.M)

    absaetze = [a.strip() for a in re.split(r"\n\s*\n", t) if woerter_zaehlen(a) >= 12]
    fliess = re.sub(r"[ \t ]+", " ", "\n\n".join(absaetze)).strip()
    return fliess, absaetze


def zaehle_phrasen(text_klein: str, phrasen: list[str]) -> list[tuple[str, int]]:
    treffer = []
    for p in phrasen:
        n = text_klein.count(p)
        if n:
            treffer.append((p, n))
    return sorted(treffer, key=lambda x: -x[1])


def finde_dreierketten(saetze: list[str], sprache: str) -> list[str]:
    """A, B und C bzw. A, B, and C — im Fliesstext, nicht in Listen."""
    if sprache == "de":
        muster = re.compile(
            r"\b([\wäöüß]+(?:\s+[\wäöüß]+){0,2}),\s+([\wäöüß]+(?:\s+[\wäöüß]+){0,2})"
            r"\s+(?:und|oder|sowie)\s+([\wäöüß]+(?:\s+[\wäöüß]+){0,2})\b", re.I)
    else:
        muster = re.compile(
            r"\b(\w+(?:\s+\w+){0,2}),\s+(\w+(?:\s+\w+){0,2})"
            r",?\s+(?:and|or)\s+(\w+(?:\s+\w+){0,2})\b", re.I)
    return [s for s in saetze if muster.search(s)]


def finde_negativparallelen(saetze: list[str], sprache: str) -> list[str]:
    if sprache == "de":
        muster = re.compile(
            r"(nicht nur\b.{0,120}?\bsondern auch)|"
            r"(\bnicht\b.{0,60}?,\s*sondern\b)|"
            r"(\bweniger\b.{0,60}?\bals vielmehr\b)", re.I | re.S)
    else:
        muster = re.compile(
            r"(not only\b.{0,120}?\bbut also)|"
            r"(\bit(?:'s| is) not\b.{0,80}?,?\s*(?:it(?:'s| is))?\s*\bit(?:'s| is)\b)|"
            r"(\bnot\b\s+\w+(?:\s+\w+){0,3},?\s+but\b)", re.I | re.S)
    return [s for s in saetze if muster.search(s)]


def finde_partizipschwaenze(saetze: list[str], sprache: str) -> list[str]:
    """Nachgestellte Partizipialphrasen, die Wirkung behaupten.

    Englisch: ", highlighting the ...", ", underscoring ...".
    Deutsch: ", was die Bedeutung ... unterstreicht".
    """
    if sprache == "en":
        muster = re.compile(
            r",\s+(?:highlighting|underscoring|emphasizing|showcasing|reflecting|"
            r"demonstrating|marking|signaling|cementing|solidifying|ensuring|"
            r"making it|serving as)\b", re.I)
    else:
        muster = re.compile(
            r",\s+was\s+(?:die|den|das|dessen|deren)\b[^.]{0,80}?"
            r"(?:unterstreicht|verdeutlicht|zeigt|belegt|widerspiegelt|"
            r"hervorhebt|untermauert)\b", re.I)
    return [s for s in saetze if muster.search(s)]


def finde_dialogschwaenze(saetze: list[str]) -> list[str]:
    """Redebegleitsatz, an den eine Deutung angehaengt wird.

    Gemeint ist nicht jeder Nachsatz. „…“, Kathy said, reapplying gloss ist eine
    Handlung: Sie zeigt etwas, das im Raum passiert. Gemeint ist der Nachsatz,
    der das Innenleben benennt, statt es zu zeigen:

        „…“, she said, her voice a mixture of excitement and unease.
        „…“, I responded, trying to mask my own apprehension.

    Das ist die haeufigste Form maschineller Belletristik, und sie faellt durch
    keine Rhythmusmessung auf. Der Text sagt dem Leser das Gefuehl, damit er es
    nicht selbst aus der Szene ziehen muss — und nimmt ihm genau die Arbeit ab,
    die das Lesen lohnend macht.
    """
    tags = (r"said|asked|replied|answered|whispered|murmured|added|continued|"
            r"responded|offered|admitted|agreed|noted|remarked")
    # Partizipien, die einen inneren Vorgang behaupten statt einer Handlung
    innen = (r"trying|hoping|feeling|attempting|struggling|wondering|realizing|"
             r"realising|sensing|masking|hiding|betraying|revealing|suggesting|"
             r"indicating|conveying|meaning|knowing|willing|daring|managing")
    # „her voice a mixture of …“, „the tremor in his voice“
    koerper = r"(?:voice|eyes|face|tone|expression|smile|gaze)"
    muster = re.compile(
        rf"\b(?:{tags})\b\s*,\s*"
        rf"(?:(?:{innen})\b|h(?:er|is)\s+{koerper}\b|"
        rf"the\s+\w+\s+in\s+h(?:er|is)\s+{koerper}\b)", re.I)
    # Auch ohne Redebegleitsatz: „X, holding a mug, glanced over with a
    # thoughtful expression.“ — Zustand statt Vorgang.
    haltung = re.compile(
        r"\bwith\s+(?:an?\s+)?\w+\s+"
        r"(?:expression|smile|look|gaze|tone|air)\b", re.I)
    return [s for s in saetze if muster.search(s) or haltung.search(s)]


def finde_adverbtags(saetze: list[str]) -> list[str]:
    """„said nervously“ — das Adverb behauptet, was der Satz zeigen muesste."""
    muster = re.compile(
        r"\b(said|asked|replied|answered|whispered|murmured|shouted|added)\b\s+"
        r"\w+ly\b", re.I)
    return [s for s in saetze if muster.search(s)]


def finde_filterverben(saetze: list[str]) -> list[str]:
    """Wahrnehmung wird gemeldet statt gezeigt: „I felt“, „I noticed“, „I could see“.

    In der Ich-Erzaehlung ist die Wahrnehmung ohnehin die der Erzaehlerin. Das
    Filterverb schiebt eine Ebene dazwischen und nimmt der Szene die Unmittelbarkeit.
    """
    muster = re.compile(
        r"\bI\s+(?:could\s+)?(?:felt|feel|noticed|realized|realised|saw|see|"
        r"heard|hear|sensed|sense|watched|observed|found myself|became aware)\b")
    return [s for s in saetze if muster.search(s)]


def finde_falsche_spannen(saetze: list[str], sprache: str) -> list[str]:
    """„von X bis Y", wo X und Y auf keiner gemeinsamen Skala liegen.

    Aus Wikipedia:Signs of AI writing, "false ranges". Die Figur suggeriert
    Vollstaendigkeit, indem sie zwei Beispiele als Endpunkte ausgibt.
    """
    if sprache == "de":
        muster = re.compile(
            r"\bvon\s+(?:der|dem|den|des|einer|einem)?\s*[\wäöüß]+"
            r"(?:\s+[\wäöüß]+){0,3}\s+bis\s+(?:zur|zum|zu|hin\s+zu)\s+", re.I)
    else:
        muster = re.compile(r"\bfrom\s+\w+(?:\s+\w+){0,3}\s+to\s+(?:the\s+)?\w+", re.I)
    return [s for s in saetze if muster.search(s)]


def finde_fettlisten(roh: str) -> list[str]:
    """Aufzaehlung, deren Punkte mit fettem Begriff und Doppelpunkt beginnen.

    Die verbreitetste Formatmasche von Chatbots und in redaktionellen Texten
    praktisch nur dort zu finden.
    """
    # Zwischen Aufzaehlungszeichen und Fettung darf ein Emoji o. ae. stehen.
    # Zwischen Aufzaehlungszeichen und Fettung darf ein Emoji stehen, und
    # der Doppelpunkt steht mal innerhalb, mal ausserhalb der Fettung.
    treffer = re.findall(
        r"^[ \t]*[-*+][ \t]+[^\w\n]{0,4}[ \t]*"
        r"(?:\*\*[^*\n]{2,60}:\*\*|\*\*[^*\n]{2,60}\*\*[ \t]*:)", roh, re.M)
    return treffer


def zaehle_emojis(roh: str) -> int:
    muster = re.compile(
        "[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U00002600-\U000026FF"
        "\U0001F000-\U0001F0FF\u2705\u274C\u2B50\u2728]")
    return len(muster.findall(roh))


def pruefe_ueberschriften(roh: str) -> tuple[int, list[str]]:
    """Ueberschriftenflut und Ueberschriften, deren erster Satz sie wiederholt.

    Zurueck kommt die Zahl der Ueberschriften und die Liste der Stellen, an
    denen direkt darunter ein kurzer Satz steht, der die Ueberschrift nur
    noch einmal sagt (Wikipedia: "fragmented headers").
    """
    zeilen = roh.split("\n")
    ueber = [(i, z) for i, z in enumerate(zeilen) if re.match(r"^#{1,6}\s+\S", z)]
    leerlauf = []
    for i, z in ueber:
        titel = re.sub(r"^#{1,6}\s+", "", z).strip()
        # naechster nicht-leerer Absatz
        for j in range(i + 1, min(i + 4, len(zeilen))):
            kandidat = zeilen[j].strip()
            if not kandidat:
                continue
            if re.match(r"^(#{1,6}\s|[-*+|>]|\d+\.)", kandidat):
                break
            if woerter_zaehlen(kandidat) <= 9:
                leerlauf.append(f'\u201e{titel}\u201c \u2192 \u201e{kandidat}\u201c')
            break
    return len(ueber), leerlauf


def stellen(n: int) -> str:
    return "1 Stelle" if n == 1 else f"{n} Stellen"


def kuerze(s: str, n: int = 110) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def analysiere(roh: str, name: str, profil: str) -> Bericht:
    fliess, absaetze = text_saeubern(roh)
    geraten = profil == "auto"
    if geraten:
        profil = STANDARDPROFIL[sprache_raten(fliess)]
    sprache = REFERENZ[profil]["sprache"]

    b = Bericht(datei=name, sprache=sprache, profil=profil)
    if geraten and profil.startswith("fiktion"):
        # Die beiden Erzaehltoene lassen sich nicht aus dem Text ableiten;
        # gegen den falschen Massstab gemessen schlaegt alles aus.
        b.befunde.append(Befund(
            "Ma\u00dfstab geraten", "notieren",
            f"Profil {profil} automatisch gew\u00e4hlt. Die beiden Erz\u00e4hlt\u00f6ne "
            "haben verschiedene Kennwerte \u2014 mit --profil ausdr\u00fccklich setzen."))
    saetze = saetze_teilen(fliess, sprache)
    laengen = [woerter_zaehlen(s) for s in saetze]
    laengen = [n for n in laengen if n > 0]

    if len(laengen) < 5:
        b.befunde.append(Befund("zu kurz", "notieren",
                                "Weniger als fünf auswertbare Sätze — keine Aussage möglich."))
        return b

    ref = REFERENZ[profil]
    b.woerter = sum(laengen)
    b.saetze = len(laengen)
    b.satz_mittel = round(statistics.mean(laengen), 1)
    b.satz_median = round(statistics.median(laengen), 1)
    b.satz_streuung = round(statistics.pstdev(laengen), 1)
    b.anteil_kurz = round(sum(1 for n in laengen if n <= 8) / len(laengen), 3)
    b.anteil_lang = round(sum(1 for n in laengen if n >= 30) / len(laengen), 3)

    abs_laengen = [woerter_zaehlen(a) for a in absaetze]
    if len(abs_laengen) >= 3:
        b.absatz_mittel = round(statistics.mean(abs_laengen), 1)
        b.absatz_streuung = round(statistics.pstdev(abs_laengen), 1)

    pro_1k = lambda n: round(n * 1000 / b.woerter, 2) if b.woerter else 0.0
    klein = fliess.lower()

    fueller = zaehle_phrasen(klein, FUELLER_DE if sprache == "de" else FUELLER_EN)
    b.fueller_pro_1k = pro_1k(sum(n for _, n in fueller))

    aufb = zaehle_phrasen(klein, AUFBLAEHUNG_DE if sprache == "de" else AUFBLAEHUNG_EN)
    b.aufblaehung_pro_1k = pro_1k(sum(n for _, n in aufb))

    striche = fliess.count("—") + fliess.count("–")
    b.gedankenstrich_pro_1k = pro_1k(striche)

    drei = finde_dreierketten(saetze, sprache)
    b.dreierketten = len(drei)
    neg = finde_negativparallelen(saetze, sprache)
    b.negativparallelen = len(neg)
    partizip = finde_partizipschwaenze(saetze, sprache)

    # ---- Befunde ---------------------------------------------------------
    lo, hi = ref["satz_mittel"]
    if not (lo <= b.satz_mittel <= hi):
        b.befunde.append(Befund(
            "Satzlänge im Mittel", "notieren",
            f"{b.satz_mittel} Wörter, Korpus liegt bei {lo}–{hi}."))

    if b.satz_streuung < ref["satz_streuung_min"]:
        b.befunde.append(Befund(
            "Satzrhythmus gleichförmig", "hinsehen",
            f"Streuung {b.satz_streuung} (Korpus ab {ref['satz_streuung_min']}). "
            "Ein Text, dessen Sätze alle gleich lang sind, liest sich mechanisch."))

    if b.anteil_kurz < ref["anteil_kurz_min"]:
        b.befunde.append(Befund(
            "kaum kurze Sätze", "hinsehen",
            f"{b.anteil_kurz:.0%} der Sätze haben höchstens acht Wörter "
            f"(Korpus ab {ref['anteil_kurz_min']:.0%}). Ergebnisse bekommen "
            "Gewicht durch einen kurzen Satz daneben."))

    if b.absatz_streuung and b.absatz_mittel:
        if b.absatz_streuung / b.absatz_mittel < 0.30 and len(abs_laengen) >= 5:
            b.befunde.append(Befund(
                "Absätze gleich lang", "hinsehen",
                f"Mittel {b.absatz_mittel} Wörter, Streuung {b.absatz_streuung}. "
                "Gleich große Blöcke sind ein starkes Maschinensignal."))

    if b.fueller_pro_1k > ref["fueller_pro_1k_max"]:
        top = ", ".join(f"„{p}“ ×{n}" for p, n in fueller[:5])
        b.befunde.append(Befund(
            "Füllformeln", "hinsehen",
            f"{b.fueller_pro_1k}/1000 Wörter — {top}"))
    elif fueller:
        top = ", ".join(f"„{p}“ ×{n}" for p, n in fueller[:4])
        b.befunde.append(Befund("Füllformeln", "notieren", top))

    if aufb and b.aufblaehung_pro_1k > 2.0:
        top = ", ".join(f"„{p}“ ×{n}" for p, n in aufb[:5])
        b.befunde.append(Befund(
            "Bedeutungsaufblähung", "notieren",
            f"{b.aufblaehung_pro_1k}/1000 — {top}. Eine Zahl wirkt stärker "
            "als ein Adjektiv, das Wirkung behauptet."))

    if b.gedankenstrich_pro_1k > ref["gedankenstrich_pro_1k_max"]:
        b.befunde.append(Befund(
            "Gedankenstriche", "hinsehen",
            f"{b.gedankenstrich_pro_1k}/1000 Wörter. Doppelpunkt, Semikolon "
            "oder ein eigener Satz tragen dieselbe Fügung unauffälliger."))

    if drei and len(drei) * 1000 / b.woerter > 3.0:
        b.befunde.append(Befund(
            "Dreierketten", "notieren",
            f"{stellen(len(drei))}. Prüfen, ob das dritte Glied Information "
            f"trägt. Beispiel: {kuerze(drei[0])}"))

    for s in neg[:3]:
        b.befunde.append(Befund(
            "Negativparallele", "notieren",
            f"„nicht X, sondern Y“ — trägt Y neue Information? {kuerze(s)}"))

    for s in partizip[:3]:
        b.befunde.append(Befund(
            "Partizipialschwanz", "hinsehen",
            f"Nachsatz behauptet Bedeutung, statt sie zu zeigen. {kuerze(s)}"))

    # Erzaehlhandwerk. Diese Muster verraten maschinelle Belletristik am
    # zuverlaessigsten und schlagen in keiner Rhythmusmessung aus.
    if profil.startswith("fiktion"):
        dialog = finde_dialogschwaenze(saetze)
        adverb = finde_adverbtags(saetze)
        filt = finde_filterverben(saetze)

        b.dialogschwaenze = len(dialog)
        b.adverbtags = len(adverb)
        b.filterverben = len(filt)

        if dialog:
            b.befunde.append(Befund(
                "Deutung am Redebegleitsatz", "hinsehen",
                f"{stellen(len(dialog))}. Der Nachsatz sagt, was die Szene zeigen "
                f"sollte. Beispiel: {kuerze(dialog[0])}"))
        if adverb:
            b.befunde.append(Befund(
                "Adverb im Redebegleitsatz", "hinsehen",
                f"{stellen(len(adverb))}. Beispiel: {kuerze(adverb[0])}"))
        if filt and len(filt) * 1000 / b.woerter > 6.0:
            b.befunde.append(Befund(
                "Filterverben", "notieren",
                f"{stellen(len(filt))} „I felt / I noticed / I saw“ "
                f"({len(filt)*1000/b.woerter:.1f}/1000). In der Ich-Erzählung ist "
                f"die Wahrnehmung ohnehin ihre. Beispiel: {kuerze(filt[0])}"))

    # ---- Muster aus Wikipedia:Signs of AI writing ------------------------
    kop = zaehle_phrasen(klein, KOPULA_DE if sprache == "de" else KOPULA_EN)
    b.kopula_pro_1k = pro_1k(sum(n for _, n in kop))
    if b.kopula_pro_1k > 2.0:
        top = ", ".join(f"\u201e{p}\u201c \u00d7{n}" for p, n in kop[:5])
        b.befunde.append(Befund(
            "Kopula-Vermeidung", "hinsehen",
            f"{b.kopula_pro_1k}/1000 \u2014 {top}. Wo \u201eist\u201c oder "
            "\u201ehat\u201c passt, ist jede aufwendigere F\u00fcgung ein Umweg."))

    hedge = zaehle_phrasen(klein, HEDGING_DE if sprache == "de" else HEDGING_EN)
    b.hedging_pro_1k = pro_1k(sum(n for _, n in hedge))
    if b.hedging_pro_1k > 1.5:
        top = ", ".join(f"\u201e{p}\u201c \u00d7{n}" for p, n in hedge[:5])
        b.befunde.append(Befund(
            "Absicherung", "notieren",
            f"{b.hedging_pro_1k}/1000 \u2014 {top}. Eine begr\u00fcndete "
            "Unsicherheit tr\u00e4gt, eine gestapelte nicht."))

    aut = zaehle_phrasen(klein, AUTORITAET_DE if sprache == "de" else AUTORITAET_EN)
    for phrase, n in aut[:3]:
        b.befunde.append(Befund(
            "Autorit\u00e4tsgestus", "notieren",
            f"\u201e{phrase}\u201c \u00d7{n}. K\u00fcndigt eine tiefere Einsicht an. "
            "Tr\u00e4gt der folgende Satz sie?"))

    art = zaehle_phrasen(klein, ARTEFAKTE_DE if sprache == "de" else ARTEFAKTE_EN)
    for phrase, n in art[:4]:
        b.befunde.append(Befund(
            "Chatbot-R\u00fcckstand", "hinsehen",
            f"\u201e{phrase}\u201c \u00d7{n}. Geh\u00f6rt nicht in den Text."))

    spannen = finde_falsche_spannen(saetze, sprache)
    b.falsche_spannen = len(spannen)
    if spannen and len(spannen) * 1000 / b.woerter > 2.0:
        b.befunde.append(Befund(
            "falsche Spanne", "notieren",
            f"{stellen(len(spannen))} \u201evon \u2026 bis \u2026\u201c. Liegen die "
            f"Endpunkte auf einer Skala? {kuerze(spannen[0])}"))

    fett = finde_fettlisten(roh)
    b.fettlisten = len(fett)
    if len(fett) >= 3:
        b.befunde.append(Befund(
            "Fettlisten", "hinsehen",
            f"{len(fett)} Punkte im Muster \u201e**Begriff:** Erkl\u00e4rung\u201c. "
            "Das ist die auff\u00e4lligste Formatmasche von Chatbots."))

    b.emojis = zaehle_emojis(roh)
    if b.emojis:
        b.befunde.append(Befund(
            "Emojis", "hinsehen",
            f"{b.emojis} St\u00fcck. In Fachtext und Belletristik nicht vorgesehen."))

    b.ueberschriften, leerlauf = pruefe_ueberschriften(roh)
    if b.ueberschriften and b.woerter / max(b.ueberschriften, 1) < 90:
        b.befunde.append(Befund(
            "\u00dcberschriftenflut", "notieren",
            f"{b.ueberschriften} \u00dcberschriften auf {b.woerter} W\u00f6rter, also rund "
            f"{b.woerter // max(b.ueberschriften,1)} W\u00f6rter je Abschnitt."))
    for stelle in leerlauf[:3]:
        b.befunde.append(Befund(
            "Aufw\u00e4rmsatz unter \u00dcberschrift", "notieren",
            f"Der erste Satz sagt die \u00dcberschrift noch einmal: {stelle}"))

    # Satzanfaenge: mehrfach dasselbe Wort in Folge
    anfaenge = [re.sub(r"[^\wäöüß]", "", s.split(" ")[0]).lower()
                for s in saetze if s.split()]
    laeufe, aktuell = [], 1
    for i in range(1, len(anfaenge)):
        if anfaenge[i] and anfaenge[i] == anfaenge[i - 1]:
            aktuell += 1
        else:
            if aktuell >= 3:
                laeufe.append((anfaenge[i - 1], aktuell))
            aktuell = 1
    if aktuell >= 3 and anfaenge:
        laeufe.append((anfaenge[-1], aktuell))
    for wort, n in laeufe[:3]:
        b.befunde.append(Befund(
            "gleicher Satzanfang", "notieren",
            f"{n} Sätze in Folge beginnen mit „{wort}“."))

    return b


def ausgeben(b: Bericht) -> str:
    z = []
    z.append(f"\n── {b.datei}  [{b.profil}]")
    if not b.saetze:
        z.append("   (kein auswertbarer Fließtext)")
        return "\n".join(z)
    z.append(f"   {b.woerter} Wörter · {b.saetze} Sätze · "
             f"Ø {b.satz_mittel} (Median {b.satz_median}, Streuung {b.satz_streuung})")
    z.append(f"   kurz ≤8 W: {b.anteil_kurz:.0%} · lang ≥30 W: {b.anteil_lang:.0%} · "
             f"Absätze Ø {b.absatz_mittel} (Streuung {b.absatz_streuung})")
    z.append(f"   Füller {b.fueller_pro_1k}/1k · Aufblähung {b.aufblaehung_pro_1k}/1k · "
             f"Gedankenstriche {b.gedankenstrich_pro_1k}/1k")

    hinsehen = [f for f in b.befunde if f.schwere == "hinsehen"]
    notieren = [f for f in b.befunde if f.schwere == "notieren"]
    if hinsehen:
        z.append("   Hinsehen:")
        z.extend(f.zeile() for f in hinsehen)
    if notieren:
        z.append("   Notiert:")
        z.extend(f.zeile() for f in notieren)
    if not b.befunde:
        z.append("   Keine Auffälligkeit in den gemessenen Merkmalen.")
    return "\n".join(z)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Misst Oberflächenmerkmale maschinell wirkender Sprache.")
    p.add_argument("dateien", nargs="+", help="Dateien oder - für stdin")
    p.add_argument("--profil", choices=list(REFERENZ) + ["auto"], default="auto",
                   help="Vergleichsmassstab; auto raet nach Sprache")
    p.add_argument("--json", action="store_true", help="Maschinenlesbare Ausgabe")
    a = p.parse_args()

    berichte = []
    for name in a.dateien:
        if name == "-":
            berichte.append(analysiere(sys.stdin.read(), "<stdin>", a.profil))
            continue
        pfad = Path(name)
        if not pfad.is_file():
            print(f"nicht gefunden: {name}", file=sys.stderr)
            continue
        berichte.append(analysiere(pfad.read_text(encoding="utf-8", errors="replace"),
                                   pfad.name, a.profil))

    if not berichte:
        return 1

    if a.json:
        print(json.dumps([asdict(b) for b in berichte], ensure_ascii=False, indent=2,
                         default=lambda o: o.__dict__))
    else:
        for b in berichte:
            print(ausgeben(b))
        print("\nDie Werte sind Hinweise, keine Vorgaben. Ein verständlicher "
              "Absatz\nwird nicht umgebaut, weil eine Zahl ausschlägt.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
