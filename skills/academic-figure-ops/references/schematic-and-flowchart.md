# 示意图 / 流程图的画法规程（双轨）

> 本文件管**非数据图**——引言的技术路线图、试验章节的流程/装置示意、机制对比图、
> 文献定位图（taxonomy）。数据图（折线/柱状/散点/云图）**不归这里**，见
> `chart-selection.md` 与 `cfd-figure-patterns.md`。
>
> 画法方法论内化自四家开源仓库（逐节来源见文末声明）。**只借方法论与体例，
> 配色、字号、正文宽度一律换成本规程的口径**；未照抄任何一段代码或配色。

## 0. 双轨决策

| 轨 | 工具 | 什么时候用 |
|---|---|---|
| **A 手绘轨** | draw.io / PPT / Illustrator | 需要反复接受批注修改的图（导出 PNG 交批注，改完再导）；第一张示意图默认走这轨 |
| **B 代码轨** | TikZ（Overleaf 编译） | 同构迭代 ≥5 版的图（改一处布局全局联动）；或需要精确对齐时 |

两轨落盘规格**完全一致**（见下），切换轨道只换画法、不换规格。
AI 生图（DALL·E / Gemini 等）**不进正文**：不可复现、不可编辑、审稿无法溯源。
它的 prompt 骨架思想（"KEY CONTRIBUTION 组件视觉强调"）已吸收进 §4，
但生成图本身最多用于灵感草稿。

## 1. 判据：这张图归谁管

> 借鉴自 zLanqing figure_synthesis_guide 的分界判据（原文：
> "If a figure requires experimental data to render, it goes through /viz.
> If it illustrates structure, flow, or concepts, it comes here."）。

**要实验数据才能画的 → 数据图**（本 skill 的 matplotlib 部分）；
**画的是结构、流程、概念的 → 本文件**。

常见分界实例：
- 数据图：流量-水压曲线、VOF 云图、黏度时程 → matplotlib
- 示意图：技术路线图（文献→理论→数值→试验→结论）、双组分灌注工艺流程、
  介质中扩散机制示意、"本文方法 vs 现有方法"对比图 → 本文件

## 2. 七原型 → 论文场景映射

> 借鉴自 zLanqing 七原型表（architecture_overview / pipeline_flow /
> component_detail / concept_illustration / comparison_schematic / taxonomy /
> deployment）。这里按实验/数值类论文改写：

| 原型 | 常见对应 | 典型位置 | 默认轨 |
|---|---|---|---|
| architecture_overview | 技术路线图（研究总体框架） | §1 引言 | A（常需反复改） |
| pipeline_flow | 试验/模拟流程图（试样制备→加载或求解→监测→分析） | 试验章节、数值章节 | A |
| component_detail | 装置示意（泵-管路-试验段-传感器细节） | 试验章节 | A |
| concept_illustration | 机制示意（输运-扩散-沉积的时空演化） | §1 引言 / §2 综述 | A |
| comparison_schematic | "现有方法失败 vs 本方法可行"结构对比 | §2 综述末尾 | A |
| taxonomy | 文献定位矩阵（2×2 或层级树，本文占哪个空格） | §2 综述 | A 或 B |
| deployment | 工程尺度部署示意（构筑物-地层-监测网） | 数值章节开篇 | A |

原型决定**提问清单**（原版每原型 5–9 问，画前自答）：
- 架构图必答：系统叫什么？几个阶段？每阶段输入/输出？**哪个是本文贡献**（视觉强调）？有无并行/反馈？
- 流程图必答：什么被转化？几步？每步是标准操作还是本文新方法？有无分支/汇合？要不要画中间状态？
- 装置示意必答：展开的是哪个总成？内部子件与数据流？哪些参数要标注？与常规装置差在哪？
- 机制示意必答：读者默认的心智模型是什么错？用哪种纠正（before/after、空间类比、视觉隐喻、过程对比）？每个形状代表什么**具名**的东西（禁止抽象团块）？
- 对比图必答：两边共享的输入是什么（必须画成一样）？现有方法**具体在哪一步**失败？我方**对应哪一步**成功？差异的**具体机制**是什么（不是"我们的更好"）？
- 文献定位必答：分类轴是什么？本文占哪个象限？是填空格还是开新枝？各类别里放哪些具名文献？

## 3. 动笔前先填规格单

> 体例借自 zLanqing figure_spec_template.md，删 AI backend、字号/正文宽度换成本规程口径。
> 填完再动手画；规格单存 `figures/figure_spec_<id>.md`（若无该目录先建）。

```markdown
# Figure Spec: <图名>

## Identity
- Figure ID: fig:<短id>
- 论文章节: §<n>
- 版位: 通栏 / 半栏（Word 里=整页宽 or 单栏宽）
- 原型: <七原型之一>
- 轨道: A 手绘 / B TikZ

## Purpose
- 支撑的论文 claim（原文抄过来）: "…"
- 读者看完该理解什么（1–2 句）: …
- 删掉这张图会丢什么: …
- 叙事角色: 动机 / 设计解释 / 证据汇总 / 定位

## Content
### Components（组件表）
| 组件 | 标签文字 | 形状 | 颜色语义 | 说明 |
|---|---|---|---|---|

### Connections（连线表）
| 从 | 到 | 标签 | 线型（实/虚/双向） | 代表什么 |

### Groupings（分组框）
| 组 | 包含 | 标签 | 样式（虚线框/底色） |

## Layout
- 流向: 左→右 / 上→下 / 放射
- 层级: <几层>
- 对称约束: <哪些组件必须画得视觉平行>
- 尺寸目标: 正文宽度（示例 14.65 cm）；字号 ≥10.5 pt 印刷态

## Styling
- 语义→颜色映射（见 §5 表）
- 强调: <哪个组件是本文贡献，用加粗描边/加深填充>

## Caption（claim-first，结论先行）
- 草稿: …

## Status
- spec 完成 / 已生成 / critique 通过 / 迭代记录
```

## 4. 画法方法论（七条铁律）

> 核心理念借自 coleam00 excalidraw-diagram-skill（"Diagrams should ARGUE,
> not DISPLAY"），全部改写为通用语境：

1. **图要论证，不要陈列**。去掉所有文字后，结构本身还能不能传达概念？
   （原版 Isomorphism Test）五个等大方框+文字不是示意图，是排版。
2. **形状即含义**。概念→视觉模式映射：
   一对多=中心辐射；汇聚=漏斗；层级=树（线+字，不必加框）；时序=线+圆点；
   循环=首尾回接箭头；模糊状态=交叠椭圆；转化=前后对比；对比=并列；
   阶段切换=留白分隔。多概念图里**每个主要概念用不同模式**，禁止一律方框。
3. **容器纪律**。默认自由文字，加框仅当：它是焦点/需要被连线/形状本身带义
   （菱形=决策）。自问"这个框改成裸文字还成立吗？"——成立就删框。
   容器内文字占比 <30%。
4. **技术图必须有"证据件"**（原版 evidence artifacts 的改造）：
   不要画标着"泵"的空框，要**标实测参数**——"H-B 流变（τ0=8.2 Pa，
   K=0.041）、入口压力 20 kPa、H=0.5、r=1 mm"；界面要标真实判据
   （α=0.5 等值面），不是"界面"两字。数据出处走你自己的数值记录。
5. **多层缩放**。综合图三层同在：顶层摘要流（一行流程）+ 中层分组框
   （虚线房间）+ 底层细节（证据件）。
6. **留白=重要度**。最重要的元素周围留白最多；层级用大小表达
   （主组件大、辅助组件小）；字号本身也要分层（标题>组标>正文标注）。
7. **画完必须目检循环**（原版 Render & Validate，手绘轨同样适用）：
   导出 PNG → 逐项查 9 类缺陷 → 改 → 再导，2–4 轮。
   9 类缺陷：文字被裁/文字重叠/箭头穿件/箭头落错/标签悬空/间距不均/
   留白失衡/字太小/构图偏侧。

## 5. 配色与形状语义表（本规程口径，唯一权威）

> 原版 Paul Tol / Tailwind 色系**全部弃用**（避免与数据图第二套色系并存）。
> 深描边+浅填充的对比原则保留。

| 语义 | 填充 | 描边 | 形状 |
|---|---|---|---|
| 主流程/中性组件 | `#C9DCE9`（INK 浅调） | `#153A60`（INK，即 figstyle.INK） | 矩形（圆角 4pt 等效） |
| **本文贡献/强调** | `#F2D4C2`（#D55E00 浅调） | `#D55E00`（Okabe-Ito 赭红）+ **加粗描边** | 矩形 |
| 输入/起点 | `#EDEDED` | `#333333`（GREY） | 椭圆 |
| 输出/结果 | `#CFE8DA`（#009E73 浅调） | `#009E73`（Okabe-Ito 绿） | 椭圆 |
| 决策/判据 | `#FDF0D5` | `#8a6d1a` | 菱形 |
| 对比图的"问题侧" | `#F5E1CC`（#E69F00 浅调） | `#E69F00`（Okabe-Ito 橙） | 矩形 |
| 可选/备选分支 | 同主流程但 **虚线描边** | `#153A60` | 矩形 |
| 数据/材料（非过程） | `#E3E3E3` | `#666666` | 圆柱（PPT/柱状符） |
| 时间线锚点 | — | 同主流程描边 | 8–12 px 圆点 |

- 文字层级：标题 `#153A60` / 组标 `#0072B2` / 正文标注 `#333333`；
  浅色填充内一律深字（`#153A60` 或 `#333333`），禁止白字。
- 语义色**全文一致**：蓝色若代表"本方法"，所有图都如此；同名组件在每张图
  里标签必须逐字相同（借 zLanqing 跨图一致性 5 条）。
- **灰度可读**：黑白打印后各语义仍可区分（靠明度差+线型差+形状差，不只靠色相）。

## 6. A 轨操作规程（draw.io / PPT）

1. 新建画布**直接按印刷尺寸**：通栏图按正文宽度（示例 14.65 cm；draw.io 里 577 px @96dpi，
   PPT 里按 14.65 cm 设），不要画大了再缩——印刷字号由几何决定。
2. 开栅格与对齐线（draw.io：View→Grid；PPT：参考线）；组件间距取栅格整数倍。
3. 文字一律按 **10.5 pt 印刷态**设置（PPT 里字号即印刷 pt；draw.io 按
   1 pt=1.333 px@96dpi 换算后 ≈14 px）。小于 10.5 pt 的文字不许出现。
4. 按 §3 规格单逐项落件：先布局（流向+分组框），再连线，最后标注与证据件。
5. 导出：**SVG 或 PDF**（矢量，批注后仍清晰）+ **PNG @600 dpi**
   （贴 Word 用）。draw.io：File→Export→勾 Crop；PPT：导出时选"更改文件
   分辨率 300→ 用另存 PDF + 单独高分辨 PNG"。
6. 批注循环：交 PNG/PDF 批注 → 回画布改 → 重新导出。
   版式级反复 ≥5 轮仍不稳 → 升 B 轨。
7. Illustrator 只做最后修饰（路径平滑、描边统一），改完**必须**回存 SVG/PDF，
   且在交付卡（`case-card.md`）里记"经 AI 手工修饰"一笔——守住可复现底线。

## 7. B 轨骨架（TikZ；需要 TeX 环境，可用 Overleaf）

> 若本地没装 TeX（无 pdflatex/xelatex/MiKTeX/TeX Live/tectonic/latexmk），就
> **不能本地编译**：把 TikZ 源码贴到 Overleaf 编译后下载 PDF，或装 MiKTeX 后本地跑
> `pdflatex -interaction=nonstopmode fig_<id>.tex`（≤3 次重试）。
> 骨架借自 chingswy layout_templates（五套可编译版式）与 zLanqing tikz_skeletons，
> 色值换 §5 的色系；tikzlibrary 需要：positioning, arrows.meta, calc, fit,
> backgrounds, decorations.pathreplacing（另有 shapes.geometric/shapes.misc 备用）。

**线性横向管线（3–6 阶段，最常用）**——最小骨架（配色已换）：

```latex
\documentclass[border=5pt]{standalone}
\usepackage{tikz}\usepackage{amsmath}
\usetikzlibrary{positioning, arrows.meta, calc, fit, backgrounds}
\definecolor{bgMain}{HTML}{C9DCE9}\definecolor{bgAcc}{HTML}{F2D4C2}
\definecolor{bdMain}{HTML}{153A60}\definecolor{bdAcc}{HTML}{D55E00}
\definecolor{bgIO}{HTML}{EDEDED}\definecolor{arCol}{HTML}{153A60}
\definecolor{txMain}{HTML}{153A60}
\tikzset{
  module/.style={draw=bdMain, fill=bgMain, rounded corners=4pt,
    minimum width=2.8cm, minimum height=1.1cm, font=\small, text=txMain,
    line width=0.6pt, align=center},
  novel/.style={module, draw=bdAcc, fill=bgAcc, line width=1.2pt, font=\small\bfseries},
  iobox/.style={draw=bdMain, fill=bgIO, rounded corners=3pt,
    minimum width=2cm, minimum height=0.9cm, font=\small, text=txMain, align=center},
  arr/.style={-{Stealth[length=5pt,width=4pt]}, line width=0.6pt, color=arCol},
}
\begin{document}\begin{tikzpicture}
  \node[iobox] (in) {输入};
  \node[module, right=1.0cm of in] (m1) {阶段 1};
  \node[novel,  right=1.0cm of m1] (m2) {本文方法};
  \node[module, right=1.0cm of m2] (m3) {阶段 3};
  \node[iobox,  right=1.0cm of m3] (out){输出};
  \draw[arr] (in)--(m1); \draw[arr] (m1)--(m2);
  \draw[arr] (m2)--(m3); \draw[arr] (m3)--(out);
\end{tikzpicture}\end{document}
```

其余骨架（按需取结构、换色）：竖排（窄栏）、U 形回环、双支独立、
多支汇合——见 chingswy/skill-research-figure 的 `layout_templates.md`；
组件盒样式库（novelmodule/optmodule/groupbox/lossbox）——见其 `tikz_elements.md`；
2×2 文献定位矩阵与层级树（本文位置加粗描边"空象限"手法）——见 zLanqing 的
`tikz_skeletons.md`。
**编译后必须过 §8 验收清单**，字号按印刷态复核（PDF 缩放到正文宽度后量）。

## 8. 验收清单（示意图专用）

> 前四查借自 zLanqing critique 五查（其 Check 3 venue 格式换成本规程口径），
> 渲染缺陷 9 类借自 coleam00。全 PASS 才能进论文。

| # | 查什么 | 判据 |
|---|---|---|
| 1 | claim 对齐 | 图只支撑规格单里那条 claim；配合图注单独能读懂；不削弱 claim |
| 2 | 完整性 | 规格单组件/连线/分组逐项在图里；强调组件真的突出；无拼错 |
| 3 | 落盘规格 | 正文宽度（示例 14.65 cm）；字号 ≥10.5 pt 印刷态；600 dpi PNG 或矢量 PDF/EPS；白底；语义色出自 §5 |
| 4 | 设计原则 | 每个视觉元素都承载信息（无装饰性边框/底色）；图能脱离正文被skim读懂；能删的都删了；风格与同论文其他示意图一致 |
| 5 | 图注质量 | claim-first（结论先行）；自足；无含糊修饰词 |
| 6 | 灰度可读 | 转灰度后语义仍可辨（打印场景） |
| 7 | 渲染缺陷 9 类 | 文字裁切/重叠/箭头穿件/落错/悬空/间距不均/留白失衡/字太小/构图偏侧——逐项目检，0 缺陷 |
| 8 | 可复现声明 | 交付卡注明轨道与源文件路径（draw.io 源文件 / .tex / .pptx），他人可重开重导 |

## 9. 来源与忠实度声明

| 借了什么 | 从哪来 | 怎么改的 |
|---|---|---|
| 数据图/示意图分界判据、七原型、原型提问清单、critique 五查、跨图一致性 5 条 | zLanqing/codex-claude-academic-skills `research-writing-skill/references/paper-writing/figure_synthesis_guide.md`（307 行，MIT） | 术语改写为通用语境；venue 条目换成本规程的 14.65 cm/10.5 pt/600 dpi |
| 规格单体例 | 同上仓库 `figure_templates/figure_spec_template.md`（93 行） | 删 AI backend；加"轨道"字段；尺寸/字号换成本规程口径 |
| ARGUE-not-DISPLAY 理念、概念→模式映射 9 条、容器纪律、shape meaning、多层缩放、证据件、目检循环与 9 类缺陷、分节生成纪律 | coleam00/excalidraw-diagram-skill `SKILL.md`（552 行，无 license）、`references/color-palette.md`、`references/element-templates.md` | 证据件从"真实事件名"改造为"实测工况参数"；excalidraw JSON 模板**未内化**（渲染依赖 Playwright，未装环境时不可用；JSON 体例仅在选 B 轨 excalidraw 时再取） |
| TikZ 骨架与盒样式库 | chingswy/skill-research-figure `.claude/skills/research-figure/references/{tikz_elements,layout_templates}.md`（489/430 行，No License）；zLanqing `figure_templates/tikz_skeletons.md`（220 行） | 只抄结构与 tikzlibrary 清单；配色全换 §5；标注无 TeX 环境时的编译路径 |
| "KEY CONTRIBUTION 视觉强调"思想 | zLanqing `figure_templates/prompt_templates.md`（246 行） | AI prompt 本身未内化（AI 生图不进正文） |

- 原文快照未随本包分发（抓取时记录了来源 URL 与 sha256，可自行重取）。
- 许可注意：coleam00 与 chingswy **无 license**（默认保留所有权利）——因此本文件
  只借**方法论**（思想不受版权保护）并全部改写，未复制其代码与色值；
  zLanqing/chingswy 骨架若需逐字复制 LaTeX 结构，交付时在 case-card 里注名出处。
