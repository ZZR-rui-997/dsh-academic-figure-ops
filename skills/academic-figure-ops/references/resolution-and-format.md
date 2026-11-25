# 分辨率与交付格式（期刊基线 + 换算做法）

> 本节来源：一份 SCI 期刊图片要求清单（出版社官网原文，逐条见 §二），
> 加上按正文宽度做的定量换算与实测。**通用基线是对的，但直接用会踩坑**——
> 见下面「⚠ 三条容易照抄出错的」。

## 一、一句话结论

**决定清晰度的不是 `savefig(dpi=...)` 这个参数，而是「落盘像素宽」。**
图会缩到正文宽度印刷（示例 14.65 cm = 5.7677 in），所以

```
有效分辨率 (dpi) = 落盘像素宽 ÷ 正文宽度英寸数（示例 5.7677）
```

要满足线条图 600 dpi，**像素宽必须 ≥ 3461 px**。这跟 PNG 里 `pHYs` 标的 300 无关。

## 二、期刊通用基线（投稿前以目标期刊 Guide for Authors 为准）

| 图类型 | 典型内容 | 通用最低 | 更严 |
|---|---|---|---|
| 线条图 Line Art | 纯图表、示意图、曲线、结构式 | **600 dpi** | 部分要 1000，极精细要 1200 |
| 照片/半色调 | 凝胶、显微、临床照片 | **300 dpi** | — |
| 组合图 Combination | 同图既有照片又有线条/文字 | **500 dpi** | 也有要求 600 |

主流出版社差异（**逐条从出版社官网抓原文核对**）：

| 出版社 | 线条图 | 照片/半色调 | 组合图 | 依据（官网原文） |
|---|---|---|---|---|
| Elsevier | **1000**（极细线 1200） | 300 | **500** | [artwork-types](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-types)：「minimum resolution of 1000 dpi (or 1200 dpi if the image contains very fine line weights)」/ 灰度 300 / 彩色 300 / 组合「Resolution 500 dpi」 |
| Springer Nature | **1200**（扫描或位图线条） | 300 | **600** | [期刊 Guide for Authors](https://link.springer.com/journal/11306/submission-guidelines)：「Scanned line drawings and line drawings in bitmap format should have a minimum resolution of 1200 dpi」/「Halftones…300 dpi」/「Combination artwork…600 dpi」 |
| Science (AAAS) | **1200** | 300 | 300 | [官方 guide to preparing figures](https://www.science.org/content/page/instructions-preparing-initial-manuscript)：「black and white line art…must be at least 1200 dpi」；**且 >600 dpi 生产端会降采样到 600，建议直接交 300–600** |
| Nature | 矢量优先 | **300** | — | [final-submission](https://www.nature.com/nature/for-authors/final-submission)：「All photographic images must be supplied at a minimum of 300 dpi at the maximum size they can be used」 |
| Cell Press | — | — | — | ⛔ **未核实，不要引用**。该社图片要求未从官网取到原文；网传"彩/灰 300、黑白 500、线条 1000"属**转述、未溯源**，不得当依据；保留此行只为提醒投稿前自己查 |
| Wiley | **>600** | **>300** | **按线条图办（>600）** | ✅ **已核实**（照 Wiley 官方 PDF 实读《Guidelines for the Preparation of Figures》[pb-assets 版](https://onlinelibrary.wiley.com/pb-assets/assets/16000722/Guidelines_for_the_Preparation_of_Figures_-_Final.pdf)，European Journal of Oral Sciences 页实例）：Resolution 表 Line art「**>600 dpi**」、Images「**>300 dpi**」；Important 注「a figure includes both line art and images → follow the **line art** guidelines」⇒ 组合图按 >600。另给**像素宽硬指标**：单栏 80 mm 宽 = **1890 px** @600 dpi / 945 px @300；整页 180 mm = **4252 px** @600 / 2126 px @300。格式 TIFF/EPS，单文件 <10 MB（zip/LZW 可），1 figure per file，命名 `Figure_1` |

> ⚠ **这张表的用法**：投稿前必须去**目标期刊自己的 Guide for Authors** 重取一次。
> 出版社层面的数字只是量级参考，同一出版社不同期刊会不一样（Springer 的 1200 是
> 该期刊页写的扫描/位图线条口径，不代表所有 Springer 期刊都要 1200）。
> Cell Press 行**没有**官网依据，不要引用；Wiley 行是
> 实读官方 PDF 得到的，可信。

### 二之二、图内字号也有官方下限（这条比 dpi 更容易被忽略）

分辨率只决定"清不清楚"，**字号决定"印出来还认不认得出"**。Science 的官方
《guide to preparing figures》(2026) 把字号写成了硬指标，原文：

| 项目 | Science 官方原文 | 示例实测（换算成印刷 pt） |
|---|---|---|
| 分幅标号 | 「Panel part labels are 9 point **bold**」 | 10.41 pt ✅ 数值够，但**未加粗** ⚠ |
| 轴标签/图内文字 | 「Axis labels or other type on the figure must be 8 pt」 | 10.41 pt ✅ |
| 最小字号 | 「Minimum font size is 6 points」 | 9.42 pt（刻度）✅ |
| 最小线宽 | 「At final print size, minimum line weight is .28 point」 | 0.65 pt ✅ |

> 换算方法（示例）：标签设定 23.666 pt（= `10.5 × 13/5.7677`），落盘 13.1133 in，
> 印刷 = 23.666 × 5.7677 ÷ 13.1133 = **10.41 pt**。刻度 21.412 → **9.42 pt**。

**⚠ 唯一真实缺口：分幅标号没加粗。** `figstyle.panel()` 里 annotate 没有
`fontweight`，`rcParams['font.weight']` 是 `'normal'`。国内学位论文/中文期刊一般
不强制，但投 Science 系（含 Science Advances）时必须加。要加就在调用处写
`ax.annotate(..., fontweight="bold")`，或给 `panel()` 传参——**目前没有这个参数，
需要时自己改**。

### 二之三、⚠ 一个会把人骗过去的测量陷阱（实测踩过）

**`Text.get_fontsize()` 在 `fig.canvas.draw()` 之前读到的是构造期快照，不是渲染值。**

曾据此报出「轴标签只有 4.398 pt，低于 Science 的 8 pt 下限」，看着像严重缺陷。
但用落盘 PNG 的像素做裁判：4 种调用顺序渲染出的图**逐字节完全相同**，底部轴名
墨迹行高 70 px——23.666 pt @300 dpi 的字高约 65–70 px，10 pt 只有约 28 px。
**所以真正印出来的是 10.41 pt，那个 4.398 pt 是假象。**

判据优先级：**落盘像素 > 任何 API 读数**。要验证字号，用 `check_figure.py`
（它量的是 PNG），不要读内存里的 `get_fontsize()`。

**格式选择**：

- 矢量图（线条图、示意图）→ 首选 **EPS / PDF**。放大清晰，线条图存 JPG 会有锯齿。
- 照片/位图 → **TIFF**（无损）或最高质量 JPEG；PNG 也可接受。避免 GIF/BMP。
- 组合图 → 整体提交高分辨率 TIFF；或 PDF 但确保内嵌照片分辨率足够。

## 三、⚠ 三条容易照抄出错的

### ⚠ 1. "脱离尺寸谈 DPI 没有意义"——这句话对，但推下去会推翻直觉做法

常见说法：「Elsevier 对单栏照片要求最小宽度 1,063 px，这正是基于 300 dpi 和单栏宽度换算得出的」。
**这个算术核过，完全对**：90 mm ÷ 25.4 × 300 = 1063.0 px。

但正因为要按尺寸换算，就会出现这个反直觉结果：

| 配方 | 印刷字号 | 有效分辨率 |
|---|---|---|
| figsize **13 in** @300dpi + `use_size(13)` | 10.4 pt ✅ | **676 dpi** ✅ |
| figsize **5.77 in** @300dpi + `use_size(5.77)` | 10.5 pt ✅ | **300 dpi** ❌ |
| figsize 5.77 in @600dpi | 10.5 pt ✅ | 600 dpi ✅ 但文件 4 倍大 |

**所以「把画布改成 5.77 in 最省事」是错的建议**（第一版曾这么写，已改）。
5.77 in @300dpi 只有 1730 px，缩到 146.5 mm 就是 300 dpi，够照片不够线条图。

**达标配方：`figsize 宽 12–14.5 in` + `use_size(同值)` + `dpi=300`。**
画布大 → 字号有放大余地（10.4 pt）+ 像素宽足够（3600–4350 px → 624–754 dpi），一举两得。
这不是绕远路，实测那 10 张就是这么做的。

> ⚠ **上面 624–754 dpi 只在不裁切时成立。** 该区间换算的是 `figsize宽 × 300 ÷ 5.7677`，
> 前提是**落盘宽 ≈ figsize 宽**——实测那 10 张的 tight 比值 0.96–1.01，所以对得上。
> 若存图带 `bbox_inches="tight"`（`fit_and_save` 恒带），落盘宽只有 figsize 的 ≈**0.82** 倍：
> 同为 13 in @300dpi，实测 **3209 px → 556 dpi**（不到 600），14 in → 598 也差一点。
> 走 `fit_and_save` 时请把画布给到 **≥14.5 in**：15 in → 3692 px → **640 dpi**、16 in → **682 dpi**。

### ⚠ 2. 严禁在 Photoshop 里"重定图像像素"提高 DPI

补一句判据：**插值出来的像素没有信息量**。
图全由脚本生成，**应该在脚本里加大画布/提高导出 dpi，绝不后期拉**。这条正好和
"可复现"原则一致——图能从脚本一键重跑，就不需要任何后期修图步骤。

### ⚠ 3. 矢量格式与 600 dpi 的关系：线条图根本不该比 dpi

线条图（折线、柱、示意）**优先出矢量 PDF/EPS**，矢量没有 dpi 概念，无限放大都清晰。
只有**位图**（云图、填色场、照片）才受 dpi 约束。

按图件类型分工：

| 图件 | 建议格式 | 理由 |
|---|---|---|
| 几何/统计图（折线、柱、散点） | **PDF**（+PNG 备份） | 纯矢量，无分辨率问题 |
| VOF 云图（contourf 填色场） | **PNG 600+** 或 PDF | 含大量填色，PDF 也能矢量但体积大；位图按 600 走 |
| 正文插图（Word 里那张） | PNG 300–600 | Word 内嵌，PDF 不好排版 |

> 注：一组实测交付是 **PNG @300dpi + 有效 535–760 dpi**（实测），
> 已经超过 600 线（除两张三维图 535/588）。**没出 PDF 只是既有状态，不是缺陷**，
> 但若改投期刊，建议补 PDF 版（脚本加一行 `savefig("x.pdf")` 即可）。

### ⚠ 4. 矢量图要"可编辑"，有三条 rcParams 必须知道（实测）

matplotlib 一行 `savefig("x.pdf")` 出的就是矢量图（PDF/SVG/EPS 都支持），
**线条和填色天然可编辑**。但"文字"这一项取决于三条 rcParams，默认值**都不利于编辑**：

| rcParams | matplotlib 默认 | 含义 | 要可编辑就改成 |
|---|---|---|---|
| `pdf.fonttype` | **3**（Type 3） | PDF 里文字存成"字形程序"，多数软件**选不中、改不了** | **42**（TrueType 嵌入，AI/Word 里文字可选中可改字） |
| `ps.fonttype` | **3** | 同上（EPS） | **42** |
| `svg.fonttype` | **'path'** | SVG 里文字被**转成路径**，完全不是文字了 | **'none'**（保留 `<text>`，可改字改字体） |

实测（matplotlib 3.11.2）：`pdf.fonttype=3 / ps.fonttype=3 / svg.fonttype='path'`。
所以**默认导出的矢量图，"可编辑"只对图形对象成立，文字不可编辑**。

要可编辑的矢量图，画图前设一次：

```python
import matplotlib as mpl
mpl.rcParams["pdf.fonttype"] = 42   # PDF 文字用 TrueType 嵌入，可编辑
mpl.rcParams["svg.fonttype"] = "none"  # SVG 保留真文字
# EPS 用 ps.fonttype=42，但注意 EPS 不支持半透明，VOF 云图慎用
```

代价要知道：`fonttype=42` 会把整张字体表嵌进文件（中文字体尤其大）——但实测
下来并不吓人（见下），期刊一般反而**要求** Type 42/TrueType（Type 3 有的出版
流程会拒），所以**要文字可编辑就 42，没有别的选项**。SVG 的 'none' 则是
编辑器（AI/Figma/Inkscape）里改字的前提。

`figstyle.apply_style()` 目前**没设**这三条（属按需开关，不是默认）。
要交"可编辑矢量图"时，在脚本里加上面三行即可，不必改 `figstyle`。

**实测验证**：设 `pdf.fonttype=42` 后出的 PDF 用 pypdf 检查，TimesNewRomanPSMT 与 SimSun
两个 Type0 字体的 FontDescriptor 均**嵌 FontFile2（TrueType）、无 FontFile3**——
即文字以真字体进 PDF，AI/Word 里可选中改字；同参数出的 SVG 保留 `<text>`
标签（11.3 KB），文字可直接改。两条注意事项：
①`fit_and_save` **只能出位图**——它内部用 PIL 量落盘宽（`saved_width_in`），
PIL 读不了 PDF/SVG 会抛 `UnidentifiedImageError`。矢量图请用
"PNG 探针收敛一次拿到 `fit_scale` → 用同 scale 直接 `fig.savefig('x.pdf')`"
的两步法。②同一张 13 in 图：
PDF 29.8 KB / SVG 11.3 KB / PNG 3934px 59.6 KB——矢量并不更大，放心用。

**与"导出尽可能高清、方便以后编辑"这条要求的对照**：
- 位图路线：dpi 300 + 大画布（本文件 §三 的配方），已覆盖；
- 矢量路线：PDF/SVG + `fonttype=42`/'none'，文字才真正"以后能编辑"。
两条线是**并存**的：投稿/打印位图或矢量都行，留底编辑建议**矢量 + 42**。

## 四、自查动作

```bash
# 只看字号
python check_figure.py --pair canvas_map.txt

# 字号 + 分辨率（线条图 600 / 照片 300）
python check_figure.py --pair canvas_map.txt --min-eff-dpi 600
```

输出里「有效dpi」一列就是 `像素宽 ÷ 正文宽度英寸数`（示例 5.7677）。
两个判据独立：**字号达标但分辨率不够，仍判 FAIL**，修复建议会分开给。

## 五、一份实测盘点（作基线参考）

### 一组 10 张已定稿图：535–760 dpi，8/10 ≥600

| 图 | 像素宽 | 有效 dpi | 判定 |
|---|---|---|---|
| 图 1 | 3934 | 682 | ✅ |
| 图 2 | 3629 | 629 | ✅ |
| 图 3 | 3518 | 610 | ✅ |
| 图 4 | 3631 | 630 | ✅ |
| 图 5 | 3391 | 588 | ⚠ 差一点（三维图） |
| 图 6 | 3790 | 657 | ✅ |
| 图 7 | 3906 | 677 | ✅ |
| 图 8 | 3854 | 668 | ✅ |
| 图 9 | 4384 | 760 | ✅ |
| 图 10 | 3087 | 535 | ⚠ 三维图 |

（编号与 `hard-params.md` §六 的配对表一致：图 5 = 三维面图，图 10 = 三维面图；
两张偏低的原因：三维图 `bbox_inches='tight'` 后画布缩水到 76%（其余 96–101%），
落盘宽比设定的小。修法：figsize 加宽到 15 左右，或 dpi 提到 400。）

### 一批 22 张 CFD 云图：247–390 dpi，**0/22 ≥600**，8 张低于 300

全部不合格。实测落盘宽 **8.08–12.50 in**（不是"画布太小"——画布其实够宽），
根因是两条叠加：

1. **导出 dpi 只用了 150 或 180**（22 张全部如此，无一张用 300）：像素宽 = 落盘宽 × dpi，
   dpi 砍一半，像素宽也就砍一半。
2. **字号没跟着画布放大**（没有 `use_size`）：10.5 pt 定值配 8–12.5 in 画布，
   印刷出来只剩 4.84–7.49 pt。

重画时按「figsize 12–14.5 in + use_size(同值) + **dpi 300**」即可同时解决字号
（现 4.84–7.49 pt → 10.4 pt）和分辨率（现 247–390 dpi → 624–754 dpi）两个问题。
注意 dpi 这一项必须真的改，光把画布调宽是没用的。
