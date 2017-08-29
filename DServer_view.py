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

baseStatusChg = 0
lockStatusChg = dict()

termHackAct = dict()
termLockAct = dict()
termMenuAct = dict()
termMsgHeadAct = dict()
termMsgBodyAct = dict()

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
termOper = dict()
termMenu = dict()
termMsgHead = dict()
termMsgBody = dict()
frameTerm = []
labelTerm = []
frameLock = []
buttonOpenLock = []
buttonBlockLock = []

start_time = datetime.now()

def millis():
    dt = datetime.now() - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms

def getDBData():
    global currentBaseStatus
    global dbName
    global colorRus
    global statusRussian
    global reversStatusRussian
    global indexStatus
    global indexStatusReverse
    global statusFontColor
    global lockLive
    global lockStatus
    global lockStatusChg
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT * from dict ORDER BY Id"):
        colorRus.append(row[2])
        statusRussian[row[1]] = row[2].upper()
        reversStatusRussian[row[2]] = row[1]
        indexStatus[row[1]] = row[0]
        indexStatusReverse[row[0]] = row[1]
        statusFontColor[row[1]] = row[3]
    req.execute("SELECT * FROM base_status")
    S = req.fetchone()
    currentBaseStatus = str(S[0])
    for row in req.execute("SELECT * from lock_status ORDER BY Id"):
        lockLive[row[0]] = row[1]
        lockStatus[row[0]] = row[2]
        lockStatusChg[row[0]] = 0
        print lockStatusChg[row[0]]
    for row in req.execute("SELECT * from term_status ORDER BY Id"):
        termLive[row[0]] = row[1]
        termHack[row[0]] = row[2]
        termLock[row[0]] = row[3]
        termOper[row[0]] = row[4]
        termMenu[row[0]] = row[5]
        termMsgHead[row[0]] = row[7]
        termMsgBody[row[0]] = row[8]
    conn.close()

def changeBaseStatusRequest():
    global currentBaseStatus
    global dbName
    global baseStatusChg
    currentBaseStatus = indexStatusReverse[(listStatus.curselection())[0]]
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("UPDATE base_action SET Current_status = ?",[currentBaseStatus])
    baseStatusChg = 1
    conn.commit()
    conn.close()

def changeBaseStatusConfirm():
    global baseStatusChg
    labelStatus.configure(text= u'Текущий стаус базы: '+statusRussian[currentBaseStatus],\
    bg = currentBaseStatus, fg = statusFontColor[currentBaseStatus])
    buttonStatus.configure(bg = currentBaseStatus, fg = statusFontColor[currentBaseStatus])
    baseStatusChg = 0

def openLockRequest(num,ipAddress):
    global buttonOpenLock
    global imgClose
    global imgOpen
    global labelStatusLock
    global lockStatusChg
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("UPDATE lock_action SET Status = 'OPEN' WHERE Id == ?", [ipAddress])
    conn.commit()
    conn.close()
    lockStatusChg[ipAddress] = 1

def openLockConfirm(num,ipAddress):
    global buttonOpenLock
    global imgClose
    global imgOpen
    global labelStatusLock
    global lockStatusChg
    print ipAddress
    print num
    buttonOpenLock[num].config(image=imgClose, command=lambda num=num,ip=ipAddress:closeLockRequest(num,ip))
    labelStatusLock[num].config(text=u'ОТКРЫТ', fg='black', bg='green')
    lockStatusChg[ipAddress] = 0

def closeLockRequest(num,ipAddress):
    global buttonOpenLock
    global imgClose
    global imgOpen
    global labelStatusLock
    global lockStatusChg
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("UPDATE lock_action SET Status = 'CLOSED' WHERE Id == ?", [ipAddress])
    conn.commit()
    conn.close()
    lockStatusChg[ipAddress] = 1

def closeLockConfirm(num, ipAddress):
    global buttonOpenLock
    global imgClose
    global imgOpen
    global labelStatusLock
    global lockStatusChg
    print ipAddress
    print num
    labelStatusLock[num].config(text=u'ЗАКРЫТ', fg='black', bg='red')
    buttonOpenLock[num].config(image=imgOpen, command=lambda num=num, ip=ipAddress: openLockRequest(num, ip))
    lockStatusChg[ipAddress] = 0

def blockLockRequest(num, ipAddress):
    global buttonOpenLock
    global imgClose
    global imgOpen
    global labelStatusLock
    global lockStatusChg
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    if labelStatusLock[num]['text'] == u'БЛОКИРОВАН':
        req.execute("UPDATE lock_action SET Status = 'CLOSED' WHERE Id == ?", [ipAddress])
    else:
        req.execute("UPDATE lock_action SET Status = 'BLOCKED' WHERE Id == ?", [ipAddress])
    conn.commit()
    conn.close()
    lockStatusChg[ipAddress] = 1

def blockLockConfirm(num, ipAddress):
    global buttonOpenLock
    global imgClose
    global imgOpen
    global labelStatusLock
    global lockStatusChg
    print ipAddress
    print num
    if labelStatusLock[num]['text'] == u'БЛОКИРОВАН':
        buttonOpenLock[num].config(image=imgOpen, command=lambda num=num, ip=ipAddress: openLockRequest(num, ip))
        labelStatusLock[num].config(text=u'ЗАКРЫТ', fg='black', bg='red')
    else:
        buttonOpenLock[num].config(image=imgOpen, command=lambda num=num, ip=ipAddress: openLockRequest(num, ip))
        labelStatusLock[num].config(text=u'БЛОКИРОВАН', fg='black', bg='red')
    lockStatusChg[ipAddress] = 0

def terminalUpdateRequest(num,ipAddress):
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    sTmp = termMBody[num].get(1.0, END)
    req.execute("UPDATE term_action SET Msg_head = ?, Msg_body = ? WHERE Id == ?", \
                [termMHead[num].get(), sTmp.rstrip(), ipAddress])
    conn.commit()
    req.execute("UPDATE term_action SET Lock_status = ?, Hack_status = ? WHERE Id == ?", \
                [termLockButtonV[num].get(), termHackButtonV[num].get(), ipAddress])
    conn.commit()
    s = termMListBL[num].get() + termMListBA[num].get() + termMListBT[num].get()
    tmpMenuList = []
    for i in s.split(','):
        if i != '':
            tmpMenuList.append(i)
            tmpMenuList.append(',')
    tmpMenuList[len(tmpMenuList)-1] = ''
    strMenuList = ''.join(tmpMenuList)
    req.execute("UPDATE term_action SET Menulist = ? WHERE Id == ?", [strMenuList, ipAddress])
    conn.commit()
    conn.close()

def scanDBChanges():
    global lockStatusChg
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("SELECT * FROM base_status")
    S = req.fetchone()
    if (currentBaseStatus == str(S[0]) and baseStatusChg == 1):
        changeBaseStatusConfirm()
    for row in req.execute("SELECT * from lock_action ORDER BY Id"):
        if (lockStatus[row[0]] == row[1] and lockStatusChg[row[0]] == 1):
            print "Confirm!"
            if row[1] == 'CLOSED':
                closeLockConfirm(lockNumber[row[0]], row[0])
            if row[1] == 'OPEN':
                openLockConfirm(lockNumber[row[0]], row[0])
            if row[1] == 'BLOCKED':
                blockLockConfirm(lockNumber[row[0]], row[0])
    for row in req.execute("SELECT * from term_action ORDER BY Id"):
        termHackAct[row[0]] = row[1]
        termLockAct[row[0]] = row[2]
        termMenuAct[row[0]] = row[3]
        termMsgHeadAct[row[0]] = row[5]
        termMsgBodyAct[row[0]] = row[6]
    for row in req.execute("SELECT * from term_status ORDER BY Id"):
        j = termNumber[row[0]]
        termLive[row[0]] = row[1]
        if row[1] == 'NO':
            bg = 'red'
        else:
            bg = 'green'
        labelTerm[j]['bg'] = bg
        termMListLabel[j]['bg'] = bg
        if row[4] == "UPDATE" :
            if row[2] == termHackAct[row[0]] :
                termHack[row[0]] = row[2]
                if row[2] == 'YES':
                    tButtonHY[j].select()
                else:
                    tButtonHN[j].select()
            termLock[row[0]] = row[3]
            if row[3] == termLockAct[row[0]]:
                if row[3] == 'YES':
                    tButtonLY[j].select()
                else:
                    tButtonLN[j].select()
#            termOper[row[0]] = row[4]
            req.execute("UPDATE term_status SET Operation = '' WHERE Id == ?", [row[0]])
            conn.commit()
    conn.close()

client_time = millis()

def workThread():
    scanDBChanges()
    labelStatus.after(500, workThread)

getDBData()

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
width=20,fg=statusFontColor[currentBaseStatus],font='arial 13',command=changeBaseStatusRequest)
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
                                     command=lambda num=j,ip=i:closeLockRequest(num,ip)))
        labelStatusLock.append(Label(frameLock[j], text=u'ОТКРЫТ', fg=fgLock, bg='green', font='arial 13'))
    elif lockStatus[i] == 'CLOSED':
        buttonOpenLock.append(Button(frameLock[j],image=imgOpen,width=35,height=35,\
                                     command=lambda num=j,ip=i:openLockRequest(num,ip)))
        labelStatusLock.append(Label(frameLock[j], text=u'ЗАКРЫТ', fg=fgLock, bg='red', font='arial 13'))
    else:
        buttonOpenLock.append(Button(frameLock[j],image=imgOpen,width=35,height=35,\
                                     command=lambda num=j,ip=i:openLockRequest(num,ip)))
        labelStatusLock.append(Label(frameLock[j], text=u'БЛОКИРОВАН', fg=fgLock, bg='red', font='arial 13'))
    buttonBlockLock.append(Button(frameLock[j],image=imgBlock,width=35,height=35,\
                                     command=lambda num=j,ip=i:blockLockRequest(num,ip)))
    labelStatusLock[j].grid(row=2, column=0, columnspan=2)
    buttonOpenLock[j].grid(row=1, column=0)
    buttonBlockLock[j].grid(row=1, column=1)
    frameLock[j].grid(row=0,column=j)
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
                                 command=lambda num=j,ip=i:terminalUpdateRequest(num,ip)))
    termMainButton[j].grid(row=3, column=0, columnspan=5)

    frameTerm[j].grid(row=j,column=0)

    j += 1

termFrame.grid(row=2, column=0, sticky=W)

root.mainloop()

#root.mainloop()