"""Minimal RAID models for the FPGA RAID Lab.

The goal is clarity, not performance.  A "block" is a small bytes object so the
mapping and XOR parity are easy to inspect before we move to RTL experiments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import reduce
from operator import xor


class DiskFailedError(RuntimeError):
    """Raised when a failed virtual disk is accessed."""


@dataclass
class VirtualDisk:
    """A tiny fixed-size block device.

    Args:
        block_count: Number of addressable blocks.
        block_size: Bytes per block.
        name: Human-readable disk name used in error messages.
    """

    block_count: int
    block_size: int = 4
    name: str = "disk"
    failed: bool = False
    _blocks: list[bytearray] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.block_count <= 0:
            raise ValueError("block_count must be positive")
        if self.block_size <= 0:
            raise ValueError("block_size must be positive")
        self._blocks = [bytearray(self.block_size) for _ in range(self.block_count)]

    def read(self, lba: int) -> bytes:
        self._check_access(lba)
        return bytes(self._blocks[lba])

    def write(self, lba: int, data: bytes) -> None:
        self._check_access(lba)
        if len(data) != self.block_size:
            raise ValueError(f"data must be exactly {self.block_size} bytes")
        self._blocks[lba][:] = data

    def fail(self) -> None:
        self.failed = True

    def repair_blank(self) -> None:
        """Bring the disk back as a blank replacement drive."""
        self.failed = False
        self._blocks = [bytearray(self.block_size) for _ in range(self.block_count)]

    def _check_access(self, lba: int) -> None:
        if self.failed:
            raise DiskFailedError(f"{self.name} is failed")
        if not 0 <= lba < self.block_count:
            raise IndexError(f"{self.name} lba {lba} out of range")


def xor_blocks(blocks: list[bytes]) -> bytes:
    """XOR equal-sized byte blocks."""
    if not blocks:
        raise ValueError("xor_blocks needs at least one block")
    size = len(blocks[0])
    if any(len(block) != size for block in blocks):
        raise ValueError("all blocks must have the same size")
    return bytes(reduce(xor, values, 0) for values in zip(*blocks))


class RAID0:
    """Striping: capacity and bandwidth, no redundancy."""

    def __init__(self, disks: list[VirtualDisk]):
        if len(disks) < 2:
            raise ValueError("RAID0 needs at least two disks")
        self.disks = disks
        self.block_size = disks[0].block_size
        self.capacity_blocks = min(d.block_count for d in disks) * len(disks)
        self._check_same_block_size()

    def map_lba(self, lba: int) -> tuple[int, int]:
        self._check_lba(lba)
        return lba % len(self.disks), lba // len(self.disks)

    def write(self, lba: int, data: bytes) -> None:
        disk_idx, disk_lba = self.map_lba(lba)
        self.disks[disk_idx].write(disk_lba, data)

    def read(self, lba: int) -> bytes:
        disk_idx, disk_lba = self.map_lba(lba)
        return self.disks[disk_idx].read(disk_lba)

    def _check_lba(self, lba: int) -> None:
        if not 0 <= lba < self.capacity_blocks:
            raise IndexError("RAID0 lba out of range")

    def _check_same_block_size(self) -> None:
        if any(d.block_size != self.block_size for d in self.disks):
            raise ValueError("all disks must use the same block_size")


class RAID1:
    """Mirroring: write every block to every disk, read from any healthy disk."""

    def __init__(self, disks: list[VirtualDisk]):
        if len(disks) < 2:
            raise ValueError("RAID1 needs at least two disks")
        self.disks = disks
        self.block_size = disks[0].block_size
        self.capacity_blocks = min(d.block_count for d in disks)
        if any(d.block_size != self.block_size for d in disks):
            raise ValueError("all disks must use the same block_size")

    def write(self, lba: int, data: bytes) -> None:
        self._check_lba(lba)
        for disk in self.disks:
            disk.write(lba, data)

    def read(self, lba: int) -> bytes:
        self._check_lba(lba)
        for disk in self.disks:
            if not disk.failed:
                return disk.read(lba)
        raise DiskFailedError("all RAID1 mirrors are failed")

    def _check_lba(self, lba: int) -> None:
        if not 0 <= lba < self.capacity_blocks:
            raise IndexError("RAID1 lba out of range")


class RAID5:
    """Rotating-parity RAID5 model.

    Logical blocks are grouped by full stripes.  For N disks, each stripe has
    N-1 data blocks and one parity block.  Parity disk rotates by stripe index.
    """

    def __init__(self, disks: list[VirtualDisk]):
        if len(disks) < 3:
            raise ValueError("RAID5 needs at least three disks")
        self.disks = disks
        self.disk_count = len(disks)
        self.data_disks = self.disk_count - 1
        self.block_size = disks[0].block_size
        if any(d.block_size != self.block_size for d in disks):
            raise ValueError("all disks must use the same block_size")
        self.stripe_count = min(d.block_count for d in disks)
        self.capacity_blocks = self.stripe_count * self.data_disks

    def parity_disk(self, stripe: int) -> int:
        self._check_stripe(stripe)
        return stripe % self.disk_count

    def data_disk_order(self, stripe: int) -> list[int]:
        parity = self.parity_disk(stripe)
        return [idx for idx in range(self.disk_count) if idx != parity]

    def map_lba(self, lba: int) -> tuple[int, int, int]:
        """Return (disk_index, disk_lba, parity_disk_index)."""
        self._check_lba(lba)
        stripe = lba // self.data_disks
        offset = lba % self.data_disks
        return self.data_disk_order(stripe)[offset], stripe, self.parity_disk(stripe)

    def write_full_stripe(self, stripe: int, data_blocks: list[bytes]) -> None:
        self._check_stripe(stripe)
        if len(data_blocks) != self.data_disks:
            raise ValueError(f"full stripe needs {self.data_disks} data blocks")
        if any(len(block) != self.block_size for block in data_blocks):
            raise ValueError(f"each block must be {self.block_size} bytes")

        parity_idx = self.parity_disk(stripe)
        for disk_idx, block in zip(self.data_disk_order(stripe), data_blocks):
            self.disks[disk_idx].write(stripe, block)
        self.disks[parity_idx].write(stripe, xor_blocks(data_blocks))

    def read(self, lba: int) -> bytes:
        disk_idx, stripe, _parity_idx = self.map_lba(lba)
        if not self.disks[disk_idx].failed:
            return self.disks[disk_idx].read(stripe)
        return self._reconstruct_block(stripe, missing_disk=disk_idx)

    def rebuild_disk(self, disk_idx: int) -> None:
        """Rebuild one blank replacement disk from all surviving disks."""
        if not 0 <= disk_idx < self.disk_count:
            raise IndexError("disk_idx out of range")
        if self._failed_disk_count(exclude=disk_idx) > 0:
            raise DiskFailedError("RAID5 can rebuild only when no other disk is failed")
        self.disks[disk_idx].repair_blank()
        for stripe in range(self.stripe_count):
            self.disks[disk_idx].write(stripe, self._reconstruct_block(stripe, disk_idx))

    def layout_row(self, stripe: int) -> list[str]:
        """Human-readable labels for one stripe, useful for docs and demos."""
        parity = self.parity_disk(stripe)
        labels: list[str] = []
        data_number = 0
        for disk_idx in range(self.disk_count):
            if disk_idx == parity:
                labels.append("P")
            else:
                labels.append(f"D{stripe * self.data_disks + data_number}")
                data_number += 1
        return labels

    def _reconstruct_block(self, stripe: int, missing_disk: int) -> bytes:
        if not 0 <= missing_disk < self.disk_count:
            raise IndexError("missing_disk out of range")
        blocks: list[bytes] = []
        for idx, disk in enumerate(self.disks):
            if idx == missing_disk:
                continue
            blocks.append(disk.read(stripe))
        return xor_blocks(blocks)

    def _failed_disk_count(self, exclude: int | None = None) -> int:
        return sum(d.failed for idx, d in enumerate(self.disks) if idx != exclude)

    def _check_lba(self, lba: int) -> None:
        if not 0 <= lba < self.capacity_blocks:
            raise IndexError("RAID5 lba out of range")

    def _check_stripe(self, stripe: int) -> None:
        if not 0 <= stripe < self.stripe_count:
            raise IndexError("RAID5 stripe out of range")
