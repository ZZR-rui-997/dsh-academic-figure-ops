# -*- coding: utf-8 -*-
"""遮挡审计最小实现：图例/文字压数据的机械检测（第 1 版，管 matplotlib 成图）。
用法：在 figstyle 同目录 import；或 python overlap_audit.py <png>...
判据（通用 audit_gallery 思路）：
  A. 图例压数据：图例 bbox 与非白像素的交集面积 > 0 且交集中非白像素密度
     明显低于图例周边（说明被白底盖住）→ 记 issue。
  B. 文字压数据：渲染前对每个 Text 艺术家取 window_extent，与 Line2D/PathCollection
     的数据点像素坐标求交，交点数 > 0 → 记 issue（需 fig 与 ax 对象，渲染前调用）。
输出：issue 列表 + 可选基线文件（--update-baseline，格式：存量登记，
基线外新问题=FAIL）。
"""
from __future__ import annotations
import sys, json, os
# 刻意不在模块顶层 import numpy：位图审计函数里按需导入，
# 这样 `python overlap_audit.py --help` 在没有 numpy 的环境里也能跑。

def audit_pre_render(fig) -> list[str]:
    """渲染前审计：需要 fig/ax 对象（fig.canvas.draw() 之后调用）。"""
    issues = []
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for ax in fig.get_axes():
        leg = ax.get_legend()   # 提前取：图像 bbox 判定与点采样判定共用
        # 数据点像素坐标（抽稀到最多 400 点/线）
        data_pts = []
        for line in ax.get_lines():
            xy = line.get_xydata()
            if len(xy) == 0:
                continue
            step = max(1, len(xy) // 400)
            data_pts.extend(ax.transData.transform(xy[::step]))
        # imshow/pcolormesh 类：用"图像 bbox 与图例/文字 bbox 相交"判定，比点采样稳
        # （点采样在图例 bbox 很小或采样间距大时会漏检）。
        img_boxes = []
        for im in ax.images:
            try:
                ext = im.get_extent()  # (x0, x1, y0, y1) 数据坐标
                (px0, py0), (px1, py1) = ax.transData.transform([(ext[0], ext[2]), (ext[1], ext[3])])
                img_boxes.append((min(px0, px1), min(py0, py1), max(px0, px1), max(py0, py1)))
            except Exception:
                pass
        for col in (ax.collections, ax.patches):
            for c in col:
                try:
                    pts = c.get_offsets() if hasattr(c, "get_offsets") else []
                    if len(pts):
                        step = max(1, len(pts) // 400)
                        data_pts.extend(ax.transData.transform(pts[::step]))
                except Exception:
                    pass
        def _box_hit(b):
            hits = 0
            for (x, y) in data_pts:
                if b[0] <= x <= b[2] and b[1] <= y <= b[3]:
                    hits += 1
            return hits

        # 图像覆盖判定：图例/文字 bbox 与任一图像 bbox 有交集 → 记 1 条（不分点位）
        if img_boxes:
            if leg is not None:
                lb = leg.get_window_extent(renderer)
                for ib in img_boxes:
                    if not (lb.x1 < ib[0] or lb.x0 > ib[2] or lb.y1 < ib[1] or lb.y0 > ib[3]):
                        issues.append(
                            f"legend covers image (imshow/pcolormesh): bbox overlap "
                            f"legend {lb.x0:.0f},{lb.y0:.0f}-{lb.x1:.0f},{lb.y1:.0f}")
                        break
            for t in ax.texts:
                st = t.get_text()
                if not st.strip():
                    continue
                tb = t.get_window_extent(renderer)
                for ib in img_boxes:
                    if not (tb.x1 < ib[0] or tb.x0 > ib[2] or tb.y1 < ib[1] or tb.y0 > ib[3]):
                        issues.append(f"text over image (no stroke/bbox): '{st[:24]}'")
                        break

        if not data_pts:
            continue
        # B1: 图例压数据
        if leg is not None:
            lb = leg.get_window_extent(renderer)
            hits = sum(1 for (x, y) in data_pts
                       if lb.x0 <= x <= lb.x1 and lb.y0 <= y <= lb.y1)
            if hits:
                issues.append(
                    f"legend covers data: {hits} pts under legend "
                    f"(bbox {lb.x0:.0f},{lb.y0:.0f}-{lb.x1:.0f},{lb.y1:.0f})")
        # B2: 文字压数据（轴内外注记/标题，跳过刻度标签）
        for t in ax.texts + [ax.title, ax.xaxis.label, ax.yaxis.label]:
            s = t.get_text()
            if not s.strip():
                continue
            tb = t.get_window_extent(renderer)
            hits = sum(1 for (x, y) in data_pts
                       if tb.x0 <= x <= tb.y1*0 + x*0 + 0 or (tb.x0 <= x <= tb.x1 and tb.y0 <= y <= tb.y1))
            if hits:
                issues.append(
                    f"text over data (no stroke/bbox): '{s[:24]}' ({hits} pts)")
    return issues

def audit_post_render(png_path: str) -> list[str]:
    """落盘后审计（位图层）：目前只做'图例区域白底密度'启发式。位图无法可靠
    区分图例与注记，故第 1 版只报可疑区域，预渲染审计才是主判据。"""
    from PIL import Image
    import numpy as np
    im = np.asarray(Image.open(png_path).convert("L"))
    h, w = im.shape
    issues = []
    # 粗筛：右下/右上角高度>宽度2倍的纯白矩形（图例惯犯位置）内含深像素则跳过，
    # 含中等灰度连续块则报可疑——保守起见第 1 版只对纯白大块报警。
    for (y0, y1, x0, x1, tag) in ((int(h*0.55), int(h*0.95), int(w*0.62), int(w*0.98), "lower-right"),
                                   (int(h*0.05), int(h*0.45), int(w*0.62), int(w*0.98), "upper-right")):
        box = im[y0:y1, x0:x1]
        white = (box > 250).mean()
        midtone = ((box > 60) & (box < 220)).mean()
        # 仅当"几乎全白 + 内部散布中灰像素"（白框盖住数据的痕迹）才报；
        # 纯空区域（坐标系本来空白）不报 → 修"无图例普通图恒报 2 条"的误报。
        if white > 0.97 and midtone > 0.02:
            issues.append(f"suspicious whiteout at {tag}: {white:.0%} white, "
                          f"{midtone:.1%} midtone under white (possible legend covering data)")
    return issues

def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    if argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    base_path = None
    pngs = []
    i = 1
    while i < len(argv):
        if argv[i] == "--update-baseline":
            i += 1
            base_path = argv[i]; i += 1
        else:
            pngs.append(argv[i]); i += 1
    all_issues = {}
    for p in pngs:
        iss = audit_post_render(p)
        if iss:
            all_issues[p] = iss
    if base_path:
        old = {}
        _write = not os.path.exists(base_path)  # 不存在=首次建档
        if _write:
            with open(base_path, "w", encoding="utf-8") as fh:
                fh.write("# 遮挡审计基线 — overlap_audit --update-baseline 生成\n")
                fh.write("# 用途：存量问题登记；基线外新问题=FAIL（对照通用 audit_gallery 做法）\n")
                for f, msgs in all_issues.items():
                    for m in msgs:
                        fh.write(f"{f} | {m}\n")
            print(f"BASELINE-CREATED: {base_path} ({sum(len(v) for v in all_issues.values())} 条存量登记)")
            return 0
        if os.path.exists(base_path):
            for line in open(base_path, encoding="utf-8"):
                line = line.rstrip("\n")
                if "|" in line and not line.startswith("#"):
                    f, _, msg = line.partition("|")
                    old.setdefault(f.strip(), set()).add(msg.strip())
        new = {}
        for f, msgs in all_issues.items():
            for m in msgs:
                if m not in old.get(f, set()):
                    new.setdefault(f, []).append(m)
        if new:
            print("BASELINE-FAIL: 基线外新问题")
            for f, msgs in new.items():
                for m in msgs:
                    print(f"  {f} | {m}")
            return 1
        print("BASELINE-OK: 无基线外新问题")
        return 0
    if all_issues:
        for f, msgs in all_issues.items():
            for m in msgs:
                print(f"{f} | {m}")
        return 1
    print("CLEAN: 未检出遮挡")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
