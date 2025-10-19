# -*- coding:utf-8 -*-
# AUTHOR: Sun

import logging
from pathlib import Path
from os.path import exists

from config import Config, serialize, deserialize
from data import Command, MotorType
from web import run_server, pi_client
from console import Console

from camera import CameraDriver
from handle import Handle
from process.control import Control

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(funcName)s(): %(message)s')

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)

logging.basicConfig(handlers=[console], level=logging.INFO)
logger = logging.getLogger(__name__)

logging.getLogger('picamera2').setLevel(logging.WARNING)

ENABLE_CONFIG_FILE = False
CONFIG_FILE = './config.byte'

def main():
    logger.info("Starting PiCar system")
    debug_dir = Path('./debug')
    for item in debug_dir.iterdir():
        item.unlink()

    if ENABLE_CONFIG_FILE and exists(CONFIG_FILE):
        config = deserialize(CONFIG_FILE)
        logger.info("Configuration loaded from file")
    else:
        config = Config()
        logger.info("Default configuration created")

    if config.web:
        logger.info(f"Starting web server on port {config.port}")
        run_server(config.port)

    camera = CameraDriver(config.camera)
    control = Control(config.control)
    handle = Handle(config.motor)

    config.process = control.get_process_config()

    console_object = Console(pi_client, camera, control, handle, config)

    try:
        logger.info("Entering main loop")
        while True:
            picture = camera.get_frame()
            commands = control.process(picture)

            if not config.pause:
                for command in commands:
                    handle.handle_command(command)
            else:
                command = Command(0, MotorType.motor, (0, 0, 0, 0))
                handle.handle_command(command)

            if config.web:
                console_object.process()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        raise

    finally:
        command = Command(0, MotorType.motor, (0, 0, 0, 0))
        handle.handle_command(command)

        camera.close()
        handle.close()

        if ENABLE_CONFIG_FILE:
            serialize(config, CONFIG_FILE)
            logger.info("Configuration saved to file")

if __name__ == '__main__':
    main()