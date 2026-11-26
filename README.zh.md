# dsh-academic-figure-ops

学术插图规程，打包成 DeepSeek Harness 的 bundle。它只回答一个几乎每篇论文都会踩的问题：**这张图缩进页面之后，字还看得清吗？**

装好 bundle 就会注册 `academic-figure-ops` 这个 skill；只要你说"画图 / 改字号 / 检查这张图能不能用"，agent 会自动读它。

## 它管什么

- **字号是算出来的，不是猜的。** 印刷字号服从 `印刷pt = 图内设定pt × 正文宽度cm ÷ 落盘图宽cm`。把你的正文宽度设一次，之后每张图都按这个口径验。
- **每次落盘验三件事**：印刷字号、缩放后的有效分辨率、文件的实际像素宽。三项里常常只有一项达标——"屏幕上看着挺好"就是这么来的。
- **图型要配表达意图**，附审丑清单（双 y 轴、截断坐标轴、彩虹色带、用装饰冒充数据等）。
- **CFD 后处理范式**：云图面板、色标、多算例横向对比的做法。
- **三维渲染路线**（`pyvista`）：几何本体就是三维的图——等值面、相界面、多机位并排——走真 3D 渲染，不硬用 2D 云图凑立体感；光照与配色配方、三个实测坑一并给出。
- **19 个可复现配方**（`assets/case-gallery/`）：每个案例都有配方脚本、说明卡和预览图，数据是合成数据 + 固定 seed，谁都能重跑。

## 目录结构

```
skills/academic-figure-ops/
├── SKILL.md                     agent 读的规程正文
├── references/                  图型选择、硬参数、审丑清单、分辨率与格式、
│                                CFD 范式、三维渲染、示意图/流程图、验收清单
├── scripts/
│   ├── figstyle.py              样式的唯一实现
│   ├── check_figure.py          只读验收器（验一张已落盘的图）
│   └── overlap_audit.py         查标签/刻度文字互相压盖
└── assets/case-gallery/         19 个配方 + 案例卡 + 预览
```

## 安装

**装 bundle（推荐）**——在 Plugins → Add plugin 里装 npm 上的 `dsh-academic-figure-ops`，或等市场收录后从市场装。bundle 会替你注册 skill。

**只当普通 skill 用**——把目录复制进 skills 根即可，不需要 bundle：

```bash
cp -r skills/academic-figure-ops ~/.dsh/skills/
```

两种方式 agent 都会发现 `SKILL.md` 并按需加载。

## 怎么用

1. 先读 `references/hard-params.md` 看默认参数。
2. 量出你页面的正文宽度（A4 + 左右 3.17 cm 页边距时是 14.65 cm），设进去：
   - 代码里：`TEXT_WIDTH_CM = 14.65` 或 `set_style(text_width_cm=14.65)`
   - 验收时：`python check_figure.py --text-width-cm 14.65 figures/fig1.png`
3. 用 `figstyle.py` 出图，宽度、字体、配色才统一。
4. 交稿前跑 `check_figure.py`：它给出印刷字号与有效分辨率，并指出是哪一项不达标。

依赖：Python 3.10+、`matplotlib`（实测 3.11）与 `numpy`（实测 2.4）；`Pillow` 只有验收器用得到。没有别的依赖，也不联网。

## 如实说明它的边界

- 它检查图**能不能看清、有没有画错**，不判断数字背后的科学结论对不对。
- CFD 那一节写的是一条常见的 Fluent/CFD-Post 做法；换别的软件，云图配色和色标位置要自己替换步骤。
- 案例库是**用合成数据演示版式**，不是数据集。
- 包内不含、也不需要任何厂商软件、第三方图库或受版权保护的图件。

## 许可与素材

代码、文字与 `icon.png` 采用 MIT（见 `LICENSE`）。19 张案例预览由包内配方用合成数据渲染，同样按 MIT 授权。**不转发行任何第三方图件**：案例卡只描述版式，预览展示的是本包自己的代码按该版式画出来的结果。

文中提到的产品与公司名（Fluent、ANSYS、matplotlib、DeepSeek Harness）归各自所有者，本包与它们没有隶属或背书关系。