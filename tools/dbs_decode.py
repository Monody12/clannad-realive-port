#!/usr/bin/env python3
"""SiglusEngine .dbs (DATABASE) 解码器 —— 复现 siglus_rs dbs.rs 的 tnm_database_expand。

用法: python dbs_decode.py <file.dbs> [max_strings]
输出: 头部信息 + 字符统计(判断日文/中文)+ 前若干条字符串
"""
import struct
import sys

XOR_A = 0x7190C70E
XOR_B = 0x499BF135
XOR_C = 0x89F4622D
TILE = [255,0,0,255,255, 0,0,255,255,0, 255,255,255,0,255,
        0,0,255,0,0, 0,0,0,255,255]
MAP_WIDTH = 16
TILE_W = TILE_H = 5


def xor_u32(buf: bytearray, code: int) -> None:
    for i in range(len(buf) // 4):
        off = i * 4
        v = struct.unpack_from("<I", buf, off)[0] ^ code
        struct.pack_into("<I", buf, off, v)


def lzss_unpack(src: bytes) -> bytes:
    arc_size, org_size = struct.unpack_from("<ii", src, 0)
    payload_end = min(arc_size, len(src))
    pos = 8
    out = bytearray()
    while len(out) < org_size and pos < payload_end:
        flags = src[pos]; pos += 1
        for _ in range(8):
            if len(out) >= org_size or pos >= payload_end:
                break
            if flags & 1:
                out.append(src[pos]); pos += 1
            else:
                token = struct.unpack_from("<H", src, pos)[0]; pos += 2
                offset = token >> 4
                length = (token & 0x0F) + 2
                if offset == 0 or offset > len(out):
                    raise ValueError(f"bad backref offset={offset} out={len(out)}")
                src_idx = len(out) - offset
                for _ in range(length):
                    if len(out) >= org_size:
                        break
                    out.append(out[src_idx]); src_idx += 1
            flags >>= 1
    if len(out) != org_size:
        raise ValueError(f"lzss size mismatch got={len(out)} want={org_size}")
    return bytes(out)


def mask_split(src: bytes, xl: int, yl: int, reverse: bool) -> bytearray:
    dst = bytearray(len(src))
    for y in range(yl):
        for x in range(xl):
            mv = TILE[(y % TILE_H) * TILE_W + (x % TILE_W)]
            cond = (mv >= 128) if not reverse else (mv < 128)
            if cond:
                p = (y * xl + x) * 4
                dst[p:p+4] = src[p:p+4]
    return dst


def expand(payload: bytes) -> bytes:
    buf = bytearray(payload)
    xor_u32(buf, XOR_C)
    unpacked = lzss_unpack(bytes(buf))
    if len(unpacked) % (MAP_WIDTH * 4) != 0:
        raise ValueError(f"unpack size {len(unpacked)} not aligned")
    yl = len(unpacked) // (MAP_WIDTH * 4)
    a = mask_split(unpacked, MAP_WIDTH, yl, reverse=False)
    b = mask_split(unpacked, MAP_WIDTH, yl, reverse=True)
    xor_u32(a, XOR_A)
    xor_u32(b, XOR_B)
    dst = bytearray(len(unpacked))
    for y in range(yl):
        for x in range(MAP_WIDTH):
            mv = TILE[(y % TILE_H) * TILE_W + (x % TILE_W)]
            p = (y * MAP_WIDTH + x) * 4
            dst[p:p+4] = a[p:p+4] if mv >= 128 else b[p:p+4]
    return bytes(dst)


def utf16_strings(expanded: bytes, limit: int = 20):
    # 从整个缓冲区提取 UTF-16LE 可打印串
    strs = []
    cur = []
    i = 0
    n = len(expanded) - 1
    while i < n:
        lo, hi = expanded[i], expanded[i+1]
        cp = lo | (hi << 8)
        if cp == 0:
            if len(cur) >= 2:
                strs.append("".join(cur))
                if len(strs) >= limit:
                    break
            cur = []
            i += 2
            continue
        if 0x20 <= cp < 0xFFFD and not (0xD800 <= cp <= 0xDFFF):
            cur.append(chr(cp))
        else:
            if len(cur) >= 2:
                strs.append("".join(cur))
                if len(strs) >= limit:
                    break
            cur = []
        i += 2
    return strs


def lang_stats(text: str) -> dict:
    hira = kata = cjk = 0
    for ch in text:
        o = ord(ch)
        if 0x3041 <= o <= 0x309F: hira += 1
        elif 0x30A1 <= o <= 0x30FF: kata += 1
        elif 0x4E00 <= o <= 0x9FFF: cjk += 1
    return {"hira": hira, "kata": kata, "cjk": cjk}


def main():
    path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    raw = open(path, "rb").read()
    db_type = struct.unpack_from("<i", raw, 0)[0]
    expanded = expand(raw[4:])
    data_size, row_cnt, col_cnt = struct.unpack_from("<iii", expanded, 0)
    print(f"type={db_type} data_size={data_size} rows={row_cnt} cols={col_cnt} expanded={len(expanded)}")
    strs = utf16_strings(expanded, limit) if db_type != 0 else []
    joined = "\n".join(strs)
    st = lang_stats(joined)
    print(f"字符串统计(前{limit}条): 平假名={st['hira']} 片假名={st['kata']} 汉字={st['cjk']}")
    verdict = []
    if st["hira"] or st["kata"]:
        verdict.append("含日文假名 → 日文文本")
    if st["cjk"] and not (st["hira"] or st["kata"]):
        verdict.append("纯汉字无假名 → 很可能是中文")
    print("判定:", "; ".join(verdict) or "样本不足")
    print("--- 字符串样例 ---")
    for s in strs[:limit]:
        print(repr(s[:60]))


if __name__ == "__main__":
    main()
