PROJECT ?= 01_logic_gates
TOP ?= tb_and_gate

DIR = projects/$(PROJECT)
RTL = $(wildcard $(DIR)/rtl/*.sv)
TB = $(DIR)/tb/$(TOP).sv

.PHONY: test lint clean

test:
	mkdir -p $(DIR)/build
	cd $(DIR) && iverilog -g2012 \
		-s $(TOP) \
		-o build/sim.vvp \
		$(patsubst $(DIR)/%,%,$(RTL)) \
		tb/$(TOP).sv
	cd $(DIR) && vvp build/sim.vvp

lint:
	verilator --lint-only -Wall --top-module and_gate $(DIR)/rtl/and_gate.sv

clean:
	rm -rf $(DIR)/build/*