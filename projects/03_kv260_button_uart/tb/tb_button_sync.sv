
`timescale 1ns/1ps

module tb_button_sync;

    // ==========================================
    // 1. Signals
    // ==========================================
    logic clk = 1'b0;
    logic rst = 1'b1;
    logic button_async = 1'b0;
    logic button_sync;

    // Reference model signals
    logic expected_ff1 = 1'b0;
    logic expected_ff2 = 1'b0;

    integer test_count = 0;

    // ==========================================
    // 2. Clock Generation
    // 100 MHz = 10 ns period
    // ==========================================
    always #5 clk = ~clk;

    // ==========================================
    // 3. DUT: Button Synchronizer
    // ==========================================
    button_sync dut (
        .clk          (clk),
        .rst          (rst),
        .button_async (button_async),
        .button_sync  (button_sync)
    );

    // ==========================================
    // 4. Waveform Generation
    // ==========================================
    initial begin
        $dumpfile("build/button_sync.vcd");
        $dumpvars(0, tb_button_sync);
    end

    // ==========================================
    // 5. Reference Model and Scoreboard
    // ==========================================
    // Matches the DUT's synchronous reset.
    // Non-blocking assignments model two FFs.

    always @(posedge clk) begin
        if (rst) begin
            expected_ff1 <= 1'b0;
            expected_ff2 <= 1'b0;
        end
        else begin
            expected_ff1 <= button_async;
            expected_ff2 <= expected_ff1;
        end

        // Wait for non-blocking updates to settle
        #1;

        if (button_sync !== expected_ff2) begin
            $display(
                "FAIL at %0t: expected=%b actual=%b",
                $time, expected_ff2, button_sync
            );
            $fatal(1);
        end

        test_count = test_count + 1;
    end

    // ==========================================
    // 6. Stimulus
    // ==========================================
    initial begin

        $display("Starting button synchronizer tests");

        // --------------------------------------
        // TEST 1: Reset
        // --------------------------------------
        $display("TEST 1: Reset");

        repeat (3) @(negedge clk);
        rst = 1'b0;

        repeat (3) @(negedge clk);

        // --------------------------------------
        // TEST 2: Clean Button Press
        // --------------------------------------
        $display("TEST 2: Clean button press");

        #2 button_async = 1'b1;

        repeat (5) @(negedge clk);

        // --------------------------------------
        // TEST 3: Clean Button Release
        // --------------------------------------
        $display("TEST 3: Clean button release");

        #2 button_async = 1'b0;

        repeat (5) @(negedge clk);

        // --------------------------------------
        // TEST 4: Mechanical Bounce on Press
        // --------------------------------------
        $display("TEST 4: Button press with bounce");

        #2  button_async = 1'b1;
        #3  button_async = 1'b0;
        #7  button_async = 1'b1;
        #12 button_async = 1'b0;
        #8  button_async = 1'b1;

        // Button remains pressed
        repeat (8) @(negedge clk);

        // --------------------------------------
        // TEST 5: Mechanical Bounce on Release
        // --------------------------------------
        $display("TEST 5: Button release with bounce");

        #2  button_async = 1'b0;
        #4  button_async = 1'b1;
        #6  button_async = 1'b0;
        #13 button_async = 1'b1;
        #7  button_async = 1'b0;

        // Button remains released
        repeat (8) @(negedge clk);

        // --------------------------------------
        // TEST 6: Short Glitch Between Edges
        // --------------------------------------
        $display("TEST 6: Short asynchronous glitch");

        #1 button_async = 1'b1;
        #2 button_async = 1'b0;

        repeat (4) @(negedge clk);

        // --------------------------------------
        // TEST 7: Reset While Button Pressed
        // --------------------------------------
        $display("TEST 7: Reset while pressed");

        #2 button_async = 1'b1;

        repeat (4) @(negedge clk);

        rst = 1'b1;

        repeat (3) @(negedge clk);

        rst = 1'b0;

        repeat (5) @(negedge clk);

        // Return to idle
        button_async = 1'b0;

        repeat (5) @(negedge clk);

        // --------------------------------------
        // TEST COMPLETE
        // --------------------------------------
        $display("--------------------------------");
        $display("PASS: All button synchronizer tests");
        $display("Checked clock cycles: %0d", test_count);
        $display("--------------------------------");

        $finish;
    end

    // Timeout protection
    initial begin
        #10000;
        $fatal(1, "FAIL: Simulation timeout");
    end

endmodule
