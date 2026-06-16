`timescale 1ns/1ps

module tb_lba_mapper;
    localparam LBA_WIDTH   = 32;
    localparam DISK_COUNT  = 4;
    localparam CHUNK_SHIFT = 0;

    reg  [LBA_WIDTH-1:0] lba;
    wire [7:0]           disk_index;
    wire [LBA_WIDTH-1:0] stripe_index;
    wire [LBA_WIDTH-1:0] disk_lba;

    reg [31:0] in_lba;
    reg [31:0] exp_disk;
    reg [31:0] exp_stripe;
    reg [31:0] exp_disk_lba;

    integer fd;
    integer rc;
    integer cases;
    integer errors;

    lba_mapper #(
        .LBA_WIDTH(LBA_WIDTH),
        .DISK_COUNT(DISK_COUNT),
        .CHUNK_SHIFT(CHUNK_SHIFT)
    ) dut (
        .lba(lba),
        .disk_index(disk_index),
        .stripe_index(stripe_index),
        .disk_lba(disk_lba)
    );

    initial begin
        cases = 0;
        errors = 0;
        fd = $fopen("rtl/lba_mapper/vectors.txt", "r");
        if (fd == 0) begin
            $display("FAIL lba_mapper: cannot open rtl/lba_mapper/vectors.txt");
            $finish_and_return(1);
        end

        while (!$feof(fd)) begin
            rc = $fscanf(fd, "%d %d %d %d\n", in_lba, exp_disk, exp_stripe, exp_disk_lba);
            if (rc == 4) begin
                lba = in_lba[LBA_WIDTH-1:0];
                #1;
                cases = cases + 1;
                if (disk_index !== exp_disk[7:0] || stripe_index !== exp_stripe[LBA_WIDTH-1:0] || disk_lba !== exp_disk_lba[LBA_WIDTH-1:0]) begin
                    errors = errors + 1;
                    $display("FAIL case %0d: lba=%0d got disk=%0d stripe=%0d disk_lba=%0d expected disk=%0d stripe=%0d disk_lba=%0d",
                             cases, in_lba, disk_index, stripe_index, disk_lba, exp_disk, exp_stripe, exp_disk_lba);
                end
            end
        end

        $fclose(fd);
        if (cases == 0) begin
            $display("FAIL lba_mapper: no vector cases loaded");
            $finish_and_return(1);
        end else if (errors == 0) begin
            $display("PASS lba_mapper cases=%0d", cases);
        end else begin
            $display("FAIL lba_mapper cases=%0d errors=%0d", cases, errors);
            $finish_and_return(1);
        end
        $finish;
    end
endmodule
