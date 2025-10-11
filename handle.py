# -*- coding:utf-8 -*-
# AUTHOR: Sun

from logging import getLogger

from config import MotorConfig
from data import Command, MotorType
from motor import MotorDriver

logger = getLogger(__name__)


class Handle(object):
    """
    @brief 小车控制句柄类
    @details 负责处理来自外部的命令并控制电机驱动器执行相应的动作
    """
    
    def __init__(self, config: MotorConfig):
        """
        @brief 初始化Handle实例
        
        @param config 电机配置对象
        """
        self._config = config

        self.motor: None | MotorDriver = None
        self.restart_motor()

    def restart_motor(self):
        """
        @brief 重启电机驱动
        @details 如果电机驱动已存在，则先关闭它，然后创建新的电机驱动实例
        """
        if self.motor:
            self.motor.close()

        self.motor = MotorDriver(bus_id=self._config.bus_id, address=self._config.address, timeout=self._config.timeout)

    def handle_command(self, command: Command):
        """
        @brief 处理传入的命令
        
        @param command 需要处理的命令对象
        @throws ValueError 当电机命令数据长度不为4或舵机命令数据长度不为2时抛出异常
        """
        if command.target == MotorType.motor:
            if len(command.data) != 4:
                raise ValueError("Motor command data length must be 4")

            logger.info(f"Motor command: {command.data}")

            self.motor.set_motors(*command.data)
        elif command.target == MotorType.servo:
            if len(command.data) != 2:
                raise ValueError("Servo command data length must be 2")

            logger.info(f"Servo command: {command.data}")

            self.motor.set_servo(*command.data)

    def close(self):
        """
        @brief 关闭Handle实例
        """
        self.motor.close()

    @property
    def config(self) -> MotorConfig:
        """
        @brief 获取当前配置
        
        @return 当前使用的电机配置对象
        """
        return self._config

    @config.setter
    def config(self, value: MotorConfig):
        """
        @brief 设置新的配置并重启电机
        
        @param value 新的电机配置对象
        """
        self._config = value
        self.restart_motor()

if __name__ == '__main__':
    pass