import socket
import time
from datetime import datetime
from PyQt5.QtCore import *
import cv2, numpy
import pickle
import struct
import SaveImageFile

class MaskServer(QThread):
    clients = []
    ui_signal = pyqtSignal(str)     #ui랑 통신
    client_signal = pyqtSignal(str)     # 클라이언트랑 통신
    client_video_signal = pyqtSignal(object)    # 클라이언트 비디오 통신
    ui_video_signal = pyqtSignal(object)
    def run(self):
        self.s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.TCP_IP = 'localhost'
        # self.TCP_PORT = 9000

        self.TCP_IP = "192.168.0.110"
        self.TCP_PORT = 9000

        self.s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s_sock.bind((self.TCP_IP, self.TCP_PORT))
        self.s_sock.listen(10)
        print("클라이언트 대기중!!")

        while True:
            try:
                c_socket, (c_ip, c_port) = self.s_sock.accept()

                print(c_ip, ':', str(c_port), ' 가 연결되었습니다.')
                self.entrance = c_socket.recv(1024).decode()
                print(self.entrance)
                self.entrance = eval(self.entrance)
                self.entrance.update({'ip': c_ip, 'port': c_port})

                #
                self.clients.append({"entrance_name": self.entrance['entrance_name'], "socket": c_socket})

                if self.entrance['address'] == "video":

                    self.th2 = Receive2(c_socket, self.entrance['entrance_name'])
                    self.th2.start()
                    print("thread2 end")

                elif self.entrance['address'] == "Image":
                    self.th3 = Receive3(c_socket, self.entrance['entrance_name'])
                    self.th3.start()

                else:
                    self.send_entrance_info()  # 출입구 이름 보내기

                    self.client_signal.connect(Receive.send_message)
                    self.client_video_signal.connect(Receive.send_video)

                    self.th = Receive(c_socket, self.entrance['entrance_name'])
                    self.th.send_signal.connect(self.receive_client_message)
                    #th.video_signal.connect(self.ui_video)
                    #th.video_signal.connect(self.ui_signal)

                    self.th.start()
            except Exception as e:
                print("여기서 오류 2")
                print(e)

    def test(self, val):        #클라이언트에 메시지 보내기
        print(val)
        try:
            for client in self.clients:
                if client['entrance_name'] == val:
                    c_socket = client['socket']

            #val = "send realtime video"
            c_socket.send(val.encode())
        except Exception as e:
            print("여기서 오류 3")
            print(e)


    def send_entrance_info(self):   # UI에 출입구 정보 보내기
        self.ui_signal.emit("E" + str(self.entrance))

    def receive_client_message(self, message):  #UI에 출입구에서 온 메시지 보내기
        try:
            self.ui_signal.emit("M" + message)
            if message[:4] == "quit":
                self.th.exit()
                self.th.wait()
                self.th2.exit()
                self.th2.wait()
        except Exception as e:
            print("여기서 오류 4")
            print(e)


class Receive(QThread):
    send_signal = pyqtSignal(str)
    video_signal = pyqtSignal(object)

    def __init__(self, c_socket, entrance_name):
        super().__init__()
        self.c_socket = c_socket
        self.entrance_name = entrance_name

    def run(self):
        while True:
            try:
                incoming_message = self.c_socket.recv(1024)
                print(type(incoming_message))
                print("message size : ", len(incoming_message))
                time.sleep(1)
                if not incoming_message or len(incoming_message) == 0:
                    #self.send_message("quit")
                    # 종료 부분
                    break
                incoming_message = incoming_message.decode()
                print("메세지 확인 1 : " + incoming_message)

                if incoming_message[:4] == "quit":  #종료 메세지 보내야됌
                    self.c_socket.send(incoming_message[:4].encode())
                    self.send_message(incoming_message)
                else:


                    message = self.entrance_name + " : " + incoming_message
                    print("메세지 확인 2 : " + message)
                    self.send_message(message)


            except Exception as e:
                print("여기서 오류 5")
                print(e)

                if str(e) == "[WinError 10054] 현재 연결은 원격 호스트에 의해 강제로 끊겼습니다":
                    message = "error" + self.entrance_name
                    print(message)
                    self.send_message(message)
                    break
                else:
                    message = "quit" + self.entrance_name
                    print(message)
                    self.send_message(message)
                    break

        self.c_socket.close()

    def send_message(self, message):
        try:
            self.send_signal.emit(message)
        except Exception as e:
            print("여기서 오류 6")

    def send_video(self, message):
        try:
            print(message)
            self.video_signal.emit(message)
        except Exception as e:
            print("여기서 오류 7")

class Receive2(QThread):
    def __init__(self, c_socket, entrance_name):
        super().__init__()
        self.c_socket = c_socket
        self.entrance_name = entrance_name

    def run(self):
        try:
            conn = self.c_socket
            while True:
                # String형의 이미지를 수신받아서 이미지로 변환 하고 화면에 출력
                length = self.recvall(conn, 16)  # 길이 16의 데이터를 먼저 수신하는 것은 여기에 이미지의 길이를 먼저 받아서 이미지를 받을 때 편리하려고 하는 것이다.
                stringData = self.recvall(conn, int(length))
                data = numpy.fromstring(stringData, dtype='uint8')

                decimg = cv2.imdecode(data, 1)
                cv2.imshow(self.entrance_name, decimg)
                #cv2.waitKey(0)
                #cv2.destroyAllWindows()
                #1초 마다 키 입력 상태를 받음

                if cv2.waitKey(1) & 0xFF == 27:
                    self.c_socket.send("End".encode())
                    cv2.destroyAllWindows()
                    break
        except Exception as e:
            print("여기서 오류 5")
            print(e)

    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf:
                return None
            buf += newbuf
            count -= len(newbuf)
        return buf

class Receive3(QThread):
    def __init__(self, c_socket, entrance_name):
        super().__init__()
        self.c_socket = c_socket
        self.entrance_name = entrance_name

    def run(self):
        try:
            conn = self.c_socket

            while True:
                # String형의 이미지를 수신받아서 이미지로 변환 하고 화면에 출력
                length = self.recvall(conn, 16)  # 길이 16의 데이터를 먼저 수신하는 것은 여기에 이미지의 길이를 먼저 받아서 이미지를 받을 때 편리하려고 하는 것이다.
                stringData = self.recvall(conn, int(length))
                data = numpy.fromstring(stringData, dtype='uint8')

                decimg = cv2.imdecode(data, 1)
                #print(decimg)
                dt_now = datetime.now()

                sif = SaveImageFile.SaveImageFile()
                path = sif.getDirPath(self.entrance_name) + "/"

                today = dt_now.strftime("%Y-%m-%d %H-%M-%S")
                cv2.imwrite(path + str(today)+ ".jpg",decimg)

                #cv2.imshow('SERVER', decimg)
                #cv2.waitKey(0)
                #cv2.destroyAllWindows()

                #1초 마다 키 입력 상태를 받음
                if cv2.waitKey(1) & 0xFF == 27:
                    self.c_socket.send("End".encode())
                    cv2.destroyAllWindows()
                    break
                time.sleep(1.0)

        except Exception as e:
            print(e)

    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf:
                return None
            buf += newbuf
            count -= len(newbuf)
        return buf