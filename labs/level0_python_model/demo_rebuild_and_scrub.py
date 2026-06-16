"""Show how RAID5 rebuild and scrub expose a hidden write hole.

Run from the repository root:

    python labs/level0_python_model/demo_rebuild_and_scrub.py

A block is one byte here so the XOR math stays visible.  The example matches
``docs/write_hole.md`` and ``docs/rebuild_and_scrub.md``:

    disk0=P  disk1=D0  disk2=D1  disk3=D2
"""

from raid_model import RAID5, VirtualDisk, xor_blocks


def b(value: int) -> bytes:
    return bytes([value])


def h(block: bytes) -> str:
    return f"0x{block[0]:02x}"


def make_array() -> RAID5:
    disks = [VirtualDisk(block_count=1, block_size=1, name=f"disk{i}") for i in range(4)]
    raid = RAID5(disks)

    # Start from the inconsistent post-write-hole state:
    # data already has new D1=0x0f, but parity is still the old P=0x66.
    disks[0].write(0, b(0x66))  # P: stale parity
    disks[1].write(0, b(0xAA))  # D0
    disks[2].write(0, b(0x0F))  # D1: new data
    disks[3].write(0, b(0x00))  # D2
    return raid


def print_stripe(raid: RAID5) -> None:
    print("Stripe 0 layout: disk0=P  disk1=D0  disk2=D1  disk3=D2")
    for idx, label in enumerate(raid.layout_row(0)):
        print(f"  disk{idx} {label:>2} = {h(raid.disks[idx].read(0))}")


def scrub_once(raid: RAID5) -> None:
    print()
    print("Scrub: recalculate parity while all disks are still readable")
    d0 = raid.disks[1].read(0)
    d1 = raid.disks[2].read(0)
    d2 = raid.disks[3].read(0)
    stored_p = raid.disks[0].read(0)
    expected_p = xor_blocks([d0, d1, d2])

    print(f"  expected_P = D0 XOR D1 XOR D2 = {h(d0)} XOR {h(d1)} XOR {h(d2)} = {h(expected_p)}")
    print(f"  stored_P   = {h(stored_p)}")
    if expected_p != stored_p:
        print("  scrub result: parity mismatch detected")
    else:
        print("  scrub result: clean stripe")


def rebuild_missing_d1(raid: RAID5) -> None:
    print()
    print("Rebuild: disk2 is missing, reconstruct logical D1 from survivors")
    rebuilt = xor_blocks([
        raid.disks[0].read(0),  # stale P
        raid.disks[1].read(0),  # D0
        raid.disks[3].read(0),  # D2
    ])
    print("  rebuild_D1 = P XOR D0 XOR D2")
    print(f"             = {h(raid.disks[0].read(0))} XOR {h(raid.disks[1].read(0))} XOR {h(raid.disks[3].read(0))}")
    print(f"             = {h(rebuilt)}")
    print("  expected current D1 was 0x0f, so rebuild produced stale data")


def main() -> None:
    raid = make_array()
    print("RAID5 rebuild/scrub mini lab")
    print("================================")
    print_stripe(raid)
    scrub_once(raid)
    rebuild_missing_d1(raid)
    print()
    print("Takeaway")
    print("--------")
    print("Scrub finds the mismatch before a disk fails; rebuild may turn the same mismatch into wrong recovered data.")


if __name__ == "__main__":
    main()
