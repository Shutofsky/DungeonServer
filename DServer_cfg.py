# -*- coding: utf-8 -*-
from tkinter import *
import paho.mqtt.client as mqtt
import socket, sqlite3, time
from datetime import datetime
from datetime import timedelta
#import image
#import Image
import time

dbName = 'DungeonStatus.db'
termWindow = []
menuFrame = []
menuLabel = []
menuBody = []
bodyFrame = []
bodyLabel = []
bodyHead = []
bodyText = []
bodyScroll = []
termButton = []

def terminalUpdateRequest(num,ip):
    print (num)
    print (ip)
    termButton[num].config(state=DISABLED)

def confirmClose(winID):
    winID.destroy()

def dbResetAllConfirm():
    dbResetAllConfirmW = Toplevel()
    confirmLabel = Label(dbResetAllConfirmW, text=u'Стереть ВСЁ содержимое базы, включая тексты. Вы уверены?')
    confirmYes = Button(dbResetAllConfirmW, text=u'Да, стереть!')
    confirmNo = Button(dbResetAllConfirmW, text=u'Нет! Отменить стирание!', \
                       command = lambda tmpW = dbResetAllConfirmW : confirmClose(tmpW))
    confirmLabel.grid(row=0, column=0, columnspan=2)
    confirmYes.grid(row=1, column=0)
    confirmNo.grid(row=1, column=1)

def dbResetOperConfirm():
    dbResetOperConfirmW = Toplevel()
    confirmLabel = Label(dbResetOperConfirmW, text=u'Стереть оперативное содержимое базы. Вы уверены?')
    confirmYes = Button(dbResetOperConfirmW, text=u'Да, стереть!')
    confirmNo = Button(dbResetOperConfirmW, text=u'Нет! Отменить стирание!', \
                       command = lambda tmpW = dbResetOperConfirmW : confirmClose(tmpW))
    confirmLabel.grid(row=0, column=0, columnspan=2)
    confirmYes.grid(row=1, column=0)
    confirmNo.grid(row=1, column=1)

root = Tk()
root.title(u'Сброс базы сервера')
root.geometry('250x80')
resetAll = Button(root, text='Сбросить всю базу!', \
                  command=lambda : dbResetAllConfirm())
resetOper = Button(root, text='Сбросить оперативные данные!', \
                   command=lambda: dbResetOperConfirm())
resetAll.grid(row=0, column=0)
resetOper.grid(row=1, column=0)

i = 0
conn = sqlite3.connect(dbName)
req = conn.cursor()
for row in req.execute("SELECT * from term_status ORDER BY Id"):
    termWindow.append(Toplevel())
#    termWindow[i].geometry('600x400')
    headTitle = u'Терминал ' + row[0]
    termWindow[i].title(headTitle)
    menuFrame.append(Frame(termWindow[i]))
    menuLabel.append(Label(menuFrame[i], text=u'Пункты меню: '))
    menuLabel[i].grid(row=0, column=0, sticky=W)
    menuBody.append(Entry(menuFrame[i], width=50))
    menuBody[i].insert(0, row[5])
    menuBody[i].grid(row=0, column=1, sticky=E)
    bodyLabel.append(Label(menuFrame[i], text=u'Заголовок: '))
    bodyLabel[i].grid(row=1, column=0, sticky=W)
    bodyHead.append(Entry(menuFrame[i], width=50))
    bodyHead[i].insert(0, row[7])
    bodyHead[i].grid(row=1, column=1, sticky=E)
    menuFrame[i].grid(row=0, column=0)
    bodyFrame.append(Frame(termWindow[i]))
    bodyText.append(Text(bodyFrame[i], width=62, height=10, wrap=WORD, font='arial 8'))
    bodyText[i].insert(END, row[8])
    bodyText[i].grid(row=1,column=0, sticky=W)
    bodyScroll.append(Scrollbar(bodyFrame[i], command=bodyText[i].yview))
    bodyScroll[i].grid(row=1, column=1, sticky=N+S)
    bodyFrame[i].grid(row=1, column = 0)
    termButton.append(Button(termWindow[i], text=u'Применить!', width=50, \
                             command=lambda num=i, ip=row[0]: terminalUpdateRequest(num, ip)))
    termButton[i].grid(row=2, column=0)

    i += 1

numTerms = i
conn.close()

root.mainloop()

