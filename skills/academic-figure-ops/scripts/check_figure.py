#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_figure — 判定一张学术插图落盘后是否达到印刷字号标准（只读）

它解决什么问题
--------------
常见的问题是：脚本里写着 font.size=10.5，看着没问题，
但画布有 10 in 宽，按版心宽度（默认 14.65 cm）排版后实际只有 **6.06 pt**
（10.5 × 5.7677 ÷ 10），只有目标 10.5 pt 的 58%。肉眼在图上看不出来，插进文档才露馅。

反算公式（唯一口径，全流程通用）：
    印刷pt = 图内设定pt × 版心宽cm ÷ (落盘像素宽 ÷ dpi)

版心宽默认 14.65 cm（A4 + 左右各 3.17 cm 页边距的常见值），
换纸张/换页边距时用 ``--text-width-cm`` 换成你自己量出的正文宽度。

为什么必须告诉它"设定pt 是多少"
------------------------------
落盘 PNG 里**量得到像素宽，量不到脚本里写的字号**。实践中常见两种写法，
它们的"设定pt"完全不同，但落盘文件长得一模一样，无法从 PNG 反推：

  口径① use_size 约定（推荐，新图一律用它）
      脚本：fig = plt.figure(figsize=(13, 11))
            figstyle.use_size(13)
      此时 use_size 把 10.5 按 K = 13 ÷ 版心宽in（默认 14.65 cm ⇒ 5.7677 in）
      = 2.254 放大，实际写进 rcParams 的轴标签字号是 10.5 × 2.254 = 23.67 pt。
      ⇒ 印刷pt = 10.5 × 13 ÷ 落盘宽in = 10.5 × canvas_w ÷ saved_w

  口径② 固定字号约定（不调 use_size 的旧脚本或别人的脚本）
      脚本：rcParams['font.size'] = 10.5
      ⇒ 印刷pt = 10.5 × 版心宽in ÷ 落盘宽in

把口径①当成②算，同一张图会得到 4.62 pt（判 FAIL），而真值是 10.41 pt（达标）。
这正是**自信的错误 FAIL**。所以本脚本强制要求显式声明口径，
**两个都不给就 exit 2「未执行」**，绝不用默认值静默判定。

用法
----
    # 用 use_size 的图：告诉它画布宽（= use_size 的实参）
    python check_figure.py --canvas-w 13 figures/fig1.png

    # 整目录、每张画布宽不同时，逐张给
    python check_figure.py \
        --canvas-w 13   figures/fig1.png \
        --canvas-w 12.6 figures/fig2.png
    # ↑ 老式写法不便于批量，推荐 --pair 清单文件（见下）

    # 批量：写一个 csv/txt，每行 "画布宽,路径"
    python check_figure.py --pair canvas_map.txt

    # 固定 10.5 pt 的图（<figs> 换成那批图所在目录）
    python check_figure.py --fs 10.5 <figs>

    # 版心宽度不是默认值时（务必按你自己量出的正文宽度改）
    python check_figure.py --text-width-cm 12.0 --canvas-w 13 figures/

    # 机器可读
    python check_figure.py --fs 10.5 --json <figs>

退出码（契约）
--------------
    0  全部达标（每张印刷字号都在目标 ±容差内）
    1  存在不达标（逐张列出实测值与偏差）
    2  未执行（没声明口径 / 没给路径 / 路径不存在 / 找不到 png / 有图读失败）
    3  缺依赖（没有 PIL）——与 1 区分开，缺依赖绝不能算 0

设计约束
--------
- **只读**。不写、不改、不移动任何文件，不创建缓存。
- 不猜落盘 dpi：优先读 PNG 的 pHYs 块，其次 --dpi 覆盖，最后退 300。
- 判断依据是"落盘文件"，不是脚本里的 figsize——这正是常见出错的根因。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 与 figstyle 保持同一口径。模块可能不同目录，故做两路解析。
try:
    from figstyle import (  # 同目录 import（推荐：两个脚本放一起）
        TARGET_LABEL_PT, TARGET_TICK_PT, TOL_PASS, TOL_TIGHT,
    )
    _STYLE_LOADED = True
except Exception:  # noqa: BLE001 — 独立分发时退到内置常量，数值必须与 figstyle 一致
    TARGET_LABEL_PT = 10.5
    TARGET_TICK_PT = 9.5
    TOL_PASS = 0.05
    TOL_TIGHT = 0.02
    _STYLE_LOADED = False

#: 页面正文版心宽默认值 [cm]：A4 + 左右各 3.17 cm 页边距的常见值。
#: 运行时由 --text-width-cm 覆盖（见 set_text_width_cm），
#: 之后所有反算都读 TEXT_WIDTH_IN，脚本里没有别处写死宽度。
DEFAULT_TEXT_WIDTH_CM = 14.65
TEXT_WIDTH_CM = DEFAULT_TEXT_WIDTH_CM
TEXT_WIDTH_IN = TEXT_WIDTH_CM / 2.54

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_NOT_RUN = 2
EXIT_NO_DEP = 3

PNG_SUFFIXES = {".png"}


class CaliberError(Exception):
    """口径声明不合规时抛出，一律映射到 exit 2（未执行）。"""


def set_text_width_cm(value: float) -> float:
    """把版心宽度设为 ``value`` cm，并重算 TEXT_WIDTH_IN。

    这是 ``--text-width-cm`` 的落地点：之后 set_pt_for() / check_one() 读到的
    都是新口径。默认 14.65 cm 只是 A4 + 左右各 3.17 cm 页边距这一种版式的
    值；换页边距就要换成你量出来的正文宽度，否则印刷字号会整体算偏。

    Returns
    -------
    float
        生效后的 TEXT_WIDTH_CM。
    """
    global TEXT_WIDTH_CM, TEXT_WIDTH_IN
    v = float(value)
    if not (v > 0.0):
        raise CaliberError(f"--text-width-cm 必须为正数，收到 {value}")
    TEXT_WIDTH_CM = v
    TEXT_WIDTH_IN = v / 2.54
    return TEXT_WIDTH_CM


def _ensure_width_consistent() -> None:
    """兜底同步：允许直接改模块级 ``TEXT_WIDTH_CM``（绕开 set_text_width_cm）。"""
    if abs(TEXT_WIDTH_IN - TEXT_WIDTH_CM / 2.54) > 1e-9:
        set_text_width_cm(TEXT_WIDTH_CM)


def _iter_pngs(targets: list[str]) -> list[Path]:
    """把入参展开成 png 文件列表（目录递归）。非 png 文件显式提示后跳过。"""
    found: list[Path] = []
    for t in targets:
        p = Path(t)
        if p.is_dir():
            found.extend(
                q for q in sorted(p.rglob("*")) if q.suffix.lower() in PNG_SUFFIXES
            )
        elif p.is_file() and p.suffix.lower() in PNG_SUFFIXES:
            found.append(p)
        elif p.is_file():
            print(f"[skip] 不是 png，已跳过：{p}", file=sys.stderr)
        else:
            print(f"[skip] 路径不存在，已跳过：{p}", file=sys.stderr)
    return found


def _read_image(path: Path, dpi_override: float | None) -> tuple[int, int, float]:
    """返回 (像素宽, 像素高, dpi)。dpi：override > pHYs > 300。"""
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
        info_dpi = im.info.get("dpi")
        if dpi_override is not None:
            dpi = float(dpi_override)
        elif info_dpi:
            dpi = float(info_dpi[0])
        else:
            dpi = 300.0
    return w, h, dpi


def set_pt_for(canvas_w_in: float | None, fs_pt: float | None) -> tuple[float, str]:
    """把口径声明换算成"图内实际设定pt"及其口径名。

    口径① use_size：图内设定pt = TARGET_LABEL_PT × canvas_w / TEXT_WIDTH_IN
    口径② 固定字号：图内设定pt = fs_pt
    """
    if canvas_w_in is not None:
        if canvas_w_in <= 0:
            raise CaliberError(f"--canvas-w 必须为正数，收到 {canvas_w_in}")
        return TARGET_LABEL_PT * canvas_w_in / TEXT_WIDTH_IN, "use_size"
    if fs_pt is not None:
        if fs_pt <= 0:
            raise CaliberError(f"--fs 必须为正数，收到 {fs_pt}")
        return float(fs_pt), "fixed"
    raise CaliberError(
        "必须声明口径：--canvas-w W（use_size 约定）或 --fs F（固定字号约定）二选一。\n"
        "  不声明就判定 = 用错的设定pt 算，会给出自信的错误结论（这类错误很常见）。\n"
        "  批量时应改用 --pair 清单（每行 '画布宽,路径'），不要逐张手敲。\n"
        "  固定字号的图：--fs 10.5\n"
        "  版心宽度不是默认 14.65 cm 时，另加 --text-width-cm <你的正文宽度 cm>"
    )


def check_one(
    path: Path,
    canvas_w_in: float | None,
    fs_pt: float | None,
    dpi_override: float | None,
    tol: float,
    min_eff_dpi: float | None = None,
) -> dict:
    """判定单张图。返回结构化结果，不打印。

    两个判据互相独立，都必须过：
      1. 印刷字号 median-ok（printed_pt 在 target ±tol 内）
      2. 有效分辨率（若给了 min_eff_dpi）：eff_dpi = 像素宽 ÷ 版心宽in
         —— 注意这不是 PNG 里那个 pHYs 的 dpi 参数，而是"缩到版心宽后
         每英寸还剩多少像素"。杂志说的 600 dpi 指的是这个。
    """
    set_pt, caliber = set_pt_for(canvas_w_in, fs_pt)
    _ensure_width_consistent()
    w, h, dpi = _read_image(path, dpi_override)
    saved_w_in = w / dpi if dpi > 0 else float("nan")
    printed = set_pt * TEXT_WIDTH_IN / saved_w_in if saved_w_in > 0 else float("nan")
    eff_dpi = w / TEXT_WIDTH_IN if w else float("nan")
    err = (
        abs(printed - TARGET_LABEL_PT) / TARGET_LABEL_PT
        if printed == printed
        else float("nan")
    )

    if printed != printed:  # NaN
        verdict = "error"
    elif err > tol:
        verdict = "fail"
    elif min_eff_dpi is not None and eff_dpi < min_eff_dpi:
        verdict = "fail"  # 字号合格但分辨率不够，仍判不合格
    else:
        verdict = "pass"

    return {
        "path": str(path),
        "caliber": caliber,
        "px": [w, h],
        "dpi": round(dpi, 4),
        "eff_dpi": eff_dpi,          # 不在这里 round，让打印层一次成型（否则双重舍入）
        "min_eff_dpi": min_eff_dpi,
        "saved_width_in": round(saved_w_in, 4),
        "saved_width_cm": round(saved_w_in * 2.54, 3),
        "set_pt": round(set_pt, 3),
        "printed_pt": round(printed, 3) if printed == printed else None,
        "target_pt": TARGET_LABEL_PT,
        "dev_pct": round(err * 100, 2) if err == err else None,
        "verdict": verdict,
    }


def _parse_pair_file(path: Path) -> list[tuple[float, str]]:
    """读 --pair 清单：每行 "画布宽,图片路径"；空行与 # 注释跳过。"""
    pairs: list[tuple[float, str]] = []
    text = path.read_text(encoding="utf-8-sig")
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # 允许中英文逗号与制表符作分隔
        for sep in ("\t", ",", "，"):
            if sep in line:
                left, _, right = line.partition(sep)
                break
        else:
            raise CaliberError(f"--pair 第 {lineno} 行无法切分（需 '画布宽,路径'）：{line}")
        try:
            cw = float(left.strip())
        except ValueError as e:
            raise CaliberError(f"--pair 第 {lineno} 行画布宽不是数字：{left!r}") from e
        pairs.append((cw, right.strip()))
    if not pairs:
        raise CaliberError(f"--pair 文件里没有任何有效行：{path}")
    return pairs


def _print_table(rows: list[dict], quiet: bool) -> None:
    if quiet:
        return
    head = (f"{'实测pt':>8} {'偏差%':>7} {'有效dpi':>8} {'落盘宽cm':>9} "
            f"{'设定pt':>8} {'口径':>9} {'px':>13}  判定  文件")
    print(head)
    print("-" * (len(head) + 20))
    for r in rows:
        # 每一列都必须做 None 保护：读失败的行（verdict=="error"）这些字段全是 None，
        # 少保护一个就会在格式化时抛 TypeError，把 exit 2「未执行」变成 exit 1
        #「有不达标」——而这个 skill 自己最强调的就是"2 和 1 含义相反"。
        pt = "     n/a" if r["printed_pt"] is None else f"{r['printed_pt']:8.2f}"
        dev = "    n/a" if r["dev_pct"] is None else f"{r['dev_pct']:7.1f}"
        # 有效 dpi 只存了原始值，这里一次成型，避免 round(x,1) + :.0f 的双重舍入
        # （246.545 会被显示成 246 而不是 247，读者会以为真值就是 246）
        ed = "     n/a" if r.get("eff_dpi") is None else f"{r['eff_dpi']:8.0f}"
        wcm = "      n/a" if r["saved_width_cm"] is None else f"{r['saved_width_cm']:9.2f}"
        spt = "     n/a" if r["set_pt"] is None else f"{r['set_pt']:8.2f}"
        cal = f"{r['caliber']:>9}"
        px = f"{r['px'][0]}x{r['px'][1]}"
        mark = {"pass": "PASS", "fail": "FAIL", "error": "ERR "}[r["verdict"]]
        print(f"{pt} {dev} {ed} {wcm} {spt} {cal} {px:>13}  {mark}  {Path(r['path']).name}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="判定学术插图落盘后的实际印刷字号是否达标（只读）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "退出码：0=全部达标  1=有不达标  2=未执行（未声明口径/无输入/无png/读失败）  "
            "3=缺依赖（无PIL）\n"
            "反算公式：印刷pt = 图内设定pt × 版心宽cm ÷ (像素宽 ÷ dpi)\n"
            "口径① --canvas-w W ：use_size 约定，设定pt = 10.5 × W ÷ 版心宽in\n"
            "口径② --fs F       ：固定字号约定，设定pt = F\n"
            "版心宽默认为 14.65 cm，用 --text-width-cm 换成本页实测宽度"
        ),
    )
    ap.add_argument("targets", nargs="*", help="png 文件或目录（目录递归找 png）")
    ap.add_argument("--canvas-w", type=float, default=None,
                    help="口径①：脚本里 use_size() 的实参（画布宽，英寸）")
    ap.add_argument("--fs", type=float, default=None,
                    help="口径②：脚本里固定写死的字号（pt）")
    ap.add_argument("--text-width-cm", type=float, default=DEFAULT_TEXT_WIDTH_CM,
                    help="你的页面正文宽度（cm）；默认 14.65 = A4 + 左右 3.17 cm "
                         "页边距的常见值，务必按你自己的页边距改")
    ap.add_argument("--pair", type=str, default=None,
                    help="批量口径①：清单文件，每行 '画布宽,图片路径'（# 开头为注释）")
    ap.add_argument("--tick-pt", type=float, default=TARGET_TICK_PT,
                    help=f"刻度字号（仅用于报告），默认 {TARGET_TICK_PT}")
    ap.add_argument("--dpi", type=float, default=None,
                    help="强制 dpi；缺省读 PNG 的 pHYs 块，再缺省用 300")
    ap.add_argument("--tol", type=float, default=TOL_PASS,
                    help=f"相对容差，默认 {TOL_PASS}（±5%%）；"
                         f"单图自检建议 {TOL_TIGHT}")
    ap.add_argument("--min-eff-dpi", type=float, default=None,
                    help="额外要求：按 --text-width-cm 给出的版心宽排版后的有效分辨率不低于此值"
                         "（线条图期刊常要 600，照片 300）。不给则只验字号。")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--quiet", action="store_true", help="不打印表格，只看退出码")
    args = ap.parse_args(argv)

    # --- 先把版心宽度定下来：后面所有反算都读 TEXT_WIDTH_IN ---
    try:
        set_text_width_cm(args.text_width_cm)
    except CaliberError as e:
        print(f"[未执行] {e}", file=sys.stderr)
        return EXIT_NOT_RUN

    # --- 依赖检查：缺 PIL 必须 exit 3，不能 0 ---
    try:
        import PIL  # noqa: F401
    except Exception as e:  # noqa: BLE001
        print(f"[未执行] 缺 PIL，无法读取落盘图：{e}", file=sys.stderr)
        print("请换成装了 Pillow 的解释器（依赖与自检见本 skill 的 SKILL.md「零、怎么用」）。",
              file=sys.stderr)
        return EXIT_NO_DEP

    # --- 口径声明与 --pair 互斥检查 ---
    n_caliber = sum(x is not None for x in (args.canvas_w, args.fs))
    if args.pair is not None:
        if n_caliber:
            print("[未执行] --pair 与 --canvas-w/--fs 不能同时用（--pair 自带逐张画布宽）",
                  file=sys.stderr)
            return EXIT_NOT_RUN
        if not Path(args.pair).is_file():
            print(f"[未执行] --pair 文件不存在：{args.pair}", file=sys.stderr)
            return EXIT_NOT_RUN
    else:
        if n_caliber != 1:
            try:
                set_pt_for(args.canvas_w, args.fs)  # 复用同一条报错文案
            except CaliberError as e:
                print(f"[未执行] {e}", file=sys.stderr)
                return EXIT_NOT_RUN
            print("[未执行] --canvas-w 与 --fs 只能给一个", file=sys.stderr)
            return EXIT_NOT_RUN

    # --pair 模式自带逐张路径，不要求 targets；非 pair 模式必须有 targets
    if args.pair is None and not args.targets:
        print("[未执行] 没有给任何路径。用法：check_figure.py --fs 10.5 <png或目录>",
              file=sys.stderr)
        return EXIT_NOT_RUN

    rows: list[dict] = []

    if args.pair is not None:
        try:
            pairs = _parse_pair_file(Path(args.pair))
        except (CaliberError, OSError) as e:
            print(f"[未执行] 读 --pair 失败：{e}", file=sys.stderr)
            return EXIT_NOT_RUN
        # --pair 模式下若同时给了 targets，则用 targets 过滤（可选便利）
        wanted = _iter_pngs(args.targets) if args.targets else None
        for cw, pstr in pairs:
            p = Path(pstr)
            if wanted is not None and p.resolve() not in {q.resolve() for q in wanted}:
                continue
            try:
                rows.append(check_one(p, cw, None, args.dpi, args.tol, args.min_eff_dpi))
            except Exception as e:  # noqa: BLE001
                print(f"[error] 读不了 {p}：{e}", file=sys.stderr)
                rows.append(_error_row(p, cw, None, args.tol))
    else:
        files = _iter_pngs(args.targets)
        if not files:
            print(f"[未执行] 在给定路径下一个 png 都没找到：{args.targets}", file=sys.stderr)
            return EXIT_NOT_RUN
        for f in files:
            try:
                rows.append(check_one(f, args.canvas_w, args.fs, args.dpi, args.tol, args.min_eff_dpi))
            except Exception as e:  # noqa: BLE001 — 单张读失败不静默跳过
                print(f"[error] 读不了 {f}：{e}", file=sys.stderr)
                rows.append(_error_row(f, args.canvas_w, args.fs, args.tol))

    if not rows:
        print("[未执行] 没有任何图被判过（--pair 与 targets 过滤后为空）", file=sys.stderr)
        return EXIT_NOT_RUN

    n_pass = sum(1 for r in rows if r["verdict"] == "pass")
    n_fail = sum(1 for r in rows if r["verdict"] == "fail")
    n_err = sum(1 for r in rows if r["verdict"] == "error")

    if args.json:
        print(json.dumps({
            "style_module_loaded": _STYLE_LOADED,
            "target_pt": TARGET_LABEL_PT,
            "text_width_cm": round(TEXT_WIDTH_CM, 6),
            "text_width_in": round(TEXT_WIDTH_IN, 6),
            "tol": args.tol,
            "min_eff_dpi": args.min_eff_dpi,
            "summary": {"total": len(rows), "pass": n_pass, "fail": n_fail, "error": n_err},
            "rows": rows,
        }, ensure_ascii=False, indent=2))
    else:
        _print_table(rows, args.quiet)
        if not args.quiet:
            print()
            print(f"合计 {len(rows)} 张：达标 {n_pass} / 不达标 {n_fail} / 读失败 {n_err}")
            print(f"判定基准：轴标签 {TARGET_LABEL_PT} pt × 版心 "
                  f"{TEXT_WIDTH_CM:g} cm（{TEXT_WIDTH_IN:.4f} in），"
                  f"容差 ±{args.tol * 100:.0f}%")
            if args.min_eff_dpi:
                print(f"　　　　　另要求有效分辨率 ≥ {args.min_eff_dpi:.0f} dpi"
                      f"（= 像素宽 ÷ {TEXT_WIDTH_IN:.4f} in）")
            if n_fail:
                # 失败可能来自两个独立判据，必须分开报，不能混成"字号不达标"
                pt_bad = [r for r in rows
                          if r["verdict"] == "fail" and r["printed_pt"] is not None
                          and abs(r["printed_pt"] - TARGET_LABEL_PT) / TARGET_LABEL_PT > args.tol]
                res_bad = [r for r in rows
                           if r["verdict"] == "fail"
                           and r not in pt_bad
                           and args.min_eff_dpi and (r["eff_dpi"] or 0) < args.min_eff_dpi]
                print()
                print("怎么修（按失败原因分开处理）：")
                if pt_bad:
                    pts = [r["printed_pt"] for r in pt_bad]
                    print(f"  【字号不达标】{len(pt_bad)} 张，实测 "
                          f"{min(pts):.2f}–{max(pts):.2f} pt（目标 {TARGET_LABEL_PT}）：")
                    print("    · 用 figstyle.use_size(W)，W = 当前 figsize 宽；或")
                    print("    · 用 figstyle.fit_and_save() 自动收敛到 ±2%。")
                    print("    · 注意：字号靠「放大设定 pt」修，不要靠缩画布——缩画布会")
                    print("      同时把有效分辨率拉低（见下一条）。")
                if res_bad:
                    eds = [r["eff_dpi"] for r in res_bad]
                    print(f"  【有效分辨率不达标】{len(res_bad)} 张，实测 "
                          f"{min(eds):.0f}–{max(eds):.0f} dpi"
                          f"（要求 ≥ {args.min_eff_dpi:.0f}）：")
                    print(f"    · 有效dpi = 像素宽 ÷ {TEXT_WIDTH_IN:.4f} in，"
                          "要提它只能「加宽画布或提高导出 dpi」。")
                    print(f"    · 需要像素宽 ≥ {TEXT_WIDTH_IN * args.min_eff_dpi:.0f} px；")
                    print("      figsize 宽 12–14.5 in @300dpi 即 3600–4350 px，达标")
                    print("      （前提：存图不裁切。走 fit_and_save 会 tight 裁到 ≈0.82 倍，")
                    print("      13 in 只有 3209 px→556 dpi，那就得给到 ≥14.5 in）。")
                    print("    · 配合 use_size 同值放大字号，字号**不会**因此变小。")
                print("  【两个都达标的最省配方】figsize 宽 12–14.5 in + "
                      "use_size(同值) + dpi 300")

    if n_err:
        return EXIT_NOT_RUN
    if n_fail:
        return EXIT_FAIL
    return EXIT_OK


def _error_row(path: Path, canvas_w_in: float | None, fs_pt: float | None,
               tol: float) -> dict:
    """构造一条"读失败"的结果行，保持字段与正常行一致（便于 --json 消费）。"""
    return {
        "path": str(path), "caliber": "use_size" if canvas_w_in else "fixed",
        "px": [0, 0], "dpi": None, "eff_dpi": None, "min_eff_dpi": None,
        "saved_width_in": None, "saved_width_cm": None,
        "set_pt": None, "printed_pt": None, "target_pt": TARGET_LABEL_PT,
        "dev_pct": None, "verdict": "error",
    }


if __name__ == "__main__":
    raise SystemExit(main())
