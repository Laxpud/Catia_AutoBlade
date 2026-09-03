param(
    [string]$WheelPath,
    [string]$UvExecutable,
    [string]$CatiaVersion = "CATIA P3 V5-6R2020"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $UvExecutable) {
    $uvCommand = Get-Command "uv" -ErrorAction SilentlyContinue
    if ($null -eq $uvCommand) {
        throw "uv was not found on PATH."
    }
    $UvExecutable = $uvCommand.Source
}

Write-Host "==> Validate repository and installed wheel before real CATIA"
& (Join-Path $PSScriptRoot "check.ps1") -SkipSync
if ($LASTEXITCODE -ne 0) {
    throw "Repository checks failed before real CATIA smoke testing."
}

$sourceVersion = (& $UvExecutable run --frozen python -c `
    "from autoblade import __version__; print(__version__)"
).Trim()
if (-not $WheelPath) {
    $wheelCandidates = @(
        Get-ChildItem -Path (Join-Path $projectRoot "dist") `
            -Filter "autoblade-$sourceVersion-*.whl"
    )
    if ($wheelCandidates.Count -ne 1) {
        throw "Expected exactly one candidate wheel for $sourceVersion."
    }
    $WheelPath = $wheelCandidates[0].FullName
}
$resolvedWheel = (Resolve-Path $WheelPath).Path

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$smokeRoot = Join-Path $projectRoot (
    ".test-tmp-real-catia-" + [Guid]::NewGuid().ToString("N")
)
$artifactRoot = Join-Path $projectRoot "output\real-catia-smoke-$stamp"
$workspaceDir = Join-Path $smokeRoot "workspace"
$venvDir = Join-Path $smokeRoot "venv"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"
$autobladeExe = Join-Path $venvDir "Scripts\autoblade.exe"
$previousPythonPath = $env:PYTHONPATH

function Get-CnextIds {
    return @(
        Get-Process -Name "CNEXT" -ErrorAction SilentlyContinue |
            ForEach-Object { $_.Id }
    )
}

try {
    $env:PYTHONPATH = ""
    New-Item -ItemType Directory -Path $smokeRoot | Out-Null
    New-Item -ItemType Directory -Path $artifactRoot | Out-Null
    & $UvExecutable venv $venvDir --python 3.14
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to create the real CATIA smoke environment."
    }
    & $UvExecutable pip install --python $pythonExe $resolvedWheel
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to install the candidate wheel."
    }
    & $autobladeExe init $workspaceDir
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to initialize the CATIA smoke workspace."
    }

    $airfoilDir = Join-Path $workspaceDir "input\airfoils"
    $sectionDir = Join-Path $workspaceDir "input\blade_sections"
    foreach ($name in @(
        "airfoil1_sharp.csv",
        "airfoil2_sharp.csv",
        "airfoil3_sharp.csv"
    )) {
        Copy-Item -LiteralPath (Join-Path $projectRoot "input\airfoils\$name") `
            -Destination (Join-Path $airfoilDir $name)
    }
    Copy-Item -LiteralPath (
        Join-Path $projectRoot `
            "input\blade_sections\blade_sections-multi-airfoil.csv"
    ) -Destination $sectionDir

    $beforeIds = Get-CnextIds
    $workspaceConfig = Join-Path $workspaceDir "config.toml"
    & $autobladeExe --config $workspaceConfig create `
        --section "blade_sections-multi-airfoil.csv" --output $artifactRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Candidate wheel failed the real CATIA build."
    }

    $catpart = Join-Path $artifactRoot "blade-multi-airfoil.CATPart"
    $step = Join-Path $artifactRoot "blade-multi-airfoil.stp"
    foreach ($artifact in @($catpart, $step)) {
        if (-not (Test-Path -LiteralPath $artifact)) {
            throw "Expected CATIA artifact not found: $artifact"
        }
        if ((Get-Item -LiteralPath $artifact).Length -le 0) {
            throw "CATIA artifact is empty: $artifact"
        }
    }
    $stepContent = [System.IO.File]::ReadAllText($step)
    if ($stepContent -notmatch "MANIFOLD_SOLID_BREP|BREP_WITH_VOIDS") {
        throw "STEP output does not contain a closed solid BREP entity."
    }
    & $pythonExe (Join-Path $PSScriptRoot "inspect_catia_artifact.py") $catpart
    if ($LASTEXITCODE -ne 0) {
        throw "CATPart feature-tree inspection failed."
    }

    Start-Sleep -Seconds 3
    $afterIds = Get-CnextIds
    $newIds = @($afterIds | Where-Object { $_ -notin $beforeIds })
    if ($newIds.Count -ne 0) {
        throw "Real CATIA smoke left new CNEXT processes: $newIds"
    }

    $commit = (git -C $projectRoot rev-parse HEAD).Trim()
    $dirty = [bool](git -C $projectRoot status --porcelain)
    $record = [ordered]@{
        version = $sourceVersion
        commit = $commit
        dirty_worktree = $dirty
        repository_check = "pass"
        installed_wheel_smoke = "pass"
        catia_smoke = [ordered]@{
            date = (Get-Date -Format "yyyy-MM-dd")
            windows = "Windows 11 x64"
            python = (& $pythonExe --version).Trim()
            pywin32 = "311"
            catia = $CatiaVersion
            input_model = "blade_sections-multi-airfoil.csv"
            catpart_result = "pass: $catpart"
            step_result = "pass: closed solid BREP at $step"
            feature_tree = (
                "pass: blade_loft_surface, blade_closed_solid, " +
                "leading_edge_guide, trailing_edge_upper_guide"
            )
            new_cnext_processes = 0
        }
    }
    $recordPath = Join-Path $artifactRoot "validation.json"
    $record | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 $recordPath
    Write-Host "Real CATIA candidate-wheel smoke: PASS"
    Write-Host "Artifacts: $artifactRoot"
    Write-Host "Validation record: $recordPath"
    if ($dirty) {
        Write-Warning (
            "The worktree is dirty; rerun this smoke test from the final tagged " +
            "commit before preparing an internal release."
        )
    }
}
finally {
    $env:PYTHONPATH = $previousPythonPath
    $resolvedRoot = [System.IO.Path]::GetFullPath($smokeRoot)
    $expectedPrefix = [System.IO.Path]::GetFullPath($projectRoot) + `
        [System.IO.Path]::DirectorySeparatorChar
    $leaf = [System.IO.Path]::GetFileName($resolvedRoot)
    if (
        $resolvedRoot.StartsWith(
            $expectedPrefix,
            [System.StringComparison]::OrdinalIgnoreCase
        ) -and $leaf.StartsWith(".test-tmp-real-catia-") -and
        (Test-Path -LiteralPath $resolvedRoot)
    ) {
        [System.IO.Directory]::Delete($resolvedRoot, $true)
    }
}
