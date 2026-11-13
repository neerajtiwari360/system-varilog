
module button_sync (
    input  logic clk,
    input  logic rst,
    input  logic button_async,
    output logic button_sync
);

    // Two-stage synchronizer
    // Xilinx Vivado attribute to identify CDC registers
    (* ASYNC_REG = "TRUE" *) logic sync_ff1;
    (* ASYNC_REG = "TRUE" *) logic sync_ff2;

    always_ff @(posedge clk) begin
        if (rst) begin
            sync_ff1 <= 1'b0;
            sync_ff2 <= 1'b0;
        end
        else begin
            sync_ff1 <= button_async;
            sync_ff2 <= sync_ff1;
        end
    end

    assign button_sync = sync_ff2;

endmodule
