# -*- coding:utf-8 -*-
# AUTHOR: Sun

from abc import ABC, abstractmethod
from typing import Type
from enum import Enum
from dataclasses import is_dataclass

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

        tokens: list[str] = [i for i in args.split(' ') if i]
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

    def return_warning(self, message: str):
        """
        @brief 添加警告消息

        @param message 警告消息内容
        """
        self.__client.put(f'warning:{message}')

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
            self.return_warning(f'too many arguments: {self.get_arg()}')

        if not self.get_arg():
            self.return_warning(f'no arguments was given')
            return

        if self.get_karg():
            self.return_warning(f'unknown arguments: {self.get_karg()}')

        arg = self.get_arg(0)
        tokens = arg.split('.')

        if tokens[0] == 'config':
            tokens = tokens[1:]

        current_config = self.config_object
        try:
            for token in tokens:
                current_config = getattr(current_config, token)
        except AttributeError:
            self.return_error(f'unknown config: {arg}')
            return

        self.return_message(f'{arg}: {current_config}')


class Set(Tool):
    """
    @brief 设置配置信息的工具类
    @details 实现设置系统配置信息的功能，继承自Tool基类
    """
    def __init__(self, client: Client, camera: CameraDriver, control: Control, handle: Handle, config: Config):
        """
        @brief 初始化Set工具实例
        
        @param client 桥接客户端对象
        @param camera 摄像头驱动对象
        @param control 控制对象
        @param handle 句柄对象
        @param config 配置对象
        """
        super().__init__(client, camera, control, handle, config)

        self.name = 'set'

    def handle(self):
        """
        @brief 处理设置配置命令
        @details 命令格式: set 配置地址 新配置数据
        """
        if len(self.get_arg()) < 2:
            self.return_warning(f'insufficient arguments: {self.get_arg()}')

        if len(self.get_arg()) > 2:
            self.return_warning(f'too many arguments: {self.get_arg()}')

        if self.get_karg():
            self.return_warning(f'unknown arguments: {self.get_karg()}')

        config_path = self.get_arg(0)
        new_value_str = self.get_arg(1)
        
        tokens = config_path.split('.')

        if tokens[0] == 'config':
            tokens = tokens[1:]

        # 获取要设置的配置项的父对象和属性名
        parent_config = self.config_object
        attr_name = tokens[-1]
        try:
            for token in tokens[:-1]:
                parent_config = getattr(parent_config, token)

            original_value = getattr(parent_config, attr_name)
        except AttributeError:
            self.return_error(f'unknown config: {config_path}')
            return

        # 转换新值为与原值相同的类型
        try:
            new_value = self._convert_value(new_value_str, original_value, attr_name)
        except Exception as e:
            self.return_error(f'failed to convert value: {str(e)}')
            return

        # 设置新值
        try:
            setattr(parent_config, attr_name, new_value)
            self.return_message(f'{config_path}: {original_value} -> {new_value}')
        except Exception as e:
            self.return_error(f'failed to set config: {str(e)}')

    @staticmethod
    def _convert_value(value_str: str, original_value, attr_name: str):
        """
        @brief 将字符串值转换为与原值相同类型的值
        
        @param value_str 字符串形式的值
        @param original_value 原始值，用于确定目标类型
        @param attr_name 属性名
        @return 转换后的值
        """
        # 如果原值是枚举类型
        if isinstance(original_value, Enum):
            enum_type = type(original_value)

            # 尝试按名称查找
            try:
                return enum_type[value_str]
            except KeyError:
                pass

            # 尝试按值查找
            try:
                # 对于整数值的枚举
                return enum_type(int(value_str))
            except (ValueError, KeyError):
                pass
            
            raise ValueError(f"Cannot convert '{value_str}' to enum {enum_type.__name__}")
        
        # 如果原值是布尔类型
        if isinstance(original_value, bool):
            if value_str.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value_str.lower() in ('false', '0', 'no', 'off'):
                return False
            else:
                raise ValueError(f"Cannot convert '{value_str}' to bool")
        
        # 如果原值是数据类实例
        if is_dataclass(original_value):
            raise ValueError(f"Cannot directly set complex dataclass object '{attr_name}'")
        
        if type(original_value) in (int, float, str):
            return type(original_value)(value_str)

        raise ValueError(f"Cannot convert '{value_str}' to {type(original_value).__name__}")


class Restart(Tool):
    """
    @brief 重启系统组件的工具类
    @details 实现重启摄像头、控制模块、句柄等系统组件的功能，继承自Tool基类
    """
    def __init__(self, client: Client, camera: CameraDriver, control: Control, handle: Handle, config: Config):
        """
        @brief 初始化Restart工具实例
        
        @param client 桥接客户端对象
        @param camera 摄像头驱动对象
        @param control 控制对象
        @param handle 句柄对象
        @param config 配置对象
        """
        super().__init__(client, camera, control, handle, config)

        self.name = 'restart'

    def handle(self):
        """
        @brief 处理重启命令
        @details 命令格式: restart [component]
                 可以指定组件: camera, control, handle
                 或者使用 restart all 重启所有组件
        """
        if len(self.get_arg()) != 1:
            self.return_warning(f'incorrect arguments number: {self.get_arg()}')

        if self.get_karg():
            self.return_warning(f'unknown arguments: {self.get_karg()}')

        # 重启指定组件
        component = self.get_arg(0)
        if component == 'camera':
            self._restart_camera()
        elif component == 'control':
            self._restart_control()
        elif component == 'handle':
            self._restart_handle()
        elif component == 'all':
            self._restart_all()
        else:
            self.return_error(f'unknown component: {component}')

    def _restart_all(self):
        """
        @brief 重启所有组件
        """
        try:
            self._restart_camera()
            self._restart_control()
            self._restart_handle()
            self.return_message('all components restarted')
        except Exception as e:
            self.return_error(f'failed to restart all components: {str(e)}')

    def _restart_camera(self):
        """
        @brief 重启摄像头组件
        """
        try:
            self.camera_object.restart_camera()
            self.return_message('camera restarted')
        except Exception as e:
            self.return_error(f'failed to restart camera: {str(e)}')

    def _restart_control(self):
        """
        @brief 重启控制组件
        """
        try:
            self.control_object.reset_process()
            self.return_message('control restarted')
        except Exception as e:
            self.return_error(f'failed to restart control: {str(e)}')

    def _restart_handle(self):
        """
        @brief 重启句柄组件
        """
        try:
            self.handle_object.restart_motor()
            self.return_message('handle restarted')
        except Exception as e:
            self.return_error(f'failed to restart handle: {str(e)}')


tools: list[Type[Tool]] = [Read, Set, Restart]


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