# Project 01 — Logic Gates in SystemVerilog

## Overview

This project introduces basic combinational digital logic using SystemVerilog.

The first implemented circuit is a **2-input AND gate**.

The project demonstrates the complete RTL development workflow:

1. Write SystemVerilog RTL.
2. Create a testbench.
3. Compile the RTL using Icarus Verilog.
4. Simulate and verify the output.
5. Run Verilator lint checks.
6. Generate a VCD waveform.
7. View the waveform using GTKWave through Docker and noVNC.

All tools run inside Docker, so no HDL compiler or waveform viewer needs to be installed directly on Windows.

## 1. Project Structure

```text
01_logic_gates/
├── rtl/
│   └── and_gate.sv
├── tb/
│   └── tb_and_gate.sv
├── build/                # Generated, ignored by Git
└── README.md
```

The Dockerfile, Compose configuration, Makefile and shared scripts are located at the repository root.

## 2. AND Gate Design

An AND gate produces a HIGH output only when both inputs are HIGH.

**Truth table**

| A | B | Y |
|---|---|---|
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

Boolean expression:

`Y = A & B`

**RTL file:** `rtl/and_gate.sv`

```systemverilog
module and_gate (
    input  logic a,
    input  logic b,
    output logic y
);

    assign y = a & b;

endmodule
```

This is combinational logic. It requires no clock or registers.

## 3. Testbench

**Testbench file:** `tb/tb_and_gate.sv`

The testbench verifies all four possible input combinations.

Each combination is applied for 10 ns of simulated time.

The testbench also generates `build/waves.vcd`, which contains the simulation waveform.

The simulation reports a failure if an output does not match the expected value.

## 4. Prerequisites

- Windows with Docker Desktop installed and running
- Docker configured for Linux containers
- PowerShell or VS Code terminal
- Web browser

All HDL tools are installed inside the Docker image.

## 5. Build the Docker Image

Open PowerShell in the **repository root**, not inside the individual project directory.

Run:

```powershell
docker compose build
```

This prepares the environment containing Icarus Verilog, Verilator, GTKWave and noVNC.

## 6. Run the Simulation

From the repository root:

```powershell
docker compose run --rm sim make test PROJECT=01_logic_gates TOP=tb_and_gate
```

This command:

1. Creates the project's `build/` directory if needed.
2. Compiles the RTL and testbench.
3. Runs the simulation.
4. Checks the AND gate outputs.
5. Generates the waveform file.

**Expected result:**

```text
VCD info: dumpfile build/waves.vcd opened for output.
Time  A  B  Y
10000  0  0  0
20000  0  1  0
30000  1  0  0
40000  1  1  1
PASS: All AND gate tests passed
```

The timestamps are reported in picoseconds because the testbench uses `1ns/1ps` timescale settings.

## 7. Run RTL Lint

```powershell
docker compose run --rm sim make lint
```

Linting uses Verilator to detect potential RTL issues and coding warnings.

Successful linting completes without warnings or errors.

## 8. View the Waveform

First, run the simulation to generate `waves.vcd`.

Then start the waveform viewer:

```powershell
docker compose up wave
```

Open the following URL in your Windows browser:

http://localhost:6080/vnc.html?autoconnect=true

Inside GTKWave:

1. Expand `tb_and_gate` in the SST panel.
2. Select the module.
3. Select signals `a`, `b`, and `y` in the Signals panel.
4. Click **Append**.
5. Use Zoom Full or Zoom Fit to display the full simulation.

**Expected waveform behaviour**

| Simulation Time | A | B | Y |
|---|---|---|---|
| 0–10 ns | 0 | 0 | 0 |
| 10–20 ns | 0 | 1 | 0 |
| 20–30 ns | 1 | 0 | 0 |
| 30–40 ns | 1 | 1 | 1 |

The output becomes HIGH at 30 ns when both inputs are HIGH.

Stop the waveform service using `Ctrl+C` in its terminal.

## 9. Clean the Build

To remove generated simulation outputs:

```powershell
docker compose run --rm sim make clean PROJECT=01_logic_gates
```

The `build/` directory and generated simulation outputs are excluded from Git using the root `.gitignore`.

## 10. Important Concepts Learned

- SystemVerilog module declaration
- Input and output ports
- The `logic` data type
- Continuous assignment using `assign`
- Combinational logic
- Module instantiation
- Testbench development
- Simulation timing using `#10`
- Automated checking using `$fatal`
- Waveform generation using `$dumpfile` and `$dumpvars`
- RTL linting with Verilator
- Docker-based simulation and verification

## 11. Development Tools

| Tool | Purpose |
|---|---|
| Icarus Verilog | RTL compilation and simulation |
| Verilator | RTL linting |
| GTKWave | Digital waveform visualisation |
| noVNC | Browser access to GTKWave |
| Docker | Reproducible development environment |
| Make | Automation of simulation commands |

## 12. Next Steps

Extend this project by implementing:

- OR gate
- NOT gate
- XOR gate
- NAND gate
- NOR gate
- 2-to-1 multiplexer

Create a corresponding testbench for every new RTL module.

The next project will introduce arithmetic circuits, starting with a half adder and full adder.