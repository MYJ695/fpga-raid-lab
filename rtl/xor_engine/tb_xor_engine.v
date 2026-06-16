`timescale 1ns/1ps

module tb_xor_engine;
    localparam WORD_WIDTH = 32;
    localparam INPUT_COUNT = 4;

    reg  [WORD_WIDTH*INPUT_COUNT-1:0] data_in;
    wire [WORD_WIDTH-1:0] xor_out;

    reg [WORD_WIDTH-1:0] in0;
    reg [WORD_WIDTH-1:0] in1;
    reg [WORD_WIDTH-1:0] in2;
    reg [WORD_WIDTH-1:0] in3;
    reg [WORD_WIDTH-1:0] expected;

    integer fd;
    integer rc;
    integer cases;
    integer errors;

    xor_engine #(
        .WORD_WIDTH(WORD_WIDTH),
        .INPUT_COUNT(INPUT_COUNT)
    ) dut (
        .data_in(data_in),
        .xor_out(xor_out)
    );

    initial begin
        cases = 0;
        errors = 0;
        fd = $fopen("rtl/xor_engine/vectors.txt", "r");
        if (fd == 0) begin
            $display("FAIL xor_engine: cannot open rtl/xor_engine/vectors.txt");
            $finish;
        end

        while (!$feof(fd)) begin
            rc = $fscanf(fd, "%h %h %h %h %h\n", in0, in1, in2, in3, expected);
            if (rc == 5) begin
                data_in = {in3, in2, in1, in0};
                #1;
                cases = cases + 1;
                if (xor_out !== expected) begin
                    errors = errors + 1;
                    $display("FAIL case %0d: %08h ^ %08h ^ %08h ^ %08h => got %08h expected %08h",
                             cases, in0, in1, in2, in3, xor_out, expected);
                end
            end
        end

        $fclose(fd);

        if (cases == 0) begin
            $display("FAIL xor_engine: no vector cases loaded");
            $finish_and_return(1);
        end else if (errors == 0) begin
            $display("PASS xor_engine cases=%0d", cases);
        end else begin
            $display("FAIL xor_engine cases=%0d errors=%0d", cases, errors);
            $finish_and_return(1);
        end
        $finish;
    end
endmodule
