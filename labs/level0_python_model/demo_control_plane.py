"""Teaching demo: a tiny AXI-Lite control-plane shadow model.

This file is not an RTL implementation.  It is a small executable story that
shows why the NVMe RAID recorder needs registers for bring-up, fault injection,
IRQ status/enable, rebuild progress, scrub results, and telemetry.
"""

from dataclasses import dataclass, field
from enum import IntEnum


class IRQ(IntEnum):
    MEMBER_FAILED = 1 << 0
    REBUILD_DONE = 1 << 1
    SCRUB_MISMATCH = 1 << 2
    ERROR_INJECT_DONE = 1 << 3


@dataclass
class ControlPlaneShadow:
    """A readable shadow register model for the tutorial.

    The names mirror docs/control_plane_registers.md, but the behavior is kept
    deliberately small: enough to teach software-visible state changes, not
    enough to be a real device model.
    """

    member_count: int = 4
    registers: dict[str, int | str] = field(default_factory=dict)
    member_state: list[str] = field(default_factory=list)
    event_log: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.registers.update(
            VERSION=0x0001,
            GLOBAL_CONTROL=0,
            GLOBAL_STATUS="RESET",
            RAID_MODE="UNSET",
            MEMBER_MASK=0,
            IRQ_STATUS=0,
            IRQ_ENABLE=0,
            ERROR_INJECT_CONTROL="NONE",
            ERROR_INJECT_STATUS="IDLE",
            REBUILD_CONTROL="IDLE",
            REBUILD_PROGRESS=0,
            SCRUB_CONTROL="IDLE",
            SCRUB_MISMATCH_COUNT=0,
            TELEMETRY_INTERVAL_MS=1000,
        )
        self.member_state = ["PRESENT" for _ in range(self.member_count)]

    def enable_irq(self, mask: int):
        self.registers["IRQ_ENABLE"] = mask
        self.event_log.append(f"irq_enable=0x{mask:02x}")

    def _raise_irq(self, bit: IRQ, event: str):
        self.registers["IRQ_STATUS"] |= int(bit)
        if self.registers["IRQ_ENABLE"] & int(bit):
            self.event_log.append(f"irq:{event}")
        else:
            self.event_log.append(f"event_masked:{event}")

    def clear_irq(self, mask: int):
        # W1C: write 1 to clear the selected bits.
        self.registers["IRQ_STATUS"] &= ~mask
        self.event_log.append(f"clear_irq=0x{mask:02x}")

    def bring_up(self, raid_mode: str = "RAID5"):
        self.registers["GLOBAL_STATUS"] = "INIT"
        self.registers["RAID_MODE"] = raid_mode
        self.registers["MEMBER_MASK"] = (1 << self.member_count) - 1
        self.member_state = ["ACTIVE" for _ in range(self.member_count)]
        self.registers["GLOBAL_CONTROL"] = 1
        self.registers["GLOBAL_STATUS"] = "RUNNING"
        self.event_log.append(f"bring_up:{raid_mode}:members=0x{self.registers['MEMBER_MASK']:x}")

    def inject_member_fail(self, index: int):
        self.registers["ERROR_INJECT_CONTROL"] = f"FAIL_MEMBER_{index}"
        self.registers["ERROR_INJECT_STATUS"] = "BUSY"
        self.member_state[index] = "FAILED"
        self.registers["GLOBAL_STATUS"] = "DEGRADED"
        self.registers["ERROR_INJECT_STATUS"] = "DONE"
        self._raise_irq(IRQ.MEMBER_FAILED, f"member{index}_failed")
        self._raise_irq(IRQ.ERROR_INJECT_DONE, "error_inject_done")

    def start_rebuild(self, index: int):
        self.registers["REBUILD_CONTROL"] = f"START_MEMBER_{index}"
        self.member_state[index] = "REBUILDING"
        self.registers["GLOBAL_STATUS"] = "REBUILDING"
        self.registers["REBUILD_PROGRESS"] = 0
        self.event_log.append(f"rebuild_start:member{index}")

    def step_rebuild(self, percent: int):
        self.registers["REBUILD_PROGRESS"] = percent
        self.event_log.append(f"rebuild_progress={percent}%")
        if percent >= 100:
            self.member_state = ["ACTIVE" for _ in range(self.member_count)]
            self.registers["GLOBAL_STATUS"] = "RUNNING"
            self.registers["REBUILD_CONTROL"] = "DONE"
            self._raise_irq(IRQ.REBUILD_DONE, "rebuild_done")

    def run_scrub(self, mismatch: bool = False):
        self.registers["SCRUB_CONTROL"] = "RUN"
        if mismatch:
            self.registers["SCRUB_MISMATCH_COUNT"] += 1
            self._raise_irq(IRQ.SCRUB_MISMATCH, "scrub_mismatch")
        else:
            self.event_log.append("scrub_clean")
        self.registers["SCRUB_CONTROL"] = "IDLE"

    def snapshot(self) -> dict[str, object]:
        keys = [
            "GLOBAL_STATUS",
            "RAID_MODE",
            "MEMBER_MASK",
            "IRQ_STATUS",
            "IRQ_ENABLE",
            "ERROR_INJECT_STATUS",
            "REBUILD_PROGRESS",
            "SCRUB_MISMATCH_COUNT",
            "TELEMETRY_INTERVAL_MS",
        ]
        data = {key: self.registers[key] for key in keys}
        data["MEMBER_STATE"] = list(self.member_state)
        return data


def format_snapshot(title: str, model: ControlPlaneShadow) -> str:
    data = model.snapshot()
    lines = [f"[{title}]"]
    for key, value in data.items():
        if key.startswith("IRQ") or key == "MEMBER_MASK":
            if isinstance(value, int):
                value = f"0x{value:02x}"
        lines.append(f"{key:24} {value}")
    return "\n".join(lines)


def run_demo() -> ControlPlaneShadow:
    model = ControlPlaneShadow()
    print(format_snapshot("reset", model))

    model.enable_irq(
        int(IRQ.MEMBER_FAILED)
        | int(IRQ.REBUILD_DONE)
        | int(IRQ.SCRUB_MISMATCH)
        | int(IRQ.ERROR_INJECT_DONE)
    )
    model.bring_up("RAID5")
    print("\n" + format_snapshot("after bring-up", model))

    model.inject_member_fail(2)
    print("\n" + format_snapshot("after SSD#2 fault injection", model))
    model.clear_irq(int(IRQ.MEMBER_FAILED) | int(IRQ.ERROR_INJECT_DONE))
    print("\n" + format_snapshot("after software clears handled IRQ bits", model))

    model.start_rebuild(2)
    for percent in (25, 50, 100):
        model.step_rebuild(percent)
    print("\n" + format_snapshot("after rebuild", model))

    model.run_scrub(mismatch=True)
    print("\n" + format_snapshot("after scrub mismatch", model))

    print("\n[event log]")
    for event in model.event_log:
        print(event)
    return model


if __name__ == "__main__":
    run_demo()
