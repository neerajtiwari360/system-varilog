`timescale 1ns/1ps

module tb_registered_and;

    logic clk = 0;
    logic rst = 0;
    logic en  = 0;
    logic a   = 0;
    logic b   = 0;
    wire y;

    registered_and dut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .a(a),
        .b(b),
        .y(y)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("build/registered_and.vcd");
        $dumpvars(0, tb_registered_and);

        // Reset on first rising edge
        rst = 1;
        #6;
        if (y !== 0)
            $fatal(1, "Reset failed");

        // Enable AND operation
        rst = 0;
        en = 1;
        a = 1;
        b = 1;
        #10;
        if (y !== 1)
            $fatal(1, "AND operation failed");

        // Disable updates; output must hold 1
        en = 0;
        a = 0;
        #10;
        if (y !== 1)
            $fatal(1, "Clock enable hold failed");

        // Reset must override disabled enable
        rst = 1;
        #10;
        if (y !== 0)
            $fatal(1, "Reset priority failed");

        $display("PASS: Reset, enable and AND tests");
        $finish;
    end

endmodule