# -*- coding:utf-8 -*-
# AUTHOR: Sun

from abc import ABC, abstractmethod
from typing import Type

from bridge import Client
from config import Config

from camera import CameraDriver
from process.control import Control
from handle import Handle


class Tool(ABC):
    """
    @brief 控制台工具抽象基类
    @details 定义控制台工具的基本结构和功能，所有具体工具都需要继承此类
    """
    def __init__(self, client: Client, camera: CameraDriver, control: Control, handle: Handle, config: Config):
        """
        @brief 初始化Tool实例
        
        @param client 桥接客户端对象
        @param camera 摄像头驱动对象
        @param control 控制对象
        @param handle 句柄对象
        @param config 配置对象
        """
        self.name: str | None = None
        self.__client = client

        self.camera_object = camera
        self.control_object = control
        self.handle_object = handle
        self.config_object = config

        self.__args: list[str] = []
        self.__kargs: dict[str, str] = {}
        self.__flag: set[str] = set()

    def process(self, args: str):
        """
        @brief 处理命令参数并执行具体操作
        
        @param args 命令行参数字符串
        """
        self._clear_flags()
        self._analysis_arg(args)

        self.handle()

    def _clear_flags(self):
        """
        @brief 清除所有标志位和参数
        """
        self.__args.clear()
        self.__kargs.clear()
        self.__flag.clear()

    def _analysis_arg(self, args: str):
        """
        @brief 解析命令行参数
        
        @param args 命令行参数字符串
        """
        if not args:
            return

        tokens: list[str] = args.split(' ')
        index: int = 0

        while index < len(tokens):
            token = tokens[index]

            if token.startswith('--'):
                self.__flag.add(token[2:])
                index += 1
                continue

            if token.startswith('-'):
                self.__kargs[token[1:]] = tokens[index + 1]
                index += 2
                continue

            self.__args.append(token)
            index += 1

    def get_arg(self, index: int | None = None) -> str | None | list[str]:
        """
        @brief 获取位置参数
        
        @param index 参数索引，如果为None则返回所有参数
        @return 指定索引的参数值，如果索引超出范围则返回None，如果index为None则返回所有参数列表
        """
        if index is not None:
            if 0 <= index < len(self.__args):
                return self.__args[index]
            else:
                return None

        return self.__args

    def get_karg(self, key: str | None = None) -> str | None | dict[str, str]:
        """
        @brief 获取关键字参数
        
        @param key 关键字参数键名，如果为None则返回所有关键字参数
        @return 指定键的关键字参数值，如果键不存在则返回None，如果key为None则返回所有关键字参数字典
        """
        if key is not None:
            return self.__kargs.get(key, None)
        else:
            return self.__kargs

    def has_flag(self, flag: str) -> bool:
        """
        @brief 检查是否存在指定标志位
        
        @param flag 标志位名称
        @return 如果存在指定标志位则返回True，否则返回False
        """
        return flag in self.__flag

    def return_message(self, message: str):
        """
        @brief 添加返回消息
        
        @param message 要返回的消息内容
        """
        self.__client.put(f'info:{message}')

    def return_error(self, message: str):
        """
        @brief 添加错误消息
        
        @param message 错误消息内容
        """
        self.__client.put(f'error:{message}')

    @abstractmethod
    def handle(self):
        """
        @brief 抽象处理方法，由子类实现具体的处理逻辑
        """
        pass


class Read(Tool):
    """
    @brief 读取配置信息的工具类
    @details 实现读取系统配置信息的功能，继承自Tool基类
    """
    def __init__(self, client: Client, camera: CameraDriver, control: Control, handle: Handle, config: Config):
        """
        @brief 初始化Read工具实例
        
        @param client 桥接客户端对象
        @param camera 摄像头驱动对象
        @param control 控制对象
        @param handle 句柄对象
        @param config 配置对象
        """
        super().__init__(client, camera, control, handle, config)

        self.name = 'read'

    def handle(self):
        """
        @brief 处理读取配置命令
        """
        if len(self.get_arg()) > 1:
            self.return_error(f'too many arguments: {self.get_arg()}')

        if not self.get_arg():
            self.return_error(f'no arguments was given')
            return

        if self.get_karg():
            self.return_error(f'unknown arguments: {self.get_karg()}')

        arg = self.get_arg(0)
        tokens = arg.split('.')

        if tokens[0] == 'config':
            tokens = tokens[1:]

        current_config = self.config_object
        for token in tokens:
            try:
                current_config = getattr(current_config, token)
            except AttributeError:
                self.return_error(f'unknown config: {arg}')
                return

        self.return_message(f'{arg}: {current_config}')


tools: list[Type[Tool]] = [Read]


class Console(object):
    """
    @brief 控制台主类
    @details 负责解析和分发控制台命令到相应的工具处理器
    """
    def __init__(self, client: Client, camera: CameraDriver, control: Control, handle: Handle, config: Config):
        """
        @brief 初始化Console实例
        
        @param client 桥接客户端对象
        @param camera 摄像头驱动对象
        @param control 控制对象
        @param handle 句柄对象
        @param config 配置对象
        """
        self._client = client

        self._camera = camera
        self._control = control
        self._handle = handle

        self._config = config

        self._tools: dict[str, Tool] = {}
        for tool_object in tools:
            tool = tool_object(self._client, self._camera, self._control, self._handle, self._config)
            self._tools[tool.name] = tool

    def process(self):
        """
        @brief 处理控制台命令
        """
        while not self._client.receive_is_empty():
            command = self._client.get()

            if not command:
                continue

            self._client.put(f'command:>{command}')
            self.handle(command)

    def handle(self, command: str):
        """
        @brief 处理单个命令
        
        @param command 待处理的命令字符串
        """
        tool: str = command.split(' ')[0]
        args: str = command[len(tool) + 1:]

        if tool not in self._tools:
            self._client.put(f'error:unknown command: {tool}')
            return

        tool_target = self._tools[tool]
        tool_target.process(args)

if __name__ == '__main__':
    pass