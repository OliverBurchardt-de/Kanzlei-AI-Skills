$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Projekte\Kanzlei-AI-Skills\.tmp\bk-additional-skills-install-20261004-ae6b3a82'
$firstTaskRoot = 'C:\Projekte\Kanzlei-AI-Skills\.tmp\bk-monatsbuchhaltung-install-20261004-963e9b20'
$skillsRoot = 'C:\Users\OBurchardt\.codex\skills'
$approvedNames = @('bk-monatsbuchhaltung', 'bk-schaubilder', 'bk-monatsreview', 'bk-jahresabschluss-vorbereitung', 'bk-gesellschafterbeschluss')
$plans = @((Get-Content -LiteralPath (Join-Path $firstTaskRoot 'installation-plan.json') -Raw | ConvertFrom-Json))
$plans += @(Get-Content -LiteralPath (Join-Path $taskRoot 'installation-plans.json') -Raw | ConvertFrom-Json)
$env:PYTHONPATH = Join-Path $taskRoot 'validation-deps'
$validator = 'C:\Users\OBurchardt\.codex\skills\.system\skill-creator\scripts\quick_validate.py'

# Validate trusted plans and exact archive bytes before modifying installations.
foreach ($plan in $plans) {
    $skillName = Split-Path -Leaf $plan.destination
    if ($skillName -notin $approvedNames) { throw 'Skill is outside the approved list.' }
    $expectedDestination = [IO.Path]::GetFullPath((Join-Path $skillsRoot $skillName))
    $expectedStage = if ($skillName -eq 'bk-monatsbuchhaltung') { Join-Path $firstTaskRoot $skillName } else { Join-Path $taskRoot $skillName }
    if ([IO.Path]::GetFullPath($plan.destination) -ne $expectedDestination -or [IO.Path]::GetFullPath($plan.stage) -ne $expectedStage) {
        throw 'Unexpected installation or staging path.'
    }
    if ((Get-FileHash -LiteralPath $plan.zip -Algorithm SHA256).Hash -ne $plan.zip_sha256) { throw 'Archive changed after staging.' }
    if ((Get-Item -LiteralPath $plan.stage -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Staging path is a link.' }
    $actualFiles = @(Get-ChildItem -LiteralPath $plan.stage -File -Recurse -Force)
    if ($actualFiles.Count -ne $plan.file_count) { throw 'Staged file count differs from archive.' }
    foreach ($file in $plan.files) {
        $filePath = [IO.Path]::GetFullPath((Join-Path $plan.stage $file.path))
        if (-not $filePath.StartsWith($expectedStage + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'File path escapes staging.' }
        if ((Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash -ne $file.sha256) { throw 'Staged file differs from archive.' }
    }
    python -B -X utf8 $validator $plan.stage
    if ($LASTEXITCODE -ne 0) { throw ('Skill validation failed: ' + $skillName) }
}

$metadataCheck = @'
import json, pathlib, yaml
plans = [json.loads(pathlib.Path(r"C:\Projekte\Kanzlei-AI-Skills\.tmp\bk-monatsbuchhaltung-install-20261004-963e9b20\installation-plan.json").read_text(encoding="utf-8-sig")), *json.loads(pathlib.Path(r"C:\Projekte\Kanzlei-AI-Skills\.tmp\bk-additional-skills-install-20261004-ae6b3a82\installation-plans.json").read_text(encoding="utf-8-sig"))]
for plan in plans:
    root = pathlib.Path(plan["stage"])
    front = yaml.safe_load(root.joinpath("SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
    assert front["name"] == root.name
    ui = root / "agents" / "openai.yaml"
    if ui.exists():
        config = yaml.safe_load(ui.read_text(encoding="utf-8"))
        assert isinstance(config, dict)
        for key in ("icon_small", "icon_large"):
            icon = config.get("interface", {}).get(key)
            if icon:
                assert root.joinpath(icon).is_file(), icon
    print(json.dumps({"skill": root.name, "metadata_valid": True}, ensure_ascii=False))
'@
python -B -X utf8 -c $metadataCheck
if ($LASTEXITCODE -ne 0) { throw 'Metadata validation failed.' }

$results = @()
foreach ($plan in $plans) {
    $skillName = Split-Path -Leaf $plan.destination
    $backupRoot = if ($skillName -eq 'bk-monatsbuchhaltung') { $firstTaskRoot } else { $taskRoot }
    $backupPath = [IO.Path]::GetFullPath((Join-Path $backupRoot ('previous-installation-' + $skillName)))
    $stagePath = [IO.Path]::GetFullPath($plan.stage)
    $destinationPath = [IO.Path]::GetFullPath((Join-Path $skillsRoot $skillName))
    if ($stagePath -ne $plan.stage -or $destinationPath -ne $plan.destination -or -not $backupPath.StartsWith($backupRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Move targets are outside the approved directories.'
    }
    if (Test-Path -LiteralPath $backupPath) { throw 'Backup path already exists.' }
    $hadPrevious = Test-Path -LiteralPath $destinationPath
    if ($hadPrevious) {
        if ((Get-Item -LiteralPath $destinationPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Installation path is a link.' }
        Move-Item -LiteralPath $destinationPath -Destination $backupPath
    }
    try {
        Move-Item -LiteralPath $stagePath -Destination $destinationPath
    } catch {
        if ($hadPrevious -and -not (Test-Path -LiteralPath $destinationPath)) {
            Move-Item -LiteralPath $backupPath -Destination $destinationPath
        }
        throw
    }
    $actualFiles = @(Get-ChildItem -LiteralPath $destinationPath -File -Recurse -Force)
    if ($actualFiles.Count -ne $plan.file_count) { throw 'Installed file count differs from archive.' }
    foreach ($file in $plan.files) {
        $installedFile = Join-Path $destinationPath $file.path
        if ((Get-FileHash -LiteralPath $installedFile -Algorithm SHA256).Hash -ne $file.sha256) { throw 'Installed file differs from archive.' }
    }
    $result = [ordered]@{skill=$skillName; installed=$destinationPath; files=$actualFiles.Count; matches_zip=$true; backup=$(if ($hadPrevious) { $backupPath } else { $null })}
    $results += $result
    $results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $taskRoot 'installation-results.json') -Encoding utf8
    $result | ConvertTo-Json -Compress
}
