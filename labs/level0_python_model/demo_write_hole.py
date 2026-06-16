"""Show how a RAID5 write hole can hide until degraded recovery.

Run from the repository root:

    python labs/level0_python_model/demo_write_hole.py

The numbers match docs/write_hole.md.  A block is one byte here so the XOR
math stays visible: D0 XOR D1 XOR D2 = P.
"""

from raid_model import RAID5, VirtualDisk, xor_blocks


def b(value: int) -> bytes:
    return bytes([value])


def hx(block: bytes) -> str:
    return f"0x{block[0]:02x}"


def recover_d1(d0: bytes, d2: bytes, parity: bytes) -> bytes:
    """Recover missing D1 from the other data blocks and RAID5 parity."""
    return xor_blocks([d0, d2, parity])


def print_case(title: str, d0: bytes, d1_on_disk: bytes, d2: bytes, parity_on_disk: bytes) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    print(f"disk data/parity : D0={hx(d0)} D1={hx(d1_on_disk)} D2={hx(d2)} P={hx(parity_on_disk)}")
    print(f"normal read D1   : {hx(d1_on_disk)}  (directly reads the data disk)")
    recovered = recover_d1(d0, d2, parity_on_disk)
    print(f"recover missing D1: {hx(recovered)}  (D0 XOR D2 XOR P)")


def make_raid5(d0: bytes, d1: bytes, d2: bytes) -> RAID5:
    raid = RAID5([VirtualDisk(block_count=1, block_size=1, name=f"disk{idx}") for idx in range(4)])
    raid.write_full_stripe(0, [d0, d1, d2])
    return raid


def print_model_case(
    title: str,
    d0: bytes,
    d1_on_disk: bytes,
    d2: bytes,
    parity_on_disk: bytes,
    failed_disk: int = 2,
) -> None:
    """Repeat the same mismatch with the real RAID5 model.

    Stripe 0 on four disks is: disk0=P, disk1=D0, disk2=D1, disk3=D2.
    Logical block 1 is therefore D1.  A normal read of LBA1 touches disk2
    directly; a degraded read after disk2 fails must reconstruct D1 from
    disk0/disk1/disk3.  The failed disk is a parameter so readers can try
    other failures after understanding the shortest D1 example.
    """
    raid = make_raid5(d0, d1_on_disk, d2)
    raid.disks[0].write(0, parity_on_disk)

    normal = raid.read(1)
    raid.disks[failed_disk].fail()
    degraded = raid.read(1)

    print(f"\nModel check - {title}")
    print("-" * (14 + len(title)))
    print("stripe 0 layout : disk0=P disk1=D0 disk2=D1 disk3=D2")
    print(f"normal RAID5.read(1)   : {hx(normal)}")
    print(f"degraded RAID5.read(1) : {hx(degraded)}  (disk{failed_disk} failed)")


def main() -> None:
    d0 = b(0xAA)
    old_d1 = b(0xCC)
    d2 = b(0x00)
    new_d1 = b(0x0F)

    old_parity = xor_blocks([d0, old_d1, d2])
    new_parity = xor_blocks([d0, new_d1, d2])

    print("RAID5 write hole demo: looks fine, fails later")
    print("================================================")
    print("Goal: change D1 from 0xcc to 0x0f in one RAID5 stripe.")
    print("Watch the two read paths: normal read may look OK, degraded read exposes the mismatch.")
    print(f"old stripe       : D0={hx(d0)} D1={hx(old_d1)} D2={hx(d2)} P={hx(old_parity)}")
    print(f"intended stripe  : D0={hx(d0)} D1={hx(new_d1)} D2={hx(d2)} P={hx(new_parity)}")
    print("\nIf power dies between the data write and the parity write, the stripe can")
    print("look readable but no longer be self-consistent.")

    print_case(
        "Case A: data new, parity old",
        d0=d0,
        d1_on_disk=new_d1,
        d2=d2,
        parity_on_disk=old_parity,
    )
    print("Result: normal read sees the new D1, but degraded recovery recreates 0xcc.")

    print_case(
        "Case B: parity new, data old",
        d0=d0,
        d1_on_disk=old_d1,
        d2=d2,
        parity_on_disk=new_parity,
    )
    print("Result: normal read sees the old D1, but degraded recovery recreates 0x0f.")

    print("\nRAID5 model cross-check")
    print("-----------------------")
    print("Now repeat both cases with the repository's RAID5 object, not just hand XOR.")
    print("The default failure is disk2 only because stripe 0 keeps D1 easy to see.")
    print_model_case("data new, parity old", d0, new_d1, d2, old_parity, failed_disk=2)
    print_model_case("parity new, data old", d0, old_d1, d2, new_parity, failed_disk=2)

    print("\nTakeaway")
    print("--------")
    print("Write hole is dangerous because the normal read path may not notice it.")
    print("A later degraded read, rebuild, or scrub is the moment the mismatch bites.")
    print("Mini challenge: change failed_disk in print_model_case() and predict the recovered byte.")


if __name__ == "__main__":
    main()
