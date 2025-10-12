# -*- coding:utf-8 -*-
# AUTHOR: Sun

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from numpy import ndarray, uint8
from cv2 import COLOR_YUV2BGR_I420

from data import Picture, Command


T = TypeVar('T')

@dataclass
class BaseConfig(object):
    """
    @brief 处理工作流基础配置类
    @details 作为所有处理工作流配置类的基类，定义配置的基本结构
    """
    name: str         #: 配置名称

    angle: int = 120  #: 摄像头旋转角度


class BaseProcess(ABC, Generic[T]):
    """
    @brief 处理工作流基础抽象类
    @details 定义所有处理工作流的通用接口和基础功能，提供图像处理的标准框架
    """

    def __init__(self, config: T):
        """
        @brief 初始化处理工作流基础类
        
        @param config 处理工作流配置对象
        """
        self.g: dict = {}                                    #: 通用元数据字典
        self.config = config                                 #: 处理工作流配置

        self.__uid: int | None = None                        #: 当前帧唯一标识符
        self.__origin_frame: ndarray[uint8, ...] | None = None  #: 原始图像帧数据

        self.__debug: list[tuple[str, ndarray[uint8, ...], int]] = []  #: 调试图像列表
        self.debug: bool = False                             #: 调试模式开关

    @abstractmethod
    def handle(self) -> Command | tuple[Command]:
        """
        @brief 抽象处理方法
        @details 子类必须实现此方法，用于执行具体的图像处理逻辑并返回控制命令
        
        @return 处理结果命令
        """
        pass

    def process(self, target: Picture) -> tuple[Command]:
        """
        @brief 处理图像的主要入口方法
        @details 接收图像数据，调用handle方法进行处理，并返回相应的控制命令
        
        @param target 输入的图像数据
        @return 处理后的控制命令
        """
        self.__debug.clear()

        self.__uid = target.uid
        self.__origin_frame = target.frame

        self.g = target.g

        commands: Command | tuple[Command] = self.handle()

        if isinstance(commands, Command):
            commands: tuple[Command] = (commands,)

        for command in commands:
            command.uid = self.__uid
            command.g = self.g

        return commands

    def debug_picture(self, description: str, frame: ndarray[uint8, ...], colour: int = COLOR_YUV2BGR_I420):
        """
        @brief 添加调试图像
        @details 在调试模式下，将中间处理结果图像添加到调试列表中
        
        @param description 图像描述信息
        @param frame 图像帧数据
        @param colour 图像颜色
        """
        self.__debug.append((description, frame, colour))

    def read_debug(self) -> list[tuple[str, ndarray[uint8, ...], int]]:
        """
        @brief 读取调试图像列表
        @details 返回当前处理过程中生成的所有调试图像
        
        @return 调试图像列表，每个元素包含描述信息和图像数据
        """
        return self.__debug.copy()

    @property
    def origin_frame(self) -> ndarray[uint8, ...]:
        """
        @brief 获取原始图像帧数据
        @return 原始图像帧数据
        """
        return self.__origin_frame

    @property
    def uid(self) -> int:
        """
        @brief 获取当前帧唯一标识符
        @return 当前帧唯一标识符
        """
        return self.__uid

if __name__ == '__main__':
    pass