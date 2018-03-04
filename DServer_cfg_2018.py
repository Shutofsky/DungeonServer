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
mqtt_broker_ip = '192.168.0.200'
#mqtt_broker_ip = '10.23.192.193'
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
lockWinFrames = dict()
lockOrder = dict()
lockIPtoName = dict()
lockNewWin = dict()
cardNames = dict()

termData = dict()
termWinFrames = dict()
termOrder = dict()
termIPtoName = dict()
termNewWin = dict()

baseData = dict()
baseCommand = dict()
baseWinFrame = dict()

rgbData = dict()

logStrCnt = 0

start_time = datetime.now()

def millis():
    dt = datetime.now() - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms

def confirmClose(winID):
    winID.destroy()

def readColorData():
    global baseColors
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT * FROM dict ORDER BY Id"):
        baseColors[str(row[0])] = [row[1],row[2],row[3]]
    print(baseColors)
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
    print (jsStr)
    baseCommand = json.loads(jsStr)
    conn.close()

def readRGBData():
    global rgbData
    jsStr = '{'
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT rgbName, rgbIPAddr \
                                     FROM rgbStatus"):
        rgbData[row[0]] = dict()
        rgbData[row[0]]['IPAddr'] = row[1]
        rgbData[row[0]]['isAlive'] = 'False'
        rgbData[row[0]]['aliveTimeStamp'] = 0
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
                 ',"menuList":"'+row[10]+'","msgHead":"'+row[11]+'","msgBody":["'+ \
                 ('","'.join(row[12].replace('"','\'').split('\n')))+\
                 '"],"lockName":"'+row[13]+'","isAlive":"False","aliveTimeStamp":0},'
        termIPtoName[row[1]] = row[0]
    jsStr = jsStr.rstrip(',') + '}'
    print (jsStr)
    termData = json.loads(jsStr)
    for row in req.execute("SELECT * FROM termOrder ORDER BY termNumber"):
        termOrder[row[0]] = row[1]
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

def bindTermIP(name, addr):
    termWinFrames[termOrder[name.curselection()[0]]]['IPAddr'].delete(0, END)
    termWinFrames[termOrder[name.curselection()[0]]]['IPAddr'].insert(0, addr)
    updateTermBaseParm(termOrder[name.curselection()[0]], 'IPAddr')
    newTermWindow.destroy()
    del(termNewWin[addr])

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

def newTermWinCreate(IPAddr):
    global newTermWindow
    newTermWindow = Toplevel()
    termNewWin[IPAddr] = dict()
    termNewWin[IPAddr]['labMain'] = Label(newTermWindow, text = 'Обнаружен новый замок с адресом: '+IPAddr)
    termNewWin[IPAddr]['listMainFrame'] = Frame(newTermWindow)
    termNewWin[IPAddr]['newNameListScroll'] = Scrollbar(termNewWin[IPAddr]['listMainFrame'], orient=VERTICAL)
    termNewWin[IPAddr]['newNameList'] = Listbox(termNewWin[IPAddr]['listMainFrame'], width=40, \
                                                height=3, selectmode = SINGLE, exportselection=0, \
                                                yscrollcommand = termNewWin[IPAddr]['newNameListScroll'].set)
    termNewWin[IPAddr]['newNameList'].delete(0, END)
    for termNum in termOrder.keys():
        termNewWin[IPAddr]['newNameList'].insert(END, termOrder[termNum])
    termNewWin[IPAddr]['newNameListScroll'].config(command=termNewWin[IPAddr]['newNameList'].yview)
    termNewWin[IPAddr]['newNameBut'] = Button(newTermWindow, text = u'Назначить имя из списка', \
            command = lambda \
            termName = termNewWin[IPAddr]['newNameList'], \
            termAddr = IPAddr : bindTermIP(termName, termAddr))
    termNewWin[IPAddr]['labMain'].grid(row = 0, column = 0)
    termNewWin[IPAddr]['newNameList'].grid(row = 1, column = 0)
    termNewWin[IPAddr]['newNameListScroll'].grid(row = 1, column = 1, sticky = W)
    termNewWin[IPAddr]['newNameBut'].grid(row = 1, column = 2)
    termNewWin[IPAddr]['listMainFrame'].grid(row = 1, column = 0)

def createLocksWindow():
    global allLockWindow
    allLockWindow = Frame(root)
    colFrame = 0
    for lockNum in lockOrder.keys():
        lockName = lockOrder[lockNum]
        createLockWindow(lockName, colFrame)
        colFrame += 1
    allLockWindow.grid(row=1, column=0, sticky=W)

def createLockWindow(lockName, colFrame):
    global lockData
    global cardNames
    global lockWinFrames
    global lockCode
    global lockOrder

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
    lockWinFrames[lockName]['mainLockFrame'].grid(row = 0, column = colFrame, sticky = W)

def createTermsWindow():
    global allTermWindow
    allTermWindow = Frame(root)
    colFrame = 0
    for termNum in termOrder.keys():
        termName = termOrder[termNum]
        createTermWindow(termName, colFrame)
        colFrame += 1
    allTermWindow.grid(row=2, column=0, sticky=W)

def updateTermBaseParm(termName, parmName):
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    if parmName == 'IPAddr':
        del (termIPtoName[termData[termName]['IPAddr']])
        termData[termName]['IPAddr'] = termWinFrames[termName]['IPAddr'].get()
        termIPtoName[termWinFrames[termName]['IPAddr'].get()] = termName
    elif parmName == 'msg':
        termData[termName]['msgHead'] = termWinFrames[termName]['msgHead'].get()
        termData[termName]['msgBody'] = termWinFrames[termName]['msgBody'].get("1.0",END).split('\n')
        client.publish("TERM", termData[termName]['IPAddr'] + '/UPDATEDB/{"msgHead":"' + \
                       termData[termName]['msgHead'] + '","msgBody":' + json.dumps(termData[termName]['msgBody']) \
                       + '}')
        req.execute("UPDATE termStatus SET msgHead = ? WHERE name = ?",
                    [termData[termName]['msgHead'], termName])
        conn.commit()
        req.execute("UPDATE termStatus SET msgBody = ? WHERE name = ?",
                    ['\n'.join(termData[termName]['msgBody']), termName])
        conn.commit()
        conn.close()
        return
    elif parmName == 'menuList1' or parmName == 'menuList2' or parmName == 'menuList3':
        tmpMenuList = termData[termName]['menuList'].split(',')
        if (termWinFrames[termName][parmName].get())[0] == '+':
            tmpMenuList.append((termWinFrames[termName][parmName].get())[1])
        else:
            tmpMenuList.remove((termWinFrames[termName][parmName].get())[1])
        termData[termName]['menuList'] = ','.join(sorted(tmpMenuList))
        req.execute("UPDATE termStatus SET menuList = ? WHERE name = ?",
                    [termData[termName]['menuList'], termName])
        conn.commit()
        conn.close()
        return
    else:
        termData[termName][parmName] = termWinFrames[termName][parmName].get()
        client.publish("TERM", termData[termName]['IPAddr'] + '/UPDATEDB/{"' + parmName + '":"' + \
                       termData[termName][parmName] + '"}')
        print(termData[termName]['IPAddr'] + '/UPDATEDB/{"' + parmName + '":"' + \
                       termData[termName][parmName] + '"}')
    req.execute("UPDATE termStatus SET "+parmName+" = ? WHERE name = ?", [termWinFrames[termName][parmName].get(), \
                                                               termName])
    conn.commit()
    conn.close()

def createTermWindow(termName, colFrame):
    global termData
    global termWinFrames
    termWinFrames[termName] = dict()
    termWinFrames[termName]['mainTermFrame'] = Frame(allTermWindow, bd = 3, relief = SUNKEN)
    termWinFrames[termName]['labTermName'] = Label(termWinFrames[termName]['mainTermFrame'], \
                                                   text=termName, font=(("Arial", 12, "bold")))
    termWinFrames[termName]['labTermName'].grid(row=0, column=0, columnspan=2, sticky=W)
    if termData[termName]['isAlive'] == 'True':
        bgAlive = "green"
    else:
        bgAlive = "red"
    termWinFrames[termName]['labTermLive'] = Button(termWinFrames[termName]['mainTermFrame'], \
                                                    bg=bgAlive, state=DISABLED, text=u'    ')
    termWinFrames[termName]['labTermLive'].grid(row=0, column=2, sticky=E)
    termWinFrames[termName]['labIPAddr'] = Label(termWinFrames[termName]['mainTermFrame'], text=u'IP адрес: ')
    termWinFrames[termName]['labIPAddr'].grid(row=1, column=0, sticky=W)
    termWinFrames[termName]['IPAddr'] = Entry(termWinFrames[termName]['mainTermFrame'], width=16)
    termWinFrames[termName]['IPAddr'].insert(0, termData[termName]['IPAddr'])
    termWinFrames[termName]['IPAddr'].grid(row=1, column=1, sticky=W + E)
    termWinFrames[termName]['butIPAddr'] = Button(termWinFrames[termName]['mainTermFrame'], text=u'Сменить', \
                                                  command=lambda name=termName, parm='IPAddr': \
                                                  updateTermBaseParm(name, parm))
    termWinFrames[termName]['butIPAddr'].grid(row=1, column=2, sticky=E)
    termWinFrames[termName]['isPowerOn'] = StringVar()
    termWinFrames[termName]['butPowered'] = Checkbutton(termWinFrames[termName]['mainTermFrame'], text=u'Питание ОК', \
                    variable=termWinFrames[termName]['isPowerOn'], onvalue='YES', offvalue='NO', \
                    command=lambda name=termName, parm='isPowerOn' : updateTermBaseParm(name, parm))
    if termData[termName]['isPowerOn'] == 'YES':
        termWinFrames[termName]['butPowered'].select()
    else:
        termWinFrames[termName]['butPowered'].deselect()
    termWinFrames[termName]['butPowered'].grid(row=2, column=0, sticky=W)
    termWinFrames[termName]['isLocked'] = StringVar()
    termWinFrames[termName]['butLocked'] = Checkbutton(termWinFrames[termName]['mainTermFrame'], text=u'Заблокирован', \
                    variable=termWinFrames[termName]['isLocked'], onvalue='YES', offvalue='NO', \
                    command=lambda name=termName, parm='isLocked': updateTermBaseParm(name, parm))
    if termData[termName]['isLocked'] == 'YES':
        termWinFrames[termName]['butLocked'].select()
    else:
        termWinFrames[termName]['butLocked'].deselect()
    termWinFrames[termName]['butLocked'].grid(row=2, column=1, sticky=W)
    termWinFrames[termName]['isHacked'] = StringVar()
    termWinFrames[termName]['butHacked'] = Checkbutton(termWinFrames[termName]['mainTermFrame'], text=u'Взломан', \
                    variable=termWinFrames[termName]['isHacked'], onvalue='YES', offvalue='NO', \
                    command=lambda name=termName, parm='isHacked':  updateTermBaseParm(name, parm))
    if termData[termName]['isLocked'] == 'YES':
        termWinFrames[termName]['butHacked'].select()
    else:
        termWinFrames[termName]['butHacked'].deselect()
    termWinFrames[termName]['butHacked'].grid(row=2, column=2, sticky=W)
    termWinFrames[termName]['menuList1'] = StringVar()
    termWinFrames[termName]['menuList2'] = StringVar()
    termWinFrames[termName]['menuList3'] = StringVar()
    termWinFrames[termName]['butMenu1'] = Checkbutton(termWinFrames[termName]['mainTermFrame'], text=u'Замок',\
                    variable=termWinFrames[termName]['menuList1'], onvalue='+1', offvalue='-1', \
                    command=lambda name=termName : updateTermBaseParm(name, 'menuList1'))
    if '1' in termData[termName]['menuList'].split(','):
        termWinFrames[termName]['butMenu1'].select()
    else:
        termWinFrames[termName]['butMenu1'].deselect()
    termWinFrames[termName]['butMenu1'].grid(row=3, column=0, sticky=W)
    termWinFrames[termName]['butMenu2'] = Checkbutton(termWinFrames[termName]['mainTermFrame'], text=u'Тревога',\
                    variable=termWinFrames[termName]['menuList2'], onvalue='+2', offvalue='-2', \
                    command=lambda name=termName : updateTermBaseParm(name, 'menuList2'))
    if '2' in termData[termName]['menuList'].split(','):
        termWinFrames[termName]['butMenu2'].select()
    else:
        termWinFrames[termName]['butMenu2'].deselect()
    termWinFrames[termName]['butMenu2'].grid(row=3, column=1, sticky=W)
    termWinFrames[termName]['butMenu3'] = Checkbutton(termWinFrames[termName]['mainTermFrame'], text=u'Сообщение',\
                    variable=termWinFrames[termName]['menuList3'], onvalue='+3', offvalue='-3', \
                    command=lambda name=termName : updateTermBaseParm(name, 'menuList3'))
    if '3' in termData[termName]['menuList'].split(','):
        termWinFrames[termName]['butMenu3'].select()
    else:
        termWinFrames[termName]['butMenu3'].deselect()
    termWinFrames[termName]['butMenu3'].grid(row=3, column=2, sticky=W)
    termWinFrames[termName]['labWordsPrinted'] = Label(termWinFrames[termName]['mainTermFrame'], \
                                                       text=u'Слов в игре:')
    termWinFrames[termName]['labWordsPrinted'].grid(row=4, column=0, sticky=W)
    termWinFrames[termName]['wordsPrinted'] = Entry(termWinFrames[termName]['mainTermFrame'], width=16)
    termWinFrames[termName]['wordsPrinted'].insert(0, termData[termName]['wordsPrinted'])
    termWinFrames[termName]['wordsPrinted'].grid(row=4, column=1, sticky=W + E)
    termWinFrames[termName]['butWordsPrinted'] = Button(termWinFrames[termName]['mainTermFrame'], text=u'Сменить', \
                                                        command=lambda name=termName, parm='wordsPrinted':
                                                        updateTermBaseParm(name, parm))
    termWinFrames[termName]['butWordsPrinted'].grid(row=4, column=2, sticky=E)
    termWinFrames[termName]['labWordLength'] = Label(termWinFrames[termName]['mainTermFrame'], \
                                                       text=u'Длина слова:')
    termWinFrames[termName]['labWordLength'].grid(row=5, column=0, sticky=W)
    termWinFrames[termName]['wordLength'] = Entry(termWinFrames[termName]['mainTermFrame'], width=16)
    termWinFrames[termName]['wordLength'].insert(0, termData[termName]['wordLength'])
    termWinFrames[termName]['wordLength'].grid(row=5, column=1, sticky=W + E)
    termWinFrames[termName]['butWordLength'] = Button(termWinFrames[termName]['mainTermFrame'], text=u'Сменить', \
                                                        command=lambda name=termName, parm='wordLength':
                                                        updateTermBaseParm(name, parm))
    termWinFrames[termName]['butWordLength'].grid(row=5, column=2, sticky=E)
    termWinFrames[termName]['termAction'] = Frame(termWinFrames[termName]['mainTermFrame'])
    termWinFrames[termName]['isLockOpen'] = StringVar()
    termWinFrames[termName]['isLevelDown'] = StringVar()
    termWinFrames[termName]['butLockOpen'] = Checkbutton(termWinFrames[termName]['termAction'], text=u'Открытие замка', \
                                                       variable=termWinFrames[termName]['isLockOpen'], onvalue='YES', \
                                                       offvalue='NO', command=lambda name=termName, \
                                                        parm='isLockOpen': updateTermBaseParm(name, parm))
    termWinFrames[termName]['butLockOpen'].grid(row=0, column=0)
    if termData[termName]['isLockOpen'] == 'YES':
        termWinFrames[termName]['butLockOpen'].select()
    else:
        termWinFrames[termName]['butLockOpen'].deselect()
    termWinFrames[termName]['butLevelDown'] = Checkbutton(termWinFrames[termName]['termAction'], \
                                                          text=u'Понижение тревоги', \
                                                          variable=termWinFrames[termName]['isLevelDown'], \
                                                          onvalue='YES', offvalue='NO', command=lambda name=termName, \
                                                          parm='isLevelDown': updateTermBaseParm(name, parm))
    termWinFrames[termName]['butLevelDown'].grid(row=0, column=1)
    if termData[termName]['isLevelDown'] == 'YES':
        termWinFrames[termName]['butLevelDown'].select()
    else:
        termWinFrames[termName]['butLevelDown'].deselect()
    termWinFrames[termName]['termAction'].grid(row=6, column=0, columnspan=3)
    termWinFrames[termName]['lockSFrame'] = Frame(termWinFrames[termName]['mainTermFrame'])
    termWinFrames[termName]['lockList'] = Listbox(termWinFrames[termName]['lockSFrame'], width=40, \
                                                  height=3, selectmode=SINGLE, exportselection=0)
    termWinFrames[termName]['lockScroll'] = Scrollbar(termWinFrames[termName]['lockSFrame'], orient=VERTICAL, \
                                                      command=termWinFrames[termName]['lockList'].yview)
    termWinFrames[termName]['lockList']['yscrollcommand']=termWinFrames[termName]['lockScroll'].set
    termWinFrames[termName]['lockList'].delete(0, END)
    for lockNum in lockOrder.keys():
        termWinFrames[termName]['lockList'].insert(END, lockOrder[lockNum])
        if lockOrder[lockNum] == termData[termName]['lockName']:
            termWinFrames[termName]['lockList'].selection_set(lockNum)
    termWinFrames[termName]['lockSetBut'] = Button(termWinFrames[termName]['lockSFrame'], \
                                                   text=u'Назначить имя из списка', \
                                                   command=lambda lockName=termWinFrames[termName]['lockList'], \
                                                   termID=termName: bindLockTerm(lockName, termID))
    termWinFrames[termName]['lockList'].grid(row=0, column=0)
    termWinFrames[termName]['lockScroll'].grid(row=0, column=1, sticky=W)
    termWinFrames[termName]['lockSetBut'].grid(row=0, column=2)
    termWinFrames[termName]['lockSFrame'].grid(row=7, column=0, columnspan=3)
    termWinFrames[termName]['msgHFrame'] = Frame(termWinFrames[termName]['mainTermFrame'])
    termWinFrames[termName]['labMsg'] = Label(termWinFrames[termName]['msgHFrame'], \
                                              text=u'Заголовок сообщения:')
    termWinFrames[termName]['labMsg'].grid(row=0, column=0)
    termWinFrames[termName]['msgHead'] = Entry(termWinFrames[termName]['msgHFrame'], width=40)
    termWinFrames[termName]['msgHead'].insert(0, termData[termName]['msgHead'])
    termWinFrames[termName]['msgHead'].grid(row=0, column=1)
    termWinFrames[termName]['msgHFrame'].grid(row=8, column=0, columnspan=3)
    termWinFrames[termName]['msgBFrame'] = Frame(termWinFrames[termName]['mainTermFrame'])
    termWinFrames[termName]['msgBody'] = Text(termWinFrames[termName]['msgBFrame'],width=62, height=8, wrap=WORD,\
                                              font = 'Arial 8')
    termWinFrames[termName]['msgBody'].insert(END, ('\n'.join(termData[termName]['msgBody'])).replace('\'','"'))
    termWinFrames[termName]['msgScroll'] = Scrollbar(termWinFrames[termName]['msgBFrame'], orient=VERTICAL, \
                                                     command=termWinFrames[termName]['msgBody'].yview)
    termWinFrames[termName]['msgBody']['yscrollcommand'] = termWinFrames[termName]['msgScroll'].set
    termWinFrames[termName]['msgBody'].grid(row=0,column=0,sticky=W)
    termWinFrames[termName]['msgScroll'].grid(row=0,column=1,sticky=N+S)
    termWinFrames[termName]['msgBut'] = Button(termWinFrames[termName]['msgBFrame'], \
                                               text=u'Править сообщение', command=lambda name=termName, parm='msg': \
                                               updateTermBaseParm(name, parm))
    termWinFrames[termName]['msgBut'].grid(row=1, column=0, columnspan = 2)
    termWinFrames[termName]['msgBFrame'].grid(row=9, column=0, columnspan=3)
    termWinFrames[termName]['mainTermFrame'].grid(row=0, column=colFrame)
    if termData[termName]['isAlive'] == 'False':
        termWinFrames[termName]['butPowered'].config(state=DISABLED)
        termWinFrames[termName]['butLocked'].config(state=DISABLED)
        termWinFrames[termName]['butHacked'].config(state=DISABLED)
        termWinFrames[termName]['butMenu1'].config(state=DISABLED)
        termWinFrames[termName]['butMenu2'].config(state=DISABLED)
        termWinFrames[termName]['butMenu3'].config(state=DISABLED)
        termWinFrames[termName]['butWordsPrinted'].config(state=DISABLED)
        termWinFrames[termName]['butWordLength'].config(state=DISABLED)
        termWinFrames[termName]['butLockOpen'].config(state=DISABLED)
        termWinFrames[termName]['butLevelDown'].config(state=DISABLED)
        termWinFrames[termName]['msgBut'].config(state=DISABLED)

def addTextLog(logString):
    global logWin
    global logBody
    global logStrCnt
    dt = datetime.now()
    logBody.config(state=NORMAL)
    logBody.insert(END, dt.strftime("%d %b %y %H:%M:%S") + ' : ' + logString)
    logStrCnt = len(logBody.get(1.0,END).split('\n'))
    if logStrCnt>=32:
        logStr = logBody.get(2.0, 30.0)
        logStr.strip('\n')
        logStr.strip('\r')
        logBody.delete(1.0,END)
        logBody.insert(1.0, logStr)
    logBody.config(state=DISABLED)

def onConnect(client, userdata, flags, rc):
    client.subscribe("TERMASK/#")    # Подписка на канал TERMASK
    client.subscribe("LOCKASK/#")    # Подписка на канал LOCKASK
    client.subscribe("RGBASK/#")     # Подписка на канал RGBASK
    client.subscribe("PWRASK/#")     # Подписка на канал RGBASK

def onMessage(client, userdata, msg):
    global lockData
    global lockWinFrames
    global lockIPtoName
    global baseColors
    global baseData
    global baseWinFrame
    commList = msg.payload.decode('utf-8').split('/')  # Разделяем тело сообщения на элементы списка по знаку /
    # commList[0] - IP-адрес устройства, и т.д.
    if msg.topic == 'TERMASK':
        # Здесь должна быть обработка сообщений для канала TERMASK
        if commList[0] not in termIPtoName.keys():
            # Стукнулось неизвестное устройтство  - терминал
            if commList[0] not in termNewWin.keys():
                # Окно для этого устройства ещё не создано
                newTermWinCreate(commList[0])
        else:
            termName = termIPtoName[commList[0]]
            if commList[1] == 'PONG':
                termData[termName]['aliveTimeStamp'] = millis()
                if termData[termName]['isAlive'] == "False":
                    jsStr = '{'
                    for parName in termData[termName].keys():
                        if parName != 'lockName' and parName != 'isAlive' \
                                and parName != 'aliveTimeStamp' and parName!='IPAddr' \
                                and parName != 'msgBody' and parName != 'msgHead':
                            jsStr += '"'+parName+'":"'+str(termData[termName][parName])+'",'
#                    jsStr += '"msgBody":["' + '","'.join(termData[termName]['msgBody']) + '"]}'
                    jsStr = jsStr.rstrip(',') + "}"
                    client.publish("TERM",commList[0]+"/UPDATEDB/"+jsStr)
                    termData[termName]['isAlive'] = 'True'
                    termWinFrames[termName]['butPowered'].config(state=NORMAL)
                    termWinFrames[termName]['butLocked'].config(state=NORMAL)
                    termWinFrames[termName]['butHacked'].config(state=NORMAL)
                    termWinFrames[termName]['butMenu1'].config(state=NORMAL)
                    termWinFrames[termName]['butMenu2'].config(state=NORMAL)
                    termWinFrames[termName]['butMenu3'].config(state=NORMAL)
                    termWinFrames[termName]['butWordsPrinted'].config(state=NORMAL)
                    termWinFrames[termName]['butWordLength'].config(state=NORMAL)
                    termWinFrames[termName]['butLockOpen'].config(state=NORMAL)
                    termWinFrames[termName]['butLevelDown'].config(state=NORMAL)
                    termWinFrames[termName]['msgBut'].config(state=NORMAL)
                    termWinFrames[termName]['labTermLive'].config(bg="green")
            elif commList[1] == 'LOCKED':
                logStr = 'Терминал "' + termName + '" заблокирован!\n'
                addTextLog(logStr)
                changeAlarmLevel(+10)
                termWinFrames[termName]['butLocked'].select()
                updateTermBaseParm(termName,'isLocked')
            elif commList[1] == 'HACKED':
                logStr = 'Терминал "' + termName + '" взломан!\n'
                addTextLog(logStr)
                changeAlarmLevel(+5)
                termWinFrames[termName]['butHacked'].select()
                updateTermBaseParm(termName, 'isHacked')
            elif commList[1] == 'DOLEVELDOWN':
                logStr = 'С терминала "' + termName + '" запрошено снижение уровня тревоги!\n'
                addTextLog(logStr)
                print ('DOLEVELDOWN')
            elif commList[1] == 'DOLOCKOPEN':
                logStr = 'С терминала "' + termName + '" запрошено открытие замка "'
                if termData[termName]['lockName'] in lockData.keys():
                    logStr += termData[termName]['lockName'] + '"!\n'
                    termWinFrames[termName]['butLockOpen'].select()
                    updateTermBaseParm(termName, 'isLockOpen')
                    client.publish('LOCK', lockData[termData[termName]['lockName']]['IPAddr'] + '/OPEN')
                addTextLog(logStr)
    elif msg.topic == 'LOCKASK':
        # Здесь должна быть обработка сообщений для канала LOCKASK
        if commList[0] not in lockIPtoName.keys():
            # Стукнулось неизвестное устройтство  - замок
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
                lockData[lockName]['isSound'] = 'YES'
                conn = sqlite3.connect(dbName)
                req = conn.cursor()
                req.execute("UPDATE lockStatus set isSound = 'YES' WHERE name == ?", [lockName])
                conn.commit()
                conn.close()
            elif commList[1] == 'NOSOUND':
                lockData[lockName]['isSound'] = 'NO'
                conn = sqlite3.connect(dbName)
                req = conn.cursor()
                req.execute("UPDATE lockStatus set isSound = 'NO' WHERE name == ?", [lockName])
                conn.commit()
                conn.close()
            elif commList[1] == 'OPENED':
                lockWinFrames[lockName]['butOpen'].config(state=DISABLED,bg="lightgreen")
                lockWinFrames[lockName]['butClose'].config(state=NORMAL,bg="lightgray")
                lockWinFrames[lockName]['butBlock'].config(state=NORMAL,bg="lightgray")
                lockData[lockName]['lockState'] = 'opened'
                logStr = 'Замок "' + lockName + '" открыт\n'
                addTextLog(logStr)
                conn = sqlite3.connect(dbName)
                req = conn.cursor()
                req.execute("UPDATE lockStatus set lockState = 'opened' WHERE name == ?", [lockName])
                conn.commit()
                conn.close()
            elif commList[1] == 'CLOSED':
                lockWinFrames[lockName]['butOpen'].config(state=NORMAL,bg="lightgray")
                lockWinFrames[lockName]['butClose'].config(state=DISABLED,bg="lightgreen")
                lockWinFrames[lockName]['butBlock'].config(state=NORMAL,bg="lightgray")
                lockData[lockName]['lockState'] = 'closed'
                logStr = 'Замок "' + lockName + '" закрыт\n'
                addTextLog(logStr)
                conn = sqlite3.connect(dbName)
                req = conn.cursor()
                req.execute("UPDATE lockStatus set lockState = 'closed' WHERE name == ?", [lockName])
                conn.commit()
                conn.close()
            elif commList[1] == 'BLOCKED':
                lockWinFrames[lockName]['butOpen'].config(state=NORMAL,bg="lightgray")
                lockWinFrames[lockName]['butClose'].config(state=NORMAL,bg="lightgray")
                lockWinFrames[lockName]['butBlock'].config(state=DISABLED,bg="lightgreen")
                lockData[lockName]['lockState'] = 'blocked'
                logStr = 'Замок "'+ lockName + '" заблокирован\n'
                addTextLog(logStr)
                conn = sqlite3.connect(dbName)
                req = conn.cursor()
                req.execute("UPDATE lockStatus set lockState = 'blocked' WHERE name == ?", [lockName])
                conn.commit()
                conn.close()
            elif commList[1] == 'CODE':
                logStr = 'К замку "' + lockName + '" приложена карта ' + commList[3]
                dt = datetime.now()
                if commList[2] == 'RIGHT':
                    logStr += ' ВЕРНО!!! \n'
                elif commList[2] == 'STATUSWRONG':
                    changeAlarmLevel(+3)
                    logStr += ' НЕВЕРНО - СТАТУС! \n'
                elif commList[2] == 'GLOBALWRONG':
                    changeAlarmLevel(+5)
                    logStr += ' НЕВЕРНО - НЕИЗВЕСТНАЯ КАРТА! \n'
                addTextLog(logStr)
                conn = sqlite3.connect(dbName)
                req = conn.cursor()
                req.execute("INSERT INTO lockLog VALUES(?, ?, ?, ?)", \
                            (lockName, dt.strftime("%A, %d. %B %Y %H:%M:%S"), commList[3], commList[2]))
                conn.commit()
                conn.close()
    elif msg.topic == 'RGBASK':
        # Здесь должна быть обработка сообщений для канала RGBASK
        # print(msg.payload)
        if commList[0] not in rgbData.keys():
            # Стукнулось неизвестное устройтство  - светильник
            rgbData[commList[0]] = dict()
            rgbData[commList[0]]['IPAddr'] = commList[0]
            rgbData[commList[0]]['isAlive'] = 'False'
            rgbData[commList[0]]['aliveTimeStamp'] = 0
            conn = sqlite3.connect(dbName)
            req = conn.cursor()
            req.execute("INSERT INTO rgbStatus VALUES(?, ?)", [commList[0], commList[0]])
            conn.commit()
            conn.close()
        else:
            if commList[1] == 'PONG':
                rgbData[commList[0]]['aliveTimeStamp'] = millis()
                if rgbData[commList[0]]['isAlive'] == 'False':
                    rgbData[commList[0]]['isAlive'] = 'True'
                    for commStr in baseCommand[baseData['colorStatus']]['rgbCommand']:
                        client.publish('RGB', commList[0] + commStr)
                        time.sleep(0.1)
    elif msg.topic == 'PWRASK':
        print(msg.payload)
	    # Здесь должна быть обработка сообщений для канала PWRASK
        if commList[0] == 'AUX':
            # Запущено промежуточное питание
            if baseData['colorStatus'] == 'blue':
                logStr = 'Силовой щиток - активировано вспомогательное питание! \n'
                addTextLog(logStr)
                baseWinFrame['statusList'].selection_clear(1)
                baseWinFrame['statusList'].selection_set(2)
                changeBaseStatus(baseWinFrame['statusList'])
        if commList[0] == 'PWR':
            # Запущено основное питание
            if baseData['colorStatus'] == 'lightblue':
                logStr = 'Силовой щиток - запуск основного реактора! \n'
                addTextLog(logStr)
                baseWinFrame['statusList'].selection_clear(2)
                baseWinFrame['statusList'].selection_set(3)
                changeBaseStatus(baseWinFrame['statusList'])

def mqttConnInit():
    try:  # Пробуем соединиться с сервером
        client.connect(mqtt_broker_ip, mqtt_broker_port, 5)  # Соединяемся с сервером. Адрес, порт, таймаут попытки.
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
    aliveDelta = 3000
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
        for termName in termData.keys():
            if curTime > (termData[termName]['aliveTimeStamp'] + aliveDelta) \
                    and termData[termName]['isAlive'] == "True":
                termData[termName]['isAlive'] = "False"
                termWinFrames[termName]['labTermLive'].config(bg="red")
                termWinFrames[termName]['butPowered'].config(state=DISABLED)
                termWinFrames[termName]['butLocked'].config(state=DISABLED)
                termWinFrames[termName]['butHacked'].config(state=DISABLED)
                termWinFrames[termName]['butMenu1'].config(state=DISABLED)
                termWinFrames[termName]['butMenu2'].config(state=DISABLED)
                termWinFrames[termName]['butMenu3'].config(state=DISABLED)
                termWinFrames[termName]['butWordsPrinted'].config(state=DISABLED)
                termWinFrames[termName]['butWordLength'].config(state=DISABLED)
                termWinFrames[termName]['butLockOpen'].config(state=DISABLED)
                termWinFrames[termName]['butLevelDown'].config(state=DISABLED)
                termWinFrames[termName]['msgBut'].config(state=DISABLED)
        for rgbName in rgbData.keys():
            if curTime > (rgbData[rgbName]['aliveTimeStamp'] + aliveDelta) \
                    and rgbData[rgbName]['isAlive'] == "True":
                rgbData[rgbName]['isAlive'] = 'False'
        time.sleep(1)
#        print (curTime)

def changeBaseStatus(newStat):
    global baseWinFrame
    global baseData
    global baseColors
    global baseCommand
    global root
    newBColor = baseColors[str(newStat.curselection()[0])][0]
    newFColor = baseColors[str(newStat.curselection()[0])][2]
    baseWinFrame['mainFrame'].config(bg=newBColor)
    baseWinFrame['labStatus'].config(bg=newBColor,fg=newFColor)
    baseData['colorStatus'] = newBColor
    for lockName in lockData.keys():
        lockData[lockName]['baseState'] = newBColor
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("UPDATE baseStatus set colorStatus = ?", [newBColor])
    req.execute("UPDATE lockStatus set baseState = ?", [newBColor])
    conn.commit()
    conn.close()
    if newBColor == 'blue':
        client.publish('PWR', '/OFF/')
    # Здесь всякие MQTT рассылки по замкам и прочему
    for commStr in baseCommand[newBColor]['rgbCommand']:
        client.publish('RGB', '*' + commStr)
        time.sleep(0.1)
    for commStr in baseCommand[newBColor]['lockCommand']:
        client.publish('LOCK', '*'+ commStr)
        time.sleep(0.1)
    for commStr in baseCommand[newBColor]['termCommand']:
        client.publish('TERM', '*'+ commStr)
        time.sleep(0.1)

def changeAlarmLevel(delta):
    global baseWinFrame
    global baseData
    global baseColors
    curLevel=int(baseWinFrame['alarmLevel'].get())
    curLevel+=delta
    baseWinFrame['alarmLevel'].delete(0, END)
    baseWinFrame['alarmLevel'].insert(0, str(curLevel))
    if curLevel>=50 and curLevel<100:
        # Смена статуса на жёлтый
        if baseData['colorStatus'] == 'green':
            logStr = 'Повышение уровня тревоги на ЖЁЛТЫЙ из-за активности на базе!!!\n'
            addTextLog(logStr)
            baseWinFrame['statusList'].selection_clear(3)
            baseWinFrame['statusList'].selection_set(4)
            changeBaseStatus(baseWinFrame['statusList'])
    elif curLevel>=100:
        if baseData['colorStatus'] == 'green':
            logStr = 'Повышение уровня тревоги на КРАСНЫЙ из-за активности на базе!!!\n'
            addTextLog(logStr)
            baseWinFrame['statusList'].selection_clear(3)
            baseWinFrame['statusList'].selection_set(5)
            changeBaseStatus(baseWinFrame['statusList'])
        elif baseData['colorStatus'] == 'yellow':
            logStr = 'Повышение уровня тревоги на КРАСНЫЙ из-за активности на базе!!!\n'
            addTextLog(logStr)
            baseWinFrame['statusList'].selection_clear(4)
            baseWinFrame['statusList'].selection_set(5)
            changeBaseStatus(baseWinFrame['statusList'])

def createBaseWindow():
    global baseWinFrame
    global baseData
    global baseColors
    global root
    for i in baseColors.keys():
        if baseColors[i][0] == baseData['colorStatus']:
            bg=baseColors[i][0]
            fg=baseColors[i][2]
    baseWinFrame['mainFrame'] = Frame(root, bg=bg, relief=SUNKEN)
    baseWinFrame['labStatus'] = Label(baseWinFrame['mainFrame'], text = u'Статус базы:', bg=bg, fg=fg)
    baseWinFrame['labStatus'].grid(row=0, column=0, rowspan=3)
    baseWinFrame['statusList'] = Listbox(baseWinFrame['mainFrame'], width=10, \
                                         height=3, selectmode=SINGLE, exportselection=0)
    baseWinFrame['statusScroll'] = Scrollbar(baseWinFrame['mainFrame'], orient=VERTICAL, \
                                             command=baseWinFrame['statusList'].yview)
    baseWinFrame['statusList']['yscrollcommand'] = baseWinFrame['statusScroll'].set
    for i in baseColors.keys():
        baseWinFrame['statusList'].insert(END, baseColors[i][1])
        if baseColors[i][0] == baseData['colorStatus']:
            baseWinFrame['statusList'].selection_set(i)
    baseWinFrame['statusBut'] = Button(baseWinFrame['mainFrame'], text=u'Сменить статус', \
                                                   command=lambda newStat=baseWinFrame['statusList'] : \
                                                   changeBaseStatus(newStat))
    baseWinFrame['statusList'].grid(row=0, column=1, rowspan=3)
    baseWinFrame['statusScroll'].grid(row=0, column=2, rowspan=3)
    baseWinFrame['statusBut'].grid(row=0, column=3, rowspan=3)
    baseWinFrame['alarmLab'] = Label(baseWinFrame['mainFrame'], text = u'Уровень тревоги:', bg=bg, fg=fg)
    baseWinFrame['alarmLab'].grid(row=0, column=4, rowspan=3)
    baseWinFrame['alarmLevel'] = Entry(baseWinFrame['mainFrame'], width=4)
    baseWinFrame['alarmLevel'].insert(0, baseData['alarmLevel'])
    baseWinFrame['alarmLevel'].grid(row=0, column=5, rowspan=3)
    baseWinFrame['alarmLevelChg']=StringVar()
    baseWinFrame['alarmBut+1'] = Button(baseWinFrame['mainFrame'], text=u'+1', \
                                             command=lambda:changeAlarmLevel(+1))
    baseWinFrame['alarmBut+1'].grid(row=0, column=6)
    baseWinFrame['alarmBut+5']= Button(baseWinFrame['mainFrame'], text=u'+5', \
                                             command=lambda:changeAlarmLevel(+5))
    baseWinFrame['alarmBut+5'].grid(row=1, column=6)
    baseWinFrame['alarmBut+10']= Button(baseWinFrame['mainFrame'], text=u'+10', \
                                             command=lambda:changeAlarmLevel(+10))
    baseWinFrame['alarmBut+10'].grid(row=2, column=6)
    baseWinFrame['alarmBut-1']= Button(baseWinFrame['mainFrame'], text=u'-1', \
                                             command=lambda:changeAlarmLevel(-1))
    baseWinFrame['alarmBut-1'].grid(row=0, column=7)
    baseWinFrame['alarmBut-5']= Button(baseWinFrame['mainFrame'], text=u'-5', \
                                             command=lambda:changeAlarmLevel(-5))
    baseWinFrame['alarmBut-5'].grid(row=1, column=7)
    baseWinFrame['alarmBut-10']= Button(baseWinFrame['mainFrame'], text=u'-10', \
                                             command=lambda:changeAlarmLevel(-10))
    baseWinFrame['alarmBut-10'].grid(row=2, column=7)
    baseWinFrame['mainFrame'].grid(row=0, column=0)

def confWindowsInit():
    global root
    global logWin
    global logBody
    root = Tk()
    root.title(u'Управление данжоном')
    readColorData()
    readLockData()
    readTermData()
    readBaseData()
    readRGBData()
    createBaseWindow()
    createLocksWindow()
    createTermsWindow()
    logWin = Toplevel()
    logBody = Text(logWin, width=120, height=30, state=DISABLED, font='Courier 8')
    logBody.grid(row=0,column=0)
    root.mainloop()

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
