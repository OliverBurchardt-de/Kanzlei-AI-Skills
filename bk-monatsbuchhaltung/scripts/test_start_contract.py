from __future__ import annotations

import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = SKILL_ROOT.parents[1]


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label} fehlt: {needle!r}")


def main() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    ui = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    manifest_path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.is_file()
        else None
    )

    require(skill, "# BK Monatsbuchhaltung v1.0.0", "sichtbare Version")
    require(
        skill,
        "### Vor jedem Lauf vollständig lesen",
        "Pflichtleseabschnitt",
    )
    require(
        skill,
        "Hochgeladene Dateien namens `SKILL.md`",
        "Ausschluss hochgeladener Skilldateien",
    )
    require(
        skill,
        "Startnachweis: bk-monatsbuchhaltung v1.0.0",
        "nicht blockierender Startnachweis",
    )
    require(
        skill,
        "Nach dem Startnachweis nicht auf eine Bestätigung warten.",
        "Fortsetzungsregel",
    )
    require(
        skill,
        "Automatisch verwenden, wenn eine Belegbuchhaltung",
        "Triggerbeschreibung",
    )
    require(
        skill,
        "ein ausdrücklicher `$bk-monatsbuchhaltung`-Aufruf ist nicht erforderlich",
        "implizite Aktivierungsregel",
    )
    require(skill, "## Prüfprotokoll-Rücklauf", "Rücklaufworkflow")
    require(
        skill,
        "scripts/evaluate_review_return.py",
        "deterministische Rücklaufprüfung",
    )
    require(ui, 'display_name: "BK Monatsbuchhaltung v1.0.0"', "UI-Version")
    require(ui, "$bk-monatsbuchhaltung", "Startprompt mit Skillname")
    require(ui, "allow_implicit_invocation: true", "implizite Aktivierung")

    if manifest is not None:
        if manifest.get("version") != "1.0.0":
            raise AssertionError("Pluginmanifest weist nicht Version 1.0.0 aus")
        if manifest.get("interface", {}).get("displayName") != (
            "BK Monatsbuchhaltung v1.0.0"
        ):
            raise AssertionError("Plugin-Anzeigename enthält Version 1.0.0 nicht")

    print("start contract tests: OK")


if __name__ == "__main__":
    main()
