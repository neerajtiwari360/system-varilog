# Project 02 — KV260 Push Button to UART using SystemVerilog

## 1. Project Overview

This project demonstrates a complete FPGA development workflow, starting with modular SystemVerilog RTL design and ending with deployment on the AMD/Xilinx Kria KV260 Vision AI Starter Kit.

### Project Objective

Connect an external push button to the KV260 FPGA and transmit its status to a laptop using UART serial communication.

**Expected behaviour:**

- When the button is pressed, transmit `PRESSED`.
- When the button is released, transmit `RELEASED`.
- Eliminate mechanical button bouncing.
- Synchronise the asynchronous button input to the FPGA clock.
- Use a UART transmitter implemented entirely in SystemVerilog.
- Verify all modules individually and as an integrated system.
- Generate and load the final FPGA bitstream.

### Development Strategy

The project uses two computers.

**Computer 1 — Windows laptop with Docker**

Used for:

1. RTL development
2. Testbench development
3. Functional simulation
4. Linting
5. Waveform analysis
6. Yosys synthesis
7. Netlist and schematic generation

**Computer 2 — Vivado 2025.2 ML Edition**

Used for:

1. KV260 hardware integration
2. Vivado synthesis
3. Placement and routing
4. Timing analysis
5. Bitstream generation
6. JTAG programming

**Important:** Yosys synthesis is used for early design verification and analysis. The original verified RTL will be transferred to Vivado for device-specific synthesis and implementation.

No Linux, PetaLinux or Yocto operating-system build is required for the intended standalone-PL UART implementation.

---

## 2. Hardware Requirements

| Hardware | Purpose |
|---|---|
| AMD/Xilinx KV260 | FPGA development board |
| External push button | Digital input |
| 10 kΩ resistor | Button pull-down |
| Jumper wires | Electrical connections |
| Breadboard | Button wiring |
| 3.3 V TTL USB-to-UART adapter | Serial output to laptop |
| Micro-USB cable | KV260 JTAG programming |
| KV260 power supply | Board power |

### Hardware Connections

The proposed design uses the KV260 J2 Pmod connector.

| Signal | Description |
|---|---|
| `button_in` | External button input |
| `uart_tx` | FPGA-generated UART output |
| `3.3V` | Button supply |
| `GND` | Common ground |

Before wiring:

- [ ] Confirm the official KV260 J2 Pmod pinout.
- [ ] Confirm signal-to-FPGA package-pin mappings.
- [ ] Confirm that the selected GPIO signals support the required 3.3 V logic standard.
- [ ] Use a suitable pull-down resistor.
- [ ] Ensure the USB-UART adapter uses 3.3 V signal levels.
- [ ] Connect the USB-UART ground to the KV260 ground.
- [ ] Do not apply 5 V or RS-232 voltages to FPGA GPIO.
- [ ] Confirm the selected board platform provides proper clocks, resets and cooling/fan control.

**Note:** Actual XDC package-pin assignments must be verified against the KV260 board files and hardware documentation before programming the FPGA.

---

## 3. Software and EDA Tools

### Computer 1 — Docker Development Environment

| Tool | Purpose |
|---|---|
| VS Code | RTL and testbench development |
| Docker | Isolated development environment |
| Docker Compose | Run development tools |
| Icarus Verilog | SystemVerilog simulation |
| Verilator | Linting and RTL checks |
| GTKWave | Waveform visualisation |
| Yosys | Logic synthesis |
| Graphviz | Netlist schematic generation |
| Make | Build and test automation |
| Python | Optional UART decoding and test-vector generation |

### Computer 2 — Vivado

| Tool | Purpose |
|---|---|
| Vivado 2025.2 ML Edition | FPGA implementation |
| Vivado Simulator | Optional secondary simulation |
| IP Integrator | KV260 processing-system and clock integration |
| Vivado Hardware Manager | JTAG programming |
| PuTTY / serial terminal | Display UART messages |

---

## 4. Project Directory Structure

```text
02_kv260_button_uart/
│
├── rtl/
│   ├── button_sync.sv
│   ├── debounce.sv
│   ├── button_event.sv
│   ├── uart_tx.sv
│   ├── uart_message.sv
│   └── button_uart_top.sv
│
├── tb/
│   ├── tb_button_sync.sv
│   ├── tb_debounce.sv
│   ├── tb_button_event.sv
│   ├── tb_uart_tx.sv
│   ├── tb_uart_message.sv
│   └── tb_button_uart_top.sv
│
├── constraints/
│   └── kv260.xdc
│
├── vivado/
│   └── build_kv260.tcl
│
├── scripts/
│   └── run_all_tests.sh
│
├── build/
│   ├── simulation/
│   ├── waves/
│   ├── synthesis/
│   └── reports/
│
├── Makefile
└── README.md
```

### Directory Guidelines

- `rtl/`: Synthesizable SystemVerilog modules.
- `tb/`: Simulation-only testbenches.
- `constraints/`: FPGA constraints.
- `vivado/`: Board-specific implementation scripts.
- `scripts/`: Test automation.
- `build/`: Generated outputs, ignored by Git.

Add this to `.gitignore`:

```gitignore
**/build/
*.vcd
*.vvp
*.fst
*.wdb
*.jou
*.log
.Xil/
*.cache/
*.runs/
*.sim/
*.hw/
```

Do not exclude important source, constraint or Vivado Tcl files from Git.

---

# PART A — SystemVerilog RTL Development

## 5. RTL Architecture

The complete data path is:

```text
External Push Button
         |
         v
+-------------------+
|  button_sync.sv   |
|  2-FF Synchronizer|
+-------------------+
         |
         v
+-------------------+
|    debounce.sv    |
|  Stable-state     |
|  filtering        |
+-------------------+
         |
         v
+-------------------+
|  button_event.sv  |
| Press / Release   |
| detection         |
+-------------------+
         |
         v
+-------------------+
|  uart_message.sv  |
| ASCII message     |
| controller        |
+-------------------+
         |
         v
+-------------------+
|     uart_tx.sv    |
| UART serialization|
+-------------------+
         |
         v
    FPGA UART TX
         |
         v
  USB-UART Adapter
         |
         v
   Laptop Terminal
```

All RTL blocks operate in the same FPGA clock domain after input synchronisation.

### Preliminary Design Parameters

| Parameter | Initial value |
|---|---|
| Target FPGA clock | 100 MHz |
| UART baud rate | 115200 |
| UART data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Button debounce duration | 20 ms |
| Button type | Active-high |
| Reset | Defined consistently across modules |

The 100 MHz clock is a design target, not an assumed KV260 default. Configure and verify the actual PL clock in Vivado.

---

## 6. Module 1 — Button Synchronizer

**File:** `rtl/button_sync.sv`

### Objective

Synchronise the external asynchronous push-button signal to the FPGA clock domain using a two-flip-flop synchronizer.

### Inputs

- `clk`
- `rst`
- `button_async`

### Output

- `button_sync`

### Implementation Tasks

- [ ] Create `button_sync.sv`.
- [ ] Implement two sequential flip-flops.
- [ ] Use non-blocking assignments.
- [ ] Define reset behaviour.
- [ ] Mark synchronizer registers appropriately for the target FPGA.
- [ ] Avoid combinational logic between the two synchronizer stages.

### Testbench

**File:** `tb/tb_button_sync.sv`

Test:

- [ ] Reset functionality.
- [ ] Button transitions from 0 to 1.
- [ ] Button transitions from 1 to 0.
- [ ] Correct two-stage propagation.
- [ ] Input transitions occurring between clock edges.

Simulation cannot prove that metastability never occurs. The synchronizer reduces metastability propagation risk in the physical design.

### Acceptance Criteria

- No unexpected output changes.
- Correct clock-domain sampling.
- Testbench completes with PASS.
- Synchronizer structure is preserved for FPGA implementation.

---

## 7. Module 2 — Button Debounce

**File:** `rtl/debounce.sv`

### Objective

Remove false transitions caused by mechanical switch bouncing.

The button state is accepted only after it remains stable for a configured number of clock cycles.

For a 100 MHz clock and 20 ms debounce interval:

```text
Clock frequency = 100,000,000 Hz

Debounce interval = 0.020 seconds

Counter threshold = 2,000,000 cycles
```

The debounce counter width must be sufficient to represent the configured threshold.

### Inputs

- `clk`
- `rst`
- `button_sync`

### Output

- `button_stable`

### Implementation Tasks

- [ ] Create `debounce.sv`.
- [ ] Add configurable clock-frequency and debounce-time parameters.
- [ ] Implement a counter.
- [ ] Reset the counter when the sampled input changes or returns to the accepted state, as required by the chosen algorithm.
- [ ] Change output only after the new level remains stable.
- [ ] Handle reset and counter limits correctly.

### Testbench

**File:** `tb/tb_debounce.sv`

Test:

- [ ] Short spurious input pulses.
- [ ] Multiple fast 0→1→0 transitions.
- [ ] Stable button press.
- [ ] Stable button release.
- [ ] Reset during debounce.
- [ ] Parameterised shorter debounce duration for faster simulation.

### Acceptance Criteria

- Only stable button changes are accepted.
- No false state changes during simulated bouncing.
- No counter overflow or width-related issues.

---

## 8. Module 3 — Button Event Detector

**File:** `rtl/button_event.sv`

### Objective

Detect rising and falling edges of the debounced button signal.

### Inputs

- `clk`
- `rst`
- `button_stable`

### Outputs

- `press_event`
- `release_event`

### Expected Behaviour

```text
0 → 1 : press_event = 1 for one clock

1 → 0 : release_event = 1 for one clock
```

### Implementation Tasks

- [ ] Create `button_event.sv`.
- [ ] Store the previous stable state.
- [ ] Implement rising-edge detection.
- [ ] Implement falling-edge detection.
- [ ] Generate one-cycle pulses.
- [ ] Ensure press and release events cannot occur simultaneously.

### Testbench

**File:** `tb/tb_button_event.sv`

Test:

- [ ] One press.
- [ ] One release.
- [ ] Multiple press/release cycles.
- [ ] Long button holds.
- [ ] Reset while the button is pressed.

### Acceptance Criteria

- Exactly one event per valid state transition.
- Events are one clock cycle wide.
- No repeated events while the button is held.

---

## 9. Module 4 — UART Transmitter

**File:** `rtl/uart_tx.sv`

### Objective

Transmit an 8-bit ASCII character over a UART TX line.

### UART Configuration

```text
Baud rate : 115200
Data bits : 8
Parity    : None
Stop bits : 1
Idle      : Logic 1
```

### UART Frame

```text
Idle | Start | D0 D1 D2 D3 D4 D5 D6 D7 | Stop
  1  |   0   |   8 data bits, LSB first  |  1
```

### Inputs

- `clk`
- `rst`
- `tx_data[7:0]`
- `tx_valid`

### Outputs

- `tx_serial`
- `tx_ready` or `tx_busy`

### Implementation Tasks

- [ ] Create `uart_tx.sv`.
- [ ] Implement a baud-rate counter.
- [ ] Implement start-bit generation.
- [ ] Transmit eight data bits in LSB-first order.
- [ ] Implement stop-bit generation.
- [ ] Keep the TX output high while idle.
- [ ] Implement a ready/valid or busy interface.
- [ ] Define behaviour if a new byte is requested while busy.

### Testbench

**File:** `tb/tb_uart_tx.sv`

Test:

- [ ] Idle level.
- [ ] Start-bit duration.
- [ ] Data-bit order.
- [ ] Stop-bit duration.
- [ ] Consecutive characters.
- [ ] Busy/ready behaviour.
- [ ] Reset during transmission.
- [ ] Baud timing within the expected integer-divider tolerance.

### Acceptance Criteria

- UART decoder in the testbench reconstructs the transmitted bytes correctly.
- No unexpected extra bits.
- Correct framing and timing.

---

## 10. Module 5 — UART Message Controller

**File:** `rtl/uart_message.sv`

### Objective

Convert button events into ASCII messages.

### Messages

```text
press_event:
PRESSED\r\n

release_event:
RELEASED\r\n
```

### Inputs

- `clk`
- `rst`
- `press_event`
- `release_event`
- `tx_ready`

### Outputs

- `tx_data[7:0]`
- `tx_valid`

### Implementation Tasks

- [ ] Create `uart_message.sv`.
- [ ] Implement a message controller or FSM.
- [ ] Store the required ASCII bytes as synthesizable constants.
- [ ] Send one byte at a time.
- [ ] Wait for UART readiness before advancing.
- [ ] Handle back-to-back button events safely.
- [ ] Choose and document an event-queue policy if UART is busy.
- [ ] Include CR/LF at the end of each message.

### Testbench

**File:** `tb/tb_uart_message.sv`

Test:

- [ ] Press message contents.
- [ ] Release message contents.
- [ ] Correct byte order.
- [ ] Valid/ready handshaking.
- [ ] Back-to-back events.
- [ ] Behaviour when UART is busy.
- [ ] Reset during message transmission.

### Acceptance Criteria

- Correct ASCII data is generated.
- No duplicated bytes.
- No silently lost events within the documented operating limits.

---

## 11. Module 6 — Top-Level Integration

**File:** `rtl/button_uart_top.sv`

### Objective

Connect all five previously verified modules into one complete design.

### External Signals

```text
clk
rst
button_in
uart_tx
```

The final clock and reset may be supplied by a Vivado wrapper containing the required Zynq UltraScale+ processing-system configuration.

### Implementation Tasks

- [ ] Create `button_uart_top.sv`.
- [ ] Instantiate button synchronizer.
- [ ] Instantiate debounce filter.
- [ ] Instantiate event detector.
- [ ] Instantiate message controller.
- [ ] Instantiate UART transmitter.
- [ ] Connect all control and data signals.
- [ ] Verify reset polarity and timing assumptions.
- [ ] Verify parameter propagation.
- [ ] Confirm no unintended multiple drivers or unconnected signals.

### Integration Testbench

**File:** `tb/tb_button_uart_top.sv`

Test the complete pipeline:

1. Apply reset.
2. Release reset.
3. Simulate a bouncing button press.
4. Hold the button pressed.
5. Verify only one `PRESSED` message.
6. Simulate a bouncing button release.
7. Verify only one `RELEASED` message.
8. Repeat the sequence.
9. Test rapid events and UART-busy behaviour.
10. Decode the serial waveform and compare exact ASCII bytes.

### Acceptance Criteria

```text
PASS: Synchronizer
PASS: Debounce
PASS: Button events
PASS: UART TX
PASS: Message controller
PASS: Top-level integration
```

---

# PART B — Docker Simulation and Verification

## 12. Simulation with Icarus Verilog

Run simulation from the project directory inside the Docker container.

Example:

```bash
mkdir -p build/simulation build/waves

iverilog -g2012 \
  -s tb_button_uart_top \
  -o build/simulation/button_uart.vvp \
  rtl/*.sv \
  tb/tb_button_uart_top.sv

vvp build/simulation/button_uart.vvp
```

The testbench should generate a waveform file:

```text
build/waves/button_uart.vcd
```

Use `$dumpfile` and `$dumpvars` in the testbench.

### Simulation Checklist

- [ ] Compilation successful.
- [ ] Testbench runs without errors.
- [ ] All checks pass.
- [ ] Waveform generated.
- [ ] Serial output decoded correctly.
- [ ] Simulation ends using `$finish`.

---

## 13. Waveform Analysis with GTKWave

Open:

```bash
gtkwave build/waves/button_uart.vcd
```

Inspect:

```text
clk
rst
button_in
button_sync
button_stable
press_event
release_event
tx_valid
tx_ready
tx_data
uart_tx
```

### Waveform Checklist

- [ ] Button input visibly changes.
- [ ] Synchronizer output responds after clock sampling.
- [ ] Debounce delays acceptance of a new state.
- [ ] Press event produces one pulse.
- [ ] Release event produces one pulse.
- [ ] UART starts with a logic-0 start bit.
- [ ] UART sends correct data bits.
- [ ] UART returns to logic-1 idle.

---

## 14. Lint with Verilator

Example:

```bash
verilator --lint-only -Wall \
  --top-module button_uart_top \
  rtl/*.sv
```

Check for:

- [ ] Missing signal declarations.
- [ ] Width mismatches.
- [ ] Unused or undriven signals.
- [ ] Unintended latches.
- [ ] Incorrect blocking/non-blocking assignment patterns.
- [ ] Multiple drivers.
- [ ] Unreachable states or suspicious logic.

Warnings must be reviewed rather than automatically ignored.

---

## 15. Synthesis with Yosys

### Generic Synthesis

```bash
mkdir -p build/synthesis

yosys -p "
  read_verilog -sv rtl/*.sv;
  synth -top button_uart_top;
  stat;
  write_verilog -noattr build/synthesis/netlist.v
"
```

### KV260-Oriented Primitive Mapping

The KV260 contains a Xilinx UltraScale+ device.

For experimental technology mapping:

```bash
yosys -p "
  read_verilog -sv rtl/*.sv;
  synth_xilinx -family xcup -top button_uart_top;
  stat;
  write_verilog -noattr build/synthesis/kv260_mapped.v
"
```

This maps logic toward UltraScale+ resources but **does not generate an FPGA bitstream**.

### Synthesis Checklist

- [ ] Yosys elaborates all RTL modules.
- [ ] Synthesis completes.
- [ ] No unintended latches.
- [ ] Inspect inferred flip-flops and counters.
- [ ] Review estimated logic resources.
- [ ] Generate netlist.
- [ ] Generate and inspect schematic.
- [ ] Investigate suspicious optimisation warnings.

The final KV260 implementation will use Vivado synthesis.

---

## 16. Makefile and Automation

The project should eventually support commands such as:

```bash
make test
make lint
make synth
make schematic
make clean
```

These are target names to implement in the project's `Makefile`, not commands assumed to exist already.

### Automation Goals

- [ ] Run individual module tests.
- [ ] Run all tests in one command.
- [ ] Stop on simulation failures.
- [ ] Generate per-module waveforms.
- [ ] Run Verilator lint.
- [ ] Generate Yosys netlists and statistics.
- [ ] Generate schematic files.
- [ ] Keep all generated files in `build/`.
- [ ] Return non-zero exit status when checks fail.

Your existing Docker Compose environment can call these Make targets once they are implemented.

---

# PART C — Vivado 2025.2 FPGA Implementation

## 17. Transfer Project to Computer 2

Transfer the following directories/files:

```text
rtl/
tb/
constraints/
vivado/
README.md
```

The `build/` directory is not required.

Use Git, USB storage or another suitable file-transfer method.

### Checklist

- [ ] RTL simulation passes before transfer.
- [ ] Lint passes.
- [ ] Yosys synthesis completes.
- [ ] Changes committed to Git.
- [ ] Vivado computer has the correct source revision.
- [ ] All required source files are included.

---

## 18. Create Vivado Project

Using Vivado 2025.2 ML Edition:

1. Create a new RTL project.
2. Select the KV260 board or exact supported device.
3. Add all synthesizable RTL files.
4. Add the validated XDC constraints.
5. Create the required hardware block design.
6. Generate the top-level wrapper.

### KV260-Specific Integration

The KV260 uses a Zynq UltraScale+ MPSoC.

The project must account for:

- Processing-system configuration.
- PL clock generation.
- Reset sequencing.
- Required board initialization.
- Safe fan/cooling control.
- External Pmod connections.

A simple approach is to use the configured Zynq PS to supply a PL clock and reset to the SystemVerilog design.

Linux is not required to run the PL UART design, but the PS must be correctly initialized when its clock/reset resources are used.

### Checklist

- [ ] Correct KV260 hardware target.
- [ ] Correct board preset.
- [ ] Clock configured.
- [ ] Reset configured.
- [ ] UART and button ports exposed.
- [ ] External pin constraints verified.
- [ ] Required fan/cooling provisions maintained.
- [ ] Block design validated.
- [ ] HDL wrapper generated.

---

## 19. Vivado Synthesis

Run:

```text
Flow Navigator → Run Synthesis
```

Check:

- [ ] Synthesis successful.
- [ ] No unresolved critical warnings.
- [ ] Resource utilisation reviewed.
- [ ] No unintended latches.
- [ ] Correct clock and reset connectivity.
- [ ] RTL hierarchy is correct.
- [ ] No unexpectedly undriven outputs.

---

## 20. Placement, Routing and Timing

Run:

```text
Flow Navigator → Run Implementation
```

Review:

- Worst Negative Slack (WNS).
- Worst Hold Slack (WHS).
- Timing violations.
- Unconstrained paths.
- Design Rule Checks (DRC).
- Placement and routing warnings.

### Acceptance Criteria

- [ ] Implementation completes.
- [ ] Setup timing meets requirements.
- [ ] Hold timing meets requirements.
- [ ] No unintended unconstrained paths.
- [ ] No unresolved critical DRC violations.
- [ ] Pmod I/O constraints are valid.

---

## 21. Generate Bitstream

Run:

```text
Flow Navigator → Generate Bitstream
```

### Checklist

- [ ] Bitstream generation successful.
- [ ] Final timing checks passed.
- [ ] Correct target device confirmed.
- [ ] Save `.bit` output.
- [ ] Save timing report.
- [ ] Save utilisation report.
- [ ] Record RTL Git commit used for the build.

The bitstream contains the implemented programmable-logic design.

---

# PART D — Physical KV260 Testing

## 22. Connect Hardware

Before powering the board:

- [ ] Verify push-button wiring.
- [ ] Verify pull-down resistor.
- [ ] Verify J2 connector orientation.
- [ ] Verify UART TX and GND connections.
- [ ] Confirm the adapter RX supports 3.3 V logic.
- [ ] Ensure no unintended 5 V connection.
- [ ] Confirm board cooling requirements.
- [ ] Connect the KV260 power supply.
- [ ] Connect JTAG to the Vivado computer.

Do not modify board connections while powered unless the interface explicitly supports hot-plugging.

---

## 23. Program KV260 via JTAG

In Vivado:

```text
Hardware Manager
    |
    v
Open Target
    |
    v
Auto Connect
    |
    v
Select Device
    |
    v
Program Device
    |
    v
Load .bit
```

### Important

If the design uses a PS-generated fabric clock, required PS configuration and initialization must occur before or as part of the programming/debug flow.

Loading a PL `.bit` file alone does not automatically guarantee the PS clocks and reset configuration are active.

### Checklist

- [ ] Board detected through JTAG.
- [ ] Required PS initialization completed.
- [ ] FPGA programmed successfully.
- [ ] Hardware clock and reset functioning.
- [ ] Fan/cooling functioning.
- [ ] No abnormal power or thermal behaviour.

---

## 24. Test UART Communication

Open PuTTY or another serial terminal on the computer connected to the external USB-UART adapter.

### Terminal Settings

```text
Baud rate  : 115200
Data bits  : 8
Parity     : None
Stop bits  : 1
Flow control: None
```

### Expected Output

```text
PRESSED
RELEASED
PRESSED
RELEASED
```

### Hardware Testing Checklist

- [ ] UART TX idles high.
- [ ] Pressing button sends `PRESSED`.
- [ ] Releasing button sends `RELEASED`.
- [ ] Holding button does not produce repeated messages.
- [ ] Mechanical bounce does not create extra events.
- [ ] Multiple button presses work.
- [ ] No corrupted UART characters.
- [ ] Reset and startup behaviour is correct.

---

# PART E — Final Acceptance and Future Improvements

## 25. Final Project Acceptance Criteria

The project is considered complete when:

- [ ] All RTL modules are implemented.
- [ ] All module testbenches pass.
- [ ] Top-level integration tests pass.
- [ ] Verilator lint is clean or warnings are documented.
- [ ] Yosys synthesis is successful.
- [ ] Netlists and schematics have been inspected.
- [ ] Vivado synthesis is successful.
- [ ] Place and route complete.
- [ ] Timing constraints are satisfied.
- [ ] Bitstream is successfully generated.
- [ ] KV260 is successfully programmed.
- [ ] Push-button input works on physical hardware.
- [ ] UART messages appear correctly in the serial terminal.
- [ ] Repository contains instructions to reproduce the complete workflow.

---

## 26. Future Improvements

After successful hardware testing:

- [ ] Add a parameter to configure the debounce interval.
- [ ] Add an event counter.
- [ ] Transmit the number of button presses.
- [ ] Add UART RX functionality.
- [ ] Implement a command-based UART interface.
- [ ] Add an AXI4-Lite register interface.
- [ ] Allow ARM processor software to read button state.
- [ ] Test communication using bare-metal C.
- [ ] Compare hardware UART with PS UART.
- [ ] Add an Integrated Logic Analyzer (ILA).
- [ ] Automate Vivado implementation with Tcl.
- [ ] Add CI tests for RTL simulation and linting.

---

## 27. Development Rules

Follow these rules throughout the project:

1. Implement one RTL module at a time.
2. Define the module's interface and expected behaviour before writing code.
3. Write a self-checking testbench for each significant module.
4. Do not modify the RTL simply to make an incorrect testbench pass.
5. Use one well-defined clock domain after button synchronisation.
6. Use non-blocking assignments for sequential registers.
7. Avoid unintended latches.
8. Make clock-dependent counters configurable.
9. Treat UART timing and data handshaking as part of the interface contract.
10. Keep simulation-only code outside synthesizable RTL.
11. Verify modules individually before system integration.
12. Keep generated files separate from source files.
13. Commit working milestones to Git.
14. Do not proceed to hardware programming until timing and board constraints are verified.
15. Preserve required KV260 hardware-infrastructure and cooling functionality.

---

## 28. Progress Tracker

### Phase 1 — RTL Development

- [ ] Module 1: Synchronizer
- [ ] Module 2: Debounce
- [ ] Module 3: Event detector
- [ ] Module 4: UART transmitter
- [ ] Module 5: UART message controller
- [ ] Module 6: Top-level integration

### Phase 2 — Verification

- [ ] Individual simulations
- [ ] Integration simulation
- [ ] Waveform verification
- [ ] Verilator lint
- [ ] Yosys generic synthesis
- [ ] Yosys UltraScale+ primitive mapping
- [ ] Schematic inspection

### Phase 3 — Vivado

- [ ] Create KV260 project
- [ ] Configure clock and reset
- [ ] Add and verify constraints
- [ ] Synthesis
- [ ] Implementation
- [ ] Timing analysis
- [ ] Generate bitstream

### Phase 4 — Board Deployment

- [ ] Connect physical hardware
- [ ] Initialize PS as required
- [ ] Program FPGA via JTAG
- [ ] Verify UART communication
- [ ] Complete hardware acceptance test

---

## 29. End Goal

Successfully build a complete modular SystemVerilog FPGA project using open-source development and verification tools, then implement and deploy it on the AMD/Xilinx KV260 using Vivado 2025.2 ML Edition.

**Final workflow:**

```text
SystemVerilog RTL
       |
       v
Icarus Verilog
       |
       v
Verilator
       |
       v
GTKWave
       |
       v
Yosys
       |
       v
Verified RTL
       |
       v
Vivado 2025.2
       |
       v
Synthesis
       |
       v
Placement & Routing
       |
       v
Timing Verification
       |
       v
Bitstream Generation
       |
       v
KV260 JTAG Programming
       |
       v
Physical Button Input
       |
       v
UART Serial Output
```

**Project status:** Not started

**Next task:** Implement `rtl/button_sync.sv` and `tb/tb_button_sync.sv`.