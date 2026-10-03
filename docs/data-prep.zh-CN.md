# 游戏数据准备指南(Steam 版《CLANNAD》)

> **2026-10-03 实测更新**:Steam 版《CLANNAD》(简中更新后)的引擎是
> **SiglusEngine**,不是 RealLive——以安装目录实机文件为准
> (`SiglusEngine_Steam.exe`,无任何 `SEEN*` 剧本文件)。因此 **rlvm 无法运行
> Steam 版数据**;经实测验证可行的运行时是 **[siglus_rs](https://github.com/xmoezzz/siglus_rs)**
> (SiglusEngine 的 Rust 跨平台重实现,MPL-2.0)。本文档记录实测过程与结论。

## 1. 实机目录结构(简中 depot)

```
steamapps/common/CLANNAD/
├── SiglusEngine_Steam.exe   # 引擎主程序(密钥自动恢复的输入)
├── GameexeZH.dat            # 简中版全局配置(加密)
├── SceneZH.pck              # 简中版剧本包(~14MB)
├── dat/                     # 系统数据库 text*.dbs、自带字体 NotoSansMonoCJKsc-Regular.otf
├── g00/  bgm/  koe/  wav/  mov/  gan/   # 图形 / 音乐 / 语音 / 音效 / 视频
└── SAVEDATA/  savedata_zh/
```

注意:按 Steam 语言仓库机制,**简中安装不含日文基础包**(没有 `Scene.pck` /
`Gameexe.dat`)。运行时重实现(siglus_rs)默认查找 `Scene.pck`,需要下述组装步骤。

## 2. 桌面端实测(已验证 ✓,2026-10-03)

环境:Windows 10,Steam 简中安装(4.5 GB),siglus_rs 最新预发布 `siglus.exe`。

1. 从 [siglus_rs releases](https://github.com/xmoezzz/siglus_rs/releases)
   下载 `siglus.exe`(Windows x86_64);
2. 组装测试目录(避免复制 4.5 GB,大目录用 NTFS 目录联接):

```
clannad_zh/
├── SiglusEngine_Steam.exe   # 复制(引擎从中恢复资源解密密钥)
├── Gameexe.dat              # ← 复制 GameexeZH.dat 并改名
├── Scene.pck                # ← 复制 SceneZH.pck 并改名
├── g00/ bgm/ koe/ wav/ mov/ gan/ dat/   # ← 目录联接(junction)到 Steam 安装目录
```

3. 无头验证(引擎自带截图模式):

```sh
./siglus.exe --project-dir <clannad_zh目录> --capture-png title.png \
             --capture-after-frames 1500 --exit-after-capture
```

**实测结果**:自动完成 Siglus EXE 密钥恢复 → 解密 Gameexe.dat → 剧本字节码
全部识别(`unknown_forms=0, unknown_elements=0`)→ 依次渲染
`_system_start`(版权警告页)与 `_system_title`(HD 标题画面,菜单
NEW GAME/LOAD/CONFIG/STAFF/EXIT 与 ©VISUAL ARTS/Key 均正确)。

## 3. Android 端

siglus_rs 官方 release 直接提供 `app-release.apk`(~157MB,arm64-v8a),
同一引擎。数据准备原则相同:手机上需要一个**组装后**的数据目录
(根目录含 `SiglusEngine_Steam.exe`、`Gameexe.dat`、`Scene.pck` 与各资源
目录)。把 Steam 目录拷到手机时,复制 `GameexeZH.dat`/`SceneZH.pck` 改名,
其余目录原样保留即可(手机上直接物理复制,不需要联接)。

## 4. 已知小问题(不影响验证结论)

| 现象 | 说明 | 处置建议 |
|---|---|---|
| 配置字体未命中 | 引擎找 "Noto Sans Mono CJK SC Regular" 未果,回落内置字体 | `dat/` 自带 `NotoSansMonoCJKsc-Regular.otf`,后续研究 siglus_rs 字体加载路径接入 |
| `DATABASE.21` 缺失 | Steam 简中 depot 本身无 `dat/text21.dbs`(00–20、22、23 存在) | 引擎仅记 note,运行无碍;亦可向上游反馈 |
| 系统 UI 文本为日/英 | `_system_start`/`_system_title` 等系统场景沿用原版文本 | 原版即如此;故事文本走 `SceneZH.pck` 简中 |

## 5. 两条路线的现状(仓库方向待定)

| | 路线 A:siglus_rs(当前可行 ✓) | 路线 B:rlvm(原计划) |
|---|---|---|
| 引擎 | SiglusEngine 重实现(Rust,活跃) | RealLive 重实现(C++,成熟) |
| 数据 | **Steam 版直接可用**(官方简中自带) | 需 2004–2006 年 RealLive 版 CLANNAD + 民间汉化补丁 |
| Android | 官方 `app-release.apk` 现成 | rlvm-r 需自行构建 |
| 本仓库 rlvm-r 壳 | 不适用(需要换基座或仅作参考) | 适用 |

## 6. 仍然有效的原则

- 数据仅个人使用,不入库、不分发、不上公开网盘;
- 仓库只存引擎/文档/工具,`data/` 永远在 `.gitignore` 里。

## 7. 已落地的修复:官方简中文本 + 字体(2026-10-03)

实测确认:Steam 简中版的 `dat/text*.dbs` 是**双语数据库**——
`call_no=0` 列存日文、`call_no=2` 列存简中(人名表 `text23.dbs` 同理),
而 siglus_rs 按场景固定读取 `call_no=0`(日文列)。修复(纯数据层,无需改引擎):

```sh
# 1) 交换 call_no=0/2 两列并重加密(静态 XOR 密钥,工具见 tools/)
python tools/dbs_swap_cn.py <steam>/dat/text00.dbs text00.dbs   # 23 个文件逐个处理
# 2) 字体:引擎只搜索 <数据目录>/font|fonts/,把自带字体放进去
mkdir -p <数据目录>/font
cp <steam>/dat/NotoSansMonoCJKsc-Regular.otf <数据目录>/font/
# 3) 重加密后的 23 个 text*.dbs + font/ 一起放入手机数据目录
```

桌面端已验证:开场对白完整显示简体中文(「一望无际的白色世界…」),
字体渲染无缺字。个别开场短句(「一面、」「雪…」)疑似场景内嵌日文,
暂未处理。`tools/dbs_decode.py` 可独立解码 DBS 检查内容。
