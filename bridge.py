# -*- coding:utf-8 -*-
# AUTHOR: Sun

from queue import Queue, Empty, Full
from logging import getLogger

logger = getLogger(__name__)


class Bridge(object):
    """
    @brief 队列桥接类
    @details 创建一个连接两个客户端的双向通信桥接，使用泛型支持不同类型的数据传输
    """
    def __init__(self):
        """
        @brief 初始化桥接对象
        @details 创建两个异步队列用于双向通信，并初始化两个客户端
        """
        self._channel_A_to_B: Queue[str | None] = Queue()
        self._channel_B_to_A: Queue[str | None] = Queue()

        self.A = Client(self._channel_A_to_B, self._channel_B_to_A)
        self.B = Client(self._channel_B_to_A, self._channel_A_to_B)


class Client(object):
    """
    @brief 客户端通信类
    @details 提供向通道发送数据和从通道接收数据的方法
    """
    def __init__(self, send_channel: Queue[str | None], receive_channel: Queue[str | None]):
        """
        @brief 初始化客户端
        @param send_channel 发送数据的通道
        @param receive_channel 接收数据的通道
        """
        self._send_channel = send_channel
        self._receive_channel = receive_channel

    def put(self, msg: str) -> bool:
        """
        @brief 立即发送消息
        @details 尝试立即将消息放入发送队列，如果队列已满或已关闭则返回False
        @param msg 要发送的消息
        @return 发送成功返回True，失败返回False
        """
        try:
            self._send_channel.put_nowait(msg)
        except Full:
            return False

        return True

    def get(self) -> str | None:
        """
        @brief 立即获取消息
        @details 尝试立即从接收队列获取消息，如果队列为空或已关闭则返回None
        @return 成功获取消息则返回消息内容，否则返回None
        """
        try:
            return self._receive_channel.get_nowait()
        except Empty:
            return None

    def receive_is_empty(self) -> bool:
        """
        @brief 检查接收队列是否为空
        @return 接收队列为空返回True，否则返回False
        """
        return self._receive_channel.empty()

    def receive_is_full(self) -> bool:
        """
        @brief 检查接收队列是否已满
        @return 接收队列已满返回True，否则返回False
        """
        return self._receive_channel.full()

    def send_is_empty(self) -> bool:
        """
        @brief 检查发送队列是否为空
        @return 发送队列为空返回True，否则返回False
        """
        return self._send_channel.empty()

    def send_is_full(self) -> bool:
        """
        @brief 检查发送队列是否已满
        @return 发送队列已满返回True，否则返回False
        """
        return self._send_channel.full()


if __name__ == '__main__':
    pass