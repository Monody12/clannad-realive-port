# CLANNAD · RealLive 跨平台移植工程(个人学习用途)

[English(上游说明)](README.md) | 简体中文

本项目基于开源 RealLive 引擎重实现 [rlvm](https://github.com/eglaysher/rlvm)
及其 Android 原生移植 [ChrisTVH/rlvm-project](https://github.com/ChrisTVH/rlvm-project)
(rlvm-r),目标是:**在不借助任何"模拟器 App"(Kirikiroid2、PPSSPP 等)的前提下,
把《CLANNAD》装进我自己的 Android 手机游玩**。

工程组织方式参考
[shuimo0413/yosuga-no-sora-remake](https://github.com/shuimo0413/yosuga-no-sora-remake)
—— 一个把 Kirikiri Z 引擎重实现为 krkrsdl2 并覆盖 Windows / macOS / Linux /
iOS / Android / OpenHarmony 的完整游戏工程。两者的架构思想一致:
**引擎源码入库,游戏数据不入库,数据由使用者自备。**

## 与缘之空项目的结构对应

| yosuga-no-sora-remake | 本项目 |
|---|---|
| `src/`(krkrsdl2 引擎) | `rlvm/`(RealLive 重实现,SDL2 C++,SCons) |
| `android-project/`(Gradle + NDK 壳) | `rlvm-r/`(Kotlin + NDK r27c,产物为独立 APK) |
| `data/`(git 外发布) | 不入库 —— 数据由使用者自备,见[数据准备指南](docs/data-prep.zh-CN.md) |
| `platform/windows-krkrz/` | 无对应(桌面端直接用 rlvm 本体验证) |
| `BootstrapActivity`(首启下载数据) | 无需(个人使用:数据一次性推送到手机存储) |
| `content-manifest.json`(SHA-256 清单) | `tools/check_data.py`(轻量完整性校验) |
| 各平台 GitHub Actions 发布 | `.github/workflows/build.yml`(云端构建 debug APK) |

## 仓库结构

```
clannad-realive-port/
├── README.md                 # 上游英文说明
├── README.zh-CN.md           # 本文件(主文档)
├── LICENSE.md                # GPLv3(继承上游 rlvm)
├── CONTRIBUTING.md           # 上游贡献指南(含功能完成度清单)
├── docs/
│   └── data-prep.zh-CN.md    # 游戏数据准备指南(Steam 版 CLANNAD)
├── tools/
│   └── check_data.py         # RealLive 数据目录校验脚本
├── rlvm/                     # 引擎本体(C++,含 encodings/ 编码支持:CP932/CP936/CP949/UTF-8)
│   ├── src/                  #   libreallive/ 解析 RealLive 文件格式,machine/ 字节码虚拟机
│   ├── vendor/               #   第三方库
│   └── scripts/
└── rlvm-r/                   # Android 移植(Kotlin,包名 io.github.rlvm)
    ├── app/                  #   MainActivity / GameActivity(SDLActivity)/ SettingsActivity
    ├── scripts/build.sh      #   原生库构建:自动下载 NDK r27c、SDL2 并编译出 libgame.so
    └── scripts/patches/
```

## 游戏数据(重要)

- **本仓库不包含、也不发布任何游戏素材。** 游戏数据仅限使用者自备(个人学习
  用途,不用于分发、传播或任何商业目的)。
- **2026-10-03 实测结论**:Steam 版《CLANNAD》(简中 depot)的引擎是
  **SiglusEngine**(`SiglusEngine_Steam.exe`,无 SEEN 剧本文件),**rlvm 无法
  运行该数据**;经本机实测,**[siglus_rs](https://github.com/xmoezzz/siglus_rs)**
  (SiglusEngine 的 Rust 跨平台重实现)可直接运行 Steam 简中数据,已渲染出
  正常的启动页与 HD 标题画面(零未知字节码)。详见
  **[docs/data-prep.zh-CN.md](docs/data-prep.zh-CN.md)**。
- 仓库当前基座(rlvm-r)对应"RealLive 版数据 + 民间汉化"路线;采用
  siglus_rs 路线时数据准备与运行时按实测文档操作,仓库基座调整见文档第 5 节。

## 构建 APK

### 方式一:GitHub Actions 云端构建(推荐,本地零环境)

仓库已带现成工作流(`.github/workflows/build.yml`):

1. GitHub 仓库页 → **Actions** → **Build rlvm-r APK** → **Run workflow**;
2. 构建完成后在该次运行页面下载 artifact `rlvm-r-debug-apk`,得到 APK。

Runner 上自动完成:JDK 21 安装、NDK r27c 下载、SDL2/Boost 等依赖编译、
rlvm 引擎交叉编译(`libgame.so`,arm64)、Gradle 打包 debug APK。

### 方式二:本地构建

需要 JDK 21、Android SDK(Platform 36)、NDK r27c、scons、cmake:

```sh
cd rlvm-r
./scripts/build.sh --arch arm64   # 编译原生库(首次会自动下载 NDK 与依赖)
./gradlew assembleDebug           # 打包 APK
```

产物:`rlvm-r/app/build/outputs/apk/debug/app-debug.apk`。

## 安装与运行

```sh
adb install app-debug.apk
adb push <游戏数据目录> /sdcard/ClannadData/
```

1. 安装并启动 App(包名 `io.github.rlvm`);
2. 授予存储权限,通过内置**文件夹选择器**选中数据目录;
3. 若文本显示异常,进入 **Settings → Encoding** 选择 **CP936(GBK 简体中文)**
   (配置按游戏目录保存在 `.rlvm/encoding.cfg`)。

## 已知待验证事项

- siglus_rs 路线:Android `app-release.apk` 实机安装与数据目录选择、
  简中故事文本实读、自带 Noto 字体接入(`dat/NotoSansMonoCJKsc-Regular.otf`)、
  长流程游玩稳定性;
- rlvm-r 路线(若采用):需 RealLive 版 CLANNAD(2004–2006)数据与 GBK 汉化
  补丁的配合验证。

## 个人使用声明

本项目仅供个人学习与技术研究,游戏脚本、图形、音频、视频等所有素材的权利归
VISUAL ARTS / Key 所有。本项目不分发、也不以任何形式传播游戏数据。

## 许可证

引擎及本工程沿用 **GNU GPL v3**(见 [LICENSE.md](LICENSE.md)),这是上游 rlvm
的许可证,由其传染性决定本工程整体必须以 GPLv3 开源。

致谢:
- [eglaysher/rlvm](https://github.com/eglaysher/rlvm) —— RealLive 重实现原作
- [xyzz/rlvm](https://github.com/xyzz/rlvm) 与
  [xyzz/rlvm-android](https://github.com/xyzz/rlvm-android) —— Android 移植奠基
- [ChrisTVH/rlvm-project](https://github.com/ChrisTVH/rlvm-project) —— 现行维护的
  rlvm-r
- [shuimo0413/yosuga-no-sora-remake](https://github.com/shuimo0413/yosuga-no-sora-remake)
  —— 工程组织方式的参考范本
