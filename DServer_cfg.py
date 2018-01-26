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

numTerms = 0

termWindow = dict()
termWindowConf = dict()
termWindowConfOpen = dict()
termWinMenuFrame = dict()
termWinMenuLabel = dict()
termWinBodyFrame = dict()
termWinBodyLabel = dict()
termWinBodyHeadFrame = dict()
termWinBodyHead = dict()
termWinBodyText = dict()
termWinBodyScroll = dict()
termWinButton = dict()
termWinMListBL = dict()
termWinMListBA = dict()
termWinMListBT = dict()
termWinMListButtonLock = dict()
termWinMListButtonAlert = dict()
termWinMListButtonText = dict()
termWinLockFrame = dict()
termWinLockLabel = dict()
termWinLockName = dict()

# JSON представление терминалов
# {"Имя терминала 1":{"IPAddr":"ИП адрес терминала 1","isPowerOn":"True", "isLocked":"False",
#                     "isHacked":"False", "isLockOpen":"False", "isLevelDown":"False",
#                     "attempts":4, "wordLength":8, "wordsPrinted":10,
#                     "menuList":"1,2,3", "msgHead":"Заголовок текста",
#                     "msgBody":"Большой и длинный текст"},
# "Имя терминала 2":{"IPAddr":"ИП адрес терминала 2","isPowerOn":"True", "isLocked":"False",
#                     "isHacked":"False", "isLockOpen":"False", "isLevelDown":"False",
#                     "attempts":4, "wordLength":8, "wordsPrinted":10,
#                     "menuList":"1,2,3", "msgHead":"Заголовок текста",
#                     "msgBody":"Большой и длинный текст"}}
#
termData = dict()

# JSON представление замков
# {"Имя замка 1":{"IPAddr":"ИП адрес замка 1","isSound":"True", "lockState":"closed",
#                     "baseState":"blue", codes:{"Номер карты или код 1":["blue","green","yellow"],
#                                                "Номер карты или код 2":["blue","green","yellow"]}},
#  "Имя замка 2":{"IPAddr":"ИП адрес замка 2","isSound":"True", "lockState":"closed",
#                     "baseState":"blue", codes:{"Номер карты или код 1":["blue","green","yellow"],
#                                                "Номер карты или код 2":["blue","green","yellow"]}}}
lockData = dict()


start_time = datetime.now()

def millis():
    dt = datetime.now() - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms

def terminalUpdateRequest(id):
    print (id)
    termWinButton[id].config(state=DISABLED)

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
    global termWindow
    i = 0
    for i in termWindow.keys():
        confirmClose(termWindow[i])
        print (i)

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
    req.execute("INSERT INTO IP_Id values(?,?,'TERM')", [IPAddr, termName.get()])
    conn.commit()
    req.execute("SELECT Id, Alive, Hack_Status, Lock_Status, Operation, \
                                Menulist, Id_lock, Msg_head, Msg_body \
                                from term_status, IP_Id \
                                WHERE term_status.Id == IP_Id.IDObj \
                                AND  Ip_ID.TypeOBJ == 'TERM' \
                                AND  Ip_ID.IDObj == ? \
                                ORDER BY term_status.Id", [termName.get()])
    if (req.rowcount == -1):  # Объект не описан, надо запросить данные и сбросить терминал в нулевое состояние
        client.publish('TERM', IPAddr + '/RESETDB')
        time.sleep(1)
        client.publish('TERM', IPAddr + '/GETDB')
    else: # Объект описан, вкачиваем в него данные с базы сервера:
        row = req.fetchone()
        client.publish('TERM', IPAddr + '/RESETDB')
        time.sleep(1)
        client.publish('TERM', IPAddr + '/LOCK/' + row[3])
        time.sleep(0.1)
        client.publish('TERM', IPAddr + '/HACK/' + row[2])
        time.sleep(0.1)
        client.publish('TERM', IPAddr + '/MENULIST/' + row[5])
        time.sleep(0.1)
        client.publish('TERM', IPAddr + '/MAILHEAD/' + row[7])
        time.sleep(0.1)
        client.publish('TERM', IPAddr + '/MAILHEAD/' + row[8])
    conn.close()
    confirmClose(termWindowConf[IPAddr])
    termWindowConfOpen[IPAddr] = 0

def termWindowOpen(id, mList, bHead, bText, idLock):
    termWindow[id] = Toplevel()
    termWindow[id].title(u'Терминал ' + id)
    termWinMenuFrame[id] = Frame(termWindow[id])
    termWinMenuLabel[id] = Label(termWinMenuFrame[id], text=u'Пункты меню: ')
    termWinMenuLabel[id].grid(row=0, column=0, sticky=E)
    termWinMListBL[id] = StringVar()
    termWinMListBA[id] = StringVar()
    termWinMListBT[id] = StringVar()
    termWinMListButtonLock[id] = Checkbutton(termWinMenuFrame[id], text='Замок', \
                                           variable=termWinMListBL[id], \
                                           onvalue="1,", offvalue="")
    termWinMListButtonAlert[id] = Checkbutton(termWinMenuFrame[id], text='Тревога', \
                                            variable=termWinMListBA[id], \
                                            onvalue="2,", offvalue="")
    termWinMListButtonText[id] = Checkbutton(termWinMenuFrame[id], text='Текст', \
                                           variable=termWinMListBT[id], \
                                           onvalue="3,", offvalue="")
    tmplist = mList.split(",")
    if "1" in tmplist:
        termWinMListButtonLock[id].select()
    if "2" in tmplist:
        termWinMListButtonAlert[id].select()
    if "3" in tmplist:
        termWinMListButtonText[id].select()
    termWinMListButtonLock[id].grid(row=0, column=1, sticky=E)
    termWinMListButtonAlert[id].grid(row=0, column=2, sticky=E)
    termWinMListButtonText[id].grid(row=0, column=3, sticky=E)
    termWinMenuFrame[id].grid(row=1, column=0, columnspan=4)
    termWinLockFrame[id] = Frame(termWindow[id])
    termWinLockLabel[id] = Label(termWinLockFrame[id], text=u'Имя связанного замка: ')
    termWinLockName[id] = Entry(termWinLockFrame[id], width=50)
    termWinLockName[id].insert(0, idLock)
    termWinLockLabel[id].grid(row=0, column=0, sticky=W)
    termWinLockName[id].grid(row=0, column=1, sticky=E)
    termWinLockFrame[id].grid(row=2, column=0, columnspan=4)
    termWinBodyHeadFrame[id] = Frame(termWindow[id])
    termWinBodyLabel[id] = Label(termWinBodyHeadFrame[id], text=u'Заголовок: ')
    termWinBodyLabel[id].grid(row=0, column=0, sticky=W)
    termWinBodyHead[id] = Entry(termWinBodyHeadFrame[id], width=50)
    termWinBodyHead[id].insert(0, bHead)
    termWinBodyHead[id].grid(row=0, column=1, sticky=E)
    termWinBodyHeadFrame[id].grid(row=3, column=0, columnspan=4)
    termWinBodyFrame[id] = Frame(termWindow[id])
    termWinBodyText[id] = Text(termWinBodyFrame[id], width=62, height=10, wrap=WORD, font='arial 8')
    termWinBodyText[id].insert(END, bText)
    termWinBodyText[id].grid(row=1, column=0, sticky=W)
    termWinBodyScroll[id] = Scrollbar(termWinBodyFrame[id], command=termWinBodyText[id].yview)
    termWinBodyScroll[id].grid(row=1, column=1, sticky=N + S)
    termWinBodyFrame[id].grid(row=4, column=0, columnspan=4)
    termWinButton[id] = Button(termWindow[id], text=u'Применить!', width=50, \
                             command=lambda id=id: terminalUpdateRequest(id))
    termWinButton[id].grid(row=5, column=0, columnspan=4)


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
        termWindowOpen(row[0], row[5], row[7], row[8], row[6])
    conn.close()

def configCompleteInit():
    readTermMenuText()

def confWindowsInit():
    root = Tk()
    root.title(u'Сброс базы сервера')
    root.geometry('240x80')
    configComplete = Button(root, text='Завершить конфигурирование устройств!', \
                      command=lambda : configCompleteInit())
    resetAll = Button(root, text='Сбросить всю базу!', \
                      command=lambda : dbResetAllConfirm())
    resetOper = Button(root, text='Сбросить оперативные данные!', \
                       command=lambda: dbResetOperConfirm())
    configComplete.grid(row=0, column=0)
    resetAll.grid(row=1, column=0)
    resetOper.grid(row=2, column=0)
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
    try:  # Пробуем соединиться с сервером
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

