# Project 01 — Logic Gates, Registers, FPGA Synthesis and Waveforms

## Overview

This project begins with a **2-input combinational AND gate** and extends it to a **registered AND gate with synchronous reset and clock enable**. Both designs are written in SystemVerilog, verified with Icarus Verilog, and mapped with Yosys to primitives appropriate for the **AMD/Xilinx Kria KV260 (K26 Zynq UltraScale+ MPSoC)**.

The goal is to understand the distinction between:

- **RTL:** the behaviour and state described in SystemVerilog.
- **Simulation:** whether the RTL does what is intended, and how signals change over time.
- **Synthesis:** what logic resources implement that behaviour.
- **Implementation:** placement, routing, physical timing, and FPGA configuration (not yet performed in this project).

The verified original AND-gate testbench reported `PASS: All AND gate tests passed`. Registered-AND verification and any new synthesis commands should be run and checked independently; this README does not claim those steps have already passed.

## 1. Project structure

```text
system-varilog/
├── Dockerfile
├── compose.yaml
├── Makefile
├── scripts/
└── projects/
    └── 01_logic_gates/
        ├── rtl/
        │   ├── and_gate.sv
        │   └── registered_and.sv
        ├── tb/
        │   ├── tb_and_gate.sv
        │   └── tb_registered_and.sv
        ├── build/                 # Generated artifacts; do not commit
        │   ├── waves.vcd          # Original AND testbench
        │   ├── registered_and.vcd # Registered AND testbench
        │   ├── and_kv260.v       # Example mapped synthesis netlist
        │   └── ...
        └── README.md
```

The registered-AND files are expected additions; create them if absent. Paths in the commands below assume that the `sim` Compose service mounts the repository and starts in its root directory, as in the verified commands used for this project.

## 2. Tools and environment

| Tool | Purpose |
|---|---|
| Docker Desktop + Compose | Reproducible Linux tools on Windows |
| Icarus Verilog 12.0 (`iverilog`, `vvp`) | Compile and simulate supported SystemVerilog |
| Yosys 0.33 | Generic synthesis and Xilinx UltraScale+ primitive mapping |
| Graphviz `dot` 2.43.0 | Convert synthesized schematic `.dot` into `.svg` |
| Verilator (if included) | Lint checks |
| GTKWave + noVNC (if configured) | Examine `.vcd` waveforms in the browser |
| Vivado (future) | Exact KV260 device implementation, timing, and bitstream |

Confirmed in the Docker environment: Icarus Verilog 12.0, Yosys 0.33, and Graphviz 2.43.0. Verify other tools and the wave service configuration before using them.

From **Windows PowerShell**, at the repository root:

```powershell
cd D:\Github\system-varilog
docker compose build
docker compose run --rm sim yosys -V
```

**PowerShell quoting tip:** invoke `yosys -p "..."` directly with `docker compose run --rm sim yosys ...`, as below. Previous attempts to nest a Yosys script inside `sh -c` caused a `read_verilog: No filename given` error.

## 3. Experiment A — Combinational AND gate

### RTL: `rtl/and_gate.sv`

```systemverilog
module and_gate (
    input  logic a,
    input  logic b,
    output logic y
);
    assign y = a & b;
endmodule
```

There is **no clock** and **no storage**. The logic is continuously evaluated as `a` and `b` change.

| a | b | y |
|---|---|---|
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

### Verify the original testbench

Use the project's existing `tb/tb_and_gate.sv` that writes `build/waves.vcd`.

```powershell
docker compose run --rm sim sh -c "cd projects/01_logic_gates && mkdir -p build && iverilog -g2012 -s tb_and_gate -o build/and_sim.vvp rtl/and_gate.sv tb/tb_and_gate.sv && vvp build/and_sim.vvp"
```

Confirmed output from this project:

```text
VCD info: dumpfile build/waves.vcd opened for output.
Time  A  B  Y
10000  0  0  0
20000  0  1  0
30000  1  0  0
40000  1  1  1
PASS: All AND gate tests passed
```

With `timescale 1ns/1ps`, the printed times can appear in picoseconds when the testbench prints `$time` using its chosen formatting.

**Important:** The testbench's `$dumpfile("build/waves.vcd")` is relative to the *runtime working directory*. Run `vvp` from `projects/01_logic_gates` (as above) to avoid `Unable to open build/waves.vcd for output`.

### Map the AND gate to KV260-family primitives

```powershell
docker compose run --rm sim yosys -Q -T -p "read_verilog -sv projects/01_logic_gates/rtl/and_gate.sv; synth_xilinx -family xcup -top and_gate -noiopad; stat; write_verilog -noattr projects/01_logic_gates/build/and_kv260.v"
Get-Content projects\01_logic_gates\build\and_kv260.v
```

The **actual generated output already observed** for this project was:

```verilog
module and_gate(a, b, y);
  input a;
  wire a;
  input b;
  wire b;
  output y;
  wire y;
  LUT2 #(
    .INIT(4'h8)
  ) _0_ (
    .I0(a),
    .I1(b),
    .O(y)
  );
endmodule
```

Interpretation:

- `LUT2`: Xilinx two-input LUT primitive.
- `INIT(4'h8)`: truth-table bits `1000`; output is 1 only when both inputs are 1.
- `.I0(a)`, `.I1(b)`, `.O(y)`: input/output connections.
- `xcup`: targets the **UltraScale+ architecture family**, not the exact K26 part's physical placement or timing.

### Generate the synthesized logical schematic

```powershell
docker compose run --rm sim yosys -Q -T -p "read_verilog -sv projects/01_logic_gates/rtl/and_gate.sv; synth_xilinx -family xcup -top and_gate -noiopad; show -format dot -prefix projects/01_logic_gates/build/and_kv260_synth"
docker compose run --rm sim dot -Tsvg projects/01_logic_gates/build/and_kv260_synth.dot -o projects/01_logic_gates/build/and_kv260_synth.svg
Start-Process projects\01_logic_gates\build\and_kv260_synth.svg
```

This schematic shows **mapped logical primitives**, not transistor-level LUT internals or physical placement.

## 4. Experiment B — Registered AND with reset and enable

### RTL: `rtl/registered_and.sv`

```systemverilog
module registered_and (
    input  logic clk,
    input  logic rst,
    input  logic en,
    input  logic a,
    input  logic b,
    output logic y
);
    always_ff @(posedge clk) begin
        if (rst)
            y <= 1'b0;
        else if (en)
            y <= a & b;
    end
endmodule
```

**Interpretation:**

- `a & b` describes the combinational AND operation.
- `always_ff @(posedge clk)` infers a positive-edge-triggered storage element.
- `rst` is **active-high synchronous reset**: it clears `y` on the next rising edge, even if `en` is 0.
- `en` controls whether the flip-flop captures a new AND result.
- With `rst=0, en=0`, the flip-flop **holds its previous output** (the missing `else` is intentional).
- There is no asynchronous reset; `rst` alone does not immediately update `y` between clock edges.

| At a rising clock edge | Next `y` |
|---|---|
| `rst=1` | `0`, regardless of enable or inputs |
| `rst=0`, `en=1` | `a & b` |
| `rst=0`, `en=0` | Previous value |

### Self-checking testbench: `tb/tb_registered_and.sv`

Create or replace the testbench with this reproducible example:

```systemverilog
`timescale 1ns/1ps

module tb_registered_and;
    logic clk = 0;
    logic rst = 0;
    logic en  = 0;
    logic a   = 0;
    logic b   = 0;
    wire y;

    registered_and dut (
        .clk(clk), .rst(rst), .en(en),
        .a(a), .b(b), .y(y)
    );

    always #5 clk = ~clk; // Period = 10 ns; rising edges at 5,15,25,... ns

    initial begin
        $dumpfile("build/registered_and.vcd");
        $dumpvars(0, tb_registered_and);

        // Reset has priority over en on the first rising edge (5 ns).
        rst = 1; en = 0; a = 1; b = 1;
        @(posedge clk); #1;
        if (y !== 0) $fatal(1, "Synchronous reset failed");

        // Apply a=b=1 while enable is active, before the next rising edge.
        @(negedge clk);
        rst = 0; en = 1; a = 1; b = 1;
        #1;
        if (y !== 0) $fatal(1, "Output changed before rising edge");
        @(posedge clk); #1;
        if (y !== 1) $fatal(1, "Enabled AND=1 failed");

        // Disable capture; even as the AND result changes to zero, y stays 1.
        @(negedge clk);
        en = 0; a = 0; b = 1;
        @(posedge clk); #1;
        if (y !== 1) $fatal(1, "Clock-enable hold failed");

        // Reset overrides en=0 at the next rising edge.
        @(negedge clk);
        rst = 1;
        #1;
        if (y !== 1) $fatal(1, "Synchronous reset applied too early");
        @(posedge clk); #1;
        if (y !== 0) $fatal(1, "Reset priority failed");

        // Re-enable with a=0, b=1; output remains zero.
        @(negedge clk);
        rst = 0; en = 1; a = 0; b = 1;
        @(posedge clk); #1;
        if (y !== 0) $fatal(1, "Enabled AND=0 failed");

        $display("PASS: registered AND, enable, hold, and synchronous reset");
        $finish;
    end
endmodule
```

The `#1` after each clock edge allows nonblocking assignments to settle before assertions. Input changes are made on falling edges to avoid sampling races.

### Simulate and generate the new VCD

From the repository root:

```powershell
docker compose run --rm sim sh -c "cd projects/01_logic_gates && mkdir -p build && iverilog -g2012 -s tb_registered_and -o build/registered_and.vvp rtl/registered_and.sv tb/tb_registered_and.sv && vvp build/registered_and.vvp"
```

Check the file:

```powershell
Get-ChildItem projects\01_logic_gates\build\*.vcd
```

Expected files:

```text
waves.vcd           # Original combinational AND
registered_and.vcd  # New registered AND with rst and en
```

The simulation should print `PASS: registered AND, enable, hold, and synchronous reset` if the test passes. That result is **expected**, not yet verified in this document.

## 5. Open the *correct* waveform in GTKWave

Running `docker compose up wave` only starts the viewer. **It does not choose the newest VCD**. Your existing `wave` service may still auto-open `build/waves.vcd`, which shows the older AND gate.

### Option A — Use the existing GTKWave GUI (no Compose edits)

```powershell
docker compose up -d wave
```

Open [GTKWave via noVNC](http://localhost:6080/vnc.html?autoconnect=true).

In GTKWave:

1. Choose **File → Open** or **File → Open New Tab**.
2. Navigate to the directory that the `wave` container uses for project files (the exact path depends on `compose.yaml`).
3. Open **`registered_and.vcd`**, *not* `waves.vcd`.
4. Expand `tb_registered_and` and add `clk`, `rst`, `en`, `a`, `b`, and `y` to the trace window.
5. Use **Zoom Fit** to inspect all transitions.

If you cannot find the file, inspect the service's effective configuration:

```powershell
docker compose config
```

Look at `wave:` volume mounts, working directory, `command:` and `entrypoint:`. If the service uses `scripts/view.sh`, examine that script. Do not assume a particular path inside the viewer without checking the mount.

### Option B — Make registered AND the default waveform

If `compose.yaml` or `scripts/view.sh` hardcodes `waves.vcd`, change only that path to the mounted location of `registered_and.vcd`, then recreate the service:

```powershell
docker compose up -d --force-recreate wave
```

Do **not** overwrite or delete the original `waves.vcd` to force GTKWave to show the new simulation; preserving both is useful for comparison.

### What to observe

| Signal | What it demonstrates |
|---|---|
| `clk` | Rising edges trigger register updates |
| `rst` | Synchronous reset only acts at an edge |
| `en` | Whether the register captures or holds |
| `a`, `b` | Inputs feeding the combinational LUT |
| `y` | Registered value; may differ from `a & b` between edges |

Key waveform tests: with `en=0`, changing `a`/`b` must not change `y`; with `rst=1`, `y` clears only after a rising edge.

## 6. Synthesize registered AND for the KV260 architecture

```powershell
docker compose run --rm sim yosys -Q -T -p "read_verilog -sv projects/01_logic_gates/rtl/registered_and.sv; synth_xilinx -family xcup -top registered_and -noiopad; stat; write_verilog -noattr projects/01_logic_gates/build/registered_and_kv260.v"
Get-Content projects\01_logic_gates\build\registered_and_kv260.v
```

Look for the following mapped resources:

- **`LUT2`** implementing `a & b`, typically with `INIT(4'h8)`.
- **`FDRE`** for the registered output. Its `D` input comes from the LUT; `Q` drives `y`.
- **`BUFG`** for distributing the clock, if inserted by the synthesis flow.
- **`CE` and `R` connections** driven by enable/reset logic, rather than the constants `1` and `0` used by the original unconditionally updated register.

Exact mapping can vary with optimization. For a synchronous active-high reset with reset priority, an `FDRE` is a natural mapping, but always examine the generated netlist.

### Generate the synthesized schematic

```powershell
docker compose run --rm sim yosys -Q -T -p "read_verilog -sv projects/01_logic_gates/rtl/registered_and.sv; synth_xilinx -family xcup -top registered_and -noiopad; show -format dot -prefix projects/01_logic_gates/build/registered_and_synth"
docker compose run --rm sim dot -Tsvg projects/01_logic_gates/build/registered_and_synth.dot -o projects/01_logic_gates/build/registered_and_synth.svg
Start-Process projects\01_logic_gates\build\registered_and_synth.svg
```

The schematic should show a path similar to:

```text
a ─┐
   ├── LUT2 (AND) ───── D   ┌───────────┐
b ─┘                      ──▶│ FDRE      │── Q ──▶ y
clk ── BUFG ───────────── C │           │
en ───────────────────── CE │           │
rst ───────────────────── R └───────────┘
```

This is a **logical post-synthesis schematic**, not an FPGA routing or transistor diagram.

## 7. Simulation versus synthesis — why only RTL is passed to Yosys

| Simulation | Synthesis |
|---|---|
| Inputs: design RTL **and testbench** | Input: synthesizable design RTL |
| Tool: Icarus Verilog | Tool: Yosys |
| Checks outputs and clock-cycle behaviour | Maps operations and state to FPGA primitives |
| Generates VCD signals and PASS/FAIL checks | Generates netlist, primitive statistics and schematic |
| Uses `#` delays, `$dumpfile`, `$fatal`, `$finish` | Testbench-only constructs are not implemented as circuit hardware |

A **testbench is necessary for verification**, but it is not part of the physical circuit being synthesized.

## 8. What is known and what is not yet measured

| Question | Status |
|---|---|
| Does the original AND gate pass simulation? | **Yes — verified** |
| Does the original AND map to a Xilinx LUT? | **Yes — `LUT2`, `INIT(4'h8)` observed** |
| Has a registered AND mapped to `LUT2`, `FDRE`, `BUFG`? | **Yes — observed in the schematic for the version without explicit en/rst** |
| Is the new reset/enable registered AND test verified? | Run the revised testbench and confirm |
| Is the latest VCD displayed in GTKWave? | Open `registered_and.vcd` explicitly |
| Is the netlist placed and routed for the exact KV260 device? | **No** |
| Are exact device delay, Fmax and power known? | **No** |
| Has a KV260 bitstream been generated and loaded? | **No** |

For exact K26 resource placement, routing, static timing and configuration, use an appropriate device-specific implementation flow such as Vivado. The Yosys option `-family xcup` selects UltraScale+ primitives but not the specific KV260 physical device.

## 9. Lint, cleanup and Git hygiene

The existing project may expose Make targets such as:

```powershell
docker compose run --rm sim make lint
```

Check the root `Makefile` before assuming `lint` automatically selects the new `registered_and.sv`. If it is hardcoded to `and_gate.sv`, update or parameterize the target first.

A manual Verilator lint check (if Verilator is installed) is:

```powershell
docker compose run --rm sim verilator --lint-only -Wall -Wno-fatal --top-module registered_and projects/01_logic_gates/rtl/registered_and.sv
```

**Do not run `make clean` before inspecting saved waveforms and netlists**; it may delete the `build/` outputs. Generated VCD, simulation, SVG and netlist files should generally remain ignored by Git.

## 10. Concepts learned

- [x] Create and simulate a combinational AND gate.
- [x] Verify all four truth-table cases.
- [x] Generate an AND-gate VCD.
- [x] Map the AND gate to Xilinx `LUT2` (`INIT=4'h8`).
- [x] View a synthesized registered-AND schematic containing a LUT, FF and clock buffer.
- [ ] Verify the synchronous reset and clock-enable behavior with a new testbench.
- [ ] Open `registered_and.vcd` in GTKWave and inspect the six key signals.
- [ ] Inspect the new mapped `FDRE.CE` and `FDRE.R` connections.
- [ ] Compare generic logic synthesis versus target-specific FPGA synthesis.
- [ ] Compare the same RTL against an ASIC standard-cell Liberty library.
- [ ] Implement on the exact K26 target, analyze timing, generate bitstream and validate on the KV260.

## 11. Next learning milestones

1. Compare `assign y = a & b` with `always_ff @(posedge clk)` and explain why one needs storage.
2. Investigate `FDRE` ports (`C`, `CE`, `D`, `R`, `Q`) and reset priority.
3. Add an 8-bit register and a counter; inspect FF counts and inferred logic.
4. Learn setup time, hold time, clock-to-Q and critical paths.
5. Implement the KV260 circuit through a real interface (for example, processor-controlled GPIO/AXI) without assuming arbitrary pins on the board.
6. Add an ASIC flow using an actual standard-cell library, then compare logical function, resources, physical implementation and timing.

**Learning principle:** RTL describes what the circuit does; the testbench proves its behaviour; synthesis reveals which hardware primitives implement it; physical implementation determines where those primitives go and whether timing is met.
