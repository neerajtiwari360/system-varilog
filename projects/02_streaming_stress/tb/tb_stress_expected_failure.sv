`timescale 1ns/1ps
// Negative control: select this top to verify Studio reports runtime failure.
module tb_stress_expected_failure;
    tb_stress_engine stimulus();
    initial begin
        #2000;
        $fatal(1, "Intentional negative-control failure");
    end
endmodule
