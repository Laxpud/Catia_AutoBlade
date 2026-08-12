param(
    [switch]$SkipSync,
    [switch]$SkipInstalledSmoke,
    [switch]$RequireTag,
    [string]$CacheDir
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$testTemp = Join-Path $projectRoot ".test-tmp-check-$PID"
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
    # 桌面沙箱会把工具运行时放在项目级 .uv，而常规开发环境可能把 uv
    # 安装进 .venv；两者都必须解析为明确文件，不能依赖当前工作目录。
    $localUv = @(
        (Join-Path $projectRoot ".uv\bin\uv.exe"),
        (Join-Path $projectRoot ".venv\Scripts\uv.exe")
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $localUv) {
        throw "uv was not found on PATH or in the project .uv/.venv runtimes."
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

    # 2. pytest 临时数据固定在项目可写目录，并按检查进程隔离。受管 Windows
    # 环境可能给子进程创建的目录附加专用 ACL，复用固定目录会导致下次清理失败。
    Invoke-UvStep -Name "Run automated tests" -Arguments @(
        "run", "--frozen", "--extra", "dev", "pytest", "-q",
        "--basetemp=$testTemp", "-p", "no:cacheprovider"
    )
    Invoke-UvStep -Name "Run Ruff" -Arguments @(
        "run", "--frozen", "--extra", "dev", "ruff", "check",
        "src", "tests", "scripts"
    )

    # 3. 构建后从实际 wheel/sdist 读取 METADATA，而不是只检查 pyproject 文本。
    Invoke-UvStep -Name "Build wheel and sdist" -Arguments @("build", "--clear")
    if (-not $SkipInstalledSmoke) {
        $sourceVersion = (& $uvExecutable run --frozen python -c `
            "from catia_autoblade import __version__; print(__version__)"
        ).Trim()
        if ($LASTEXITCODE -ne 0) {
            throw "Read source version failed with exit code $LASTEXITCODE."
        }
        $wheel = @(
            Get-ChildItem -Path (Join-Path $projectRoot "dist") `
                -Filter "catia_autoblade-$sourceVersion-*.whl"
        )
        if ($wheel.Count -ne 1) {
            throw "Expected exactly one wheel for installed smoke testing."
        }
        Write-Host "==> Run non-editable installed wheel smoke test"
        & (Join-Path $PSScriptRoot "smoke_installed_wheel.ps1") `
            -WheelPath $wheel[0].FullName -UvExecutable $uvExecutable
        if ($LASTEXITCODE -ne 0) {
            throw "Installed wheel smoke test failed with exit code $LASTEXITCODE."
        }
    }
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
