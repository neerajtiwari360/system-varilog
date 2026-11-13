`timescale 1ns/1ps

module tb_button_event;

logic clk = 0;
    logic rst = 1;
    logic button_stable = 0;
    logic press_event;
    logic release_event;

integer presses = 0;
    integer releases = 0;

    always #5 clk = ~clk;

button_event dut (
        .clk(clk),
        .rst(rst),
        .button_stable(button_stable),
        .press_event(press_event),
        .release_event(release_event)
    );

initial begin
        $dumpfile("build/button_event.vcd");
        $dumpvars(0, tb_button_event);
    end

always @(posedge clk) begin
        #1;

if (press_event && release_event)
            $fatal(1, "Both events asserted");

if (press_event)   presses = presses + 1;
        if (release_event) releases = releases + 1;
    end

task automatic wait_cycles(input integer n);
        repeat(n) @(negedge clk);
    endtask

initial begin
        wait_cycles(2);
        rst = 0;

// First press, long hold, release
        button_stable = 1;
        wait_cycles(8);

button_stable = 0;
        wait_cycles(5);

// Second press and release
        button_stable = 1;
        wait_cycles(4);

button_stable = 0;
        wait_cycles(4);

if (presses != 2 || releases != 2)
            $fatal(1,
                "Wrong event counts: press=%0d release=%0d",
                presses, releases);

// Reset while the button is held
        button_stable = 1;
        wait_cycles(3);

rst = 1;
        wait_cycles(2);

if (press_event || release_event)
            $fatal(1, "Events active during reset");

// Ensure test starts from a known low state
        button_stable = 0;
        rst = 0;
        wait_cycles(3);

$display("PASS: Button event detector");
        $finish;
    end

initial begin
        #10000;
        $fatal(1, "Button event simulation timeout");
    end

endmodule