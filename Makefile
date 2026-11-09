PROJECT ?= 01_logic_gates
TOP ?= tb_or_gate
SYNTH_TOP ?= or_gate

DIR = projects/$(PROJECT)
RTL = $(wildcard $(DIR)/rtl/*.sv)
TB = $(DIR)/tb/$(TOP).sv

.PHONY: test lint synth clean

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
	yosys -p "read_verilog -sv $(RTL); synth -top $(SYNTH_TOP); stat; write_verilog -noattr $(DIR)/build/netlist.v; show -format svg -prefix $(DIR)/build/schematic"

clean:
	rm -rf $(DIR)/build/*