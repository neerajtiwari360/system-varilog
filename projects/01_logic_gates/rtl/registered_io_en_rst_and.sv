module registered_io_en_rst_and (
    input  logic clk,
    input  logic rst,
    input  logic en,
    input  logic a,
    input  logic b,
    output logic y
);

    // Registered inputs and controls
    logic a_reg;
    logic b_reg;
    logic rst_reg;
    logic en_reg;

    // Stage 1: Register inputs and control signals
    always_ff @(posedge clk) begin
        a_reg   <= a;
        b_reg   <= b;
        rst_reg <= rst;
        en_reg  <= en;
    end

    // Stage 2: Registered AND output
    always_ff @(posedge clk) begin
        if (rst_reg)
            y <= 1'b0;
        else if (en_reg)
            y <= a_reg & b_reg;
    end

endmodule