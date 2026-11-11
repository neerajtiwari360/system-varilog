module stress_fifo #(
    parameter integer WIDTH = 40,
    parameter integer DEPTH = 8,
    parameter integer PTR_W = $clog2(DEPTH)
) (
    input wire clk, rst,
    input wire in_valid,
    output wire in_ready,
    input wire [WIDTH-1:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [WIDTH-1:0] out_data,
    output reg [PTR_W:0] level
);
    reg [WIDTH-1:0] storage [0:DEPTH-1];
    reg [PTR_W-1:0] write_ptr, read_ptr;
    wire pop = out_valid && out_ready;
    wire push = in_valid && in_ready;
    assign out_valid = !rst && (level != 0);
    assign in_ready = !rst && ((level < (PTR_W+1)'(DEPTH)) || pop);
    assign out_data = storage[read_ptr];

    always @(posedge clk) begin
        if (rst) begin
            write_ptr <= 0;
            read_ptr <= 0;
            level <= 0;
        end else begin
            if (push) begin
                storage[write_ptr] <= in_data;
                write_ptr <= (write_ptr == PTR_W'(DEPTH-1)) ? 0 : write_ptr + 1'b1;
            end
            if (pop)
                read_ptr <= (read_ptr == PTR_W'(DEPTH-1)) ? 0 : read_ptr + 1'b1;
            case ({push, pop})
                2'b10: level <= level + 1'b1;
                2'b01: level <= level - 1'b1;
                default: level <= level;
            endcase
        end
    end
endmodule
