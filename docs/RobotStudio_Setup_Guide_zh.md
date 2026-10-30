---
title: MA6212 弯管取放工作站 · RobotStudio 搭建步骤
---

所有坐标单位为 mm，与报告表 3 和 RAPID 程序 `ElbowPickPlace.mod` 一致。机器人底座中心是世界坐标原点。

# 0. 准备

1. 安装 RobotStudio（ABB 官网下载，用学校许可证激活）。
2. 把 `CAD` 文件夹（7 个 STL）和 `ElbowPickPlace.mod` 放在同一个项目文件夹里。
3. 新建一个空工作站：File → New → Empty Station。

# 1. 机器人和控制器

1. Home → ABB Library → **IRB 1300**，选 **7 kg / 1.4 m** 版本。
2. Import Geometry → `robot_stand.stl`，放在原点。然后把机器人移到 (0, 0, 400)，也就是放在底座顶面上。
3. Robot System → **From Layout**，一路默认建好控制器（IRB 1300 通常需要 RobotWare 7 / OmniCore）。
4. 如果报错建不出来，换成 IRB 1200 或 IRB 120，记下来，在报告里说明。

> 导入 STL 后先检查尺寸：弯管外形应约 257 × 257 × 215 mm。如果大了或小了 1000 倍，右键 → Modify → Set Scale 修正，或在导入时选单位 mm。

# 2. 摆放设备（Set Position，世界坐标）

| 模型 | 位置 (X, Y, Z) | 说明 |
|---|---|---|
| interim_station.stl | (700, −200, 0) | 中间工位，台面高 600 |
| box_conveyor.stl | (−150, −750, 0) | 纸箱辊筒线，顶面高 400 |
| packing_box.stl | (−150, −750, 400) | 纸箱 |
| Belt Conveyor（课件 Library 里的 `Belt Conveyor.rslib`） | 皮带面高 600，沿 X 方向，中心线 Y = 650 | 来料传送带 |
| fence.rslib | 围住整个工作站 | 安全围栏 |
| elbow_pipe.stl | 作为 Source 的模板，放在 (400, 540, 600) | 弯管 |
| gasket.stl | 中间工位上，套在弯管 A 端 | 垫片（静态） |

# 3. 吸盘工具

1. Import Geometry → `vacuum_gripper.stl`。
2. Modeling → **Create Tool**：
   - Tool name 填 `tVacuum`，Mass 1.2 kg，CoG (0, 0, 70)。
   - TCP 名 `tVacuum`，位置 (0, 0, 175)，方向 (0, 0, 0)。
3. 把工具拖到机器人上，安装到法兰（Update position 选 Yes）。

# 4. Smart Component

## 4.1 吸盘 SC_Gripper

- 组件：**LineSensor**（Start 为 TCP 上方 20 mm，End 为 TCP 下方 10 mm，半径 3 mm）+ **Attacher** + **Detacher** + **LogicGate (NOT)**。
- 输入信号 `diVacuum`：
  - `diVacuum` → LineSensor.Active 和 Attacher.Execute
  - `diVacuum` → NOT → Detacher.Execute
- LineSensor.SensedPart → Attacher.Child；Attacher.Child → Detacher.Child；Attacher.Parent = 吸盘工具。
- 把 SC_Gripper 拖到机器人上，作为工具的一部分。

## 4.2 来料传送带 SC_Infeed

- **Source**（Source = elbow_pipe，Position (400, 900, 600)，即上游位置）
- **Queue**
- **LinearMover**（Direction (0, −1, 0)，Speed 200 mm/s，Reference = World）
- **PlaneSensor**（放在 Y = 540 平面附近）
- 逻辑：
  - Source.Executed → Queue.Enqueue
  - PlaneSensor.SensorOut = 1 → 停止 LinearMover，并输出 `doPartReady`
  - 机器人吸走工件后 → Queue.Dequeue，Source.Execute 生成下一个
- 如果做起来太复杂，可以简化为：Source 直接在 (400, 540, 600) 生成工件，PlaneSensor 检测到就置位 `doPartReady`。

# 5. I/O 信号和 Station Logic

1. Controller → Configuration → I/O System → **Signal**，新建 5 个虚拟信号（Assigned to Device 留空）：
   - `diPartReady`（DI）
   - `doVacuum`（DO）
   - `doGasket`（DO）
   - `doBoxFull`（DO）
   - `doConvStop`（DO）
2. 重启控制器。
3. Simulation → **Station Logic** → Signals and Connections，连接：
   - 控制器 `doVacuum` → SC_Gripper.`diVacuum`
   - SC_Infeed.`doPartReady` → 控制器 `diPartReady`
   - 控制器 `doConvStop` → SC_Infeed 的停止输入（可选）

# 6. 导入 RAPID

1. RAPID 选项卡 → 在 T_ROB1 上右键 → Load Module → `ElbowPickPlace.mod`。
2. 如果已有一个空的 `MainModule` 里也有 `main`，把那个删掉，避免重复定义。
3. 点 **Apply**，再点 **Check Program**，确认没有错误。
4. 把 3 个工件坐标系同步到工作站：RAPID → Synchronize → **Synchronize to Station**，然后在 Paths & Targets 里能看到 `wobjVision`、`wobjInterim`、`wobjBox`。
5. 检查目标点 `pCP1` / `pCP2` 能否到达：右键 → Jump to Target。
   - 如果姿态翻转或不可达，在 Paths & Targets 里对目标点做 Configurations → Auto Configuration。
   - 也可以把 orient 改成 [0, 0, 1, 0]（绕 Y 轴翻转），再重新同步。

# 7. 仿真和测量

1. Simulation → Collision Set：一组放工具 + 弯管，另一组放传送带、工位和纸箱。
2. Simulation → **Play**，跑完 16 件。
3. 节拍数据看 RAPID 输出窗口（TPWrite），或者取控制器 HOME 目录下的 `cycle_log.csv`（Controller → File Transfer）。
4. 可选：Simulation → **Signal Analyzer** 记录 `doVacuum` 的时序图，截图放进报告。

# 8. 截图清单（报告里黄色占位处）

- 全站视图（图 3）
- 路径和目标点，要显示 `wobjVision` 坐标系（图 4）
- 仿真运行中 + 节拍输出（图 7）
- 节拍数据填进表 6、第 6.3 节和结论里的 [avg] / [throughput]

# 9. 打包提交

1. File → Share → **Pack and Go** → `MA6212_ElbowCell.rspag`，勾选包含控制器。
2. 换一台电脑解包测试，确认能正常打开和运行。
3. 提交以下文件：
   - 报告 docx（另存为 PDF 也可以）
   - `.rspag` 文件
   - `CAD` 文件夹（7 个 STL）
   - `ElbowPickPlace.mod`
