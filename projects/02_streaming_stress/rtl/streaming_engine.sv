module stress_engine (
    input wire clk, rst,
    input wire in_valid,
    output wire in_ready,
    input wire [2:0] opcode,
    input wire [15:0] a, b,
    input wire [7:0] in_tag,
    output wire out_valid,
    input wire out_ready,
    output wire [31:0] out_data,
    output wire [7:0] out_tag,
    output wire [3:0] fifo_level
);
    wire [31:0] arithmetic_result;
    reg pending_valid;
    reg [39:0] pending_data;
    wire fifo_ready;
    wire pipeline_ready = !pending_valid || fifo_ready;
    assign in_ready = !rst && pipeline_ready;

    stress_alu alu(.opcode(opcode), .a(a), .b(b), .result(arithmetic_result));
    stress_fifo #(.WIDTH(40), .DEPTH(8)) queue (
        .clk(clk), .rst(rst), .in_valid(pending_valid), .in_ready(fifo_ready),
        .in_data(pending_data), .out_valid(out_valid), .out_ready(out_ready),
        .out_data({out_tag, out_data}), .level(fifo_level)
    );
    always @(posedge clk) begin
        if (rst) begin
            pending_valid <= 0;
            pending_data <= 0;
        end else if (pipeline_ready) begin
            pending_valid <= in_valid;
            if (in_valid)
                pending_data <= {in_tag, arithmetic_result};
        end
    end
endmodule
