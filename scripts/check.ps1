param(
    [switch]$SkipSync,
    [switch]$RequireTag,
    [string]$CacheDir
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$testTemp = Join-Path $projectRoot ".test-tmp-check"
if ($CacheDir) {
    $env:UV_CACHE_DIR = [System.IO.Path]::GetFullPath(
        (Join-Path $projectRoot $CacheDir)
    )
}
$uvCommand = Get-Command "uv" -ErrorAction SilentlyContinue
if ($null -ne $uvCommand) {
    $uvExecutable = $uvCommand.Source
}
else {
    $localUv = Join-Path $projectRoot ".venv\Scripts\uv.exe"
    if (-not (Test-Path $localUv)) {
        throw "uv was not found on PATH or in the project .venv."
    }
    $uvExecutable = $localUv
}

function Invoke-UvStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Host "==> $Name"
    & $uvExecutable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

Push-Location $projectRoot
try {
    # 文件使用 UTF-8 BOM，兼容 Windows PowerShell 5.1 对中文注释的解析。
    # 1. 锁文件必须能在已声明的 Python 3.14/Windows 环境中原样安装。
    if (-not $SkipSync) {
        Invoke-UvStep -Name "Sync locked development environment" -Arguments @(
            "sync", "--frozen", "--extra", "dev"
        )
    }

    # 2. pytest 临时数据固定在项目可写目录，避免受系统临时目录权限影响。
    Invoke-UvStep -Name "Run automated tests" -Arguments @(
        "run", "--frozen", "--extra", "dev", "pytest", "-q",
        "--basetemp=$testTemp", "-p", "no:cacheprovider"
    )
    Invoke-UvStep -Name "Run Ruff" -Arguments @(
        "run", "--frozen", "--extra", "dev", "ruff", "check",
        "src", "tests", "scripts"
    )

    # 3. 构建后从实际 wheel/sdist 读取 METADATA，而不是只检查 pyproject 文本。
    Invoke-UvStep -Name "Build wheel and sdist" -Arguments @("build")
    $metadataArguments = @(
        "run", "--frozen", "python", "scripts/validate_distribution.py"
    )
    if ($RequireTag -or $env:GITHUB_REF_TYPE -eq "tag") {
        $metadataArguments += "--require-tag"
    }
    Invoke-UvStep -Name "Validate distribution metadata" -Arguments $metadataArguments
}
finally {
    Pop-Location
}
