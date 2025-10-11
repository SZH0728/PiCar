# -*- coding:utf-8 -*-
# AUTHOR: Sun
from dataclasses import dataclass
from logging import getLogger

from data import Command, MotorType
from process.base import BaseProcess, BaseConfig


logger = getLogger(__name__)

@dataclass
class ExampleConfig(BaseConfig):
    name: str = 'example'

    description: str = "Example process"


class ExampleProcess(BaseProcess[ExampleConfig]):
    def handle(self) -> Command:

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