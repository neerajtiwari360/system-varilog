`timescale 1ns/1ps

module tb_registered_io_and;

    logic clk = 0;
    logic rst = 1;
    logic a = 0;
    logic b = 0;
    logic y;

    logic [1:0] input_data [0:3];
    logic expected;

    always #5 clk = ~clk;

    registered_io_and dut (
        .clk(clk),
        .rst(rst),
        .a(a),
        .b(b),
        .y(y)
    );

    initial begin
        $dumpfile("build/registered_io_and.vcd");
        $dumpvars(0, tb_registered_io_and);

        $readmemb("tb/inputs.txt", input_data);

        repeat (2) @(posedge clk);

        @(negedge clk);
        rst = 0;

        for (int i = 0; i < 4; i++) begin

            @(negedge clk);
            {a, b} = input_data[i];

            expected = a & b;

            // First clock: capture inputs
            @(posedge clk);

            // Second clock: capture AND result
            @(posedge clk);
            #1;

            $display(
                "A=%b B=%b Expected=%b Actual=%b",
                a, b, expected, y
            );

            if (y !== expected)
                $fatal(1, "FAIL: AND output mismatch");
        end

        $display("PASS: All AND tests completed");

        $finish;
    end

endmodule