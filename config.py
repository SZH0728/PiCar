# -*- coding:utf-8 -*-
# AUTHOR: Sun

from dataclasses import dataclass, field
from enum import Enum

from process.base import BaseConfig


class BaseCameraConfigType(Enum):
    """
    @brief 摄像头基本配置类型枚举
    @details 定义Picamera2支持的不同摄像头配置类型
    """
    PreviewConfiguration = 1  #: 预览配置
    StillConfiguration = 2    #: 静态图像配置
    VideoConfiguration = 3    #: 视频流配置


@dataclass
class CameraConfig(object):
    """
    @brief 摄像头配置数据类
    @details 存储摄像头相关的所有配置参数
    """
    base_config_type: BaseCameraConfigType = BaseCameraConfigType.VideoConfiguration  #: 基本配置类型
    size: tuple[int, int] = (640, 360)  #: 图像尺寸(宽度,高度)
    format: str = 'YUV420'              #: 图像格式

    reverse: bool = True                #: 图像翻转

    fix_AE_AWB: bool = True             #: 是否固定自动曝光和白平衡
    fix_wait_time: float = 0.5          #: 自动曝光和白平衡固定前的等待时间(秒)


@dataclass
class MotorConfig(object):
    """
    @brief 电机配置数据类
    @details 存储电机驱动相关的所有配置参数
    """
    bus_id: int = 1      #: I2C总线编号
    address: int = 0x16  #: I2C设备地址
    timeout: float = 0.02  #: I2C通信超时时间(秒)


@dataclass
class ControlConfig(object):
    used: str = 'example'

    save_debug: bool = True
    interval: int = 30


class ProcessConfig(object):
    __slots__ = ['_process_config_map']

    def __init__(self, process_config_map: dict[str, BaseConfig]):
        self._process_config_map = process_config_map

    def __getattr__(self, item):
        if item in self._process_config_map:
            return self._process_config_map[item]

        raise AttributeError(f"Process {item} config not found")

    def __getitem__(self, item):
        if not item in self._process_config_map:
            raise KeyError(f"Process {item} config not found")

        return self._process_config_map[item]

    def __setattr__(self, key: str, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
            return

        if not key in self._process_config_map:
            raise AttributeError(f"Process {key} config not found")

        self._process_config_map[key] = value

    def __setitem__(self, key, value):
        if not key in self._process_config_map:
            raise KeyError(f"Process {key} config not found")

        self._process_config_map[key] = value


@dataclass
class Config(object):
    """
    @brief 全局配置数据类
    @details 包含整个小车系统的各项配置参数
    """
    camera: CameraConfig = field(default_factory=CameraConfig)  #: 摄像头配置
    motor: MotorConfig = field(default_factory=MotorConfig)     #: 电机配置
    control: ControlConfig = field(default_factory=ControlConfig)
    process: ProcessConfig | None = None

if __name__ == '__main__':
    pass