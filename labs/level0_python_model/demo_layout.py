"""Print small RAID0/1/5 layout tables for Level 0.

Run from this directory:

    python demo_layout.py

The output is intentionally ASCII-only so it can be pasted into docs and RTL
notebooks later.
"""

from raid_model import RAID0, RAID1, RAID5, VirtualDisk


def make_disks(count: int, blocks: int = 4) -> list[VirtualDisk]:
    return [VirtualDisk(blocks, name=f"d{i}") for i in range(count)]


def print_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def fmt(row: list[str]) -> str:
        return " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row))

    print(f"\n{title}")
    print("=" * len(title))
    print(fmt(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(fmt(row))


def demo_raid0() -> None:
    raid = RAID0(make_disks(3, blocks=3))
    rows = []
    for lba in range(raid.capacity_blocks):
        disk_idx, disk_lba = raid.map_lba(lba)
        rows.append([f"LBA {lba}", f"disk{disk_idx}", f"block {disk_lba}"])
    print_table("RAID0: stripe only, no safety net", ["logical", "disk", "disk_lba"], rows)


def demo_raid1() -> None:
    raid = RAID1(make_disks(2, blocks=4))
    rows = []
    for lba in range(raid.capacity_blocks):
        rows.append([f"LBA {lba}", "disk0 + disk1", "same data on both mirrors"])
    print_table("RAID1: mirror every block", ["logical", "where", "meaning"], rows)


def demo_raid5() -> None:
    raid = RAID5(make_disks(4, blocks=4))
    headers = [f"disk{i}" for i in range(raid.disk_count)]
    rows = [[f"stripe {stripe}", *raid.layout_row(stripe)] for stripe in range(raid.stripe_count)]
    print_table(
        "RAID5: rotating parity, one disk may disappear",
        ["stripe", *headers],
        rows,
    )


def main() -> None:
    demo_raid0()
    demo_raid1()
    demo_raid5()
    print("\nLegend: Dn = logical data block n, P = XOR parity block for that stripe.")


if __name__ == "__main__":
    main()
