
module uart_message #(
    parameter integer FIFO_DEPTH = 4
)(
    input  logic       clk,
    input  logic       rst,

    input  logic       press_event,
    input  logic       release_event,

    input  logic       tx_ready,

    output logic [7:0] tx_data,
    output logic       tx_valid,
    output logic       event_overflow
);

    // ==========================================
    // 1. FIFO Parameters
    // ==========================================

    localparam integer PW =
        (FIFO_DEPTH <= 1) ? 1 :
        $clog2(FIFO_DEPTH);

    localparam integer CW =
        $clog2(FIFO_DEPTH + 1);

    // ==========================================
    // 2. FIFO Storage
    // ==========================================

    // 1 = Press, 0 = Release
    logic fifo [0:FIFO_DEPTH-1];

    logic [PW-1:0] wr_ptr;
    logic [PW-1:0] rd_ptr;

    logic [CW-1:0] count;

    // ==========================================
    // 3. Event and Handshake Logic
    // ==========================================

    wire event_request =
        press_event ^ release_event;

    // Data is available when FIFO is not empty
    assign tx_valid = (count != 0) && !rst;

    // Convert 1-bit event into an 8-bit byte
    assign tx_data =
        tx_valid ?
        {7'b0000000, fifo[rd_ptr]} :
        8'h00;

    // UART accepts a byte at a rising clock edge
    // when both valid and ready are high.
    wire pop_event = tx_valid && tx_ready;

    // Accept new events if there is space,
    // or an existing event is being removed.
    wire push_event =
        event_request &&
        ((count < FIFO_DEPTH) || pop_event);

    // ==========================================
    // 4. Circular FIFO Pointer
    // ==========================================

    function automatic [PW-1:0] next_ptr(
        input [PW-1:0] ptr
    );
        if (ptr == FIFO_DEPTH-1)
            next_ptr = '0;
        else
            next_ptr = ptr + 1'b1;
    endfunction

    // ==========================================
    // 5. Sequential FIFO Control
    // ==========================================

    always_ff @(posedge clk) begin

        if (rst) begin
            wr_ptr         <= '0;
            rd_ptr         <= '0;
            count          <= '0;
            event_overflow <= 1'b0;
        end
        else begin

            // Store new button event
            if (push_event) begin
                fifo[wr_ptr] <= press_event;
                wr_ptr <= next_ptr(wr_ptr);
            end

            // Remove event accepted by UART
            if (pop_event) begin
                rd_ptr <= next_ptr(rd_ptr);
            end

            // Update FIFO occupancy
            case ({push_event, pop_event})

                2'b10: count <= count + 1'b1;

                2'b01: count <= count - 1'b1;

                default: count <= count;

            endcase

            // Sticky overflow / invalid-event flag
            if ((event_request && !push_event) ||
                (press_event && release_event)) begin

                event_overflow <= 1'b1;

            end
        end
    end

endmodule







// module uart_message #(
//     parameter integer FIFO_DEPTH = 4
// )(
//     input  logic       clk,
//     input  logic       rst,
//     input  logic       press_event,
//     input  logic       release_event,
//     input  logic       tx_ready,
//     output logic [7:0] tx_data,
//     output logic       tx_valid,
//     output logic       event_overflow
// );

// localparam integer PW =
//         (FIFO_DEPTH <= 1) ? 1 : $clog2(FIFO_DEPTH);

//     localparam integer CW = $clog2(FIFO_DEPTH + 1);

// // 1 = press, 0 = release
//     logic fifo [0:FIFO_DEPTH-1];
//     logic [PW-1:0] wr_ptr, rd_ptr;
//     logic [CW-1:0] count;

// logic message_kind;
//     logic [3:0] byte_index;

// typedef enum logic {
//         WAIT_EVENT, SEND_MESSAGE
//     } state_t;

//     state_t state;

// wire event_request = press_event ^ release_event;
//     wire pop_event =
//         (state == WAIT_EVENT) && (count != 0);

// wire push_event =
//         event_request &&
//         ((count < FIFO_DEPTH) || pop_event);

//     wire byte_accepted = tx_valid && tx_ready;

// function automatic [PW-1:0] next_ptr(
//         input [PW-1:0] ptr
//     );
//         if (ptr == FIFO_DEPTH-1)
//             next_ptr = '0;
//         else
//             next_ptr = ptr + 1'b1;
//     endfunction

// // ASCII message lookup
//     always_comb begin
//         tx_data = 8'h00;

// if (message_kind) begin
//             // PRESSED\r\n
//             case (byte_index)
//                 0: tx_data = "P";
//                 1: tx_data = "R";
//                 2: tx_data = "E";
//                 3: tx_data = "S";
//                 4: tx_data = "S";
//                 5: tx_data = "E";
//                 6: tx_data = "D";
//                 7: tx_data = 8'h0D;
//                 8: tx_data = 8'h0A;
//                 default: tx_data = 8'h00;
//             endcase
//         end
//         else begin
//             // RELEASED\r\n
//             case (byte_index)
//                 0: tx_data = "R";
//                 1: tx_data = "E";
//                 2: tx_data = "L";
//                 3: tx_data = "E";
//                 4: tx_data = "A";
//                 5: tx_data = "S";
//                 6: tx_data = "E";
//                 7: tx_data = "D";
//                 8: tx_data = 8'h0D;
//                 9: tx_data = 8'h0A;
//                 default: tx_data = 8'h00;
//             endcase
//         end
//     end

//     assign tx_valid = (state == SEND_MESSAGE) && !rst;

// always_ff @(posedge clk) begin
//         if (rst) begin
//             state          <= WAIT_EVENT;
//             wr_ptr         <= '0;
//             rd_ptr         <= '0;
//             count          <= '0;
//             byte_index     <= '0;
//             message_kind   <= 1'b0;
//             event_overflow <= 1'b0;
//         end
//         else begin

// // Enqueue incoming event
//             if (push_event) begin
//                 fifo[wr_ptr] <= press_event;
//                 wr_ptr <= next_ptr(wr_ptr);
//             end

// if (event_request && !push_event)
//                 event_overflow <= 1'b1;

// if (press_event && release_event)
//                 event_overflow <= 1'b1;

// // FIFO occupancy
//             case ({push_event, pop_event})
//                 2'b10: count <= count + 1'b1;
//                 2'b01: count <= count - 1'b1;
//                 default: count <= count;
//             endcase

// if (pop_event)
//                 rd_ptr <= next_ptr(rd_ptr);

//             case (state)

// WAIT_EVENT: begin
//                     byte_index <= '0;

// if (pop_event) begin
//                         message_kind <= fifo[rd_ptr];
//                         state <= SEND_MESSAGE;
//                     end
//                 end

// SEND_MESSAGE: begin
//                     if (byte_accepted) begin
//                         if ((message_kind &&
//                              byte_index == 8) ||
//                             (!message_kind &&
//                              byte_index == 9)) begin

// byte_index <= '0;
//                             state <= WAIT_EVENT;
//                         end
//                         else
//                             byte_index <= byte_index + 1'b1;
//                     end
//                 end

//                 default: state <= WAIT_EVENT;

// endcase
//         end
//     end

// endmodule