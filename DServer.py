# -*- coding: utf-8 -*-
from Tkinter import *
import paho.mqtt.client as mqtt
import socket, sqlite3
import image
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
    # Добавить MQTT команду на открытие замка по IP


def closeLock(num,ipAddress):
    global buttonOpenLock
    global imgClose
    global imgOpen
    global labelStatusLock
    print ipAddress
    print num
    labelStatusLock[num].config(text=u'ЗАКРЫТ', fg='black', bg='red')
    buttonOpenLock[num].config(image=imgOpen, command=lambda num=num,ip=ipAddress:openLock(num,ip))
    # Добавить MQTT команду на закрытие замка по IP

getDBData()

root = Tk()
root.title(u'Сервер управления базой')
root.geometry('800x600')

statusFrame = Frame(root)
labelStatus = Label(statusFrame,text=u'Текущий стаус базы: '+statusRussian[currentBaseStatus],\
width=30,height=3,bg=currentBaseStatus,fg=statusFontColor[currentBaseStatus],font='arial 14')
labelStatus.grid(row=0,column=0)
listStatus = Listbox(statusFrame,selectmode=SINGLE,height=4,width=30)
for i in colorRus:
     listStatus.insert(END,i) 
scrStatus = Scrollbar(statusFrame,command=listStatus.yview)
listStatus.configure(yscrollcommand=scrStatus.set)
listStatus.select_set(indexStatus[currentBaseStatus])
listStatus.grid(row=0,column=1)
scrStatus.grid(row=0,column=2)
buttonStatus = Button(statusFrame,text=u'Изменить статус базы',bg=currentBaseStatus, \
width=20,height=3,fg=statusFontColor[currentBaseStatus],font='arial 14',command=changeStatus)
buttonStatus.grid(row=0,column=3)
statusFrame.grid(row=0,column=0)

lockFrame = Frame(root)
imgOpen = PhotoImage(file='ButtonOpen.gif', width=35, height=35)
imgClose = PhotoImage(file='ButtonClose.gif', width=35, height=35)
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
    labelStatusLock[j].grid(row=2, column=0, columnspan=2)
    buttonOpenLock[j].grid(row=1, column=0)

    frameLock[j].grid(row=0,column=j)
    j += 1
lockFrame.grid(row=1,column=0)

root.mainloop()