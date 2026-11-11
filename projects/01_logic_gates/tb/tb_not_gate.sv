
`timescale 1ns/1ps

module tb_not_gate;

    logic a;
    logic y;

    // Instantiate the Device Under Test
    not_gate dut (
        .a(a),
        .y(y)
    );

    initial begin
        // Generate waveform file
        $dumpfile("waves.vcd");
        $dumpvars(0, tb_not_gate);

        // Test 1: Input = 0
        a = 0;
        #10;

        assert (y === 1'b1)
            else $fatal(1, "FAIL: NOT(0) should be 1");

        $display("PASS: a=%b, y=%b", a, y);

        // Test 2: Input = 1
        a = 1;
        #10;

        assert (y === 1'b0)
            else $fatal(1, "FAIL: NOT(1) should be 0");

        $display("PASS: a=%b, y=%b", a, y);

        $display("All NOT gate tests PASSED!");
        $finish;
    end

endmodule
