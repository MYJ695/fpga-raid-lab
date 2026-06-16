"""Generate golden vectors for rtl/xor_engine.

The file has no header line because old Icarus Verilog versions can get stuck when
`$fscanf` sees a non-hex comment line.
"""

from pathlib import Path

WORD_MASK = 0xFFFFFFFF
CASES = [
    (0x00000000, 0x00000000, 0x00000000, 0x00000000),
    (0x00000000, 0x11111111, 0x22222222, 0x33333333),
    (0xFFFFFFFF, 0x00000000, 0x12345678, 0x12345678),
    (0xDEADBEEF, 0xCAFEBABE, 0x01020304, 0x11223344),
    (0xAAAAAAAA, 0x55555555, 0x0F0F0F0F, 0xF0F0F0F0),
]


def xor_words(words):
    acc = 0
    for word in words:
        acc ^= word & WORD_MASK
    return acc & WORD_MASK


def main():
    out_path = Path(__file__).with_name("vectors.txt")
    lines = []
    for case in CASES:
        expected = xor_words(case)
        lines.append(" ".join(f"{value:08X}" for value in (*case, expected)))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_path.as_posix()} cases={len(CASES)}")


if __name__ == "__main__":
    main()
