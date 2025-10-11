# -*- coding:utf-8 -*-
# AUTHOR: Sun
import cv2

from config import Config
from camera import CameraDriver
from handle import Handle

def main():
    config = Config()

    camera = CameraDriver(config.camera)
    handle = Handle(config.motor)


if __name__ == '__main__':
    main()
