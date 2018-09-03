#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DSQT2018.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!


import sys
import threading
import sqlite3
import paho.mqtt.client as mqtt
import json
from PyQt5 import QtCore, QtGui, QtWidgets, uic

# from DSQT2018 import *

dbName = 'DungeonStatus.db'

alarmValue = 0

baseColors = dict()
baseData = dict()
baseCommand = dict()

lockData = dict()
lockCode = dict()
lockOrder = dict()
lockIPtoName = dict()
lockFrames = dict()
cardNames = dict()

def readColorData():
    global baseColors
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT * FROM dict ORDER BY Id"):
        baseColors[str(row[0])] = [row[1],row[2],row[3]]
    conn.close()

def readBaseData():
    global baseData
    global baseCommand
    jsStr = '{'
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT colorStatus, alarmLevel \
                                     FROM baseStatus"):
        jsStr += '"colorStatus":"' + row[0] + '","alarmLevel":"' + str(row[1]) + '",'
    jsStr = jsStr.rstrip(',') + '}'
    baseData = json.loads(jsStr)
    jsStr = '{'
    req = conn.cursor()
    for row in req.execute("SELECT * \
                                    FROM baseCommands"):
        lockStr=json.dumps(row[1].split('\n'))
        termStr = json.dumps(row[2].split('\n'))
        rgbStr = json.dumps(row[3].split('\n'))
        jsStr += '"'+row[0]+'":{"lockCommand":'+lockStr+',"termCommand":'+ \
                 termStr+',"rgbCommand":'+rgbStr+'},'
    jsStr = jsStr.rstrip(',') + '}'
    baseCommand = json.loads(jsStr)
    conn.close()

def readLockData():
    global lockData
    global cardNames
    global lockOrder
    global lockIPtoName
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    reqCodes = conn.cursor()
    reqCardList = conn.cursor()
    for rowId in reqCardList.execute("SELECT * FROM cardList"):
        cardNames[rowId[0]] = rowId[1]
    jsStr = '{'
    for row in req.execute("SELECT name, IPAddr, isSound, lockState, baseState \
                                FROM lockStatus \
                                ORDER BY name"):
        jsStr += '"'+row[0]+'":{"IPAddr":"'+row[1]+'","isSound":"'+row[2]+'","lockState":"'+row[3]+ \
                 '","baseState":"'+row[4]+'","isAlive":"False","aliveTimeStamp":0,"codes":{'
        lockIPtoName[row[1]] = row[0]
        for rowCard in reqCodes.execute("SELECT cardNumber, stateList \
                                        FROM lockCodes \
                                        WHERE lockName = ?",[row[0]]):
            jsStr += '"'+rowCard[0]+'":["'+'","'.join(rowCard[1].split(','))+'"],'

        jsStr = jsStr.rstrip(',') + '}},'
    jsStr = jsStr.rstrip(',') + '}'
    lockData = json.loads(jsStr)
    print (jsStr)
    for row in req.execute("SELECT * FROM lockOrder ORDER BY lockNumber"):
        lockOrder[row[0]] = row[1]
    conn.close()

def lockExpand():
    sender = window.sender()
    lockNum = int(sender.objectName()[len(sender.objectName())-1])
    lockName = lockOrder[lockNum]
    window.lockNameExpand.setText(lockName)
    window.entryIPAddrLock.setText(lockData[lockName]['IPAddr'])
    window.scrollCodesBox = QtWidgets.QGroupBox('')
    window.scrollCodesForm = QtWidgets.QVBoxLayout()
    for idCode in cardNames.keys():
        window.frame = QtWidgets.QFrame()
        window.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        window.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        window.frame.setGeometry(QtCore.QRect(10, 10, 351, 21))
        window.frame.setFixedHeight(20)
        window.frame.setMaximumHeight(20)
        window.labCardName = QtWidgets.QLabel(window.frame)
        window.labCardName.setText(str(cardNames[idCode]))
        window.labCardName.setGeometry(QtCore.QRect(0, 0, 231, 21))
        window.labCardName.setObjectName("labCard_" + idCode)
        i = 1
        while i<6:
            print(i)
            window.checkBox = QtWidgets.QCheckBox(window.frame)
            window.checkBox.setGeometry(QtCore.QRect(230+19*i, 0, 17, 17))
            window.checkBox.setText("")
            bgColor=baseColors[str(i)][0]
            window.checkBox.setStyleSheet('background-color: ' + bgColor)
            window.checkBox.setObjectName("checkBox_"+str(i))
            i = i + 1
        window.frame.setObjectName("frame_" + idCode)
        window.scrollCodesForm.addWidget(window.frame)
    window.scrollCodesBox.setLayout(window.scrollCodesForm)
    window.scrollCodes.setWidget(window.scrollCodesBox)
    window.scrollCodes.setWidgetResizable(True)




def createLockFrame(lockNum,lockName):
    global lockData
    global cardNames
    global lockOrder
    global lockIPtoName
    global lockFrames
    global window

    window.frame = QtWidgets.QFrame()
    window.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    window.frame.setFrameShadow(QtWidgets.QFrame.Raised)
    window.frame.setGeometry(QtCore.QRect(10, 10, 380, 60))
    window.frame.setFixedHeight(60)
    window.frame.setMaximumHeight(60)
    window.lockName = QtWidgets.QLabel(window.frame)
    window.lockName.setText(lockName)
    font = QtGui.QFont()
    font.setPointSize(10)
    font.setBold(True)
    font.setWeight(75)
    window.lockName.setFont(font)
    if lockData[lockName]['isAlive'] == 'True':
        fgColor = 'green'
    else:
        fgColor = 'red'
    palette = window.lockName.palette()
    palette.setColor(palette.WindowText, QtGui.QColor(fgColor))
    window.lockName.setPalette(palette)
    window.lockName.setObjectName(lockName)
    if lockData[lockName]['lockState'] == 'opened':
        stateText = 'Закрыть'
        blockText = 'Заблокировать'
        bgStateColor = '#FF8080'
        bgBlockColor = 'lightgreen'
    elif lockData[lockName]['lockState'] == 'closed':
        stateText = 'Открыть'
        blockText = 'Заблокировать'
        bgStateColor = 'lightgreen'
        bgBlockColor = 'lightgreen'
    else:
        stateText = 'Открыть'
        blockText = 'Разблокировать'
        bgStateColor = 'lightgreen'
        bgBlockColor = '#F08080'
    window.butState = QtWidgets.QPushButton(window.frame)
    window.butState.setGeometry(QtCore.QRect(10, 20, 75, 31))
    window.butState.setText(stateText)
    window.butState.setStyleSheet("QPushButton:hover { background-color: " + bgStateColor + " }")
    window.butState.setStyleSheet("QPushButton:!hover { background-color: " + bgStateColor + " }")
    # Добавить коннект на обработку кнопки открыть/закрыть
    window.butState.setObjectName("butState"+str(lockNum))
    window.butBlock = QtWidgets.QPushButton(window.frame)
    window.butBlock.setGeometry(QtCore.QRect(90, 20, 101, 31))
    window.butBlock.setText(blockText)
    window.butBlock.setStyleSheet("QPushButton:hover { background-color: " + bgBlockColor + " }")
    window.butBlock.setStyleSheet("QPushButton:!hover { background-color: " + bgBlockColor + " }")
    # Добавить коннект на обработку кнопки блокировать/разблокировать
    window.butBlock.setObjectName("butBlock"+str(lockNum))
    if lockData[lockName]['isSound'] == 'True':
        soundText = 'Звук ВЫКЛ'
        bgSoundColor = 'lightgreen'
    else:
        soundText = 'Звук ВКЛ'
        bgSoundColor = '#FF8080'
    window.butSound = QtWidgets.QPushButton(window.frame)
    window.butSound.setGeometry(QtCore.QRect(200, 20, 71, 31))
    window.butSound.setText(soundText)
    window.butSound.setStyleSheet("QPushButton:hover { background-color: " + bgSoundColor + " }")
    window.butSound.setStyleSheet("QPushButton:!hover { background-color: " + bgSoundColor + " }")
    window.butSound.setObjectName("butSound"+str(lockNum))
    # Добавить коннект на обработку кнопки включения/выключения звука
    window.butExpand = QtWidgets.QPushButton(window.frame)
    window.butExpand.setGeometry(QtCore.QRect(280, 20, 71, 31))
    window.butExpand.setText("Подробнее")
    window.butExpand.clicked.connect(lockExpand)
    window.butExpand.setObjectName("butExpand"+str(lockNum))
    window.frame.setObjectName("frameLock" + str(lockNum))
    window.scrollLocksForm.addWidget(window.frame)

def changeBaseScore():
    global window
    global alarmValue
    sender = window.sender()
    alarmChanged(int(sender.text()))

def alarmChanged(delta):
    global window
    global alarmValue
    alarmValue += delta
    window.baseScore.display(alarmValue)
    #
    # Обработка изменения тревоги
    #


def changeBaseStatus(colorIndex):
    global baseData
    global baseColors
    baseStatusChanged(colorIndex)

def baseStatusChanged(colorIndex):
    global baseData
    global baseColors
    global window
    colorIndex=str(colorIndex)
    baseData['colorStatus'] = baseColors[colorIndex][0]
    window.baseStatusList.setCurrentIndex(window.baseStatusList.findText(baseColors[colorIndex][1]))
    window.baseFrame.setAutoFillBackground(True)
    palette = window.baseFrame.palette()
    palette.setColor(palette.Background, QtGui.QColor(baseColors[colorIndex][0]))
    window.baseFrame.setPalette(palette)
    #
    # Дальше логическая обработка смены цвета базы, выдача команд и всё вот это вот.
    #

class ExampleApp(QtWidgets.QMainWindow):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        super().__init__()
        uic.loadUi('DSQT2018.ui', self)
        self.baseStatusList.activated.connect(self.baseStatusUserChanged)

    def baseStatusUserChanged(self, value):
        changeBaseStatus(value)

def main():
    global window
    global dbName

    # Читаем данные из БД
    readColorData()     # Цвета
    readBaseData()      # Текущий статус базы
    readLockData()      # Замки

    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp

    # Заполняем цветовые статусы в меню
    for cStatus in baseColors.keys():
        window.baseStatusList.addItem(baseColors[cStatus][1])
    # Ищем номер цвета
    for cStatus in baseColors.keys():
        if baseColors[cStatus][0] == baseData['colorStatus']:
            break
    # Меняем цвет

    baseStatusChanged(cStatus)

    # Назначаем кнопки управления уровнем тревоги
    window.butMinus1.clicked.connect(changeBaseScore)
    window.butMinus5.clicked.connect(changeBaseScore)
    window.butMinus10.clicked.connect(changeBaseScore)
    window.butPlus1.clicked.connect(changeBaseScore)
    window.butPlus5.clicked.connect(changeBaseScore)
    window.butPlus10.clicked.connect(changeBaseScore)

    # Выводим данные по замкам

    window.scrollLocksBox = QtWidgets.QGroupBox('')
    window.scrollLocksForm = QtWidgets.QVBoxLayout()
    for lockNum in lockOrder.keys():
        createLockFrame(lockNum,lockOrder[lockNum])
    window.scrollLocksBox.setLayout(window.scrollLocksForm)
    window.scrollLocks.setWidget(window.scrollLocksBox)
    window.scrollLocks.setWidgetResizable(True)





    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()