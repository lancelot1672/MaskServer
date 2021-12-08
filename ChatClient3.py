import socket
from threading import *

import cv2, numpy, time
import struct
import pickle
import ChatClientVideo
import ChatClientImage

from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import numpy as np
import cv2
import tensorflow as tf

class ChatClient:
    def __init__(self):
        self.c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.TCP_IP = 'localhost'
        # self.TCP_PORT = 9000
        self.TCP_IP = "211.199.232.191"
        self.TCP_PORT = 9122
        self.flag = True
        self.entrance_name = "출입구3"
        self.address = "1자연관 3층 메인 출입구"
        # import ControllDoor
        # self.door = ControllDoor.ControllDoor()

        self.source = cv2.VideoCapture(0)
        self.c_sock.connect((self.TCP_IP, self.TCP_PORT))
        self.listen_thread()

    def send_chat(self):
        entrance = {'entrance_name': self.entrance_name , 'address': self.address}
        entrance = str(entrance)

        self.c_sock.send(entrance.encode())
        while True:
            try:
                message = input("message :: ")

                if not message:
                    break
                elif message == "quit":
                    message = message + self.entrance_name
                    self.c_sock.send(message.encode())
                    time.sleep(2)
                    print("보내기 종료")
                    break
                else:
                    message = "M" + message
                    self.c_sock.send(message.encode())

            except Exception as e:
                print(e)

    def listen_thread(self):
        self.t = Thread(target=self.receive_message, args=(self.c_sock,))
        self.t2 = Thread(target=self.send_chat)
        self.t3 = Thread(target=self.startVideo, args=(self.c_sock, ))

        self.imageClient = ChatClientImage.ImageClient(self.source,  self.entrance_name)
        self.t4 = Thread(target=self.imageClient.send_image)

        self.t2.start()
        self.t.start()
        self.t3.start()
        self.t4.start()

        self.t2.join()
        self.t.join()
        self.t3.join()

    def receive_message(self, c_socket):
        # server로부터 message를 수신하고 표시
        while True:
            buf = c_socket.recv(1024)
            if not buf:
                print("아마 끝..")
                break
            elif buf.decode() == "quit":
                print("메시지 받기 종료")
                self.flag = False

                break
            else:
                buf = buf.decode()
                print("recv_message :: ", buf)
                if buf == self.entrance_name:
                    print("video 전송을 시작합니다.")

                    a = ChatClientVideo.ChatClient2()
                    t = Thread(target=a.receive_message)
                    t.start()

                    a.send_video(self.source)
                    print("종료 해줘..")
                elif buf == 'End':
                    print("종료")

    def detect_and_predict_mask(self, frame, faceNet):
        # grab the dimensions of the frame and then construct a blob
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104.0, 177.0, 123.0))

        faceNet.setInput(blob)
        detections = faceNet.forward()

        # initialize our list of faces, their corresponding locations and list of predictions
        locs = []
        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > 0.2:
                # we need the X,Y coordinates
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype('int')

                # ensure the bounding boxes fall within the dimensions of the frame
                (startX, startY) = (max(0, startX), max(0, startY))
                (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

                # # extract the face ROI, convert it from BGR to RGB channel, resize it to 224,224 and preprocess it
                # face = frame[startY:endY, startX:endX]
                # face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                # face = cv2.resize(face, (64, 64))
                # face = img_to_array(face)
                # face = preprocess_input(face)
                #
                # faces.append(face)
                # locs.append((startX - 30, startY - 50, endX + 30, endY + 20))
                locs.append((startX, startY, endX, endY))

            # # only make a predictions if atleast one face was detected
            # if len(faces) > 0:
            #     faces = np.array(faces, dtype='float32')
            return locs

    def startVideo(self, c_socket):
        try:
            self.prototxtPath = "./face_detector/deploy.prototxt"
            self.weightsPath = "./face_detector/res10_300x300_ssd_iter_140000.caffemodel"
            faceNet = cv2.dnn.readNet(self.prototxtPath, self.weightsPath)



            from keras import models
            model = tf.keras.models.load_model('Maskmodel7.h5')

            while True:
                # grab the frame from the threaded video stream and resize it
                # to have a maximum width of 400 pixels
                ret, self.frame = self.source.read()

                # detect faces in the frame and preict if they are waring masks or not
                # (locs, preds) = detect_and_predict_mask(frame, faceNet, maskNet)
                locs = self.detect_and_predict_mask(self.frame, faceNet)

                for (box) in locs:
                    (startX, startY, endX, endY) = box
                    img = self.frame[startY:endY, startX:endX]
                    try:
                        img = cv2.resize(img, (128, 128))
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                        x = np.expand_dims(img, axis=0)
                        images = np.vstack([x])
                        classes = model.predict(x, batch_size=1)

                        if classes[0] < 0.2:
                            cv2.rectangle(self.frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                            # self.door.controller(str(1))
                        else:
                            cv2.rectangle(self.frame, (startX, startY), (endX, endY), (0, 0, 255), 2)
                            # self.door.controller(str(0))
                            self.send_message_no_mask(c_socket)


                    except Exception as e:
                        print(e)
                    # show the output frame
                cv2.imshow("Frame", self.frame)

                if self.flag == False:
                    break

                if cv2.waitKey(1) & 0xFF == 27:
                    self.c_socket.send("End".encode())
                    cv2.destroyAllWindows()
                    break

                #time.sleep(1.0)
        except Exception as e:
            print(e)
    def send_message_no_mask(self, c_socket):
        message = "마스크 미착용자 출입 발생"

        c_socket.send(message.encode())
        #self.door.controller(str(1))
        self.imageClient.flag = False

if __name__ == "__main__":
    ChatClient()