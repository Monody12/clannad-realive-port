#!/usr/bin/env python3
"""DBS 日/中列交换重加密器。

text*.dbs 中 col1(call_no=0, 日文) 与 col2(call_no=2, 中文) 为双语对;
siglus_rs 引擎读 call_no=0。本工具交换两列的字符串偏移,使引擎读 call_no=0
时得到中文。输出重加密的 .dbs,可直接放回游戏数据目录。

用法:
    python dbs_swap_cn.py <in.dbs> <out.dbs>
    python dbs_swap_cn.py --verify <file.dbs>   # 解码并打印样例验证
"""
import struct
import sys

from dbs_decode import expand, XOR_A, XOR_B, XOR_C, TILE, MAP_WIDTH


def lzss_pack_literal(data: bytes) -> bytes:
    """仅字面量的 Siglus LZSS 流(解码器兼容)。"""
    out = bytearray()
    out += struct.pack("<ii", 8 + (len(data) + 7) // 8 * 9, len(data))
    i = 0
    while i < len(data):
        group = data[i:i + 8]
        out.append(0xFF)
        out += group
        i += 8
    return bytes(out)


def xor_u32(buf: bytearray, code: int) -> None:
    for i in range(len(buf) // 4):
        off = i * 4
        v = struct.unpack_from("<I", buf, off)[0] ^ code
        struct.pack_into("<I", buf, off, v)


def swap_jp_cn_columns(expanded: bytearray) -> bytearray:
    row_cnt = struct.unpack_from("<i", expanded, 4)[0]
    col_cnt = struct.unpack_from("<i", expanded, 8)[0]
    col_hdr_off = struct.unpack_from("<i", expanded, 16)[0]
    data_off = struct.unpack_from("<i", expanded, 20)[0]
    # 按 call_no 定位日文槽(0)与中文槽(2),要求均为字符串列
    idx0 = idx2 = None
    for c in range(col_cnt):
        call_no, dtype = struct.unpack_from("<ii", expanded, col_hdr_off + c * 8)
        if call_no == 0 and chr(dtype & 0xFF) == "S":
            idx0 = c
        if call_no == 2 and chr(dtype & 0xFF) == "S":
            idx2 = c
    if idx0 is None or idx2 is None:
        raise ValueError(f"未找到 call_no=0/2 的字符串列(col_cnt={col_cnt})")
    out = bytearray(expanded)
    for r in range(row_cnt):
        i1 = data_off + (r * col_cnt + idx0) * 4
        i2 = data_off + (r * col_cnt + idx2) * 4
        v1 = out[i1:i1 + 4]
        v2 = out[i2:i2 + 4]
        out[i1:i1 + 4] = v2
        out[i2:i2 + 4] = v1
    return out


def reencrypt(expanded: bytes) -> bytes:
    xl = MAP_WIDTH
    yl = len(expanded) // (xl * 4)

    # expand 的逆:按 mask 拆 A/B → 各自异或还原 → 交错合成 unpacked
    a = bytearray(len(expanded))
    b = bytearray(len(expanded))
    for y in range(yl):
        for x in range(xl):
            mv = TILE[(y % 5) * 5 + (x % 5)]
            p = (y * xl + x) * 4
            if mv >= 128:
                a[p:p+4] = expanded[p:p+4]
            else:
                b[p:p+4] = expanded[p:p+4]
    xor_u32(a, XOR_A)
    xor_u32(b, XOR_B)
    unpacked = bytearray(len(expanded))
    for y in range(yl):
        for x in range(xl):
            mv = TILE[(y % 5) * 5 + (x % 5)]
            p = (y * xl + x) * 4
            unpacked[p:p+4] = a[p:p+4] if mv >= 128 else b[p:p+4]

    # LZSS(仅字面量)→ XOR_C → [type][payload]
    packed = bytearray(lzss_pack_literal(bytes(unpacked)))
    xor_u32(packed, XOR_C)
    return struct.pack("<i", 1) + bytes(packed)


def main():
    if len(sys.argv) >= 3 and sys.argv[1] != "--verify":
        raw = open(sys.argv[1], "rb").read()
        expanded = bytearray(expand(raw[4:]))
        swapped = swap_jp_cn_columns(expanded)
        out = reencrypt(bytes(swapped))
        open(sys.argv[2], "wb").write(out)
        print(f"OK {sys.argv[1]} -> {sys.argv[2]} ({len(out)} bytes)")
    else:
        path = sys.argv[2] if sys.argv[1] == "--verify" else sys.argv[1]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 8
        raw = open(path, "rb").read()
        exp = expand(raw[4:])
        row_cnt, col_cnt = struct.unpack_from("<ii", exp, 4)
        data_off = struct.unpack_from("<i", exp, 20)[0]
        str_off = struct.unpack_from("<i", exp, 24)[0]
        print(f"rows={row_cnt} cols={col_cnt}")
        def get_str(off):
            base = str_off + off
            cells = []
            while base + 2 <= len(exp):
                cp = struct.unpack_from("<H", exp, base)[0]
                if cp == 0:
                    break
                cells.append(chr(cp)); base += 2
            return "".join(cells)
        for r in range(1, min(limit, row_cnt)):
            cells = []
            for c in range(1, 3):
                v = struct.unpack_from("<I", exp, data_off + (r*col_cnt + c)*4)[0]
                cells.append(get_str(v)[:30])
            print(f"row{r}: col1(JP槽)={cells[0]!r} col2(CN槽)={cells[1]!r}")


if __name__ == "__main__":
    main()
