module registered_and (
    input  logic clk,
    input  logic rst,
    input  logic en,
    input  logic a,
    input  logic b,
    output logic y
);

    always_ff @(posedge clk) begin
        if (rst)
            y <= 1'b0;
        else if (en)
            y <= a & b;
    end

endmodule
