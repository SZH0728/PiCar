# -*- coding:utf-8 -*-
# AUTHOR: Sun

from logging import getLogger
from time import sleep

from picamera2 import Picamera2
from libcamera import Transform

from config import CameraConfig, BaseCameraConfigType
from data import Picture

logger = getLogger(__name__)


class CameraDriver(object):
    """
    @brief 树莓派摄像头驱动类
    @details 提供对树莓派摄像头模块的控制接口，基于Picamera2库实现，
             支持摄像头配置、初始化和图像捕获功能。
    """

    def __init__(self, config: CameraConfig):
        """
        @brief 使用指定配置初始化摄像头驱动
        
        @param config 摄像头配置参数
        """
        self._config = config
        self._frame_id: int = -1
        self.camera: None | Picamera2 = None
        self.restart_camera()

    def restart_camera(self):
        """
        @brief 使用当前配置重启摄像头
        
        该方法负责初始化或重新初始化摄像头，包括关闭现有连接、
        配置摄像头参数以及启动摄像头等操作。
        """
        if self.camera:
            self.camera.close()

        self.camera = Picamera2()
        main_config = {
            'size': self.config.size,
            'format': self.config.format,
        }

        camera_config = self._create_camera_configuration(main_config)

        if self._config.reverse:
            camera_config['transform'] = Transform(hflip=1, vflip=1)

        self.camera.configure(camera_config)
        self.camera.start()

        if self._config.fix_AE_AWB:
            self._fix_auto_exposure_and_white_balance()

    def _create_camera_configuration(self, main_config: dict) -> dict:
        """
        @brief 根据基础配置类型创建摄像头配置
        
        @param main_config 主要配置参数（尺寸、格式）
        @return 摄像头配置对象
        @throws ValueError 当提供无效的BaseCameraConfigType时抛出
        """
        if self._config.base_config_type == BaseCameraConfigType.PreviewConfiguration:
            return self.camera.create_preview_configuration(main_config)
        elif self._config.base_config_type == BaseCameraConfigType.StillConfiguration:
            return self.camera.create_still_configuration(main_config)
        elif self._config.base_config_type == BaseCameraConfigType.VideoConfiguration:
            return self.camera.create_video_configuration(main_config)
        else:
            raise ValueError(f'Invalid BaseCameraConfigType: {self._config.base_config_type}')

    def _fix_auto_exposure_and_white_balance(self):
        """
        @brief 固定自动曝光和白平衡设置
        
        该方法捕获摄像头的元数据，并使用这些数据来固定曝光和白平衡设置，
        禁用自动调整功能以确保图像参数的一致性。
        """
        sleep(self._config.fix_wait_time)

        meta_data: dict = self.camera.capture_metadata()
        self.camera.set_controls({
            "AeEnable": False,
            "AwbEnable": False,
            "ExposureTime": meta_data.get("ExposureTime", 5000),  # 曝光
            "AnalogueGain": meta_data.get("AnalogueGain", 1.0),  # 增益
        })

    def get_frame(self) -> Picture:
        """
        @brief 从摄像头捕获一帧图像
        
        @return 包含捕获图像的Picture对象
        """
        self._frame_id += 1

        logger.debug(f'Capture frame {self._frame_id}')

        return Picture(
            uid=self._frame_id,
            frame=self.camera.capture_array(),
            g={}
        )

    def close(self):
        """
        @brief 关闭摄像头连接
        """
        self.camera.close()

    @property
    def config(self) -> CameraConfig:
        """
        @brief 获取当前摄像头配置
        
        @return 当前摄像头配置
        """
        return self._config

    @config.setter
    def config(self, value: CameraConfig):
        """
        @brief 设置新的摄像头配置
        
        @param value 新的摄像头配置
        """
        self._config = value
        self.camera = None


if __name__ == '__main__':
    pass