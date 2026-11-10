# SystemVerilog learning guide

For setup, simulation, waveforms, and synthesis, use the [root README](../README.md). This guide contains lessons and future learning goals; FPGA and ASIC target mapping are not part of the current generic synthesis command.

## 1. Learning Objectives

By completing this repository, I aim to:

- Understand fundamental digital logic and hardware design.

- Learn SystemVerilog syntax and synthesizable RTL.

- Understand combinational and sequential logic.

- Design clocked circuits, registers, counters, and state machines.

- Develop reusable hardware modules.

- Understand parallelism, pipelining, latency, and throughput.

- Implement fixed-point and INT8 arithmetic.

- Develop multiply-accumulate (MAC) architectures.

- Implement streaming image-processing pipelines.

- Build convolution, pooling, and activation hardware.

- Understand FPGA resources such as LUTs, flip-flops, DSPs, and BRAM.

- Learn simulation, linting, synthesis, timing analysis, and hardware verification.

- Implement an AI accelerator on FPGA and compare the same RTL against an ASIC standard-cell flow.

### Fundamental Principle: Think in Hardware, Not Software

In software, instructions execute according to program control flow.

In RTL, multiple circuits can operate **concurrently**.

For example:

```systemverilog

assign sum = a + b;

assign product = a * b;

```

These statements describe two independent combinational hardware operations that can occur simultaneously.

SystemVerilog describes hardware structure and behaviour. It is not simply another programming language executed instruction by instruction.

---

## 2. Learning Roadmap

### Stage 1 — Digital Logic and SystemVerilog Basics

**Goal:** Understand how basic hardware circuits are described.

Topics:

- Binary numbers and Boolean algebra

- AND, OR, NOT, XOR, NAND, NOR gates

- Multiplexers and decoders

- Modules and ports

- `logic`, `wire`, vectors, and bit widths

- Continuous assignments with `assign`

- `always_comb`

- Conditional statements and `case`

- Signed and unsigned arithmetic

- Basic testbenches and simulation

Practical projects:

- Logic gates

- Half adder

- Full adder

- 8-bit adder

- 2-to-1 multiplexer

### Stage 2 — Sequential Logic

**Goal:** Understand how hardware stores data and operates with clocks.

Topics:

- SR and D latches

- D flip-flops

- Clock signals and rising/falling edges

- Setup time and hold time

- Registers and shift registers

- Synchronous and asynchronous reset

- `always_ff`

- Blocking (`=`) versus nonblocking (`<=`) assignments

- Counters and clock enables

Practical projects:

- 8-bit register

- Shift register

- Binary counter

- Register with enable and reset

### Stage 3 — Hardware Architecture

**Goal:** Connect modules into larger hardware systems.

Topics:

- Hierarchical module design

- Finite-state machines (FSMs)

- Datapath versus control path

- Register-transfer operations

- Pipelines

- Latency and throughput

- FIFOs

- Memories and address generation

- Ready/valid handshakes

- Resource sharing versus parallel execution

- Basic clock-domain crossing concepts

Practical projects:

- Simple FSM controller

- FIFO buffer

- Pipelined arithmetic unit

- Streaming data interface

### Stage 4 — Arithmetic for AI/ML

**Goal:** Implement mathematical operations used by neural networks.

Topics:

- Binary arithmetic

- Signed two's-complement representation

- Fixed-point arithmetic

- INT8 and INT16 arithmetic

- Multiplication and division concepts

- Accumulators

- Multiply-accumulate (MAC) units

- Overflow and saturation

- Rounding

- Quantisation and scaling

- Parallel and pipelined MAC architectures

Practical projects:

- 8-bit multiplier

- Signed INT8 multiplier

- MAC unit

- Pipelined MAC unit

- Vector dot-product engine

### Stage 5 — Image Processing and CNN Operations

**Goal:** Build a streaming image-processing datapath.

Topics:

- Image pixel representation

- Row-major pixel streaming

- Line buffers

- Shift registers

- Sliding 3×3 windows

- 2D convolution

- Sobel edge detection

- ReLU activation

- Max pooling

- Data buffering and reuse

- Parallel pixel processing

Practical projects:

- 3×3 Sobel filter

- 2×2 max pooling

- ReLU module

- 3×3 INT8 convolution

- Streaming image-processing pipeline

### Stage 6 — FPGA AI Accelerator Development

**Goal:** Design, synthesise, and deploy a practical accelerator.

Topics:

- FPGA architecture

- LUTs and flip-flops

- DSP blocks

- BRAM and distributed RAM

- Resource utilisation

- Synthesis

- Static timing analysis

- Critical paths

- Clock constraints

- Timing closure

- AXI4-Stream and memory interfaces

- Parallel processing elements

- Systolic-array fundamentals

- Dataflow and memory bandwidth

- FPGA deployment and hardware validation

Practical projects:

- Parallel MAC array

- INT8 convolution engine

- Streaming CNN processing unit

- FPGA-hosted AI inference datapath

### Stage 7 — ASIC Physical Design Fundamentals

**Goal:** Understand how RTL becomes physical silicon.

Topics:

- RTL synthesis and gate-level netlists

- Standard-cell libraries

- Floorplanning

- Placement

- Clock-tree synthesis

- Routing

- Static timing analysis

- Power, performance, and area (PPA)

- Design-rule checking

- Layout-versus-schematic verification

- GDSII generation

Potential tools:

- Yosys

- OpenROAD

- OpenSTA

- KLayout

- Open-source standard-cell libraries

ASIC **logic synthesis begins in Stage 1 alongside FPGA LUT mapping**. Full physical design (floorplan, placement, clock tree, routing, GDSII) is introduced later after the RTL and verification foundations.

---

# Part I — SystemVerilog Fundamentals

## 5. Combinational vs Sequential Logic

Digital hardware can be divided into two important categories.

\| Property | Combinational Logic | Sequential Logic |

\|---|---|---|

\| Uses stored state | No | Yes |

\| Requires a clock | No | Usually, for synchronous designs |

\| Output depends on | Current inputs | Inputs and stored state |

\| Examples | Gates, adders, comparators | Registers, counters, FSMs |

\| Common RTL constructs | `assign`, `always_comb` | `always_ff` |

**Combinational example:**

```systemverilog

assign y = a & b;

```

The output responds to input changes after a propagation delay.

**Sequential example:**

```systemverilog

always_ff @(posedge clk) begin

    q <= d;

end

```

The register captures `d` on each rising clock edge and holds the stored value between edges.

A complete FPGA design normally combines both types of logic.

---

## 6. Lesson 1 — AND Gate

### Objective

Learn to define a module, declare signals, and describe combinational logic.

### SystemVerilog RTL

```systemverilog

module and_gate (

    input  logic a,

    input  logic b,

    output logic y

);

    assign y = a & b;

endmodule

```

### Understanding the Code

\| Code | Explanation |

\|---|---|

\| `module and_gate` | Begins the hardware module |

\| `input logic a` | Declares a one-bit input |

\| `input logic b` | Declares another one-bit input |

\| `output logic y` | Declares a one-bit output |

\| `assign` | Defines a continuous assignment |

\| `&` | Bitwise AND operator |

\| `endmodule` | Ends the module |

### Truth Table

\| A | B | Y |

\|---|---|---|

\| 0 | 0 | 0 |

\| 0 | 1 | 0 |

\| 1 | 0 | 0 |

\| 1 | 1 | 1 |

Boolean equation:

`Y = A & B`

### Hardware Interpretation

The synthesis tool can implement this module using an AND gate or an equivalent FPGA LUT configuration.

There is no clock or register in this design.

### Exercise

Modify the project to implement:

- OR gate

- XOR gate

- NAND gate

- NOR gate

For each gate, write a separate testbench and verify the complete truth table.

---

## 7. Lesson 2 — Parallel Hardware

### Objective

Understand that RTL describes circuits operating concurrently.

```systemverilog

module simple_math (

    input  logic [7:0] a, b,

    output logic [8:0] sum,

    output logic [7:0] and_result

);

    assign sum = {1'b0, a} + {1'b0, b};

    assign and_result = a & b;

endmodule

```

This describes:

- One 8-bit bitwise-AND datapath

- One adder with a 9-bit result

Both operations are evaluated concurrently.

### Key Concepts

`logic [7:0] a` represents eight bits.

The range `[7:0]` means the vector contains bit positions 7 through 0.

The addition uses zero extension to preserve the full unsigned result, including a possible carry-out bit.

### Hardware vs Software

In typical sequential Python code:

```python

total = a + b

masked = a & b

```

The statements are executed in program order.

In SystemVerilog, separate combinational assignments represent hardware that operates concurrently.

This distinction is essential when designing FPGA accelerators.

### Exercise

Implement a module that calculates all of the following simultaneously:

- A + B

- A - B

- A & B

- A ^ B

Verify the results with a testbench.

---

## 8. Lesson 3 — Clocked Registers

### Objective

Learn how digital hardware stores information.

```systemverilog

module register_example (

    input  logic       clk,

    input  logic [7:0] data_in,

    output logic [7:0] data_out

);

    always_ff @(posedge clk) begin

        data_out <= data_in;

    end

endmodule

```

### Understanding the Code

\| Code | Meaning |

\|---|---|

\| `clk` | Clock input |

\| `always_ff` | Describes clocked sequential behaviour |

\| `posedge clk` | Rising edge of the clock |

\| `<=` | Nonblocking assignment |

\| `data_in` | Input data |

\| `data_out` | Stored output |

### Example

Suppose the clock rises every 10 ns.

\| Time | Input | Stored Output |

\|---|---|---|

\| Before first edge | 5 | Previous or unknown value |

\| First rising edge | 5 | 5 |

\| Between edges | 7 | 5 |

\| Second rising edge | 7 | 7 |

Changing the input does not immediately update the stored output.

The output changes when a rising clock edge captures the input.

### Exercise

Implement:

- 8-bit register

- 8-bit register with reset

- 8-bit register with enable

- 8-bit shift register

Observe each module using GTKWave.

---

## 9. Lesson 4 — Multiply-Accumulate (MAC)

### Objective

Understand an essential arithmetic operation in neural networks.

A MAC computes:

`accumulator_next = accumulator_current + (A × B)`

Example:

- A = 3

- B = 4

- Previous accumulator = 10

- New accumulator = 22

MAC units are commonly used in:

- Matrix multiplication

- Convolutional neural networks

- Fully connected layers

- Digital signal processing

### Basic Sequential MAC Example

```systemverilog

module mac_example (

    input  logic clk,

    input  logic reset,

    input  logic signed [7:0] a,

    input  logic signed [7:0] b,

    output logic signed [31:0] accumulator

);

    logic signed [15:0] product;

    assign product = a * b;

    always_ff @(posedge clk) begin

        if (reset)

            accumulator <= 32'sd0;

        else

            accumulator <= accumulator

                         + {{16{product[15]}}, product};

    end

endmodule

```

The multiplier is combinational.

The accumulator is sequential and updates at each rising clock edge.

This example uses a 32-bit accumulator but does not implement saturation or overflow protection.

### Future Improvements

- Enable input

- Signed arithmetic verification

- Overflow handling

- Saturation

- Pipelining

- Multiple MAC units operating in parallel

---

# Part II — Building Toward AI Hardware

## 10. Practical Projects and AI Connections

\| Project | Hardware Concepts | AI/ML Connection |

\|---|---|---|

\| Logic gates | Boolean logic | Basic digital datapaths |

\| Adders | Arithmetic, carry propagation | Accumulation |

\| Registers and counters | Clocked storage | Pipeline stages and control |

\| Multipliers | Signed arithmetic, bit widths | Neural network multiplication |

\| MAC units | Multiplication and accumulation | CNN and dense layers |

\| Sobel filter | Sliding windows, line buffers | Image edge detection |

\| Max pooling | Comparators and buffering | CNN downsampling |

\| INT8 convolution | Parallel MAC operations | CNN inference |

\| CNN accelerator | Dataflow, control, memory | FPGA AI inference |

## 11. Understanding a CNN Accelerator

A convolutional layer performs many multiply-accumulate operations.

For a 3×3 kernel:

```text

Input window       Weights

P00 P01 P02        W00 W01 W02

P10 P11 P12        W10 W11 W12

P20 P21 P22        W20 W21 W22

```

The convolution result is:

`Y = Σ(Pij × Wij) + Bias`

A hardware implementation may use:

1. Pixel input interface

2. Line buffers

3. Sliding-window generator

4. MAC processing elements

5. Accumulation

6. Bias and quantisation

7. Activation

8. Output register or streaming interface

The learning projects in this repository progressively introduce these components.

---

## 12. Standard Development Workflow

Every project should follow the same process:

**1. Understand the hardware problem**

Define inputs, outputs, arithmetic, state, latency and throughput requirements.

**2. Draw the hardware architecture**

Identify combinational blocks, registers, memories and module connections.

**3. Write synthesizable RTL**

Implement the hardware module in SystemVerilog.

**4. Write a testbench**

Test expected results, edge cases and reset behaviour where applicable.

**5. Simulate**

Run the testbench using Icarus Verilog or a compatible simulator.

**6. Inspect the waveform**

Use GTKWave to understand signal transitions and clock-cycle behaviour.

**7. Run lint**

Check RTL style, suspicious constructs and potential design problems using Verilator.

**8. Run synthesis when appropriate**

Inspect the resulting hardware structure, resource usage and critical paths. Yosys is already available in the Docker simulation environment; compare generic FPGA LUT mapping and generic gate-level synthesis now. Device-specific FPGA implementation and ASIC physical design require additional tools and technology files.

**9. Document the project**

Record architecture, commands, tests, results and limitations in the project's README.

**10. Commit source files**

Commit RTL, testbenches, documentation and relevant configuration.

Do not commit generated build files.

---

## 13. Recommended Learning Resources

- [HDLBits](https://hdlbits.01xz.net/wiki/Main_Page) — digital logic and RTL practice exercises.

- [EDA Playground](https://www.edaplayground.com/) — browser-based HDL simulation.

- [Verilator Documentation](https://verilator.org/guide/latest/) — linting and simulation.

- [ChipVerify SystemVerilog Tutorial](https://www.chipverify.com/systemverilog/systemverilog-tutorial) — syntax and testbench concepts.

- [FPGA4Student](https://www.fpga4student.com/) — practical Verilog and FPGA projects.

- [Yosys Documentation](https://yosyshq.readthedocs.io/) — open-source RTL synthesis.

---

# Part III — Learning Progress Tracker

Use these checkboxes to track actual progress. Mark a task complete only after understanding the concept and verifying the hardware behaviour.

## Week 1 — SystemVerilog Basics

### Day 1 — Modules and Logic Gates

- [ ] Understand what an RTL module represents.

- [ ] Understand `input`, `output`, and `logic`.

- [x] Write an AND gate in SystemVerilog.

- [x] Write and execute its testbench.

- [x] Verify all four AND gate input combinations.

- [x] Generate and inspect the waveform in GTKWave.

- [ ] Complete lint checks without warnings.

- [ ] Implement OR and NOT gates.

### Day 2 — Vectors and Arithmetic

- [ ] Understand individual bits and vectors.

- [ ] Understand `[7:0]` notation.

- [ ] Learn unsigned and signed numbers.

- [ ] Implement an 8-bit adder.

- [ ] Understand arithmetic overflow.

- [ ] Verify addition with a testbench.

- [ ] Inspect waveforms.

### Day 3 — Combinational RTL

- [ ] Understand `assign`.

- [ ] Understand `always_comb`.

- [ ] Learn `if/else` and `case`.

- [ ] Implement a 2-to-1 multiplexer.

- [ ] Understand blocking assignments.

- [ ] Verify all multiplexer input combinations.

### Day 4 — Sequential RTL

- [ ] Understand clock signals.

- [ ] Understand rising and falling edges.

- [ ] Learn D flip-flop behaviour.

- [ ] Implement an 8-bit register.

- [ ] Learn `always_ff`.

- [ ] Understand nonblocking assignments.

- [ ] Implement reset and enable.

- [ ] Inspect register timing in GTKWave.

### Day 5 — Counters and FSMs

- [ ] Implement a 4-bit binary counter.

- [ ] Understand counter rollover.

- [ ] Understand state machines.

- [ ] Design a two-state FSM.

- [ ] Verify state transitions.

### Day 6 — Testbench and Waveform Skills

- [ ] Understand `initial` blocks.

- [ ] Learn `$display` and `$monitor`.

- [ ] Understand simulation delays.

- [ ] Learn `$dumpfile` and `$dumpvars`.

- [ ] Use `$fatal` for automated checks.

- [ ] Understand VCD waveforms.

- [ ] Identify clock-cycle boundaries.

### Day 7 — Arithmetic Mini-Project

- [ ] Implement an unsigned 8-bit multiplier.

- [ ] Understand the 16-bit product width.

- [ ] Add a register to capture the result.

- [ ] Write a self-checking testbench.

- [ ] Test edge cases.

- [ ] Inspect the waveform.

- [ ] Complete lint checks.

- [ ] Document the project.

---

## Stage 1 Completion Checklist — Digital Logic

- [ ] Logic gates

- [ ] Multiplexers

- [ ] Half adder

- [ ] Full adder

- [ ] 8-bit adder

- [ ] Signed and unsigned arithmetic

- [ ] `assign`

- [ ] `always_comb`

- [ ] Basic testbenches

- [ ] Waveform analysis

## Stage 2 Completion Checklist — Sequential Logic

- [ ] D flip-flop

- [ ] Register

- [ ] Shift register

- [ ] Clock enable

- [ ] Reset

- [ ] Binary counter

- [ ] `always_ff`

- [ ] Blocking vs nonblocking assignments

- [ ] Clock timing concepts

## Stage 3 Completion Checklist — Architecture

- [ ] FSM

- [ ] Datapath and control

- [ ] Pipelining

- [ ] Latency and throughput

- [ ] FIFO

- [ ] RAM interface

- [ ] Ready/valid handshake

- [ ] Module integration

## Stage 4 Completion Checklist — AI Arithmetic

- [ ] Signed INT8 multiplier

- [ ] Fixed-point representation

- [ ] Accumulator

- [ ] MAC unit

- [ ] Pipelined MAC

- [ ] Saturation and rounding

- [ ] Quantisation scaling

- [ ] Vector dot-product engine

## Stage 5 Completion Checklist — Image Processing

- [ ] Pixel streaming

- [ ] Line buffer

- [ ] Sliding 3×3 window

- [ ] Sobel gradient calculation

- [ ] Complete Sobel filter

- [ ] ReLU

- [ ] Max pooling

- [ ] INT8 convolution

## Stage 6 Completion Checklist — FPGA Acceleration

- [ ] Understand FPGA LUTs and flip-flops

- [ ] Understand DSP blocks

- [ ] Understand BRAM

- [ ] Learn RTL synthesis

- [ ] Analyse resource utilisation

- [ ] Understand timing constraints

- [ ] Learn static timing analysis

- [ ] Implement a parallel MAC architecture

- [ ] Integrate a streaming interface

- [ ] Deploy a design on an FPGA

- [ ] Compare hardware output with a Python reference

## Stage 7 Completion Checklist — ASIC Fundamentals

- [ ] RTL-to-gate synthesis

- [ ] Standard-cell libraries

- [ ] Floorplanning

- [ ] Placement

- [ ] Clock-tree synthesis

- [ ] Routing

- [ ] Static timing analysis

- [ ] DRC and LVS concepts

- [ ] GDSII generation

- [ ] Compare FPGA and ASIC implementation results

---

## Project Completion Template

For every new project, verify the following before marking it complete:

- [ ] Requirements understood

- [ ] Hardware block diagram drawn

- [ ] RTL implemented

- [ ] Testbench implemented

- [ ] Simulation passed

- [ ] Edge cases tested

- [ ] Waveforms inspected

- [ ] Lint passed

- [ ] Synthesis checked, if applicable

- [ ] Project README completed

- [ ] Source committed to Git

---


---

## 14. The Common Workflow

```text
                                RTL (*.sv)
                                   |
                              Icarus/Verilator
                         testbench + VCD waveform
                                   |
                              Yosys synthesis
                                   |
                  +----------------+----------------+
                  |                                 |
          FPGA learning path                 ASIC learning path
          generic LUT mapping                generic logic netlist
          (Yosys -lut 4)                     (Yosys synth)
                  |                                 |
           LUT truth table                  AND/OR/FF/etc. cells
           LUT resource count                generic gate count
                  |                                 |
       Target-specific FPGA tools          Liberty cell library +
       (later: place, route, STA)           technology mapping (later)
                  |                                 |
        Device-specific timing            OpenROAD/OpenSTA (later)
        resources and bitstream            place/route/timing/layout
```

**Remember:** Generic LUT counts and generic gate counts are educational, not a fair apples-to-apples performance or area comparison. Real FPGA timing needs a particular FPGA part, clock constraints, placement/routing and timing analysis. Real ASIC area/timing needs a chosen technology library, operating corner, constraints and implementation flow.

## 19. Study LUTs, Flip-Flops and Transistors as Three Distinct Levels

| Level | FPGA question | ASIC question | Current tools? |
|---|---|---|---|
| RTL behaviour | What should `A & B` do? | Same question | Yes: Icarus |
| Logic synthesis | How many generic LUTs/FFs? | What generic gates/FFs? | Yes: Yosys |
| Technology mapping | Which exact FPGA primitives? | Which Liberty cells? | FPGA: needs device flow; ASIC: needs `.lib` |
| Physical timing | Routed delays, max clock | Path delays at chosen library corner | Requires target-specific tools/constraints |
| Transistors | SRAM bits, mux tree, routing switches | CMOS NAND/AND/FF structures | Study schematics; SPICE optional |
| Real-world results | Hardware latency, throughput, power | Silicon measurement or qualified estimates | Not from current generic synthesis |

**Combinational AND** has no clock-cycle latency, but real gates and routing have non-zero propagation delay. **Registered AND** has a clocked capture and must meet setup/hold requirements. A testbench can check which clock edge captures data; it cannot establish the maximum safe clock frequency from generic behavioral simulation.

## 20. Compare Every New RTL Module in Two Flows

After each project reaches a verified testbench, repeat this checklist:

- [ ] Explain the Boolean function, input/output widths, and state.
- [ ] Run self-checking simulation and inspect VCD waveform.
- [ ] Run Verilator lint (if configured).
- [ ] Run generic FPGA 4-LUT mapping and record LUT/FF counts.
- [ ] Open the LUT mapping and explain its truth table/logic.
- [ ] Run generic ASIC-style gate synthesis and inspect the netlist.
- [ ] Draw the corresponding gate-level schematic.
- [ ] If a suitable Liberty library is configured, map real ASIC standard cells.
- [ ] State which timing figures are only simulation timing vs. actual implementation timing.
- [ ] Save findings and limitations in the project's README.

Use the following table in each project (fill only values actually observed):

| Metric | FPGA-style Yosys LUT mapping | Generic ASIC gates | Mapped ASIC cells (future) |
|---|---|---|---|
| RTL source | Same file | Same file | Same file |
| Functional test | Pass/fail | Same functional specification | Same functional specification |
| Logic cells | To measure | To measure | To measure |
| Flip-flops | To measure | To measure | To measure |
| Timing | Not established | Not established | Depends on library/corner/STA |
| Physical area | Not established | Not established | Estimate after technology mapping; improve after placement |
| Power | Not established | Not established | Requires activity and power models |
| Notes | Generic LUT only | Generic logic only | Specific standard-cell library required |

## 21. Side-by-Side Experiment Roadmap

| Project | FPGA learning question | ASIC learning question |
|---|---|---|
| AND / OR / XOR | Which LUT configuration implements each truth table? | Which gates implement the Boolean function? |
| 2:1 mux | Can a LUT implement selection? | How does it map to mux/gates? |
| D flip-flop / register | When is an FF inferred? | Which sequential cell implements storage? |
| Counter / adder | LUTs vs carry structure, register counts | Adder/logic/FF area and path delay |
| FSM | State encoding and LUT/FF cost | State encoding and standard-cell cost |
| FIFO / memory | Registers vs inferred block/distributed RAM | FF array vs SRAM macro and inference limits |
| INT8 MAC | DSP inference vs LUT-based arithmetic | Multiplier/adder standard cells or macros |
| Sobel | Line buffers, pipeline stages, routing | Gate count, timing, memories and layout |
| CNN accelerator | BRAM/DSP/LUT budget and throughput | Cell/macro area, timing and physical PPA |

**Progress gate:** Once the AND experiment is complete, do the **registered AND** variation (`always_ff @(posedge clk) y <= a & b;`) to observe how adding a clocked register changes both netlists. Follow with a 2:1 mux and a 4-bit counter before comparing large AI datapaths.

## Final Goal

Build and verify a practical **INT8 CNN accelerator architecture** using SystemVerilog.

Target capabilities:

- Streaming input data

- Fixed-point processing

- Multiple parallel MAC units

- Hardware convolution

- Activation and pooling

- Efficient on-chip buffering

- Configurable processing parameters

- Automated functional verification

- FPGA synthesis and timing analysis

- Real FPGA hardware deployment

The long-term goal is to develop the ability to design AI accelerators from first principles and understand how they map to both FPGA and ASIC hardware.

**Learning philosophy:**

Understand the logic → Draw the circuit → Write RTL → Write a testbench → Simulate → Inspect waveforms → Lint → Synthesise → Verify hardware.
