
`timescale 1ns/1ps

module tb_debounce;

    localparam integer DB_CYCLES = 4;

    logic clk = 0;
    logic rst = 1;
    logic button_sync = 0;
    logic button_stable;

    integer transitions = 0;
    logic previous_stable = 0;

    always #5 clk = ~clk;

    debounce #(
        .DEBOUNCE_CYCLES(DB_CYCLES)
    ) dut (
        .clk(clk),
        .rst(rst),
        .button_sync(button_sync),
        .button_stable(button_stable)
    );

    initial begin
        $dumpfile("build/debounce.vcd");
        $dumpvars(0, tb_debounce);
    end

    // Compare actual stable output at every clock.
    always @(posedge clk) begin
        #1;

        if (!rst && button_stable !== previous_stable)
            transitions = transitions + 1;

        previous_stable = button_stable;
    end

    task automatic wait_cycles(input integer n);
        repeat(n) @(negedge clk);
    endtask

    task automatic check(input logic expected);
        if (button_stable !== expected) begin
            $display("FAIL debounce at %0t", $time);
            $fatal(1);
        end
    endtask

    initial begin
        $display("Testing debounce module");

        wait_cycles(3);
        check(0);
        rst = 0;

        // Short spurious pulse: must be rejected
        button_sync = 1;
        wait_cycles(2);
        button_sync = 0;
        wait_cycles(2);
        check(0);

        // Multiple rapid transitions
        button_sync = 1;
        wait_cycles(1);
        button_sync = 0;
        wait_cycles(1);
        button_sync = 1;
        wait_cycles(1);
        button_sync = 0;
        wait_cycles(1);
        check(0);

        // Stable press
        button_sync = 1;
        wait_cycles(DB_CYCLES + 1);
        check(1);

        // Short low glitch while pressed
        button_sync = 0;
        wait_cycles(2);
        button_sync = 1;
        wait_cycles(2);
        check(1);

        // Stable release
        button_sync = 0;
        wait_cycles(DB_CYCLES + 1);
        check(0);

        // Reset during debounce
        button_sync = 1;
        wait_cycles(2);
        rst = 1;
        wait_cycles(2);
        check(0);

        button_sync = 0;
        rst = 0;
        wait_cycles(2);
        check(0);

        if (transitions != 2)
            $fatal(1, "Expected 2 accepted transitions");

        $display("PASS: Debounce");
        $finish;
    end

    initial begin
        #10000;
        $fatal(1, "Debounce simulation timeout");
    end

endmodule
