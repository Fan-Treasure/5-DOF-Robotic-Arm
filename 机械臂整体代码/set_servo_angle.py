import sys

sys.path.append("../../src")
import time
import struct
import serial

from uservo import UartServoManager

SERVO_PORT_NAME = 'COM3'
SERVO_BAUDRATE = 115200
SERVO_ID0 = 0
SERVO_ID1 = 0
SERVO_ID2 = 2
SERVO_ID3 = 3
SERVO_ID4 = 4
SERVO_HAS_MTURN_FUNC = False


def dong(theta3, theta4, theta5, theta6, theta7):
    uart = serial.Serial(port=SERVO_PORT_NAME, baudrate=SERVO_BAUDRATE, parity=serial.PARITY_NONE, stopbits=1,
                         bytesize=8, timeout=0)

    uservo = UartServoManager(uart, is_debug=True)
    uservo.set_servo_angle(SERVO_ID0, theta3, velocity=60.0, t_acc=100, t_dec=100)  # 设置舵机角度(指定转速 单位°/s)
    print("-> {}".format(uservo.query_servo_angle(SERVO_ID0)))
    uservo.set_servo_angle(SERVO_ID1, theta4, velocity=60.0, t_acc=100, t_dec=100)  # 设置舵机角度(指定转速 单位°/s)
    print("-> {}".format(uservo.query_servo_angle(SERVO_ID1)))
    uservo.set_servo_angle(SERVO_ID2, theta5, velocity=60.0, t_acc=100, t_dec=100)  # 设置舵机角度(指定转速 单位°/s)
    print("-> {}".format(uservo.query_servo_angle(SERVO_ID2)))
    uservo.set_servo_angle(SERVO_ID3, theta6, velocity=60.0, t_acc=100, t_dec=100)  # 设置舵机角度(指定转速 单位°/s)
    print("-> {}".format(uservo.query_servo_angle(SERVO_ID3)))
    uservo.set_servo_angle(SERVO_ID4, theta7, velocity=60.0, t_acc=100, t_dec=100)  # 设置舵机角度(指定转速 单位°/s)
    print("-> {}".format(uservo.query_servo_angle(SERVO_ID4)))
    uservo.wait()  # 等待舵机静止
