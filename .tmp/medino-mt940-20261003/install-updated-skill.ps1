$ErrorActionPreference = 'Stop'
$workspaceSkillPath = [IO.Path]::GetFullPath('C:\Projekte\Kanzlei-AI-Skills\mt940-dateien-erstellen')
$installedSkillPath = [IO.Path]::GetFullPath('C:\Users\OBurchardt\.codex\skills\mt940-dateien-erstellen')
$relativeFiles = @(
    'SKILL.md',
    'agents\openai.yaml',
    'references\bankreferenzmodelle.md',
    'references\technischer-aufbau.md',
    'profiles\unverified-example.json',
    'profiles\dortmunder-volksbank-onlinebanking-business-pdf-2026.json',
    'profiles\dortmunder-volksbank-onlinebanking-business-pdf-2026.py',
    'scripts\build-mt940.py',
    'scripts\mt940_common.py',
    'scripts\source_check.py',
    'scripts\validate-mt940.py',
    'scripts\reconstruction.py',
    'scripts\learn-bank-profile.py',
    'tests\test_learning.py'
)
foreach ($relativeFile in $relativeFiles) {
    $sourceFile = [IO.Path]::GetFullPath((Join-Path $workspaceSkillPath $relativeFile))
    $targetFile = [IO.Path]::GetFullPath((Join-Path $installedSkillPath $relativeFile))
    if (-not $sourceFile.StartsWith($workspaceSkillPath + '\', [StringComparison]::OrdinalIgnoreCase) -or -not $targetFile.StartsWith($installedSkillPath + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Resolved skill path escaped its intended directory.'
    }
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) { throw "Missing source file: $relativeFile" }
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($targetFile)) -Force | Out-Null
    Copy-Item -LiteralPath $sourceFile -Destination $targetFile -Force
    if ((Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $targetFile -Algorithm SHA256).Hash) {
        throw "Installed file differs: $relativeFile"
    }
}
Write-Output "Installed and hash-verified $($relativeFiles.Count) skill files."
