# -*- coding:utf-8 -*-
# AUTHOR: Sun

from enum import Enum
from dataclasses import dataclass, field
from pickle import dumps, loads

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
    """
    @brief 控制配置数据类
    @details 存储控制模块相关的配置参数
    """
    used: str = 'example'   #: 使用的控制模块

    save_debug: bool = True  #: 是否保存调试信息
    interval: int = 30       #: 控制间隔时间(毫秒)


class ProcessConfig(object):
    """
    @brief 处理工作流配置管理类
    @details 管理不同处理工作流的配置映射，提供获取和设置配置的方法
    """
    __slots__ = ['_process_config_map']

    def __init__(self, process_config_map: dict[str, BaseConfig]):
        """
        @brief 初始化处理工作流配置管理器
        @param process_config_map 处理工作流配置映射字典
        """
        self._process_config_map = process_config_map

    def __getattr__(self, item):
        """
        @brief 通过属性方式获取处理工作流配置
        @param item 处理工作流名称
        @throws AttributeError 当指定的处理工作流配置不存在时抛出异常
        @return 对应的处理工作流配置
        """
        if item.startswith('_'):
            super().__getattribute__(item)
            return

        if item in self._process_config_map:
            return self._process_config_map[item]

        raise AttributeError(f"Process {item} config not found")

    def __getitem__(self, item):
        """
        @brief 通过索引方式获取处理工作流配置
        @param item 处理工作流名称
        @throws KeyError 当指定的处理工作流配置不存在时抛出异常
        @return 对应的处理工作流配置
        """
        if not item in self._process_config_map:
            raise KeyError(f"Process {item} config not found")

        return self._process_config_map[item]

    def __setattr__(self, key: str, value):
        """
        @brief 通过属性方式设置处理工作流配置
        @param key 处理工作流名称
        @param value 处理工作流配置值
        @throws AttributeError 当指定的处理工作流配置不存在时抛出异常
        """
        if key.startswith('_'):
            super().__setattr__(key, value)
            return

        if not key in self._process_config_map:
            raise AttributeError(f"Process {key} config not found")

        self._process_config_map[key] = value

    def __setitem__(self, key, value):
        """
        @brief 通过索引方式设置处理工作流配置
        @param key 处理工作流名称
        @param value 处理工作流配置值
        @throws KeyError 当指定的处理工作流配置不存在时抛出异常
        """
        if not key in self._process_config_map:
            raise KeyError(f"Process {key} config not found")

        self._process_config_map[key] = value

    def __str__(self):
        string: str = ''
        for key, value in self._process_config_map.items():
            string += f'{key}={value}, '

        return string[:-2]

    def __repr__(self):
        return f'Process({self.__str__()})'


@dataclass
class Config(object):
    """
    @brief 全局配置数据类
    @details 包含整个小车系统的各项配置参数
    """
    web: bool = True   #: 是否启用Web服务
    port: int = 8080   #: Web服务端口号

    camera: CameraConfig = field(default_factory=CameraConfig)  #: 摄像头配置
    motor: MotorConfig = field(default_factory=MotorConfig)     #: 电机配置
    control: ControlConfig = field(default_factory=ControlConfig)  #: 控制配置
    process: ProcessConfig | None = None                        #: 处理配置



def serialize(config: Config, file: str):
    """
    @brief 将配置数据序列化并保存到文件中

    @param config 配置数据
    @param file 文件路径
    """
    with open(file, 'wb') as f:
        f.write(dumps(config))

def deserialize(file: str) -> Config:
    """
    @brief 从文件中反序列化配置数据

    @param file 文件路径
    @return 配置数据
    """
    with open(file, 'rb') as f:
        return loads(f.read())

if __name__ == '__main__':
    pass