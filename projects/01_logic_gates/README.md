# Project 01: Logic gates and registers

Use the [root run guide](../../README.md#quick-run-waveform-and-synthesis) for setup, waveform generation, synthesis, and viewing results. All commands run from the repository root. Select a testbench from the table below with `TOP=...`; no script edits are needed.

## Designs

Each RTL file is `rtl/<module>.sv`, and its testbench is `tb/tb_<module>.sv`.

| RTL module | Testbench (`TOP`) | Behavior | Waveform in `build/` |
|---|---|---|---|
| `and_gate` | `tb_and_gate` | Combinational AND | `waves.vcd` |
| `or_gate` | `tb_or_gate` | Combinational OR | `waves.vcd` |
| `registered_and` | `tb_registered_and` | Registered AND with synchronous reset and enable | `registered_and.vcd` |
| `registered_io_and` | `tb_registered_io_and` | Registered inputs followed by registered AND output; synchronous reset | `registered_io_and.vcd` |
| `registered_io_en_rst_and` | `tb_registered_io_en_rst_and` | Registered inputs, reset, and enable followed by registered output | `registered_io_en_rst_and.vcd` |

The default is `tb_registered_io_and`. AND and OR currently share `waves.vcd`, so running one replaces the other's waveform. Other designs have separate VCD files.

## Files and outputs

- `rtl/`: the five synthesizable modules listed above.
- `tb/`: their five self-checking testbenches and `inputs.txt` containing `00`, `01`, `10`, and `11`.
- `build/`: generated VCDs, simulator output, and `<module>_netlist.v`, `<module>_schematic.svg`, and `<module>_synth.log`; ignored by Git.

The Makefile runs simulation inside this project directory so `tb/inputs.txt` and `build/` resolve correctly. Yosys receives RTL files only, not testbenches.

## What to inspect

- Combinational gates: check all four input combinations.
- `registered_and`: check reset, enabled capture, disabled hold, and reset priority.
- `registered_io_and`: inputs are captured on one rising edge and their AND result on the next. Reset clears both stages.
- `registered_io_en_rst_and`: controls are also registered; external reset and enable affect the output stage after passing through their control registers.

All five existing testbenches passed the local Icarus simulation check and generated VCDs. This verifies their existing assertions, not exhaustive design correctness. Docker synthesis and the browser viewer were not verified in that check because Docker/Yosys were unavailable in the execution environment.

The shared synthesis target generates generic logic. Device-specific KV260 mapping, placement/routing, timing analysis, bitstreams, and ASIC standard-cell mapping are future work. See the [learning guide](../../docs/learning-guide.md) for the broader roadmap.

## Adding another design

Follow [Adding a new RTL design and testbench](../../README.md#adding-a-new-rtl-design-and-testbench). Keep the `<module>` / `tb_<module>` naming convention and choose a unique `build/<module>.vcd` filename.

## SV Studio simulation status

`sv_studio.json` maps each testbench to its final completion message. Studio reports
**Passed** only after that message is observed, the simulator exits successfully,
and no failure is reported. Individual per-vector PASS messages are not used as
the completion criterion. Add a final marker to this mapping when adding a testbench.

If an earlier run shows **Warning** despite printing PASS, rerun Simulation after
the configuration update. Configuration is read on every run; no server restart
is needed. Saved run history keeps its original status. An unconfigured testbench
continues to show Warning because exit code zero alone does not establish success.
