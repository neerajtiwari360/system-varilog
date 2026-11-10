# SystemVerilog Lab

A hands-on workspace for learning RTL, simulation, and synthesis, progressing from logic gates toward FPGA and AI hardware.

This README is the single run guide. Use the same Make targets for existing and new designs; there is no need to edit command files for each module.

## Repository layout

```text
system-varilog/
|-- README.md                      # Setup and run instructions
|-- Dockerfile                     # Linux tool installation
|-- compose.yml                    # Simulation and browser viewer services
|-- Makefile                       # Shared simulation/synthesis commands
|-- scripts/view.sh                # Open the latest waveform
|-- docs/learning-guide.md          # Lessons, roadmap, and learning checklist
`-- projects/
    `-- 01_logic_gates/
        |-- README.md              # Design descriptions and testbench names
        |-- rtl/                   # Synthesizable .sv modules
        |-- tb/                    # tb_<module>.sv and stimulus data
        `-- build/                 # Generated files, ignored by Git
```

Keep source files in `rtl/`, testbenches and input data in `tb/`, and generated outputs in `build/`. New projects use this same layout.

## Setup

Install and start Docker Desktop with Linux containers and Docker Compose available. Run all commands below in PowerShell from the repository root. The image provides Icarus Verilog, Yosys, Graphviz, Verilator, GTKWave, and noVNC.

## Quick run: waveform and synthesis

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

## Optional tasks using the same workflow

Use the same `TOP` value as your main run:

```powershell
docker compose run --rm sim make lint TOP=tb_counter
docker compose run --rm sim make test TOP=tb_counter
docker compose run --rm sim make synth TOP=tb_counter
```

`counter` is the example design described above; create it before running those commands. `test` and `synth` are the individual stages of `run`, not alternative tool setups.

Stop the viewer with `docker compose stop wave`. To delete generated outputs for a project, run `docker compose run --rm sim make clean PROJECT=01_logic_gates` only after saving anything you want to keep.

## Project notes and learning material

- [Project 01: available designs and checks](projects/01_logic_gates/README.md)
- [Lessons, roadmap, and learning checklist](docs/learning-guide.md)

Generic synthesis produces a logical netlist and schematic. It does not produce a device bitstream, routed timing, physical layout, or a technology-mapped ASIC.
