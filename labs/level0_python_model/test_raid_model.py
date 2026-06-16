import pytest

from raid_model import DiskFailedError, RAID0, RAID1, RAID5, VirtualDisk, xor_blocks


def disks(count, blocks=4, block_size=4):
    return [VirtualDisk(blocks, block_size, name=f"d{i}") for i in range(count)]


def test_virtual_disk_read_write_and_failure():
    disk = VirtualDisk(block_count=2, block_size=4, name="tiny")
    disk.write(0, b"ABCD")
    assert disk.read(0) == b"ABCD"
    with pytest.raises(ValueError):
        disk.write(1, b"TOO-LONG")
    disk.fail()
    with pytest.raises(DiskFailedError):
        disk.read(0)


def test_xor_blocks_round_trip_property():
    a = b"ABCD"
    b = b"\x10\x20\x30\x40"
    parity = xor_blocks([a, b])
    assert xor_blocks([a, parity]) == b
    assert xor_blocks([b, parity]) == a


def test_raid0_stripes_logical_blocks_across_disks():
    raid = RAID0(disks(2, blocks=3))
    raid.write(0, b"A000")
    raid.write(1, b"B111")
    raid.write(2, b"C222")

    assert raid.map_lba(0) == (0, 0)
    assert raid.map_lba(1) == (1, 0)
    assert raid.map_lba(2) == (0, 1)
    assert raid.read(0) == b"A000"
    assert raid.read(1) == b"B111"
    assert raid.read(2) == b"C222"


def test_raid1_reads_from_surviving_mirror():
    ds = disks(2, blocks=2)
    raid = RAID1(ds)
    raid.write(0, b"MIRR")

    ds[0].fail()
    assert raid.read(0) == b"MIRR"

    ds[1].fail()
    with pytest.raises(DiskFailedError):
        raid.read(0)


def test_raid5_layout_rotates_parity():
    raid = RAID5(disks(4, blocks=3))
    assert raid.layout_row(0) == ["P", "D0", "D1", "D2"]
    assert raid.layout_row(1) == ["D3", "P", "D4", "D5"]
    assert raid.layout_row(2) == ["D6", "D7", "P", "D8"]


def test_raid5_full_stripe_read_degraded_read_and_rebuild():
    ds = disks(4, blocks=2)
    raid = RAID5(ds)
    stripe0 = [b"A000", b"B111", b"C222"]
    stripe1 = [b"D333", b"E444", b"F555"]
    raid.write_full_stripe(0, stripe0)
    raid.write_full_stripe(1, stripe1)

    assert [raid.read(i) for i in range(6)] == stripe0 + stripe1

    # In stripe 0, disk 2 holds D1.  RAID5 should reconstruct it from
    # D0, D2, and parity.  In stripe 1 the same disk holds D4.
    ds[2].fail()
    assert raid.read(1) == b"B111"
    assert raid.read(4) == b"E444"

    raid.rebuild_disk(2)
    assert not ds[2].failed
    assert [raid.read(i) for i in range(6)] == stripe0 + stripe1


def test_raid5_cannot_survive_two_failed_disks():
    ds = disks(3, blocks=1)
    raid = RAID5(ds)
    raid.write_full_stripe(0, [b"A000", b"B111"])
    ds[0].fail()
    ds[1].fail()
    with pytest.raises(DiskFailedError):
        raid.read(0)


def test_raid0_failed_member_loses_mapped_blocks():
    ds = disks(2, blocks=2)
    raid = RAID0(ds)
    raid.write(0, b"A000")
    raid.write(1, b"B111")

    ds[1].fail()
    assert raid.read(0) == b"A000"
    with pytest.raises(DiskFailedError):
        raid.read(1)


def test_raid5_reads_when_parity_disk_failed():
    ds = disks(4, blocks=1)
    raid = RAID5(ds)
    raid.write_full_stripe(0, [b"A000", b"B111", b"C222"])

    ds[raid.parity_disk(0)].fail()

    assert [raid.read(i) for i in range(3)] == [b"A000", b"B111", b"C222"]


def test_raid5_rebuilds_parity_disk():
    ds = disks(4, blocks=1)
    raid = RAID5(ds)
    blocks = [b"A000", b"B111", b"C222"]
    raid.write_full_stripe(0, blocks)
    parity_idx = raid.parity_disk(0)
    original_parity = ds[parity_idx].read(0)

    ds[parity_idx].fail()
    raid.rebuild_disk(parity_idx)

    assert not ds[parity_idx].failed
    assert ds[parity_idx].read(0) == original_parity
    assert [raid.read(i) for i in range(3)] == blocks


def test_raid5_five_disk_array_degraded_read_and_rebuild():
    ds = disks(5, blocks=2)
    raid = RAID5(ds)
    stripe0 = [b"A000", b"B111", b"C222", b"D333"]
    stripe1 = [b"E444", b"F555", b"G666", b"H777"]
    raid.write_full_stripe(0, stripe0)
    raid.write_full_stripe(1, stripe1)

    assert raid.layout_row(0) == ["P", "D0", "D1", "D2", "D3"]
    assert raid.layout_row(1) == ["D4", "P", "D5", "D6", "D7"]

    ds[3].fail()
    assert raid.read(2) == b"C222"
    assert raid.read(6) == b"G666"

    raid.rebuild_disk(3)
    assert [raid.read(i) for i in range(8)] == stripe0 + stripe1


def test_raid5_full_stripe_write_fails_if_target_disk_failed():
    ds = disks(3, blocks=1)
    raid = RAID5(ds)
    ds[1].fail()

    with pytest.raises(DiskFailedError):
        raid.write_full_stripe(0, [b"A000", b"B111"])

