PROJECT ?= 01_logic_gates
TOP ?= tb_registered_io_and
SYNTH_TOP ?= $(patsubst tb_%,%,$(TOP))

DIR = projects/$(PROJECT)
RTL = $(wildcard $(DIR)/rtl/*.sv)
TB = $(DIR)/tb/$(TOP).sv

.PHONY: test run lint synth clean

# Simulate (including VCD generation) and synthesize the same design.
run: test synth

test:
	mkdir -p $(DIR)/build
	cd $(DIR) && iverilog -g2012 \
		-s $(TOP) \
		-o build/sim.vvp \
		$(patsubst $(DIR)/%,%,$(RTL)) \
		tb/$(TOP).sv
	cd $(DIR) && vvp build/sim.vvp

lint:
	verilator --lint-only -Wall \
		--top-module $(SYNTH_TOP) $(RTL)

synth:
	mkdir -p $(DIR)/build
	yosys -l $(DIR)/build/$(SYNTH_TOP)_synth.log -p "read_verilog -sv $(RTL); synth -top $(SYNTH_TOP); stat; write_verilog -noattr $(DIR)/build/$(SYNTH_TOP)_netlist.v; show -format svg -prefix $(DIR)/build/$(SYNTH_TOP)_schematic $(SYNTH_TOP)"

clean:
	rm -rf $(DIR)/build/*
