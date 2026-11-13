
`timescale 1ns/1ps

module tb_uart_message;

    // ==========================================
    // 1. Signals
    // ==========================================

    logic clk = 0;
    logic rst = 1;

    logic press_event = 0;
    logic release_event = 0;

    logic tx_ready = 0;

    logic [7:0] tx_data;
    logic tx_valid;
    logic event_overflow;

    integer received_count = 0;
    integer cycle_count = 0;

    logic check_bytes = 1;

    reg [7:0] expected [0:3];

    // 100 MHz clock
    always #5 clk = ~clk;

    // ==========================================
    // 2. DUT
    // ==========================================

    uart_message #(
        .FIFO_DEPTH(4)
    ) dut (
        .clk(clk),
        .rst(rst),

        .press_event(press_event),
        .release_event(release_event),

        .tx_ready(tx_ready),

        .tx_data(tx_data),
        .tx_valid(tx_valid),
        .event_overflow(event_overflow)
    );

    // ==========================================
    // 3. Waveform
    // ==========================================

    initial begin
        $dumpfile("build/uart_message.vcd");
        $dumpvars(0, tb_uart_message);

        expected[0] = 8'h01; // Press
        expected[1] = 8'h00; // Release
        expected[2] = 8'h01; // Press
        expected[3] = 8'h00; // Release
    end

    // ==========================================
    // 4. Simulated UART Ready Signal
    // ==========================================

    // UART is ready once every 5 cycles.
    // This creates backpressure.

    always @(negedge clk) begin
        if (rst) begin
            cycle_count = 0;
            tx_ready = 0;
        end
        else begin
            cycle_count = cycle_count + 1;
            tx_ready = (cycle_count % 5 == 0);
        end
    end

    // ==========================================
    // 5. Scoreboard
    // ==========================================

    always @(posedge clk) begin

        if (!rst && tx_valid && tx_ready &&
            check_bytes) begin

            if (received_count >= 4)
                $fatal(1, "Unexpected extra byte");

            if (tx_data !== expected[received_count]) begin

                $display(
                    "FAIL: Byte %0d expected=%02h got=%02h",
                    received_count,
                    expected[received_count],
                    tx_data
                );

                $fatal(1);
            end

            $display(
                "PASS BYTE %0d: 0x%02h",
                received_count,
                tx_data
            );

            received_count = received_count + 1;
        end
    end

    // ==========================================
    // 6. Button Event Tasks
    // ==========================================

    task automatic issue_press;
        begin
            @(negedge clk);
            #1 press_event = 1'b1;

            @(negedge clk);
            #1 press_event = 1'b0;
        end
    endtask

    task automatic issue_release;
        begin
            @(negedge clk);
            #1 release_event = 1'b1;

            @(negedge clk);
            #1 release_event = 1'b0;
        end
    endtask

    // ==========================================
    // 7. Main Tests
    // ==========================================

    initial begin

        $display("Starting binary UART message tests");

        repeat (3) @(negedge clk);
        #1 rst = 0;

        // Test 1: Press
        issue_press();

        // Test 2: Release
        issue_release();

        // Test 3: Second press
        issue_press();

        // Test 4: Second release
        issue_release();

        // Wait for all expected bytes
        wait(received_count == 4);

        // Ensure no extra bytes appear
        repeat (10) @(negedge clk);

        if (received_count != 4)
            $fatal(1, "Incorrect number of bytes");

        if (event_overflow)
            $fatal(1, "Unexpected FIFO overflow");

        if (tx_valid)
            $fatal(1, "FIFO should be empty");

        $display("PASS: Four binary events received");

        // ======================================
        // 8. Reset During Pending Transmission
        // ======================================

        check_bytes = 0;

        // Force UART to remain busy
        // by keeping reset active briefly,
        // then controlling readiness separately
        // through the existing generator.

        issue_press();

        // Assert reset before consuming
        // the pending event.
        @(negedge clk);
        #1 rst = 1;

        repeat (2) @(negedge clk);

        if (tx_valid !== 0)
            $fatal(1, "tx_valid not cleared by reset");

        if (dut.count !== 0)
            $fatal(1, "FIFO not cleared by reset");

        if (event_overflow !== 0)
            $fatal(1, "Overflow flag not cleared");

        $display("PASS: Reset clears FIFO");

        $display("--------------------------------");
        $display("PASS: Binary UART message controller");
        $display("--------------------------------");

        $finish;
    end

    // ==========================================
    // 9. Timeout
    // ==========================================

    initial begin
        #100000;
        $fatal(1, "UART message test timeout");
    end

endmodule





// `timescale 1ns/1ps

// module tb_uart_message;

// logic clk = 0;
//     logic rst = 1;
//     logic press_event = 0;
//     logic release_event = 0;
//     logic tx_ready = 0;
//     logic [7:0] tx_data;
//     logic tx_valid;
//     logic event_overflow;

// integer cycle = 0;
//     integer received_count = 0;

//     reg [7:0] expected [0:27];

//     always #5 clk = ~clk;

// uart_message #(
//         .FIFO_DEPTH(4)
//     ) dut (
//         .clk(clk),
//         .rst(rst),
//         .press_event(press_event),
//         .release_event(release_event),
//         .tx_ready(tx_ready),
//         .tx_data(tx_data),
//         .tx_valid(tx_valid),
//         .event_overflow(event_overflow)
//     );

// initial begin
//         $dumpfile("build/waves/uart_message.vcd");
//         $dumpvars(0, tb_uart_message);

// // PRESSED\r\n
//         expected[0] = "P";
//         expected[1] = "R";
//         expected[2] = "E";
//         expected[3] = "S";
//         expected[4] = "S";
//         expected[5] = "E";
//         expected[6] = "D";
//         expected[7] = 8'h0D;
//         expected[8] = 8'h0A;

// // RELEASED\r\n
//         expected[9]  = "R";
//         expected[10] = "E";
//         expected[11] = "L";
//         expected[12] = "E";
//         expected[13] = "A";
//         expected[14] = "S";
//         expected[15] = "E";
//         expected[16] = "D";
//         expected[17] = 8'h0D;
//         expected[18] = 8'h0A;

// // PRESSED\r\n again
//         for (integer i = 0; i<9; i = i + 1)
//             expected[i+19] = expected[i];
//     end

// // Simulated UART backpressure
//     always @(negedge clk) begin
//         if (rst) begin
//             cycle = 0;
//             tx_ready = 0;
//         end
//         else begin
//             cycle = cycle + 1;
//             tx_ready = ((cycle % 4) == 0);
//         end
//     end

// // Check every accepted byte
//     always @(posedge clk) begin
//         if (!rst && tx_valid && tx_ready) begin
//             if (received_count >= 28)
//                 $fatal(1, "Unexpected extra byte");

// if (tx_data !== expected[received_count])
//                 $fatal(1,
//                     "Byte %0d expected %h got %h",
//                     received_count,
//                     expected[received_count],
//                     tx_data);

// received_count = received_count + 1;
//         end
//     end

// task automatic issue_press;
//         @(negedge clk);
//         press_event = 1;
//         @(negedge clk);
//         press_event = 0;
//     endtask

// task automatic issue_release;
//         @(negedge clk);
//         release_event = 1;
//         @(negedge clk);
//         release_event = 0;
//     endtask

// initial begin
//         repeat (3) @(negedge clk);
//         rst = 0;

// issue_press();
//         issue_release();
//         issue_press();

// wait(received_count == 28);
//         repeat (5) @(negedge clk);

// if (received_count != 28 || event_overflow)
//             $fatal(1, "Message controller failed");

// // Reset during a message
//         issue_press();
//         repeat (5) @(negedge clk);
//         rst = 1;
//         repeat (2) @(negedge clk);

// if (tx_valid !== 0)
//             $fatal(1, "TX valid not cleared by reset");

// $display("PASS: UART message controller");
//         $finish;
//     end

// initial begin
//         #100000;
//         $fatal(1, "UART message timeout");
//     end

// endmodule