`timescale 1ns/1ps

module tb_or_gate;

    logic a;
    logic b;
    logic y;

    // Connect testbench to actual AND gate
    or_gate dut (
        .a(a),
        .b(b),
        .y(y)
    );

    initial begin
        // Record waveforms
        $dumpfile("build/waves.vcd");
        $dumpvars(0, tb_or_gate);

        $display("Time  A  B  Y");

        a = 0; b = 0;
        #10;
        $display("%0t  %b  %b  %b", $time, a, b, y);
        if (y !== 0) $fatal(1, "FAILED: 0 OR 0");

        a = 0; b = 1;
        #10;
        $display("%0t  %b  %b  %b", $time, a, b, y);
        if (y !== 1) $fatal(1, "FAILED: 0 OR 1");

        a = 1; b = 0;
        #10;
        $display("%0t  %b  %b  %b", $time, a, b, y);
        if (y !== 1) $fatal(1, "FAILED: 1 OR 0");

        a = 1; b = 1;
        #10;
        $display("%0t  %b  %b  %b", $time, a, b, y);
        if (y !== 1) $fatal(1, "FAILED: 1 OR 1");

        $display("PASS: All OR gate tests passed");
        $finish;
    end

endmodule