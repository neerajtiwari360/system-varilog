# Streaming arithmetic stress project

A three-module, synthesizable design for exercising SV Studio beyond individual
logic gates. It combines a 16-bit arithmetic datapath (including a 16x16 multiplier),
an elastic pipeline register, an eight-entry 40-bit FIFO, ready/valid backpressure,
transaction tags and synchronous reset. It is generic RTL, not a board-specific design.

## Run in SV Studio

Select project **02_streaming_stress**, RTL top **stress_engine**, and testbench
top **tb_stress_engine**. Keep the manifest's sources selected, then use Simulation,
Waveform, Lint, Synthesis and Generate schematic. The top is deliberately declared
in `rtl/streaming_engine.sv` to exercise module selection independently of filenames.
Verilator therefore reports one expected DECLFILENAME warning; it is not a functional failure.

The native waveform viewer displays the actual VCD, including the FIFO occupancy,
pipeline-valid flag, operands, operation, transaction tags, output and handshake signals.
During long backpressure intervals, occupancy should reach eight and output data/tag
must remain stable while `out_valid && !out_ready`.

## Operations

| Opcode | Result |
|---|---|
| 0 | Unsigned addition, extended to 32 bits |
| 1 | 32-bit wrapping subtraction of zero-extended operands |
| 2 | XOR, zero extended |
| 3 | `{a & b, a \| b}` |
| 4 | Full unsigned 16x16 product |
| 5 | Zero-extended `a` shifted left by `b[3:0]` |
| 6 | Zero-extended `a` shifted right by `b[3:0]` |
| 7 | 16-bit left rotation by `b[3:0]`, zero extended |

The producer holds an input transaction until it is accepted. Reset discards all
pending transactions. No output is consumed during reset. The scoreboard explicitly
accounts for transactions discarded by reset separately from checked outputs.

## Testbench checks

* Directed zero, maximum-value, alternating-bit and shift/rotation corners for all opcodes.
* Three reproducible xorshift seeds: `12345678`, `c001d00d`, `deadbeef`.
* 6,000 randomized stimulus cycles per seed, with bubbles and prolonged backpressure.
* Ordered data/tag scoreboard; independent shift/add multiplication and indexed rotation models.
* Output stability under stalls, occupancy <=8, FIFO-full exercise and simultaneous transfers.
* Mid-stream resets and complete queue drains, with transaction accounting.
* Every opcode accepted at least 100 times; at least 4,000 outputs checked and 1,000 stall/full/simultaneous cycles.
* A watchdog and `$fatal` on any mismatch or unmet coverage requirement.

PASS requires the final `STRESS_ENGINE_ALL_CHECKS_COMPLETE` marker. Merely executing
without a process error is not sufficient. This directed/random test is useful
regression evidence, not exhaustive formal verification or physical timing validation.

To verify failure reporting, select **tb_stress_expected_failure** instead. It
deliberately calls `$fatal` after 2 us; Studio must label that run **Failed**.
This is a negative control, not a hardware defect. Select the normal top afterward.

## Repeat the acceptance test

From repository PowerShell with Docker Desktop running:

```powershell
$env:SV_STUDIO_DOCKER_TESTS = '1'
.venv/Scripts/python.exe -m pytest sv_studio/tests/test_stress_project.py -q
```

The test clicks the Studio controls through NiceGUI's simulated client and executes
the real Docker tools. It validates the VCD, generated JSON/Verilog netlist and SVG,
then recompiles the synthesized netlist against the same scoreboard. It also runs
the intentional-failure top. Machine-readable evidence is saved to
`build/stress_acceptance.json`; each tool run retains its own logs and metadata.
Pixel-level browser inspection is separate from this automated acceptance test.

The normal testbench also follows the original Make filename convention:

```powershell
docker compose run --rm sim make run PROJECT=02_streaming_stress TOP=tb_stress_engine
```

The negative-control top depends on the main testbench and is intended for the
Studio manifest flow, which includes both files.
