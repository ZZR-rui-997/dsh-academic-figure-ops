# 案例库与配方索引

> 版式参考公开期刊图版与常见制图惯例：**只借鉴版式手法，不复制任何上游文件、图件或数据**。
> 19 份配方脚本、合成数据与预览图均由本包自行实现，可独立运行与再分发（MIT）。
> 配方只用于演示「图型—表达意图」的对应关系，不进入 skill 的判定逻辑。

## 目录结构（扁平，无子目录）

- `case_segNNN.md` —— 鉴赏卡（六段式：一句话/高级感/适用场景/有什么用/部件亮点/复现）
- `case_segNNN.py` —— 配方脚本（**本目录可直接运行**：`python case_seg001.py`）
- `case_segNNN.png` —— 已实跑落盘的成品图（19 配方全量实跑生成，逐张对应；
  **所有案例都用合成数据 + 固定 seed，可直接重跑**）
- `lib/paper_style.py` —— 共享样式模块（本 skill 重实现，figstyle 口径；**非原库文件**）
- `lib/newick.py` —— 系统发育树工具（seg012–015 用；本 skill 重实现）
- `lib/helpers/chord.py` —— 和弦图几何 patch（seg027 用；本 skill 重实现）

## 19 张清单

seg001 抖动散点叠柱+显著性支架（Nature, wow3）、seg002 双柱+误差棒、
seg003 分组柱、seg004 箱线+散点、seg005 小提琴、seg006 基因表达柱+显著性、
seg007 相关散点+回归、seg008 边际分布、seg009 双轴时序、seg010 堆叠面积、
seg011 电流密度极化、seg012 环形发育树、seg013 发育树圈图(二, wow3)、
seg014 树+热图环、seg015 树+柱状环、seg027 和弦图(wow3)、seg060 多边形雷达、
seg100 环状条形图(ES&T, wow3)、seg143 3D 双层填充地图(wow3)。

## 怎么用（画图前 30 秒）

1. 说需求 → 按卡 front-matter 的 `purpose` 字段（组间比较/趋势变化/相关关系…）找对应 seg 号；
2. 读该号 `.md` 卡（"部件亮点"记手法）；
3. 需要参考实现时直接跑 `python case_segNNN.py`（合成数据 seed 固定，出 png 看效果）；
4. 仿出的图过 `qa-checklist.md` C/D 验收后才能进论文——**案例是参考，验收线不变**。

## 与原库的差异（诚实声明）

- 原配方依赖其上游 `paper_style`/`newick`/`helpers.chord`，未随案例分发
  （曾经 19 个配方同时 import 失败，原因就是路径写死）。`lib/` 下三个模块是**本 skill
  按配方实际调用接口重实现**的，风格走本 skill 统一的 figstyle 口径（Times+SimSun、
  Okabe-Ito）——图的味道与原库不同属预期，配方教的是图型做法。
- 卡 front-matter 的 `input` 字段只标注数据形状（`long`/`xy`/`matrix`/`newick`/`edges`
  等），配方脚本各自用合成数据造出该形状，不需要外部数据文件。
- 原卡 `recipe:`/`preview:` 指向原库子目录结构，已改为本包扁平结构。

## 素材库扩展约定（往里加图）

- 每张新案例 = 一张卡（六段式）+ 配方（可跑）+ 成品 png；
- front-matter 必带 `purpose`（原库 11 类）与 `wow` 1–3；来源写进"复现"段。
