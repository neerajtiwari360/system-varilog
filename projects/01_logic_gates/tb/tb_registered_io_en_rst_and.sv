
`timescale 1ns/1ps

module tb_registered_io_en_rst_and;

    logic clk = 0;
    logic rst = 0;
    logic en  = 0;
    logic a   = 0;
    logic b   = 0;
    logic y;

    logic [1:0] input_data [0:3];
    logic expected;

    int errors = 0;

    // Clock period = 10 ns (100 MHz)
    always #5 clk = ~clk;

    // Device Under Test
    registered_io_en_rst_and dut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .a(a),
        .b(b),
        .y(y)
    );

    // Check output
    task automatic check_output(
        input logic expected_y
    );
        #1;

        if (y !== expected_y) begin
            $display(
                "FAIL: time=%0t expected=%b actual=%b",
                $time, expected_y, y
            );
            errors++;
        end
        else begin
            $display(
                "PASS: time=%0t A=%b B=%b RST=%b EN=%b Y=%b",
                $time, a, b, rst, en, y
            );
        end
    endtask

    initial begin

        $dumpfile("build/registered_io_en_rst_and.vcd");
        $dumpvars(0, tb_registered_io_en_rst_and);

        // Read input combinations
        $readmemb("tb/inputs.txt", input_data);

        // ---------------------------------
        // TEST 1: Synchronous reset
        // ---------------------------------

        $display("TEST 1: Reset");

        @(negedge clk);
        rst = 1;
        en  = 0;

        // First edge registers rst
        @(posedge clk);

        // Second edge applies reset to Y
        @(posedge clk);
        check_output(0);

        // ---------------------------------
        // TEST 2: AND truth table
        // ---------------------------------

        $display("TEST 2: AND truth table");

        @(negedge clk);
        rst = 0;
        en  = 1;

        // Wait for reset to be released
        @(posedge clk);
        @(negedge clk);

        for (int i = 0; i < 4; i++) begin

            {a, b} = input_data[i];
            expected = a & b;

            // Register inputs
            @(posedge clk);

            // Register AND output
            @(posedge clk);

            check_output(expected);

            @(negedge clk);
        end

        // ---------------------------------
        // TEST 3: Enable = 0
        // ---------------------------------

        $display("TEST 3: Enable hold");

        en = 0;
        a  = 0;
        b  = 0;

        // Register enable
        @(posedge clk);

        // Allow output to observe registered enable
        @(posedge clk);

        check_output(1);

        // ---------------------------------
        // TEST 4: Reset overrides enable
        // ---------------------------------

        $display("TEST 4: Reset priority");

        @(negedge clk);
        rst = 1;
        en  = 0;

        @(posedge clk);
        @(posedge clk);

        check_output(0);

        // ---------------------------------
        // Final result
        // ---------------------------------

        if (errors == 0)
            $display("PASS: All tests completed");
        else
            $fatal(1, "FAIL: %0d tests failed", errors);

        $finish;

    end

endmodule
