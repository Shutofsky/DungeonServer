# -*- coding: utf-8 -*-
from tkinter import *
import paho.mqtt.client as mqtt
import socket, sqlite3, time
from datetime import datetime
from datetime import timedelta
import threading
#import image
#import Image
import time

dbName = 'DungeonStatus.db'
mqtt_broker_ip = '10.23.192.193'
mqtt_broker_port = 1883
mqttFlag = 0

termWindow = []
termWindowConf = dict()
termWindowConfOpen = dict()
menuFrame = []
menuLabel = []
bodyFrame = []
bodyLabel = []
bodyHeadFrame = []
bodyHead = []
bodyText = []
bodyScroll = []
termButton = []
numTerms = 0
termMListBL = []
termMListBA = []
termMListBT = []
termMListButtonLock = []
termMListButtonAlert = []
termMListButtonText = []

start_time = datetime.now()
def millis():
    dt = datetime.now() - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms

def terminalUpdateRequest(num,id):
    print (num)
    print (id)
    termButton[num].config(state=DISABLED)

def confirmClose(winID):
    winID.destroy()

def dbResetAll(winID):
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("DELETE from term_status")
    req.execute("DELETE from term_action")
    req.execute("DELETE from lock_status")
    req.execute("DELETE from lock_action")
    req.execute("DELETE from lock_log")
    req.execute("DELETE from base_action")
    req.execute("UPDATE base_status SET Current_status = 'blue'")
    req.execute("UPDATE base_status SET Alarm_level = 0 ")
    conn.commit()
    conn.close()
    confirmClose(winID)
    closeAllTermWin()

def dbResetOper(winID):
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("DELETE from term_action")
    req.execute("DELETE from lock_action")
    req.execute("DELETE from base_action")
    req.execute("UPDATE base_status SET Current_status = 'blue'")
    req.execute("UPDATE base_status SET Alarm_level = 0 ")
    conn.commit()
    conn.close()
    confirmClose(winID)

def dbResetAllConfirm():
    dbResetAllConfirmW = Toplevel()
    confirmLabel = Label(dbResetAllConfirmW, text=u'Стереть ВСЁ содержимое базы, включая тексты. Вы уверены?')
    confirmYes = Button(dbResetAllConfirmW, text=u'Да, стереть!', \
                        command = lambda tmpW = dbResetAllConfirmW : dbResetAll(tmpW))
    confirmNo = Button(dbResetAllConfirmW, text=u'Нет! Отменить стирание!', \
                       command = lambda tmpW = dbResetAllConfirmW : confirmClose(tmpW))
    confirmLabel.grid(row=0, column=0, columnspan=2)
    confirmYes.grid(row=1, column=0)
    confirmNo.grid(row=1, column=1)

def dbResetOperConfirm():
    dbResetOperConfirmW = Toplevel()
    confirmLabel = Label(dbResetOperConfirmW, text=u'Стереть оперативное содержимое базы. Вы уверены?')
    confirmYes = Button(dbResetOperConfirmW, text=u'Да, стереть!', \
                        command = lambda tmpW = dbResetOperConfirmW : dbResetOper(tmpW))
    confirmNo = Button(dbResetOperConfirmW, text=u'Нет! Отменить стирание!', \
                       command = lambda tmpW = dbResetOperConfirmW : confirmClose(tmpW))
    confirmLabel.grid(row=0, column=0, columnspan=2)
    confirmYes.grid(row=1, column=0)
    confirmNo.grid(row=1, column=1)

def closeAllTermWin():
    global numTerms
    global termWindow
    i = 0
    while i < numTerms:
        confirmClose(termWindow[i])
        print (i)
        i += 1
    numTerms = 0

def termWindowConfInit(IPAddr):
    termWindowConfOpen[IPAddr] = 1
    termWindowConf[IPAddr] = Toplevel()
    termWindowConf[IPAddr].title(u'Терминал ' + IPAddr)
    termConfLabel = Label(termWindowConf[IPAddr], text = u'Для терминала с адресом ' + \
                  IPAddr + u'укажите имя:')
    termConfEntry = Entry(termWindowConf[IPAddr], width = 50)
    termConfButton = Button(termWindowConf[IPAddr], text = u'Назначить имя', \
                            command = lambda ip = IPAddr, termName = termConfEntry: \
                                        termWindowConfClose(ip, termName))
    termConfLabel.grid(row=0, column=0)
    termConfEntry.grid(row=0, column=1)
    termConfButton.grid(row=1, column=0, columnspan=2)


def termWindowConfClose(IPAddr, termName):
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("INSERT INTO IP_Id values(?,?,'TERM')",[IPAddr,termName.get()])
    conn.commit()
    conn.close()
    confirmClose(termWindowConf[IPAddr])
    termWindowConfOpen[IPAddr] = 0

def readTermMenuText():
    global numTerms
    i = 0
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    # Работаем с ID только для терминалов, которые уже зарегистрированы.
    for row in req.execute("SELECT Id, Alive, Hack_Status, Lock_Status, Operation, \
                                Menulist, Id_lock, Msg_head, Msg_body \
                                from term_status, IP_Id \
                                WHERE term_status.Id == IP_Id.IDObj AND \
                                Ip_ID.TypeOBJ== 'TERM' \
                                ORDER BY term_status.Id"):
        termWindow.append(Toplevel())
        headTitle = u'Терминал ' + row[0]
        termWindow[i].title(headTitle)
        menuFrame.append(Frame(termWindow[i]))
        menuLabel.append(Label(menuFrame[i], text=u'Пункты меню: '))
        menuLabel[i].grid(row=0, column=0, sticky=E)
        termMListBL.append(StringVar())
        termMListBA.append(StringVar())
        termMListBT.append(StringVar())
        termMListButtonLock.append(Checkbutton(menuFrame[i], text='Замок', \
                                               variable=termMListBL[i], \
                                               onvalue="1,", offvalue=""))
        termMListButtonAlert.append(Checkbutton(menuFrame[i], text='Тревога', \
                                                variable=termMListBA[i], \
                                                onvalue="2,", offvalue=""))
        termMListButtonText.append(Checkbutton(menuFrame[i], text='Текст', \
                                               variable=termMListBT[i], \
                                               onvalue="3,", offvalue=""))
        tmplist = row[5].split(",")
        if "1" in tmplist:
            termMListButtonLock[i].select()
        if "2" in tmplist:
            termMListButtonAlert[i].select()
        if "3" in tmplist:
            termMListButtonText[i].select()
        termMListButtonLock[i].grid(row=0, column=1, sticky=E)
        termMListButtonAlert[i].grid(row=0, column=2, sticky=E)
        termMListButtonText[i].grid(row=0, column=3, sticky=E)
        menuFrame[i].grid(row=1, column=0, columnspan=4)

        bodyHeadFrame.append(Frame(termWindow[i]))
        bodyLabel.append(Label(bodyHeadFrame[i], text=u'Заголовок: '))
        bodyLabel[i].grid(row=0, column=0, sticky=W)
        bodyHead.append(Entry(bodyHeadFrame[i], width=50))
        bodyHead[i].insert(0, row[7])
        bodyHead[i].grid(row=0, column=1, sticky=E)
        bodyHeadFrame[i].grid(row=2, column=0, columnspan=4)
        bodyFrame.append(Frame(termWindow[i]))
        bodyText.append(Text(bodyFrame[i], width=62, height=10, wrap=WORD, font='arial 8'))
        bodyText[i].insert(END, row[8])
        bodyText[i].grid(row=1,column=0, sticky=W)
        bodyScroll.append(Scrollbar(bodyFrame[i], command=bodyText[i].yview))
        bodyScroll[i].grid(row=1, column=1, sticky=N+S)
        bodyFrame[i].grid(row=3, column=0, columnspan=4)
        termButton.append(Button(termWindow[i], text=u'Применить!', width=50, \
                                 command=lambda num=i, ip=row[0]: terminalUpdateRequest(num, ip)))
        termButton[i].grid(row=4, column=0, columnspan=4)
        i += 1
    numTerms = i
    print(numTerms)
    conn.close()

def confWindowsInit():
    root = Tk()
    root.title(u'Сброс базы сервера')
    root.geometry('160x80')
    resetAll = Button(root, text='Сбросить всю базу!', \
                      command=lambda : dbResetAllConfirm())
    resetOper = Button(root, text='Сбросить оперативные данные!', \
                       command=lambda: dbResetOperConfirm())
    resetAll.grid(row=0, column=0)
    resetOper.grid(row=1, column=0)
    readTermMenuText()
    root.mainloop()

def on_connect(client, userdata, flags, rc):
    client.subscribe("TERMASK/#")    # Подписка на канал TERMASK
    client.subscribe("LOCKASK/#")    # Подписка на канал LOCKASK
    client.subscribe("RGBASK/#")     # Подписка на канал LOCKASK

def on_message(client, userdata, msg):
    commList = msg.payload.decode('utf-8').split('/')  # Разделяем тело сообщения на элементы списка по знаку /
    # commList[0] - IP-адрес устройства, и т.д.
    if msg.topic == 'TERMASK':
#        print(msg.payload)
        print (commList[0])
        print (commList[1])
        conn = sqlite3.connect(dbName)
        req = conn.cursor()
        if (commList[1] == 'PONG'): # Ответ на проверку доступности
            req.execute("SELECT Id, Alive \
                         FROM term_status, IP_Id \
                         WHERE term_status.Id == IP_Id.IDObj \
                         AND Ip_ID.TypeOBJ == 'TERM' \
                         AND IP_ID.IPAddr == ? \
                         ORDER BY term_status.Id",[commList[0]])
            row = req.fetchall()
            print(req.rowcount)
            if (req.rowcount == -1):   # Объект не описан
                if (commList[0] not in termWindowConfOpen.keys()): # Окно ещё не открывали
                    termWindowConfInit(commList[0])
            else:           # Объект описан, обновляем время опроса
                if (termWindowConfOpen[commList[0]!=1]): # Терминал УЖЕ поименован
                    req.execute("UPDATE term_status SET Alive = ? WHERE Id == ?",
                                [millis(),row[0]])
                    conn.commit()
        conn.close()
        # Здесь должна быть обработка сообщений для канала TERMASK
    elif msg.topic == 'LOCKASK':
        print(msg.payload)
	# Здесь должна быть обработка сообщений для канала LOCKASK
    elif msg.topic == 'RGBASK':
        print(msg.payload)
	# Здесь должна быть обработка сообщений для канала RGBASK

def mqttConnInit():
    try:  # Продбуем соединиться с сервером
        client.connect(mqtt_broker_ip, mqtt_broker_port, 5)	# Соединяемся с сервtром. Адрес, порт, таймаут попытки.
    except BaseException:
        # Соединение не удалось!
        mqttFlag = 0
    else:
        # Соединение успешно.
        mqttFlag = 1
        client.loop_start() # Клиентский цикл запустили - реконнект при разрыв связи и работа обработчика сообщений
    while mqttFlag :
        client.publish('TERM', "*/PING") # Запрос PING для всех терминалов (канал TERM)
        client.publish('LOCK', "*/PING") # Запрос PING для всех замков (канал LOCK)
        client.publish('RGB', "*/PING")  # Запрос PING для всех светильников (канал RGB)
        time.sleep(1) # Пауза одна секунда

client = mqtt.Client()   	# Создаём объект типа MQTT Client
client.on_connect = on_connect	# Привязываем функцию для исполнения при успешном соединении с сервером
client.on_message = on_message	# Привязываем функцию для исполнения при приходе сообщения в любом из подписанных каналов

confWindows = threading.Thread(name='confWindows', \
                               target=confWindowsInit)

mqttConn = threading.Thread(name='mqttConn', \
                               target=mqttConnInit)

mqttConn.start()
confWindows.start()

