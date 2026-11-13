
module uart_tx #(
    parameter integer CLOCK_HZ = 100_000_000,
    parameter integer BAUD_RATE = 115200
)(
    input  logic       clk,
    input  logic       rst,
    input  logic [7:0] tx_data,
    input  logic       tx_valid,
    output logic       tx_serial,
    output logic       tx_ready
);

    localparam integer CLKS_PER_BIT =
        (CLOCK_HZ + BAUD_RATE / 2) / BAUD_RATE;

    localparam integer CW =
        (CLKS_PER_BIT <= 1) ? 1 :
        $clog2(CLKS_PER_BIT);

    typedef enum logic [1:0] {
        IDLE, START_BIT, DATA_BITS, STOP_BIT
    } state_t;

    state_t state;

    logic [CW-1:0] baud_counter;
    logic [2:0] bit_index;
    logic [7:0] data_reg;

    assign tx_ready = (state == IDLE) && !rst;

    always_comb begin
        case (state)
            START_BIT: tx_serial = 1'b0;
            DATA_BITS: tx_serial = data_reg[bit_index];
            default:   tx_serial = 1'b1;
        endcase
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            state        <= IDLE;
            baud_counter <= '0;
            bit_index    <= '0;
            data_reg     <= '0;
        end
        else begin
            case (state)

                IDLE: begin
                    baud_counter <= '0;
                    bit_index    <= '0;

                    if (tx_valid && tx_ready) begin
                        data_reg <= tx_data;
                        state    <= START_BIT;
                    end
                end

                START_BIT: begin
                    if (baud_counter == CLKS_PER_BIT-1) begin
                        baud_counter <= '0;
                        state <= DATA_BITS;
                    end
                    else
                        baud_counter <= baud_counter + 1'b1;
                end

                DATA_BITS: begin
                    if (baud_counter == CLKS_PER_BIT-1) begin
                        baud_counter <= '0;

                        if (bit_index == 3'd7) begin
                            state <= STOP_BIT;
                        end
                        else
                            bit_index <= bit_index + 1'b1;
                    end
                    else
                        baud_counter <= baud_counter + 1'b1;
                end

                STOP_BIT: begin
                    if (baud_counter == CLKS_PER_BIT-1) begin
                        baud_counter <= '0;
                        state <= IDLE;
                    end
                    else
                        baud_counter <= baud_counter + 1'b1;
                end

                default: state <= IDLE;

            endcase
        end
    end

endmodule
