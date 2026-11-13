
`timescale 1ns/1ps

module tb_uart_tx;

    localparam integer CLOCK_HZ = 1_000_000;
    localparam integer BAUD_RATE = 100_000;
    localparam integer BIT_NS = 10000;

    logic clk = 0;
    logic rst = 1;
    logic [7:0] tx_data = 0;
    logic tx_valid = 0;
    logic tx_serial;
    logic tx_ready;

    integer received_count = 0;
    reg [7:0] received;

    always #500 clk = ~clk; // 1 MHz

    uart_tx #(
        .CLOCK_HZ(CLOCK_HZ),
        .BAUD_RATE(BAUD_RATE)
    ) dut (
        .clk(clk),
        .rst(rst),
        .tx_data(tx_data),
        .tx_valid(tx_valid),
        .tx_serial(tx_serial),
        .tx_ready(tx_ready)
    );

    initial begin
        $dumpfile("build/uart_tx.vcd");
        $dumpvars(0, tb_uart_tx);
    end

    task automatic send_byte(input logic [7:0] value);
        begin
            wait(tx_ready);
            @(negedge clk);
            tx_data = value;
            tx_valid = 1;

            @(posedge clk);
            #1;
            tx_valid = 0;

            if (tx_ready)
                $fatal(1, "TX did not become busy");
        end
    endtask

    task automatic decode_byte(output reg [7:0] value);
        integer i;
        begin
            @(negedge tx_serial);
            #(BIT_NS / 2);

            if (tx_serial !== 0)
                $fatal(1, "Invalid start bit");

            for (i = 0; i < 8; i = i + 1) begin
                #BIT_NS;
                value[i] = tx_serial;
            end

            #BIT_NS;

            if (tx_serial !== 1)
                $fatal(1, "Invalid stop bit");
        end
    endtask

    // Serial receiver / scoreboard
    initial begin
        wait(!rst);

        repeat (3) begin
            decode_byte(received);

            case (received_count)
                0: if (received !== 8'h41)
                    $fatal(1, "Expected A");
                1: if (received !== 8'h55)
                    $fatal(1, "Expected U");
                2: if (received !== 8'h0A)
                    $fatal(1, "Expected LF");
            endcase

            received_count = received_count + 1;
        end
    end

    initial begin
        repeat (3) @(negedge clk);

        if (tx_serial !== 1)
            $fatal(1, "UART idle must be high");

        rst = 0;

        send_byte(8'h41); // A
        send_byte(8'h55); // U
        send_byte(8'h0A); // Newline

        wait(received_count == 3);
        wait(tx_ready);

        // Reset during transmission
        send_byte(8'hAA);

        repeat (3) @(negedge clk);
        rst = 1;

        repeat (2) @(negedge clk);

        if (tx_serial !== 1)
            $fatal(1, "UART not idle after reset");

        rst = 0;

        $display("PASS: UART transmitter");
        $finish;
    end

    initial begin
        #1000000;
        $fatal(1, "UART TX simulation timeout");
    end

endmodule
