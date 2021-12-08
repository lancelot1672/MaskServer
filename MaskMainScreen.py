from PyQt5 import QtCore, QtWidgets, Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import MaskServer
from threading import *
from PyQt5.QtCore import QThread
import socket
import cv2
import pickle
import struct

class MainScreen(QtWidgets.QMainWindow):
    main_signal_1 = pyqtSignal(str) #str 타입으로 전송할 시그널 만들기
    ui_video_signal = pyqtSignal(object)
    clients = []
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.show()

        self.setConnect()

    def setupUi(self):
        self.setObjectName("MainWindow")
        self.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.setTableWidget()
        self.setRecode_Browser()
        self.setEntrance_Browser()
        self.setButton()
        self.label3 = QtWidgets.QLabel()
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(517, 369, 281, 31))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(517, 0, 281, 20))
        self.label_2.setObjectName("label_2")
        self.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(self )
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        self.tableWidget.cellClicked.connect(self.cellCliecked_event)
        # QDialog 설정
        self.dialog = QtWidgets.QDialog()

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def cellCliecked_event(self, row, col):     # cell 클릭 이벤트
        self.data = self.tableWidget.item(row, col)  # 클릭 된 해당 셀의 내용

        if self.data:
            print("셀 클릭 셀 값 : ", self.data.text())
            for client in self.clients:
                if(client['entrance_name'] == self.data.text()):
                    self.setEntranceInfo(client)
        else:
            pass

    def setConnect(self):
        try:
            maskServer = MaskServer.MaskServer(self)        # self

            self.main_signal_1.connect(maskServer.ui_signal)
            self.ui_video_signal.connect(maskServer.ui_video_signal)

            maskServer.ui_signal.connect(self.messageGate)  # 메시지 받는거고
            maskServer.ui_signal.connect(maskServer.test)   # 보내는거임

            maskServer.ui_video_signal.connect(self.get_video)  # 비디오 받기

            maskServer.start()
        except Exception as e:
            print("여기서 오류 3")

    def setTableEntrance(self, entrance): # 연결 되었을 때, 세팅

        entrance = eval(entrance)
        self.entrance_Browser.clear()
        self.clients.append(entrance)
        self.setEntranceInfo(entrance)
        for i in range(0, 8):
            if self.tableWidget.item(i, 0):
                pass
            else:
                self.tableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(str(entrance['entrance_name'])))
                self.tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(str(entrance['address'])))
                self.tableWidget.setItem(i, 2, QtWidgets.QTableWidgetItem(str("Active On")))
                self.tableWidget.item(i, 0).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)      # 가운데 정렬
                self.tableWidget.item(i, 1).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                self.tableWidget.item(i, 2).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                break

    def repaintTableWidget(self):
        self.tableWidget.clearContents()

        i = 0
        try:
            for client in self.clients:
                self.tableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(str(client['entrance_name'])))
                self.tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(str(client['address'])))
                self.tableWidget.setItem(i, 2, QtWidgets.QTableWidgetItem(str("Active On")))

                self.tableWidget.item(i, 0).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)  # 가운데 정렬
                self.tableWidget.item(i, 1).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                self.tableWidget.item(i, 2).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                if i == len(self.clients):
                    break
                i = i + 1

        except Exception as e:
            print("여기서 오류1")
            print(e)
    def repaintEntrance_Browser(self):
        self.entrance_Browser.clear()

    def receiveEntranceRecode(self, message):
        try:
            self.recode_Browser.append(message)
        except Exception as e:
            print("여기서 오류6")
            print(e)
    def messageGate(self, val):
        try:
            message = val

            if message[0] == "E":       # 출입구 flag 이면
                self.setTableEntrance(message[1:])
            elif message[0] == "M":     # 메세지 flag 이면
                message = message[1:]
                if message[:4] == "quit":       # 종료 메시지 이면
                     entrance = message[4:]
                     print("entrance :: " ,entrance)
                     for client in self.clients:
                         if client['entrance_name'] == entrance:        # 출입구 딕셔너리 제거
                             self.clients.remove(client)
                             self.repaintTableWidget()              # 테이블 위젯 다시그리기
                             self.repaintEntrance_Browser()
                             break
                elif message[:5] == "error":        # 에러로 클라이언트가 종료시
                    entrance = message[5:]
                    print("entrance :: ", entrance)
                    for client in self.clients:
                        if client['entrance_name'] == entrance:  # 출입구 딕셔너리 제거
                            self.clients.remove(client)
                            self.repaintTableWidget()  # 테이블 위젯 다시그리기
                            self.repaintEntrance_Browser()
                            break
                else:
                    print(message)
                    self.receiveEntranceRecode(message)
        except Exception as e:
            print(e)

    def setEntranceInfo(self, entrance):
        self.entrance_Browser.clear()
        self.entrance_Browser.append('출입구 : ' + str(entrance['entrance_name']))
        self.entrance_Browser.append('ip : ' + str(entrance['ip']))
        self.entrance_Browser.append('port : ' + str(entrance['port']))

    def setTableWidget(self):
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(0, 0, 511, 281))
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(8)
        self.tableWidget.setColumnWidth(0, 150)
        self.tableWidget.setColumnWidth(1, 240)
        self.tableWidget.setColumnWidth(2, 115)


        for i in range(0, 8):
            self.tableWidget.setVerticalHeaderItem(i, QtWidgets.QTableWidgetItem())

        for i in range(0, 3):
            self.tableWidget.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem())


        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText("출입구")
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText("위치")
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText("동작")

        # 수정 불가능하게 만듬.
        self.tableWidget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

    def setRecode_Browser(self):        # 출입 기록
        self.recode_Browser = QtWidgets.QTextBrowser(self.centralwidget)
        self.recode_Browser.setGeometry(QtCore.QRect(510, 20, 291, 351))
        self.recode_Browser.setObjectName("textBrowser")

    def setEntrance_Browser(self):      # 출입구 정보
        self.entrance_Browser = QtWidgets.QTextBrowser(self.centralwidget)
        self.entrance_Browser.setGeometry(QtCore.QRect(510, 401, 291, 161))
        self.entrance_Browser.setObjectName("textBrowser_2")

    def setButton(self):
        self.button1 = QtWidgets.QPushButton("출입 로그 확인", self)
        self.button1.setGeometry(QtCore.QRect(80, 280, 221, 91))

        self.button2 = QtWidgets.QPushButton("출입구 확인", self)
        self.button2.setGeometry(QtCore.QRect(290, 280, 221, 91))
        self.button2.clicked.connect(self.button2ClickEvent)

    def button2ClickEvent(self):
        #클라이언트에게 메시지를 보내 영상 전송하게 만듬
        # self.main_signal_1.emit("UI에서 보낸 메세지 일세 ㅋㅋ")
        try:
            message = self.data.text()

            if message:
                self.main_signal_1.emit(message)
        except:
            pass

    def get_video(self, message):
        print("get video test")
        print(message)
        pass

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "1자연관 출입 서버"))

        self.label.setText(_translate("MainWindow", "출입구 정보"))
        self.label_2.setText(_translate("MainWindow", "출입 로그 기록"))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myWindow = MainScreen()
    app.exec_()
