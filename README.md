# SystemVerilog Lab

A hands-on workspace for learning RTL, simulation, and synthesis, progressing from logic gates toward FPGA and AI hardware.

You can use either **SV Studio**, the local browser IDE, or the original **Docker/Make commands**. Both use the same Docker toolchain and project sources. The command-line workflow remains available; SV Studio does not replace or remove it.

## Repository layout

```text
system-varilog/
|-- README.md                      # Setup and run instructions
|-- Dockerfile                     # Linux tool installation
|-- compose.yml                    # Simulation and browser viewer services
|-- Makefile                       # Shared simulation/synthesis commands
|-- start_sv_studio.ps1             # Browser IDE launcher
|-- pyproject.toml                 # Python application dependencies
|-- sv_studio/                     # IDE, native waveform viewer, services and tests
|-- scripts/view.sh                # Open the latest waveform
|-- docs/learning-guide.md          # Lessons, roadmap, and learning checklist
|-- build/sv_studio/                # Independent IDE run snapshots and outputs
`-- projects/
    |-- sv_studio_examples/        # Additional self-checking IDE examples
    `-- 01_logic_gates/
        |-- README.md              # Design descriptions and testbench names
        |-- rtl/                   # Synthesizable .sv modules
        |-- tb/                    # tb_<module>.sv and stimulus data
        `-- build/                 # Generated files, ignored by Git
```

Keep source files in `rtl/`, testbenches and input data in `tb/`, and generated outputs in `build/`. New projects use this same layout.

## Setup

Install and start Docker Desktop with Linux containers and Docker Compose available. Run all commands below in PowerShell from the repository root. The image provides Icarus Verilog, Yosys, Graphviz, Verilator, GTKWave, and noVNC.

SV Studio additionally requires Python 3.11+ or `uv`. Python is not required on the Windows host for the original Docker/Make workflow.

## Option 1: SV Studio browser IDE

Launch from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_sv_studio.ps1
```

Open [SV Studio](http://127.0.0.1:8080). The launcher prepares a local Python environment and builds the existing Docker services. The execution-policy override applies only to this PowerShell process.

1. Select the project, RTL top and testbench top.
2. Open files in the explorer, edit and save them. Expand **Source files** to select dependencies.
3. Click **Simulation**, then **Waveform** to inspect the generated VCD in SV Studio's own waveform viewer. No GTKWave or noVNC is launched by this action.
4. Use **Lint**, **Synthesis**, and **Generate schematic** to inspect diagnostics, generic cell counts, netlists and actual generated SVGs.
5. Use **Reopen run** to inspect earlier results. Each IDE execution has its own source snapshot, logs, metadata and artifacts.

Waveform opens in a focus layout. **Restore layout** brings back the explorer, results and console; the toolbar icons toggle them individually. The waveform viewer supports signal selection, zoom, pan, a time cursor, bus values and X/Z states.

Use `-Port 8082` after the launcher filename if port 8080 is occupied. Stop the server with Ctrl+C in its PowerShell window. See the [application README](sv_studio/README.md) for configuration, success criteria, installation, tests and limitations.

## Option 2: original Docker/Make workflow

The Makefile, Dockerfile, Compose configuration, existing RTL and testbenches are unchanged. You can continue running the commands below without starting SV Studio or installing its Python dependencies.

### Quick run: waveform and synthesis

From the repository root, build the tools once with `docker compose build`.
Then select only the testbench; synthesis automatically uses its name without `tb_`:

```powershell
docker compose run --rm sim make run TOP=tb_registered_io_en_rst_and
docker compose up -d --force-recreate wave
```

Open [GTKWave](http://localhost:6080/vnc.html?autoconnect=true), select signals in the hierarchy and click **Append**, then **Zoom Fit**.
The viewer opens the most recently generated VCD in the selected project's `build/` directory.
Recreate the viewer after another simulation to load the new waveform.

Available `TOP` values are `tb_and_gate`, `tb_or_gate`, `tb_registered_and`,
`tb_registered_io_and` (the default), and `tb_registered_io_en_rst_and`.
No command-file edits are needed to switch between them.
Use `make test` for simulation only or `make synth` for synthesis only, with the same `TOP=...` argument.
Existing `SYNTH_TOP=...` overrides remain supported.

Outputs are under `projects/01_logic_gates/build/`: the testbench's VCD,
`<module>_netlist.v`, `<module>_schematic.svg`, and `<module>_synth.log`.
AND and OR testbenches both write `waves.vcd`, so those two overwrite that waveform.
`make synth` performs generic Yosys logic synthesis; device-specific FPGA mapping and ASIC standard-cell mapping require separate future flows.

For another project, pass `PROJECT=<folder>` to Make and set `$env:PROJECT="<folder>"`
before starting the viewer. To open an older waveform, set
`$env:WAVE_FILE="registered_and.vcd"` before recreating the viewer;
`Remove-Item Env:WAVE_FILE -ErrorAction SilentlyContinue` restores automatic selection.

### Adding a new RTL design and testbench

For example, create these files with matching module names:

```text
projects/01_logic_gates/rtl/counter.sv      # module counter
projects/01_logic_gates/tb/tb_counter.sv    # module tb_counter
```

Instantiate `counter` in `tb_counter`, add input stimulus and output checks,
and end the simulation with `$finish`. Inside the testbench module, include:

```systemverilog
initial begin
    $dumpfile("build/counter.vcd");
    $dumpvars(0, tb_counter);
end
```

Run these commands from the repository root:

```powershell
docker compose run --rm sim make run TOP=tb_counter
docker compose up -d --force-recreate wave
Start-Process projects/01_logic_gates/build/counter_schematic.svg
```

The first command generates `counter.vcd`, `counter_netlist.v`,
`counter_schematic.svg`, and `counter_synth.log` in
`projects/01_logic_gates/build/`. Open
[GTKWave](http://localhost:6080/vnc.html?autoconnect=true), select and append
your signals, then use **Zoom Fit**.

No Makefile or script edits are required: RTL files in the project's `rtl/`
directory are included automatically, and `TOP=tb_counter` selects
`tb/tb_counter.sv` for simulation and `counter` for synthesis.
If the RTL top module has a different name, pass it explicitly:
`docker compose run --rm sim make run TOP=tb_counter SYNTH_TOP=my_counter`.

### Individual command-line tasks

Use the same `TOP` value as your main run:

```powershell
docker compose run --rm sim make lint TOP=tb_counter
docker compose run --rm sim make test TOP=tb_counter
docker compose run --rm sim make synth TOP=tb_counter
```

`counter` is the example design described above; create it before running those commands. `test` and `synth` are the individual stages of `run`, not alternative tool setups.

Stop the viewer with `docker compose stop wave`. To delete generated outputs for a project, run `docker compose run --rm sim make clean PROJECT=01_logic_gates` only after saving anything you want to keep.

## How the two workflows coexist

| Item | SV Studio | Docker/Make |
|---|---|---|
| Sources | Existing `projects/<project>/rtl/` and `tb/` files | The same project files |
| Top and dependencies | Select module declarations and source files; optional ordered manifest | `PROJECT`, `TOP`, and `SYNTH_TOP`; current Makefile filename conventions |
| Generated outputs | `build/sv_studio/<project>/<run-id>/` | `projects/<project>/build/` |
| Waveform display | Native viewer in the IDE | GTKWave through noVNC on localhost:6080 |
| Previous results | Separate run directories and history | Repeated commands can overwrite filenames |

Saving a source file in the IDE changes the same file used by later Make runs. Avoid editing that file simultaneously in multiple editors. Each IDE tool execution uses its own snapshot, so a completed run retains the source version used for that run.

The `sv_studio_examples` project uses an IDE source manifest and multiple modules per file; the current Makefile's `tb/<TOP>.sv` convention does not directly apply to that sample project. Existing `01_logic_gates` commands shown above continue to work.

Both workflows produce generic Yosys synthesis results, not final KV260 utilization or routed timing. SV Studio's simulation success labels require configured testbench completion criteria; a zero exit code alone is not proof of functional correctness.

## Project notes and learning material

- [Project 01: available designs and checks](projects/01_logic_gates/README.md)
- [Lessons, roadmap, and learning checklist](docs/learning-guide.md)

Generic synthesis produces a logical netlist and schematic. It does not produce a device bitstream, routed timing, physical layout, or a technology-mapped ASIC.

- [SV Studio: detailed application guide](sv_studio/README.md)
- [Implementation and validation record](sv_studio/VALIDATION.md)
