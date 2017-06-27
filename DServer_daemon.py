# -*- coding: utf-8 -*-
from Tkinter import *
import paho.mqtt.client as mqtt
import socket, sqlite3, time
from datetime import datetime
from datetime import timedelta
#import image
import Image
import time

mqtt_broker_ip = '10.23.192.193'
mqtt_broker_port = 1883

dbName = 'DungeonStatus.db'

colorRus = []
statusRussian = dict()
reversStatusRussian = dict()
indexStatus = dict()
indexStatusReverse = dict()
statusFontColor = dict()
lockLive = dict()
lockStatus = dict()
labelLock = []
lockNumber = dict()
labelStatusLock = []
termLive = dict()
termHack = dict()
termHackButtonV = []
tButtonHY = []
tButtonHN = []
tButtonLY = []
tButtonLN = []
termNumber = dict()
termMainButton = []
termHackButton = dict()
termLock = dict()
termLockButtonV = []
termLockButton = dict()
termMListLabel = []
termMListButtonLock = []
termMListButtonAlert = []
termMListButtonText = []
termMListBL = []
termMListBA = []
termMListBT = []
termMHead = []
termMBody = []
termMBodyScr = []
#termAttempts = dict()
#termDifficulty = dict()
termOper = dict()
termResult = dict()
termMenu = dict()
termMsgHead = dict()
termMsgBody = dict()
termDBUpdate = dict()
frameTerm = []
labelTerm = []
frameLock = []
buttonOpenLock = []
buttonBlockLock = []

termPongTime = dict()

start_time = datetime.now()
def millis():
    dt = datetime.now() - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms

def getDBData():
    global currentBaseStatus
    global dbName
    global mqtt_broker_ip
    global mqtt_broker_port
    global colorRus
    global statusRussian
    global reversStatusRussian
    global indexStatus
    global indexStatusReverse
    global statusFontColor
    global lockLive
    global lockStatus
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT * from dict ORDER BY Id"):
        colorRus.append(row[2])
        statusRussian[row[1]] = row[2].upper()
        reversStatusRussian[row[2]] = row[1]
        indexStatus[row[1]] = row[0]
        indexStatusReverse[row[0]] = row[1]
        statusFontColor[row[1]] = row[3]
    req.execute("SELECT * FROM base")
    S = req.fetchone()
    currentBaseStatus = str(S[0])
    for row in req.execute("SELECT * from lock ORDER BY Id"):
        lockLive[row[0]] = row[1]
        lockStatus[row[0]] = row[2]
    for row in req.execute("SELECT * from term ORDER BY Id"):
        termLive[row[0]] = row[1]
        termHack[row[0]] = row[2]
        termLock[row[0]] = row[3]
        termOper[row[0]] = row[4]
        termResult[row[0]] = row[5]
        termMenu[row[0]] = row[6]
        termMsgHead[row[0]] = row[8]
        termMsgBody[row[0]] = row[9]
        termDBUpdate[row[0]] = 0
        if row[1] == 'YES':
            termPongTime[row[0]] = millis()
        else:
            termPongTime[row[0]] = millis() - 10000
    conn.close()

def changeStatus():
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("SELECT * FROM base_action")
    S = req.fetchone()
    currentBaseStatus = str(S[0])
    # Добавить рассылку по mqtt
    client.publish("LOCK", ipAddress + '/STATUS/' + currentBaseStatus)

    req.execute("UPDATE base_status SET Current_status = ?",[currentBaseStatus])
    conn.commit()
    conn.close()

def openLock(ipAddress):
    client.publish("LOCK", ipAddress + '/OPEN')

def closeLock(num,ipAddress):
    client.publish("LOCK", ipAddress + '/CLOSE')

def blockLock(num, ipAddress):
    client.publish("LOCK", ipAddress + '/CLOSE')
    client.publish("LOCK", ipAddress + '/STATUS/BLOCKED')

def terminalUpdate(num,ipAddress):
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    sTmp = termMBody[num].get(1.0, END)
    req.execute("UPDATE term SET Msg_head = ?, Msg_body = ? WHERE Id == ?", \
                [termMHead[num].get(), sTmp.rstrip(), ipAddress])
    conn.commit()

    client.publish('TERM', ipAddress + '/MAILHEAD/' + termMHead[num].get())
    client.publish('TERM', ipAddress + '/MAILBODY/' + sTmp.rstrip())

    req.execute("UPDATE term SET Lock_status = ?, Hack_status = ? WHERE Id == ?", \
                [termLockButtonV[num].get(), termHackButtonV[num].get(), ipAddress])
    conn.commit()

    client.publish('TERM', ipAddress + '/LOCK/' + termLockButtonV[num].get())
    client.publish('TERM', ipAddress + '/HACK/' + termHackButtonV[num].get())

    s = termMListBL[num].get() + termMListBA[num].get() + termMListBT[num].get()
    tmpMenuList = []
    for i in s.split(','):
        if i != '':
            tmpMenuList.append(i)
            tmpMenuList.append(',')
    tmpMenuList[len(tmpMenuList)-1] = ''
    strMenuList = ''.join(tmpMenuList)
    req.execute("UPDATE term SET Menulist = ? WHERE Id == ?", \
                [strMenuList, ipAddress])

    client.publish('TERM', ipAddress + '/MENULIST/' + strMenuList)

    conn.commit()
    conn.close()

def on_connect(client, userdata, flags, rc):
    client.subscribe("TERMASK/#")

def on_message(client, userdata, msg):
    global my_ip
    global dbName
    commList = str(msg.payload).split('/')
    print str(msg.payload)
    if commList[0] in termLive.keys():
        j = termNumber[commList[0]]
        if commList[1] == 'PONG':
            termPongTime[commList[0]] = millis()
        if commList[1] == 'Hack_status':
            if commList[2] != termHackButtonV[j]:
                sqlOper = "UPDATE term SET " + commList[1] + "='" + commList[2] + "' WHERE Id == '" + commList[0] + "'"
                conn = sqlite3.connect(dbName)
                req = conn.cursor()
                req.execute(sqlOper)
                conn.commit()
                conn.close()
                if commList[2] == 'YES':
                    tButtonHY[j].select()
                else:
                    tButtonHN[j].select()
        elif commList[1] == 'Lock_status':
            if commList[2] != termLockButtonV[j]:
                sqlOper = "UPDATE term SET " + commList[1] + "='" + commList[2] + "' WHERE Id == '" + \
                          commList[0] + "'"
                conn = sqlite3.connect(dbName)
                req = conn.cursor()
                req.execute(sqlOper)
                conn.commit()
                conn.close()
                if commList[2] == 'YES':
                    tButtonLY[j].select()
                else:
                    tButtonLN[j].select()
        elif commList[1] == 'Menulist':
            tmplist = termMenu[commList[0]].split(",")
            if "1" in tmplist:
                termMListButtonLock[j].select()
            else:
                termMListButtonLock[j].deselect()
            if "2" in tmplist:
                termMListButtonAlert[j].select()
            else:
                termMListButtonAlert[j].deselect()
            if "3" in tmplist:
                termMListButtonText[j].select()
            else:
                termMListButtonText[j].deselect()
            sqlOper = "UPDATE term SET " + commList[1] + "='" + commList[2] + "' WHERE Id == '" + \
                        commList[0] + "'"
            conn = sqlite3.connect(dbName)
            req = conn.cursor()
            req.execute(sqlOper)
            conn.commit()
            conn.close()
        elif commList[1] == 'Msg_head':
            if commList[2].decode('utf-8') != termMHead[j].get():
                termMHead[j].delete(0, END)
                termMHead[j].insert(0, commList[2])
                conn = sqlite3.connect(dbName)
                req = conn.cursor()
                req.execute("UPDATE term SET Msg_head = ? WHERE Id == ?", \
                            [commList[2].decode('utf-8'), commList[0]])
                conn.commit()
                conn.close()
        elif commList[1] == 'Msg_body':
            sTmp = termMBody[j].get(1.0,END)
            if commList[2].decode('utf-8') != sTmp.rstrip():
                termMBody[j].delete(1.0, END)
                termMBody[j].insert(END, commList[2])
                conn = sqlite3.connect(dbName)
                req = conn.cursor()
                req.execute("UPDATE term SET Msg_body = ? WHERE Id == ?", \
                            [commList[2].decode('utf-8'), commList[0]])
                conn.commit()
                conn.close()
        elif commList[1] == 'DOLEVELDOWN':
            tmpStatus = indexStatus[currentBaseStatus]
            listStatus.select_clear(tmpStatus)
            if tmpStatus == 4 or tmpStatus == 5:
                listStatus.select_set(tmpStatus - 1)
                client.publish('TERM',commList[0] + "/ISLEVEL/YES")
                changeStatus()
        elif commList[1] == 'DOLOCKOPEN':
            client.publish('TERM', commList[0] + "/ISLOCK/YES")
            conn = sqlite3.connect(dbName)
            req = conn.cursor()
            req.execute("SELECT Id_lock FROM term WHERE Id == ?",[commList[0]])
            S = req.fetchone()
            conn.close()
            openLock(lockNumber[S[0]],S[0])

client_time = millis()

def workThread():
    global client_time
    global client
    global termDBUpdate
    c_time = millis()
    if c_time >= client_time + 1500:
        client.publish("TERM", '*/PING')
        client_time = c_time
        conn = sqlite3.connect(dbName)
        req = conn.cursor()
        j = 0
        for ipTerm in sorted(termPongTime.keys()):
            if c_time >= termPongTime[ipTerm] + 4000:
                req.execute("UPDATE term SET Alive = 'NO' WHERE Id == ?",[ipTerm])
                termLive[ipTerm] = 'NO'
                bg = 'red'
                termDBUpdate[ipTerm] = 0
            else:
                req.execute("UPDATE term SET Alive = 'YES' WHERE Id == ?",[ipTerm])
                termLive[ipTerm] = 'YES'
                bg = 'green'
                if(termDBUpdate[ipTerm] == 0):
                    client.publish("TERM",ipTerm + '/GETDB')
                    termDBUpdate[ipTerm] = 1
            conn.commit()
#            print ipTerm
            labelTerm[j]['bg'] = bg
            j += 1
        conn.close()
    labelStatus.after(1000, workThread)

getDBData()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_broker_ip, mqtt_broker_port, 5)
client.loop_start()

root = Tk()
root.title(u'Сервер управления базой')
root.geometry('800x600')

statusFrame = Frame(root)
labelStatus = Label(statusFrame,text=u'Текущий стаус базы: '+statusRussian[currentBaseStatus],\
width=30,bg=currentBaseStatus,fg=statusFontColor[currentBaseStatus],font='arial 13')
labelStatus.grid(row=0,column=0)

labelStatus.after_idle(workThread)

listStatus = Listbox(statusFrame,selectmode=SINGLE,height=2,width=30)
for i in colorRus:
     listStatus.insert(END,i) 
scrStatus = Scrollbar(statusFrame,command=listStatus.yview)
listStatus.configure(yscrollcommand=scrStatus.set)
listStatus.select_set(indexStatus[currentBaseStatus])
listStatus.grid(row=0,column=1)
scrStatus.grid(row=0,column=2)
buttonStatus = Button(statusFrame,text=u'Изменить статус базы',bg=currentBaseStatus, \
width=20,fg=statusFontColor[currentBaseStatus],font='arial 13',command=changeStatus)
buttonStatus.grid(row=0,column=3)
statusFrame.grid(row=0,column=0)

lockFrame = Frame(root)
imgOpen = PhotoImage(file='ButtonOpen.gif', width=35, height=35)
imgClose = PhotoImage(file='ButtonClose.gif', width=35, height=35)
imgBlock = PhotoImage(file='ButtonBlock.gif', width=35, height=35)
j = 0
for i in sorted(lockLive.keys()):
    if lockLive[i] == 'YES':
        bgLock = 'green'
        fgLock = 'black'
    else:
        bgLock = 'red'
        fgLock = 'black'
    frameLock.append(Frame(lockFrame,bd=2))
    labelLock.append(Label(frameLock[j], text=i, fg=fgLock, bg=bgLock, font='arial 13'))
    labelLock[j].grid(row=0, column=0, columnspan=2)
    lockNumber[i] = j
    if lockStatus[i] == 'OPEN':
        buttonOpenLock.append(Button(frameLock[j],image=imgClose,width=35,height=35,\
                                     command=lambda num=j,ip=i:closeLock(num,ip)))
        labelStatusLock.append(Label(frameLock[j], text=u'ОТКРЫТ', fg=fgLock, bg='green', font='arial 13'))
    else:
        buttonOpenLock.append(Button(frameLock[j],image=imgOpen,width=35,height=35,\
                                     command=lambda num=j,ip=i:openLock(num,ip)))
        labelStatusLock.append(Label(frameLock[j], text=u'ЗАКРЫТ', fg=fgLock, bg='red', font='arial 13'))
    buttonBlockLock.append(Button(frameLock[j],image=imgBlock,width=35,height=35,\
                                     command=lambda num=j,ip=i:blockLock(num,ip)))
    labelStatusLock[j].grid(row=2, column=0, columnspan=2)
    buttonOpenLock[j].grid(row=1, column=0)
    buttonBlockLock[j].grid(row=1, column=1)
    frameLock[j].grid(row=0,column=j)
    lockNumber[i] = j
    j += 1
lockFrame.grid(row=1,column=0)

j = 0
termFrame = Frame(root)
for i in sorted(termLive.keys()):
    if termLive[i] == 'YES':
        bgLock = 'green'
        fgLock = 'black'
    else:
        bgLock = 'red'
        fgLock = 'black'
    frameTerm.append(Frame(termFrame, bd=2))
    labelTerm.append(Label(frameTerm[j], text=i, fg=fgLock, bg=bgLock, font='arial 13'))
    labelTerm[j].grid(row=0, column=0, columnspan=5, sticky=W)
    termNumber[i] = j
    termHackButtonV.append(StringVar())
    if termHack[i] == 'YES':
        tButtonHY.append(Radiobutton(frameTerm[j], text="Взломан", variable=termHackButtonV[j], \
                              value='YES'))
        tButtonHY[j].select()
        tButtonHY[j].grid(row=1, column=0, sticky=W)
        tButtonHN.append(Radiobutton(frameTerm[j], text="Не взломан", variable=termHackButtonV[j], \
                              value='NO'))
        tButtonHN[j].grid(row=2, column=0, sticky=W)
    else:
        tButtonHY.append(Radiobutton(frameTerm[j], text="Взломан", variable=termHackButtonV[j], \
                              value='YES'))
        tButtonHY[j].grid(row=1, column=0, sticky=W)
        tButtonHN.append(Radiobutton(frameTerm[j], text="Не взломан", variable=termHackButtonV[j], \
                              value='NO'))
        tButtonHN[j].select()
        tButtonHN[j].grid(row=2, column=0, sticky=W)

    termLockButtonV.append(StringVar())
    if termLock[i] == 'YES':
        tButtonLY.append(Radiobutton(frameTerm[j], text="Блокирован", variable=termLockButtonV[j], \
                              value='YES'))
        tButtonLY[j].select()
        tButtonLY[j].grid(row=1, column=1, sticky=W)
        tButtonLN.append(Radiobutton(frameTerm[j], text="Разблокирован", variable=termLockButtonV[j], \
                              value='NO'))
        tButtonLN[j].grid(row=2, column=1, sticky=W)
    else:
        tButtonLY.append(Radiobutton(frameTerm[j], text="Блокирован", variable=termLockButtonV[j], \
                              value='YES'))
        tButtonLY[j].grid(row=1, column=1, sticky=W)
        tButtonLN.append(Radiobutton(frameTerm[j], text="Разблокирован", variable=termLockButtonV[j], \
                              value='NO'))
        tButtonLN[j].select()
        tButtonLN[j].grid(row=2, column=1, sticky=W)

    termMListLabel.append(Label(frameTerm[j], text="Выбор меню", fg=fgLock, bg=bgLock, font='arial 10'))
    termMListLabel[j].grid(row=1, column=2, columnspan=3)

    termMListBL.append(StringVar())
    termMListBA.append(StringVar())
    termMListBT.append(StringVar())
    termMListButtonLock.append(Checkbutton(frameTerm[j],text='Замок',variable=termMListBL[j],\
                                           onvalue="1,", offvalue=""))
    termMListButtonAlert.append(Checkbutton(frameTerm[j],text='Тревога',variable=termMListBA[j], \
                                            onvalue="2,", offvalue=""))
    termMListButtonText.append(Checkbutton(frameTerm[j],text='Текст',variable=termMListBT[j], \
                                           onvalue="3,", offvalue=""))

    tmplist = termMenu[i].split(",")

    if "1" in tmplist:
        termMListButtonLock[j].select()
    if "2" in tmplist:
        termMListButtonAlert[j].select()
    if "3" in tmplist:
        termMListButtonText[j].select()
    termMListButtonLock[j].grid(row=2, column=2)
    termMListButtonAlert[j].grid(row=2, column=3)
    termMListButtonText[j].grid(row=2, column=4)

    termMHead.append(Entry(frameTerm[j],width=65))
    termMHead[j].insert(0, termMsgHead[i])
    termMHead[j].grid(row=0, column=5, columnspan=2, sticky=W)

    termMBody.append(Text(frameTerm[j],width=62, height=5, wrap=WORD, font='arial 8'))
    termMBody[j].insert(END, termMsgBody[i])
    termMBodyScr.append(Scrollbar(frameTerm[j],command=termMBody[j].yview))
    termMBody[j].grid(row=1, column=5, rowspan=3, sticky=W)
    termMBodyScr[j].grid(row=1, column=6, rowspan=3, sticky=E)

    termMainButton.append(Button(frameTerm[j], text='Обновить всё!', width=50, \
                                 command=lambda num=j,ip=i:terminalUpdate(num,ip)))
    termMainButton[j].grid(row=3, column=0, columnspan=5)

    frameTerm[j].grid(row=j,column=0)

    j += 1

termFrame.grid(row=2, column=0, sticky=W)

root.mainloop()

#root.mainloop()