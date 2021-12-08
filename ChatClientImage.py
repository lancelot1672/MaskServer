import socket
import cv2, numpy, time

class ImageClient:
    def __init__(self, source, entrance_name):
        self.c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.TCP_IP = 'localhost'
        # self.TCP_PORT = 9000
        self.TCP_IP = "211.199.232.191"
        self.TCP_PORT = 9122
        self.c_sock.connect((self.TCP_IP, self.TCP_PORT))

        self.capture = source
        self.entrance_name = entrance_name

        self.image_socket_connect()
        self.flag = True

    def image_socket_connect(self):
        entrance = {'entrance_name': 'entrance3_Image', 'address': 'Image'}
        entrance = str(entrance)
        self.c_sock.send(entrance.encode())

    def send_image(self):
        while True:
            # 크기 지정
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 가로
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # 세로

            ret, frame = self.capture.read()

            # 추출한 이미지를 String 형태로 변환(인코딩)시키는 과정
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, imgencode = cv2.imencode('.jpg', frame, encode_param)
            data = numpy.array(imgencode)
            stringData = data.tostring()

            if self.flag == False:
                #여기서 if문 돌려서 마스크 미착용 메시지 발생 시 이미지 전송.
                # String 형태로 변환한 이미지를 socket을 통해서 전송
                self.c_sock.send(str(len(stringData)).ljust(16).encode());
                self.c_sock.send(stringData);
                time.sleep(1)
            self.flag = True
