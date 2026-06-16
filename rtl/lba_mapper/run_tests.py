"""Run lba_mapper RTL regression tests.

Run from the repository root:

    python rtl/lba_mapper/run_tests.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LBA_DIR = ROOT / "rtl" / "lba_mapper"
PY_MODEL_DIR = ROOT / "labs" / "level0_python_model"
if str(PY_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(PY_MODEL_DIR))

from raid_model import RAID0, VirtualDisk  # noqa: E402

DEFAULT_CASES = list(range(0, 17)) + [31, 32, 33]
PARAM_CASES = [
    (3, 2, list(range(0, 18)) + [23, 24, 25]),
    (5, 0, list(range(0, 16)) + [24, 25, 26]),
]


def golden(lba: int, disk_count: int, chunk_shift: int) -> tuple[int, int, int]:
    chunk_size = 1 << chunk_shift
    logical_chunk = lba >> chunk_shift
    chunk_offset = lba & (chunk_size - 1)
    disk_index = logical_chunk % disk_count
    stripe_index = logical_chunk // disk_count
    disk_lba = (stripe_index << chunk_shift) + chunk_offset
    return disk_index, stripe_index, disk_lba


def cross_check_python_raid0(lbas: list[int], disk_count: int, chunk_shift: int) -> None:
    """For one-block chunks, keep this RTL runner tied to the Python model."""
    if chunk_shift != 0:
        return
    block_count = max(lbas) // disk_count + 2
    raid0 = RAID0([VirtualDisk(block_count=block_count, name=f"d{i}") for i in range(disk_count)])
    for lba in lbas:
        model_disk, model_disk_lba = raid0.map_lba(lba)
        disk, _stripe, disk_lba = golden(lba, disk_count, chunk_shift)
        if (disk, disk_lba) != (model_disk, model_disk_lba):
            raise SystemExit(
                f"golden drift at lba={lba}: formula={(disk, disk_lba)} "
                f"python_model={(model_disk, model_disk_lba)}"
            )


def run(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 30) -> str:
    print("$", " ".join(str(part) for part in cmd))
    try:
        result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    except FileNotFoundError as exc:
        tool = str(cmd[0])
        raise SystemExit(
            f"missing external tool: {tool}\n"
            "Install Icarus Verilog and make sure both `iverilog` and `vvp` are on PATH.\n"
            "Then rerun: python rtl/lba_mapper/run_tests.py"
        ) from exc
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output)
    if result.returncode != 0:
        raise SystemExit(f"command failed with exit code {result.returncode}: {' '.join(cmd)}")
    return output


def write_default_vectors() -> None:
    cross_check_python_raid0(DEFAULT_CASES, disk_count=4, chunk_shift=0)
    lines = []
    for lba in DEFAULT_CASES:
        disk, stripe, disk_lba = golden(lba, disk_count=4, chunk_shift=0)
        lines.append(f"{lba} {disk} {stripe} {disk_lba}\n")
    (LBA_DIR / "vectors.txt").write_text("".join(lines), encoding="utf-8")


def write_param_tb(path: Path, disk_count: int, chunk_shift: int, lbas: list[int]) -> None:
    checks = []
    for lba in lbas:
        disk, stripe, disk_lba = golden(lba, disk_count, chunk_shift)
        checks.append(
            f"        check_case(32'd{lba}, 8'd{disk}, 32'd{stripe}, 32'd{disk_lba});\n"
        )

    path.write_text(
        f"""`timescale 1ns/1ps

module tb_lba_mapper_param;
    localparam LBA_WIDTH   = 32;
    localparam DISK_COUNT  = {disk_count};
    localparam CHUNK_SHIFT = {chunk_shift};

    reg  [LBA_WIDTH-1:0] lba;
    wire [7:0]           disk_index;
    wire [LBA_WIDTH-1:0] stripe_index;
    wire [LBA_WIDTH-1:0] disk_lba;

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

    task check_case;
        input [LBA_WIDTH-1:0] in_lba;
        input [7:0] exp_disk;
        input [LBA_WIDTH-1:0] exp_stripe;
        input [LBA_WIDTH-1:0] exp_disk_lba;
        begin
            lba = in_lba;
            #1;
            cases = cases + 1;
            if (disk_index !== exp_disk || stripe_index !== exp_stripe || disk_lba !== exp_disk_lba) begin
                errors = errors + 1;
                $display("FAIL_PARAM dc={disk_count} cs={chunk_shift} lba=%0d got disk=%0d stripe=%0d disk_lba=%0d expected disk=%0d stripe=%0d disk_lba=%0d",
                         in_lba, disk_index, stripe_index, disk_lba, exp_disk, exp_stripe, exp_disk_lba);
            end
        end
    endtask

    initial begin
        cases = 0;
        errors = 0;
{''.join(checks)}
        if (errors == 0) begin
            $display("PASS_PARAM dc={disk_count} cs={chunk_shift} cases=%0d", cases);
        end else begin
            $display("FAIL_PARAM dc={disk_count} cs={chunk_shift} cases=%0d errors=%0d", cases, errors);
            $finish_and_return(1);
        end
        $finish;
    end
endmodule
""",
        encoding="utf-8",
    )


def run_default_testbench() -> None:
    write_default_vectors()
    with tempfile.TemporaryDirectory(prefix="lba_mapper_default_") as tmp_name:
        out_vvp = Path(tmp_name) / "tb_lba_mapper.vvp"
        run(["iverilog", "-o", str(out_vvp), str(LBA_DIR / "lba_mapper.v"), str(LBA_DIR / "tb_lba_mapper.v")])
        output = run(["vvp", str(out_vvp)])
    if "PASS lba_mapper" not in output:
        raise SystemExit("default lba_mapper testbench did not report PASS")


def run_param_matrix() -> None:
    with tempfile.TemporaryDirectory(prefix="lba_mapper_param_") as tmp_name:
        tmp = Path(tmp_name)
        for disk_count, chunk_shift, lbas in PARAM_CASES:
            cross_check_python_raid0(lbas, disk_count, chunk_shift)
            tb_path = tmp / f"tb_lba_mapper_param_d{disk_count}_c{chunk_shift}.v"
            vvp_path = tmp / f"tb_lba_mapper_param_d{disk_count}_c{chunk_shift}.vvp"
            write_param_tb(tb_path, disk_count, chunk_shift, lbas)
            run(["iverilog", "-o", str(vvp_path), str(LBA_DIR / "lba_mapper.v"), str(tb_path)])
            output = run(["vvp", str(vvp_path)])
            expected = f"PASS_PARAM dc={disk_count} cs={chunk_shift}"
            if expected not in output:
                raise SystemExit(f"parameterized test did not report {expected}")


def main() -> None:
    print("== lba_mapper default vectors/testbench ==")
    run_default_testbench()
    print("\n== lba_mapper parameter matrix ==")
    run_param_matrix()
    print("\nPASS lba_mapper regression: default + parameter matrix")


if __name__ == "__main__":
    main()
