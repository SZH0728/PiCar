# -*- coding:utf-8 -*-
# AUTHOR: Sun

from pathlib import Path

from config import Config
from web import run_server, pi_client
from console import Console

from camera import CameraDriver
from handle import Handle
from process.control import Control

def main():
    debug_dir = Path('./debug')
    for item in debug_dir.iterdir():
        item.unlink()

    config = Config()

    if config.web:
        run_server(config.port)

    camera = CameraDriver(config.camera)
    control = Control(config.control)
    handle = Handle(config.motor)

    config.process = control.get_process_config()

    console = Console(pi_client, camera, control, handle, config)

    try:
        while True:
            picture = camera.get_frame()
            command = control.process(picture)
            # handle.handle_command(command)

            if config.web:
                console.process()

    except KeyboardInterrupt:
        camera.close()
        handle.close()

if __name__ == '__main__':
    main()