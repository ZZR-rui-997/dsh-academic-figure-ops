# 三维渲染章（pyvista 路线）

> **何时用**：需要真 3D 效果的图——三维几何体、相界面（锋面）推进过程、等值面、多视角并排、剖切与剖视。
> 2D 云图 / 流线**不走这里**（那是样式问题，见 `cfd-figure-patterns.md`）。matplotlib 的 mplot3d 曲面也不走这里：它仍按普通数据图走字号与落盘链。本章专指 **pyvista / VTK 渲染的真三维场景**。
> 依赖：`pyvista`（本文实测 0.49.3，VTK 9.7.1 底座）。整章路线**不依赖** Blender / ParaView。

## 0. 什么时候用 3D、什么时候别用

- **用**：几何本体就是三维的（带起伏的上下两个界面、厚度/间隙场、相界面推进过程）；需要多视角并排（等轴 / 侧视 / 正视三机位）来交代空间关系。
- **别用**：平面的场量分布（XY 云图）——2D matplotlib 更可控，也更容易过 `check_figure.py` 的字号链。
- 3D 图落盘后**同样要过 `check_figure.py`**（字号 / 有效分辨率判定）；渲染窗口从 `window_size=(1600, 900)` 起步，印刷不够再放大。

## 1. 三个实测坑（先读，省一次返工）

1. **`add_text()` 不渲染中文**（VTK 内置无中文字库，中文直接丢字）。图内文字一律英文 + 数字（如 `Phase front x=180 mm, aperture b=1.0 mm`）；中文标题 / 轴名用 matplotlib 后期合成（`imshow` 渲染帧 + `fig.text`），或交给图题注。
2. **`StructuredGrid` 没有 `.wireframe()` 方法**——先 `extract_surface()` 再给 `style="wireframe"`；且 0.49+ 要显式传 `algorithm=`（否则触发 PyVistaFutureWarning）。
3. **`pv.Plane(i_size=, j_size=)` 的两个尺寸是实际长度、不是网格数**——做"贴合上下界面的锋面"时，要用该 x 处上下界面的高差当 `j_size`、y 向长度当 `i_size`，中心 z 取两者均值。

## 2. 标准场景配方（通用口径）

```python
import pyvista as pv
pv.OFF_SCREEN = True

p = pv.Plotter(off_screen=True, window_size=(1600, 900))
p.set_background("white")                      # 白底——印刷要求
p.add_mesh(grid_top, color="#CFE8DA", smooth_shading=True)   # 上界面：浅绿
p.add_mesh(grid_bot, color="#C9DCE9", smooth_shading=True)   # 下界面：浅蓝
p.add_mesh(surf,     color="#D55E00", opacity=0.6, smooth_shading=True)  # 相界面：Okabe-Ito 橙
p.add_mesh(grid_top.extract_surface(), style="wireframe",
           color="#333333", opacity=0.06, line_width=1)      # 上界面网格：极淡
p.add_text("...", font_size=11, color="#153A60")             # 英文文字
p.camera_position = "iso"
p.screenshot("out.png")   # 或 p.show(screenshot=...)
```

- **配色**：沿用语义色表（`schematic-and-flowchart.md` §5）——界面 / 几何面用浅绿 / 浅蓝、相界面用 Okabe–Ito 橙 `#D55E00`、文字 `#153A60`；灰度打印时橙 → 中灰、两个界面 → 浅灰 / 深灰，仍能区分。
- **光照**：默认三点光够用；要更强立体感用 `p.enable_eye_dome_lighting()`（等值面 / 点云）+ `smooth_shading=True`。
- **透明度纪律**：遮挡关系一次说清——锋面 0.5–0.65，内部填充体 ≤0.2，网格线 ≤0.08；叠加超过三层必须另给分解视图。

## 3. 多视角（多方向并排）

同一个 Plotter 里循环换 `camera_position` 再截图**会被复用覆盖**——要么每个机位独立建 Plotter，要么每次截图前重设相机三件套：
`p.camera_position = [focal, position, up]`（等轴视角可直接用内置 `"iso"`；正视 / 侧视给三元组）。
三机位并排 = matplotlib `subplots` 各塞一张渲染帧，再按正常落盘链过验收（此时字号与版心由 matplotlib 那一层负责，不再由渲染窗口负责）。

## 4. 数据源

- 求解器结果：Fluent 的 `.cas.h5 / .dat.h5` 用 PyFluent 读出各场，转成 `StructuredGrid` / `UnstructuredGrid` 再进 pyvista；**不要**拿求解器自带截图当交付。
- 几何：已有的面数据（点云 / 三角面 / 结构化网格节点）可直接构造 `StructuredGrid` 或 `UnstructuredGrid`；只有面片时先 `extract_surface()` / 三角化再喂。
- 点序与维度对不上时，模型会"拧成麻花"——先核对 `grid.dims` 与数据点的排列顺序（哪个方向是 i / j / k），这不是渲染问题，改渲染参数治不好。

## 5. 来源与忠实度

- 光照 / 相机 / 材质的"参数表思路"编目自公开仓库 `chingswy/skill-research-figure`（Blender 路线，★186，**无 license——只借方法论**，不复制其代码或素材）；本文全部代码按 pyvista 0.49.3 实测重写并冒烟通过。
- 与 Blender / ParaView 的边界：本文路线不依赖它们；真要影视级重场景渲染（体积光、景深、动画序列），那是另一个量级的工作，另立项做，不要在这份规程里假装能用。