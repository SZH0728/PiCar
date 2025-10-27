# -*- coding:utf-8 -*-
# AUTHOR: Sun

from dataclasses import dataclass
from logging import getLogger
from enum import Enum
from time import time

import cv2
from numpy import float32

from data import Command, MotorType
from process.base import BaseProcess, BaseConfig

logger = getLogger(__name__)


class ColourType(Enum):
    """
    @brief 颜色空间类型枚举
    @details 定义图像处理中使用的颜色空间类型
    """
    GREY = 1  #: 灰度图
    HSV = 2   #: HSV色彩空间


@dataclass
class MorphologyConfig(BaseConfig):
    """
    @brief 形态学处理配置类
    @details 存储形态学图像处理过程所需的所有配置参数
    """
    name: str = 'morphology'           #: 配置名称
    angle: int = 165                   #: 摄像头旋转角度

    offset: int = 40                   #: 图像左右偏移量，用于裁剪图像边缘减少畸变影响

    roi_area: float = 0.4              #: ROI(感兴趣区域)占 전체图像的比例
    colour_type: ColourType = ColourType.GREY  #: 颜色空间类型

    otsu: bool = True                  #: 是否使用Otsu自动阈值算法
    threshold: int = 150               #: 固定阈值，当otsu=False时使用

    kernel_size: int = 5               #: 形态学操作的核函数大小
    open_iterations: int = 1           #: 开运算迭代次数
    close_iterations: int = 1          #: 闭运算迭代次数

    min_size_percent: float = 0.01     #: 最小区域百分比，用于过滤过小的区域

    Kp: float = 0.8                    #: PID控制器比例系数
    Ki: float = 0.0                    #: PID控制器积分系数
    Kd: float = 0.05                   #: PID控制器微分系数

    turn_gain: float = 1            #: 转向增益，影响左右轮速度差异程度


class MorphologyProcess(BaseProcess[MorphologyConfig]):
    """
    @brief 形态学图像处理类
    @details 基于形态学操作的道路识别算法，通过对图像进行透视变换、阈值处理、形态学操作等步骤，
             提取道路特征并计算小车控制指令
    """

    def __init__(self, config: MorphologyConfig):
        """
        @brief 初始化形态学处理实例
        @param config 形态学处理配置对象
        """
        super(MorphologyProcess, self).__init__(config)

        self.matrix: cv2.Mat | None = None  #: 透视变换矩阵

        self.last_x_line: float = 0.0       #: 上一次检测到的重心x坐标
        self.last_error: float = 0.0        #: 上一次的误差值
        self.last_time: float = 0.0         #: 上一次处理的时间戳

        self.sum_error: float = 0.0         #: 误差累积值，用于PID控制器的积分项

    def handle(self) -> Command | tuple[Command]:
        """
        @brief 执行形态学图像处理并计算小车控制指令
        @details 该方法通过透视变换、阈值处理、形态学操作等步骤提取道路特征，
                 并基于提取的道路中心线计算转向误差，最终输出电机控制指令
        
        @return Command 控制命令对象
        """
        # 如果是第一次执行，则记录初始时间
        if not self.last_time:
            self.last_time = time()

        # 获取原始图像的高度和宽度
        height, width = self.origin_frame.shape[:2]
        
        # 计算感兴趣区域(ROI)的高度，并截取图像下半部分作为ROI
        roi_height = int(height * self.config.roi_area)
        roi = self.origin_frame[height - roi_height:, 0:width]

        # 如果透视变换矩阵未初始化，则创建透视变换矩阵
        if self.matrix is None:
            self.initialize_perspective_transform(width, roi_height)

        # 对ROI区域进行透视变换校正
        roi = cv2.warpPerspective(roi, self.matrix, (width, roi_height))
        
        # 根据偏移量裁剪图像左右边缘，减小畸变影响
        roi = roi[:, self.config.offset:width - self.config.offset]
        width = width - self.config.offset * 2

        # 如果处于调试模式，保存ROI图像用于调试
        if self.debug:
            self.debug_picture('1_roi', roi)

        # 色彩空间转换
        colour_picture = self.convert_color_space(roi)

        # 如果处于调试模式，保存色彩转换后的图像用于调试
        if self.debug:
            self.debug_picture('2_colour', colour_picture)

        # 阈值处理
        binary = self.apply_threshold(colour_picture)

        # 如果处于调试模式，保存二值化图像用于调试
        if self.debug:
            self.debug_picture('3_binary', binary)

        # 对二值图像取反，使目标区域变为白色
        binary = cv2.bitwise_not(binary)

        # 形态学操作处理
        binary = self.apply_morphology_operations(binary)

        # 如果处于调试模式，保存形态学处理后的图像用于调试
        if self.debug:
            self.debug_picture('4_morphology', binary)

        # 计算重心位置
        x_line = self.calculate_centroid(binary, width)

        # 计算误差值：(重心x坐标 - 图像中心x坐标) / (图像中心x坐标)
        # 归一化误差值到[-1, 1]区间
        error = (x_line - width / 2) / (width / 2)

        # 计算转向值和速度
        steer, v_left, v_right = self.calculate_control_values(error)

        # 如果处于调试模式，绘制可视化结果
        if self.debug:
            visual = self.create_visualization(binary, width, x_line)
            self.debug_picture(f'5_visual_{steer}_{v_left}_{v_right}', visual)

        # 创建控制命令对象
        command = Command(self.uid, MotorType.motor, (0, v_left, 0, v_right), self.g)
        # command = Command(self.uid, MotorType.motor, (0, 0, 0, 0), self.g)
        return command

    def initialize_perspective_transform(self, width: int, roi_height: int) -> None:
        """
        @brief 初始化透视变换矩阵
        @details 根据配置参数计算透视变换矩阵，用于后续的透视变换校正
        
        @param width 图像宽度
        @param roi_height 感兴趣区域高度
        """
        # 定义目标点坐标（梯形区域）
        dst_points = float32([
            [0, 0],  # 左上
            [width, 0],  # 右上
            [width - self.config.offset, roi_height],  # 右下
            [self.config.offset, roi_height]  # 左下
        ])

        # 定义源点坐标（矩形区域）
        src_points = float32([
            [0, 0],  # 左上
            [width, 0],  # 右上
            [width, roi_height],  # 右下
            [0, roi_height]  # 左下
        ])

        # 计算透视变换矩阵
        self.matrix = cv2.getPerspectiveTransform(src_points, dst_points)

    def convert_color_space(self, roi: cv2.Mat) -> cv2.Mat:
        """
        @brief 色彩空间转换
        @details 根据配置选择色彩空间转换方式，将ROI区域转换为指定色彩空间
        
        @param roi 感兴趣区域图像
        @return 转换后的图像
        @throws ValueError 当配置的色彩类型无效时抛出异常
        """
        if self.config.colour_type == ColourType.GREY:
            # 转换为灰度图
            return cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        elif self.config.colour_type == ColourType.HSV:
            # 转换为HSV色彩空间
            return cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        else:
            raise ValueError('Invalid colour type')

    def apply_threshold(self, colour_picture: cv2.Mat) -> cv2.Mat:
        """
        @brief 应用阈值处理
        @details 根据配置选择阈值处理方式，将彩色图像转换为二值图像
        
        @param colour_picture 彩色图像
        @return 二值化处理后的图像
        """
        if self.config.otsu:
            # 使用Otsu自动阈值算法进行二值化处理
            _, binary = cv2.threshold(colour_picture, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            # 使用固定阈值进行二值化处理
            _, binary = cv2.threshold(colour_picture, self.config.threshold, 255, cv2.THRESH_BINARY)
        return binary

    def apply_morphology_operations(self, binary: cv2.Mat) -> cv2.Mat:
        """
        @brief 应用形态学操作
        @details 对二值图像先进行闭运算填充空洞，再进行开运算去除噪声
        
        @param binary 二值图像
        @return 形态学处理后的图像
        """
        # 创建形态学操作的核函数
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (self.config.kernel_size, self.config.kernel_size))
        
        # 先进行闭运算填充空洞，再进行开运算去除噪声
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=self.config.close_iterations)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=self.config.open_iterations)
        return binary

    def calculate_centroid(self, binary: cv2.Mat, width: int) -> float:
        """
        @brief 计算图像重心位置
        @details 通过计算图像矩来获取形状特征，并根据区域面积判断是否更新重心位置
        
        @param binary 二值图像
        @param width 图像宽度
        @return 重心的x坐标
        """
        # 计算图像的矩，用于获取形状特征
        moments = cv2.moments(binary, binaryImage=True)
        
        # 计算区域面积
        area = moments["m00"] / 255.0
        
        # 判断区域面积是否足够大，防止误检
        if area > self.config.min_size_percent * binary.size or True:
            # 计算区域重心的x坐标
            x_line: float = moments["m10"] / moments["m00"]
            # 更新最后检测到的重心位置
            self.last_x_line = x_line
        else:
            # 如果面积太小，使用上次的位置数据
            x_line = self.last_x_line
        return x_line

    def create_visualization(self, binary: cv2.Mat, width: int, x_line: float) -> cv2.Mat:
        """
        @brief 创建可视化图像
        @details 根据色彩类型转换图像以便绘制彩色标记，并绘制图像中心线和重心位置
        
        @param binary 二值图像
        @param width 图像宽度
        @param x_line 重心的x坐标
        @return 可视化图像
        @throws ValueError 当配置的色彩类型无效时抛出异常
        """
        # 根据色彩类型转换图像以便绘制彩色标记
        if self.config.colour_type == ColourType.GREY:
            visual = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        elif self.config.colour_type == ColourType.HSV:
            visual = cv2.cvtColor(binary, cv2.COLOR_HSV2BGR)
        else:
            raise ValueError('Invalid colour type')

        # 获取图像高度
        height = visual.shape[0]
        
        # 绘制图像中心线（黄色）
        cv2.line(visual, (width // 2, 0), (width // 2, height - 1), (0, 255, 255), 1)
        
        # 绘制检测到的重心位置（红色圆点）
        cv2.circle(visual, (int(x_line), height - 5), 4, (0, 0, 255), -1)
        return visual

    def calculate_control_values(self, error: float) -> tuple[float, int, int]:
        """
        @brief 计算控制值
        @details 使用PID控制器计算转向值，并根据误差大小动态调整左右轮速度
        
        @param error 归一化的误差值
        @return (转向值, 左轮速度, 右轮速度)的元组
        """
        # 计算时间差，用于PID控制器的微分项
        dt = time() - self.last_time
        self.last_time = time()

        # 计算误差变化率
        de = error - self.last_error
        self.last_error = error
        
        # 使用PID控制器计算转向值
        # Kp项：比例控制，直接响应当前误差
        # Kd项：微分控制，预测未来趋势，减少震荡
        # Ki项：积分控制，消除稳态误差
        steer = self.config.Kp * error + self.config.Kd * (de / dt) + self.config.Ki * (self.sum_error * dt)
        
        # 限制转向值在[-1, 1]范围内
        steer = max(-1.0, min(1.0, steer))

        # 根据误差大小动态调整基本速度，误差越大速度越慢
        v_base = max(0.0, min(180.0, 160-110 * abs(error)))

        # 根据转向值计算左右轮的权重
        mix = max(-1.0, min(1.0, steer))
        weight_left = 1.0 + self.config.turn_gain * mix
        weight_right = 1.0 - self.config.turn_gain * mix

        # 调整权重使其最小值为0
        weight_min = min(weight_left, weight_right)
        if weight_min < 0:
            weight_left -= weight_min
            weight_right -= weight_min

        # 根据权重计算左右轮的速度
        if max(weight_left, weight_right) > 0:
            # 计算缩放因子以保证最大速度不超过v_base
            scale = (v_base - weight_min) / max(weight_left, weight_right)
            v_left = weight_min + weight_left * scale
            v_right = weight_min + weight_right * scale
        else:
            # 特殊情况下的处理
            v_left = v_right = weight_min

        # 将速度值转换为整数并限制在[0, 180]范围内
        v_left = int(max(0, min(180, round(v_left))))
        v_right = int(max(0, min(180, round(v_right))))
        
        return steer, v_left, v_right

if __name__ == '__main__':
    pass