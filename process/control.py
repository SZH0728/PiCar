# -*- coding:utf-8 -*-
# AUTHOR: Sun

from typing import Type

from cv2 import cvtColor, COLOR_YUV2BGR_I420, imwrite

from process.base import BaseProcess, BaseConfig
from process.example import ExampleProcess, ExampleConfig
from config import ControlConfig, ProcessConfig
from data import Picture, Command

PROCESS: list[tuple[Type[BaseProcess], Type[BaseConfig]]] = [
    (ExampleProcess, ExampleConfig),
]


class Control(object):
    def __init__(self, config: ControlConfig):
        self._config = config

        self._process: BaseProcess | None = None

        self.process_object_map: dict[str, Type[BaseProcess]] = {}
        self.process_config_map: dict[str, BaseConfig] = {}

        for process, config in PROCESS:
            config = config()

            self.process_object_map[config.name] = process
            self.process_config_map[config.name] = config

        self.reset_process()

    def process(self, picture: Picture) -> Command:
        if not self._process:
            raise RuntimeError('No process')

        command: Command = self._process.process(picture)

        if self._config.save_debug and self._process.uid % self._config.interval == 0:
            for description, frame in self._process.read_debug():
                image = cvtColor(frame, COLOR_YUV2BGR_I420, frame)
                imwrite(f'./debug/{self._process.uid}_{description}.jpg', image)

        return command

    def reset_process(self):
        process_object: Type[BaseProcess] = self.process_object_map[self._config.used]
        process_config: BaseConfig = self.process_config_map[self._config.used]
        self._process = process_object(process_config)

    def get_process_config(self) -> ProcessConfig:
        return ProcessConfig(self.process_config_map)

    @property
    def config(self) -> ControlConfig:
        return self._config

    @config.setter
    def config(self, value: ControlConfig):
        self._config = value
        self.reset_process()

if __name__ == '__main__':
    pass
