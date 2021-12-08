import serial
import time

class ControllDoor:
    def __init__(self):
        # 'COM3' 부분에 환경에 맞는 포트 입력
        self.ser = serial.Serial('COM3', 9600)

    def controller(self, val):
        if self.ser.readable():

            if val == '1':                              # 마스크 썼으면
                val = val.encode('utf-8')
                self.ser.write(val)
                #print("LED TURNED ON")
                time.sleep(0.5)

            elif val == '0':                            # 마스크 안썼으면
                val = val.encode('utf-8')
                self.ser.write(val)
                #print("LED TURNED OFF")
                time.sleep(0.5)