# -*- coding: utf-8 -*-
"""paper_style — 案例库配方共享工具（本 skill 自带，替代原库的 paper_style 模块）。

来源说明：案例配方原先依赖一个外部样式模块；本文件是按同一版式口径重新实现的版本
（未随案例分发，导致 19 个配方 import 即 ModuleNotFoundError）。本文件按
配方实际用到的符号**重实现**同名接口，让配方开箱可跑；实现走本 skill 统一 figstyle
口径（Times+SimSun、Okabe-Ito、版心 14.65 cm 反算），风格与原库不同属预期——
配方教的是"图型做法"，配色/字体交给本 skill 统一管。

提供符号（逐个核对 19 个配方后汇总）：
  set_style()          应用本 skill 统一样式（等价 figstyle.apply_style，另配 dpi=150 便于快速预览）
  save(fig, path, dpi=150)   便捷落盘（tight）
  rng(seed)            -> numpy.random.default_rng(seed)
  cm2in(x)             cm -> inch
  p_to_stars(p)        p 值 -> "*"/"**"/"***"/"ns"
  sig_bracket(ax, x1, x2, y, h, text)  显著性横线+支架
  italic_gene(s)       基因名斜体包装
  PALETTE              Okabe-Ito 色表 dict（blue/orange/green/vermillion/sky/bluishpurple/reddishpurple）
  CMAP_AP              蓝-白-红发散 cmap（同 figstyle.CMAP_AP）
"""
from __future__ import annotations
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

try:
    import figstyle as _fs
    _TEXT_WIDTH_IN = _fs.TEXT_WIDTH_IN
    _apply_style = _fs.apply_style
except Exception:  # figstyle 不在 path 时退化为内置样式（保证配方仍可跑）
    _TEXT_WIDTH_IN = 14.65 / 2.54
    def _apply_style():
        matplotlib.rcParams.update({
            "font.family": ["Times New Roman", "SimSun"],
            "axes.unicode_minus": False,
            "font.size": 21.0,
            "axes.linewidth": 1.46,
            "xtick.direction": "in", "ytick.direction": "in",
            "xtick.top": True, "ytick.right": True,
            "savefig.dpi": 150,
        })

PALETTE = dict(
    blue="#0072B2", orange="#E69F00", green="#009E73",
    vermillion="#D55E00", sky="#56B4E9", bluishpurple="#CC79A7",
    reddishpurple="#8B4A9E", ink="#153A60", grey="#333333",
)

CMAP_AP = LinearSegmentedColormap.from_list(
    "AP", ["#153A60", "#3D6FA8", "#7FA6C9", "#FFFFFF", "#F2B8A0", "#D55E00", "#8A2A10"])

def set_style() -> None:
    """应用本 skill 统一印刷样式（figstyle 口径）。"""
    _apply_style()
    matplotlib.rcParams["savefig.dpi"] = 150   # 配方预览用，正文图请走 figstyle.use_size 全链

def save(fig, path, dpi: int = 150) -> None:
    fig.savefig(path, dpi=dpi, bbox_inches="tight")

def rng(seed: int):
    return np.random.default_rng(seed)

def cm2in(w: float, h: float | None = None):
    """cm -> inch；给两个数直接返回 figsize 元组。"""
    if h is None:
        return w / 2.54
    return (w / 2.54, h / 2.54)

def p_to_stars(p: float) -> str:
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"

def sig_bracket(ax, x1, x2, y, text="*", h=None, **kw):
    """显著性横线+支架：从 (x1,y) 到 (x2,y) 带两脚高 h，text 居中在上。
    （h 是比例，如 0.03=当前 ylim 的 3%；text 也可作第 5 位置参数传入。）"""
    if isinstance(text, (int, float)) and h is None:
        text, h = "*", text  # 不可能：仅防御
    if h is None:
        h = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.03
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=1.1, c="k")
    if text:
        fs = kw.pop("fontsize", matplotlib.rcParams["font.size"] * 0.85)
        ax.text((x1 + x2) / 2, y + h, text, ha="center", va="bottom", fontsize=fs, **kw)

def italic_gene(s: str) -> str:
    # mathtext 里 '-' 是减号、会破坏解析；转成 \\mathit{} 内安全形式（hyphen 用 \\text? mathtext 不支持 text，
    # 改为把 '-' 换成 Unicode 连字符 U+2010，matplotlib 能正常显示）
    safe = s.replace("-", "\u2010")
    return "$\\mathit{" + safe + "}$"


def despine(ax, left=False, right=True, top=True, bottom=False):
    """seaborn 风格去框：默认去掉上/右，保留左/下（参数 True=去掉）。"""
    for side, hide in (("top", top), ("right", right),
                       ("left", left), ("bottom", bottom)):
        ax.spines[side].set_visible(not hide)
