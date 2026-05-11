---
name: gaps-stitch-cli
description: Use this skill whenever the user asks an AI agent to run, automate, troubleshoot, or write commands for the Gaps/RDP Cache puzzle stitching CLI on Windows or Linux. Always detect the operating system first, then use the matching Windows PowerShell or Linux shell commands. Always verify GAPS_STITCH_CLI, GAPS_STITCH_INPUT_DIR, and GAPS_STITCH_OUTPUT_DIR before running the tool; do not guess missing paths. This skill covers gaps_stitch_cli.exe, Linux-built gaps_stitch_cli binaries, run_gaps_stitch.py, automatic grid detection, rectangular adaptive mode, progress interpretation, output inspection, and environment-variable based operation.
---

# Gaps Stitch CLI Agent Skill

Use this skill to operate the command-line stitching tool safely and repeatably.
The CLI reads `.png`/`.bmp` tiles from a folder, creates a shuffled solver input,
uses the bundled `gaps` solver, automatically adapts rectangular tiles, and
writes the final image to an output folder.

## First Step: Detect OS

Before writing or running any command, identify the target operating system:

- Windows: use PowerShell syntax, Windows paths, and `gaps_stitch_cli.exe`.
- Linux: use POSIX shell syntax, slash paths, and a Linux-built `gaps_stitch_cli`
  binary or `python run_gaps_stitch.py`.

Do not run a Windows `.exe` on Linux unless the user explicitly asks to use
Wine. In normal Linux use, point `GAPS_STITCH_CLI` to a Linux binary or a shell
wrapper script that runs `python run_gaps_stitch.py`. Do not write Linux
`export` commands for Windows PowerShell.

## Required Environment

Before invoking the tool, verify these variables. If any required variable is
missing, stop and ask the user to set it; do not invent paths.

| Variable | Required | Purpose |
| --- | --- | --- |
| `GAPS_STITCH_CLI` | Yes | Full path to the platform-specific CLI command. |
| `GAPS_STITCH_INPUT_DIR` | Yes | Folder containing tile images. |
| `GAPS_STITCH_OUTPUT_DIR` | Yes | Folder where output images should be written. |

Optional variables consumed by the CLI:

| Variable | Default | Purpose |
| --- | --- | --- |
| `GAPS_STITCH_AUTO_GRID` | `1` | `1` enables automatic columns/rows; `0` uses manual grid values. |
| `GAPS_STITCH_COLUMNS` | `28` | Manual grid columns. |
| `GAPS_STITCH_ROWS` | `16` | Manual grid rows. |
| `GAPS_STITCH_SIZE` | `64` | Fallback piece size; real tile dimensions are detected. |
| `GAPS_STITCH_GENERATIONS` | `5` | Genetic algorithm generation count; must be at least `2`. |
| `GAPS_STITCH_POPULATION` | `50` | Genetic algorithm population size. |
| `GAPS_STITCH_SEED` | unset | Optional deterministic shuffle seed. |

## Windows PowerShell

Use this section only on Windows.

Temporary environment variables for the current PowerShell session:

```powershell
$env:GAPS_STITCH_CLI = "E:\puzzle-tool\dist\gaps_stitch_cli.exe"
$env:GAPS_STITCH_INPUT_DIR = "E:\tiles"
$env:GAPS_STITCH_OUTPUT_DIR = "E:\puzzle-tool\output"
$env:GAPS_STITCH_AUTO_GRID = "1"
$env:GAPS_STITCH_GENERATIONS = "5"
$env:GAPS_STITCH_POPULATION = "50"
```

Persistent user environment variables, effective in newly opened terminals:

```powershell
setx GAPS_STITCH_CLI "E:\puzzle-tool\dist\gaps_stitch_cli.exe"
setx GAPS_STITCH_INPUT_DIR "E:\tiles"
setx GAPS_STITCH_OUTPUT_DIR "E:\puzzle-tool\output"
setx GAPS_STITCH_AUTO_GRID "1"
setx GAPS_STITCH_GENERATIONS "5"
setx GAPS_STITCH_POPULATION "50"
```

Windows preflight:

```powershell
$required = "GAPS_STITCH_CLI","GAPS_STITCH_INPUT_DIR","GAPS_STITCH_OUTPUT_DIR"
foreach ($name in $required) {
  if (-not [Environment]::GetEnvironmentVariable($name)) {
    throw "Missing required environment variable: $name"
  }
}
if (-not (Test-Path $env:GAPS_STITCH_CLI)) { throw "CLI not found: $env:GAPS_STITCH_CLI" }
if (-not (Test-Path $env:GAPS_STITCH_INPUT_DIR)) { throw "Input folder not found: $env:GAPS_STITCH_INPUT_DIR" }
New-Item -ItemType Directory -Force -Path $env:GAPS_STITCH_OUTPUT_DIR | Out-Null
```

Windows default run:

```powershell
& $env:GAPS_STITCH_CLI `
  --folder $env:GAPS_STITCH_INPUT_DIR `
  --output-dir $env:GAPS_STITCH_OUTPUT_DIR `
  --auto-grid
```

Windows manual grid run:

```powershell
& $env:GAPS_STITCH_CLI `
  --folder $env:GAPS_STITCH_INPUT_DIR `
  --output-dir $env:GAPS_STITCH_OUTPUT_DIR `
  --manual-grid `
  --columns 25 `
  --rows 20
```

## Linux Shell

Use this section only on Linux.

Temporary environment variables for the current shell:

```bash
export GAPS_STITCH_CLI="/opt/puzzle-tool/dist/gaps_stitch_cli"
export GAPS_STITCH_INPUT_DIR="/data/tiles"
export GAPS_STITCH_OUTPUT_DIR="/data/output"
export GAPS_STITCH_AUTO_GRID="1"
export GAPS_STITCH_GENERATIONS="5"
export GAPS_STITCH_POPULATION="50"
```

Persistent user environment variables:

```bash
cat >> ~/.bashrc <<'EOF'
export GAPS_STITCH_CLI="/opt/puzzle-tool/dist/gaps_stitch_cli"
export GAPS_STITCH_INPUT_DIR="/data/tiles"
export GAPS_STITCH_OUTPUT_DIR="/data/output"
export GAPS_STITCH_AUTO_GRID="1"
export GAPS_STITCH_GENERATIONS="5"
export GAPS_STITCH_POPULATION="50"
EOF
```

If the user uses `zsh`, write the same exports to `~/.zshrc` instead.

Linux preflight:

```bash
for name in GAPS_STITCH_CLI GAPS_STITCH_INPUT_DIR GAPS_STITCH_OUTPUT_DIR; do
  value="$(printenv "$name")"
  if [ -z "$value" ]; then
    echo "Missing required environment variable: $name" >&2
    exit 1
  fi
done
if [ ! -x "$GAPS_STITCH_CLI" ]; then
  echo "CLI not found or not executable: $GAPS_STITCH_CLI" >&2
  exit 1
fi
if [ ! -d "$GAPS_STITCH_INPUT_DIR" ]; then
  echo "Input folder not found: $GAPS_STITCH_INPUT_DIR" >&2
  exit 1
fi
mkdir -p "$GAPS_STITCH_OUTPUT_DIR"
```

Linux default run:

```bash
"$GAPS_STITCH_CLI" \
  --folder "$GAPS_STITCH_INPUT_DIR" \
  --output-dir "$GAPS_STITCH_OUTPUT_DIR" \
  --auto-grid
```

Linux manual grid run:

```bash
"$GAPS_STITCH_CLI" \
  --folder "$GAPS_STITCH_INPUT_DIR" \
  --output-dir "$GAPS_STITCH_OUTPUT_DIR" \
  --manual-grid \
  --columns 25 \
  --rows 20
```

If no Linux executable exists but the source project is available, the user may
set `GAPS_STITCH_CLI` to a wrapper script. This is the recommended way for an
AI agent to call the tool on Linux, because the agent can invoke one stable
command regardless of where the project source lives.

Example wrapper script:

```bash
sudo tee /usr/local/bin/gaps_stitch_cli >/dev/null <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd /opt/puzzle-tool
exec python3 run_gaps_stitch.py "$@"
EOF
sudo chmod +x /usr/local/bin/gaps_stitch_cli
export GAPS_STITCH_CLI="/usr/local/bin/gaps_stitch_cli"
```

The `cd /opt/puzzle-tool` line must point to the folder that contains
`run_gaps_stitch.py`, `puzzle_stitcher/`, and `gaps/`.

After that, the AI agent should call:

```bash
"$GAPS_STITCH_CLI" \
  --folder "$GAPS_STITCH_INPUT_DIR" \
  --output-dir "$GAPS_STITCH_OUTPUT_DIR" \
  --auto-grid
```

If the agent is running inside the source project and no wrapper is configured,
it may run:

```bash
python run_gaps_stitch.py \
  --folder "$GAPS_STITCH_INPUT_DIR" \
  --output-dir "$GAPS_STITCH_OUTPUT_DIR" \
  --auto-grid
```

## Standard Workflow

1. Detect Windows or Linux.
2. Use only the matching OS section above.
3. Check required environment variables.
4. Verify the input folder exists and contains `.png` or `.bmp` files.
5. Prefer automatic grid mode unless the user gives exact columns and rows.
6. Run the CLI and monitor progress.
7. Report `gaps_solved_final.png` as the main result.

Fast preview settings on either OS:

```text
--generations 5 --population 50
```

Higher quality settings on either OS:

```text
--generations 20 --population 200
```

## Behavior Notes

- Automatic grid mode chooses factor pairs from the tile count and prefers a
  landscape grid close to square. For example, `500` tiles becomes `25 x 20`.
- Rectangular adaptive mode is automatic. Rectangular tiles are temporarily
  stretched to square solver pieces and the final result is restored to the
  original tile ratio.
- The CLI prints a progress bar for deterministic stages and an indeterminate
  solver message while the internal solver is running.
- The solver can take minutes for hundreds of tiles. A pause after `Piece size`
  usually means the solver is still working.

## Outputs

The output directory may contain:

- `gaps_input_shuffled.png`: temporary shuffled input for `gaps`.
- `gaps_solved_square.png`: intermediate square result when rectangular
  adaptive mode is active.
- `gaps_solved_final.png`: final restored image. Always point the user here.

Use the platform's path style in reports:

- Windows: `E:\puzzle-tool\output\gaps_solved_final.png`
- Linux: `/data/output/gaps_solved_final.png`

## Troubleshooting

- Missing environment variable: ask the user to set it, especially
  `GAPS_STITCH_CLI`, `GAPS_STITCH_INPUT_DIR`, and `GAPS_STITCH_OUTPUT_DIR`.
- Wrong OS command style: rewrite the command using the matching Windows or
  Linux section. Do not mix `$env:NAME` with bash or `export NAME=value` with
  PowerShell.
- Linux permission error: run `chmod +x "$GAPS_STITCH_CLI"` if the file exists
  but is not executable.
- Windows execution policy error: use a direct exe invocation with
  `& $env:GAPS_STITCH_CLI`; execution policy mainly affects `.ps1` scripts.
- Prime tile count: automatic grid may become `N x 1`; ask whether tiles are
  missing or whether the user should provide manual rows/columns.
- Mixed tile dimensions: ask the user to split or normalize the tile folder.
- Output missing: verify `GAPS_STITCH_OUTPUT_DIR`, permissions, and whether the
  process exited with an error.
- Slow solve: suggest `--generations 5 --population 50` first, then increase
  after the workflow is confirmed.

## Response Format

When reporting back to the user, match the user's language and include paths:

```text
Run complete.
OS: <Windows or Linux>
Input folder: <path>
Output folder: <path>
Grid: <columns> x <rows>
Final result: <path-to-gaps_solved_final.png>
Notes: <warnings or "none">
```
