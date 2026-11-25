# CFD 流场图的成图范式

> 适用范围：VOF 相界面推进云图、速度场、压力场、沿程剖面。
> 本文件不讲 CFD 计算本身，只讲**算完之后怎么画成图**。

## 零、先明确一件事：这套规程没有现成的 CFD 模板可抄

调研过二十余个开源制图仓库与插件市场条目，用 `cfd / contour / streamline / vof / turbulence /
paraview / ansys / fluent / velocity field / pressure field / vector field / quiver / 流场 / 云图`
全量检索：

**命中数全部为 0**（唯一相近的是一条"Flow field with trajectory, sensors, and zoomed anomaly"
分幅，但那是通用场示意，非 CFD）。

⇒ 所以下面的范式是**从这类数据的形态出发自己定的**，不是移植来的。
好处是贴合；代价是**没有外部权威背书**，凡引用须注明"本规程的约定"。

## 一、VOF 云图（结果类章节主力图型）

### 画什么

VOF 的标量是**相分数 α**（如水/气两相中的液相），本质是 0–1 的**区间量**，不是连续场。
这决定了三件事：

1. **不要用连续渐变 cmap 直接铺满**——α=0.5 的界面会糊在过渡色里；
2. **必须画出界面等值线**（α = 0.5）——这是"界面推到哪了"的直接读数；
3. colorbar 范围**固定 0–1**，不许按数据自适应（否则两张图无法对比）。

### 标准画法

```python
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs

fs.use_size(13)                         # 画布宽 12-14.5 in：字号 + 分辨率双达标
fig, axes = plt.subplots(2, 3, figsize=(13.0, 8.1), layout='constrained',
                         sharex=True, sharey=True)

levels_f = np.linspace(0, 1, 21)        # 填色 21 档，够细但不过分
for ax, (t, alpha) in zip(axes.flat, snapshots):
    cf = ax.contourf(X, Y, alpha, levels=levels_f, cmap=fs.CMAP_AP,
                     vmin=0, vmax=1, extend='neither')
    ax.contour(X, Y, alpha, levels=[0.5], colors='white',
               linewidths=0.9)          # 界面线：白色，压在填色上更清楚
    ax.set_aspect('equal')              # 流场必须等比例，否则形态失真
    ax.set_title(f't = {t:.1f} s', fontsize=...)   # 若标题太占地方，改用 panel()
    fs.panel(ax, f'({chr(97+i)})')

# 共享 colorbar：只画一个，范围由全部数据决定
cbar = fig.colorbar(cf, ax=axes, fraction=0.046, pad=0.04, ticks=[0, 0.5, 1])
cbar.set_label('液相体积分数 α')
```

### 必须守住的 5 条

| # | 规矩 | 违反后果 |
|---|---|---|
| 1 | **`vmin=0, vmax=1` 固定** | 自适应范围会让"该相少"的图看起来和"该相多"一样满 |
| 2 | **`set_aspect('equal')`** | 纵横比不同 → 推进形态肉眼判断全错 |
| 3 | **`contourf` 而非 `imshow`** | `imshow` 的像素插值会在界面上造假梯度 |
| 4 | **共享 colorbar** | 每个分幅各自归一 → 分幅之间不可比 |
| 5 | **分幅时刻等间隔或按事件取** | 随意取时刻 → 图在讲自己的故事 |

### 配色选择

- **两相推进（界面主导）** → `CMAP_AP`（蓝白红）：一相=蓝、另一相=红、界面=白，直观；
- **浓度/龄期（单调累积）** → `INK_SEQ`（深蓝递进）：单调量用单调色；
- **速度大小** → `viridis`（感知均匀）或 `INK_SEQ`；
- **禁止** `jet` / `rainbow`（感知不均匀，会产生假边界）。

## 二、速度场 + 流线

### 什么时候画流线、什么时候画箭头

| 目的 | 用法 |
|---|---|
| 看**整体流动结构**（绕流、回流区） | `streamplot`（连续流线，密度可控） |
| 看**局部方向**（关键几个位置） | `quiver`（离散箭头，必须抽稀） |
| 两者都要 | 填色场打底 + `streamplot` 叠线，**不要**再加 quiver |

### 抽稀是必须的

原始网格动辄 10⁵ 个单元，直接 `quiver` 会画成一片黑。控制器是 `stride`：

```python
skip = max(1, len(x) // 24)
ax.quiver(X[::skip, ::skip], Y[::skip, ::skip],
          U[::skip, ::skip], V[::skip, ::skip],
          color='black', scale=..., width=0.003, pivot='mid')
```

**箭头长度靠 `scale` 调，不要靠改数据**。改数据 = 改结论。

### `streamplot` 的两个坑

1. 数据必须是**规则网格**。非结构网格要先插值到规则网格（`scipy.interpolate.griddata`），
   插值本身会引入误差，**图注要说明"已插值到规则网格"**；
2. `density` 参数控制线密度，`density=(2, 2)` 比默认 `(1,1)` 更密。太密会糊。

## 三、压力场

压力是**连续标量**，但通常有正负或相对参考值。规矩：

> 下面三节（压力场 / 沿程剖面 / 小多图）都是**承接 §一 的代码片段**：假定 `np`、`plt`、`fs` 已 import，`X`/`Y` 网格与 `ax`/`fig` 已建好。单独复制不行。

```python
vmax = np.abs(P).max()
cf = ax.contourf(X, Y, P, levels=21, cmap=fs.CMAP_AP,
                 vmin=-vmax, vmax=+vmax)      # 对称
ax.contour(X, Y, P, levels=10, colors='white', linewidths=0.5)  # 等值线
```

- **对称范围**：`vmin=-vmax, vmax=+vmax`，保证 0 在中点（白）；
- **等值线必须叠**：填色看不出梯度陡缓，等值线能；
- **等值线间距写进图注**（`等值线间隔 50 Pa`），否则读数不准；
- 若压力范围跨两个量级 → 改画 `log10(P)`，图注写明"对数刻度"。

## 四、沿程剖面 / 时间曲线

常要展示"沿计算域某一方向某量的变化"。

> 承接片段（同 §三）：假定 `fs` 已 import、`ax` 已建好。

```python
for i, (label, prof) in enumerate(profiles.items()):
    ax.plot(dist, prof, color=fs.INK_SEQ[i], lw=1.0,
            label=label, marker=['o','s','^','D','v'][i], ms=3,
            markevery=5)          # marker 抽稀，别每个点都画
ax.set_xlabel('沿程距离 $x$ / mm')
ax.set_ylabel('压力 $p$ / kPa')
ax.legend(frameon=False)
```

- **多时刻/多参数**用 `INK_SEQ` 顺序色（**不要**用 `OKABE_ITO`——那是类别色，会暗示无序）；
- **marker 抽稀**（`markevery`），否则点密时线看着粗；
- **≥ 5 条线就改用直接标注**（在线末端写字），别堆图例。

## 五、参数敏感性：小多图

同一组图讲"参数 A 变大时，结果怎么变"：

> 承接片段：假定 `plt`、`fs` 已 import。这一块要重新建 `fig`，不能沿用上面的 `ax`。

```python
fig, axes = plt.subplots(2, 3, figsize=(13.0, 8.6), layout='constrained',
                         sharex=True, sharey=True)
# 关键：显式设定统一范围
for ax in axes.flat:
    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo, y_hi)
```

**必须统一轴范围**。这是结果类章节最大的造假风险：
如果每个分幅各自 `autoscale`，一张"缓慢上升"和一张"剧烈上升"看起来一样陡。

图注里写清：`各分幅轴范围一致，便于横向比较`。

## 六、网格与几何示意

这类图**不是数据图**，衡量标准是"读者看懂了没有"，不是色彩好不好。

- 用 `matplotlib.patches`（`Rectangle`/`Polygon`/`FancyArrowPatch`）画，**不要贴外部位图**；
- 线宽统一 `0.65K`，文字 10.5 印刷 pt；
- 尺寸标注用**双箭头 + 文字**，别用引线拖到图外；
- 剖面图要标**坐标方向**（流向 / 重力方向），否则读者不知道哪边是上。

## 七、一批 CFD 图的典型问题清单（修图时对照）

对一批已出成品的 CFD 云图做批量体检（`check_figure.py` 量印刷字号与有效 dpi），
问题高度集中在下面几条：

| 问题 | 现象 | 根因 | 修法 |
|---|---|---|---|
| **印刷字号普遍偏小**（实测 4.84–7.49 pt，而同文档已定稿图 10.39–10.96） | 整批不合格 | 见下面的"字号没跟着画布放大" | 按最小改动路径重设画布与 `use_size` |
| 配色多套体系并存 | 跨图不一致 | 具名 cmap 4 种（`RdYlBu_r`/`viridis`/`magma`/`cividis`）+ 一套自定义色标 | 统一到 `CMAP_AP` + `INK_SEQ`，成图走 `figstyle` |
| dpi 只两种但都偏低 | 分辨率不可控 | **150** 与 **180**，**无一张 300** | 统一 300；画布同时给足 |
| 轴线宽 0.8（应为 0.65K） | 与定稿图不一致 | 绘图模板里写死 `"axes.linewidth" = 0.8` | 走 `figstyle.apply_style()` |
| 字号根本没跟着画布放大 | 这才是印刷字号塌到 5–7 pt 的直接原因 | `font.size` 写死 10.5，画布宽 9.2–12.5 in，10.5 pt 印到 14.65 cm 上只剩 5–7 pt | `fs.use_size(同值)` 自动按 K 放大 |
| 多数缺 `(a)(b)(c)` 分幅标号 | 无法在正文引用 | 手写时漏掉 | `fs.panel(ax, "(a)")` |

**⚠ 一个容易写错的更正**：不要想当然把"字体两套（部分用 SimHei/YaHei）"记到这批图头上——
实测这批产出脚本的 `font.family` 全部是 `["Times New Roman", "SimSun"]`，**只有 1 套**。
用 SimHei/YaHei 的往往是同一项目里另一批早期脚本，属"全目录的问题"，
不要记到这一批名下。**归因错误比缺陷本身更难查。**

**修复优先级**（不是全部重写）：

1. **先修字号**——这一条决定"印出来看不清"，其他都是次要；
2. 再统一配色（成图时走 `figstyle`）；
3. 再统一轴线宽（0.8 → 0.65K）；
4. 分幅标号最后加（改动最小）。

最小改动路径：把每个绘图脚本的 `figsize` 宽改成 **12–14.5 in**，加一行
`fs.use_size(同值)`，字号保持 10.5 不变（use_size 会按 K 自动放大）。300 dpi 出来
3600–4350 px，缩到 14.65 cm 后字号 10.4 pt、有效 624–754 dpi，两项都达标。

> ⚠ **上面 624–754 dpi 的前提是"不裁切"**（存图时不带 `bbox_inches="tight"`，落盘宽≈figsize 宽；
> 实测那批定稿图的 tight 比值 0.96–1.01，所以成立）。如果走 `fit_and_save`（它恒用 tight），
> 落盘宽只有 figsize 的 **0.82 倍**左右，同为 13 in @300dpi 时实测 **3209 px → 556 dpi**，不达 600。
> 这种情形把画布给到 **≥14.5 in**（15–16 留余量）：15 in → 3692 px → 640 dpi、16 in → 3932 px → 682 dpi。

⚠ **不要改成 5.77 in**：那样字号虽然天然达标，但 300 dpi 只有 1730 px，
缩到正文宽度后有效分辨率仅 300 dpi，达不到线条图 600 的要求（见
`resolution-and-format.md`）。

## 八、常见错误（实际踩过的）

| 错误 | 现象 | 根因 | 修法 |
|---|---|---|---|
| 三维图字号看着够，落盘后偏小 | 三维 tight 裁切只留 76% 宽 | 用了 figsize 宽当基准 | 实测落盘宽，或 `fit_and_save` 迭代 |
| 多子图轴名连成 `x / mmy / mm` | 共享轴没关 | 每个子图都 `set_xlabel` | 只给最下一行/最左一列加标签 |
| 变差函数曲线异常平滑 | 分箱过粗 | bins 太少 | bins 加倍，图注标分箱数 |
| 中文变方框 | mathtext 处理中文 | `$中文$` 语法 | 中文放 `r'$x$ / mm（中文）'` 的普通文本部分 |
| 字号调大后坐标区被吃掉 | K 太大 | 画布宽远大于正文宽度 | 优先加大画布高度/减分幅，别硬压字号 |
| 云图两张无法对比 | colorbar 各自归一 | 没固定 vmin/vmax | 见 §一 规矩 1 |
