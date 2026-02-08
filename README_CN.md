# Z.A.T.O. // 我爱这世界及其中的一切 - PS Vita 移植版

[EN](README.md)

![Screenshot](ScreenShot.jpg)

Z.A.T.O. // I Love the World and Everything In It 的 PS Vita 移植脚本。

## 依赖项

- Python 3.7+
- Pillow >= 9.0.0
- 其他依赖项在脚本中会自动检查和安装

## 使用说明

### 第一步：在 PC 上准备游戏文件

1. 在 Steam 上安装 [Z.A.T.O. // I Love the World and Everything In It](https://store.steampowered.com/app/2889740/ZATO__I_Love_the_World_and_Everything_In_It/)，这是一个非常棒的免费视觉小说游戏，时长约4个小时。
2. 如果你需要翻译，请自行在steam或其他地方寻找合适的翻译补丁并按要求安装。注意：本移植不保证翻译可以正常运行，但我个人测试时使用的中文翻译补丁运行基本正常，希望其他语言的补丁也可以正常进行。
3. 在 Steam 库中右键点击游戏，选择 `管理 -> 浏览本地文件`。
4. 将 Steam 游戏文件夹中的`game/`复制到此仓库的根目录（包含 `scripts_for_vita/` 的文件夹）。

### 第二步：运行优化脚本（必需）

**⚠️ 你必须运行以下其中一个脚本**

**选项 1：真无损版本（纯解包并删除视频，不做其他优化）**
```bash
python scripts_for_vita/run_true_lossless.py
```
仅执行解包和移除 WebM 视频，不修改任何图片或 GUI，保持游戏资源完全原汁原味。

**选项 2：无损优化（进行Vita分辨率的优化，让文本更易读，可能导致部分翻译补丁表现异常）**
```bash
python scripts_for_vita/run_lossless_w_gui.py
```
在选项 1 的基础上，额外将原游戏720P的分辨率进行针对PsVita的 GUI 缩放和图片尺寸优化。

**选项 3：有损压缩（更流畅的游戏体验）**
```bash
python scripts_for_vita/run_compressed.py
```
在选项 2 的基础上，对图像和音频进行有损压缩，获得最小的文件体积，降低Vita IO压力，得到更流畅的游戏体验。

**执行过程中如果有未安装的依赖项，请交互并自动安装。等待优化完成后继续下一步！**

### 第三步：将优化后的文件复制到 Vita

1. 下载 VPK 文件并安装到你的 PS Vita
2. 将**优化后的** `game/` 文件夹（刚刚由脚本处理的）复制到 `ux0:app/ZATO01986/`
3. 在 Vita 上运行 Z.A.T.O（首次启动可能需要 5-10 分钟）
4. Have fun!

## 需要注意的问题

- **首次加载时间：** 由于资源缓存和Python预编译，游戏首次启动可能需要 5-10 分钟，第二次启动速度就会快很多。
- **资源加载卡顿：** 当加载不在缓存中的新资源时（图片，音频），游戏会出现卡顿。这是 Vita IO 速度的硬件限制。
- **不支持视频：** Ren'Py Vita 目前不支持视频播放，因此所有视频将被`remove_op.py`脚本移除（幸运的是此游戏只包含开场动画视频）。[原作开场动画制作相当精良，强烈建议观看](https://www.youtube.com/watch?v=qjlY1ksx4tw)。
- **内存限制：** 某些高分辨率资源可能会导致内存问题。如果遇到崩溃，请使用有损压缩选项。
- **存档数据：** 存档文件存储在 Vita 上的标准 Ren'Py 位置。游戏使用与 PC 版相同的存档格式。如果你更改了`game/`文件夹，存档似乎会失效，也有可能是第一次安装之后会失效，我没有进行此处的充分验证。

## 各脚本详细说明，供想此了解移植是如何进行的人参考

### 工作流脚本

#### run_true_lossless.py

执行顺序：unpack_and_decompile.py → remove_op.py

#### run_lossless_w_gui.py

执行顺序：unpack_and_decompile.py → remove_op.py → optimize_gui.py → optimize_images.py

#### run_compressed.py

执行顺序：unpack_and_decompile.py → remove_op.py → optimize_gui.py → optimize_images_v2.py → optimize_snow.py → optimize_audio.py

### 独立功能脚本

#### unpack_and_decompile.py
解包 .rpa 资源文件并将 .rpyc 文件反编译为可编辑的 .rpy 脚本。自动检测并安装所需依赖（rpatool、unrpyc）。

处理步骤：
1. 查找并解压所有 .rpa 文件
2. 反编译所有 .rpyc 文件
3. 删除残留的 .rpa 文件
4. 删除反编译后的 .rpyc 文件

#### optimize_gui.py
将 GUI 元素缩放以适应 PS Vita 屏幕分辨率（960x544）。将原始分辨率 1280x720 按 0.75 比例缩放，自动创建 .backup 备份文件。

主要修改：
- 缩放所有 GUI 数值配置（文本框、按钮、边框等）
- 调整字体大小保持可读性
- 修改 gui.init 为 960x544
- 为对话文本添加滚动支持（viewport）

#### optimize_images.py
无损调整图片尺寸以适应 PS Vita 屏幕，保持原始图像质量。

- 目标目录：`game/images/` 和 `game/gui/`
- 使用 LANCZOS 重采样保持画质
- JPEG 保存质量 95%

#### optimize_images_v2.py
有损调色板压缩版本，降低IO压力。使用 pngquant（自动下载）或内置 MAXCOVERAGE 算法，获得更好的压缩率。

压缩策略：
- 透明 PNG → 64 色调色板
- 大文件 PNG（>150KB）→ 128 色调色板
- 小文件 PNG → 32 色调色板
- JPEG → quality 60

#### optimize_audio.py
自动根据文件类型和大小自动选择最佳压缩策略进行音频压缩，降低IO压力。自动下载 ffmpeg（如未安装）。

压缩策略：
- BGM（>1MB）：MP3 64kbps / OGG quality 3
- 音效（<100KB）：MP3 96kbps / OGG quality 5
- 语音（voice/*）：MP3 80kbps / OGG quality 4
- WAV/其他格式：转换为 OGG

#### optimize_snow.py
优化雪花粒子效果以在 Vita 上获得更好性能，修改 `game/snowblossom.rpy`。

优化内容：
- 最大粒子数：50 → 25
- 深度层数：10 → 5
- 缓存屏幕尺寸避免每帧访问 config
- 使用局部变量减少属性访问
- 优化边界检查逻辑

#### remove_op.py
扫描并移除 WebM 视频引用（Vita 不支持视频播放）。
```bash
python remove_op.py              # 默认：扫描并清理
python remove_op.py --dry-run    # 预览模式：显示将要执行的操作
python remove_op.py --restore    # 恢复模式：取消注释 WebM 代码
python remove_op.py --scan-only  # 仅扫描：显示发现的 WebM 文件和引用
```
处理内容：
1. 扫描所有 .webm 文件
2. 注释掉包含 movie_cutscene 的代码行
3. 删除 .webm 文件（恢复模式下不删除）

#### generate_sys_imgs.py
从游戏资源生成 PS Vita 系统图片（LiveArea 用），此脚本的结果已经打包在vpk中，仅作为流程参考。

生成文件：
- `scripts_for_vita/sce_sys/icon0.png` (128x128) - 游戏图标
- `scripts_for_vita/sce_sys/livearea/contents/startup.png` (280x158) - 启动图
- `scripts_for_vita/sce_sys/livearea/contents/bg.png` (960x544) - 背景图
- `scripts_for_vita/sce_sys/pic0.png` (960x544) - 封面图

## 致谢

- [Z.A.T.O. // I Love the World and Everything In It](https://store.steampowered.com/app/2889740/ZATO__I_Love_the_World_and_Everything_In_It/)：我爱这个游戏
- [Ren'Py PSVita](https://github.com/SonicMastr/renpy-vita)：多亏了它，我才能将这个游戏移植到 Vita 上
- [RenPy-Vita-8](https://github.com/Grimiku/RenPy-Vita-8)：多亏了它，python3的renpy游戏才能成功移植
- [Kimi K2.5](https://www.kimi.com/blog/kimi-k2-5.html)：我使用这个LLM编写了此仓库的代码和文档
- 希望此仓库也能帮助其他人移植更多 Ren'Py 游戏到 Vita
