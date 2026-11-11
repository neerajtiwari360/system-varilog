# Implementation and validation record

Validated locally on Windows on 11 November 2026.

## Results

* Unit and NiceGUI simulated-client suite: **28 passed** including hierarchy-count regressions.
* Regression coverage now reruns simulation while the Waveform tab is active,
  checks the running message, verifies automatic refresh to the new run and confirms
  that a missing VCD replaces old traces with an explanation. Tab transitions are
  disabled and the editor tabs use explicit grid rows and full-width panel sizing.
* Native canvas drawing and interaction: **4 JavaScript checks passed**, including
  trace edge coordinates, cursor values at transitions, zoom/pan/fit, X/Z coloring,
  wide-bus hexadecimal formatting, unsigned values, shortened names and readable time units.
* Layout regression tests cover automatic waveform focus, hiding all supporting
  panels, restoring panel visibility and preserving user choices when restoring.
* The native viewer was tested through the real UI callbacks with Icarus-produced VCD,
  after synthesis, with no GTKWave/noVNC viewer launched. Earlier noVNC checks below
  describe the retained legacy workflow, not the current Waveform action.
* Real Docker integration: **4 tests passed**, executed in separate targeted runs:
  all sample designs plus legacy test-data loading; intentional failures/timeouts/
  cancellation; GTKWave/noVNC; real UI callback-to-tool integration.
* One symlink-creation test skipped because Windows denied creating symlinks.
  The four opt-in Docker tests are additionally skipped in the default test command.
* Actual tools: Icarus 12.0, Verilator 5.020, Yosys 0.33. Graphviz generated actual SVGs.
* AND, registered AND and counter: configured completion criteria met in simulation;
  lint completed with warnings; generic synthesis netlists and schematics generated.
* Legacy `tb_registered_io_and`: simulation completed with its expected output and
  relative `$readmemb` data. IDE correctly reported Warning without configured criteria.
* Intentional `$fatal`, compiler syntax errors and Yosys parse errors reported Failed.
  Missing VCD did not turn a completed simulation into a failure.
* Real Docker timeout and cancellation cleanup completed; no `svstudio-` test
  containers remained after verification.
* noVNC served HTTP 200 and GTKWave startup logs identified the explicitly selected
  run's VCD. A discovered proxy/readiness race was fixed by checking HTTP readiness.
* NiceGUI simulated-client tests clicked Save, Simulation, Lint, Synthesis and Generate
  schematic using the real Docker services, then opened the generated SVG dialog.
  The follow-up integration test also opened the embedded Waveform tab after synthesis,
  checked iframe-compatible HTTP headers and completed the WebSocket connection to
  the real VNC server (RFB protocol banner received).
* Toolbar order is Save, Simulation, Waveform, Lint, Synthesis, Generate schematic,
  Stop. Regression tests verify that order, native waveform access after synthesis,
  and no fallback to stale waveforms when the newest run lacks a VCD.
* Existing `docker compose run --rm --no-deps sim make test synth`: succeeded.
* Documented launcher with a process-only PowerShell execution-policy override:
  dependency installation and existing image builds succeeded; app served HTTP 200
  on temporary port 8082. The latest server was left available at that port.
* Python compilation and `git diff --check` passed.

## Remaining verification limits

The larger streaming ALU/pipeline/FIFO acceptance project is documented in
[its validation report](../projects/02_streaming_stress/VALIDATION.md). It exercises
all tool actions using real containers, native waveform data/drawing, post-synthesis
simulation and an intentional failure. It exposed and fixed hierarchy undercounting
in resource statistics and duplicate counting of Verilator warning-help lines.

Pixel-level browser layout inspection was blocked by the unavailable browser
automation host and a minimized Edge window. No claim is made that GTKWave's
interactive signal display, browser keyboard behavior or drag resizing received
visual end-to-end verification. Component/event tests and real backend/viewer HTTP
checks passed. The full UI is implemented, but this visual acceptance check remains.

CodeMirror is used instead of Monaco; gate-level diagrams use zoom and scrollbars
instead of freeform drag panning. Hierarchy drill-down, tab closing/recovery and
advanced SystemVerilog language-server support remain future work. The README
documents source, synthesis frontend, waveform and local-trust limitations.

## Exact source file changes

Modified:

```text
.dockerignore
.gitignore
README.md
```

Created:

```text
pyproject.toml
start_sv_studio.ps1
projects/sv_studio_examples/rtl/designs.sv
projects/sv_studio_examples/tb/checks.sv
projects/sv_studio_examples/sv_studio.json
sv_studio/__init__.py
sv_studio/app.py
sv_studio/models.py
sv_studio/README.md
sv_studio/VALIDATION.md
sv_studio/services/__init__.py
sv_studio/services/workspace.py
sv_studio/services/runner.py
sv_studio/services/tools.py
sv_studio/ui/__init__.py
sv_studio/ui/layout.py
sv_studio/ui/shell.py
sv_studio/ui/studio.css
sv_studio/ui/waveform_viewer.py
sv_studio/ui/waveform_canvas.py
sv_studio/ui/waveform_canvas.js
sv_studio/services/vcd.py
sv_studio/tests/conftest.py
sv_studio/tests/test_services.py
sv_studio/tests/test_ui.py
sv_studio/tests/test_docker_integration.py
sv_studio/tests/test_vcd.py
sv_studio/tests/test_waveform_lifecycle.py
sv_studio/tests/waveform_canvas.test.mjs
```

Ignored local environment/cache and generated build outputs were also created.
Existing RTL, testbenches, Makefile, Dockerfile, Compose configuration and viewer
script were not edited. Existing Make targets generated their normal project build
outputs during verification.

Suggested next improvements: complete visual browser acceptance, add hierarchy-level
schematics, then tab closing/recovery and richer diagnostic decorations.
