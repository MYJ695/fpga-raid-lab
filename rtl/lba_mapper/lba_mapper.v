// RAID0 LBA mapper.
//
// Pure combinational learning module: no clock, no reset, no handshake.
// It maps one logical LBA to a disk index plus disk-local LBA.

module lba_mapper #(
    parameter LBA_WIDTH   = 32,
    parameter DISK_COUNT  = 4,
    parameter CHUNK_SHIFT = 0
)(
    input  [LBA_WIDTH-1:0] lba,
    output [7:0]           disk_index,
    output [LBA_WIDTH-1:0] stripe_index,
    output [LBA_WIDTH-1:0] disk_lba
);

    wire [LBA_WIDTH-1:0] logical_chunk;
    wire [LBA_WIDTH-1:0] chunk_offset;

    assign logical_chunk = lba >> CHUNK_SHIFT;
    assign chunk_offset  = lba - (logical_chunk << CHUNK_SHIFT);

    assign disk_index   = logical_chunk % DISK_COUNT;
    assign stripe_index = logical_chunk / DISK_COUNT;
    assign disk_lba     = (stripe_index << CHUNK_SHIFT) + chunk_offset;

endmodule
