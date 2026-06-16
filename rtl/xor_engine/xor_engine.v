// Parameterized combinational XOR engine.
//
// This is intentionally tiny: no clock, no reset, no handshake.
// It matches the first RTL learning step in docs/fpga_architecture.md.

module xor_engine #(
    parameter WORD_WIDTH = 32,
    parameter INPUT_COUNT = 4
)(
    input  [WORD_WIDTH*INPUT_COUNT-1:0] data_in,
    output [WORD_WIDTH-1:0]             xor_out
);

    integer i;
    reg [WORD_WIDTH-1:0] acc;

    always @* begin
        acc = {WORD_WIDTH{1'b0}};
        for (i = 0; i < INPUT_COUNT; i = i + 1) begin
            acc = acc ^ data_in[i*WORD_WIDTH +: WORD_WIDTH];
        end
    end

    assign xor_out = acc;

endmodule
