import time
import Board
import signal

start = True


def Stop(signum, frame):
    global start

    start = False
    print('关闭中...')


Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
Board.RGB.show()

signal.signal(signal.SIGINT, Stop)


def light():
    Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
    Board.RGB.show()
    time.sleep(1)

    Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
    Board.RGB.show()
    time.sleep(1)

    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
    Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
    Board.RGB.show()
    time.sleep(1)

    Board.RGB.setPixelColor(0, Board.PixelColor(255, 255, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(255, 255, 0))
    Board.RGB.show()
    time.sleep(1)




def close():
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
    print('已关闭')
