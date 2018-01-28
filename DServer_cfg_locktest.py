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
import json

dbName = 'DungeonStatus.db'
mqtt_broker_ip = '192.168.0.103'
mqtt_broker_port = 1883
mqttFlag = False

numLocks = 0

baseColors = dict()

# JSON представление замков
# {"Имя замка 1":{"IPAddr":"ИП адрес замка 1","isSound":"True", "lockState":"closed","isAlive":"True",
#           "aliveTimeStamp":12345,"baseState":"blue", codes:{"Номер карты или код 1":["blue","green","yellow"],
#                                                "Номер карты или код 2":["blue","green","yellow"]}},
#  "Имя замка 2":{"IPAddr":"ИП адрес замка 2","isSound":"True", "lockState":"closed",
#                     "baseState":"blue", codes:{"Номер карты или код 1":["blue","green","yellow"],
#                                                "Номер карты или код 2":["blue","green","yellow"]}}}
lockData = dict()
lockCode = dict()
lockWinFrames =  dict()
lockOrder = dict()
lockIPtoName = dict()
lockNewWin = dict()
cardNames = dict()

start_time = datetime.now()

def millis():
    dt = datetime.now() - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms

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
                        command=lambda tmpW=dbResetOperConfirmW: dbResetOper(tmpW))
    confirmNo = Button(dbResetOperConfirmW, text=u'Нет! Отменить стирание!', \
                       command = lambda tmpW = dbResetOperConfirmW : confirmClose(tmpW))
    confirmLabel.grid(row=0, column=0, columnspan=2)
    confirmYes.grid(row=1, column=0)
    confirmNo.grid(row=1, column=1)

def readColorData():
    global baseColors
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT * FROM dict ORDER BY Id"):
        baseColors[str(row[0])] = [row[1],row[2],row[3]]
    print(baseColors)
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
    for row in req.execute("SELECT * FROM lockOrder ORDER BY lockNumber"):
        lockOrder[row[0]] = row[1]
    conn.close()

def updateLockIP(name,newIP):
    global lockData
    global lockWinFrames
    global lockIPtoName
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("UPDATE lockStatus SET IPAddr = ? WHERE name = ?",[newIP.get(),name])
    conn.commit()
    conn.close()
    del(lockIPtoName[lockData[name]['IPAddr']])
    lockData[name]['IPAddr']=newIP.get()
    lockIPtoName[newIP.get()] = name

def updateLockSound(name,newState):
    global lockData
    global lockWinFrames
#    lockWinFrames[name]['butSoundOn'].config(state=DISABLED, bg='lightgray')
#    lockWinFrames[name]['butSoundOff'].config(state=DISABLED, bg='lightgray')
    if newState == 'True':
        # MQTT sending here
        client.publish('LOCK',lockWinFrames[name]['valIPAddr'].get() + \
                       '/SOUND')
        print (lockWinFrames[name]['valIPAddr'].get() + \
                       '/SOUND')
        lockWinFrames[name]['butSoundOn'].config(state=DISABLED, bg='lightgreen')
        lockWinFrames[name]['butSoundOff'].config(state=NORMAL, bg='lightgray')
    else:
        # MQTT sending here
        client.publish('LOCK',lockWinFrames[name]['valIPAddr'].get() + \
                       '/NOSOUND')
        print (lockWinFrames[name]['valIPAddr'].get() + \
                       '/NOSOUND')
        lockWinFrames[name]['butSoundOn'].config(state=NORMAL, bg='lightgray')
        lockWinFrames[name]['butSoundOff'].config(state=DISABLED, bg='red')
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("UPDATE lockStatus SET isSound = ? WHERE name = ?",[newState,name])
    conn.commit()
    conn.close()
    lockData[name]['isSound']=newState

def updateLockState(name, newState):
    global lockData
    global lockWinFrames
    ipAddr = lockData[name]['IPAddr']
    if newState == 'opened':
        # MQTT sending here
        client.publish("LOCK", ipAddr + "/OPEN")
        lockWinFrames[name]['butOpen'].config(state=DISABLED)
        lockWinFrames[name]['butClose'].config(state=DISABLED)
        lockWinFrames[name]['butBlock'].config(state=DISABLED)
    elif newState == 'closed':
        # MQTT sending here
        client.publish("LOCK", ipAddr + "/CLOSE")
        lockWinFrames[name]['butOpen'].config(state=DISABLED)
        lockWinFrames[name]['butClose'].config(state=DISABLED)
        lockWinFrames[name]['butBlock'].config(state=DISABLED)
    else:
        # MQTT sending here
        client.publish("LOCK", ipAddr + "/BLOCK")
        lockWinFrames[name]['butOpen'].config(state=DISABLED)
        lockWinFrames[name]['butClose'].config(state=DISABLED)
        lockWinFrames[name]['butBlock'].config(state=DISABLED)
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("UPDATE lockStatus SET lockState = ? WHERE name = ?",[newState,name])
    conn.commit()
    conn.close()
    lockData[name]['lockState']=newState

def updateLockCard(name,card,color,mode):
    global lockData
    global baseColors
    IPAddr = lockData[name]['IPAddr']
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    if card not in lockData[name]['codes'].keys():
        # MQTT sending here
        client.publish("LOCK", IPAddr + "/ADDID/"+card+"/"+color)
        req.execute("INSERT INTO lockCodes VALUES(?,?,?)", [name, card, color])
        lockData[name]['codes'][card] = [color]
        conn.commit()
        conn.close()
        return()
    else:
        colorList = list(lockData[name]['codes'][card])
        newColorList = []
        if mode.get() == 'True':
            colorList.append(color)
        else:
            colorList.remove(color)
        for col in colorList:
            newColorList.append(col.strip())
        if len(newColorList) == 0:
            # MQTT sending here
            client.publish("LOCK", IPAddr + "/DELID/" + card)
            req.execute("DELETE FROM lockCodes WHERE lockName = ? AND cardNumber = ?", \
                        [name, card])
            conn.commit()
            del(lockData[name]['codes'][card])
            return()
        addColorList = []
        for numColor in baseColors.keys():
            if baseColors[numColor][0] in newColorList:
                addColorList.append(str(baseColors[numColor][0]))
        # MQTT sending here
        client.publish("LOCK", IPAddr + "/CHGID/" + card + "/" + ','.join(addColorList))
        req.execute("UPDATE lockCodes SET stateList = ? WHERE lockName = ? AND cardNumber = ?", \
                    [','.join(addColorList), name, card])
        lockData[name]['codes'][card] = addColorList
        conn.commit()
    conn.close()

def bindLockIP(name, addr):
    lockWinFrames[lockOrder[name.curselection()[0]]]['valIPAddr'].delete(0, END)
    lockWinFrames[lockOrder[name.curselection()[0]]]['valIPAddr'].insert(0, addr)
    updateLockIP(lockOrder[name.curselection()[0]],lockWinFrames[lockOrder[name.curselection()[0]]]['valIPAddr'])
    newLockWindow.destroy()
    del(lockNewWin[addr])

def newLockWinCreate(IPAddr):
    global newLockWindow
    newLockWindow = Toplevel()
    lockNewWin[IPAddr] = dict()
    lockNewWin[IPAddr]['labMain'] = Label(newLockWindow, text = 'Обнаружен новый замок с адресом: '+IPAddr)
    lockNewWin[IPAddr]['listMainFrame'] = Frame(newLockWindow)
    lockNewWin[IPAddr]['newNameListScroll'] = Scrollbar(lockNewWin[IPAddr]['listMainFrame'], orient=VERTICAL)
    lockNewWin[IPAddr]['newNameList'] = Listbox(lockNewWin[IPAddr]['listMainFrame'], width=40, \
                                                height=3, selectmode = SINGLE, exportselection=0, \
                                                yscrollcommand = lockNewWin[IPAddr]['newNameListScroll'].set)
    lockNewWin[IPAddr]['newNameList'].delete(0, END)
    for lockNum in lockOrder.keys():
        lockNewWin[IPAddr]['newNameList'].insert(END, lockOrder[lockNum])
    lockNewWin[IPAddr]['newNameListScroll'].config(command=lockNewWin[IPAddr]['newNameList'].yview)
    lockNewWin[IPAddr]['newNameBut'] = Button(newLockWindow, text = u'Назначить имя из списка', \
            command = lambda \
            lockName = lockNewWin[IPAddr]['newNameList'], \
            lockAddr = IPAddr : bindLockIP(lockName, lockAddr))
    lockNewWin[IPAddr]['labMain'].grid(row = 0, column = 0)
    lockNewWin[IPAddr]['newNameList'].grid(row = 1, column = 0)
    lockNewWin[IPAddr]['newNameListScroll'].grid(row = 1, column = 1, sticky = W)
    lockNewWin[IPAddr]['newNameBut'].grid(row = 1, column = 2)
    lockNewWin[IPAddr]['listMainFrame'].grid(row = 1, column = 0)

def createLocksWindow():
    global lockData
    global cardNames
    global lockWinFrames
    global lockCode
    global lockOrder
    allLockWindow = Toplevel()
    colFrame = 0
    for lockNum in lockOrder.keys():
        lockName = lockOrder[lockNum]
        lockWinFrames[lockName] = dict()
        lockWinFrames[lockName]['mainLockFrame'] = Frame(allLockWindow, bd = 3, relief = SUNKEN)
        lockWinFrames[lockName]['labLockName'] = Label(lockWinFrames[lockName]['mainLockFrame'],\
                                                         text = lockName, font = (("Arial", 12, "bold")))
        lockWinFrames[lockName]['labLockName'].grid(row = 0, column = 0, columnspan = 2, sticky = W)
        if lockData[lockName]['isAlive'] == 'True':
            bgAlive = "green"
        else:
            bgAlive = "red"
        lockWinFrames[lockName]['labLockLive'] = Button(lockWinFrames[lockName]['mainLockFrame'], \
                                                        bg = bgAlive, state = DISABLED, text=u'    ')
        lockWinFrames[lockName]['labLockLive'].grid(row = 0, column = 2, sticky = E)
        lockWinFrames[lockName]['labIPAddr'] = Label(lockWinFrames[lockName]['mainLockFrame'], text=u'IP адрес: ')
        lockWinFrames[lockName]['labIPAddr'].grid(row = 1, column = 0, sticky = W)
        lockWinFrames[lockName]['valIPAddr'] = Entry(lockWinFrames[lockName]['mainLockFrame'], width = 16)
        lockWinFrames[lockName]['valIPAddr'].insert(0, lockData[lockName]['IPAddr'])
        lockWinFrames[lockName]['valIPAddr'].grid(row = 1, column = 1, sticky = W+E)
        lockWinFrames[lockName]['butIPAddr'] = Button(lockWinFrames[lockName]['mainLockFrame'], text=u'Сменить', \
                                                      command=lambda name=lockName, \
                                                        IPAddr=lockWinFrames[lockName]['valIPAddr'] : \
                                                        updateLockIP(name, IPAddr))
        lockWinFrames[lockName]['butIPAddr'].grid(row = 1, column = 2, sticky = E)
        lockWinFrames[lockName]['labSound'] = Label(lockWinFrames[lockName]['mainLockFrame'], text=u'Звук: ')
        lockWinFrames[lockName]['labSound'].grid(row = 2, column = 0, sticky = W)
        lockWinFrames[lockName]['butSoundOn'] = Button(lockWinFrames[lockName]['mainLockFrame'], \
                                                       text=u'Вкл', command=lambda name=lockName, state='True': \
                                                       updateLockSound(name, state))
        lockWinFrames[lockName]['butSoundOn'].grid(row=2, column=1)
        lockWinFrames[lockName]['butSoundOff'] = Button(lockWinFrames[lockName]['mainLockFrame'], \
                                                        text=u'Выкл', command=lambda name=lockName, state='False': \
                                                        updateLockSound(name, state))
        lockWinFrames[lockName]['butSoundOff'].grid(row=2, column=2)
        if lockData[lockName]['isSound'] == 'True':
            lockWinFrames[lockName]['butSoundOn'].config(state=DISABLED, bg='lightgreen')
            lockWinFrames[lockName]['butSoundOff'].config(state=NORMAL, bg='lightgray')
        else:
            lockWinFrames[lockName]['butSoundOn'].config(state=NORMAL, bg='lightgray')
            lockWinFrames[lockName]['butSoundOff'].config(state=DISABLED, bg='red')
        lockWinFrames[lockName]['butOpen'] = Button(lockWinFrames[lockName]['mainLockFrame'], \
                                                    text=u'Открыть', \
                                                    command=lambda name=lockName, state='opened': \
                                                        updateLockState(name, state))
        lockWinFrames[lockName]['butOpen'].grid(row=3, column=0)

        lockWinFrames[lockName]['butClose'] = Button(lockWinFrames[lockName]['mainLockFrame'], \
                                                     text=u'Закрыть', \
                                                     command=lambda name=lockName, state='closed': \
                                                         updateLockState(name, state))
        lockWinFrames[lockName]['butClose'].grid(row=3, column=1)
        lockWinFrames[lockName]['butBlock'] = Button(lockWinFrames[lockName]['mainLockFrame'], \
                                                     text=u'Блокировать', \
                                                     command=lambda name=lockName, state='blocked': \
                                                         updateLockState(name, state))
        lockWinFrames[lockName]['butBlock'].grid(row=3, column=2)
        if lockData[lockName]['lockState'] == 'opened':
            lockWinFrames[lockName]['butOpen'].config(state=DISABLED,bg="lightgreen")
            lockWinFrames[lockName]['butClose'].config(state=NORMAL,bg="lightgray")
            lockWinFrames[lockName]['butBlock'].config(state=NORMAL,bg="lightgray")
        elif lockData[lockName]['lockState'] == 'closed':
            lockWinFrames[lockName]['butOpen'].config(state=NORMAL,bg="lightgray")
            lockWinFrames[lockName]['butClose'].config(state=DISABLED,bg="lightgreen")
            lockWinFrames[lockName]['butBlock'].config(state=NORMAL,bg="lightgray")
        else:
            lockWinFrames[lockName]['butOpen'].config(state=NORMAL,bg="lightgray")
            lockWinFrames[lockName]['butClose'].config(state=NORMAL,bg="lightgray")
            lockWinFrames[lockName]['butBlock'].config(state=DISABLED,bg="lightgreen")
        if lockData[lockName]['isAlive'] == 'False':
            lockWinFrames[lockName]['butSoundOn'].config(state=DISABLED)
            lockWinFrames[lockName]['butSoundOff'].config(state=DISABLED)
            lockWinFrames[lockName]['butOpen'].config(state=DISABLED)
            lockWinFrames[lockName]['butClose'].config(state=DISABLED)
            lockWinFrames[lockName]['butBlock'].config(state=DISABLED)
        lockWinFrames[lockName]['codeFrame'] = dict()
        lockWinFrames[lockName]['codeFrame']['frame'] = Frame(lockWinFrames[lockName]['mainLockFrame'], \
                                                              bd = 1, relief = SUNKEN)
        lockCode[lockName] = dict()
        rowColor = 0
        for idCode in cardNames.keys():
            lockCode[lockName][idCode] = dict()
            i = 1
            while i<6:
                lockCode[lockName][idCode][baseColors[str(i)][0]] = StringVar()
                i += 1
        for idCode in cardNames.keys():
            lockWinFrames[lockName]['codeFrame']['lab' + idCode] = Label(lockWinFrames[lockName]['codeFrame']['frame'], \
                                                                         text=cardNames[idCode])
            lockWinFrames[lockName]['codeFrame']['lab' + idCode].grid(row = rowColor, column = 0, sticky = W)
            i = 1
            while i<6:
                lockWinFrames[lockName]['codeFrame']['but' + idCode + baseColors[str(i)][0]] = \
                    Checkbutton(lockWinFrames[lockName]['codeFrame']['frame'], \
                                variable = lockCode[lockName][idCode][baseColors[str(i)][0]], \
                                onvalue = 'True', offvalue = 'False', bg=baseColors[str(i)][0], \
                                command = lambda name = lockName, card = idCode, idcolor = baseColors[str(i)][0], \
                                mode = lockCode[lockName][idCode][baseColors[str(i)][0]] : \
                                    updateLockCard(name, card, idcolor, mode))
                if (idCode not in lockData[lockName]['codes'].keys()) \
                        or (baseColors[str(i)][0] not in lockData[lockName]['codes'][idCode]):
                    lockWinFrames[lockName]['codeFrame']['but' + idCode + baseColors[str(i)][0]].deselect()
                else:
                    lockWinFrames[lockName]['codeFrame']['but' + idCode + baseColors[str(i)][0]].select()
                lockWinFrames[lockName]['codeFrame']['but' + idCode + baseColors[str(i)][0]].grid(row = rowColor, \
                                                                                                  column = i, \
                                                                                                  sticky = N)
                if lockData[lockName]['isAlive'] == 'False':
                    lockWinFrames[lockName]['codeFrame']['but' + idCode + baseColors[str(i)][0]].config(state=DISABLED)
                i += 1
            rowColor += 1
        lockWinFrames[lockName]['codeFrame']['frame'].grid(row=4, columnspan = 3, sticky = W)
        lockWinFrames[lockName]['mainLockFrame'].grid(row = 0, column = colFrame, sticky = N+E)
        colFrame += 1

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
    readColorData()
    readLockData()
    createLocksWindow()
#    readTermMenuText()
    root.mainloop()

def onConnect(client, userdata, flags, rc):
    client.subscribe("TERMASK/#")    # Подписка на канал TERMASK
    client.subscribe("LOCKASK/#")    # Подписка на канал LOCKASK
    client.subscribe("RGBASK/#")     # Подписка на канал LOCKASK
    print ("Connected to MQTT!")

def onMessage(client, userdata, msg):
    global lockData
    global lockWinFrames
    global lockIPtoName
    global baseColors
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
        # Здесь должна быть обработка сообщений для канала LOCKASK
        if commList[0] not in lockIPtoName.keys():
            # Стукнулось неизвестное устройтство  - замок
            print (lockNewWin.keys())
            if commList[0] not in lockNewWin.keys():
                # Окно для этого устройства ещё не создано
                newLockWinCreate(commList[0])
        else:
            lockName = lockIPtoName[commList[0]]
            if commList[1] == 'PONG':
                lockData[lockName]['aliveTimeStamp'] = millis()
                if lockData[lockName]['isAlive'] == "False":
                    client.publish("LOCK",commList[0]+"/DELALLID")
                    for idCode in lockData[lockName]['codes'].keys():
                        client.publish("LOCK", commList[0] + "/ADDID/"+idCode+"/"+ \
                                               ','.join(lockData[lockName]['codes'][idCode]))
                    jsStr = '{'
                    for parName in lockData[lockName].keys():
                        if parName != 'codes' and parName != 'isAlive' \
                                and parName != 'aliveTimeStamp' and parName!='IPAddr':
                            jsStr += '"'+parName+'":"'+lockData[lockName][parName]+'",'
                    jsStr = jsStr.rstrip(',') + "}"
                    client.publish("LOCK",commList[0]+"/SETPARMS/"+jsStr)
                    lockData[lockName]['isAlive'] = "True"
                    lockWinFrames[lockName]['labLockLive'].config(bg="green")
                    if lockData[lockName]['isSound'] == 'True':
                        lockWinFrames[lockName]['butSoundOn'].config(state=DISABLED)
                        lockWinFrames[lockName]['butSoundOff'].config(state=NORMAL)
                    else:
                        lockWinFrames[lockName]['butSoundOn'].config(state=NORMAL)
                        lockWinFrames[lockName]['butSoundOff'].config(state=DISABLED)
                    if lockData[lockName]['lockState'] == 'closed':
                        lockWinFrames[lockName]['butOpen'].config(state=NORMAL,bg="lightgray")
                        lockWinFrames[lockName]['butClose'].config(state=DISABLED,bg="lightgreen")
                        lockWinFrames[lockName]['butBlock'].config(state=NORMAL,bg="lightgray")
                    elif lockData[lockName]['lockState'] == 'opened':
                        lockWinFrames[lockName]['butOpen'].config(state=DISABLED,bg="lightgreen")
                        lockWinFrames[lockName]['butClose'].config(state=NORMAL,bg="lightgray")
                        lockWinFrames[lockName]['butBlock'].config(state=NORMAL,bg="lightgray")
                    else:
                        lockWinFrames[lockName]['butOpen'].config(state=DISABLED,bg="lightgreen")
                        lockWinFrames[lockName]['butClose'].config(state=NORMAL,bg="lightgray")
                        lockWinFrames[lockName]['butBlock'].config(state=NORMAL,bg="lightgray")
                    for idBStr in lockWinFrames[lockName]['codeFrame'].keys():
                        if idBStr.find("but") != -1:
                            lockWinFrames[lockName]['codeFrame'][idBStr].config(state=NORMAL)
            elif commList[1] == 'SOUND':
                print(".")
            elif commList[1] == 'OPENED':
                lockWinFrames[lockName]['butOpen'].config(state=DISABLED,bg="lightgreen")
                lockWinFrames[lockName]['butClose'].config(state=NORMAL,bg="lightgray")
                lockWinFrames[lockName]['butBlock'].config(state=NORMAL,bg="lightgray")
            elif commList[1] == 'CLOSED':
                lockWinFrames[lockName]['butOpen'].config(state=NORMAL,bg="lightgray")
                lockWinFrames[lockName]['butClose'].config(state=DISABLED,bg="lightgreen")
                lockWinFrames[lockName]['butBlock'].config(state=NORMAL,bg="lightgray")
            elif commList[1] == 'BLOCKED':
                lockWinFrames[lockName]['butOpen'].config(state=NORMAL,bg="lightgray")
                lockWinFrames[lockName]['butClose'].config(state=NORMAL,bg="lightgray")
                lockWinFrames[lockName]['butBlock'].config(state=DISABLED,bg="lightgreen")
    elif msg.topic == 'RGBASK':
        print(msg.payload)
	# Здесь должна быть обработка сообщений для канала RGBASK

def mqttConnInit():
    try:  # Пробуем соединиться с сервером
        client.connect(mqtt_broker_ip, mqtt_broker_port, 5)  # Соединяемся с сервtром. Адрес, порт, таймаут попытки.
    except BaseException:
        # Соединение не удалось!
        mqttFlag = False
    else:
        # Соединение успешно.
        mqttFlag = True
        client.loop_start()  # Клиентский цикл запустили - реконнект при разрыв связи и работа обработчика сообщений
    while mqttFlag :
        client.publish('TERM', "*/PING") # Запрос PING для всех терминалов (канал TERM)
        client.publish('LOCK', "*/PING") # Запрос PING для всех замков (канал LOCK)
        client.publish('RGB', "*/PING")  # Запрос PING для всех светильников (канал RGB)
        time.sleep(1) # Пауза одна секунда

def checkAliveTime():
    global lockData
    global lockWinFrames
    aliveDelta = 1500
    while True:
        curTime = millis()
        for lockName in lockData.keys():
            if curTime > (lockData[lockName]['aliveTimeStamp'] + aliveDelta) \
                    and lockData[lockName]['isAlive'] == "True":
                lockData[lockName]['isAlive'] = "False"
                lockWinFrames[lockName]['labLockLive'].config(bg="red")
                lockWinFrames[lockName]['butSoundOn'].config(state=DISABLED)
                lockWinFrames[lockName]['butSoundOff'].config(state=DISABLED)
                lockWinFrames[lockName]['butOpen'].config(state=DISABLED)
                lockWinFrames[lockName]['butClose'].config(state=DISABLED)
                lockWinFrames[lockName]['butBlock'].config(state=DISABLED)
                for idBStr in lockWinFrames[lockName]['codeFrame'].keys():
                    if idBStr.find("but") != -1:
                        lockWinFrames[lockName]['codeFrame'][idBStr].config(state=DISABLED)
        time.sleep(0.5)
#        print (curTime)


client = mqtt.Client()  # Создаём объект типа MQTT Client
client.on_connect = onConnect  # Привязываем функцию для исполнения при успешном соединении с сервером
client.on_message = onMessage  # Привязываем функцию для исполнения при приходе сообщения в любом из подписанных каналов



confWindows = threading.Thread(name='confWindows', \
                               target=confWindowsInit)

mqttConn = threading.Thread(name='mqttConn', \
                               target=mqttConnInit)

checkAlive = threading.Thread(name='checkAlive', \
                               target=checkAliveTime)


mqttConn.start()
confWindows.start()
checkAlive.start()

