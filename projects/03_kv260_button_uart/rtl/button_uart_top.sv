
module button_uart_top #(
    parameter integer CLOCK_HZ = 100_000_000,
    parameter integer BAUD_RATE = 115200,
    parameter integer DEBOUNCE_MS = 20,
    parameter integer DEBOUNCE_CYCLES =
        (CLOCK_HZ / 1000) * DEBOUNCE_MS,
    parameter integer EVENT_FIFO_DEPTH = 4
)(
    input  logic clk,
    input  logic rst,
    input  logic button_in,
    output logic uart_tx
);

    logic button_sync_signal;
    logic button_stable;
    logic press_event;
    logic release_event;

    logic [7:0] tx_data;
    logic tx_valid;
    logic tx_ready;
    logic event_overflow;

    // Module 1: Synchronizer
    button_sync u_sync (
        .clk(clk),
        .rst(rst),
        .button_async(button_in),
        .button_sync(button_sync_signal)
    );

    // Module 2: Debounce
    debounce #(
        .CLOCK_HZ(CLOCK_HZ),
        .DEBOUNCE_MS(DEBOUNCE_MS),
        .DEBOUNCE_CYCLES(DEBOUNCE_CYCLES)
    ) u_debounce (
        .clk(clk),
        .rst(rst),
        .button_sync(button_sync_signal),
        .button_stable(button_stable)
    );

    // Module 3: Event Detection
    button_event u_event (
        .clk(clk),
        .rst(rst),
        .button_stable(button_stable),
        .press_event(press_event),
        .release_event(release_event)
    );

    // Module 5: ASCII Message Controller
    uart_message #(
        .FIFO_DEPTH(EVENT_FIFO_DEPTH)
    ) u_message (
        .clk(clk),
        .rst(rst),
        .press_event(press_event),
        .release_event(release_event),
        .tx_ready(tx_ready),
        .tx_data(tx_data),
        .tx_valid(tx_valid),
        .event_overflow(event_overflow)
    );

    // Module 4: UART Transmitter
    uart_tx #(
        .CLOCK_HZ(CLOCK_HZ),
        .BAUD_RATE(BAUD_RATE)
    ) u_uart_tx (
        .clk(clk),
        .rst(rst),
        .tx_data(tx_data),
        .tx_valid(tx_valid),
        .tx_serial(uart_tx),
        .tx_ready(tx_ready)
    );

endmodule
