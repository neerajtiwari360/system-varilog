module registered_io_and (
    input  logic clk,
    input  logic rst,
    input  logic a,
    input  logic b,
    output logic y
);

    logic a_reg;
    logic b_reg;

    always_ff @(posedge clk) begin
        if (rst) begin
            a_reg <= 1'b0;
            b_reg <= 1'b0;
            y     <= 1'b0;
        end
        else begin
            a_reg <= a;
            b_reg <= b;
            y     <= a_reg & b_reg;
        end
    end

endmodule
