from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.5.0"
# Paketvertrag der Skripte (build_package.py, validate_package.py); v1.5.0 ergänzt nur SKILL.md Abschnitt 5.
CONTRACT_VERSION = "1.4.1"
FORBIDDEN_TARGET_VERSION = "1.5.1"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label} fehlt: {needle!r}")


def parse_simple_yaml(path: Path) -> dict:
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        list_match = re.match(r"^(\s*)-\s+(.*)$", raw)
        if list_match:
            indent = len(list_match.group(1))
            while stack[-1][0] >= indent:
                stack.pop()
            if not stack[-1][1] and len(stack) > 1:
                stack.pop()
            parent = stack[-1][1]
            if not parent:
                raise AssertionError(f"Listeneintrag ohne Schlüssel in {path.name}: {raw!r}")
            last_key = next(reversed(parent))
            if not isinstance(parent[last_key], list):
                parent[last_key] = []
            parent[last_key].append(list_match.group(2).strip())
            continue
        match = re.match(r"^(\s*)([^:#]+):(?:\s*(.*))?$", raw)
        if not match:
            raise AssertionError(f"Ungültige YAML-Zeile in {path.name}: {raw!r}")
        indent = len(match.group(1))
        key = match.group(2).strip()
        value = (match.group(3) or "").strip()
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if not value:
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if value.casefold() in {"true", "false"}:
            parsed: object = value.casefold() == "true"
        else:
            parsed = value
        parent[key] = parsed
    return root


def require_python_version(path: Path, constant: str) -> None:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(constant)}\s*=\s*[\"']([^\"']+)[\"']", text, re.MULTILINE)
    if not match or match.group(1) != CONTRACT_VERSION:
        actual = match.group(1) if match else "nicht gefunden"
        raise AssertionError(f"{path.name}: {constant}={actual}, erwartet Paketvertrag {CONTRACT_VERSION}")


def test_structural_yaml_and_version_mismatch() -> None:
    with tempfile.TemporaryDirectory(prefix="bk_start_contract_") as temp_name:
        temp = Path(temp_name)
        quoted = temp / "quoted.yaml"
        unquoted = temp / "unquoted.yaml"
        quoted.write_text(f'interface:\n  display_name: "BK Monatsbuchhaltung v{VERSION}"\n', encoding="utf-8")
        unquoted.write_text(f'interface:\n  display_name: BK Monatsbuchhaltung v{VERSION}\n', encoding="utf-8")
        assert parse_simple_yaml(quoted) == parse_simple_yaml(unquoted)
        mismatch = temp / "mismatch.py"
        mismatch.write_text('SKILL_VERSION = "9.9.9"\n', encoding="utf-8")
        try:
            require_python_version(mismatch, "SKILL_VERSION")
        except AssertionError:
            pass
        else:
            raise AssertionError("Eine echte Versionsabweichung wurde nicht erkannt")

def main() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    ui = parse_simple_yaml(SKILL_ROOT / "agents" / "openai.yaml")

    require(skill, f"# BK Monatsbuchhaltung v{VERSION}", "sichtbare Version")
    require(skill, "### Vor jedem Lauf vollständig lesen", "Pflichtleseabschnitt")
    require(skill, "Hochgeladene Dateien namens `SKILL.md`", "Ausschluss hochgeladener Skilldateien")
    require(skill, f"Startnachweis: bk-monatsbuchhaltung v{VERSION} (Paketvertrag {CONTRACT_VERSION})", "nicht blockierender Startnachweis")
    require(skill, "Nach dem Startnachweis nicht auf eine Bestätigung warten.", "Fortsetzungsregel")
    require(skill, "Automatisch verwenden, wenn eine Belegbuchhaltung", "Triggerbeschreibung")
    require(skill, "ein ausdrücklicher `$bk-monatsbuchhaltung`-Aufruf ist nicht erforderlich", "implizite Aktivierungsregel")
    require(skill, "## Prüfprotokoll-Rücklauf", "Rücklaufworkflow")
    require(skill, "scripts/evaluate_review_return.py", "deterministische Rücklaufprüfung")
    require(skill, "references/PARALLELVERARBEITUNG.md", "Parallelmodus-Referenz")
    require(skill, "scripts/merge_parallel_results.py", "globale Parallelkonsolidierung")
    require(skill, "eine unabhängige Kontrolle, nicht Laufzeit oder eine feste Agentenzahl", "Qualitätsziel Mehragentenmodus")
    require(skill, "doppelte GUIDs technisch abweisen", "GUID-Integritätskontrolle")
    require(skill, "niemals Kassenbuchungen", "Ausschluss Kassenbuchung")
    require(skill, "getrennte Stapel Buchungsstapel/Klärungsposten", "Startnachweis Output-Vertrag v1.4")
    require(skill, "Kostenstellen nach Profil", "Startnachweis Kostenstellen")
    require(skill, "EXTF_Klaerungsposten_<JJJJ-MM>.csv", "Klärungsstapel-Dateiname")
    require(skill, "unkonfigurierter Pflichtkostenstelle", "verbleibender Kostenstellen-Stopp")
    require(skill, "Riecken-DATEV-Connector", "DATEV-Anbindung über Riecken")
    require(skill, "`datev_health_check`", "Riecken-Erreichbarkeitsprüfung")
    # v1.4.1: Durchführungspflicht, Abschluss-Gate, Klärungsquote, Belegdateiregel.
    require(skill, "Auftrag zur vollständigen Abarbeitung", "Durchführungspflicht")
    require(skill, "kein freiwilliger Abbruch", "Verbot des vorzeitigen Abbruchs")
    require(skill, "Abschluss-Gate", "Abschluss-Gate")
    require(skill, "nicht vollständig abgeschlossen", "Kennzeichnung unvollständiger Läufe")
    require(skill, "Klärungsquote", "Klärungsquote")
    require(skill, "scripts/clarification_rate.py", "Klärungsquotenprüfung")
    require(skill, "ein Buchungsbeleg = genau eine eigene PDF-Datei", "Belegdateiregel")
    require(skill, "scripts/beleg_pdf.py", "PDF-Werkzeug")
    require(skill, "Beide Stapel werden übertragen", "Übertragung des Klärungsstapels")
    require(skill, "Niemals melden oder ausweisen, Klärungsposten würden nicht übertragen", "Verbot der Falschmeldung")
    # v1.5.0: Übertragung über den Riecken-Connector nur auf ausdrücklichen Auftrag, Klärungskonto.
    require(skill, "### 5. Übertragung über den Riecken-Connector (nur auf ausdrücklichen Auftrag)", "Abschnitt 5 Riecken-Übertragung")
    require(skill, "Riecken-Übertragung nur auf ausdrücklichen Auftrag mit Klärungskonto", "Startnachweis Riecken-Übertragung")
    require(skill, f"Paketvertrag der Skripte (`build_package.py`, `validate_package.py`) bleibt Version `{CONTRACT_VERSION}`", "Paketvertrag")
    require(skill, "159900 Klärungskonto Buchhaltung", "Kanzleistandard Klärungskonto")
    for path in (SKILL_ROOT / "SKILL.md", SKILL_ROOT / "agents" / "openai.yaml"):
        if FORBIDDEN_TARGET_VERSION in path.read_text(encoding="utf-8"):
            raise AssertionError(f"{path.name} verweist auf die unzulässige Zielversion {FORBIDDEN_TARGET_VERSION}")

    interface = ui.get("interface", {})
    policy = ui.get("policy", {})
    if interface.get("display_name") != f"BK Monatsbuchhaltung v{VERSION}":
        raise AssertionError("UI-Anzeigename oder UI-Version weicht ab")
    if "$bk-monatsbuchhaltung" not in str(interface.get("default_prompt", "")):
        raise AssertionError("Startprompt enthält den Skillnamen nicht")
    if policy.get("allow_implicit_invocation") is not True:
        raise AssertionError("Implizite Aktivierung ist nicht eingeschaltet")

    require_python_version(SKILL_ROOT / "scripts" / "build_package.py", "SKILL_VERSION")
    require_python_version(SKILL_ROOT / "scripts" / "validate_package.py", "EXPECTED_SKILL_VERSION")

    manifest = None
    for root in (SKILL_ROOT.parent, SKILL_ROOT.parents[1]):
        path = root / ".codex-plugin" / "plugin.json"
        if path.is_file():
            manifest = json.loads(path.read_text(encoding="utf-8"))
            break
    if manifest is not None:
        if manifest.get("version") not in {VERSION, CONTRACT_VERSION}:
            raise AssertionError(f"Pluginmanifest weist weder Version {VERSION} noch Paketvertrag {CONTRACT_VERSION} aus")
        if manifest.get("interface", {}).get("displayName") != f"BK Monatsbuchhaltung v{VERSION}":
            raise AssertionError(f"Plugin-Anzeigename enthält Version {VERSION} nicht")

    print("start contract tests: OK")


if __name__ == "__main__":
    main()
