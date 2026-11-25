#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""figstyle — 学术插图样式的唯一实现（这套规程）

设计原则（为什么这样写）
------------------------
1. **只有一个实现**。样式函数（use_size / apply_style / panel）很容易被每个
   出图脚本各抄一份，改一处漏三处。本模块是唯一副本，其余脚本只 import。

2. **反算链的唯一正确形式**是：

       印刷字号[pt] = 设定字号[pt] × 版心宽[in] ÷ 落盘图实际宽[in]
       版心宽[in]   = TEXT_WIDTH_CM ÷ 2.54（默认 14.65 cm，可覆盖）
       落盘图实际宽[in] = 像素宽 ÷ dpi

   注意分母是**落盘图的实际宽**，不是 figsize 宽——`bbox_inches='tight'`
   会把画布裁到内容边界，两者不等（实测：多数图落在 figsize 的 96–101%，
   三维图低到 76%）。把 figsize 宽当分母是常见的错误算法。

3. **版心宽度不是常数**。默认 14.65 cm 只是"A4 + 左右各 3.17 cm 页边距"
   这一种版式的常见值。换纸张/换页边距时先量出自己的正文宽度，再调
   ``set_text_width_cm(你的值)``，整条反算链和所有字号换算会自动跟着变。
   文档里出现"14.65"处一律指默认值，不是硬编码。

4. **不猜，量**。`fit_and_save()` 会真落盘、真读像素、真回算，迭代到收敛，
   并把每一轮的数字返回给调用者，而不是"设好了应该就对"。

需要的解释器
------------
必须是有 numpy + matplotlib 的解释器：不是所有环境里排第一的 python 都装了
这两个包，用它 import 本模块会 ModuleNotFoundError。先
``python -c "import numpy, matplotlib, PIL"`` 验证，不要凭 PATH 顺序猜。
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

# --------------------------------------------------------------------------
# 常量：默认值取自"A4 + 左右各 3.17 cm 页边距"的常见版式口径
# --------------------------------------------------------------------------

#: `fit_and_save()` 专用的补偿因子（见下）。默认 1.0 = 不改任何行为；
#: 只有 fit_and_save 在迭代时临时改它，并在 finally 里还原。
#
# 为什么需要它：调用者写的 `makefig(w)` 用**同一个 w** 同时建 figsize 和
# 调 use_size(w)，于是
#     printed = (10.5·w/TW)·TW / (α·w) = 10.5/α
# **与 w 无关**，只由 tight 裁切比 α 决定。所以"改画布宽"这条路根本改不动
# printed（旧版就是在这里走偏的：它每轮令 w ← α·w，w 一路缩到 2.7 in，
# 产出 919×496 px 的废图，还不报错）。真正要调的是"字号相对画布的比例"，
# 即这个补偿因子：令 c = target·α/10.5，则 printed = 10.5·c/α = target。
_FIT_SCALE = 1.0

#: 页面正文版心宽 [cm]。**默认 14.65 = A4 + 左右各 3.17 cm 页边距的常见值**。
#: 换纸张/换页边距时改这里——推荐调 ``set_text_width_cm(你的值)``（会一并
#: 重算 K/FS/FT 并刷新已生效的 rcParams）；也可直接给 TEXT_WIDTH_CM 赋值后
#: 调一次 ``apply_style()``。所有长度换算都经由本变量，代码里没有别处写死。
TEXT_WIDTH_CM = 14.65
TEXT_WIDTH_IN = TEXT_WIDTH_CM / 2.54          # 默认 = 5.767716535433071 in

#: 图内轴标签目标印刷字号（中文五号 10.5 pt，比正文小四 12 pt 小一号）
TARGET_LABEL_PT = 10.5
#: 刻度数字与图例目标印刷字号（9.5 pt）
TARGET_TICK_PT = 9.5

#: 判定容差。已定稿图件的实测范围约 10.39–10.96 pt（±5% 内全部达标），
#: 故 ±5% 是"已达成"的经验带；单图自检用更严的 ±2%。
TOL_PASS = 0.05
TOL_TIGHT = 0.02

DEFAULT_DPI = 300

#: use_size() 最近一次的画布宽 [in]；set_text_width_cm() 用它重算 K/FS/FT。
_CANVAS_W_IN = 13.0
#: apply_style() 是否已调用过；set_text_width_cm() 据此决定要不要刷新 rcParams。
_STYLE_APPLIED = False


def cm2in(cm: float) -> float:
    """cm → in。所有长度换算都走这里，别处不要再写 ``/ 2.54`` 字面量。"""
    return cm / 2.54


def set_text_width_cm(value: float) -> float:
    """把版心宽度设为 ``value`` cm，并按**当前画布宽**重算 K/FS/FT。

    默认值是 14.65 cm（A4 + 左右各 3.17 cm 页边距）。换纸张、换页边距、
    投期刊（单栏/双栏正文宽度各不相同）时，先量出自己的正文宽度再调本函数，
    反算链与字号换算就会整体跟着变——这正是本模块不把 14.65 写成字面量的
    原因。

    Parameters
    ----------
    value : float
        页面正文宽度 [cm]，必须为正。

    Returns
    -------
    float
        生效后的 TEXT_WIDTH_CM。

    Notes
    -----
    本函数会重算模块级 K/FS/FT。若此前已调用过 ``apply_style()``（通常经由
    ``use_size()``），会再刷一次 rcParams；否则只更新常量，保持导入无副作用。
    已落盘的图不会变，需要重新出图才会用上新版心。
    """
    global TEXT_WIDTH_CM, TEXT_WIDTH_IN, K, FS, FT
    v = float(value)
    if not (v > 0.0):
        raise ValueError(f"版心宽度必须为正，收到 {value!r}")
    TEXT_WIDTH_CM = v
    TEXT_WIDTH_IN = cm2in(v)
    K = _CANVAS_W_IN * _FIT_SCALE / TEXT_WIDTH_IN
    FS = TARGET_LABEL_PT * K
    FT = TARGET_TICK_PT * K
    if _STYLE_APPLIED:
        apply_style()
    return TEXT_WIDTH_CM


def _ensure_width_consistent() -> None:
    """兜底同步：允许调用者绕开 ``set_text_width_cm()``，直接改模块级的
    ``TEXT_WIDTH_CM``。

    直接赋值只会改那一个名字，``TEXT_WIDTH_IN``/K/FS/FT 会留在旧值上，静默算错。
    本函数在所有读这些派生量的入口被调用：一旦发现不同步，就按当前
    ``TEXT_WIDTH_CM`` 重算一遍。正常走 ``set_text_width_cm()`` 时是空操作。
    """
    if abs(TEXT_WIDTH_IN - cm2in(TEXT_WIDTH_CM)) > 1e-9:
        set_text_width_cm(TEXT_WIDTH_CM)


# 这些在 use_size() 里被重算，模块级保留是为了兼容既有脚本的写法
# （13.0 是旧实现里默认画布宽的兼容值，不代表版心）
K = _CANVAS_W_IN * _FIT_SCALE / TEXT_WIDTH_IN
FS = TARGET_LABEL_PT * K
FT = TARGET_TICK_PT * K

matplotlib.rcParams["axes.unicode_minus"] = False


# --------------------------------------------------------------------------
# 配色：集中管理，避免每个脚本自己铺一套彩虹
# --------------------------------------------------------------------------

#: 主线条色（线图、柱状图默认）
INK = "#153A60"
#: 中性灰（辅助线、非重点元素）
GREY = "#333333"
#: Okabe–Ito 色盲友好五色。多系列区分时优先用它，
#: 并**同时**用记号形状区分——不靠灰度深浅（黑白打印会糊成一片）
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7"]
#: 单色系明度递进（需要"同一含义的程度差异"时用它，而不是彩虹）
INK_SEQ = ["#0B1F33", "#153A60", "#2E6C9E", "#6FA3C8", "#B8D3E6"]

#: 开度场双向色标（蓝—白—红降低饱和度版）：中心白 = 平均开度
CMAP_AP = matplotlib.colors.LinearSegmentedColormap.from_list(
    "ap_soft", ["#2E6C9E", "#9FBBD6", "#FAFAFA", "#D89A8C", "#B5443A"]
)


# --------------------------------------------------------------------------
# 样式
# --------------------------------------------------------------------------

def apply_style() -> None:
    """把当前 K/FS/FT 写进 rcParams。由 use_size() 调用，一般不用直接调。"""
    _ensure_width_consistent()
    global _STYLE_APPLIED
    matplotlib.rcParams.update({
        "font.family": ["Times New Roman", "SimSun"],
        "font.size": FS,
        "axes.labelsize": FS,
        "axes.unicode_minus": False,
        "axes.linewidth": 0.65 * K,
        "axes.edgecolor": "black",
        "xtick.labelsize": FT,
        "ytick.labelsize": FT,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.size": 3.0 * K,
        "ytick.major.size": 3.0 * K,
        "xtick.minor.size": 1.7 * K,
        "ytick.minor.size": 1.7 * K,
        "xtick.major.width": 0.65 * K,
        "ytick.major.width": 0.65 * K,
        "xtick.minor.width": 0.55 * K,
        "ytick.minor.width": 0.55 * K,
        "xtick.top": True,
        "ytick.right": True,
        "legend.fontsize": FT,
        "legend.frameon": True,
        "legend.edgecolor": "black",
        "legend.fancybox": False,
        "savefig.dpi": DEFAULT_DPI,
        "figure.dpi": 120,
    })
    _STYLE_APPLIED = True


def use_size(canvas_w_in: float) -> float:
    """按本图画布宽度 [in] 设定缩放比，返回 K。

    参数是**你打算画的 figsize 宽度**。因为 tight 裁剪一般只让宽度缩 0–5%，
    所以直接用 figsize 宽做近似即可；要精确到 ±2% 请用 `fit_and_save()`，
    它会实测后自动补偿（补偿的是字号比例，不是画布宽）。

    缩放比由"当前版心宽"决定（见 `set_text_width_cm()`）：画布宽恰好等于
    版心宽时 K=1、设定字号即印刷字号；画布越宽 K 越大。
    """
    if canvas_w_in <= 0:
        raise ValueError(f"画布宽度必须为正，收到 {canvas_w_in!r}")
    _ensure_width_consistent()
    global K, FS, FT, _CANVAS_W_IN
    _CANVAS_W_IN = float(canvas_w_in)
    K = canvas_w_in * _FIT_SCALE / TEXT_WIDTH_IN
    FS = TARGET_LABEL_PT * K
    FT = TARGET_TICK_PT * K
    apply_style()
    return K


def panel(ax, label: str, gap_pt: float = 6.0,
          fs: float | None = None, dy: float | None = None,
          weight: str = "bold") -> None:
    """分幅编号 (a)(b)(c) 写在坐标区**下方**、且**避开 x 轴名与刻度数字**。

    这个函数改过两次，两次都是被实图否掉的，原因值得记住：

    * **v1** 用 ``dy=-0.28``（坐标区高度的比例）。在 13×8.1 in 的六分幅里算成
      21 mm，标号悬在行间，画布越高越难看。
    * **v2** 改用固定 32 pt。两行共享 x 轴时只有底行有刻度数字，底行的
      "刻度数字 + 轴名" 超过 32 pt，于是 ``(d)(e)(f)`` 直接压在 ``x / mm`` 上。
      固定点数不可能同时适配"有轴名/没轴名/有刻度/没刻度"四种情况。

    * **v3（现在）**：先让 figure 渲染一次，**实测**该坐标区 x 轴名与刻度标签
      实际占到哪里（取最低的那个下边界），再把标号放到它下面 ``gap_pt`` 处。

    Parameters
    ----------
    gap_pt : float
        标号顶端与"下方最低文字下边界"的间距（点）。默认 6 pt。
    fs : float, optional
        字号，默认模块级 FS。
    weight : str, default "bold"
        标号字重。期刊惯例分幅标号加粗（Science 明确 9 pt bold）；
        传 ``"normal"`` 可回到不加粗的旧行为。
    dy : float, optional
        已废弃（v1 行为），仅为兼容旧脚本保留。

    Notes
    -----
    因为要实测，本函数会触发一次 ``fig.canvas.draw()``。请在**布局确定后**
    （即 ``set_xlabel`` 等都已调用完、紧接 ``savefig`` 之前）调用它。
    在 constrained/tight layout 下，annotate 不参与约束计算，所以这次 draw
    不会反过来改变布局。
    """
    if dy is not None:  # v1 行为，兜底
        ax.annotate(
            label, xy=(0.5, dy), xycoords="axes fraction",
            ha="center", va="top",
            fontsize=fs if fs is not None else FS,
            fontweight=weight,
            annotation_clip=False,
        )
        return

    fig = ax.figure
    fig.canvas.draw()                       # 先落定布局，才能量到真实位置
    renderer = fig.canvas.get_renderer()
    ax_bb = ax.get_window_extent(renderer)

    # 收集坐标区下方所有可能占位的文字，取最低的下边界（显示坐标，向上为正）
    bottoms = []
    xlab = ax.xaxis.label
    if xlab.get_text().strip() and xlab.get_visible():
        bottoms.append(xlab.get_window_extent(renderer).y0)
    ticks = [t for t in ax.get_xticklabels()
             if t.get_text().strip() and t.get_visible()]
    if ticks:
        bottoms.append(min(t.get_window_extent(renderer).y0 for t in ticks))
    low = min(bottoms) if bottoms else ax_bb.y0

    # 显示坐标 → 相对坐标区底边的 offset points（向下为负）
    offset_pt = (low - ax_bb.y0) / fig.dpi * 72.0 - gap_pt

    ax.annotate(
        label,
        xy=(0.5, 0.0),
        xycoords="axes fraction",
        xytext=(0, offset_pt),
        textcoords="offset points",
        ha="center",
        va="top",
        fontsize=fs if fs is not None else FS,
        fontweight=weight,
        annotation_clip=False,
    )


def fix_corner_labels(ax, which: str = "bottomleft") -> int:
    """缓解"两根轴在角上各有一个最小刻度"时标签互相压住的问题。

    现象：坐标区左下角，y 轴最小值 ``0.00`` 的**下半截**与 x 轴最小值 ``0.0``
    的**左半截**落在同一小方块里互相压住（matplotlib 默认布局不处理这种角部
    交叉，constrained/ tight 都不管，因为它把 y 标签给左外边距、x 标签给下边
    距，角上那块被两边同时占用）。

    做法：把该角那个 y 刻度标签改为**外对齐**（最小值 ``va='bottom'`` 只向上
    长、最大值 ``va='top'`` 只向下长），于是它不再向下越过轴线，与 x 标签彻底
    分开。只改对齐方式、不改刻度值。

    Parameters
    ----------
    which : {"bottomleft", "topleft", "both"}
        处理哪个角。默认左下角（最常见）。

    Returns
    -------
    int
        实际调整的标签个数（0 表示该轴没有可识别的极值标签）。
    """
    labels = [t for t in ax.get_yticklabels() if t.get_text().strip()]
    if not labels:
        return 0

    # 找出哪个标签在**下方**、哪个在**上方**。
    # 不能直接拿 labels[0] 当"最小值"：y 轴反转时（``ax.invert_yaxis()``，
    # 云图/深度剖面常用），刻度顺序不变但屏幕位置颠倒，labels[0] 实际在顶部。
    # 这里按轴是否反转来定，比依赖顺序稳妥。
    inverted = ax.yaxis_inverted()
    lo_label = labels[-1] if inverted else labels[0]
    hi_label = labels[0] if inverted else labels[-1]

    n = 0
    if which in ("bottomleft", "both"):
        lo_label.set_verticalalignment("bottom")   # 下方那个：只向上长
        n += 1
    if which in ("topleft", "both"):
        hi_label.set_verticalalignment("top")      # 上方那个：只向下长
        n += 1
    return n


# --------------------------------------------------------------------------
# 测量：这是整个模块的核心，其余都是它的附属
# --------------------------------------------------------------------------

def saved_width_in(png_path: str | Path, dpi: float | None = None) -> float:
    """读落盘 PNG 的实际宽 [in] = 像素宽 ÷ dpi。

    dpi 优先用入参，其次读 PNG 自带的 pHYs 块，最后退到 300。
    这是反算链的分母，务必用**落盘文件**，不要用 figsize。
    """
    from PIL import Image

    p = Path(png_path)
    if not p.is_file():
        raise FileNotFoundError(f"落盘图不存在：{p}")

    with Image.open(p) as im:
        px = im.size[0]
        if dpi is None:
            info_dpi = im.info.get("dpi")
            dpi = float(info_dpi[0]) if info_dpi else float(DEFAULT_DPI)

    if dpi <= 0:
        raise ValueError(f"dpi 必须为正，收到 {dpi!r}")
    return px / dpi


def printed_pt(set_pt: float, actual_width_in: float) -> float:
    """反算印刷字号 [pt]。

        printed = set_pt × 版心宽[in] ÷ 落盘图实际宽

    版心宽读的是当前 TEXT_WIDTH_CM（默认 14.65 cm ⇒ 5.7677 in）。
    例：设定 23.7 pt、落盘图宽 12.5 in
        → 23.7 × 5.7677 ÷ 12.5 = 10.94 pt  ✓（落在 10.5 pt 目标带内）
    反例：设定 10.5 pt、落盘图宽 ≈ 版心宽（5.77 in）
        → 10.5 × 5.7677 ÷ 5.77 = 10.50 pt
    反例：设定 10.5 pt、落盘图宽 10.2 in（画布远宽于版心）
        → 10.5 × 5.7677 ÷ 10.2 = 5.94 pt  ✗（正是要抓的失配）
    """
    if actual_width_in <= 0:
        raise ValueError(f"落盘图宽度必须为正，收到 {actual_width_in!r}")
    _ensure_width_consistent()
    return set_pt * TEXT_WIDTH_IN / actual_width_in


# --------------------------------------------------------------------------
# 收敛：落盘 → 实测 → 回调 → 再落盘，直到印刷字号落在目标带内
# --------------------------------------------------------------------------

def fit_and_save(
    makefig,
    out_path: str | Path,
    *,
    canvas_w_in: float,
    target_pt: float = TARGET_LABEL_PT,
    tol: float = TOL_TIGHT,
    max_iter: int = 5,
    dpi: int = DEFAULT_DPI,
    **savefig_kw,
):
    """画图 → 落盘 → 量宽 → 回算 → 调**字号补偿**重画，直到收敛。

    参数
    ----
    makefig : 可调用对象，签名 `makefig(canvas_w_in) -> matplotlib.figure.Figure`。
        它**必须自己调用 use_size(canvas_w_in)**，并按该宽度建 figsize。
        画布宽在迭代中**保持不变**（这是关键，见下）。
        首轮后本函数会**机制校验**这条契约：比对 rcParams["font.size"] 与期望的
        设定字号，偏差 >5% 直接 raise ValueError —— 回调忘了调 use_size 不再
        静默虚报（复核人实测：不调时返回 printed=10.5 而真实印刷仅 5.66 pt）。
        已知局限：若调用前环境字号恰好等于期望值则查不出；契约本身仍以本
        docstring 为准，校验只是兜底。
    out_path : 落盘路径（.png）
    canvas_w_in : 画布宽度 [in]。它决定**像素宽**（≈ canvas_w_in × dpi），
        而 tight 会把落盘宽裁到 α×canvas（α 常见 0.82–0.98），所以有效分辨率
        = saved_width_in×dpi ÷ 版心宽[in]，**不是** canvas_w_in×dpi ÷ 版心宽。
        实测（dpi=300，1:0.43 单图）：13 in → 556 dpi、14 in → 598、15 in → 640、
        16 in → 682。要线条图 600 dpi 请给 **≥14.5 in**（想留余量给 15–16）。
        ⚠ 别把画布宽直接设成版心宽（默认 5.77 in 量级）：那只有 300 dpi。
    target_pt : 目标印刷字号，默认 10.5
    tol : 相对容差，默认 0.02（±2%）
    max_iter : 最多迭代次数

    返回
    ----
    dict(converged, canvas_w_in, saved_width_in, set_pt, printed_pt,
         iterations, fit_scale, effective_canvas_w_in, path, history)

    其中 ``effective_canvas_w_in`` = ``canvas_w_in × fit_scale``，即
    "若不用 fit_and_save、手工写 ``use_size(该值)`` 也能得到同样字号"的那个宽度，
    它收敛后等于 ``saved_width_in``（因为补偿量的定义就是让它相等）。
    核查这张图时用返回的 ``set_pt`` 走 ``--fs`` 口径，**不要**用
    ``--canvas-w canvas_w_in``——后者假定 ``use_size(canvas_w_in)``，口径不符。

    为什么这样能收敛
    ----------------
    设 α = 落盘宽 / 画布宽（tight 裁切的收缩比，同一张图近似常数），
    c 为字号补偿因子（内部 ``_FIT_SCALE``），则

        printed = (10.5·c·w/TW) · TW / (α·w) = 10.5·c/α

    **注意 printed 与 w 无关**——所以"改画布宽"永远改不动 printed。
    旧版正是踩了这个坑：它每轮令 w ← saved_in·target/printed = αw·target/printed，
    而 printed 不变 ⇒ w 每轮乘 α 的平方，画布一路缩到 2.7 in，
    最终产出 919×496 px 的废图**却不报错**。
    正确做法是固定 w、只调 c：令 c ← target·α/10.5，一轮即可精确命中；
    由于 α 会随字号极轻微变化，最多 2–3 轮。

    调用者要读 `converged`，**不要假定它一定收敛**。

    两点语义说明（第 4 轮复核实测发现，易误读）：
    1. `converged=False` 时返回的 `fit_scale` 是**下一轮的建议值**
       （"再往下调多少"），**不是**磁盘上那张图实际用的补偿量；磁盘图用的是
       `history[-1]["fit_scale"]`。`converged=True` 时两者相同。
    2. matplotlib 的 rcParams 是进程级全局状态：同一进程里先画过别的图、
       改过 rcParams，再调本函数，结果可能轻微漂移（实测极差 ~0.04 pt，
       仍在 ±2% 内）。要严格复现，请每张图用独立进程跑。
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    global _FIT_SCALE
    w = float(canvas_w_in)
    if w <= 0:
        raise ValueError(f"画布宽度必须为正，收到 {canvas_w_in!r}")

    history = []
    printed = math.nan
    saved_in = math.nan
    set_pt = math.nan
    prev_scale = _FIT_SCALE
    scale = 1.0

    try:
        for i in range(1, max_iter + 1):
            _FIT_SCALE = scale
            fig = makefig(w)
            if i == 1:
                # 契约机制校验（第 4 轮复核 ★）：makefig 必须调 use_size(w)。
                # 若没调，rcParams["font.size"] 保持调用前的旧值，与期望设定字号
                # 偏差极大 —— 在这里显式报错，而不是静默产出虚报字号的图。
                _want_fs = TARGET_LABEL_PT * (w * scale / TEXT_WIDTH_IN)
                try:
                    _got_fs = float(matplotlib.rcParams.get("font.size"))
                except (TypeError, ValueError):
                    _got_fs = math.nan
                if (not math.isfinite(_got_fs)
                        or abs(_got_fs - _want_fs) > 0.05 * _want_fs):
                    raise ValueError(
                        "makefig 违反契约：期望它在内部调用 use_size(canvas_w_in) "
                        f"把 font.size 设到 {_want_fs:.3f} pt（w={w:g} in, "
                        f"scale={scale:g}），实测 rcParams['font.size']={_got_fs}。"
                        "fit_and_save 不替你设字号 —— 请在 makefig 内先调 "
                        "figstyle.use_size(canvas_w_in) 再返回 Figure。"
                        "（已知局限：若调用前环境字号恰好等于期望值则查不出。）"
                    )
            try:
                fig.savefig(out_path, bbox_inches="tight", dpi=dpi, **savefig_kw)
            finally:
                import matplotlib.pyplot as plt
                plt.close(fig)

            saved_in = saved_width_in(out_path, dpi=dpi)
            # makefig 内部调用了 use_size(w)，其 K 已含 _FIT_SCALE 补偿
            set_pt = TARGET_LABEL_PT * (w * scale / TEXT_WIDTH_IN)
            printed = printed_pt(set_pt, saved_in)
            err = abs(printed - target_pt) / target_pt
            history.append({
                "iter": i, "canvas_w_in": round(w, 4),
                "saved_w_in": round(saved_in, 4),
                "set_pt": round(set_pt, 3), "printed_pt": round(printed, 3),
                "fit_scale": round(scale, 6), "err": round(err, 5),
            })
            if err <= tol:
                return {
                    "converged": True, "path": str(out_path),
                    "canvas_w_in": round(w, 4), "saved_width_in": round(saved_in, 4),
                    "set_pt": round(set_pt, 3), "printed_pt": round(printed, 3),
                    "iterations": i, "fit_scale": round(scale, 6),
                    "effective_canvas_w_in": round(w * scale, 4),
                    "history": history,
                }
            # 画布宽**不动**，只按实测比例修正字号补偿因子。
            # printed 与 scale 严格成正比（printed = 10.5·scale/α），故直接按比例修正即可；
            # 若 α 随字号轻微变化，下一轮会再纠一次，通常 2–3 轮收敛。
            scale *= (target_pt / printed)
    finally:
        _FIT_SCALE = prev_scale

    return {
        "converged": False, "path": str(out_path),
        "canvas_w_in": round(w, 4), "saved_width_in": round(saved_in, 4),
        "set_pt": round(set_pt, 3), "printed_pt": round(printed, 3),
        "iterations": max_iter, "fit_scale": round(scale, 6),
        "effective_canvas_w_in": round(w * scale, 4),
        "history": history,
    }


# --------------------------------------------------------------------------
# 自检：不依赖任何外部图，就地验算反算链（可作为 CI 的第一道闸门）
# --------------------------------------------------------------------------

def _selftest(verbose: bool = True) -> int:
    """就地验算反算链。返回 0=全部通过，1=有失败。

    关于"断言有没有鉴别力"：本自检里有一条**负向对照**（negative control），
    它构造一个必然不成立的关系并要求判定器把它判成"不成立"。只有当判定器
    真的报出"不成立"时，才说明这些断言不是永远为真的空话。负向对照的结果
    单独标注为 `NEG`，不混进 PASS/FAIL 计数，避免读者把它误读成自检失败。
    """
    global _FIT_SCALE                 # 8e 要临时改它验证生效性
    fails: list[str] = []
    lines: list[str] = []

    def out(s: str) -> None:
        lines.append(s)
        if verbose:
            print(s)

    def check(name: str, got: float, want: float, tol: float = 1e-9) -> None:
        ok = abs(got - want) <= tol
        out(f"  [{'PASS' if ok else 'FAIL'}] {name}: got={got:.6f} want={want:.6f}")
        if not ok:
            fails.append(name)

    def negative_control(name: str, got: float, wrong_want: float) -> None:
        """断言 got != wrong_want；若两者相等，说明判定器失去鉴别力。"""
        assert abs(got - wrong_want) > 1e-6, (
            f"负向对照失效：{name} 的 got 竟然等于故意给错的值 {wrong_want}"
        )
        out(f"  [NEG ] {name}: 已确认判定器能区分（{got:.6f} != {wrong_want:.6f}）")

    out("figstyle 自检")

    # ======================================================================
    # 设计原则：期望值一律写**黄金字面量**，不用本模块的常量或函数现算
    # ======================================================================
    # 旧版自检在这里是 `check("版心宽 in", TEXT_WIDTH_IN, "14.65 / 2.54 的
    # 现算值")`——左右两边是同一个式子，恒为真；`check("某量级",
    # printed_pt(23.7, 12.5), 用 TEXT_WIDTH_IN 重写一遍的式子)` 更是把被测
    # 函数原样抄了一遍当期望值。结果是：把 TARGET_LABEL_PT 改成 12、把
    # use_size 里的 K 除以 2、把刻度长 3.0K 改成 5.0K，**自检全都照样报
    # "全部通过"**。
    #
    # 所以下面每个期望值都是独立的字面量，来源写在注释里。它们只在这一处出现，
    # 与模块常量**没有任何代码联系**——改坏了实现，数字就对不上。
    #
    # 这些黄金值定义在"默认版心 14.65 cm"这一个参考点上（14.65 是文档写的
    # 默认值，不是实现里的硬编码）。若调用者已改过 TEXT_WIDTH_CM，本自检先钉
    # 回默认再验、最后还原；"版心可覆盖"这件事由第 1b 节单独验。
    #
    # 黄金值来源（独立算式，与实现无共享代码）：
    #   5.767716535433071 = 14.65 / 2.54          （默认版心的定义）
    #   2.253924914675768 = 13.0 / 5.7677165354   （use_size(13) 的 K）
    #   23.666211604095558 = 10.5 × 2.25392491    （use_size(13) 的 font.size）
    #   21.412286689419794 = 9.5 × 2.25392491     （use_size(13) 的 tick 字号）
    #   10.409252669039144 = 23.66621160 × 5.7677165354 / 13.1133333333
    #                        （一张实图：3934px @300dpi = 13.1133333 in）
    #   6.761774744027303 = 3.0 × 2.25392491      （刻度长；参考实现是同值）
    #   1.465051194539249 = 0.65 × 2.25392491     （轴线宽/刻度宽）
    #   3.831672354948805 = 1.7 × 2.25392491      （次刻度长）
    #   1.239658703071672 = 0.55 × 2.25392491     （次刻度宽）
    #   3460.629921259842831 = 600 × 5.7677165354 （600dpi 所需像素宽）
    #   1062.992125984251970 = 90/25.4 × 300      （Elsevier 单栏照片 1063px）
    # ======================================================================

    # --- 1. 版心宽度：先验恒等式（与具体数值无关），再验可参数化 ---
    _REF_CM = 14.65                    # 黄金字面量所在的参考版心（文档默认值）
    _orig_cm = TEXT_WIDTH_CM
    set_text_width_cm(_REF_CM)
    # 恒等式：inch 口径必须、且只能由 TEXT_WIDTH_CM 经 cm2in() 得到。
    # 这里比的是**当前** TEXT_WIDTH_CM，不写死具体数字——换版心后依然成立。
    check("版心恒等式 TEXT_WIDTH_IN == cm2in(TEXT_WIDTH_CM)",
          TEXT_WIDTH_IN, cm2in(TEXT_WIDTH_CM), tol=1e-12)
    check("cm2in 定义 2.54cm == 1in", cm2in(2.54), 1.0, tol=1e-15)

    # --- 1b. 版心可覆盖：改宽度后，同一设定的印刷字号必须按比例变 ---
    _p_ref = printed_pt(10.5, 5.0)     # 同一落盘宽 5.0 in 下的参考印刷字号
    _k_ref = use_size(13.0)            # 同一画布宽 13 in 下的参考 K
    set_text_width_cm(12.0)
    check("TEXT_WIDTH_IN 跟随 TEXT_WIDTH_CM", TEXT_WIDTH_IN, 12.0 / 2.54,
          tol=1e-12)
    check("印刷字号 ∝ 版心宽（12.0/14.65）",
          printed_pt(10.5, 5.0) / _p_ref, 12.0 / _REF_CM, tol=1e-12)
    check("K 反比于版心宽（14.65/12.0）", use_size(13.0) / _k_ref,
          _REF_CM / 12.0, tol=1e-12)

    # --- 1c. 兜底：绕开 set_text_width_cm() 直接改模块级常量也必须生效 ---
    globals()["TEXT_WIDTH_CM"] = 15.0   # 故意只改这一个，制造派生量不同步
    check("直接赋值 TEXT_WIDTH_CM 后派生量自动同步",
          printed_pt(10.5, 5.0), 10.5 * cm2in(15.0) / 5.0, tol=1e-12)
    check("同步后 TEXT_WIDTH_IN 一致", TEXT_WIDTH_IN, 15.0 / 2.54, tol=1e-12)
    # 黄金值必须在参考版心下验；调用者原来的版心在收尾处还原
    set_text_width_cm(_REF_CM)

    # --- 2. use_size() 必须真的改 rcParams（旧版从不调用它）---
    try:
        k13 = use_size(13.0)
        check("use_size(13) 返回 K", k13, 2.253924914675768, tol=1e-12)
        check("font.size", matplotlib.rcParams["font.size"],
              23.666211604095558, tol=1e-10)
        check("axes.labelsize", matplotlib.rcParams["axes.labelsize"],
              23.666211604095558, tol=1e-10)
        check("xtick.labelsize", matplotlib.rcParams["xtick.labelsize"],
              21.412286689419794, tol=1e-10)
        check("axes.linewidth", matplotlib.rcParams["axes.linewidth"],
              1.465051194539249, tol=1e-12)
        check("xtick.major.size", matplotlib.rcParams["xtick.major.size"],
              6.761774744027303, tol=1e-12)
        check("xtick.minor.size", matplotlib.rcParams["xtick.minor.size"],
              3.831672354948805, tol=1e-12)
        check("xtick.major.width", matplotlib.rcParams["xtick.major.width"],
              1.465051194539249, tol=1e-12)
        check("xtick.minor.width", matplotlib.rcParams["xtick.minor.width"],
              1.239658703071672, tol=1e-12)
        # 刻度方向与四边轴（期刊图件常见口径）
        ok_d = (matplotlib.rcParams["xtick.direction"] == "in"
                and matplotlib.rcParams["ytick.direction"] == "in"
                and matplotlib.rcParams["xtick.top"] is True
                and matplotlib.rcParams["ytick.right"] is True)
        out(f"  [{'PASS' if ok_d else 'FAIL'}] 刻度朝内 + 四边轴")
        if not ok_d:
            fails.append("刻度朝内+四边轴")
        # 字体族（含中文字体，避免中文变方框）
        fam = list(matplotlib.rcParams["font.family"])
        ok_f = fam[:2] == ["Times New Roman", "SimSun"]
        out(f"  [{'PASS' if ok_f else 'FAIL'}] 字体族前两位 = {fam[:2]}")
        if not ok_f:
            fails.append("字体族")
    except Exception as e:  # noqa: BLE001
        out(f"  [FAIL] use_size/apply_style 抛异常: {type(e).__name__}: {e}")
        fails.append("use_size")

    # --- 3. printed_pt()：独立黄金值，不是把公式重写一遍 ---
    # 一张实图：3934px @300dpi = 13.11333... in，脚本调 use_size(13)，
    # 故设定字号 = 10.5 × 2.25392491 = 23.6662116 pt
    check("printed_pt(宽画布实图)", printed_pt(23.666211604095558, 3934 / 300.0),
          10.409252669039144, tol=1e-12)
    # 恒等：设定字号 × 版心 ÷ 版心 = 设定字号本身（对任意当前版心都成立）
    check("printed_pt 等宽恒等", printed_pt(10.5, TEXT_WIDTH_IN), 10.5,
          tol=1e-12)
    # 画布远宽于版心的失配：10.5 pt 画在 10.2 in 上
    check("printed_pt(画布过宽失配)", printed_pt(10.5, 10.2),
          5.937355257063456, tol=1e-12)
    # 300dpi 像素宽阈值（resolution-and-format.md 里的 3461）
    check("600dpi 所需像素宽", 600 * TEXT_WIDTH_IN, 3460.629921259842831,
          tol=1e-9)
    # Elsevier 单栏照片最小宽 1063 px = 300dpi × 90 mm
    check("Elsevier 1063px 换算", 90 / 25.4 * 300, 1062.992125984251970,
          tol=1e-9)

    # --- 4. fitted 边界：非法入参必须抛 ValueError，不能静默返回 ---
    for bad_w, who in ((0.0, "use_size(0)"), (-1.0, "use_size(-1)")):
        try:
            use_size(bad_w)
        except ValueError:
            out(f"  [PASS] {who} 抛 ValueError")
        except Exception as e:  # noqa: BLE001
            out(f"  [FAIL] {who} 抛了 {type(e).__name__}，应为 ValueError")
            fails.append(who)
        else:
            out(f"  [FAIL] {who} 未抛异常（会静默算出负字号）")
            fails.append(who)
    for bad_w, who in ((0.0, "printed_pt(w=0)"), (-3.0, "printed_pt(w=-3)")):
        try:
            printed_pt(10.5, bad_w)
        except ValueError:
            out(f"  [PASS] {who} 抛 ValueError")
        except Exception as e:  # noqa: BLE001
            out(f"  [FAIL] {who} 抛了 {type(e).__name__}，应为 ValueError")
            fails.append(who)
        else:
            out(f"  [FAIL] {who} 未抛异常")
            fails.append(who)

    # --- 6. 容差常量：TOL_PASS / TOL_TIGHT 必须真的在判定带上 ---
    # 这两个常量在 figstyle 内部没有调用点（TOL_PASS 由 check_figure 作为 --tol
    # 默认值引用，TOL_TIGHT 由 fit_and_save 默认参数引用），所以变异它们不会
    # 触发任何行为差异 —— 只会让"什么算达标"悄悄变宽。这正是复核单点出的缺口：
    # 旧自检里它们出现 0 次，把 0.05 改成 0.10 仍 exit 0。这里改成显式断言。
    check("TOL_PASS 达标带", TOL_PASS, 0.05, tol=1e-12)
    check("TOL_TIGHT 单图带", TOL_TIGHT, 0.02, tol=1e-12)
    if not (0.0 < TOL_TIGHT <= TOL_PASS <= 0.10):
        out(f"  [FAIL] 容差关系不成立：需 0 < TOL_TIGHT({TOL_TIGHT}) "
            f"<= TOL_PASS({TOL_PASS}) <= 0.10")
        fails.append("容差关系")
    else:
        out(f"  [PASS] 容差关系 0 < {TOL_TIGHT} <= {TOL_PASS} <= 0.10")

    # --- 7. DEFAULT_DPI：必须真的被 savefig 用上，且 pHYs 兜底也走它 ---
    # 旧自检从不碰它，变异 300→200 抓不到（复核单 #7）。
    check("DEFAULT_DPI", DEFAULT_DPI, 300, tol=1e-12)
    if matplotlib.rcParams.get("savefig.dpi") != DEFAULT_DPI:
        out(f"  [FAIL] savefig.dpi={matplotlib.rcParams.get('savefig.dpi')!r} "
            f"应为 DEFAULT_DPI={DEFAULT_DPI}")
        fails.append("savefig.dpi 接线")
    else:
        out(f"  [PASS] savefig.dpi 已接到 DEFAULT_DPI={DEFAULT_DPI}")
    # pHYs 兜底路径：读一张**没有 pHYs 块**的 PNG，宽度必须按 DEFAULT_DPI 换算。
    # 造法：正常存一张 4 in 的图，然后从 PNG 字节流里**删掉 pHYs 块**。
    # （matplotlib 不接受 dpi=() 这种写法，只能事后剥块。）
    import tempfile as _tf

    def _strip_phys(src: Path, dst: Path) -> bool:
        """删除 PNG 的 pHYs 块。返回 True 表示确实删掉了。"""
        import struct

        raw = src.read_bytes()
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("不是 PNG")
        pos, outb, removed = 8, bytearray(raw[:8]), False
        while pos < len(raw):
            (ln,) = struct.unpack(">I", raw[pos:pos + 4])
            typ = raw[pos + 4:pos + 8]
            chunk = raw[pos:pos + 8 + ln + 4]
            if typ != b"pHYs":
                outb += chunk
            else:
                removed = True
            pos += 8 + ln + 4
        dst.write_bytes(bytes(outb))
        return removed

    import matplotlib.pyplot as _plt

    with _tf.TemporaryDirectory() as _td:
        _raw = Path(_td) / "with_phys.png"
        _np = Path(_td) / "no_phys.png"
        _f, _a = _plt.subplots(figsize=(4, 2))
        _a.plot([0, 1], [0, 1])
        _f.savefig(_raw, dpi=DEFAULT_DPI)          # 先正常存（带 pHYs）
        _plt.close(_f)
        _removed = _strip_phys(_raw, _np)
        _w = saved_width_in(_np)                   # 不给 dpi ⇒ 走 pHYs 兜底
    _want = 4.0                                     # figsize 宽 4 in，未裁切
    if not _removed:
        out("  [FAIL] 剥 pHYs 失败（原图本来就没有 pHYs？）")
        fails.append("pHYs 剥离")
    elif abs(_w - _want) > 1e-6:
        out(f"  [FAIL] pHYs 兜底：无 dpi 的 4 in 图读成 {_w:.6f} in，"
            f"期望 {_want}（说明兜底没用 DEFAULT_DPI={DEFAULT_DPI}）")
        fails.append("pHYs 兜底")
    else:
        out(f"  [PASS] pHYs 兜底：无 dpi 的 4 in 图读成 {_w:.6f} in")

    # --- 8. 负向对照：证明上面的比较不是恒真 ---
    # 若 printed_pt 写成"返回 set_pt 本身"，下面第一条就会相等而触发断言
    negative_control("反算链非常数", printed_pt(10.5, 12.0),
                     printed_pt(10.5, TEXT_WIDTH_IN))
    negative_control("失配非达标", printed_pt(10.5, 10.2), TARGET_LABEL_PT)

    # --- 回归保护：fix_corner_labels 必须按**屏幕位置**、而非 labels[0] ---
    # 这条曾经是真 bug：旧实现直接取 labels[0] 当"最小值"，在 y 轴反转
    # （ax.invert_yaxis()，云图/深度剖面常用）时会把上下两端标反。
    # 下面用同一组用例验证新实现正确、并证明旧逻辑确实会被判错。
    def _screen_va(invert: bool, use_old_logic: bool) -> tuple[str, str]:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([0, 1], [0, 1])
        if invert:
            ax.invert_yaxis()
        if use_old_logic:                      # 旧实现：按列表顺序当上下
            labs = [t for t in ax.get_yticklabels() if t.get_text().strip()]
            if labs:
                labs[0].set_verticalalignment("bottom")
                labs[-1].set_verticalalignment("top")
        else:
            fix_corner_labels(ax, which="both")
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        pairs = []
        for t in ax.get_yticklabels():
            if not t.get_text().strip():
                continue
            bb = t.get_window_extent(r)
            pairs.append(((bb.y0 + bb.y1) / 2.0, t.get_verticalalignment()))
        pairs.sort(key=lambda p: p[0])
        res = (pairs[0][1], pairs[-1][1]) if pairs else ("", "")
        plt.close(fig)
        return res

    try:
        got_norm = _screen_va(False, False)
        got_inv = _screen_va(True, False)
        old_inv = _screen_va(True, True)
        want = ("bottom", "top")
        ok_norm = got_norm == want
        ok_inv = got_inv == want
        out(f"  [{'PASS' if ok_norm else 'FAIL'}] fix_corner_labels 未反转轴: "
            f"屏幕下={got_norm[0]} 屏幕上={got_norm[1]}")
        out(f"  [{'PASS' if ok_inv else 'FAIL'}] fix_corner_labels 反转轴: "
            f"屏幕下={got_inv[0]} 屏幕上={got_inv[1]}")
        if not ok_norm:
            fails.append("fix_corner_labels 未反转轴")
        if not ok_inv:
            fails.append("fix_corner_labels 反转轴")
        # 负向对照：旧逻辑在反转轴上**必须**与正确结果不同，否则这条检查无效
        assert old_inv != want, (
            f"负向对照失效：旧 labels[0] 逻辑居然在反转轴上也得到 {want}，"
            "说明这条回归检查区分不出新旧实现"
        )
        out(f"  [NEG ] 旧 labels[0] 逻辑在反转轴上确实不同"
            f"（屏幕下={old_inv[0]}，应为 {want[0]}）")
    except Exception as e:  # noqa: BLE001  自检里任何异常都算失败
        out(f"  [FAIL] fix_corner_labels 回归检查抛异常: {type(e).__name__}: {e}")
        fails.append("fix_corner_labels 回归检查")

    # --- 9. fit_and_save 与 _FIT_SCALE 的自检覆盖（第 4 轮复核新增）---
    # 旧自检对 fit_and_save / _FIT_SCALE 零覆盖（AST 审计：调用 0 次），
    # 而它恰是曾经"数学上不可能收敛"的高危函数。以下每条断言都对应复核人
    # r4_mut2 清单里的一种"偷懒实现也能骗过表面检查"的写法。
    def _mkfig_ok(w):
        fig, ax = _plt.subplots(figsize=(w, w * 0.43))
        use_size(w)                        # ← 契约：回调自己设字号
        ax.plot([0, 1], [0, 1])
        ax.set_xlabel("x / mm")
        return fig

    def _mkfig_bad(w):                     # 违反契约：不调 use_size
        fig, ax = _plt.subplots(figsize=(w, w * 0.43))
        ax.plot([0, 1], [0, 1])
        return fig

    with _tf.TemporaryDirectory() as _td2:
        _p = Path(_td2) / "fit_ok.png"
        _r = None
        try:
            _r = fit_and_save(_mkfig_ok, _p, canvas_w_in=13.0,
                              tol=0.02, max_iter=5)
        except Exception as e:  # noqa: BLE001
            out(f"  [FAIL] fit_and_save 正常回调抛异常: "
                f"{type(e).__name__}: {e}")
            fails.append("fit_and_save 正常回调")
        if _r is not None:
            # 9a 收敛且轮数少（旧版 5 轮不收敛、缩到 2.7 in）
            _ok_a = bool(_r.get("converged")) and _r.get("iterations", 99) <= 3
            out(f"  [{'PASS' if _ok_a else 'FAIL'}] 9a fit_and_save 收敛: "
                f"converged={_r['converged']} iterations={_r['iterations']} "
                f"printed={_r['printed_pt']:.4f} pt")
            if not _ok_a:
                fails.append("fit_and_save 收敛")
            # 9b 独立复算 printed：不信返回值，从**落盘文件**宽度反推
            # （对应 MUT-A/MUT-D：返回值抄 target 骗不过这条）
            _saved_file = saved_width_in(_p, dpi=DEFAULT_DPI)
            _printed_ind = _r["set_pt"] * TEXT_WIDTH_IN / _saved_file
            _ok_b = abs(_printed_ind - TARGET_LABEL_PT) <= TOL_TIGHT * TARGET_LABEL_PT
            out(f"  [{'PASS' if _ok_b else 'FAIL'}] 9b 独立复算印刷字号: "
                f"{_printed_ind:.4f} pt（目标 {TARGET_LABEL_PT}，"
                f"文件宽 {_saved_file:.4f} in）")
            if not _ok_b:
                fails.append("fit_and_save printed 独立复算")
            # 9c history 里画布宽恒定（旧"缩画布"缺陷的回归闸）
            _hs = {h["canvas_w_in"] for h in _r["history"]}
            _ok_c = len(_hs) == 1
            out(f"  [{'PASS' if _ok_c else 'FAIL'}] 9c history 画布宽恒定: "
                f"{sorted(_hs)}")
            if not _ok_c:
                fails.append("fit_and_save 画布恒定")
            # 9d effective_canvas_w_in = canvas×fit_scale 且 ≠ canvas（R4-c）
            _eff = _r["effective_canvas_w_in"]
            _ok_d = (abs(_eff - _r["canvas_w_in"] * _r["fit_scale"]) <= 1e-3
                     and _eff != _r["canvas_w_in"])
            out(f"  [{'PASS' if _ok_d else 'FAIL'}] 9d effective_canvas_w_in="
                f"{_eff} = canvas {_r['canvas_w_in']} × scale {_r['fit_scale']}")
            if not _ok_d:
                fails.append("effective_canvas_w_in 语义")
        # 9e _FIT_SCALE 真的参与 K 的计算（R4-a：use_size 丢 _FIT_SCALE 骗不过）
        _prev = _FIT_SCALE
        try:
            _FIT_SCALE = 0.8
            use_size(13.0)
            _got8 = float(matplotlib.rcParams["font.size"])
            _want8 = TARGET_LABEL_PT * (13.0 * 0.8 / TEXT_WIDTH_IN)
            _ok_e = abs(_got8 - _want8) <= 1e-3 * _want8
            out(f"  [{'PASS' if _ok_e else 'FAIL'}] 9e _FIT_SCALE=0.8 时 "
                f"font.size={_got8:.4f}（期望 {_want8:.4f}）")
            if not _ok_e:
                fails.append("_FIT_SCALE 生效")
        finally:
            _FIT_SCALE = _prev
        # 9f 契约机制校验：makefig 不调 use_size → 必须 ValueError（第 4 轮 ★）
        _p2 = Path(_td2) / "fit_bad.png"
        try:
            fit_and_save(_mkfig_bad, _p2, canvas_w_in=13.0)
            out("  [FAIL] 9f 契约校验未触发（makefig 不调 use_size 却没报错）")
            fails.append("makefig 契约校验")
        except ValueError:
            _plt.close("all")
            out("  [PASS] 9f makefig 不调 use_size 被拒（ValueError）")
        except Exception as e:  # noqa: BLE001
            _plt.close("all")
            out(f"  [FAIL] 9f 契约校验抛错异常类型 {type(e).__name__}: {e}")
            fails.append("makefig 契约校验")

    # --- 10. panel 分幅标号字重（默认 bold，weight 可覆盖）---
    try:
        _fig10, _ax10 = _plt.subplots(figsize=(4, 3))
        apply_style()
        panel(_ax10, "(a)")
        _ann = [a for a in _ax10.texts if a.get_text() == "(a)"][0]
        _w1 = str(_ann.get_fontweight()).lower()
        panel(_ax10, "(b)", weight="normal")
        _ann2 = [a for a in _ax10.texts if a.get_text() == "(b)"][0]
        _w2 = str(_ann2.get_fontweight()).lower()
        _plt.close(_fig10)
        if _w1 in ("bold", "700") and _w2 == "normal":
            out("  [PASS] panel 默认 bold；weight='normal' 可覆盖")
        else:
            out(f"  [FAIL] panel 字重 default={_w1!r} override={_w2!r}")
            fails.append("panel 字重")
    except Exception as e:  # noqa: BLE001
        out(f"  [FAIL] panel weight: {type(e).__name__}: {e}")
        fails.append("panel weight")

    # 收尾：黄金值验完后，还原调用者原来的版心（不把 14.65 强加给调用者）
    if abs(_orig_cm - _REF_CM) > 1e-12:
        set_text_width_cm(_orig_cm)
        out(f"  [INFO] 已还原调用者版心 TEXT_WIDTH_CM={TEXT_WIDTH_CM:g}")

    out(f"结论：{'全部通过' if not fails else '失败 ' + str(len(fails)) + ' 项: ' + str(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
