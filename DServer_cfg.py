# -*- coding: utf-8 -*-
from tkinter import *
#import paho.mqtt.client as mqtt
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


def terminalUpdateRequest(num,ip):
    print (num)
    print (ip)
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

def readTermMenuText():
    global numTerms
    i = 0
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT * from term_status ORDER BY Id"):
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

