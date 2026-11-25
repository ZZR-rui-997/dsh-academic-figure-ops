# -*- coding: utf-8 -*-
"""chord — 和弦图两个几何 patch（本 skill 自带，替代原库 helpers/chord.py）。

接口（按 case_seg027 配方调用形态）：
  _arc_patch(center, R, a1, a2, width, color, alpha=1.0) -> matplotlib Patch
      圆弧段：半径 R、角 [a1,a2]（弧度）、环厚度 width（径向）。
  _ribbon(center, R, a1, a2, b1, b2, color, alpha=0.5) -> matplotlib Patch
      贝塞尔弦带：连接弧 [a1,a2] 与 [b1,b2] 的带状区。
"""
import numpy as np
from matplotlib.path import Path
from matplotlib.patches import PathPatch

def _arc_points(center, R, a1, a2, n=60):
    t = np.linspace(a1, a2, n)
    return np.column_stack([center[0] + R * np.cos(t), center[1] + R * np.sin(t)])

def _arc_patch(center, R, a1, a2, width, color, alpha=1.0, n=60):
    outer = _arc_points(center, R, a1, a2, n)
    inner = _arc_points(center, max(R - width, 1e-6), a2, a1, n)
    verts = np.vstack([outer, inner, [outer[0]]])
    codes = np.full(len(verts), Path.LINETO, dtype=np.int8)
    codes[0] = Path.MOVETO
    return PathPatch(Path(verts, codes), facecolor=color, edgecolor="none",
                     alpha=alpha, zorder=2)

def _ribbon(center, R, a1, a2, b1, b2, color, alpha=0.5, n=40):
    """弦带：两端各取弧段端点，用三次贝塞尔（控制点在圆心附近）连接。"""
    p1 = _arc_points(center, R, a1, a2, 2)          # 弧段端点（外沿两点）
    p2 = _arc_points(center, R, b1, b2, 2)
    start, end = p1[0], p2[0]
    # 控制点向圆心收缩，形成向内弯的弦
    c1 = center + (start - center) * 0.25
    c2 = center + (end - center) * 0.25
    end2, start2 = p2[1], p1[1]
    c3 = center + (end2 - center) * 0.25
    c4 = center + (start2 - center) * 0.25
    verts = [start, c1, c2, end,
             end, end2, c3, c4, start2, start2]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
             Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
             Path.CURVE4, Path.CLOSEPOLY]
    return PathPatch(Path(np.array(verts), codes), facecolor=color,
                     edgecolor="none", alpha=alpha, zorder=1)
