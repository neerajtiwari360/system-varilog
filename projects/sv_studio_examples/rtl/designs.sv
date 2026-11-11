module studio_and(input logic a, b, output logic y);
    assign y = a & b;
endmodule

module studio_registered_and(input logic clk, rst, en, a, b, output logic y);
    always_ff @(posedge clk)
        if (rst) y <= 0;
        else if (en) y <= a & b;
endmodule

module studio_counter(input logic clk, rst, en, output logic [3:0] count);
    always_ff @(posedge clk)
        if (rst) count <= 0;
        else if (en) count <= count + 1'b1;
endmodule
