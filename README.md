# PiCar - Raspberry Pi 小车控制系统

PiCar 是一个基于 Raspberry Pi 的智能小车控制系统，具备计算机视觉处理能力，能够自主导航和避障。该项目利用摄像头捕捉图像，通过图像处理算法分析环境，并根据分析结果控制小车的运动。

## 功能特点

- **计算机视觉导航**：使用摄像头和图像处理算法实现道路跟踪
- **模块化设计**：采用插件式处理流程架构，易于扩展新的图像处理算法
- **Web 控制界面**：内置 Web 服务器，可通过浏览器远程监控和控制小车
- **实时控制**：基于形态学处理的道路识别和 PID 控制算法
- **灵活配置**：支持多种配置选项，可根据需要调整系统行为

## 系统架构

```
main.py (主程序入口)
├── camera.py (摄像头驱动)
├── process/
│   ├── control.py (处理流程管理)
│   ├── morphology.py (形态学处理算法)
│   ├── base.py (基础类)
│   └── example.py (示例处理流程)
├── handle.py (命令处理器)
├── motor.py (电机驱动)
├── config.py (配置管理)
├── data.py (数据结构)
├── web.py (Web 服务器)
└── console.py (控制台界面)
```

## 核心组件

### 图像处理流程

系统采用模块化的图像处理流程设计，目前实现了基于形态学的道路跟踪算法 ([morphology.py](process/morphology.py))：

1. **透视变换**：校正图像视角，获得鸟瞰图
2. **色彩空间转换**：将图像转换为灰度图或 HSV 色彩空间
3. **阈值处理**：使用 Otsu 算法或固定阈值进行二值化
4. **形态学操作**：通过开运算和闭运算去噪和填充
5. **重心计算**：计算道路区域的重心位置
6. **PID 控制**：根据重心偏差计算转向角度和速度

### 硬件控制

- **电机控制**：通过 I2C 接口控制小车的驱动电机和舵机
- **摄像头**：使用 Raspberry Pi Camera 模块捕获图像

### Web 界面

系统内置 Web 服务器，提供以下功能：
- 实时查看处理后的图像
- 远程控制小车
- 查看调试信息

## 安装与配置

### 硬件要求

- Raspberry Pi (推荐 4B 或更高版本)
- Raspberry Pi Camera Module
- 支持 I2C 通信的小车底盘
- 适当的动力电源

### 软件依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：
- picamera2 - Raspberry Pi 摄像头支持
- opencv-python - 图像处理
- numpy - 数值计算
- bottle - Web 框架
- waitress - WSGI 服务器
- smbus2 - I2C 通信

### 配置说明

系统配置在 [config.py](config.py) 中定义，主要包括：

- **CameraConfig** - 摄像头配置（分辨率、格式等）
- **MotorConfig** - 电机配置（I2C 地址、超时等）
- **ControlConfig** - 控制配置（处理流程选择、调试选项等）

## 使用方法

### 启动系统

```bash
python main.py
```

默认情况下，系统会在 8080 端口启动 Web 服务器。

### Web 界面操作

访问 `http://<树莓派IP>:8080` 可以打开 Web 控制界面：
- 查看实时处理图像
- 控制小车运动
- 调整系统参数

### 自定义图像处理流程

系统支持添加自定义的图像处理流程，详细请参考 [process/process.md](process/process.md)。

## 项目结构

```
.
├── main.py              # 主程序入口
├── config.py            # 系统配置
├── camera.py            # 摄像头驱动
├── motor.py             # 电机驱动
├── handle.py            # 命令处理
├── data.py              # 数据结构定义
├── web.py               # Web 服务器
├── console.py           # 控制台界面
├── bridge.py            # 数据桥接
├── process/             # 图像处理流程
│   ├── base.py          # 基础类
│   ├── control.py       # 流程管理器
│   ├── morphology.py    # 形态学处理（默认）
│   ├── example.py       # 示例流程
│   └── process.md       # 开发指南
└── debug/               # 调试图像存储目录
```

## 开发指南

要添加新的图像处理算法，请按照以下步骤操作：

1. 在 `process/` 目录下创建新的处理流程文件
2. 继承 `BaseProcess` 类并实现 `handle()` 方法
3. 创建对应的配置类继承 `BaseConfig`
4. 在 `control.py` 的 `PROCESS` 列表中注册新流程
5. 在配置中选择使用新的处理流程

详细开发指南请参考 [process/process.md](process/process.md)。
