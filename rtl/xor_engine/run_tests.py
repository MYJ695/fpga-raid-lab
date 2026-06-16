"""Run xor_engine RTL regression tests.

This script keeps the first RTL lab Python-first:

1. regenerate the default 4-input/32-bit vectors;
2. compile and run the checked-in Icarus Verilog testbench;
3. generate small temporary parameterized testbenches for non-default shapes.

Run from the repository root:

    python rtl/xor_engine/run_tests.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
XOR_DIR = ROOT / "rtl" / "xor_engine"

PARAM_CASES = [
    (8, [(0x00, 0x00), (0xA5, 0x5A), (0xFF, 0x0F)]),
    (16, [(0x0000, 0x1234, 0x1234), (0xFFFF, 0x00FF, 0x0F0F)]),
    (64, [(0x0000000000000000, 0x1111111111111111, 0x2222222222222222, 0x3333333333333333, 0x4444444444444444)]),
]


def run(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 30) -> str:
    """Run a command and return combined output, failing with teaching-friendly errors."""
    print("$", " ".join(str(part) for part in cmd))
    try:
        result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    except FileNotFoundError as exc:
        tool = str(cmd[0])
        raise SystemExit(
            f"missing external tool: {tool}\n"
            "Install Icarus Verilog and make sure both `iverilog` and `vvp` are on PATH.\n"
            "Then rerun: python rtl/xor_engine/run_tests.py"
        ) from exc
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output)
    if result.returncode != 0:
        raise SystemExit(f"command failed with exit code {result.returncode}: {' '.join(cmd)}")
    return output


def xor_words(words: tuple[int, ...], width: int) -> int:
    mask = (1 << width) - 1
    acc = 0
    for word in words:
        acc ^= word & mask
    return acc & mask


def hex_literal(value: int, width: int) -> str:
    digits = (width + 3) // 4
    return f"{width}'h{value & ((1 << width) - 1):0{digits}X}"


def packed_literal(words: tuple[int, ...], width: int) -> str:
    # xor_engine maps data_in[i*WORD_WIDTH +: WORD_WIDTH] to input i.
    # Verilog concatenation writes the highest slice first, so reverse here.
    return "{" + ", ".join(hex_literal(word, width) for word in reversed(words)) + "}"


def write_param_tb(path: Path, width: int, cases: list[tuple[int, ...]]) -> None:
    input_count = len(cases[0])
    checks = []
    for index, words in enumerate(cases, start=1):
        expected = xor_words(words, width)
        checks.append(
            f"        data_in = {packed_literal(words, width)};\n"
            f"        #1;\n"
            f"        cases = cases + 1;\n"
            f"        if (xor_out !== {hex_literal(expected, width)}) begin\n"
            f"            errors = errors + 1;\n"
            f"            $display(\"FAIL_PARAM ww={width} ic={input_count} case={index}: got %h expected {expected:0{(width + 3) // 4}X}\", xor_out);\n"
            f"        end\n"
        )
    path.write_text(
        f"""`timescale 1ns/1ps

module tb_xor_engine_param;
    localparam WORD_WIDTH = {width};
    localparam INPUT_COUNT = {input_count};

    reg  [WORD_WIDTH*INPUT_COUNT-1:0] data_in;
    wire [WORD_WIDTH-1:0] xor_out;
    integer cases;
    integer errors;

    xor_engine #(
        .WORD_WIDTH(WORD_WIDTH),
        .INPUT_COUNT(INPUT_COUNT)
    ) dut (
        .data_in(data_in),
        .xor_out(xor_out)
    );

    initial begin
        cases = 0;
        errors = 0;
{''.join(checks)}
        if (errors == 0) begin
            $display("PASS_PARAM ww={width} ic={input_count} cases=%0d", cases);
        end else begin
            $display("FAIL_PARAM ww={width} ic={input_count} cases=%0d errors=%0d", cases, errors);
        end
        $finish;
    end
endmodule
""",
        encoding="utf-8",
    )


def run_default_testbench() -> None:
    run([sys.executable, str(XOR_DIR / "gen_vectors.py")])
    with tempfile.TemporaryDirectory(prefix="xor_engine_default_") as tmp_name:
        out_vvp = Path(tmp_name) / "tb_xor_engine.vvp"
        run([
            "iverilog",
            "-o",
            str(out_vvp),
            str(XOR_DIR / "xor_engine.v"),
            str(XOR_DIR / "tb_xor_engine.v"),
        ])
        output = run(["vvp", str(out_vvp)])
    if "PASS xor_engine" not in output:
        raise SystemExit("default xor_engine testbench did not report PASS")


def run_param_matrix() -> None:
    with tempfile.TemporaryDirectory(prefix="xor_engine_param_") as tmp_name:
        tmp = Path(tmp_name)
        for width, cases in PARAM_CASES:
            input_count = len(cases[0])
            tb_path = tmp / f"tb_xor_engine_param_{width}x{input_count}.v"
            vvp_path = tmp / f"tb_xor_engine_param_{width}x{input_count}.vvp"
            write_param_tb(tb_path, width, cases)
            run(["iverilog", "-o", str(vvp_path), str(XOR_DIR / "xor_engine.v"), str(tb_path)])
            output = run(["vvp", str(vvp_path)])
            expected = f"PASS_PARAM ww={width} ic={input_count}"
            if expected not in output:
                raise SystemExit(f"parameterized test did not report {expected}")


def main() -> None:
    print("== xor_engine default vectors/testbench ==")
    run_default_testbench()
    print("\n== xor_engine parameter matrix ==")
    run_param_matrix()
    print("\nPASS xor_engine regression: default + parameter matrix")


if __name__ == "__main__":
    main()
