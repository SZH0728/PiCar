# -*- coding:utf-8 -*-
# AUTHOR: Sun

from typing import Type

from cv2 import cvtColor, imwrite

from process.base import BaseProcess, BaseConfig
from process.example import ExampleProcess, ExampleConfig
from config import ControlConfig, ProcessConfig
from data import Picture, Command

"""处理工作流注册列表: 包含所有可用的处理工作流及其配置类型"""
PROCESS: list[tuple[Type[BaseProcess], Type[BaseConfig]]] = [
    (ExampleProcess, ExampleConfig),
]


class Control(object):
    """
    @brief 控制管理器类
    @details 管理图像处理工作流的注册、配置和执行，负责协调整个图像处理流程
    """

    def __init__(self, config: ControlConfig):
        """
        @brief 初始化控制管理器
        
        @param config 控制配置对象
        """
        self._config = config                      #: 控制配置

        self._process: BaseProcess | None = None   #: 当前处理工作流实例

        self.process_object_map: dict[str, Type[BaseProcess]] = {}  #: 处理工作流类映射
        self.process_config_map: dict[str, BaseConfig] = {}         #: 处理工作流配置映射

        for process, config in PROCESS:
            config = config()

            self.process_object_map[config.name] = process
            self.process_config_map[config.name] = config

        self.reset_process()

    def process(self, picture: Picture) -> Command:
        """
        @brief 处理图像并生成控制命令
        @details 对输入图像执行当前选择的处理工作流，并根据配置保存调试信息
        
        @param picture 输入的图像数据
        @return 生成的控制命令
        @throws RuntimeError 当没有可用的处理工作流时抛出异常
        """
        if not self._process:
            raise RuntimeError('No process')

        if self._config.save_debug and picture.uid % self._config.interval == 0:
            self._process.debug = True
        else:
            self._process.debug = False

        command: Command = self._process.process(picture)

        # 保存调试图像
        for description, frame, colour in self._process.read_debug():
            image = cvtColor(frame, colour, frame)
            imwrite(f'./debug/{self._process.uid}_{description}.jpg', image)

        return command

    def reset_process(self):
        """
        @brief 重置当前处理工作流
        @details 根据配置中的使用标识符重新初始化对应的处理工作流实例
        """
        process_object: Type[BaseProcess] = self.process_object_map[self._config.used]
        process_config: BaseConfig = self.process_config_map[self._config.used]
        self._process = process_object(process_config)

    def get_process_config(self) -> ProcessConfig:
        """
        @brief 获取处理工作流配置管理器
        @return 处理工作流配置管理器实例
        """
        return ProcessConfig(self.process_config_map)

    @property
    def config(self) -> ControlConfig:
        """
        @brief 获取当前控制配置
        @return 当前控制配置对象
        """
        return self._config

    @config.setter
    def config(self, value: ControlConfig):
        """
        @brief 设置新的控制配置
        @details 更新控制配置并重置处理工作流以应用新配置
        
        @param value 新的控制配置对象
        """
        self._config = value
        self.reset_process()

if __name__ == '__main__':
    pass