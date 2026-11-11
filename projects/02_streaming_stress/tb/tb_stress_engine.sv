`timescale 1ns/1ps
module tb_stress_engine;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst = 1, in_valid = 0, out_ready = 0;
    reg [2:0] opcode = 0;
    reg [15:0] a = 0, b = 0;
    reg [7:0] in_tag = 0;
    wire in_ready, out_valid;
    wire [31:0] out_data;
    wire [7:0] out_tag;
    wire [3:0] fifo_level;
    stress_engine dut(.*);

    reg [31:0] expected_data [0:65535];
    reg [7:0] expected_tag [0:65535];
    integer head = 0, tail = 0;
    integer accepted = 0, checked = 0, discarded = 0;
    integer stalls = 0, full_cycles = 0, simultaneous = 0, reset_count = 0;
    integer coverage [0:7];
    integer cycles = 0;
    reg [31:0] random_state;
    reg was_stalled = 0;
    reg input_accepted = 0;
    reg [39:0] held_output;

    // Independent arithmetic model: multiplication is shift/add; rotations use bit indexing.
    function automatic [31:0] reference_result(input [2:0] op, input [15:0] x, y);
        reg [31:0] value;
        integer k;
        begin
            value = 0;
            case (op)
                0: value = {16'd0,x} + {16'd0,y};
                1: value = {16'd0,x} - {16'd0,y};
                2: for (k=0; k<16; k=k+1) value[k] = x[k] != y[k];
                3: for (k=0; k<16; k=k+1) begin value[k] = x[k] | y[k]; value[k+16] = x[k] & y[k]; end
                4: for (k=0; k<16; k=k+1) if (y[k]) value = value + ({16'd0,x} << k);
                5: value = {16'd0,x} * (32'd2 ** y[3:0]);
                6: value = {16'd0,x} / (32'd2 ** y[3:0]);
                7: for (k=0; k<16; k=k+1) value[(k+int'(y[3:0]))%16] = x[k];
            endcase
            reference_result = value;
        end
    endfunction

    task automatic next_random;
        begin
            random_state = random_state ^ (random_state << 13);
            random_state = random_state ^ (random_state >> 17);
            random_state = random_state ^ (random_state << 5);
        end
    endtask

    // Sample pre-edge handshakes, before the DUT's nonblocking register updates.
    always @(posedge clk) begin
        cycles = cycles + 1;
        if (rst) begin
            discarded = discarded + tail - head;
            head = 0; tail = 0; was_stalled = 0;
            input_accepted = 0;
            reset_count = reset_count + 1;
            if (out_valid !== 0 || in_ready !== 0) $fatal(1, "reset handshake not suppressed");
        end else begin
            input_accepted = in_valid && in_ready;
            if (was_stalled && ({out_tag,out_data} !== held_output || !out_valid))
                $fatal(1, "output changed while stalled at cycle %0d", cycles);
            if (fifo_level > 8) $fatal(1, "FIFO occupancy overflow");
            if (fifo_level == 8) full_cycles = full_cycles + 1;
            if (in_valid && !in_ready) stalls = stalls + 1;
            if (out_valid && out_ready) begin
                if (head == tail) $fatal(1, "unexpected output with empty scoreboard");
                if (out_data !== expected_data[head] || out_tag !== expected_tag[head])
                    $fatal(1, "scoreboard mismatch cycle=%0d index=%0d expected=%h/%h actual=%h/%h", cycles, head, expected_tag[head], expected_data[head], out_tag, out_data);
                head = head + 1; checked = checked + 1;
            end
            if (in_valid && in_ready) begin
                if (tail >= 65536) $fatal(1, "scoreboard capacity exhausted");
                expected_data[tail] = reference_result(opcode, a, b);
                expected_tag[tail] = in_tag;
                tail = tail + 1; accepted = accepted + 1;
                coverage[opcode] = coverage[opcode] + 1;
            end
            if (in_valid && in_ready && out_valid && out_ready) simultaneous = simultaneous + 1;
            was_stalled = out_valid && !out_ready;
            held_output = {out_tag,out_data};
        end
    end

    task automatic drive_cycle(input bit valid, ready, reset_signal, input [2:0] op, input [15:0] x, y);
        begin
            @(negedge clk);
            rst = reset_signal; out_ready = ready;
            // Producer holds its complete transaction until the consumer accepts it.
            if (reset_signal) begin in_valid = 0; end
            else if (!in_valid || input_accepted) begin
                in_valid = valid; opcode = op; a = x; b = y; in_tag = in_tag + 1'b1;
            end
        end
    endtask

    task automatic drain;
        integer guard_count;
        begin
            // Stop generating new inputs, but finish any already held transaction first.
            drive_cycle(0, 1, 0, 0, 0, 0);
            for (guard_count=0; guard_count<40; guard_count=guard_count+1)
                drive_cycle(0, 1, 0, 0, 0, 0);
            @(negedge clk);
            if (head != tail || out_valid || dut.pending_valid || fifo_level != 0)
                $fatal(1, "drain incomplete");
        end
    endtask

    initial begin : stimulus
        integer seed_index, i, op_index;
        for (i=0; i<8; i=i+1) coverage[i] = 0;
        $dumpfile("build/stress_engine.vcd");
        // Bound dump size: ports and pipeline/FIFO status, not the reference arrays.
        $dumpvars(0, clk, rst, in_valid, in_ready, opcode, a, b, in_tag,
                     out_valid, out_ready, out_data, out_tag, fifo_level,
                     dut.pending_valid, dut.pending_data);
        repeat (3) @(negedge clk);
        // Directed arithmetic corners, maximum shifts and every opcode.
        for (op_index=0; op_index<8; op_index=op_index+1) begin
            drive_cycle(1,1,0,3'(op_index),16'h0000,16'h0000);
            drive_cycle(1,1,0,3'(op_index),16'hffff,16'hffff);
            drive_cycle(1,1,0,3'(op_index),16'h8001,16'h000f);
            drive_cycle(1,1,0,3'(op_index),16'ha55a,16'h0001);
        end
        drain();
        for (seed_index=0; seed_index<3; seed_index=seed_index+1) begin
            case (seed_index)
                0: random_state = 32'h12345678;
                1: random_state = 32'hc001d00d;
                2: random_state = 32'hdeadbeef;
            endcase
            $display("SEED_START %0d %h", seed_index, random_state);
            for (i=0; i<6000; i=i+1) begin
                next_random();
                drive_cycle(random_state[0] | random_state[1],
                            (i%200 < 60) ? 1'b0 : random_state[2],
                            (i==901 || i==3001), random_state[5:3],
                            random_state[31:16], random_state[15:0]);
            end
            drain();
        end
        for (i=0; i<8; i=i+1) begin
            $display("OPCODE_COVERAGE %0d %0d", i, coverage[i]);
            if (coverage[i] < 100) $fatal(1, "insufficient opcode exercise");
        end
        if (checked < 4000 || stalls < 1000 || full_cycles < 1000 || simultaneous < 1000 || discarded == 0)
            $fatal(1, "insufficient stress coverage");
        if (accepted != checked + discarded) $fatal(1, "transaction accounting mismatch");
        $display("SUMMARY accepted=%0d checked=%0d discarded=%0d stalls=%0d full=%0d simultaneous=%0d resets=%0d cycles=%0d", accepted, checked, discarded, stalls, full_cycles, simultaneous, reset_count, cycles);
        $display("STRESS_ENGINE_ALL_CHECKS_COMPLETE");
        $finish;
    end
    initial begin #250000; $fatal(1, "watchdog timeout"); end
endmodule
