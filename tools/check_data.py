#!/usr/bin/env python3
"""RealLive 游戏数据目录校验脚本。

用法:
    python tools/check_data.py <游戏数据目录>

检查项:
    - Gameexe.dat 是否存在(rlvm 启动的必需文件)
    - SEEN* 剧本文件数量
    - 数据目录总体积
    - 自带字体文件(.ttf/.ttc/.otf)
"""

import sys
from pathlib import Path

REQUIRED = ["Gameexe.dat"]
FONT_EXTS = {".ttf", ".ttc", ".otf"}
MEDIA_MIN_BYTES = 200 * 1024 * 1024  # 正常数据目录应在数百 MB 以上


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"[错误] 目录不存在: {root}")
        return 1

    ok = True

    for name in REQUIRED:
        p = root / name
        if p.is_file():
            print(f"[必需] {name}: 存在({human(p.stat().st_size)})")
        else:
            print(f"[必需] {name}: 缺失 —— 这不是 RealLive 数据目录")
            ok = False

    seen = sorted(root.glob("SEEN*"))
    print(f"[剧本] SEEN* 文件: {len(seen)} 个"
          + ("(正常)" if len(seen) > 0 else "(异常:未找到任何剧本文件)"))
    if not seen:
        ok = False

    fonts = [p for p in root.rglob("*") if p.suffix.lower() in FONT_EXTS]
    if fonts:
        print(f"[字体] 自带字体文件: {len(fonts)} 个")
        for f in fonts[:10]:
            print(f"       - {f.relative_to(root)}")
    else:
        print("[字体] 未发现自带字体文件(若中文不渲染,可能需要补充)")

    total = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
    print(f"[体积] 数据目录总计: {human(total)}")
    if total < MEDIA_MIN_BYTES:
        print("[提示] 体积偏小,可能是不完整拷贝(全语音版应为数 GB)")

    subdirs = sorted(d.name for d in root.iterdir() if d.is_dir())
    if subdirs:
        print(f"[子目录] {', '.join(subdirs[:15])}{' ...' if len(subdirs) > 15 else ''}")

    print("\n结论:", "数据可用,可推送到手机。" if ok else "数据不完整,请重新检查来源。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
