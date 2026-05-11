param(
    [switch]$SkipPathlibCheck,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

if (-not $SkipPathlibCheck) {
    $pathlibInfo = $null
    try {
        $pathlibInfo = & $Python -m pip show pathlib 2>$null
    } catch {
        $pathlibInfo = $null
    }
    if ($LASTEXITCODE -eq 0 -and $pathlibInfo) {
        Write-Warning "The obsolete pathlib backport is installed in this Python environment."
        Write-Warning "PyInstaller refuses to run with that package installed."
        Write-Warning "Fix with: python -m pip uninstall pathlib"
        throw "Remove pathlib or rerun with -SkipPathlibCheck after fixing the environment."
    }
}

$baseArgs = @(
    "--noconfirm",
    "--clean",
    "--onefile",
    "--distpath", "dist",
    "--workpath", "build",
    "--specpath", "build\spec",
    "--paths", ".",
    "--paths", "gaps"
)

$gapsSolverImports = @(
    "--hidden-import", "gaps.crossover",
    "--hidden-import", "gaps.fitness",
    "--hidden-import", "gaps.genetic_algorithm",
    "--hidden-import", "gaps.image_analysis",
    "--hidden-import", "gaps.individual",
    "--hidden-import", "gaps.piece",
    "--hidden-import", "gaps.progress_bar",
    "--hidden-import", "gaps.selection",
    "--hidden-import", "gaps.utils"
)

$cliArgs = @(
    @($baseArgs) +
    @($gapsSolverImports) +
    @(
        "--exclude-module", "PyQt5",
        "--exclude-module", "matplotlib",
        "--exclude-module", "tkinter",
        "--name", "gaps_stitch_cli",
        "run_gaps_stitch.py"
    )
)

$guiArgs = @(
    @($baseArgs) +
    @($gapsSolverImports) +
    @(
        "--windowed",
        "--name", "gaps_stitch_gui",
        "gui_stitch.py"
    )
)

function Invoke-PyInstaller {
    param(
        [string]$Target,
        [string[]]$PyInstallerArgs
    )

    & $Python -m PyInstaller @PyInstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed for $Target with exit code $LASTEXITCODE"
    }
}

Invoke-PyInstaller -Target "CLI" -PyInstallerArgs $cliArgs
Invoke-PyInstaller -Target "GUI" -PyInstallerArgs $guiArgs

Write-Host ""
Write-Host "Built executables:"
Write-Host "  dist\gaps_stitch_cli.exe"
Write-Host "  dist\gaps_stitch_gui.exe"
