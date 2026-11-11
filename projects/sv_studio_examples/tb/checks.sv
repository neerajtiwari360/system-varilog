`timescale 1ns/1ps
module tb_studio_and;
    logic a, b;
    wire y;
    studio_and dut(.*);
    initial begin
        $dumpfile("build/and.vcd"); $dumpvars(0, tb_studio_and);
        for (int i=0; i<4; i++) begin
            {a,b}=i[1:0]; #1;
            if (y !== (a & b)) $fatal(1, "FAIL: AND");
        end
        $display("STUDIO_AND_COMPLETE"); $finish;
    end
endmodule

module tb_studio_registered_and;
    logic clk=0, rst=1, en=0, a=1, b=1;
    wire y;
    studio_registered_and dut(.*);
    always #5 clk=~clk;
    initial begin
        $dumpfile("build/registered.vcd"); $dumpvars(0, tb_studio_registered_and);
        @(posedge clk); #1; if (y !== 0) $fatal(1, "FAIL: reset");
        @(negedge clk); rst=0; en=1;
        @(posedge clk); #1; if (y !== 1) $fatal(1, "FAIL: update");
        @(negedge clk); en=0; a=0;
        @(posedge clk); #1; if (y !== 1) $fatal(1, "FAIL: hold");
        @(negedge clk); rst=1;
        @(posedge clk); #1; if (y !== 0) $fatal(1, "FAIL: reset priority");
        $display("STUDIO_REGISTERED_COMPLETE"); $finish;
    end
endmodule

module tb_studio_counter;
    logic clk=0, rst=1, en=0;
    wire [3:0] count;
    studio_counter dut(.*);
    always #5 clk=~clk;
    initial begin
        $dumpfile("build/counter.vcd"); $dumpvars(0, tb_studio_counter);
        @(posedge clk); #1; if (count !== 0) $fatal(1, "FAIL: reset");
        @(negedge clk); rst=0; en=1;
        for (int i=1; i<=18; i++) begin
            @(posedge clk); #1; if (count !== (i % 16)) $fatal(1, "FAIL: count");
        end
        @(negedge clk); en=0;
        @(posedge clk); #1; if (count !== 2) $fatal(1, "FAIL: hold");
        $display("STUDIO_COUNTER_COMPLETE"); $finish;
    end
endmodule
