# -*- coding:utf-8 -*-
# AUTHOR: Sun
import cv2

from config import Config
from camera import CameraDriver
from handle import Handle
from process.control import Control

def main():
    config = Config()

    camera = CameraDriver(config.camera)
    handle = Handle(config.motor)
    control = Control(config.control)

    config.process = control.get_process_config()

    try:
        while True:
            picture = camera.get_frame()
            command = control.process(picture)
            # handle.handle_command(command)
    except KeyboardInterrupt:
        camera.close()
        handle.close()

if __name__ == '__main__':
    main()
