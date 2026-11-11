// Combinational arithmetic datapath. Filename and module names are independent.
module stress_alu (
    input wire [2:0] opcode,
    input wire [15:0] a, b,
    output reg [31:0] result
);
    reg [15:0] rotated;
    always_comb begin
        rotated = (a << b[3:0]) | (a >> (5'd16 - {1'b0, b[3:0]}));
        case (opcode)
            3'd0: result = {16'd0, a} + {16'd0, b};
            3'd1: result = {16'd0, a} - {16'd0, b};
            3'd2: result = {16'd0, a ^ b};
            3'd3: result = {a & b, a | b};
            3'd4: result = a * b;
            3'd5: result = {16'd0, a} << b[3:0];
            3'd6: result = {16'd0, a} >> b[3:0];
            3'd7: result = {16'd0, rotated};
            default: result = 32'd0;
        endcase
    end
endmodule
