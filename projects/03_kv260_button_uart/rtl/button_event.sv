module button_event (
    input  logic clk,
    input  logic rst,
    input  logic button_stable,
    output logic press_event,
    output logic release_event
);

    logic previous_state;

always_ff @(posedge clk) begin
        if (rst) begin
            previous_state <= 1'b0;
            press_event    <= 1'b0;
            release_event  <= 1'b0;
        end
        else begin
            press_event <=
                button_stable && !previous_state;

release_event <=
                !button_stable && previous_state;

previous_state <= button_stable;
        end
    end

endmodule