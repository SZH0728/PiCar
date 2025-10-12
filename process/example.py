# -*- coding:utf-8 -*-
# AUTHOR: Sun
from dataclasses import dataclass
from logging import getLogger

from data import Command, MotorType
from process.base import BaseProcess, BaseConfig


logger = getLogger(__name__)

@dataclass
class ExampleConfig(BaseConfig):
    """
    @brief 示例处理工作流配置类
    @details 继承自BaseConfig，为示例处理工作流提供配置参数
    """
    name: str = 'example'          #: 处理工作流名称
    
    description: str = "Example process"  #: 处理工作流描述信息


class ExampleProcess(BaseProcess[ExampleConfig]):
    """
    @brief 示例处理工作流类
    @details 继承自BaseProcess，实现基本的图像处理逻辑，用于演示和测试
    """

    def handle(self) -> Command:
        """
        @brief 处理方法实现
        @details 执行示例图像处理逻辑，在调试模式下保存图像，并返回控制命令
        
        @return 控制命令对象
        """

        if self.debug:
            self.debug_picture('example', self.origin_frame)

        logger.info(f'Example process: {self.config.description}')

        return Command(
            uid=self.uid,
            target=MotorType.motor,
            data=(0, 80, 0, 80),
            g={}
        )

if __name__ == '__main__':
    pass