
module debounce #(
    parameter integer CLOCK_HZ = 100_000_000,
    parameter integer DEBOUNCE_MS = 20,
    parameter integer DEBOUNCE_CYCLES =
        (CLOCK_HZ / 1000) * DEBOUNCE_MS
)(
    input  logic clk,
    input  logic rst,
    input  logic button_sync,
    output logic button_stable
);

    localparam integer COUNTER_WIDTH =
        (DEBOUNCE_CYCLES <= 1) ? 1 :
        $clog2(DEBOUNCE_CYCLES);

    logic [COUNTER_WIDTH-1:0] counter;

    always_ff @(posedge clk) begin
        if (rst) begin
            counter       <= '0;
            button_stable <= 1'b0;
        end
        else if (button_sync == button_stable) begin
            counter <= '0;
        end
        else if (counter == DEBOUNCE_CYCLES - 1) begin
            button_stable <= button_sync;
            counter       <= '0;
        end
        else begin
            counter <= counter + 1'b1;
        end
    end

endmodule
