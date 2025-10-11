# -*- coding:utf-8 -*-
# AUTHOR: Sun

from logging import getLogger
from time import sleep

from smbus2 import SMBus

logger = getLogger(__name__)


class CarI2CError(Exception):
    """
    @brief I2C 通讯相关异常。
    """
    pass


class CarProtocolError(ValueError):
    """
    @brief 参数越界或协议使用错误。
    """
    pass


class MotorDriver(object):
    """
    @brief 树莓派 I2C 小车驱动（单例）。
    @details 使用 python-smbus2 与底层单片机通讯，封装电机与舵机控制。
    """

    # 单例实例
    _instance = None

    # 协议寄存器
    REG_MOTOR = 0x01      #: 电机控制寄存器
    REG_STOP_ALL = 0x02   #: 停止所有电机寄存器
    REG_SERVO = 0x03      #: 舵机控制寄存器

    def __new__(cls, bus_id: int = 1, address: int = 0x16, timeout: float = 0.02):
        """
        @brief 创建MotorDriver类的单例实例

        @param bus_id I2C 总线号（树莓派通常为 1）
        @param address I2C 设备地址（根据实际硬件设置）
        @param timeout 写操作后最小等待时间（秒），避免过快重复写导致底层处理不过来
        @return MotorDriver类的实例
        """
        if cls._instance is None:
            cls._instance = super(MotorDriver, cls).__new__(cls)
        return cls._instance

    def __init__(self, bus_id: int = 1, address: int = 0x16, timeout: float = 0.02):
        """
        @brief 初始化MotorDriver实例

        @param bus_id I2C 总线号（树莓派通常为 1）
        @param address I2C 设备地址（根据实际硬件设置）
        @param timeout 写操作后最小等待时间（秒），避免过快重复写导致底层处理不过来
        """
        # 防止重复初始化
        if hasattr(self, '_initialized'):
            return
            
        self.address = address              #: I2C设备地址
        self.timeout = float(timeout)       #: 写操作超时时间

        self._bus = SMBus(bus_id)           #: I2C总线对象
        self._initialized = True            #: 初始化标记

    @staticmethod
    def _clamp(val: int, low: int, high: int) -> int:
        """
        @brief 将值限制在指定范围内

        @param val 需要限制的值
        @param low 最小值
        @param high 最大值
        @return 限制在范围内的值
        """
        return max(low, min(high, int(val)))

    def _write_block(self, register: int, data_bytes: list[int]) -> None:
        """
        @brief 统一写入方法。根据协议，写寄存器 + 最多 4 个数据字节。

        @param register 寄存器地址
        @param data_bytes 要写入的数据字节列表
        """
        if not (0x00 <= register <= 0xFF):
            raise CarProtocolError(f"寄存器无效: 0x{register:02X}")

        try:
            self._bus.write_i2c_block_data(self.address, register, data_bytes)
            if self.timeout > 0:
                sleep(self.timeout)
        except OSError as e:
            raise CarI2CError(f"I2C write failed: addr=0x{self.address:02X}, reg=0x{register:02X}, data={data_bytes}, err={e}") from e

    def stop_all(self) -> None:
        """
        @brief 停止所有电机（寄存器 0x02，发送 0x00）
        """
        self._write_block(self.REG_STOP_ALL, [0x00])

    def set_motors(self, left_dir: int, left_speed: int, right_dir: int, right_speed: int) -> None:
        """
        @brief 控制小车运动状态（寄存器 0x01）

        @param left_dir 左电机方向：0 为前进，非 0 为后退（建议 0/1）
        @param left_speed 左电机速度：0-180
        @param right_dir 右电机方向：0 为前进，非 0 为后退（建议 0/1）
        @param right_speed 右电机速度：0-180
        """
        left_direction = 0 if int(left_dir) == 0 else 1
        right_direction = 0 if int(right_dir) == 0 else 1

        ls = self._clamp(left_speed, 0, 180)
        rs = self._clamp(right_speed, 0, 180)

        logger.debug(f"Motor: left_dir={left_direction}, left_speed={ls}, right_dir={right_direction}, right_speed={rs}")

        self._write_block(self.REG_MOTOR, [left_direction, ls, right_direction, rs])

    def set_servo(self, channel: int, angle: int) -> None:
        """
        @brief 控制舵机（寄存器 0x03）

        @param channel 舵机通道: 1-4
        @param angle 舵机角度: 0-180
        """
        ch = int(channel)

        if ch < 1 or ch > 4:
            raise CarProtocolError("Servo channel should be between 1 and 4")

        ang = self._clamp(angle, 0, 180)

        logger.debug(f"Servo: channel={ch}, angle={ang}")

        self._write_block(self.REG_SERVO, [ch, ang])

    def forward(self, speed: int) -> None:
        """
        @brief 控制小车向前运动

        @param speed 小车前进速度: 0-180
        """
        s = self._clamp(speed, 0, 180)
        self.set_motors(0, s, 0, s)

    def backward(self, speed: int) -> None:
        """
        @brief 控制小车向后运动

        @param speed 小车后退速度: 0-180
        """
        s = self._clamp(speed, 0, 180)
        self.set_motors(1, s, 1, s)

    def close(self) -> None:
        """
        @brief 关闭I2C总线连接
        """
        try:
            if self._bus is not None:
                self._bus.close()
        finally:
            self._bus = None

    def __del__(self):
        """
        @brief 析构函数，确保正确关闭I2C连接
        """
        try:
            self.close()
        except Exception:
            pass


if __name__ == "__main__":
    motor = MotorDriver()
    motor.stop_all()
    motor.close()
