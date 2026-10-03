# 游戏数据准备指南(Steam 版《CLANNAD》)

本指南说明如何把自备的正版游戏数据整理成 rlvm-r 可以运行的形态。
**仓库与 APK 均不含任何游戏素材;数据仅在个人设备上使用。**

## 1. 获取数据

1. 在 Steam 购买并安装《CLANNAD》(App ID **324160**)。
   - Steam 版由 VisualArt's 官方维护,已通过更新加入**官方简体中文**,
     无需再应用任何民间汉化补丁;
   - 引擎为 RealLive 的 SE 改进版(RealLiveSE),与 rlvm 的重实现目标一致,
     社区已有在 rlvm(含 Android 端)上运行 Steam 版数据的成功记录。
2. 安装完成后,数据目录位于:

```
<SteamLibrary>\steamapps\common\CLANNAD\
```

判别标志:该目录下存在 `Gameexe.dat`(RealLive 引擎的全局配置文件,
rlvm 启动时的必需文件),以及大量 `SEEN*.txt` 剧本文件和 `.g00`(图形)、
`.nwa` / `.ogg`(音频)资源。

## 2. 校验数据完整性

```sh
python tools/check_data.py "C:\Program Files (x86)\Steam\steamapps\common\CLANNAD"
```

脚本会检查 `Gameexe.dat`、统计 `SEEN*` 剧本数量、识别字体文件并汇总体积。
只要 `Gameexe.dat` 存在且体积正常(数百 MB 以上),数据即可用。

## 3. 推送到手机

推荐用 adb(数据目录有数 GB,确保手机存储充足):

```sh
adb push "<steamapps>/common/CLANNAD" /sdcard/ClannadData/
```

也可以用 USB 大容量传输或任意文件管理器完成,目录位置无硬性要求
(rlvm-r 通过存储权限 + 文件夹选择器定位)。

## 4. rlvm-r 内的设置

| 设置项 | 位置 | 说明 |
|---|---|---|
| 游戏目录 | 主界面文件夹选择器 | 选中包含 `Gameexe.dat` 的目录 |
| 编码 | Settings → Encoding | 官方简中数据选 **CP936**;按目录保存在数据目录的 `.rlvm/encoding.cfg` |
| 字号/字体 | 暂未提供 | 上游 TO-DO 项;若默认字体不渲染中文,见"待验证事项" |

## 5. 待验证事项(首次运行时留意)

1. **中文如何生效**:桌面版 Steam 客户端通过 RealLiveSE 的中文启动模式
   显示简中;Android 端没有 launcher,预期流程是 rlvm 的编码覆盖(CP936)
   + 游戏自身语言配置。若首次启动显示日文:先在 rlvm-r 设置里切 CP936;
   仍无效时,对照桌面版 `Gameexe.dat` 与语言相关的配置键做最小修改实验。
2. **字体**:确认数据目录内是否自带 `.ttf/.ttc` 字体文件(`check_data.py`
   会列出)。Steam 版大概率自带简体字体;若没有,需要把一款中文 TTF 放入
   数据目录并研究 rlvm 的字体搜索路径(`rlvm/src/` 中 FreeType 相关代码)。
3. **特效兼容性**:转场/滤镜类指令可能有渲染差异,不影响通关可暂时忽略,
   有问题可对照上游 CONTRIBUTING.md 的 TO-DO 与 issue 反馈渠道。

## 6. 之后:《AIR》

同一引擎内核直接复用,只需换数据:AIR 需使用 **Standard Edition / HD**
(RealLive 版;2000 年原版是更早的 AVG32 引擎,rlvm 不支持)。Steam 版
AIR 的官方语言支持情况需另行确认;若无官方中文,则需评估民间汉化补丁
(编码 GBK)与 rlvm CP936 通道的配合,流程与本文档相同。
