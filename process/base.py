# -*- coding:utf-8 -*-
# AUTHOR: Sun

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from numpy import ndarray, uint8

from data import Picture, Command


T = TypeVar('T')

@dataclass
class BaseConfig(object):
    name: str


class BaseProcess(ABC, Generic[T]):
    def __init__(self, config: T):
        self.g: dict = {}
        self.config = config

        self.__uid: int | None = None
        self.__origin_frame: ndarray[uint8, ...] | None = None

        self.__debug: list[tuple[str, ndarray[uint8, ...]]] = []
        self.debug: bool = False

    @abstractmethod
    def handle(self) -> Command:
        pass

    def process(self, target: Picture) -> Command:
        self.__debug.clear()

        self.__uid = target.uid
        self.__origin_frame = target.frame

        self.g = target.g

        command = self.handle()

        command.uid = self.__uid
        command.g = self.g

        return command

    def debug_picture(self, description: str, frame: ndarray[uint8, ...]):
        self.__debug.append((description, frame))

    def read_debug(self) -> list[tuple[str, ndarray[uint8, ...]]]:
        return self.__debug.copy()

    @property
    def origin_frame(self) -> ndarray[uint8, ...]:
        return self.__origin_frame

    @property
    def uid(self) -> int:
        return self.__uid

if __name__ == '__main__':
    pass