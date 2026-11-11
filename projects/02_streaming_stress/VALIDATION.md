# Streaming stress acceptance results

Verified on 11 November 2026 using the repository Docker services and Studio UI callbacks.

## Expected versus observed

| Check | Expected | Observed |
|---|---|---|
| RTL simulation | Completion marker, no scoreboard mismatches | Passed; 6,242 checked outputs |
| Accounting | accepted = checked + reset-discarded | 6,296 = 6,242 + 54 |
| Random stimulus | Three fixed seeds, 6,000 cycles each | All three completed |
| Backpressure | At least 1,000 stalled-input cycles | 9,738 |
| FIFO full | At least 1,000 full cycles, occupancy never >8 | 16,125; maximum occupancy 8 |
| Concurrent input/output | At least 1,000 simultaneous transfers | 5,269 |
| Reset | Pending transactions flushed and accounted for | 54 discarded; 10 sampled reset cycles |
| Native waveform | Actual transitions, occupancy reaches eight | 15 signals; 105,774 transitions; 182.03 us |
| Lint | No errors; intentional filename/module-name warning | One DECLFILENAME warning |
| Synthesis | Real hierarchical netlist; counts agree with Yosys | 3,130 generic leaf cells |
| Schematic | Nonempty actual Yosys/Graphviz SVG | Generated, parsed as SVG, opened in Studio dialog |
| Post-synthesis simulation | Same scoreboard and counters as RTL | Passed, identical summary |
| Negative control | Intentional $fatal must report Failed | Failed with the expected diagnostic |

## Opcode exercise

| Opcode | Accepted transactions |
|---|---|
| 0 | 784 |
| 1 | 795 |
| 2 | 813 |
| 3 | 810 |
| 4 | 811 |
| 5 | 779 |
| 6 | 751 |
| 7 | 753 |

## Generic cell counts

| Cell type | Count |
|---|---|
| `$_ANDNOT_` | 749 |
| `$_AND_` | 216 |
| `$_DFFE_PP_` | 320 |
| `$_MUX_` | 410 |
| `$_NAND_` | 148 |
| `$_NOR_` | 136 |
| `$_NOT_` | 113 |
| `$_ORNOT_` | 47 |
| `$_OR_` | 376 |
| `$_SDFFE_PP0P_` | 51 |
| `$_SDFF_PP0_` | 3 |
| `$_XNOR_` | 114 |
| `$_XOR_` | 447 |

Total: **3,130** generic leaf cells, including **374** flip-flop cells. These match Yosys's printed design-hierarchy totals. They are not KV260 LUT/FF/BRAM utilization or timing closure.

## Saved runs

| Operation | Run ID | Status |
|---|---|
| simulation | `2026-11-11T212525-816933+0000-791cf36c` | Passed |
| lint | `2026-11-11T212541-521883+0000-681932c1` | Warning |
| synthesis | `2026-11-11T212546-172761+0000-a3a336ce` | Passed |
| schematic | `2026-11-11T212559-489895+0000-d8b88e60` | Passed |
| expected_failure | `2026-11-11T212626-003738+0000-98e53f92` | Failed |

All run directories are under `build/sv_studio/02_streaming_stress/`.
The synthesis run also contains `post_synth_compile.log` and `post_synth_simulation.log`, with exact commands added to its metadata. Machine-readable acceptance evidence is in `build/stress_acceptance.json`.

## Fixes exposed by this test

* Hierarchical synthesis statistics previously omitted ALU/FIFO internals. Studio now counts instantiated leaf cells, including repeated instances; regression tests cover multiplicity and unused modules.
* The diagnostic counter previously counted Verilator's warning-help URL as another warning. It now counts the actual warning record while keeping full log text.

## Test scope and limitations

* Full acceptance: **1 passed** (real tool execution through NiceGUI simulated-client button events).
* Unit/UI suite: **28 passed**, with Docker tests opt-in and one Windows symlink test skipped.
* Four JavaScript drawing/interaction checks passed; the real stress VCD also produced native canvas drawing commands for 12 selected signals and the correct 182.03 us axis.
* VCD parsing, cursor/drawing logic, artifact generation, source selection and control callbacks were checked. Pixel-level browser interaction was not reverified; browser automation remains unavailable.
* The post-synthesis test is a zero-delay functional simulation. No FPGA mapping, placement, routing, clock constraints, timing closure or exhaustive formal proof was performed.
* The schematic shows the selected top with hierarchical submodule cells; it is not a flattened drawing of every internal gate.

## Source fingerprints

SHA-256 fingerprints of the tested project sources (excluding this report):

```text
1612921642a8aa2de9d926bc6630205663e6957296250a3803834bea9ce516c3  rtl/streaming_engine.sv
77e18b72aaa293b4fc3a307d4974cc965ad0237d05aa81b647bc8fe0d14f7368  rtl/stress_alu.sv
8b11ae92c947c003f295f6baeba1acdde62c8f062646959e9d53c17470833553  rtl/stress_fifo.sv
0081c53fcc62b27c5c645506153d2f503614e551f0b5d513ad5f3117efbda2a0  sv_studio.json
adc5ea5398adc1ac01a2b9e2ae32c6970d1a2eecab7c3491df89ff7047f1a5ad  tb/tb_stress_engine.sv
e518c350fb8fac9c22a5d6e015c4f555ff25456d6ff315b99bfbb47787b40fa0  tb/tb_stress_expected_failure.sv
```
