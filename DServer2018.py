#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DSQT2018.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!


import sys
from datetime import datetime
from datetime import timedelta
import time
import threading
import sqlite3
import paho.mqtt.client as mqtt
import json
from PyQt5 import QtCore, QtGui, QtWidgets, uic

# Настройки MQTT

#mqtt_broker_ip = '192.168.0.200'
mqtt_broker_ip = '10.23.192.193'
mqtt_broker_port = 1883
mqttFlag = False

dbName = 'DungeonStatus.db'

# Описание рабочих структур данных

alarmValue = 0
baseColors = dict()
baseData = dict()
baseCommand = dict()

lockData = dict()
lockCode = dict()
lockOrder = dict()
lockIPtoName = dict()
lockNameToNum = dict()
cardNames = dict()

termData = dict()
termOrder = dict()
termIPtoName = dict()
termNameToNum = dict()

def onMessage(client, userdata, msg):
    global lockData
    global lockWinFrames
    global lockIPtoName
    global baseColors
    global baseData
    global baseWinFrame
    print(msg.payload.decode('utf-8'))
    commList = msg.payload.decode('utf-8').split('/')  # Разделяем тело сообщения на элементы списка по знаку /
    print(commList[1])

def onConnect(client, userdata, flags, rc):
    global mqttFlag
    if rc == 0:
        mqttFlag = True  # set flag
        addTextLog('Соединение с MQTT брокером ' + mqtt_broker_ip + ' успешно. Обработка сообщений начата.')
    else:
        addTextLog('Соединение с MQTT брокером ' + mqtt_broker_ip + ' не удалось!')
    client.subscribe("TERMASK/#")    # Подписка на канал TERMASK
    client.subscribe("LOCKASK/#")    # Подписка на канал LOCKASK
    client.subscribe("RGBASK/#")     # Подписка на канал RGBASK
    client.subscribe("PWRASK/#")     # Подписка на канал RGBASK

def onDisonnect(client, userdata, flags, rc):
    global mqttFlag
    mqttFlag = False
    addTextLog('Соединение с MQTT брокером ' + mqtt_broker_ip + ' разорвано!')

def addTextLog(logString):
    dt = datetime.now()
    window.logWindow.insertPlainText(dt.strftime("%d %b %y %H:%M:%S") + ' : ' + logString + '\n')

def getButonByName(name):
    print(name)
    widgets = QtWidgets.QApplication.allWidgets()
    for x in widgets:
        if str(x.objectName()) == name:
            return x

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
    global lockNameToNum
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
        lockNameToNum[row[1]] = row[0]
    conn.close()

def readTermData():
    global termData
    global termOrder
    global termIPtoName
    jsStr = '{'
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT name, IPAddr, isPowerOn, isLocked, isHacked, \
                                isLockOpen, isLevelDown, attempts, wordLength, \
                                wordsPrinted, menuList, msgHead, msgBody, lockName  \
                                FROM termStatus \
                                ORDER BY name"):
        jsStr += '"'+row[0]+'":{"IPAddr":"'+row[1]+'","isPowerOn":"'+row[2]+'","isLocked":"'+row[3]+ \
                 '","isHacked":"'+row[4]+'","isLockOpen":"'+row[5]+'","isLevelDown":"'+row[6]+\
                 '","attempts":'+str(row[7])+',"wordLength":'+str(row[8])+',"wordsPrinted":'+str(row[9])+\
                 ',"menuList":"'+row[10]+'","msgHead":"'+row[11]+'","msgBody":"'+ \
                 row[12].replace('"','\\"').replace('\n', '\\"n\\"')+\
                 '","lockName":"'+row[13]+'","isAlive":"False","aliveTimeStamp":0},'
        termIPtoName[row[1]] = row[0]
    jsStr = jsStr.rstrip(',') + '}'
    print (jsStr)
    termData = json.loads(jsStr)
    for row in req.execute("SELECT * FROM termOrder ORDER BY termNumber"):
        termOrder[row[0]] = row[1]
        termNameToNum[row[1]] = row[0]
    conn.close()

def lockIPChange():
    doc = QtGui.QTextDocument()
    doc.setHtml(window.lockNameExpand.text())
    lockName = doc.toPlainText()
    lockIP = window.entryIPAddrLock.text()
    updateLockParm(lockName, 'IPAddr', lockIP)

def lockStateChange():
    global lockData
    global lockOrder
    sender = window.sender()
    butName = sender.objectName()
    (bName, bNum) = butName.split('_')
    lockName = lockOrder[int(bNum)]
    if bName == 'butState':
        parmName = 'lockState'
        if lockData[lockName][parmName] == 'opened':
            parmVal = 'closed'
            bgColor = 'lightgreen'
            sender.setText('Открыть')
        elif lockData[lockName][parmName] == 'closed':
            parmVal = 'opened'
            bgColor = '#FF8080'
            sender.setText('Закрыть')
        sender.setStyleSheet("QPushButton:hover { background-color: " + bgColor + " }")
        sender.setStyleSheet("QPushButton:!hover { background-color: " + bgColor + " }")
    elif bName == 'butBlock':
        parmName = 'lockState'
        bState = getButonByName('butState_' + str(bNum))
        bgColor = 'lightgreen'
        bState.setStyleSheet("QPushButton:hover { background-color: " + bgColor + " }")
        bState.setStyleSheet("QPushButton:!hover { background-color: " + bgColor + " }")
        bState.setText('Открыть')
        if lockData[lockName][parmName] == 'blocked':
            bState.setDisabled(False)
            bgColor = 'lightgreen'
            parmVal = 'closed'
            sender.setText('Заблокировать')
        else:
            bState.setDisabled(True)
            bgColor = '#FF8080'
            parmVal = 'blocked'
            sender.setText('Разблокировать')
        sender.setStyleSheet("QPushButton:hover { background-color: " + bgColor + " }")
        sender.setStyleSheet("QPushButton:!hover { background-color: " + bgColor + " }")
    else:
        parmName = 'isSound'
        if lockData[lockName][parmName] == 'True':
            bgColor = '#FF8080'
            parmVal = 'False'
            sender.setText('Звук ВКЛ')
        else:
            bgColor = 'lightgreen'
            parmVal = 'True'
            sender.setText('Звук ВЫКЛ')
        sender.setStyleSheet("QPushButton:hover { background-color: " + bgColor + " }")
        sender.setStyleSheet("QPushButton:!hover { background-color: " + bgColor + " }")
    updateLockParm(lockName, parmName, parmVal)

def lockCardChange():
    sender = window.sender()
    butName = sender.objectName()
    (bName, cardCode, colorCode) = butName.split('_')
    lockName = window.lockNameExpand.text()
    if sender.checkState():
        mode = 'True'
    else:
        mode = 'False'
    updateLockCard(lockName, cardCode, colorCode, mode)

def updateLockCard(lockName, cardCode, colorCode, mode):
    global lockData
    global baseColors
    global dbName
    global mqttFlag
    colorName = baseColors[colorCode][0]
    print(lockName, cardCode, colorCode, colorName)
    IPAddr = lockData[lockName]['IPAddr']
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    if cardCode not in lockData[lockName]['codes'].keys():
        # MQTT sending here
        # client.publish("LOCK", IPAddr + "/ADDID/"+card+"/"+color)
        req.execute("INSERT INTO lockCodes VALUES(?,?,?)", [lockName, cardCode, colorName])
        lockData[lockName]['codes'][cardCode] = [colorName]
        conn.commit()
        conn.close()
        return()
    else:
        colorList = list(lockData[lockName]['codes'][cardCode])
        newColorList = []
        if mode == 'True':
            print(colorList)
            colorList.append(str(colorName))
        else:
            colorList.remove(str(colorName))
        for col in colorList:
            newColorList.append(col.strip())
        if len(newColorList) == 0:
            # MQTT sending here
            # client.publish("LOCK", IPAddr + "/DELID/" + cardCode)
            req.execute("DELETE FROM lockCodes WHERE lockName = ? AND cardNumber = ?", \
                        [lockName, cardCode])
            conn.commit()
            del(lockData[lockName]['codes'][cardCode])
            return()
        addColorList = []
        for numColor in baseColors.keys():
            if baseColors[numColor][0] in newColorList:
                addColorList.append(str(baseColors[numColor][0]))
        # MQTT sending here
        # client.publish("LOCK", IPAddr + "/CHGID/" + cardCode + "/" + ','.join(addColorList))
        req.execute("UPDATE lockCodes SET stateList = ? WHERE lockName = ? AND cardNumber = ?", \
                    [','.join(addColorList), lockName, cardCode])
        lockData[lockName]['codes'][cardCode] = addColorList
        conn.commit()
    conn.close()

def updateLockParm(lockName,parName,parValue):
    global dbName
    global lockData
    global lockIPtoName
    global mqttFlag
    IPAddr = lockData[lockName]['IPAddr']
    lockData[lockName][parName] = parValue
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    reqStr = "UPDATE lockStatus SET "+parName+" = ? WHERE name = ?"
    print (reqStr)
    req.execute(reqStr,[str(parValue),str(lockName)])
    conn.commit()
    conn.close()
    if parName=='IPAddr':
        del(lockIPtoName[IPAddr])
        lockIPtoName[parValue] = lockName
        return
    # mqtt добавить
    jStr = '{"' + parName + '":"' + parValue + '"}'
    print(jStr)
    if mqttFlag:
        client.publish("LOCK", IPAddr + "/SETPARMS/" + jStr)
    else:
        addTextLog('Нет связи с брокером MQTT ' + mqtt_broker_ip + '!')

    print(IPAddr)

def termIPChange():
    doc = QtGui.QTextDocument()
    doc.setHtml(window.termNameExp.text())
    termName = doc.toPlainText()
    termIP = window.entryIPAddrTerm.text()
    termIPChanged(termName, termIP)

def termIPChanged(termName,termIP):
    print("Смена ИП адреса " + termIP + " у терминала "+termName)

def termExpand():
    sender = window.sender()
    bName = sender.objectName()
    termNum = int((bName.split('_'))[1])
    termName = termOrder[termNum]
    termExpanded(termName)

def termExpanded(termName):
    global lockOrder
    global termOrder
    global termData
    window.termNameExp.setText(termName)
    window.entryIPAddrTerm.setText(termData[termName]['IPAddr'])

    if '1' in termData[termName]['menuList'].split(','):
        window.checkLockTerm.setChecked(True)
    else:
        window.checkLockTerm.setChecked(False)
    if '2' in termData[termName]['menuList'].split(','):
        window.checkAlarmTerm.setChecked(True)
    else:
        window.checkAlarmTerm.setChecked(False)
    if '3' in termData[termName]['menuList'].split(','):
        window.checkTextTerm.setChecked(True)
    else:
        window.checkTextTerm.setChecked(False)

    # window.checkLockTerm.clicked.connect()
    # window.checkAlarmTerm.clicked.connect()
    # window.checkTextTerm.clicked.connect()

    window.termWordPrint.setCurrentIndex(window.termWordPrint.findText(str(termData[termName]['wordsPrinted'])))
    # window.termWordPrint.activated.connect(функция смены параметров)
    window.termWordLength.setCurrentIndex(window.termWordLength.findText(str(termData[termName]['wordLength'])))
    # window.termWordPrint.activated.connect(функция смены параметров)

    for i in lockOrder.keys():
        window.termLockLink.addItem(lockOrder[i])
    window.termLockLink.setCurrentIndex(window.termLockLink.findText(str(termData[termName]['lockName'])))
    # window.termLockLink.activated.connect(функция смены параметров)

    window.entryMsgHead.setText(termData[termName]['msgHead'])
    window.editMsgBody.insertPlainText(termData[termName]['msgBody'].replace('"n"','\n').replace('\\"','"'))
    window.editMsgBody.moveCursor(QtGui.QTextCursor.Start,QtGui.QTextCursor.MoveAnchor)
    # window.butMsgEdit.clicked.connect(функция обновления текста)

def createTermFrame(termNum,termName):
    global termData
    global termOrder
    global termIPtoName
    global window
    window.frame = QtWidgets.QFrame()
    window.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    window.frame.setFrameShadow(QtWidgets.QFrame.Raised)
    window.frame.setGeometry(QtCore.QRect(10, 10, 390, 70))
    window.frame.setFixedHeight(70)
    window.frame.setMaximumHeight(70)
    window.termName = QtWidgets.QLabel(window.frame)
    window.termName.setText(termName)
    font = QtGui.QFont()
    font.setPointSize(10)
    font.setBold(True)
    font.setWeight(75)
    window.termName.setFont(font)
    if termData[termName]['isAlive'] == 'True':
        fgColor = 'green'
    else:
        fgColor = 'red'
    palette = window.termName.palette()
    palette.setColor(palette.WindowText, QtGui.QColor(fgColor))
    window.termName.setPalette(palette)
    window.termName.setObjectName(termName)
    if termData[termName]['isPowerOn'] == 'YES':
        powerText = 'Питание ВЫКЛ'
        bgPowerColor = 'lightgreen'
    else:
        powerText = 'Питание ВКЛ'
        bgPowerColor = '#FF8080'
    window.butPower = QtWidgets.QPushButton(window.frame)
    window.butPower.setGeometry(QtCore.QRect(0, 20, 95, 31))
    window.butPower.setText(powerText)
    window.butPower.setStyleSheet("QPushButton:hover { background-color: " + bgPowerColor + " }")
    window.butPower.setStyleSheet("QPushButton:!hover { background-color: " + bgPowerColor + " }")
    # Добавить коннект на обработку кнопки включить/выключить питание
    window.butState.setObjectName("butTPower_"+str(termNum))

    if termData[termName]['isHacked'] == 'YES':
        hackText = 'Отмена взлома'
        bgHackColor = '#FF8080'
    else:
        hackText = 'Взломать'
        bgHackColor = 'lightgreen'
    window.butHack = QtWidgets.QPushButton(window.frame)
    window.butHack.setGeometry(QtCore.QRect(100, 20, 90, 31))
    window.butHack.setText(hackText)
    window.butHack.setStyleSheet("QPushButton:hover { background-color: " + bgHackColor + " }")
    window.butHack.setStyleSheet("QPushButton:!hover { background-color: " + bgHackColor + " }")
    # Добавить коннект на обработку кнопки включить/выключить питание
    window.butState.setObjectName("butTHack_"+str(termNum))

    if termData[termName]['isLocked'] == 'YES':
        lockTText = 'Разблокировать'
        bgLockColor = '#FF8080'
    else:
        lockTText = 'Заблокировать'
        bgLockColor = 'lightgreen'
    window.butLock = QtWidgets.QPushButton(window.frame)
    window.butLock.setGeometry(QtCore.QRect(195, 20, 100, 31))
    window.butLock.setText(lockTText)
    window.butLock.setStyleSheet("QPushButton:hover { background-color: " + bgLockColor + " }")
    window.butLock.setStyleSheet("QPushButton:!hover { background-color: " + bgLockColor + " }")
    # Добавить коннект на обработку кнопки включить/выключить питание
    window.butState.setObjectName("butTLock_"+str(termNum))

    window.butExpand = QtWidgets.QPushButton(window.frame)
    window.butExpand.setGeometry(QtCore.QRect(300, 20, 70, 31))
    window.butExpand.setText("Подробнее")
    window.butExpand.clicked.connect(termExpand)
    window.butExpand.setObjectName("butTermExpand_"+str(termNum))
    window.frame.setObjectName("frameTLock" + str(termNum))
    window.scrollTermsWidget.layout().addWidget(window.frame)
    #window.scrollTermsForm.addWidget(window.frame)

def lockExpand():
    sender = window.sender()
    bName = sender.objectName()
    lockNum = int((bName.split('_'))[1])
    lockName = lockOrder[lockNum]
    lockExpanded(lockName)

def lockExpanded(lockName):
    window.lockNameExpand.setText(lockName)
    window.entryIPAddrLock.setText(lockData[lockName]['IPAddr'])
    # Очищаем окно (layout)
    for i in reversed(range(window.scrollCodesWidget.layout().count())):
        widgetToRemove = window.scrollCodesWidget.layout().itemAt(i).widget()
        window.scrollCodesWidget.layout().removeWidget(widgetToRemove)
        widgetToRemove.setParent(None)
    for idCode in cardNames.keys():
        window.frame = QtWidgets.QFrame()
        window.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        window.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        window.frame.setGeometry(QtCore.QRect(10, 10, 351, 21))
        window.frame.setFixedHeight(20)
        window.frame.setMaximumHeight(20)
        window.labCardName = QtWidgets.QLabel(window.frame)
        window.labCardName.setGeometry(QtCore.QRect(0, 0, 231, 21))
        window.labCardName.setText(str(cardNames[idCode]))
        window.labCardName.setObjectName("labCard_" + idCode)
        i = 1
        while i<6:
            window.checkBox = QtWidgets.QCheckBox(window.frame)
            window.checkBox.setGeometry(QtCore.QRect(230+19*i, 0, 17, 17))
            window.checkBox.setText("")
            bgColor=baseColors[str(i)][0]
            if (idCode not in lockData[lockName]['codes'].keys()) \
                    or (bgColor not in lockData[lockName]['codes'][idCode]):
                window.checkBox.setChecked(False)
            else:
                window.checkBox.setChecked(True)
            window.checkBox.setStyleSheet('background-color: ' + bgColor)
            window.checkBox.clicked.connect(lockCardChange)
            window.checkBox.setObjectName("checkBox_"+idCode+"_"+str(i))
            i = i + 1
        window.frame.setObjectName("frame_" + idCode)
        window.scrollCodesWidget.layout().addWidget(window.frame)

def createLockFrame(lockNum, lockName):
    global lockData
    global cardNames
    global lockOrder
    global lockIPtoName
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
    window.butState.clicked.connect(lockStateChange)
    window.butState.setObjectName("butState_" + str(lockNum))
    window.butBlock = QtWidgets.QPushButton(window.frame)
    window.butBlock.setGeometry(QtCore.QRect(90, 20, 101, 31))
    window.butBlock.setText(blockText)
    window.butBlock.setStyleSheet("QPushButton:hover { background-color: " + bgBlockColor + " }")
    window.butBlock.setStyleSheet("QPushButton:!hover { background-color: " + bgBlockColor + " }")
    window.butBlock.clicked.connect(lockStateChange)
    window.butBlock.setObjectName("butBlock_" + str(lockNum))
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
    window.butSound.setObjectName("butSound_" + str(lockNum))
    window.butSound.clicked.connect(lockStateChange)
    window.butExpand = QtWidgets.QPushButton(window.frame)
    window.butExpand.setGeometry(QtCore.QRect(280, 20, 71, 31))
    window.butExpand.setText("Подробнее")
    window.butExpand.clicked.connect(lockExpand)
    window.butExpand.setObjectName("butExpand_" + str(lockNum))
    window.frame.setObjectName("frameLock" + str(lockNum))
    window.scrollLocksWidget.layout().addWidget(window.frame)

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

# Инициализируем MQTT
client = mqtt.Client()  # Создаём объект типа MQTT Client
client.on_connect = onConnect  # Привязываем функцию для исполнения при успешном соединении с сервером
client.on_disconnect = onDisonnect  # Привязываем функцию для исполнения при обрыве связи
client.on_socket_close = onDisonnect
client.on_message = onMessage  # Привязываем функцию для исполнения при приходе сообщения в любом из подписанных каналов

class ExampleApp(QtWidgets.QMainWindow):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        super().__init__()
        uic.loadUi('DSQT2018.ui', self)
        self.baseStatusList.activated.connect(self.baseStatusUserChanged)
        self.butIPAddrTerm.clicked.connect(termIPChange)
        self.butIPAddrLock.clicked.connect(lockIPChange)

    def baseStatusUserChanged(self, value):
        changeBaseStatus(value)

class mqttThread(threading.Thread):
    def __init__(self, name='mqttThread'):
        self._stopevent = threading.Event( )
        self._sleepperiod = 1.0
        threading.Thread.__init__(self, name=name)
    def run(self):
        global mqttFlag
        global client
        while not self._stopevent.isSet( ):
            if not mqttFlag:
                client.loop_start()
                try:  # Пробуем соединиться с сервером
                    addTextLog('Устанавливаю соединение с MQTT брокером ' + mqtt_broker_ip + '...')
                    client.connect(mqtt_broker_ip, mqtt_broker_port)
                except BaseException:
                    # Соединение не удалось!
                    addTextLog('Соединение с MQTT брокером ' + mqtt_broker_ip + ' не удалось! Повтор через 5 сек.')
                    mqttFlag = False
                    time.sleep(4)
                else:
                    mqttFlag = True
                    client.loop_start()
                    time.sleep(2)
            else:
                client.publish('TERM', "*/PING")  # Запрос PING для всех терминалов (канал TERM)
                client.publish('LOCK', "*/PING")  # Запрос PING для всех замков (канал LOCK)
                client.publish('RGB', "*/PING")  # Запрос PING для всех светильников (канал RGB)
            self._stopevent.wait(self._sleepperiod)
    def join(self, timeout=None):
        self._stopevent.set( )
        threading.Thread.join(self, timeout)

def main():
    global window
    global dbName
    global app

    # Читаем данные из БД
    readColorData()     # Цвета
    readBaseData()      # Текущий статус базы
    readLockData()      # Замки
    readTermData()      # Терминалы

    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp

    # mqttConn = threading.Thread(name='mqttConn', target=mqttConnInit)
    mqttConn = mqttThread()
    # mqttConn = mqttThread(name='mqttConn', target=mqttConnInit)
    mqttConn.start()

    # mqttConnInit()

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

    for lockNum in lockOrder.keys():
        createLockFrame(lockNum,lockOrder[lockNum])
    lockExpanded(lockOrder[0])

    # Выводим данные по терминалам

    for termNum in termOrder.keys():
        createTermFrame(termNum,termOrder[termNum])
    termExpanded(termOrder[0])

    doc = window.logWindow.document()
    doc.setMaximumBlockCount(10)
#    i=0
#    while i<100:
#        #window.logWindow.insertHtml('<TABLE BORDER=0, WIDTH=100%>')
#        # window.logWindow.insertPlainText(repr(i) + '\n')
#        # window.logWindow.insertHtml('<HTML><BODY><P>Текст ' + str(i) + ' <BR></P></BODY></HTML>')
#        # window.logWindow.insertHtml('<TR><TD style="background-color:#FFFFFF">' + repr(i) + '</TD></TR>')
#        #window.logWindow.insertHtml('</TABLE>')
#        window.logWindow.insertPlainText('Текст ' + str(i) + '\n')
#        i+=1

    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение
    if (mqttConn.isAlive()):
        mqttConn.join()

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()