# -*- coding:utf-8 -*-
# AUTHOR: Sun

from dataclasses import dataclass, field
from enum import Enum

from numpy import ndarray, uint8


class MotorType(Enum):
    """
    @brief 电机类型枚举
    @details 定义系统支持的电机类型，用于区分不同类型的电机控制命令
    """
    motor = 1  #: 驱动电机
    servo = 2  #: 舵机


@dataclass
class Picture(object):
    """
    @brief 图像数据类
    @details 用于存储从摄像头捕获的单帧图像及相关元数据
    """
    uid: int                    #: 帧唯一标识符
    frame: ndarray[uint8, ...]  #: 图像数据(numpy数组)
    g: dict = field(default_factory=dict)  #: 通用元数据字典


@dataclass
class Command(object):
    """
    @brief 控制命令数据类
    @details 用于封装发送给小车的各种控制指令
    """
    uid: int                 #: 帧对应命令的唯一标识符

    target: MotorType        #: 目标电机类型
    data: tuple[int, ...]    #: 控制数据元组

    g: dict = field(default_factory=dict)  #: 通用元数据字典


if __name__ == '__main__':
    pass