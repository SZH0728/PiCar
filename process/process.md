# 编写自定义 Process 工作流指南

本文档将指导你如何在现有框架中新增一个图像处理“Process”工作流，以便在运行时根据相机画面生成控制小车的命令。最后附录列出相关的
API 与数据结构，便于查阅。

---

## 总览

项目中的处理流程由以下模块协同工作：

- CameraDriver 捕获图像，封装为 Picture。
- Control 管理并执行具体的 Process。
- 每个 Process 继承自 BaseProcess，接收 Picture，输出 Command。
- Handle 接收 Command，调用 MotorDriver 控制电机或舵机。
- Console/Web 可用于查看与调整配置。

你需要做的：

1) 新建一个 Process 子类与其配置类。
2) 将该 Process 注册到 Control 的 PROCESS 列表。
3) 在配置中选择新 Process 为当前使用项。
4) 按需调试与输出中间结果。

---

## 基础概念与数据流

1. CameraDriver.get_frame() 产出 Picture(uid, frame, g)
2. Control.process(picture)

- 将 Picture 交给当前 Process 实例的 process()
- process() 内部调用你的 handle()，返回 Command
- Control 保存调试图片（可选）、并将 Command 返回

3. Handle.handle_command(command)

- 根据 Command.target 将动作落到 MotorDriver（电机/舵机）

你的核心工作：实现 BaseProcess.handle()，把输入图像转成 Command。

---

## 快速上手：创建一个新的 Process

假设你要新增一个“ExampleProcess”。

步骤 1：创建配置类与过程类

- 新建文件：process/example.py
- 定义配置类继承 BaseConfig
- 定义过程类继承 BaseProcess[ExampleConfig]

示例：

[example.py](example.py)

注意：

- BaseProcess.handle() 必须返回 Command。
- 调试图像的保存由 Control 负责：当 ControlConfig.save_debug 为 True 且 uid % interval == 0 时，Control 将读取你通过
  debug_picture() 收集的帧并保存到 ./debug。
- CameraDriver 当前配置格式为 YUV420，

步骤 2：在 Control 中注册你的 Process

- 修改 process/control.py 的 PROCESS 列表，添加你的类与配置类：

```python
from process.example import ExampleProcess, ExampleConfig

PROCESS: list[tuple[Type[BaseProcess], Type[BaseConfig]]] = [
    (ExampleProcess, ExampleConfig),
]
```

步骤 3：选择新 Process 为当前使用项

- 可以在运行时通过配置切换，也可直接修改默认配置。
- 方式 A：在启动前修改 Config.ControlConfig.used = 'follow_line'
- 方式 B：通过 Console/Web 工具读取/确认配置

例如，直接在 config.py 的 ControlConfig 默认值中设置：

```python
class ControlConfig(object):


    used: str = 'follow_line'
    save_debug: bool = True
    interval: int = 30
```

步骤 4：验证与调试

- 运行 main.py，确保 debug 目录已存在且可写。
- 若开启了 web 控制台（config.web=True），Console 会持续处理来自桥接客户端的命令。
- 检查日志输出与 ./debug/ 下的调试图像。

---

## 设计建议与最佳实践

- 明确输入输出：handle() 只使用必要的图像与元数据，确保输出的 Command 数据范围合法（速度 0-180；方向 0/1）。
- 性能与实时性：在 handle() 内避免过重的计算；将可调参数放入配置类，便于现场调参。
- 调试与可视化：
- 使用 self.debug 标志控制调试成本（Control 会按 interval 开关）。
- 使用 debug_picture(description, frame) 输出关键中间结果。确保帧格式与 Control 保存一致（默认 YUV420）。
- 可靠性：
- 对找不到特征的情况提供容错（如置中、减速、停车等）。
- 日志记录关键信息，便于定位问题。

---

## 附录：相关 API 参考

数据结构

- data.Picture
  - uid: int
  - frame: numpy.ndarray[uint8, ...] // 默认 YUV420
  - g: dict
  - data.Command

- data.Command
  - uid: int
  - target: MotorType // motor 或 servo
  - data: tuple[int, ...]
  - motor: (left_dir, left_speed, right_dir, right_speed)
    - dir: 0 前进，非 0 后退（建议 0/1）
    - speed: 0-180
  - servo: (channel, angle)
    - channel: 1-4
    - angle: 0-180
  - g: dict

- data.MotorType: Enum
  - motor = 1
  - servo = 2

BaseProcess 与控制流

- process.base.BaseConfig
  - name: str

- process.base.BaseProcess[T]
  - 属性
    - config: T
    - uid: int 只读
    - origin_frame: ndarray 只读
    - debug: bool
  - 方法
    - handle() -> Command 抽象，需实现
    - process(target: Picture) -> Command
      - 设置内部状态后调用 handle()
      - 将 uid、g 写回返回的 Command
    - debug_picture(description: str, frame: ndarray, colour: int)
    - read_debug() -> list[(description: str, frame: ndarray)]

- process.control.Control
  - __init__(config: ControlConfig)
  - process(picture: Picture) -> Command
    - 根据 ControlConfig.save_debug 与 interval 决定是否开启 debug
    - 保存调试图像到 ./debug/{uid}_{description}.jpg
  - reset_process() 依据 config.used 选择并实例化 Process
  - get_process_config() -> ProcessConfig
    - 属性 config 可读写（写入后会 reset_process）

---

## 小结

创建一个新的 Process 包含三步：

1) 新建 BaseProcess 子类与对应 BaseConfig，并实现 handle() 返回 Command。
2) 在 Control.PROCESS 中注册（类与配置类）。
3) 将 ControlConfig.used 指向新工作流名称，按需使用调试输出。
