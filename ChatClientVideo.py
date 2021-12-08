import socket
from threading import *

import cv2, numpy, time
import struct
import pickle

class ChatClient2:
    def __init__(self):
        self.c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.TCP_IP = 'localhost'
        # self.TCP_PORT = 9000
        self.TCP_IP = "211.199.232.191"
        self.TCP_PORT = 9122
        self.c_sock.connect((self.TCP_IP, self.TCP_PORT))
        self.flag = True


    def __del__(self):
        print("종료했으~~~")
        return True

    def send_video(self, capture):
        entrance = {'entrance_name': 'entrance3_video', 'address': 'video'}
        entrance = str(entrance)
        self.c_sock.send(entrance.encode())

        # OpenCV를 이용해서 webcam으로 부터 이미지 추출
        # capture = cv2.VideoCapture(0)
        # 크기 지정
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 가로
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # 세로

        while True:
            ret, frame = capture.read()

            # 추출한 이미지를 String 형태로 변환(인코딩)시키는 과정
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, imgencode = cv2.imencode('.jpg', frame, encode_param)
            data = numpy.array(imgencode)
            stringData = data.tostring()

            # String 형태로 변환한 이미지를 socket을 통해서 전송
            self.c_sock.send(str(len(stringData)).ljust(16).encode());
            self.c_sock.send(stringData);

            if self.flag == False:
                break

        # 메모리를 해제
        # capture.release()
        print("끝")

    def receive_message(self):
        while True:
            buf = self.c_sock.recv(1024)
            print(buf.decode())
            if not buf:
                break
            else:
                buf = buf.decode()
                if buf == "End":
                    self.flag = False
                    break



if __name__== "__main__":
    ChatClient2()