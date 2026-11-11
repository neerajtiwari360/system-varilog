# SV Studio

A local NiceGUI IDE for this repository's existing Icarus, Verilator, Yosys,
Graphviz tools, with its own native VCD waveform viewer. No cloud service or Vivado is required.
Existing RTL, Makefile, Dockerfile, Compose configuration and viewer script are unchanged.

## Launch on Windows

From PowerShell in `D:\Github\system-varilog`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_sv_studio.ps1
```

Open **http://127.0.0.1:8080**. Stop the Python server with Ctrl+C. The command's
execution policy override applies only to that process; it does not change your
system policy. If your policy already permits local scripts, `.\start_sv_studio.ps1`
also works.
Use `-Port 8082` if 8080 is occupied. The launcher requires Docker Desktop
in Linux-container mode and either uv or Python 3.11+ (`py`). It creates a
repository `.venv`, installs dependencies and builds the existing Compose images.
Only dependency installation and image building require Internet access;
the running application and tools are local.

Manual setup with uv:

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -e '.[test]'
docker compose build sim wave
.venv/Scripts/python.exe -m sv_studio.app
```

## Workflow

1. Select a project, RTL top and testbench top. Candidate module names come from
   declarations, not filenames. The HDL tools perform actual elaboration.
2. Open files from the expandable project explorer. Tabs retain independent buffers.
   A star marks unsaved content. Save all or Ctrl+S writes changes. Run actions save
   all open changed files first. External disk edits cause a conflict message.
   The browser warns before closing a page with unsaved edits.
3. The toolbar follows **Save → Simulation → Waveform → Lint → Synthesis → Generate schematic**.
   These remain independent actions, so lint can also be run before simulation.
   Select source dependencies in **Compile sources**. Simulation includes the
   selected testbench sources; lint and synthesis exclude sources under `tb/`,
   `testbench/`, `testbenches/` or `tests/`. Select all RTL dependencies, including
   packages in the required order using a manifest. Elaboration errors identify
   missing or duplicate modules; adjust the selection and rerun.
4. Click Simulation, Lint or Synthesis. The interface streams real stdout/stderr,
   shows exact argv commands, exit codes, run identity, duration and diagnostics.
   Stop requests container removal as well as terminating the Docker client.
5. Generate schematic uses Yosys synthesis and Graphviz, then **View SVG** opens
   the generated gate-level diagram. The slider zooms, scrollbars pan, and Fit
   restores container width. Download original SVG is available.
6. After simulation, **Waveform** opens SV Studio's native canvas viewer in a
   **Waveform editor tab** and reads the selected run's VCD directly. It does not
   launch GTKWave, noVNC, a container, or an iframe. The first 12 distinct signals
   are shown automatically; use the signal list to search and select up to 64 traces.
   Use Zoom +/−, Fit, pan arrows, or the mouse wheel (Shift+wheel pans). Click a
   trace to position the time cursor and inspect exact values. Bus values can be
   hexadecimal, binary or unsigned decimal; unknown X and high-impedance Z states
   remain explicit. The tab identifies the run, testbench, VCD and timescale, with
   download and reload controls. Waveform stays accessible after lint or synthesis: it uses
   the latest simulation for the selected testbench, or an explicitly reopened simulation.
   A newer simulation without a VCD shows its missing-waveform state, never an older VCD.
   The original Make/GTKWave/noVNC workflow remains available independently.
7. Reopen previous run restores its own logs, metadata and artifacts. Clear logs
   only clears the current display; it does not delete saved logs.

CodeMirror is NiceGUI's bundled editor; it supplies SystemVerilog highlighting,
line numbers, indentation and Ctrl+F search/replace. Diagnostic buttons reveal
source lines. This version does not bundle an external Monaco integration.
Waveform opens in a full-width focus layout, hiding explorer, run results and console.
Use **Restore layout** to bring those panels back, or the folder/terminal/results
buttons to toggle individual panels. **Focus** maximizes any active tab. The console
has a resizable divider; sidebars keep readable widths. Signal selection is behind
the native viewer's **Signals** button. Trace names omit the common testbench prefix;
the selector retains full-name tooltips. Time labels automatically use readable
units (for example, 150 ns instead of 150000 ps). The layout fills the available
viewport with compact toolbars and independent scrolling for trees, results and traces.
Rerunning simulation while the Waveform tab is open shows a running state, then
automatically replaces the traces with that run's data. If no VCD is generated,
the viewer shows an explanation instead of retaining old traces or a blank panel.
The contrast button toggles the application theme;
the code editor retains its dark theme for readability.

## Project configuration

Projects are direct subdirectories of `projects/`. Use `rtl/` for synthesizable
sources, `tb/` for testbenches and `build/` for generated files. New file accepts
`rtl/name.sv`, `tb/name.sv` and nested directories. Generated files are read-only
in the editor. Existing projects work without configuration.

Optional `projects/<name>/sv_studio.json`:

```json
{
  "sources": ["rtl/package.sv", "rtl/core.sv", "tb/checks.sv"],
  "success": {"tb_core": "ALL_CORE_TESTS_COMPLETE"},
  "lint_config": "lint.vlt"
}
```

`sources` is an explicit ordered manifest; paths are project-relative. Selection
in the UI can remove or add files; manifest ordering is preserved for selected
entries. Include directories are derived from the source directories and project
root. A project-local Verilator `.vlt` configuration is supported. Arbitrary
browser-provided command flags or shell commands are not accepted.

Success markers are literal case-sensitive strings keyed by testbench module.
Choose a unique final completion message emitted only after every intended check.
Exit zero alone produces **Warning: execution completed, verification not established**.
Nonzero compile/runtime exits, `$fatal`, or reported FAIL/FAILED/FATAL/ERROR words
produce Failed. Reported warning/error counts are log diagnostics, not guaranteed
unique tool issue counts. A testbench that hides errors or prints an incorrect
completion marker cannot be verified by the IDE. Passing one test does not establish
complete functional verification.

The separate `sv_studio_examples` project contains combinational AND, registered
AND with reset/enable, and wrapping counter designs with self-checking testbenches.
Its manifest configures explicit completion markers. Existing examples were not edited.

## Architecture and generated files

* `app.py` binds only 127.0.0.1 and creates the shared workspace/tool service.
* `ui/layout.py` owns browser session buffers, controls, console and dialogs.
* `services/workspace.py` discovers projects, reads manifests and validates paths.
* `services/runner.py` runs argument-array subprocesses asynchronously, streams output,
  applies per-process timeouts (120 seconds by default) and removes cancelled containers.
* `services/tools.py` orchestrates compile/runtime/lint/synthesis and manages immutable
  run snapshots, metadata, artifacts and the viewer lifecycle.
* `services/netlist.py` counts instantiated leaf cells across the selected hierarchy,
  including repeated module instances, while excluding unused modules.
* `models.py` defines serializable run metadata without a frontend dependency.
* `services/vcd.py` reads bounded VCD files off the UI event loop, preserving scopes,
  aliases, widths, X/Z values and integer time ticks.
* `ui/waveform_viewer.py` loads run artifacts; `waveform_canvas.py`/`.js` draw traces
  and handle native browser selection, zoom, pan, radix and cursor controls.

Only one tool or viewer launch runs at a time across browser sessions. The frontend
can be replaced while retaining these services. Docker tools use `compose run --rm
--no-deps --workdir ... sim <tool>`, preserving the current tool images and mount.

Outputs are under `build/sv_studio/<project>/<timestamp-uuid>/`:

```text
metadata.json       selected sources/tops, status, UTC timestamps, versions,
                    exact argv commands and exit codes, diagnostics, statistics
version.log         actual tool version output
compile.log         Icarus compiler output (simulation only)
simulation.log      vvp output (simulation only)
lint.log            Verilator output (lint only)
synthesis.log       Yosys/Graphviz output (synthesis/schematic only)
work/               source and test-data snapshot, excluding previous build files
  build/            run-specific simulator binary, VCD, netlist.v/json, schematic.svg
```

Each tool runs inside its snapshot. Relative `$readmemb("tb/inputs.txt")` and
`$dumpfile("build/waves.vcd")` continue to work without editing RTL. Absolute paths
inside user HDL are not rewritten; use relative output paths for run isolation.
The native waveform viewer reads the selected artifact in place and creates no extra copy.
Generated files are ignored by Git. Runs are retained until manually removed.

All browser paths are workspace-relative and resolved before use. Traversal,
absolute paths, symlinks/junctions and editing outside project sources are rejected.
Tools use fixed argv templates. Yosys source paths are restricted to simple names
because Yosys has its own command parser. This is a trusted local development tool:
Docker has the existing writable repository mount, so only execute trusted HDL and
project configuration. Do not expose the server or Docker socket to a network.

## Accuracy and limitations

* Yosys 0.33 `read_verilog -sv` supports a subset of SystemVerilog. Unsupported
  interfaces/classes or verification constructs produce an error; sources are never
  transformed silently. Testbench modules must remain outside RTL directories.
* Statistics come from the actual generic synthesized JSON netlist and retain raw
  cell type names. Counts include instantiated child modules, rather than just cells
  directly in the top module. They are **not KV260 LUT/FF/BRAM utilization**, placement results
  or timing closure. Mapped memories may be flattened into logic by generic synthesis.
* Candidate discovery is lexical, not a full macro preprocessor or language server.
  Manual top selection can enter an identifier absent from the dropdown, provided
  the module declaration is discoverable in a selected source. Escaped identifiers,
  macro-generated module names, custom defines and external source trees are not
  supported yet. A source manifest replaces dependency inference.
* Only gate-level schematic is currently generated. Large flattened diagrams may
  be unwieldy; hierarchy/module drill-down is a future improvement.
* SVGs use an image context, rather than injecting SVG markup into the page.
* Warnings are distinct from errors. Verilator uses `-Wno-fatal`; warnings give
  Warning, not a hardware functional failure. Lint is separate from simulation.
* Missing VCD is an artifact state, not a simulation failure. VCDs already present
  in project input folders are excluded from snapshots.
* The native viewer supports digital VCD and displays real/string records as labeled
  segments, rather than analog plots. Limits: 16 MB file, 4096 declarations, 4096-bit
  signals, 500,000 value changes, 64 displayed traces, timestamps <= 2^53−1 ticks.
  Larger or unsupported input produces a clear error; FST/EVCD are not supported.
  Delta-cycle updates at the same tick show the settled value. At low zoom,
  subpixel activity is compressed into activity marks; zoom in to inspect transitions.
  Cursor values use the complete parsed events. Time labels apply the VCD timescale
  and choose an appropriate display unit; the cursor tooltip retains exact ticks.
  No assumptions about nanoseconds are made.
* Buffers are session-local and unsaved tabs are not restored after a browser reload.
  Run history is durable. Closing a tab within the IDE is not yet supported.
* Large snapshots and result lists are not optimized; service source-copying may
  briefly block the event loop for very large projects. Log output is streamed in chunks.

## Tests

```powershell
uv pip install --python .venv/Scripts/python.exe -e '.[test]'
.venv/Scripts/python.exe -m pytest -q
# Opt in to real tests using the existing Docker images:
$env:SV_STUDIO_DOCKER_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q
```

Unit tests use an explicit process fixture, never fake application results.
They cover discovery, manifests, module names, safe file operations, result states,
multi-source runs, stale artifacts, lint warnings, synthesis failures, path checks,
and real Python subprocess timeout/cancellation. NiceGUI user tests exercise editing,
saving and all four tool buttons through the backend. Real Docker tests cover all
three sample designs, legacy relative test data, intentional compile/runtime/synthesis
failures, missing VCD, timeouts and cancellation. Windows may skip symlink creation
without Developer Mode or the corresponding privilege.

## Troubleshooting

* **Docker missing:** the launcher checks PATH, the standard system install and
  `%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin`. Restart PowerShell after
  Docker installation. Ensure Linux containers are enabled.
* **Docker daemon unavailable:** start Docker Desktop and wait for its engine;
  verify `docker info` and `docker compose config`.
* **Image missing:** run `docker compose build sim wave`. SV Studio does not install
  another RTL toolchain.
* **Missing module:** select the declaration source and its dependencies. Names
  come from declarations, not the filename. Check duplicate declarations and manifest order.
* **Readmem file not found:** place test data under the project using a relative
  path. The snapshot preserves non-build project files.
* **No waveform:** add `$dumpfile("build/name.vcd")` and `$dumpvars` to the testbench,
  then rerun. Select that new simulation run before opening Waveform.
* **Port 6081 occupied:** stop this app's viewer with Stop viewer. For abandoned
  viewers inspect `docker ps --filter name=svstudio-wave-` and stop the specific
  container with `docker stop <container-name>`. Do not stop unrelated containers.
* **A run remains Running after an app crash:** inspect that run's logs and exact
  recorded command; check `docker ps --filter name=svstudio-`. Crash recovery is not
  automatic. Start a new run; previous artifacts are never adopted by the new run.
* **Synthesis parse failure:** inspect synthesis.log. Simplify unsupported syntax
  yourself or extend the frontend deliberately; the IDE never changes hardware behavior.

Suggested next work: hierarchy-aware source management, inline diagnostic decorations,
tab closing/recovery, larger-waveform streaming and module-level schematic navigation.
