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
    def __init__(self, client: Client, camera: CameraDriver, control: Control, handle: Handle, config: Config):
        self.name: str | None = None
        self.__client = client

        self.camera_object = camera
        self.control_object = control
        self.handle_object = handle
        self.config_object = config

        self.__messages: list[str] = []

        self.__args: list[str] = []
        self.__kargs: dict[str, str] = {}
        self.__flag: set[str] = set()

    def process(self, args: str):
        self._clear_flags()
        self._analysis_arg(args)

        self.handle()

        for message in self.__messages:
            self.__client.put(message)

    def _clear_flags(self):
        self.__args.clear()
        self.__kargs.clear()
        self.__flag.clear()
        self.__messages.clear()

    def _analysis_arg(self, args: str):
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
        if index is not None:
            if 0 <= index < len(self.__args):
                return self.__args[index]
            else:
                return None

        return self.__args

    def get_karg(self, key: str | None = None) -> str | None | dict[str, str]:
        if key is not None:
            return self.__kargs.get(key, None)
        else:
            return self.__kargs

    def has_flag(self, flag: str) -> bool:
        return flag in self.__flag

    def return_message(self, message: str):
        self.__messages.append(f'info:{message}')

    def return_error(self, message: str):
        self.__messages.append(f'error:{message}')

    @abstractmethod
    def handle(self):
        pass


class Read(Tool):
    def __init__(self, client: Client, camera: CameraDriver, control: Control, handle: Handle, config: Config):
        super().__init__(client, camera, control, handle, config)

        self.name = 'read'

    def handle(self):
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
    def __init__(self, client: Client, camera: CameraDriver, control: Control, handle: Handle, config: Config):
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
        while not self._client.receive_is_empty():
            command = self._client.get()

            if not command:
                continue

            self._client.put(f'command:>{command}')
            self.handle(command)

    def handle(self, command: str):
        tool: str = command.split(' ')[0]
        args: str = command[len(tool) + 1:]

        if tool not in self._tools:
            self._client.put(f'error:unknown command: {tool}')
            return

        tool_target = self._tools[tool]
        tool_target.process(args)

if __name__ == '__main__':
    pass
