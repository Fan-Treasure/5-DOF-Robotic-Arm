2#!/usr/bin/env python3
# coding=utf8
import smbus
import time
import numpy
import os
    
class TTS:
        address = 0x40
        bus = None

        def __init__(self, bus=1):
            self.bus = smbus.SMBus(bus)
        
        def WireReadTTSDataByte(self):
            try:
                val = self.bus.read_byte(self.address)
            except:
                return False
            return True
        
def TTSModuleSpeak(self, sign, words):
            head = [0xFD,0x00,0x00,0x01,0x00]
            wordslist = words.encode("gb2312")
            signdata = sign.encode("gb2312")    
            length = len(signdata) + len(wordslist) + 2
            head[1] = length >> 8
            head[2] = length
            head.extend(list(signdata))
            head.extend(list(wordslist))       
            try:
                self.bus.write_i2c_block_data(self.address, 0, head)
            except:
                print('Sensor not connected!')
            time.sleep(0.05)


def speak1()：
    if __name__ == '__main__':
        v = TTS()
        v.TTSModuleSpeak("[h0][v10][m53]","真有一手为您服务")   
        time.sleep(1) 

def speak2()：
    if __name__ == '__main__':
        v = TTS()
        v.TTSModuleSpeak("[h0][v10][m53]","真有一手来了")   
        time.sleep(1) 

def speak3()：
    if __name__ == '__main__':
        v = TTS()
        v.TTSModuleSpeak("[h0][v10][m53]","真有一手对准您了")  
        time.sleep(0.5) 
        v.TTSModuleSpeak("[h0][v10][m53]","您现在可以用手势指挥我")  
        time.sleep(1)



def speak4()：
    if __name__ == '__main__':
        v = TTS()
        m=cnt
        m=str.format(m)
        v.TTSModuleSpeak("[h0][v10][m53]","已经框出",m,"张人脸")  
        time.sleep(0.5)

def speak5()：
    if __name__ == '__main__':
        v = TTS()
        v.TTSModuleSpeak("[h0][v10][m53]","检测到人脸")   
        time.sleep(1) 



def begin():
    speak1()
    print('kaishi')


class ASR:

        # Global Variables
        address = 0x79
        bus = None

        ASR_RESULT_ADDR = 100

        ASR_WORDS_ERASE_ADDR = 101

        ASR_MODE_ADDR = 1


        ASR_ADD_WORDS_ADDR = 160

def __init__(self, bus=1):
    self.bus = smbus.SMBus(bus)

def readByte(self):
    try:
        result = self.bus.read_byte(self.address)
                except:
                    return None
                return result

            def writeByte(self, val):
                try:
                    value = self.bus.write_byte(self.address, val)
                except:
                    return False
                if value != 0:
                    return False
                return True

            def writeData(self, reg, val):
                try:
                    self.bus.write_byte(self.address,  reg)
                    self.bus.write_byte(self.address,  val)
                except:
                    pass

def getResult(self):
            if ASR.writeByte(self, self.ASR_RESULT_ADDR):
                return -1
            try:
                value = self.bus.read_byte(self.address)
            except:
                return None
            return value

def addWords(self, idNum, words):
            buf = [idNum]
            for i in range(0, len(words)):
                buf.append(eval(hex(ord(words[i]))))
            try:
                self.bus.write_i2c_block_data(self.address, self.ASR_ADD_WORDS_ADDR, buf)
            except:
                pass
            time.sleep(0.1)

def eraseWords(self):
            try:
                result = self.bus.write_byte_data(self.address, self.ASR_WORDS_ERASE_ADDR, 0)
            except:
                return False
            time.sleep(0.1)
            if result != 0:
            return False
            return True

def setMode(self, mode):
            try:
                result = self.bus.write_byte_data(self.address, self.ASR_MODE_ADDR, mode)
            except:
                return False
            time.sleep(0.1)
            if result != 0:
            return False
            return True

    
def asr():
    if __name__ == "__main__":
            asr = ASR()
            if 1:
                asr.eraseWords()
                asr.setMode(1)
                asr.addWords(1, 'kai shi')
                asr.addWords(2, 'shi bie ren lian')
                asr.addWords(3, '')
                asr.addWords(4, '')
                asr.addWords(5, 'lou yi shou')
            while 1:
                data = asr.getResult()
                if data==5:
                    print("result:", data)
                    speak2()
                
                if data==2:
                    print("result:", data)
                    time.sleep(1)
                    speak3()