# -*- coding: utf-8 -*-
from Tkinter import *
import paho.mqtt.client as mqtt
import socket, sqlite3
import image
#import Image
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
labelStatusLock = []
termLive = dict()
termHack = dict()
termHackButtonV = []
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
frameTerm = []
labelTerm = []
frameLock = []
buttonOpenLock = []
buttonBlockLock = []

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
    conn.close()
    conn.close()

def changeStatus():
    global currentBaseStatus
    global dbName
    currentBaseStatus = indexStatusReverse[(listStatus.curselection())[0]]
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("UPDATE base SET Current_status = ?",[currentBaseStatus])
    conn.commit()
    conn.close()
    labelStatus.configure(text= u'Текущий стаус базы: '+statusRussian[currentBaseStatus],\
    bg = currentBaseStatus, fg = statusFontColor[currentBaseStatus])
    buttonStatus.configure(bg = currentBaseStatus, fg = statusFontColor[currentBaseStatus])
    # Добавить рассылку по mqtt

def openLock(num,ipAddress):
    global buttonOpenLock
    global imgClose
    global imgOpen
    global labelStatusLock
    print ipAddress
    print num
    buttonOpenLock[num].config(image=imgClose, command=lambda num=num,ip=ipAddress:closeLock(num,ip))
    labelStatusLock[num].config(text=u'ОТКРЫТ', fg='black', bg='green')
    # Добавить MQTT команду на открытие замка по IP и запись в локальную базу

def closeLock(num,ipAddress):
    global buttonOpenLock
    global imgClose
    global imgOpen
    global labelStatusLock
    print ipAddress
    print num
    labelStatusLock[num].config(text=u'ЗАКРЫТ', fg='black', bg='red')
    buttonOpenLock[num].config(image=imgOpen, command=lambda num=num,ip=ipAddress:openLock(num,ip))
    # Добавить MQTT команду на закрытие замка по IP и запись в локальную базу

def blockLock(num, ipAddress):
    global buttonOpenLock
    global imgClose
    global imgOpen
    global labelStatusLock
    print ipAddress
    print num
    if labelStatusLock[num]['text'] == u'ОТКРЫТ':
        closeLock(num,ipAddress)
    if labelStatusLock[num]['text'] == u'БЛОКИРОВАН':
        labelStatusLock[num].config(text=u'ЗАКРЫТ', fg='black', bg='red')
        # Добавить MQTT команду на закрытие замка по IP и запись в локальную базу
    else:
        labelStatusLock[num].config(text=u'БЛОКИРОВАН', fg='black', bg='red')
        # Добавить MQTT команду на блокировку замка по IP и запись в локальную базу

def terminalUpdate(num,ipAddress):


    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("UPDATE term SET Msg_head = ?, Msg_body = ? WHERE Id == ?", \
                [termMHead[num].get(), termMBody[num].get(1.0, END), ipAddress])
    conn.commit()
    # добавить MQTT обновление заголовка и тела сообщения

    req.execute("UPDATE term SET Lock_status = ?, Hack_status = ? WHERE Id == ?", \
                [termLockButtonV[num].get(), termHackButtonV[num].get(), ipAddress])
    conn.commit()
    # добавить MQTT обновление статуса взлома и блокировки

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
    # добавить MQTT обновление списка меню

    conn.commit()

    conn.close()



getDBData()

root = Tk()
root.title(u'Сервер управления базой')
root.geometry('800x600')

statusFrame = Frame(root)
labelStatus = Label(statusFrame,text=u'Текущий стаус базы: '+statusRussian[currentBaseStatus],\
width=30,bg=currentBaseStatus,fg=statusFontColor[currentBaseStatus],font='arial 13')
labelStatus.grid(row=0,column=0)
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

    termHackButtonV.append(StringVar())
    if termHack[i] == 'YES':
        tButtonH = Radiobutton(frameTerm[j], text="Взломан", variable=termHackButtonV[j], \
                              value='YES')
        tButtoH.select()
        tButtonH.grid(row=1, column=0, sticky=W)
        tButtonH = Radiobutton(frameTerm[j], text="Не взломан", variable=termHackButtonV[j], \
                              value='NO')
        tButtonH.grid(row=2, column=0, sticky=W)
    else:
        tButtonH = Radiobutton(frameTerm[j], text="Взломан", variable=termHackButtonV[j], \
                              value='YES')
        tButtonH.grid(row=1, column=0, sticky=W)
        tButtonH = Radiobutton(frameTerm[j], text="Не взломан", variable=termHackButtonV[j], \
                              value='NO')
        tButtonH.select()
        tButtonH.grid(row=2, column=0, sticky=W)

    termLockButtonV.append(StringVar())
    if termLock[i] == 'YES':
        tButtonL = Radiobutton(frameTerm[j], text="Блокирован", variable=termLockButtonV[j], \
                              value='YES')
        tButtonL.select()
        tButtonL.grid(row=1, column=1, sticky=W)
        tButtonL = Radiobutton(frameTerm[j], text="Разблокирован", variable=termLockButtonV[j], \
                              value='NO')
        tButtonL.grid(row=2, column=1, sticky=W)
    else:
        tButtonL = Radiobutton(frameTerm[j], text="Блокирован", variable=termLockButtonV[j], \
                              value='YES')
        tButtonL.grid(row=1, column=1, sticky=W)
        tButtonL = Radiobutton(frameTerm[j], text="Разблокирован", variable=termLockButtonV[j], \
                              value='NO')
        tButtonL.select()
        tButtonL.grid(row=2, column=1, sticky=W)

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