param(
    [Parameter(Mandatory = $true)]
    [string]$WheelPath,
    [string]$UvExecutable
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$resolvedWheel = (Resolve-Path $WheelPath).Path
if (-not $UvExecutable) {
    $uvCommand = Get-Command "uv" -ErrorAction SilentlyContinue
    if ($null -eq $uvCommand) {
        throw "uv was not found on PATH."
    }
    $UvExecutable = $uvCommand.Source
}

$smokeRoot = Join-Path $projectRoot (
    ".test-tmp-wheel-smoke-" + [Guid]::NewGuid().ToString("N")
)
$venvDir = Join-Path $smokeRoot "venv"
$workspaceDir = Join-Path $smokeRoot "workspace"
$libraryWorkspaceDir = Join-Path $smokeRoot "library-workspace"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"
$autobladeExe = Join-Path $venvDir "Scripts\autoblade.exe"
$createExe = Join-Path $venvDir "Scripts\autoblade-create.exe"
$batchExe = Join-Path $venvDir "Scripts\autoblade-batch.exe"
$previousPythonPath = $env:PYTHONPATH

function Invoke-SmokeStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host "==> $Name"
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

try {
    $env:PYTHONPATH = ""
    New-Item -ItemType Directory -Path $smokeRoot | Out-Null
    Invoke-SmokeStep -Name "Create clean Python 3.14 environment" -Action {
        & $UvExecutable venv $venvDir --python 3.14
    }
    Invoke-SmokeStep -Name "Install wheel without editable source" -Action {
        & $UvExecutable pip install --python $pythonExe $resolvedWheel
    }

    Invoke-SmokeStep -Name "Check autoblade help" -Action {
        & $autobladeExe --help
    }
    Invoke-SmokeStep -Name "Check autoblade version" -Action {
        & $autobladeExe --version
    }
    foreach ($entrypoint in @($createExe, $batchExe)) {
        Invoke-SmokeStep -Name "Check $entrypoint help" -Action {
            & $entrypoint --help
        }
        Invoke-SmokeStep -Name "Check $entrypoint version" -Action {
            & $entrypoint --version
        }
    }

    Invoke-SmokeStep -Name "Initialize external workspace" -Action {
        & $autobladeExe init $workspaceDir --with-examples
    }
    Invoke-SmokeStep -Name "Initialize audited airfoil library workspace" -Action {
        & $autobladeExe init $libraryWorkspaceDir --with-airfoil-library
    }
    $workspaceConfig = Join-Path $workspaceDir "config.toml"
    Invoke-SmokeStep -Name "Discover initialized inputs" -Action {
        & $autobladeExe --config $workspaceConfig list
    }
    Invoke-SmokeStep -Name "Read initialized configuration" -Action {
        & $autobladeExe --config $workspaceConfig config show
    }
    Invoke-SmokeStep -Name "Run installed input preflight and mock build" -Action {
        & $pythonExe (Join-Path $PSScriptRoot "installed_wheel_smoke.py") `
            --workspace $workspaceDir `
            --library-workspace $libraryWorkspaceDir `
            --repository-root $projectRoot
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
        ) -and $leaf.StartsWith(".test-tmp-wheel-smoke-") -and
        (Test-Path -LiteralPath $resolvedRoot)
    ) {
        [System.IO.Directory]::Delete($resolvedRoot, $true)
    }
}
