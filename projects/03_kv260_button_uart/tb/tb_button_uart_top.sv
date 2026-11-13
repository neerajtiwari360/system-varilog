`timescale 1ns/1ps


module tb_button_uart_top;

// ==========================================
// 1. Simulation Parameters
// ==========================================

localparam integer CLOCK_HZ = 1_000_000;
localparam integer BAUD_RATE = 100_000;

localparam integer BIT_NS = 10000;
localparam integer DB_CYCLES = 4;

localparam integer EXPECTED_BYTES = 4;

// ==========================================
// 2. Signals
// ==========================================

logic clk = 0;
logic rst = 1;
logic button_in = 0;
logic uart_tx;

integer received_count = 0;
integer press_count = 0;
integer release_count = 0;

reg [7:0] received;
reg [7:0] expected [0:3];

// 1 MHz clock
always #500 clk = ~clk;

// ==========================================
// 3. Top-Level DUT
// ==========================================

button_uart_top #(
.CLOCK_HZ(CLOCK_HZ),
.BAUD_RATE(BAUD_RATE),
.DEBOUNCE_CYCLES(DB_CYCLES),
.EVENT_FIFO_DEPTH(4)
) dut (
.clk(clk),
.rst(rst),
.button_in(button_in),
.uart_tx(uart_tx)
);

// ==========================================
// 4. Waveform
// ==========================================

initial begin
$dumpfile("build/button_uart.vcd");
$dumpvars(0, tb_button_uart_top);

expected[0] = 8'h01;
expected[1] = 8'h00;
expected[2] = 8'h01;
expected[3] = 8'h00;
end

// ==========================================
// 5. Wait Task
// ==========================================

task automatic wait_cycles(input integer n);
repeat(n) @(negedge clk);
endtask

// ==========================================
// 6. Button Press with Bounce
// ==========================================

task automatic press_with_bounce;
begin
@(negedge clk);

#100 button_in = 1'b1;
#200 button_in = 1'b0;
#150 button_in = 1'b1;
#200 button_in = 1'b0;
#150 button_in = 1'b1;

// Remain pressed
wait_cycles(10);
end
endtask

// ==========================================
// 7. Button Release with Bounce
// ==========================================

task automatic release_with_bounce;
begin
@(negedge clk);

#100 button_in = 1'b0;
#200 button_in = 1'b1;
#150 button_in = 1'b0;
#200 button_in = 1'b1;
#150 button_in = 1'b0;

// Remain released
wait_cycles(10);
end
endtask

// ==========================================
// 8. UART Serial Decoder
// ==========================================

task automatic decode_uart(
output reg [7:0] value
);

integer bit_num;

begin
// Detect falling edge of start bit
@(negedge uart_tx);

// Sample middle of start bit
#(BIT_NS / 2);

if (uart_tx !== 1'b0)
$fatal(1, "Invalid UART start bit");

// Sample eight bits, LSB first
for (bit_num = 0;
bit_num < 8;
bit_num = bit_num + 1) begin

                #BIT_NS;

value[bit_num] = uart_tx;
            end

// Verify stop bit
            #BIT_NS;

if (uart_tx !== 1'b1)
                $fatal(1, "Invalid UART stop bit");
        end
    endtask

// ==========================================
    // 9. Serial Receiver / Scoreboard
    // ==========================================

    initial begin

        wait(!rst);

        forever begin

            decode_uart(received);

if (received_count >= EXPECTED_BYTES)
                $fatal(1, "Unexpected extra UART byte");

            if (received !== expected[received_count]) begin

$display(
                    "FAIL: Byte %0d expected=0x%02h got=0x%02h",
                    received_count,
                    expected[received_count],
                    received
                );

$fatal(1);
            end

$display(
                "PASS: UART byte %0d = 0x%02h",
                received_count,
                received
            );

            received_count = received_count + 1;

end
    end

// ==========================================
    // 10. Event Monitor
    // ==========================================

always @(posedge clk) begin
        #1;

        if (!rst) begin

if (dut.press_event &&
                dut.release_event)
                $fatal(1, "Simultaneous button events");

if (dut.press_event)
                press_count = press_count + 1;

if (dut.release_event)
                release_count = release_count + 1;

end
    end

// ==========================================
    // 11. Main Integration Test
    // ==========================================

    initial begin

        $display("Starting binary button UART test");

// Reset
        wait_cycles(4);

if (uart_tx !== 1'b1)
            $fatal(1, "UART idle must be high");

rst = 0;
        wait_cycles(4);

// First press and release
        press_with_bounce();
        release_with_bounce();

// Second press and release
        press_with_bounce();
        release_with_bounce();

// Wait until all bytes decoded
        wait(received_count == EXPECTED_BYTES);

// Allow time to detect unwanted bytes
        #(BIT_NS * 11);

// ======================================
        // 12. Final Checks
        // ======================================

if (received_count != EXPECTED_BYTES)
            $fatal(1, "Incorrect byte count");

if (press_count != 2)
            $fatal(1, "Expected 2 press events");

if (release_count != 2)
            $fatal(1, "Expected 2 release events");

if (dut.event_overflow)
            $fatal(1, "FIFO overflow detected");

if (dut.button_stable !== 1'b0)
            $fatal(1, "Button not released");

if (dut.tx_valid !== 1'b0)
            $fatal(1, "Event FIFO not empty");

if (dut.tx_ready !== 1'b1)
            $fatal(1, "UART not ready");

// ======================================
        // 13. Results
        // ======================================

$display("--------------------------------");
        $display("PASS: Synchronizer");
        $display("PASS: Debounce");
        $display("PASS: Button event detector");
        $display("PASS: Binary message controller");
        $display("PASS: UART transmitter");
        $display("PASS: Top-level integration");
        $display("--------------------------------");

$finish;
    end

// ==========================================
    // 14. Timeout
    // ==========================================

initial begin
        #1000000;
        $fatal(1, "Integration test timeout");
    end

endmodule






// `timescale 1ns/1ps

// module tb_button_uart_top;

//     localparam integer CLOCK_HZ = 1_000_000;
//     localparam integer BAUD_RATE = 100_000;
//     localparam integer BIT_NS = 10000;
//     localparam integer DB_CYCLES = 4;
//     localparam integer EXPECTED_BYTES = 38;

//     logic clk = 0;
//     logic rst = 1;
//     logic button_in = 0;
//     logic uart_tx;

//     integer received_count = 0;

//     reg [7:0] expected [0:EXPECTED_BYTES-1];
//     reg [7:0] received;

//     always #500 clk = ~clk;

//     button_uart_top #(
//         .CLOCK_HZ(CLOCK_HZ),
//         .BAUD_RATE(BAUD_RATE),
//         .DEBOUNCE_CYCLES(DB_CYCLES),
//         .EVENT_FIFO_DEPTH(4)
//     ) dut (
//         .clk(clk),
//         .rst(rst),
//         .button_in(button_in),
//         .uart_tx(uart_tx)
//     );

//     initial begin
//         $dumpfile("build/button_uart.vcd");
//         $dumpvars(0, tb_button_uart_top);

//         // PRESSED\r\n, RELEASED\r\n, repeated twice
//         expected[0] = "P";
//         expected[1] = "R";
//         expected[2] = "E";
//         expected[3] = "S";
//         expected[4] = "S";
//         expected[5] = "E";
//         expected[6] = "D";
//         expected[7] = 8'h0D;
//         expected[8] = 8'h0A;

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

//         for (integer i = 0; i < 19; i = i + 1)
//             expected[i+19] = expected[i];
//     end

//     task automatic wait_cycles(input integer n);
//         repeat (n) @(negedge clk);
//     endtask

//     // Simulate bouncing button press
//     task automatic press_with_bounce;
//         begin
//             @(negedge clk);
//             #100 button_in = 1;
//             #200 button_in = 0;
//             #150 button_in = 1;
//             #200 button_in = 0;
//             #150 button_in = 1;

//             // Stable press
//             wait_cycles(10);
//         end
//     endtask

//     // Simulate bouncing button release
//     task automatic release_with_bounce;
//         begin
//             @(negedge clk);
//             #100 button_in = 0;
//             #200 button_in = 1;
//             #150 button_in = 0;
//             #200 button_in = 1;
//             #150 button_in = 0;

//             // Stable release
//             wait_cycles(10);
//         end
//     endtask

//     // Decode one UART 8N1 frame
//     task automatic decode_uart(
//         output reg [7:0] value
//     );
//         integer bit_num;
//         begin
//             @(negedge uart_tx);

//             #(BIT_NS / 2);

//             if (uart_tx !== 0)
//                 $fatal(1, "Invalid UART start bit");

//             for (bit_num = 0; bit_num < 8;
//                  bit_num = bit_num + 1) begin

//                 #BIT_NS;
//                 value[bit_num] = uart_tx;
//             end

//             #BIT_NS;

//             if (uart_tx !== 1)
//                 $fatal(1, "Invalid UART stop bit");
//         end
//     endtask

//     // Serial scoreboard
//     initial begin
//         wait(!rst);

//         forever begin
//             decode_uart(received);

//             if (received_count >= EXPECTED_BYTES)
//                 $fatal(1, "Unexpected UART byte");

//             if (received !== expected[received_count]) begin
//                 $display(
//                     "FAIL byte %0d: expected=%h received=%h",
//                     received_count,
//                     expected[received_count],
//                     received
//                 );
//                 $fatal(1);
//             end

//             $display(
//                 "UART BYTE %0d: %h (%c)",
//                 received_count,
//                 received,
//                 received
//             );

//             received_count = received_count + 1;
//         end
//     end

//     initial begin
//         wait_cycles(4);

//         if (uart_tx !== 1)
//             $fatal(1, "UART idle not high");

//         rst = 0;
//         wait_cycles(4);

//         // First press/release
//         press_with_bounce();
//         release_with_bounce();

//         // Second press/release while UART is busy
//         press_with_bounce();
//         release_with_bounce();

//         // Wait for all four messages
//         wait(received_count == EXPECTED_BYTES);

//         // Leave enough time to detect an extra frame
//         #(BIT_NS * 11);

//         if (received_count != EXPECTED_BYTES)
//             $fatal(1, "Wrong UART byte count");

//         if (dut.event_overflow)
//             $fatal(1, "Event FIFO overflow");

//         if (dut.button_stable !== 0)
//             $fatal(1, "Button failed to return low");

//         $display("--------------------------------");
//         $display("PASS: Synchronizer");
//         $display("PASS: Debounce");
//         $display("PASS: Button events");
//         $display("PASS: UART TX");
//         $display("PASS: Message controller");
//         $display("PASS: Top-level integration");
//         $display("--------------------------------");

//         $finish;
//     end

//     initial begin
//         #10000000;
//         $fatal(1, "Integration simulation timeout");
//     end

// endmodule
